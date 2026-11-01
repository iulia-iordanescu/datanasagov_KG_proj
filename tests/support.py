"""
tests/support.py -- what the test files share.

    from support import ROOT, use_step, temp_repo

use_step("070_evaluate") lets a test import that step's helpers by plain
name (import pairing), the way the step's own files import each other.
temp_repo() copies the code into a temporary folder, so a test can run a
step, or write annotations, without touching the repository;
import_from_copy(tmp) then makes that copy's code the one imported.

Importing this file also guards the real annotations/: from then on, in this
Python process, any attempt to write, create, rename, move or delete a file
or folder under the repository's annotations/ is refused with a
PermissionError (an audit hook, so it holds however the test file was
started: run_all.py, `python -m unittest`, or the file itself).
"""
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

#: The folder no test may change: the ground truth, the ground truth schema, the schema additions, the translation
#: table, and the rest of the person-made files.
PROTECTED = ROOT / "annotations"
_PROTECTED = os.path.normcase(os.path.abspath(PROTECTED))

#: Audit events that change the file system, and which of their arguments are paths it changes
#: (https://docs.python.org/3/library/audit_events.html). "open" is handled on its own: only a write is refused.
_CHANGES = {"os.rename": (0, 1), "os.remove": (0,), "os.rmdir": (0,), "os.mkdir": (0,), "os.truncate": (0,),
            "os.utime": (0,), "os.chmod": (0,), "os.link": (1,), "os.symlink": (1,), "shutil.rmtree": (0,),
            "shutil.copyfile": (1,), "shutil.copytree": (1,), "shutil.move": (0, 1), "shutil.copymode": (1,),
            "shutil.copystat": (1,), "shutil.chown": (0,)}
_WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_TRUNC


def is_protected(path) -> bool:
    """Whether a path (str, bytes or path-like; relative ones from the current folder) is annotations/ itself or
    lies inside it. A file descriptor (an int) names no path here."""
    if isinstance(path, int) or path is None:
        return False
    try:
        full = os.path.normcase(os.path.abspath(os.fsdecode(path)))
    except (TypeError, ValueError):
        return False
    return full == _PROTECTED or full.startswith(_PROTECTED + os.sep)


def refused(event: str, args: tuple):
    """The path an audit event would change inside annotations/, or None if it changes nothing there."""
    if event == "open":
        path, mode, flags = (tuple(args) + (None, None, None))[:3]
        writes = ((isinstance(mode, str) and any(c in mode for c in "wax+"))
                  or (isinstance(flags, int) and bool(flags & _WRITE_FLAGS)))
        return path if writes and is_protected(path) else None
    for i in _CHANGES.get(event, ()):
        if i < len(args) and is_protected(args[i]):
            return args[i]
    return None


def _guard(event: str, args: tuple) -> None:
    if event != "open" and event not in _CHANGES:
        return
    path = refused(event, args)
    if path is not None:
        raise PermissionError(f"a test tried to change the real {os.fsdecode(path)} ({event}); tests must work in a "
                              f"temporary copy (support.temp_repo) or on temporary files")


if not getattr(sys, "_kg_annotations_guarded", False):   # one hook per process, even if this file is loaded twice
    sys.addaudithook(_guard)
    sys._kg_annotations_guarded = True

#: Folders no test sweeps: old material kept for reference (never run, never imported), and local-only notes.
EXCLUDED_DIRS = ("archive/", "DONOTTRACK/")

#: The folders a temporary copy needs to run every step and the annotation tool.
CODE = ["common", "helpers", "010_harvest", "020_clean", "030_split", "040_induce_schema",
        "050_annotate", "060_extract", "070_evaluate"]


def use_step(step: str) -> Path:
    """Put <step>/<step>_helpers/ on the import path; return the step folder."""
    folder = ROOT / step / f"{step}_helpers"
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))
    return ROOT / step


#: annotations/ files a temporary copy starts with: copied whole, or only
#: their first line (a CSV file's header; for the additions file, see below).
WHOLE = ("README.md", "ground_truth_schema.txt", "guidelines.md")
HEADER_ONLY = ("component_class_mapping.csv", "partial_pair_reviews.csv", "held_out_looks.csv", "second_opinion.csv")
#: annotations/pending_triples.csv's header (common/common_helpers/left_out.py, PENDING_COLUMNS), for a copy made
#: before the file exists.
PENDING_HEADER = "id,subject,subject_class,predicate,object,object_class,source_text,left_out,question"


def temp_repo(annotations: bool = True) -> Path:
    """A temporary copy of the code. With annotations, annotations/ holds the
    README, the ground truth schema, the person-made CSV files with no rows
    (annotations/pending_triples.csv among them), left_out.md's introduction with no record's section,
    and the additions file's comments with no entries: never the ground
    truth, the pool, or anyone's rows. The caller removes it (shutil.rmtree).
    To import the copy's code, use import_from_copy(tmp)."""
    tmp = Path(tempfile.mkdtemp(prefix="kg_test_"))
    ignore = shutil.ignore_patterns("__pycache__", "*.pyc")
    for name in CODE:
        shutil.copytree(ROOT / name, tmp / name, ignore=ignore)
    (tmp / "docs").mkdir()
    shutil.copy2(ROOT / "docs" / "terminology.md", tmp / "docs" / "terminology.md")   # the annotation tool's term tooltips
    (tmp / "annotations" / "ground_truth").mkdir(parents=True)
    if annotations:
        real = ROOT / "annotations"
        for name in WHOLE:
            shutil.copy2(real / name, tmp / "annotations" / name)
        for name in HEADER_ONLY:
            header = (real / name).read_text(encoding="utf-8-sig").splitlines()[0]
            (tmp / "annotations" / name).write_text(header + "\n", encoding="utf-8")
        # the facts that wait on an expert: none (the header only), and left_out.md's introduction with no section
        pending = real / "pending_triples.csv"
        (tmp / "annotations" / "pending_triples.csv").write_text(
            (pending.read_text(encoding="utf-8-sig").splitlines()[0] if pending.exists() else PENDING_HEADER) + "\n",
            encoding="utf-8")
        intro = (real / "left_out.md").read_text(encoding="utf-8").split("\n## ", 1)[0]
        (tmp / "annotations" / "left_out.md").write_text(intro.rstrip() + "\n", encoding="utf-8")
        comments = [line for line in (real / "schema_additions.txt").read_text(encoding="utf-8-sig").splitlines()
                    if line.startswith("#") or not line.strip()]
        (tmp / "annotations" / "schema_additions.txt").write_text("\n".join(comments).rstrip() + "\n", encoding="utf-8")
    return tmp


#: Packages a temporary copy holds that a test imports by plain name (common, and the helpers' annotator).
COPIED_PACKAGES = ("common", "annotator")


def import_from_copy(tmp: Path) -> None:
    """Make the next `import common...` or `import annotator...` load the copy's code in tmp, not the repository's.
    Every path those modules write to is worked out from their own place on disk, so the copy's code writes into
    the copy. Another test file run earlier in the same process (python -m unittest test_a test_b) may already
    have imported the repository's: those modules are taken out of sys.modules (that file keeps its own
    references, so its tests still run on the repository's code)."""
    sys.path[:0] = [str(tmp), str(tmp / "helpers")]
    for name in list(sys.modules):
        if name.split(".")[0] in COPIED_PACKAGES:
            del sys.modules[name]
