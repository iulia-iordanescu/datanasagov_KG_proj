"""
extract.py -- stage 2: the triple instances each text states, with no schema
imposed, each checked against its text.

One model call per text piece (040_induce_schema_prompts/extract.txt): list
every fact the text states as a triple instance, with the text's own words as
its subject instance and object instance, a short verb phrase in the model's
words as its predicate instance ("MODIS" – "is aboard" – "Aqua"), and its
source text, the passage that states it. Nothing tells the model which types of things or
relations to look for; that is what the later stages learn. (The prompt says
"facts": it speaks plainly to the model.)

Everything else is what 050 and 060 use too (common/common_helpers/extraction.py),
so the schema is learned from the same type of facts extraction later has to
produce: the shared extraction rules, the reply format (here without entity
classes, which stage 3 learns), the record's text between BEGIN/END RECORD
lines, and the model calls themselves (ask_model: cached, `workers` at a
time, a text with a failed call left out whole and asked again on the next
run).

The reply also names describes_class: the type of thing the text's title
names ("Dataset", "WebTool", …), judged from the whole text. The first piece
of a text to name one decides it. Stage 3 uses it as the title's label, so
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

from common import extraction
from common.audit import log
from common.prompt_files import load
from common.report import this_report
from common.text_match import Text
from common.triples_io import REQUIRED
from common.validate import check_triple_instance

PROMPTS_DIR = Path(__file__).resolve().parents[1] / "040_induce_schema_prompts"   # 040_induce_schema/040_induce_schema_prompts/
PROMPT = load(PROMPTS_DIR / "extract.txt")
SLOTS = REQUIRED                                  # subject, predicate, object


@dataclass
class TripleInstances:
    texts: list = field(default_factory=list)     # {"id", "maintainer", "title", "describes_class",
                                                  #  "triple_instances", "unverified"}
    failed: dict = field(default_factory=dict)    # {text id: why}: left out whole, asked again on the next run
    failed_note: str | None = None                # the report's warning about them
    malformed: int = 0                            # items in replies that weren't a triple instance
    errors: dict = field(default_factory=dict)    # {check: triple instances left out for it}
    flags: dict = field(default_factory=dict)     # {check: verified triple instances that raised it}
    calls: int = 0                                # model calls made by this stage
    reused: int = 0                               # pieces answered from the cache


def _from_reply(reply: dict) -> tuple:
    """The triple instances in a reply, how many items weren't one (all
    three slots must hold non-empty text), and its describes_class ("" if
    none). The source text is kept as given ("" if missing); the checks
    judge it."""
    items = reply["triples"] if isinstance(reply, dict) and not extraction.shape_error(reply) else []
    good = []
    for t in items:
        if isinstance(t, dict) and all(isinstance(t.get(k), str) and t[k].strip() for k in SLOTS):
            instance = {k: " ".join(t[k].split()) for k in SLOTS}
            instance["source_text"] = t["source_text"].strip() if isinstance(t.get("source_text"), str) else ""
            good.append(instance)
    describes = reply.get("describes_class") if isinstance(reply, dict) else None
    describes = " ".join(describes.split()) if isinstance(describes, str) else ""
    return good, len(items) - len(good), describes


def extract_triple_instances(texts, calls, settings: dict) -> TripleInstances:
    def prompt_for(item, piece):
        return extraction.prompt(PROMPT, "", item["record"], piece, with_classes=False)
    replies = extraction.ask_model(texts.items, prompt_for, calls, settings["workers"], "extract",
                                   "040 will extract triple instances (then make a few more calls to label, merge "
                                   f"and define what it finds, all counted in {this_report()}, section *Results*, subsection "
                                   f"*Model calls*)", "extracting")
    result = TripleInstances(failed=dict(replies.failed), failed_note=extraction.failed_note(replies, "the evidence"),
                             calls=replies.calls, reused=replies.reused)

    errors, flags = collections.Counter(), collections.Counter()
    for t in texts.items:
        if t["id"] not in replies.of:              # a call failed: left out whole, asked again next run
            continue
        whole = Text(t["text"])                    # checked against the whole record, every piece
        verified, unverified, seen, describes = [], [], set(), ""
        for reply in replies.of[t["id"]]:
            instances, bad, named = _from_reply(reply)
            result.malformed += bad
            describes = describes or named
            for instance in instances:
                spo = tuple(instance[k] for k in SLOTS)
                if spo in seen:                    # stated by two pieces of one text: counts once
                    continue
                seen.add(spo)
                errs, flgs = check_triple_instance(instance, whole, t["title"])
                flags.update(flgs)
                if errs:
                    errors.update(errs)
                    unverified.append({**instance, "errors": errs})
                else:
                    verified.append(instance)
        result.texts.append({"id": t["id"], "maintainer": t["maintainer"], "title": t["title"],
                             "describes_class": describes, "triple_instances": verified,
                             "unverified": unverified})
    result.errors, result.flags = dict(errors), dict(flags)
    n = sum(len(t["triple_instances"]) for t in result.texts)
    left_out = sum(len(t["unverified"]) for t in result.texts)
    log.info(f"  {n:,} verified triple instances from {len(result.texts)} texts, {left_out:,} left out as "
             f"unverified ({result.calls} calls, {result.reused} from the cache)")
    return result
