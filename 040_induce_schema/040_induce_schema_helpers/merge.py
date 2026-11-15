"""
merge.py -- stage 4: one last look at all the labels, to merge synonyms.

Stage 3's running vocabulary prevents most synonymous labels, but a few can
slip through (a label coined early, before its better-known synonym was in
use). So the finished list of labels goes to the model in ONE call per kind
(the labels of subject and object instances, then the labels of predicate
instances), each label with the component instances that most
often got it (prompts/merge_entity_classes.txt, merge_predicates.txt). Every
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

Then, in code, labels that differ only in case, spacing, or punctuation
("Space craft", "Spacecraft") are folded into one, the most frequent
spelling (a spelling fold, the second kind of canonicalization). Digits are
kept: "Level2" and "Level3" stay apart. Every fold is listed in
induction_evidence.json (the report shows the first 20). Each component
instance's final label (stage 3's label, merged, then folded) is what stage 5
(splitting) and stage 6 (counting) read.
"""
from __future__ import annotations

import collections
import json
from pathlib import Path

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
    for kind in KINDS:
        instances_of = collections.defaultdict(collections.Counter)   # {label: Counter of component instances}
        texts_with = collections.defaultdict(set)                     # {label: text ids}
        for t in triples.texts:
            for ti in t["triple_instances"]:
                for k2, value in (("entity", ti["subject"]), ("entity", ti["object"]),
                                  ("predicate", ti["predicate"])):
                    if k2 == kind and value in labels.of[kind]:
                        instances_of[labels.of[kind][value]][value] += 1
                        texts_with[labels.of[kind][value]].add(t["id"])
            # A text's title is labeled with its describes_class (stage 3): it counts, as in stage 6 (count.py),
            # so a label used only for titles reaches the model with its texts and its titles as examples.
            if kind == "entity" and t.get("describes_class") and t.get("title") in labels.of["entity"]:
                instances_of[labels.of["entity"][t["title"]]][t["title"]] += 1
                texts_with[labels.of["entity"][t["title"]]].add(t["id"])
        sent = sorted(labels.vocabulary[kind])
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
            listing = [{"label": lbl, "texts": len(texts_with[lbl]),
                        "examples": [v for v, _ in instances_of[lbl].most_common(EXAMPLES)]} for lbl in sent]
            reply = ask_cached(cache, calls, fill(PROMPTS[kind], labels=json.dumps(listing, ensure_ascii=False, indent=0)),
                               "  040 will ask the model to merge synonymous labels, one call per kind", check=SHAPE)
            decided = {}
            for m in reply["merges"]:
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
                    elif _final(decided, into) == lbl:
                        issues["cycle"].append(lbl)             # into already merged into lbl: the first merge stands
                    else:
                        decided[lbl] = into
            mapping = {label: _final(decided, label) for label in mapping}
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
    fold_spellings(labels)
    return labels


def _folding(finals: collections.Counter, kind: str, folds: list) -> dict:
    """{label: its spelling-folded label}: labels equal once case, spacing and
    punctuation are ignored become the most frequent spelling (ties
    alphabetically)."""
    groups = collections.defaultdict(collections.Counter)
    for label, n in finals.items():
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
    """Each component instance's final label, labels.final: stage 3's label, then stage 4's merge, then the
    spelling fold; every fold in labels.spelling_folds."""
    labels.spelling_folds = []
    for kind in KINDS:
        merged = {value: labels.merged_into.get(kind, {}).get(lbl, lbl) for value, lbl in labels.of[kind].items()}
        fold = _folding(collections.Counter(merged.values()), BECOMES[kind], labels.spelling_folds)
        labels.final[kind] = {value: fold[lbl] for value, lbl in merged.items()}
