"""
records.py -- stage 1: which records this batch drafts, and anything about
that choice the person should know BEFORE paying.

By default, the next records of the ground truth candidates pool, in the
pool's order (splits.json, from 030), from pool position `start_position`
on, `records_per_batch` of them. Given `ids`, those records instead, in the
order listed (still at most `records_per_batch`).

Always skipped, whatever was asked:
  - a record already in the ground truth (annotations/ground_truth/): it's done;
  - a record in a draft batch in this step's output folder: it's waiting to
    be corrected (a record deleted from a corrected batch stays skipped too,
    as the person decided it);
  - an id that isn't a record of the catalog, or a record with no text.

For the default choice the first two are expected and just counted. Anything
that makes the batch differ from what was asked (an id listed that is
skipped, fewer records than asked, …) becomes a NOTE: shown before the
paid-call question (common/llm.py PaidCalls) and in the report.

Fair sample: the pool is shuffled, so its first N records are a fair sample
of the catalog, and step 070 can only claim results for the whole catalog
from such a sample. `fair` says whether the ground truth, the waiting drafts
and this batch together are still exactly the first N of the pool.
"""
from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path

from common.chunking import full_text, pieces
from common.ground_truth import DRAFT_NUMBERED, DRAFT_PATTERN, NUMBERED, fair_sample, fair_words, read_ground_truth
from common.records_io import has_text, load_records, read_ids
from common.report import named
from common.schema_io import read_hand_schema
from common.step import check_settings, input_files
from common.validate import SchemaNames


@dataclass
class Chosen:
    items: list = field(default_factory=list)      # {"id", "position", "title", "text", "pieces"}
    batch: int = 1                                 # this batch's number
    notes: list = field(default_factory=list)      # shown before paying: where the batch differs from what was asked
    records: dict = field(default_factory=dict)    # every record, {id: record}
    ground_truth: object = None                    # common.ground_truth.GroundTruth
    done: set = field(default_factory=set)         # ids in the ground truth
    waiting: dict = field(default_factory=dict)    # {id: draft batch number} not yet corrected
    pool: list = field(default_factory=list)       # the pool's ids, in order
    positions: dict = field(default_factory=dict)  # {id: pool position}
    schema_text: str = ""                          # the hand-built schema, as the prompt shows it
    names: object = None                           # its names, as the checks compare them
    fair: dict = field(default_factory=dict)       # see common/ground_truth.fair_sample()
    how: str = ""                                  # the choice in words, for the report
    skipped: dict = field(default_factory=dict)    # {reason: [ids]} passed over while choosing


def _waiting(output: Path) -> tuple:
    """({id: batch number} of every draft batch in the output folder, the
    highest draft batch number)."""
    waiting, highest = {}, 0
    for path in sorted(Path(output).glob(DRAFT_PATTERN)):
        m = DRAFT_NUMBERED.fullmatch(path.name)
        if not m:
            continue
        n = int(m.group(1))
        highest = max(highest, n)
        with open(path, encoding="utf-8-sig", newline="") as fh:
            for row in csv.DictReader(fh):
                rid = (row.get("id") or "").strip()
                if rid:
                    waiting.setdefault(rid, n)
    return waiting, highest


def pick_records(inputs: dict, settings: dict, output: Path) -> Chosen:
    check_settings(settings, {"records_per_batch": 1, "start_position": 0})
    chosen = Chosen()
    chosen.records = load_records(inputs["records"])
    splits = json.loads(Path(inputs["splits"]).read_text(encoding="utf-8"))
    pool_rows = splits["ground_truth_candidates"]["records"]
    chosen.pool = [r["id"] for r in pool_rows]
    chosen.positions = {r["id"]: r["position"] for r in pool_rows}
    chosen.schema_text = Path(inputs["hand_schema"]).read_text(encoding="utf-8-sig").strip()
    chosen.names = SchemaNames(read_hand_schema(inputs["hand_schema"]))

    gt_files = input_files(Path(inputs["ground_truth"]))
    chosen.ground_truth = read_ground_truth(gt_files[0].parent)     # run_step made sure there is one
    chosen.notes += [f"Ground truth: {p}" for p in chosen.ground_truth.problems]
    chosen.done = {r["id"] for r in chosen.ground_truth.rows}
    chosen.waiting, highest = _waiting(output)
    gt_numbers = [int(m.group(1)) for f in gt_files if (m := NUMBERED.fullmatch(f.name))]
    chosen.batch = max([highest, *gt_numbers]) + 1

    per, ids = settings["records_per_batch"], read_ids(settings["ids"])
    skipped = {"not in the catalog": [], "without text": [], "already in the ground truth": [],
               "waiting in a draft batch to be corrected": []}
    picked = []

    def usable(rid: str) -> bool:
        reason = ("not in the catalog" if rid not in chosen.records else
                  "without text" if not has_text(chosen.records[rid]) else
                  "already in the ground truth" if rid in chosen.done else
                  "waiting in a draft batch to be corrected" if rid in chosen.waiting else None)
        if reason:
            skipped[reason].append(rid)
        return reason is None

    if ids:
        chosen.how = f"the {len(ids)} id(s) given in the setting ids"
        if settings["start_position"]:
            chosen.notes.append(f"start_position ({settings['start_position']}) is ignored, because ids "
                                f"names the records.")
        ok = [i for i in ids if usable(i)]
        picked = ok[:per]
        if len(ok) > per:
            chosen.notes.append(f"You listed {len(ok)} records that can be drafted, but records_per_batch "
                                f"is {per}: the first {per} are drafted now, and these {len(ok) - per} "
                                f"wait for a later run: {named(ok[per:])}.")
    else:
        start = settings["start_position"]
        chosen.how = f"the next records of the pool from position {start}"
        for rid in chosen.pool:
            if len(picked) == per:
                break
            if chosen.positions[rid] >= start and usable(rid):
                picked.append(rid)
        if len(picked) < per:
            chosen.notes.append(f"You asked for {per} records (records_per_batch), but only {len(picked)} "
                                f"are left in the pool from position {start} on.")

    chosen.skipped = {reason: rids for reason, rids in skipped.items() if rids}
    for reason, rids in chosen.skipped.items():
        if ids:                                    # by default, passing over done records is expected
            where = ""
            if reason == "waiting in a draft batch to be corrected":
                where = " (" + ", ".join(sorted({f"batch {chosen.waiting[r]}" for r in rids})) + ")"
            chosen.notes.append(f"{len(rids)} record(s) you listed {'are' if len(rids) > 1 else 'is'} "
                                f"{reason}{where}, so skipped: {named(rids)}.")

    for rid in picked:
        record = chosen.records[rid]
        chosen.items.append({"id": rid, "position": chosen.positions.get(rid), "title": record.get("title") or "",
                             "text": full_text(record), "pieces": pieces(record, settings["max_chars"])})

    before = fair_sample(chosen.pool, chosen.done | set(chosen.waiting))
    chosen.fair = fair_sample(chosen.pool, chosen.done | set(chosen.waiting) | set(picked))
    if before["fair"] and not chosen.fair["fair"] and picked:
        chosen.notes.append("With this batch, the ground truth is no longer the first records of the pool "
                            "(a fair sample of the catalog): " + fair_words(chosen.fair, chosen.positions) +
                            " Fine for a closer look at chosen records, but step 070 scores only the fair "
                            "part, so they won't be scored until the records before them are annotated.")
    if not chosen.items:
        raise SystemExit("Nothing to draft. " + " ".join(chosen.notes))
    return chosen
