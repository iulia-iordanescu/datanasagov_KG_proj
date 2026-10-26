"""common/common_helpers/status.py: where the project stands, and what to do next. Each test builds a temporary
copy of the code (support.temp_repo) with only the files its situation needs (made-up manifests, a ground truth
file, a translation table, ...) and reads the status there, in its own process, so the real repository is never
read or touched."""
import csv
import hashlib
import json
import shutil
import subprocess
import sys
import unittest

from support import temp_repo

READ = ("import json, sys; sys.path.insert(0, '.'); from common.status import project_status; "
        "print(json.dumps(project_status()))")
GT_COLUMNS = ["id", "subject", "subject_class", "predicate", "object", "object_class", "source_text",
              "all_facts_extracted"]


class Status(unittest.TestCase):

    def setUp(self):
        self.tmp = temp_repo()
        self.results = self.tmp / "outputs" / "intermediate_results"

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def status(self) -> dict:
        r = subprocess.run([sys.executable, "-c", READ], cwd=self.tmp, capture_output=True, text=True,
                           timeout=120, encoding="utf-8", env={"PYTHONIOENCODING": "utf-8", "SYSTEMROOT": "C:\\Windows",
                                                  "PATH": ""})
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)

    def texts(self, st: dict, area: str) -> list:
        return [i["text"] for i in st["items"] if i["area"] == area]

    # ---- made-up files
    def manifest(self, step: str, inputs=()):
        folder = self.results / step
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "_manifest.json").write_text(json.dumps({
            "run_id": f"{step}_2026-10-14_1200", "step": step, "finished": "2026-10-14T12:00:00-04:00",
            "inputs": [{"name": n, "path": p, "sha256": h} for n, p, h in inputs]}), encoding="utf-8")

    def output(self, step: str, name: str, text: str) -> str:
        """Write an output file; its sha256, as a manifest records it."""
        path = self.results / step / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def splits(self, ids_parts):
        self.output("030_split", "splits.json", json.dumps({"ground_truth_candidates": {"records": [
            {"id": i, "position": k, "part": part} for k, (i, part) in enumerate(ids_parts)]}}))

    def ground_truth(self, n: int, rows):
        with open(self.tmp / "annotations" / "ground_truth" / f"batch_{n:03d}.csv", "w", encoding="utf-8",
                  newline="") as fh:
            w = csv.writer(fh)
            w.writerow(GT_COLUMNS)
            w.writerows(rows)

    # ---- the steps
    def test_nothing_run_yet(self):
        st = self.status()
        self.assertEqual([s["state"] for s in st["steps"]], ["no run recorded"] * 7)
        steps = self.texts(st, "Steps")
        self.assertEqual(len(steps), 1)                                   # only the first step not run: the rest wait
        self.assertIn("Step 010_harvest hasn't run on this computer yet", steps[0])
        self.assertTrue(all(i["doc"].startswith("docs/upkeep.md#") for i in st["items"]))

    def test_out_of_date_only_when_an_input_that_counts_changed(self):
        h = self.output("010_harvest", "batch_00000.json", "[]")
        self.manifest("010_harvest")
        self.manifest("020_clean", [("batches", "outputs/intermediate_results/010_harvest/batch_*.json", h)])
        self.manifest("030_split", [("candidates", "annotations/ground_truth_candidates.csv", "an old hash")])
        st = self.status()
        states = {s["step"]: s["state"] for s in st["steps"]}
        self.assertEqual(states["020_clean"], "ran")                      # its input is as it was
        self.assertEqual(states["030_split"], "ran")                      # a person's file 030 doesn't count
        self.output("010_harvest", "batch_00000.json", "[{}]")            # the harvest changed since 020 ran
        st = self.status()
        self.assertEqual({s["step"]: s["state"] for s in st["steps"]}["020_clean"], "out of date")
        self.assertTrue(any("Step 020_clean is out of date" in t and "`batches`" in t and "--from 020" in t
                            for t in self.texts(st, "Steps")), self.texts(st, "Steps"))

    def test_070_out_of_date_when_a_person_changed_what_it_read(self):
        mapping = self.tmp / "annotations" / "component_class_mapping.csv"
        self.manifest("070_evaluate", [("component_class_mapping", "annotations/component_class_mapping.csv",
                                        hashlib.sha256(mapping.read_bytes()).hexdigest())])
        self.assertEqual(self.status()["steps"][6]["state"], "ran")
        mapping.write_text(mapping.read_text(encoding="utf-8") + "entity class,Gadget,Device,,yes,,\n", encoding="utf-8")
        st = self.status()
        self.assertEqual(st["steps"][6]["state"], "out of date")
        self.assertTrue(any("to see the numbers with those changes" in t for t in self.texts(st, "Steps")))

    # ---- the ground truth
    def test_draft_waiting_and_records_not_finished(self):
        self.splits([("r0", "tuning"), ("r1", "tuning"), ("r2", "held-out")])
        self.output("050_annotate", "drafted_triples_batch1.csv", "id\n")
        self.ground_truth(0, [["r1", "MODIS", "Instrument", "ABOARD", "Aqua", "Spacecraft", "MODIS aboard Aqua", "0"],
                              ["r2", "", "", "", "", "", "", "0"]])
        gt = self.texts(self.status(), "Ground truth")
        self.assertTrue(any("Drafted batch 1 from step 050 isn't opened yet" in t for t in gt), gt)
        self.assertTrue(any("batch_000.csv has 2 record(s) not finished (pool position): #1 and #2" in t
                            or "batch_000.csv has 2 record(s) not finished (pool position): #1, #2" in t for t in gt), gt)

    def test_coined_component_class_and_070s_stop(self):
        self.ground_truth(0, [["r1", "MODIS", "Gizmo", "ABOARD", "Aqua", "Spacecraft", "MODIS aboard Aqua", "1"]])
        gt = self.texts(self.status(), "Ground truth")
        coined = [t for t in gt if "aren't in the ground truth schema" in t]
        self.assertEqual(len(coined), 1, gt)
        self.assertIn("Gizmo (entity class, coined in the ground truth)", coined[0])
        self.assertIn("Step 070 stops while a finished record uses one (1 do)", coined[0])
        # a describes triple's entity class counts too, as step 070 checks it
        self.ground_truth(0, [["r1", "r1", "CatalogEntry", "DESCRIBES", "A title", "Gadgetry", "(record structure)", "1"]])
        coined = [t for t in self.texts(self.status(), "Ground truth") if "aren't in the ground truth schema" in t]
        self.assertIn("Gadgetry (entity class, coined in the ground truth)", coined[0])
        self.assertIn("(1 do)", coined[0])

    def test_rows_with_an_error_point_to_the_checks(self):
        self.output("020_clean", "records.jsonl", json.dumps({"id": "r1", "title": "MODIS", "notes": "MODIS aboard Aqua"}))
        self.ground_truth(0, [["r1", "MODIS", "Instrument", "ABOARD", "Aqua", "Spacecraft", "MODIS aboard Aqua", "0"],
                              ["zz", "MODIS", "Instrument", "ABOARD", "Aqua", "Spacecraft", "MODIS aboard Aqua", "0"]])
        errors = [t for t in self.texts(self.status(), "Ground truth") if "have an error to fix" in t]
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("1 ground truth triple(s) or describes triple(s) have an error to fix (each kind: "
                      "050_annotate/050_annotate.md, Checks on each row): batch_000.csv line 3", errors[0])

    # ---- the schema additions, the translation table, the partial pairs
    def test_addition_without_a_source(self):
        additions = self.tmp / "annotations" / "schema_additions.txt"
        additions.write_text(additions.read_text(encoding="utf-8") + "\nENTITY CLASSES\nGadget  a small device\n",
                             encoding="utf-8")
        texts = self.texts(self.status(), "Schema additions")
        self.assertTrue(any("Gadget (additions file) needs a source" in t for t in texts), texts)

    def test_translation_rows_to_check_and_classes_without_a_row(self):
        self.output("060_extract", "schema_used.json", json.dumps({
            "entity_classes": [{"component_class": "Gadget", "definition": "a small device"},
                               {"component_class": "Probe", "definition": "a craft sent to explore"}],
            "predicates": []}))
        mapping = self.tmp / "annotations" / "component_class_mapping.csv"
        mapping.write_text(mapping.read_text(encoding="utf-8") + "entity class,Gadget,Device,,no,a small device,\n",
                           encoding="utf-8")
        texts = self.texts(self.status(), "Translation table")
        self.assertTrue(any("1 row(s) of the translation table still to check: Gadget (current schema)" in t
                            for t in texts), texts)
        self.assertTrue(any("1 component class(es) of the current schema have no row" in t for t in texts), texts)
        mapping.write_text(mapping.read_text(encoding="utf-8") + "entity class,Probe,Gizmoid,,yes,a craft sent to explore,\n",
                           encoding="utf-8")                              # checked, but Gizmoid was never in it
        texts = self.texts(self.status(), "Translation table")
        self.assertTrue(any("with a missing target (translating to an entity class or predicate the ground truth schema "
                            "doesn't have): choose the right one, or add it to the ground truth schema: Probe (current schema)"
                            in t for t in texts), texts)

    def test_partial_pairs_waiting_tuning_only(self):
        self.splits([("r0", "tuning"), ("r1", "held-out")])
        self.manifest("070_evaluate")
        header = ["record_id", "status"] + [f"ground_truth_{s}" for s in ("subject", "predicate", "object")] \
            + [f"translated_{s}" for s in ("subject", "predicate", "object")]
        rows = [["r0", "partial pair", "MODIS", "ABOARD", "Aqua", "MODIS Terra", "ABOARD", "Aqua"],
                ["r1", "partial pair", "AIRS", "ABOARD", "Aqua", "AIRS sounder", "ABOARD", "Aqua"]]
        path = self.results / "070_evaluate" / "compared_triples.csv"
        with open(path, "w", encoding="utf-8", newline="") as fh:
            csv.writer(fh).writerows([header] + rows)
        texts = self.texts(self.status(), "Partial pairs")
        self.assertEqual(len(texts), 1, texts)
        self.assertIn("1 partial pair(s) of tuning records", texts[0])     # the held-out one is never shown

    def test_no_git_item_outside_a_repository(self):
        self.assertEqual(self.texts(self.status(), "Git"), [])


if __name__ == "__main__":
    unittest.main()
