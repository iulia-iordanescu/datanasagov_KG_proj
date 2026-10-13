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

    def test_link_goes_back_where_it_was(self):
        # the linked word also appears earlier in the line, as a setting's `name`: the link stays on its own use
        self.doc.write_text("| `model` | old | The AI [model](t.md#m) to ask. |", encoding="utf-8")
        doc_guard.edit("doc.md", "| old | The AI model to ask.", "| new | The AI model to ask: by default another.")
        self.assertEqual(self.doc.read_text(encoding="utf-8"),
                         "| `model` | new | The AI [model](t.md#m) to ask: by default another. |")

    def test_lost_links(self):
        """check(): a link whose words stay but whose target nothing links any more is lost; one relinked under other
        words (e.g. "2026-10-12" -> "Evidence") is not."""
        import contextlib
        import io
        from unittest import mock

        def checked(before, now, old, new):
            self.doc.write_text(now, encoding="utf-8")
            doc_guard._record("doc.md", old, new, 1)
            out = io.StringIO()
            with mock.patch.object(doc_guard, "_docs_changed", lambda: ["doc.md"]), \
                    mock.patch.object(doc_guard, "_at_head", lambda rel: before), contextlib.redirect_stdout(out):
                ok = doc_guard.check()
            doc_guard.LEDGER.unlink()
            return ok, out.getvalue()
        ok, _ = checked("A line [2026-10-12](#a). Dated 2026-10-12.\n", "A line [Evidence](#a). Dated 2026-10-12.\n",
                        "A line 2026-10-12.", "A line Evidence.")
        self.assertTrue(ok)
        ok, out = checked("A [record](t.md#r) here; a record.\n", "A record here; a record.\n", "A record here", "A record here")
        self.assertFalse(ok)
        self.assertIn("links gone whose words remain", out)

    def test_refuses_when_not_found_or_counted_wrong(self):
        self.doc.write_text("one two one", encoding="utf-8")
        with self.assertRaises(AssertionError):
            doc_guard.edit("doc.md", "three", "four")
        with self.assertRaises(AssertionError):
            doc_guard.edit("doc.md", "one", "five")            # twice, but one expected
        doc_guard.edit("doc.md", "one", "five", count=2)
        self.assertEqual(self.doc.read_text(encoding="utf-8"), "five two five")

    def test_edit_block_moves_whole_lines(self):
        self.doc.write_text("# A\n\n- one [x](x.md)\n- two\n\n# B\n", encoding="utf-8")
        doc_guard.edit_block("doc.md", "- one [x](x.md)\n- two\n", "- two\n- one [x](x.md)\n")
        self.assertEqual(self.doc.read_text(encoding="utf-8"), "# A\n\n- two\n- one [x](x.md)\n\n# B\n")
        self.assertEqual(json.loads(doc_guard.LEDGER.read_text(encoding="utf-8"))[0]["old"], "- one x\n- two\n")
        with self.assertRaises(AssertionError):
            doc_guard.edit_block("doc.md", "- three\n", "- four\n")

    def test_words_inside_another_link_dont_count(self):
        text = "No [model calls](t.md#m) here; a [model](t.md#m) there."
        self.assertNotIn("model", doc_guard.outside_links("No [model calls](t.md#m) here."))
        self.assertIn("there", doc_guard.outside_links(text))

    def test_create_writes_a_new_doc_only(self):
        doc_guard.create("new.md", "# New\n\nSee [x](x.md).\n")
        self.assertEqual((self.tmp / "new.md").read_text(encoding="utf-8"), "# New\n\nSee [x](x.md).\n")
        self.assertTrue(json.loads(doc_guard.LEDGER.read_text(encoding="utf-8"))[0]["create"])
        with self.assertRaises(AssertionError):
            doc_guard.create("new.md", "again")

    def test_records_each_edit(self):
        self.doc.write_text("alpha beta", encoding="utf-8")
        doc_guard.edit("doc.md", "beta", "gamma")
        self.assertEqual(json.loads(doc_guard.LEDGER.read_text(encoding="utf-8")),
                         [{"file": "doc.md", "old": "beta", "new": "gamma", "count": 1}])


if __name__ == "__main__":
    unittest.main()
