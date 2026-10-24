"""
stats.py -- stage 4: the numbers, each with its margin of error. Code only, no model.

Every number is a ratio of sums over the evaluated records (e.g. precision =
pairs in all records / occurrences in all records), so a record with many
triples weighs more than one with few, as each triple is one answer. What
each number is, its formula and how to read it: 070_evaluate/metrics.md and
the files it lists (precision, recall, F1, entity-class accuracy, the recall
upper bound, recall within reach, and the describes metrics).

MARGIN OF ERROR, by the bootstrap (070_evaluate/metrics/approximately.md,
Sampling error): the numbers are recomputed REDRAWS times, each time from as
many records as were evaluated, drawn at random, with repeats, from all the
evaluated ones together; the middle 95% of the results is the margin. It draws
WHOLE RECORDS (a record's triples come from one text and one model call, so
they succeed or fail together; drawing triples one by one would give margins
too narrow). It draws from all strata together, NOT within each stratum: the
evaluated records are the first records of the shuffled pool, so how many come
from each stratum is itself random, and the redraws let it vary the same way
(redrawing within strata of 1 or 2 records would give margins too narrow). It
is valid only for a random sample (records.py evaluates only the fair sample)
of enough records: below MIN_RECORDS, no margin is given, only a plain
warning. The draws are seeded, so a rerun gives the same margins.
"""
from __future__ import annotations

import collections
import random

from pairing import LEVELS, PER_COMPONENT_CLASS
from common.triples_io import component_class_key

#: Fewer evaluated records than this: no margin of error (a bootstrap on very
#: few records gives margins that are themselves unreliable, usually too
#: narrow). A rule of thumb, not a law; the report says so.
MIN_RECORDS = 20
REDRAWS = 1000
SEED = 70
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
                      "subject_class_accuracy": _ratio(total[f"{level}_subject_class_pairs"], m),
                      "object_class_accuracy": _ratio(total[f"{level}_object_class_pairs"], m),
                      "subject_class_pairs": total[f"{level}_subject_class_pairs"],
                      "object_class_pairs": total[f"{level}_object_class_pairs"],
                      "recall_within_reach": _ratio(total[f"{level}_pairs_within_reach"], total["within_reach"]),
                      "strict_recall_within_reach": _ratio(sw, total["within_strict_reach"]),
                      "pairs": m, "strict_pairs": s, "pairs_within_reach": total[f"{level}_pairs_within_reach"],
                      "strict_pairs_within_reach": sw}
    known = [r["compared"]["describes"] for r in records if r["compared"]["describes"]["truth"]]
    describes_classes = collections.Counter(component_class_key(d["truth"]) for d in known)
    per_describes_class = {k: _ratio(sum(d["right"] for d in known if component_class_key(d["truth"]) == k), n) for k, n in describes_classes.items()}
    out["describes"] = {"records": len(known), "accuracy": _ratio(sum(d["right"] for d in known), len(known)),
                        "majority_baseline": _ratio(max(describes_classes.values(), default=0), len(known)),
                        "per_entity_class_average": _ratio(sum(per_describes_class.values()), len(per_describes_class))}
    return out


#: The numbers that get a margin: (path in numbers(), label).
WITH_MARGIN = [((level, key), f"{level}: {key}") for level in LEVELS
               for key in ("precision", "recall", "f1", "strict_precision", "strict_recall", "strict_f1",
                           "entity_class_accuracy", "subject_class_accuracy", "object_class_accuracy",
                           "recall_within_reach", "strict_recall_within_reach")] + \
              [(("recall_upper_bound",), "recall upper bound"), (("strict_recall_upper_bound",), "strict recall upper bound"),
               (("describes", "accuracy"), "describes accuracy")]


def _get(d: dict, path: tuple):
    for p in path:
        d = d.get(p) if isinstance(d, dict) else None
    return d


def _middle_95(vals: list) -> tuple:
    """The middle 95% of sorted redraw results: (low, high)."""
    return vals[int(0.025 * (len(vals) - 1))], vals[int(round(0.975 * (len(vals) - 1)))]


def with_margins(records: list) -> dict:
    """numbers(records), each number in WITH_MARGIN turned into
    {"value", "low", "high"} (low/high None below MIN_RECORDS)."""
    point = numbers(records)
    enough = len(records) >= MIN_RECORDS
    samples = {path: [] for path, _ in WITH_MARGIN}
    if enough:
        rng = random.Random(SEED)
        for _ in range(REDRAWS):
            drawn = [rng.choice(records) for _ in records]
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
            low, high = _middle_95(vals)
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
    records (070_evaluate/metrics/approximately.md, Sampling error): metrics
    whose range reaches 0% or 100% (where a percentile range is unreliable),
    the largest record's proportion of the triples, and the proportion of the
    catalog evaluated."""
    at_bound = [label for path, label in WITH_MARGIN
                if (m := _get(point, path)) and m.get("low") is not None and (m["low"] <= 0 or m["high"] >= 1)]
    largest = {}
    for key, what in (("extracted", "extracted triples"), ("gt", "ground truth triples")):
        total = sum(r["compared"]["counts"][key] for r in records)
        top = max(records, key=lambda r: r["compared"]["counts"][key])
        largest[what] = {"record": top["id"], "proportion": _ratio(top["compared"]["counts"][key], total)}
    return {"at_bound": at_bound, "largest_record": largest,
            "catalog_proportion": _ratio(len(records), catalog_records)}


def by_part(evaluated) -> dict:
    return {part: [r for r in evaluated.records if r["part"] == part] for part in ("tuning", "held-out")}


def strata_table(records: list, pool_strata: dict) -> list:
    """Per stratum: records evaluated, proportion of the evaluated records vs proportion of the
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


def twins(records: list) -> dict | None:
    """The twins among records (records.py) and the numbers without them: {"records": [{"id", "kind"}],
    "without": with_margins(the others), or None when there is no twin or no other}. None when which records are
    twins isn't known."""
    if any(r.get("twin") is None for r in records):
        return None
    twin = [{"id": r["id"], "kind": r["twin"]} for r in records if r["twin"]]
    rest = [r for r in records if not r["twin"]]
    return {"records": twin, "without": with_margins(rest) if twin and rest else None}


def _component_class_numbers(c) -> dict:
    """Precision and recall at each level from summed counts."""
    return {level: {"precision": _ratio(c[f"{level}_pairs"], c["occurrences"]),
                    "recall": _ratio(c[f"{level}_pairs"], c["ground_truth_triples"])} for level in LEVELS}


def per_component_class(records: list) -> dict:
    """Precision and recall per predicate, per subject class, and per object class (each of the ground truth
    schema, or of the current schema marked as translating to (none)), at each pair level, over records' counts
    (pairing.component_class_counts), each with its margin of error from the same redraws of whole records as the other
    numbers (none below MIN_RECORDS). {table: [row]}, each row {"component_class", "occurrences",
    "ground_truth_triples", "counted_against" (occurrences and ground truth triples with no exact pair that counts
    for it), "<level>": {"pairs", "precision", "recall"} (each a {"value", "low", "high"})}, sorted by
    counted_against, most first: what the component class costs at the exact level, so the frequent and badly
    extracted ones come first, and one seen once can cost at most two."""
    per_record = [r["compared"]["component_class_counts"] for r in records]
    labels = {}
    for x in reversed(per_record):           # the spelling first met
        labels.update(x["labels"])
    total = collections.defaultdict(collections.Counter)
    for x in per_record:
        for key, c in x["counts"].items():
            total[key].update(c)
    enough = len(records) >= MIN_RECORDS
    samples = collections.defaultdict(list)
    if enough:
        rng = random.Random(SEED)
        for _ in range(REDRAWS):
            drawn = collections.defaultdict(collections.Counter)
            for x in (rng.choice(per_record) for _ in records):
                for key, c in x["counts"].items():
                    drawn[key].update(c)
            for key in total:
                for level, m in _component_class_numbers(drawn.get(key, collections.Counter())).items():
                    for what, v in m.items():
                        if v is not None:
                            samples[(key, level, what)].append(v)
    out = {table: [] for table, _ in PER_COMPONENT_CLASS}
    for key, c in total.items():
        row = {"component_class": labels[key], "occurrences": c["occurrences"],
               "ground_truth_triples": c["ground_truth_triples"],
               "counted_against": c["occurrences"] + c["ground_truth_triples"] - 2 * c["exact_pairs"]}
        for level, m in _component_class_numbers(c).items():
            row[level] = {"pairs": c[f"{level}_pairs"]}
            for what, v in m.items():
                vals = sorted(samples.get((key, level, what), []))
                low = high = None
                if enough and vals:
                    low, high = _middle_95(vals)
                row[level][what] = {"value": v, "low": low, "high": high}
        out[key[0]].append(row)
    for rows in out.values():
        rows.sort(key=lambda r: (-r["counted_against"], component_class_key(r["component_class"])))
    return out


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
    with the setting evaluate_held_out. {part: {"numbers", "strata", "confusion", "per_component_class", "removed_by_060", ...},
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
                        "per_component_class": per_component_class(recs),
                        "removed_by_060": removed_by_reason(recs),
                        "margin_checks": margin_checks(recs, numbers, evaluated.catalog_records)
                        if numbers and numbers["margins"] else None,
                        "twins": twins(recs)}
    result["kept_aside"] = {p: len(parts[p]) for p in ("tuning", "held-out") if p not in shown}
    return result
