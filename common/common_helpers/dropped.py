"""Records left out of a run because a model call for one of their text pieces failed (040, 050, 060; 070 reads 060's),
and, below, the record of every item any stage of any pipeline step discards (discard, fold, replace, account: written
by run_step to discarded.jsonl, helpers/audit.md, *Items discarded*).

One implementation for every step, so every report counts them the same way and says the same thing:

    kind(error)                       why a call failed, as one of KINDS (refused, cut off, malformed, service error, other)
    left_out(replies, items)          one entry per record left out: {"id", "maintainer", "reason", "why"}
    details(entries)                  the same, counted by reason and by maintainer, for a step's details file
    section(entries, items, where, details_file)
                                      the report's section "Records left out", identical in every step
    reasks_lines(counts), reasks_headline(counts)
                                      the run's replies that came back malformed and were asked once more
                                      (llm.REASKS, counted by llm.call_llm_json), for the report and the manifest

A record left out is missing from everything the run computes. If those records cluster (e.g. the model's safety
filter refuses one maintainer's biology records), the run's numbers describe a sample without them, which is why each
report counts them by maintainer as well as by reason (prompt audit F17, docs/improvements.md).
"""
from __future__ import annotations

import collections

import requests

from common import llm
from common.report import cell

#: Why a record was left out, in the order reports list them.
KINDS = {
    "refused": "refused: the model or its service declined to answer (a filter's finish reason, or prose declining "
               "the task)",
    "cut_off": "cut off: the answer reached the answer length limit",
    "malformed": "malformed: the reply wasn't in the required shape, even when asked again",
    "service_error": "service error: the model's service returned an error",
    "other": "other error",
}
#: What to do about each kind, for the report.
TO_DO = {
    "refused": "Asking again gets the same answer. Read the record's text; if refusals cluster in one maintainer, "
               "say wherever this run's numbers are reported that they leave those records out.",
    "cut_off": "Asking again with the same limit gets the same cut: see the warning about the answer length limit.",
    "malformed": "Run the step again: only these records are asked again.",
    "service_error": "Run the step again: only these records are asked again. If it keeps failing, the warning "
                     "above gives the service's error.",
    "other": "Run the step again; if it keeps failing, the log gives the error.",
}
#: finish_reason values that mean a filter withheld the answer: llm.REFUSAL_REASONS, the one home (llm.classify_reply
#: judges every reply with it).
REFUSAL_REASONS = llm.REFUSAL_REASONS
UNDEFINED = "undefined"                  # a record without a maintainer (docs/terminology.md, *maintainer*)


def kind(error) -> str:
    """Why a model call failed, as a key of KINDS."""
    reasons = {str(getattr(error, a, "") or "").lower() for a in ("finish_reason", "native_finish_reason")}
    if isinstance(error, llm.Refused) or reasons & REFUSAL_REASONS:
        return "refused"                 # a filter's finish reason, or prose declining the task (llm.classify_reply)
    if isinstance(error, llm.CutOff):
        return "cut_off"
    if isinstance(error, llm.BadReply):
        return "malformed"
    if isinstance(error, (llm.ApiError, llm.BudgetExhausted, RuntimeError, ConnectionError, TimeoutError,
                          requests.RequestException)):
        return "service_error"          # RuntimeError: what call_llm raises for a server error or rate limit it gave up on
    return "other"


def kind_from_text(why: str) -> str:
    """The kind of a failure known only by its message (an older run's details file): refused when the message names a
    filter's finish_reason (llm_replies.py words it "finish_reason 'content_filter'") or says the model refused (llm.Refused's
    words), else other."""
    why = why or ""
    if "the model refused to answer" in why or any(f"finish_reason {r!r}" in why for r in REFUSAL_REASONS):
        return "refused"
    return "other"


def left_out(replies, items: list) -> list:
    """One entry per item ({"id", "maintainer"?, …}) whose model call failed, in the items' order. The reason is
    replies.kinds[id] (set by extraction.ask_model from the error, with kind()); without it, it is read from what
    ask_model kept: cut off if the answer was cut off, refused if the service named a filter, else other."""
    kinds = getattr(replies, "kinds", None) or {}
    entries = []
    for item in items:
        rid = item["id"]
        if rid in replies.failed:
            why = replies.failed[rid]
            reason = kinds.get(rid) or ("cut_off" if rid in replies.cut_off else kind_from_text(why))
            entries.append({"id": rid, "maintainer": item.get("maintainer") or UNDEFINED, "reason": reason, "why": why})
    return entries


def details(entries: list) -> dict:
    """For a step's details file: the records left out, counted by reason and by maintainer."""
    return {"by_reason": dict(collections.Counter(e["reason"] for e in entries)),
            "by_maintainer": dict(collections.Counter(e["maintainer"] for e in entries)),
            "records": entries}


def section(entries: list, items: list, where: str, details_file: str | None) -> list:
    """The report's section on the records left out, the same in every step. where: what they are missing from
    ("the drafted batch", "the output", …); details_file: the file whose key `left_out` lists them, or None when the
    run wrote none (their ids are then in the report's warnings)."""
    lines = ["### Records left out", ""]
    if not entries:
        return lines + [f"None: every record chosen ({len(items)}) was answered, so {where} covers all of them.", ""]
    lines += [f"{len(entries)} of the {len(items)} record(s) chosen were left out of {where}, because a model call for "
              f"one of their text pieces failed. Every number this run gives is computed without them. "
              + (f"Their ids, with the reason for each, are in `{details_file}` (key `left_out`)." if details_file else
                 "Their ids, with the reason for each, are in this report's warnings."), "",
              "| Reason | Records | To do |", "|---|---:|---|"]
    by_reason = collections.Counter(e["reason"] for e in entries)
    lines += [f"| {KINDS[k]} | {by_reason[k]} | {TO_DO[k]} |" for k in KINDS if by_reason[k]]
    chosen = collections.Counter(i.get("maintainer") or UNDEFINED for i in items)
    by_maintainer = collections.Counter(e["maintainer"] for e in entries)
    lines += ["", "| Maintainer | Left out | Of the records chosen from this maintainer |", "|---|---:|---:|"]
    lines += [f"| {cell(m)} | {n} | {chosen[m]} |" for m, n in by_maintainer.most_common()]
    return lines + [""]


def reasks_lines(counts: dict) -> list:
    """The report's lines on the replies asked once more because they weren't JSON or not of the shape asked for
    (llm.call_llm_json), the same in every step. counts: llm.REASKS."""
    first = counts.get("not_json", 0) + counts.get("wrong_shape", 0)
    lines = ["### Replies asked again", ""]
    if not first:
        return lines + ["None: every reply of this run was a JSON object of the shape asked for, the first time.", ""]
    return lines + [
        f"{first} repl(ies) came back unusable the first time and were asked once more, saying what was wrong: "
        f"{counts.get('not_json', 0)} not a JSON object, {counts.get('wrong_shape', 0)} a JSON object of the wrong "
        f"shape. Asking again fixed {counts.get('fixed', 0)}; {counts.get('still_failed', 0)} were still unusable, "
        f"so their records are left out (*Records left out*, reason malformed). Each unusable reply is in this run's "
        f"log, on a DEBUG line starting \"unusable answer\". Nothing to do; the counts tell whether the model's "
        f"structured-output mode is worth trying (docs/improvements.md).", ""]


def reasks_headline(counts: dict) -> dict:
    """The same counts for the manifest's headline numbers."""
    return {"replies asked again": counts.get("not_json", 0) + counts.get("wrong_shape", 0),
            "replies fixed by asking again": counts.get("fixed", 0),
            "replies still unusable": counts.get("still_failed", 0)}


# --------------------------------------------------------------------------
# Every item any stage discards (docs/improvements.md, 2026-11-15: nothing is dropped without a record)
# --------------------------------------------------------------------------
#
#     reset()                                           run_step, before a step's main: an empty list for the run
#     discard(stage, item_type, reason, item, ...)      one entry per item a stage removes, filters, skips or caps
#     fold(stage, item_type, reason, item, kept_as, ...)
#                                                       one entry per item folded into another (a duplicate, a merge)
#     replace(stage, item_type, reason, item, kept_as, ...)
#                                                       one entry per value replaced (the item itself stays)
#     mark(); account(stage, what, items_in, kept, since)
#                                                       items in = items kept + items discarded or folded since
#                                                       the mark, for that stage, or the run stops (a fault in
#                                                       the step's code: something vanished without a record)
#     write(output) -> path; discards_section(path)     run_step, after main: DISCARDS_FILE in the step's output
#                                                       folder and the report's section "Items discarded"
#
# One entry, one line of DISCARDS_FILE:
#     {"stage": "stage 2 (extract)", "action": "discarded" | "folded" | "replaced", "item_type": "triple instance",
#      "reason": "...", "setting": {"max_new_predicates": 50} (when a setting decided it), "record_id": "..." (when
#      the item belongs to one record), "item": {the item's own words and values}, "kept_as": {what it folded into,
#      or its new value} (folded and replaced), "where": "file#position" (when the item came from a file)}

#: The file every pipeline step writes in its output folder, one entry per line (JSON Lines), every run.
DISCARDS_FILE = "discarded.jsonl"
ACTIONS = ("discarded", "folded", "replaced")
#: The entries of the run in progress (run_step resets it before main and writes it after).
DISCARDS: list = []


def reset() -> None:
    """An empty list of discarded items, for a new run (run_step, before the step's main; tests between cases)."""
    DISCARDS.clear()


def _entry(action: str, stage: str, item_type: str, reason: str, item, record_id=None, setting: dict | None = None,
           kept_as=None, where: str | None = None) -> dict:
    if action not in ACTIONS:
        raise ValueError(f"action must be one of {ACTIONS}, not {action!r}")
    if not stage or not item_type or not reason:
        raise ValueError(f"every discarded item needs its stage, item type and reason (got {stage!r}, {item_type!r}, "
                         f"{reason!r})")
    entry = {"stage": stage, "action": action, "item_type": item_type, "reason": reason}
    if setting:
        entry["setting"] = dict(setting)
    if record_id not in (None, ""):
        entry["record_id"] = record_id
    entry["item"] = item
    if action != "discarded":
        entry["kept_as"] = kept_as
    if where:
        entry["where"] = where
    DISCARDS.append(entry)
    return entry


def discard(stage: str, item_type: str, reason: str, item, record_id=None, setting: dict | None = None,
            where: str | None = None) -> dict:
    """Record one item a stage removed, filtered, skipped or capped: the stage, the item's type (docs/terminology.md),
    why (which check; setting: {name: value} when a setting decided it), the item's own words and values, its record
    id and where it came from, when it has them."""
    return _entry("discarded", stage, item_type, reason, item, record_id, setting, None, where)


def fold(stage: str, item_type: str, reason: str, item, kept_as, record_id=None, setting: dict | None = None,
         where: str | None = None) -> dict:
    """Record one item folded into another that is kept (a duplicate into its kept copy, a label into the one it
    merges into): kept_as says which."""
    return _entry("folded", stage, item_type, reason, item, record_id, setting, kept_as, where)


def replace(stage: str, item_type: str, reason: str, item, kept_as, record_id=None, setting: dict | None = None,
            where: str | None = None) -> dict:
    """Record one value a stage replaced (the item it belongs to is kept): item holds the old value, kept_as the
    new. An accounting check (account) doesn't count these: nothing left."""
    return _entry("replaced", stage, item_type, reason, item, record_id, setting, kept_as, where)


def mark() -> int:
    """Where the list stands now, for account(since=...)."""
    return len(DISCARDS)


def account(stage: str, what: str, items_in: int, kept: int, since: int = 0, item_type: str | None = None,
            only=None) -> None:
    """The accounting check of one stage: items_in items went in, kept were kept, and every other one must have been
    recorded, by discard or fold, under this stage since the mark (since=mark(), taken before the stage looked at
    them; item_type: only entries of that item type, for a stage that checks two types of items; only(entry): only
    the entries it is true for, e.g. one kind's). Else something vanished without a record, a fault in the step's
    code: the run stops, naming the stage and the counts. what: the items, in words ("records read from the batch
    files")."""
    recorded = sum(1 for e in DISCARDS[since:] if e["stage"] == stage and e["action"] != "replaced"
                   and (item_type is None or e["item_type"] == item_type) and (only is None or only(e)))
    if items_in != kept + recorded:
        from common.stop import Stop
        missing = items_in - kept - recorded
        raise Stop(f"Accounting check failed in {stage}: {items_in:,} {what} went in, {kept:,} were kept and "
                   f"{recorded:,} were recorded as discarded, so {abs(missing):,} "
                   + ("went missing without a record" if missing > 0 else
                      "were recorded as discarded more than once, or were both kept and recorded as discarded")
                   + ". This is a fault in the step's code, not in its inputs, so no manifest is written for this "
                     "run's outputs. Nothing to fix in the files: tell whoever maintains the code, giving this run's "
                     "log (outputs/logs/), then run the step again once it is fixed.")


def write(output) -> str:
    """Write the run's discarded items to DISCARDS_FILE in the step's output folder (an empty file when nothing was
    discarded, so a file from an earlier run never stays), and return its path."""
    from pathlib import Path

    from common.files import write_jsonl
    path = Path(output) / DISCARDS_FILE
    write_jsonl(path, DISCARDS)
    return str(path)


def discards_section(path: str, entries: list | None = None) -> list:
    """The report's section on the items this run discarded, the same in every step: counted by stage, item type,
    action and reason, with the file that lists each one (path: as the report names it)."""
    entries = DISCARDS if entries is None else entries
    lines = ["### Items discarded", ""]
    if not entries:
        return lines + [f"None: no stage of this run discarded, folded or replaced an item, so `{path}` is empty.", ""]
    lines += [f"{len(entries):,} item(s) were discarded, folded into another item or had a value replaced by a stage "
              f"of this run. Each one is one line of `{path}`, with its stage, its reason, its own words and values, "
              f"its record id and where it came from (search the file for the reason or the record id). Nothing to "
              f"do, unless a count below is not what you expect.", "",
              "| Stage | Item type | Action | Reason | Items |", "|---|---|---|---|---:|"]
    counts = collections.Counter((e["stage"], e["item_type"], e["action"], e["reason"]) for e in entries)
    lines += [f"| {cell(s)} | {cell(t)} | {a} | {cell(r)} | {n:,} |" for (s, t, a, r), n in counts.items()]
    return lines + [""]
