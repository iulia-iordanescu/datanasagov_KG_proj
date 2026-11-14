"""The rules each ground truth triple uses (common/common_helpers/rules_by_triple.py, py helpers/rules_by_triple.py):
the real ground truth files have the column rules, every value is rule numbers the guidelines have, ascending, each
once, never on a describes triple or on a record that states no facts, and annotations/rules_by_triple.md is what the
files and the guidelines give now (the failure names the command); the value's near misses; the doc's shape on a
made-up case; and the drafted values merged into the files, each row checked against the ground truth row at its
position, every mismatch refused with nothing written. The real files are only read."""
import csv
import re
import shutil
import tempfile
import unittest
from pathlib import Path

from support import ROOT  # noqa: F401  (imported first: it refuses any change to the real annotations/)
from common.expert_questions import guideline_rules
from common.ground_truth import FILE_COLUMNS, RULES
from common.left_out import rule_quote_problems
from common.rules_by_triple import (ALWAYS, COMMAND, DESCRIBES_SECTION, DOC_PATH, DRAFT_COLUMNS, GUIDELINES_PATH, doc_text,
                                    file_problems, format_rules, guideline_section, merge_drafts, parse_rules, rule_count,
                                    rule_texts, rules_problem, write_doc)

class LeftOutQuotes(unittest.TestCase):
    """Each Rule line of annotations/left_out.md quotes the rule it names as annotations/guidelines.md has it now."""

    def test_the_real_file(self):
        self.assertEqual(rule_quote_problems(), [])

    def test_near_misses(self):
        tmp = Path(tempfile.mkdtemp())
        g, lo = tmp / "guidelines.md", tmp / "left_out.md"
        g.write_text("## What counts as a fact" + chr(10) * 2 + "1. **Only what the record states.** Never add what you know." + chr(10),
                     encoding="utf-8")
        lines = ['  - **Rule:** What counts as a fact, rule 1: "Never add what you know." A note.',      # fine
                 '  - **Rule:** What counts as a fact, rule 1: "Never add what you knew." A note.',      # a word changed
                 '  - **Rule:** What counts as a fact, rule 2: "Never add what you know."',               # no rule 2
                 '  - **Rule:** What counts as a fact, rule 1: "Never add" what you know.']               # too short
        lo.write_text(chr(10).join(lines) + chr(10), encoding="utf-8")
        found = rule_quote_problems(lo, g)
        self.assertEqual([p.split(":")[1] for p in found], ["2", "3", "4"])


GUIDELINES = """# Annotation guidelines

## What counts as a fact

1. **Only what the record states.** Never add what you know.
2. **Every fact the record states.** All of them.
3. **Not opinions.** Leave out "great".
    - **A sub-rule.** Its words, with a [link](../docs/terminology.md#2-triples).

## Writing a classed triple

4. **One fact per triple.** Two facts, two triples.

## The describes triple

Every record has one classed triple that no text states, written by code.

## Finishing a record

- **Commit.**
"""
LEFT_OUT = """# Left out on purpose

Intro.

## "Title r1" (pool position 3, id r1)

1 item, none that may matter.

- **Left out:** "great" (notes)
  - **Rule:** What counts as a fact, rule 3: "Leave out "great"."
"""


def gt_row(rid, s, sc, p, o, oc, source, mark="1", rules=""):
    return {"id": rid, "subject": s, "subject_class": sc, "predicate": p, "object": o, "object_class": oc,
            "source_text": source, "all_facts_extracted": mark, "drafted_by": "m", RULES: rules}


def describes(rid, title, mark="1"):
    return gt_row(rid, rid, "CatalogEntry", "DESCRIBES", title, "Dataset", "(record structure)", mark)


def write_csv(path, columns, rows):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, columns, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def read_csv(path):
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


class RealFiles(unittest.TestCase):
    """The real ground truth files and the real doc, read only."""

    def test_the_column_and_its_values(self):
        for path in sorted((ROOT / "annotations" / "ground_truth").glob("batch_*.csv")):
            with self.subTest(file=path.name):
                with open(path, encoding="utf-8-sig", newline="") as fh:
                    header = next(csv.reader(fh))
                self.assertEqual(header[-1], RULES, f"{path.name}: the column {RULES} must be last")
        self.assertEqual(file_problems(), [])

    def test_the_doc_is_in_step(self):
        self.assertTrue(DOC_PATH.exists(), f"annotations/{DOC_PATH.name} is missing: run `{COMMAND}`")
        now = DOC_PATH.read_text(encoding="utf-8")
        self.assertEqual(now, doc_text(), f"annotations/{DOC_PATH.name} is out of step with the ground truth files, "
                                          f"annotations/guidelines.md or annotations/left_out.md: run `{COMMAND}`")

    def test_the_guidelines_read_as_before(self):
        """rule_texts and guideline_rules read the same rules (one reader: guideline_rule_lines)."""
        texts, words = rule_texts(), guideline_rules()
        self.assertEqual(sorted(texts), sorted(n for _, n in words))
        self.assertEqual(sorted(texts), list(range(1, rule_count() + 1)))
        for (section, n), plain in words.items():
            self.assertEqual(texts[n]["section"], section)
            self.assertTrue(texts[n]["title"], n)
            title = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", texts[n]["title"]).replace("`", "").replace("*", "")
            self.assertTrue(plain.startswith(title[:20]), (n, title, plain[:40]))
        self.assertTrue(all(n in texts for n in ALWAYS))
        self.assertIn("written by code", guideline_section(DESCRIBES_SECTION))


class Values(unittest.TestCase):

    def test_parse(self):
        self.assertEqual(parse_rules("", 24), [])
        self.assertEqual(parse_rules("  ", 24), [])
        self.assertEqual(parse_rules("1", 24), [1])
        self.assertEqual(parse_rules("1, 19, 24", 24), [1, 19, 24])
        for bad in ("19, 1", "1,19", "1, 1", "25", "0", "a", "1, ", ", 1", "1;19", "rule 1"):
            with self.subTest(value=bad):
                with self.assertRaises(ValueError) as e:
                    parse_rules(bad, 24)
                self.assertIn(bad.strip() or bad, str(e.exception))
        self.assertEqual(format_rules([19, 1, 19]), "1, 19")
        self.assertEqual(format_rules([]), "")

    def test_rules_problem(self):
        triple = gt_row("r", "MODIS", "Instrument", "ABOARD", "Aqua", "Platform", "x")
        self.assertIsNone(rules_problem({**triple, RULES: ""}, 24))
        self.assertIsNone(rules_problem({**triple, RULES: "1, 19"}, 24))
        self.assertIn("isn't ascending", rules_problem({**triple, RULES: "19, 1"}, 24))
        self.assertIn("rules 1 to 24", rules_problem({**triple, RULES: "25"}, 24))
        self.assertIsNone(rules_problem({**describes("r", "T"), RULES: ""}, 24))
        self.assertIn(DESCRIBES_SECTION, rules_problem({**describes("r", "T"), RULES: "1"}, 24))
        blank = gt_row("r", "", "", "", "", "", "")
        self.assertIsNone(rules_problem(blank, 24))
        self.assertIn("states no facts", rules_problem({**blank, RULES: "1"}, 24))

    def test_rule_count_is_the_highest_number(self):
        self.assertEqual(rule_count(GUIDELINES_PATH), max(n for _, n in guideline_rules()))


class MadeUpCase(unittest.TestCase):
    """A small ground truth, guidelines and left_out.md in a temporary folder."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="kg_rules_"))
        self.addCleanup(shutil.rmtree, self.tmp)
        self.gt = self.tmp / "ground_truth"
        self.gt.mkdir()
        self.guidelines = self.tmp / "guidelines.md"
        self.guidelines.write_text(GUIDELINES, encoding="utf-8")
        self.left_out = self.tmp / "left_out.md"
        self.left_out.write_text(LEFT_OUT, encoding="utf-8")
        self.doc = self.tmp / "rules_by_triple.md"
        # r0: finished, before r1 in the files but after it in the doc (r1 has the section in left_out.md);
        # r2: unfinished; r3: states no facts
        write_csv(self.gt / "batch_000.csv", FILE_COLUMNS, [
            describes("r0", "Title r0"),
            gt_row("r0", "MODIS", "Instrument", "ABOARD", "Aqua", "Platform", "MODIS aboard Aqua", rules="1, 3"),
            gt_row("r0", "Aqua", "Platform", "ORBITS", "Earth", "Planet", "Aqua orbits Earth", rules="3"),
            describes("r1", "Title r1"),
            gt_row("r1", "AIRS", "Instrument", "ABOARD", "Aqua", "Platform", "AIRS aboard Aqua", rules="4"),
            gt_row("r1", "AIRS", "Instrument", "MEASURES", "heat", "Quantity", "AIRS measures heat")])
        write_csv(self.gt / "batch_001.csv", FILE_COLUMNS, [
            describes("r2", "Title r2", "0"),
            gt_row("r2", "CERES", "Instrument", "ABOARD", "Terra", "Platform", "CERES aboard Terra", "0", rules="2"),
            gt_row("r3", "", "", "", "", "", "")])

    def kw(self):
        return dict(folder=self.gt, guidelines_path=self.guidelines, left_out_path=self.left_out)

    def test_the_doc(self):
        text = doc_text(**self.kw())
        heads = [l for l in text.split("\n") if l.startswith("## ")]
        self.assertEqual(heads, ["## Rules every ground truth triple follows", f"## {DESCRIBES_SECTION}",
                                 '## "Title r1" (pool position 3, id r1)',             # left_out.md's order first
                                 '## "Title r0" (id r0; no section in left_out.md yet)',
                                 '## "Title r2" (id r2; no section in left_out.md yet)',
                                 '## "(no title)" (id r3; no section in left_out.md yet)'])
        self.assertIn(f"Generated by `{COMMAND}`", text)
        self.assertIn("preliminary, still to be reviewed by a person", text)
        # the rules that apply to every triple: quoted once at the top (those the guidelines have), not per record
        top = text.split(f"## {DESCRIBES_SECTION}")[0]
        self.assertIn("### Rule 2 (part of the guidelines)\n\n**Every fact the record states.** All of them.", top)
        self.assertNotIn("### Rule 11", top)
        self.assertIn("written by code", text.split(f"## {DESCRIBES_SECTION}")[1].split("\n## ")[0])
        r1 = text.split('## "Title r1"')[1].split("\n## ")[0]
        self.assertIn('- Describes triple: "r1" (CatalogEntry) DESCRIBES "Title r1" (Dataset): the section *The describes '
                      'triple*, quoted above.', r1)
        self.assertIn('- "AIRS" (Instrument) ABOARD "Aqua" (Platform): rule 4.', r1)
        self.assertIn('- "AIRS" (Instrument) MEASURES "heat" (Quantity): no rules recorded yet.', r1)
        self.assertIn("### Rule 4 (part of the guidelines)\n\n**One fact per triple.** Two facts, two triples.", r1)
        self.assertNotIn("### Rule 1 ", r1)
        r0 = text.split('## "Title r0"')[1].split("\n## ")[0]
        self.assertIn('ABOARD "Aqua" (Platform): rules 1, 3.', r0)
        self.assertEqual(r0.count("### Rule 3 (part of the guidelines)"), 1)         # once per record, used twice
        self.assertIn("### Rule 1 (part of the guidelines)\n\n**Only what the record states.**", r0)
        self.assertIn("- **A sub-rule.** Its words, with a [link](../docs/terminology.md#2-triples).", r0)   # as the file has it
        self.assertEqual([l for l in r0.split("\n") if l.startswith("### ")],
                         ["### Rule 1 (part of the guidelines)", "### Rule 3 (part of the guidelines)"])
        r2 = text.split('## "Title r2"')[1].split("\n## ")[0]
        self.assertIn("Not finished: its ground truth triples may still change.", r2)
        self.assertNotIn("### Rule 2", r2)                                            # applies to every triple: at the top
        r3 = text.split('## "(no title)"')[1]
        self.assertIn("This record states no facts.", r3)
        # written only when it changes
        self.assertTrue(write_doc(self.doc, **self.kw()))
        self.assertEqual(self.doc.read_text(encoding="utf-8"), text)
        self.assertFalse(write_doc(self.doc, **self.kw()))
        # the same text whatever the order the files were written in: it depends on their content alone
        self.assertEqual(doc_text(**self.kw()), text)

    def test_file_problems(self):
        self.assertEqual(file_problems(self.gt, 4), [])
        rows = read_csv(self.gt / "batch_000.csv")
        rows[1][RULES] = "3, 1"
        rows[0][RULES] = "1"
        write_csv(self.gt / "batch_000.csv", FILE_COLUMNS, rows)
        write_csv(self.gt / "batch_002.csv", FILE_COLUMNS[:-1], [gt_row("r4", "A", "I", "P", "B", "J", "A P B")])
        problems = file_problems(self.gt, 4)
        self.assertEqual(len(problems), 3, problems)
        self.assertIn("batch_000.csv, line 2: The describes triple has rules", problems[0])
        self.assertIn("batch_000.csv, line 3: The rules value", problems[1])
        self.assertIn("batch_002.csv lacks the column rules", problems[2])
        # a left_out.md not in its format doesn't stop the doc: it says so, and orders the records by the files
        self.left_out.write_text("# Left out\n\n## not a heading in the format\n", encoding="utf-8")
        text = doc_text(**self.kw())
        self.assertIn("left_out.md couldn't be read", text)
        self.assertIn("every record is in the files' order", text)
        self.assertIn('rules "3, 1" (not a valid value: the test names the line to fix)', text)

    def draft(self, name, rows):
        folder = self.tmp / "drafts"
        folder.mkdir(exist_ok=True)
        write_csv(folder / name, DRAFT_COLUMNS, rows)
        return folder

    def test_merge(self):
        before = {p.name: p.read_bytes() for p in self.gt.glob("*.csv")}
        folder = self.draft("a.csv", [
            {"file": "batch_000.csv", "row": "5", "id": "r1", "subject": "AIRS", "predicate": "ABOARD", "object": "Aqua", "rules": "1, 4"},
            {"file": "batch_000.csv", "row": "6", "id": "r1", "subject": " AIRS", "predicate": "MEASURES", "object": "heat ", "rules": "3"},
            {"file": "batch_000.csv", "row": "2", "id": "r0", "subject": "MODIS", "predicate": "ABOARD", "object": "Aqua", "rules": "1, 3"}])
        done = merge_drafts(folder, self.gt, self.doc, 4, guidelines_path=self.guidelines, left_out_path=self.left_out)
        self.assertEqual(done, {"problems": [], "written": {"batch_000.csv": 2}})     # row 2 already held its value
        rows = read_csv(self.gt / "batch_000.csv")
        self.assertEqual([r[RULES] for r in rows], ["", "1, 3", "3", "", "1, 4", "3"])
        self.assertEqual({k: v for k, v in rows[4].items() if k != RULES},
                         {k: v for k, v in gt_row("r1", "AIRS", "Instrument", "ABOARD", "Aqua", "Platform", "AIRS aboard Aqua").items() if k != RULES})
        self.assertEqual((self.gt / "batch_001.csv").read_bytes(), before["batch_001.csv"])       # not drafted: untouched
        self.assertTrue(self.doc.exists())
        self.assertIn('ABOARD "Aqua" (Platform): rules 1, 4.', self.doc.read_text(encoding="utf-8"))
        # only the rules cells changed: the file with them put back is the file before
        rows[4][RULES], rows[5][RULES] = "4", ""
        write_csv(self.tmp / "back.csv", FILE_COLUMNS, rows)
        self.assertEqual((self.tmp / "back.csv").read_bytes(), before["batch_000.csv"])

    def test_merge_refusals(self):
        """Each mismatch is refused, all are listed, and nothing is written while any is."""
        before = {p.name: p.read_bytes() for p in self.gt.glob("*.csv")}
        good = {"file": "batch_000.csv", "row": "5", "id": "r1", "subject": "AIRS", "predicate": "ABOARD", "object": "Aqua", "rules": "4"}
        folder = self.draft("a.csv", [
            good,
            {**good, "row": "6", "predicate": "MEASURES", "object": "cold"},                # another object: refused
            {**good, "row": "2", "id": "r1"},                                                # row 2 is r0's: refused
            {**good, "row": "9"},                                                            # out of range
            {**good, "row": "0"},
            {**good, "row": "x"},
            {**good, "file": "batch_009.csv"},                                               # no such file
            {"file": "batch_000.csv", "row": "1", "id": "r0", "subject": "r0", "predicate": "DESCRIBES", "object": "Title r0", "rules": "1"},
            {"file": "batch_001.csv", "row": "3", "id": "r3", "subject": "", "predicate": "", "object": "", "rules": "1"},
            {**good, "rules": "4, 1"},                                                       # not ascending
            {**good, "rules": "5"},                                                          # no such rule
            {**good, "rules": "2"}])                                                         # row 5 drafted twice
        self.draft("b.csv", [])
        (folder / "c.csv").write_text("file,row,id\n", encoding="utf-8")                     # columns missing
        done = merge_drafts(folder, self.gt, self.doc, 4, guidelines_path=self.guidelines, left_out_path=self.left_out)
        self.assertEqual(done["written"], {})
        self.assertEqual({p.name: p.read_bytes() for p in self.gt.glob("*.csv")}, before)
        self.assertFalse(self.doc.exists())
        said = "\n".join(done["problems"])
        self.assertEqual(len(done["problems"]), 12, said)
        self.assertIn("a.csv, line 3: the object given ('cold') differ from row 6 of batch_000.csv ('heat')", said)
        self.assertIn("a.csv, line 4: the id, subject given ('r1'; 'AIRS') differ from row 2 of batch_000.csv ('r0'; 'MODIS')", said)
        for line in (5, 6, 7):
            self.assertIn(f"a.csv, line {line}: row ", said)
        self.assertIn("isn't a data row of batch_000.csv (1 to 6, counted after the header)", said)
        self.assertIn("a.csv, line 8: no ground truth file 'batch_009.csv'", said)
        self.assertIn("a.csv, line 9: The describes triple has rules", said)
        self.assertIn("a.csv, line 10: The row of a record that states no facts has rules", said)
        self.assertIn("a.csv, line 11: The rules value \"4, 1\" isn't ascending", said)
        self.assertIn("a.csv, line 12: The rules value \"5\" names rule 5, and annotations/guidelines.md has rules 1 to 4: "
                      "write only those.", said)
        self.assertIn("a.csv, line 13: row 5 of batch_000.csv is drafted twice (also at a.csv, line 2)", said)
        self.assertIn("c.csv lacks the column(s) subject, predicate, object, rules", said)
        # an empty folder
        empty = self.tmp / "none"
        empty.mkdir()
        self.assertIn("holds no .csv file", merge_drafts(empty, self.gt, self.doc, 4)["problems"][0])


if __name__ == "__main__":
    unittest.main()
