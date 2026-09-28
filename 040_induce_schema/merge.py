"""
merge.py -- stage 4: one last look at all the labels, to merge synonyms.

Stage 3's running vocabulary prevents most synonyms, but a few can slip
through (a label coined early, before its better-known synonym was in use).
So the finished list of labels goes to the model in ONE call per kind (class
labels, then predicate labels), each label with the names that most often got
it (prompts/merge_classes.txt, merge_predicates.txt). Every label is seen
beside every other, so no pair of synonyms is missed for being in different
batches.

The model lists only the merges it finds, {"into": "Instrument", "labels":
["Sensor", "Detector"]}, not every label, so its reply stays short however
many labels there are.

What code checks in the reply:
  - "into" must be one of the labels sent (the model can't invent a name);
  - a label that wasn't sent is ignored;
  - a label merged into two different labels keeps the first;
  - chains (Sensor -> Detector, Detector -> Instrument) are followed to
    their end, so each label maps straight to its final name.
Every merge and every ignored item is listed in the report: a wrong merge
(two different ideas made one) is the one mistake code can't catch, so it
must be visible.

If a list is too long for one call (over MAX_LABELS_ONE_CALL), the step
stops and says so, rather than splitting it into groups where synonyms could
miss each other.
"""
from __future__ import annotations

import collections
import json
from pathlib import Path

from cache import Cache, key
from common import llm
from common.audit import log
from common.prompt_files import fill, load

PROMPTS = {"entities": load(Path(__file__).parent / "prompts" / "merge_classes.txt"),
           "predicates": load(Path(__file__).parent / "prompts" / "merge_predicates.txt")}

#: The most labels sent in one call. Each takes a few dozen characters with
#: its example names, so this is far below what one call can read; the reply
#: holds only the merges. Above it, the step stops (see the docstring).
MAX_LABELS_ONE_CALL = 800

#: Example names shown for each label.
EXAMPLES = 3

#: What each kind of label is called in the report and the evidence file: the
#: labels of entity names are class labels.
KIND_NAME = {"entities": "classes", "predicates": "predicates"}


def _flatten(mapping: dict) -> dict:
    """Follow chains so each label maps straight to its final name; a cycle
    stops where it would repeat."""
    out = {}
    for label in mapping:
        seen, target = {label}, mapping[label]
        while target in mapping and mapping[target] != target and mapping[target] not in seen:
            seen.add(target)
            target = mapping[target]
        out[label] = target
    return out


def merge_labels(labels, facts, calls):
    cache = Cache(calls.cache_dir, "merge")
    before = calls.paid.made
    for kind in ("entities", "predicates"):
        names_of = collections.defaultdict(collections.Counter)
        texts_with = collections.defaultdict(set)
        for t in facts.texts:
            for f in t["triples"]:
                for k2, name in (("entities", f["subject"]), ("entities", f["object"]),
                                 ("predicates", f["predicate"])):
                    if k2 == kind and name in labels.of[kind]:
                        names_of[labels.of[kind][name]][name] += 1
                        texts_with[labels.of[kind][name]].add(t["id"])
        sent = sorted(labels.vocabulary[kind])
        if len(sent) > MAX_LABELS_ONE_CALL:
            raise ValueError(f"{len(sent)} {kind} labels are more than one call takes "
                             f"({MAX_LABELS_ONE_CALL}). Merging them in separate groups would let "
                             f"synonyms miss each other; group them by meaning first (see "
                             f"instructions/040_induce_schema.md, Known limits).")
        issues = {"into_not_a_label": [], "not_sent": [], "merged_twice": []}
        mapping = {label: label for label in sent}
        if len(sent) > 1:
            listing = [{"label": lbl, "texts": len(texts_with[lbl]),
                        "names": [n for n, _ in names_of[lbl].most_common(EXAMPLES)]} for lbl in sent]
            k = key(PROMPTS[kind].template, kind, listing)
            reply = cache.get(k)
            if reply is None:
                calls.paid.start("  040 needs model calls to merge synonymous labels")
                reply = llm.call_llm_json(fill(PROMPTS[kind],
                                               labels=json.dumps(listing, ensure_ascii=False, indent=0)),
                                          read_timeout=600)
                calls.paid.made_call()
                cache.put(k, reply)
            decided = {}
            for m in reply.get("merges") if isinstance(reply.get("merges"), list) else []:
                if not isinstance(m, dict):
                    continue
                into = m.get("into")
                if into not in mapping:
                    issues["into_not_a_label"].append(into)
                    continue
                for lbl in m.get("labels") if isinstance(m.get("labels"), list) else []:
                    if lbl not in mapping:
                        issues["not_sent"].append(lbl)
                    elif lbl == into:
                        continue
                    elif lbl in decided and decided[lbl] != into:
                        issues["merged_twice"].append(lbl)      # the first merge stands
                    else:
                        decided[lbl] = into
            mapping.update(decided)
            mapping = _flatten(mapping)
        for lbl, final in sorted(mapping.items()):
            if final != lbl:
                labels.merges.append({"kind": KIND_NAME[kind], "label": lbl, "into": final,
                                      "names": len(names_of[lbl]), "texts": len(texts_with[lbl])})
        labels.merged_into[kind] = mapping
        labels.merge_issues[kind] = issues
        merged = sum(1 for m in labels.merges if m["kind"] == KIND_NAME[kind])
        log.info(f"  {KIND_NAME[kind]}: {merged} of {len(sent)} labels merged into others")
    labels.merge_calls = calls.paid.made - before
    return labels
