"""Reading and writing schemas (common/common_helpers/schema_io.py): both
shapes, the additions file, the source rule for additions, and the careful
edits the annotation tool makes to the ground truth schema."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from support import ROOT
from common import schema_io                      # noqa: E402

TEXT = """# a comment
ENTITY CLASSES
--------------
Instrument        a device that takes measurements
Spacecraft        a vehicle in space
Instrument        a repeat, not read
Dataset           a collection of data

PREDICATES
----------
Each entry reads subject -> object.

ABOARD            is carried on
                  Instrument -> Spacecraft; Instrument -> Mission
HAS_PART          has as a part
                  source: mentor, 2026-10-01

PATTERNS
--------
Dataset HAS_PART Dataset
                  source: ground truth tuning #3
"""

HAND = ROOT / "annotations" / "ground_truth_schema.txt"


class Reading(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def write(self, name, text, encoding="utf-8"):
        path = self.tmp / name
        path.write_bytes(text.encode(encoding))
        return path

    def test_text(self):
        s = schema_io.read_schema(self.write("s.txt", TEXT))
        self.assertEqual(list(s["entity_classes"]), ["Instrument", "Spacecraft", "Dataset"])
        self.assertEqual(s["entity_classes"]["Instrument"], "a device that takes measurements")
        self.assertEqual(s["predicates"], {"ABOARD": "is carried on", "HAS_PART": "has as a part"})
        self.assertEqual(s["patterns"], [("Instrument", "ABOARD", "Spacecraft"), ("Instrument", "ABOARD", "Mission"),
                                         ("Dataset", "HAS_PART", "Dataset")])
        self.assertEqual(s["pattern_entries"], [("Dataset", "HAS_PART", "Dataset")])
        self.assertEqual(s["sources"], {"entity_classes": {}, "predicates": {"HAS_PART": "mentor, 2026-10-01"},
                                        "patterns": {"Dataset HAS_PART Dataset": "ground truth tuning #3"}})
        self.assertEqual(len(s["unread"]), 2)                        # the repeat and the prose line
        self.assertTrue(any("repeats" in u for u in s["unread"]))

    def test_pins(self):
        text = TEXT.replace("                  source: mentor, 2026-10-01\n",
                            "                  source: mentor, 2026-10-01\n                  only: any -> Dataset; Instrument -> Spacecraft\n")
        path = self.write("pins.txt", text)
        s = schema_io.read_schema(path)
        self.assertEqual(s["pinned"], {"HAS_PART": [("any", "Dataset"), ("Instrument", "Spacecraft")]})
        self.assertEqual(len(s["unread"]), 2)                        # the "only:" line is read
        self.assertIn("only: any -> Dataset; Instrument -> Spacecraft", schema_io.schema_text(s))
        # renaming an entity class renames it in the pins; renaming the predicate keeps its pins
        path.write_bytes(schema_io.rename_in_ground_truth_schema(path, "entity class", "Dataset", "Collection")[0])
        self.assertEqual(schema_io.read_schema(path)["pinned"]["HAS_PART"], [("any", "Collection"), ("Instrument", "Spacecraft")])
        path.write_bytes(schema_io.rename_in_ground_truth_schema(path, "predicate", "HAS_PART", "HAS_COMPONENT")[0])
        self.assertEqual(schema_io.read_schema(path)["pinned"], {"HAS_COMPONENT": [("any", "Collection"), ("Instrument", "Spacecraft")]})
        path.write_bytes(schema_io.redefine_in_ground_truth_schema(path, "predicate", "HAS_COMPONENT", "has as a component"))
        self.assertIn("HAS_COMPONENT", schema_io.read_schema(path)["pinned"])

    def test_old_heading_bom_crlf(self):
        text = TEXT.replace("ENTITY CLASSES\n--------------", "CLASSES\n-------").replace("\n", "\r\n")
        s = schema_io.read_schema(self.write("s.txt", "﻿" + text))
        self.assertEqual(list(s["entity_classes"]), ["Instrument", "Spacecraft", "Dataset"])
        self.assertEqual(len(s["patterns"]), 3)

    def test_json(self):
        data = {"entity_classes": [{"component_class": " Instrument ", "definition": "d"}, {"component_class": "X"}],
                "predicates": [{"component_class": "ABOARD", "definition": "carried", "support": 3}],
                "patterns": [{"pattern": ["Instrument", "ABOARD", "X"]}, ["X", "ABOARD", "X"]]}
        s = schema_io.read_schema(self.write("s.json", json.dumps(data)))
        self.assertEqual(s["entity_classes"], {"Instrument": "d", "X": ""})
        self.assertEqual(s["patterns"], [("Instrument", "ABOARD", "X"), ("X", "ABOARD", "X")])

    def test_json_errors(self):
        bad = [[], {"entity_classes": {}}, {"entity_classes": [{"definition": "d"}], "predicates": []},
               {"entity_classes": [], "predicates": [], "patterns": [["a", "b"]]}]
        for data in bad:
            with self.subTest(data=data), self.assertRaises(ValueError):
                schema_io.read_schema(self.write("s.json", json.dumps(data)))

    def test_schema_text_round_trip(self):
        s = schema_io.read_schema(self.write("s.txt", TEXT))
        text = schema_io.schema_text(s)
        # what the model reads leaves out every entry's source (where the idea came from), which says nothing to it
        self.assertTrue(s["sources"]["predicates"] and s["sources"]["patterns"])
        self.assertNotIn("source", text.lower())
        self.assertNotIn("mentor", text)
        again = schema_io.read_schema(self.write("t.txt", text))
        self.assertEqual(again["entity_classes"], s["entity_classes"])
        self.assertEqual(again["predicates"], s["predicates"])
        self.assertEqual(sorted(again["patterns"]), sorted(s["patterns"]))
        self.assertEqual(again["unread"], ["line 9: Each entry reads subject -> object, with its patterns (subject class -> object class)."])

    def test_hand_built_schema_reads_cleanly(self):
        s = schema_io.read_ground_truth_schema(HAND)
        self.assertGreater(len(s["entity_classes"]), 10)
        self.assertGreater(len(s["predicates"]), 10)
        for kind in ("entity_classes", "predicates"):
            for name, definition in s[kind].items():
                self.assertTrue(definition, f"{name} has no definition")
        names = set(s["entity_classes"])
        for subject_class, predicate, object_class in s["patterns"]:
            self.assertIn(predicate, s["predicates"])
            self.assertIn(subject_class, names, f"pattern {subject_class} {predicate} {object_class}")
            self.assertIn(object_class, names, f"pattern {subject_class} {predicate} {object_class}")
        self.assertFalse([u for u in s["unread"] if "repeats" in u], s["unread"])


class Additions(unittest.TestCase):

    def test_round_trip(self):
        entries = [{"entry_type": "entity class", "component_class": "Probe", "definition": "a small spacecraft",
                    "source": "mentor"},
                   {"entry_type": "predicate", "component_class": "CARRIES", "definition": "carries",
                    "source": "ground truth tuning #1", "patterns": [["Spacecraft", "Instrument"]]},
                   {"entry_type": "pattern", "subject_class": "Probe", "predicate": "ABOARD",
                    "object_class": "Mission", "source": "mentor"}]
        tmp = Path(tempfile.mkdtemp())
        try:
            path = tmp / "a.txt"
            path.write_text(schema_io.additions_text("# my notes\n# more\n", entries), encoding="utf-8")
            self.assertEqual(schema_io.additions_header(path), "# my notes\n# more\n")
            s = schema_io.read_schema(path)
            self.assertEqual(s["entity_classes"], {"Probe": "a small spacecraft"})
            self.assertEqual(s["predicates"], {"CARRIES": "carries"})
            self.assertEqual(s["patterns"], [("Spacecraft", "CARRIES", "Instrument"), ("Probe", "ABOARD", "Mission")])
            self.assertEqual(s["sources"], {"entity_classes": {"Probe": "mentor"},
                                            "predicates": {"CARRIES": "ground truth tuning #1"},
                                            "patterns": {"Probe ABOARD Mission": "mentor"}})
            self.assertEqual(s["unread"], [])
            empty = schema_io.additions_text("", [])
            path.write_text(empty, encoding="utf-8")
            self.assertEqual(schema_io.read_schema(path)["unread"], [])
        finally:
            shutil.rmtree(tmp)

    def test_source_rule(self):
        parts = {0: "tuning", 1: "tuning", 8: "held-out"}
        ok = ["mentor, 2026-10-01", "ground truth tuning #0, #1", "Ground-Truth tuning #1", ""]
        for source in ok:
            with self.subTest(source=source):
                self.assertIsNone(schema_io.ground_truth_source_problem(source, parts))
        bad = {"ground truth": "names no record", "ground_truth tuning #8": "held-out",
               "ground truth #1": "doesn't say tuning", "ground truth tuning #1, #99": "not a pool position",
               "groundtruth tuning #8": "held-out"}
        for source, why in bad.items():
            with self.subTest(source=source):
                self.assertIn(why, schema_io.ground_truth_source_problem(source, parts))


class HandSchemaEdits(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.path = self.tmp / "hand.txt"

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def start(self, text):
        self.path.write_bytes(text)
        return self.path.read_bytes()

    def test_adds_keep_bom_and_line_endings(self):
        for bom, newline in [(b"", "\n"), (b"\xef\xbb\xbf", "\r\n")]:
            with self.subTest(bom=bom, newline=newline):
                self.start(bom + TEXT.replace("\n", newline).encode("utf-8"))
                schema_io.add_to_ground_truth_schema(self.path, "entity class", "Probe", "a small  spacecraft", source="mentor")
                schema_io.add_to_ground_truth_schema(self.path, "predicate", "CARRIES", "carries",
                                             patterns=[("Spacecraft", "Instrument")], source="ground truth tuning #2")
                raw = self.path.read_bytes()
                self.assertEqual(raw.startswith(b"\xef\xbb\xbf"), bool(bom))
                text = raw.decode("utf-8-sig")
                self.assertEqual(text.count("\r\n") > 0, newline == "\r\n")
                if newline == "\r\n":
                    self.assertNotIn("\n", text.replace("\r\n", ""))
                s = schema_io.read_ground_truth_schema(self.path)
                self.assertEqual(s["entity_classes"]["Probe"], "a small spacecraft")
                self.assertEqual(list(s["entity_classes"])[-1], "Probe")
                self.assertIn(("Spacecraft", "CARRIES", "Instrument"), s["patterns"])
                self.assertEqual(s["sources"]["predicates"]["CARRIES"], "ground truth tuning #2")
                self.assertEqual(s["sources"]["predicates"]["HAS_PART"], "mentor, 2026-10-01")
                self.assertIn("Instrument -> Spacecraft; Instrument -> Mission", text)

    def test_refusals_leave_file_alone(self):
        before = self.start(TEXT.encode("utf-8"))
        refused = [lambda: schema_io.add_to_ground_truth_schema(self.path, "entity class", "instrument", "again"),
                   lambda: schema_io.add_to_ground_truth_schema(self.path, "entity class", "Two words", "d"),
                   lambda: schema_io.add_to_ground_truth_schema(self.path, "entity class", "A->B", "d"),
                   lambda: schema_io.add_to_ground_truth_schema(self.path, "entity class", "Probe", "  "),
                   lambda: schema_io.add_to_ground_truth_schema(self.path, "predicate", "P", "d", patterns=[("Two words", "X")])]
        for call in refused:
            with self.assertRaises(ValueError):
                call()
            self.assertEqual(self.path.read_bytes(), before)

    def test_anything_else_changing_restores(self):
        # A name that the reader would take as prose under the last entry
        # changes more than the one addition: the file is put back.
        before = self.start(TEXT.encode("utf-8"))
        real = schema_io._edit_text

        def sloppy(path, edit, expected, what):
            return real(path, lambda lines: edit(lines) + ["Stray  line"], expected, what)
        schema_io._edit_text = sloppy
        try:
            with self.assertRaisesRegex(ValueError, "left as it was"):
                schema_io.add_to_ground_truth_schema(self.path, "entity class", "Probe", "d")
        finally:
            schema_io._edit_text = real
        self.assertEqual(self.path.read_bytes(), before)
        self.assertFalse(list(self.tmp.glob("*.part")))

    def test_real_ground_truth_schema(self):
        shutil.copy2(HAND, self.path)
        before = schema_io.read_ground_truth_schema(self.path)
        schema_io.add_to_ground_truth_schema(self.path, "entity class", "TestProbe", "a test", source="ground truth tuning #0")
        schema_io.add_to_ground_truth_schema(self.path, "predicate", "TEST_CARRIES", "a test",
                                     patterns=[(next(iter(before["entity_classes"])),) * 2])
        after = schema_io.read_ground_truth_schema(self.path)
        self.assertEqual(len(after["entity_classes"]), len(before["entity_classes"]) + 1)
        self.assertEqual(len(after["predicates"]), len(before["predicates"]) + 1)
        self.assertEqual(len(after["unread"]), len(before["unread"]))
        self.assertEqual(HAND.read_bytes()[:3] == b"\xef\xbb\xbf", self.path.read_bytes()[:3] == b"\xef\xbb\xbf")



class ExtractionChecksPatternSources(unittest.TestCase):
    """Step 060 notes every entry of its schema file whose source names ground truth records other than tuning
    ones, patterns included (060_extract/060_extract_helpers/schema.py, load_schema)."""

    def test_held_out_pattern_noted(self):
        from support import use_step
        use_step("060_extract")
        import schema as extract_schema
        tmp = Path(tempfile.mkdtemp())
        try:
            hand = tmp / "hand.txt"
            hand.write_text(TEXT + "Dataset ABOARD Spacecraft\n                  source: ground truth held-out #8\n",
                            encoding="utf-8")                            # a pattern in the PATTERNS section
            (tmp / "additions.txt").write_text("", encoding="utf-8")
            pool = [{"id": f"r{i}", "position": i, "part": "held-out" if i == 8 else "tuning"} for i in range(10)]
            (tmp / "splits.json").write_text(json.dumps({"ground_truth_candidates": {"records": pool}}), encoding="utf-8")
            s = extract_schema.load_schema({"schema": hand, "additions": tmp / "additions.txt", "splits": tmp / "splits.json"})
            noted = [n for n in s.notes if "whose source names ground truth records" in n]
            self.assertEqual(len(noted), 1)
            self.assertIn("Dataset ABOARD Spacecraft (schema file;", noted[0])
        finally:
            shutil.rmtree(tmp)

class ExtractionKeepsPins(unittest.TestCase):
    """Step 060's merged schema keeps the "only:" lines of its schema file and of the additions file, in the merged
    schema's spelling; a pinned predicate of the additions file left out for not coming from tuning records takes
    its pins with it (060_extract/060_extract_helpers/schema.py, load_schema)."""

    def load(self, schema_text, additions_text):
        from support import use_step
        use_step("060_extract")
        import schema as extract_schema
        from common.validate import check_against_schema
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp)
        (tmp / "hand.txt").write_text(schema_text, encoding="utf-8")
        (tmp / "additions.txt").write_text(additions_text, encoding="utf-8")
        pool = [{"id": f"r{i}", "position": i, "part": "held-out" if i == 8 else "tuning"} for i in range(10)]
        (tmp / "splits.json").write_text(json.dumps({"ground_truth_candidates": {"records": pool}}), encoding="utf-8")
        s = extract_schema.load_schema({"schema": tmp / "hand.txt", "additions": tmp / "additions.txt",
                                        "splits": tmp / "splits.json"})
        flags = lambda sc, p, oc: check_against_schema({"subject_class": sc, "predicate": p, "object_class": oc},
                                                       s.schema_entries)
        return s, flags

    def test_schema_file_pins_kept(self):
        s, flags = self.load(TEXT.replace("HAS_PART          has as a part\n",
                                          "HAS_PART          has as a part\n                  only: Dataset -> any\n"), "")
        self.assertEqual(s.content["pinned"], {"HAS_PART": [("Dataset", "any")]})
        self.assertEqual(flags("Dataset", "HAS_PART", "Instrument"), [])
        self.assertEqual(flags("Instrument", "HAS_PART", "Dataset"), ["pattern_not_pinned"])
        self.assertIn("only: Dataset -> any", s.text)

    def test_additions_pins_kept_and_respelled(self):
        additions = ("PREDICATES\n----------\nhas_part          has as a part\n"
                     "                  only: dataset -> spacecraft\n                  source: mentor\n"
                     "ON_BOARD          is carried on\n                  only: Instrument -> Spacecraft\n"
                     "                  source: mentor\n")
        s, flags = self.load(TEXT, additions)
        self.assertEqual(s.content["pinned"], {"HAS_PART": [("Dataset", "Spacecraft")],
                                               "ON_BOARD": [("Instrument", "Spacecraft")]})
        self.assertEqual(flags("Dataset", "ON_BOARD", "Spacecraft"), ["pattern_not_pinned"])
        self.assertEqual(flags("Instrument", "ON_BOARD", "Spacecraft"), [])

    def test_held_out_pin_left_out(self):
        additions = ("PREDICATES\n----------\nON_BOARD          is carried on\n"
                     "                  only: Instrument -> Spacecraft\n                  source: ground truth held-out #8\n")
        s, _ = self.load(TEXT, additions)
        self.assertEqual(s.content["pinned"], {})
        self.assertEqual([x["entry_type"] for x in s.not_tuning], ["predicate"])    # as every output file writes it

    def test_pin_naming_unknown_entity_class_noted(self):
        additions = ("PREDICATES\n----------\nON_BOARD          is carried on\n"
                     "                  only: Instrumnet -> any\n                  source: mentor\n")
        s, _ = self.load(TEXT, additions)
        noted = [n for n in s.notes if "only:\" lines aren't in the schema" in n]
        self.assertEqual(len(noted), 1)
        self.assertIn("Instrumnet", noted[0])
        self.assertNotIn("any (", noted[0])

    def test_json_pins_read(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp)
        path = tmp / "s.json"
        path.write_text(json.dumps({"entity_classes": [{"component_class": "Dataset"}],
                                    "predicates": [{"component_class": "HAS_PART"}],
                                    "pinned": {"HAS_PART": [["Dataset", "any"]]}}), encoding="utf-8")
        self.assertEqual(schema_io.read_schema(path)["pinned"], {"HAS_PART": [("Dataset", "any")]})
        path.write_text(json.dumps({"entity_classes": [], "predicates": [], "pinned": {"HAS_PART": [["Dataset"]]}}),
                        encoding="utf-8")
        with self.assertRaises(ValueError):
            schema_io.read_schema(path)


if __name__ == "__main__":
    unittest.main()
