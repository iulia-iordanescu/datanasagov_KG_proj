"""Evaluation's report (070_evaluate_helpers/stats.py and moves.py): precision and recall per predicate and per
entity class, and per record, on a case worked out by hand; the part's numbers pooled, not averaged over records;
what 060 removed, per reason."""
import unittest

from support import use_step

use_step("070_evaluate")
import moves                                     # noqa: E402
import pairing                                   # noqa: E402
import stats                                     # noqa: E402
from test_evaluate_pairing import counts_record, record, translation, triple   # noqa: E402

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


class PerRecord(unittest.TestCase):
    """Each record's own numbers, on the case above: 5 occurrences, 3 ground truth triples; exact pairs e0-g0 and
    e1-g1, partial pair e3-g2; strict: e0 (exact) and e3 (partial), since e1's subject class is wrong; all 3 ground
    truth triples within reach and within strict reach."""
    def setUp(self):
        self.r = dict(compared(), position=3, part="tuning", stratum="g",
                      title="MODIS and AIRS aboard Aqua: a title longer than fifty characters")

    def test_numbers(self):
        (row,) = stats.per_record([self.r])
        self.assertEqual((row["id"], row["position"], row["occurrences"], row["ground_truth_triples"],
                          row["counted_against"], row["recall_upper_bound"], row["strict_recall_upper_bound"]),
                         ("r1", 3, 5, 3, 4, 1.0, 1.0))                        # 5 + 3 - 2 x 2 exact pairs
        self.assertEqual(row["exact"], {"pairs": 2, "strict_pairs": 1, "precision": 2 / 5, "recall": 2 / 3,
                                        "f1": 4 / 8, "strict_precision": 1 / 5, "strict_recall": 1 / 3,
                                        "strict_f1": 2 / 8, "recall_within_reach": 2 / 3,
                                        "strict_recall_within_reach": 1 / 3})
        self.assertEqual(row["partial"], {"pairs": 3, "strict_pairs": 2, "precision": 3 / 5, "recall": 1.0,
                                          "f1": 6 / 8, "strict_precision": 2 / 5, "strict_recall": 2 / 3,
                                          "strict_f1": 4 / 8, "recall_within_reach": 1.0,
                                          "strict_recall_within_reach": 2 / 3})

    def test_worst_first_then_pool_position(self):
        perfect = [triple("MODIS", "Instrument", "ABOARD", "Aqua", "Spacecraft")]
        recs = [dict(compared(perfect, perfect, rid="good"), position=0, title=""),
                dict(compared(rid="late"), position=9, title=""), dict(compared(rid="early"), position=5, title="")]
        self.assertEqual([(x["id"], x["counted_against"]) for x in stats.per_record(recs)],
                         [("early", 4), ("late", 4), ("good", 0)])

    def test_no_value(self):
        """A record with no occurrences: no precision; with no ground truth triples: no recall, no upper bound."""
        (row,) = stats.per_record([dict(compared(GT, [], rid="none said"), position=0, title="")])
        self.assertEqual((row["exact"]["precision"], row["exact"]["recall"], row["exact"]["f1"]), (None, 0.0, 0.0))
        (row,) = stats.per_record([dict(compared([], EXTRACTED[:1], rid="no truth"), position=0, title="")])
        self.assertEqual((row["exact"]["precision"], row["exact"]["recall"], row["recall_upper_bound"],
                          row["exact"]["recall_within_reach"]), (0.0, None, None, None))
        text = "\n".join(moves._per_record_lines([row]))
        self.assertIn("| 0 | `no truth` |  | 1 | 0 | 1 | no value | no value | 0 | 0 | 0% | no value | 0% |", text)

    def test_report_table(self):
        text = "\n".join(moves._per_record_lines(stats.per_record([self.r])))
        self.assertIn("never averaged into them (`070_evaluate/metrics.md`, *Pooled, not averaged*)", text)
        self.assertIn("| Pool position | Record id (first 8 characters) | Title (first 50 characters) | Occurrences | "
                      "Ground truth triples | Counted against it (exact) | Recall upper bound | Strict recall upper "
                      "bound | Pairs (exact) | Strict pairs (exact) | Precision (exact) | Recall (exact) | F1 (exact) | "
                      "Precision (strict exact) | Recall (strict exact) | F1 (strict exact) | Recall within reach "
                      "(exact) | Recall within reach (strict exact) | Pairs (partial) | Strict pairs (partial) | "
                      "Precision (partial) | Recall (partial) | F1 (partial) | Precision (strict partial) | Recall "
                      "(strict partial) | F1 (strict partial) | Recall within reach (partial) | Recall within reach "
                      "(strict partial) |", text)
        self.assertIn("| 3 | `r1` | MODIS and AIRS aboard Aqua: a title longer than fi\u2026 | 5 | 3 | 4 | 100% | 100% | "
                      "2 | 1 | 40% | 67% | 50% | 20% | 33% | 25% | 67% | 33% | "
                      "3 | 2 | 60% | 100% | 75% | 40% | 67% | 50% | 100% | 67% |", text)
        many = stats.per_record([dict(compared(rid=f"r{i}"), position=i, title="") for i in range(moves.SHOW + 2)])
        self.assertIn("| \u2026 2 more, in `metrics.json` and `per_record.md` |", "\n".join(moves._per_record_lines(many)))
        self.assertEqual(moves._per_record_lines([])[-2], "| none |" + " |" * 27)

    def test_block_in_per_record_md(self):
        text = moves._per_record([self.r], 0)
        block = ("Occurrences 5 \u00b7 ground truth triples 3 \u00b7 counted against it (exact) 4 \u00b7 recall "
                 "upper bound 100% \u00b7 strict recall upper bound 100%\n\n"
                 "| | exact | partial | strict exact | strict partial |\n|---|---:|---:|---:|---:|\n"
                 "| Pairs | 2 | 3 | 1 | 2 |\n| Precision | 40% | 60% | 20% | 40% |\n| Recall | 67% | 100% | 33% | 67% |\n"
                 "| F1 | 50% | 75% | 25% | 50% |\n| Recall within reach | 67% | 100% | 33% | 67% |\n")
        self.assertIn(block, text)
        self.assertLess(text.index(block), text.index("**Pairs**"))           # above the record's pairs


class PooledNotAveraged(unittest.TestCase):
    """070_evaluate/metrics.md, *Pooled, not averaged*: record A has 2 ground truth triples and extraction found 2,
    record B has 48 and extraction found 12."""
    def test_part_pools_and_differs_from_the_mean_of_the_records(self):
        recs = [counts_record(2, 2, 2, 2, id="A", position=0), counts_record(12, 48, 12, 12, id="B", position=1)]
        pooled = stats.numbers(recs)["exact"]["recall"]
        own = [x["exact"]["recall"] for x in stats.per_record(recs)]
        self.assertAlmostEqual(pooled, 14 / 50)
        self.assertEqual(sorted(own), [0.25, 1.0])
        self.assertAlmostEqual(sum(own) / len(own), 0.625)
        self.assertNotAlmostEqual(pooled, sum(own) / len(own))


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
