"""
label.py -- stage 3: give every component instance a label, with a running
vocabulary.

A label is the general word for a component instance: for a subject
or object instance, the type of thing it is ("MODIS" → `Instrument`), which
becomes an entity class; for a predicate instance, the relationship it
expresses ("is aboard" → `ABOARD`), which becomes a predicate. The two kinds
are labeled in two separate passes, each with its own running vocabulary.

The component instances are sent in batches of LABEL_BATCH, and every batch
is shown the labels chosen so far, with the instruction to reuse one whenever
it fits and coin a new one only when none does. So one idea doesn't end up
under several labels just because its component instances were in different
batches (`Instrument` in one, `Sensor` in another). The most common
component instances (found in the most texts) go first, so the main labels
are set early and later batches reuse them.

Each component instance is judged by one usage example, the shortest
triple instance it appears in, sent with that triple instance's source text
(the passage of the record that states it, which stage 2 keeps). A triple
instance alone may not say what a thing is: "Dawn" -- "carries" -- "GRaND"
fits a mission and a spacecraft, while its source text, "the GRaND
instrument aboard the Dawn spacecraft", says which. The idea is TRACE-KG's
(Abolhasani, Ba, He & Pan, "Traceable Context-Enriched Knowledge Graph
Generation with Induced Schemas", arXiv:2604.03496v3), whose prompt for
entity classes gives the model context for each thing as its "PRIMARY
evidence for meaning" (TKG_Prompts.py, line 419); there the context is the
model's own words, here the record's. Predicate instances are sent the same
way, so both kinds are judged alike. One the model leaves unlabeled is asked
once more; if it is still unlabeled it is listed, and it counts toward no
schema entry.

A text's title is not sent: its label is the describes_class stage 2 got
for it, judged from the whole text. Those labels also start the running
vocabulary of entity class labels (most common first), so other component instances reuse them.

The running vocabulary shows one spelling of each label: a new label that
differs from one already in it only in case, spacing or punctuation
(common/common_helpers/triples_io.component_class_key: "Space craft" and
"Spacecraft") isn't added to it again, so later batches are never shown two
spellings of one label. The component instances keep the label the model gave;
stage 4 folds the spellings, by its rule (the most frequent wins), and records
each fold.

Each batch's answer is cached under a key that includes the labels in use
before it, so a rerun reuses every batch whose component instances and
preceding labels are unchanged.

Adapted from conceptualize() in archive/to_be_reshaped/best_induce_schema.py, whose
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

from common import dropped
from common.cache import Cache, ask_cached, ask_split, needs
from common.audit import log
from common.prompt_files import fill, load
from common.triples_io import component_class_key

#: The two kinds of component instance, by slot: "entity" for subject and
#: object slots (labeled with entity classes), "predicate" for the predicate
#: slot (labeled with predicates).
KINDS = ("entity", "predicate")
#: What each kind of label becomes: the labels of subject and object instances
#: are entity classes; those of predicate component instances are predicates.
BECOMES = {"entity": "entity class", "predicate": "predicate"}

PROMPTS_DIR = Path(__file__).resolve().parents[1] / "040_induce_schema_prompts"   # 040_induce_schema/040_induce_schema_prompts/
PROMPTS = {"entity": load(PROMPTS_DIR / "label_entity_instances.txt"),
           "predicate": load(PROMPTS_DIR / "label_predicate_instances.txt")}

#: Component instances per call. A batch's reply lists every component
#: instance it was sent, so this bounds the reply's length.
LABEL_BATCH = 80
#: The stage name its discarded items carry (common/common_helpers/dropped.py).
STAGE = "stage 3 (label_component_instances)"


@dataclass
class Labels:
    of: dict = field(default_factory=dict)          # {"entity": {component instance: label}, "predicate": {...}}
    vocabulary: dict = field(default_factory=dict)  # {"entity": [labels, in order of first use], ...}
    unlabeled: dict = field(default_factory=dict)   # {"entity": [component instances], ...}
    refused: dict = field(default_factory=dict)     # {"entity": [{"component_instance", "why"}], ...}: the service
                                                    # wouldn't label them (e.g. its content filter); also unlabeled
    batches: list = field(default_factory=list)     # {"kind", "component_instances", "new_labels", "reused"}
    merged_into: dict = field(default_factory=dict) # filled by stage 4: {"entity": {label: label merged into}, ...}
    merges: list = field(default_factory=list)      # filled by stage 4
    spelling_folds: list = field(default_factory=list)  # filled by stage 4: {"kind", "into", "folded"}
    folded: dict = field(default_factory=dict)      # filled by stage 4: {"entity": {stage 3's label: its spelling},
                                                    #  "predicate": {...}}, before the merge call
    final: dict = field(default_factory=dict)       # filled by stage 4: {"entity": {component instance: its label,
                                                    #  folded by spelling, then merged}, "predicate": {...}}
    merge_issues: dict = field(default_factory=dict)
    calls: int = 0                                  # model calls made by stage 3
    reused: int = 0                                 # stage 3's batches answered from the cache
    merge_calls: int = 0                            # model calls made by stage 4
    merge_reused: int = 0                           # stage 4's calls answered from the cache


def component_instances(triples) -> dict:
    """{kind: {component instance: (ids of the texts it appears in, what the model is shown: {"example": its
    shortest usage example, "source_text": that triple instance's source text})}}, from the verified triple
    instances. Of usage examples of one length, the first in the order the texts are read is kept."""
    found = {kind: {} for kind in KINDS}
    for t in triples.texts:
        for ti in t["triple_instances"]:
            usage = f"{ti['subject']} -- {ti['predicate']} -- {ti['object']}"
            for kind, value in (("entity", ti["subject"]), ("entity", ti["object"]),
                                ("predicate", ti["predicate"])):
                ids, shown = found[kind].get(value, (set(), None))
                ids.add(t["id"])
                if shown is None or len(usage) < len(shown["example"]):
                    shown = {"example": usage, "source_text": ti.get("source_text", "")}
                found[kind][value] = (ids, shown)
    return found


def one_spelling(vocabulary: list, labels) -> list:
    """The labels to add to the running vocabulary: each of labels, in order, unless it, or another spelling of it
    (component_class_key), is already in the vocabulary or earlier among labels."""
    have = {component_class_key(v) for v in vocabulary}
    out = []
    for lbl in labels:
        if component_class_key(lbl) not in have:
            have.add(component_class_key(lbl))
            out.append(lbl)
    return out


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


def _unused_answers(sent: list, reply) -> list:
    """[(key, value, why)] for every key of a labeling reply _match took no label from: a component instance that
    wasn't sent, a label that isn't non-empty text, or a key whose case- and spacing-folded form another key gave
    first. The same matching as _match."""
    reply = reply if isinstance(reply, dict) else {}
    loose_first = {}
    for k, v in reply.items():
        if isinstance(v, str) and v.strip():
            loose_first.setdefault(_loose(k), k)
    used = set()
    for value in sent:
        v = reply.get(value)
        if isinstance(v, str) and v.strip():
            used.add(value)
        elif _loose(value) in loose_first:
            used.add(loose_first[_loose(value)])
    sent_loose = {_loose(v) for v in sent}
    out = []
    for k, v in reply.items():
        if k in used:
            continue
        why = ("a label that isn't non-empty text" if not (isinstance(v, str) and v.strip()) else
               "a component instance that wasn't sent in this call" if _loose(k) not in sent_loose else
               "the same component instance once case and spacing are folded as another key, whose label was taken")
        out.append((k, v, why))
    return out


def _record_unused(kind: str, sent: list, reply) -> None:
    """One entry per key of a labeling reply that gave no label (_unused_answers)."""
    for key, value, why in _unused_answers(sent, reply):
        dropped.discard(STAGE, "label", f"in the model's reply, but not taken: {why}",
                        {"kind": BECOMES[kind], "component_instance": key, "label": value})


def _record_labels(kind: str, found: dict, titles: dict, labels: dict, unlabeled: list, refused: list,
                   since: int, triples) -> None:
    """One entry per component instance stage 3 left unlabeled (refused, or unlabeled after the second ask) and per
    title whose describes class another text with the same title replaced; then the kind's accounting check."""
    why_refused = dict(refused)
    for value in unlabeled:
        texts = sorted(found[kind][value][0]) if value in found[kind] else []
        reason = (f"refused by the model's service: {why_refused[value]}" if value in why_refused else
                  "left unlabeled: no label in the reply, even when asked again")
        dropped.discard(STAGE, "component instance", reason, {"kind": BECOMES[kind], "component_instance": value,
                                                              "texts": texts})
    if kind == "entity":
        for t in triples.texts:
            title, named = t.get("title"), t.get("describes_class")
            if title and named and titles.get(title) != named:
                dropped.replace(STAGE, "label", "another text with the same title named another describes class, "
                                "and the last text's is the title's label", {"title": title, "describes_class": named},
                                {"label": titles.get(title)}, record_id=t["id"])
    n_in = len(set(found[kind]) | set(titles))
    dropped.account(STAGE, f"{BECOMES[kind]} component instances", n_in, len(labels), since=since,
                    item_type="component instance")


#: The shape of a labeling answer (the prompts' reply format): a "labels" object. One of another shape is asked again,
#: never kept (common/common_helpers/cache.py, ask_cached).
SHAPE = needs(labels=dict)


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
        since, titles = dropped.mark(), {}
        if kind == "entity":
            labels = titles_labeled(triples)
            titles = dict(labels)
            counted = collections.Counter(labels.values())
            vocabulary = one_spelling([], sorted(counted, key=lambda lbl: (-counted[lbl], lbl)))
        order = sorted((v for v in found[kind] if v not in labels),
                       key=lambda v: (-len(found[kind][v][0]), v))

        def ask(items: dict) -> dict:
            """The labels for one batch: from the cache, else from the model."""
            reply = ask_cached(cache, calls, fill(prompt, vocabulary=json.dumps(vocabulary, ensure_ascii=False),
                                                  items=json.dumps(items, ensure_ascii=False, indent=0)),
                               f"  040 will ask the model to label component instances, {LABEL_BATCH} per call",
                               check=SHAPE)
            return reply["labels"]

        refused = []
        for start in range(0, len(order), LABEL_BATCH):
            batch = order[start:start + LABEL_BATCH]
            items = {value: found[kind][value][1] for value in batch}
            # A batch the service refuses is asked in halves; component instances it still refuses alone stay
            # unlabeled, with the reason (common.cache.ask_split).
            answers = {}
            for reply in ask_split(lambda values: ask({v: items[v] for v in values}), batch, refused):
                answers.update(reply)
            got, missing = _match(batch, answers)
            _record_unused(kind, batch, answers)
            missing = [v for v in missing if v not in {r for r, _ in refused}]
            if missing:
                # One more try for those left out, with the running vocabulary as it is now.
                again = {}
                for reply in ask_split(lambda values: ask({v: items[v] for v in values}), missing, refused):
                    again.update(reply)
                asked_again = missing
                more, missing = _match(missing, again)
                _record_unused(kind, asked_again, again)
                got.update(more)
                missing = [v for v in missing if v not in {r for r, _ in refused}]
            new = one_spelling(vocabulary, got.values())
            vocabulary += new
            labels.update(got)
            unlabeled += missing
            result.batches.append({"kind": BECOMES[kind], "component_instances": len(batch), "new_labels": new,
                                   "reused": len(set(got.values())) - len(new)})
        unlabeled += [v for v, _ in refused]
        result.refused[kind] = [{"component_instance": v, "why": why} for v, why in refused]
        result.of[kind], result.vocabulary[kind], result.unlabeled[kind] = labels, vocabulary, unlabeled
        _record_labels(kind, found, titles, labels, unlabeled, refused, since, triples)
        log.info(f"  {kind} component instances: {len(labels):,} labeled with {len(vocabulary):,} labels"
                 + (f"; {len(unlabeled)} left unlabeled" if unlabeled else ""))
    result.calls, result.reused = calls.paid.made - before, cache.reused
    return result
