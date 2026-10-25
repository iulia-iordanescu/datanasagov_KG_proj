"""
pairing.py -- stage 3: compare, record by record, what 060 extracted with the
ground truth. Code only, no model.

Each extracted triple is first TRANSLATED into the ground truth schema (component_classes.py): its
predicate and entity classes; a reversed predicate also swaps subject and
object (and their entity classes). Then, per record, the ground truth's
triples and the extracted triples are PAIRED: every triple, in either list, ends
with zero or one partner, always from the other list (so a triple stated twice
earns one pair, not two). Two passes, each finding the largest possible set
of pairs (in math, a maximum matching: a pair may be swapped to free a
partner for another triple), not just each triple's first possible partner,
and among the largest sets, one with the most strict pairs:

  1. exact   subject and object equal once evened out (common/common_helpers/text_match.py
             norm_text: case, spacing, quote marks, dashes, edge punctuation,
             a leading "the/a/an", and the space between a number and its
             unit ignored, so "500m" is "500 m"), predicate the same
  2. partial among the triples still unpaired: the same, except that the
             subject (or object) may be CONTAINED in the other one as whole
             words, the extracted one in the ground truth one or the
             ground truth one in the extracted one: "MODIS" in "Moderate
             Resolution Imaging Spectroradiometer (MODIS)". It can be fooled ("MODIS" in "MODIS
             Terra"), so a person can review partial pairs (annotation tool,
             Partial pairs; common/common_helpers/partial_reviews.py): two triples marked "not
             the same fact" are never paired.

A SYMMETRIC predicate of the ground truth schema (SYMMETRIC_PREDICATES:
ALSO_KNOWN_AS, "is the same thing under another name") says the same fact
either way round, so for it both passes also try the occurrence with its
subject and object swapped (and its subject class and object class with them):
a pair "matched with subject and object swapped" (record["compared"]["swapped"]).
Strictness then compares the swapped entity classes. Every other predicate
pairs only as written.

The "exact" level counts pass 1's pairs; the "partial" level counts both
passes'. At each level a pair is STRICT when both entity classes are also
the same. A ground truth triple is WITHIN REACH when its predicate is
something the current schema could say (some checked row translates to it): all a
pair needs, since a pair doesn't need the entity classes to agree. It is
WITHIN STRICT REACH when both its entity classes are too: all a strict pair
needs. The describes triples are compared on their entity class only, apart from
the triples, since code writes the rest of them.

COMPONENT CLASS MISMATCHES (component_class_mismatches): a wrong or missing row of the
translation table leaves a trace in the triples. Extraction stated the fact,
but a component class differs:
  - a paired triple whose entity class differs from the ground truth's: the
    current schema's entity class may translate to the wrong one (or to (none));
  - an extracted only occurrence and a ground truth only triple with the
    same subject and object (or the two swapped) but different predicates:
    the predicate's row may be wrong, or its swap_subject_and_object.
Each mismatch (current schema's component class, ground truth schema's
component class) is counted; the frequent ones point at rows to look at. A single
one may just be extraction choosing the wrong component class.
"""
from __future__ import annotations

import collections
import re

from common.audit import log
from common.partial_reviews import NOT_SAME, pair_key
from common.text_match import norm_text
from common.triples_io import UNDECIDED, component_class_key

LEVELS = ("exact", "partial")
#: Predicates of the ground truth schema that say the same fact either way round
#: (subject and object may be swapped when pairing). The ground truth schema's
#: file has no marker for this, so they are listed here.
SYMMETRIC_PREDICATES = frozenset({"ALSO_KNOWN_AS"})
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
    """The triple in the ground truth schema. A component class whose row
    says (none) keeps its own spelling, marked NO_TRANSLATION, so it can never
    equal a component class of the ground truth schema. "crt" keeps the
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


def multiset_element(t: dict) -> tuple:
    """Which element of the record's multiset of translated extracted triples an occurrence is: two occurrences are
    of the same element when they read the same (subject instances and object instances evened out, as for an
    exact pair; component classes by loose match), as translated (070_evaluate/metrics/pairs.md, Example, *A
    multiset of translated extracted triples*)."""
    return (norm_text(t["subject"]), component_class_key(t["subject_class"]), component_class_key(t["predicate"]),
            norm_text(t["object"]), component_class_key(t["object_class"]))


def _can_pair(g: dict, t: dict, level: str) -> bool:
    """Whether g and t pair at this level as written (subject with subject)."""
    if component_class_key(g["predicate"]) != component_class_key(t["predicate"]):
        return False
    if level == "exact":
        return norm_text(g["subject"]) == norm_text(t["subject"]) and norm_text(g["object"]) == norm_text(t["object"])
    return _contains(g["subject"], t["subject"]) and _contains(g["object"], t["object"])


def is_symmetric(predicate) -> bool:
    """Whether the predicate (ground truth schema) says the same fact either way round."""
    return component_class_key(predicate) in {component_class_key(p) for p in SYMMETRIC_PREDICATES}


def swapped(t: dict) -> dict:
    """The translated triple with subject and object swapped, and their entity classes with them."""
    s = dict(t, subject=t["object"], object=t["subject"], subject_class=t["object_class"], object_class=t["subject_class"])
    if "crt" in t:
        s["crt"] = dict(t["crt"], subject_class=t["crt"]["object_class"], object_class=t["crt"]["subject_class"])
    return s


def _ways(g: dict, t: dict, level: str) -> list:
    """The ways t can pair with g at this level: [False] as written, [True]
    with subject and object swapped (a symmetric predicate only), both, or none."""
    ways = [False] if _can_pair(g, t, level) else []
    if is_symmetric(g["predicate"]) and _can_pair(g, swapped(t), level):
        ways.append(True)
    return ways


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


def _max_pairs(can: dict, strict, turned=lambda gi, ei: False) -> dict:
    """The largest pairing {gt index: extracted index}, each triple in either
    list with zero or one partner from the other, each gt triple paired with
    one of the extracted triples it can pair with (can[gi]); among the
    largest pairings, one with the most strict pairs (strict(gi, ei)), and
    among those, one with the fewest pairs matched with subject and object
    swapped (turned(gi, ei)), so an occurrence as written is preferred.
    Taking each gt triple's first free partner instead can leave a triple
    unpaired that another choice would have paired, or pair a triple with a
    partner whose entity classes differ while another partner's agree.

    The standard method for this: a minimum-cost maximum matching by
    successive shortest augmenting paths (a pair costs 0 if strict, BIG if
    not, plus 1 if turned, BIG being more than all the turned pairs together;
    Bellman-Ford finds each path, since swapping partners along a path
    can lower the cost). Each augmentation adds one pair at the lowest cost
    possible, so the result has the most pairs and, among those, the fewest
    non-strict ones, then the fewest turned ones. Deterministic: triples are
    tried in order."""
    edges = [(gi, ei) for gi in can for ei in can[gi]]
    big = len(edges) + 1
    cost = {(gi, ei): (0 if strict(gi, ei) else big) + (1 if turned(gi, ei) else 0) for gi, ei in edges}
    partner_of_g, partner_of_e = {}, {}               # the pairing so far, both ways
    while True:
        # shortest path from any unpaired gt triple, alternating "pair with
        # ei" (cost +c) and "ei leaves its partner" (cost -c), to an unpaired ei
        dist = {("g", gi): 0 for gi in can if gi not in partner_of_g}
        came = {}
        changed = True
        while changed:
            changed = False
            for gi in can:
                if ("g", gi) not in dist:
                    continue
                for ei in can[gi]:
                    if partner_of_g.get(gi) == ei:
                        continue
                    d = dist[("g", gi)] + cost[(gi, ei)]
                    if d < dist.get(("e", ei), float("inf")):
                        dist[("e", ei)], came[("e", ei)], changed = d, gi, True
            for ei, gi in partner_of_e.items():
                if ("e", ei) in dist:
                    d = dist[("e", ei)] - cost[(gi, ei)]
                    if d < dist.get(("g", gi), float("inf")):
                        dist[("g", gi)], came[("g", gi)], changed = d, ei, True
        ends = sorted((d, k[1]) for k, d in dist.items() if k[0] == "e" and k[1] not in partner_of_e)
        if not ends:
            return dict(partner_of_g)
        ei = ends[0][1]
        while True:                                   # walk the path back, swapping partners
            gi = came[("e", ei)]
            before = partner_of_g.get(gi)
            partner_of_g[gi], partner_of_e[ei] = ei, gi
            if ("g", gi) not in came:
                break
            ei = before


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
    turned = set()                                    # pairs matched with subject and object swapped
    free_g, free_e = set(range(len(gt))), set(range(len(ex)))
    for level in LEVELS:
        way = {}                                      # (gi, ei): swapped?, as written when both work unless only swapped is strict
        for gi in sorted(free_g):
            for ei in sorted(free_e):
                ways = _ways(gt[gi], ex[ei], level) if allowed(gi, ei) else []
                if ways:
                    agree = [w for w in ways if classes_agree(gt[gi], swapped(ex[ei]) if w else ex[ei])]
                    way[(gi, ei)] = (agree or ways)[0]
        can = {gi: [ei for ei in sorted(free_e) if (gi, ei) in way] for gi in sorted(free_g)}

        def oriented(gi, ei):
            return swapped(ex[ei]) if way[(gi, ei)] else ex[ei]
        for gi, ei in sorted(_max_pairs(can, lambda gi, ei: classes_agree(gt[gi], oriented(gi, ei)),
                                        lambda gi, ei: way[(gi, ei)]).items()):
            pairs.append((gi, ei, level))
            if way[(gi, ei)]:
                turned.add((gi, ei))
            free_g.discard(gi)
            free_e.discard(ei)

    def paired(gi, ei):                               # the occurrence the way round it was paired
        return swapped(ex[ei]) if (gi, ei) in turned else ex[ei]
    reach = [_within_reach(g, translation) for g in gt]
    strict_reach = [_within_strict_reach(g, translation) for g in gt]
    element = collections.Counter(multiset_element(t) for t in ex)
    multiplicity = [element[multiset_element(t)] for t in ex]     # each occurrence's element's multiplicity
    counts = {"extracted": len(ex), "gt": len(gt), "within_reach": sum(reach),
              "within_strict_reach": sum(strict_reach),
              "occurrences_multiplicity_above_1": sum(m > 1 for m in multiplicity)}
    for level in LEVELS:
        used = [(gi, ei) for gi, ei, lv in pairs if level == "partial" or lv == "exact"]
        counts[f"{level}_pairs"] = len(used)
        strict = [(gi, ei) for gi, ei in used if classes_agree(gt[gi], paired(gi, ei))]
        counts[f"{level}_strict_pairs"] = len(strict)
        for slot in ("subject_class", "object_class"):           # each entity class alone: which slot goes wrong
            counts[f"{level}_{slot}_pairs"] = sum(component_class_key(gt[gi][slot]) == component_class_key(paired(gi, ei)[slot])
                                                  for gi, ei in used)
        counts[f"{level}_pairs_within_reach"] = sum(reach[gi] for gi, _ in used)
        counts[f"{level}_strict_pairs_within_strict_reach"] = sum(strict_reach[gi] for gi, _ in strict)

    gd, ed = record["gt_describes"], record["extracted_describes"]
    truth = gd["object_class"] if gd and gd["object_class"] not in ("", UNDECIDED) else None
    said = None
    if ed and ed["object_class"] not in ("", UNDECIDED):
        said = translation.entity.get(component_class_key(ed["object_class"])) or f"{ed['object_class']}{NO_TRANSLATION}"
    rejected = sum(1 for gi in range(len(gt)) for ei in range(len(ex))
                   if not allowed(gi, ei) and _ways(gt[gi], ex[ei], "partial"))
    # the verdicts that apply to this record: those filed under a ground truth triple and an occurrence that pair
    # at the partial level (the rest no longer apply: a triple or a translation changed since the review)
    candidates = {pair_key(record["id"], gt[gi], ex[ei]) for gi in range(len(gt)) for ei in range(len(ex))
                  if _ways(gt[gi], ex[ei], "partial")}
    applied = sorted(k for k in reviews if k[0] == record["id"].strip() and k in candidates)
    stale_reviews = sorted(k for k in reviews if k[0] == record["id"].strip() and k not in candidates)
    unreviewed = sum(1 for gi, ei, lv in pairs
                     if lv == "partial" and pair_key(record["id"], gt[gi], ex[ei]) not in reviews)
    record["compared"] = {
        "translated": ex, "multiplicity": multiplicity, "pairs": pairs, "swapped": turned, "within_reach": reach, "within_strict_reach": strict_reach, "counts": counts,
        "partial_review": {"rejected": rejected, "unreviewed": unreviewed, "applied": len(applied),
                           "not_applying": stale_reviews},
        "describes": {"truth": truth, "said": said,
                      "right": bool(truth and said and component_class_key(truth) == component_class_key(said))},
    }
    record["compared"]["component_class_counts"] = component_class_counts(record, translation)
    return record


#: The tables of stats.per_component_class: what each row is, and which slot of a classed triple names it.
PER_COMPONENT_CLASS = (("predicate", "predicate"), ("subject class", "subject_class"), ("object class", "object_class"))


def component_class_counts(record: dict, translation) -> dict:
    """One record's counts for stats.per_component_class: {"counts": {(table, component_class_key): Counter} with "occurrences",
    "occurrences_multiplicity_above_1" (of those occurrences, the ones whose element has multiplicity above 1 in the
    record's multiset of translated extracted triples), "ground_truth_triples", "within_strict_reach" (of those ground truth triples), and per level "<level>_pairs" and
    "<level>_strict_pairs", "labels": {(table, key): spelling}, "within_reach": {(table, key): whether some checked
    row of the translation table translates to it (translation.reachable), or None for a component class of the
    current schema whose row says (none)}}.

    Attribution (070_evaluate/070_evaluate.md, *Per predicate and per entity class*):
      - an occurrence counts for its translated predicate, subject class, and object class (the way round it was
        paired, if it was; a component class whose row says (none) keeps its own spelling, marked);
      - a ground truth triple counts for its own predicate, subject class, and object class;
      - a pair counts for a predicate when its two triples have it (pairing needs the same predicate, so always),
        and for a subject class (or object class) only when both its triples have that one there, so that a
        wrong entity class counts against the precision of the one extraction named and the recall of the one
        the ground truth has;
      - a pair that counts for a row is also strict for it when both its triples have the same entity classes.
    Reach (070_evaluate.md, *Per predicate and per entity class*): a predicate or entity class is within reach when
    some checked row translates to it; a ground truth triple within strict reach (pairing's within_strict_reach)
    counts for its own predicate, subject class, and object class."""
    c = record["compared"]
    gt, ex = record["gt"], c["translated"]
    partner = {ei: (gi, level) for gi, ei, level in c["pairs"]}
    counts, labels, reach = collections.defaultdict(collections.Counter), {}, {}
    kind = {"predicate": "predicate", "subject class": "entity class", "object class": "entity class"}

    def add(table, name, field):
        key = (table, component_class_key(name))
        labels.setdefault(key, name)
        reach.setdefault(key, None if str(name).endswith(NO_TRANSLATION)
                         else key[1] in translation.reachable[kind[table]])
        counts[key][field] += 1
    for gi, g in enumerate(gt):
        for table, slot in PER_COMPONENT_CLASS:
            add(table, g[slot], "ground_truth_triples")
            if c["within_strict_reach"][gi]:
                add(table, g[slot], "within_strict_reach")
    for ei in range(len(ex)):
        t = as_paired(c, partner[ei][0], ei) if ei in partner else ex[ei]
        for table, slot in PER_COMPONENT_CLASS:
            add(table, t[slot], "occurrences")
            if c["multiplicity"][ei] > 1:
                add(table, t[slot], "occurrences_multiplicity_above_1")
        if ei not in partner:
            continue
        gi, level = partner[ei]
        strict = classes_agree(gt[gi], t)
        for table, slot in PER_COMPONENT_CLASS:
            if component_class_key(gt[gi][slot]) == component_class_key(t[slot]):
                for counted in LEVELS:
                    if counted == "partial" or level == "exact":
                        counts[(table, component_class_key(t[slot]))][f"{counted}_pairs"] += 1
                        if strict:
                            counts[(table, component_class_key(t[slot]))][f"{counted}_strict_pairs"] += 1
    return {"counts": counts, "labels": labels, "within_reach": reach}


def as_paired(compared: dict, gi: int, ei: int) -> dict:
    """The pair's occurrence the way round it was paired: its translated triple,
    with subject and object swapped if the pair was matched that way."""
    t = compared["translated"][ei]
    return swapped(t) if (gi, ei) in compared.get("swapped", ()) else t


def component_class_mismatches(records: list) -> list:
    """Traces of wrong or missing translations in compared records (see the
    module docstring): [{"kind", "crt_component_class", "translated_to", "gtt_component_class",
    "count", "swapped"}], most frequent first. kind is one of three: "entity class, subject" (a pair's subject
    classes differ), "entity class, object" (its object classes differ), "predicate" (an extracted only occurrence
    and a ground truth only triple with the same subject and object instances, other predicates). translated_to is the
    current schema's component class after translation (marked NO_TRANSLATION if its
    row says (none)); swapped: predicate mismatches where subject and object are
    the other way round."""
    found = {}

    def add(kind, crt_component_class, translated_to, gtt_component_class, swapped=False):
        key = (kind, crt_component_class, translated_to, gtt_component_class, swapped)
        found[key] = found.get(key, 0) + 1

    for rec in records:
        c = rec["compared"]
        gt, ex = rec["gt"], c["translated"]
        for gi, ei, _ in c["pairs"]:
            t = as_paired(c, gi, ei)
            for slot in ("subject_class", "object_class"):
                if component_class_key(gt[gi][slot]) != component_class_key(t[slot]):
                    add(f"entity class, {slot.split('_')[0]}", t["crt"][slot], t[slot], gt[gi][slot])
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
    return [{"kind": k, "crt_component_class": c, "translated_to": t, "gtt_component_class": g, "swapped": s, "count": n}
            for (k, c, t, g, s), n in sorted(found.items(), key=lambda kv: (-kv[1], kv[0]))]


def compare_all(evaluated, translation):
    for record in evaluated.records:
        compare_record(record, translation, evaluated.reviews)
    log.info(f"  compared {len(evaluated.records)} record(s)")
    return evaluated
