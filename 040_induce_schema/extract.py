"""
extract.py -- stage 2: the triple instances each text states, with no schema
imposed, each checked against its text.

One model call per text piece (prompts/extract.txt): list every fact the
text states as a triple instance, with the text's own words as its component
instances ("MODIS" – "is aboard" – "Aqua"), and with its source text, the
passage that states it. Nothing tells the model which kinds of things or
relations to look for; that is what the later stages learn. (The prompt says
"facts": it speaks plainly to the model.)

Every triple instance is then checked in code against its record's whole
text (common/validate.py). One that fails (no source text, or a source text
that isn't in the text) is unverified: it may be invented, so it is left out
of everything the later stages count, and kept, with why, in the evidence
file. One whose component instances are reworded ("the instrument" for
"MODIS") is verified, and its flags are counted in the report.

A piece whose answer is in the cache is not asked again. Pieces are asked
`workers` at a time, and each answer is stored the moment it arrives, so an
interrupted run keeps what it paid for. A call that fails is logged and left
out; the next run asks it again.
"""
from __future__ import annotations

import collections
from dataclasses import dataclass, field
from pathlib import Path

from common.cache import Cache, key
from common import llm
from common.audit import log
from common.prompt_files import fill, load
from common.text_match import Text
from common.validate import check_triple_instance

PROMPT = load(Path(__file__).parent / "prompts" / "extract.txt")
END_LINE = "----- END TEXT -----"
SLOTS = ("subject", "predicate", "object")


@dataclass
class TripleInstances:
    texts: list = field(default_factory=list)     # {"id", "maintainer", "triple_instances", "unverified", "failed_pieces"}
    malformed: int = 0                            # items in replies that weren't a triple instance
    errors: dict = field(default_factory=dict)    # {check: triple instances left out for it}
    flags: dict = field(default_factory=dict)     # {check: verified triple instances that raised it}
    calls: int = 0                                # model calls made by this stage
    reused: int = 0                               # pieces answered from the cache


def _from_reply(reply: dict) -> tuple:
    """The triple instances in a reply, and how many items weren't one: all
    three slots must hold non-empty text. The source text is kept as given
    ("" if missing); the checks judge it."""
    items = reply.get("triples") if isinstance(reply.get("triples"), list) else []
    good = []
    for t in items:
        if isinstance(t, dict) and all(isinstance(t.get(k), str) and t[k].strip() for k in SLOTS):
            instance = {k: " ".join(t[k].split()) for k in SLOTS}
            instance["source_text"] = t["source_text"].strip() if isinstance(t.get("source_text"), str) else ""
            good.append(instance)
    return good, len(items) - len(good)


def extract_triple_instances(texts, calls, settings: dict) -> TripleInstances:
    cache = Cache(calls.cache_dir, "extract")
    answers, todo = {}, {}
    for t in texts.items:
        for i, piece in enumerate(t["pieces"]):
            k = key(PROMPT.template, piece)
            stored = cache.get(k)
            if stored is not None:
                answers[(t["id"], i)] = stored
            else:
                todo[(t["id"], i)] = (k, piece)

    result = TripleInstances(reused=len(answers))
    if todo:
        calls.paid.start(f"  040 will make {len(todo)} model call(s) to extract triple instances, then a "
                         f"few more to label, merge and define what it finds (all counted in the report)")
        before = calls.paid.made

        def ask(k, piece):
            reply = llm.call_llm_json(fill(PROMPT, text=llm.fence_safe(piece, END_LINE)))
            calls.paid.made_call()
            return k, reply

        def handle(n, where, answer, error):
            if error is not None:
                log.warning(f"extraction failed for {where[0]} piece {where[1] + 1}: {error}")
                return
            k, reply = answer
            instances, bad = _from_reply(reply)
            answers[where] = {"triple_instances": instances, "malformed": bad}
            cache.put(k, answers[where])
            log.debug(f"extracted {where[0]} piece {where[1] + 1}: {len(instances)} triple instances "
                      f"({n}/{len(todo)})")

        llm.run_parallel(ask, dict(todo), settings["workers"], handle,
                         "Answers already received are kept in the cache.")
        result.calls = calls.paid.made - before

    errors, flags = collections.Counter(), collections.Counter()
    for t in texts.items:
        whole = Text(t["text"])                    # checked against the whole record, every piece
        verified, unverified, seen, pieces_failed = [], [], set(), []
        for i in range(len(t["pieces"])):
            answer = answers.get((t["id"], i))
            if answer is None:
                pieces_failed.append(i)
                continue
            result.malformed += answer.get("malformed", 0)
            for instance in answer["triple_instances"]:
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
        result.texts.append({"id": t["id"], "maintainer": t["maintainer"], "triple_instances": verified,
                             "unverified": unverified, "failed_pieces": pieces_failed})
    result.errors, result.flags = dict(errors), dict(flags)
    n = sum(len(t["triple_instances"]) for t in result.texts)
    left_out = sum(len(t["unverified"]) for t in result.texts)
    log.info(f"  {n:,} verified triple instances from {len(result.texts)} texts, {left_out:,} left out as "
             f"unverified ({result.calls} calls, {result.reused} from the cache)")
    return result
