"""The keys that decide "the same" (common/common_helpers/triples_io.py and text_match.py), on the one table of
variants (key_variants.py): every key evens out what the table says is the same and keeps apart what it says isn't,
near misses included; the annotation page's own keys (helpers/annotator/page.html, looseKey and isDescribes) give
the same answers on the same table, run in headless Chrome or Edge; and no code outside those two files compares
component classes, component instances or source texts its own way."""
import html
import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from support import ROOT
import key_variants as V                                                  # noqa: E402
from common import ground_truth, text_match, triples_io                 # noqa: E402

CHROME = next((p for p in (shutil.which("chrome"), shutil.which("google-chrome"), shutil.which("chromium"),
                           r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                           r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                           r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
               if p and Path(p).exists()), None)


def triple(t) -> dict:
    return dict(zip(("subject", "predicate", "object"), t))


class Keys(unittest.TestCase):

    def test_names(self):
        for a, b, same in V.NAMES:
            ka, kb = triples_io.component_class_key(a), triples_io.component_class_key(b)
            self.assertEqual(ka == kb, same, (ascii(a), ascii(b), ka, kb))
        self.assertTrue(triples_io.component_class_key("Δ"))                  # a letter: never "no letter at all"

    def test_instances(self):
        for a, b, same in V.INSTANCES:
            ka, kb = text_match.instance_key(a), text_match.instance_key(b)
            self.assertEqual(ka == kb, same, (ascii(a), ascii(b), ka, kb))

    def test_facts(self):
        """The one key of the same fact: the ground truth's repeat check, 050's and 060's duplicate check and 070's
        exact pairs."""
        for a, b, same in V.FACTS:
            self.assertEqual(triples_io.triple_key(triple(a)) == triples_io.triple_key(triple(b)), same, (a, b))
        # the classed key adds both entity classes, swapped with a symmetric predicate's subject and object
        a = {**triple(("Terra", "ALSO_KNOWN_AS", "EOS AM-1")), "subject_class": "Spacecraft", "object_class": "Name"}
        b = {**triple(("EOS AM-1", "ALSO_KNOWN_AS", "Terra")), "subject_class": "name", "object_class": "spacecraft"}
        self.assertEqual(triples_io.classed_key(a), triples_io.classed_key(b))
        self.assertNotEqual(triples_io.classed_key(a), triples_io.classed_key({**b, "object_class": "Instrument"}))

    def test_repeats_in_the_ground_truth_use_the_same_key(self):
        """A ground truth record with "1 km" and "1000 m", or HAS_PART and HASPART, holds the same classed triple
        twice: only one copy could be paired, so 070 refuses to run (gt.repeats); a near miss (10 km) is two facts."""
        import csv
        with tempfile.TemporaryDirectory() as tmp:
            for objects, predicates, repeated in ((("1 km", "1000 m"), ("HAS_SPATIAL_RESOLUTION",) * 2, True),
                                                  (("1 km", "1 km"), ("HAS_PART", "HASPART"), True),
                                                  (("1 km", "10 km"), ("HAS_SPATIAL_RESOLUTION",) * 2, False)):
                with open(Path(tmp) / "batch_000.csv", "w", encoding="utf-8", newline="") as fh:
                    w = csv.writer(fh)
                    w.writerow(ground_truth.COLUMNS)
                    for o, p in zip(objects, predicates):
                        w.writerow(["r1", "MODIS", "Dataset", p, o, "SpatialResolution", "s", "1"])
                self.assertEqual(bool(ground_truth.read_ground_truth(tmp).repeats), repeated, (objects, predicates))

    def test_describes(self):
        for (sc, p), want in V.DESCRIBES:
            self.assertEqual(triples_io.is_describes({"subject_class": sc, "predicate": p}), want, (ascii(sc), ascii(p)))
        for x in ("X", "x", "", " "):
            self.assertTrue(triples_io.is_undecided(x), x)
        self.assertFalse(triples_io.is_undecided("Dataset"))

    def test_in_text(self):
        for text, needle, found in V.IN_TEXT:
            self.assertEqual(text_match.Text(text).contains(needle), found, (ascii(text), needle))

    def test_passages(self):
        from common.validate import source_in_text
        for source, parts in V.PASSAGES:
            self.assertEqual(triples_io.passages(source), parts, source)
        text = text_match.Text("MODIS aboard Aqua was launched. Data since 2002 are kept.")
        for source, parts in V.PASSAGES:
            self.assertTrue(source_in_text(source, text), source)            # each way of writing the join
        self.assertFalse(source_in_text("MODIS aboard Aqua … since 2003", text))      # near miss: a part not there

    def test_numbers_as_the_text_writes_them(self):
        """A JSON number in a model's triple is written as the record's text writes it (or in full, without one), so
        it is found there."""
        text = "Pixels of 1.50 km; 1,000 files; a threshold of 1e-6."
        for value, written in ((1.5, "1.50"), (1000, "1,000"), (1e3, "1,000"), (0.000001, "1e-6"), (2020, "2020"),
                               (2.25, "2.25"), (1e-07, "0.0000001")):
            t = triples_io.clean_triple({"subject": "MODIS", "predicate": "HAS", "object": value}, text)
            self.assertEqual(t["object"], written, value)
        self.assertIsNone(triples_io.clean_triple({"subject": "MODIS", "predicate": "HAS", "object": float("nan")}))
        self.assertIsNone(triples_io.clean_triple({"subject": "MODIS", "predicate": "HAS", "object": True}))

    def test_canonical_row(self):
        row = triples_io.canonical_row({"subject": "  MODIS \n aboard ", "object": "", "flags": ["x"], "id": "r1"})
        self.assertEqual(row, {"subject": "MODIS aboard", "object": None, "flags": ["x"], "id": "r1"})
        self.assertEqual(triples_io.canonical_row(row), row)                  # tidying twice changes nothing
        # a file's row keeps its empty cells empty (blank=""), so its fingerprint and its columns stay strings
        self.assertEqual(triples_io.canonical_row({"subject": " a  b ", "object": ""}, blank=""), {"subject": "a b", "object": ""})


@unittest.skipUnless(CHROME, "no Chrome or Edge on this computer to run the page's script")
class PageKeys(unittest.TestCase):
    """helpers/annotator/page.html's looseKey and isDescribes, as the page has them, run in headless Chrome on the
    table the server's keys pass."""

    def test_same_answers_as_the_server(self):
        page = (ROOT / "helpers" / "annotator" / "page.html").read_text(encoding="utf-8")
        code = []
        for name in ("looseKey", "isDescribes"):
            m = re.search(r"^const %s = .*?;\n(?=\S)" % name, page, re.M | re.S)
            self.assertIsNotNone(m, name)
            code.append(m.group(0))
        names = [[a, b] for a, b, _ in V.NAMES]
        describes = [list(x) for x, _ in V.DESCRIBES]
        script = ("\n".join(code) + f"\nconst names = {json.dumps(names)}, describes = {json.dumps(describes)};\n"
                  "document.body.dataset.out = JSON.stringify({names: names.map(([a, b]) => [looseKey(a), looseKey(b)]),"
                  " describes: describes.map(([s, p]) => isDescribes({subject_class: s, predicate: p}))});")
        with tempfile.TemporaryDirectory() as tmp:
            harness = Path(tmp) / "keys.html"
            harness.write_text(f"<!DOCTYPE html><html><body><script>{script}</script></body></html>", encoding="utf-8")
            dom = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-first-run",
                                  f"--user-data-dir={Path(tmp) / 'profile'}", "--dump-dom", harness.as_uri()],
                                 capture_output=True, text=True, encoding="utf-8", timeout=120).stdout
        out = json.loads(html.unescape(re.search(r'data-out="([^"]*)"', dom).group(1)))
        for (a, b, same), (ka, kb) in zip(V.NAMES, out["names"]):
            self.assertEqual((ka, kb), (triples_io.component_class_key(a), triples_io.component_class_key(b)),
                             (ascii(a), ascii(b)))
            self.assertEqual(ka == kb, same, (ascii(a), ascii(b)))
        self.assertEqual(out["describes"], [want for _, want in V.DESCRIBES])


class OneHome(unittest.TestCase):
    """A guard: outside triples_io.py and text_match.py, no code compares component classes, component instances,
    the describes triple's component classes, "(none)", or a source text's passages by their exact words."""

    #: Each a pattern of an exact comparison that has a key instead (the key in the message).
    PATTERNS = [
        (r'\[["\'](subject|object|subject_class|object_class|predicate)["\']\] *(==|!=) *[a-z_]+\[["\'](subject|object|subject_class|object_class|predicate)',
         "two triples' slots compared word for word: use triple_key, classed_key or instance_key"),
        (r'all\(row\[k\] == t\[k\]', "triples compared word for word: use classed_key"),
        (r'\[["\']predicate["\']\] *(==|!=) *ENTRY_PREDICATE', "the describes triple told by its exact predicate: use is_describes"),
        (r'(?<!for )\b\w+ (?:not )?in \(ENTRY_CLASS, ENTRY_PREDICATE, UNDECIDED\)|in \("", UNDECIDED\)|== UNDECIDED\b',
         "a describes class compared exactly: use is_undecided or component_class_key"),
        (r'\.split\(PASSAGES_JOIN\)', "a source text split on one spelling of the join: use passages"),
        (r'\bnorm_predicate\b', "a second key for predicates: use component_class_key"),
        (r'\[\^?a-z0-9\]', "a key of ASCII letters only: use component_class_key"),
    ]
    HOMES = ("common/common_helpers/triples_io.py", "common/common_helpers/text_match.py")

    def test_the_guard_catches_what_it_should(self):
        """Each pattern catches the lines it was written for (the old code's own), and leaves the key-based ones."""
        caught = ['if r["predicate"] != ENTRY_PREDICATE', 'same = [row for row in rows if all(row[k] == t[k] for k in',
                  'if name not in (ENTRY_CLASS, ENTRY_PREDICATE, UNDECIDED)', 'if c in ("", UNDECIDED):',
                  'parts = source.split(PASSAGES_JOIN)', 'return re.sub(r"[^a-z0-9]", "", s)',
                  'if g["subject"] == t["subject"]:', 'norm_predicate(row.get("predicate"))']
        left = ['FIXED = {component_class_key(n) for n in (ENTRY_CLASS, ENTRY_PREDICATE, UNDECIDED)}',
                'if not is_describes(r):', 'if classed_key(row) == classed_key(t):', 'parts = passages(source)',
                'if row["id"] == rec["id"]:']
        hits = lambda line: [why for pattern, why in self.PATTERNS if re.search(pattern, line)]     # noqa: E731
        for line in caught:
            self.assertTrue(hits(line), line)
        for line in left:
            self.assertEqual(hits(line), [], line)

    def test_no_exact_comparisons(self):
        found = []
        for path in ROOT.rglob("*.py"):
            rel = path.relative_to(ROOT).as_posix()
            if rel.startswith(("archive/", ".myvenv/", "DONOTTRACK/", "tests/")) or rel in self.HOMES:
                continue
            for n, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                for pattern, why in self.PATTERNS:
                    if re.search(pattern, line):
                        found.append(f"{rel}:{n}: {why}: {line.strip()}")
        self.assertEqual(found, [])


if __name__ == "__main__":
    unittest.main()
