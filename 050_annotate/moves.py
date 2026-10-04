"""
moves.py -- the main moves of 050_annotate, as called by 050_annotate.py.

    stage 1  records.py  pick_records        code: which records this batch drafts; notes to show before paying
    -        (here)      paid_calls          code: asks before paying; keeps every answer in cache/
    stage 2  draft.py    ask_model           LLM: every fact each record states, as triple instances
    stage 3  (here)      build_rows          code: DESCRIBES row, duplicates out, every row checked
    stage 4  (here)      check_ground_truth  code: typos in the ground truth files
    -        (here)      results             writes the draft batch; the report

Every model answer is cached in cache/ inside the step's output folder
(common/cache.py), so a rerun pays only for what isn't there yet.
Terms are as defined in docs/terminology.md.
"""
from __future__ import annotations

import collections
from dataclasses import dataclass, field

import draft
import records as records_stage
from common import audit, extraction, llm
from common.audit import ORIGIN_COLUMN, check_origins, log
from common.files import write_csv, write_json
from common.ground_truth import (COLUMNS as GROUND_TRUTH_COLUMNS, ROW_ERRORS, check_rows, draft_name, fair_words,
                                 file_name)
from common.report import cell, counted, model_calls, named
from common.step import Results
from common.triples_io import ENTRY_PREDICATE

#: A draft batch's columns: the ground truth's, then the checks, then where each row came from.
COLUMNS = GROUND_TRUTH_COLUMNS + ["flags", ORIGIN_COLUMN]
SHOW = 20                        # rows listed in the report before "…"


@dataclass
class Drafts:
    rows: dict = field(default_factory=dict)      # {id: [checked rows]}, in the batch's order
    removed: dict = field(default_factory=dict)   # {id: [removed items]}
    errors: dict = field(default_factory=dict)    # {check: rows}
    flags: dict = field(default_factory=dict)     # {check: rows}


# --------------------------------------------------------------------------

def pick_records(inputs, settings, output):
    return records_stage.pick_records(inputs, settings, output)


def paid_calls(chosen, settings, output) -> llm.Calls:
    return llm.paid_calls(settings, output, notes=chosen.notes)


def ask_model(chosen, calls, settings):
    return draft.ask_model(chosen, calls, settings)


def build_rows(chosen, replies) -> Drafts:
    drafts = Drafts()
    errors, flags = collections.Counter(), collections.Counter()
    for item in chosen.items:
        if item["id"] not in replies.of:
            continue
        rows, removed = extraction.build_rows(item["id"], item["title"], item["text"],
                                              replies.of[item["id"]], chosen.names)
        drafts.rows[item["id"]], drafts.removed[item["id"]] = rows, removed
        for r in rows:
            errors.update(r["errors"])
            flags.update(r["flags"])
    drafts.errors, drafts.flags = dict(errors), dict(flags)
    n = sum(len(r) for r in drafts.rows.values())
    log.info(f"  {n:,} rows for {len(drafts.rows)} record(s); "
             f"{sum(len(r) for r in drafts.removed.values())} removed (malformed or duplicate)")
    return drafts


def check_ground_truth(chosen) -> list:
    typos = check_rows(chosen.ground_truth, chosen.records)
    log.info(f"  ground truth: {len(chosen.ground_truth.records)} records in "
             f"{len(chosen.ground_truth.files)} file(s); {len(typos)} row(s) to fix, "
             f"{len(chosen.ground_truth.problems)} other problem(s)")
    return typos


# --------------------------------------------------------------------------

def results(chosen, replies, drafts, typos, calls, settings, output) -> Results:
    n = chosen.batch
    batch_path = output / draft_name(n)
    details_path = batch_path.with_name(f"{batch_path.stem}_details.json")
    files, csv_rows = [], []
    for item in chosen.items:
        for r in drafts.rows.get(item["id"], []):
            csv_rows.append({**{c: r.get(c, "") for c in GROUND_TRUTH_COLUMNS}, "all_facts_extracted": "0",
                             "flags": " ".join(r["errors"] + r["flags"]),
                             ORIGIN_COLUMN: audit.origin("records", item["id"])})
    if csv_rows:
        write_csv(batch_path, COLUMNS, csv_rows, new=True)       # a draft batch is never overwritten
        write_json(details_path, {
            "made": {"run_id": audit.current_run_id(), "model": llm.MODEL, "settings": settings},
            "batch": n, "chosen": chosen.how,
            "records": [{"id": i["id"], "pool_position": i["position"], "title": i["title"],
                         "pieces": len(i["pieces"]),
                         "status": "drafted" if i["id"] in drafts.rows else "failed",
                         "error": replies.failed.get(i["id"]),
                         "rows": len(drafts.rows.get(i["id"], [])),
                         "removed": drafts.removed.get(i["id"], [])} for i in chosen.items],
            "skipped_while_choosing": chosen.skipped,
            "fair_sample": chosen.fair,
        }, new=True)
        files = [batch_path, details_path]
        log.info(f"  wrote {batch_path.name} and {details_path.name}")

    warnings = list(chosen.notes)                  # shown before paying too, if the run paid
    if replies.failed:
        warnings.append(f"{len(replies.failed)} record(s) failed and are not in the batch: "
                        f"{named(list(replies.failed), 3)}. "
                        f"Run the step again: only those are asked again; every answer already paid for is reused.")
    if not csv_rows:
        warnings.append("No record was drafted, so no batch was written.")
    coined = [n for kind in ("entity_classes", "predicates") for n in chosen.coined[kind]]
    if coined:
        warnings.append(f"{len(coined)} name(s) used in the ground truth aren't in the hand-built schema, so the model "
                        f"saw them without a definition: "
                        f"{named([f'{n} (ground truth vocabulary)' for n in coined], 5, '; ')}. "
                        f"Add each one you mean to keep, with a "
                        f"one-line definition, to the hand-built schema; fix any typo in the ground truth.")
    if typos:
        warnings.append(f"{len(typos)} row(s) of the ground truth have something to fix; listed in the "
                        f"report under Your ground truth.")
    missing = check_origins(csv_rows, "draft rows")
    if missing:
        warnings.append(missing)

    gt = chosen.ground_truth
    lines = ["### What this run worked on", ""]
    if csv_rows:
        lines += [f"Batch {n}: `{batch_path.name}`, {len(csv_rows):,} rows for {len(drafts.rows)} record(s), "
                  f"chosen as {chosen.how}. To correct it, run `py annotate.py` and pick batch {n}: it "
                  f"copies it to `annotations/ground_truth/{file_name(n)}` and saves your changes there.", ""]
    lines += ["| Pool position | Record | Rows | With an error | With a flag |", "|---:|---|---:|---:|---:|"]
    for item in chosen.items:
        rows = drafts.rows.get(item["id"])
        if rows is None:
            lines.append(f"| {item['position'] if item['position'] is not None else '–'} | "
                         f"{cell(item['title'])} | failed | | |")
        else:
            lines.append(f"| {item['position'] if item['position'] is not None else '–'} | "
                         f"{cell(item['title'])} | {len(rows)} | {sum(bool(r['errors']) for r in rows)} | "
                         f"{sum(bool(r['flags']) for r in rows)} |")
    removed = collections.Counter(x["reason"] for v in drafts.removed.values() for x in v)
    lines += ["", f"- Errors (must be fixed): {counted(drafts.errors)}.",
              f"- Flags (worth a look; a name not in the schema is often a good new one): {counted(drafts.flags)}.",
              f"- Removed: {counted(removed)} (listed in `{details_path.name}`).",
              "", "### Fair sample", "", fair_words(chosen.fair, chosen.positions), ""]
    if chosen.skipped:
        lines += ["Passed over while choosing: " + "; ".join(f"{len(v)} {k}" for k, v in chosen.skipped.items())
                  + ".", ""]
    lines += ["### Your ground truth", "",
              f"{len(gt.records)} records in {len(gt.files)} file(s), {sum(r['finished'] for r in gt.records.values())} "
              f"finished (all facts extracted). Rows with something to fix: {len(typos)}.", ""]
    if typos:
        lines += ["| Where | Record | To fix |", "|---|---|---|"]
        lines += [f"| {t['where']} | {t['id']} | {'; '.join(ROW_ERRORS[e] for e in t['errors'])} |"
                  for t in typos[:SHOW]]
        if len(typos) > SHOW:
            lines.append(f"| … {len(typos) - SHOW} more | | |")
        lines.append("")
    lines += model_calls([("draft triple instances (one per text piece)", replies.calls, replies.reused)],
                         calls.paid.test_calls, llm.MODEL)

    return Results(
        files=files,
        headline={"records drafted": len(drafts.rows),
                  "triple instances drafted": sum(1 for r in csv_rows if r["predicate"] != ENTRY_PREDICATE)},
        details="\n".join(lines),
        warnings=warnings,
    )
