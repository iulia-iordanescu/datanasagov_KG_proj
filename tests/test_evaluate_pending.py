"""Evaluation and the facts that wait on an expert (annotations/pending_triples.csv, read by
common/common_helpers/left_out.py's read_pending): an extracted triple matching one is left out of precision's
denominator, never counted for recall, never paired across records, and never counted twice; the report says so,
and the recipe records it, so py helpers/compare_runs.py shows it."""
import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from support import ROOT, use_step

use_step("070_evaluate")
import moves                                     # noqa: E402
import pairing                                   # noqa: E402
import stats                                     # noqa: E402
from common.left_out import NO_TRIPLE, PENDING_COLUMNS, WAITS, read_pending   # noqa: E402
from common.partial_reviews import EXTRACTED_ONLY, MATCHES_WAITING            # noqa: E402
from test_evaluate_pairing import record, translation, triple                 # noqa: E402

CLASSES = ["Instrument", "Spacecraft", "Dataset", "Algorithm", "Purpose"]
PREDICATES = ["ABOARD", "ACQUIRED_BY_INSTRUMENT", "HAS_PURPOSE"]
GT = [triple("MODIS", "Instrument", "ABOARD", "Aqua", "Spacecraft")]
WAITING = {**triple("SF", "Algorithm", "HAS_PURPOSE", "ensemble analysis", "Purpose"),
           "id": "r1", "source_text": "SF allows for an ensemble analysis", "left_out": "\"SF\" HAS_PURPOSE",
           "question": "Q9 (d)"}
EXTRACTED = [triple("MODIS", "Instrument", "ABOARD", "Aqua", "Spacecraft"),              # pairs with the ground truth
             triple("SF", "Algorithm", "HAS_PURPOSE", "ensemble analysis", "Purpose"),    # matches the waiting fact
             triple("MODIS", "Instrument", "ABOARD", "Terra", "Spacecraft")]              # extracted only


def compared(gt=GT, extracted=EXTRACTED, pending=(WAITING,), rid="r1"):
    r = record(gt, extracted, rid=rid)
    r.update({"pending": [p for p in pending if p["id"] == rid], "position": 0, "title": "T " + rid})
    return pairing.compare_record(r, translation(CLASSES, PREDICATES))


class Pairing(unittest.TestCase):
    def test_paired_with_the_waiting_fact(self):
        c = compared()["compared"]
        self.assertEqual(c["pairs"], [(0, 0, "exact")])
        self.assertEqual(c["pending_pairs"], [(0, 1, "exact")])
        self.assertEqual((c["counts"]["exact_pending_pairs"], c["counts"]["partial_pending_pairs"], c["counts"]["pending"]),
                         (1, 1, 1))

    def test_partial_level_too(self):
        ex = EXTRACTED[:1] + [triple("the SF", "Algorithm", "HAS_PURPOSE", "an ensemble analysis of AGN", "Purpose")]
        c = compared(extracted=ex)["compared"]
        self.assertEqual(c["pending_pairs"], [(0, 1, "partial")])
        self.assertEqual((c["counts"]["exact_pending_pairs"], c["counts"]["partial_pending_pairs"]), (0, 1))

    def test_ground_truth_first(self):
        """An occurrence that pairs with a ground truth triple is never also counted as matching a waiting fact."""
        same = {**WAITING, **triple("MODIS", "Instrument", "ABOARD", "Aqua", "Spacecraft")}
        c = compared(extracted=EXTRACTED[:1], pending=(same,))["compared"]
        self.assertEqual(c["pairs"], [(0, 0, "exact")])
        self.assertEqual(c["pending_pairs"], [])
        self.assertEqual(c["counts"]["exact_pending_pairs"], 0)

    def test_another_records_fact_never_pairs(self):
        other = {**WAITING, "id": "r2"}
        c = compared(pending=(other,))["compared"]
        self.assertEqual(c["pending_pairs"], [])
        self.assertEqual(c["counts"]["pending"], 0)

    def test_one_partner_each(self):
        """Two occurrences of the waiting fact: one pairs, the other stays extracted only (a fact stated twice earns
        one pair, as with ground truth triples)."""
        c = compared(extracted=EXTRACTED + [EXTRACTED[1]])["compared"]
        self.assertEqual(len(c["pending_pairs"]), 1)


class Numbers(unittest.TestCase):
    def test_precision_leaves_them_out_recall_unchanged(self):
        n = stats.numbers([compared()])
        none = stats.numbers([compared(pending=())])
        for level in pairing.LEVELS:
            self.assertAlmostEqual(n[level]["precision"], 1 / 2)          # 1 pair ÷ (3 occurrences − 1 waiting)
            self.assertAlmostEqual(none[level]["precision"], 1 / 3)       # without it: 1 ÷ 3
            self.assertEqual(n[level]["recall"], none[level]["recall"])   # 1 ÷ 1 either way
            self.assertAlmostEqual(n[level]["f1"], 2 * 1 / (2 + 1))      # 2 × pairs ÷ (counted occurrences + gt)
            self.assertAlmostEqual(n[level]["strict_precision"], 1 / 2)
            self.assertEqual(n[level]["counted_occurrences"], 2)
        self.assertEqual((n["extracted"], n["pending"]), (3, 1))

    def test_header_only_changes_nothing(self):
        a = stats.numbers([compared(pending=())])
        r = record(GT, EXTRACTED)
        r.update(position=0, title="T")                                    # no "pending" key at all
        b = stats.numbers([pairing.compare_record(r, translation(CLASSES, PREDICATES))])
        self.assertEqual(a, b)

    def test_per_record_and_per_component_class(self):
        row = stats.per_record([compared()])[0]
        self.assertAlmostEqual(row["exact"]["precision"], 1 / 2)
        self.assertEqual(row["pending_pairs"], 1)
        self.assertEqual(row["counted_against"], 3 - 1 + 1 - 2)            # occurrences − waiting + gt − 2 × pairs
        tables = stats.per_component_class([compared()])
        purpose = next(r for r in tables["predicate"] if r["component_class"] == "HAS_PURPOSE")
        self.assertEqual((purpose["occurrences"], purpose["pending_pairs"], purpose["counted_against"]), (1, 1, 0))
        self.assertIsNone(purpose["exact"]["precision"]["value"])          # 0 pairs ÷ (1 − 1): nothing to divide

    def test_margins_use_the_same_formula(self):
        recs = [compared(rid=f"r{i}", pending=({**WAITING, "id": f"r{i}"},)) for i in range(stats.MIN_RECORDS)]
        n = stats.with_margins(recs)
        self.assertAlmostEqual(n["exact"]["precision"]["value"], 1 / 2)
        self.assertEqual((n["exact"]["precision"]["low"], n["exact"]["precision"]["high"]), (0.5, 0.5))


class Report(unittest.TestCase):
    def test_section_lists_the_pair(self):
        r = compared()
        n = stats.numbers([r])
        lines = "\n".join(moves._waiting_lines(n, [r]))
        self.assertIn(f"#### {moves.WAITING_SECTION}", lines)
        self.assertIn("Extracted triples matching facts that wait on an expert", lines)
        self.assertIn("SF (Algorithm) HAS_PURPOSE ensemble analysis (Purpose)", lines)
        self.assertIn("Q9 (d)", lines)
        self.assertIn("1 at the exact level", lines.replace("Occurrences left out of precision: ", ""))

    def test_section_when_none(self):
        r = compared(pending=())
        self.assertIn("None: no fact of these records waits on an expert.", "\n".join(moves._waiting_lines(stats.numbers([r]), [r])))

    def test_formula_stated(self):
        self.assertIn("Precision = pairs ÷ (occurrences − occurrences paired with a fact that waits on an expert)",
                      moves.PRECISION_FORMULA)

    def test_compared_rows_and_per_record(self):
        r = {**compared(), "part": "tuning", "stratum": "g"}
        for i, f in enumerate(r["extracted"]):
            f["_position"] = i
        statuses = [x["status"] for x in moves._compared_rows([r])]
        self.assertEqual(statuses.count(MATCHES_WAITING), 1)
        self.assertEqual(statuses.count(EXTRACTED_ONLY), 1)                 # the waiting match is not extracted only
        waiting = next(x for x in moves._compared_rows([r]) if x["status"] == MATCHES_WAITING)
        self.assertEqual((waiting["waiting_object"], waiting["waiting_question"]), ("ensemble analysis", "Q9 (d)"))
        page = moves._per_record([r], 0)
        self.assertIn("**Matching a fact that waits on an expert**", page)
        extracted_only = page.split("**Extracted only**")[1]
        self.assertNotIn("HAS_PURPOSE", extracted_only)


class Recipe(unittest.TestCase):
    def evaluated(self, pending):
        return SimpleNamespace(extraction_made={}, schema_used={}, pending=list(pending))

    def test_recorded_and_shown_by_compare_runs(self):
        import importlib.util
        t = translation(CLASSES, PREDICATES)
        a = moves._recipe(self.evaluated([]), t, {})
        b = moves._recipe(self.evaluated([WAITING]), t, {})
        field = b["evaluation (070)"]["facts_waiting_on_an_expert"]
        self.assertEqual((field["excluded_from_precision"], field["pending_triples"]), (True, 1))
        self.assertNotEqual(field["sha256"], a["evaluation (070)"]["facts_waiting_on_an_expert"]["sha256"])
        spec = importlib.util.spec_from_file_location("compare_runs", ROOT / "helpers" / "compare_runs.py")
        cr = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cr)
        diffs = dict(cr.differences([{"recipe": a}, {"recipe": b}]))
        self.assertEqual(diffs["evaluation (070) / facts_waiting_on_an_expert / pending_triples"], ["0", "1"])
        old = {"recipe": {"evaluation (070)": {"git_commit": None}}}               # a run from before the exclusion
        self.assertIn("evaluation (070) / facts_waiting_on_an_expert / excluded_from_precision",
                      dict(cr.differences([old, {"recipe": b}])))


LEFT_OUT = """# Left out on purpose

Intro.

## "T" (pool position 0, id r1)

2 items, none that may matter.

- **Left out:** "SF" HAS_PURPOSE
  - **Rule:** What counts as a fact, rule 2: "{waits}". Q9.
- **Left out:** "time domain"
  - **Rule:** What counts as a fact, rule 2: "{waits}". Q28.
  - {note} it needs a predicate to coin.
"""


class Reader(unittest.TestCase):
    """read_pending: the file's format, and its agreement with left_out.md."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="kg_pending_"))
        self.addCleanup(shutil.rmtree, self.tmp)
        self.write_left_out()

    def write_left_out(self, note=NO_TRIPLE):
        (self.tmp / "left_out.md").write_text(LEFT_OUT.format(waits=WAITS, note=note), encoding="utf-8")

    def read(self, *rows, header=",".join(PENDING_COLUMNS)):
        import csv
        path = self.tmp / "pending_triples.csv"
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(header + "\n")
            csv.writer(fh).writerows([[row[c] for c in PENDING_COLUMNS] for row in rows])
        return read_pending(path, self.tmp / "left_out.md")

    def test_valid(self):
        rows = self.read(WAITING)
        self.assertEqual([(r["id"], r["object"], r["line"]) for r in rows], [("r1", "ensemble analysis", 2)])

    def bad(self, words, *rows, **kw):
        with self.assertRaises(ValueError) as e:
            self.read(*rows, **kw)
        self.assertIn(words, str(e.exception))
        return str(e.exception)

    def test_wrong_left_out_words(self):
        said = self.bad("has the words", {**WAITING, "left_out": "\"SF\" HAS_PURPOSES"})
        self.assertIn("pending_triples.csv, line 2", said)

    def test_record_without_a_section(self):
        self.bad("has no section", {**WAITING, "id": "r9"})

    def test_item_that_doesnt_wait(self):
        text = LEFT_OUT.format(waits=WAITS, note=NO_TRIPLE).replace(
            f'rule 2: "{WAITS}". Q9.', 'rule 9: "A ground truth triple needs a subject".')
        (self.tmp / "left_out.md").write_text(text, encoding="utf-8")
        self.bad("doesn't wait on an expert", WAITING)

    def test_waiting_item_without_row_or_note(self):
        self.bad("waits on an expert but has no row")                        # the SF item, header only
        self.write_left_out(note="Something else:")
        said = self.bad("waits on an expert but has no row", WAITING)        # the time-domain item lost its note
        self.assertIn("left_out.md, line 11", said)

    def test_header_twice_and_empty(self):
        self.bad("the header must be", WAITING, header="id,subject")
        self.bad("the same row as line 2", WAITING, WAITING)
        self.bad("no value in question", {**WAITING, "question": ""})

    def test_the_real_files_agree(self):
        """The repository's own pending_triples.csv and left_out.md, read only."""
        real = ROOT / "annotations" / "pending_triples.csv"
        if not real.exists():
            self.skipTest("annotations/pending_triples.csv isn't written yet")
        rows = read_pending(real, ROOT / "annotations" / "left_out.md")
        self.assertTrue(all(r["question"].startswith("Q") for r in rows))


if __name__ == "__main__":
    unittest.main()
