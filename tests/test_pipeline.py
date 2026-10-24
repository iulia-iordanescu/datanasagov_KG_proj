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
import collections
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
COLUMNS = ["id", "subject", "subject_class", "predicate", "object", "object_class", "source_text", "all_facts_extracted",
           "drafted_by"]                                                       # as the annotation tool writes them
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

    def run_step(self, step, *args, expect=0, env=None):
        """Run one step; return (output, prompts the stand-in model answered). env: more environment variables
        (e.g. the stand-in model's faults, tests/stand_ins.py)."""
        r = subprocess.run([sys.executable, str(HERE / "stand_in_run.py"), str(self.repo), step, *args],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL,
                           env={**os.environ, "KG_TEST_CATALOG": self.catalog.url, **(env or {})})
        out = r.stdout + r.stderr
        self.assertEqual(r.returncode, expect, f"{step} {args}:\n{out[-3000:]}")
        self.assertNotIn("Traceback", out, out[-3000:])
        prompts = int(re.search(r"stand-in model answered (\d+) prompt", out).group(1))
        return out, prompts

    def output(self, step, name):
        return self.results / step / name

    def manifest(self, step):
        return json.loads(self.output(step, "_manifest.json").read_text(encoding="utf-8"))

    def per_text(self, step, counts: dict):
        """The latest report of `step` shows, in its per-text count table (common/common_helpers/report.py), each
        row label's counts as computed here from the step's output files: {row label: [count per text]}."""
        report = max((self.repo / "outputs" / "reports").glob(f"{step}_*.md"),
                     key=lambda p: p.stat().st_mtime).read_text(encoding="utf-8")
        for label, c in counts.items():
            row = re.search(r"^\| " + re.escape(label) + r" \| (.*) \|$", report, re.M)
            self.assertTrue(row, f"{step}: no row {label!r} in its report")
            texts, low, high, _, _, total, none = [x.replace(",", "") for x in row.group(1).split(" | ")]
            self.assertEqual((int(texts), int(low), int(high), int(total), int(none)),
                             (len(c), min(c), max(c), sum(c), c.count(0)), label)

    # ------------------------------------------------------------- 010 to 030

    def test_t01_harvest(self):
        self.run_step("010_harvest", "--page_size", "10", "--pause_seconds", "0")
        files = sorted(p.name for p in (self.results / "010_harvest").glob("batch_*.json"))
        self.assertEqual(files, ["batch_00000.json", "batch_00010.json", "batch_00020.json", "batch_00030.json"])
        m = self.manifest("010_harvest")
        self.assertEqual(m["headline"], {"records harvested": 40})
        self.assertEqual(m["warnings"], 2)                                      # a repeated id, a record with no id
        self.assertEqual(len(m["outputs"]), 4)
        self.assertIs(m["harvest_partial"], False)                              # the whole catalog

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
        self.assertIs(self.manifest("020_clean")["harvest_partial"], False)    # passed on from 010

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

    def test_t03z_a_fixable_problem_stops(self):
        """A setting out of range is something the person can fix: the run is stopped (exit code 2), with the
        message, not failed with a traceback; its report says stopped."""
        out, prompts = self.run_step("040_induce_schema", "--workers", "0", expect=2)
        self.assertIn("workers must be at least 1", out)
        self.assertEqual(prompts, 0)
        report = max(self.repo.glob("outputs/reports/040_induce_schema_*.md"), key=lambda p: p.stat().st_mtime)
        self.assertIn("| Status | stopped |", report.read_text(encoding="utf-8"))

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
        evidence = json.loads(self.output("040_induce_schema", "induction_evidence.json").read_text(encoding="utf-8"))
        sat = evidence["saturation"]["curve"]
        self.assertEqual(sat["texts"][-1], len(evidence["texts"]))              # the curve ends at every text read
        self.assertGreaterEqual(round(sat["entity classes"][-1]), len(found))    # before the too-vague check
        raw = [len(t["triple_instances"]) + len(t["unverified"]) for t in evidence["texts"]]
        verified = [len(t["triple_instances"]) for t in evidence["texts"]]
        self.assertGreater(sum(raw), sum(verified))                            # the stand-in's invented ones
        self.per_text("040_induce_schema", {"raw (everything the model listed: verified + unverified)": raw,
                                            "verified (kept)": verified})
        headline = self.manifest("040_induce_schema")["headline"]
        self.assertEqual((headline["raw triple instances"], headline["verified triple instances"]),
                         (sum(raw), sum(verified)))
        self.assertEqual(headline["verified triple instances, mean per text"], round(sum(verified) / len(verified), 1))
        # helpers/audit.py --induction reads these real files: every triple instance matches ".", and the summary
        # accounts for each one once
        r = subprocess.run([sys.executable, str(self.repo / "helpers" / "audit.py"), "--induction", ".", "--limit",
                            "10000", "--folder", str(self.output("040_induce_schema", ""))], capture_output=True,
                           text=True, encoding="utf-8", errors="replace")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("IN THE SCHEMA", r.stdout)
        summary = r.stdout.split("Summary: matched triple instances per final predicate", 1)[1]
        self.assertEqual(sum(int(n) for n in re.findall(r"^ +(\d+)  ", summary, re.M)), sum(raw), r.stdout[-2000:])
        _, again = self.run_step("040_induce_schema", *NO_CONFIRM, "--induction_maintainers", "3",
                                 "--texts_per_maintainer", "4")
        self.assertEqual(again, 0, "a rerun paid again")
        self.assertGreater(prompts, 0)

    # ---------------------------------------------------------------- 050

    def test_t05_annotate(self):
        self.assertEqual(list((self.annotations / "ground_truth").iterdir()), [])     # a first run: no ground truth yet
        out, _ = self.run_step("050_annotate", *NO_CONFIRM, "--records_per_batch", "9")
        self.assertIn("stand-in model got reasoning_effort: low]", out)        # gemini-2.5-pro: the thinking cap sent
        self.assertIn("test call: ok (answer ", out)
        self.assertIn("model calls: 9 of 9 done, 0 failed, took", out)          # the last progress line
        self.assertNotIn("failed model calls:", out)                           # nothing failed: no failed-call record
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
        drafted = [sum(1 for r in rows if r["id"] == rid and r["predicate"] != "DESCRIBES") for rid in ids]
        self.per_text("050_annotate", {"drafted (everything the model listed)": drafted})
        self.assertEqual(self.manifest("050_annotate")["headline"]["drafted triples"], sum(drafted))

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
        keep.insert(2, {**keep[0], "subject": title, "subject_class": "Dataset", "predicate": "ACQUIRED_BY_INSTRUMENT",
                        "object": "MODIS", "object_class": "Instrument", "source_text": title,
                        "drafted_by": ""})                                      # a row the person wrote
        write_csv(self.annotations / "ground_truth" / "batch_001.csv", keep, COLUMNS)
        type(self).ground_truth = keep

    # ---------------------------------------------------------------- 060

    def test_t06z_extract_stops_early(self):
        """Every call refused: the early stop ends the run after 3, before paying for the rest; the report and the
        run's last lines name the failed-call record, one line per failed or not-made call."""
        out, prompts = self.run_step("060_extract", *NO_CONFIRM, expect=2,
                                     env={"KG_STAND_IN_FAIL": "BEGIN RECORD", "KG_STAND_IN_DELAY": "0.3"})
        self.assertIn("Step 060 stopped early: 3 of the first 3 model calls of this run failed", out)
        self.assertLess(prompts, 10)                                            # not every record was asked (4 at a time)
        record = re.search(r"failed model calls: (outputs/logs/\S+_failed_calls\.jsonl) \((\d+);", out)
        lines = (self.repo / record.group(1)).read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), int(record.group(2)))
        self.assertEqual(len(lines), 9)                                         # 3 failed, 6 not made
        report = sorted((self.repo / "outputs" / "reports").glob("060_extract_*.md"))[-1].read_text(encoding="utf-8")
        self.assertIn("| Failed model calls |", report)

    def test_t07_extract(self):
        out, prompts = self.run_step("060_extract", *NO_CONFIRM)
        self.assertEqual(prompts, 10)                                           # 9 records, 1 test call
        self.assertIn("stand-in model got reasoning_effort: None]", out)       # claude-opus-5.5: nothing sent
        self.assertNotIn("the same model as this run's", out)              # 050 drafts with another maker's model
        self.assertNotIn("a model from the same maker", out)
        kept = read_csv(self.output("060_extract", "extracted_triples.csv"))
        removed = read_csv(self.output("060_extract", "extracted_triples_removed.csv"))
        self.assertEqual(len({r["id"] for r in kept}), 9)
        self.assertFalse([r for r in kept if r["object"] == "Moon" or r["object_class"] == "Satellite"])
        self.assertEqual(sorted({r["reason"] for r in removed}),
                         ["component_class_not_in_schema", "duplicate", "malformed", "source_text"])
        ids = list(dict.fromkeys(r["id"] for r in kept))
        facts = [sum(1 for r in kept if r["id"] == rid and r["predicate"] != "DESCRIBES") for rid in ids]
        checked_out = [sum(1 for r in removed if r["id"] == rid and r["reason"] not in ("malformed", "duplicate"))
                       for rid in ids]
        self.assertTrue(any(checked_out))
        self.per_text("060_extract", {"raw (everything the model listed: kept + removed by a check)":
                                      [a + b for a, b in zip(facts, checked_out)],
                                      "kept (extracted triples)": facts})
        headline = self.manifest("060_extract")["headline"]
        self.assertEqual((headline["raw classed triples"], headline["extracted triples"]),
                         (sum(facts) + sum(checked_out), sum(facts)))
        used = json.loads(self.output("060_extract", "schema_used.json").read_text(encoding="utf-8"))
        schema = json.loads(self.output("040_induce_schema", "the_schema.json").read_text(encoding="utf-8"))
        self.assertEqual({e["component_class"] for e in used["entity_classes"]},
                         {e["component_class"] for e in schema["entity_classes"]})
        evidence = json.loads(self.output("040_induce_schema", "induction_evidence.json").read_text(encoding="utf-8"))
        self.assertTrue(used["learned_from"]["known"])                          # the induced schema: the texts it learned from
        self.assertEqual(set(used["learned_from"]["ids"]), {x["id"] for x in evidence["texts"]})
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

    def test_t09b_redefined_ground_truth_component_class(self):
        """A row checked against one definition in the ground truth schema stops evaluation once that definition changes."""
        self.run_step("060_extract", *NO_CONFIRM, "--schema", str(self.annotations / "ground_truth_schema.txt"))
        table = self.repo / "redefined_table.csv"
        table.write_text((self.annotations / "component_class_mapping.csv").read_text(encoding="utf-8").splitlines()[0] + "\n",
                         encoding="utf-8")
        hand = self.repo / "redefined_ground_truth_schema.txt"
        hand.write_text((self.annotations / "ground_truth_schema.txt").read_text(encoding="utf-8-sig"),
                        encoding="utf-8")
        args = [*NO_CONFIRM, "--component_class_mapping", str(table), "--ground_truth_schema", str(hand)]
        self.run_step("070_evaluate", *args, expect=2)                          # rows added, each with both definitions
        aboard = [r for r in read_csv(table) if r["component_class_in_gtt"] == "ABOARD"]
        self.assertEqual([r["definition_in_gtt"] for r in aboard], ["is carried on"])
        self.run_step("070_evaluate", *args)                                   # evaluates
        hand.write_text(hand.read_text(encoding="utf-8").replace("is carried on", "is anywhere on"), encoding="utf-8")
        out, _ = self.run_step("070_evaluate", *args, expect=2)
        self.assertIn("ground truth schema", out)
        self.assertIn("ABOARD (ground truth schema)", out)

    def test_t09_known_numbers(self):
        """Extraction with the ground truth schema, evaluated with a table of
        its own: worked out by hand, 8 tuning records with one fact each,
        all found; record 0 has a second fact extraction can't find."""
        self.run_step("060_extract", *NO_CONFIRM, "--schema", str(self.annotations / "ground_truth_schema.txt"))
        # t07 extracted with the induced schema, later runs with the ground truth schema: the earlier version of each file a run
        # changed is kept in previous_runs/<that run>/, with its manifest; a file a run left as it was is not kept
        kept = sorted((self.results / "060_extract" / "previous_runs").iterdir())
        self.assertTrue(kept)
        first = json.loads((kept[0] / "schema_used.json").read_text(encoding="utf-8"))
        self.assertEqual(first["made"]["schema"], "040_induce_schema/the_schema.json")
        for folder in kept:
            self.assertTrue((folder / "_manifest.json").is_file())
            later = kept[kept.index(folder) + 1:] or [self.results / "060_extract"]
            for f in (x for x in folder.rglob("*") if x.is_file() and x.name != "_manifest.json"):
                successor = next((d / f.relative_to(folder) for d in later if (d / f.relative_to(folder)).is_file()),
                                 self.results / "060_extract" / f.relative_to(folder))
                self.assertNotEqual(f.read_bytes(), successor.read_bytes(), f)       # kept only when it changed
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
        report = max((self.repo / "outputs" / "reports").glob("070_evaluate_*.md"), key=lambda p: p.stat().st_mtime).read_text(encoding="utf-8")
        self.assertIn("Drafted by a model (step 050) and corrected by a person", report)   # the guide says the report says so
        # per text, worked out by hand: 8 records, one ground truth triple each and two for record 0; one occurrence each
        self.assertRegex(report, r"\| ground truth triples \| 8 \| 1 \| 2 \| 1\.1 \| 1 \| 9 \| 0 \|")
        self.assertRegex(report, r"\| occurrences \(translated extracted triples\) \| 8 \| 1 \| 1 \| 1\.0 \| 1 \| 8 \| 0 \|")
        # per predicate and per entity class, worked out by hand: all 8 occurrences pair exactly, with the right entity
        # classes; record 0's second ground truth triple is the only one left without a partner
        self.assertIn("#### Per predicate and per entity class", report)
        tables = metrics["parts"]["tuning"]["per_component_class"]
        for table in ("predicate", "subject class", "object class"):
            rows = tables[table]
            self.assertEqual([sum(r[k] for r in rows) for k in ("occurrences", "ground_truth_triples", "counted_against")],
                             [8, 9, 1], table)
            self.assertEqual(sum(r["exact"]["pairs"] for r in rows), 8, table)
            self.assertEqual(rows[0]["counted_against"], 1, table)                # the one that costs something first
            self.assertTrue(all(r["exact"]["precision"]["value"] in (1.0, None) for r in rows), table)
        # what 060 removed from the 8 tuning records, per reason: the same as counted in 060's file of removed items
        removed = collections.Counter(r["reason"] for r in read_csv(self.output("060_extract", "extracted_triples_removed.csv"))
                                      if r["id"] in set(metrics["evaluated"]["tuning"]))
        self.assertEqual({x["reason"]: x["removed"] for x in metrics["parts"]["tuning"]["removed_by_060"]}, dict(removed))
        self.assertIn("#### Removed by 060", report)
        self.assertEqual(set(removed), {"source_text", "component_class_not_in_schema", "duplicate", "malformed"})  # the stand-in's mistakes
        # the ground truth schema was learned from pool positions 0-5: those evaluated are twins (of themselves)
        compared = read_csv(self.output("070_evaluate", "compared_triples.csv"))
        first = {r["record_id"] for r in compared if int(r["position"]) < 6 and r["part"] == "tuning"}
        twins = metrics["parts"]["tuning"]["twins"]
        self.assertTrue(first and first <= {x["id"] for x in twins["records"] if x["kind"] == "whole text"})
        self.assertEqual(twins["without"]["records"], 8 - len(twins["records"]))
        self.assertIn("#### Twins", report)

    def test_t10_held_out_look_logged(self):
        args = [*NO_CONFIRM, "--component_class_mapping", str(self.repo / "own_table.csv"), "--evaluate_held_out", "true"]
        self.run_step("070_evaluate", *args)
        metrics = json.loads(self.output("070_evaluate", "metrics.json").read_text(encoding="utf-8"))
        self.assertEqual(metrics["parts"]["held-out"]["numbers"]["records"], 1)
        looks = read_csv(self.annotations / "held_out_looks.csv")
        self.assertEqual([int(x["held_out_records"]) for x in looks], [1])
        self.assertTrue(all(looks[0][k] for k in ("extraction_run_id", "translation_sha256", "held_out_ground_truth_sha256")))
        self.assertEqual(metrics["held_out_looks"], {"count": 1, "changed_since_previous": None})
        # a second look with nothing changed: the same fingerprints, and the report says so
        out, _ = self.run_step("070_evaluate", *args)
        looks = read_csv(self.annotations / "held_out_looks.csv")
        self.assertEqual(len(looks), 2)
        for k in ("schema", "extraction_run_id", "translation_sha256", "held_out_ground_truth_sha256"):
            self.assertEqual(looks[0][k], looks[1][k], k)
        self.assertIn("nothing that sets the held-out numbers changed", out)
        # every run keeps its tuning records' counts; two runs of the same version compare as the same
        # in the order the runs started (common.audit.run_order: names alone sort "…_1641-6" before "…_1641")
        from common.audit import run_order
        kept = sorted((self.results / "070_evaluate" / "evaluations").glob("*.json"), key=lambda f: run_order(f.stem))
        self.assertGreaterEqual(len(kept), 2)
        last = json.loads(kept[-1].read_text(encoding="utf-8"))
        self.assertEqual({r["id"] for r in last["records"]}, set(metrics["evaluated"]["tuning"]))   # never held-out ones
        r = subprocess.run([sys.executable, str(self.repo / "helpers" / "compare_runs.py"), kept[-2].stem, kept[-1].stem],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=self.repo)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("Compared 2 runs on 8 tuning records", r.stdout)
        report = (self.repo / r.stdout.strip().rsplit(": ", 1)[1]).read_text(encoding="utf-8")
        self.assertIn("Nothing recorded differs.", report)
        self.assertIn("| exact: precision | 100.0% | 100.0% | +0.0 points | – | the same |", report)

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
            # an entity class the ground truth schema doesn't have, in a finished record: stops, saying where
            write_csv(path, self.ground_truth + [{**fact, "object_class": "Gizmo"}], COLUMNS)
            out, _ = self.run_step("070_evaluate", *args, expect=2)
            self.assertIn("use 1 entity class(es) or predicate(s) that aren't in the ground truth schema", out)
            self.assertIn("Gizmo (entity class): batch_001.csv line ", out)
            # with someone to ask: the same stop comes first (stage 1), before the warnings are shown and asked about
            out, _ = self.run_step("070_evaluate", "--component_class_mapping", str(self.repo / "own_table.csv"), expect=2)
            self.assertIn("use 1 entity class(es) or predicate(s) that aren't in the ground truth schema", out)
            self.assertNotIn("Press Enter to evaluate anyway", out)
            # another entity class of the ground truth schema: only warns
            write_csv(path, self.ground_truth + [{**fact, "object_class": "Mission"}], COLUMNS)
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
        reports = sorted(p for p in (self.repo / "outputs" / "reports").glob("*.md")
                         if not p.name.startswith("compare_runs_"))     # a comparison isn't a run: no log
        logs = sorted((self.repo / "outputs" / "logs").glob("*.log"))
        self.assertEqual(len(reports), len(logs))
        self.assertGreaterEqual(len(reports), 15)
        for r in reports:
            text = r.read_text(encoding="utf-8")
            self.assertNotIn("Traceback", text, r.name)
        written = sorted(p.relative_to(self.annotations).as_posix() for p in self.annotations.rglob("*") if p.is_file())
        self.assertEqual(written, ["README.md", "component_class_mapping.csv", "ground_truth/batch_001.csv",
                                   "ground_truth_candidates.csv", "ground_truth_schema.txt", "guidelines.md", "held_out_looks.csv",
                                   "partial_pair_reviews.csv", "schema_additions.txt"])


if __name__ == "__main__":
    unittest.main()
