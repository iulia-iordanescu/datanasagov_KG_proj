"""
stats.py -- stage 4: the numbers, each with its margin of error. Code only, no model.

Every number is a ratio of sums over the evaluated records (e.g. precision =
pairs in all records / triples extracted in all records), so a record with
many triples weighs more than one with few, as each triple is one answer.

  precision        pairs / extracted triples
  recall           pairs / ground truth triples
  (both at the two name levels, exact and partial, and for all pairs and
   STRICT pairs, i.e. with both entity classes right too)
  entity-class accuracy   strict pairs / pairs
  schema ceiling          ground truth triples within reach / all of them
  recall within reach     pairs whose ground truth triple is within reach /
                          ground truth triples within reach
  describes accuracy      records whose DESCRIBES entity class is right /
                          records where the ground truth names one; with
                          the MAJORITY BASELINE (the share of the most common
                          kind: what always guessing it would get) and the
                          PER-KIND average (each kind's accuracy, averaged)

MARGIN OF ERROR, by the bootstrap: the numbers are recomputed RESHUFFLES
times, each time from records drawn at random, with repeats, from the evaluated
ones; the middle 95% of the results is the margin. It draws WHOLE RECORDS
(a record's triples come from one text and one model call, so they succeed or
fail together; drawing triples one by one would give margins too narrow), and
draws WITHIN EACH SAMPLING GROUP, as many as the group has, the way the pool
was drawn. It is valid only for a random sample (records.py metrics only the
fair part) of enough records: below MIN_RECORDS, no margin is given, only a
plain warning. The draws are seeded, so a rerun gives the same margins.
"""
from __future__ import annotations

import collections
import random

from pairing import LEVELS
from common.triples_io import label_key

#: Fewer evaluated records than this: no margin of error (a bootstrap on very
#: few records gives margins that are themselves unreliable, usually too
#: narrow). A rule of thumb, not a law; the report says so.
MIN_RECORDS = 20
RESHUFFLES = 1000
SEED = 70
#: A sampling group whose share of the evaluated records differs from its share
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
           "within_reach": total["within_reach"],
           "schema_ceiling": _ratio(total["within_reach"], total["gt"])}
    for level in LEVELS:
        m, s = total[f"{level}_pairs"], total[f"{level}_strict_pairs"]
        out[level] = {"precision": _ratio(m, total["extracted"]), "recall": _ratio(m, total["gt"]),
                      "strict_precision": _ratio(s, total["extracted"]), "strict_recall": _ratio(s, total["gt"]),
                      "entity_class_accuracy": _ratio(s, m),
                      "recall_within_reach": _ratio(total[f"{level}_pairs_within_reach"], total["within_reach"]),
                      "pairs": m, "strict_pairs": s, "pairs_within_reach": total[f"{level}_pairs_within_reach"]}
    known = [r["compared"]["describes"] for r in records if r["compared"]["describes"]["truth"]]
    kinds = collections.Counter(label_key(d["truth"]) for d in known)
    per_kind = {k: _ratio(sum(d["right"] for d in known if label_key(d["truth"]) == k), n) for k, n in kinds.items()}
    out["describes"] = {"records": len(known), "accuracy": _ratio(sum(d["right"] for d in known), len(known)),
                        "majority_baseline": _ratio(max(kinds.values(), default=0), len(known)),
                        "per_kind_average": _ratio(sum(per_kind.values()), len(per_kind))}
    return out


#: The numbers that get a margin: (path in numbers(), label).
WITH_MARGIN = [((level, key), f"{level}: {key}") for level in LEVELS
               for key in ("precision", "recall", "strict_precision", "strict_recall",
                           "entity_class_accuracy", "recall_within_reach")] + \
              [(("schema_ceiling",), "schema ceiling"), (("describes", "accuracy"), "describes accuracy")]


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
        by_group = collections.defaultdict(list)
        for r in records:
            by_group[r["group"]].append(r)
        groups = [by_group[g] for g in sorted(by_group)]
        for _ in range(RESHUFFLES):
            drawn = [rng.choice(g) for g in groups for _ in g]
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


def by_part(evaluated) -> dict:
    return {part: [r for r in evaluated.records if r["part"] == part] for part in ("tuning", "held-out")}


def group_table(records: list, pool_groups: dict) -> list:
    """Per sampling group: records evaluated, share of evaluated vs share of the
    pool, and its numbers when it has enough records."""
    total_pool = sum(pool_groups.values())
    by_group = collections.defaultdict(list)
    for r in records:
        by_group[r["group"]].append(r)
    rows = []
    for g in sorted(set(pool_groups) | set(by_group), key=lambda g: (-pool_groups.get(g, 0), g)):
        recs = by_group.get(g, [])
        rows.append({"group": g or "(no group)", "records": len(recs),
                     "share_evaluated": _ratio(len(recs), len(records)),
                     "share_pool": _ratio(pool_groups.get(g, 0), total_pool),
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
    with the setting evaluate_held_out. {part: {"numbers", "groups", "confusion"},
    "kept_aside": {part: records not shown}}."""
    parts = by_part(evaluated)
    shown = ["tuning"] + (["held-out"] if settings["evaluate_held_out"] else [])
    result = {}
    for part in shown:
        recs = parts[part]
        result[part] = {"numbers": with_margins(recs) if recs else None,
                        "groups": group_table(recs, evaluated.pool_groups) if recs else [],
                        "confusion": describes_confusion(recs)}
    result["kept_aside"] = {p: len(parts[p]) for p in ("tuning", "held-out") if p not in shown}
    return result
