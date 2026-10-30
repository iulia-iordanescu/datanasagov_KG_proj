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
        self.assertEqual(len(gt.rows), 5)
        self.assertEqual(gt.records["a"], {"file": "batch_000.csv", "rows": 2, "finished": True})
        self.assertFalse(gt.records["b"]["finished"])
        self.assertEqual(gt.problems, [])
        self.assertEqual([r[ground_truth.LINE_FIELD] for r in gt.rows], [2, 3, 5, 7, 8])   # file lines
        self.assertTrue(gt.rows[1]["_origin"][0].endswith("batch_000.csv#1"))

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
        self.assertNotIn("a", gt.records)                                         # in two files: kept out
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
        found = ground_truth.check_rows(ground_truth.read_ground_truth(self.tmp), records)
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
        v = ground_truth.with_coined(hand, ground_truth.read_ground_truth(self.tmp))
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
        for bad in ("tunning", "", "Both"):
            with self.assertRaises(Stop):
                self.chosen(part=bad)

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
        derives from statements in two places). Then it is in the text when each passage is. Near misses: one passage
        not in the text, passages joined by "..." or "…" without spaces (taken as one passage), and a lone passage."""
        text = text_match.Text("The first is a skin SST (NSST). Other words here. The SST4 product has lower uncertainty.")
        row = {"subject": "SST4", "object": "skin SST", "source_text": ""}
        def errors(source):
            return validate.check_triple_instance({**row, "source_text": source}, text)[0]
        self.assertEqual(errors("The first is a skin SST … The SST4 product has lower uncertainty"), [])
        self.assertEqual(errors("The first is a skin SST … The SST4 product has higher uncertainty"),
                         ["source_not_in_text"])
        self.assertEqual(errors("The first is a skin SST ... The SST4 product has lower uncertainty"), ["source_not_in_text"])
        self.assertEqual(errors("The first is a skin SST…The SST4 product has lower uncertainty"), ["source_not_in_text"])
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
        self.assertEqual(rows[0]["object_class"], "Dataset")                         # the first entity class named
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
        listed = row.split("with the reason, one of five:", 1)[1].split(". How the five relate", 1)[0]
        named = re.findall(r"`([a-z_ ]+)` \(", listed)
        self.assertEqual(named, ["source_text", "component_class_not_in_schema",
                                 extraction.joined_reason([extraction.SOURCE_TEXT, extraction.COMPONENT_CLASS_NOT_IN_SCHEMA]),
                                 "duplicate", "malformed"])
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
            got = partial_reviews.read_reviews(path)
            key = partial_reviews.pair_key("a", {"subject": "modis", "predicate": "aboard", "object": "aqua"},
                                           {"subject": "MODIS terra", "predicate": "ABOARD", "object": "Aqua."})
            self.assertEqual(got, {key: partial_reviews.NOT_SAME})                  # the last row wins
            self.assertEqual(partial_reviews.read_reviews(tmp / "missing.csv"), {})
            self.assertEqual(len(read_csv(path)), 2)
        finally:
            shutil.rmtree(tmp)


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
            self.assertEqual({r["id"]: r["drafted_by"] for r in gt.rows}, {"a": "", "b": "gpt-4o"})
        finally:
            shutil.rmtree(tmp)

    def test_note(self):
        from support import use_step
        use_step("060_extract")
        from records import same_model_notes                                   # 060_extract_helpers/records.py
        rows = [{"id": "a", "drafted_by": "google-claude-sonnet-5"}, {"id": "a", "drafted_by": ""},
                {"id": "b", "drafted_by": "claude-opus-4"}, {"id": "c", "drafted_by": "gpt-4o"}, {"id": "d", "drafted_by": ""}]
        gt = type("GT", (), {"rows": rows})
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


class TwoPasses(unittest.TestCase):
    """060's prompt (060_extract_prompts/extract.txt) always asks for TRACE-KG's order of work: first find every thing
    the record names, then state the facts about each. The instruction is a paragraph of its own before the schema,
    inside the part sent for prompt caching; the list is not asked for in the reply, so the reply format is 050's.
    It replaced the setting list_things_first (2026-10-30), which no longer exists."""

    RECORD = {"id": "r1", "title": "Kestrel Lake Ice L2", "notes": "Made by the Tern algorithm."}

    def setUp(self):
        from support import use_step
        use_step("060_extract")
        import extract                                                         # 060_extract_helpers/extract.py
        self.extract = extract

    def prompt(self) -> str:
        return extraction.prompt(self.extract.PROMPT, "ENTITY CLASSES\nInstrument  a device", self.RECORD,
                                 "title: Kestrel Lake Ice L2")

    def test_always_two_passes(self):
        prompt = self.prompt()
        self.assertNotIn("$", self.extract.PROMPT.template.replace("$schema", "").replace("$rules", "")
                         .replace("$reply", "").replace("$text", ""))           # no other placeholder left
        first = prompt.index("Work in two passes")
        self.assertIn("1. Find every thing the record names", prompt)
        self.assertIn("2. Take the things one at a time.", prompt)
        self.assertIn("this list in your answer.", prompt)
        self.assertLess(prompt.index("leave describes_class empty."), first)
        self.assertLess(first, prompt.index("\nSCHEMA\n"))                      # before the schema
        self.assertLess(first, prompt.index(extraction.BEGIN_LINE))            # in the part sent for prompt caching
        self.assertIn(extraction.reply(True), prompt)                          # the shared reply format, unchanged

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
                                "temperature": 0, "max_tokens": llm.MAX_ANSWER_TOKENS})
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
                                          "served_as": ["claude-sonnet-5-20260101"], "temperature": 0,
                                          "max_answer_tokens": llm.MAX_ANSWER_TOKENS, "thinking": llm.THINKING,
                                          "thinking_sent": None})
        self.assertEqual(llm.model_label(), "`claude-sonnet-5` through LiteLLM (answered as `claude-sonnet-5-20260101`)")

    def test_unknown_service(self):
        with self.assertRaisesRegex(ValueError, "asksage, litellm"):
            self.llm.paid_calls({"service": "openai", "model": "x", "confirm_paid_calls": False}, Path("060_extract"))


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
