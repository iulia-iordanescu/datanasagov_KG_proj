"""
count.py -- stage 5: the evidence behind every candidate schema entry. Code
only, no model.

Each verified triple instance becomes, through the labels of its component
instances (stage 3) and the merges (stage 4):

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

Before counting, labels that differ only in case, spacing or punctuation
("Space craft", "Spacecraft") are folded into one, the most frequent
spelling. Digits are kept: "Level2" and "Level3" stay apart. Every fold is
listed in induction_evidence.json (the report shows the first 20).

Each text's title also counts once toward its label (the describes_class
of stage 2), as an entity class, whether or not the title is in a triple
instance: so the kinds of thing records describe are always counted.

Each quantity is counted independently: a component instance left
unlabeled costs its own schema entry and every pattern through it, not its
neighbors' entries.

Adapted from consolidate() in to_be_reshaped/best_induce_schema.py.
"""
from __future__ import annotations

import collections
from dataclasses import dataclass, field

from common.audit import log
from common.triples_io import label_key
from merge import BECOMES

#: Example component instances kept per entity class.
EXAMPLES = 5


@dataclass
class Counts:
    entity_classes: list = field(default_factory=list)  # {"name", "support", "texts", "maintainers", "examples"}
    predicates: list = field(default_factory=list)      # {"name", "support", "texts", "maintainers"}
    patterns: list = field(default_factory=list)        # {"pattern", "support", "texts", "maintainers"}
    spelling_folds: list = field(default_factory=list)  # {"kind", "into", "folded"}
    unlabeled_slots: dict = field(default_factory=dict) # {slot: component instances without a label}
    texts_with_triple_instances: int = 0
    texts_with_describes_class: int = 0             # texts whose title got a describes_class


def _folding(finals: collections.Counter, kind: str, folds: list) -> dict:
    """{label: its spelling-folded label}: labels equal once case, spacing and
    punctuation are ignored become the most frequent spelling (ties
    alphabetically)."""
    groups = collections.defaultdict(collections.Counter)
    for label, n in finals.items():
        groups[label_key(label)][label] += n
    out = {}
    for spellings in groups.values():
        into = sorted(spellings.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
        for label in spellings:
            out[label] = into
        if len(spellings) > 1:
            folds.append({"kind": kind, "into": into, "folded": sorted(spellings)})
    return out


def _entries(ids: dict, maintainers: dict, key_name: str, examples: dict | None = None) -> list:
    rows = []
    for k, texts in ids.items():
        row = {key_name: list(k) if key_name == "pattern" else k, "support": len(texts),
               "texts": sorted(texts), "maintainers": sorted(maintainers[k])}
        if examples is not None:
            row["examples"] = [v for v, _ in examples[k].most_common(EXAMPLES)]
        rows.append(row)
    return sorted(rows, key=lambda r: (-r["support"], r[key_name]))


def count_support(triples, labels) -> Counts:
    counts = Counts()
    final = {}
    for kind in ("entity", "predicate"):
        # component instance -> stage 3 label -> stage 4 merge; then fold spellings.
        merged = {value: labels.merged_into[kind].get(lbl, lbl) for value, lbl in labels.of[kind].items()}
        fold = _folding(collections.Counter(merged.values()), BECOMES[kind], counts.spelling_folds)
        final[kind] = {value: fold[lbl] for value, lbl in merged.items()}

    ids = {k: collections.defaultdict(set) for k in ("entity class", "predicate", "pattern")}
    maint = {k: collections.defaultdict(set) for k in ("entity class", "predicate", "pattern")}
    examples = collections.defaultdict(collections.Counter)
    unlabeled = collections.Counter()
    for t in triples.texts:
        if t["triple_instances"]:
            counts.texts_with_triple_instances += 1
        for ti in t["triple_instances"]:
            sc = final["entity"].get(ti["subject"])
            oc = final["entity"].get(ti["object"])
            p = final["predicate"].get(ti["predicate"])
            for slot, label, value, entry in (("subject", sc, ti["subject"], "entity class"),
                                              ("object", oc, ti["object"], "entity class"),
                                              ("predicate", p, ti["predicate"], "predicate")):
                if label is None:
                    unlabeled[slot] += 1
                    continue
                ids[entry][label].add(t["id"])
                maint[entry][label].add(t["maintainer"])
                if entry == "entity class":
                    examples[label][value] += 1
            if sc and oc and p:
                ids["pattern"][(sc, p, oc)].add(t["id"])
                maint["pattern"][(sc, p, oc)].add(t["maintainer"])
        described = final["entity"].get(t.get("title")) if t.get("describes_class") else None
        if described:
            counts.texts_with_describes_class += 1
            ids["entity class"][described].add(t["id"])
            maint["entity class"][described].add(t["maintainer"])
            examples[described][t["title"]] += 1

    counts.entity_classes = _entries(ids["entity class"], maint["entity class"], "name", examples)
    counts.predicates = _entries(ids["predicate"], maint["predicate"], "name")
    counts.patterns = _entries(ids["pattern"], maint["pattern"], "pattern")
    counts.unlabeled_slots = dict(unlabeled)
    log.info(f"  found {len(counts.entity_classes):,} entity classes, {len(counts.predicates):,} "
             f"predicates, {len(counts.patterns):,} patterns")
    return counts
