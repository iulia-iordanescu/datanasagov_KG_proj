"""
label.py -- stage 3: give every name one general label, with a running
vocabulary.

Names are the subjects and objects of the facts ("MODIS", "Aqua"), labeled
with a class ("Instrument", "Spacecraft"), and the facts' predicates ("is
aboard"), labeled with a predicate label ("ABOARD"). Classes and predicates
are two separate vocabularies, labeled in two separate passes.

The names are sent in batches of LABEL_BATCH, and every batch is shown the
labels chosen so far, with the instruction to reuse one whenever it fits and
coin a new one only when none does. So one idea doesn't end up under several
labels just because its names were in different batches ("Instrument" in one,
"Sensor" in another). The most common names (found in the most texts) go
first, so the main labels are set early and later batches reuse them.

Each name is judged by one usage example: the shortest fact it appears in.
A name the model leaves unlabeled is asked once more; if it is still
unlabeled it is listed, and it counts toward no class or predicate.

Each batch's answer is cached under a key that includes the labels in use
before it, so a rerun reuses every batch whose names and preceding labels are
unchanged.

Adapted from conceptualize() in to_be_reshaped/best_induce_schema.py, whose
batches couldn't see each other's labels; a later stage then had to repair
the drift, in alphabetical groups where synonyms like "Instrument" and
"Sensor" rarely met.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from cache import Cache, key
from common import llm
from common.audit import log
from common.prompt_files import fill, load

PROMPTS = {"entities": load(Path(__file__).parent / "prompts" / "label_entities.txt"),
           "predicates": load(Path(__file__).parent / "prompts" / "label_predicates.txt")}

#: Names per call. A batch's reply lists every name it was sent, so this
#: bounds the reply's length.
LABEL_BATCH = 80


@dataclass
class Labels:
    of: dict = field(default_factory=dict)          # {"entities": {name: label}, "predicates": {...}}
    vocabulary: dict = field(default_factory=dict)  # {"entities": [labels, in order of first use], ...}
    unlabeled: dict = field(default_factory=dict)   # {"entities": [names], ...}
    batches: list = field(default_factory=list)     # {"kind", "names", "new_labels", "reused"}
    merged_into: dict = field(default_factory=dict) # filled by stage 4: {"entities": {label: final}, ...}
    merges: list = field(default_factory=list)      # filled by stage 4
    merge_issues: dict = field(default_factory=dict)
    calls: int = 0                                  # paid calls made by stage 3
    merge_calls: int = 0                            # paid calls made by stage 4


def _names(facts) -> dict:
    """{kind: {name: (texts it appears in, shortest usage example)}}"""
    found = {"entities": {}, "predicates": {}}
    for t in facts.texts:
        for f in t["triples"]:
            usage = f"{f['subject']} -- {f['predicate']} -- {f['object']}"
            for kind, name in (("entities", f["subject"]), ("entities", f["object"]),
                               ("predicates", f["predicate"])):
                ids, example = found[kind].get(name, (set(), None))
                ids.add(t["id"])
                if example is None or len(usage) < len(example):
                    example = usage
                found[kind][name] = (ids, example)
    return found


def _loose(name: str) -> str:
    """Case and spacing folded: absorbs differences a model introduces when
    it echoes a name back."""
    return re.sub(r"\s+", " ", str(name).strip().lower())


def _match(sent: list, reply) -> tuple:
    """Labels for the names SENT, keyed by the sent name: exact match first,
    then a case- and spacing-insensitive one. A label must be non-empty text.
    Returns (labels, names left unlabeled)."""
    reply = reply if isinstance(reply, dict) else {}
    loose = {}
    for k, v in reply.items():
        if isinstance(v, str) and v.strip():
            loose.setdefault(_loose(k), v.strip())
    labels, missing = {}, []
    for name in sent:
        v = reply.get(name)
        if isinstance(v, str) and v.strip():
            labels[name] = v.strip()
        elif _loose(name) in loose:
            labels[name] = loose[_loose(name)]
        else:
            missing.append(name)
    return labels, missing


def label_names(facts, calls) -> Labels:
    cache = Cache(calls.cache_dir, "label")
    result = Labels()
    before = calls.paid.made
    found = _names(facts)

    for kind in ("entities", "predicates"):
        prompt = PROMPTS[kind]
        # Most common first (found in the most texts); ties by name, so the
        # order never depends on the order of the facts.
        order = sorted(found[kind], key=lambda n: (-len(found[kind][n][0]), n))
        vocabulary, labels, unlabeled = [], {}, []

        def ask(items: dict) -> dict:
            """The labels for one batch: from the cache, else from the model."""
            k = key(prompt.template, kind, items, vocabulary)
            reply = cache.get(k)
            if reply is None:
                calls.paid.start("  040 needs model calls to label names")
                reply = llm.call_llm_json(fill(prompt, vocabulary=json.dumps(vocabulary, ensure_ascii=False),
                                               items=json.dumps(items, ensure_ascii=False, indent=0)))
                calls.paid.made_call()
                reply = reply.get("labels") if isinstance(reply.get("labels"), dict) else {}
                cache.put(k, reply)
            return reply

        for start in range(0, len(order), LABEL_BATCH):
            batch = order[start:start + LABEL_BATCH]
            items = {name: found[kind][name][1] for name in batch}
            got, missing = _match(batch, ask(items))
            if missing:
                # One more try for the names left out, with the vocabulary as it is now.
                more, missing = _match(missing, ask({n: items[n] for n in missing}))
                got.update(more)
            new = [lbl for lbl in dict.fromkeys(got.values()) if lbl not in vocabulary]
            vocabulary += new
            labels.update(got)
            unlabeled += missing
            result.batches.append({"kind": kind, "names": len(batch), "new_labels": new,
                                   "reused": len(set(got.values())) - len(new)})
        result.of[kind], result.vocabulary[kind], result.unlabeled[kind] = labels, vocabulary, unlabeled
        log.info(f"  {kind}: {len(labels):,} names labeled with {len(vocabulary):,} labels"
                 + (f"; {len(unlabeled)} left unlabeled" if unlabeled else ""))
    result.calls = calls.paid.made - before
    return result
