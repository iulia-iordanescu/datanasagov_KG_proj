"""The doc guard's edit(): it changes only the agreed words, keeps every link whose words survive (also inside
**bold** or `code`), refuses when the old words aren't there exactly as expected, and records each edit."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

import support  # noqa: F401  (the repository on the import path)
import doc_guard


class Edit(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.root, self.ledger = doc_guard.ROOT, doc_guard.LEDGER
        doc_guard.ROOT, doc_guard.LEDGER = self.tmp, self.tmp / "ledger.json"
        self.doc = self.tmp / "doc.md"

    def tearDown(self):
        doc_guard.ROOT, doc_guard.LEDGER = self.root, self.ledger
        shutil.rmtree(self.tmp)

    def test_keeps_links_inside_bold_and_code(self):
        self.doc.write_text("Press **[Partial pairs](a.md)** and see [`b.md`](b.md); a [record](t.md#r) shows here.\n"
                            "Another line stays.", encoding="utf-8")
        doc_guard.edit("doc.md", "Partial pairs** and see `b.md`; a record shows here.",
                       "Partial pairs** and read `b.md`; each record shows here.")   # old words span three links
        self.assertEqual(self.doc.read_text(encoding="utf-8"),
                         "Press **[Partial pairs](a.md)** and read [`b.md`](b.md); each [record](t.md#r) shows here.\n"
                         "Another line stays.")

    def test_refuses_when_not_found_or_counted_wrong(self):
        self.doc.write_text("one two one", encoding="utf-8")
        with self.assertRaises(AssertionError):
            doc_guard.edit("doc.md", "three", "four")
        with self.assertRaises(AssertionError):
            doc_guard.edit("doc.md", "one", "five")            # twice, but one expected
        doc_guard.edit("doc.md", "one", "five", count=2)
        self.assertEqual(self.doc.read_text(encoding="utf-8"), "five two five")

    def test_records_each_edit(self):
        self.doc.write_text("alpha beta", encoding="utf-8")
        doc_guard.edit("doc.md", "beta", "gamma")
        self.assertEqual(json.loads(doc_guard.LEDGER.read_text(encoding="utf-8")),
                         [{"file": "doc.md", "old": "beta", "new": "gamma", "count": 1}])


if __name__ == "__main__":
    unittest.main()
