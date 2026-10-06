"""Cleaning (020_clean): HTML to plain text with nothing lost
(note_cleaning.py), joining a maintainer's spellings (maintainers.py), and
the step's moves on a small batch file."""
import doctest
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path

from support import use_step

use_step("020_clean")
import maintainers                                # noqa: E402
import moves                                      # noqa: E402
import note_cleaning                              # noqa: E402


class Maintainers(unittest.TestCase):

    def test_selftest(self):
        maintainers.selftest()

    def test_as_harvested(self):
        self.assertEqual(maintainers.as_harvested("  Jane \t Roe\n"), "Jane Roe")
        for blank in (None, "", "   "):
            self.assertEqual(maintainers.as_harvested(blank), maintainers.UNKNOWN)

    def test_same_key(self):
        same = [("Morgan, Kristan", "Kristan Morgan"), ("José Núñez", "JOSÉ NÚÑEZ"),
                ("Ｊａｎｅ Ｒｏｅ", "Jane Roe"),               # full-width letters (NFKC)
                ("MRS. Jane Roe", "Jane Roe"), ("Jane Roe, Ph.D", "Roe Jane")]
        for a, b in same:
            with self.subTest(a=a, b=b):
                self.assertEqual(maintainers.name_key(a), maintainers.name_key(b))

    def test_different_key(self):
        different = [("Jane Roe", "Jane Rowe"), ("Drew Smith", "Smith"), ("Ms Pac", "Pac Man"),
                     ("—", "–"), ("", "undefined")]
        for a, b in different:
            with self.subTest(a=a, b=b):
                self.assertNotEqual(maintainers.name_key(a), maintainers.name_key(b))

    def test_no_letters_never_joined(self):
        mapping, joins = maintainers.join(["-", "-", "?", "..."])
        self.assertEqual(mapping, {"-": "-", "?": "?", "...": "..."})
        self.assertEqual(joins, [])

    def test_join(self):
        names = ["KRISTAN MORGAN", "Kristan Morgan", "Kristan Morgan", "Morgan, Kristan", "NASA Team", "nasa team",
                 "Solo Name"]
        mapping, joins = maintainers.join(names)
        self.assertEqual(mapping["KRISTAN MORGAN"], "Kristan Morgan")
        self.assertEqual(mapping["Morgan, Kristan"], "Kristan Morgan")
        self.assertEqual(mapping["Solo Name"], "Solo Name")               # one spelling: untouched
        self.assertEqual(mapping["nasa team"], "NASA Team")               # mixed case preferred
        self.assertEqual(joins[0], {"name": "Kristan Morgan", "records": 4,
                                    "spellings": ["KRISTAN MORGAN", "Kristan Morgan", "Morgan, Kristan"]})
        self.assertEqual([j["records"] for j in joins], sorted((j["records"] for j in joins), reverse=True))

    def test_display_name(self):
        from collections import Counter
        self.assertEqual(maintainers.display_name(Counter({"JANE ROE": 3, "jane roe": 1})), "Jane Roe")
        self.assertEqual(maintainers.display_name(Counter({"Dr. Jane Roe": 1, "JANE ROE": 5})), "Jane Roe")


class NoteCleaning(unittest.TestCase):

    def test_selftest(self):
        note_cleaning.selftest()

    def test_doctests(self):
        failed, tried = doctest.testmod(note_cleaning)
        self.assertGreater(tried, 5)
        self.assertEqual(failed, 0)

    def test_fuzz_loses_nothing(self):
        report = note_cleaning._fuzz(count=3000, seed=1)
        self.assertTrue(report.ok, str(report))
        self.assertEqual(report.total, 3000)

    def test_plain_text_untouched(self):
        for text in ["plain", "two  spaces", "line\n\nbreak", "≥ 5 µm, Ångström, 数据"]:
            with self.subTest(text=text):
                note = note_cleaning.clean_note(text)
                self.assertFalse(note.had_markup)
                self.assertEqual(note.tier, note_cleaning.TIER_PARSED)
                self.assertEqual(note_cleaning.verify(text, note.text), {})

    def test_every_token_kept(self):
        cases = ["&lt;p&gt;MODIS aboard &lt;b&gt;Aqua&lt;/b&gt;, 2002–2023&lt;/p&gt;",
                 "&lt;a href='https://ex.org/a_b?x=1'&gt;link&lt;/a&gt; Ångström_unit 数据集",
                 "&lt;table&gt;&lt;tr&gt;&lt;td&gt;Band 1&lt;/td&gt;&lt;td&gt;0.62&lt;/td&gt;&lt;/tr&gt;&lt;/table&gt;",
                 "&amp;amp;lt;b&amp;amp;gt;triple escaped&amp;amp;lt;/b&amp;amp;gt;",
                 "<p>already decoded <i>HTML</i></p>", "&lt;p&gt;unclosed &lt;b&gt;bold", None, 42, b"bytes &amp; more"]
        for raw in cases:
            with self.subTest(raw=raw):
                note = note_cleaning.clean_note(raw)
                self.assertEqual(note.lost, {})
                if note.token_verified:
                    self.assertEqual(note_cleaning.verify(raw, note.text), {})
                self.assertNotIn("<b>", note.text)

    def test_tokens_any_script(self):
        # Letters and digits of every script are tokens; "_" separates them.
        self.assertEqual(note_cleaning.TOKEN.findall("Ångström_unit 数据 x2"), ["Ångström", "unit", "数据", "x2"])

    def test_verify_notices_a_loss(self):
        self.assertTrue(note_cleaning.verify("&lt;b&gt;MODIS&lt;/b&gt; Aqua", "MODIS"))

    def test_records(self):
        result = note_cleaning.clean_record({"title": "A &lt;b&gt;B&lt;/b&gt;", "notes": None}, ("title", "notes", "x"))
        self.assertEqual((result.text("title"), result.text("notes"), result.missing), ("A B", "", ("x",)))


def batch(records, start=0):
    return {"request": {"start": start, "rows": len(records)}, "records": records}


class Moves(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        raw = [{"id": "a", "name": "n-a", "title": "Title\n   two lines", "notes": "&lt;p&gt;MODIS &lt;b&gt;Aqua&lt;/b&gt;&lt;/p&gt;",
                "maintainer": "KRISTAN MORGAN", "organization": {"title": "NASA"},
                "tags": [{"name": "earth"}, {"bad": 1}], "resources": [{"format": "HDF"}, {"format": " HDF "}, {"format": ""}],
                "license_title": "PD", "author": "&lt;i&gt;Me&lt;/i&gt;"},
               {"name": "no-id", "title": "dropped"},
               {"id": " ", "name": "blank-id", "title": "dropped too"},
               {"id": "b", "title": None, "maintainer": "Kristan  Morgan"},
               {"id": "a", "title": "a repeat, dropped"}]
        (self.tmp / "batch_00000.json").write_text(json.dumps(batch(raw[:3])), encoding="utf-8")
        (self.tmp / "batch_01000.json").write_text(json.dumps(batch(raw[3:], 1000)), encoding="utf-8")
        self.inputs = {"batches": self.tmp / "batch_*.json"}

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def run_moves(self, **settings):
        settings = {"extra_text_fields": "", "join_maintainers": True, **settings}
        c = moves.load_raw(self.inputs, settings)
        c = moves.keep_fields(c)
        c = moves.clean_text(c)
        return moves.join_maintainers(c, settings)

    def test_records(self):
        c = self.run_moves(extra_text_fields="author")
        self.assertEqual([r["id"] for r in c.records], ["a", "b"])
        self.assertEqual((c.read, len(c.dropped_no_id), c.repeats), (5, 2, ["a"]))
        a, b = c.records
        self.assertEqual(a["title"], "Title two lines")                # one line
        self.assertEqual(a["notes"], "MODIS Aqua")
        self.assertEqual(a["author"], "Me")
        self.assertEqual(a["formats"], ["HDF"])
        self.assertEqual(a["tags"], ["earth"])
        self.assertEqual((a["maintainer"], b["maintainer"]), ("Kristan Morgan", "Kristan Morgan"))
        self.assertEqual(a["maintainer_as_harvested"], "KRISTAN MORGAN")
        self.assertEqual(b["title"], "")
        self.assertEqual(c.no_text, 1)
        self.assertTrue(a["_origin"][0].endswith("batch_00000.json#a"))

    def test_no_join(self):
        c = self.run_moves(join_maintainers=False)
        self.assertEqual({r["maintainer"] for r in c.records}, {"KRISTAN MORGAN", "Kristan Morgan"})

    def test_extra_field_clash(self):
        with self.assertRaises(ValueError):
            moves.load_raw(self.inputs, {"extra_text_fields": "maintainer", "join_maintainers": True})

    def test_old_format(self):
        (self.tmp / "batch_00000.json").write_text("[]", encoding="utf-8")
        with self.assertRaises(ValueError):
            moves.load_raw(self.inputs, {"extra_text_fields": "", "join_maintainers": True})

    def test_results_file(self):
        out = self.tmp / "out"
        out.mkdir()
        r = moves.results(self.run_moves(), out)
        lines = (out / moves.OUTPUT_NAME).read_text(encoding="utf-8").splitlines()
        self.assertEqual([json.loads(x)["id"] for x in lines], ["a", "b"])
        self.assertTrue(any("no id" in w for w in r.warnings))
        self.assertTrue(re.search(r"Dropped: no id \| 2 \|", r.details))


if __name__ == "__main__":
    unittest.main()
