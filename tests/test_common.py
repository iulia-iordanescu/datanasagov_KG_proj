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
        for needle in ["Aquar", "5 minutes", "500 m", "START", "2.5 km", "sat", "MOD0", "500 meters per"]:
            self.assertFalse(t.contains(needle), needle)
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
                 (row("entity class", "(none)", ""), False)]                              # nothing to compare
        for r, stale in cases:
            with self.subTest(r=r):
                self.assertEqual(component_class_mapping.is_stale_gtt(r, gtt), stale)

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
        write_csv(path, cols[:-1], [])
        with self.assertRaisesRegex(ValueError, "lacks the column"):
            component_class_mapping.read_mapping(path)

    def test_real_file_reads(self):
        component_class_mapping.read_mapping()


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
            with mock.patch.object(llm, "call_llm_json", lambda prompt, read_timeout=180: next(answers)):
                self.assertEqual(cache_module.ask_cached(c, calls, "prompt A", "plan"), {"n": 1})
                self.assertEqual(cache_module.ask_cached(c, calls, "prompt A", "plan"), {"n": 1})   # from the cache
                self.assertEqual(cache_module.ask_cached(c, calls, "prompt B", "plan"), {"n": 2})   # changed: asked
            self.assertEqual((paid.made, c.reused, started), (2, 1, ["plan", "plan"]))
            self.assertEqual(cache_module.Cache(tmp, "stage").answers, c.answers)                   # kept on disk
        finally:
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


if __name__ == "__main__":
    unittest.main()
