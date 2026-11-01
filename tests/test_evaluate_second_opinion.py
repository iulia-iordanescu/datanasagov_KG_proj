"""Step 070 and the second opinion (annotations/second_opinion.csv, read by common/common_helpers/second_opinion.py):
each ground truth triple's group (found, not found, not checked), the counts and the numbers per group (recall,
precision, partial F1, by the stated formula), the report's table, nothing when no triple was checked, and a wrong
grouping refused. The helper that writes the file: tests/test_second_opinion.py."""
import unittest

from support import use_step

use_step("070_evaluate")
import moves                                     # noqa: E402
import pairing                                   # noqa: E402
import stats                                     # noqa: E402
from common.second_opinion import FOUND, NOT_CHECKED, NOT_FOUND, groups_of, key_of   # noqa: E402
from test_evaluate_pairing import record, translation, triple                      # noqa: E402


class Evaluation(unittest.TestCase):

    def compared(self, groups):
        gt = [triple("MODIS", "Instrument", "ABOARD", "Aqua", "Spacecraft"),
              triple("AIRS", "Instrument", "ABOARD", "Aqua", "Spacecraft"),
              triple("CERES", "Instrument", "ABOARD", "Aqua", "Spacecraft")]
        ex = [triple("MODIS", "Instrument", "ABOARD", "Aqua", "Spacecraft"),             # pairs with gt 0
              triple("AIRS", "Instrument", "ABOARD", "Aqua", "Spacecraft"),              # pairs with gt 1
              triple("OMI", "Instrument", "ABOARD", "Aura", "Spacecraft")]               # extracted only
        r = record(gt, ex)
        if groups is not None:
            r["second_opinion"] = groups
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

    def test_groups_from_the_file(self):
        table = {key_of("r1", triple("MODIS", "Instrument", "ABOARD", "Aqua", "Spacecraft")):
                 {"checked_by": ["m"], "found_by": ["m"], "found_exact_by": []},
                 key_of("r1", triple("AIRS", "Instrument", "ABOARD", "Aqua", "Spacecraft")):
                 {"checked_by": ["m"], "found_by": [], "found_exact_by": []}}
        gt = [triple("the MODIS", "instrument", "aboard", "Aqua", "spacecraft"),   # evened out as 070's exact pairs compare
              triple("AIRS", "Instrument", "ABOARD", "Aqua", "Spacecraft"),
              triple("CERES", "Instrument", "ABOARD", "Aqua", "Spacecraft")]
        self.assertEqual(groups_of("r1", gt, table), [FOUND, NOT_FOUND, NOT_CHECKED])
        self.assertEqual(groups_of("r2", gt, table), [NOT_CHECKED] * 3)


if __name__ == "__main__":
    unittest.main()
