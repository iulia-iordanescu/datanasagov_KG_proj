"""
moves.py -- the main moves of 030_split, as called by 030_split/run.py.

    stage 1  (here)  load_records             code: 020's cleaned records, by id
    stage 2  (here)  ground_truth_candidates  code: the pool, read from annotations/, in its order; ids no longer
                                              in the catalog dropped; each record's part (tuning or held-out)
    stage 3  (here)  induction_candidates     code: every maintainer's records that may be learned from (not in
                                              the pool, with text), in a fixed random order
    stage 4  (here)  check_disjoint           code: no record is in both
    -        (here)  results                  writes splits.json, once; the report

Terms are as defined in docs/terminology.md.

Each ground truth candidate also gets its part, for scoring (070):

    tuning     its scores may be looked at while improving the pipeline
    held-out   its scores are kept aside, looked at only at the end: the
               number reported as how well the pipeline works

by a rule fixed here, before any scoring: pool positions 0-5 are tuning (the
hand-built schema was written while annotating them, so they're not unseen);
from position 6 on, every third record is held-out (8, 11, 14, ...) and the
rest tuning. Both parts grow as annotation proceeds in pool order, and both
stay fair samples, since the pool is shuffled. A position is the record's
row in the pool file, so a dropped candidate changes no one's part.

Both lists are ordered so that their first records are always a fair random
sample: the pool was shuffled when it was drawn, and each maintainer's
induction candidates are shuffled here. Later steps take from the top: 050
annotates the pool in order; 040 learns the schema from the first
texts_per_maintainer induction candidates of each of its largest maintainers.
Taking more later (more texts, or more maintainers) keeps the records already
taken, so model calls already paid for stay valid.

splits.json, shortened:

    {"ground_truth_candidates": {
        "records": [{"id": "3122be4c…", "position": 0, "maintainer": "Paul Gill", "part": "tuning",
                     "_origin": ["annotations/ground_truth_candidates.csv#3122be4c…",
                                 "020_clean/records.jsonl#3122be4c…"]}, …],
        "dropped": [{"id": "d57e1e22…", "position": 946, "reason": "…"}]},
     "induction_candidates": {
        "maintainers": [{"maintainer": "Earthdata Forum", "rank": 1,
                         "records": 10649, "eligible": 10356}, …],
        "records": [{"id": "…", "maintainer": "Earthdata Forum", "position": 0,
                     "_origin": ["020_clean/records.jsonl#…"]}, …]},
     "drawn": {"run_id": "030_split_…", "settings": {…}, "inputs": {…}}}

WRITE-ONCE. The pool is annotated in order, and the induction candidates'
order decides what the schema is learned from, so neither may change under
work in progress. If splits.json already exists it is kept as it is; the run
still draws, and warns if the new draw differs, which means the catalog or the
pool file changed since.
"""
from __future__ import annotations

import collections
import csv
import json
import random
from dataclasses import dataclass, field
from pathlib import Path

from common import audit
from common.audit import ORIGIN_FIELD, check_origins, log, origin
from common.files import write_json
from common.records_io import has_text, load_records as read_records
from common.report import cell
from common.step import Results, input_files

OUTPUT_NAME = "splits.json"
CANDIDATES = "ground_truth_candidates"      # the pool, in splits.json and messages
INDUCTION = "induction_candidates"
SHOW = 20                                   # rows listed in the report before "…"
#: The tuning / held-out rule (see above). Fixed, not settings: changing them
#: after scores have been looked at would defeat the held-out part.
ALL_TUNING_BEFORE = 6                       # positions 0-5: tuning
HELD_OUT_EVERY = 3                          # from there on, every third position is held-out


def part_of(position: int) -> str:
    """ "tuning" or "held-out", by the rule above: 8, 11, 14, … are held-out."""
    if position < ALL_TUNING_BEFORE:
        return "tuning"
    return "held-out" if (position - ALL_TUNING_BEFORE) % HELD_OUT_EVERY == HELD_OUT_EVERY - 1 else "tuning"


@dataclass
class Candidates:
    records: list = field(default_factory=list)   # {"id", "position", "maintainer", "part", "_origin"}
    dropped: list = field(default_factory=list)   # {"id", "position", "reason"}
    in_file: int = 0
    renamed: list = field(default_factory=list)   # {"id", "in_pool", "now"}: maintainer differs from 020's
    pool_ids: set = field(default_factory=set)    # every id in the file, kept or dropped


@dataclass
class Induction:
    records: list = field(default_factory=list)      # {"id", "maintainer", "position", "_origin"}
    maintainers: list = field(default_factory=list)  # {"maintainer", "rank", "records", "eligible"}
    in_pool: int = 0                                 # records left out: ground truth candidates
    without_text: int = 0                            # records left out: no title or notes


# --------------------------------------------------------------------------

def load_records(inputs: dict) -> dict:
    records = read_records(inputs["records"])
    log.info(f"  {len(records):,} records from 020")
    return records


def ground_truth_candidates(inputs: dict, records: dict) -> Candidates:
    path = Path(inputs["candidates"])
    with open(path, encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    if not rows or "id" not in rows[0] or "maintainer" not in rows[0]:
        raise ValueError(f"{path.name} needs the columns id and maintainer")
    ids = [row["id"].strip() for row in rows]
    repeated = sorted(i for i, n in collections.Counter(ids).items() if n > 1)
    if repeated:
        raise ValueError(f"{path.name} lists these ids more than once: {', '.join(repeated[:5])}")

    pool = Candidates(in_file=len(rows), pool_ids=set(ids))
    for position, row in enumerate(rows):
        rid = row["id"].strip()
        record = records.get(rid)
        if record is None:
            pool.dropped.append({"id": rid, "position": position,
                                 "reason": "not in 020's records: no longer in the catalog"})
            log.debug(f"candidate #{position} {rid}: not in the records; dropped")
            continue
        if row["maintainer"] != record["maintainer"]:
            pool.renamed.append({"id": rid, "in_pool": row["maintainer"], "now": record["maintainer"]})
        pool.records.append({"id": rid, "position": position, "maintainer": record["maintainer"],
                             "part": part_of(position),
                             ORIGIN_FIELD: [origin("candidates", rid), origin("records", rid)]})
    log.info(f"  {len(pool.records):,} of {pool.in_file:,} ground truth candidates are in the records")
    return pool


def induction_candidates(records: dict, pool: Candidates, settings: dict) -> Induction:
    # Maintainers ranked by their records in the catalog; ties broken by name,
    # so the ranking never depends on the order of the file.
    size = collections.Counter(r["maintainer"] for r in records.values())
    ranked = sorted(size, key=lambda m: (-size[m], m))

    # Eligible: never a record of the pool (kept or dropped), never one with
    # no title or notes, which gives the schema nothing to learn from.
    eligible = collections.defaultdict(list)
    induction = Induction()
    for rid, r in records.items():
        if rid in pool.pool_ids:
            induction.in_pool += 1
        elif not has_text(r):
            induction.without_text += 1
        else:
            eligible[r["maintainer"]].append(rid)

    for rank, m in enumerate(ranked, 1):
        # Each maintainer's order has its own random generator, seeded by the
        # seed and the maintainer's name, so it never depends on any other
        # maintainer. The ids are sorted first, so the same records and seed
        # always give the same order, whatever the order of the file.
        # random.sample returns its picks in selection order, "so that all
        # sub-slices will also be valid random samples" (Python docs): the
        # first k are a random sample of the maintainer for every k.
        rng = random.Random(f"{settings['induction_seed']}/{m}")
        order = rng.sample(sorted(eligible[m]), len(eligible[m]))
        induction.records += [{"id": rid, "maintainer": m, "position": i,
                               ORIGIN_FIELD: [origin("records", rid)]}
                              for i, rid in enumerate(order)]
        induction.maintainers.append({"maintainer": m, "rank": rank,
                                      "records": size[m], "eligible": len(order)})
    log.info(f"  {len(induction.records):,} induction candidates across {len(ranked):,} maintainers")
    return induction


def check_disjoint(pool: Candidates, induction: Induction) -> None:
    shared = pool.pool_ids & {r["id"] for r in induction.records}
    if shared:
        raise ValueError(f"{len(shared)} records are both ground truth candidates and induction "
                         f"candidates, e.g. {sorted(shared)[:3]}; the two must never overlap")


# --------------------------------------------------------------------------

def _lists(pool: Candidates, induction: Induction) -> dict:
    """The part of splits.json that says which records are in each list."""
    return {CANDIDATES: {"records": pool.records, "dropped": pool.dropped},
            INDUCTION: {"maintainers": induction.maintainers, "records": induction.records}}


def results(pool: Candidates, induction: Induction, inputs: dict, settings: dict,
            output: Path) -> Results:
    path = output / OUTPUT_NAME
    drawn = _lists(pool, induction)
    warnings = []

    kept, same = path.exists(), True
    if kept:
        existing = json.loads(path.read_text(encoding="utf-8"))
        same = {k: existing.get(k) for k in drawn} == drawn
        log.info(f"  {OUTPUT_NAME} already exists: kept as it is"
                 + ("" if same else " (this run's draw differs)"))
        if not same:
            warnings.append(f"{OUTPUT_NAME} already exists and was kept, but this run's draw "
                            f"differs from it: the records, the pool file or the settings changed "
                            f"since it was written. Work in progress relies on the kept file; to "
                            f"replace it, delete it and rerun.")
    else:
        document = {**drawn, "drawn": {
            "run_id": audit.current_run_id(), "settings": settings,
            "inputs": {name: audit.ref_path(input_files(Path(p))[0]) for name, p in inputs.items()}}}
        write_json(path, document)
        log.info(f"  wrote {OUTPUT_NAME}")

    if pool.dropped:
        n = len(pool.dropped)
        warnings.append(f"{n} ground truth candidate{'s are' if n != 1 else ' is'} no longer in "
                        f"the catalog and {'were' if n != 1 else 'was'} dropped; the others keep "
                        f"their positions. Listed in the report.")
    if pool.renamed:
        warnings.append(f"{len(pool.renamed)} ground truth candidates have a different maintainer "
                        f"in 020's records than in the pool file (e.g. a spelling now joined "
                        f"differently); the records' maintainer is used. Listed in the report.")
    for items, what in ((pool.records, "ground truth candidates"),
                        (induction.records, "induction candidates")):
        missing = check_origins(items, what)
        if missing:
            warnings.append(missing)

    lines = ["### What this run worked on", "",
             f"{len(induction.records) + induction.in_pool + induction.without_text:,} cleaned records from 020, and the {pool.in_file:,} records of "
             f"`{audit.ref_path(Path(inputs['candidates']))}`.", ""]
    if kept:
        lines += [f"**{OUTPUT_NAME} already existed and was kept as it is** (write-once). "
                  + ("This run's draw is identical to it, so the numbers below describe the kept file."
                     if same else
                     "This run's draw DIFFERS from it (see Warnings); the numbers below describe "
                     "this run's draw, not the kept file."), ""]
    lines += [
        "### Ground truth candidates pool", "",
        "| | |", "|---|---:|",
        f"| In `{audit.ref_path(Path(inputs['candidates']))}` | {pool.in_file:,} |",
        f"| Dropped: no longer in the catalog | {len(pool.dropped):,} |",
        f"| **Kept, in pool order** | **{len(pool.records):,}** |",
        f"| of which tuning | {sum(r['part'] == 'tuning' for r in pool.records):,} |",
        f"| of which held-out (from position {ALL_TUNING_BEFORE} on, every {HELD_OUT_EVERY}rd) | "
        f"{sum(r['part'] == 'held-out' for r in pool.records):,} |",
        f"| Maintainer differs from 020's | {len(pool.renamed):,} |", ""]
    if pool.dropped:
        lines += ["Dropped candidates:", "", "| Position | Id | Reason |", "|---:|---|---|"]
        lines += [f"| {d['position']} | {d['id']} | {d['reason']} |" for d in pool.dropped]
        lines.append("")
    if pool.renamed:
        lines += ["Candidates whose maintainer changed:", "",
                  "| Id | In the pool file | In 020's records |", "|---|---|---|"]
        lines += [f"| {r['id']} | {cell(r['in_pool'])} | {cell(r['now'])} |" for r in pool.renamed[:SHOW]]
        lines.append("")
    by_maintainer = collections.Counter(r["maintainer"] for r in pool.records).most_common(10)
    lines += ["Largest maintainers in the pool:", "", "| Maintainer | Candidates |", "|---|---:|"]
    lines += [f"| {cell(m)} | {n:,} |" for m, n in by_maintainer]

    total = len(induction.records) + induction.in_pool + induction.without_text
    lines += ["",
              "### Induction candidates", "",
              "Every maintainer's records that the schema may be learned from, each maintainer's "
              "in a fixed random order. 040 takes the first `texts_per_maintainer` of each of its "
              "`induction_maintainers` largest maintainers.", "",
              "| | |", "|---|---:|",
              f"| Records | {total:,} |",
              f"| Left out: ground truth candidates | {induction.in_pool:,} |",
              f"| Left out: no title or notes | {induction.without_text:,} |",
              f"| **Induction candidates** | **{len(induction.records):,}** |",
              f"| Maintainers | {len(induction.maintainers):,} |", "",
              f"Largest maintainers (all {len(induction.maintainers):,} are in `{OUTPUT_NAME}`):", "",
              "| Rank | Maintainer | Records | Induction candidates |", "|---:|---|---:|---:|"]
    lines += [f"| {m['rank']} | {cell(m['maintainer'])} | {m['records']:,} | {m['eligible']:,} |"
              for m in induction.maintainers[:SHOW]]
    lines += ["", "Records in both lists: **0** (checked)."]

    return Results(
        files=[path],
        headline={"ground truth candidates": len(pool.records),
                  "induction candidates": len(induction.records)},
        details="\n".join(lines),
        warnings=warnings,
    )
