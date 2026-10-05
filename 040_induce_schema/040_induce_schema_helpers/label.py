"""
label.py -- stage 3: give every component instance a label, with a running
vocabulary.

A label is the general name for a component instance: for one in a subject
or object slot, the kind of thing it is ("MODIS" → `Instrument`), which
becomes an entity class; for one in a predicate slot, the relation it
expresses ("is aboard" → `ABOARD`), which becomes a predicate. The two kinds
are labeled in two separate passes, each with its own vocabulary of labels.

The component instances are sent in batches of LABEL_BATCH, and every batch
is shown the labels chosen so far, with the instruction to reuse one whenever
it fits and coin a new one only when none does. So one idea doesn't end up
under several labels just because its component instances were in different
batches (`Instrument` in one, `Sensor` in another). The most common
component instances (found in the most texts) go first, so the main labels
are set early and later batches reuse them.

Each component instance is judged by one usage example: the shortest
triple instance it appears in. One the model leaves unlabeled is asked once
more; if it is still unlabeled it is listed, and it counts toward no schema
entry.

A text's title is not sent: its label is the describes_class stage 2 got
for it, judged from the whole text. Those labels also start the entity
vocabulary (most common first), so other component instances reuse them.

Each batch's answer is cached under a key that includes the labels in use
before it, so a rerun reuses every batch whose component instances and
preceding labels are unchanged.

Adapted from conceptualize() in to_be_reshaped/best_induce_schema.py, whose
batches couldn't see each other's labels; a later stage then had to repair
the drift, in alphabetical groups where synonyms like `Instrument` and
`Sensor` rarely met.
"""
from __future__ import annotations

import collections
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from common.cache import Cache, key
from common import llm
from common.audit import log
from common.prompt_files import fill, load

#: The two kinds of component instance, by slot: "entity" for subject and
#: object slots (labeled with entity classes), "predicate" for the predicate
#: slot (labeled with predicates).
KINDS = ("entity", "predicate")

PROMPTS_DIR = Path(__file__).resolve().parents[1] / "040_induce_schema_prompts"   # 040_induce_schema/040_induce_schema_prompts/
PROMPTS = {"entity": load(PROMPTS_DIR / "label_entity_instances.txt"),
           "predicate": load(PROMPTS_DIR / "label_predicate_instances.txt")}

#: Component instances per call. A batch's reply lists every component
#: instance it was sent, so this bounds the reply's length.
LABEL_BATCH = 80


@dataclass
class Labels:
    of: dict = field(default_factory=dict)          # {"entity": {component instance: label}, "predicate": {...}}
    vocabulary: dict = field(default_factory=dict)  # {"entity": [labels, in order of first use], ...}
    unlabeled: dict = field(default_factory=dict)   # {"entity": [component instances], ...}
    batches: list = field(default_factory=list)     # {"kind", "component_instances", "new_labels", "reused"}
    merged_into: dict = field(default_factory=dict) # filled by stage 4: {"entity": {label: final label}, ...}
    merges: list = field(default_factory=list)      # filled by stage 4
    merge_issues: dict = field(default_factory=dict)
    calls: int = 0                                  # model calls made by stage 3
    merge_calls: int = 0                            # model calls made by stage 4


def component_instances(triples) -> dict:
    """{kind: {component instance: (ids of the texts it appears in, its
    shortest usage example)}}, from the verified triple instances."""
    found = {kind: {} for kind in KINDS}
    for t in triples.texts:
        for ti in t["triple_instances"]:
            usage = f"{ti['subject']} -- {ti['predicate']} -- {ti['object']}"
            for kind, value in (("entity", ti["subject"]), ("entity", ti["object"]),
                                ("predicate", ti["predicate"])):
                ids, example = found[kind].get(value, (set(), None))
                ids.add(t["id"])
                if example is None or len(usage) < len(example):
                    example = usage
                found[kind][value] = (ids, example)
    return found


def titles_labeled(triples) -> dict:
    """{title: its describes_class} for every text whose reply named one."""
    return {t["title"]: t["describes_class"] for t in triples.texts
            if t.get("describes_class") and t.get("title")}


def _loose(value: str) -> str:
    """Case and spacing folded: absorbs differences a model introduces when
    it echoes a component instance back."""
    return re.sub(r"\s+", " ", str(value).strip().lower())


def _match(sent: list, reply) -> tuple:
    """Labels for the component instances SENT, keyed as sent: exact match
    first, then a case- and spacing-insensitive one. A label must be
    non-empty text. Returns (labels, component instances left unlabeled)."""
    reply = reply if isinstance(reply, dict) else {}
    loose = {}
    for k, v in reply.items():
        if isinstance(v, str) and v.strip():
            loose.setdefault(_loose(k), v.strip())
    labels, missing = {}, []
    for value in sent:
        v = reply.get(value)
        if isinstance(v, str) and v.strip():
            labels[value] = v.strip()
        elif _loose(value) in loose:
            labels[value] = loose[_loose(value)]
        else:
            missing.append(value)
    return labels, missing


def label_component_instances(triples, calls) -> Labels:
    cache = Cache(calls.cache_dir, "label")
    result = Labels()
    before = calls.paid.made
    found = component_instances(triples)

    for kind in KINDS:
        prompt = PROMPTS[kind]
        # Most common first (found in the most texts); ties alphabetically,
        # so the order never depends on the order of the triple instances.
        vocabulary, labels, unlabeled = [], {}, []
        if kind == "entity":
            labels = titles_labeled(triples)
            counted = collections.Counter(labels.values())
            vocabulary = sorted(counted, key=lambda lbl: (-counted[lbl], lbl))
        order = sorted((v for v in found[kind] if v not in labels),
                       key=lambda v: (-len(found[kind][v][0]), v))

        def ask(items: dict) -> dict:
            """The labels for one batch: from the cache, else from the model."""
            k = key(prompt.template, kind, items, vocabulary)
            reply = cache.get(k)
            if reply is None:
                calls.paid.start("  040 needs model calls to label component instances")
                reply = llm.call_llm_json(fill(prompt, vocabulary=json.dumps(vocabulary, ensure_ascii=False),
                                               items=json.dumps(items, ensure_ascii=False, indent=0)))
                calls.paid.made_call()
                reply = reply.get("labels") if isinstance(reply.get("labels"), dict) else {}
                cache.put(k, reply)
            return reply

        for start in range(0, len(order), LABEL_BATCH):
            batch = order[start:start + LABEL_BATCH]
            items = {value: found[kind][value][1] for value in batch}
            got, missing = _match(batch, ask(items))
            if missing:
                # One more try for those left out, with the vocabulary as it is now.
                more, missing = _match(missing, ask({v: items[v] for v in missing}))
                got.update(more)
            new = [lbl for lbl in dict.fromkeys(got.values()) if lbl not in vocabulary]
            vocabulary += new
            labels.update(got)
            unlabeled += missing
            result.batches.append({"kind": kind, "component_instances": len(batch), "new_labels": new,
                                   "reused": len(set(got.values())) - len(new)})
        result.of[kind], result.vocabulary[kind], result.unlabeled[kind] = labels, vocabulary, unlabeled
        log.info(f"  {kind} component instances: {len(labels):,} labeled with {len(vocabulary):,} labels"
                 + (f"; {len(unlabeled)} left unlabeled" if unlabeled else ""))
    result.calls = calls.paid.made - before
    return result
