"""
stats.py -- stage 4: the numbers, each with its margin of error. Code only, no model.

Every number is a ratio of sums over the evaluated records (e.g. precision =
pairs in all records / occurrences in all records, less the untranslatable
occurrences and the occurrences paired with a fact that waits on an expert:
pairing.py), so a record with many
triples weighs more than one with few, as each triple is one answer. What
each number is, its formula and how to read it: 070_evaluate/metrics.md and
the files it lists (precision, recall, F1, entity-class accuracy, the recall
upper bound, recall within reach, schema fit, and the describes metrics).

MARGIN OF ERROR, by the clustered Wilson interval (070_evaluate/metrics/
approximately.md, Sampling error): every number is a ratio A / B of sums over
the evaluated records, a proportion estimated from a cluster sample with the
RECORDS as clusters (a record's triples come from one text and one model call,
so they succeed or fail together). The records' clustering is measured by the
design effect (the linearized variance of the ratio over records, against the
variance B independent triples would give), which turns the B triples into an
effective sample size; that, adjusted for the degrees of freedom of n records,
goes into the Wilson score interval (clustered_wilson). One formula for the
part, each stratum, each component class: no redraws, no seed. It is valid only
for a random sample (records.py evaluates only the fair sample). From 2 records
on there is a range; below FEW_RECORDS the report adds that the design effect
is itself estimated from few records. Every number's parts (what it divides by
what, per record) have one home, RATIO_PARTS, which numbers() reads too, so a
value and its range can never disagree.
"""
from __future__ import annotations

import collections
import math
from functools import lru_cache

from pairing import NO_DRAFTING_MODEL, GROUPINGS, LEVELS, MATCH_KINDS, PER_COMPONENT_CLASS, REACH_BUCKETS, SECOND_OPINION_GROUPS
from common.ground_truth import HELD_OUT, PARTS, TUNING
from common.triples_io import component_class_key

#: Fewer records than this (records with something to divide by): the report adds to a range that the design
#: effect is itself estimated from few records, so the range may still be too narrow. Our choice: the nearest
#: published line is the few-clusters literature's "fewer than eleven clusters" (070_evaluate/metrics/approximately.md).
FEW_RECORDS = 10
#: The standard normal quantile of a two-sided 95% interval.
Z = 1.959963984540054
#: A stratum whose proportion of the evaluated records differs from its proportion
#: of the pool by more than this is pointed out (with enough records).
SHARE_GAP = 0.10


def _ratio(a, b):
    return a / b if b else None


def numbers(records: list) -> dict:
    """Every number, as a point value, from records' counts."""
    total = collections.Counter()
    for r in records:
        total.update(r["compared"]["counts"])
    translatable = total["extracted"] - total["untranslatable"]
    out = {"records": len(records), "extracted": total["extracted"], "gt_triples": total["gt"],
           "untranslatable": total["untranslatable"], "translatable": translatable,
           "pending": total["pending"],
           "within_reach": total["within_reach"], "within_strict_reach": total["within_strict_reach"]}
    for level in LEVELS:
        m, s = total[f"{level}_pairs"], total[f"{level}_strict_pairs"]
        sw = total[f"{level}_strict_pairs_within_strict_reach"]
        waiting = total[f"{level}_pending_pairs"]
        out[level] = {"pending_pairs": waiting, "counted_occurrences": _counted(total, level),
                      "subject_class_pairs": total[f"{level}_subject_class_pairs"],
                      "object_class_pairs": total[f"{level}_object_class_pairs"],
                      "pairs": m, "strict_pairs": s, "pairs_within_reach": total[f"{level}_pairs_within_reach"],
                      "strict_pairs_within_reach": sw}
    for path, (a, b) in RATIO_PARTS.items():         # every number with a margin, from its one definition
        if path[0] != "describes":
            _put(out, path, _ratio(a(total), b(total)))
    # by match kind (pairing.py, BY MATCH KIND and PIN MISFITS): counts only, no margins, part of no metric
    key = lambda k: k.replace(" ", "_")                                       # noqa: E731
    out["by_match"] = {
        "occurrences": {k: total[f"occurrences_match_{key(k)}"] for k in MATCH_KINDS},
        "extracted_only": {k: total[f"extracted_only_match_{key(k)}"] for k in MATCH_KINDS},
        "entity_classes": {**{k: total[f"entity_classes_match_{key(k)}"] for k in MATCH_KINDS},
                           "(none)": total["entity_classes_to_none"]},
        "within_reach": {b: total[f"within_reach_{key(b)}"] for b in REACH_BUCKETS},
        "recall_upper_bound": {b: _ratio(total[f"within_reach_{key(b)}"], total["gt"]) for b in REACH_BUCKETS},
        "pin_checked": total["pin_checked"], "pin_misfits": total["pin_misfits"]}
    out["second_opinion_repeats"] = _second_opinion_repeats(records)
    known = [r["compared"]["describes"] for r in records if r["compared"]["describes"]["truth"]]
    describes_classes = collections.Counter(component_class_key(d["truth"]) for d in known)
    per_describes_class = {k: _ratio(sum(d["right"] for d in known if component_class_key(d["truth"]) == k), n) for k, n in describes_classes.items()}
    a, b = RATIO_PARTS[("describes", "accuracy")]
    out["describes"] = {"records": len(known),
                        "accuracy": _ratio(sum(a(_describes_counts(r)) for r in records),
                                           sum(b(_describes_counts(r)) for r in records)),
                        "majority_baseline": _ratio(max(describes_classes.values(), default=0), len(known)),
                        "per_entity_class_average": _ratio(sum(per_describes_class.values()), len(per_describes_class))}
    return out


def by_group(records: list, grouping: str) -> dict | None:
    """The numbers of each group of ground truth triples by one provenance grouping (pairing.GROUPINGS:
    "second_opinion" or "drafted_by"; 070_evaluate/070_evaluate.md, *Shared-model bias*), each with its margin of
    error by clustered_wilson over the records, from the records' group counts (record["compared"]["groups"]).
    {group: {"gt_triples", "records" (records with a ground truth triple in it), "spellings" (drafted_by only: the
    names as the ground truth writes them), "exact_share", level: {"pairs", "strict_pairs", "recall", "precision",
    "f1", "entity_class_accuracy"}}}, each number a {"value", "low", "high", "n_eff", "deff", "few_records"}.
    For a group g, at a level, with each record's sums:
      recall                  = g's pairs ÷ g's ground truth triples
      precision (attributed)  = g's pairs ÷ (counted occurrences − the pairs of the other groups): an occurrence
                                paired with another group's triple is left out, as an untranslatable one and one
                                paired with a fact that waits on an expert are; every unpaired occurrence counts
                                against each group alike, since it belongs to no group. An attribution, not a true
                                per-group precision.
      F1                      = 2 × g's pairs ÷ (that denominator + g's ground truth triples)
      entity-class accuracy   = g's strict pairs ÷ g's pairs
      exact share             = g's exact pairs ÷ g's partial pairs (every pair, both levels)
    The groups split the same records, so their ranges aren't independent of each other. None when the records have
    no group counts (a run kept from before 2026-11-01), no ground truth triple, or, for "second_opinion", no ground
    truth triple was checked. Groups in order: the most ground truth triples first; for "drafted_by", the rows
    with no drafting model recorded (pairing.NO_DRAFTING_MODEL) last."""
    per = [((r["compared"].get("groups") or {}).get(grouping), r) for r in records]
    if not per or any(g is None for g, _ in per):
        return None
    keys = collections.Counter()
    for g, _ in per:
        for k, c in g.items():
            keys[k] += c["gt"]
    if not keys or (grouping == "second_opinion" and not any(keys[k] for k in SECOND_OPINION_GROUPS[:-1])):
        return None
    if grouping == "second_opinion":
        order = list(SECOND_OPINION_GROUPS)
    else:
        order = sorted(keys, key=lambda k: (k == NO_DRAFTING_MODEL, -keys[k], k))
    empty = collections.Counter()

    def margin(parts):
        ci = clustered_wilson(parts)
        return {"value": ci["value"], "low": ci["low"], "high": ci["high"], "n_eff": ci["n_eff"], "deff": ci["deff"],
                "few_records": ci["n_records"] < FEW_RECORDS}
    out = {}
    for k in order:
        rows = [(g.get(k, empty), r["compared"]["counts"]) for g, r in per]
        entry = {"gt_triples": keys[k], "records": sum(1 for c, _ in rows if c["gt"])}
        if grouping == "drafted_by":
            entry["spellings"] = sorted({s for _, r in per for s in r["compared"].get("drafted_by_spellings", {}).get(k, [])})
        entry["exact_share"] = margin([(c["exact_pairs"], c["partial_pairs"]) for c, _ in rows])
        for level in LEVELS:
            denom = [_counted(t, level) - t[f"{level}_pairs"] + c[f"{level}_pairs"] for c, t in rows]
            entry[level] = {
                "pairs": sum(c[f"{level}_pairs"] for c, _ in rows),
                "strict_pairs": sum(c[f"{level}_strict_pairs"] for c, _ in rows),
                "recall": margin([(c[f"{level}_pairs"], c["gt"]) for c, _ in rows]),
                "precision": margin([(c[f"{level}_pairs"], d) for (c, _), d in zip(rows, denom)]),
                "f1": margin([(2 * c[f"{level}_pairs"], d + c["gt"]) for (c, _), d in zip(rows, denom)]),
                "entity_class_accuracy": margin([(c[f"{level}_strict_pairs"], c[f"{level}_pairs"]) for c, _ in rows])}
        out[k] = entry
    return out


def _second_opinion_repeats(records: list) -> list:
    """How many of the records' ground truth triples each second opinion found in 0, 1, ..., N of its N repeats
    (record["second_opinion_repeats"], from annotations/second_opinion.csv: common.second_opinion.repeats_of):
    [{"model", "repeats": N, "gt_triples", "found_in_repeats": [triples found in k repeats, for k = 0 .. N]}], one entry per
    model and number of repeats (a record drafted in fewer repeats than the others, its repeats having failed, counts under
    its own N), sorted; [] when none was checked."""
    tally = {}
    for r in records:
        for by in r.get("second_opinion_repeats") or []:
            for model, (found, repeats) in by.items():
                tally.setdefault((model, repeats), collections.Counter())[found] += 1
    return [{"model": model, "repeats": repeats, "gt_triples": sum(c.values()),
             "found_in_repeats": [c[k] for k in range(repeats + 1)]} for (model, repeats), c in sorted(tally.items())]


#: The numbers that get a margin: (path in numbers(), label).
WITH_MARGIN = [((level, key), f"{level}: {key}") for level in LEVELS
               for key in ("precision", "recall", "f1", "strict_precision", "strict_recall", "strict_f1",
                           "entity_class_accuracy", "subject_class_accuracy", "object_class_accuracy",
                           "recall_within_reach", "strict_recall_within_reach")] + \
              [(("recall_upper_bound",), "recall upper bound"), (("strict_recall_upper_bound",), "strict recall upper bound"),
               (("schema_fit",), "schema fit"),
               (("describes", "accuracy"), "describes accuracy")]


def _counted(c, level: str) -> int:
    """Precision's denominator, from one record's counts or summed ones: the occurrences less the untranslatable ones
    and those paired with a fact that waits on an expert (pairing.py)."""
    return c["extracted"] - c["untranslatable"] - c[f"{level}_pending_pairs"]


def _describes_counts(r: dict) -> collections.Counter:
    """A record's describes result as counts: describes_known (its ground truth names a describes class) and
    describes_right (extraction named the same one)."""
    d = r["compared"]["describes"]
    return collections.Counter({"describes_known": int(bool(d["truth"])),
                                "describes_right": int(bool(d["truth"]) and bool(d["right"]))})


def _level_parts(level: str) -> dict:
    """The parts of each number of a pair level: {key: (numerator, denominator)}, each a function of counts."""
    m = lambda c: c[f"{level}_pairs"]                                          # noqa: E731
    s = lambda c: c[f"{level}_strict_pairs"]                                   # noqa: E731
    counted = lambda c: _counted(c, level)                                     # noqa: E731
    return {"precision": (m, counted), "recall": (m, lambda c: c["gt"]),
            "f1": (lambda c: 2 * m(c), lambda c: counted(c) + c["gt"]),
            "strict_precision": (s, counted), "strict_recall": (s, lambda c: c["gt"]),
            "strict_f1": (lambda c: 2 * s(c), lambda c: counted(c) + c["gt"]),
            "entity_class_accuracy": (s, m),
            "subject_class_accuracy": (lambda c: c[f"{level}_subject_class_pairs"], m),
            "object_class_accuracy": (lambda c: c[f"{level}_object_class_pairs"], m),
            "recall_within_reach": (lambda c: c[f"{level}_pairs_within_reach"], lambda c: c["within_reach"]),
            "strict_recall_within_reach": (lambda c: c[f"{level}_strict_pairs_within_strict_reach"],
                                           lambda c: c["within_strict_reach"])}


#: What each number with a margin divides by what: {path in numbers(): (numerator, denominator)}, each a function of
#: one record's counts (record["compared"]["counts"], or for the describes accuracy _describes_counts), or of summed
#: ones. The one home of every formula: numbers() computes the values from it, and with_margins the ranges, so a value
#: and its range can never disagree. In every record the numerator is at most the denominator (F1: a pair uses one
#: counted occurrence and one ground truth triple), so each is a proportion of record sums.
RATIO_PARTS = {**{(level, key): parts for level in LEVELS for key, parts in _level_parts(level).items()},
               ("recall_upper_bound",): (lambda c: c["within_reach"], lambda c: c["gt"]),
               ("strict_recall_upper_bound",): (lambda c: c["within_strict_reach"], lambda c: c["gt"]),
               ("schema_fit",): (lambda c: c["extracted"] - c["untranslatable"], lambda c: c["extracted"]),
               ("describes", "accuracy"): (lambda c: c["describes_right"], lambda c: c["describes_known"])}
assert [p for p, _ in WITH_MARGIN] == list(RATIO_PARTS), "WITH_MARGIN and RATIO_PARTS name the same numbers"


def _get(d: dict, path: tuple):
    for p in path:
        d = d.get(p) if isinstance(d, dict) else None
    return d


def _put(d: dict, path: tuple, value) -> None:
    for p in path[:-1]:
        d = d.setdefault(p, {})
    d[path[-1]] = value


def _betacf(a: float, b: float, x: float) -> float:
    """The continued fraction of the regularized incomplete beta function, by the modified Lentz method (Press,
    Teukolsky, Vetterling & Flannery, Numerical Recipes, 3rd ed., 2007, section 6.4, betacf)."""
    tiny, eps = 1e-300, 3e-16
    qab, qap, qam = a + b, a + 1, a - 1
    c, d = 1.0, 1 - qab * x / qap
    d = 1 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, 300):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1 + aa * d
        d = 1 / (d if abs(d) > tiny else tiny)
        c = 1 + aa / c
        c = c if abs(c) > tiny else tiny
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1 + aa * d
        d = 1 / (d if abs(d) > tiny else tiny)
        c = 1 + aa / c
        c = c if abs(c) > tiny else tiny
        h *= d * c
        if abs(d * c - 1) < eps:
            break
    return h


def _betainc(a: float, b: float, x: float) -> float:
    """The regularized incomplete beta function I_x(a, b)."""
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    front = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log(1 - x))
    if x < (a + 1) / (a + b + 2):
        return front * _betacf(a, b, x) / a
    return 1 - front * _betacf(b, a, 1 - x) / b


def _t_cdf(t: float, df: int) -> float:
    tail = 0.5 * _betainc(df / 2, 0.5, df / (df + t * t))
    return 1 - tail if t > 0 else tail


@lru_cache(maxsize=None)
def t_quantile(p: float, df: int) -> float:
    """The Student t distribution's quantile (p above 0.5, df degrees of freedom), by bisection on its CDF: in plain
    Python, since the project has no scipy (requirements.txt). t_quantile(0.975, 19) = 2.0930."""
    lo, hi = 0.0, 1e4
    for _ in range(200):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if _t_cdf(mid, df) < p else (lo, mid)
    return (lo + hi) / 2


def clustered_wilson(parts: list) -> dict:
    """The 95% clustered Wilson interval of A / B (070_evaluate/metrics/approximately.md, Sampling error): parts is
    one (a_r, b_r) per evaluated record (means over the repeats for py helpers/compare_runs.py), A = Σ a_r, B = Σ b_r.
    Only the records with b_r > 0 count as clusters (n): a record with nothing to divide by adds nothing.
      1. B = 0: no value. p̂ = A / B.
      2. n = 1: the value, no range.
      3. The linearized (Taylor) variance of the ratio over the records, with the small-sample factor n / (n − 1):
         v̂ = n / (n − 1) · Σ (a_r − p̂·b_r)² / B² (Cochran 1977, chapter 6).
      4. The design effect deff = v̂ ÷ (p̂(1 − p̂) / B), at least 1; effective sample size n_eff = B / deff, kept
         between n and B. When p̂ is 0 or 1 the variance is 0 and the ratio undefined: every record counts as one
         trial, n_eff = n (our choice, the conservative side).
      5. The degrees-of-freedom adjustment (Korn & Graubard 1998, as Dean & Pagano 2015 apply it):
         n′ = n_eff · (z / t_{0.975, n − 1})².
      6. The Wilson score interval with n′ and p̂.
    Returns {"value", "low", "high", "n_records", "n_items" (B), "n_eff" (n′), "deff"} (low, high None below 2
    records; deff None at 0 and 1)."""
    used = [(a, b) for a, b in parts if b > 0]
    n, A, B = len(used), sum(a for a, _ in used), sum(b for _, b in used)
    out = {"value": None, "low": None, "high": None, "n_records": n, "n_items": B, "n_eff": None, "deff": None}
    if B <= 0:
        return out
    p = A / B
    out["value"] = p
    if n < 2:
        return out
    if 0 < p < 1:
        v = n / (n - 1) * sum((a - p * b) ** 2 for a, b in used) / B ** 2
        deff = max(1.0, v / (p * (1 - p) / B))
        n_eff = min(max(B / deff, n), B)
        out["deff"] = deff
    else:
        n_eff = n
    n_eff *= (Z / t_quantile(0.975, n - 1)) ** 2
    z2 = Z * Z
    centre = (p + z2 / (2 * n_eff)) / (1 + z2 / n_eff)
    half = Z * math.sqrt(p * (1 - p) / n_eff + z2 / (4 * n_eff * n_eff)) / (1 + z2 / n_eff)
    # at 0% (100%) the Wilson bound is 0 (1) exactly; rounding error would leave it a hair above (below)
    out.update(low=0.0 if p == 0 else max(0.0, centre - half), high=1.0 if p == 1 else min(1.0, centre + half),
               n_eff=n_eff)
    return out


def record_parts(records: list, path: tuple) -> list:
    """[(a_r, b_r)] of one number (RATIO_PARTS) for each record."""
    a, b = RATIO_PARTS[path]
    counts = (_describes_counts(r) if path[0] == "describes" else _with_zeros(r["compared"]["counts"])
              for r in records)
    return [(a(c), b(c)) for c in counts]


def _with_zeros(c) -> collections.Counter:
    """A record's counts as a Counter, so a count it lacks (a kept evaluation of an older version) reads 0."""
    return c if isinstance(c, collections.Counter) else collections.Counter(c)


def with_margins(records: list, provenance: bool = False) -> dict:
    """numbers(records), each number in WITH_MARGIN turned into {"value", "low", "high", "n_eff", "deff",
    "few_records"} by clustered_wilson over the records; point["interval"] says how ({"method", "records",
    "few_records": fewer than FEW_RECORDS records}). provenance: also the numbers by each provenance grouping
    (by_group: point["second_opinion"], point["drafted_by"]), for a part's numbers."""
    point = numbers(records)
    for grouping in GROUPINGS:
        if provenance:
            point[grouping] = by_group(records, grouping)
    for path, _ in WITH_MARGIN:
        ci = clustered_wilson(record_parts(records, path))
        assert ci["value"] == _get(point, path) or (ci["value"] is not None and _get(point, path) is not None
                                                    and abs(ci["value"] - _get(point, path)) < 1e-12), path
        _put(point, path, {"value": _get(point, path), "low": ci["low"], "high": ci["high"], "n_eff": ci["n_eff"],
                           "deff": ci["deff"], "few_records": ci["n_records"] < FEW_RECORDS})
    point["interval"] = {"method": "clustered Wilson", "records": len(records), "few_records": len(records) < FEW_RECORDS}
    return point


#: Below this proportion of the catalog evaluated, drawing with repeats from a
#: finite catalog changes the margin negligibly (a rule of survey sampling:
#: Cochran, Sampling Techniques, 1977, chapter 2; not verified in the book).
FINITE_NEGLIGIBLE = 0.05


def margin_checks(records: list, point: dict, catalog_records: int) -> dict:
    """The margin of error's assumptions that can be checked on the evaluated records (070_evaluate/metrics/
    approximately.md, Sampling error): the largest record's proportion of the triples, the proportion of the catalog
    evaluated, and, for reading, the lowest and highest design effect across the numbers (how much the records'
    triples move together)."""
    largest = {}
    for key, what in (("extracted", "extracted triples"), ("gt", "ground truth triples")):
        total = sum(r["compared"]["counts"][key] for r in records)
        top = max(records, key=lambda r: r["compared"]["counts"][key])
        largest[what] = {"record": top["id"], "proportion": _ratio(top["compared"]["counts"][key], total)}
    deffs = [m["deff"] for path, _ in WITH_MARGIN if (m := _get(point, path)) and m.get("deff") is not None]
    return {"largest_record": largest, "catalog_proportion": _ratio(len(records), catalog_records),
            "deff_range": {"low": min(deffs), "high": max(deffs)} if deffs else None}


def by_part(evaluated) -> dict:
    return {part: [r for r in evaluated.records if r["part"] == part] for part in PARTS}


def strata_table(records: list, pool_strata: dict) -> list:
    """Per stratum: records evaluated, proportion of the evaluated records vs proportion of the
    pool, and its numbers with their ranges (with_margins; the caveat below FEW_RECORDS), None with no record."""
    total_pool = sum(pool_strata.values())
    by_stratum = collections.defaultdict(list)
    for r in records:
        by_stratum[r["stratum"]].append(r)
    rows = []
    for g in sorted(set(pool_strata) | set(by_stratum), key=lambda g: (-pool_strata.get(g, 0), g)):
        recs = by_stratum.get(g, [])
        rows.append({"stratum": g or "(no stratum)", "records": len(recs),
                     "share_evaluated": _ratio(len(recs), len(records)),
                     "share_pool": _ratio(pool_strata.get(g, 0), total_pool),
                     "numbers": with_margins(recs) if recs else None})
    return rows


def describes_confusion(records: list) -> dict:
    """{(truth, said): records}."""
    c = collections.Counter()
    for r in records:
        d = r["compared"]["describes"]
        if d["truth"]:
            c[(d["truth"], d["said"] or "(none named)")] += 1
    return dict(c)


def twins(records: list) -> dict | None:
    """The twins among records (records.py) and the numbers without them: {"records": [{"id", "kind"}],
    "without": with_margins(the others), or None when there is no twin or no other}. None when which records are
    twins isn't known."""
    if any(r.get("twin") is None for r in records):
        return None
    twin = [{"id": r["id"], "kind": r["twin"]} for r in records if r["twin"]]
    rest = [r for r in records if not r["twin"]]
    return {"records": twin, "without": with_margins(rest) if twin and rest else None}


def _component_class_parts() -> dict:
    """What each number of a row per component class divides by what: {(level or "row", key): (numerator,
    denominator)}, each a function of one record's (or summed) counts for the row (pairing.component_class_counts).
    The same formulas as numbers(); a strict pair's ground truth triple is always within strict reach, so strict
    recall within reach counts every strict pair."""
    out = {("row", "strict_recall_upper_bound"): (lambda c: c["within_strict_reach"], lambda c: c["ground_truth_triples"])}
    for level in LEVELS:
        m = lambda c, level=level: c[f"{level}_pairs"]                                          # noqa: E731
        s = lambda c, level=level: c[f"{level}_strict_pairs"]                                   # noqa: E731
        # less the untranslatable occurrences and those matching a fact that waits on an expert
        counted = lambda c, level=level: c["occurrences"] - c["untranslatable"] - c[f"{level}_pending_pairs"]  # noqa: E731
        gt = lambda c: c["ground_truth_triples"]                                                  # noqa: E731
        out.update({(level, "precision"): (m, counted), (level, "recall"): (m, gt),
                    (level, "f1"): (lambda c, m=m: 2 * m(c), lambda c, counted=counted: counted(c) + gt(c)),
                    (level, "strict_precision"): (s, counted), (level, "strict_recall"): (s, gt),
                    (level, "strict_f1"): (lambda c, s=s: 2 * s(c), lambda c, counted=counted: counted(c) + gt(c)),
                    (level, "strict_recall_within_reach"): (s, lambda c: c["within_strict_reach"])})
    return out


#: The one home of a row's formulas (per_component_class): its value and its range both come from here.
COMPONENT_CLASS_PARTS = _component_class_parts()


def _component_class_numbers(c) -> dict:
    """Precision, recall, and F1, their strict versions, and strict recall within reach, at each level, and the
    strict recall upper bound ("row": the same at both levels), from summed counts (COMPONENT_CLASS_PARTS)."""
    out = {}
    for (level, key), (a, b) in COMPONENT_CLASS_PARTS.items():
        out.setdefault(level, {})[key] = _ratio(a(c), b(c))
    return out


def per_component_class(records: list) -> dict:
    """Precision, recall, and F1, and their strict versions, per predicate, per subject class, and per object class
    (each of the ground truth schema, or of the current schema marked as translating to (none)), at each pair level,
    over records' counts (pairing.component_class_counts), each with its margin of error by clustered_wilson over
    the records, as the part's numbers ("few_records": the row's numbers come from fewer than FEW_RECORDS records
    with something to divide by). {table: [row]}, each row {"component_class",
    "within_reach" (whether some checked row translates to it; None for one whose row says (none)), "occurrences",
    "occurrences_multiplicity_above_1" (of those, the ones whose element has multiplicity above 1 in its record),
    "untranslatable" (of those, the untranslatable ones, left out of precision), "ground_truth_triples",
    "within_strict_reach" (of those ground truth triples), "strict_recall_upper_bound",
    "pending_pairs" (occurrences paired exactly with a fact that waits on an expert, left out of precision),
    "counted_against" (occurrences and ground truth triples with no exact pair that counts for it, less the
    untranslatable occurrences and those paired with a fact that waits), "<level>":
    {"pairs", "strict_pairs", "precision", "recall", "f1", "strict_precision", "strict_recall", "strict_f1",
    "strict_recall_within_reach"}} (each number a {"value", "low", "high", "n_eff", "deff", "few_records"}), sorted by
    counted_against, most first: what the component class costs at the exact level, so the frequent and badly
    extracted ones come first, and one seen once can cost at most two."""
    per_record = [r["compared"]["component_class_counts"] for r in records]
    labels, reach = {}, {}
    for x in reversed(per_record):           # the spelling first met
        labels.update(x["labels"])
        reach.update(x["within_reach"])
    total = collections.defaultdict(collections.Counter)
    for x in per_record:
        for key, c in x["counts"].items():
            total[key].update(c)
    out = {table: [] for table, _ in PER_COMPONENT_CLASS}
    for key, c in total.items():
        row = {"component_class": labels[key], "within_reach": reach[key], "occurrences": c["occurrences"],
               "occurrences_multiplicity_above_1": c["occurrences_multiplicity_above_1"],
               "untranslatable": c["untranslatable"],
               "ground_truth_triples": c["ground_truth_triples"], "within_strict_reach": c["within_strict_reach"],
               "pending_pairs": c["exact_pending_pairs"],
               "counted_against": c["occurrences"] - c["untranslatable"] - c["exact_pending_pairs"]
               + c["ground_truth_triples"] - 2 * c["exact_pairs"]}
        for level in LEVELS:
            row[level] = {"pairs": c[f"{level}_pairs"], "strict_pairs": c[f"{level}_strict_pairs"]}
        empty = collections.Counter()
        for (level, what), (a, b) in COMPONENT_CLASS_PARTS.items():
            ci = clustered_wilson([(a(x["counts"].get(key, empty)), b(x["counts"].get(key, empty))) for x in per_record])
            assert ci["value"] == _ratio(a(c), b(c)) or abs(ci["value"] - _ratio(a(c), b(c))) < 1e-12, (key, what)
            (row if level == "row" else row[level])[what] = {
                "value": _ratio(a(c), b(c)), "low": ci["low"], "high": ci["high"], "n_eff": ci["n_eff"],
                "deff": ci["deff"], "few_records": ci["n_records"] < FEW_RECORDS}
        out[key[0]].append(row)
    for rows in out.values():
        rows.sort(key=lambda r: (-r["counted_against"], component_class_key(r["component_class"])))
    return out


#: The numbers of each level in a row of per_record, besides its pairs.
PER_RECORD_NUMBERS = ("precision", "recall", "f1", "strict_precision", "strict_recall", "strict_f1",
                      "recall_within_reach", "strict_recall_within_reach")


def per_record(records: list) -> list:
    """Each record's own numbers, from its own counts by the same formulas as numbers() (None where a denominator is
    0), with no margin of error: for finding the weak records, never averaged into the part's numbers, which pool
    every record's counts (070_evaluate/metrics.md, *Pooled, not averaged*). [{"id", "position", "title",
    "occurrences", "occurrences_multiplicity_above_1" (of those, the ones whose element has multiplicity above 1 in
    the record's multiset of translated extracted triples), "untranslatable" (of those, the untranslatable ones, left
    out of its precision), "ground_truth_triples", "within_reach",
    "within_strict_reach" (of those ground truth triples), "pending_pairs" (occurrences paired exactly with a fact that
    waits on an expert), "counted_against" (occurrences and ground truth triples with no exact pair, less the
    untranslatable occurrences and those paired with a fact that waits), "recall_upper_bound", "strict_recall_upper_bound", "<level>": {"pairs", "strict_pairs", and each of
    PER_RECORD_NUMBERS}}], sorted by counted_against, most first (as per_component_class), then by pool position."""
    rows = []
    for r in records:
        n, c = numbers([r]), r["compared"]["counts"]
        row = {"id": r["id"], "position": r["position"], "title": r["title"], "occurrences": c["extracted"],
               "occurrences_multiplicity_above_1": c["occurrences_multiplicity_above_1"],
               "untranslatable": c.get("untranslatable", 0),
               "ground_truth_triples": c["gt"], "within_reach": c["within_reach"],
               "within_strict_reach": c["within_strict_reach"], "pending_pairs": c.get("exact_pending_pairs", 0),
               "counted_against": c["extracted"] - c.get("untranslatable", 0) - c.get("exact_pending_pairs", 0) + c["gt"]
               - 2 * c["exact_pairs"],
               "recall_upper_bound": n["recall_upper_bound"], "strict_recall_upper_bound": n["strict_recall_upper_bound"]}
        for level in LEVELS:
            row[level] = {"pairs": n[level]["pairs"], "strict_pairs": n[level]["strict_pairs"],
                          **{k: n[level][k] for k in PER_RECORD_NUMBERS}}
        rows.append(row)
    return sorted(rows, key=lambda x: (-x["counted_against"], x["position"]))


def removed_by_reason(records: list) -> list:
    """What 060's checks removed from records, per reason as 060 wrote it (records.py, "removed"): [{"reason",
    "removed", "records" (how many of the records had any)}], most removed first."""
    removed, having = collections.Counter(), collections.Counter()
    for r in records:
        removed.update(r.get("removed") or {})
        having.update(set(r.get("removed") or {}))
    return [{"reason": k, "removed": n, "records": having[k]}
            for k, n in sorted(removed.items(), key=lambda kv: (-kv[1], kv[0]))]


def compute_metrics(evaluated, settings: dict) -> dict:
    """Every number, per part: the tuning part always; the held-out part only
    with the setting evaluate_held_out. {part: {"numbers", "strata", "confusion", "per_component_class", "per_record", "removed_by_060", ...},
    "kept_aside": {part: records not shown}}."""
    parts = by_part(evaluated)
    shown = [TUNING] + ([HELD_OUT] if settings["evaluate_held_out"] else [])
    result = {}
    for part in shown:
        recs = parts[part]
        numbers = with_margins(recs, provenance=True) if recs else None
        result[part] = {"numbers": numbers,
                        "strata": strata_table(recs, evaluated.pool_strata) if recs else [],
                        "confusion": describes_confusion(recs),
                        "per_component_class": per_component_class(recs),
                        "per_record": per_record(recs),
                        "removed_by_060": removed_by_reason(recs),
                        "margin_checks": margin_checks(recs, numbers, evaluated.catalog_records)
                        if numbers else None,
                        "twins": twins(recs)}
    result["kept_aside"] = {p: len(parts[p]) for p in PARTS if p not in shown}
    return result
