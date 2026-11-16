"""Reading and writing schemas (common/common_helpers/schema_io.py): both
shapes, the additions file, the source rule for additions, and the careful
edits the annotation tool makes to the ground truth schema."""
import json
import re
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
        self.assertNotIn("only:", schema_io.schema_text(s))         # a prompt never shows the pins; the checks use them
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
        # only entity classes and predicates with their definitions: no pattern, no pin (decided 2026-11-15)
        self.assertTrue(s["patterns"])
        self.assertEqual(again["patterns"], [])
        self.assertEqual(again["pinned"], {})
        self.assertNotIn("->", text)
        self.assertEqual(again["unread"], ["line 9: " + schema_io.READS])
        self.assertEqual(schema_io.schema_text(again), text)                 # written the same way again

    def test_schema_text_near_misses(self):
        """A pinned predicate with no pattern, a pattern whose predicate isn't in the schema, a predicate without a
        definition: none puts anything but entity classes and predicates with their definitions in the text."""
        s = {"entity_classes": {"Dataset": "a set of data", "Instrument": ""},
             "predicates": {"ACQUIRED_BY": "was collected by this Instrument", "BARE": ""},
             "patterns": [("Dataset", "ACQUIRED_BY", "Instrument"), ("Dataset", "MISSING", "Instrument")],
             "pinned": {"ACQUIRED_BY": [("any", "Instrument")], "BARE": [("Dataset", "Dataset")]}}
        text = schema_io.schema_text(s)
        self.assertEqual(text.splitlines(), [
            "ENTITY CLASSES", "--------------", "Dataset      a set of data", "Instrument",
            "", "PREDICATES", "----------", schema_io.READS, "",
            "ACQUIRED_BY  was collected by this Instrument", "BARE"])

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


class RuleNineteenMarks(unittest.TestCase):
    """The "rule 19:" lines of a schema in the text shape: an entity class's mark (standalone or describing) and a qualifier
    predicate's kind, read; a bad or second line is not read, and says why; a rename carries the mark along."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_read_and_near_misses(self):
        pad, nl = " " * 18, chr(10)
        marks = {"Spacecraft        a vehicle in space": ["rule 19: standalone", "rule 19: describing"],   # a second line
                 "Dataset           a collection of data": ["rule 19: standalones"],                    # not a mark
                 "HAS_PART          has as a part": ["rule 19: qualifier, a part"],
                 "ABOARD            is carried on": ["rule 19: qualifier"]}                        # no kind
        text = TEXT
        for entry, added in marks.items():
            text = text.replace(entry + nl, entry + nl + "".join(pad + a + nl for a in added))
        path = self.tmp / "s.txt"
        path.write_text(text, encoding="utf-8")
        s = schema_io.read_schema(path)
        self.assertEqual(s["rule_19_classes"], {"Spacecraft": "standalone"})            # the second line isn't read
        self.assertEqual(s["rule_19_predicates"], {"HAS_PART": "a part"})          # "qualifier" alone names no kind
        self.assertEqual(schema_io.qualifier_predicates(s), ("HAS_PART",))
        bad = [u for u in s["unread"] if "rule 19" in u]
        self.assertEqual(len(bad), 3, bad)
        self.assertTrue(any("a second rule 19 line" in u for u in bad))
        path.write_bytes(schema_io.rename_in_ground_truth_schema(path, "entity class", "Spacecraft", "Craft")[0])
        self.assertEqual(schema_io.read_schema(path)["rule_19_classes"], {"Craft": "standalone"})
        path.write_bytes(schema_io.rename_in_ground_truth_schema(path, "predicate", "HAS_PART", "HAS_PIECE")[0])
        self.assertEqual(schema_io.read_schema(path)["rule_19_predicates"], {"HAS_PIECE": "a part"})
        schema_io.add_to_ground_truth_schema(path, "entity class", "Probe", "a small craft")
        self.assertNotIn("Probe", schema_io.read_schema(path)["rule_19_classes"])  # a new one has no mark yet

    def test_ground_truth_schema(self):
        """Every entity class of the ground truth schema has exactly one mark, standalone or describing; every qualifier
        predicate is a predicate of it; and their kinds are exactly the kinds rule 19's first sentence lists
        (annotations/guidelines.md), so the rule and the schema can't drift apart."""
        import re
        s = schema_io.read_ground_truth_schema(HAND)
        missing = [n for n in s["entity_classes"] if n not in s["rule_19_classes"]]
        self.assertEqual(missing, [], "add a line \"rule 19: standalone\" or \"rule 19: describing\" under each of these "
                         "entity classes in annotations/ground_truth_schema.txt (rule 19 of Writing a classed triple, "
                         "annotations/guidelines.md: Whose fact it is)")
        self.assertEqual([u for u in s["unread"] if "rule 19 line" in u or "not a rule 19 mark" in u], [])
        self.assertEqual(set(s["rule_19_classes"]), set(s["entity_classes"]))
        self.assertTrue(set(s["rule_19_classes"].values()) <= {"standalone", "describing"})
        for p in schema_io.qualifier_predicates(s):
            self.assertIn(p, s["predicates"])
        rule = re.search(r"^19\. \*\*A qualifier that is (.+?) is a ground truth triple of its own",
                         (ROOT / "annotations" / "guidelines.md").read_text(encoding="utf-8"), re.M).group(1)
        kinds = [k.strip() for k in re.split(r", or |, ", rule)]
        self.assertEqual(sorted(s["rule_19_predicates"].values()), sorted(kinds))

    def test_no_code_keeps_its_own_list(self):
        """No code outside the schema lists the qualifier predicates itself (one home: the schema's rule 19 lines).
        A near miss, one or two of them on a line, is ordinary use and isn't flagged."""
        s = schema_io.read_ground_truth_schema(HAND)
        names = schema_io.qualifier_predicates(s)
        found = []
        for path in ROOT.rglob("*.py"):
            rel = path.relative_to(ROOT).as_posix()
            if rel.startswith(("archive/", "to_be_reshaped/", "tests/", "outputs/", ".myvenv/")) or "/." in rel:
                continue
            for n, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                if sum(f'"{q}"' in line for q in names) >= 3:
                    found.append(f"{rel}:{n}")
        self.assertEqual(found, [], "read the qualifier predicates with schema_io.qualifier_predicates instead")


#: Where a predicate's definition names its object's entity class: "this Instrument", "this Person or Organization",
#: or "(a Time)" after the words it explains ("on this date (a Time)").
NAMED_CLASS = __import__("re").compile(r"\bthis ([A-Z][A-Za-z]*(?: or [A-Z][A-Za-z]*)*)|\(an? ([A-Z][A-Za-z]*)\)")


def unpinned(schema: dict) -> list:
    """The predicates whose definition names an entity class of the schema as its object without a pin to it
    ("only: ... -> that entity class"), as "PREDICATE: EntityClass, ..."; a capitalized word that is no entity class is
    ignored."""
    out = []
    for predicate, definition in schema["predicates"].items():
        named = [w for m in NAMED_CLASS.finditer(definition) for w in (m.group(1) or m.group(2)).split(" or ")
                 if w in schema["entity_classes"]]
        pinned = {o for _, o in schema["pinned"].get(predicate, [])}
        missing = [c for c in named if c not in pinned]
        if missing:
            out.append(f"{predicate}: {', '.join(missing)}")
    return out


class RuleNineteenMarksInPrompts(unittest.TestCase):
    """Which prompts show the rule 19 marks (decided 2026-11-15, docs/improvements.md): those that write or check the
    ground truth (050's drafting; the second opinion, which drafts with 050's prompt; the second judge) show each
    entity class's mark on a line under it, as the ground truth schema's file writes it, in their schema and in the
    worked examples' example schema; extraction (060) never shows them, with the ground truth schema or any other.
    Patterns and pins stay out of every prompt."""

    MARK = re.compile(r"^ +rule 19: (?:standalone|describing)$", re.M)

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)

    @staticmethod
    def module(name: str, path: Path):
        import importlib.util
        import sys
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module

    def test_schema_text_near_misses(self):
        s = {"entity_classes": {"Dataset": "a set of data", "Purpose": "what something is for", "Probe": "a small craft"},
             "predicates": {"BASED_IN": "is based in this place"},
             "patterns": [("Dataset", "BASED_IN", "Purpose")], "pinned": {"BASED_IN": [("any", "Purpose")]},
             "rule_19_classes": {"Dataset": "standalone", "Purpose": "describing", "Ghost": "standalone"},
             "rule_19_predicates": {"BASED_IN": "a country"}}
        plain = schema_io.schema_text(s)
        self.assertEqual(plain, schema_io.schema_text(s, rule_19_marks=False))         # the default: no marks
        self.assertNotIn("rule 19", plain)
        marked = schema_io.schema_text(s, rule_19_marks=True)
        self.assertEqual(marked.splitlines(), [
            "ENTITY CLASSES", "--------------", schema_io.MARKS_READ, "",
            "Dataset   a set of data", "          rule 19: standalone",
            "Purpose   what something is for", "          rule 19: describing",
            "Probe     a small craft",                    # no mark in the file: no line, and MARKS_READ says to decide
            "", "PREDICATES", "----------", schema_io.READS, "",
            "BASED_IN  is based in this place"])           # a qualifier predicate's mark, a pattern, a pin: never shown
        self.assertNotIn("Ghost", marked)                   # a mark of an entity class the schema doesn't have
        path = self.tmp / "marked.txt"
        path.write_text(marked, encoding="utf-8")
        again = schema_io.read_schema(path)                 # read back: the file's own marks, the same texts
        self.assertEqual(again["rule_19_classes"], {"Dataset": "standalone", "Purpose": "describing"})
        self.assertEqual(schema_io.schema_text(again, rule_19_marks=True), marked)
        self.assertEqual(schema_io.schema_text(again), plain)
        bare = {"entity_classes": {"Dataset": "a set of data"}, "predicates": {}}   # no marks at all (a JSON schema)
        self.assertEqual(self.MARK.findall(schema_io.schema_text(bare, rule_19_marks=True)), [])

    def test_which_prompts_show_them(self):
        from support import use_step
        from common import dropped, extraction
        from common.ground_truth import GROUND_TRUTH_SCHEMA
        dropped.reset()
        self.addCleanup(dropped.reset)
        shown = schema_io.without_held_out_only(schema_io.read_ground_truth_schema(GROUND_TRUTH_SCHEMA))
        marks = len(shown["rule_19_classes"])
        self.assertGreater(marks, 10)                       # marks to show, or the checks below would prove nothing
        example = len(schema_io.read_schema(extraction.EXAMPLE_SCHEMA.path)["rule_19_classes"])
        self.assertGreater(example, 10)
        record = {"id": "r0", "title": "Kestrel Lake Ice L2", "notes": "Made by the Tern algorithm."}
        (self.tmp / "records.jsonl").write_text(json.dumps(record) + "\n", encoding="utf-8")
        pool = [{"id": "r0", "position": 0, "part": "tuning"}]
        (self.tmp / "splits.json").write_text(json.dumps({"ground_truth_candidates": {"records": pool}}),
                                              encoding="utf-8")
        (self.tmp / "ground_truth").mkdir()
        (self.tmp / "additions.txt").write_text("", encoding="utf-8")
        piece = "title: Kestrel Lake Ice L2"

        # 050's drafting, which the second opinion uses as it is: the ground truth schema and the example schema marked
        records_050 = self.module("records_050_marks", ROOT / "050_annotate" / "050_annotate_helpers" / "records.py")
        draft_050 = self.module("draft_050_marks", ROOT / "050_annotate" / "050_annotate_helpers" / "draft.py")
        chosen, _ = records_050.read_inputs({"records": self.tmp / "records.jsonl", "splits": self.tmp / "splits.json",
                                             "ground_truth": self.tmp / "ground_truth" / "batch_*.csv",
                                             "ground_truth_schema": GROUND_TRUTH_SCHEMA})
        self.assertIn(schema_io.schema_text(shown, rule_19_marks=True), chosen.schema_text)
        drafting = draft_050.prompt_for(chosen)({"id": "r0"}, piece)
        self.assertIn(chosen.schema_text, drafting)
        self.assertIn(extraction.examples_text(rule_19_marks=True), drafting)
        self.assertEqual(len(self.MARK.findall(drafting)), marks + example)
        self.assertEqual(drafting.count(schema_io.MARKS_READ), 2)

        # the second judge: the ground truth schema as 050 shows it, marked
        judge = self.module("second_judge_marks", ROOT / "helpers" / "second_judge.py")
        row = {"id": "r0", "subject": "Kestrel Lake Ice L2", "subject_class": "Dataset", "predicate": "P",
               "object": "Tern", "object_class": "Algorithm", "source_text": "Made by the Tern algorithm."}
        judging = judge.facts_prompt(chosen, [], "GUIDELINES", row)
        self.assertIn(chosen.schema_text, judging)
        self.assertEqual(len(self.MARK.findall(judging)), marks)

        # 060's extraction: no mark, with the ground truth schema (a copy: the same content) or any other schema
        use_step("060_extract")
        import schema as extract_schema
        extract_060 = self.module("extract_060_marks", ROOT / "060_extract" / "060_extract_helpers" / "extract.py")
        copy = self.tmp / "copy_of_the_ground_truth_schema.txt"
        shutil.copy2(GROUND_TRUTH_SCHEMA, copy)
        other = self.tmp / "other.txt"            # near miss: a schema file with marks that isn't the ground truth's
        other.write_text(schema_io.schema_text({**shown, "entity_classes": {**shown["entity_classes"], "Extra": "x"}},
                                               rule_19_marks=True), encoding="utf-8")
        induced = self.tmp / "the_schema.json"
        induced.write_text(json.dumps({"entity_classes": [{"component_class": "Dataset", "definition": "a set"}],
                                       "predicates": [{"component_class": "P", "definition": "has"}]}),
                           encoding="utf-8")
        for path, ground_truth in ((copy, True), (other, False), (induced, False)):
            with self.subTest(schema=path.name):
                s = extract_schema.load_schema({"schema": path, "additions": self.tmp / "additions.txt",
                                                "splits": self.tmp / "splits.json",
                                                "ground_truth": self.tmp / "ground_truth" / "batch_*.csv"})
                self.assertEqual(s.ground_truth, ground_truth)
                extracting = extraction.prompt(extract_060.PROMPT, s.text, record, piece,
                                               **extraction.task_parts(extraction.SCOPE_SCHEMA))
                self.assertEqual(self.MARK.findall(extracting), [])
                self.assertNotIn(schema_io.MARKS_READ, extracting)
                self.assertIn(extraction.examples_text(), extracting)        # the example schema unmarked too


class PinsFollowDefinitions(unittest.TestCase):
    """The ground truth schema's rule "A predicate whose definition names its object's entity class is pinned to it"
    (annotations/ground_truth_schema.txt, PREDICATES), checked: every such predicate has a pin to each entity class
    its definition names, so a definition and its pin can't drift apart."""

    def test_near_misses(self):
        text = """ENTITY CLASSES
--------------
Grid              a fixed set of cells
Time              a point or period on the calendar
Person            one named human being
Organization      a named institution

PREDICATES
----------
IN_GRID           its values were collected into this Grid
                  only: any -> Grid
IN_GRID_2         its values were collected into this Grid
STARTED_ON        started on this date (a Time)
RUN_BY            is run by this Person or Organization
                  only: any -> Person
REPLACES          replaces this earlier one
ABOUT             is about this Topic
LIKE_A_GRID       looks like a Grid (IN_GRID)
"""
        tmp = Path(tempfile.mkdtemp())
        try:
            path = tmp / "s.txt"
            path.write_text(text, encoding="utf-8")
            s = schema_io.read_schema(path)
        finally:
            shutil.rmtree(tmp)
        self.assertEqual(unpinned(s), ["IN_GRID_2: Grid", "STARTED_ON: Time", "RUN_BY: Organization"])

    def test_ground_truth_schema(self):
        s = schema_io.read_ground_truth_schema(HAND)
        self.assertEqual(unpinned(s), [], "add a line \"only: any -> <entity class>\" under each of these predicates "
                         "in annotations/ground_truth_schema.txt, or reword its definition")


#: The entity classes an "only:" line names (other than "any") that its predicate's definition doesn't name, as
#: "PREDICATE: EntityClass, ...": the converse of unpinned. The check is shared with 040's defining (stage 7), which
#: asks a pinned predicate's definition to name its pin: common/common_helpers/schema_io.py, unnamed_pinned.
pins_not_in_definition = schema_io.pins_not_in_definition


class DefinitionsNamePins(unittest.TestCase):
    """The converse of PinsFollowDefinitions: every entity class on a predicate's "only:" line (other than "any")
    appears in that predicate's definition in the ground truth schema. No prompt shows the pins (common/common_helpers/
    schema_io.schema_text), so the definition, the one home of a predicate's meaning, must say what the pin allows."""

    def test_near_misses(self):
        text = """ENTITY CLASSES
--------------
Grid              a fixed set of cells
Channel           a range of wavelengths
Instrument        a device
Person            one named human being
Organization      a named institution

PREDICATES
----------
ON_GRID           its values are given on this Grid
                  only: any -> Grid
GRIDDED_AS        its values are gridded
                  only: any -> Grid
ON_A_GRID         its values are given on a grid
                  only: any -> Grid
CHANNEL_OF        is one of the Channels this Instrument measures in
                  only: Channel -> Instrument
RUN_BY            is run by this Person
                  only: any -> Organization; any -> Person
LED_BY            is led by this Person or Organization
                  only: any -> Organization; any -> Person
"""
        tmp = Path(tempfile.mkdtemp())
        try:
            path = tmp / "s.txt"
            path.write_text(text, encoding="utf-8")
            s = schema_io.read_schema(path)
        finally:
            shutil.rmtree(tmp)
        self.assertEqual(pins_not_in_definition(s), ["GRIDDED_AS: Grid", "ON_A_GRID: Grid", "RUN_BY: Organization"])

    def test_ground_truth_schema(self):
        s = schema_io.read_ground_truth_schema(HAND)
        self.assertEqual(len(s["pinned"]), 64)                  # every pinned predicate is checked, held-out only too
        self.assertEqual(pins_not_in_definition(s), [], "name each of these entity classes in the predicate's "
                         "definition in annotations/ground_truth_schema.txt (e.g. \"this Purpose\", \"(a Time)\"), "
                         "or correct its \"only:\" line")


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

class ExtractionWithTheGroundTruthSchema(unittest.TestCase):
    """Step 060 given the ground truth schema (annotations/ground_truth_schema.txt, or a copy of it anywhere: the
    same content) extracts with the one view every step uses (ground_truth_schema_view, in
    common/common_helpers/ground_truth.py): its file's patterns, then those the finished tuning records use, never a draft's or a
    held-out record's; and it knows which records the schema was learned from. A file that differs in one definition
    is another schema."""

    def test_patterns_and_learned_from(self):
        import csv
        from support import use_step
        use_step("060_extract")
        import schema as extract_schema
        from common.ground_truth import COLUMNS, GROUND_TRUTH_SCHEMA
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp)
        copy = tmp / "copy_of_the_ground_truth_schema.txt"
        # the ground truth schema 060 compares with: the real file, or, when the annotation tool's tests run first in
        # this process, their temporary copy (support.temp_repo leaves out the held-out-only entries)
        shutil.copy2(GROUND_TRUTH_SCHEMA, copy)
        (tmp / "additions.txt").write_text("", encoding="utf-8")
        pool = [{"id": f"r{i}", "position": i, "part": "held-out" if i == 8 else "tuning"} for i in range(10)]
        (tmp / "splits.json").write_text(json.dumps({"ground_truth_candidates": {"records": pool}}), encoding="utf-8")
        (tmp / "ground_truth").mkdir()
        hand = schema_io.read_ground_truth_schema(GROUND_TRUTH_SCHEMA)
        a, b = sorted(hand["entity_classes"])[:2]
        p = sorted(hand["predicates"])[0]
        new = [(a, p, b), (b, p, a), (a, p, a)]
        self.assertFalse(set(new) & set(hand["patterns"]))                 # three patterns the file lacks
        with open(tmp / "ground_truth" / "batch_000.csv", "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(COLUMNS)
            for rid, (s_, p_, o_), mark in (("r1", new[0], "1"), ("r2", new[1], "0"), ("r8", new[2], "1")):
                w.writerow([rid, "x", s_, p_, "y", o_, "x y", mark])      # finished tuning; unfinished; held-out
        inputs = {"schema": copy, "additions": tmp / "additions.txt", "splits": tmp / "splits.json",
                  "ground_truth": tmp / "ground_truth" / "batch_*.csv"}
        s = extract_schema.load_schema(inputs)
        self.assertIn(new[0], s.content["patterns"])
        self.assertNotIn(new[1], s.content["patterns"])
        self.assertNotIn(new[2], s.content["patterns"])
        self.assertTrue(s.learned_from["known"])
        # learned from: the finished tuning records (r1 here; not r2, unfinished, nor r8, held-out), plus the pool
        # positions the file's source lines name
        parts = {r["position"]: r["part"] for r in pool}
        named = {f"r{n}" for of_kind in hand["sources"].values() for source in of_kind.values()
                 for key in ("tuning", "held_out") for n in schema_io.parse_source(source, parts)[key] if n in parts}
        self.assertEqual(set(s.learned_from["ids"]), {"r1"} | named)
        self.assertTrue(any("finished tuning records" in h for h in s.learned_from["how"]))
        # the near miss: one definition changed, so it is another schema (the patterns its own, learned from unknown)
        copy.write_text(copy.read_text(encoding="utf-8-sig").replace(hand["predicates"][p], "something else", 1),
                        encoding="utf-8")
        s = extract_schema.load_schema(inputs)
        self.assertNotIn(new[0], s.content["patterns"])
        self.assertFalse(s.learned_from["known"])


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
        self.assertNotIn("only:", s.text)                       # kept for the checks, never shown (2026-11-15)

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

    def test_left_out_entries_recorded(self):
        """Every additions entry 060 leaves out is one entry of the record of discarded items
        (common/common_helpers/dropped.py): one already in the schema (folded into it), one from a held-out record
        with its pin, an unread line; the accounting check stops the run when one vanishes without a record."""
        from unittest import mock
        from common import dropped
        from common.stop import Stop
        dropped.reset()
        self.addCleanup(dropped.reset)
        additions = ("PREDICATES\n----------\nhas_part          has as a part\n                  source: mentor\n"
                     "ON_BOARD          is carried on\n                  only: Instrument -> Spacecraft\n"
                     "                  source: ground truth held-out #8\n"
                     "NOT AN ENTRY      two words\n")
        s, _ = self.load(TEXT, additions)
        got = sorted((e["action"], e["item_type"], e["item"].get("schema_entry") or e["item"].get("predicate")
                      or e["item"].get("line")) for e in dropped.DISCARDS)
        self.assertIn(("folded", "schema entry", "has_part"), got)
        self.assertIn(("discarded", "schema entry", "ON_BOARD"), got)
        self.assertIn(("discarded", "pinned predicate", "ON_BOARD"), got)
        self.assertTrue(any(t == "line of a schema file" and "NOT AN ENTRY" in str(w) for _, t, w in got), got)
        folded = next(e for e in dropped.DISCARDS if e["action"] == "folded" and e["item_type"] == "schema entry")
        self.assertEqual(folded["kept_as"], {"schema_entry": "HAS_PART"})
        with mock.patch.object(dropped, "fold", lambda *a, **k: None), self.assertRaises(Stop) as caught:
            self.load(TEXT, additions)
        self.assertIn("Accounting check failed in stage 2 (load_schema): 2 predicate entries of the additions file "
                      "went in, 0 were kept and 1 were recorded", str(caught.exception))

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


class HeldOutOnly(unittest.TestCase):
    """Held-out-only entries (docs/terminology.md, *held-out-only entry*): the line "held-out only" under an entity
    class or a predicate, read, written, kept by a rename, dropped by Unmark, and left out of what models see."""
    TEXT = "\n".join(["ENTITY CLASSES", "--------------",
                      "Instrument        a device",
                      "Moonlet           a small moon",
                      "                  Held-Out   only",
                      "                  source: ground truth held-out #8",
                      "Spacecraft        a vehicle",
                      "", "PREDICATES", "----------",
                      "ABOARD            is carried on",
                      "                  Instrument -> Spacecraft; Instrument -> Moonlet",
                      "                  only: Instrument -> Spacecraft; any -> Moonlet",
                      "ORBITS            goes around",
                      "                  held-out only",
                      "                  held-out only",
                      "                  rule 19: qualifier, a target body",
                      "                  Moonlet -> Spacecraft",
                      "                  source: ground truth held-out #8, #11",
                      "", "PATTERNS", "--------",
                      "Moonlet ABOARD Spacecraft",
                      "                  held-out only",
                      "                  source: mentor",
                      "Instrument ABOARD Spacecraft", ""])

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.path = self.tmp / "ground_truth_schema.txt"
        self.path.write_text(self.TEXT, encoding="utf-8")

    def test_read(self):
        s = schema_io.read_ground_truth_schema(self.path)
        self.assertEqual(s["held_out_only"], {"entity_classes": {"Moonlet"}, "predicates": {"ORBITS"}})
        unread = [u.split(": ", 1)[1] for u in s["unread"]]
        self.assertIn("held-out only (a second held-out only line; the first is kept)", unread)   # a second line
        self.assertIn("held-out only", unread)                                    # under a pattern entry: not read
        self.assertTrue(schema_io.is_held_out_only(s, "entity class", "moonlet"))   # any spelling
        self.assertFalse(schema_io.is_held_out_only(s, "predicate", "ABOARD"))      # near miss: not marked

    def test_without_held_out_only(self):
        s = schema_io.read_ground_truth_schema(self.path)
        w = schema_io.without_held_out_only(s)
        self.assertEqual((list(w["entity_classes"]), list(w["predicates"])), (["Instrument", "Spacecraft"], ["ABOARD"]))
        self.assertEqual(w["patterns"], [("Instrument", "ABOARD", "Spacecraft"), ("Instrument", "ABOARD", "Spacecraft")])
        self.assertEqual(w["pinned"], {"ABOARD": [("Instrument", "Spacecraft")]})      # the pin naming Moonlet goes
        self.assertEqual((w["rule_19_predicates"], w["sources"]["entity_classes"], w["sources"]["predicates"]),
                         ({}, {}, {}))
        self.assertEqual(w["sources"]["patterns"], {})                               # Moonlet ABOARD Spacecraft's
        self.assertEqual(s["entity_classes"]["Moonlet"], "a small moon")             # the original is left alone
        unmarked = {**s, "held_out_only": {"entity_classes": set(), "predicates": set()}}
        self.assertIs(schema_io.without_held_out_only(unmarked), unmarked)           # nothing marked: the same
        text = schema_io.schema_text(w)                                        # what 050's prompt shows of it
        for gone in ("Moonlet", "ORBITS", "held-out"):
            self.assertNotIn(gone, text, gone)
        self.assertIn("Instrument", text)

    def test_source_line(self):
        self.assertEqual(schema_io.source_line([3], [8, 8]), "ground truth tuning #3; held-out #8")
        self.assertEqual(schema_io.source_line((), [11, 8]), "ground truth held-out #8, #11")
        self.assertEqual(schema_io.source_line([], []), "")
        found = schema_io.parse_source("ground truth tuning #3; held-out #8", {3: "tuning", 8: "held-out"})
        self.assertEqual((found["tuning"], found["held_out"]), ([3], [8]))

    def test_add_rename_unmark(self):
        schema_io.add_to_ground_truth_schema(self.path, "entity class", "Comet", "a comet", source="ground truth held-out #8",
                                             held_out_only=True)
        text = self.path.read_text(encoding="utf-8")
        self.assertIn("Comet             a comet\n                  held-out only\n                  source: ground truth "
                      "held-out #8\n", text)
        s = schema_io.read_ground_truth_schema(self.path)
        self.assertEqual(s["held_out_only"]["entity_classes"], {"Moonlet", "Comet"})
        schema_io.add_to_ground_truth_schema(self.path, "entity class", "Asteroid", "a rock")   # near miss: unmarked
        self.assertNotIn("Asteroid", schema_io.read_ground_truth_schema(self.path)["held_out_only"]["entity_classes"])
        data, how = schema_io.rename_in_ground_truth_schema(self.path, "entity class", "Comet", "IcyBody")
        self.path.write_bytes(data)
        self.assertEqual(how, "renamed")
        s = schema_io.read_ground_truth_schema(self.path)
        self.assertEqual(s["held_out_only"]["entity_classes"], {"Moonlet", "IcyBody"})     # the mark follows the name
        data, how = schema_io.rename_in_ground_truth_schema(self.path, "entity class", "IcyBody", "Moonlet")
        self.path.write_bytes(data)
        self.assertEqual(how, "merged")
        self.assertEqual(schema_io.read_ground_truth_schema(self.path)["held_out_only"]["entity_classes"], {"Moonlet"})
        self.path.write_bytes(schema_io.unmark_held_out_only(self.path, "entity class", "Moonlet", [3], [8]))
        s = schema_io.read_ground_truth_schema(self.path)
        self.assertEqual(s["held_out_only"]["entity_classes"], set())
        self.assertEqual(s["sources"]["entity_classes"]["Moonlet"], "ground truth tuning #3; held-out #8")
        self.assertEqual(s["entity_classes"]["Moonlet"], "a small moon")
        with self.assertRaises(ValueError):                                          # no longer marked
            schema_io.unmark_held_out_only(self.path, "entity class", "Moonlet", [3])
        with self.assertRaises(ValueError):                                          # no tuning record to name
            schema_io.unmark_held_out_only(self.path, "predicate", "ORBITS", [])


if __name__ == "__main__":
    unittest.main()
