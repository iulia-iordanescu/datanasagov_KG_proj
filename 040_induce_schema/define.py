"""
define.py -- stage 6: one sentence defining each entity class and each
predicate.

Every entity class and predicate whose support reaches min_support is sent
to the model, DEFINE_BATCH at a time, with its support (and, for an entity
class, its example component instances) (prompts/define_entity_classes.txt,
define_predicates.txt). The model writes one sentence for each, or, for a
schema entry too vague to tell anything apart ("Thing", "RELATED_TO"), says
so with a reason.

This stage only writes words. It merges nothing (merging is stage 4's job,
done once, over all labels at a time) and chooses nothing: the examples are
picked by code, from the component instances that most often got each
entity class (stage 5). Stage 7 checks what the model sent back.

Adapted from assemble() in to_be_reshaped/best_induce_schema.py, which also
merged near-duplicates here, a second merge in batches of 40 where synonyms
could miss each other, and asked the model to pick examples.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from common.cache import Cache, key
from common import llm
from common.audit import log
from common.prompt_files import fill, load

#: The two kinds of schema entry that get a definition.
KINDS = ("entity_classes", "predicates")

PROMPTS = {"entity_classes": load(Path(__file__).parent / "prompts" / "define_entity_classes.txt"),
           "predicates": load(Path(__file__).parent / "prompts" / "define_predicates.txt")}

#: Schema entries per call. The reply holds one sentence per entry, so this
#: bounds its length.
DEFINE_BATCH = 40


@dataclass
class Definitions:
    of: dict = field(default_factory=dict)          # {"entity_classes": {name: sentence}, "predicates": {...}}
    too_vague: dict = field(default_factory=dict)   # {"entity_classes": {name: reason}, ...}
    unknown: list = field(default_factory=list)     # schema entries in replies that weren't sent
    calls: int = 0                                  # model calls made by this stage


def write_definitions(counts, settings: dict, calls) -> Definitions:
    cache = Cache(calls.cache_dir, "define")
    result = Definitions()
    before = calls.paid.made
    for kind in KINDS:
        result.of[kind], result.too_vague[kind] = {}, {}
        wanted = [e for e in getattr(counts, kind) if e["support"] >= settings["min_support"]]
        for start in range(0, len(wanted), DEFINE_BATCH):
            batch = [{"name": e["name"], "texts": e["support"],
                      **({"examples": e["examples"]} if kind == "entity_classes" else {})}
                     for e in wanted[start:start + DEFINE_BATCH]]
            k = key(PROMPTS[kind].template, kind, batch)
            reply = cache.get(k)
            if reply is None:
                calls.paid.start("  040 needs model calls to define the schema's entries")
                reply = llm.call_llm_json(fill(PROMPTS[kind],
                                               entries=json.dumps(batch, ensure_ascii=False, indent=0)),
                                          read_timeout=600)
                calls.paid.made_call()
                cache.put(k, reply)
            sent = {e["name"] for e in batch}
            for field_name, target in (("definitions", result.of[kind]),
                                       ("too_vague", result.too_vague[kind])):
                given = reply.get(field_name) if isinstance(reply.get(field_name), dict) else {}
                for name, text in given.items():
                    if name not in sent:
                        result.unknown.append({"kind": kind, "name": name})
                    elif isinstance(text, str) and text.strip() and name not in result.of[kind] \
                            and name not in result.too_vague[kind]:
                        target[name] = " ".join(text.split())
        log.info(f"  {kind.replace('_', ' ')}: {len(result.of[kind]):,} defined, "
                 f"{len(result.too_vague[kind])} too vague")
    result.calls = calls.paid.made - before
    return result
