"""
records.py -- stage 1: which records are evaluated, and what is known about
each.

A record is evaluated when a person has finished it in the ground truth (all
triples extracted, on every row) AND step 060's last run extracted from it.
Of those, only the FAIR SAMPLE is evaluated: the longest run of the pool's first
records that are all evaluated. The pool is shuffled, so that run is a fair
sample of the catalog, which the margins of error require (see stats.py). A
record after a gap (an unfinished or unextracted record before it) or not in
the pool at all (hand-picked) is left out and listed, with what to do.

For each evaluated record: its pool position, its part (tuning or held-out,
from 030), its sampling group (from the pool file), its title, its ground
truth triples and DESCRIBES row, and 060's extracted triples and DESCRIBES row.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from common.files import read_csv
from common.ground_truth import fair_prefix, read_ground_truth, read_pool
from common.partial_reviews import read_reviews
from common.records_io import load_records
from common.report import named
from common.step import check_settings, input_files
from common.triples_io import is_describes


@dataclass
class Evaluated:
    records: list = field(default_factory=list)    # see pick_records
    left_out: dict = field(default_factory=dict)   # {reason: [ids]}
    notes: list = field(default_factory=list)      # shown before paying (mapping calls) and in the report
    pool: list = field(default_factory=list)       # the pool's ids, in order
    pool_groups: dict = field(default_factory=dict)  # {group: pool records in it}
    ground_truth: object = None                    # common.ground_truth.GroundTruth
    schema_used: dict = field(default_factory=dict)  # 060's schema_used.json
    unfinished: int = 0                            # ground truth records not finished yet
    reviews: dict = field(default_factory=dict)    # a person's verdicts on partial pairs (common/common_helpers/partial_reviews.py)
    extraction_made: dict = field(default_factory=dict)  # 060's run: run id, model, settings (from its details file)


def _triples(rows: list) -> tuple:
    """(triples, DESCRIBES row or None): rows with subject, predicate and object."""
    triples, describes = [], None
    for r in rows:
        if not (r.get("subject") and r.get("predicate") and r.get("object")):
            continue                                   # "annotated, states no triples"
        if is_describes(r):
            describes = describes or r
        else:
            triples.append(r)
    return triples, describes


def pick_records(inputs: dict, settings: dict) -> Evaluated:
    check_settings(settings, {})
    evaluated = Evaluated()
    gt_files = input_files(Path(inputs["ground_truth"]))
    gt = evaluated.ground_truth = read_ground_truth(gt_files[0].parent)        # run_step made sure there is one
    evaluated.notes += [f"Ground truth: {p}" for p in gt.problems]
    pool_rows = read_pool(inputs["splits"])
    if any("part" not in r for r in pool_rows):
        raise ValueError("splits.json has no tuning / held-out part for its records: rebuild it with 030 "
                         "(delete 030's splits.json, then run py 030_split/run.py)")
    evaluated.pool = [r["id"] for r in pool_rows]
    by_id = {r["id"]: r for r in pool_rows}
    groups = {r["id"].strip(): (r.get("group") or "").strip() for r in read_csv(Path(inputs["candidates"]))}
    for r in pool_rows:
        g = groups.get(r["id"], "")
        evaluated.pool_groups[g] = evaluated.pool_groups.get(g, 0) + 1
    details = json.loads(Path(inputs["extracted_triples_details"]).read_text(encoding="utf-8"))
    evaluated.extraction_made = details.get("made") or {}
    extracted_ids = {r["id"] for r in details["records"] if r["status"] == "extracted"}
    evaluated.schema_used = json.loads(Path(inputs["schema_used"]).read_text(encoding="utf-8"))
    extracted = {}
    for position, row in enumerate(read_csv(Path(inputs["extracted_triples"]))):
        extracted.setdefault(row["id"], []).append({**row, "_position": position})
    titles = {rid: (r.get("title") or "") for rid, r in load_records(inputs["records"]).items()}

    finished = {rid for rid, r in gt.records.items() if r["finished"]}
    evaluated.unfinished = len(gt.records) - len(finished)
    not_extracted = sorted(finished - extracted_ids)
    taken = finished & extracted_ids
    fair = set(fair_prefix(evaluated.pool, taken))
    outside = sorted(taken - fair)
    evaluated.left_out = {k: v for k, v in {
        "finished, but not extracted by 060's last run": not_extracted,
        "outside the fair sample (after an unfinished or unextracted pool record, or not in the pool)": outside,
    }.items() if v}
    if not_extracted:
        evaluated.notes.append(f"{len(not_extracted)} finished ground truth record(s) weren't extracted by 060's "
                            f"last run, so can't be evaluated: {named(not_extracted)}. Run py 060_extract/run.py.")
    if outside:
        evaluated.notes.append(f"{len(outside)} record(s) are left out because they aren't in the fair sample (the "
                            f"pool's first records, with none skipped): {named(outside)}. Finish (or extract) "
                            f"the pool records before them to bring them in.")

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
            "group": groups.get(rid, ""), "title": titles.get(rid, ""),
            "gt": gt_triples, "gt_describes": gt_describes, "extracted": ex_triples, "extracted_describes": ex_describes,
        })
    missing_group = [r["id"] for r in evaluated.records if not r["group"]]
    if missing_group:
        evaluated.notes.append(f"{len(missing_group)} evaluated record(s) have no sampling group in the pool file, so "
                            f"the per-group numbers show them as the group \"(no group)\": {named(missing_group)}.")
    if not evaluated.records:
        raise SystemExit("Nothing to evaluate yet: no finished ground truth record that 060 extracted is in the "
                         "fair sample. " + " ".join(evaluated.notes))
    evaluated.reviews = read_reviews(Path(inputs["partial_reviews"]))
    return evaluated
