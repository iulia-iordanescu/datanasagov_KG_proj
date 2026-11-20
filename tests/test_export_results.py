"""py helpers/export_results.py on made-up runs: the run list read (tuning and held-out lines, a bad line refused), a
held-out look found its model through its 060 run, the pooled numbers checked by hand (partial F1 = Σ 2 × pairs ÷
Σ (counted occurrences + ground truth triples) over the records and repeats), each file's columns, a run's spread,
060's report parsed (thousands commas, a reason of two words, a cut-off), and the compared triples split into
occurrences and ground truth outcomes. Nothing is written into the repository: the files go to a temporary folder."""
import importlib.util
import shutil
import tempfile
import unittest
from pathlib import Path

from support import ROOT, use_step

use_step("070_evaluate")
spec = importlib.util.spec_from_file_location("export_results", ROOT / "helpers" / "export_results.py")
ex = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ex)
from common.files import read_csv  # noqa: E402


def record(rid, position, pairs, extracted, gt, drafted="model-a"):
    """A record of a kept evaluation, with the counts stats.numbers reads (both pair levels alike)."""
    counts = {"extracted": extracted, "gt": gt, "within_reach": gt, "within_strict_reach": gt,
              **{f"{lv}_{k}": pairs for lv in ("exact", "partial")
                 for k in ("pairs", "strict_pairs", "subject_class_pairs", "object_class_pairs", "pairs_within_reach",
                           "strict_pairs_within_strict_reach")}}
    groups = {"drafted_by": {drafted: {"gt": gt, "exact_pairs": pairs, "exact_strict_pairs": pairs,
                                       "partial_pairs": pairs, "partial_strict_pairs": pairs}}}
    return {"id": rid, "position": position, "stratum": "s", "twin": "", "ground_truth_sha256": "g" + rid,
            "pending_sha256": "p", "translation": {}, "counts": counts, "groups": groups,
            "drafted_by_spellings": {drafted: [drafted]}, "describes": {"truth": "Dataset", "said": "Dataset",
                                                                       "right": True}, "extraction_failed": None}


def run(run_id, run060, repeat, recs, part=None):
    recipe = {"extraction (060)": {"run_id": run060, "settings": {"model": "m", "repeat": repeat},
                                   "model_calls": {"thinking_sent": "low", "served_as": ["m"]}},
              "evaluation (070)": {}}
    out = {"run_id": run_id, "recipe": recipe, "records": recs}
    if part:
        out.update(part=part, look={"extraction_run_id": run060})
    return out


#: Two repeats on two tuning records: record a has 3 pairs of 4 occurrences and 5 ground truth triples, then 1 of 2
#: and 5; record b has 2 of 2 and 2, then 2 of 3 and 2.
TUNING = [run("e1", "x1", 1, [record("a", 0, 3, 4, 5), record("b", 1, 2, 2, 2)]),
          run("e2", "x2", 2, [record("a", 0, 1, 2, 5), record("b", 1, 2, 3, 2)])]
HELD = [run("h1", "x1", 1, [record("c", 5, 1, 1, 1)], part="held-out")]
LIST = ("# schema\tthinking\tmodel\trepeat\trun of 070 (tuning)\trun of 060\n"
        "induced\tlowest\tm\t1\te1\tx1\ninduced\tlowest\tm\t2\te2\tx2\n\nheld-out\th1\n")
REPORT = """- **records extracted:** 2
Chosen: the 2 finished tuning record(s). Extracted: 2; failed: 0.
| listed (each well-formed item once: kept + removed by a check) | 2 | 1 | 1,203 | 602.0 | 602.0 | 849.9 | 1,204 | 0 |
| kept (extracted triples) | 2 | 1 | 1,200 | 600.5 | 600.5 | 847.8 | 1,201 | 0 |
- Removed: 1,003 (component_class_not_in_schema 1,000, component_class_not_in_schema source_text 3), in `x`.
| sent, not from the cache | 1,234 |
| sent, read from the cache (billed at a fraction) | 5 |
| received | 99 |
| failed (after the model client's own retries), cut-offs included | 1 |
| cut off at the answer length limit (64,000 tokens) | 1 |
"""


class Export(unittest.TestCase):

    def setUp(self):
        tuning, held = ex.read_run_list(LIST)
        self.assertEqual(held, ["h1"])
        loaded = {r["run_id"]: r for r in TUNING}
        self.gs = ex.groups(tuning, HELD, loaded.__getitem__)
        self.out = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.out)

    def test_groups(self):
        self.assertEqual([(g["part"], g["model"], len(g["runs"])) for g in self.gs], [("tuning", "m", 2), ("held-out", "m", 1)])
        self.assertEqual(self.gs[1]["runs"][0]["repeat"], 1)            # found through its 060 run, x1

    def test_a_bad_line(self):
        with self.assertRaises(SystemExit):
            ex.read_run_list("induced\tlowest\tm\t1\te1\n")

    def test_the_files(self):
        written = ex.export(self.gs, self.out, {"a": "Title A"}, lambda run_id: REPORT)
        self.assertEqual(set(written), {"metrics_pooled.csv", "metrics_per_run.csv", "runs.csv", "per_record.csv",
                                        "by_drafting_model.csv", "notable_records.csv"})
        pooled = read_csv(self.out / "metrics_pooled.csv")
        self.assertEqual(list(pooled[0]), ex.POOLED_COLUMNS)
        f1 = next(r for r in pooled if r["part"] == "tuning" and r["metric"] == "partial: f1")
        # Σ 2 × pairs = 2 × (3 + 2 + 1 + 2) = 16; Σ (occurrences + ground truth) = 9 + 4 + 7 + 5 = 25
        self.assertEqual(f1["value"], f"{16 / 25:.4f}")
        self.assertEqual((f1["runs"], f1["records_pooled"]), ("2", "2"))
        self.assertTrue(f1["low_95"] and f1["bootstrap_low_95"])
        held = next(r for r in pooled if r["part"] == "held-out" and r["metric"] == "partial: f1")
        self.assertEqual(held["value"], "1.0000")
        per_run = read_csv(self.out / "metrics_per_run.csv")
        f1 = next(r for r in per_run if r["part"] == "tuning" and r["metric"] == "partial: f1")
        self.assertEqual((f1["value_1"], f1["value_2"]), (f"{10 / 13:.4f}", f"{6 / 12:.4f}"))
        self.assertEqual(f1["width"], f"{10 / 13 - 0.5:.4f}")
        per_record = read_csv(self.out / "per_record.csv")
        self.assertEqual(list(per_record[0]), ex.PER_RECORD_COLUMNS)
        self.assertEqual([(r["record_id"], r["title"], r["partial_f1"]) for r in per_record[:2]],
                         [("a", "Title A", f"{6 / 9:.4f}"), ("b", "", "1.0000")])
        runs = read_csv(self.out / "runs.csv")
        self.assertEqual(len(runs), 2)
        self.assertEqual((runs[0]["run_070_held_out"], runs[1]["run_070_held_out"]), ("h1", ""))
        self.assertEqual((runs[0]["removed_component_class_not_in_schema_and_source_text"], runs[0]["removed_duplicate"],
                          runs[0]["removed_describes_triple"]), ("3", "0", "0"))
        self.assertEqual(read_csv(self.out / "by_drafting_model.csv")[0]["drafted_by"], "model-a")
        notable = read_csv(self.out / "notable_records.csv")
        self.assertEqual(list(notable[0]), ex.NOTABLE_COLUMNS)

    def test_the_report(self):
        got = ex.parse_060_report(REPORT)
        self.assertEqual((got["classed_triples_in_answer_max"], got["classed_triples_in_answer_total"],
                          got["extracted_triples_mean"]), (1203, 1204, 600.5))
        self.assertEqual(got["removed_total"], 1003)
        self.assertEqual(got["reasons"], {"component_class_not_in_schema": 1000,
                                          "component_class_not_in_schema source_text": 3})
        with self.assertRaises(ValueError):                               # a reason no column holds
            ex.parse_060_report(REPORT.replace("source_text 3", "new_reason 3"))
        self.assertEqual((got["model_calls_failed"], got["model_calls_cut_off"], got["answer_limit_tokens"]), (1, 1, 64000))
        tokens = ex.parse_tokens(REPORT)
        self.assertEqual((tokens["sent_not_from_cache"], tokens["sent_read_from_cache"], tokens["received"],
                          tokens["received_as_thinking"]), (1234, 5, 99, ""))
        with self.assertRaises(ValueError):
            ex.parse_060_report("nothing here")

    def test_compared_triples(self):
        compared = [
            {"record_id": "a", "part": "tuning", "status": "exact pair", "entity_classes_right": "yes",
             "within_reach": "yes", "extracted_subject": "Aqua", "extracted_subject_class": "Platform",
             "translated_subject_class": "Platform", "extracted_predicate": "HAS", "translated_predicate": "HAS_PART",
             "origin": "x1/extracted_triples.csv#1; annotations/ground_truth/batch_001.csv#4"},
            {"record_id": "a", "part": "tuning", "status": "ground truth only", "within_reach": "no",
             "origin": "annotations/ground_truth/batch_001.csv#5"},
            {"record_id": "a", "part": "tuning", "status": "extracted only",
             "origin": "x1/extracted_triples.csv#2"},
            {"record_id": "c", "part": "held-out", "status": "extracted only", "origin": "x#0"}]
        extracted = [{"source_text": "(record structure)"}, {"source_text": "Aqua has it", "flags": "f"},
                     {"source_text": "other"}]
        occ, outcomes = ex.compared_rows({"model": "m"}, "tuning", compared, extracted)
        self.assertEqual([(r["extracted_ref"], r["status"], r["source_text"], r["ground_truth_ref"]) for r in occ],
                         [("extracted_triples.csv#1", "exact pair", "Aqua has it", "annotations/ground_truth/batch_001.csv#4"),
                          ("extracted_triples.csv#2", "extracted only", "other", "")])
        self.assertEqual((occ[0]["translated_subject_class"], occ[0]["translated_predicate"]), ("", "HAS_PART"))
        self.assertEqual([(r["ground_truth_ref"], r["outcome"], r["within_reach"]) for r in outcomes],
                         [("annotations/ground_truth/batch_001.csv#4", "exact pair", "yes"),
                          ("annotations/ground_truth/batch_001.csv#5", "missed", "no")])
        self.assertTrue(set(occ[0]) <= set(ex.EXTRACTED_COLUMNS) and set(outcomes[0]) <= set(ex.OUTCOME_COLUMNS))

    def test_records(self):
        evidence = {"texts": [{"id": "t", "title": "T", "maintainer": "M", "stratum": "M",
                               "triple_instances": [{"subject": "s", "predicate": "p", "object": "o"}]}]}
        columns, rows = ex.record_rows(self.gs, {"a": {"title": "Title A", "maintainer": "N"}}, evidence, {"a": "notes only"})
        self.assertEqual([(r["record_id"], r["role"]) for r in rows], [("t", "induction text"), ("a", "tuning"),
                                                                      ("b", "tuning"), ("c", "held-out")])
        a = rows[1]
        self.assertEqual((a["induction_duplicate_kind"], a["ground_truth_triples_by_drafting_model"]), ("notes only", "model-a: 5"))
        self.assertEqual(a["partial_f1_induced_lowest_m"], f"{8 / 16:.4f}")      # 2 × (3 + 1) ÷ ((4 + 5) + (2 + 5))
        self.assertEqual(a["partial_pairs_induced_lowest_m"], "2.00")
        self.assertTrue(set(a) <= set(columns))
        self.assertEqual(ex.instance_rows(evidence)[0]["text_id"], "t")


if __name__ == "__main__":
    unittest.main()
