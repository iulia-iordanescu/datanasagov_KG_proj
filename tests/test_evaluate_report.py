"""Evaluation's report (070_evaluate_helpers/stats.py and moves.py): precision and recall per predicate and per
entity class, on a case worked out by hand; what 060 removed, per reason."""
import unittest

from support import use_step

use_step("070_evaluate")
import moves                                     # noqa: E402
import pairing                                   # noqa: E402
import stats                                     # noqa: E402
from test_evaluate_pairing import record, translation, triple   # noqa: E402

# Worked out by hand. The translation table: every component class below translates to itself; USES_GADGET and
# Gadget (current schema) have rows that say (none).
CLASSES = ["Instrument", "Spacecraft", "Dataset", "MissionName"]
PREDICATES = ["ABOARD", "ACQUIRED_BY_INSTRUMENT", "ALSO_KNOWN_AS"]
GT = [triple("MODIS", "Instrument", "ABOARD", "Aqua", "Spacecraft"),                                   # g0
      triple("AIRS", "Instrument", "ABOARD", "Aqua", "Spacecraft"),                                    # g1
      triple("MODIS Snow Cover", "Dataset", "ACQUIRED_BY_INSTRUMENT", "MODIS", "Instrument")]          # g2
EXTRACTED = [triple("MODIS", "Instrument", "ABOARD", "Aqua", "Spacecraft"),          # e0: exact pair with g0
             triple("AIRS", "Dataset", "ABOARD", "Aqua", "Spacecraft"),              # e1: exact pair with g1, subject class wrong
             triple("MODIS", "Instrument", "ABOARD", "Terra", "Spacecraft"),         # e2: extracted only
             triple("Snow Cover", "Dataset", "ACQUIRED_BY_INSTRUMENT", "MODIS", "Instrument"),   # e3: partial pair with g2
             triple("MODIS Snow Cover", "Dataset", "USES_GADGET", "G1", "Gadget")]   # e4: extracted only, (none) rows
NONE = pairing.NO_TRANSLATION


def compared(gt=GT, extracted=EXTRACTED, rid="r1"):
    return pairing.compare_record(record(gt, extracted, rid=rid), translation(CLASSES, PREDICATES))


def rows(tables, table):
    """{component class: (occurrences, ground truth triples, counted against, exact pairs, partial-level pairs,
    exact precision, exact recall, partial precision, partial recall)}, in the table's order."""
    return {r["component_class"]: (r["occurrences"], r["ground_truth_triples"], r["counted_against"],
                                   r["exact"]["pairs"], r["partial"]["pairs"],
                                   r["exact"]["precision"]["value"], r["exact"]["recall"]["value"],
                                   r["partial"]["precision"]["value"], r["partial"]["recall"]["value"])
            for r in tables[table]}


class PerComponentClass(unittest.TestCase):
    def setUp(self):
        self.tables = stats.per_component_class([compared()])

    def test_per_predicate(self):
        got = rows(self.tables, "predicate")
        self.assertEqual(got, {
            "ACQUIRED_BY_INSTRUMENT": (1, 1, 2, 0, 1, 0.0, 0.0, 1.0, 1.0),
            "ABOARD": (3, 2, 1, 2, 2, 2 / 3, 1.0, 2 / 3, 1.0),
            f"USES_GADGET{NONE}": (1, 0, 1, 0, 0, 0.0, None, 0.0, None)})
        self.assertEqual(list(got), ["ACQUIRED_BY_INSTRUMENT", "ABOARD", f"USES_GADGET{NONE}"])  # most counted against first

    def test_per_subject_class(self):
        # e1's wrong subject class: against Dataset's precision (extraction named it) and Instrument's recall (the
        # ground truth has it), though e1 and g1 are a pair
        got = rows(self.tables, "subject class")
        self.assertEqual(got, {
            "Dataset": (3, 1, 4, 0, 1, 0.0, 0.0, 1 / 3, 1.0),
            "Instrument": (2, 2, 2, 1, 1, 0.5, 0.5, 0.5, 0.5)})
        self.assertEqual(list(got), ["Dataset", "Instrument"])

    def test_per_object_class(self):
        got = rows(self.tables, "object class")
        self.assertEqual(got, {
            "Instrument": (1, 1, 2, 0, 1, 0.0, 0.0, 1.0, 1.0),
            f"Gadget{NONE}": (1, 0, 1, 0, 0, 0.0, None, 0.0, None),
            "Spacecraft": (3, 2, 1, 2, 2, 2 / 3, 1.0, 2 / 3, 1.0)})
        self.assertEqual(list(got), ["Instrument", f"Gadget{NONE}", "Spacecraft"])

    def test_counts_agree_with_the_totals(self):
        """Each table's occurrences, ground truth triples, and predicate pairs add up to the part's counts."""
        c = compared()["compared"]["counts"]
        for table in ("predicate", "subject class", "object class"):
            self.assertEqual(sum(r["occurrences"] for r in self.tables[table]), c["extracted"])
            self.assertEqual(sum(r["ground_truth_triples"] for r in self.tables[table]), c["gt"])
        for level in pairing.LEVELS:
            self.assertEqual(sum(r[level]["pairs"] for r in self.tables["predicate"]), c[f"{level}_pairs"])
            self.assertEqual(sum(r[level]["pairs"] for r in self.tables["subject class"]), c[f"{level}_subject_class_pairs"])
            self.assertEqual(sum(r[level]["pairs"] for r in self.tables["object class"]), c[f"{level}_object_class_pairs"])

    def test_swapped_pair_counts_the_way_round_it_was_paired(self):
        """An ALSO_KNOWN_AS occurrence paired with subject and object swapped counts for the entity classes it was
        paired with: Spacecraft as subject class, MissionName as object class."""
        gt = [triple("Aqua", "Spacecraft", "ALSO_KNOWN_AS", "EOS PM-1", "MissionName")]
        ex = [triple("EOS PM-1", "MissionName", "ALSO_KNOWN_AS", "Aqua", "Spacecraft")]
        tables = stats.per_component_class([compared(gt, ex)])
        self.assertEqual(rows(tables, "subject class"), {"Spacecraft": (1, 1, 0, 1, 1, 1.0, 1.0, 1.0, 1.0)})
        self.assertEqual(rows(tables, "object class"), {"MissionName": (1, 1, 0, 1, 1, 1.0, 1.0, 1.0, 1.0)})

    def test_margins_from_20_records(self):
        few = stats.per_component_class([compared(rid=f"r{i}") for i in range(stats.MIN_RECORDS - 1)])
        self.assertIsNone(few["predicate"][0]["exact"]["precision"]["low"])
        other = [triple("MODIS", "Instrument", "ABOARD", "Aqua", "Spacecraft")]
        recs = [compared(rid=f"r{i}") if i % 2 else compared(other, other, rid=f"r{i}") for i in range(stats.MIN_RECORDS)]
        aboard = next(r for r in stats.per_component_class(recs)["predicate"] if r["component_class"] == "ABOARD")
        p = aboard["exact"]["precision"]
        self.assertAlmostEqual(p["value"], (10 * 2 + 10) / (10 * 3 + 10))
        self.assertLess(p["low"], p["value"])
        self.assertGreater(p["high"], p["value"])

    def test_report_tables(self):
        n = {"records": 1, "margins": False}
        text = "\n".join(moves._per_component_class_lines(n, self.tables))
        self.assertIn("**Too few records (1, fewer than 20) for a margin of error", text)
        self.assertIn("| ABOARD | 3 | 2 | 1 | 2 | 67% | 100% | 2 | 67% | 100% |", text)
        self.assertIn("| Dataset | 3 | 1 | 4 | 0 | 0% | 0% | 1 | 33% | 100% |", text)
        self.assertIn(f"| Gadget{NONE} | 1 | 0 | 1 | 0 | 0% | – | 0 | 0% | – |", text)
        n["margins"] = True
        self.assertIn("about 1 in 20 margins misses by chance", "\n".join(moves._per_component_class_lines(n, self.tables)))


class RemovedBy060(unittest.TestCase):
    """What 060's checks removed from the evaluated records, per reason as 060 wrote it."""
    RECORDS = [{"removed": {"source_text": 2, "duplicate": 1}},
               {"removed": {"source_text": 1, "component_class_not_in_schema source_text": 1}},
               {"removed": {}}]

    def test_per_reason(self):
        self.assertEqual(stats.removed_by_reason(self.RECORDS), [
            {"reason": "source_text", "removed": 3, "records": 2},
            {"reason": "component_class_not_in_schema source_text", "removed": 1, "records": 1},
            {"reason": "duplicate", "removed": 1, "records": 1}])

    def test_report_table(self):
        text = "\n".join(moves._removed_lines(3, stats.removed_by_reason(self.RECORDS)))
        self.assertIn("| `source_text` | its source text is missing, or isn't in the record's text | 3 | 2 |", text)
        self.assertIn("| `component_class_not_in_schema source_text` | an entity class or predicate the current schema "
                      "doesn't have and its source text is missing, or isn't in the record's text | 1 | 1 |", text)
        self.assertIn("| all | | 5 | |", text)
        self.assertIn("None: 060 removed nothing from these records.", "\n".join(moves._removed_lines(1, [])))


if __name__ == "__main__":
    unittest.main()
