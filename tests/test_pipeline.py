"""The whole pipeline, end to end, in a temporary copy of the repository:
harvest from a stand-in catalog, clean, split, induce a schema, draft
ground truth, correct it as a person would, extract, and evaluate, with the
stand-in model (tests/stand_ins.py). Each step runs as it does for a
person (its run.py, through run_step), in its own process.

Checked: every step finishes (or stops when it should), its outputs hold
what it says, the model's deliberate faults are caught, a rerun pays
nothing twice, and evaluation's numbers are right on a case worked out by
hand: 8 tuning records, each with one fact extraction finds, plus one fact
only the ground truth has."""
import csv
import json
import os
import re
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

from stand_ins import StandInCatalog
from support import temp_repo

HERE = Path(__file__).resolve().parent
COLUMNS = ["id", "subject", "subject_class", "predicate", "object", "object_class", "source_text", "all_facts_extracted"]
NO_CONFIRM = ["--confirm_paid_calls", "false"]


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(path, rows, columns):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, columns)
        w.writeheader()
        w.writerows(rows)


class Pipeline(unittest.TestCase):
    """The tests run in name order (t01, t02, ...): each step uses the one before."""

    @classmethod
    def setUpClass(cls):
        cls.repo = temp_repo()
        cls.results = cls.repo / "outputs" / "intermediate_results"
        cls.annotations = cls.repo / "annotations"
        cls.catalog = StandInCatalog(count=40).__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.catalog.__exit__()
        shutil.rmtree(cls.repo)

    def run_step(self, step, *args, expect=0):
        """Run one step; return (output, prompts the stand-in model answered)."""
        r = subprocess.run([sys.executable, str(HERE / "stand_in_run.py"), str(self.repo), step, *args],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL,
                           env={**os.environ, "KG_TEST_CATALOG": self.catalog.url})
        out = r.stdout + r.stderr
        self.assertEqual(r.returncode, expect, f"{step} {args}:\n{out[-3000:]}")
        self.assertNotIn("Traceback", out, out[-3000:])
        prompts = int(re.search(r"stand-in model answered (\d+) prompt", out).group(1))
        return out, prompts

    def output(self, step, name):
        return self.results / step / name

    def manifest(self, step):
        return json.loads(self.output(step, "_manifest.json").read_text(encoding="utf-8"))

    # ------------------------------------------------------------- 010 to 030

    def test_t01_harvest(self):
        self.run_step("010_harvest", "--page_size", "10", "--pause_seconds", "0")
        files = sorted(p.name for p in (self.results / "010_harvest").glob("batch_*.json"))
        self.assertEqual(files, ["batch_00000.json", "batch_00010.json", "batch_00020.json", "batch_00030.json"])
        m = self.manifest("010_harvest")
        self.assertEqual(m["headline"], {"records harvested": 40})
        self.assertEqual(m["warnings"], 2)                                      # a repeated id, a record with no id
        self.assertEqual(len(m["outputs"]), 4)

    def test_t02_clean(self):
        self.run_step("020_clean")
        records = [json.loads(x) for x in self.output("020_clean", "records.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual(len(records), 38)                                      # no id, repeat: dropped
        self.assertEqual(len({r["id"] for r in records}), 38)
        for r in records:
            self.assertNotRegex(r["notes"] + r["title"], r"&lt;|&amp;|<b>|<p>")
        r0 = next(r for r in records if r["id"] == "rec-0000")
        self.assertEqual(r0["title"], "MODIS Aqua Dataset 0 & more")
        self.assertTrue(r0["notes"].startswith("MODIS aboard Aqua measured record 0."))
        self.assertIn("https://example.org/0", r0["notes"])
        self.assertEqual({r["maintainer"] for r in records},
                         {"Kristan Morgan", "Jane Roe", "Earthdata Forum", "Ames Team", "undefined"})
        self.assertEqual(self.manifest("020_clean")["inputs"][0]["run_id"], self.manifest("010_harvest")["run_id"])

    def test_t03_split(self):
        records = [json.loads(x) for x in self.output("020_clean", "records.jsonl").read_text(encoding="utf-8").splitlines()]
        pool = sorted(records, key=lambda r: r["id"][::-1])[:12]                # a fixed "random" order
        write_csv(self.annotations / "ground_truth_candidates.csv",
                  [{"id": r["id"], "maintainer": r["maintainer"], "stratum": r["maintainer"], "stratum_size": 1,
                    "drawn_from_stratum": 1} for r in pool],
                  ["id", "maintainer", "stratum", "stratum_size", "drawn_from_stratum"])
        self.run_step("030_split")
        splits = json.loads(self.output("030_split", "splits.json").read_text(encoding="utf-8"))
        candidates = splits["ground_truth_candidates"]["records"]
        self.assertEqual([r["id"] for r in candidates], [r["id"] for r in pool])
        self.assertEqual([r["position"] for r in candidates if r["part"] == "held-out"], [8, 11])
        induction = {r["id"] for r in splits["induction_candidates"]["records"]}
        self.assertFalse(induction & {r["id"] for r in pool})
        self.assertEqual(len(induction), 38 - 12)
        before = self.output("030_split", "splits.json").read_bytes()
        self.run_step("030_split", "--induction_seed", "8")                     # written once: kept
        self.assertEqual(self.output("030_split", "splits.json").read_bytes(), before)

    # ------------------------------------------------------------------- 040

    def test_t04_induce_schema(self):
        _, prompts = self.run_step("040_induce_schema", *NO_CONFIRM, "--induction_maintainers", "3",
                                   "--texts_per_maintainer", "4")
        schema = json.loads(self.output("040_induce_schema", "the_schema.json").read_text(encoding="utf-8"))
        found = {e["component_class"] for e in schema["entity_classes"]}
        predicates = {e["component_class"] for e in schema["predicates"]}
        self.assertTrue(found and predicates)
        for e in schema["entity_classes"] + schema["predicates"]:
            self.assertTrue(e["definition"].endswith("(stand-in definition)."), e)
            self.assertGreaterEqual(e["support"], 1)
        for p in schema["patterns"]:
            s, pr, o = p["pattern"]
            self.assertTrue(s in found and o in found and pr in predicates, p)
        self.assertNotIn("Mission", found)                                    # too vague
        self.assertNotIn("Bogus", found | predicates)                         # named but not sent
        self.assertFalse({"Sensor", "Instrument"} <= found or {"Satellite", "Spacecraft"} <= found,
                         "a merge was not applied")
        texts = {t for e in schema["entity_classes"] for t in e["texts"]}
        pool = {r["id"] for r in read_csv(self.annotations / "ground_truth_candidates.csv")}
        self.assertFalse(texts & pool, "the schema was learned from ground truth candidates")
        _, again = self.run_step("040_induce_schema", *NO_CONFIRM, "--induction_maintainers", "3",
                                 "--texts_per_maintainer", "4")
        self.assertEqual(again, 0, "a rerun paid again")
        self.assertGreater(prompts, 0)

    # ---------------------------------------------------------------- 050

    def test_t05_annotate(self):
        self.assertEqual(list((self.annotations / "ground_truth").iterdir()), [])     # a first run: no ground truth yet
        self.run_step("050_annotate", *NO_CONFIRM, "--records_per_batch", "9")
        rows = read_csv(self.output("050_annotate", "drafted_triples_batch1.csv"))
        pool = [r["id"] for r in read_csv(self.annotations / "ground_truth_candidates.csv")]
        ids = list(dict.fromkeys(r["id"] for r in rows))
        self.assertEqual(ids, pool[:9])
        for rid in ids:
            mine = [r for r in rows if r["id"] == rid]
            self.assertEqual((mine[0]["predicate"], mine[0]["subject"]), ("DESCRIBES", rid))
            facts = [(r["subject"], r["predicate"], r["object"], r["object_class"]) for r in mine[1:]]
            self.assertEqual(len(facts), len(set(facts)), "a repeat was kept")
        flags = {(r["object"], r["object_class"]): r["flags"].split() for r in rows}
        moon = [f for (o, _), f in flags.items() if o == "Moon"]
        self.assertTrue(moon and all("source_not_in_text" in f for f in moon))
        satellite = [f for (_, c), f in flags.items() if c == "Satellite"]
        self.assertTrue(satellite and all("object_class_not_in_schema" in f for f in satellite))
        self.assertTrue(any(r["object_class"] == "X" and "describes_undecided" in r["flags"] for r in rows))

    def test_t06_person_corrects(self):
        """What a person does with the annotation tool, written directly."""
        keep = []
        for r in read_csv(self.output("050_annotate", "drafted_triples_batch1.csv")):
            flags = r["flags"].split()
            if "source_not_in_text" in flags or any(f.endswith("_class_not_in_schema") for f in flags):
                continue
            keep.append({**{c: r[c] for c in COLUMNS}, "all_facts_extracted": "1",
                         "object_class": "Dataset" if r["object_class"] == "X" else r["object_class"]})
        title = keep[0]["object"]                                               # record 0: a fact only a person saw
        keep.insert(2, {**keep[0], "subject": title, "subject_class": "Dataset", "predicate": "ACQUIRED_BY",
                        "object": "MODIS", "object_class": "Instrument", "source_text": title})
        write_csv(self.annotations / "ground_truth" / "batch_001.csv", keep, COLUMNS)
        type(self).ground_truth = keep

    # ---------------------------------------------------------------- 060

    def test_t07_extract(self):
        _, prompts = self.run_step("060_extract", *NO_CONFIRM)
        self.assertEqual(prompts, 10)                                           # 9 records, 1 test call
        kept = read_csv(self.output("060_extract", "extracted_triples.csv"))
        removed = read_csv(self.output("060_extract", "extracted_triples_removed.csv"))
        self.assertEqual(len({r["id"] for r in kept}), 9)
        self.assertFalse([r for r in kept if r["object"] == "Moon" or r["object_class"] == "Satellite"])
        self.assertEqual(sorted({r["reason"] for r in removed}),
                         ["component_class_not_in_schema", "duplicate", "malformed", "source_text"])
        used = json.loads(self.output("060_extract", "schema_used.json").read_text(encoding="utf-8"))
        schema = json.loads(self.output("040_induce_schema", "the_schema.json").read_text(encoding="utf-8"))
        self.assertEqual({e["component_class"] for e in used["entity_classes"]},
                         {e["component_class"] for e in schema["entity_classes"]})
        _, again = self.run_step("060_extract", *NO_CONFIRM)
        self.assertEqual(again, 0, "a rerun paid again")

    # ---------------------------------------------------------------- 070

    def test_t08_evaluate_waits_for_the_table(self):
        mapping = self.annotations / "component_class_mapping.csv"
        out, _ = self.run_step("070_evaluate", *NO_CONFIRM, expect=2)
        self.assertIn("Check those rows", out)
        rows = read_csv(mapping)
        self.assertTrue(rows)
        self.assertTrue(all(r["checked"] in ("no", "same component class") for r in rows))
        out, _ = self.run_step("070_evaluate", *NO_CONFIRM, expect=2)
        self.assertIn("still need checking", out)
        self.assertEqual(read_csv(mapping), rows)                               # rows are never changed
        for r in rows:
            r["checked"] = "yes" if r["checked"] == "no" else r["checked"]
        write_csv(mapping, rows, list(rows[0]))
        self.run_step("070_evaluate", *NO_CONFIRM)
        metrics = json.loads(self.output("070_evaluate", "metrics.json").read_text(encoding="utf-8"))
        self.assertEqual(sorted(metrics["parts"]), ["tuning"])                  # held-out: kept aside
        self.assertEqual(len(metrics["evaluated"]["held-out"]), 1)
        self.check_counts(metrics)

    def check_counts(self, metrics):
        """metrics.json's counts agree with compared_triples.csv, row by row."""
        compared = [r for r in read_csv(self.output("070_evaluate", "compared_triples.csv")) if r["part"] == "tuning"]
        n = metrics["parts"]["tuning"]["numbers"]
        status = [r["status"] for r in compared]
        self.assertEqual(n["records"], len({r["record_id"] for r in compared}))
        self.assertEqual(n["exact"]["pairs"], status.count("exact pair"))
        self.assertEqual(n["partial"]["pairs"], status.count("exact pair") + status.count("partial pair"))
        self.assertEqual(n["extracted"], n["partial"]["pairs"] + status.count("extracted only"))
        self.assertEqual(n["gt_triples"], n["partial"]["pairs"] + status.count("ground truth only"))
        return n

    def test_t09_known_numbers(self):
        """Extraction with the hand-built schema, evaluated with a table of
        its own: worked out by hand, 8 tuning records with one fact each,
        all found; record 0 has a second fact extraction can't find."""
        self.run_step("060_extract", *NO_CONFIRM, "--schema", str(self.annotations / "schema_derived_from_manual_annotation.txt"))
        table = self.repo / "own_table.csv"
        table.write_text((self.annotations / "component_class_mapping.csv").read_text(encoding="utf-8").splitlines()[0] + "\n",
                           encoding="utf-8")
        args = [*NO_CONFIRM, "--component_class_mapping", str(table)]
        _, prompts = self.run_step("070_evaluate", *args, expect=2)             # every row: the same component class
        self.assertEqual(prompts, 0)                                            # nothing to ask the model
        self.assertTrue(all(r["checked"] == "same component class" for r in read_csv(table)))
        self.run_step("070_evaluate", *args)
        metrics = json.loads(self.output("070_evaluate", "metrics.json").read_text(encoding="utf-8"))
        n = self.check_counts(metrics)
        self.assertEqual((n["records"], n["extracted"], n["gt_triples"]), (8, 8, 9))
        for level in ("exact", "partial"):
            m = n[level]
            self.assertEqual(m["precision"]["value"], 1.0)
            self.assertAlmostEqual(m["recall"]["value"], 8 / 9)
            self.assertAlmostEqual(m["f1"]["value"], 16 / 17)
            self.assertEqual(m["strict_precision"]["value"], 1.0)
            self.assertEqual(m["entity_class_accuracy"]["value"], 1.0)
            self.assertIsNone(m["precision"]["low"])                            # fewer than 20 records: no margin
        self.assertEqual(n["recall_upper_bound"]["value"], 1.0)
        extracted = read_csv(self.output("060_extract", "extracted_triples.csv"))
        tuning = {r["record_id"] for r in read_csv(self.output("070_evaluate", "compared_triples.csv")) if r["part"] == "tuning"}
        named = [r for r in extracted if r["predicate"] == "DESCRIBES" and r["id"] in tuning]
        self.assertAlmostEqual(n["describes"]["accuracy"]["value"], sum(r["object_class"] == "Dataset" for r in named) / 8)
        self.assertEqual(read_csv(self.annotations / "held_out_looks.csv"), [])

    def test_t10_held_out_look_logged(self):
        args = [*NO_CONFIRM, "--component_class_mapping", str(self.repo / "own_table.csv"), "--evaluate_held_out", "true"]
        self.run_step("070_evaluate", *args)
        metrics = json.loads(self.output("070_evaluate", "metrics.json").read_text(encoding="utf-8"))
        self.assertEqual(metrics["parts"]["held-out"]["numbers"]["records"], 1)
        looks = read_csv(self.annotations / "held_out_looks.csv")
        self.assertEqual([int(x["held_out_records"]) for x in looks], [1])

    def test_t10b_evaluate_refuses_a_repeat(self):
        """A classed triple twice in a record stops evaluation; the same subject
        instance, predicate, and object instance with different entity classes
        only warns, before anything is evaluated."""
        path = self.annotations / "ground_truth" / "batch_001.csv"
        before = path.read_bytes()
        fact = next(r for r in self.ground_truth if r["predicate"] != "DESCRIBES")
        args = [*NO_CONFIRM, "--component_class_mapping", str(self.repo / "own_table.csv")]
        try:
            # entity classes differing only in case: the same classed triple
            write_csv(path, self.ground_truth + [{**fact, "subject": "the " + fact["subject"],
                                                  "subject_class": fact["subject_class"].lower()}], COLUMNS)
            out, _ = self.run_step("070_evaluate", *args, expect=2)
            self.assertIn("Step 070 can't evaluate: 1 classed triple appears twice in a record of the ground truth, "
                          "and only one copy could be paired.", out)
            self.assertIn(f"1. Record {fact['id']} (batch_001.csv): lines", out)
            write_csv(path, self.ground_truth + [{**fact, "object_class": "Other"}], COLUMNS)
            out, _ = self.run_step("070_evaluate", *args)
            self.assertIn("Step 070 found 1 warning:\n1. Ground truth, record", out)
            warning = out.index("with different entity classes")
            self.assertLess(warning, out.index("compared "), "warned only after comparing")
            # with someone to ask: the run stops at the question (no keyboard here: cancelled), before comparing
            out, _ = self.run_step("070_evaluate", "--component_class_mapping", str(self.repo / "own_table.csv"), expect=2)
            self.assertIn("Press Enter to evaluate anyway", out)
            self.assertIn("with different entity classes", out)
            self.assertNotIn("compared ", out)
        finally:
            path.write_bytes(before)

    def test_t11_every_run_reported(self):
        reports = sorted((self.repo / "outputs" / "reports").glob("*.md"))
        logs = sorted((self.repo / "outputs" / "logs").glob("*.log"))
        self.assertEqual(len(reports), len(logs))
        self.assertGreaterEqual(len(reports), 15)
        for r in reports:
            text = r.read_text(encoding="utf-8")
            self.assertNotIn("Traceback", text, r.name)
        written = sorted(p.relative_to(self.annotations).as_posix() for p in self.annotations.rglob("*") if p.is_file())
        self.assertEqual(written, ["README.md", "component_class_mapping.csv", "ground_truth/batch_001.csv",
                                   "ground_truth_candidates.csv", "held_out_looks.csv", "partial_pair_reviews.csv",
                                   "schema_additions.txt", "schema_derived_from_manual_annotation.txt"])


if __name__ == "__main__":
    unittest.main()
