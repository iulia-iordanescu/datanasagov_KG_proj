"""
stats.py -- stage 4: the numbers, each with its margin of error. Code only, no model.

Every number is a ratio of sums over the evaluated records (e.g. precision =
pairs in all records / triples extracted in all records), so a record with
many triples weighs more than one with few, as each triple is one answer.

  precision        pairs / extracted triples
  recall           pairs / ground truth triples
  F1               2 x precision x recall / (precision + recall), the same as
                   2 x pairs / (extracted triples + ground truth triples)
  (all three at the two pair levels, exact and partial, and for all pairs
   and STRICT pairs, i.e. with both entity classes right too)
  entity-class accuracy   strict pairs / pairs
  recall upper bound          ground truth triples within reach (their predicate
                          has a counterpart in the schema: all a pair needs) / all
                          of them: the most recall can be
  strict recall upper bound   the same, within strict reach (predicate and both
                          entity classes): the most strict recall can be
  recall within reach     pairs whose ground truth triple is within reach /
                          ground truth triples within reach; strict recall
                          within reach likewise, with strict pairs and
                          strict reach
  describes accuracy      records whose DESCRIBES entity class is right /
                          records where the ground truth names one; with
                          the MAJORITY BASELINE (the share of the most common
                          kind: what always guessing it would get) and the
                          PER-ENTITY-CLASS average (each entity class's accuracy, averaged)

MARGIN OF ERROR, by the bootstrap: the numbers are recomputed REDRAWS
times, each time from records drawn at random, with repeats, from the evaluated
ones; the middle 95% of the results is the margin. It draws WHOLE RECORDS
(a record's triples come from one text and one model call, so they succeed or
fail together; drawing triples one by one would give margins too narrow), and
draws WITHIN EACH STRATUM, as many as the stratum has, the way the pool
was drawn. It is valid only for a random sample (records.py evaluates only the
fair sample) of enough records: below MIN_RECORDS, no margin is given, only a
plain warning. The draws are seeded, so a rerun gives the same margins.
"""
from __future__ import annotations

import collections
import random

from pairing import LEVELS
from common.triples_io import component_class_key

#: Fewer evaluated records than this: no margin of error (a bootstrap on very
#: few records gives margins that are themselves unreliable, usually too
#: narrow). A rule of thumb, not a law; the report says so.
MIN_RECORDS = 20
REDRAWS = 1000
SEED = 70
#: A stratum whose share of the evaluated records differs from its share
#: of the pool by more than this is pointed out (with enough records).
SHARE_GAP = 0.10


def _ratio(a, b):
    return a / b if b else None


def numbers(records: list) -> dict:
    """Every number, as a point value, from records' counts."""
    total = collections.Counter()
    for r in records:
        total.update(r["compared"]["counts"])
    out = {"records": len(records), "extracted": total["extracted"], "gt_triples": total["gt"],
           "within_reach": total["within_reach"], "within_strict_reach": total["within_strict_reach"],
           "recall_upper_bound": _ratio(total["within_reach"], total["gt"]),
           "strict_recall_upper_bound": _ratio(total["within_strict_reach"], total["gt"])}
    for level in LEVELS:
        m, s = total[f"{level}_pairs"], total[f"{level}_strict_pairs"]
        sw = total[f"{level}_strict_pairs_within_strict_reach"]
        out[level] = {"precision": _ratio(m, total["extracted"]), "recall": _ratio(m, total["gt"]),
                      "f1": _ratio(2 * m, total["extracted"] + total["gt"]),
                      "strict_precision": _ratio(s, total["extracted"]), "strict_recall": _ratio(s, total["gt"]),
                      "strict_f1": _ratio(2 * s, total["extracted"] + total["gt"]),
                      "entity_class_accuracy": _ratio(s, m),
                      "recall_within_reach": _ratio(total[f"{level}_pairs_within_reach"], total["within_reach"]),
                      "strict_recall_within_reach": _ratio(sw, total["within_strict_reach"]),
                      "pairs": m, "strict_pairs": s, "pairs_within_reach": total[f"{level}_pairs_within_reach"],
                      "strict_pairs_within_reach": sw}
    known = [r["compared"]["describes"] for r in records if r["compared"]["describes"]["truth"]]
    kinds = collections.Counter(component_class_key(d["truth"]) for d in known)
    per_kind = {k: _ratio(sum(d["right"] for d in known if component_class_key(d["truth"]) == k), n) for k, n in kinds.items()}
    out["describes"] = {"records": len(known), "accuracy": _ratio(sum(d["right"] for d in known), len(known)),
                        "majority_baseline": _ratio(max(kinds.values(), default=0), len(known)),
                        "per_entity_class_average": _ratio(sum(per_kind.values()), len(per_kind))}
    return out


#: The numbers that get a margin: (path in numbers(), label).
WITH_MARGIN = [((level, key), f"{level}: {key}") for level in LEVELS
               for key in ("precision", "recall", "f1", "strict_precision", "strict_recall", "strict_f1",
                           "entity_class_accuracy", "recall_within_reach", "strict_recall_within_reach")] + \
              [(("recall_upper_bound",), "recall upper bound"), (("strict_recall_upper_bound",), "strict recall upper bound"),
               (("describes", "accuracy"), "describes accuracy")]


def _get(d: dict, path: tuple):
    for p in path:
        d = d.get(p) if isinstance(d, dict) else None
    return d


def with_margins(records: list) -> dict:
    """numbers(records), each number in WITH_MARGIN turned into
    {"value", "low", "high"} (low/high None below MIN_RECORDS)."""
    point = numbers(records)
    enough = len(records) >= MIN_RECORDS
    samples = {path: [] for path, _ in WITH_MARGIN}
    if enough:
        rng = random.Random(SEED)
        by_stratum = collections.defaultdict(list)
        for r in records:
            by_stratum[r["stratum"]].append(r)
        strata = [by_stratum[g] for g in sorted(by_stratum)]
        for _ in range(REDRAWS):
            drawn = [rng.choice(g) for g in strata for _ in g]
            n = numbers(drawn)
            for path, _ in WITH_MARGIN:
                v = _get(n, path)
                if v is not None:
                    samples[path].append(v)
    for path, _ in WITH_MARGIN:
        value = _get(point, path)
        low = high = None
        vals = sorted(samples[path])
        if enough and vals:
            low, high = vals[int(0.025 * (len(vals) - 1))], vals[int(round(0.975 * (len(vals) - 1)))]
        target = point
        for p in path[:-1]:
            target = target[p]
        target[path[-1]] = {"value": value, "low": low, "high": high}
    point["margins"] = enough
    return point


#: Below this proportion of the catalog evaluated, drawing with repeats from a
#: finite catalog changes the margin negligibly (a rule of survey sampling:
#: Cochran, Sampling Techniques, 1977, chapter 2).
FINITE_NEGLIGIBLE = 0.05


def margin_checks(records: list, point: dict, catalog_records: int) -> dict:
    """The margin of error's assumptions that can be checked on the evaluated
    records (070_evaluate/metrics.md, Sampling error): strata with
    only one evaluated record (they add no spread to the redraws), metrics
    whose range reaches 0% or 100% (where a percentile range is unreliable),
    the largest record's proportion of the triples, and the proportion of the
    catalog evaluated."""
    sizes = collections.Counter(r["stratum"] for r in records)
    alone = sorted(g or "(no stratum)" for g, k in sizes.items() if k == 1)
    at_bound = [label for path, label in WITH_MARGIN
                if (m := _get(point, path)) and m.get("low") is not None and (m["low"] <= 0 or m["high"] >= 1)]
    largest = {}
    for key, what in (("extracted", "extracted triples"), ("gt", "ground truth triples")):
        total = sum(r["compared"]["counts"][key] for r in records)
        top = max(records, key=lambda r: r["compared"]["counts"][key])
        largest[what] = {"record": top["id"], "proportion": _ratio(top["compared"]["counts"][key], total)}
    return {"single_record_strata": alone, "at_bound": at_bound, "largest_record": largest,
            "catalog_proportion": _ratio(len(records), catalog_records)}


def by_part(evaluated) -> dict:
    return {part: [r for r in evaluated.records if r["part"] == part] for part in ("tuning", "held-out")}


def strata_table(records: list, pool_strata: dict) -> list:
    """Per stratum: records evaluated, share of evaluated vs share of the
    pool, and its numbers when it has enough records."""
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
                     "numbers": with_margins(recs) if len(recs) >= MIN_RECORDS else None})
    return rows


def describes_confusion(records: list) -> dict:
    """{(truth, said): records}."""
    c = collections.Counter()
    for r in records:
        d = r["compared"]["describes"]
        if d["truth"]:
            c[(d["truth"], d["said"] or "(none named)")] += 1
    return dict(c)


def compute_metrics(evaluated, settings: dict) -> dict:
    """Every number, per part: the tuning part always; the held-out part only
    with the setting evaluate_held_out. {part: {"numbers", "strata", "confusion"},
    "kept_aside": {part: records not shown}}."""
    parts = by_part(evaluated)
    shown = ["tuning"] + (["held-out"] if settings["evaluate_held_out"] else [])
    result = {}
    for part in shown:
        recs = parts[part]
        numbers = with_margins(recs) if recs else None
        result[part] = {"numbers": numbers,
                        "strata": strata_table(recs, evaluated.pool_strata) if recs else [],
                        "confusion": describes_confusion(recs),
                        "margin_checks": margin_checks(recs, numbers, evaluated.catalog_records)
                        if numbers and numbers["margins"] else None}
    result["kept_aside"] = {p: len(parts[p]) for p in ("tuning", "held-out") if p not in shown}
    return result
