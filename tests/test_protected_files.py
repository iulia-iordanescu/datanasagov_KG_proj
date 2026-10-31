"""No test changes the real annotations/, however it is started: support.py, which every test file imports,
refuses any write, creation, rename, move or deletion there (an audit hook), and the annotation tool's tests
import the temporary copy's code even when another test file, run first in the same process, imported the
repository's. With the near misses: reading is allowed, and so are folders that only look like annotations/."""
import ast
import os
import shutil
import subprocess
import sys
import unittest
import warnings
from pathlib import Path

import support
from support import PROTECTED, ROOT, is_protected, refused

HERE = Path(__file__).resolve().parent
#: The real files the tests must never change.
REAL = sorted((PROTECTED / "ground_truth").glob("*.csv")) + [PROTECTED / "schema_additions.txt",
                                                              PROTECTED / "ground_truth_schema.txt",
                                                              PROTECTED / "component_class_mapping.csv"]
#: A folder that doesn't exist, so a probe that got past the guard would fail on its own and change nothing.
NOWHERE = PROTECTED / "no_such_folder_for_the_guard_test"


class A_Refused(unittest.TestCase):

    def test_attempts_are_refused(self):
        """Each way of changing a file there stops with PermissionError (without the guard: FileNotFoundError)."""
        self.assertFalse(NOWHERE.exists())
        probe = NOWHERE / "probe.csv"
        attempts = {"open w": lambda: open(probe, "w"),
                    "open a": lambda: open(probe, "a"),
                    "open r+": lambda: open(probe, "r+"),
                    "write_text": lambda: probe.write_text("x"),
                    "os.open": lambda: os.open(probe, os.O_WRONLY | os.O_CREAT),
                    "rename from": lambda: os.rename(probe, NOWHERE / "other.csv"),
                    "replace into": lambda: os.replace(HERE / "no_such_file.csv", probe),
                    "remove": lambda: os.remove(probe),
                    "unlink": lambda: probe.unlink(),
                    "rmdir": lambda: os.rmdir(NOWHERE),
                    "rmtree": lambda: shutil.rmtree(NOWHERE),
                    "copyfile into": lambda: shutil.copyfile(HERE / "support.py", probe)}
        for what, attempt in attempts.items():
            with self.subTest(what), self.assertRaises(PermissionError) as caught:
                attempt()
            self.assertIn("temporary copy", str(caught.exception))
        self.assertFalse(NOWHERE.exists())

    def test_every_real_file_is_covered(self):
        self.assertTrue(any(p.parent.name == "ground_truth" for p in REAL))
        for path in REAL:
            for mode in ("w", "a", "x", "r+", "wb", "ab"):
                self.assertEqual(refused("open", (str(path), mode, 0)), str(path), (path, mode))
            self.assertIsNotNone(refused("open", (str(path), None, os.O_WRONLY | os.O_TRUNC)))   # os.open
            self.assertIsNotNone(refused("os.rename", (str(HERE / "x"), str(path), -1, -1)))     # replaced
            self.assertIsNotNone(refused("os.rename", (str(path), str(HERE / "x"), -1, -1)))     # moved away
            self.assertIsNotNone(refused("os.remove", (str(path), -1)))
            self.assertIsNotNone(refused("os.utime", (str(path), None, None, -1)))
        self.assertTrue(is_protected(PROTECTED))
        self.assertTrue(is_protected(os.fsencode(PROTECTED / "ground_truth" / "batch_000.csv")))      # bytes


class B_NearMisses(unittest.TestCase):

    def test_reading_is_allowed(self):
        for path in REAL:
            self.assertIsNone(refused("open", (str(path), "r", os.O_RDONLY)))
            self.assertIsNone(refused("open", (str(path), "rb", os.O_RDONLY)))
            with open(path, "rb") as fh:                                           # really, through the guard
                fh.read(1)

    def test_lookalikes_are_allowed(self):
        tmp = support.temp_repo(annotations=False)
        try:
            for path in (ROOT / "annotations_old" / "batch_000.csv", ROOT / "annotations.csv",
                         ROOT / "annotations" / ".." / "outputs" / "x.csv", tmp / "annotations" / "schema_additions.txt",
                         HERE / "annotations" / "x.csv"):
                self.assertFalse(is_protected(path), path)
                self.assertIsNone(refused("open", (str(path), "w", 0)), path)
            (tmp / "annotations" / "ground_truth" / "batch_000.csv").write_text("a copy's file\n")   # really allowed
        finally:
            shutil.rmtree(tmp)
        self.assertIsNone(refused("open", (3, "w", 0)))                            # a file descriptor: no path
        self.assertIsNone(refused("os.listdir", (str(PROTECTED),)))                # not a change

    def test_relative_paths_from_the_current_folder(self):
        here = os.getcwd()
        try:
            os.chdir(ROOT)
            self.assertTrue(is_protected("annotations/ground_truth/batch_000.csv"))
            os.chdir(HERE)
            self.assertFalse(is_protected("annotations/ground_truth/batch_000.csv"))   # tests/ has no such folder
        finally:
            os.chdir(here)

    def test_case_on_windows(self):
        upper = str(PROTECTED).upper() + os.sep + "SCHEMA_ADDITIONS.TXT"
        self.assertEqual(is_protected(upper), os.name == "nt")           # Windows paths ignore case; others don't


def imports_support_first(source: str) -> bool:
    """Whether a test file imports support at the top level before any module of common/ or the helpers."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SyntaxWarning)            # another file's escapes are not checked here
        tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.Import) and any(a.name.split(".")[0] == "support" for a in node.names):
            return True
        if isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[0] == "support":
            return True
        names = [a.name for a in node.names] if isinstance(node, ast.Import) else \
            [node.module or ""] if isinstance(node, ast.ImportFrom) else []
        if any(n.split(".")[0] in ("common", "annotator", "review_page") for n in names):
            return False
    return False


class C_EveryTestFile(unittest.TestCase):

    def test_every_test_file_imports_support_first(self):
        """So the guard is on in every process that runs a test file, whichever way it was started."""
        files = sorted(HERE.glob("test_*.py"))
        self.assertGreater(len(files), 10)
        for f in files:
            self.assertTrue(imports_support_first(f.read_text(encoding="utf-8")), f.name)

    def test_the_check_near_misses(self):
        self.assertTrue(imports_support_first("import os\nfrom support import ROOT\nfrom common import x\n"))
        self.assertTrue(imports_support_first("import support\n"))
        self.assertFalse(imports_support_first("from common import x\nfrom support import ROOT\n"))   # too late
        self.assertFalse(imports_support_first("import os\n"))
        self.assertFalse(imports_support_first("def f():\n    from support import ROOT\n"))           # not top level
        self.assertFalse(imports_support_first("from supporting import x\n"))

    def test_annotation_tool_after_another_file(self):
        """The case that once wrote into the real ground truth and schema additions: a test file that imports the
        repository's common/ runs first in the same process, then the annotation tool's tests. The tool must still
        get the temporary copy's paths, and the tests must pass (the guard would fail any write here)."""
        script = ("import sys, shutil; import support; import common.step as s; "
                  "print('first', s.ROOT); import test_annotator as t; "
                  "ok = all(p.resolve().is_relative_to(t.TMP.resolve()) for p in "
                  "(t.server.ANNOTATIONS_DIR, t.server.ADDITIONS, t.server.GROUND_TRUTH_DIR, t.server.MAPPING_PATH, "
                  "t.server.GROUND_TRUTH_SCHEMA, t.server.REVIEWS_PATH)); "
                  "shutil.rmtree(t.TMP); print('copy', ok)")
        run = subprocess.run([sys.executable, "-c", script], cwd=HERE, capture_output=True, text=True,
                             encoding="utf-8", timeout=120)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn(f"first {ROOT}", run.stdout)                  # the repository's common/ was imported first
        self.assertIn("copy True", run.stdout)
        run = subprocess.run([sys.executable, "-m", "unittest", "test_schema_io", "test_annotator"], cwd=HERE,
                             capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=240)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)


if __name__ == "__main__":
    unittest.main()
