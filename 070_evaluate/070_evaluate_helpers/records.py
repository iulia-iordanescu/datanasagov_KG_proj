"""
records.py -- stage 1: which records are evaluated, and what is known about
each.

Evaluation refuses to run while the ground truth has the same classed triple
twice in a record (common/common_helpers/ground_truth.py, gt.repeats), or while
a finished record uses an entity class or predicate the ground truth schema
lacks (a coined one: common.ground_truth.with_coined), since stage 2 can't
translate into it. Both stop before anything is shown or asked. Every
other warning found here (ground truth problems, records left out, …) is
shown before anything is evaluated, and the person is asked whether to go
ahead (unless confirm_paid_calls is false).

A record is evaluated when a person has finished it in the ground truth
(all_facts_extracted = 1 on every row) AND step 060's last run extracted from it.
Of those, only the FAIR SAMPLE is evaluated: for EACH PART of the pool (tuning,
held-out) separately, the longest run of that part's first records (in pool
order) that are all evaluated. The pool is shuffled, so its order restricted to
one part is still random, and that run is a fair sample of the part (and the two
runs together of the catalog), which the margins of error require (see stats.py).
An unfinished record of one part never holds back the other part. A record after
a gap in its own part (an unfinished or unextracted record before it) or not in
the pool at all (hand-picked) is left out and listed, with what to do.

For each evaluated record: its pool position, its part (tuning or held-out,
from 030), its stratum (from the pool file), its title, its ground
truth triples and describes triple, 060's extracted triples and describes triple,
how many items 060's checks removed from it, per reason (extracted_triples_removed.csv),
and its twin kind (docs/terminology.md, twin): what it shares with a record
the current schema was learned from (060's schema_used.json, learned_from),
"" when it isn't a twin, None when that isn't known.
"""
from __future__ import annotations

import collections
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace

from common.audit import ref_path
from common.files import read_csv
from common.ground_truth import (HELD_OUT, coined_uses, fair_prefix, pool_parts, read_ground_truth, read_pool, twin_kinds,
                                 with_coined)
from common.llm import confirm, numbered, show_warnings
from common.partial_reviews import read_reviews, review_problems
from common.records_io import load_records
from common import dropped
from common.report import named
from common.schema_io import read_ground_truth_schema
from common.step import MANIFEST_NAME, check_settings, input_files, repo_path
from common.stop import Stop
from common.triples_io import is_describes

AGAIN = "then run `py 070_evaluate/run.py` again."


@dataclass
class Evaluated:
    records: list = field(default_factory=list)    # see pick_records
    left_out: dict = field(default_factory=dict)   # {reason: [ids]}
    notes: list = field(default_factory=list)      # shown (and asked about) before evaluating, and in the report
    pool: list = field(default_factory=list)       # the pool's ids, in order
    pool_strata: dict = field(default_factory=dict)  # {stratum: pool records in it}
    ground_truth: object = None                    # common.ground_truth.GroundTruth
    schema_used: dict = field(default_factory=dict)  # 060's schema_used.json
    unfinished: int = 0                            # ground truth records not finished yet
    reviews: dict = field(default_factory=dict)    # a person's verdicts on partial pairs (common/common_helpers/partial_reviews.py)
    review_problems: list = field(default_factory=list)  # rows of that file whose verdict is neither of the two
    extraction_made: dict = field(default_factory=dict)  # 060's run: run id, model, settings (from its details file)
    catalog_records: int = 0                       # records in 020's records.jsonl: the whole catalog
    learned_from: dict = field(default_factory=dict)  # the records the current schema was learned from (060's schema_used.json)
    extraction_manifest: dict = field(default_factory=dict)  # 060's _manifest.json: its run's code version, settings, prompts, inputs
    extraction_failed: list = field(default_factory=list)  # finished records 060's model calls failed for, with why and
                                                   # maintainer (common/common_helpers/dropped.py); left out of every number
    finished: list = field(default_factory=list)   # the finished ground truth records, {"id", "maintainer"}


def _triples(rows: list) -> tuple:
    """(triples, describes triple or None): rows with subject, predicate, and object."""
    triples, describes = [], None
    for r in rows:
        if not (r.get("subject") and r.get("predicate") and r.get("object")):
            continue                                   # "annotated, states no triples"
        if is_describes(r):
            describes = describes or r
        else:
            triples.append(r)
    return triples, describes


def refusal(repeats: list) -> str:
    """Why evaluation can't run: every classed triple that appears more than
    once in a record (common.ground_truth's gt.repeats), numbered."""
    n = len(repeats)
    how_often = "twice" if all(r["copies"] == 2 for r in repeats) else "more than once"
    head = (f"Step 070 can't evaluate: {n} classed triple{'s' if n != 1 else ''} "
            f"{'appear' if n != 1 else 'appears'} {how_often} in a record of the ground truth, and only one "
            f"copy could be paired.")
    return head + "\n" + numbered([r["message"][0].upper() + r["message"][1:] for r in repeats])



def check_coined(gt, ground_truth_schema_path) -> None:
    """Stop if a finished record's ground truth triples or describes triple use an entity class or predicate that
    the ground truth schema lacks (a coined one): stage 2 translates only into the ground truth schema. Only the
    finished records are evaluated, so only theirs must use it."""
    finished = SimpleNamespace(rows=[r for r in gt.rows if gt.records.get(r["id"], {}).get("finished")])
    coined = with_coined(read_ground_truth_schema(ground_truth_schema_path), finished)["coined"]
    if coined["entity_classes"] or coined["predicates"]:
        uses = coined_uses(finished, coined)
        raise Stop(f"The finished records' ground truth triples and describes triples use {len(uses)} "
                   f"entity class(es) or predicate(s) that aren't in the ground truth schema ({ref_path(Path(ground_truth_schema_path))}), so 070 can't translate into "
                   f"them: {named(uses, 10, '; ')}. For each one, either add it to the ground truth schema with a "
                   f"one-line definition (`py helpers/annotate.py`, view *Ground truth*: the ✖ under it has a "
                   f"button), or fix the typo where it's used; {AGAIN}")


#: In a "source:" line of the ground truth schema (written by the annotation tool), the held-out records it names.
HELD_OUT_SOURCE = re.compile(r"held-out\s+(#\d+(?:\s*,\s*#\d+)*)")


def held_out_sources(ground_truth_schema_path, pool_rows: list) -> list:
    """The ground truth schema's entity classes and predicates whose "source:" line names a held-out record, i.e. that
    were added while a held-out record used them, though the ground truth schema is frozen for held-out records
    (annotations/guidelines.md, Before you start): [(kind, component class, source, [(pool position, record id)])]."""
    held = {r["position"]: r["id"] for r in pool_rows if r.get("part") == HELD_OUT}
    sources = read_ground_truth_schema(ground_truth_schema_path)["sources"]
    found = []
    for section, kind in (("entity_classes", "entity class"), ("predicates", "predicate")):
        for name, source in sources[section].items():
            named_ = [int(n) for m in HELD_OUT_SOURCE.finditer(source) for n in re.findall(r"\d+", m.group(1))]
            records = [(n, held[n]) for n in named_ if n in held]
            if records:
                found.append((kind, name, source, records))
    return found


def _mark_twins(evaluated: Evaluated, catalog: dict, inputs: dict) -> None:
    """Each evaluated record's "twin": its twin kind against the records the current schema was learned from
    (common.ground_truth.twin_kinds), "" when it isn't a twin, None when that isn't known (a note says why, and
    what to do)."""
    learned = evaluated.schema_used.get("learned_from") or {}
    evaluated.learned_from = learned
    if not learned.get("known"):
        why = (learned.get("how") or [f"{repo_path(inputs['schema_used'])} doesn't say (an older step 060 wrote it)"])[0]
        evaluated.notes.append(f"Which records the current schema was learned from isn't known: {why}. So 070 can't "
                               f"tell which evaluated records are twins (the same title, the same `notes`, or both as a record"
                               f"the schema was learned from; docs/terminology.md, section *Evaluating extraction*), and gives no "
                               f"numbers without them. To get them, extract with the induced schema or the ground truth schema "
                               f"(`py 060_extract/run.py`), then run `py 070_evaluate/run.py` again.")
        for r in evaluated.records:
            r["twin"] = None
        return
    kind = twin_kinds({r["id"]: catalog.get(r["id"], {}) for r in evaluated.records},
                       [catalog[i] for i in learned["ids"] if i in catalog])
    for r in evaluated.records:
        r["twin"] = kind[r["id"]]


def _first_gap(order: list, part: str, positions: dict, taken: set, finished: set, in_ground_truth) -> str:
    """The first record of one part (`order`: that part's ids in pool order) that is not taken, why, and what brings
    it in (for messages); "" if none."""
    gap = next((rid for rid in order if rid not in taken), None)
    if gap is None:
        return ""
    where = f"pool position #{positions[gap]} (`{gap}`)"
    head = f"The first {part} record missing from the fair sample of the {part} part is {where}"
    if gap in finished:
        return f"{head}: finished, but not extracted by 060's last run. Run `py 060_extract/run.py`"
    if gap in in_ground_truth:
        return f"{head}: not finished in the ground truth. Finish it in `py helpers/annotate.py` (tick *All facts extracted*), run `py 060_extract/run.py`"
    return (f"{head}: not in the ground truth yet. Draft it with "
            f"`py 050_annotate/run.py` (set --part {part}), correct and finish it in `py helpers/annotate.py`, run `py 060_extract/run.py`")


def pick_records(inputs: dict, settings: dict) -> Evaluated:
    check_settings(settings, {})
    evaluated = Evaluated()
    gt_files = input_files(Path(inputs["ground_truth"]))
    gt = evaluated.ground_truth = read_ground_truth(gt_files[0].parent)        # run_step made sure there is one
    evaluated.notes += [f"Ground truth, {p}" for p in gt.problems]
    if gt.repeats:
        raise Stop(refusal(gt.repeats))
    check_coined(gt, inputs["ground_truth_schema"])
    pool_rows = read_pool(inputs["splits"])
    if any("part" not in r for r in pool_rows):
        splits = repo_path(inputs["splits"])
        raise Stop(f"{splits} has no tuning / held-out part for its records (an older step 030 wrote it), so 070 "
                   f"can't keep the held-out part apart. Delete {splits}, run `py 030_split/run.py`, then run "
                   f"`py 070_evaluate/run.py` again.")
    evaluated.pool = [r["id"] for r in pool_rows]
    frozen = held_out_sources(inputs["ground_truth_schema"], pool_rows)
    if frozen:
        evaluated.notes.append(
            f"{len(frozen)} entity class(es) or predicate(s) of the ground truth schema "
            f"({ref_path(Path(inputs['ground_truth_schema']))}) were added from held-out records, though the ground truth "
            f"schema is frozen for held-out records (annotations/guidelines.md, Before you start): "
            + named([f"{name} ({kind}; source: {source}; held-out "
                     + ", ".join(f"pool position {n} ({rid})" for n, rid in records) + ")"
                     for kind, name, source, records in frozen], 10, "; ")
            + ". So those held-out records shaped the ground truth schema, and their numbers may flatter the pipeline. "
              "In those records, use an entity class or predicate the ground truth schema had before, or delete the "
              "ground truth triple and write the fact in annotations/left_out.md with a question for the experts; "
              "then delete the entry from the ground truth schema if no tuning record uses it, or change its source "
              "line to name only the tuning records that use it; " + AGAIN)
    by_id = {r["id"]: r for r in pool_rows}
    strata = {r["id"].strip(): (r.get("stratum") or "").strip() for r in read_csv(Path(inputs["candidates"]))}
    for r in pool_rows:
        g = strata.get(r["id"], "")
        evaluated.pool_strata[g] = evaluated.pool_strata.get(g, 0) + 1
    details = json.loads(Path(inputs["extracted_triples_details"]).read_text(encoding="utf-8"))
    evaluated.extraction_made = details.get("made") or {}
    manifest = Path(inputs["extracted_triples"]).parent / MANIFEST_NAME
    evaluated.extraction_manifest = json.loads(manifest.read_text(encoding="utf-8")) if manifest.is_file() else {}
    extracted_ids = {r["id"] for r in details["records"] if r["status"] == "extracted"}
    evaluated.schema_used = json.loads(Path(inputs["schema_used"]).read_text(encoding="utf-8"))
    removed = {}
    for row in read_csv(Path(inputs["extracted_triples_removed"])):
        removed.setdefault(row["id"], collections.Counter())[row["reason"]] += 1
    extracted = {}
    for position, row in enumerate(read_csv(Path(inputs["extracted_triples"]))):
        extracted.setdefault(row["id"], []).append({**row, "_position": position})
    catalog = load_records(inputs["records"])
    evaluated.catalog_records = len(catalog)
    titles = {rid: (r.get("title") or "") for rid, r in catalog.items()}

    finished = {rid for rid, r in gt.records.items() if r["finished"]}
    evaluated.unfinished = len(gt.records) - len(finished)
    not_extracted = sorted(finished - extracted_ids)
    # Why each was not extracted: 060's model calls failed for it (its details file, key left_out, or for an older
    # 060 its records' status), or 060's last run didn't choose it.
    failed_by_060 = {e["id"]: e for e in (details.get("left_out") or {}).get("records", [])}
    for r in details["records"]:
        if r.get("status") == "failed" and r["id"] not in failed_by_060:
            why = r.get("error") or ""
            failed_by_060[r["id"]] = {"id": r["id"], "maintainer": (catalog.get(r["id"]) or {}).get("maintainer")
                                      or dropped.UNDEFINED, "why": why,
                                      "reason": dropped.kind_from_text(why)}
    evaluated.finished = [{"id": rid, "maintainer": (catalog.get(rid) or {}).get("maintainer") or dropped.UNDEFINED}
                          for rid in sorted(finished)]
    evaluated.extraction_failed = [failed_by_060[rid] for rid in not_extracted if rid in failed_by_060]
    not_chosen = [rid for rid in not_extracted if rid not in failed_by_060]
    taken = finished & extracted_ids
    parts = pool_parts(pool_rows)                  # each part is a fair sample on its own: its own run from its own first record
    fair = {rid for order in parts.values() for rid in fair_prefix(order, taken)}
    outside = sorted(taken - fair)
    evaluated.left_out = {k: v for k, v in {
        "finished, but 060's model calls failed for them in its last run": [e["id"] for e in evaluated.extraction_failed],
        "finished, but not extracted by 060's last run": not_chosen,       # 060 didn't choose them
        "outside the fair sample (after an unfinished or unextracted record of their own part of the pool, or not in the pool)": outside,
    }.items() if v}
    positions = {r["id"]: r["position"] for r in pool_rows}
    part_of = {r["id"]: r["part"] for r in pool_rows}

    def gaps_of(only=None) -> str:      # the first gap of each part (of those with a record in `only`, if given), as sentences
        found = [_first_gap(order, name, positions, taken, finished, gt.records) for name, order in parts.items()
                 if only is None or any(part_of.get(rid) == name for rid in only)]
        return "; ".join(g for g in found if g)

    gap = gaps_of()
    if evaluated.extraction_failed:
        failed = evaluated.extraction_failed
        evaluated.notes.append(f"{len(failed)} finished ground truth record(s) are left out because 060's model calls "
                            f"failed for them in its last run, so every number of this run is computed without them: "
                            + named([f"{e['id']} ({dropped.KINDS[e['reason']].split(':')[0]}; maintainer "
                                     f"{e['maintainer']})" for e in failed], 5, "; ")
                            + ". The report's section *Records left out* counts them by reason and by maintainer, and "
                              "says for each reason whether running `py 060_extract/run.py` again can bring them in "
                              "(then run `py 070_evaluate/run.py` again).")
    if not_chosen:
        evaluated.notes.append(f"{len(not_chosen)} finished ground truth record(s) weren't extracted by 060's "
                            f"last run, so this run leaves them out: {named(not_chosen)}. To evaluate them, run "
                            f"`py 060_extract/run.py`, then run `py 070_evaluate/run.py` again.")
    if outside:
        not_in_pool = [rid for rid in outside if rid not in positions]
        evaluated.notes.append(f"{len(outside)} record(s) are left out because they aren't in the fair sample (the "
                            f"first records of their own part of the pool, with none skipped), so this run doesn't evaluate them: "
                            f"{named(outside)}."
                            + (f" {gaps_of(outside)}, then run `py 070_evaluate/run.py` again." if len(not_in_pool) < len(outside) else "")
                            + (f" {len(not_in_pool)} of them aren't in the pool at all (hand-picked): {named(not_in_pool)}. "
                               f"Nothing to do for those: only pool records can form a fair sample." if not_in_pool else ""))

    rows_of = {}
    for r in gt.rows:
        rows_of.setdefault(r["id"], []).append(r)
    for rid in evaluated.pool:
        if rid not in fair:
            continue
        gt_triples, gt_describes = _triples(rows_of.get(rid, []))
        ex_triples, ex_describes = _triples(extracted.get(rid, []))
        evaluated.records.append({
            "id": rid, "position": by_id[rid]["position"], "part": by_id[rid]["part"],
            "stratum": strata.get(rid, ""), "title": titles.get(rid, ""),
            "gt": gt_triples, "gt_describes": gt_describes, "extracted": ex_triples, "extracted_describes": ex_describes,
            "removed": dict(removed.get(rid, {})),
        })
    _mark_twins(evaluated, catalog, inputs)
    missing_stratum = [r["id"] for r in evaluated.records if not r["stratum"]]
    if missing_stratum:
        candidates = repo_path(inputs["candidates"])
        evaluated.notes.append(f"{len(missing_stratum)} evaluated record(s) have no stratum in the pool file "
                            f"({candidates}, column stratum), so the per-stratum numbers show them as the stratum "
                            f"\"(no stratum)\"; the other numbers count them as usual: {named(missing_stratum)}. That "
                            f"file was written with a stratum for every pool record, so it was probably edited: "
                            f"compare it with Git's copy (`git diff {candidates}`).")
    if not evaluated.records:
        raise Stop("Nothing to evaluate yet: no finished ground truth record that 060 extracted is in the "
                   "fair sample, so 070 can't evaluate. "
                   + (f"{gap}, then run `py 070_evaluate/run.py` again. " if gap else "")
                   + " ".join(evaluated.notes))
    if evaluated.notes:                            # before anything is evaluated, even on a run that pays nothing
        show_warnings("070", evaluated.notes)
        if settings["confirm_paid_calls"]:
            confirm("Press Enter to evaluate anyway, or anything else to cancel.")
    evaluated.reviews = read_reviews(Path(inputs["partial_reviews"]))
    evaluated.review_problems = review_problems(Path(inputs["partial_reviews"]))
    return evaluated
