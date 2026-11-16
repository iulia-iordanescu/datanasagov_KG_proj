"""
extract.py -- stage 2: the triple instances each text states, with no schema
imposed, each checked against its text.

One model call per text piece (040_induce_schema_prompts/extract.txt): list
every fact the text states as a triple instance, with the text's own words as
its subject instance and object instance, a short verb phrase in the model's
words as its predicate instance ("MODIS" – "is aboard" – "Aqua"), and its
source text, the passage that states it. Nothing tells the model which entity classes or
predicates to look for; that is what the later stages learn. (The prompt says
"facts": it speaks plainly to the model.)

Everything else is what 060 uses too (common/common_helpers/extraction.py), so
the schema is learned from the same type of facts extraction later has to
produce: the shared extraction rules; the prompt's layout (the rules first,
then the task, the shared two passes, the reply format, the record between
BEGIN/END RECORD lines, and the shared closing line); the reply format (here
without entity classes, which stage 3 learns); prompt caching of everything
before the record (Anthropic's models); the duplicate count (same_fact,
triple_key); and the model calls themselves (ask_model: cached, `workers` at
a time, a text with a failed call left out whole and asked again on the next
run). What the task requires to differ: no schema is given, and no worked
examples, since those come with an example schema and answers written with
its entity classes and predicates, which would steer a schema learned from
the records (tests/allowed_differences.txt).

The reply also names describes_class: the entity class of the title's
instance ("Dataset", "WebTool", …), judged from the whole text. The one named
by the most text pieces decides it (compared loosely; on a tie, the first
named, in its first spelling), as in 050 and 060 (common/common_helpers/
extraction.describes_class). Stage 3 uses it as the title's label, so
the schema always has entity classes for what records describe, which the
describes triple of 050 and 060 needs.

Every triple instance is then checked in code against its record's whole
text (common/common_helpers/validate.py). One that fails (no source text, or a source text
that isn't in the text) is unverified: it may be invented, so it is left out
of everything the later stages count, and kept, with why, in the evidence
file. One whose component instances are reworded ("the instrument" for
"MODIS") is verified, and its flags are counted in the report.
"""
from __future__ import annotations

import collections
from dataclasses import dataclass, field
from pathlib import Path

from common import dropped, extraction
from common.audit import log
from common.prompt_files import load
from common.report import this_report
from common.text_match import Text
from common.triples_io import REQUIRED, _scalar, component_class_key, triple_key
from common.abbreviations import short_forms
from common.validate import check_abbreviations, check_triple_instance

PROMPTS_DIR = Path(__file__).resolve().parents[1] / "040_induce_schema_prompts"   # 040_induce_schema/040_induce_schema_prompts/
PROMPT = load(PROMPTS_DIR / "extract.txt")
SLOTS = REQUIRED                                  # subject, predicate, object
#: The stage name its discarded items carry (common/common_helpers/dropped.py).
STAGE = "stage 2 (extract_triple_instances)"


def same_fact(instance: dict) -> tuple:
    """The key two triple instances share when they state the same fact, as 050 and 060 count duplicates
    (common/common_helpers/triples_io.triple_key; 040's triple instances have no entity classes)."""
    return triple_key(instance)


@dataclass
class TripleInstances:
    texts: list = field(default_factory=list)     # {"id", "maintainer", "stratum", "title", "describes_class",
                                                  #  "triple_instances", "unverified", "malformed", "duplicates"}
    failed: dict = field(default_factory=dict)    # {text id: why}: left out whole, asked again on the next run
    failed_note: str | None = None                # the report's warning about them
    left_out: list = field(default_factory=list)  # the same, with why and maintainer (common/common_helpers/dropped.py)
    malformed: int = 0                            # items in replies that weren't a triple instance
    errors: dict = field(default_factory=dict)    # {check: triple instances left out for it}
    flags: dict = field(default_factory=dict)     # {check: verified triple instances that raised it}
    calls: int = 0                                # model calls made by this stage
    reused: int = 0                               # pieces answered from the cache
    cut_reused: int = 0                           # pieces cut off in an earlier run, not asked again


def _from_reply(reply: dict) -> tuple:
    """The triple instances in a reply, how many items weren't one (all
    three slots must hold a non-empty value: text, or a number read as text,
    as 050 and 060 read them, triples_io._scalar), and its describes_class
    ("" if none). The source text is kept as given ("" if missing); the
    checks judge it."""
    items = _items(reply)
    good = []
    for t in items:
        if _is_instance(t):
            instance = {k: _scalar(t[k]) for k in SLOTS}
            instance["source_text"] = t["source_text"].strip() if isinstance(t.get("source_text"), str) else ""
            good.append(instance)
    describes = reply.get("describes_class") if isinstance(reply, dict) else None
    describes = " ".join(describes.split()) if isinstance(describes, str) else ""
    return good, len(items) - len(good), describes


def _items(reply) -> list:
    """The items of a reply's "triples" list (none when the reply isn't of the shape asked for)."""
    return reply["triples"] if isinstance(reply, dict) and not extraction.shape_error(reply) else []


def _is_instance(t) -> bool:
    """Whether a reply's item is a triple instance: all three slots hold a non-empty value (_from_reply)."""
    return isinstance(t, dict) and all(_scalar(t.get(k)) for k in SLOTS)


def _record_text(t: dict, replies: list, describes: str, kept: list, copies: list, unverified: list, since: int,
                 verified: list) -> None:
    """One entry per item of a text's replies that stage 2 doesn't keep: an item that isn't a triple instance, a
    copy of a fact stated twice (folded into the copy kept), an unverified triple instance; each describes class a
    text piece named other than the one chosen (the most pieces'). Then the text's accounting check."""
    rid = t["id"]
    n_items = 0
    for reply in replies:
        named = reply.get("describes_class") if isinstance(reply, dict) else None
        named = " ".join(named.split()) if isinstance(named, str) else ""
        if named and named != describes:
            why = ("another spelling of the one chosen, which is kept in its first spelling"
                   if component_class_key(named) == component_class_key(describes) else
                   "more text pieces of the same text named another one (or as many, and it was named first)")
            dropped.replace(STAGE, "describes class", f"named by a text piece, but {why}", {"describes_class": named},
                            {"describes_class": describes}, record_id=rid)
        for item in _items(reply):
            n_items += 1
            if not _is_instance(item):
                dropped.discard(STAGE, "triple instance", "not a triple instance: its subject, predicate or object is "
                                "missing, empty or not text or a number", {"raw": item}, record_id=rid)
    kept_by_key = {same_fact(c[0]): c[0] for c in kept}
    for instance, errs, _ in copies:
        dropped.fold(STAGE, "triple instance", "the same fact stated twice in one text (triple_key): one copy is "
                     "kept, the first that passed the checks", {**instance, "errors": errs},
                     kept_by_key[same_fact(instance)], record_id=rid)
    for instance in unverified:
        dropped.discard(STAGE, "triple instance", "unverified: " + ", ".join(instance["errors"]), instance,
                        record_id=rid)
    dropped.account(STAGE, f"items in the replies about text {rid}", n_items, len(verified), since=since,
                    item_type="triple instance")


def extract_triple_instances(texts, calls, settings: dict) -> TripleInstances:
    def prompt_for(item, piece):
        return extraction.prompt(PROMPT, "", item["record"], piece, with_classes=False,
                                 **extraction.task_parts(extraction.SCOPE_NO_SCHEMA, examples=False))
    replies = extraction.ask_model(texts.items, prompt_for, calls, settings["workers"], "extract",
                                   "040 will extract triple instances (then make a few more calls to label, merge "
                                   f"and define what it finds, all counted in {this_report()}, section *Results*, subsection "
                                   f"*Model calls*)", "extracting", cache_until=extraction.BEGIN_LINE)
    result = TripleInstances(failed=dict(replies.failed), failed_note=extraction.failed_note(replies, "the evidence"),
                             calls=replies.calls, reused=replies.reused, cut_reused=replies.cut_reused,
                             left_out=dropped.left_out(replies, texts.items))

    errors, flags = collections.Counter(), collections.Counter()
    extraction.record_left_out(STAGE, replies, texts.items, "text")
    for t in texts.items:
        if t["id"] not in replies.of:              # a call failed: left out whole, asked again next run
            continue
        since = dropped.mark()
        whole = Text(t["text"])                    # checked against the whole record, every piece
        forms = short_forms(t["text"])             # rule 20's short forms, found once for the text
        checked, named_by_pieces, malformed = [], [], 0
        for reply in replies.of[t["id"]]:
            instances, bad, named = _from_reply(reply)
            malformed += bad
            named_by_pieces.append(named)
            for instance in instances:
                errs, flgs = check_triple_instance(instance, whole, t["title"])
                flgs += check_abbreviations(instance, forms, t["title"])
                checked.append((instance, errs, flgs))
        describes, _ = extraction.describes_class(named_by_pieces)    # the most pieces' (050's and 060's rule)
        # stated by two pieces of one text: counts once, the first copy that passed the checks kept; the same fact as
        # 050 and 060 judge it (triple_key: instances and predicate compared as their keys, case and punctuation aside)
        kept, copies = extraction.best_copies(checked, lambda c: same_fact(c[0]), lambda c: bool(c[1]))
        verified, unverified = [], []
        for instance, errs, flgs in kept:
            if errs:                               # unverified: its errors counted, its flags not
                errors.update(errs)
                unverified.append({**instance, "errors": errs})
            else:                                  # verified: its flags counted
                flags.update(flgs)
                verified.append(instance)
        result.malformed += malformed
        _record_text(t, replies.of[t["id"]], describes, kept, copies, unverified, since, verified)
        result.texts.append({"id": t["id"], "maintainer": t["maintainer"], "stratum": t.get("stratum", ""),
                             "title": t["title"], "describes_class": describes, "triple_instances": verified,
                             "unverified": unverified, "malformed": malformed, "duplicates": len(copies)})
    result.errors, result.flags = dict(errors), dict(flags)
    n = sum(len(t["triple_instances"]) for t in result.texts)
    left_out = sum(len(t["unverified"]) for t in result.texts)
    log.info(f"  {n:,} verified triple instances from {len(result.texts)} texts, {left_out:,} left out as "
             f"unverified ({result.calls} calls, {result.reused} from the cache)")
    return result
