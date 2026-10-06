"""
pairing.py -- stage 3: compare, record by record, what 060 extracted with the
ground truth. Code only, no model.

Each extracted triple is first TRANSLATED into the ground truth vocabulary (component_classes.py): its
predicate and entity classes; a reversed predicate also swaps subject and
object (and their entity classes). Then, per record, the ground truth's
triples and the extracted triples are PAIRED: every triple, in either list, ends
with zero or one partner, always from the other list (so a triple stated twice
earns one pair, not two). Two passes, each finding the largest possible set
of pairs (in maths, a maximum matching: a pair may be swapped to free a
partner for another triple), not just each triple's first possible partner:

  1. exact   subject and object equal once evened out (common/common_helpers/text_match.py
             norm_text: case, spacing, quote marks, dashes, edge punctuation
             and a leading "the/a/an" ignored), predicate the same
  2. partial among the triples still unpaired: the same, except that the
             subject (or object) may be CONTAINED in the other one as whole
             words, either way round: "MODIS" in "Moderate Resolution Imaging
             Spectroradiometer (MODIS)". It can be fooled ("MODIS" in "MODIS
             Terra"), so a person can review partial pairs (annotation tool,
             Partial pairs; common/common_helpers/partial_reviews.py): two triples marked "not
             the same fact" are never paired.

The "exact" level counts pass 1's pairs; the "partial" level counts both
passes'. At each level a pair is STRICT when both entity classes are also
the same. A ground truth triple is WITHIN REACH when its predicate is
something the current schema could say (some checked row translates to it): all a
pair needs, since a pair doesn't need the entity classes to agree. It is
WITHIN STRICT REACH when both its entity classes are too: all a strict pair
needs. The DESCRIBES rows are compared on their entity class only, apart from
the triples, since code writes the rest of them.

COMPONENT CLASS MISMATCHES (component_class_mismatches): a wrong or missing row of the
translation table leaves a trace in the triples. Extraction found the triple,
but a component class differs:
  - a paired triple whose entity class differs from the ground truth's: the
    current schema's entity class may translate to the wrong one (or to (none));
  - an unpaired extracted triple and an unpaired ground truth triple with the
    same subject and object (or the two swapped) but different predicates:
    the predicate's row may be wrong, or its swap_subject_and_object.
Each mismatch (current schema's component class, ground truth vocabulary's
component class) is counted; the frequent ones point at rows to look at. A single
one may just be extraction choosing the wrong component class.
"""
from __future__ import annotations

import re

from common.audit import log
from common.partial_reviews import NOT_SAME, pair_key
from common.text_match import norm_text
from common.triples_io import UNDECIDED, component_class_key

LEVELS = ("exact", "partial")
MISMATCH_WARN = 2                 # a component class mismatch seen this often is a warning: a row to look at


def _words(s) -> list:
    return re.findall(r"\w+", norm_text(s))


def _contains(a, b) -> bool:
    """Whether one subject (or object) instance holds the other as a run of whole words."""
    wa, wb = _words(a), _words(b)
    if not wa or not wb:
        return False
    short, long_ = (wa, wb) if len(wa) <= len(wb) else (wb, wa)
    return any(long_[i:i + len(short)] == short for i in range(len(long_) - len(short) + 1))


NO_TRANSLATION = " (current schema; translates to (none))"


def translate(triple: dict, translation) -> dict:
    """The triple in the ground truth vocabulary. A component class whose row
    says (none) keeps its own spelling, marked NO_TRANSLATION, so it can never
    equal a component class of the ground truth vocabulary. "crt" keeps the
    current schema's component classes, slot by slot as translated (swapped along with subject and
    object), for component_class_mismatches."""
    p_mine, flipped = translation.predicate.get(component_class_key(triple["predicate"]), (None, False))
    sc, oc = (translation.entity.get(component_class_key(triple[c])) for c in ("subject_class", "object_class"))
    t = {"subject": triple["subject"], "subject_class": sc or f"{triple['subject_class']}{NO_TRANSLATION}",
         "predicate": p_mine or f"{triple['predicate']}{NO_TRANSLATION}",
         "object": triple["object"], "object_class": oc or f"{triple['object_class']}{NO_TRANSLATION}",
         "crt": {"subject_class": triple["subject_class"], "predicate": triple["predicate"],
                 "object_class": triple["object_class"]}}
    if flipped and p_mine:
        t["subject"], t["object"] = t["object"], t["subject"]
        t["subject_class"], t["object_class"] = t["object_class"], t["subject_class"]
        t["crt"]["subject_class"], t["crt"]["object_class"] = t["crt"]["object_class"], t["crt"]["subject_class"]
    return t


def _can_pair(g: dict, t: dict, level: str) -> bool:
    if component_class_key(g["predicate"]) != component_class_key(t["predicate"]):
        return False
    if level == "exact":
        return norm_text(g["subject"]) == norm_text(t["subject"]) and norm_text(g["object"]) == norm_text(t["object"])
    return _contains(g["subject"], t["subject"]) and _contains(g["object"], t["object"])


def classes_agree(g: dict, t: dict) -> bool:
    """Both triples name the same entity classes (what "strict" counts)."""
    return component_class_key(g["subject_class"]) == component_class_key(t["subject_class"]) and \
        component_class_key(g["object_class"]) == component_class_key(t["object_class"])


def _within_reach(g: dict, translation) -> bool:
    """Its predicate is something the current schema could say: all a pair needs
    (a pair doesn't need the entity classes to agree)."""
    return component_class_key(g["predicate"]) in translation.reachable["predicate"]


def _within_strict_reach(g: dict, translation) -> bool:
    """Its predicate and both its entity classes are: all a strict pair needs."""
    return _within_reach(g, translation) and component_class_key(g["subject_class"]) in translation.reachable["entity class"] and \
        component_class_key(g["object_class"]) in translation.reachable["entity class"]


def _max_pairs(can: dict) -> dict:
    """The largest pairing {gt index: extracted index}, each triple in either
    list with zero or one partner from the other, each gt triple paired with
    one of the extracted triples it can pair with (can[gi]): the standard
    augmenting-path method (Kuhn's algorithm). Taking each gt triple's first
    free partner instead can leave a triple unpaired that another choice of
    pairs would have paired. Deterministic: triples are tried in order."""
    owner = {}                                        # extracted index -> gt index

    def place(gi, seen) -> bool:
        for ei in can[gi]:
            if ei in seen:
                continue
            seen.add(ei)
            if ei not in owner or place(owner[ei], seen):
                owner[ei] = gi
                return True
        return False

    for gi in can:
        place(gi, set())
    return {gi: ei for ei, gi in owner.items()}


def compare_record(record: dict, translation, reviews: dict | None = None) -> dict:
    """The record's pairs and counts: record["compared"]. reviews: a person's
    verdicts on partial pairs ({pair_key: verdict}); a pair marked "not the
    same fact" is never made."""
    reviews = reviews or {}
    gt = record["gt"]
    ex = [translate(f, translation) for f in record["extracted"]]

    def allowed(gi, ei) -> bool:
        return reviews.get(pair_key(record["id"], gt[gi], ex[ei])) != NOT_SAME

    pairs = []                                        # (gt index, extracted index, "exact" | "partial")
    free_g, free_e = set(range(len(gt))), set(range(len(ex)))
    for level in LEVELS:
        can = {gi: [ei for ei in sorted(free_e) if _can_pair(gt[gi], ex[ei], level) and allowed(gi, ei)]
               for gi in sorted(free_g)}
        for gi, ei in sorted(_max_pairs(can).items()):
            pairs.append((gi, ei, level))
            free_g.discard(gi)
            free_e.discard(ei)
    reach = [_within_reach(g, translation) for g in gt]
    strict_reach = [_within_strict_reach(g, translation) for g in gt]
    counts = {"extracted": len(ex), "gt": len(gt), "within_reach": sum(reach),
              "within_strict_reach": sum(strict_reach)}
    for level in LEVELS:
        used = [(gi, ei) for gi, ei, lv in pairs if level == "partial" or lv == "exact"]
        counts[f"{level}_pairs"] = len(used)
        strict = [(gi, ei) for gi, ei in used if classes_agree(gt[gi], ex[ei])]
        counts[f"{level}_strict_pairs"] = len(strict)
        counts[f"{level}_pairs_within_reach"] = sum(reach[gi] for gi, _ in used)
        counts[f"{level}_strict_pairs_within_strict_reach"] = sum(strict_reach[gi] for gi, _ in strict)

    gd, ed = record["gt_describes"], record["extracted_describes"]
    truth = gd["object_class"] if gd and gd["object_class"] not in ("", UNDECIDED) else None
    said = None
    if ed and ed["object_class"] not in ("", UNDECIDED):
        said = translation.entity.get(component_class_key(ed["object_class"])) or f"{ed['object_class']}{NO_TRANSLATION}"
    rejected = sum(1 for gi in range(len(gt)) for ei in range(len(ex))
                   if not allowed(gi, ei) and _can_pair(gt[gi], ex[ei], "partial"))
    unreviewed = sum(1 for gi, ei, lv in pairs
                     if lv == "partial" and pair_key(record["id"], gt[gi], ex[ei]) not in reviews)
    record["compared"] = {
        "translated": ex, "pairs": pairs, "within_reach": reach, "within_strict_reach": strict_reach, "counts": counts,
        "partial_review": {"rejected": rejected, "unreviewed": unreviewed},
        "describes": {"truth": truth, "said": said,
                      "right": bool(truth and said and component_class_key(truth) == component_class_key(said))},
    }
    return record


def component_class_mismatches(records: list) -> list:
    """Traces of wrong or missing translations in compared records (see the
    module docstring): [{"kind", "crt_class", "translated_to", "gtt_class",
    "count", "swapped"}], most frequent first. translated_to is the
    current schema's component class after translation (marked NO_TRANSLATION if its
    row says (none)); swapped: predicate mismatches where subject and object are
    the other way round."""
    found = {}

    def add(kind, crt_class, translated_to, gtt_class, swapped=False):
        key = (kind, crt_class, translated_to, gtt_class, swapped)
        found[key] = found.get(key, 0) + 1

    for rec in records:
        c = rec["compared"]
        gt, ex = rec["gt"], c["translated"]
        for gi, ei, _ in c["pairs"]:
            for slot in ("subject_class", "object_class"):
                if component_class_key(gt[gi][slot]) != component_class_key(ex[ei][slot]):
                    add("entity class", ex[ei]["crt"][slot], ex[ei][slot], gt[gi][slot])
        paired_g = {gi for gi, _, _ in c["pairs"]}
        paired_e = {ei for _, ei, _ in c["pairs"]}
        for gi, g in enumerate(gt):
            if gi in paired_g:
                continue
            for ei, t in enumerate(ex):
                if ei in paired_e:
                    continue
                same = norm_text(g["subject"]) == norm_text(t["subject"]) and \
                    norm_text(g["object"]) == norm_text(t["object"])
                swapped = norm_text(g["subject"]) == norm_text(t["object"]) and \
                    norm_text(g["object"]) == norm_text(t["subject"])
                if same or swapped:
                    add("predicate", t["crt"]["predicate"], t["predicate"], g["predicate"], swapped and not same)
                    break                             # one mismatch per ground truth triple
    return [{"kind": k, "crt_class": c, "translated_to": t, "gtt_class": g, "swapped": s, "count": n}
            for (k, c, t, g, s), n in sorted(found.items(), key=lambda kv: (-kv[1], kv[0]))]


def compare_all(evaluated, translation):
    for record in evaluated.records:
        compare_record(record, translation, evaluated.reviews)
    log.info(f"  compared {len(evaluated.records)} record(s)")
    return evaluated
