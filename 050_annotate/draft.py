"""
draft.py -- stage 2: the model drafts each chosen record's triple instances.

One call per text piece (a long record is split, as in 040: common/chunking.py).
The prompt (prompts/draft.txt) puts COMPLETENESS FIRST: every fact the
record states, whether or not the hand-built schema can express it; then
NAMING: the schema's entity classes and predicates when one fits, a new
name otherwise. Its rules and reply format are shared with 060
(common/prompts/), so the ground truth and what 060 extracts are asked for
the same way.

Every answer is kept in cache/draft.json (common/cache.py) the moment it
arrives: a rerun, e.g. after a failed call or Ctrl+C, pays only for what
it doesn't have. A record whose call fails, for any piece, is left out of
the batch, never half drafted; the next run drafts it again.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from common import extraction, llm
from common.audit import log
from common.cache import Cache, key
from common.prompt_files import fill, load

PROMPT = load(Path(__file__).parent / "prompts" / "draft.txt")


@dataclass
class Replies:
    of: dict = field(default_factory=dict)        # {id: [reply per piece]} for records fully answered
    failed: dict = field(default_factory=dict)    # {id: why}
    calls: int = 0                                # model calls made by this stage
    reused: int = 0                               # pieces answered from the cache


def prompt_for(chosen, item: dict, piece: str) -> str:
    return fill(PROMPT, schema=chosen.schema_text, rules=extraction.rules_for(chosen.records[item["id"]]),
                reply=extraction.REPLY.template.strip(), text=extraction.wrap(piece))


def ask_model(chosen, calls, settings: dict) -> Replies:
    cache = Cache(calls.cache_dir, "draft")
    answers, todo = {}, {}
    for item in chosen.items:
        for i, piece in enumerate(item["pieces"]):
            prompt = prompt_for(chosen, item, piece)
            k = key(prompt)
            stored = cache.get(k)
            if stored is not None:
                answers[(item["id"], i)] = stored
            else:
                todo[(item["id"], i)] = (k, prompt)

    result = Replies(reused=len(answers))
    if todo:
        n_records = len({rid for rid, _ in todo})
        calls.paid.start(f"  050 will draft {len(chosen.items)} record(s) into batch {chosen.batch}: "
                         f"{len(todo)} model call(s) for {n_records} record(s)"
                         + (f", {len(answers)} text piece(s) answered from the cache" if answers else ""))
        before = calls.paid.made

        def ask(k, prompt):
            reply = llm.call_llm_json(prompt)
            calls.paid.made_call()
            return k, reply

        def handle(n, where, answer, error):
            if error is not None:
                result.failed[where[0]] = f"piece {where[1] + 1}: {error}"
                log.warning(f"drafting failed for {where[0]} piece {where[1] + 1}: {error}")
                return
            k, reply = answer
            answers[where] = reply
            cache.put(k, reply)
            log.debug(f"drafted {where[0]} piece {where[1] + 1} ({n}/{len(todo)})")

        llm.run_parallel(ask, dict(todo), settings["workers"], handle,
                         "Answers already received are kept in the cache; no batch was written.")
        result.calls = calls.paid.made - before

    for item in chosen.items:
        replies = [answers.get((item["id"], i)) for i in range(len(item["pieces"]))]
        if item["id"] not in result.failed and all(r is not None for r in replies):
            result.of[item["id"]] = replies
    log.info(f"  {len(result.of)} record(s) drafted, {len(result.failed)} failed "
             f"({result.calls} calls, {result.reused} text piece(s) from the cache)")
    return result
