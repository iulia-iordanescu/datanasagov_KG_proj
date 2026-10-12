"""
define.py -- stage 6: one sentence defining each entity class and each
predicate.

Every entity class and predicate whose support reaches min_support is sent
to the model, DEFINE_BATCH at a time, with its support and its examples (an
entity class's component instances; a predicate's triple instances, which show
its subject and object) (prompts/define_entity_classes.txt,
define_predicates.txt). The model writes one sentence for each, or, for a
schema entry too vague to tell anything apart ("Thing", "RELATED_TO"), says
so with a reason.

This stage only writes words. It merges nothing (merging is stage 4's job,
done once, over all labels at a time) and chooses nothing: the examples are
picked by code (stage 5): the component instances that most often got each
entity class, the triple instances that most often state each predicate. Stage 7 checks what the model sent back.

Adapted from assemble() in to_be_reshaped/best_induce_schema.py, which also
merged near-duplicates here, a second merge in batches of 40 where synonyms
could miss each other, and asked the model to pick examples.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from common.cache import Cache, ask_cached, ask_split
from common.audit import log
from common.prompt_files import fill, load

#: The two kinds of schema entry that get a definition.
KINDS = ("entity_classes", "predicates")
#: The words for KINDS in the output files ("kind", "entry_type").
WORD = {"entity_classes": "entity class", "predicates": "predicate"}

PROMPTS_DIR = Path(__file__).resolve().parents[1] / "040_induce_schema_prompts"   # 040_induce_schema/040_induce_schema_prompts/
PROMPTS = {"entity_classes": load(PROMPTS_DIR / "define_entity_classes.txt"),
           "predicates": load(PROMPTS_DIR / "define_predicates.txt")}

#: Schema entries per call. The reply holds one sentence per entry, so this
#: bounds its length.
DEFINE_BATCH = 40


@dataclass
class Definitions:
    of: dict = field(default_factory=dict)          # {"entity_classes": {entity class: sentence}, "predicates": {...}}
    too_vague: dict = field(default_factory=dict)   # {"entity_classes": {entity class: reason}, ...}
    unknown: list = field(default_factory=list)     # schema entries in replies that weren't sent
    refused: list = field(default_factory=list)     # {"kind", "component_class", "why"}: the service wouldn't define
                                                    # them (e.g. its content filter), so they get no definition
    calls: int = 0                                  # model calls made by this stage
    reused: int = 0                                 # batches answered from the cache


def write_definitions(counts, settings: dict, calls) -> Definitions:
    cache = Cache(calls.cache_dir, "define")
    result = Definitions()
    before = calls.paid.made
    for kind in KINDS:
        result.of[kind], result.too_vague[kind] = {}, {}
        wanted = [e for e in getattr(counts, kind) if e["support"] >= settings["min_support"]]
        for start in range(0, len(wanted), DEFINE_BATCH):
            batch = [{"component_class": e["component_class"], "texts": e["support"], "examples": e["examples"]}
                     for e in wanted[start:start + DEFINE_BATCH]]
            refused = []
            # A batch the service refuses is asked in halves; an entry it still refuses alone gets no definition, with
            # the reason (common.cache.ask_split).
            replies = ask_split(lambda part: ask_cached(
                cache, calls, fill(PROMPTS[kind], entries=json.dumps(part, ensure_ascii=False, indent=0)),
                f"  040 will ask the model to define the schema's entries, {DEFINE_BATCH} per call"), batch, refused)
            result.refused += [{"kind": WORD[kind], "component_class": e["component_class"], "why": why}
                               for e, why in refused]
            sent = {e["component_class"] for e in batch}
            for reply, (field_name, target) in [(r, ft) for r in replies for ft in (("definitions", result.of[kind]),
                                                                                    ("too_vague", result.too_vague[kind]))]:
                given = reply.get(field_name) if isinstance(reply.get(field_name), dict) else {}
                for name, text in given.items():
                    if name not in sent:
                        result.unknown.append({"kind": WORD[kind], "component_class": name})
                    elif isinstance(text, str) and text.strip() and name not in result.of[kind] \
                            and name not in result.too_vague[kind]:
                        target[name] = " ".join(text.split())
        log.info(f"  {kind.replace('_', ' ')}: {len(result.of[kind]):,} defined, "
                 f"{len(result.too_vague[kind])} too vague")
    result.calls, result.reused = calls.paid.made - before, cache.reused
    return result
