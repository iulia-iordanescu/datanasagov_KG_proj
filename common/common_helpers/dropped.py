"""Records left out of a run because a model call for one of their text pieces failed (040, 050, 060; 070 reads 060's).

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
    "refused": "refused: the model's service withheld the answer (a safety filter)",
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
#: finish_reason values (the service's, or the model maker's own) that mean a filter withheld the answer.
REFUSAL_REASONS = {"content_filter", "refusal", "safety", "prohibited_content", "blocklist", "spii"}
UNDEFINED = "undefined"                  # a record without a maintainer (docs/terminology.md, *maintainer*)


def kind(error) -> str:
    """Why a model call failed, as a key of KINDS."""
    reasons = {str(getattr(error, a, "") or "").lower() for a in ("finish_reason", "native_finish_reason")}
    if reasons & REFUSAL_REASONS:
        return "refused"
    if isinstance(error, llm.CutOff):
        return "cut_off"
    if isinstance(error, llm.BadReply):
        return "malformed"
    if isinstance(error, (llm.ApiError, RuntimeError, ConnectionError, TimeoutError, requests.RequestException)):
        return "service_error"          # RuntimeError: what call_llm raises for a server error or rate limit it gave up on
    return "other"


def kind_from_text(why: str) -> str:
    """The kind of a failure known only by its message (an older run's details file): refused when the message names a
    filter's finish_reason (llm.py words it "finish_reason 'content_filter'"), else other."""
    return "refused" if any(f"finish_reason {r!r}" in (why or "") for r in REFUSAL_REASONS) else "other"


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
