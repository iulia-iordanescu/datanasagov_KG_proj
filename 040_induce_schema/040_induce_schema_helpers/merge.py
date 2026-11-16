"""
merge.py -- stage 4: one last look at all the labels, to merge synonyms.

First, in code, labels that differ only in case, spacing, or punctuation
("Space craft", "Spacecraft") are folded into one, the most frequent
spelling (the one most component instances got; ties alphabetically): a
spelling fold, the second kind of canonicalization. Digits are kept:
"Level2" and "Level3" stay apart. Every fold is listed in
induction_evidence.json (the report shows the first 20) and recorded in the
record of discarded items (common/common_helpers/dropped.py). Folding comes
before the merge call, so the model is never shown two spellings of one label
(it would merge them, or leave them apart, by its own judgment).

Stage 3's running vocabulary prevents most synonymous labels, but a few can
slip through (a label coined early, before its better-known synonym was in
use). So the finished list of labels goes to the model in ONE call per kind
(the labels of subject and object instances, then the labels of predicate
instances), each label with its examples (below; prompts/
merge_entity_classes.txt, merge_predicates.txt). Every
label is seen beside every other, so no pair of synonyms is missed for being
in different batches.

The model lists only the merges it finds, {"into": "Instrument", "labels":
["Sensor", "Detector"]}, not every label, so its reply stays short however
many labels there are.

What code checks in the reply:
  - "into" must be one of the labels sent (the model can't invent a label);
  - a label that wasn't sent is ignored;
  - a label merged into two different labels keeps the first;
  - chains (Sensor -> Detector, Detector -> Instrument) are followed to
    their end, so each label maps straight to its final label.
Every merge is listed in the report, and every ignored item in
induction_evidence.json (the report counts them): a wrong merge (two
different ideas made one) is the one mistake code can't catch, so it must
be visible.

If a list is too long for one call (over MAX_LABELS_ONE_CALL), the step
stops and says so, rather than splitting it into groups where synonyms could
miss each other.

Each component instance's final label (stage 3's label, folded by spelling,
then merged) is what stage 5 (splitting) and stage 6 (counting) read.

How a label is shown to the merge call: an entity class label with the
subject or object instances that most often got it; a predicate label with
up to EXAMPLES triple instances that state it, each written "subject instance
(its entity class) -- predicate instance -- object instance (its entity
class)" (predicate_examples), the most frequent first. The entity classes are
those after this stage's own entity class merge, which runs first (KINDS),
so the model sees them as counting will. Two predicate labels can share
their words ("produced by") and still stand for different relationships
(the instrument measured, the organization processed), which the entity
classes show; the prompt states the verb test, as splitting's does: one verb
for both means one predicate, whatever the entity classes, and the same
words alone are no reason to merge. Stage 5's merging again shows its
predicates the same way, each new predicate with the triple instances it
took, so the parts of one split arrive with different examples.
"""
from __future__ import annotations

import collections
import json
from pathlib import Path

from common import dropped
from common.cache import Cache, ask_cached, needs
from common.audit import log
from common.prompt_files import fill, load
from common.stop import Stop
from common.triples_io import component_class_key
from label import BECOMES, KINDS

PROMPTS_DIR = Path(__file__).resolve().parents[1] / "040_induce_schema_prompts"   # 040_induce_schema/040_induce_schema_prompts/
PROMPTS = {"entity": load(PROMPTS_DIR / "merge_entity_classes.txt"),
           "predicate": load(PROMPTS_DIR / "merge_predicates.txt")}

#: The most labels sent in one call. Each takes a few dozen characters with
#: its example component instances, so this is far below what one call can
#: read; the reply holds only the merges. Above it, the step stops.
MAX_LABELS_ONE_CALL = 800
#: The stage name its discarded items carry (common/common_helpers/dropped.py).
STAGE = "stage 4 (merge_labels)"
#: Why code set a merge of the model's aside, for each of the merge issues' codes.
ISSUE_WHY = {"into_not_a_label": "it merges into a label that wasn't sent",
             "not_sent": "it merges a label that wasn't sent",
             "merged_twice": "it merges a label already merged into another one: the first merge stands",
             "cycle": "it would merge a label into one already merged into it: the first merge stands",
             "not_an_object": "the item isn't a JSON object",
             "labels_not_a_list": "its labels aren't a list",
             "into_itself": "it merges a label into itself",
             "both_seen": "both predicates were there at stage 4, whose merge call judged them already: merging "
                          "again (stage 5) keeps only merges with a new predicate of a predicate split in them"}

#: Example component instances shown for each label.
EXAMPLES = 3


def _final(decided: dict, label: str) -> str:
    """Where a label ends up, following the merges decided (which never form
    a cycle): A merged into B, and B into C, puts A in C."""
    while label in decided:
        label = decided[label]
    return label


#: The shape of a merging answer (the prompts' reply format): a "merges" list. One of another shape is asked again,
#: never kept (common/common_helpers/cache.py, ask_cached).
SHAPE = needs(merges=list)


def merge_labels(labels, triples, calls):
    cache = Cache(calls.cache_dir, "merge")
    before = calls.paid.made
    since = dropped.mark()
    fold_spellings(labels)                    # before the call: the model sees one spelling of each label
    for kind in KINDS:
        folded = labels.folded[kind]
        instances_of = collections.defaultdict(collections.Counter)   # {folded label: Counter of component instances}
        texts_with = collections.defaultdict(set)                     # {folded label: text ids}
        for t in triples.texts:
            for ti in t["triple_instances"]:
                for k2, value in (("entity", ti["subject"]), ("entity", ti["object"]),
                                  ("predicate", ti["predicate"])):
                    if k2 == kind and value in labels.of[kind]:
                        instances_of[folded[labels.of[kind][value]]][value] += 1
                        texts_with[folded[labels.of[kind][value]]].add(t["id"])
            # A text's title is labeled with its describes_class (stage 3): it counts, as in stage 6 (count.py),
            # so a label used only for titles reaches the model with its texts and its titles as examples.
            if kind == "entity" and t.get("describes_class") and t.get("title") in labels.of["entity"]:
                instances_of[folded[labels.of["entity"][t["title"]]]][t["title"]] += 1
                texts_with[folded[labels.of["entity"][t["title"]]]].add(t["id"])
        if kind == "predicate":
            # each predicate label with example triple instances that show its subjects' and objects' entity classes,
            # as merged just above (KINDS: the entity classes first), so the call can apply the verb test
            entity = lambda v: labels.merged_into["entity"].get(labels.folded["entity"].get(  # noqa: E731
                labels.of["entity"].get(v)), labels.folded["entity"].get(labels.of["entity"].get(v)))
            examples, instances_of, texts_with = predicate_examples(
                triples, lambda ti: folded.get(labels.of["predicate"].get(ti["predicate"])), entity)
        sent = sorted(set(folded.values()))
        if len(sent) > MAX_LABELS_ONE_CALL:
            raise Stop(f"{len(sent)} {BECOMES[kind]} labels are more than one call takes "
                       f"({MAX_LABELS_ONE_CALL}), so 040 can't merge them: merging them in separate groups "
                       f"would let synonyms miss each other. Learn from fewer texts (lower "
                       f"`--texts_per_stratum`), then run "
                       f"`py 040_induce_schema/run.py` again; learning from this many would first need the labels "
                       f"grouped by meaning, which isn't built (040_induce_schema/040_induce_schema.md, Known limits).")
        issues = {"into_not_a_label": [], "not_sent": [], "merged_twice": [], "cycle": []}
        mapping = {label: label for label in sent}
        if len(sent) > 1:
            shown = examples if kind == "predicate" else instances_of
            listing = [{"label": lbl, "texts": len(texts_with[lbl]),
                        "examples": [v for v, _ in shown[lbl].most_common(EXAMPLES)]} for lbl in sent]
            mapping, issues = ask_merges(kind, listing, cache, calls, STAGE,
                                         "  040 will ask the model to merge synonymous labels, one call per kind")
        for lbl, final in sorted(mapping.items()):
            if final != lbl:
                labels.merges.append({"kind": BECOMES[kind], "label": lbl, "into": final,
                                      "component_instances": len(instances_of[lbl]),
                                      "texts": len(texts_with[lbl])})
        labels.merged_into[kind] = mapping
        labels.merge_issues[kind] = issues
        merged = sum(1 for m in labels.merges if m["kind"] == BECOMES[kind])
        log.info(f"  {BECOMES[kind]} labels: {merged} of {len(sent)} merged into others")
    labels.merge_calls, labels.merge_reused = calls.paid.made - before, cache.reused
    final_labels(labels)
    _record_folds(labels, since)
    return labels


def example(ti: dict, subject_class, object_class) -> str:
    """A triple instance as a predicate merge listing shows it: "subject instance (Subject class) -- predicate instance
    -- object instance (Object class)"; an instance without an entity class is written without one."""
    s = ti["subject"] + (f" ({subject_class})" if subject_class else "")
    o = ti["object"] + (f" ({object_class})" if object_class else "")
    return f"{s} -- {ti['predicate']} -- {o}"


def predicate_examples(triples, predicate_of, entity_class_of) -> tuple:
    """(examples, instances_of, texts_with), each {predicate label: ...}, for a predicate merge call: Counters of
    example() strings and of predicate instances, and the text ids, over the verified triple instances whose
    predicate_of(triple instance) is a label (entity_class_of(instance): its entity class, or None). Shared by stage 4
    and stage 5's merging again (split.py), so both show a predicate the same way; the examples shown are the most
    frequent, ties in the order the texts were read (Counter.most_common)."""
    examples = collections.defaultdict(collections.Counter)
    instances_of = collections.defaultdict(collections.Counter)
    texts_with = collections.defaultdict(set)
    for t in triples.texts:
        for ti in t["triple_instances"]:
            p = predicate_of(ti)
            if p is None:
                continue
            examples[p][example(ti, entity_class_of(ti["subject"]), entity_class_of(ti["object"]))] += 1
            instances_of[p][ti["predicate"]] += 1
            texts_with[p].add(t["id"])
    return examples, instances_of, texts_with


def ask_merges(kind: str, listing: list, cache, calls, stage: str, plan: str, takes_part=None) -> tuple:
    """(mapping, issues) from one merge call about these labels (listing: [{"label", "texts", "examples"}], every
    label sent): mapping {label: the label it ends in, chains followed}, issues {code: [labels]}. Code checks every
    item of the reply (see above) and sets aside, with why, each one that fails, under the stage given; takes_part(
    label, into), when given, says whether a merge may be kept at all (stage 5's merging again keeps only those with a
    new predicate in them: "both_seen"). Shared by stage 4 and stage 5's merging again (split.py)."""
    issues = {"into_not_a_label": [], "not_sent": [], "merged_twice": [], "cycle": []}
    if takes_part is not None:
        issues["both_seen"] = []
    mapping = {e["label"]: e["label"] for e in listing}
    reply = ask_cached(cache, calls, fill(PROMPTS[kind], labels=json.dumps(listing, ensure_ascii=False, indent=0)),
                       plan, check=SHAPE)
    decided = {}
    for m in reply["merges"]:
        if not isinstance(m, dict):
            _set_aside(kind, "not_an_object", m, stage)
            continue
        into = m.get("into")
        if into not in mapping:
            issues["into_not_a_label"].append(into)
            _set_aside(kind, "into_not_a_label", m, stage)
            continue
        if not isinstance(m.get("labels"), list):
            _set_aside(kind, "labels_not_a_list", m, stage)
        for lbl in m.get("labels") if isinstance(m.get("labels"), list) else []:
            if lbl not in mapping:
                issues["not_sent"].append(lbl)
                _set_aside(kind, "not_sent", {"label": lbl, "into": into}, stage)
            elif lbl == into:
                _set_aside(kind, "into_itself", {"label": lbl, "into": into}, stage)
                continue
            elif takes_part is not None and not takes_part(lbl, into):
                issues["both_seen"].append(lbl)
                _set_aside(kind, "both_seen", {"label": lbl, "into": into}, stage)
            elif lbl in decided and decided[lbl] != into:
                issues["merged_twice"].append(lbl)      # the first merge stands
                _set_aside(kind, "merged_twice", {"label": lbl, "into": into, "stands": decided[lbl]}, stage)
            elif _final(decided, into) == lbl:
                issues["cycle"].append(lbl)             # into already merged into lbl: the first merge stands
                _set_aside(kind, "cycle", {"label": lbl, "into": into}, stage)
            else:
                decided[lbl] = into
    return {label: _final(decided, label) for label in mapping}, issues


def _folding(counted: collections.Counter, kind: str, folds: list) -> dict:
    """{label: its spelling-folded label}: labels equal once case, spacing and
    punctuation are ignored become the most frequent spelling (counted: {label:
    component instances that got it}; ties alphabetically)."""
    groups = collections.defaultdict(collections.Counter)
    for label, n in counted.items():
        groups[component_class_key(label)][label] += n
    out = {}
    for spellings in groups.values():
        into = sorted(spellings.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
        for label in spellings:
            out[label] = into
        if len(spellings) > 1:
            folds.append({"kind": kind, "into": into, "folded": sorted(spellings)})
    return out


def fold_spellings(labels) -> None:
    """labels.folded: {kind: {stage 3's label: its spelling}}, every label of the kind (those component instances got,
    and any other of stage 3's vocabulary, counted as got by none); every fold in labels.spelling_folds."""
    labels.spelling_folds = []
    for kind in KINDS:
        counted = collections.Counter(labels.of[kind].values())
        for lbl in labels.vocabulary.get(kind, []):
            counted[lbl] += 0
        labels.folded[kind] = _folding(counted, BECOMES[kind], labels.spelling_folds)


def final_labels(labels) -> None:
    """Each component instance's final label, labels.final: stage 3's label, folded by spelling (labels.folded),
    then merged (labels.merged_into, over the folded labels)."""
    for kind in KINDS:
        folded = labels.folded.get(kind, {})
        merged = labels.merged_into.get(kind, {})
        labels.final[kind] = {value: merged.get(folded.get(lbl, lbl), folded.get(lbl, lbl))
                              for value, lbl in labels.of[kind].items()}


def _set_aside(kind: str, code: str, merge, stage: str = STAGE) -> None:
    """One entry per merge of the model's reply (or label in it) that code set aside, with why (ISSUE_WHY)."""
    dropped.discard(stage, "merge", f"proposed by the model, set aside: {ISSUE_WHY[code]}",
                    {"kind": BECOMES[kind], "merge": merge})


def _record_folds(labels, since: int) -> None:
    """One entry per label stage 4 folded into another: folded by spelling (a loose match), or, once folded, merged by
    the model's merge; then each kind's accounting check: labels in = labels kept + labels folded."""
    for m in labels.merges:
        dropped.fold(STAGE, "label", "merged by the model into a synonym", {"kind": m["kind"], "label": m["label"],
                     "component_instances": m["component_instances"], "texts": m["texts"]}, {"label": m["into"]})
    for f in labels.spelling_folds:
        for lbl in f["folded"]:
            if lbl != f["into"]:
                dropped.fold(STAGE, "label", "a loose match of another label (spelling fold): the most used "
                             "spelling is kept", {"kind": f["kind"], "label": lbl}, {"label": f["into"]})
    for kind in KINDS:                    # the labels component instances have (stage 3's vocabulary is these)
        used = set(labels.of[kind].values())
        dropped.account(STAGE, f"{BECOMES[kind]} labels", len(used), len(set(labels.final[kind].values())),
                        since=since, only=lambda e, k=BECOMES[kind], u=used: e["item_type"] == "label"
                        and e["item"].get("kind") == k and e["item"].get("label") in u)
