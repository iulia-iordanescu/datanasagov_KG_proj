"""Step 070's margin of error (070_evaluate_helpers/stats.py, clustered_wilson; 070_evaluate/metrics/approximately.md,
Sampling error): the Student t quantiles it needs, the worked checks of the guide, the edge cases (no records with
anything to divide by, one record, every record at 0% or 100%), the measured coverage on synthetic records, and
the repeats pooled by py helpers/compare_runs.py."""
import importlib.util
import math
import random
import unittest

from support import ROOT, use_step

use_step("070_evaluate")
import stats                                     # noqa: E402

#: The coverage simulation's settings (approximately.md quotes the numbers it prints): a record has 1 + Poisson(6)
#: occurrences, and a success rate of its own, Beta(2.8, 1.2) (mean 0.7, intracluster correlation 1 / (2.8 + 1.2 + 1)
#: = 0.2); each occurrence is correct with its record's rate. SAMPLES samples of each size, seeded.
TRUE, ALPHA, BETA, MEAN_SIZE, SAMPLES, SEED = 0.7, 2.8, 1.2, 6, 3000, 70
SIZES = (5, 10, 20, 28, 40)


def _poisson(rng, lam: float) -> int:
    limit, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= rng.random()
        if p <= limit:
            return k
        k += 1


def synthetic_records(rng, n: int) -> list:
    """n records' (a_r, b_r): b_r occurrences, a_r of them correct."""
    out = []
    for _ in range(n):
        b = 1 + _poisson(rng, MEAN_SIZE)
        rate = rng.betavariate(ALPHA, BETA)
        out.append((sum(rng.random() < rate for _ in range(b)), b))
    return out


def coverage(n: int, samples: int = SAMPLES, seed: int = SEED) -> float:
    """The proportion of the samples of n synthetic records whose 95% clustered Wilson interval holds TRUE."""
    rng = random.Random(seed + n)
    hits = 0
    for _ in range(samples):
        ci = stats.clustered_wilson(synthetic_records(rng, n))
        hits += ci["low"] <= TRUE <= ci["high"]
    return hits / samples


class TQuantile(unittest.TestCase):
    def test_table_values(self):
        for df, t in ((1, 12.7062), (2, 4.3027), (5, 2.5706), (10, 2.2281), (19, 2.0930), (29, 2.0452), (99, 1.9842)):
            with self.subTest(df=df):
                self.assertAlmostEqual(stats.t_quantile(0.975, df), t, places=4)


class ClusteredWilson(unittest.TestCase):
    def test_worked_checks(self):
        """The guide's two checks: 20 records of 7 correct in 10 (no clustering: deff floored to 1), and the same
        totals as 10 records at 10/10 and 10 at 4/10 (clustered: deff 4.5, a wider range)."""
        even = stats.clustered_wilson([(7, 10)] * 20)
        self.assertEqual((even["value"], even["deff"]), (0.7, 1.0))
        self.assertAlmostEqual(even["n_eff"], 175.4, places=1)
        self.assertEqual((round(even["low"], 3), round(even["high"], 3)), (0.628, 0.763))
        clustered = stats.clustered_wilson([(10, 10)] * 10 + [(4, 10)] * 10)
        self.assertAlmostEqual(clustered["deff"], 4.51, places=2)
        self.assertAlmostEqual(clustered["n_eff"], 38.9, places=1)
        self.assertEqual((round(clustered["low"], 3), round(clustered["high"], 3)), (0.543, 0.821))
        self.assertGreater(clustered["high"] - clustered["low"], even["high"] - even["low"])

    def test_edge_cases(self):
        self.assertEqual(stats.clustered_wilson([])["value"], None)
        self.assertEqual(stats.clustered_wilson([(0, 0), (0, 0)])["value"], None)          # nothing to divide by
        one = stats.clustered_wilson([(3, 4)])
        self.assertEqual((one["value"], one["low"], one["high"]), (0.75, None, None))       # one record: no range
        self.assertEqual(stats.clustered_wilson([(3, 4), (0, 0)])["low"], None)              # near miss: b = 0 isn't one
        two = stats.clustered_wilson([(3, 4), (1, 4)])
        self.assertIsNotNone(two["low"])                                                     # from 2 records on
        # every record at 100%: each record counts as one trial (our choice), so 3 records x 100 give no 99%
        full = stats.clustered_wilson([(100, 100)] * 3)
        self.assertEqual((full["value"], full["deff"], full["high"]), (1.0, None, 1.0))
        self.assertAlmostEqual(full["n_eff"], 3 * (stats.Z / stats.t_quantile(0.975, 2)) ** 2)
        self.assertLess(full["low"], 0.5)
        zero = stats.clustered_wilson([(0, 5)] * 4)
        self.assertEqual((zero["value"], zero["low"]), (0.0, 0.0))
        self.assertLess(zero["high"], 1.0)

    def test_value_is_the_pooled_ratio(self):
        """The interval's value is numbers()'s: one home for each formula (stats.RATIO_PARTS)."""
        self.assertEqual([p for p, _ in stats.WITH_MARGIN], list(stats.RATIO_PARTS))


class Coverage(unittest.TestCase):
    def test_coverage(self):
        """A tripwire, not a claim: the measured coverage is at least 0.85 at 20 and 40 records. The numbers it prints
        are the ones approximately.md quotes."""
        measured = {n: coverage(n) for n in SIZES}
        print("\nclustered Wilson coverage, " + ", ".join(f"n = {n}: {c:.3f}" for n, c in measured.items()))
        self.assertGreaterEqual(measured[20], 0.85)
        self.assertGreaterEqual(measured[40], 0.85)


class PooledRepeats(unittest.TestCase):
    """py helpers/compare_runs.py, *Pooled over the repeats*: the record stays the cluster, its parts the means over
    the K repeats, so the value is that of pooling all the counts, and the range is narrower than one run's."""

    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("compare_runs", ROOT / "helpers" / "compare_runs.py")
        cls.cr = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.cr)

    @staticmethod
    def kept_run(run_id: str, pairs: list) -> dict:
        records = []
        for i, (m, n) in enumerate(pairs):
            counts = {"extracted": n, "untranslatable": 0, "gt": n, "within_reach": n, "within_strict_reach": n}
            for level in ("exact", "partial"):
                counts.update({f"{level}_pairs": m, f"{level}_strict_pairs": m, f"{level}_subject_class_pairs": m,
                               f"{level}_object_class_pairs": m, f"{level}_pairs_within_reach": m,
                               f"{level}_strict_pairs_within_strict_reach": m, f"{level}_pending_pairs": 0})
            records.append({"id": f"r{i:02d}", "counts": counts, "describes": {"truth": "D", "said": "D", "right": True}})
        return {"run_id": run_id, "records": records}

    def test_pooled(self):
        rng = random.Random(7)
        sizes = [rng.randint(3, 12) for _ in range(20)]
        runs = [self.kept_run(f"R{k}", [(rng.randint(0, n), n) for n in sizes]) for k in range(3)]
        ids = [r["id"] for r in runs[0]["records"]]
        rows = {r["label"]: r for r in self.cr.pooled(runs, ids)}
        p = rows["exact: precision"]
        total_pairs = sum(r["counts"]["exact_pairs"] for run in runs for r in run["records"])
        self.assertAlmostEqual(p["value"], total_pairs / (3 * sum(sizes)))
        one = stats.with_margins(self.cr.as_records(runs[0], ids))["exact"]["precision"]
        self.assertLess(p["high"] - p["low"], one["high"] - one["low"])
        self.assertIsNotNone(p["between"])
        self.assertIsNotNone(p["within"])


if __name__ == "__main__":
    unittest.main()
