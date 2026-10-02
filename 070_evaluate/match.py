"""
match.py -- stage 3: compare, record by record, what 060 extracted with the
ground truth. Code only, no model.

Each extracted fact is first TRANSLATED into your names (names.py): its
predicate and entity classes; a reversed predicate also swaps subject and
object (and their entity classes). Then, per record, the ground truth's
facts and the extracted facts are PAIRED: every fact, in either list, ends
with zero or one partner, always from the other list (so a fact stated twice
earns one match, not two). Two passes, each finding the largest possible set
of pairs (maximum matching: a pairing may switch to free a partner for
another fact), not just each fact's first match:

  1. exact   subject and object equal once evened out (common/text_match
             norm_text: case, spacing, quote marks, dashes, edge punctuation
             and a leading "the/a/an" ignored), predicate the same name
  2. partial among the facts still unpaired: the same, except that the
             subject (or object) may be CONTAINED in the other one as whole
             words: "MODIS" in "Moderate Resolution Imaging Spectroradiometer
             (MODIS)". It can be fooled ("MODIS" in "MODIS Terra"), which is
             why every partial pair is listed for a person to see.

The "exact" level counts pass 1's pairs; the "partial" level counts both
passes'. At each level a pair is STRICT when both entity classes are also
the same name. A ground truth fact is WITHIN REACH when its predicate and
both its entity classes are something 060's schema could say (some checked
row translates to them); the others no extractor using that schema could
find. The DESCRIBES rows are compared on their entity class only, apart from
the facts, since code writes the rest of them.
"""
from __future__ import annotations

import re

from common.audit import log
from common.text_match import norm_text
from common.triples_io import UNDECIDED, label_key

LEVELS = ("exact", "partial")


def _words(s) -> list:
    return re.findall(r"\w+", norm_text(s))


def _contains(a, b) -> bool:
    """Whether one name holds the other as a run of whole words."""
    wa, wb = _words(a), _words(b)
    if not wa or not wb:
        return False
    short, long_ = (wa, wb) if len(wa) <= len(wb) else (wb, wa)
    return any(long_[i:i + len(short)] == short for i in range(len(long_) - len(short) + 1))


def translate(fact: dict, names) -> dict:
    """The fact in your names. A name whose row says (none) keeps its own
    spelling, marked "no counterpart in your names", so it can never equal
    one of yours."""
    p_mine, flipped = names.predicate.get(label_key(fact["predicate"]), (None, False))
    sc, oc = (names.entity.get(label_key(fact[c])) for c in ("subject_class", "object_class"))
    t = {"subject": fact["subject"], "subject_class": sc or f"{fact['subject_class']} (no counterpart in your names)",
         "predicate": p_mine or f"{fact['predicate']} (no counterpart in your names)",
         "object": fact["object"], "object_class": oc or f"{fact['object_class']} (no counterpart in your names)"}
    if flipped and p_mine:
        t["subject"], t["object"] = t["object"], t["subject"]
        t["subject_class"], t["object_class"] = t["object_class"], t["subject_class"]
    return t


def _same_fact(g: dict, t: dict, level: str) -> bool:
    if label_key(g["predicate"]) != label_key(t["predicate"]):
        return False
    if level == "exact":
        return norm_text(g["subject"]) == norm_text(t["subject"]) and norm_text(g["object"]) == norm_text(t["object"])
    return _contains(g["subject"], t["subject"]) and _contains(g["object"], t["object"])


def _strict(g: dict, t: dict) -> bool:
    return label_key(g["subject_class"]) == label_key(t["subject_class"]) and \
        label_key(g["object_class"]) == label_key(t["object_class"])


def _within_reach(g: dict, names) -> bool:
    return label_key(g["predicate"]) in names.reachable["predicate"] and \
        label_key(g["subject_class"]) in names.reachable["entity class"] and \
        label_key(g["object_class"]) in names.reachable["entity class"]


def _max_pairs(can: dict) -> dict:
    """The largest pairing {gt index: extracted index}, each fact in either
    list with zero or one partner from the other, each gt fact paired with
    one of the extracted facts it matches (can[gi]): the
    standard augmenting-path method (Kuhn's algorithm). Taking each gt
    fact's first free match instead can leave a fact unpaired that another
    pairing would have matched. Deterministic: facts are tried in order."""
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


def compare_record(record: dict, names) -> dict:
    """The record's pairs and counts: record["compared"]."""
    gt = record["gt"]
    ex = [translate(f, names) for f in record["extracted"]]
    pairs = []                                        # (gt index, extracted index, "exact" | "partial")
    free_g, free_e = set(range(len(gt))), set(range(len(ex)))
    for level in LEVELS:
        can = {gi: [ei for ei in sorted(free_e) if _same_fact(gt[gi], ex[ei], level)] for gi in sorted(free_g)}
        for gi, ei in sorted(_max_pairs(can).items()):
            pairs.append((gi, ei, level))
            free_g.discard(gi)
            free_e.discard(ei)
    reach = [_within_reach(g, names) for g in gt]
    counts = {"extracted": len(ex), "gt": len(gt), "within_reach": sum(reach)}
    for level in LEVELS:
        used = [(gi, ei) for gi, ei, lv in pairs if level == "partial" or lv == "exact"]
        counts[f"{level}_matched"] = len(used)
        counts[f"{level}_strict"] = sum(_strict(gt[gi], ex[ei]) for gi, ei in used)
        counts[f"{level}_matched_within_reach"] = sum(reach[gi] for gi, _ in used)

    gd, ed = record["gt_describes"], record["extracted_describes"]
    truth = gd["object_class"] if gd and gd["object_class"] not in ("", UNDECIDED) else None
    said = None
    if ed and ed["object_class"] not in ("", UNDECIDED):
        said = names.entity.get(label_key(ed["object_class"])) or f"{ed['object_class']} (no counterpart in your names)"
    record["compared"] = {
        "translated": ex, "pairs": pairs, "within_reach": reach, "counts": counts,
        "describes": {"truth": truth, "said": said,
                      "right": bool(truth and said and label_key(truth) == label_key(said))},
    }
    return record


def compare_all(scored, names):
    for record in scored.records:
        compare_record(record, names)
    log.info(f"  compared {len(scored.records)} record(s)")
    return scored
