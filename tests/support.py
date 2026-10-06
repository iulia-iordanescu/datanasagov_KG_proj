"""
tests/support.py -- what the test files share.

    from support import ROOT, use_step, temp_repo

use_step("070_evaluate") lets a test import that step's helpers by plain
name (import pairing), the way the step's own files import each other.
temp_repo() copies the code into a temporary folder, so a test can run a
step, or write annotations, without touching the repository.
"""
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

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
WHOLE = ("README.md", "schema_derived_from_manual_annotation.txt")
HEADER_ONLY = ("component_class_mapping.csv", "partial_pair_reviews.csv", "held_out_looks.csv")


def temp_repo(annotations: bool = True) -> Path:
    """A temporary copy of the code. With annotations, annotations/ holds the
    README, the hand-built schema, the person-made CSV files with no rows,
    and the additions file's comments with no entries: never the ground
    truth, the pool, or anyone's rows. The caller removes it (shutil.rmtree).
    (No module of common/ is imported here: a test that imports the copy's
    code must be the first to import it.)"""
    tmp = Path(tempfile.mkdtemp(prefix="kg_test_"))
    ignore = shutil.ignore_patterns("__pycache__", "*.pyc")
    for name in CODE:
        shutil.copytree(ROOT / name, tmp / name, ignore=ignore)
    (tmp / "annotations" / "ground_truth").mkdir(parents=True)
    if annotations:
        real = ROOT / "annotations"
        for name in WHOLE:
            shutil.copy2(real / name, tmp / "annotations" / name)
        for name in HEADER_ONLY:
            header = (real / name).read_text(encoding="utf-8-sig").splitlines()[0]
            (tmp / "annotations" / name).write_text(header + "\n", encoding="utf-8")
        comments = [line for line in (real / "schema_additions.txt").read_text(encoding="utf-8-sig").splitlines()
                    if line.startswith("#") or not line.strip()]
        (tmp / "annotations" / "schema_additions.txt").write_text("\n".join(comments).rstrip() + "\n", encoding="utf-8")
    return tmp
