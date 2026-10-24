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


def strict_rows(tables, table):
    """{component class: (within reach, ground truth triples within strict reach, strict recall upper bound, then at
    each level: strict pairs, F1, strict precision, strict recall, strict F1, strict recall within reach)}."""
    return {r["component_class"]: (r["within_reach"], r["within_strict_reach"], r["strict_recall_upper_bound"]["value"])
            + tuple(x for level in pairing.LEVELS for x in (
                r[level]["strict_pairs"], r[level]["f1"]["value"], r[level]["strict_precision"]["value"],
                r[level]["strict_recall"]["value"], r[level]["strict_f1"]["value"],
                r[level]["strict_recall_within_reach"]["value"]))
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

    def test_strict_f1_and_reach(self):
        """Every component class here is within reach and every ground truth triple within strict reach. Strict:
        e1 pairs with g1 but its subject class is wrong, so it is strict for no row; e0 (exact) and e3 (partial)
        are strict."""
        self.assertEqual(strict_rows(self.tables, "predicate"), {
            "ACQUIRED_BY_INSTRUMENT": (True, 1, 1.0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 1, 1.0, 1.0, 1.0, 1.0, 1.0),
            "ABOARD": (True, 2, 1.0, 1, 0.8, 1 / 3, 0.5, 0.4, 0.5, 1, 0.8, 1 / 3, 0.5, 0.4, 0.5),
            f"USES_GADGET{NONE}": (None, 0, None, 0, 0.0, 0.0, None, 0.0, None, 0, 0.0, 0.0, None, 0.0, None)})
        self.assertEqual(strict_rows(self.tables, "subject class"), {
            "Dataset": (True, 1, 1.0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 1, 0.5, 1 / 3, 1.0, 0.5, 1.0),
            "Instrument": (True, 2, 1.0, 1, 0.5, 0.5, 0.5, 0.5, 0.5, 1, 0.5, 0.5, 0.5, 0.5, 0.5)})
        self.assertEqual(strict_rows(self.tables, "object class"), {
            "Instrument": (True, 1, 1.0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 1, 1.0, 1.0, 1.0, 1.0, 1.0),
            f"Gadget{NONE}": (None, 0, None, 0, 0.0, 0.0, None, 0.0, None, 0, 0.0, 0.0, None, 0.0, None),
            "Spacecraft": (True, 2, 1.0, 1, 0.8, 1 / 3, 0.5, 0.4, 0.5, 1, 0.8, 1 / 3, 0.5, 0.4, 0.5)})

    def test_out_of_reach(self):
        """Checked rows translate only to ABOARD, Instrument, and Spacecraft; extraction says only e0. Then
        ACQUIRED_BY_INSTRUMENT and Dataset (subject class) are out of reach, so g2 is within strict reach for no
        row; Instrument as object class is within reach, but its one ground truth triple (g2) isn't within strict
        reach, since its subject class (Dataset) is out of reach."""
        t = translation(CLASSES, PREDICATES, reachable_entity=["Instrument", "Spacecraft"], reachable_predicates=["ABOARD"])
        tables = stats.per_component_class([pairing.compare_record(record(GT, EXTRACTED[:1]), t)])
        reach = {table: {r["component_class"]: (r["within_reach"], r["within_strict_reach"], r["ground_truth_triples"],
                                                 r["strict_recall_upper_bound"]["value"],
                                                 r["exact"]["strict_recall_within_reach"]["value"])
                         for r in tables[table]} for table in tables}
        self.assertEqual(reach, {
            "predicate": {"ACQUIRED_BY_INSTRUMENT": (False, 0, 1, 0.0, None), "ABOARD": (True, 2, 2, 1.0, 0.5)},
            "subject class": {"Dataset": (False, 0, 1, 0.0, None), "Instrument": (True, 2, 2, 1.0, 0.5)},
            "object class": {"Instrument": (True, 0, 1, 0.0, None), "Spacecraft": (True, 2, 2, 1.0, 0.5)}})
        text = "\n".join(moves._per_component_class_lines({"records": 1, "margins": False}, tables))
        self.assertIn("| ACQUIRED_BY_INSTRUMENT | out of reach; within strict reach: 0 of 1 ground truth triple | 0% | 0 "
                      "| 1 | 1 | 0 | – | 0% | 0% | – | 0% | 0% | no value: none within strict reach | 0 |", text)
        self.assertIn("| Instrument | within reach; within strict reach: 0 of 1 ground truth triple | 0% |", text)

    def test_counts_agree_with_the_totals(self):
        """Each table's occurrences, ground truth triples, and predicate pairs add up to the part's counts."""
        c = compared()["compared"]["counts"]
        for table in ("predicate", "subject class", "object class"):
            self.assertEqual(sum(r["occurrences"] for r in self.tables[table]), c["extracted"])
            self.assertEqual(sum(r["ground_truth_triples"] for r in self.tables[table]), c["gt"])
        for level in pairing.LEVELS:
            self.assertEqual(sum(r[level]["pairs"] for r in self.tables["predicate"]), c[f"{level}_pairs"])
            for table in ("predicate", "subject class", "object class"):       # a strict pair counts for every row it names
                self.assertEqual(sum(r[level]["strict_pairs"] for r in self.tables[table]), c[f"{level}_strict_pairs"])
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
        f = aboard["exact"]["strict_f1"]                          # the strict versions get margins from the same redraws
        self.assertAlmostEqual(f["value"], 2 * (10 + 10) / (10 * 5 + 10 * 2))
        self.assertLess(f["low"], f["value"])
        self.assertEqual(aboard["strict_recall_upper_bound"]["low"], 1.0)   # every redraw: all within strict reach

    def test_report_tables(self):
        n = {"records": 1, "margins": False}
        text = "\n".join(moves._per_component_class_lines(n, self.tables))
        self.assertIn("**Too few records (1, fewer than 20) for a margin of error", text)
        self.assertIn("| Predicate (ground truth schema) | Reach | Strict recall upper bound | Occurrences | Ground truth "
                      "triples | Counted against it (exact) | Exact pairs that count for it | Precision (exact) | Recall "
                      "(exact) | F1 (exact) | Precision (strict exact) | Recall (strict exact) | F1 (strict exact) | "
                      "Recall within reach (strict exact) | Pairs that count for it (partial level) | Precision (partial) "
                      "| Recall (partial) | F1 (partial) | Precision (strict partial) | Recall (strict partial) | F1 "
                      "(strict partial) | Recall within reach (strict partial) |", text)
        self.assertIn("| ABOARD | within reach; within strict reach: 2 of 2 ground truth triples | 100% | 3 | 2 | 1 | 2 | "
                      "67% | 100% | 80% | 33% | 50% | 40% | 50% | 2 | 67% | 100% | 80% | 33% | 50% | 40% | 50% |", text)
        self.assertIn("| Dataset | within reach; within strict reach: 1 of 1 ground truth triple | 100% | 3 | 1 | 4 | 0 | "
                      "0% | 0% | 0% | 0% | 0% | 0% | 0% | 1 | 33% | 100% | 50% | 33% | 100% | 50% | 100% |", text)
        self.assertIn(f"| Gadget{NONE} | none: not in the ground truth schema | – | 1 | 0 | 1 | 0 | 0% | – | 0% | 0% | – | "
                      f"0% | no value: none within strict reach | 0 | 0% | – | 0% | 0% | – | 0% | no value: none within "
                      f"strict reach |", text)
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
