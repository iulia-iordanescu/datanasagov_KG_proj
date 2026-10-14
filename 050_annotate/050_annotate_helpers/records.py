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
paid-call question (common/common_helpers/llm.py PaidCalls) and in the report.

Fair sample: the pool is shuffled, so its first N records are a fair sample
of the catalog, and step 070 can only claim results for the whole catalog
from such a sample. `fair` says whether the ground truth, the waiting drafts
and this batch together are still exactly the first N of the pool.

The model is shown the ground truth schema plus the component classes a
person coined in the ground truth and hasn't added to it yet
(common/common_helpers/ground_truth.with_coined), so a coined one is reused
from the next batch on. The checks compare with the ground truth schema alone,
so a coined component class (or a typo) stays an error until it is added there.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path

from common.chunking import full_text, pieces
from common.ground_truth import (DRAFT_NUMBERED, DRAFT_PATTERN, NUMBERED, fair_sample, fair_words, read_ground_truth,
                                 read_pool, with_coined)
from common.records_io import has_text, load_records, read_ids
from common.report import named
from common.schema_io import read_ground_truth_schema
from common.step import check_settings, input_files, repo_path
from common.stop import Stop
from common.validate import SchemaEntries


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
    schema_text: str = ""                          # the ground truth schema, as the prompt shows it
    schema_entries: object = None  # the ground truth schema's entries, as the checks compare them (common.validate.SchemaEntries)
    coined: dict = field(default_factory=dict)     # {kind: [component classes]} used in the ground truth, not in the ground truth schema
    fair: dict = field(default_factory=dict)       # see common/common_helpers/ground_truth.fair_sample()
    how: str = ""                                  # the choice in words, for the report
    skipped: dict = field(default_factory=dict)    # {reason: [ids]} passed over while choosing


def vocabulary_text(hand_text: str, coined: dict) -> str:
    """The ground truth schema as the model sees it: the ground truth
    schema's text as written, then the component classes coined in the ground truth,
    which have no definition yet. With nothing coined, just the schema's
    text, so earlier answers stay in the cache."""
    lines = [f"{label}: {', '.join(coined[kind])}"
             for kind, label in (("entity_classes", "Entity classes"), ("predicates", "Predicates")) if coined[kind]]
    if not lines:
        return hand_text
    return hand_text + "\n\nALSO USED IN THE GROUND TRUTH (no definition yet)\n" + "\n".join(lines)


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
    pool_rows = read_pool(inputs["splits"])
    chosen.pool = [r["id"] for r in pool_rows]
    chosen.positions = {r["id"]: r["position"] for r in pool_rows}
    gt_files = input_files(Path(inputs["ground_truth"]))
    chosen.ground_truth = read_ground_truth(Path(inputs["ground_truth"]).parent)   # none yet: no record done
    hand = read_ground_truth_schema(inputs["ground_truth_schema"])
    chosen.schema_entries = SchemaEntries(hand)
    chosen.coined = with_coined(hand, chosen.ground_truth)["coined"]
    chosen.schema_text = vocabulary_text(Path(inputs["ground_truth_schema"]).read_text(encoding="utf-8-sig").strip(),
                                         chosen.coined)
    chosen.notes += [f"Ground truth, {p}" for p in chosen.ground_truth.problems]
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
            chosen.notes.append(f"start_position ({settings['start_position']}) is ignored, because the setting "
                                f"ids names the records: this run drafts the records listed in ids. To draft "
                                f"from a pool position instead, leave ids empty.")
        ok = [i for i in ids if usable(i)]
        picked = ok[:per]
        if len(ok) > per:
            chosen.notes.append(f"You listed {len(ok)} records that can be drafted, but records_per_batch "
                                f"is {per}, so this run drafts the first {per}, and these {len(ok) - per} "
                                f"wait for a later run: {named(ok[per:])}. To draft all {len(ok)} now, "
                                f"set --records_per_batch {len(ok)}.")
    else:
        start = settings["start_position"]
        chosen.how = f"the next records of the pool from position {start}"
        for rid in chosen.pool:
            if len(picked) == per:
                break
            if chosen.positions[rid] >= start and usable(rid):
                picked.append(rid)
        if len(picked) < per:
            passed = "; ".join(f"{len(v)} {k}" for k, v in skipped.items() if v) or "none"
            chosen.notes.append(f"You asked for {per} records (records_per_batch), but only {len(picked)} "
                                f"are left in the pool from position {start} on, so this batch has "
                                f"{len(picked)}. The other pool records from position {start} on: {passed}. "
                                + (f"To draft records before position {start}, set a lower --start_position."
                                   if start else "Nothing to do: the pool has no other record to draft."))

    chosen.skipped = {reason: rids for reason, rids in skipped.items() if rids}
    to_do = {      # what to do about records skipped for each reason (the first two worded as in 060)
        "not in the catalog": f"Check these ids in the setting ids for typos: each must be a record id in "
                              f"{repo_path(inputs['records'])}.",
        "without text": "Nothing to do: a record without text has nothing for the model to read.",
        "already in the ground truth": "Nothing to do: they are already annotated in annotations/ground_truth/.",
        "waiting in a draft batch to be corrected": f"Correct them with `py helpers/annotate.py`; to draft one "
                                                    f"again instead, delete its draft batch (both files) from "
                                                    f"{repo_path(output)}/ before correcting it."}
    for reason, rids in chosen.skipped.items():
        if ids:                                    # by default, passing over done records is expected
            where = ""
            if reason == "waiting in a draft batch to be corrected":
                where = " (" + ", ".join(sorted({f"batch {chosen.waiting[r]}" for r in rids})) + ")"
            chosen.notes.append(f"{len(rids)} record(s) you listed {'are' if len(rids) > 1 else 'is'} "
                                f"{reason}{where}, so skipped: {named(rids)}. {to_do[reason]}")

    for rid in picked:
        record = chosen.records[rid]
        chosen.items.append({"id": rid, "position": chosen.positions.get(rid), "title": record.get("title") or "",
                             "text": full_text(record), "pieces": pieces(record, settings["max_chars"])})

    before = fair_sample(chosen.pool, chosen.done | set(chosen.waiting))
    chosen.fair = fair_sample(chosen.pool, chosen.done | set(chosen.waiting) | set(picked))
    if before["fair"] and not chosen.fair["fair"] and picked:
        chosen.notes.append("With this batch, the ground truth is no longer the first records of the pool "
                            "(a fair sample of the catalog): " + fair_words(chosen.fair, chosen.positions) +
                            " Step 070 evaluates only the fair sample, so the records after the first one not "
                            "taken won't be evaluated until the records before them are annotated. Nothing to "
                            "do if you chose these records on purpose; otherwise leave ids empty and set "
                            "--start_position 0, so the batch takes the pool's next records.")
    if not chosen.items:
        raise Stop("Nothing to draft: none of the records chosen can be drafted, so 050 can't write a batch. "
                   + " ".join(chosen.notes) + " Change the settings as these reasons say, then run "
                   "`py 050_annotate/run.py` again.")
    return chosen
