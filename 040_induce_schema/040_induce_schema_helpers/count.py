"""
count.py -- stage 6 (counting): the evidence behind every schema entry found.
Code only, no model.

Each verified triple instance becomes, through the final labels of its
component instances (stage 3's labels, merged and folded by spelling in
stage 4) and the splits of stage 5 (a predicate split by its object's entity
class becomes, for that triple instance, the split's new predicate):

    "MODIS" – "is aboard" – "Aqua"   ->   Instrument  ABOARD  Spacecraft

and three kinds of schema entry are counted:

    entity class   Instrument, Spacecraft          from the subject and object slots together
    predicate      ABOARD                          from the predicate slot
    pattern        Instrument ABOARD Spacecraft    from triple instances whose three component
                                                   instances all have labels

For each schema entry: its support (the number of different texts it was
found in; a text stating it twice counts once), the texts themselves, and
the maintainers they came from. Support from several maintainers is a
catalog-wide regularity; support from one may be that maintainer's house
style, so both are kept. Entity classes also keep, as examples, the
component instances that most often got them.

Each text's title also counts once toward its label (the describes_class
of stage 2), as an entity class, whether or not the title is in a triple
instance: so the types of thing records describe are always counted.

Each quantity is counted independently: a component instance left
unlabeled costs its own schema entry and every pattern through it, not its
neighbors' entries.

Adapted from consolidate() in archive/to_be_reshaped/best_induce_schema.py.
"""
from __future__ import annotations

import collections
from dataclasses import dataclass, field

from common.audit import log

#: Examples kept per entity class (the component instances that most often got it) and per predicate (the
#: triple instances that most often state it, "subject -- predicate -- object": a predicate's examples need its
#: subject and object, since the definition says what they are).
EXAMPLES = 5


@dataclass
class Counts:
    entity_classes: list = field(default_factory=list)  # {"component_class", "support", "texts", "maintainers", "examples"}
    predicates: list = field(default_factory=list)      # {"component_class", "support", "texts", "maintainers", "examples"}
    patterns: list = field(default_factory=list)        # {"pattern", "support", "texts", "maintainers"}
    unlabeled_slots: dict = field(default_factory=dict) # {slot: component instances without a label}
    pattern_of: dict = field(default_factory=dict)      # {text id: [each verified triple instance's pattern
                                                        #  (subject class, predicate, object class), or None]}
    texts_with_triple_instances: int = 0
    texts_with_describes_class: int = 0             # texts whose title got a describes_class


def _entries(ids: dict, maintainers: dict, key_name: str, examples: dict | None = None) -> list:
    rows = []
    for k, texts in ids.items():
        row = {key_name: list(k) if key_name == "pattern" else k, "support": len(texts),
               "texts": sorted(texts), "maintainers": sorted(maintainers[k])}
        if examples is not None:
            row["examples"] = [v for v, _ in examples[k].most_common(EXAMPLES)]
        rows.append(row)
    return sorted(rows, key=lambda r: (-r["support"], r[key_name]))


def count_support(triples, labels, splits) -> Counts:
    counts = Counts()
    final = labels.final                          # stage 3's labels, merged and folded by spelling (stage 4)

    ids = {k: collections.defaultdict(set) for k in ("entity class", "predicate", "pattern")}
    maint = {k: collections.defaultdict(set) for k in ("entity class", "predicate", "pattern")}
    examples = {"entity class": collections.defaultdict(collections.Counter),
                "predicate": collections.defaultdict(collections.Counter)}
    unlabeled = collections.Counter()
    for t in triples.texts:
        if t["triple_instances"]:
            counts.texts_with_triple_instances += 1
        counts.pattern_of[t["id"]] = []
        for ti in t["triple_instances"]:
            sc = final["entity"].get(ti["subject"])
            oc = final["entity"].get(ti["object"])
            p = splits.predicate(final["predicate"].get(ti["predicate"]), oc)   # stage 5's split, if any
            for slot, label, value, entry in (("subject", sc, ti["subject"], "entity class"),
                                              ("object", oc, ti["object"], "entity class"),
                                              ("predicate", p, ti["predicate"], "predicate")):
                if label is None:
                    unlabeled[slot] += 1
                    continue
                ids[entry][label].add(t["id"])
                maint[entry][label].add(t["maintainer"])
                examples[entry][label][value if entry == "entity class" else
                                       f"{ti['subject']} -- {ti['predicate']} -- {ti['object']}"] += 1
            counts.pattern_of[t["id"]].append((sc, p, oc) if sc and oc and p else None)
            if sc and oc and p:
                ids["pattern"][(sc, p, oc)].add(t["id"])
                maint["pattern"][(sc, p, oc)].add(t["maintainer"])
        described = final["entity"].get(t.get("title")) if t.get("describes_class") else None
        if described:
            counts.texts_with_describes_class += 1
            ids["entity class"][described].add(t["id"])
            maint["entity class"][described].add(t["maintainer"])
            examples["entity class"][described][t["title"]] += 1

    counts.entity_classes = _entries(ids["entity class"], maint["entity class"], "component_class",
                                     examples["entity class"])
    counts.predicates = _entries(ids["predicate"], maint["predicate"], "component_class", examples["predicate"])
    counts.patterns = _entries(ids["pattern"], maint["pattern"], "pattern")
    counts.unlabeled_slots = dict(unlabeled)
    log.info(f"  found {len(counts.entity_classes):,} entity classes, {len(counts.predicates):,} "
             f"predicates, {len(counts.patterns):,} patterns")
    return counts
