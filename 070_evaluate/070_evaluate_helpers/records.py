"""
records.py -- stage 1: which records are evaluated, and what is known about
each.

Evaluation refuses to run while the ground truth has the same classed triple
twice in a record (common/common_helpers/ground_truth.py, gt.repeats). Every
other warning found here (ground truth problems, records left out, …) is
shown before anything is evaluated, and the person is asked whether to go
ahead (unless confirm_paid_calls is false).

A record is evaluated when a person has finished it in the ground truth (all
triples extracted, on every row) AND step 060's last run extracted from it.
Of those, only the FAIR SAMPLE is evaluated: the longest run of the pool's first
records that are all evaluated. The pool is shuffled, so that run is a fair
sample of the catalog, which the margins of error require (see stats.py). A
record after a gap (an unfinished or unextracted record before it) or not in
the pool at all (hand-picked) is left out and listed, with what to do.

For each evaluated record: its pool position, its part (tuning or held-out,
from 030), its stratum (from the pool file), its title, its ground
truth triples and describes triple, 060's extracted triples and describes triple,
and its twin kind (docs/terminology.md, twin): what it shares with a record
the current schema was learned from (060's schema_used.json, learned_from),
"" when it isn't a twin, None when that isn't known.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from common.files import read_csv
from common.ground_truth import fair_prefix, read_ground_truth, read_pool, twin_kinds
from common.llm import confirm, numbered, show_warnings
from common.partial_reviews import read_reviews
from common.records_io import load_records
from common.report import named
from common.step import MANIFEST_NAME, check_settings, input_files, repo_path
from common.stop import Stop
from common.triples_io import is_describes


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
    extraction_made: dict = field(default_factory=dict)  # 060's run: run id, model, settings (from its details file)
    catalog_records: int = 0                       # records in 020's records.jsonl: the whole catalog
    learned_from: dict = field(default_factory=dict)  # the records the current schema was learned from (060's schema_used.json)
    extraction_manifest: dict = field(default_factory=dict)  # 060's _manifest.json: its run's code version, settings, prompts, inputs


def _triples(rows: list) -> tuple:
    """(triples, describes triple or None): rows with subject, predicate and object."""
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



def _mark_twins(evaluated: Evaluated, catalog: dict, inputs: dict) -> None:
    """Each evaluated record's "twin": its twin kind against the records the current schema was learned from
    (common.ground_truth.twin_kinds), "" when it isn't a twin, None when that isn't known (a note says why, and
    what to do)."""
    learned = evaluated.schema_used.get("learned_from") or {}
    evaluated.learned_from = learned
    if not learned.get("known"):
        why = (learned.get("how") or [f"{repo_path(inputs['schema_used'])} doesn't say (an older step 060 wrote it)"])[0]
        evaluated.notes.append(f"Which records the current schema was learned from isn't known: {why}. So 070 can't "
                               f"tell which evaluated records are twins (the same title, description, or both as a record "
                               f"the schema was learned from; docs/terminology.md, section *Evaluating extraction*), and gives no "
                               f"numbers without them. To get them, extract with 040's schema or the ground truth schema "
                               f"(`py 060_extract/run.py`), then run `py 070_evaluate/run.py` again.")
        for r in evaluated.records:
            r["twin"] = None
        return
    kind = twin_kinds({r["id"]: catalog.get(r["id"], {}) for r in evaluated.records},
                       [catalog[i] for i in learned["ids"] if i in catalog])
    for r in evaluated.records:
        r["twin"] = kind[r["id"]]


def _first_gap(pool: list, positions: dict, taken: set, finished: set, in_ground_truth) -> str:
    """The first pool record not taken, why, and what brings it in (for messages); "" if none."""
    gap = next((rid for rid in pool if rid not in taken), None)
    if gap is None:
        return ""
    where = f"pool position #{positions[gap]} (`{gap}`)"
    if gap in finished:
        return f"The first pool record missing from the fair sample is {where}: finished, but not extracted by 060's last run. Run `py 060_extract/run.py`"
    if gap in in_ground_truth:
        return f"The first pool record missing from the fair sample is {where}: not finished in the ground truth. Finish it in `py helpers/annotate.py` (tick *All facts extracted*), run `py 060_extract/run.py`"
    return (f"The first pool record missing from the fair sample is {where}: not in the ground truth yet. Draft it with "
            f"`py 050_annotate/run.py`, correct and finish it in `py helpers/annotate.py`, run `py 060_extract/run.py`")


def pick_records(inputs: dict, settings: dict) -> Evaluated:
    check_settings(settings, {})
    evaluated = Evaluated()
    gt_files = input_files(Path(inputs["ground_truth"]))
    gt = evaluated.ground_truth = read_ground_truth(gt_files[0].parent)        # run_step made sure there is one
    evaluated.notes += [f"Ground truth, {p}" for p in gt.problems]
    if gt.repeats:
        raise Stop(refusal(gt.repeats))
    pool_rows = read_pool(inputs["splits"])
    if any("part" not in r for r in pool_rows):
        splits = repo_path(inputs["splits"])
        raise Stop(f"{splits} has no tuning / held-out part for its records (an older step 030 wrote it), so 070 "
                   f"can't keep the held-out part apart. Delete {splits}, run `py 030_split/run.py`, then run "
                   f"`py 070_evaluate/run.py` again.")
    evaluated.pool = [r["id"] for r in pool_rows]
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
    extracted = {}
    for position, row in enumerate(read_csv(Path(inputs["extracted_triples"]))):
        extracted.setdefault(row["id"], []).append({**row, "_position": position})
    catalog = load_records(inputs["records"])
    evaluated.catalog_records = len(catalog)
    titles = {rid: (r.get("title") or "") for rid, r in catalog.items()}

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
    positions = {r["id"]: r["position"] for r in pool_rows}
    gap = _first_gap(evaluated.pool, positions, taken, finished, gt.records)
    if not_extracted:
        evaluated.notes.append(f"{len(not_extracted)} finished ground truth record(s) weren't extracted by 060's "
                            f"last run, so this run leaves them out: {named(not_extracted)}. To evaluate them, run "
                            f"`py 060_extract/run.py`, then run `py 070_evaluate/run.py` again.")
    if outside:
        not_in_pool = [rid for rid in outside if rid not in positions]
        evaluated.notes.append(f"{len(outside)} record(s) are left out because they aren't in the fair sample (the "
                            f"pool's first records, with none skipped), so this run doesn't evaluate them: "
                            f"{named(outside)}."
                            + (f" {gap}, then run `py 070_evaluate/run.py` again." if len(not_in_pool) < len(outside) else "")
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
    return evaluated
