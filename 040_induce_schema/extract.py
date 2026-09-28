"""
extract.py -- stage 2: the facts each text states, with no schema imposed.

One model call per text piece (prompts/extract.txt): "list every fact as
subject / predicate / object, in the text's own words". Nothing tells the
model which kinds of things or relations to look for; that is what the later
stages learn.

Every fact is then checked in code against the record's whole text
(common/validate.py): its source_text, the passage that states it, must
really be in the text. A fact that fails (no passage, or a passage that isn't
in the text) can't be verified and may be invented, so it is left out of
everything the later stages count; it is kept, with why, in the evidence
file. A fact whose names are reworded ("the instrument" for "MODIS") passes,
and its flags are counted in the report.

A piece whose answer is in the cache is not asked again. Pieces are asked
`workers` at a time, and each answer is stored the moment it arrives, so an
interrupted run keeps what it paid for. A call that fails is logged and left
out; the next run asks it again.
"""
from __future__ import annotations

import collections
from dataclasses import dataclass, field
from pathlib import Path

from cache import Cache, key
from common import llm
from common.audit import log
from common.text_match import Text
from common.validate import check_fact
from common.prompt_files import fill, load

PROMPT = load(Path(__file__).parent / "prompts" / "extract.txt")
END_LINE = "----- END TEXT -----"


@dataclass
class Facts:
    texts: list = field(default_factory=list)     # {"id", "maintainer", "triples", "unverified", "failed_pieces"}
    malformed: int = 0                            # items in replies that were not a usable triple
    errors: dict = field(default_factory=dict)    # {check: facts left out for it}
    flags: dict = field(default_factory=dict)     # {check: facts that raised it, kept}
    calls: int = 0                                # paid calls made by this stage
    reused: int = 0                               # pieces answered from the cache


def _triples(reply: dict) -> tuple:
    """The usable triples in a reply, and how many items were not usable:
    subject, predicate and object must each be non-empty text. source_text
    is kept as given ("" if missing); the checks judge it."""
    items = reply.get("triples") if isinstance(reply.get("triples"), list) else []
    good = []
    for t in items:
        if isinstance(t, dict) and all(isinstance(t.get(k), str) and t[k].strip()
                                       for k in ("subject", "predicate", "object")):
            fact = {k: " ".join(t[k].split()) for k in ("subject", "predicate", "object")}
            fact["source_text"] = t["source_text"].strip() if isinstance(t.get("source_text"), str) else ""
            good.append(fact)
    return good, len(items) - len(good)


def extract_facts(texts, calls, settings: dict) -> Facts:
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

    facts = Facts(reused=len(answers))
    failed = {}
    if todo:
        calls.paid.start(f"  040 will make {len(todo)} call(s) to extract facts, then a few more "
                         f"to label, merge and define what it finds (all counted in the report)")
        before = calls.paid.made

        def ask(k, piece):
            reply = llm.call_llm_json(fill(PROMPT, text=llm.fence_safe(piece, END_LINE)))
            calls.paid.made_call()
            return k, reply

        def handle(n, where, result, error):
            if error is not None:
                failed[where] = str(error)
                log.warning(f"extraction failed for {where[0]} piece {where[1] + 1}: {error}")
                return
            k, reply = result
            triples, bad = _triples(reply)
            answers[where] = {"triples": triples, "malformed": bad}
            cache.put(k, answers[where])
            log.debug(f"extracted {where[0]} piece {where[1] + 1}: {len(triples)} triples ({n}/{len(todo)})")

        llm.run_parallel(ask, {w: v for w, v in todo.items()}, settings["workers"], handle,
                         "Answers already received are kept in the cache.")
        facts.calls = calls.paid.made - before

    errors, flags = collections.Counter(), collections.Counter()
    for t in texts.items:
        whole = Text(t["text"])                    # checked against the whole record, every piece
        triples, unverified, seen, pieces_failed = [], [], set(), []
        for i in range(len(t["pieces"])):
            answer = answers.get((t["id"], i))
            if answer is None:
                pieces_failed.append(i)
                continue
            facts.malformed += answer.get("malformed", 0)
            for fact in answer["triples"]:
                spo = (fact["subject"], fact["predicate"], fact["object"])
                if spo in seen:                    # a fact repeated by two pieces counts once
                    continue
                seen.add(spo)
                errs, flgs = check_fact(fact, whole, t["title"])
                flags.update(flgs)
                if errs:
                    errors.update(errs)
                    unverified.append({**fact, "errors": errs})
                else:
                    triples.append(fact)
        facts.texts.append({"id": t["id"], "maintainer": t["maintainer"], "triples": triples,
                            "unverified": unverified, "failed_pieces": pieces_failed})
    facts.errors, facts.flags = dict(errors), dict(flags)
    n = sum(len(t["triples"]) for t in facts.texts)
    left_out = sum(len(t["unverified"]) for t in facts.texts)
    log.info(f"  {n:,} verified facts from {len(facts.texts)} texts, {left_out:,} left out as unverified "
             f"({facts.calls} calls, {facts.reused} from the cache)")
    return facts
