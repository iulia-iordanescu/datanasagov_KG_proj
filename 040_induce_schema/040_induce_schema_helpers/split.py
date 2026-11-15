"""
split.py -- stage 5 (splitting): split a predicate whose objects of different
entity classes give it different meanings, checked by code.

After stage 4, a predicate label can still cover several relationships that
differ by what its object is. Suppose SOURCED_FROM has triple instances with
Mission objects ("data from the Apollo 11 mission": which mission produced
the data) and with Spacecraft objects ("images from the Cassini spacecraft":
which spacecraft carried the instrument). Then one predicate for each says
more, and each can translate to its own ground truth schema predicate.

Every predicate whose triple instances reach several object entity classes
(through the final labels of stage 4) goes to the model, SPLIT_BATCH at a time
(040_induce_schema_prompts/split_predicates.txt), with each object entity
class, the number of texts it was found in, and up to EXAMPLES triple
instances. The model proposes predicate splits only where the meaning
differs: a predicate split is a new predicate with the object entity classes
it takes. An object entity class no predicate split takes stays with the
predicate.

What code checks in each proposed predicate split, in this order (the first
that fails rejects it, and the reason is listed):
  - it is a JSON object;
  - its predicate is one of the predicates sent;
  - its new predicate is non-empty text;
  - the new predicate isn't the name of a predicate found (the one split
    included), and no earlier split took the same name (names compared by
    common/common_helpers/triples_io.component_class_key, as spelling folds
    compare them);
  - it names at least one object entity class;
  - every object entity class it names is among the predicate's (its
    patterns' object entity classes);
  - no earlier split of the same predicate took any of them (the first split
    stands, as the first merge does in stage 4);
  - it doesn't take every object entity class of the predicate (that would
    rename the predicate, not split it).

Then the cap, max_new_predicates. A predicate split into n new predicates adds
n predicates, or n - 1 when the splits take every object entity class (the
predicate itself is then left with no triple instance). If the splits that
passed the checks would add more than the cap, they are kept one by one, the
split with the most supporting texts (texts with a triple instance of the
predicate whose object has one of the split's entity classes) first, each kept
only if the total stays within the cap; the others are dropped (their
predicate keeps those objects) and listed. max_new_predicates 0 asks the model
nothing.

Stage 6 (counting) then gives each triple instance of a split predicate,
whose object has an entity class a kept split took, that split's new
predicate. Splitting reads only the induced schema's own labels and triple
instances, never the ground truth or the translation table.

From TRACE-KG (Abolhasani, Ba, He & Pan, "Traceable Context-Enriched Knowledge
Graph Generation with Induced Schemas", arXiv:2604.03496v3): its model may
split an entity class into several (split_class, appendix B.4.2), and its code
keeps only the split entity class's own members, each in one split only
(execute_split_class, TKG_Main.py, line 4796); it sets each triple instance's
predicate with its subject's and object's entity classes in view (section
4.5); and its code carries out only actions it has checked (section 4.6). Here
the split is of a predicate, by its object's entity class.
"""
from __future__ import annotations

import collections
import json
from dataclasses import dataclass, field
from pathlib import Path

from common.audit import log
from common.cache import Cache, ask_cached, ask_split, needs
from common.prompt_files import fill, load
from common.triples_io import component_class_key

PROMPTS_DIR = Path(__file__).resolve().parents[1] / "040_induce_schema_prompts"   # 040_induce_schema/040_induce_schema_prompts/
PROMPT = load(PROMPTS_DIR / "split_predicates.txt")

#: Predicates per call. Each comes with every object entity class it reaches and their examples.
SPLIT_BATCH = 20
#: Example triple instances shown for each object entity class of a predicate.
EXAMPLES = 3

#: The shape of a splitting answer (the prompt's reply format): a "splits" list. One of another shape is asked again,
#: never kept (common/common_helpers/cache.py, ask_cached).
SHAPE = needs(splits=list)

#: Why a proposed split is rejected, in the order code checks (see above).
NOT_AN_OBJECT = "not a JSON object"
NOT_SENT = "its predicate wasn't sent"
NO_NAME = "no new predicate named"
NAME_TAKEN = "its new predicate is the name of a predicate found"
NAME_TWICE = "its new predicate is the name an earlier predicate split took"
NO_CLASSES = "names no object entity class"
NOT_AN_OBJECT_CLASS = "names an object entity class that isn't among the predicate's"
CLASS_TWICE = "names an object entity class an earlier predicate split of the predicate took"
EVERY_CLASS = "takes every object entity class of the predicate (a renaming, not a split)"
REASONS = (NOT_AN_OBJECT, NOT_SENT, NO_NAME, NAME_TAKEN, NAME_TWICE, NO_CLASSES, NOT_AN_OBJECT_CLASS, CLASS_TWICE,
           EVERY_CLASS)


@dataclass
class Splits:
    into: dict = field(default_factory=dict)       # {predicate: {object entity class: new predicate}}: kept splits
    sent: list = field(default_factory=list)       # the predicates sent: {"predicate", "texts", "object_classes"}
    kept: list = field(default_factory=list)       # {"predicate", "into", "object_classes", "texts", "triple_instances"}
    dropped: list = field(default_factory=list)    # passed the checks, left unsplit by the cap: the same fields
    rejected: list = field(default_factory=list)   # {"predicate", "into", "object_classes", "why"}
    refused: list = field(default_factory=list)    # {"predicate", "why"}: the service wouldn't answer about them
    added: int = 0                                 # predicates the kept splits add
    cap: int = 0                                   # max_new_predicates
    calls: int = 0                                 # model calls made by this stage
    reused: int = 0                                # batches answered from the cache

    def predicate(self, predicate, object_class):
        """A triple instance's predicate after splitting: the new predicate of the kept split that took its object's
        entity class, else its predicate as it was."""
        return self.into.get(predicate, {}).get(object_class, predicate)


def object_classes(triples, labels) -> dict:
    """{predicate: {object entity class: {"texts": ids, "examples": Counter of "subject -- predicate -- object"}}}
    from the verified triple instances whose predicate instance and object instance have a final label."""
    found = collections.defaultdict(lambda: collections.defaultdict(
        lambda: {"texts": set(), "examples": collections.Counter()}))
    for t in triples.texts:
        for ti in t["triple_instances"]:
            p = labels.final["predicate"].get(ti["predicate"])
            oc = labels.final["entity"].get(ti["object"])
            if p and oc:
                found[p][oc]["texts"].add(t["id"])
                found[p][oc]["examples"][f"{ti['subject']} -- {ti['predicate']} -- {ti['object']}"] += 1
    return found


def added_by(splits: list, classes_of: dict) -> int:
    """The predicates these splits add: per predicate, one per split, less one when its splits take every object
    entity class it has (classes_of: {predicate: set of its object entity classes})."""
    by = collections.defaultdict(list)
    for s in splits:
        by[s["predicate"]].append(s)
    return sum(len(ss) - (set().union(*(set(s["object_classes"]) for s in ss)) == classes_of[p]) for p, ss in by.items())


def check(replies: list, found: dict, predicates: set) -> tuple:
    """(splits that passed every check, splits rejected with why), from the replies' "splits" items in order.
    found: object_classes(); only its predicates with several object entity classes were sent. predicates: every
    predicate found (the final labels), whose names a new predicate may not take."""
    sent = {component_class_key(p): p for p, ocs in found.items() if len(ocs) > 1}
    taken_names = {component_class_key(p) for p in predicates}
    taken_classes = collections.defaultdict(set)
    passed, rejected = [], []
    for item in (i for reply in replies for i in reply["splits"]):
        if not isinstance(item, dict):
            rejected.append({"predicate": None, "into": None, "object_classes": [], "why": NOT_AN_OBJECT})
            continue
        named = item.get("predicate")
        into = item.get("into")
        ocs = item.get("object_classes")
        row = {"predicate": named, "into": into, "object_classes": ocs if isinstance(ocs, list) else []}
        p = sent.get(component_class_key(named)) if isinstance(named, str) else None
        why = None
        if p is None:
            why = NOT_SENT
        elif not (isinstance(into, str) and into.strip()):
            why = NO_NAME
        elif component_class_key(into) in taken_names:
            why = NAME_TAKEN
        elif component_class_key(into) in {component_class_key(s["into"]) for s in passed}:
            why = NAME_TWICE
        elif not (isinstance(ocs, list) and any(isinstance(c, str) and c.strip() for c in ocs)):
            why = NO_CLASSES
        if why is None:
            own = {component_class_key(oc): oc for oc in found[p]}
            mapped = [own.get(component_class_key(c)) if isinstance(c, str) else None for c in ocs]
            if None in mapped:
                why = NOT_AN_OBJECT_CLASS + ": " + ", ".join(str(c) for c, m in zip(ocs, mapped) if m is None)
            elif set(mapped) & taken_classes[p]:
                why = CLASS_TWICE + ": " + ", ".join(sorted(set(mapped) & taken_classes[p]))
            elif set(mapped) == set(found[p]):
                why = EVERY_CLASS
        if why is not None:
            rejected.append({**row, "why": why})
            continue
        chosen = list(dict.fromkeys(mapped))
        taken_classes[p] |= set(chosen)
        passed.append({"predicate": p, "into": " ".join(into.split()), "object_classes": chosen})
    return passed, rejected


def capped(passed: list, found: dict, cap: int) -> tuple:
    """(kept, dropped): the splits that passed the checks, kept the one with the most supporting texts first (ties:
    by predicate, then new predicate), each only if the predicates added stay within cap."""
    classes_of = {p: set(ocs) for p, ocs in found.items()}
    order = sorted(passed, key=lambda s: (-s["texts"], s["predicate"], s["into"]))
    kept, dropped = [], []
    for s in order:
        (kept if added_by(kept + [s], classes_of) <= cap else dropped).append(s)
    return kept, dropped


def split_predicates(triples, labels, settings: dict, calls) -> Splits:
    result = Splits(cap=settings["max_new_predicates"])
    found = object_classes(triples, labels)
    several = sorted((p for p, ocs in found.items() if len(ocs) > 1),
                     key=lambda p: (-len(set().union(*(oc["texts"] for oc in found[p].values()))), p))
    for p in several:
        ocs = sorted(found[p].items(), key=lambda kv: (-len(kv[1]["texts"]), kv[0]))
        result.sent.append({"predicate": p, "texts": len(set().union(*(oc["texts"] for _, oc in ocs))),
                            "object_classes": [{"entity_class": oc, "texts": len(e["texts"]),
                                                "examples": [x for x, _ in e["examples"].most_common(EXAMPLES)]}
                                               for oc, e in ocs]})
    if result.cap == 0 or not result.sent:
        log.info(f"  splitting: {len(result.sent)} predicate(s) reach several object entity classes; "
                 + ("max_new_predicates is 0, so none is sent" if result.sent else "nothing to ask"))
        if result.cap == 0:
            result.sent = []
        return result

    cache = Cache(calls.cache_dir, "split")
    before = calls.paid.made
    replies, refused = [], []
    for start in range(0, len(result.sent), SPLIT_BATCH):
        batch = result.sent[start:start + SPLIT_BATCH]
        # A batch the service refuses is asked in halves; a predicate it still refuses alone isn't split, with the
        # reason (common.cache.ask_split).
        replies += ask_split(lambda part: ask_cached(
            cache, calls, fill(PROMPT, predicates=json.dumps(part, ensure_ascii=False, indent=0)),
            f"  040 will ask the model which predicates to split by their object's entity class, {SPLIT_BATCH} per "
            f"call", check=SHAPE), batch, refused)
    result.refused = [{"predicate": e["predicate"], "why": why} for e, why in refused]
    result.calls, result.reused = calls.paid.made - before, cache.reused

    passed, result.rejected = check(replies, found, set(labels.final["predicate"].values()))
    for s in passed:
        texts = [t for oc in s["object_classes"] for t in found[s["predicate"]][oc]["texts"]]
        s["texts"] = len(set(texts))
        s["triple_instances"] = sum(sum(found[s["predicate"]][oc]["examples"].values()) for oc in s["object_classes"])
    result.kept, result.dropped = capped(passed, found, result.cap)
    for s in result.kept:
        for oc in s["object_classes"]:
            result.into.setdefault(s["predicate"], {})[oc] = s["into"]
    result.added = added_by(result.kept, {p: set(ocs) for p, ocs in found.items()})
    log.info(f"  splitting: {len(result.sent)} predicate(s) sent; {len(result.kept)} split(s) kept, adding "
             f"{result.added} predicate(s); {len(result.dropped)} dropped by max_new_predicates; "
             f"{len(result.rejected)} rejected")
    return result
