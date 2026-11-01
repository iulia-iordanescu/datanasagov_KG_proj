"""Step 070 and the second opinion (annotations/second_opinion.csv, read by common/common_helpers/second_opinion.py):
each ground truth triple's group (found in at least one run, found in none, not checked), the counts and the numbers
per group (recall, precision, partial F1, by the stated formula), how many triples were found in 0, 1, ..., N runs,
the report's tables, nothing when no triple was checked, and a wrong grouping refused. The helper that writes the
file: tests/test_second_opinion.py."""
import unittest

from support import use_step

use_step("070_evaluate")
import moves                                     # noqa: E402
import pairing                                   # noqa: E402
import stats                                     # noqa: E402
from common.second_opinion import FOUND, NOT_CHECKED, NOT_FOUND, counts, groups_of, key_of, runs_of   # noqa: E402
from test_evaluate_pairing import record, translation, triple                      # noqa: E402


class Evaluation(unittest.TestCase):

    def compared(self, groups, runs=None):
        gt = [triple("MODIS", "Instrument", "ABOARD", "Aqua", "Spacecraft"),
              triple("AIRS", "Instrument", "ABOARD", "Aqua", "Spacecraft"),
              triple("CERES", "Instrument", "ABOARD", "Aqua", "Spacecraft")]
        ex = [triple("MODIS", "Instrument", "ABOARD", "Aqua", "Spacecraft"),             # pairs with gt 0
              triple("AIRS", "Instrument", "ABOARD", "Aqua", "Spacecraft"),              # pairs with gt 1
              triple("OMI", "Instrument", "ABOARD", "Aura", "Spacecraft")]               # extracted only
        r = record(gt, ex)
        if groups is not None:
            r["second_opinion"] = groups
        if runs is not None:
            r["second_opinion_runs"] = runs
        return pairing.compare_record(r, translation())

    def test_counts_and_numbers(self):
        r = self.compared([FOUND, NOT_FOUND, NOT_FOUND])
        c = r["compared"]["counts"]
        self.assertEqual((c["gt_found"], c["gt_not_found"], c["gt_not_checked"]), (1, 2, 0))
        self.assertEqual((c["exact_pairs_found"], c["exact_pairs_not_found"], c["partial_pairs_not_found"]), (1, 1, 1))
        by = stats.numbers([r])["second_opinion"]
        self.assertEqual(by[FOUND]["gt_triples"], 1)
        self.assertEqual(by[FOUND]["partial"]["recall"], 1.0)                               # 1 pair ÷ 1 triple
        self.assertAlmostEqual(by[NOT_FOUND]["partial"]["recall"], 1 / 2)                  # 1 pair ÷ 2 triples
        # precision for a group: its pairs ÷ (3 occurrences − the other groups' pairs): found 1 ÷ (3 − 1), not found 1 ÷ (3 − 1)
        self.assertAlmostEqual(by[FOUND]["partial"]["precision"], 1 / 2)
        self.assertAlmostEqual(by[FOUND]["partial"]["f1"], 2 * 1 / (2 + 1))
        self.assertAlmostEqual(by[NOT_FOUND]["partial"]["f1"], 2 * 1 / (2 + 2))
        self.assertIsNone(by[NOT_CHECKED]["partial"]["recall"])
        self.assertIn("second_opinion", stats.with_margins([r]))                        # kept in metrics.json

    def test_none_when_nothing_checked(self):
        for groups in (None, [NOT_CHECKED] * 3):
            r = self.compared(groups)
            self.assertEqual(r["compared"]["counts"]["gt_not_checked"], 3)
            self.assertIsNone(stats.numbers([r])["second_opinion"])
            self.assertEqual(moves._second_opinion_lines(stats.numbers([r]), []), [])

    def test_wrong_groups_refused(self):
        with self.assertRaises(ValueError):
            self.compared([FOUND, NOT_FOUND])                                                 # one short
        with self.assertRaises(ValueError):
            self.compared(["maybe", FOUND, FOUND])

    def test_report_table(self):
        n = stats.numbers([self.compared([FOUND, NOT_FOUND, NOT_CHECKED])])
        lines = "\n".join(moves._second_opinion_lines(n, ["gemini-4-argon"]))
        self.assertIn(f"#### {moves.SECOND_OPINION_SECTION}", lines)
        self.assertIn("`gemini-4-argon`", lines)
        self.assertIn(moves.SECOND_OPINION_FORMULA, lines)
        self.assertIn("| found by the second opinion | 1 | 100% | 100% | 1 |", lines)
        self.assertIn("| not found by the second opinion | 1 | 100% | 100% | 1 |", lines)
        self.assertIn("| not checked by the second opinion | 1 | 0% | 0% | 0 |", lines)
        self.assertIn("at least one run", lines)
        self.assertNotIn("Found in 0", lines)                                               # no runs given: no spread table

    def test_found_in_how_many_runs(self):
        """The spread of found_in_runs per model and number of runs, summed over records; a model with fewer runs on
        some records counted under its own number; the report's table padded to the most runs."""
        a = self.compared([FOUND, NOT_FOUND, FOUND], [{"m": (3, 3)}, {"m": (0, 3), "k": (0, 1)}, {"m": (1, 3)}])
        b = self.compared([FOUND, FOUND, NOT_CHECKED], [{"m": (2, 3)}, {"m": (1, 2)}, {}])
        spread = stats.numbers([a, b])["second_opinion_runs"]
        self.assertEqual(spread, [{"model": "k", "runs": 1, "gt_triples": 1, "found_in_runs": [1, 0]},
                                  {"model": "m", "runs": 2, "gt_triples": 1, "found_in_runs": [0, 1, 0]},
                                  {"model": "m", "runs": 3, "gt_triples": 4, "found_in_runs": [1, 1, 1, 1]}])
        lines = "\n".join(moves._second_opinion_lines(stats.numbers([a, b]), ["k", "m"]))
        self.assertIn("| Model | Runs | Ground truth triples | Found in 0 | Found in 1 | Found in 2 | Found in 3 |", lines)
        self.assertIn("| `m` | 3 | 4 | 1 | 1 | 1 | 1 |", lines)
        self.assertIn("| `k` | 1 | 1 | 1 | 0 | | |", lines)
        self.assertEqual(stats.numbers([self.compared(None)])["second_opinion_runs"], [])

    def test_groups_from_the_file(self):
        table = {key_of("r1", triple("MODIS", "Instrument", "ABOARD", "Aqua", "Spacecraft")):
                 {"by": {"m": counts(3, 1, 0), "n": counts(1, 0, 0)}},                       # found in 1 of 3 runs of m
                 key_of("r1", triple("AIRS", "Instrument", "ABOARD", "Aqua", "Spacecraft")):
                 {"by": {"m": counts(3, 0, 0)}}}                                              # in none
        gt = [triple("the MODIS", "instrument", "aboard", "Aqua", "spacecraft"),   # evened out as 070's exact pairs compare
              triple("AIRS", "Instrument", "ABOARD", "Aqua", "Spacecraft"),
              triple("CERES", "Instrument", "ABOARD", "Aqua", "Spacecraft")]
        self.assertEqual(groups_of("r1", gt, table), [FOUND, NOT_FOUND, NOT_CHECKED])
        self.assertEqual(groups_of("r2", gt, table), [NOT_CHECKED] * 3)
        self.assertEqual(runs_of("r1", gt, table), [{"m": (1, 3), "n": (0, 1)}, {"m": (0, 3)}, {}])


if __name__ == "__main__":
    unittest.main()
