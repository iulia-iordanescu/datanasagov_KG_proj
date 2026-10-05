"""
records.py -- stage 1: which records this run extracts from.

The setting `extract_from` says which:

    ground_truth   (default) the records of the ground truth a person has
                   finished (all facts extracted on every row), the only ones
                   070 can score; a record still in progress is skipped
    all            every record with text: once the schema is final

or `ids` names exactly the records, as in 050 (common/common_helpers/records_io.read_ids).
Anything that makes the run differ from what was asked (a listed id not in
the catalog or without text, a record not yet finished, …) becomes a NOTE,
shown before the paid-call question and in the report.
"""
from __future__ import annotations

import json

from dataclasses import dataclass, field
from pathlib import Path

from common.chunking import full_text, pieces
from common.ground_truth import read_ground_truth
from common.records_io import has_text, load_records, read_ids
from common.report import named
from common.step import check_settings, input_files

MODES = ("ground_truth", "all")


@dataclass
class Chosen:
    items: list = field(default_factory=list)      # {"id", "title", "text", "pieces"}
    records: dict = field(default_factory=dict)    # every record, {id: record}
    ground_truth: set = field(default_factory=set) # ids of every record in the ground truth
    how: str = ""                                  # the choice in words, for the report
    notes: list = field(default_factory=list)      # where the run differs from what was asked
    skipped: dict = field(default_factory=dict)    # {reason: [ids]}
    pool: dict = field(default_factory=dict)       # {id: (pool position, "tuning" | "held-out")} (030's splits.json)


def pick_records(inputs: dict, settings: dict) -> Chosen:
    check_settings(settings, {})
    if settings["extract_from"] not in MODES:
        raise ValueError(f"extract_from must be one of {', '.join(MODES)} (got {settings['extract_from']!r}); "
                         f"to name records, use ids")
    chosen = Chosen(records=load_records(inputs["records"]))
    splits = json.loads(Path(inputs["splits"]).read_text(encoding="utf-8"))
    chosen.pool = {r["id"]: (r["position"], r.get("part")) for r in splits["ground_truth_candidates"]["records"]}
    gt_files = input_files(Path(inputs["ground_truth"]))
    gt = read_ground_truth(gt_files[0].parent)                  # run_step made sure there is one
    chosen.ground_truth = {r["id"] for r in gt.rows}
    chosen.notes += [f"Ground truth: {p}" for p in gt.problems]
    ids = read_ids(settings["ids"])
    skipped = {"not in the catalog": [], "without text": [], "not finished in the ground truth": []}

    if ids:
        chosen.how = f"the {len(ids)} id(s) given in the setting ids"
        if settings["extract_from"] != "ground_truth":
            chosen.notes.append(f"extract_from ({settings['extract_from']}) is ignored, because ids names the records.")
        wanted = ids
    elif settings["extract_from"] == "ground_truth":
        finished = [rid for rid, r in gt.records.items() if r["finished"]]
        skipped["not finished in the ground truth"] = [rid for rid, r in gt.records.items() if not r["finished"]]
        chosen.how = f"the {len(finished)} finished record(s) of the ground truth"
        wanted = finished
    else:
        chosen.how = "every record with text"
        wanted = list(chosen.records)

    for rid in wanted:
        record = chosen.records.get(rid)
        if record is None:
            skipped["not in the catalog"].append(rid)
        elif not has_text(record):
            skipped["without text"].append(rid)
        else:
            chosen.items.append({"id": rid, "title": record.get("title") or "", "text": full_text(record),
                                 "pieces": pieces(record, settings["max_chars"])})
    chosen.skipped = {k: v for k, v in skipped.items() if v}

    for reason, rids in chosen.skipped.items():
        if reason == "without text" and not ids and settings["extract_from"] == "all":
            continue                                             # expected: most catalogs have a few
        if reason == "not finished in the ground truth":
            chosen.notes.append(f"{len(rids)} record(s) of the ground truth aren't finished yet (all facts "
                                f"extracted not ticked), so skipped: {named(rids)}.")
        else:
            who = "record(s) you listed" if ids else "ground truth record(s)"
            chosen.notes.append(f"{len(rids)} {who} {'are' if len(rids) > 1 else 'is'} {reason}, "
                                f"so skipped: {named(rids)}.")
    if not chosen.items:
        raise SystemExit("Nothing to extract. " + " ".join(chosen.notes))
    return chosen
