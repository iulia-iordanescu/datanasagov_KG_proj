"""
moves.py -- the main moves of 030_split, as called by 030_split.py.

    load_records            020's cleaned records, by id
    ground_truth_candidates the ground truth candidates pool, read from
                            annotations/, in its order; ids no longer in the
                            catalog are dropped
    induction_sample        texts_per_maintainer records from each of the
                            induction_maintainers largest maintainers, never
                            one from the pool, never one without text
    check_disjoint          no record is in both samples
    results                 write splits.json, once; report numbers, warnings

splits.json, shortened:

    {"ground_truth_candidates": {
        "records": [{"id": "3122be4c…", "position": 0, "maintainer": "Paul Gill",
                     "_origin": ["annotations/ground_truth_candidates.csv#3122be4c…",
                                 "020_clean/records.jsonl#3122be4c…"]}, …],
        "dropped": [{"id": "d57e1e22…", "position": 412, "reason": "…"}]},
     "induction_sample": {
        "records": [{"id": "…", "maintainer": "Earthdata Forum",
                     "_origin": ["020_clean/records.jsonl#…"]}, …],
        "maintainers": [{"maintainer": "Earthdata Forum", "records": 10649,
                         "eligible": 10356, "sampled": 15}, …]},
     "drawn": {"run_id": "030_split_…", "settings": {…}, "inputs": {…}}}

WRITE-ONCE. The ground truth candidates pool is annotated in order, and the
induction sample decides what the schema is learned from, so neither may
change under work in progress. If splits.json already exists it is kept as
it is; the run still draws, and warns if the new draw differs, which means
the catalog or the pool file changed since.
"""
from __future__ import annotations

import collections
import csv
import json
import os
import random
from dataclasses import dataclass, field
from pathlib import Path

from common import audit
from common.audit import ORIGIN_FIELD, check_origins, log, origin
from common.records_io import has_text, load_records as read_records
from common.step import Results

OUTPUT_NAME = "splits.json"
CANDIDATES = "ground_truth_candidates"      # the pool's name, in splits.json and messages
INDUCTION = "induction_sample"
SHOW = 20                                   # items listed in the report before "…"


@dataclass
class Candidates:
    records: list = field(default_factory=list)   # {"id", "position", "maintainer", "_origin"}
    dropped: list = field(default_factory=list)   # {"id", "position", "reason"}
    in_file: int = 0
    renamed: list = field(default_factory=list)   # {"id", "in_pool", "now"}: maintainer differs from 020's
    pool_ids: set = field(default_factory=set)    # every id in the file, kept or dropped


@dataclass
class Induction:
    records: list = field(default_factory=list)      # {"id", "maintainer", "_origin"}
    maintainers: list = field(default_factory=list)  # {"maintainer", "records", "eligible", "sampled"}
    catalog_share: float = 0.0                       # share of the catalog's records these maintainers hold


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
                             ORIGIN_FIELD: [origin("candidates", rid), origin("records", rid)]})
    log.info(f"  {len(pool.records):,} of {pool.in_file:,} ground truth candidates are in the records")
    return pool


def _check(settings: dict) -> None:
    for name in ("texts_per_maintainer", "induction_maintainers"):
        if settings[name] < 1:
            raise ValueError(f"{name} must be at least 1 (got {settings[name]})")


def induction_sample(records: dict, pool: Candidates, settings: dict) -> Induction:
    _check(settings)
    per, how_many = settings["texts_per_maintainer"], settings["induction_maintainers"]

    # Largest maintainers by their records in the catalog; ties broken by
    # name, so the choice never depends on the order of the file.
    size = collections.Counter(r["maintainer"] for r in records.values())
    chosen = sorted(size, key=lambda m: (-size[m], m))[:how_many]

    # Never a record of the pool (kept or dropped), never one with no text.
    eligible = collections.defaultdict(list)
    for rid, r in records.items():
        if r["maintainer"] in chosen and rid not in pool.pool_ids and has_text(r):
            eligible[r["maintainer"]].append(rid)

    sample = Induction(catalog_share=sum(size[m] for m in chosen) / len(records))
    rng = random.Random(settings["induction_seed"])
    for m in chosen:
        # Sorted ids: the same records and seed always give the same sample,
        # whatever order the records file is in.
        picked = rng.sample(sorted(eligible[m]), min(per, len(eligible[m])))
        sample.records += [{"id": rid, "maintainer": m, ORIGIN_FIELD: [origin("records", rid)]}
                           for rid in picked]
        sample.maintainers.append({"maintainer": m, "records": size[m],
                                   "eligible": len(eligible[m]), "sampled": len(picked)})
    log.info(f"  {len(sample.records):,} induction texts from {len(chosen)} maintainers")
    return sample


def check_disjoint(pool: Candidates, sample: Induction) -> None:
    shared = pool.pool_ids & {r["id"] for r in sample.records}
    if shared:
        raise ValueError(f"{len(shared)} records are in both samples, e.g. {sorted(shared)[:3]}; "
                         f"the induction sample must never contain a ground truth candidate")


# --------------------------------------------------------------------------

def _listed(items: list) -> str:
    shown = ", ".join(f"`{i}`" for i in items[:SHOW])
    return shown + (f" … ({len(items) - SHOW:,} more)" if len(items) > SHOW else "")


def _cell(value) -> str:
    return "" if value is None else str(value).replace("|", "\\|").replace("\n", " ")


def _samples(pool: Candidates, sample: Induction) -> dict:
    """The part of splits.json that says which records are in each sample."""
    return {CANDIDATES: {"records": pool.records, "dropped": pool.dropped},
            INDUCTION: {"records": sample.records, "maintainers": sample.maintainers}}


def results(pool: Candidates, sample: Induction, inputs: dict, settings: dict,
            output: Path) -> Results:
    path = output / OUTPUT_NAME
    drawn = _samples(pool, sample)
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
        from common.step import input_files
        document = {**drawn, "drawn": {
            "run_id": audit.current_run_id(), "settings": settings,
            "inputs": {name: audit.ref_path(input_files(Path(p))[0]) for name, p in inputs.items()}}}
        tmp = path.with_suffix(".json.part")
        tmp.write_text(json.dumps(document, indent=1, ensure_ascii=False), encoding="utf-8",
                       newline="\n")
        os.replace(tmp, path)
        log.info(f"  wrote {OUTPUT_NAME}")

    if pool.dropped:
        warnings.append(f"{len(pool.dropped)} ground truth candidate{'s are' if len(pool.dropped) != 1 else ' is'} "
                        f"no longer in the catalog and {'were' if len(pool.dropped) != 1 else 'was'} dropped; "
                        f"the others keep their positions. Listed in the report.")
    if pool.renamed:
        warnings.append(f"{len(pool.renamed)} ground truth candidates have a different maintainer "
                        f"in 020's records than in the pool file (e.g. a spelling now joined "
                        f"differently); the records' maintainer is used. Listed in the report.")
    short = [m for m in sample.maintainers if m["sampled"] < settings["texts_per_maintainer"]]
    if short:
        warnings.append(f"{len(short)} induction maintainer{'s have' if len(short) != 1 else ' has'} "
                        f"fewer than {settings['texts_per_maintainer']} eligible records, so "
                        f"{'they' if len(short) != 1 else 'it'} gave fewer: "
                        f"{', '.join(m['maintainer'] for m in short)}.")
    for items, what in ((pool.records, "ground truth candidates"), (sample.records, "induction texts")):
        missing = check_origins(items, what)
        if missing:
            warnings.append(missing)

    lines = []
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
        f"| Maintainer differs from 020's | {len(pool.renamed):,} |", ""]
    if pool.dropped:
        lines += ["Dropped candidates:", "", "| Position | Id | Reason |", "|---:|---|---|"]
        lines += [f"| {d['position']} | {d['id']} | {d['reason']} |" for d in pool.dropped]
        lines.append("")
    if pool.renamed:
        lines += ["Candidates whose maintainer changed:", "", "| Id | In the pool file | In 020's records |",
                  "|---|---|---|"]
        lines += [f"| {r['id']} | {_cell(r['in_pool'])} | {_cell(r['now'])} |" for r in pool.renamed[:SHOW]]
        lines.append("")
    by_maintainer = collections.Counter(r["maintainer"] for r in pool.records).most_common(10)
    lines += ["Largest maintainers in the pool:", "", "| Maintainer | Candidates |", "|---|---:|"]
    lines += [f"| {_cell(m)} | {n:,} |" for m, n in by_maintainer]
    lines += ["",
              "### Induction sample", "",
              f"{len(sample.records):,} records: up to {settings['texts_per_maintainer']} from each "
              f"of the {settings['induction_maintainers']} largest maintainers, which hold "
              f"{sample.catalog_share:.1%} of the catalog's records. *Eligible* excludes every "
              f"ground truth candidate and every record without a title or notes.", "",
              "| Maintainer | Records | Eligible | Sampled |", "|---|---:|---:|---:|"]
    lines += [f"| {_cell(m['maintainer'])} | {m['records']:,} | {m['eligible']:,} | {m['sampled']} |"
              for m in sample.maintainers]
    lines += ["", f"Records in both samples: **0** (checked)."]

    return Results(
        files=[path],
        headline={"ground truth candidates": len(pool.records), "induction texts": len(sample.records)},
        details="\n".join(lines),
        warnings=warnings,
    )
