"""
records.py -- stage 1: which records this drafted batch holds, and anything about
that choice the person should know BEFORE paying.

By default, the next records of the ground truth candidates pool, in the
pool's order (splits.json, from 030), from pool position `start_position`
on, `records_per_batch` of them, of the part(s) the setting `part` names
(tuning by default: held-out records are drafted only when asked for). Given `ids`, those records instead, in the
order listed (still at most `records_per_batch`).

Always skipped, whatever was asked:
  - a record already in the ground truth (annotations/ground_truth/): it's done;
  - a record in a drafted batch in this step's output folder: it's waiting to
    be corrected (a record deleted from a corrected drafted batch stays skipped too,
    as the person decided it);
  - an id that isn't a record of the catalog, or a record with no text.

For the default choice the first two are expected and just counted. Anything
that makes the drafted batch differ from what was asked (an id listed that is
skipped, fewer records than asked, …) becomes a NOTE: shown before the
paid-call question (common/common_helpers/llm_paid.py PaidCalls) and in the report.

Fair sample: the pool is shuffled, so its first N records are a fair sample
of the catalog, and so are the first N of each part (tuning, held-out) taken
alone; step 070 can only claim results from such a sample. `fair` says, for
each part, whether the ground truth, the drafted batches waiting and this
drafted batch together are still exactly the first N records of that part
in pool order.

The model is shown the ground truth schema's entity classes and predicates with their
definitions, each entity class with its rule 19 mark (common/common_helpers/schema_io.schema_text
with rule_19_marks: no pattern and no pin; 060 shows a schema the same way but without the
marks), plus the component classes coined in the FINISHED TUNING records of the ground truth
that the file lacks (common/common_helpers/ground_truth.ground_truth_schema_view): what a person has checked, so a coined one is reused from the next drafted batch on, while
a model's uncorrected draft (an unfinished record) or a held-out record never
reaches the prompt or the checks. The checks compare entity classes and predicates
with the ground truth schema alone, so a coined component class (or a typo) stays an
error until it is added there; patterns with the file's plus those the finished
tuning records use. A record in the ground truth in any state (finished or not,
in two files, a bad mark: ANNOTATED) is never drafted again.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from common import dropped
from common.files import read_csv
from common.chunking import full_text, pieces
from common.ground_truth import (ANNOTATED, DRAFT_NUMBERED, DRAFT_PATTERN, HELD_OUT, NUMBERED, PARTS, TUNING, fair_sample,
                                 fair_words, ground_truth_schema_view, pool_parts, read_ground_truth, read_pool,
                                 record_skipped)
from common.records_io import NOT_IN_CATALOG, WITHOUT_TEXT, WITHOUT_TEXT_TO_DO, has_text, load_records, read_ids
from common.report import named
from common.schema_io import (read_ground_truth_schema, record_left_out_of_view, record_unread, schema_text,
                              without_held_out_only)
from common.step import Spec, check_settings, input_files, repo_path
from common.stop import Stop
from common.validate import SchemaEntries

#: The stage name its discarded items carry (common/common_helpers/dropped.py).
STAGE = "stage 1 (pick_records)"


#: 050's own reasons for skipping a record (the shared ones: common/common_helpers/records_io.py).
ALREADY_ANNOTATED, WAITING = "already in the ground truth", "waiting in a drafted batch to be corrected"

@dataclass
class Chosen:
    items: list = field(default_factory=list)      # {"id", "position", "title", "maintainer", "text", "pieces"}
    batch: int = 1                                 # this drafted batch's number
    notes: list = field(default_factory=list)      # shown before paying: where the drafted batch differs from what was asked
    records: dict = field(default_factory=dict)    # every record, {id: record}
    ground_truth: object = None                    # common.ground_truth.GroundTruth
    done: set = field(default_factory=set)         # ids in the ground truth
    waiting: dict = field(default_factory=dict)    # {id: drafted batch number} not yet corrected
    pool: list = field(default_factory=list)       # the pool's ids, in order
    positions: dict = field(default_factory=dict)  # {id: pool position}
    schema_text: str = ""                          # the ground truth schema, as the prompt shows it
    # Whether the prompt shows each entity class's rule 19 mark ("rule 19: standalone" / "rule 19: describing"), in
    # the ground truth schema (read_inputs) and in the worked examples' example schema (draft.prompt_for; both through
    # common/common_helpers/schema_io.schema_text). True (decided 2026-11-15, docs/improvements.md): drafting writes the
    # ground truth, so it follows the person's decisions, and nothing it produces is scored against the ground truth.
    # The second opinion and the second judge show the schema as 050 does (read_inputs). 060 never shows the marks.
    rule_19_marks: bool = True
    schema_entries: object = None  # the ground truth schema's entries, as the checks compare them (common.validate.SchemaEntries)
    coined: dict = field(default_factory=dict)     # {kind: [component classes]} the finished tuning records use, not in the ground truth schema
    fair: dict = field(default_factory=dict)       # {part: common/common_helpers/ground_truth.fair_sample()'s answer}
    parts: dict = field(default_factory=dict)      # {id: "tuning" or "held-out"}
    how: str = ""                                  # the choice in words, for the report
    skipped: dict = field(default_factory=dict)    # {reason: [ids]} passed over while choosing


def vocabulary_text(shown: str, coined: dict) -> str:
    """The ground truth schema as the model sees it: shown (common.schema_io.schema_text of the file without its
    held-out-only entries: entity classes and predicates with their definitions, and each entity class's rule 19
    mark),
    then the component classes coined in the finished tuning records of the ground truth
    (common.ground_truth.ground_truth_schema_view's coined), which have no definition yet. With none coined, just
    shown. No pattern and no pin is shown (decided 2026-11-15, docs/improvements.md); the checks still use them."""
    lines = [f"{label}: {', '.join(coined[kind])}"
             for kind, label in (("entity_classes", "Entity classes"), ("predicates", "Predicates")) if coined[kind]]
    return shown + ("\n\nALSO USED IN THE GROUND TRUTH (no definition yet)\n" + "\n".join(lines) if lines else "")


def _waiting(output: Path) -> tuple:
    """({id: batch number} of every drafted batch in the output folder, the
    highest drafted batch number)."""
    waiting, highest = {}, 0
    for path in sorted(Path(output).glob(DRAFT_PATTERN)):
        m = DRAFT_NUMBERED.fullmatch(path.name)
        if not m:
            continue
        n = int(m.group(1))
        highest = max(highest, n)
        for row in read_csv(path):                        # Stop, naming the file, if it isn't UTF-8 (Excel's cp1252)
            rid = (row.get("id") or "").strip()
            if rid:
                waiting.setdefault(rid, n)
    return waiting, highest


#: The step's settings' rules (common.step.Spec); run_step checks them before any input is read, and so does
#: pick_records, with the same table (the shared settings' rules: common.step.shared_specs).
SPECS = {"records_per_batch": Spec(int, 1, 1000), "start_position": Spec(int, 0, 10_000_000),
         "part": Spec(str, choices=(*PARTS, "both"))}


def read_inputs(inputs: dict) -> tuple:
    """(a Chosen with everything read from the inputs, the pool's rows): the records, the pool (ids, positions, parts),
    the ground truth (its problems as notes), and the ground truth schema as the model sees it (schema_text) and as
    the checks compare it (schema_entries), with the component classes coined. What every run that drafts the way
    050 does starts from: pick_records, and the second opinion (py helpers/second_opinion.py), which drafts finished
    records again with 050's prompt and checks."""
    chosen = Chosen()
    chosen.records = load_records(inputs["records"])
    pool_rows = read_pool(inputs["splits"])
    chosen.pool = [r["id"] for r in pool_rows]
    chosen.positions = {r["id"]: r["position"] for r in pool_rows}
    chosen.parts = {r["id"]: r["part"] for r in pool_rows}
    chosen.ground_truth = read_ground_truth(Path(inputs["ground_truth"]).parent, pool_rows)   # none yet: no record done
    hand = read_ground_truth_schema(inputs["ground_truth_schema"])
    vocab = ground_truth_schema_view(hand, chosen.ground_truth)
    # the checks: the file's entity classes and predicates, less the held-out-only ones (no model and no check sees
    # them: docs/terminology.md, *held-out-only entry*); its patterns and every one the finished tuning records use
    chosen.schema_entries = SchemaEntries({**without_held_out_only(hand), "patterns": vocab["patterns"]})
    record_unread(STAGE, hand, repo_path(inputs["ground_truth_schema"]))
    record_skipped(STAGE, chosen.ground_truth)
    record_left_out_of_view(STAGE, hand, {**without_held_out_only(hand), "patterns": vocab["patterns"]},
                            where=repo_path(inputs["ground_truth_schema"]))
    chosen.coined = vocab["coined"]
    chosen.schema_text = vocabulary_text(schema_text(without_held_out_only(hand), chosen.rule_19_marks), chosen.coined)
    chosen.notes += [f"Ground truth, {p}" for p in chosen.ground_truth.problems]
    return chosen, pool_rows


def items_for(chosen: Chosen, picked: list, max_chars: int) -> list:
    """The items the model is asked about, one per record picked: its id, pool position, title, maintainer, whole
    text, and text pieces (common/common_helpers/chunking.py)."""
    items = []
    for rid in picked:
        record = chosen.records[rid]
        items.append({"id": rid, "position": chosen.positions.get(rid), "title": record.get("title") or "",
                      "maintainer": record.get("maintainer"),
                      "text": full_text(record), "pieces": pieces(record, max_chars)})
    return items


def pick_records(inputs: dict, settings: dict, output: Path) -> Chosen:
    check_settings(settings, SPECS)
    part = settings["part"].strip().lower()
    chosen, pool_rows = read_inputs(inputs)
    gt_files = input_files(Path(inputs["ground_truth"]))
    chosen.done = set(chosen.ground_truth.select(ANNOTATED).ids)
    chosen.waiting, highest = _waiting(output)
    gt_numbers = [int(m.group(1)) for f in gt_files if (m := NUMBERED.fullmatch(f.name))]
    chosen.batch = max([highest, *gt_numbers]) + 1

    since = dropped.mark()
    per, ids = settings["records_per_batch"], read_ids(settings["ids"], STAGE)
    skipped = {NOT_IN_CATALOG: [], WITHOUT_TEXT: [], ALREADY_ANNOTATED: [], WAITING: []}
    picked = []
    considered = []                                   # every record usable() judged

    def usable(rid: str) -> bool:
        reason = (NOT_IN_CATALOG if rid not in chosen.records else
                  WITHOUT_TEXT if not has_text(chosen.records[rid]) else
                  ALREADY_ANNOTATED if rid in chosen.done else
                  WAITING if rid in chosen.waiting else None)
        considered.append(rid)
        if reason:
            skipped[reason].append(rid)
            r = chosen.records.get(rid) or {}
            dropped.discard(STAGE, "record", f"skipped while choosing: {reason}"
                            + (f" (drafted batch {chosen.waiting[rid]})" if reason == WAITING else ""),
                            {"id": rid, "title": r.get("title"), "pool_position": chosen.positions.get(rid)},
                            record_id=rid)
        return reason is None

    if ids:
        chosen.how = f"the {len(ids)} id(s) given in the setting ids"
        if part != TUNING:
            chosen.notes.append(f"part ({part}) is ignored, because the setting ids names the records: this run "
                                f"drafts the records listed in ids, whatever part they are in.")
        if settings["start_position"]:
            chosen.notes.append(f"start_position ({settings['start_position']}) is ignored, because the setting "
                                f"ids names the records: this run drafts the records listed in ids. To draft "
                                f"from a pool position instead, leave ids empty.")
        ok = [i for i in ids if usable(i)]
        picked = ok[:per]
        for rid in ok[per:]:
            dropped.discard(STAGE, "record", "listed in the setting ids, but beyond records_per_batch: waits for a "
                            "later run", {"id": rid, "title": chosen.records[rid].get("title"),
                                          "pool_position": chosen.positions.get(rid)},
                            record_id=rid, setting={"records_per_batch": per})
        if len(ok) > per:
            chosen.notes.append(f"You listed {len(ok)} records that can be drafted, but records_per_batch "
                                f"is {per}, so this run drafts the first {per}, and these {len(ok) - per} "
                                f"wait for a later run: {named(ok[per:])}. To draft all {len(ok)} now, "
                                f"set --records_per_batch {len(ok)}.")
    else:
        start = settings["start_position"]
        which = "" if part == "both" else f"{part} "
        chosen.how = f"the next {which}records of the pool from position {start}"
        for rid in chosen.pool:
            if len(picked) == per:
                break
            if chosen.positions[rid] >= start and part in ("both", chosen.parts[rid]) and usable(rid):
                picked.append(rid)
        if picked:
            other = HELD_OUT if part == TUNING else TUNING
            chosen.notes.append(
                f"This run drafts {len(picked)} {which}record(s), at pool positions "
                f"{', '.join(str(chosen.positions[r]) for r in picked)} (setting part: {part}"
                + (f"; the {other} records are not drafted" if part != "both" else "") + ").")
        if len(picked) < per:
            passed = "; ".join(f"{len(v)} {k}" for k, v in skipped.items() if v) or "none"
            chosen.notes.append(f"You asked for {per} records (records_per_batch), but only {len(picked)} "
                                f"are left in the {which}pool from position {start} on, so this drafted batch has "
                                f"{len(picked)}. The other {which}pool records from position {start} on: {passed}. "
                                + ("To draft the other part too, set --part both. " if part != "both" else "")
                                + (f"To draft records before position {start}, set a lower --start_position."
                                   if start else "Nothing to do: the pool has no other record to draft."))

    chosen.skipped = {reason: rids for reason, rids in skipped.items() if rids}
    dropped.account(STAGE, "records listed in the setting ids, or reached in the pool", len(considered), len(picked), since=since, item_type="record")
    to_do = {      # what to do about records skipped for each reason (the first two worded as in 060)
        NOT_IN_CATALOG: f"Check these ids in the setting ids for typos: each must be a record id in "
                              f"{repo_path(inputs['records'])}.",
        WITHOUT_TEXT: WITHOUT_TEXT_TO_DO,
        ALREADY_ANNOTATED: "Nothing to do: they are already annotated in annotations/ground_truth/.",
        WAITING: f"Correct them with `py helpers/annotate.py`; to draft one "
                                                    f"again instead, delete its drafted batch (both files) from "
                                                    f"{repo_path(output)}/ before correcting it."}
    for reason, rids in chosen.skipped.items():
        if ids:                                    # by default, passing over done records is expected
            where = ""
            if reason == WAITING:
                where = " (" + ", ".join(sorted({f"drafted batch {chosen.waiting[r]}" for r in rids})) + ")"
            chosen.notes.append(f"{len(rids)} record(s) you listed {'are' if len(rids) > 1 else 'is'} "
                                f"{reason}{where}, so skipped: {named(rids)}. {to_do[reason]}")

    chosen.items = items_for(chosen, picked, settings["max_chars"])

    taken_now, taken_after = chosen.done | set(chosen.waiting), chosen.done | set(chosen.waiting) | set(picked)
    for name, in_part in pool_parts(pool_rows).items():
        members = set(in_part)
        before = fair_sample(in_part, taken_now & members)
        chosen.fair[name] = fair_sample(in_part, taken_after & members)
        if before["fair"] and not chosen.fair[name]["fair"] and picked:
            chosen.notes.append(f"With this drafted batch, the ground truth is no longer the first records of the {name} part of the pool "
                                "(a fair sample of that part): " + fair_words(chosen.fair[name], chosen.positions, part=name) +
                                f" Step 070 evaluates only the fair sample of each part, so the {name} records after the "
                                "first one not taken won't be evaluated until the records before them are annotated. Nothing to "
                                "do if you chose these records on purpose; otherwise leave ids empty and set "
                                "--start_position 0, so the drafted batch takes the pool's next records.")
    if not chosen.items:
        raise Stop("Nothing to draft: none of the records chosen can be drafted, so 050 can't write a drafted batch. "
                   + " ".join(chosen.notes) + " Change the settings as these reasons say, then run "
                   "`py 050_annotate/run.py` again.")
    return chosen
