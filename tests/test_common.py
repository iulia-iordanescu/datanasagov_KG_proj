"""Shared code (common/common_helpers/): reading the ground truth, the
ground truth vocabulary, the fair sample, the checks of each triple
instance, building rows from the model's replies, text pieces, the
translation table, and the partial pair reviews."""
import csv
import json
import shutil
import tempfile
import unittest
from pathlib import Path

import support                                    # noqa: F401  (the repository on the import path)
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
                                             row("c", "modis", "Other", "ABOARD", "aqua", "S", "y")])
        gt_file(self.tmp, "batch_001.csv", [row("a", "AIRS", "I", "ABOARD", "Aqua", "S", "x")])
        gt_file(self.tmp, "batch_002.csv", [["a", "b"]], columns=["id", "subject"])
        gt = ground_truth.read_ground_truth(self.tmp)
        self.assertEqual(len(gt.problems), 4)
        self.assertNotIn("a", gt.records)                                         # in two files: kept out
        joined = "\n".join(gt.problems)
        self.assertIn("record a is in batch_000.csv and batch_001.csv", joined)
        self.assertIn("record b in batch_000.csv: all_facts_extracted", joined)
        self.assertIn("record c in batch_000.csv: lines 5 and 6 are the same triple", joined)
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

    def test_vocabulary(self):
        gt_file(self.tmp, "batch_000.csv", [
            row("a", "a", "CatalogEntry", "DESCRIBES", "T", "Dataset", "(record structure)"),
            row("a", "MODIS", "instrument", "ABOARD", "Aqua", "Probe", "s"),
            row("a", "MODIS", "Instrument", "CARRIED_BY", "Aqua", "probe", "s"),
            row("a", "MODIS", "-", "x", "Aqua", "X", "s")])
        hand = {"entity_classes": {"Instrument": "d", "Dataset": "d"}, "predicates": {"ABOARD": "d"},
                "patterns": [("Instrument", "ABOARD", "Dataset")]}
        v = ground_truth.vocabulary(hand, ground_truth.read_ground_truth(self.tmp))
        self.assertEqual(v["coined"], {"entity_classes": ["Probe"], "predicates": ["CARRIED_BY", "x"]})
        self.assertEqual(v["entity_classes"]["Probe"], "")
        self.assertEqual(v["entity_classes"]["Instrument"], "d")
        self.assertNotIn("CatalogEntry", v["entity_classes"])
        self.assertNotIn("DESCRIBES", v["predicates"])

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
        r = triples_io.describes_row("id1", " A\n title ", "")
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
        head = triples_io.describes_row("r", "T", "Probe")
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
