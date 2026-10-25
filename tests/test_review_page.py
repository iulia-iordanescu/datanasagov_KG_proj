"""The review page (helpers/review_page.py): the page it writes is one self-contained file that reaches nothing
outside itself, shows every entity class, predicate and row of the translation table, and says which version it
is; the comment files reviewers send back are read into a summary that flags comments on entries that changed or
are gone. Works on temporary copies; nothing in annotations/ or outputs/ is touched."""
import csv
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

from support import ROOT

sys.path.insert(0, str(ROOT / "helpers"))
import review_page as R                                                        # noqa: E402

SCHEMA = """ENTITY CLASSES
--------------
Instrument        a device that takes measurements
Spacecraft        a craft that operates in space
                  source: ground truth tuning #2

PREDICATES
----------
Each entry below reads subject -> object.

ABOARD               is carried on
                     Instrument -> Spacecraft
                     only: any -> Spacecraft
"""
MAPPING = """kind,component_class_from_past_or_crt_schema,component_class_in_gtt,swap_subject_and_object,checked,definition_from_past_or_crt_schema,definition_in_gtt
entity class,Satellite,Spacecraft,no,yes,"A craft that orbits a body, e.g. Aqua.",a craft that operates in space
predicate,CARRIES,ABOARD,yes,yes,Has on board.,is carried on
entity class,Gadget,(none),no,no,A small device.,
"""


def files(folder: Path, schema: str = SCHEMA, mapping: str = MAPPING) -> dict:
    (folder / "ground_truth_schema.txt").write_text(schema, encoding="utf-8")
    (folder / "component_class_mapping.csv").write_text(mapping, encoding="utf-8")
    return {"schema_path": folder / "ground_truth_schema.txt", "mapping_path": folder / "component_class_mapping.csv"}


def page_json(page: str) -> dict:
    return json.loads(re.search(r'<script type="application/json" id="data">(.*?)</script>', page, re.S).group(1))


class Page(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        cls.path = R.generate(out_dir=cls.tmp, **files(cls.tmp))
        cls.page = cls.path.read_text(encoding="utf-8")
        cls.data = page_json(cls.page)

    def test_named_by_date_and_commit(self):
        self.assertRegex(self.path.name, r"^review_\d{4}-\d{2}-\d{2}_\w+\.html$")

    def test_reaches_nothing_outside_itself(self):
        """No address the browser would load (the page's own data may quote a web address as text: it is never
        loaded); no script call that sends or fetches; a policy that forbids any request."""
        code = self.page.replace(re.search(r'<script type="application/json" id="data">.*?</script>', self.page, re.S).group(0), "")
        loads = (r"(?i)(src|href)\s*=\s*[\"']?(https?:)?//|(?<![\w.])url\(\s*(?![\"']?data:)|@import|\bfetch\("
                 r"|XMLHttpRequest|sendBeacon|WebSocket|EventSource|[\"(]/fonts/")
        self.assertEqual([m.group(0) for m in re.finditer(loads, code)], [])
        self.assertIn("default-src 'none'", code)
        self.assertIn("data:font/woff2;base64,", code)                        # the typefaces, inside
        self.assertNotRegex(code, r"{{[A-Z_]+}}")                            # every placeholder filled

    def test_the_annotation_tools_look(self):
        """The annotation tool's style sheets, as its page holds them."""
        tool = (ROOT / "helpers" / "annotator" / "page.html").read_text(encoding="utf-8")
        first = re.findall(r"<style>(.*?)</style>", tool, re.S)[1]
        self.assertIn(first.strip()[:2000], self.page)

    def test_every_entry(self):
        s, m = self.data["schema"], self.data["mapping"]["rows"]
        self.assertEqual([e["entry"] for e in s["entity_classes"]], ["Instrument", "Spacecraft"])
        self.assertEqual([e["entry"] for e in s["predicates"]], ["ABOARD"])
        aboard = s["predicates"][0]
        self.assertEqual((aboard["patterns"], aboard["pins"]), ([["Instrument", "Spacecraft"]], [["any", "Spacecraft"]]))
        self.assertEqual(s["entity_classes"][1]["source"], "ground truth tuning #2")
        self.assertEqual(s["notes"], ["Each entry below reads subject -> object."])
        self.assertEqual([r["entry"] for r in m], ["entity class Satellite", "predicate CARRIES", "entity class Gadget"])
        self.assertEqual((m[1]["swap"], m[2]["gtt"], m[2]["checked"]), ("yes", "(none)", "no"))

    def test_version(self):
        v = self.data["version"]
        self.assertEqual([f["sha256"] for f in v["files"]],
                         [R.fingerprint(self.tmp / "ground_truth_schema.txt"), R.fingerprint(self.tmp / "component_class_mapping.csv")])
        self.assertEqual(v["id"], self.path.stem)
        self.assertTrue(v["commit"] and v["generated"])
        self.assertIn("A read-only copy: it can't change anything", self.page)

    def test_terms_from_terminology(self):
        """Each term the page shows is docs/terminology.md's entry, word for word (markup aside)."""
        terms = (ROOT / "docs" / "terminology.md").read_text(encoding="utf-8")
        self.assertEqual([t["term"] for t in self.data["glossary"]], R.GLOSSARY)
        for t in self.data["glossary"]:
            words = re.sub(r"<[^>]+>", "", t["meaning_html"]).replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
            plain = re.sub(r"\[([^\[\]]*)\]\([^)]*\)", r"\1", terms).replace("`", "").replace("**", "")
            self.assertIn(words[:120].replace("*", ""), plain.replace("*", ""))

    def test_a_missing_term_stops(self):
        with self.assertRaises(ValueError):
            R.glossary(terms=["no such term"])

    def test_the_real_files(self):
        """The real ground truth schema and translation table make a page with every entry."""
        with tempfile.TemporaryDirectory() as out:
            data = page_json(R.generate(out_dir=Path(out)).read_text(encoding="utf-8"))
        from common.schema_io import read_ground_truth_schema
        from common.component_class_mapping import read_mapping
        schema = read_ground_truth_schema(R.SCHEMA_PATH)
        self.assertEqual([e["entry"] for e in data["schema"]["entity_classes"]], list(schema["entity_classes"]))
        self.assertEqual([e["entry"] for e in data["schema"]["predicates"]], list(schema["predicates"]))
        self.assertEqual(len(data["mapping"]["rows"]), len(read_mapping(R.MAPPING_PATH)))
        self.assertEqual(len({r["entry"] for r in data["mapping"]["rows"]}), len(data["mapping"]["rows"]))   # ids unique


class Comments(unittest.TestCase):
    """A comment file as the page saves it, read back with --read."""

    def write(self, folder: Path, name: str, rows: list) -> Path:
        path = folder / name
        with open(path, "w", encoding="utf-8-sig", newline="") as fh:
            w = csv.DictWriter(fh, R.COMMENT_COLUMNS, lineterminator="\r\n")
            w.writeheader()
            w.writerows(rows)
        return path

    def row(self, kind, entry, shown, comment, at="2026-10-24T10:00:00-04:00", who="Jane Smith"):
        return {"reviewer": who, "page_version": "review_2026-10-24_abc1234", "git_commit": "abc1234", "kind": kind,
                "entry": entry, "entry_text_shown": shown, "comment": comment, "timestamp": at}

    def test_round_trip_and_flags(self):
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            paths = files(t)
            now = R.entry_texts(**paths)
            reviews = t / "reviews"
            reviews.mkdir()
            self.write(reviews, "a.csv", [
                self.row("general", "(general)", "", "Clear overall, thanks."),
                self.row("entity class", "Instrument", now[("entity class", "Instrument")], 'Also "sensor", maybe.'),
                self.row("entity class", "Spacecraft", "Spacecraft: a vehicle in space", "Too vague."),       # changed since
                self.row("predicate", "HAS_WIDGET", "HAS_WIDGET: has a widget", "Drop it."),                 # gone
                self.row("translation row", "predicate CARRIES", now[("translation row", "predicate CARRIES")], "Right, swapped."),
                self.row("entity class", "Instrument", "", "older words", at="2026-10-23T09:00:00-04:00")])  # older: replaced
            (reviews / "notes.txt").write_text("not a comment file", encoding="utf-8")                      # not read
            self.write(reviews, "b.csv", [self.row("predicate", "ABOARD", now[("predicate", "ABOARD")], "Fine.", who="Bo Lee")])
            out, text = R.read_and_summarize([reviews], out_dir=t / "out", **paths)
            self.assertTrue(out.exists())
            self.assertIn("6 comment(s) from 2 reviewer(s): Bo Lee, Jane Smith.", text)
            self.assertIn("⚑ 1 comment(s) on an entry that changed since the page they were written on; 1 on an entry "
                          "no longer in the files.", text)
            self.assertIn('Also "sensor", maybe.', text)
            self.assertNotIn("older words", text)
            spacecraft = text.split("### Spacecraft", 1)[1].split("###", 1)[0]
            self.assertIn("⚑ Changed since that page. Then: Spacecraft: a vehicle in space", spacecraft)
            self.assertIn("Now: Spacecraft: a craft that operates in space | source: ground truth tuning #2", spacecraft)
            self.assertIn("⚑ No longer in the files", text.split("### HAS_WIDGET", 1)[1])
            self.assertNotIn("⚑", text.split("### Instrument", 1)[1].split("###", 1)[0])
            self.assertLess(text.index("## General comments"), text.index("## Entity classes"))

    def test_a_file_of_another_shape_is_skipped(self):
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            (t / "x.csv").write_text("name,note\nA,B\n", encoding="utf-8")
            _, text = R.read_and_summarize([t / "x.csv"], out_dir=t / "out", **files(t))
            self.assertIn("x.csv: lacks the column(s) reviewer", text)
            self.assertIn("0 comment(s)", text)


if __name__ == "__main__":
    unittest.main()
