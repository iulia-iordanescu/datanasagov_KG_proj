"""
count.py -- stage 5: the evidence behind every candidate schema entry. Code
only, no model.

Each fact becomes, through its names' labels (stage 3) and the merges
(stage 4):

    MODIS -- is aboard -- Aqua   ->   Instrument  ABOARD  Spacecraft

and three kinds of entry are counted:

    class      Instrument, Spacecraft         from subjects and objects together
    predicate  ABOARD                         from the facts' predicates
    pattern    Instrument ABOARD Spacecraft   from facts whose three names all have labels

For each entry: its SUPPORT, the number of different texts that produced it
(a text stating a fact twice counts once), the texts themselves, and the
maintainers they came from. Support from several maintainers is a
catalog-wide regularity; support from one may be that maintainer's house
style, so both are kept. Classes also keep their most common names as
examples.

Before counting, labels that differ only in case, spacing or punctuation
("Space craft", "Spacecraft") are folded into one, the most frequent
spelling. Digits are kept: "Level2" and "Level3" stay apart. Every fold is
listed in the report.

Each quantity is counted independently: a name left unlabeled costs its own
class and every pattern through it, not its neighbors' classes.

Adapted from consolidate() in to_be_reshaped/best_induce_schema.py.
"""
from __future__ import annotations

import collections
import re
from dataclasses import dataclass, field

from common.audit import log

#: Example names kept per class.
EXAMPLES = 5


@dataclass
class Counts:
    classes: list = field(default_factory=list)     # {"name", "support", "texts", "maintainers", "examples"}
    predicates: list = field(default_factory=list)  # {"name", "support", "texts", "maintainers"}
    patterns: list = field(default_factory=list)    # {"pattern", "support", "texts", "maintainers"}
    spelling_folds: list = field(default_factory=list)  # {"kind", "into", "folded"}
    unlabeled_slots: dict = field(default_factory=dict)
    texts_with_facts: int = 0


def _norm(label: str) -> str:
    return re.sub(r"[^a-z0-9]", "", label.lower())     # digits kept on purpose


def _folding(finals: collections.Counter, kind: str, folds: list) -> dict:
    """{label: its spelling-folded name}: labels equal once case, spacing and
    punctuation are ignored become the most frequent spelling (ties by name)."""
    groups = collections.defaultdict(collections.Counter)
    for label, n in finals.items():
        groups[_norm(label)][label] += n
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
            row["examples"] = [n for n, _ in examples[k].most_common(EXAMPLES)]
        rows.append(row)
    return sorted(rows, key=lambda r: (-r["support"], r[key_name]))


def count_support(facts, labels) -> Counts:
    counts = Counts()
    final = {}
    for kind in ("entities", "predicates"):
        # name -> stage 3 label -> stage 4 merge; then fold spellings.
        merged = {name: labels.merged_into[kind].get(lbl, lbl) for name, lbl in labels.of[kind].items()}
        fold = _folding(collections.Counter(merged.values()),
                        "classes" if kind == "entities" else "predicates", counts.spelling_folds)
        final[kind] = {name: fold[lbl] for name, lbl in merged.items()}

    ids = {k: collections.defaultdict(set) for k in ("class", "predicate", "pattern")}
    maint = {k: collections.defaultdict(set) for k in ("class", "predicate", "pattern")}
    examples = collections.defaultdict(collections.Counter)
    unlabeled = collections.Counter()
    for t in facts.texts:
        if t["triples"]:
            counts.texts_with_facts += 1
        for f in t["triples"]:
            sc = final["entities"].get(f["subject"])
            oc = final["entities"].get(f["object"])
            rel = final["predicates"].get(f["predicate"])
            for slot, label, name, kind in (("subject", sc, f["subject"], "class"),
                                            ("object", oc, f["object"], "class"),
                                            ("predicate", rel, f["predicate"], "predicate")):
                if label is None:
                    unlabeled[slot] += 1
                    continue
                ids[kind][label].add(t["id"])
                maint[kind][label].add(t["maintainer"])
                if kind == "class":
                    examples[label][name] += 1
            if sc and oc and rel:
                ids["pattern"][(sc, rel, oc)].add(t["id"])
                maint["pattern"][(sc, rel, oc)].add(t["maintainer"])

    counts.classes = _entries(ids["class"], maint["class"], "name", examples)
    counts.predicates = _entries(ids["predicate"], maint["predicate"], "name")
    counts.patterns = _entries(ids["pattern"], maint["pattern"], "pattern")
    counts.unlabeled_slots = dict(unlabeled)
    log.info(f"  {len(counts.classes):,} classes, {len(counts.predicates):,} predicates, "
             f"{len(counts.patterns):,} patterns found")
    return counts
