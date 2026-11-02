"""Step 070's numbers by the ground truth's provenance (070_evaluate/070_evaluate.md, *Shared-model bias*): by the
second opinion (annotations/second_opinion.csv, read by common/common_helpers/second_opinion.py: found in at least one
repeat, found in none, not checked) and by who drafted the ground truth (its column drafted_by). Per group the counts
and the numbers (recall, exact share, entity-class accuracy, attributed precision, F1, by the stated formulas, each
with its clustered Wilson interval), how many triples were found in 0, 1, ..., N repeats, the report's tables, nothing
when no triple was checked, and a wrong grouping refused; spellings of one model name together, other versions apart,
an empty or blank drafted_by as a person's row, a group with no pairs. The helper that writes the second-opinion file:
tests/test_second_opinion.py."""
import unittest

from support import use_step

use_step("070_evaluate")
import moves                                     # noqa: E402
import pairing                                   # noqa: E402
import readings                                  # noqa: E402
import stats                                     # noqa: E402
from common.second_opinion import FOUND, NOT_CHECKED, NOT_FOUND, counts, groups_of, key_of, repeats_of   # noqa: E402
from test_evaluate_pairing import record, translation, triple                      # noqa: E402


class Evaluation(unittest.TestCase):

    def compared(self, groups, repeats=None):
        gt = [triple("MODIS", "Instrument", "ABOARD", "Aqua", "Spacecraft"),
              triple("AIRS", "Instrument", "ABOARD", "Aqua", "Spacecraft"),
              triple("CERES", "Instrument", "ABOARD", "Aqua", "Spacecraft")]
        ex = [triple("MODIS", "Instrument", "ABOARD", "Aqua", "Spacecraft"),             # pairs with gt 0
              triple("AIRS", "Instrument", "ABOARD", "Aqua", "Spacecraft"),              # pairs with gt 1
              triple("OMI", "Instrument", "ABOARD", "Aura", "Spacecraft")]               # extracted only
        r = record(gt, ex)
        if groups is not None:
            r["second_opinion"] = groups
        if repeats is not None:
            r["second_opinion_repeats"] = repeats
        return pairing.compare_record(r, translation())

    def test_counts_and_numbers(self):
        r = self.compared([FOUND, NOT_FOUND, NOT_FOUND])
        g = r["compared"]["groups"]["second_opinion"]
        self.assertEqual((g[FOUND]["gt"], g[NOT_FOUND]["gt"]), (1, 2))
        self.assertNotIn(NOT_CHECKED, g)                                                    # no triple of the record in it
        self.assertEqual((g[FOUND]["exact_pairs"], g[NOT_FOUND]["exact_pairs"], g[NOT_FOUND]["partial_pairs"]), (1, 1, 1))
        by = stats.with_margins([r], provenance=True)["second_opinion"]
        self.assertEqual(by[FOUND]["gt_triples"], 1)
        self.assertEqual(by[FOUND]["partial"]["recall"]["value"], 1.0)                      # 1 pair ÷ 1 triple
        self.assertAlmostEqual(by[NOT_FOUND]["partial"]["recall"]["value"], 1 / 2)          # 1 pair ÷ 2 triples
        # precision for a group: its pairs ÷ (3 occurrences − the other groups' pairs): found 1 ÷ (3 − 1), not found 1 ÷ (3 − 1)
        self.assertAlmostEqual(by[FOUND]["partial"]["precision"]["value"], 1 / 2)
        self.assertAlmostEqual(by[FOUND]["partial"]["f1"]["value"], 2 * 1 / (2 + 1))
        self.assertAlmostEqual(by[NOT_FOUND]["partial"]["f1"]["value"], 2 * 1 / (2 + 2))
        self.assertEqual(by[FOUND]["exact_share"]["value"], 1.0)                            # both pairs are exact
        self.assertEqual(by[FOUND]["partial"]["entity_class_accuracy"]["value"], 1.0)
        self.assertIsNone(by[NOT_CHECKED]["partial"]["recall"]["value"])                    # no triple: no value
        self.assertEqual(by[NOT_CHECKED]["partial"]["precision"]["value"], 0.0)              # 0 ÷ (3 − 2): unpaired OMI
        self.assertIsNone(by[NOT_CHECKED]["exact_share"]["value"])                           # a group with no pairs
        self.assertIsNone(by[NOT_CHECKED]["partial"]["entity_class_accuracy"]["value"])
        self.assertNotIn("second_opinion", stats.with_margins([r]))                         # only a part's numbers have it
        self.assertNotIn("second_opinion", stats.numbers([r]))                              # nor per record

    def test_none_when_nothing_checked(self):
        """No second-opinion file (no group given) or no triple checked: no second-opinion numbers, no table; who
        drafted the ground truth is still reported."""
        for groups in (None, [NOT_CHECKED] * 3):
            r = self.compared(groups)
            self.assertEqual(r["compared"]["groups"]["second_opinion"][NOT_CHECKED]["gt"], 3)
            n = stats.with_margins([r], provenance=True)
            self.assertIsNone(n["second_opinion"])
            self.assertEqual(moves._second_opinion_lines(n, []), [])
            self.assertIsNotNone(n["drafted_by"])

    def test_kept_counts_without_groups(self):
        """A run kept from before the groups (helpers/compare_runs.py rebuilds records with counts only): None."""
        r = self.compared(None)
        del r["compared"]["groups"]
        self.assertIsNone(stats.by_group([r], "second_opinion"))
        self.assertIsNone(stats.by_group([r], "drafted_by"))

    def test_wrong_groups_refused(self):
        with self.assertRaises(ValueError):
            self.compared([FOUND, NOT_FOUND])                                                 # one short
        with self.assertRaises(ValueError):
            self.compared(["maybe", FOUND, FOUND])

    def test_report_table(self):
        n = stats.with_margins([self.compared([FOUND, NOT_FOUND, NOT_CHECKED])], provenance=True)
        lines = "\n".join(moves._second_opinion_lines(n, ["gemini-4-argon"]))
        self.assertIn(f"#### {moves.SECOND_OPINION_SECTION}", lines)
        self.assertIn("`gemini-4-argon`", lines)
        self.assertIn(moves.GROUP_FORMULA, lines)
        self.assertIn("not a true per-group precision", lines)
        self.assertIn("| found by the second opinion | 1 | 1 | 100% | 100% | 100% | 100% |", lines)
        self.assertIn("| not found by the second opinion | 1 | 1 | 100% | 100% | 100% | 100% |", lines)
        self.assertIn(f"| not checked by the second opinion | 1 | 1 | 0% | 0% | {readings.NO_VALUE} | "
                      f"{readings.NO_VALUE} | 0% | 0% |", lines)                            # a group with no pairs
        self.assertIn("at least one repeat", lines)
        self.assertNotIn("Found in 0", lines)                                               # no repeats given: no spread table

    def test_found_in_how_many_repeats(self):
        """The spread of found_in_repeats per model and number of repeats, summed over records; a model with fewer repeats on
        some records counted under its own number; the report's table padded to the most repeats."""
        a = self.compared([FOUND, NOT_FOUND, FOUND], [{"m": (3, 3)}, {"m": (0, 3), "k": (0, 1)}, {"m": (1, 3)}])
        b = self.compared([FOUND, FOUND, NOT_CHECKED], [{"m": (2, 3)}, {"m": (1, 2)}, {}])
        spread = stats.numbers([a, b])["second_opinion_repeats"]
        self.assertEqual(spread, [{"model": "k", "repeats": 1, "gt_triples": 1, "found_in_repeats": [1, 0]},
                                  {"model": "m", "repeats": 2, "gt_triples": 1, "found_in_repeats": [0, 1, 0]},
                                  {"model": "m", "repeats": 3, "gt_triples": 4, "found_in_repeats": [1, 1, 1, 1]}])
        lines = "\n".join(moves._second_opinion_lines(stats.with_margins([a, b], provenance=True), ["k", "m"]))
        self.assertIn("| Model | Repeats | Ground truth triples | Found in 0 | Found in 1 | Found in 2 | Found in 3 |", lines)
        self.assertIn("| `m` | 3 | 4 | 1 | 1 | 1 | 1 |", lines)
        self.assertIn("| `k` | 1 | 1 | 1 | 0 | | |", lines)
        self.assertEqual(stats.numbers([self.compared(None)])["second_opinion_repeats"], [])

    def test_groups_from_the_file(self):
        table = {key_of("r1", triple("MODIS", "Instrument", "ABOARD", "Aqua", "Spacecraft")):
                 {"by": {"m": counts(3, 1, 0), "n": counts(1, 0, 0)}},                       # found in 1 of 3 repeats of m
                 key_of("r1", triple("AIRS", "Instrument", "ABOARD", "Aqua", "Spacecraft")):
                 {"by": {"m": counts(3, 0, 0)}}}                                              # in none
        gt = [triple("the MODIS", "instrument", "aboard", "Aqua", "spacecraft"),   # evened out as 070's exact pairs compare
              triple("AIRS", "Instrument", "ABOARD", "Aqua", "Spacecraft"),
              triple("CERES", "Instrument", "ABOARD", "Aqua", "Spacecraft")]
        self.assertEqual(groups_of("r1", gt, table), [FOUND, NOT_FOUND, NOT_CHECKED])
        self.assertEqual(groups_of("r2", gt, table), [NOT_CHECKED] * 3)
        self.assertEqual(repeats_of("r1", gt, table), [{"m": (1, 3), "n": (0, 1)}, {"m": (0, 3)}, {}])


class DraftedBy(unittest.TestCase):
    """The numbers by who drafted the ground truth (column drafted_by): spellings of one model name together, other
    versions apart, an empty or blank cell as a person's row, a group with no pairs, the ranges, and the report."""

    def compared(self, drafted, rid="r1", ex=None):
        names = ("MODIS", "AIRS", "CERES", "AMSU")
        gt = [{**triple(n, "Instrument", "ABOARD", "Aqua", "Spacecraft"), "drafted_by": d}
              for n, d in zip(names, drafted)]
        ex = ex if ex is not None else [
            triple("MODIS", "Instrument", "ABOARD", "Aqua", "Spacecraft"),               # exact, strict, with gt 0
            triple("AIRS", "Sensor", "ABOARD", "Aqua", "Spacecraft"),                    # exact, not strict, with gt 1
            triple("CERES instrument", "Instrument", "ABOARD", "Aqua", "Spacecraft"),    # partial, with gt 2
            triple("OMI", "Instrument", "ABOARD", "Aura", "Spacecraft")]                 # extracted only
        return pairing.compare_record(record(gt, ex, rid=rid), translation(entity=("Instrument", "Sensor", "Spacecraft")))

    def test_spellings_and_people(self):
        r = self.compared(["claude-opus-5.5", "Claude-Opus-5-5", "", "  "])
        g = r["compared"]["groups"]["drafted_by"]
        self.assertEqual(set(g), {"claude-opus-5-5", pairing.DRAFTED_BY_PERSON})            # two spellings, one model
        self.assertEqual((g["claude-opus-5-5"]["gt"], g[""]["gt"]), (2, 2))                # blank = empty: a person
        self.assertEqual(r["compared"]["drafted_by_spellings"]["claude-opus-5-5"], ["Claude-Opus-5-5", "claude-opus-5.5"])

    def test_near_misses_stay_apart(self):
        g = self.compared(["claude-opus-5-5", "claude-opus-5", "gemini-2.5-pro", "gemini-4-argon"])["compared"]["groups"]["drafted_by"]
        self.assertEqual(set(g), {"claude-opus-5-5", "claude-opus-5", "gemini-2-5-pro", "gemini-4-argon"})

    def test_numbers(self):
        r = self.compared(["gemini-2.5-pro", "gemini-2.5-pro", "claude-opus-5.5", ""])
        by = stats.by_group([r], "drafted_by")
        self.assertEqual(list(by), ["gemini-2-5-pro", "claude-opus-5-5", ""])              # most triples first, people last
        gem, cl, person = by["gemini-2-5-pro"], by["claude-opus-5-5"], by[""]
        self.assertEqual(gem["spellings"], ["gemini-2.5-pro"])
        self.assertEqual(gem["exact"]["recall"]["value"], 1.0)                              # MODIS and AIRS, exact
        self.assertEqual(gem["exact_share"]["value"], 1.0)
        self.assertEqual(gem["exact"]["entity_class_accuracy"]["value"], 0.5)               # AIRS: Sensor, not Instrument
        # attributed precision: 2 pairs ÷ (4 occurrences − 1 pair of the other groups)
        self.assertAlmostEqual(gem["partial"]["precision"]["value"], 2 / 3)
        self.assertAlmostEqual(gem["partial"]["f1"]["value"], 2 * 2 / (3 + 2))
        self.assertEqual((cl["exact"]["recall"]["value"], cl["partial"]["recall"]["value"]), (0.0, 1.0))
        self.assertEqual(cl["exact_share"]["value"], 0.0)                                   # its one pair is partial
        self.assertAlmostEqual(cl["partial"]["precision"]["value"], 1 / 2)                 # 1 ÷ (4 − 2 − 0 + ... ) = 1 ÷ 2
        # a group with no pairs: recall 0, exact share and entity-class accuracy no value, precision 0
        self.assertEqual(person["partial"]["recall"]["value"], 0.0)
        self.assertIsNone(person["exact_share"]["value"])
        self.assertIsNone(person["partial"]["entity_class_accuracy"]["value"])
        self.assertEqual(person["partial"]["precision"]["value"], 0.0)
        self.assertIsNone(gem["exact"]["recall"]["low"])                                    # one record: no range

    def test_ranges_over_records(self):
        """The clustered Wilson interval over the records, one group's parts per record; a record with none of the
        group's triples adds nothing to its recall but still to its attributed precision."""
        a = self.compared(["gemini-2.5-pro", "", "", ""], rid="a")
        b = self.compared(["", "gemini-2.5-pro", "gemini-2.5-pro", ""], rid="b")
        c = self.compared(["", "", "", ""], rid="c")
        by = stats.by_group([a, b, c], "drafted_by")
        rec = by["gemini-2-5-pro"]["partial"]["recall"]
        self.assertEqual(rec, {**rec, **{k: v for k, v in stats.clustered_wilson([(1, 1), (2, 2), (0, 0)]).items()
                                         if k in ("value", "low", "high", "n_eff", "deff")}})
        self.assertEqual(by["gemini-2-5-pro"]["records"], 2)
        prec = by["gemini-2-5-pro"]["partial"]["precision"]
        self.assertEqual(prec["value"], stats.clustered_wilson([(1, 4 - 2), (2, 4 - 1), (0, 4 - 3)])["value"])
        self.assertTrue(prec["few_records"])

    def test_report(self):
        r = self.compared(["claude-opus-5.5", "claude-opus-5-5", "gemini-2.5-pro", ""])
        n = stats.with_margins([r], provenance=True)
        lines = "\n".join(moves._drafted_by_lines(n, "claude-opus-5-5"))
        self.assertIn(f"#### {moves.DRAFTED_BY_SECTION}", lines)
        self.assertIn(moves.GROUP_FORMULA, lines)
        self.assertIn("| drafted by `claude-opus-5-5` or `claude-opus-5.5` (the extraction model's name) | 2 | 1 |", lines)
        self.assertIn("| drafted by `gemini-2.5-pro` | 1 | 1 |", lines)
        self.assertIn("| written by a person (`drafted_by` empty) | 1 | 1 | 0% | 0% |", lines)
        self.assertNotIn("extraction model's name", "\n".join(moves._drafted_by_lines(n, "gpt-4o")))
        self.assertEqual(moves._drafted_by_lines({"drafted_by": None}, ""), [])

    def test_in_a_parts_numbers(self):
        """compute_metrics gives both groupings in the part's numbers (so in metrics.json)."""
        n = stats.with_margins([self.compared(["gemini-2.5-pro"] * 4)], provenance=True)
        self.assertIn("drafted_by", n)
        self.assertIn("second_opinion", n)


if __name__ == "__main__":
    unittest.main()
