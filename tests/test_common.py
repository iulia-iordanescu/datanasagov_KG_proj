"""Shared code (common/common_helpers/): reading the ground truth, the
ground truth schema, the fair sample, the checks of each triple
instance, building rows from the model's replies, text pieces, the
translation table, and the partial pair reviews."""
import csv
import json
import shutil
import tempfile
import unittest
from pathlib import Path

import sys

import support                                    # noqa: F401  (the repository on the import path)
from support import ROOT
from common import chunking, component_class_mapping, extraction, ground_truth, partial_reviews, text_match, \
    triples_io, validate
from common.files import read_csv, write_csv

COLUMNS = ground_truth.COLUMNS


def gt_file(folder, name, rows, columns=COLUMNS):
    with open(folder / name, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(columns)
        w.writerows(rows)


def row(rid, s="", sc="", p="", o="", oc="", src="", done="1"):
    return [rid, s, sc, p, o, oc, src, done]


class GroundTruthFiles(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_read(self):
        gt_file(self.tmp, "batch_000.csv", [
            row("a", "a", "CatalogEntry", "DESCRIBES", "Title A", "Dataset", "(record structure)"),
            row("a", "MODIS", "Instrument", "ABOARD", "Aqua", "Spacecraft", "MODIS aboard Aqua"),
            ["", "", "", "", "", "", "", ""],                                     # a blank line
            row("b", done="0"),
            row("c", "X", "Y", "Z", "W", "V", "multi\nline source"),
            row("c", "X2", "Y", "Z", "W", "V", "s")])
        gt = ground_truth.read_ground_truth(self.tmp)
        rows = gt.select(ground_truth.ANNOTATED).rows
        self.assertEqual(len(rows), 5)
        self.assertEqual(gt.records["a"], {"file": "batch_000.csv", "files": ["batch_000.csv"], "rows": 2,
                                           "part": None, "state": "finished", "finished": True})
        self.assertFalse(gt.records["b"]["finished"])
        self.assertEqual(gt.problems, [])
        self.assertEqual([r[ground_truth.LINE_FIELD] for r in rows], [2, 3, 5, 7, 8])   # file lines
        self.assertTrue(rows[1]["_origin"][0].endswith("batch_000.csv#1"))
        self.assertFalse(hasattr(gt, "rows"))                    # rows are handed out by purpose only (select)
        with self.assertRaises(ValueError):                      # read without the pool: no record's part is known
            gt.select(ground_truth.SCHEMA_EVIDENCE)

    def test_problems(self):
        gt_file(self.tmp, "batch_000.csv", [row("a", "MODIS", "I", "ABOARD", "Aqua", "S", "x"),
                                             row("b", "MODIS", "I", "ABOARD", "Aqua", "S", "x", "1"),
                                             row("b", "AIRS", "I", "ABOARD", "Aqua", "S", "x", "0"),
                                             row("c", "The MODIS", "I", "aboard", "Aqua.", "S", "x"),
                                             row("c", "modis", "Other", "ABOARD", "aqua", "S", "y"),
                                             row("d", "AIRS", "Instrument", "ABOARD", "Aqua", "S", "x"),
                                             row("d", "the AIRS", "instrument", "aboard", "Aqua", "s", "y"),
                                             row("d", "AIRS", "Other", "ABOARD", "Aqua", "S", "z")])
        gt_file(self.tmp, "batch_001.csv", [row("a", "AIRS", "I", "ABOARD", "Aqua", "S", "x")])
        gt_file(self.tmp, "batch_002.csv", [["a", "b"]], columns=["id", "subject"])
        gt = ground_truth.read_ground_truth(self.tmp)
        self.assertEqual(len(gt.problems), 6)
        self.assertEqual(gt.state("a"), ground_truth.IN_TWO_FILES)               # in two files: kept out
        self.assertNotIn("a", gt.select(ground_truth.EVALUABLE).ids)
        joined = "\n".join(gt.problems)
        self.assertIn("record a is in batch_000.csv and batch_001.csv", joined)
        self.assertIn("record b (batch_000.csv): all_facts_extracted", joined)
        self.assertIn("record c (batch_000.csv): lines 5 and 6 state the same subject instance, predicate, and object "
                      "instance, with different entity classes.", joined)
        # entity classes differing only in case are the same: lines 7 and 8 are one classed triple twice
        self.assertEqual(len(gt.repeats), 1)
        self.assertEqual(gt.repeats[0], {"copies": 2, "message":
                         "record d (batch_000.csv): lines 7 and 8 are the same classed triple.\n"
                         "- Line 7: AIRS (Instrument) ABOARD Aqua (S)\n"
                         "- Line 8: the AIRS (instrument) aboard Aqua (s)\n\n"
                         "Delete one of the two lines (py helpers/annotate.py), then rerun."})
        self.assertIn(gt.repeats[0]["message"], gt.problems)
        self.assertIn("record d (batch_000.csv): lines 7, 8, and 9 state the same subject instance, predicate, and "
                      "object instance, with different entity classes.\n"
                      "- Line 7: AIRS (Instrument) ABOARD Aqua (S)\n"
                      "- Line 8: the AIRS (instrument) aboard Aqua (s)\n"
                      "- Line 9: AIRS (Other) ABOARD Aqua (S)\n\n"
                      "If they state one fact, delete the line with the wrong entity classes.", gt.problems)
        self.assertIn("batch_002.csv lacks the column(s)", joined)

    def test_check_rows(self):
        gt_file(self.tmp, "batch_000.csv", [
            row("a", "a", "CatalogEntry", "DESCRIBES", "Title A", "X", "(record structure)"),
            row("a", "MODIS", "Instrument", "ABOARD", "Aqua", "Spacecraft", "MODIS aboard Aqua"),
            row("a", "MODIS", "Instrument", "ABOARD", "Terra", "Spacecraft", "MODIS aboard Terra"),
            row("a", "MODIS", "Instrument", "ABOARD", "", "Spacecraft", "x"),
            row("a", "the instrument", "Instrument", "ABOARD", "Aqua", "Spacecraft", ""),
            row("a"),
            row("gone", "x", "y", "z", "w", "v", "s")])
        records = {"a": {"id": "a", "title": "Title A", "notes": "MODIS aboard Aqua since 2002."}}
        found = ground_truth.check_rows(ground_truth.read_ground_truth(self.tmp).select(ground_truth.ANNOTATED), records)
        self.assertEqual([(f["where"], f["errors"]) for f in found], [
            ("batch_000.csv line 2", ["describes_undecided"]),
            ("batch_000.csv line 4", ["source_not_in_text"]),
            ("batch_000.csv line 5", ["incomplete"]),
            ("batch_000.csv line 6", ["no_source_text"]),
            ("batch_000.csv line 8", ["id_not_in_records"])])

    def test_run_order(self):
        from common.audit import run_order
        ids = ["070_evaluate_2026-10-17_1641-10", "070_evaluate_2026-10-17_1642", "070_evaluate_2026-10-17_1641",
               "070_evaluate_2026-10-17_1641-2", "070_evaluate_2026-10-16_2359", "070_evaluate_2026-10-17_1641-9"]
        self.assertEqual(sorted(ids, key=run_order),
                         ["070_evaluate_2026-10-16_2359", "070_evaluate_2026-10-17_1641", "070_evaluate_2026-10-17_1641-2",
                          "070_evaluate_2026-10-17_1641-9", "070_evaluate_2026-10-17_1641-10", "070_evaluate_2026-10-17_1642"])

    def test_vocabulary(self):
        gt_file(self.tmp, "batch_000.csv", [
            row("a", "a", "CatalogEntry", "DESCRIBES", "T", "Dataset", "(record structure)"),
            row("a", "MODIS", "instrument", "ABOARD", "Aqua", "Probe", "s"),
            row("a", "MODIS", "Instrument", "CARRIED_BY", "Aqua", "probe", "s"),
            row("a", "MODIS", "-", "x", "Aqua", "X", "s")])
        hand = {"entity_classes": {"Instrument": "d", "Dataset": "d"}, "predicates": {"ABOARD": "d"},
                "patterns": [("Instrument", "ABOARD", "Dataset")]}
        v = ground_truth.with_coined(hand, ground_truth.read_ground_truth(self.tmp).select(ground_truth.ANNOTATED))
        self.assertEqual(v["coined"], {"entity_classes": ["Probe"], "predicates": ["CARRIED_BY", "x"]})
        self.assertEqual(v["entity_classes"]["Probe"], "")
        self.assertEqual(v["entity_classes"]["Instrument"], "d")
        self.assertNotIn("CatalogEntry", v["entity_classes"])
        self.assertNotIn("DESCRIBES", v["predicates"])
        # the patterns: the file's, then every other one the ground truth uses (not the describes triple's, nor one
        # missing a component class), as first spelled
        self.assertEqual(v["used_patterns"], [("instrument", "ABOARD", "Probe"), ("Instrument", "CARRIED_BY", "probe")])
        self.assertEqual(v["patterns"], [("Instrument", "ABOARD", "Dataset")] + v["used_patterns"])
        # what 050's drafting model is shown: the file's text, then the coined ones, then the pairs the file lacks
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "records_050", ROOT / "050_annotate" / "050_annotate_helpers" / "records.py")
        records_050 = importlib.util.module_from_spec(spec)
        sys.modules["records_050"] = records_050                           # its dataclass needs it registered
        spec.loader.exec_module(records_050)
        text = records_050.vocabulary_text("FILE", v["coined"], v["used_patterns"])
        self.assertTrue(text.startswith("FILE\n\nALSO USED IN THE GROUND TRUTH (no definition yet)\n"))
        self.assertIn("MORE PATTERNS THE GROUND TRUTH USES (subject class -> object class)\nABOARD: instrument -> Probe\n"
                      "CARRIED_BY: Instrument -> probe", text)
        self.assertEqual(records_050.vocabulary_text("FILE", {"entity_classes": [], "predicates": []}, []), "FILE")

    def test_fair_sample(self):
        pool = ["p0", "p1", "p2", "p3"]
        self.assertTrue(ground_truth.fair_sample(pool, {"p0", "p1"})["fair"])
        self.assertTrue(ground_truth.fair_sample(pool, set())["fair"])
        gap = ground_truth.fair_sample(pool, {"p0", "p2"})
        self.assertEqual((gap["fair"], gap["skipped_in_pool"], gap["first_skipped"]), (False, 1, "p1"))
        out = ground_truth.fair_sample(pool, {"p0", "zz"})
        self.assertEqual((out["fair"], out["outside_pool"]), (False, 1))
        self.assertEqual(ground_truth.fair_prefix(pool, {"p0", "p1", "p3"}), ["p0", "p1"])
        self.assertIn("pool position 1", ground_truth.fair_words(gap, {"p1": 1}))


class FairSampleByPart(unittest.TestCase):
    """The fair sample is the longest unbroken run from the start of EACH part of the pool (tuning, held-out) in
    pool order, not of the whole pool: common.ground_truth.pool_parts / fair_prefix, 070's pick_records and
    _first_gap, and 050's choice of records (setting part)."""

    #: pool position -> part: r0 r1 r3 r5 r6 are tuning, r2 r4 r7 held-out
    PARTS = ["tuning", "tuning", "held-out", "tuning", "held-out", "tuning", "tuning", "held-out"]

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.ids = [f"r{i}" for i in range(len(self.PARTS))]
        pool = [{"id": i, "position": n, "part": p} for n, (i, p) in enumerate(zip(self.ids, self.PARTS))]
        (self.tmp / "splits.json").write_text(json.dumps({"ground_truth_candidates": {"records": pool}}), encoding="utf-8")
        (self.tmp / "records.jsonl").write_text(
            "\n".join(json.dumps({"id": i, "title": f"title {i}", "notes": f"notes of {i}"}) for i in self.ids), encoding="utf-8")
        (self.tmp / "ground_truth").mkdir()
        self.pool = pool

    def parts(self):
        return ground_truth.pool_parts(self.pool)

    def write_ground_truth(self, finished=(), unfinished=()):
        rows = [dict(zip(ground_truth.COLUMNS, [i, "", "", "", "", "", "", mark]))
                for ids, mark in ((finished, "1"), (unfinished, "0")) for i in ids]
        if rows:
            write_csv(self.tmp / "ground_truth" / "batch_000.csv", ground_truth.COLUMNS, rows)

    # --- the pure functions

    def test_pool_parts_keeps_pool_order(self):
        self.assertEqual(self.parts(), {"tuning": ["r0", "r1", "r3", "r5", "r6"], "held-out": ["r2", "r4", "r7"]})

    def test_prefix_of_one_part_ignores_the_other(self):
        parts = self.parts()
        taken = {"r0", "r1", "r3", "r5"}                   # held-out r2 not taken: it used to cut off r3, r5
        self.assertEqual(ground_truth.fair_prefix(parts["tuning"], taken), ["r0", "r1", "r3", "r5"])
        self.assertEqual(ground_truth.fair_prefix(parts["held-out"], taken), [])
        self.assertEqual(ground_truth.fair_prefix(self.ids, taken), ["r0", "r1"])      # the whole-pool run: not the rule any more

    def test_gap_in_tuning_stops_tuning_only(self):
        parts = self.parts()
        taken = {"r0", "r3", "r2", "r4"}                   # r1 (tuning) missing
        self.assertEqual(ground_truth.fair_prefix(parts["tuning"], taken), ["r0"])
        self.assertEqual(ground_truth.fair_prefix(parts["held-out"], taken), ["r2", "r4"])

    def test_fair_words_names_the_part(self):
        fair = ground_truth.fair_sample(self.parts()["tuning"], {"r0", "r3"})
        words = ground_truth.fair_words(fair, {"r1": 1}, part="tuning")
        self.assertIn("the tuning part of the pool", words)
        self.assertIn("pool position 1", words)
        ok = ground_truth.fair_sample(self.parts()["held-out"], {"r2", "r4"})
        self.assertIn("first 2 records of the held-out part of the pool", ground_truth.fair_words(ok, {}, part="held-out"))

    # --- step 070

    def evaluated(self, finished, unfinished=(), extracted=None):
        import importlib.util
        import sys
        spec = importlib.util.spec_from_file_location("records_070", ROOT / "070_evaluate" / "070_evaluate_helpers" / "records.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules["records_070"] = module
        spec.loader.exec_module(module)
        self.write_ground_truth(finished, unfinished)
        extracted = list(finished) if extracted is None else extracted
        (self.tmp / "details.json").write_text(json.dumps({"made": {}, "records": [
            {"id": i, "status": "extracted"} for i in extracted]}), encoding="utf-8")
        write_csv(self.tmp / "extracted.csv", ["id"], [])
        write_csv(self.tmp / "removed.csv", ["id", "reason"], [])
        write_csv(self.tmp / "candidates.csv", ["id", "stratum"], [{"id": i, "stratum": "s"} for i in self.ids])
        (self.tmp / "schema_used.json").write_text(json.dumps({"learned_from": {"known": True, "ids": []}}), encoding="utf-8")
        (self.tmp / "reviews.csv").write_text(",".join(partial_reviews.COLUMNS) + "\n", encoding="utf-8")
        inputs = {"ground_truth": self.tmp / "ground_truth" / "batch_*.csv", "ground_truth_schema": ROOT / "annotations" / "ground_truth_schema.txt",
                  "splits": self.tmp / "splits.json", "candidates": self.tmp / "candidates.csv",
                  "extracted_triples_details": self.tmp / "details.json", "extracted_triples": self.tmp / "extracted.csv",
                  "extracted_triples_removed": self.tmp / "removed.csv", "schema_used": self.tmp / "schema_used.json",
                  "records": self.tmp / "records.jsonl", "partial_reviews": self.tmp / "reviews.csv"}
        return module.pick_records(inputs, {"confirm_paid_calls": False})

    def test_070_tuning_continues_past_an_unfinished_held_out_record(self):
        ev = self.evaluated(finished=["r0", "r1", "r3", "r5"], unfinished=["r2"])
        self.assertEqual([r["id"] for r in ev.records], ["r0", "r1", "r3", "r5"])
        self.assertEqual({r["part"] for r in ev.records}, {"tuning"})
        self.assertEqual(ev.left_out, {})

    def test_070_held_out_run_is_independent(self):
        ev = self.evaluated(finished=["r2", "r4", "r0"], unfinished=["r1"])          # tuning r1 unfinished: tuning stops at r0
        self.assertEqual([r["id"] for r in ev.records], ["r0", "r2", "r4"])

    def test_070_gap_in_tuning_stops_tuning_only(self):
        ev = self.evaluated(finished=["r0", "r3", "r2", "r4"], unfinished=["r1"])
        self.assertEqual([r["id"] for r in ev.records], ["r0", "r2", "r4"])
        left = next(v for k, v in ev.left_out.items() if k.startswith("outside the fair sample"))
        self.assertEqual(left, ["r3"])
        note = next(n for n in ev.notes if "left out because they aren't in the fair sample" in n)
        self.assertIn("The first tuning record missing from the fair sample of the tuning part is pool position #1 (`r1`)", note)
        self.assertIn("not finished in the ground truth", note)
        self.assertNotIn("held-out record missing", note)                              # the held-out part has no gap

    def test_070_near_misses(self):
        # a held-out record finished but not extracted stops the held-out run, not the tuning one
        ev = self.evaluated(finished=["r0", "r1", "r2", "r3"], extracted=["r0", "r1", "r3", "r4"])
        self.assertEqual([r["id"] for r in ev.records], ["r0", "r1", "r3"])
        self.assertEqual(ev.left_out["finished, but not extracted by 060's last run"], ["r2"])
        # nothing evaluable: the message names the first gap of each part
        from common.stop import Stop
        with self.assertRaises(Stop) as stop:
            self.evaluated(finished=["r5"])                                           # r0 (tuning) and r2 (held-out) missing
        text = str(stop.exception)
        self.assertIn("The first tuning record missing", text)
        self.assertIn("The first held-out record missing", text)
        self.assertIn("not in the ground truth yet", text)
        self.assertIn("set --part tuning", text)

    # --- step 050

    def chosen(self, per=3, part="tuning", start=0, finished=(), waiting=(), ids=""):
        import importlib.util
        import sys
        spec = importlib.util.spec_from_file_location("records_050", ROOT / "050_annotate" / "050_annotate_helpers" / "records.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules["records_050"] = module
        spec.loader.exec_module(module)
        self.write_ground_truth(finished)
        out = self.tmp / "out"
        out.mkdir(exist_ok=True)
        if waiting:
            write_csv(out / "drafted_triples_batch1.csv", ["id"], [{"id": i} for i in waiting])
        inputs = {"records": self.tmp / "records.jsonl", "splits": self.tmp / "splits.json",
                  "ground_truth_schema": ROOT / "annotations" / "ground_truth_schema.txt",
                  "ground_truth": self.tmp / "ground_truth" / "batch_*.csv"}
        return module.pick_records(inputs, {"records_per_batch": per, "start_position": start, "part": part, "ids": ids,
                                            "max_chars": 8000}, out)

    def test_050_picks_tuning_positions_skipping_held_out(self):
        c = self.chosen(per=4)
        self.assertEqual([i["id"] for i in c.items], ["r0", "r1", "r3", "r5"])
        self.assertEqual([i["position"] for i in c.items], [0, 1, 3, 5])
        self.assertTrue(any("pool positions 0, 1, 3, 5" in n and "setting part: tuning" in n for n in c.notes))
        self.assertTrue(all(f["fair"] for f in c.fair.values()))                      # held-out untouched: still fair

    def test_050_skips_done_and_waiting_in_the_part(self):
        c = self.chosen(per=2, finished=["r0"], waiting=["r1"])
        self.assertEqual([i["id"] for i in c.items], ["r3", "r5"])

    def test_050_held_out_and_both(self):
        self.assertEqual([i["id"] for i in self.chosen(per=5, part="held-out").items], ["r2", "r4", "r7"])
        self.assertEqual([i["id"] for i in self.chosen(per=5, part="both").items], ["r0", "r1", "r2", "r3", "r4"])
        short = self.chosen(per=5, part="held-out")
        self.assertTrue(any("only 3 are left in the held-out pool" in n and "--part both" in n for n in short.notes))

    def test_050_drafting_one_part_keeps_the_other_fair_and_names_the_gap_part(self):
        c = self.chosen(per=1, part="tuning", ids="r3")                              # hand-picked: tuning r0, r1 skipped
        self.assertFalse(c.fair["tuning"]["fair"])
        self.assertTrue(c.fair["held-out"]["fair"])
        note = next(n for n in c.notes if "no longer the first records" in n)
        self.assertIn("the tuning part of the pool", note)
        self.assertNotIn("held-out part", note)

    def test_050_refuses_an_unknown_part(self):
        from common.stop import Stop
        for bad in ("tunning", "", "held_out", "all"):
            with self.subTest(part=bad), self.assertRaises(Stop):
                self.chosen(part=bad)
        for ok in ("Both", " tuning "):                       # read without case or surrounding spaces (common.step.Spec)
            self.chosen(part=ok)

    def test_050_ids_ignore_part_with_a_note(self):
        c = self.chosen(part="held-out", ids="r0")
        self.assertEqual([i["id"] for i in c.items], ["r0"])
        self.assertTrue(any("part (held-out) is ignored" in n for n in c.notes))


class UnitsListed(unittest.TestCase):

    def test_terminology_lists_every_unit(self):
        """docs/terminology.md (evened out) lists exactly text_match.UNITS, in its order."""
        import re
        text = (ROOT / "docs" / "terminology.md").read_text(encoding="utf-8")
        listed = text.split("(`UNITS` in that file): ", 1)[1].split("; and only when", 1)[0]
        listed = re.sub(r" \(also written with the micro sign, `µm`\)", "", listed)
        self.assertEqual(tuple(re.findall(r"`([^`]+)`", listed)), text_match.UNITS)


class Quantities(unittest.TestCase):
    """text_match: an instance that is wholly a quantity is the same as another of the same quantity, however
    written; anything else is compared as words, as before."""

    def test_same_quantity(self):
        key = text_match.instance_key
        for a, b in [("1km", "1 kilometer (km)"), ("1 km", "1 kilometer (km)"), ("1 km", "1 Kilometre"),
                     ("4.63 km", "4630 m"), ("4,630 m", "4.63 km"), ("8 day", "8 days"), ("500 meters", "500m"),
                     ("5 min", "5 minutes"), ("1.5 µm", "1500 nm"), ("3.95micron", "3.95 μm"), ("0.1 km", "100 m"),
                     ("36 km/h", "10 m/s"), ("10 meters per second", "10 m s-1"), ("1013 hPa", "1013 mbar"),
                     ("300 K", "300 kelvin"), ("25°C", "25 degrees Celsius"), ("The 1 km.", "1 km")]:
            with self.subTest(a=a, b=b):
                self.assertEqual(key(a), key(b))

    def test_near_misses_differ(self):
        key = text_match.instance_key
        for a, b in [("1 km", "10 km"), ("1 km", "1 km²"), ("1 km", "1 km2"), ("1 km", "1 square kilometer"),
                     ("1 km", "1 kilometer per second"), ("1 km", "1 m"), ("500 m", "500 nm"), ("500 m", "500 mm"),
                     ("5 minutes", "5 seconds"), ("5 ms", "5 m"), ("300 K", "300 °C"), ("273.15 K", "0 °C"),
                     ("1 kilometer (m)", "1 km"), ("8day", "8 days")]:
            with self.subTest(a=a, b=b):
                self.assertNotEqual(key(a), key(b))

    def test_not_quantities_left_as_words(self):
        for s in ["2002", "10 to 2.15 hPa", "50%", "50 percent", "1 km x 1 km", "MOD021KM", "Level 3", "8day",
                  "1 kilometer per second", "1 km/s", "1 square kilometer", "1 kilometer (m)", "Version 2.5"]:
            with self.subTest(s=s):
                self.assertIsNone(text_match.quantity(s))
                self.assertEqual(text_match.instance_key(s), text_match.norm_text(s))
        self.assertIsNone(text_match.quantity_words("bands 1 and 2 at 250 m"))     # three numbers
        self.assertIsNone(text_match.quantity_words("the 2002 product"))           # a number, no unit

    def test_quantity_inside_a_longer_instance(self):
        words = text_match.quantity_words
        self.assertEqual(words("1 kilometer (km) pixel"), ["1000 m", "pixel"])
        self.assertEqual(words("weekly (8 day)"), ["weekly", "691200 s"])
        self.assertEqual(words("1 km"), words("1km"))

    def test_found_in_a_text(self):
        t = text_match.Text("Gridded at 1 kilometer (km) and 4.63 km; sampled every 8 days at 10 to 20 hPa.")
        for needle in ["1 km", "1000 m", "4630 m", "8 day", "20 hPa", "1 kilometer (km)"]:
            self.assertTrue(t.contains(needle), needle)
        for needle in ["10 km", "1 m", "4.63 m", "8 hours", "10 km/h", "1 km pixel", "2 km"]:
            self.assertFalse(t.contains(needle), needle)
        self.assertFalse(text_match.Text("an area of 1 square kilometer").contains("1 km"))
        self.assertFalse(text_match.Text("moving at 1 kilometer per second").contains("1 km"))

    def test_units_built_from_the_one_table(self):
        self.assertEqual(text_match.UNITS, tuple(sp for row in text_match.QUANTITY_UNITS for sp in row[3]))
        spellings = [sp for row in text_match.QUANTITY_UNITS for sp in row[3] + row[4]]
        self.assertEqual(len(spellings), len(set(spellings)))                     # each spelling is one unit
        dimensions = {row[1] for row in text_match.QUANTITY_UNITS}
        for d in dimensions:                                                      # each has one base unit
            self.assertEqual(sum(1 for row in text_match.QUANTITY_UNITS if row[1] == d and row[2] == 1), 1, d)


class FinishedMarks(unittest.TestCase):
    """all_facts_extracted is 0 or 1; any other value is a problem of the ground truth, and the record isn't
    finished (ground_truth.read_ground_truth)."""

    def test_other_values(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp)
        rows = [dict(zip(ground_truth.COLUMNS, row(rid, f"MODIS {k}", "I", "ABOARD", "Aqua", "S", "x", mark)))
                for k, (rid, mark) in enumerate((("a", "yes"), ("a", "yes"), ("b", "1"), ("c", "1"), ("c", "0"), ("d", " 1 ")))]
        write_csv(tmp / "batch_000.csv", ground_truth.COLUMNS, rows)
        gt = ground_truth.read_ground_truth(tmp)
        self.assertEqual(len(gt.problems), 2, gt.problems)
        self.assertIn("record a (batch_000.csv): all_facts_extracted is 'yes' on 2 row(s), which is neither 0 nor 1",
                      gt.problems[0])
        self.assertIn("record c (batch_000.csv): all_facts_extracted is 0 on some rows, 1 on others", gt.problems[1])
        self.assertEqual({r: v["finished"] for r, v in gt.records.items()},
                         {"a": False, "b": True, "c": False, "d": True})      # spaces around a value are ignored


class Checks(unittest.TestCase):

    def test_text_match(self):
        t = text_match.Text("MODIS – the “Moderate” Resolution\nImaging   Spectroradiometer, aboard Aqua.")
        for needle in ["modis - the \"moderate\" resolution imaging spectroradiometer", "The Aqua.", "aboard  aqua",
                       "‘Moderate’ resolution"]:
            self.assertTrue(t.contains(needle), needle)
        for needle in ["", "  ", "...", "Terra", None]:
            self.assertFalse(t.contains(needle), needle)
        self.assertEqual(text_match.norm_text("  The MODIS, "), "modis")
        self.assertEqual(text_match.norm_text("Theory"), "theory")                    # "the" only as a word

    def test_inner_punctuation_in_a_lookup(self):
        # a passage copied without (or with an extra) comma is still found; punctuation counts as a space, not nothing
        t = text_match.Text("The MODIS, aboard Aqua, measures snow (daily). Version 2.5 since 2002.")
        for needle in ["MODIS aboard Aqua", "MODIS, aboard Aqua", "MODIS aboard Aqua measures", "snow daily",
                       "measures snow (daily)", "Version 2.5", "aboard Aqua; measures"]:
            self.assertTrue(t.contains(needle), needle)
        for needle in ["Version 25", "MODIS aboard Terra", "snowdaily", "MODIS Aqua"]:
            self.assertFalse(t.contains(needle), needle)
        # comparing two component instances (pairing) keeps inner punctuation
        self.assertNotEqual(text_match.norm_text("MODIS, Aqua"), text_match.norm_text("MODIS Aqua"))

    def test_source_text_in_passages(self):
        """Suppose a fact's source text is two passages of the record joined by " … " (a fact a predicate's definition
        derives from statements in two places). Then it is in the text when each passage is, the join written in any
        of its ways (" … ", " ... ", "…" or "..." without spaces: common.triples_io.passages). Near misses: one passage
        not in the text, two dots (not a join), and a lone passage."""
        text = text_match.Text("The first is a skin SST (NSST). Other words here. The SST4 product has lower uncertainty.")
        row = {"subject": "SST4", "object": "skin SST", "source_text": ""}
        def errors(source):
            return validate.check_triple_instance({**row, "source_text": source}, text)[0]
        self.assertEqual(errors("The first is a skin SST … The SST4 product has lower uncertainty"), [])
        self.assertEqual(errors("The first is a skin SST … The SST4 product has higher uncertainty"),
                         ["source_not_in_text"])
        self.assertEqual(errors("The first is a skin SST ... The SST4 product has lower uncertainty"), [])
        self.assertEqual(errors("The first is a skin SST…The SST4 product has lower uncertainty"), [])
        self.assertEqual(errors("The first is a skin SST...The SST4 product has lower uncertainty"), [])
        self.assertEqual(errors("The first is a skin SST .. The SST4 product has lower uncertainty"), ["source_not_in_text"])
        self.assertEqual(errors("The SST4 product has lower uncertainty"), [])
        self.assertEqual(validate.PASSAGES_JOIN, " … ")

    def test_twin_kinds(self):
        # one kind each, the one sharing the most text: whole text, notes only, title only; empty fields never match
        import doctest
        runner = doctest.DocTestRunner()
        for test in doctest.DocTestFinder().find(ground_truth.twin_kinds, globs={"twin_kinds": ground_truth.twin_kinds}):
            runner.run(test)
        self.assertEqual(runner.summarize(verbose=False), (0, 2))
        learned = [{"title": "Snow, Aqua", "notes": ""}, {"title": "", "notes": ""}]
        self.assertEqual(ground_truth.twin_kinds({"a": {"title": "Snow, Aqua", "notes": ""}, "b": {"title": "", "notes": ""}},
                                                  learned), {"a": "title only", "b": ""})

    def test_whole_words_in_a_lookup(self):
        # a match may not cut a word or a number in two; a plural ending may follow; a letter next to a digit is a break
        t = text_match.Text("Salinity from Aquarius and the Aqua satellites, in 25 minutes at 500 meter, "
                            "near Comet67P (MOD04_L2), CO2-based, starting at 12.5 km.")
        for needle in ["Aqua satellite", "Aqua satellites", "Aquarius", "67P", "Comet", "L2", "CO2", "12.5 km", "25 minutes"]:
            self.assertTrue(t.contains(needle), needle)
        for needle in ["Aquar", "5 minutes", "500 me", "START", "2.5 km", "sat", "MOD0", "500 meters per"]:
            self.assertFalse(t.contains(needle), needle)
        self.assertTrue(t.contains("500 m"))          # not as words ("meter" isn't cut), but as the same quantity
        self.assertTrue(text_match.Text("See Aquarius. Aqua too.").contains("Aqua"))     # a later whole-word match

    def test_number_and_unit(self):
        # a number and a unit in UNITS match with or without a space; anything else is left as it was
        norm = text_match.norm_text
        for a, b in [("500m", "500 m"), ("4.63km", "4.63 km"), ("3.95 micron", "3.95micron"), ("1KM", "1 km"),
                     ("10µm", "10 μm"), ("25°C", "25 °C"), ("5m/s", "5 m/s"), ("8.5GHz", "8.5 ghz"),
                     ("1,000m", "1,000 m")]:
            self.assertEqual(norm(a), norm(b), (a, b))
        self.assertEqual(norm("4.63km"), "4.63 km")                                     # one space is the evened-out form
        self.assertEqual(norm("the 3 and 9micron channels"), "3 and 9 micron channels")  # only "9micron"
        for s, unchanged in [("the 3 and 9 micron channels", "3 and 9 micron channels"), ("8 Day", "8 day"),
                             ("8Day", "8day"), ("500 meters", "500 meters"), ("500meters", "500meters"),
                             ("Level 3", "level 3"), ("V 2019", "v 2019"), ("V061", "v061"), ("5-Min", "5-min"),
                             ("2015-10-22 to 2015-12-31", "2015-10-22 to 2015-12-31"), ("L2 pixels", "l2 pixels"),
                             ("L2s", "l2s"), ("36 spectral bands", "36 spectral bands"), ("m", "m"),
                             ("MOD021KM", "mod021km"), ("500m2", "500m2"), ("5mins", "5mins")]:
            self.assertEqual(norm(s), unchanged, s)
        for a, b in [("500 mm", "500 m"), ("500mm", "500m"), ("500 meters", "500 m"), ("8 Day", "8Day"), ("5 ms", "5 m")]:
            self.assertNotEqual(norm(a), norm(b), (a, b))
        # in a lookup too, whichever side lost the space
        t = text_match.Text("Swath at 500m and 4.63 km, from the 3 and 9micron channels.")
        for needle in ["500 m", "500m", "4.63km", "4.63 km", "9 micron channels", "3 and 9 micron"]:
            self.assertTrue(t.contains(needle), needle)
        for needle in ["500 mm", "500", "463 km", "3 micron"]:
            self.assertEqual(t.contains(needle), needle == "500", needle)

    def test_keys(self):
        self.assertEqual(triples_io.component_class_key("physical quantity"), triples_io.component_class_key("PhysicalQuantity"))
        self.assertEqual(triples_io.component_class_key("HAS_VERSION"), triples_io.component_class_key("has-version"))
        self.assertNotEqual(triples_io.component_class_key("Level1"), triples_io.component_class_key("Level2"))
        self.assertEqual(triples_io.triple_key({"subject": "The MODIS", "predicate": "is_aboard", "object": "Aqua"}),
                         triples_io.triple_key({"subject": "modis", "predicate": "IS ABOARD", "object": "aqua."}))

    def test_clean_triple(self):
        self.assertEqual(triples_io.clean_triple({"subject": " A  b ", "predicate": "P", "object": 2020, "source_text": ""}),
                         {"subject": "A b", "predicate": "P", "object": "2020", "flags": []})
        for bad in [None, [], {"subject": "", "predicate": "P", "object": "O"}, {"subject": ["A"], "predicate": "P", "object": "O"},
                    {"subject": True, "predicate": "P", "object": "O"}, {"subject": "S", "predicate": "P"}]:
            self.assertIsNone(triples_io.clean_triple(bad), bad)

    def test_describes(self):
        r = triples_io.describes_triple("id1", " A\n title ", "")
        self.assertEqual((r["object"], r["object_class"]), ("A title", triples_io.UNDECIDED))
        self.assertTrue(triples_io.is_describes(r))
        self.assertTrue(triples_io.is_describes({"subject_class": "catalog entry", "predicate": "describes"}))

    def test_check_triple_instance(self):
        text = text_match.Text("title: MODIS Snow\n\nnotes: MODIS aboard Aqua since 2002.")
        ok = {"subject": "MODIS", "predicate": "ABOARD", "object": "Aqua", "source_text": "MODIS aboard Aqua"}
        self.assertEqual(validate.check_triple_instance(ok, text), ([], []))
        self.assertEqual(validate.check_triple_instance({**ok, "source_text": " "}, text)[0], ["no_source_text"])
        self.assertEqual(validate.check_triple_instance({**ok, "source_text": "aboard Terra"}, text)[0], ["source_not_in_text"])
        flags = validate.check_triple_instance({**ok, "subject": "MODIS Snow", "object": "Terra"}, text, title="MODIS Snow")[1]
        self.assertEqual(flags, ["object_not_in_text", "object_not_in_source"])      # the title may be the subject
        self.assertIn("subject_equals_object", validate.check_triple_instance({**ok, "object": "the modis"}, text)[1])

    def test_dataset_subject_not_title(self):
        title = "MODIS Snow Cover Daily"
        text = text_match.Text(f"title: {title}\n\nnotes: The radiance data and the {title} are used.")
        row = {"subject": title, "subject_class": "Dataset", "predicate": "USES", "object": "radiance data",
               "object_class": "Dataset", "source_text": "The radiance data"}
        flag = "dataset_subject_not_title"
        flags = lambda r: validate.check_triple_instance(r, text, title)[1]
        self.assertNotIn(flag, flags(row))
        self.assertNotIn(flag, flags({**row, "subject": "  modis SNOW   cover daily "}))
        self.assertIn(flag, flags({**row, "subject": "MODIS snow product"}))
        self.assertIn(flag, flags({**row, "subject": "radiance data", "object": "MODIS Snow Cover Daily"}))
        self.assertNotIn(flag, flags({**row, "subject": "radiance data", "subject_class": "Instrument"}))
        describes = {"id": "r1", "subject": "r1", "subject_class": "CatalogEntry", "predicate": "describes",
                     "object": title, "object_class": "Dataset", "source_text": title}
        self.assertNotIn(flag, flags(describes))
        self.assertNotIn(flag, validate.check_triple_instance({**row, "subject": "radiance data"}, text)[1])   # no title
        self.assertIn(flag, validate.FLAGS)

    def test_schema_flags(self):
        entries = validate.SchemaEntries({"entity_classes": {"Instrument": "", "Spacecraft": ""}, "predicates": {"ABOARD": ""},
                                          "patterns": [("Instrument", "ABOARD", "Spacecraft")]})
        t = {"subject_class": "instrument", "predicate": "aboard", "object_class": "Space craft"}
        self.assertEqual(validate.check_against_schema(t, entries), [])
        self.assertEqual(validate.check_against_schema({**t, "object_class": "Instrument"}, entries), ["pattern_not_in_schema"])
        self.assertEqual(validate.check_against_schema({**t, "predicate": "CARRIES", "subject_class": "Probe"}, entries),
                         ["subject_class_not_in_schema", "predicate_not_in_schema"])
        self.assertEqual(entries.spelling["entity_classes"]["spacecraft"], "Spacecraft")
        # a pinned predicate: its pins decide, "any" for any entity class; a pattern not seen yet but pinned is fine
        pinned = validate.SchemaEntries({"entity_classes": {"Instrument": "", "Spacecraft": "", "Person": ""},
                                         "predicates": {"BUILT_BY": ""}, "patterns": [],
                                         "pinned": {"BUILT_BY": [("any", "Person"), ("Spacecraft", "Instrument")]}})
        b = {"subject_class": "Instrument", "predicate": "BUILT_BY", "object_class": "Person"}
        self.assertEqual(validate.check_against_schema(b, pinned), [])
        self.assertEqual(validate.check_against_schema({**b, "subject_class": "Spacecraft", "object_class": "Instrument"},
                                                       pinned), [])
        self.assertEqual(validate.check_against_schema({**b, "object_class": "Spacecraft"}, pinned), ["pattern_not_pinned"])
        self.assertEqual(validate.check_against_schema({**b, "subject_class": "Instrument", "object_class": "Instrument"},
                                                       pinned), ["pattern_not_pinned"])
        head = triples_io.describes_triple("r", "T", "Probe")
        self.assertEqual(validate.check_describes(head, "r", entries), ([], ["describes_class_not_in_schema"]))
        self.assertEqual(validate.check_describes(head, "other")[0], ["describes_subject_not_id"])


class BuildRows(unittest.TestCase):

    def test_build_rows(self):
        entries = validate.SchemaEntries({"entity_classes": {"Instrument": "", "Spacecraft": ""}, "predicates": {"ABOARD": ""},
                                          "patterns": [("Instrument", "ABOARD", "Spacecraft")]})
        good = {"subject": "MODIS", "subject_class": "Instrument", "predicate": "ABOARD", "object": "Aqua",
                "object_class": "Spacecraft", "source_text": "MODIS aboard Aqua"}
        replies = [{"describes_class": "", "triples": [good, dict(good, subject="the MODIS"), {"subject": None}]},
                   {"describes_class": "Dataset", "triples": [dict(good, object_class="Instrument"),
                                                              dict(good, object="Moon", source_text="aboard the Moon")]},
                   "not a dict", {"triples": "not a list"}]
        rows, removed = extraction.build_rows("r1", "T", "title: T\n\nnotes: MODIS aboard Aqua.", replies, entries)
        self.assertEqual(rows[0]["object_class"], "Dataset")                         # the only entity class named
        self.assertEqual(rows[0]["flags"], ["describes_class_not_in_schema"])
        self.assertEqual([r["object"] for r in rows[1:]], ["Aqua", "Aqua", "Moon"])
        self.assertEqual(rows[1]["flags"], ["conflicting_classes"])
        self.assertIn("conflicting_classes", rows[2]["flags"])
        self.assertIn("pattern_not_in_schema", rows[2]["flags"])
        self.assertEqual(rows[3]["errors"], ["source_not_in_text"])
        self.assertEqual(sorted(r["reason"] for r in removed), ["duplicate", "malformed", "malformed", "malformed"])

    def test_duplicate_keeps_the_copy_that_passed(self):
        """A fact stated twice: the copy kept is the first that passed its checks, so a first copy with a wrong
        source text doesn't lose the fact; both good, the first is kept; both bad, the first is kept (with its
        errors); the describes triple is never one of them."""
        entries = validate.SchemaEntries({"entity_classes": {"Instrument": "", "Spacecraft": ""}, "predicates": {"ABOARD": ""},
                                          "patterns": [("Instrument", "ABOARD", "Spacecraft")]})
        good = {"subject": "MODIS", "subject_class": "Instrument", "predicate": "ABOARD", "object": "Aqua",
                "object_class": "Spacecraft", "source_text": "MODIS aboard Aqua"}
        bad = dict(good, source_text="MODIS rides Aqua")
        text = "title: T\n\nnotes: MODIS aboard Aqua."
        for first, second, kept_source, errors in [(bad, good, "MODIS aboard Aqua", []),
                                                   (good, bad, "MODIS aboard Aqua", []),
                                                   (good, dict(good), "MODIS aboard Aqua", []),
                                                   (bad, dict(bad, source_text="nowhere"), "MODIS rides Aqua",
                                                    ["source_not_in_text"])]:
            with self.subTest(first=first["source_text"], second=second["source_text"]):
                rows, removed = extraction.build_rows("r1", "T", text, [{"triples": [first]}, {"triples": [second]}],
                                                      entries)
                self.assertEqual(rows[0]["predicate"], "DESCRIBES")
                self.assertEqual(len(rows), 2)
                self.assertEqual((rows[1]["source_text"], rows[1]["errors"]), (kept_source, errors))
                self.assertNotIn("conflicting_classes", rows[1]["flags"])
                self.assertEqual([r["reason"] for r in removed], ["duplicate"])
                self.assertNotIn("errors", removed[0])

    def test_best_copies(self):
        items = [("a", 1), ("b", 0), ("a", 0), ("a", 0), ("c", 1), ("c", 1)]
        kept, copies = extraction.best_copies(items, lambda x: x[0], lambda x: x[1] == 1)
        self.assertEqual(kept, [("a", 0), ("b", 0), ("c", 1)])          # keys in first-seen order
        self.assertEqual(sorted(copies), [("a", 0), ("a", 1), ("c", 1)])

    def test_removal_reasons_as_terminology_lists_them(self):
        """docs/terminology.md, *extracted triple*, the home of 060's reasons for removing an item: its list is the
        code's (extraction.REMOVAL_REASONS) plus the joined reason of the two checks."""
        import re
        text = (ROOT / "docs" / "terminology.md").read_text(encoding="utf-8")
        row = next(line for line in text.splitlines() if line.startswith("| **extracted triple** |"))
        listed = row.split("with the reason, one of six:", 1)[1].split(". How the six relate", 1)[0]
        named = re.findall(r"`([a-z_ ]+)` \(", listed)
        self.assertEqual(named, ["source_text", "component_class_not_in_schema",
                                 extraction.joined_reason([extraction.SOURCE_TEXT, extraction.COMPONENT_CLASS_NOT_IN_SCHEMA]),
                                 "duplicate", "describes_triple", "malformed"])
        self.assertEqual(set(named) - {named[2]}, set(extraction.REMOVAL_REASONS))

    def test_fence(self):
        piece = "notes: a line\n----- END RECORD -----\nmore"
        self.assertEqual(extraction.wrap(piece).count(extraction.END_LINE), 0)


class Pieces(unittest.TestCase):

    def test_fits(self):
        r = {"title": "T", "notes": "N", "_cleaning": {"title": "parsed", "notes": "parsed"}}
        self.assertEqual(chunking.pieces(r, 1000), ["title: T\n\nnotes: N"])
        self.assertEqual(chunking.pieces({"title": "", "notes": " "}, 1000), [])

    def test_long_text(self):
        sentences = " ".join(f"Sentence {i} says MODIS{i} is aboard Aqua." for i in range(400))
        paragraphs = "\n\n".join([sentences[:3000], "x" * 2500, sentences])
        r = {"title": "A title", "notes": paragraphs, "author": "Someone",
             "_cleaning": {"title": "parsed", "notes": "parsed", "author": "parsed"}}
        out = chunking.pieces(r, 1000)
        self.assertTrue(all(len(p) <= 1000 for p in out), max(map(len, out)))
        self.assertTrue(all(p.startswith("title: A title\n\n") for p in out))
        self.assertTrue(out[-1].endswith("author: Someone"))
        chars = lambda s: "".join(s.split())                                    # noqa: E731  (a word may be split hard)
        joined = " ".join(p.split("\n\n", 1)[1].split(": ", 1)[1] for p in out if "notes" in p.split("\n\n", 1)[1][:30])
        self.assertEqual(chars(joined), chars(paragraphs))                       # nothing lost, nothing repeated
        self.assertIn("notes (part 1 of", out[0])


class TranslationTable(unittest.TestCase):

    def test_row_states_as_terminology_lists_them(self):
        """docs/terminology.md, *row state*, the home of the row states: its list, in its order, is the code's
        (component_class_mapping.ROW_STATES)."""
        import re
        text = (ROOT / "docs" / "terminology.md").read_text(encoding="utf-8")
        row = next(line for line in text.splitlines() if line.startswith("| **row state** |"))
        listed = row.split("one of six", 1)[1].split("How they relate", 1)[0]
        named = list(dict.fromkeys(re.findall(r"\*\*([a-z ]+)\*\*", listed)))
        self.assertEqual(tuple(named), component_class_mapping.ROW_STATES)

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_stale_gtt(self):
        """A checked row is stale when the ground truth schema's definition of its component class of the ground truth
        vocabulary differs from the one stored when the row was checked, including a first definition."""
        gtt = component_class_mapping.gtt_definitions(
            {"entity_classes": {"Spacecraft": "a vehicle  in space", "Probe": ""}, "predicates": {"ABOARD": "is on"}})
        row = lambda kind, gtt_name, stored: {"kind": kind, "component_class_in_gtt": gtt_name,   # noqa: E731
                                              "definition_in_gtt": stored}
        cases = [(row("entity class", "Spacecraft", "a vehicle in space"), False),        # spacing aside
                 (row("entity class", "spacecraft", "a vehicle in space"), False),        # loose match
                 (row("entity class", "Spacecraft", "a craft"), True),                    # redefined
                 (row("entity class", "Probe", ""), False),                               # coined, still undefined
                 (row("predicate", "ABOARD", ""), True),                                  # given its first definition
                 (row("entity class", "(none)", ""), False),                              # nothing to compare
                 (row("entity class", "Rocket", "a craft"), False)]                       # a missing target instead
        for r, stale in cases:
            with self.subTest(r=r):
                self.assertEqual(component_class_mapping.is_stale_gtt(r, gtt), stale)

    def test_missing_target(self):
        """A row translating to a component class the ground truth schema doesn't have (not (none)) has a missing
        target; a spelling the loose match finds, and (none), don't."""
        gtt = component_class_mapping.gtt_definitions({"entity_classes": {"Spacecraft": "a craft"}, "predicates": {}})
        for kind, name, missing in (("entity class", "Rocket", True), ("entity class", "space-craft", False),
                                    ("entity class", "(none)", False), ("predicate", "Spacecraft", True)):
            with self.subTest(name=name, kind=kind):
                r = {"kind": kind, "component_class_in_gtt": name, "definition_in_gtt": ""}
                self.assertEqual(component_class_mapping.is_missing_target(r, gtt), missing)

    def test_read_stale_repeats(self):
        cols = component_class_mapping.COLUMNS
        path = self.tmp / "m.csv"
        write_csv(path, cols, [
            dict(zip(cols, ["entity class", "Satellite", "Spacecraft", "", "yes", "an  orbiting craft"])),
            dict(zip(cols, ["entity class", "", "", "", "", ""])),
            dict(zip(cols, ["predicate", "MOUNTED_ON", "ABOARD", "", "", "is on"])),
            dict(zip(cols, ["entity class", "satellite", "(none)", "", "", "old"]))])
        rows = component_class_mapping.read_mapping(path)
        self.assertEqual([r["_line"] for r in rows], [2, 4, 5])
        definitions = component_class_mapping.crt_definitions(
            {"entity_classes": [{"component_class": "Satellite", "definition": "an orbiting craft"}],
             "predicates": [{"component_class": "MOUNTED_ON", "definition": "sits on"}]})
        self.assertEqual([component_class_mapping.is_stale(r, definitions) for r in rows], [False, True, True])
        self.assertEqual(component_class_mapping.repeats(rows),
                         [{"kind": "entity class", "component_class": "Satellite", "lines": [2, 5]}])
        write_csv(path, [c for c in cols if c != "checked"], [])
        with self.assertRaisesRegex(ValueError, "lacks the column"):
            component_class_mapping.read_mapping(path)
        # a table from before conditional rows has no condition columns: its rows read as unconditional
        old = [c for c in cols if c not in component_class_mapping.CONDITIONS]
        write_csv(path, old, [dict(zip(old, ["predicate", "MOUNTED_ON", "ABOARD", "no", "yes", "is on", "is carried on"]))])
        self.assertEqual(component_class_mapping.condition(component_class_mapping.read_mapping(path)[0]), (None, None))

    def test_real_file_reads(self):
        component_class_mapping.read_mapping()
        self.assertEqual(component_class_mapping.value_problems(component_class_mapping.read_mapping()), [])

    def test_fixed_values(self):
        """kind, swap_subject_and_object and checked are read ignoring case and spaces at either end; any other value
        (or "yes" to swap an entity class) is a problem, naming its line."""
        cols = component_class_mapping.COLUMNS
        path = self.tmp / "m.csv"
        write_csv(path, cols, [
            dict(zip(cols, ["Entity Class", "Satellite", "Spacecraft", " No", "YES", "", ""])),
            dict(zip(cols, ["predicate", "CARRIES", "ABOARD", "Yes", "Same  Component class", "", ""])),
            dict(zip(cols, ["predicate", "HOSTS", "ABOARD", "y", "checked", "", ""])),
            dict(zip(cols, ["entity class", "Probe", "Spacecraft", "yes", "no", "", ""])),
            dict(zip(cols, ["sort", "Rover", "(none)", "", "", "", ""]))])
        rows = component_class_mapping.read_mapping(path)
        self.assertEqual([(r["kind"], r["swap_subject_and_object"], r["checked"]) for r in rows[:2]],
                         [("entity class", "no", "yes"), ("predicate", "yes", "same component class")])
        self.assertEqual(component_class_mapping.value_problems(rows), [
            "line 4 (HOSTS): swap_subject_and_object 'y'", "line 4 (HOSTS): checked 'checked'",
            "line 5 (Probe): swap_subject_and_object 'yes'",
            "line 6 (Rover): kind 'sort'", "line 6 (Rover): swap_subject_and_object ''", "line 6 (Rover): checked ''"])


class AskCached(unittest.TestCase):
    """common/common_helpers/cache.ask_cached: one model call per new prompt, the answer kept; the same prompt again
    is answered from the cache (and counted), any change to the filled prompt asks again."""

    def test_asks_once_per_prompt(self):
        from types import SimpleNamespace
        from unittest import mock
        from common import cache as cache_module, llm
        tmp = Path(tempfile.mkdtemp())
        try:
            started, answers = [], iter([{"n": 1}, {"n": 2}])
            paid = SimpleNamespace(made=0, start=started.append)
            paid.made_call = lambda: setattr(paid, "made", paid.made + 1)
            paid.outcome = lambda where, prompt, error=None, watched=True: None
            calls = SimpleNamespace(paid=paid)
            c = cache_module.Cache(tmp, "stage")
            with mock.patch.object(llm, "call_llm_json", lambda prompt, read_timeout=180, check=None: next(answers)):
                self.assertEqual(cache_module.ask_cached(c, calls, "prompt A", "plan"), {"n": 1})
                self.assertEqual(cache_module.ask_cached(c, calls, "prompt A", "plan"), {"n": 1})   # from the cache
                self.assertEqual(cache_module.ask_cached(c, calls, "prompt B", "plan"), {"n": 2})   # changed: asked
            self.assertEqual((paid.made, c.reused, started), (2, 1, ["plan", "plan"]))
            self.assertEqual(cache_module.Cache(tmp, "stage").answers, c.answers)                   # kept on disk
        finally:
            shutil.rmtree(tmp)

    def test_unreadable_file_kept_aside(self):
        """A cache file that isn't JSON is treated as empty, but first copied aside (a second one gets its own
        name), and the run warns, naming both; a readable one raises no warning."""
        from common import cache as cache_module, llm
        tmp = Path(tempfile.mkdtemp())
        saved = list(llm.RUN_WARNINGS)
        try:
            (tmp / "stage.json").write_text('{"cut sho', encoding="utf-8")
            self.assertEqual(cache_module.Cache(tmp, "stage").answers, {})
            self.assertEqual((tmp / "stage.unreadable.json").read_text(encoding="utf-8"), '{"cut sho')
            note = llm.RUN_WARNINGS[-1]
            self.assertIn("stage.json couldn't be read", note)
            self.assertIn("stage.unreadable.json", note)
            cache_module.Cache(tmp, "stage")
            self.assertTrue((tmp / "stage.unreadable-2.json").exists())
            n = len(llm.RUN_WARNINGS)
            (tmp / "stage.json").write_text('{"k": 1}', encoding="utf-8")
            self.assertEqual(cache_module.Cache(tmp, "stage").answers, {"k": 1})
            self.assertEqual(len(llm.RUN_WARNINGS), n)
        finally:
            llm.RUN_WARNINGS[:] = saved
            shutil.rmtree(tmp)

    def shape_run(self, tmp, texts):
        """ask_cached with the shape check needs(labels=dict), the model's answers (text, as the service sends
        them) in turn: (cache, calls, the prompts sent, the failed calls given to outcome)."""
        from types import SimpleNamespace
        from common import cache as cache_module
        sent, failed, answers = [], [], iter(texts)
        paid = SimpleNamespace(made=0, start=lambda plan: None)
        paid.made_call = lambda: setattr(paid, "made", paid.made + 1)
        paid.outcome = lambda where, prompt, error=None, watched=True: error and failed.append((where, error))
        return cache_module.Cache(tmp, "label"), SimpleNamespace(paid=paid), sent, failed, \
            lambda prompt, **kw: sent.append(prompt) or next(answers)

    def test_shape(self):
        """A wrong-shaped answer is asked once more and never saved; twice wrong, it fails with what was wrong; a
        saved wrong-shaped answer is ignored and asked again (the run's warnings name the file); a right-shaped
        saved answer is reused without a call. Near misses: "labels" a list, "labels" missing, extra fields."""
        from unittest import mock
        from common import cache as cache_module, llm, step
        check = cache_module.needs(labels=dict)
        self.assertIsNone(check({"labels": {}, "extra": 1}))                                      # extra fields are fine
        self.assertEqual(check({"labels": ["a"]}), '"labels" should be a JSON object, but is a JSON list')
        self.assertEqual(check({"label": {}}), '"labels" should be a JSON object, but is missing')
        self.assertEqual(check([]), "the answer should be a JSON object, but is a JSON list")    # a hand-edited file
        tmp = Path(tempfile.mkdtemp())
        saved_warnings = list(llm.RUN_WARNINGS)
        llm.RUN_WARNINGS.clear()
        try:
            # 1. wrong, then right: asked twice, the right one saved
            c, calls, sent, failed, model = self.shape_run(tmp, ['{"labels": ["Instrument"]}',
                                                                 '{"labels": {"MODIS": "Instrument"}}'])
            with mock.patch.object(llm, "call_llm", model):
                self.assertEqual(cache_module.ask_cached(c, calls, "prompt A", "plan", check=check),
                                 {"labels": {"MODIS": "Instrument"}})
            self.assertEqual(len(sent), 2)
            self.assertIn('not in the shape asked for: "labels" should be a JSON object, but is a JSON list', sent[1])
            self.assertEqual(list(cache_module.Cache(tmp, "label").answers.values()), [{"labels": {"MODIS": "Instrument"}}])

            # 2. wrong twice: not saved, BadReply saying what was wrong, given to outcome (the failed-call record)
            c, calls, sent, failed, model = self.shape_run(tmp, ['{"merges": []}', '{"labels": "x"}'])
            with mock.patch.object(llm, "call_llm", model), self.assertRaises(llm.BadReply) as e:
                cache_module.ask_cached(c, calls, "prompt B", "plan", check=check)
            self.assertIn("isn't a JSON object of the shape asked for, 2 times", str(e.exception))
            self.assertIn('"labels" should be a JSON object, but is a JSON string', str(e.exception))
            self.assertEqual([(w, type(x)) for w, x in failed], [({"stage": "label"}, llm.BadReply)])
            self.assertEqual(len(cache_module.Cache(tmp, "label").answers), 1)                    # only prompt A's

            # 3. a wrong-shaped answer saved before (an older version of the code): ignored, asked again, replaced
            k = cache_module.key("prompt C")
            c = cache_module.Cache(tmp, "label")
            c.put(k, {"labels": ["Instrument"]})
            c, calls, sent, failed, model = self.shape_run(tmp, ['{"labels": {"AIRS": "Instrument"}}'])
            with mock.patch.object(llm, "call_llm", model):
                self.assertEqual(cache_module.ask_cached(c, calls, "prompt C", "plan", check=check),
                                 {"labels": {"AIRS": "Instrument"}})
            self.assertEqual((len(sent), c.reused, calls.paid.made), (1, 0, 1))
            self.assertEqual(cache_module.Cache(tmp, "label").answers[k], {"labels": {"AIRS": "Instrument"}})
            self.assertEqual(len(llm.RUN_WARNINGS), 1)
            self.assertIn("1 answer(s) saved in", llm.RUN_WARNINGS[0])
            self.assertIn(f"{step.repo_path(c.path)} were JSON of the wrong shape", llm.RUN_WARNINGS[0])
            self.assertIn('"labels" should be a JSON object, but is a JSON list', llm.RUN_WARNINGS[0])

            # 4. right-shaped answers saved: reused, no call, no warning added
            c, calls, sent, failed, model = self.shape_run(tmp, [])
            with mock.patch.object(llm, "call_llm", model):
                for prompt in ("prompt A", "prompt C"):
                    cache_module.ask_cached(c, calls, prompt, "plan", check=check)
            self.assertEqual((sent, c.reused, len(llm.RUN_WARNINGS)), ([], 2, 1))
        finally:
            llm.RUN_WARNINGS[:] = saved_warnings
            shutil.rmtree(tmp)


class Reviews(unittest.TestCase):

    def test_reviews(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            path = tmp / "r.csv"
            rows = [{"record_id": "a", "ground_truth_subject": "The MODIS", "ground_truth_predicate": "ABOARD",
                     "ground_truth_object": "Aqua", "translated_subject": "MODIS Terra", "translated_predicate": "ABOARD",
                     "translated_object": "Aqua", "verdict": "same fact"}]
            write_csv(path, partial_reviews.COLUMNS, rows + [{**rows[0], "verdict": " not the same fact "}])
            key = partial_reviews.pair_key("a", {"subject": "modis", "predicate": "aboard", "object": "aqua"},
                                           {"subject": "MODIS terra", "predicate": "ABOARD", "object": "Aqua."})
            # two different verdicts for one pair: a conflict, neither counts, both rows named (common.latest)
            self.assertEqual(partial_reviews.read_reviews(path), {})
            problems = partial_reviews.review_problems(path)
            self.assertEqual(len(problems), 1)
            self.assertIn("conflict: line 2 (a) ('same fact') and line 3 (a) ('not the same fact')", problems[0])
            self.assertIn("neither counts", problems[0])
            # the same verdict twice, in another spelling: one verdict, no problem
            write_csv(path, partial_reviews.COLUMNS, rows + [{**rows[0], "verdict": " Same  Fact "}])
            self.assertEqual(partial_reviews.read_reviews(path), {key: partial_reviews.SAME})
            self.assertEqual(partial_reviews.review_problems(path), [])
            # a verdict that isn't one is ignored and listed, and doesn't make a conflict with the good row
            write_csv(path, partial_reviews.COLUMNS, rows + [{**rows[0], "verdict": "maybe"}])
            self.assertEqual(partial_reviews.read_reviews(path), {key: partial_reviews.SAME})
            self.assertEqual(partial_reviews.review_problems(path), ["line 3 (a): 'maybe'"])
            self.assertEqual(partial_reviews.read_reviews(tmp / "missing.csv"), {})
            self.assertEqual(len(read_csv(path)), 2)
        finally:
            shutil.rmtree(tmp)


class LatestByKey(unittest.TestCase):
    """common.latest.latest_by_key: the one rule for several rows about one thing. With timestamps the latest wins,
    a withdrawal (an empty value) too; without, or at one moment, the rows must agree, else a conflict is reported
    and nothing is chosen."""

    def rows(self, *specs):
        return [{"k": k, "v": v, "t": t, "n": i + 1} for i, (k, v, t) in enumerate(specs)]

    def run_it(self, rows, when=True):
        from common.latest import latest_by_key
        return latest_by_key(rows, lambda r: r["k"], lambda r: r["v"], when=(lambda r: r["t"]) if when else None,
                             where=lambda r: f"row {r['n']}")

    def test_latest_wins_and_withdrawal(self):
        chosen, problems = self.run_it(self.rows(("a", "first", "2026-10-24T10:00:00Z"),
                                                 ("a", "second", "2026-10-24T11:00:00Z"),
                                                 ("b", "kept", "2026-10-24T10:00:00Z"),
                                                 ("b", "", "2026-10-24T12:00:00Z"),          # withdrawn later
                                                 ("c", "", "2026-10-24T09:00:00Z"),
                                                 ("c", "back", "2026-10-24T10:00:00Z")))    # withdrawn, then said again
        self.assertEqual({k: r["v"] for k, r in chosen.items()}, {"a": "second", "c": "back"})
        self.assertEqual(problems, [])

    def test_timestamps_read_as_moments(self):
        """Two spellings of one moment are equal (so no spelling sorts above another); an offset counts; a timestamp
        that can't be read is a problem and its row is skipped."""
        chosen, problems = self.run_it(self.rows(("a", "utc", "2026-10-24T14:00:00Z"),
                                                 ("a", "local", "2026-10-24 11:00:00-04:00"),   # 15:00 UTC: later
                                                 ("b", "x", "yesterday"),
                                                 ("b", "y", "2026-10-24T10:00:00+00:00")))
        self.assertEqual({k: r["v"] for k, r in chosen.items()}, {"a": "local", "b": "y"})
        self.assertEqual(len(problems), 1)
        self.assertIn("row 3: its timestamp 'yesterday' can't be read", problems[0])
        same = self.run_it(self.rows(("a", "one", "2026-10-24T14:00:00Z"), ("a", "one", "2026-10-24 14:00:00+00:00")))
        self.assertEqual(({k: r["v"] for k, r in same[0].items()}, same[1]), ({"a": "one"}, []))

    def test_conflict_reported(self):
        chosen, problems = self.run_it(self.rows(("a", "yes", "2026-10-24T10:00:00Z"), ("a", "no", "2026-10-24T10:00:00Z")))
        self.assertEqual(chosen, {})
        self.assertIn("conflict: row 1 ('yes') and row 2 ('no') are about the same thing with the same timestamp", problems[0])
        chosen, problems = self.run_it(self.rows(("a", "yes", None), ("a", "no", None), ("b", "k", None)), when=False)
        self.assertEqual(list(chosen), ["b"])
        self.assertIn("conflict: row 1 ('yes') and row 2 ('no') are about the same thing, and differ", problems[0])
        # the same value twice, spelled otherwise, is no conflict; an earlier different value loses to a later one
        chosen, problems = self.run_it(self.rows(("a", "Same  fact", None), ("a", "same fact", None)), when=False)
        self.assertEqual((list(chosen), problems), (["a"], []))
        chosen, problems = self.run_it(self.rows(("a", "yes", "2026-10-24T10:00:00Z"), ("a", "no", "2026-10-24T10:00:01Z")))
        self.assertEqual(({k: r["v"] for k, r in chosen.items()}, problems), ({"a": "no"}, []))


class SameModel(unittest.TestCase):
    """Who drafted the ground truth (column drafted_by) against extraction's model: llm.maker and 060's note."""

    def test_maker(self):
        from common.llm import maker
        self.assertEqual(maker("google-claude-sonnet-5"), "Anthropic")      # the host first, the family decides
        self.assertEqual(maker("claude-opus-4"), "Anthropic")
        self.assertEqual(maker("gpt-4o"), "OpenAI")
        self.assertEqual(maker("o3-mini"), "OpenAI")
        self.assertEqual(maker("google-gemini-2.5-pro"), "Google")
        self.assertEqual(maker("llama-3.1-70b"), "Meta")
        self.assertIsNone(maker("some-new-model"))
        self.assertIsNone(maker(""))

    def test_guide_lists_every_maker(self):
        """060's guide lists the makers and their words exactly as llm.MAKERS has them."""
        from common.llm import MAKERS
        guide = (ROOT / "060_extract" / "060_extract.md").read_text(encoding="utf-8")
        listed = guide.split("`MAKERS`): ", 1)[1].split("; a model whose name", 1)[0]
        import re
        found = tuple((m, tuple(re.findall(r"`([^`]+)`", words))) for m, words in re.findall(r"(\w+) \(([^)]*)\)", listed))
        self.assertEqual(found, MAKERS)

    def test_drafted_by_read(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            write_csv(tmp / "batch_000.csv", ground_truth.COLUMNS, [dict(zip(ground_truth.COLUMNS, row("a", "MODIS", "I", "ABOARD", "Aqua", "S", "x")))])
            write_csv(tmp / "batch_001.csv", ground_truth.FILE_COLUMNS,
                      [{**dict(zip(ground_truth.COLUMNS, row("b", "AIRS", "I", "ABOARD", "Aqua", "S", "x"))), "drafted_by": "gpt-4o"}])
            gt = ground_truth.read_ground_truth(tmp)
            self.assertEqual(gt.problems, [])                                  # the column is optional
            self.assertEqual({r["id"]: r["drafted_by"] for r in gt.select(ground_truth.ANNOTATED).rows},
                             {"a": "", "b": "gpt-4o"})
        finally:
            shutil.rmtree(tmp)

    def test_note(self):
        from support import use_step
        use_step("060_extract")
        from records import same_model_notes                                   # 060_extract_helpers/records.py
        rows = [{"id": "a", "drafted_by": "google-claude-sonnet-5"}, {"id": "a", "drafted_by": ""},
                {"id": "b", "drafted_by": "claude-opus-4"}, {"id": "c", "drafted_by": "gpt-4o"}, {"id": "d", "drafted_by": ""}]
        gt = ground_truth.Selection(ground_truth.ANNOTATED, tuple(rows), ("a", "b", "c", "d"))
        same = same_model_notes(gt, {"a", "b", "c", "d"}, "google-claude-sonnet-5")
        self.assertEqual(len(same), 2)                                         # a: same model; b: same maker; c: other maker
        self.assertIn("drafted (step 050) by claude-opus-4, a model from the same maker (Anthropic)", same[0])
        self.assertIn("drafted (step 050) by google-claude-sonnet-5, the same model as this run's", same[1])
        self.assertEqual(same_model_notes(gt, {"c", "d"}, "google-claude-sonnet-5"), [])   # other maker; written by a person
        self.assertEqual(same_model_notes(gt, {"a"}, "gpt-4o"), [])
        self.assertEqual(len(same_model_notes(gt, {"b"}, "some-new-model")), 0)            # unknown maker: only the same name


class ExtractWithoutGroundTruth(unittest.TestCase):
    """060's choice of records when the ground truth has no files yet (060_extract_helpers/records.py, pick_records):
    extract_from all and ids don't need it; extract_from ground_truth stops, saying what to do."""

    def setUp(self):
        from support import use_step
        use_step("060_extract")
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        (self.tmp / "records.jsonl").write_text(
            "\n".join(json.dumps({"id": i, "title": f"title {i}", "notes": ""}) for i in ("a", "b")), encoding="utf-8")
        (self.tmp / "splits.json").write_text(json.dumps({"ground_truth_candidates": {"records": [
            {"id": "a", "position": 0, "part": "tuning"}]}}), encoding="utf-8")
        self.inputs = {"records": self.tmp / "records.jsonl", "splits": self.tmp / "splits.json",
                       "ground_truth": self.tmp / "ground_truth" / "batch_*.csv"}     # no such folder

    def pick(self, extract_from, ids=""):
        from records import pick_records                                       # 060_extract_helpers/records.py
        return pick_records(self.inputs, {"extract_from": extract_from, "ids": ids, "max_chars": 8000,
                                          "workers": 1, "model": "m"})

    def test_all_and_ids(self):
        chosen = self.pick("all")
        self.assertEqual([i["id"] for i in chosen.items], ["a", "b"])
        self.assertEqual(chosen.ground_truth, set())
        self.assertEqual([i["id"] for i in self.pick("ground_truth", ids="b").items], ["b"])

    def test_ground_truth_stops(self):
        from common.stop import Stop
        with self.assertRaises(Stop) as stop:
            self.pick("ground_truth")
        self.assertIn("No ground truth files at", str(stop.exception))
        self.assertIn("--extract_from all", str(stop.exception))


class WorkedExamples(unittest.TestCase):
    """The two invented worked examples 050 and 060 show the model (common/common_prompts/extraction_examples.txt;
    prompt audit F7, 2026-10-30) pass the pipeline's own checks on their answers: every row is a well-formed
    classed triple, every source text is in its record's text (as one passage, or passages joined by " … "), every
    entity class, predicate and pattern is in the example schema shown with them, no fact is given twice, and the
    record's dataset is written as its title. They share no 5-word run with any harvested record either (the ground
    truth is checked for every prompt by tests/test_docs.py, PromptsQuoteNoGroundTruth)."""

    def examples(self) -> tuple:
        text = extraction.EXAMPLES.template
        schema_block = text.split("EXAMPLE SCHEMA", 1)[1].split("----- BEGIN EXAMPLE RECORD", 1)[0]
        found = []
        for n in ("1", "2"):
            record = text.split(f"----- BEGIN EXAMPLE RECORD {n} -----\n", 1)[1].split(
                f"\n----- END EXAMPLE RECORD {n} -----", 1)[0]
            answer = text.split(f"EXAMPLE ANSWER {n}\n", 1)[1].split("\n]}", 1)[0] + "\n]}"
            found.append((n, record, json.loads(answer)))
        return schema_block, found

    def test_answers_pass_the_checks(self):
        from common import schema_io
        from common.validate import SchemaEntries
        schema_block, found = self.examples()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "example_schema.txt"
            path.write_text(schema_block, encoding="utf-8")
            schema = schema_io.read_schema(path)
        self.assertEqual([u for u in schema["unread"] if "Each entry reads" not in u], [])   # only the header's prose
        entries = SchemaEntries(schema)
        self.assertEqual(len(found), 2)
        for n, record, answer in found:
            with self.subTest(example=n):
                title = record.split("\n", 1)[0].removeprefix("title: ")
                rows, removed = extraction.build_rows("example", title, record, [answer], entries)
                self.assertEqual(removed, [], "a malformed or repeated triple")
                self.assertEqual(rows[0]["errors"] + rows[0]["flags"], [], "the describes triple")
                for row in rows[1:]:
                    with self.subTest(triple=(row["subject"], row["predicate"], row["object"])):
                        self.assertEqual(row["errors"], [])
                        schema_flags = [f for f in row["flags"] if "schema" in f or "pinned" in f]
                        self.assertEqual(schema_flags, [])
                        if row["subject_class"] == "Dataset":
                            self.assertEqual(row["subject"], title)       # rule 23: the record's dataset is its title

    def test_no_run_of_a_real_record(self):
        records = ROOT / "outputs" / "intermediate_results" / "020_clean" / "records.jsonl"
        if not records.exists():
            self.skipTest("no harvested records on this computer")
        import re
        words = lambda s: re.sub(r"\W+", " ", s.lower()).split()
        runs = lambda w: {" ".join(w[i:i + 5]) for i in range(len(w) - 4)}
        example_runs = set()
        for _, record, _ in self.examples()[1]:
            example_runs |= runs(words(record))
        hits = set()
        with open(records, encoding="utf-8") as fh:
            for line in fh:
                r = json.loads(line)
                hits |= runs(words(f"{r.get('title') or ''} {r.get('notes') or ''}")) & example_runs
        self.assertFalse(hits, f"the worked examples share these 5-word runs with harvested records: {sorted(hits)[:10]}")


class TwoPasses(unittest.TestCase):
    """050's and 060's prompts share their instructions from common/common_prompts: the completeness instruction and
    TRACE-KG's order of work (first find every thing the record names, then state the facts about each;
    extraction_passes.txt, $passes), the worked examples (extraction_examples.txt, $examples) and the closing line after
    the record (extraction_closing.txt, $closing); they differ only in which facts they ask for (050 every fact, 060
    only the ones its schema can express) and in how they may name (050 coins, 060 uses its schema only). The layout
    (prompt audit F5, 2026-10-30): schema, rules, examples, task, reply format, record, closing line. Everything
    before the record is the part sent for prompt caching. It replaced 060's setting list_things_first (2026-10-30),
    which no longer exists."""

    RECORD = {"id": "r1", "title": "Kestrel Lake Ice L2", "notes": "Made by the Tern algorithm."}
    SCHEMA = "ENTITY CLASSES\nInstrument  a device"

    def setUp(self):
        from support import use_step
        use_step("060_extract")
        import extract                                                         # 060_extract_helpers/extract.py
        self.extract = extract
        use_step("050_annotate")
        import draft                                                           # 050_annotate_helpers/draft.py
        self.draft = draft

    def prompt(self, step="060") -> str:
        if step == "060":
            return extraction.prompt(self.extract.PROMPT, self.SCHEMA, self.RECORD, "title: Kestrel Lake Ice L2",
                                     **extraction.task_parts(extraction.SCOPE_SCHEMA))
        return extraction.prompt(self.draft.PROMPT, self.SCHEMA, self.RECORD, "title: Kestrel Lake Ice L2",
                                 **extraction.task_parts(extraction.SCOPE_ALL))

    def test_always_two_passes(self):
        for step in ("050", "060"):
            with self.subTest(step=step):
                template = (self.extract if step == "060" else self.draft).PROMPT.template
                for name in ("$schema", "$rules", "$reply", "$text", "$passes", "$examples", "$closing"):
                    template = template.replace(name, "")
                self.assertNotIn("$", template)                                # no other placeholder left
                prompt = self.prompt(step)
                first = prompt.index("Work in two passes")
                self.assertIn("Completeness comes first.", prompt)
                self.assertLess(prompt.index("Completeness comes first."), first)
                self.assertIn("1. Find every thing the record names", prompt)
                self.assertIn("2. Take the things one at a time.", prompt)
                self.assertIn("this list in your answer.", prompt)
                self.assertLess(first, prompt.index(extraction.BEGIN_LINE))        # in the part sent for prompt caching
                self.assertIn(extraction.reply(True), prompt)                      # the shared reply format, unchanged
        self.assertLess(self.prompt("060").index("leave describes_class empty."),
                        self.prompt("060").index("Work in two passes"))

    def test_layout(self):
        """Schema, rules, examples, task, reply format, record, closing line: long reference first, the task after it,
        and the task restated after the record (Anthropic: queries at the end; Google: instructions at the end)."""
        for step in ("050", "060"):
            with self.subTest(step=step):
                p = self.prompt(step)
                marks = ["SCHEMA\n", "RULES\n", "WORKED EXAMPLES", "TASK\n", "Work in two passes", "REPLY FORMAT",
                         extraction.BEGIN_LINE, extraction.END_LINE, "Now state every fact"]
                where = [p.index(m) for m in marks]
                self.assertEqual(where, sorted(where), marks)
                self.assertEqual(p.count(extraction.BEGIN_LINE), 1)              # the cache split is unambiguous
                self.assertTrue(p.rstrip().endswith("the reply format above."))

    def test_same_shared_text_different_scope(self):
        p050, p060 = self.prompt("050"), self.prompt("060")
        self.assertIn("every fact the record states (whether or not the schema can express it)", p050)
        self.assertIn("every fact the record states that the schema can express", p060)
        for shared in (extraction.PASSES, extraction.CLOSING):
            for part in shared.template.split("$scope"):
                self.assertIn(part.strip(), p050)
                self.assertIn(part.strip(), p060)
        self.assertIn(extraction.EXAMPLES.template.strip(), p050)
        self.assertIn(extraction.EXAMPLES.template.strip(), p060)

    def test_setting_is_gone(self):
        import contextlib
        import importlib.util
        import io
        from common.step import _parse_command_line
        spec = importlib.util.spec_from_file_location("run_060", ROOT / "060_extract" / "run.py")
        run = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(run)
        self.assertNotIn("list_things_first", run.SETTINGS)
        self.assertFalse((ROOT / "060_extract" / "060_extract_prompts" / "list_things_first.txt").exists())
        with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
            _parse_command_line("060_extract", run.INPUTS, run.SETTINGS, ["--list_things_first", "true"])


class Confirm(unittest.TestCase):
    """The question before paying (llm.confirm): Enter, y, or yes (any case, spaces ignored) go ahead; anything
    else, or a closed input stop (Ctrl+C interrupts), as docs/running_on_nasa_laptop.md, section 5, says."""

    def answer(self, typed):
        import builtins
        from unittest import mock
        from common.llm import confirm
        effect = typed if isinstance(typed, type) else None
        with mock.patch.object(builtins, "input", side_effect=effect, return_value=None if effect else typed):
            try:
                confirm("Go?")
                return "went ahead"
            except SystemExit as e:
                return str(e).strip()

    def test_go_ahead(self):
        for typed in ("", "  ", "y", "Y", "yes", " YES ", "Yes"):
            self.assertEqual(self.answer(typed), "went ahead", typed)

    def test_stop(self):
        for typed in ("n", "no", "ye", "yess", "ok", "1", EOFError):       # Ctrl+C: test_model_calls.py, CtrlC
            self.assertEqual(self.answer(typed), "Cancelled. Nothing was spent.", typed)


class InputsNotCommitted(unittest.TestCase):
    """An input kept in Git whose file differs from Git's copy, or isn't in Git yet, is noted in the report's Inputs
    (step._describe_inputs, step.UNCOMMITTED), so the Git commit isn't taken for its version."""

    def test_origin(self):
        import subprocess
        from unittest import mock
        from common import step
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            git = lambda *a: subprocess.run(["git", *a], cwd=repo, capture_output=True, check=True)
            git("init", "-q")
            f = repo / "guidelines.md"
            f.write_text("rule 1", encoding="utf-8")
            new = repo / "new.md"
            new.write_text("not added", encoding="utf-8")
            git("add", "guidelines.md")
            git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "x")
            origin = lambda path: step._describe_inputs({"x": path})[0][0]["origin"]
            with mock.patch.object(step, "ROOT", repo):
                self.assertEqual(origin(f), "kept in Git, made by a person")
                f.write_text("rule 1, changed", encoding="utf-8")
                self.assertEqual(origin(f), "kept in Git, made by a person" + step.UNCOMMITTED)
                self.assertEqual(origin(new), "kept in Git, made by a person" + step.UNCOMMITTED)
            with tempfile.TemporaryDirectory() as other:   # outside the repository: Git can't say, so no note
                out = Path(other) / "a.md"
                out.write_text("x", encoding="utf-8")
                with mock.patch.object(step, "ROOT", repo):
                    self.assertEqual(origin(out), "kept in Git, made by a person")


class TrueFalseSetting(unittest.TestCase):
    """A true/false setting's values (step._parse_bool), as docs/running_on_nasa_laptop.md, *Settings several steps
    share*, lists them."""

    def test_values(self):
        import argparse
        from common.step import _parse_bool
        for text in ("true", "TRUE", " Yes ", "on", "1"):
            self.assertIs(_parse_bool(text), True, text)
        for text in ("false", "No", "OFF", "0"):
            self.assertIs(_parse_bool(text), False, text)
        for text in ("tru", "y", "n", "2", ""):
            with self.assertRaises(argparse.ArgumentTypeError, msg=text):
                _parse_bool(text)


class IdsSetting(unittest.TestCase):
    """The ids setting (records_io.read_ids), as docs/running_on_nasa_laptop.md, *Settings several steps share*,
    says: ids separated by commas or spaces, or a file's path; an id listed twice counts once."""

    def test_listed(self):
        from common.records_io import read_ids
        self.assertEqual(read_ids(" a1, b2  c3,,a1 "), ["a1", "b2", "c3"])
        self.assertEqual(read_ids(""), [])

    def test_file(self):
        from common.records_io import read_ids
        from common.stop import Stop
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp)
        path = tmp / "ids.csv"
        path.write_text("ID,title\n# a comment\n\n\"a1\",Aqua\nb2\na1,again\n", encoding="utf-8")
        self.assertEqual(read_ids(str(path)), ["a1", "b2"])
        with self.assertRaises(Stop) as stop:
            read_ids(str(tmp / "missing.txt"))
        self.assertIn("names the file", str(stop.exception))
        with self.assertRaises(Stop):
            read_ids("folder/list")                                      # a "/" makes it a path, whatever its ending


class AskSplit(unittest.TestCase):

    def test_refused_item_isolated(self):
        """A refused batch is asked in halves down to the refused item; everything else is answered."""
        from common import llm
        from common.cache import ask_split
        asked = []

        def ask(batch):
            asked.append(list(batch))
            if "bad" in batch:
                raise llm.ApiError("the model gave no usable answer (finish_reason 'content_filter')")
            return {x: x.upper() for x in batch}
        refused = []
        items = [f"w{i}" for i in range(7)] + ["bad"]
        answers = {}
        for reply in ask_split(ask, items, refused):
            answers.update(reply)
        self.assertEqual(answers, {f"w{i}": f"W{i}" for i in range(7)})
        self.assertEqual([r for r, _ in refused], ["bad"])
        self.assertIn("content_filter", refused[0][1])
        self.assertLessEqual(len(asked), 2 * 3 + 1)                             # halves down to one item: log2(8) levels
        self.assertEqual(ask_split(ask, ["a", "b"], []), [{"a": "A", "b": "B"}])  # nothing refused: one call


class TryModels(unittest.TestCase):

    def test_try(self):
        """py helpers/models.py --try: one test call per model, usable or refused with the reason, asked first."""
        import importlib.util
        import io
        from contextlib import redirect_stdout
        from unittest import mock
        from common import llm
        spec = importlib.util.spec_from_file_location("models_helper", support.ROOT / "helpers" / "models.py")
        models = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(models)
        asked = []

        def fake(prompt, attempts=4, read_timeout=180, model=None, service=None):
            asked.append(model)
            if model == "refuser":
                raise llm.ApiError("model_not_permitted (http_status 400): Sorry, this model is not authorized")
            return '{"ok": true}'
        out = io.StringIO()
        with mock.patch.object(llm, "call_llm", fake), mock.patch("builtins.input", lambda q: ""), redirect_stdout(out):
            tried = models.try_models(["good", "refuser", "unknown", "good"], ["good", "refuser"], "asksage")
        self.assertEqual(asked, ["good", "refuser", "unknown"])                 # each once, the prompt as a step's first call
        self.assertEqual([(n, ok) for n, ok, _ in tried], [("good", True), ("refuser", False), ("unknown", True)])
        self.assertIn("model_not_permitted", tried[1][2])
        self.assertIn("Not in Ask Sage's list", out.getvalue())
        with mock.patch.object(llm, "call_llm", fake), mock.patch("builtins.input", lambda q: "n"),                 redirect_stdout(io.StringIO()), self.assertRaises(SystemExit):
            models.try_models(["all"], ["good", "refuser"])                     # declined: nothing paid
        self.assertEqual(len(asked), 3)


class CheckEffort(unittest.TestCase):
    """py helpers/check_effort.py: step A's reading of an invalid effort value's reply, step B's answer parsing and
    decision rule, and both steps against fake replies, with the near misses."""

    @classmethod
    def setUpClass(cls):
        import importlib.util
        spec = importlib.util.spec_from_file_location("check_effort", support.ROOT / "helpers" / "check_effort.py")
        cls.ce = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.ce)

    def test_step_a_verdict(self):
        v = self.ce.step_a_verdict
        for status in (400, 422):
            got = v(status, "Invalid reasoning_effort", "reasoning_effort")
            self.assertTrue(got.startswith("refused"), got)
            self.assertIn("Invalid reasoning_effort", got)                      # the error text, quoted
            # a refusal that doesn't name the setting says nothing about it
            self.assertTrue(v(status, "model not found", "reasoning_effort").startswith("no verdict"))
        self.assertIn("dropped or ignored", v(200, "OK", "reasoning_effort"))
        # a 401, 403, 404 or 429 is about the key, the access, the model name or the rate limit: no verdict, and it
        # says what it is about
        for status, about in ((401, "the key"), (403, "your access"), (404, "the model name"), (429, "the rate limit")):
            got = v(status, "Invalid reasoning_effort", "reasoning_effort")     # even when the text names the setting
            self.assertTrue(got.startswith("no verdict"), got)
            self.assertIn(about, got)
        for status in (399, 499, 500, 503, 302):                                # near misses: no verdict
            self.assertTrue(v(status, "x", "reasoning_effort").startswith("no verdict"))
            self.assertNotIn("dropped", v(status, "x"))

    def test_answer_number(self):
        n = self.ce.answer_number
        self.assertEqual(n("First 360, then 240.\nSo the answer is:\n168"), 168)
        self.assertEqual(n("168\n\n"), 168)
        self.assertEqual(n("Answer: 1,168"), 1168)
        self.assertEqual(n("I count 168.\nThat is all."), 168)                 # the last line with a number
        self.assertIsNone(n("no number here"))
        self.assertIsNone(n(None))

    def test_step_b_rule(self):
        rule = self.ce.step_b_verdict
        self.assertEqual(rule([100, 120, 110], [300, 400, 350])[0], "passed on")      # every high above every low
        self.assertEqual(rule([100, 120, 110], [121, 125, 130])[0], "passed on")      # just above the highest low
        self.assertEqual(rule([100, 120, 110], [120, 125, 130])[0], "not shown")      # a tie with the highest low
        self.assertEqual(rule([100, 100, 100], [90, 200, 160])[0], "passed on")       # overlap, mean 150 = 1.5 x 100
        self.assertEqual(rule([100, 100, 100], [90, 200, 159])[0], "not shown")       # overlap, mean 149.7 < 150
        self.assertEqual(rule([40, 39, 40], [40, 40, 40])[0], "not shown")            # 2026-10-31's numbers
        self.assertEqual(rule([100, None, 100], [500, 500, 500])[0], "not shown")     # a call failed
        self.assertEqual(rule([100, 100], [500, 500, 500])[0], "not shown")           # too few calls
        self.assertIn("a call failed", rule([100, 100, 100], [500, None, 500])[1])

    def test_puzzle_answer(self):
        """The expected answer, by listing every arrangement."""
        from itertools import permutations
        count = sum(1 for p in permutations("ABCDEF") if p.index("A") < p.index("B")
                    and abs(p.index("C") - p.index("D")) != 1 and p[0] != "E" and p[-1] != "E")
        self.assertEqual(count, self.ce.PUZZLE_ANSWER)

    def run_steps(self, replies, only=None, answer=""):
        """main() against fake replies (one per request, in order): what it printed, and the payloads sent."""
        import io
        from contextlib import redirect_stdout
        from unittest import mock
        from common import llm
        sent, replies = [], list(replies)

        class Reply:
            def __init__(self, status, body):
                self.status_code, self._body, self.text = status, body, json.dumps(body)

            def json(self):
                return self._body

        def post(url, headers=None, json=None, timeout=None):
            sent.append(json)
            return Reply(*replies.pop(0))
        out = io.StringIO()
        argv = ["check_effort.py"] + (["--only", only] if only else [])
        with mock.patch.object(llm, "_post", post), mock.patch.object(llm, "_litellm", lambda p: ("u", {})), \
                mock.patch("builtins.input", lambda q: answer), mock.patch.object(sys, "argv", argv), \
                redirect_stdout(out):
            self.ce.main()
        return out.getvalue(), sent

    @staticmethod
    def answered(text, completion):
        return 200, {"choices": [{"message": {"content": text}}],
                     "usage": {"completion_tokens": completion, "completion_tokens_details": {"reasoning_tokens": 0}}}

    def test_step_a_requests(self):
        out, sent = self.run_steps([(400, {"error": {"message": "Invalid reasoning_effort: not_a_level"}}),
                                    self.answered("OK", 2)], only="a")
        self.assertEqual(sent[0]["reasoning_effort"], "not_a_level")
        self.assertEqual(sent[1]["output_config"], {"effort": "not_a_level"})
        self.assertIn("refused (HTTP 400, naming reasoning_effort)", out)
        self.assertIn("Invalid reasoning_effort: not_a_level", out)
        self.assertIn("answered (HTTP 200), so the setting was dropped or ignored", out)
        self.assertNotIn("Step B", out)

    def test_step_a_other_refusals_give_no_verdict(self):
        """A 404 (the model name) or a 400 that doesn't name the setting says nothing about the setting."""
        out, _ = self.run_steps([(404, {"error": {"message": "model not found"}}),
                                 (400, {"error": {"message": "max_tokens too large"}})], only="a")
        self.assertIn("no verdict: HTTP 404 is about the model name", out)
        self.assertIn("no verdict: refused (HTTP 400) without naming output_config", out)
        self.assertNotIn("so the setting is read", out)

    def test_step_b_requests(self):
        replies = [self.answered("...\n168", 900)] * 3 + [self.answered("...\n168", 300)] * 3 \
            + [self.answered("...\n170", 2000)] * 3
        out, sent = self.run_steps(replies, only="b")
        self.assertEqual(len(sent), 9)
        self.assertEqual([s.get("reasoning_effort") for s in sent], [None] * 3 + ["low"] * 3 + ["high"] * 3)
        self.assertLess(out.index("Decision rule (fixed before the calls)"), out.index("call 1"))   # written first
        self.assertIn("completion tokens 300", out)
        self.assertIn("reasoning_effort high: mean completion tokens 2000", out)
        self.assertIn("answer 168 (correct)", out)
        self.assertIn("answer 170 (wrong, expected 168)", out)
        self.assertIn("Step B's verdict: passed on", out)

    def test_step_b_declined_pays_nothing(self):
        with self.assertRaises(SystemExit):
            self.run_steps([], only="b", answer="n")

    def test_answer_cache_control_sent_when_switched_on(self):
        """check_effort's requests carry LiteLLM's cache control with LITELLM_BYPASS_ANSWER_CACHE=1, and not without."""
        from unittest import mock
        from common import llm
        for switch, expected in (("1", llm.ANSWER_CACHE_CONTROL["cache"]), ("", None)):
            with mock.patch.dict("os.environ", {llm.ANSWER_CACHE_SWITCH: switch}), \
                    mock.patch.object(llm, "load_dotenv", lambda *a, **k: None):
                _, sent = self.run_steps([(400, {"error": {"message": "no"}})] * 2, only="a")
            self.assertEqual([s.get("cache") for s in sent], [expected] * 2)
            self.assertEqual(sent[0]["reasoning_effort"], "not_a_level")              # the setting checked, kept


class CheckAnswerCache(unittest.TestCase):
    """py helpers/check_answer_cache.py: the decision rule and the cache control's acceptance with fake replies
    (the cache header present or absent, identical or different answers, a refusal), the near misses, and the 4
    requests it sends."""

    @classmethod
    def setUpClass(cls):
        import importlib.util
        spec = importlib.util.spec_from_file_location("check_answer_cache",
                                                      support.ROOT / "helpers" / "check_answer_cache.py")
        cls.cc = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.cc)

    @staticmethod
    def call(text="The Moon is bright.", tokens=12, key=None, status=200):
        return {"status": status, "key": key, "text": text if status == 200 else "HTTP error text",
                "usage": {"completion_tokens": tokens} if status == 200 else {}, "cache_fields": {}}

    def test_cached(self):
        c, cc = self.call, self.cc
        a, b, d = c("The Moon is bright."), c("The Moon orbits Earth.", 14), c("The Moon has no air.", 11)
        # the second plain call carries the header
        self.assertEqual(cc.verdict([a, c(key="k1"), b, d])[0], cc.CACHE_VERDICT)
        # byte-identical with identical usage, the no-cache calls differing
        self.assertEqual(cc.verdict([a, c(), b, d])[0], cc.CACHE_VERDICT)
        # byte-identical, the no-cache calls identical too but carrying no header
        found, why = cc.verdict([a, c(), b, dict(b)])
        self.assertEqual(found, cc.CACHE_VERDICT)
        self.assertIn("carry no x-litellm-cache-key", why)
        # 2026-10-31's pattern: identical counts and words, no header seen anywhere, fresh no-cache answers
        self.assertEqual(cc.verdict([c(tokens=717), c(tokens=717), c("Other.", 717), c("Else.", 717)])[0],
                         cc.CACHE_VERDICT)

    def test_no_cache_seen(self):
        c, cc = self.call, self.cc
        found, why = cc.verdict([c("A."), c("B."), c("C."), c("D.")])
        self.assertEqual(found, cc.NO_CACHE_VERDICT)
        self.assertIn("the two plain answers differ", why)
        # different words with the same token count: still no cache
        self.assertEqual(cc.verdict([c("A.", 9), c("B.", 9), c("C."), c("D.")])[0], cc.NO_CACHE_VERDICT)

    def test_near_misses(self):
        c, cc = self.call, self.cc
        # same words, usage differs by one token, no header: neither verdict
        found, why = cc.verdict([c(tokens=12), c(tokens=13), c("C."), c("D.")])
        self.assertEqual(found, cc.NOT_SHOWN)
        self.assertIn("same words with different usage", why)
        # different answers, but a no-cache call carries the header: not "no cache seen"
        found, why = cc.verdict([c("A."), c("B."), c("C.", key="k"), c("D.")])
        self.assertEqual(found, cc.NOT_SHOWN)
        self.assertIn("no-cache call 1 carries", why)
        # different answers, the first plain call carries the header (stored), the second doesn't
        self.assertEqual(cc.verdict([c("A.", key="k"), c("B."), c("C."), c("D.")])[0], cc.NOT_SHOWN)
        # cached plain calls, and the no-cache calls cached as well: the control ignored
        found, why = cc.verdict([c(), c(key="k"), c("C.", key="k2"), c("C.", key="k2")])
        self.assertEqual(found, cc.NOT_SHOWN)
        self.assertIn("ignored the cache control", why)
        # a plain call failed
        found, why = cc.verdict([c(), c(status=500), c("C."), c("D.")])
        self.assertEqual(found, cc.NOT_SHOWN)
        self.assertIn("HTTP 500", why)
        # cached plain calls, the no-cache calls refused: nothing to compare
        found, why = cc.verdict([c(), c(), c(status=400), c(status=400)])
        self.assertEqual(found, cc.NOT_SHOWN)
        self.assertIn("wasn't answered", why)

    def test_accepted(self):
        c, cc = self.call, self.cc
        self.assertEqual(cc.accepted([c(), c(), c("C."), c("D.")])[0], True)
        taken, words = cc.accepted([c(), c(), c(status=400), c(status=400)])
        self.assertIs(taken, False)
        self.assertIn("refused (HTTP 400)", words)
        self.assertIn("HTTP error text", words)                                    # the error, quoted
        self.assertIs(cc.accepted([c(), c(), c("C."), c(status=422)])[0], False)    # one refusal is enough
        self.assertIsNone(cc.accepted([c(), c(), c("C."), c(status=503)])[0])       # 5xx: not a refusal
        self.assertEqual(cc.accepted([c(), c(status=400), c("C."), c("D.")])[0], True)   # a plain refusal: not it

    def test_advice(self):
        cc = self.cc
        self.assertIn("LITELLM_BYPASS_ANSWER_CACHE=1", cc.advice(cc.CACHE_VERDICT, True))
        self.assertIn("Leave LITELLM_BYPASS_ANSWER_CACHE unset", cc.advice(cc.CACHE_VERDICT, False))
        self.assertNotIn("=1", cc.advice(cc.CACHE_VERDICT, None))
        self.assertIn("Nothing to change", cc.advice(cc.NO_CACHE_VERDICT, True))
        self.assertIn("Run the check again", cc.advice(cc.NOT_SHOWN, True))

    def test_cache_fields(self):
        found = self.cc.cache_fields({"completion_tokens": 5, "prompt_tokens_details": {"cached_tokens": 0},
                                      "cache_read_input_tokens": 3},
                                     {"x-litellm-cache-key": "k", "content-type": "application/json"})
        self.assertEqual(found, {"usage prompt_tokens_details.cached_tokens": 0, "usage cache_read_input_tokens": 3,
                                 "header x-litellm-cache-key": "k"})

    def run_check(self, replies, answer=""):
        """main() against fake replies (status, body, headers), one per request: what it printed, and what it sent."""
        import io
        from contextlib import redirect_stdout
        from unittest import mock
        from common import llm
        sent, replies = [], list(replies)

        class Reply:
            def __init__(self, status, body, headers):
                self.status_code, self._body, self.text, self.headers = status, body, json.dumps(body), headers

            def json(self):
                return self._body

        def post(url, headers=None, json=None, timeout=None):
            sent.append(json)
            return Reply(*replies.pop(0))
        out = io.StringIO()
        with mock.patch.object(llm, "_post", post), mock.patch.object(llm, "_litellm", lambda p: ("u", {})), \
                mock.patch("builtins.input", lambda q: answer), \
                mock.patch.object(sys, "argv", ["check_answer_cache.py"]), redirect_stdout(out):
            self.cc.main()
        return out.getvalue(), sent

    @staticmethod
    def answered(text, tokens=12, headers=None):
        return 200, {"choices": [{"message": {"content": text}}], "usage": {"completion_tokens": tokens}}, headers or {}

    def test_requests(self):
        out, sent = self.run_check([self.answered("A."), self.answered("A.", headers={"X-LiteLLM-Cache-Key": "k1"}),
                                    self.answered("C."), self.answered("D.")])
        self.assertEqual(len(sent), 4)
        self.assertEqual([s.get("cache") for s in sent], [None, None] + [{"no-cache": True, "no-store": True}] * 2)
        self.assertEqual(len({s["messages"][0]["content"] for s in sent}), 1)          # one question, 4 times
        self.assertTrue(all("temperature" not in s for s in sent))                     # never to Claude
        self.assertTrue(all(s["max_tokens"] == sent[0]["max_tokens"] for s in sent))  # nothing else differs
        self.assertLess(out.index("Decision rule (fixed before the calls)"), out.index("plain call 1:"))
        self.assertIn("x-litellm-cache-key present (k1)", out)                          # header names in any case
        self.assertIn("Verdict: LiteLLM answers from its cache: the second plain call carries", out)
        self.assertIn("The cache control: accepted", out)
        self.assertIn("LITELLM_BYPASS_ANSWER_CACHE=1", out)

    def test_refused_control(self):
        out, _ = self.run_check([self.answered("A."), self.answered("B."),
                                 (400, {"error": {"message": "unknown parameter cache"}}, {}),
                                 (400, {"error": {"message": "unknown parameter cache"}}, {})])
        self.assertIn("Verdict: no answer cache seen", out)
        self.assertIn("refused (HTTP 400)", out)
        self.assertIn("unknown parameter cache", out)
        self.assertIn("Leave LITELLM_BYPASS_ANSWER_CACHE unset", out)

    def test_declined_pays_nothing(self):
        with self.assertRaises(SystemExit):
            self.run_check([], answer="n")


class LiteLLM(unittest.TestCase):
    """The second service: requests in the OpenAI shape, errors that will not fix themselves raised at once, the
    exact model that answered recorded, and Ask Sage's cache keys unchanged."""

    class Reply:
        def __init__(self, status, body):
            self.status_code, self._body = status, body
            self.text = json.dumps(body)

        def json(self):
            return self._body

    def setUp(self):
        from common import llm
        self.llm = llm
        self.saved = (llm.MODEL, llm.SERVICE)
        llm.SERVED.clear()

    def tearDown(self):
        self.llm.MODEL, self.llm.SERVICE = self.saved
        self.llm.SERVED.clear()

    def test_call(self):
        from unittest import mock
        llm, sent = self.llm, []

        def post(url, headers=None, json=None, timeout=None):
            sent.append((url, headers, json))
            return self.Reply(200, {"model": "claude-opus-5-5-20260101",
                                    "choices": [{"message": {"content": '{"ok": true}'}}]})
        with mock.patch.dict("os.environ", {"LITELLM_API_KEY": "sk-test", "LITELLM_BASE_URL": ""}), \
                mock.patch.object(llm.requests, "post", post), mock.patch.object(llm, "load_dotenv", lambda: None):
            self.assertEqual(llm.call_llm("hi", model="claude-opus-5.5", service="litellm"), '{"ok": true}')
        url, headers, body = sent[0]
        self.assertEqual(url, "https://proxy.fast.luna.nasa.gov/v1/chat/completions")
        self.assertEqual(headers, {"Authorization": "Bearer sk-test"})
        self.assertEqual(body, {"model": "claude-opus-5.5", "messages": [{"role": "user", "content": "hi"}],
                                "max_tokens": llm.MAX_ANSWER_TOKENS})            # no temperature: Claude takes none
        self.assertEqual(llm.SERVED, {"claude-opus-5-5-20260101"})

    def test_refusal_not_retried(self):
        from unittest import mock
        llm, calls = self.llm, []

        def post(url, headers=None, json=None, timeout=None):
            calls.append(1)
            return self.Reply(403, {"error": {"message": "key not allowed to access model"}})
        with mock.patch.dict("os.environ", {"LITELLM_API_KEY": "sk-test"}), \
                mock.patch.object(llm.requests, "post", post), mock.patch.object(llm, "load_dotenv", lambda: None):
            ok, why = llm.try_model("gpt-6-astra", "litellm")
        self.assertEqual((ok, len(calls)), (False, 1))
        self.assertIn("HTTP 403: key not allowed to access model", why)

    def test_cut_off_answer(self):
        """An answer cut off at the length limit says so, and isn't asked again (the same limit cuts it again)."""
        from unittest import mock
        llm, calls = self.llm, []

        def post(url, headers=None, json=None, timeout=None):
            calls.append(1)
            return self.Reply(200, {"choices": [{"message": {"content": '{"triples": [{"subject": "MO'},
                                                 "finish_reason": "length"}]})
        with mock.patch.dict("os.environ", {"LITELLM_API_KEY": "sk-test"}), \
                mock.patch.object(llm.requests, "post", post), mock.patch.object(llm, "load_dotenv", lambda: None):
            with self.assertRaisesRegex(llm.CutOff, "cut off at the longest length allowed"):
                llm.call_llm_json("extract", read_timeout=5)
        self.assertEqual(len(calls), 1)

    def _with(self, post):
        from unittest import mock
        llm = self.llm
        return [mock.patch.dict("os.environ", {"LITELLM_API_KEY": "sk-test"}),
                mock.patch.object(llm.requests, "post", post), mock.patch.object(llm, "load_dotenv", lambda: None),
                mock.patch.object(llm.time, "sleep", lambda s: self.slept.append(s))]

    def call(self, post, **kw):
        import contextlib
        self.slept = []
        with contextlib.ExitStack() as stack:
            for m in self._with(post):
                stack.enter_context(m)
            return self.llm.call_llm("x", model="m", service="litellm", **kw)

    def test_read_timeout_not_asked_again(self):
        llm, calls = self.llm, []

        def post(url, headers=None, json=None, timeout=None):
            calls.append(1)
            raise llm.requests.ReadTimeout("read timed out")
        with self.assertRaisesRegex(llm.ApiError, "no answer within"):
            self.call(post)
        self.assertEqual(len(calls), 1)

    def test_no_usable_answer(self):
        llm = self.llm
        for choice, words in (({"message": {"content": None}, "finish_reason": "content_filter"}, "content filter"),
                              ({"message": {"content": "  "}, "finish_reason": "stop"}, "no usable answer")):
            calls = []

            def post(url, headers=None, json=None, timeout=None, choice=choice):
                calls.append(1)
                return self.Reply(200, {"choices": [choice]})
            with self.assertRaisesRegex(llm.ApiError, words):
                self.call(post)
            self.assertEqual(len(calls), 1, words)                               # not asked again

    def test_rate_limit_waits_as_told_and_counts_requests(self):
        llm, replies = self.llm, []

        class Limited(self.Reply):
            headers = {"Retry-After": "30"}

        def post(url, headers=None, json=None, timeout=None):
            replies.append(1)
            if len(replies) < 3:
                return Limited(429, {"error": {"message": "rate limited"}})
            return self.Reply(200, {"choices": [{"message": {"content": '{"ok": true}'}, "finish_reason": "stop"}]})
        llm.REQUESTS["sent"] = 0
        self.assertEqual(self.call(post), '{"ok": true}')
        self.assertEqual(llm.REQUESTS["sent"], 3)                                 # every attempt counted
        self.assertTrue(all(30 <= s <= 32 for s in self.slept), self.slept)       # the service's wait, plus jitter

    def test_prompt_caching_messages(self):
        """For an Anthropic model, the prompt's identical start (before the record) goes as a cached system block; the
        words are the same; other makers' models, and prompts without the line, get one plain message."""
        llm = self.llm
        prompt = "RULES and SCHEMA\n----- BEGIN RECORD -----\nthe record\n----- END RECORD -----"
        m = llm._messages(prompt, "claude-opus-5.5", "----- BEGIN RECORD -----")
        self.assertEqual(m[0], {"role": "system", "content": [{"type": "text", "text": "RULES and SCHEMA\n",
                                                               "cache_control": {"type": "ephemeral"}}]})
        self.assertEqual(m[0]["content"][0]["text"] + m[1]["content"], prompt)
        for model, until in (("gemini-2.5-pro", "----- BEGIN RECORD -----"), ("claude-opus-5.5", None),
                             ("claude-opus-5.5", "not in the prompt")):
            self.assertEqual(llm._messages(prompt, model, until), [{"role": "user", "content": prompt}], model)

    def test_token_counts(self):
        llm = self.llm
        for k in llm.REQUESTS:
            llm.REQUESTS[k] = 0
        llm._count_tokens({"prompt_tokens": 2545, "completion_tokens": 9, "cache_creation_input_tokens": 2523,
                           "cache_read_input_tokens": 0})
        llm._count_tokens({"prompt_tokens": 2545, "completion_tokens": 9, "cache_creation_input_tokens": 0,
                           "cache_read_input_tokens": 2523})
        self.assertEqual({k: llm.REQUESTS[k] for k in ("input_tokens", "cache_read_tokens", "cache_write_tokens",
                                                       "output_tokens")},
                         {"input_tokens": 44, "cache_read_tokens": 2523, "cache_write_tokens": 2523, "output_tokens": 18})

    def test_cache_and_record(self):
        llm = self.llm
        llm.MODEL, llm.SERVICE = "google-claude-sonnet-5", "asksage"
        self.assertEqual(llm.cache_identity(), "google-claude-sonnet-5")       # as before: paid answers stay valid
        llm.MODEL, llm.SERVICE = "claude-sonnet-5", "litellm"
        self.assertEqual(llm.cache_identity(), "litellm:claude-sonnet-5")
        llm.SERVED.add("claude-sonnet-5-20260101")
        self.assertEqual(llm.describe(), {"service": "litellm", "model": "claude-sonnet-5",
                                          "served_as": ["claude-sonnet-5-20260101"],
                                          "temperature": "not sent (the model does not accept it, or its maker "
                                                         "advises against changing it)",
                                          "max_answer_tokens": llm.MAX_ANSWER_TOKENS,
                                          "thinking": f"not sent (the step's setting, {llm.THINKING}, isn't sent to "
                                                      "this model)",
                                          "thinking_sent": None, "effort": "not sent (model default)",
                                          "service_note": llm.SERVICE_NOTES["litellm"], "repeat": 1,
                                          "answer_cache": llm.answer_cache_note("litellm")})   # values: test_model_calls
        self.assertEqual(llm.model_label(), "`claude-sonnet-5` through LiteLLM (answered as `claude-sonnet-5-20260101`)")
        llm.MODEL = "claude-opus-5.5"                                            # its documented default effort
        self.assertEqual(llm.describe()["effort"], "not sent (model default, medium)")

    def test_temperature_sent(self):
        """Temperature 0 goes only to models that take it: not Claude (no sampling parameters on Opus 5.5), not
        Gemini 3 and later (Google advises the default); Gemini 2.5 and other makers' models get it."""
        llm = self.llm
        self.assertFalse(llm.temperature_sent("claude-opus-5.5", "litellm"))
        self.assertFalse(llm.temperature_sent("google-claude-sonnet-5", "asksage"))
        self.assertFalse(llm.temperature_sent("gemini-3-pro", "litellm"))
        self.assertTrue(llm.temperature_sent("gemini-2.5-pro", "litellm"))
        self.assertTrue(llm.temperature_sent("gpt-5", "litellm"))
        self.assertIsNone(llm.effort_note("gemini-2.5-pro"))

    def test_unknown_service(self):
        with self.assertRaisesRegex(ValueError, "asksage, litellm"):
            self.llm.paid_calls({"service": "openai", "model": "x", "confirm_paid_calls": False}, Path("060_extract"))



def _helper(step: str, name: str = "records"):
    """A step's helper module, loaded under a name of its own (the steps' helper folders share file names)."""
    import importlib.util
    folder = step.split("_", 1)[0]
    spec = importlib.util.spec_from_file_location(f"{name}_{folder}", ROOT / step / f"{step}_helpers" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[f"{name}_{folder}"] = module                                # its dataclasses need it registered
    spec.loader.exec_module(module)
    return module


class ReadThenWrite(unittest.TestCase):
    """common.files: a file read with its fingerprint is written back only if it still has it (write_if_unchanged,
    under locked), so a change made in between (another tab, a hand edit, a step) is never overwritten."""

    def test_variants(self):
        import tempfile
        from common import files
        tmp = Path(tempfile.mkdtemp())
        try:
            path = tmp / "a.csv"
            self.assertEqual(files.read_snapshot(path), (None, None))
            self.assertIsNone(files.fingerprint(path))
            fp = files.write_if_unchanged(path, "x\n", None)                    # no file yet: expected None
            self.assertEqual(fp, files.fingerprint(path))
            text, fp2 = files.read_snapshot(path)
            self.assertEqual((text, fp2), ("x\n", fp))
            fp3 = files.write_if_unchanged(path, "y\n", fp)                      # unchanged since read: written
            self.assertNotEqual(fp3, fp)
            with self.assertRaises(files.Changed) as c:
                files.write_if_unchanged(path, "z\n", fp)                        # a stale fingerprint: refused
            self.assertIn("a.csv changed on disk since it was loaded", str(c.exception))
            self.assertEqual(path.read_text(encoding="utf-8"), "y\n")           # nothing written
            path.write_bytes(b"\xef\xbb\xbfhand\r\nedit\r\n")                      # a hand edit (Excel: BOM, CRLF)
            with self.assertRaises(files.Changed):
                files.write_if_unchanged(path, "w\n", fp3)
            self.assertEqual(files.read_snapshot(path)[0], "hand\nedit\n")      # read evened: no BOM, \n
            with self.assertRaises(files.Changed):
                files.write_if_unchanged(path, "w\n", None)                      # "no file" expected, but one is there
            path.unlink()
            with self.assertRaises(files.Changed):
                files.write_if_unchanged(path, "w\n", fp3)                       # a file expected, but gone
            self.assertFalse((tmp / "a.csv.lock").exists())                     # the lock never stays
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_locked(self):
        import tempfile
        import threading
        from unittest import mock
        from common import files
        tmp = Path(tempfile.mkdtemp())
        try:
            path = tmp / "f.json"
            lock = tmp / "f.json.lock"
            with files.locked(path):
                self.assertTrue(lock.exists())
            self.assertFalse(lock.exists())
            lock.write_text("held by a crashed program")                           # a lock left behind
            with mock.patch.object(files, "LOCK_WAIT_SECONDS", 0.2), self.assertRaises(TimeoutError) as t:
                with files.locked(path):
                    pass
            self.assertIn("delete", str(t.exception))
            lock.unlink()
            order = []

            def hold():
                with files.locked(path):
                    order.append("a")
                    threading.Event().wait(0.3)
                    order.append("b")
            t1 = threading.Thread(target=hold)
            t1.start()
            threading.Event().wait(0.05)
            with files.locked(path):
                order.append("c")
            t1.join()
            self.assertEqual(order, ["a", "b", "c"])                                # one at a time within a process
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_sha256_of_several_files_sees_a_rename(self):
        import hashlib
        import tempfile
        from common import audit
        tmp = Path(tempfile.mkdtemp())
        try:
            a, b = tmp / "batch_004.csv", tmp / "batch_005.csv"
            a.write_bytes(b"one"), b.write_bytes(b"two")
            self.assertEqual(audit.sha256([a]), hashlib.sha256(b"one").hexdigest())    # one file: its plain sha256
            both = audit.sha256([a, b])
            c = tmp / "batch_007.csv"
            a.rename(c)
            self.assertNotEqual(audit.sha256([c, b]), both)                           # renamed: another hash
            c.rename(a)
            self.assertEqual(audit.sha256([a, b]), both)
            a.write_bytes(b"on"), b.write_bytes(b"etwo")                              # the same bytes, split otherwise
            self.assertNotEqual(audit.sha256([a, b]), both)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_two_caches_on_one_file_keep_both_answers(self):
        import tempfile
        from common import cache as cache_module
        tmp = Path(tempfile.mkdtemp())
        try:
            one, two = cache_module.Cache(tmp, "extract"), cache_module.Cache(tmp, "extract")   # two processes
            one.put("k1", {"triples": [1]})
            two.put("k2", {"triples": [2]})
            self.assertEqual(set(cache_module.Cache(tmp, "extract").answers), {"k1", "k2"})
            one.put("k3", {"triples": [3]})
            self.assertEqual(set(cache_module.Cache(tmp, "extract").answers), {"k1", "k2", "k3"})
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_an_input_changed_during_the_run_stops_it(self):
        """run_step hashes the inputs before main and checks them again after: a file changed in between (the
        annotation tool saving while 070 waited at its question) ends the run stopped, with no manifest."""
        import tempfile
        from unittest import mock
        from common import step
        tmp = Path(tempfile.mkdtemp())
        try:
            src = tmp / "in.txt"
            src.write_text("v1", encoding="utf-8")

            def main(inputs, settings, output):
                Path(inputs["records"]).write_text("v2", encoding="utf-8")       # something writes the input
                return step.Results(headline={})
            with mock.patch.object(step, "RESULTS_DIR", tmp / "results"), mock.patch.object(step, "REPORTS_DIR", tmp / "reports"), \
                    mock.patch.object(step, "LOGS_DIR", tmp / "logs"), self.assertRaises(SystemExit) as caught:
                step.run_step("999_stand_in", {"records": str(src)}, {}, main, argv=[])
            self.assertEqual(caught.exception.code, 2)
            report = max((tmp / "reports").glob("999_stand_in_*.md")).read_text(encoding="utf-8")
            self.assertIn("1 input(s) changed while the step ran: records", report)
            self.assertFalse((tmp / "results" / "999_stand_in" / "_manifest.json").exists())
            # unchanged inputs: the run ends ran, and the manifest says which inputs were given on the command line
            with mock.patch.object(step, "RESULTS_DIR", tmp / "results"), mock.patch.object(step, "REPORTS_DIR", tmp / "reports"), \
                    mock.patch.object(step, "LOGS_DIR", tmp / "logs"):
                step.run_step("999_stand_in", {"records": str(src), "other": str(src)}, {},
                              lambda i, s, o: step.Results(headline={}), argv=["--other", str(tmp / "in.txt")])
            m = json.loads((tmp / "results" / "999_stand_in" / "_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual({r["name"]: r["given"] for r in m["inputs"]}, {"records": False, "other": False})
        finally:
            import logging
            logging.shutdown()
            shutil.rmtree(tmp, ignore_errors=True)


class HasText(unittest.TestCase):
    """One definition of "has text" (common.records_io.has_text): the same fields as the text a model reads
    (full_text: title, notes and the extra text fields 020 kept), blank once evened out."""

    def test_variants(self):
        from common.records_io import full_text, has_text, text_fields
        for record, expected in (({"title": "MODIS", "notes": ""}, True),
                                 ({"title": "", "notes": "x"}, True),
                                 ({"title": "", "notes": ""}, False),
                                 ({}, False),
                                 ({"title": None, "notes": None}, False),
                                 ({"notes": "\u200b"}, False),                         # a zero-width space only
                                 ({"notes": "\ufeff "}, False),                        # a byte-order mark and a space
                                 ({"notes": "\u00a0\t\n"}, False),                    # a no-break space, blank space
                                 ({"notes": "\u00ad"}, False),                         # a soft hyphen
                                 ({"notes": "\u200bx"}, True),                         # near miss: a letter too
                                 ({"_cleaning": {"title": "a", "notes": "a", "author": "a"}, "author": "Smith"}, True),
                                 ({"author": "Smith"}, False),                        # not a text field of this record
                                 ({"_cleaning": {"title": "a", "notes": "a"}, "author": "Smith"}, False)):
            with self.subTest(record=record):
                self.assertEqual(has_text(record), expected)
                self.assertEqual(has_text(record), bool(full_text(record).strip()) and expected)
        r = {"_cleaning": {"title": "a", "notes": "a", "author": "a"}, "title": "T", "notes": "", "author": "Smith"}
        self.assertEqual(text_fields(r), ["title", "notes", "author"])
        self.assertEqual(full_text(r), "title: T\n\nauthor: Smith")
        from common import chunking
        self.assertIs(chunking.full_text, full_text)                              # one home, imported from chunking too

    def test_every_consumer_uses_it(self):
        """020's count, 030's induction candidates, 050, 060 and 070 take has_text from common.records_io: no other
        definition of "has text" (a strip() over the text fields) in the steps."""
        from support import ROOT
        for rel in ("020_clean/020_clean_helpers/moves.py", "030_split/030_split_helpers/moves.py",
                    "050_annotate/050_annotate_helpers/records.py", "060_extract/060_extract_helpers/records.py",
                    "070_evaluate/070_evaluate_helpers/records.py"):
            text = (ROOT / rel).read_text(encoding="utf-8")
            self.assertIn("has_text", text, rel)
            self.assertNotRegex(text, r"any\(.*\.strip\(\) for name in", rel)


class SettingsCheck(unittest.TestCase):
    """One validator (common.step.check_settings, with each step's Spec table) for every setting: kind, lowest and
    highest value, allowed values. Every step's settings at the bound, just outside it, as true/false, as a fraction,
    and an allowed-values setting with a near miss."""

    #: Run in a process of its own per step (two steps' helpers can't be imported into one process: tests/run_all.py).
    PER_STEP = """
import json, sys
sys.path.insert(0, sys.argv[1])
from common.step import Spec, check_settings, load_moves, shared_specs
from common.stop import Stop
step, defaults = sys.argv[2], json.loads(sys.argv[3])
own = load_moves(step).SPECS
specs = {**{k: v for k, v in shared_specs().items() if k in defaults}, **own}
assert set(specs) == set(defaults), (step, set(specs) ^ set(defaults))     # every setting has a Spec
check_settings(defaults, specs)                                             # the defaults pass
for name, spec in specs.items():
    assert not spec.problem(defaults[name]), (name, defaults[name])
    if spec.kind in (int, float):
        if spec.low is not None:
            assert not spec.problem(spec.low) and spec.problem(spec.low - 1), name
        if spec.high is not None:
            assert not spec.problem(spec.high) and spec.problem(spec.high + 1), name
        assert spec.problem(True) and spec.problem("3"), name                 # never a number
        assert spec.problem(2.5) == (spec.kind is int), name
    elif spec.kind is bool:
        assert spec.problem("true") and spec.problem(1), name
    elif spec.choices:
        for near in (spec.choices[0] + "s", spec.choices[0][:-1], "", None):
            assert spec.problem(near), (name, near)
        assert not spec.problem(spec.choices[0].upper()) and not spec.problem(f" {spec.choices[0]} "), name
    else:
        assert spec.problem(3) and spec.problem("") == (not spec.empty), name
    try:
        check_settings({**defaults, name: object()}, specs)
    except Stop as e:
        assert f"The setting {name} must be {spec.allows()}, but is" in str(e), str(e)
    else:
        raise AssertionError(name)
print("ok", step, sorted(specs))
"""

    def test_every_step(self):
        import json
        import subprocess
        import sys
        from support import ROOT
        from test_docs import panel
        for step in ("010_harvest", "020_clean", "030_split", "040_induce_schema", "050_annotate", "060_extract", "070_evaluate"):
            with self.subTest(step=step):
                run = subprocess.run([sys.executable, "-c", self.PER_STEP, str(ROOT), step, json.dumps(panel(step)["SETTINGS"])],
                                     capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=ROOT)
                self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
                self.assertTrue(run.stdout.startswith(f"ok {step}"), run.stdout)

    def test_message_names_what_to_give(self):
        from common.step import Spec, check_settings
        from common.stop import Stop
        specs = {"n": Spec(int, 1, 64), "part": Spec(str, choices=("tuning", "held-out")), "m": Spec(str, empty=False)}
        for settings, words in (({"n": 0}, "The setting n must be a whole number from 1 to 64, but is 0, so the step can't run. Give --n 1,"),
                                ({"n": 65}, "but is 65, so the step can't run. Give --n 64,"),
                                ({"n": True}, "but is True, so the step can't run. Give --n <a whole number from 1 to 64>,"),
                                ({"part": "Tuning "}, None),
                                ({"part": "tunings"}, "The setting part must be one of tuning, held-out, but is 'tunings'"),
                                ({"m": "  "}, "The setting m must be a text (not empty), but is '  '")):
            if words is None:
                check_settings(settings, specs)
                continue
            with self.subTest(settings=settings), self.assertRaises(Stop) as stop:
                check_settings(settings, specs)
            self.assertIn(words, str(stop.exception))
        check_settings({"other": -5}, specs)                                           # a setting without a Spec: not checked

    def test_run_step_checks_before_reading_inputs(self):
        """run_step stops on a bad setting before any input is looked at: a missing input file isn't what stops it."""
        import tempfile
        from unittest import mock
        from common import step
        tmp = Path(tempfile.mkdtemp())
        try:
            with mock.patch.object(step, "RESULTS_DIR", tmp / "results"), mock.patch.object(step, "REPORTS_DIR", tmp / "reports"), \
                    mock.patch.object(step, "LOGS_DIR", tmp / "logs"), self.assertRaises(SystemExit) as caught:
                step.run_step("999_stand_in", {"records": str(tmp / "missing.jsonl")}, {"workers": 4}, lambda *a: None,
                              argv=["--workers", "0"], specs={})
            self.assertEqual(caught.exception.code, 2)
            report = max((tmp / "reports").glob("999_stand_in_*.md")).read_text(encoding="utf-8")
            self.assertIn("The setting workers must be a whole number from 1 to 64, but is 0", report)
            self.assertNotIn("missing.jsonl", report.split("The setting workers")[1][:200])
        finally:
            import logging
            import shutil
            logging.shutdown()
            shutil.rmtree(tmp, ignore_errors=True)


class OneSelection(unittest.TestCase):
    """common/common_helpers/ground_truth.py: every record has one state, every consumer takes its rows by purpose
    (GroundTruth.select), and nothing but finished tuning records shapes the ground truth schema a model or a check
    sees. One fixture of every state, run through every consumer."""

    #: (id, pool position, part, files and marks, what its row coins or uses)
    HAND = {"entity_classes": {"Instrument": "d", "Spacecraft": "d", "Dataset": "d"}, "predicates": {"ABOARD": "d"},
            "patterns": [("Instrument", "ABOARD", "Spacecraft")]}

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.pool = [{"id": rid, "position": i, "part": part} for i, (rid, part) in enumerate(
            [("fin_t", "tuning"), ("draft_t", "tuning"), ("fin_h", "held-out"), ("draft_h", "held-out"),
             ("twice", "tuning"), ("bad", "tuning")])]
        gt_file(self.tmp, "batch_000.csv", [
            row("fin_t", "MODIS", "Instrument", "ABOARD", "Gauge", "Gauge", "s"),                 # checked: coins Gauge
            row("draft_t", "MODIS", "Instrument", "DRAFTED", "Aqua", "Spacecraft", "s", "0"),      # a model's draft,
            row("draft_t", "AIRS", "Instrument", "DRAFTED", "Aqua", "Spacecraft", "s", "0"),       # its pattern twice
            row("fin_h", "MODIS", "Instrument", "ABOARD", "Data", "Dataset", "s"),                 # held-out: new pattern
            row("fin_h", "MODIS", "HeldThing", "ABOARD", "Aqua", "Spacecraft", "s"),               # and a coined one
            row("draft_h", "MODIS", "HeldDraft", "ABOARD", "Aqua", "Spacecraft", "s", "0"),
            row("twice", "MODIS", "TwiceThing", "ABOARD", "Aqua", "Spacecraft", "s"),
            row("bad", "MODIS", "BadThing", "ABOARD", "Aqua", "Spacecraft", "s", "2")])
        gt_file(self.tmp, "batch_001.csv", [row("twice", "MODIS", "TwiceThing", "ABOARD", "Aqua", "Spacecraft", "s")])
        self.gt = ground_truth.read_ground_truth(self.tmp, self.pool)

    def test_states_and_purposes(self):
        g = ground_truth
        self.assertEqual({rid: self.gt.state(rid) for rid in ("fin_t", "draft_t", "fin_h", "draft_h", "twice", "bad", "nope")},
                         {"fin_t": g.FINISHED, "draft_t": g.UNFINISHED, "fin_h": g.FINISHED, "draft_h": g.UNFINISHED,
                          "twice": g.IN_TWO_FILES, "bad": g.BAD_MARK, "nope": g.ABSENT})
        ids = lambda *a, **k: set(self.gt.select(*a, **k).ids)                 # noqa: E731
        self.assertEqual(ids(g.SCHEMA_EVIDENCE), {"fin_t"})
        self.assertEqual(ids(g.SCHEMA_EVIDENCE, parts="held-out"), set())      # parts never widens it
        self.assertEqual(ids(g.EVALUABLE), {"fin_t", "fin_h"})
        self.assertEqual(ids(g.EVALUABLE, parts="held-out"), {"fin_h"})
        self.assertEqual(ids(g.ANNOTATED), {"fin_t", "draft_t", "fin_h", "draft_h", "twice", "bad"})
        self.assertEqual(ids(g.TO_FIX), {"draft_t", "draft_h", "twice", "bad"})
        self.assertEqual(self.gt.records["twice"]["files"], ["batch_000.csv", "batch_001.csv"])
        # the same files, read again with one file replaced (the annotation tool's save): states follow
        after = self.gt.with_file("batch_001.csv", [])
        self.assertEqual(after.state("twice"), g.FINISHED)
        self.assertEqual(self.gt.state("twice"), g.IN_TWO_FILES)               # the original is left alone
        self.assertEqual(g.marks_state(["1", "1"]), g.FINISHED)
        self.assertEqual([g.marks_state(m) for m in (["1", "0"], ["0"], ["1", "2"], ["", "1"], ["yes"])],
                         [g.UNFINISHED, g.UNFINISHED, g.BAD_MARK, g.BAD_MARK, g.BAD_MARK])

    def test_schema_view_takes_finished_tuning_records_only(self):
        view = ground_truth.ground_truth_schema_view(self.HAND, self.gt)
        self.assertEqual(view["coined"], {"entity_classes": ["Gauge"], "predicates": []})
        self.assertEqual(view["used_patterns"], [("Instrument", "ABOARD", "Gauge")])
        # what 050's drafting model is shown, and what its checks compare with
        text = _helper("050_annotate").vocabulary_text("FILE", view["coined"], view["used_patterns"])
        for leaked in ("DRAFTED", "HeldThing", "HeldDraft", "TwiceThing", "BadThing", "Dataset"):
            self.assertNotIn(leaked, text.replace("FILE", ""), leaked)
        entries = validate.SchemaEntries({**self.HAND, "patterns": view["patterns"]})
        self.assertIn(validate.PATTERN_NOT_IN_SCHEMA, validate.check_against_schema(
            {"subject_class": "Instrument", "predicate": "ABOARD", "object_class": "Dataset"}, entries))   # held-out's
        self.assertNotIn(validate.PATTERN_NOT_IN_SCHEMA, validate.check_against_schema(
            {"subject_class": "Instrument", "predicate": "ABOARD", "object_class": "Gauge"}, entries))
        # every consumer refuses the whole ground truth: it must say which purpose
        for f in (lambda: ground_truth.with_coined(self.HAND, self.gt), lambda: ground_truth.uses_of(self.gt, "predicate", "x"),
                  lambda: ground_truth.used_patterns(self.gt), lambda: ground_truth.coined_uses(self.gt, view["coined"]),
                  lambda: ground_truth.pattern_uses(self.gt), lambda: ground_truth.check_rows(self.gt, {})):
            with self.assertRaises(TypeError):
                f()

    def test_what_070_and_the_status_stop_on(self):
        """Step 070 and the status ask about the finished records of every part (EVALUABLE): Gauge (tuning) and
        HeldThing (held-out, which can't be added); a draft's, a bad mark's or a record in two files' never."""
        gaps = ground_truth.ground_truth_schema_gaps(self.HAND, self.gt)["component_classes"]
        self.assertEqual([(g["component_class"], g["parts"]) for g in gaps], [("Gauge", ["tuning"]), ("HeldThing", ["held-out"])])
        records_070 = _helper("070_evaluate")
        schema = self.tmp / "ground_truth_schema.txt"
        schema.write_text("ENTITY CLASSES\n--------------\nInstrument  d\nSpacecraft  d\nDataset  d\n\nPREDICATES\n"
                          "----------\nABOARD  d\n", encoding="utf-8")
        from common.stop import Stop
        catalog = {rid: {"id": rid, "title": "T", "notes": "s"} for rid in ("fin_t", "draft_t", "fin_h", "draft_h", "twice", "bad")}
        with self.assertRaises(Stop) as stop:
            records_070.check_evaluable(self.gt, catalog, schema)
        self.assertIn("Gauge (entity class): batch_000.csv line 2: not in the ground truth schema", str(stop.exception))
        self.assertIn("HeldThing (entity class): batch_000.csv line 6: not in the ground truth schema", str(stop.exception))
        for absent in ("DRAFTED", "HeldDraft", "TwiceThing", "BadThing"):
            self.assertNotIn(absent, str(stop.exception))
        # the advice for the first gap of each part names the state of the record there
        positions = {r["id"]: r["position"] for r in self.pool}
        gap = lambda order: records_070._first_gap(order, "tuning", positions, set(), self.gt)   # noqa: E731
        self.assertIn("finished, but not extracted", gap(["fin_t"]))
        self.assertIn("not finished in the ground truth", gap(["draft_t"]))
        self.assertIn("in batch_000.csv and batch_001.csv, annotated twice", gap(["twice"]))
        self.assertIn("neither 0 nor 1", gap(["bad"]))
        self.assertIn("has no text (no title, notes or other text field), so 050 and 060 skip it",
                      records_070._first_gap(["mute"], "tuning", {"mute": 3}, set(), self.gt, {"mute"}))
        self.assertIn("not in the ground truth yet. Draft it", records_070._first_gap(["new"], "tuning", {"new": 9},
                                                                                       set(), self.gt))

    def test_one_reading_of_a_source_line(self):
        """common.schema_io.parse_source, used by 060's source check and learned_from, 070's note on held-out
        sources and the annotation tool: a position's part comes from the pool, never from the word before it."""
        from common.schema_io import ground_truth_source_problem, parse_source, source_line
        parts = {0: "tuning", 1: "tuning", 2: "held-out"}
        cases = [   # source, (tuning, held-out, unknown), problem's start or None
            ("ground truth tuning #0, #1", ([0, 1], [], []), None),
            ("Ground-Truth tuning #0", ([0], [], []), None),
            ("ground_truth tuning #1; mentor", ([1], [], []), None),
            ("ground truth tuning #0, #2", ([0], [2], []), "comes from held-out record(s) #2"),     # no word "held-out"
            ("ground truth tuning #0; held-out #2", ([0], [2], []), "comes from held-out record(s) #2"),
            ("ground truth #2", ([], [2], []), "comes from held-out record(s) #2"),
            ("ground truth held-out #0", ([0], [], []), "names ground truth records but doesn't say tuning"),
            ("ground truth tuning #9", ([], [], [9]), "names #9, not a pool position"),
            ("ground truth tuning", ([], [], []), "says ground truth but names no record"),
            ("mentor, 2026-10-01 #2", ([], [], []), None),                    # not the ground truth: names no record
            ("", ([], [], []), None)]
        for source, (tuning, held, unknown), problem in cases:
            found = parse_source(source, parts)
            self.assertEqual((found["tuning"], found["held_out"], found["unknown"]), (tuning, held, unknown), source)
            why = ground_truth_source_problem(source, parts)
            self.assertEqual(why is None, problem is None, (source, why))
            if problem:
                self.assertTrue(why.startswith(problem), (source, why))
        self.assertEqual(source_line([8, 3, 3]), "ground truth tuning #3, #8")
        self.assertEqual(parse_source(source_line([8, 3]), {3: "tuning", 8: "tuning"})["tuning"], [3, 8])
        self.assertEqual(source_line([]), "")

    def test_held_out_sources_070(self):
        """070's note on the ground truth schema's entries learned from held-out records reads parse_source too."""
        records_070 = _helper("070_evaluate")
        schema = self.tmp / "ground_truth_schema.txt"
        schema.write_text("ENTITY CLASSES\n--------------\nGauge  d\n          source: ground truth tuning #0, #2\n"
                          "Meter  d\n          source: ground truth tuning #0\n\nPREDICATES\n----------\nABOARD  d\n",
                          encoding="utf-8")
        found = records_070.held_out_sources(schema, self.pool)
        self.assertEqual([(kind, name, records) for kind, name, _, records in found], [("entity class", "Gauge", [(2, "fin_h")])])

    def test_no_consumer_reads_the_rows_itself(self):
        """A guard: outside ground_truth.py, no code reads a GroundTruth's rows; every consumer asks select()."""
        import re
        offenders = []
        for path in ROOT.rglob("*.py"):
            rel = path.relative_to(ROOT).as_posix()
            if rel.startswith(("archive/", ".myvenv/", "DONOTTRACK/")) or rel == "common/common_helpers/ground_truth.py":
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for n, line in enumerate(text.splitlines(), 1):
                if re.search(r"\._rows\b|\b(gt|ground_truth|truth)\.rows\b|read_ground_truth\([^)]*\)\.rows", line) \
                        and "tests/" not in rel[:6]:
                    offenders.append(f"{rel}:{n}: {line.strip()}")
        self.assertEqual(offenders, [])

    def test_names_written_by_code_are_never_coined(self):
        """CatalogEntry (entity class), DESCRIBES (predicate) and X (the undecided entity class) are never coined, in
        any spelling; the same words in another kind are (a predicate "x" is a typo to fix)."""
        gt_file(self.tmp, "batch_000.csv", [
            row("fin_t", "fin_t", "catalog_entry", "describes", "T", "x", "(record structure)"),
            row("fin_t", "MODIS", "Instrument", "x", "Aqua", "CatalogEntry", "s"),
            row("fin_t", "MODIS", "Instrument", "Describes", "Aqua", "Spacecraft", "s")])
        (self.tmp / "batch_001.csv").unlink()
        gt = ground_truth.read_ground_truth(self.tmp, self.pool)
        v = ground_truth.ground_truth_schema_view(self.HAND, gt)
        self.assertEqual(v["coined"], {"entity_classes": [], "predicates": ["x"]})

    def test_one_file_name_rule(self):
        """Only batch_<NNN>.csv is read (the name 050 numbers its drafted batches by); any other batch_*.csv is a
        problem, named, and not read."""
        for name in ("batch_6.csv", "batch_06.csv", "batch_abc.csv", "batch_.csv"):
            gt_file(self.tmp, name, [row("other", "MODIS", "Gizmo", "ABOARD", "Aqua", "Spacecraft", "s")])
            gt = ground_truth.read_ground_truth(self.tmp, self.pool)
            self.assertEqual(gt.state("other"), ground_truth.ABSENT, name)
            self.assertTrue(any(f"{name} isn't read" in p for p in gt.problems), (name, gt.problems))
            (self.tmp / name).unlink()
        gt_file(self.tmp, "batch_1000.csv", [row("other", "MODIS", "Gizmo", "ABOARD", "Aqua", "Spacecraft", "s")])
        self.assertEqual(ground_truth.read_ground_truth(self.tmp, self.pool).state("other"), ground_truth.FINISHED)



class Evaluable(unittest.TestCase):
    """common.ground_truth.evaluable_problems: step 070's one gate. A finished record with any row error, a second
    describes triple, a component class the ground truth schema lacks, or a fact that waits on an expert whose
    entity classes or predicate the ground truth schema lacks, is named with its file, line, problem and what to do;
    the same rows in a record not finished are not (they aren't evaluated)."""

    HAND = {"entity_classes": {"Instrument": "d", "Spacecraft": "d", "Dataset": "d"}, "predicates": {"ABOARD": "d"},
            "patterns": []}
    RECORDS = {"r1": {"id": "r1", "title": "Title one", "notes": "MODIS aboard Aqua."},
               "r2": {"id": "r2", "title": "Title two", "notes": "MODIS aboard Aqua."}}

    def problems(self, rows, pending=()):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp)
        gt_file(tmp, "batch_000.csv", rows)
        gt = ground_truth.read_ground_truth(tmp, [{"id": "r1", "position": 0, "part": "tuning"},
                                                  {"id": "r2", "position": 1, "part": "held-out"}])
        return ground_truth.evaluable_problems(gt, self.RECORDS, self.HAND, "annotations/ground_truth_schema.txt",
                                               list(pending))

    def describes(self, rid="r1", cls="Dataset", done="1"):
        return row(rid, rid, "CatalogEntry", "DESCRIBES", f"Title {'one' if rid == 'r1' else 'two'}", cls,
                   "(record structure)", done)

    def test_each_problem_and_its_near_miss(self):
        good = row("r1", "MODIS", "Instrument", "ABOARD", "Aqua", "Spacecraft", "MODIS aboard Aqua")
        self.assertEqual(self.problems([self.describes(), good]), [])
        cases = [   # (rows of record r1, the words the problem must have)
            ([self.describes(), row("r1", "MODIS", "Instrument", "ABOARD", "", "Spacecraft", "x")], "but not all three"),
            ([self.describes(), row("r1", "MODIS", "Instrument", "ABOARD", "Aqua", "Spacecraft", "")], "no source text"),
            ([self.describes(), row("r1", "MODIS", "Instrument", "ABOARD", "Aqua", "Spacecraft", "aboard Terra")],
             "isn't in the record's text"),
            ([self.describes(cls="X"), good], "has no describes class"),
            ([self.describes(cls="x"), good], "has no describes class"),             # X in any spelling
            ([row("r1", "other", "CatalogEntry", "DESCRIBES", "Title one", "Dataset", "(record structure)"), good],
             "subject isn't the record's id"),
            ([self.describes(), self.describes(cls="Instrument"), good], "another describes triple before this one"),
            ([self.describes(), row("r1", "MODIS", "Instrument", "aboard", "Aqua", "Spacecraft", "MODIS aboard Aqua"),
              row("r1", "MODIS", "Gizmo", "ABOARD", "Aqua", "Spacecraft", "MODIS aboard Aqua")], "Gizmo (entity class)"),
        ]
        for rows, words in cases:
            found = self.problems(rows)
            self.assertEqual(len(found), 1, (words, found))
            self.assertIn(words, found[0])
            self.assertTrue(found[0].startswith("batch_000.csv line ") or found[0].startswith("Gizmo"), found[0])
            # the near miss: the same rows in a record not finished are not evaluated, so not named
            self.assertEqual(self.problems([r[:-1] + ["0"] for r in rows]), [], words)
        # a held-out finished record is evaluated too
        self.assertIn("isn't in the record's text", self.problems(
            [self.describes("r2"), row("r2", "MODIS", "Instrument", "ABOARD", "Aqua", "Spacecraft", "Terra")])[0])
        # an id not in the catalog
        self.assertIn("isn't a record of the catalog", self.problems([row("zz", "a", "Instrument", "ABOARD", "b",
                                                                           "Spacecraft", "s")])[0])

    def test_pending_rows(self):
        good = [self.describes(), row("r1", "MODIS", "Instrument", "ABOARD", "Aqua", "Spacecraft", "MODIS aboard Aqua")]
        wait = {"id": "r1", "subject": "MODIS", "subject_class": "instrument", "predicate": "aboard", "object": "Aqua",
                "object_class": "SPACECRAFT", "source_text": "MODIS aboard Aqua", "left_out": "x", "question": "Q1",
                "line": 2}
        self.assertEqual(self.problems(good, [wait]), [])                   # the schema's, in another spelling
        for slot, value in (("predicate", "CARRIED_ON"), ("subject_class", "Sensor"), ("object_class", "Satelite")):
            found = self.problems(good, [{**wait, slot: value}])
            self.assertEqual(len(found), 1, slot)
            self.assertTrue(found[0].startswith("annotations/pending_triples.csv line 2 (record r1): its "), found[0])
            self.assertIn(value, found[0])
            self.assertIn("No clear would-be triple:", found[0])

    def test_070_stops_on_them(self):
        records_070 = _helper("070_evaluate")
        from common.stop import Stop
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp)
        gt_file(tmp, "batch_000.csv", [self.describes(), self.describes(cls="Instrument"),
                                       row("r1", "MODIS", "Instrument", "ABOARD", "Aqua", "Spacecraft", "Terra")])
        schema = tmp / "ground_truth_schema.txt"
        schema.write_text("ENTITY CLASSES\n--------------\nInstrument  d\nSpacecraft  d\nDataset  d\n\nPREDICATES\n"
                          "----------\nABOARD  d\n", encoding="utf-8")
        gt = ground_truth.read_ground_truth(tmp, [{"id": "r1", "position": 0, "part": "tuning"}])
        with self.assertRaises(Stop) as stop:
            records_070.check_evaluable(gt, self.RECORDS, schema)
        said = str(stop.exception)
        self.assertIn("Step 070 can't evaluate", said)
        self.assertIn("batch_000.csv line 3 (record r1): the record has another describes triple", said)
        self.assertIn("batch_000.csv line 4 (record r1): its source text isn't in the record's text", said)
        self.assertIn("then run `py 070_evaluate/run.py` again", said)


class DescribesClassOfThePieces(unittest.TestCase):
    """common.extraction.describes_class: the text pieces of one record each name a describes class (or none). The
    one named by the most pieces is kept (by loose match; on a tie, the first named), and when they disagree the
    describes triple is flagged describes_classes_differ, never resolved without a word."""

    def test_cases(self):
        cases = [(["Dataset"], ("Dataset", False)), (["", "Dataset", ""], ("Dataset", False)),
                 (["Dataset", "dataset", "DATA_SET"], ("Dataset", False)),           # one entity class, three spellings
                 (["Dataset", "Instrument"], ("Dataset", True)),                     # a tie: the first named
                 (["Instrument", "Dataset", "Dataset"], ("Dataset", True)),          # the most pieces
                 ([], ("", False)), (["", ""], ("", False))]
        for named, want in cases:
            self.assertEqual(extraction.describes_class(named), want, named)
        entries = validate.SchemaEntries({"entity_classes": {"Dataset": "", "Instrument": ""}, "predicates": {}})
        replies = [{"describes_class": "Instrument", "triples": []}, {"describes_class": "Dataset", "triples": []},
                   {"describes_class": "dataset", "triples": []}]
        rows, _ = extraction.build_rows("r1", "T", "title: T", replies, entries)
        self.assertEqual((rows[0]["object_class"], rows[0]["flags"]), ("Dataset", ["describes_classes_differ"]))
        rows, _ = extraction.build_rows("r1", "T", "title: T", replies[1:], entries)
        self.assertEqual((rows[0]["object_class"], rows[0]["flags"]), ("Dataset", []))

    def test_a_describes_triple_of_the_models_own_is_removed(self):
        entries = validate.SchemaEntries({"entity_classes": {"Dataset": ""}, "predicates": {}})
        own = {"subject": "r1", "subject_class": "catalog_entry", "predicate": "Describes", "object": "T",
               "object_class": "Dataset", "source_text": "T"}
        rows, removed = extraction.build_rows("r1", "T", "title: T", [{"describes_class": "Dataset", "triples": [own]}],
                                              entries)
        self.assertEqual(len(rows), 1)                                       # the code's describes triple only
        self.assertEqual([r["reason"] for r in removed], ["describes_triple"])

class AnnotationsReadCleanly(unittest.TestCase):
    """The real annotations/ files read without problems (read only)."""

    def test_ground_truth(self):
        gt = ground_truth.read_ground_truth()
        self.assertEqual(gt.problems, [])

    def test_pool(self):
        rows = read_csv(support.ROOT / "annotations" / "ground_truth_candidates.csv")
        self.assertEqual(len(rows), 1000)
        self.assertEqual(len({r["id"] for r in rows}), 1000)


class PerTextCounts(unittest.TestCase):
    """The per-text count table and headline numbers 040, 050, 060, and 070 share (common/common_helpers/report.py)."""

    def test_stats(self):
        from common.report import per_text_stats
        self.assertEqual(per_text_stats([3, 0, 7, 2]),
                         {"texts": 4, "min": 0, "max": 7, "mean": 3, "median": 2.5, "total": 12, "none": 1})
        self.assertEqual(per_text_stats([5])["median"], 5)
        self.assertEqual(per_text_stats([1, 2, 9])["median"], 2)                    # odd count: the middle one
        self.assertEqual(per_text_stats(iter([0, 0]))["none"], 2)                  # any iterable

    def test_empty(self):
        from common.report import per_text_headline, per_text_stats, per_text_table
        self.assertEqual(per_text_stats([]),
                         {"texts": 0, "min": None, "max": None, "mean": None, "median": None, "total": 0, "none": 0})
        self.assertEqual(per_text_table("X per text", [("raw", [])])[2], "| raw | 0 | – | – | – | – | 0 | 0 |")
        self.assertEqual(per_text_headline([("raw X", [])]), {"raw X": 0, "raw X, mean per text": "–"})

    def test_table_and_headline(self):
        from common.report import per_text_headline, per_text_table
        lines = per_text_table("Triple instances per text", [("raw (a | b)", [3, 0, 8, 2]), ("kept", [1000, 1, 2])])
        self.assertEqual(lines[0], "| Triple instances per text | Texts | Min | Max | Mean | Median | Total | Texts with none |")
        self.assertEqual(lines[2], "| raw (a \| b) | 4 | 0 | 8 | 3.2 | 2.5 | 13 | 1 |")      # mean 1 decimal, | escaped
        self.assertEqual(lines[3], "| kept | 3 | 1 | 1,000 | 334.3 | 2 | 1,003 | 0 |")
        self.assertEqual(per_text_headline([("raw", [3, 0, 8, 2])]), {"raw": 13, "raw, mean per text": 3.2})


if __name__ == "__main__":
    unittest.main()
