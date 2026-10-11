"""run_pipeline.py: which steps run, the human gates (050 kept, 060 and 070 skipped), stopping at the first step that
doesn't finish, and the pipeline report. Steps are stood in for by tiny scripts that write a report and a manifest and
exit with a chosen code; the ground truth and outputs are temporary folders. Nothing real is run or touched."""
import csv
import json
import shutil
import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

import support  # noqa: F401  (the repository on the import path)
import run_pipeline as rp
from common import ground_truth

FAKE_STEP = r'''
import json, sys
from pathlib import Path
step, code, reports, results = sys.argv[1], int(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4])
(reports / f"{step}_2026-01-01_0000.md").write_text("report", encoding="utf-8")
if code == 0:
    (results / step).mkdir(parents=True, exist_ok=True)
    (results / step / "_manifest.json").write_text(json.dumps({"headline": {"things": 3}, "warnings": 1}))
sys.exit(code)
'''


class Base(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.saved = {k: getattr(rp, k) for k in ("REPORTS_DIR", "LOGS_DIR", "RESULTS_DIR", "GROUND_TRUTH_DIR",
                                                    "read_ground_truth", "command", "STEPS", "PAYING")}
        rp.REPORTS_DIR, rp.LOGS_DIR, rp.RESULTS_DIR = self.tmp / "reports", self.tmp / "logs", self.tmp / "results"
        rp.GROUND_TRUTH_DIR = self.tmp / "gt"
        rp.GROUND_TRUTH_DIR.mkdir()
        rp.read_ground_truth = lambda: ground_truth.read_ground_truth(rp.GROUND_TRUTH_DIR)

    def tearDown(self):
        for k, v in self.saved.items():
            setattr(rp, k, v)
        shutil.rmtree(self.tmp)

    def gt_file(self, n, finished):
        """A ground truth file with one record, finished or not."""
        with open(rp.GROUND_TRUTH_DIR / ground_truth.file_name(n), "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(ground_truth.COLUMNS)
            w.writerow([f"r{n}", "MODIS", "Instrument", "ABOARD", "Aqua", "Spacecraft", "MODIS aboard Aqua",
                        "1" if finished else "0"])

    def draft(self, n):
        folder = rp.RESULTS_DIR / "050_annotate"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / ground_truth.draft_name(n)).write_text("id\n", encoding="utf-8")


class Choosing(Base):

    def pick(self, **kw):
        return rp.chosen_steps(Namespace(**{"start": None, "to": None, "only": None, **kw}))

    def test_ranges(self):
        self.assertEqual(self.pick(), rp.STEPS)
        self.assertEqual(self.pick(start="040"), rp.STEPS[3:])
        self.assertEqual(self.pick(start="040", to="060_extract"), rp.STEPS[3:6])
        self.assertEqual(self.pick(only="070"), ["070_evaluate"])

    def test_refusals(self):
        for kw, words in [({"start": "090"}, "no step"), ({"start": "060", "to": "040"}, "comes after"),
                          ({"only": "070", "start": "040"}, "can't be combined")]:
            with self.subTest(kw=kw), self.assertRaisesRegex(SystemExit, words):
                self.pick(**kw)

    def test_confirm_passed_to_paying_steps_only(self):
        self.assertIn("--confirm_paid_calls", rp.command("060_extract", "false"))
        self.assertNotIn("--confirm_paid_calls", rp.command("020_clean", "false"))
        self.assertNotIn("--confirm_paid_calls", rp.command("060_extract", None))


class Gates(Base):

    def test_050_kept_while_a_batch_waits(self):
        self.gt_file(0, finished=True)
        self.assertEqual(rp.gate("050_annotate", False), (None, None))         # nothing waiting: drafts
        self.draft(1)
        status, why = rp.gate("050_annotate", False)
        self.assertEqual(status, "kept")
        self.assertIn("draft batch 1 isn't opened", why)
        self.gt_file(1, finished=False)                                        # opened, not finished
        self.assertIn("batch_001.csv has a record not finished", rp.gate("050_annotate", False)[1])
        self.gt_file(1, finished=True)
        self.assertEqual(rp.gate("050_annotate", False), (None, None))
        self.draft(2)
        self.assertEqual(rp.gate("050_annotate", True), (None, None))          # --only: runs anyway

    def test_060_070_skipped_without_a_finished_record(self):
        for step in ("060_extract", "070_evaluate"):
            self.assertEqual(rp.gate(step, False)[0], "skipped")
        self.gt_file(0, finished=False)
        self.assertEqual(rp.gate("070_evaluate", False)[0], "skipped")
        self.gt_file(1, finished=True)
        self.assertEqual(rp.gate("060_extract", False), (None, None))
        self.assertEqual(rp.gate("020_clean", False), (None, None))


class Running(Base):

    def run_fake(self, codes, argv=()):
        rp.STEPS = list(codes)
        rp.PAYING = set()
        rp.command = lambda step, confirm: [sys.executable, "-c", FAKE_STEP, step, str(codes[step]),
                                            str(rp.REPORTS_DIR), str(rp.RESULTS_DIR)]
        exit_code = rp.main(list(argv))
        report = next(rp.REPORTS_DIR.glob("000_pipeline_*.md")).read_text(encoding="utf-8")
        return exit_code, report

    def test_stops_at_the_first_step_that_does_not_finish(self):
        code, report = self.run_fake({"010_a": 0, "020_b": 2, "030_c": 0})
        self.assertEqual(code, 2)
        self.assertIn("| 010_a | ran |", report)
        self.assertIn("things: 3", report)                                     # the headline, from the manifest
        self.assertIn("| 020_b | stopped |", report)
        self.assertIn("| 030_c | not run |", report)
        self.assertIn("**020_b stopped**", report)
        self.assertIn("[020_b_2026-01-01_0000.md](020_b_2026-01-01_0000.md)", report)
        self.assertTrue(any(rp.LOGS_DIR.glob("000_pipeline_*.log")))

    def test_all_ran(self):
        code, report = self.run_fake({"010_a": 0, "020_b": 0}, ["--from", "010"])
        self.assertEqual(code, 0)
        self.assertIn("**010_a** has 1 warning(s)", report)
        self.assertIn("| Steps requested | --from 010 |", report)

    def test_failure(self):
        code, report = self.run_fake({"010_a": 1})
        self.assertEqual(code, 1)
        self.assertIn("| 010_a | failed |", report)


if __name__ == "__main__":
    unittest.main()
