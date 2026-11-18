"""
count.py -- stage 6 (counting): the evidence behind every schema entry found.
Code only, no model.

Each verified triple instance becomes, through the final labels of its
component instances (stage 3's labels, folded by spelling and merged in
stage 4) and stage 5 (a predicate split by its subject's or object's entity
class, or both, becomes, for a triple instance in a group the split took, the
split's new predicate; then the predicate merging again made of it):

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
style, so both are kept. Entity classes and predicates also keep EXAMPLES
examples (representative()): one from each of the schema entry's patterns
found in the most texts, each from another text and, where possible, another
maintainer, so near-duplicate texts don't fill the examples with one wording.

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

from common import dropped
from common.audit import log

#: Examples kept per entity class (its component instances) and per predicate (its triple instances, "subject --
#: predicate -- object": a predicate's examples need its subject and object, since the definition says what they
#: are), chosen by representative().
EXAMPLES = 5
#: The stage name its discarded items carry (common/common_helpers/dropped.py).
STAGE = "stage 6 (count_support)"
#: The group of a text's title among an entity class's examples (representative()): a title is in no pattern.
TITLE_GROUP = ("title",)


def representative(candidates, n: int) -> list:
    """Up to n distinct examples that show a schema entry's range rather than its most repeated wording.
    candidates: (group, example, text id, maintainer) for every occurrence; a group is what the example shows the
    schema entry in (a pattern, or the title of a text). The groups are taken in turn, the one found in the most texts
    first (ties by the group written as text), one example from each per round, so the most supported groups each show
    one before any shows a second; within a round, the groups with an example from a text not yet shown come first.
    Within a group, an example from a new text by a new maintainer comes first,
    then the example found in the most texts (ties alphabetically). Each example is shown once, credited to the
    occurrence that brings the newest text and maintainer. Deterministic: the order of the candidates doesn't matter.
    So near-duplicate texts, which repeat one wording, give one example, not all of them."""
    texts_of = collections.defaultdict(set)                  # {group: texts}
    seen = collections.defaultdict(lambda: collections.defaultdict(set))   # {group: {example: {(text, maintainer)}}}
    for group, ex, text, maintainer in candidates:
        texts_of[group].add(text)
        seen[group][ex].add((text, maintainer))
    rank = {g: i for i, g in enumerate(sorted(texts_of, key=lambda g: (-len(texts_of[g]), str(g))))}
    left = {g: sorted(exs, key=lambda e: (-len({t for t, _ in exs[e]}), e)) for g, exs in seen.items()}
    shown, used_texts, used_maintainers, picks = [], set(), set(), collections.Counter()
    while len(shown) < n:
        best = None
        for g, exs in left.items():
            for i, ex in enumerate(exs):
                if ex in shown:
                    continue
                occ = seen[g][ex]
                new_text = any(t not in used_texts for t, _ in occ)
                new_both = any(t not in used_texts and m not in used_maintainers for t, m in occ)
                key = (picks[g], not new_text, rank[g], not new_both, i)
                if best is None or key < best[0]:
                    best = (key, g, ex)
        if best is None:
            break
        _, g, ex = best
        occ = sorted(seen[g][ex], key=lambda tm: (tm[0] in used_texts, tm[1] in used_maintainers, tm))
        used_texts.add(occ[0][0])
        used_maintainers.add(occ[0][1])
        picks[g] += 1
        shown.append(ex)
    return shown


@dataclass
class Counts:
    entity_classes: list = field(default_factory=list)  # {"component_class", "support", "texts", "maintainers", "examples"}
    predicates: list = field(default_factory=list)      # {"component_class", "support", "texts", "maintainers", "examples"}
    patterns: list = field(default_factory=list)        # {"pattern", "support", "texts", "maintainers"}
    unlabeled_slots: dict = field(default_factory=dict) # {slot: component instances without a label}
    pattern_of: dict = field(default_factory=dict)      # {text id: [each verified triple instance's pattern
                                                        #  (subject class, predicate, object class), or None]}
    pinned: dict = field(default_factory=dict)          # {predicate: [(subject class or "any", object class or
                                                        #  "any")]}: the pins of stage 5's predicates counted
    texts_with_triple_instances: int = 0
    texts_with_describes_class: int = 0             # texts whose title got a describes_class


def _entries(ids: dict, maintainers: dict, key_name: str, examples: dict | None = None) -> list:
    rows = []
    for k, texts in ids.items():
        row = {key_name: list(k) if key_name == "pattern" else k, "support": len(texts),
               "texts": sorted(texts), "maintainers": sorted(maintainers[k])}
        if examples is not None:
            row["examples"] = representative(examples[k], EXAMPLES)
        rows.append(row)
    return sorted(rows, key=lambda r: (-r["support"], r[key_name]))


def count_support(triples, labels, splits) -> Counts:
    counts = Counts()
    final = labels.final                          # stage 3's labels, merged and folded by spelling (stage 4)

    ids = {k: collections.defaultdict(set) for k in ("entity class", "predicate", "pattern")}
    maint = {k: collections.defaultdict(set) for k in ("entity class", "predicate", "pattern")}
    # {entry: {schema entry: [(group, example, text id, maintainer)]}}, for representative(): an example's group is
    # the pattern of its triple instance (with None for a component instance without a label), or a text's title
    examples = {"entity class": collections.defaultdict(list), "predicate": collections.defaultdict(list)}
    unlabeled = collections.Counter()
    since, n_in, with_pattern = dropped.mark(), 0, 0
    for t in triples.texts:
        if t["triple_instances"]:
            counts.texts_with_triple_instances += 1
        counts.pattern_of[t["id"]] = []
        for ti in t["triple_instances"]:
            sc = final["entity"].get(ti["subject"])
            oc = final["entity"].get(ti["object"])
            p = splits.predicate(final["predicate"].get(ti["predicate"]), sc, oc)   # stage 5's split, if any
            for slot, label, value, entry in (("subject", sc, ti["subject"], "entity class"),
                                              ("object", oc, ti["object"], "entity class"),
                                              ("predicate", p, ti["predicate"], "predicate")):
                if label is None:
                    unlabeled[slot] += 1
                    continue
                ids[entry][label].add(t["id"])
                maint[entry][label].add(t["maintainer"])
                examples[entry][label].append(((sc, p, oc), value if entry == "entity class" else
                                               f"{ti['subject']} -- {ti['predicate']} -- {ti['object']}",
                                               t["id"], t["maintainer"]))
            counts.pattern_of[t["id"]].append((sc, p, oc) if sc and oc and p else None)
            n_in += 1
            if not (sc and oc and p):
                no_label = [slot for slot, label in (("subject", sc), ("predicate", p), ("object", oc)) if not label]
                dropped.discard(STAGE, "triple instance", "no pattern: its " + " and ".join(no_label)
                                + " instance has no label, so it supports no pattern", ti, record_id=t["id"])
            else:
                with_pattern += 1
            if sc and oc and p:
                ids["pattern"][(sc, p, oc)].add(t["id"])
                maint["pattern"][(sc, p, oc)].add(t["maintainer"])
        described = final["entity"].get(t.get("title")) if t.get("describes_class") else None
        if t.get("describes_class") and not described:
            dropped.discard(STAGE, "component instance", "a title whose describes class has no final label, so it "
                            "supports no entity class", {"title": t.get("title"),
                                                         "describes_class": t["describes_class"]}, record_id=t["id"])
        if described:
            counts.texts_with_describes_class += 1
            ids["entity class"][described].add(t["id"])
            maint["entity class"][described].add(t["maintainer"])
            examples["entity class"][described].append((TITLE_GROUP, t["title"], t["id"], t["maintainer"]))

    dropped.account(STAGE, "verified triple instances", n_in, with_pattern, since=since, item_type="triple instance")
    counts.entity_classes = _entries(ids["entity class"], maint["entity class"], "component_class",
                                     examples["entity class"])
    counts.predicates = _entries(ids["predicate"], maint["predicate"], "component_class", examples["predicate"])
    counts.patterns = _entries(ids["pattern"], maint["pattern"], "pattern")
    counts.unlabeled_slots = dict(unlabeled)
    counts.pinned = {p: list(pins) for p, pins in splits.pinned.items() if p in ids["predicate"]}
    log.info(f"  found {len(counts.entity_classes):,} entity classes, {len(counts.predicates):,} "
             f"predicates, {len(counts.patterns):,} patterns")
    return counts
