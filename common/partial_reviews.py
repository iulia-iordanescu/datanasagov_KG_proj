"""
common/partial_reviews.py -- a person's verdicts on partial pairs,
annotations/partial_pair_reviews.csv.

A partial pair (step 070, match.py) is a ground truth triple and an extracted
triple whose predicates agree and whose subjects and objects agree only
loosely: one contained in the other as whole words ("MODIS" in "Moderate
Resolution Imaging Spectroradiometer (MODIS)"). That can be fooled ("MODIS"
in "MODIS Terra"), so a person can review each one:

    record_id,ground_truth_subject,ground_truth_predicate,ground_truth_object,
    translated_subject,translated_predicate,translated_object,verdict

    verdict   "same fact" or "not the same fact"

The extracted triple is written as translated into the ground truth
vocabulary (as matches.csv shows it), so a verdict stops applying if the
translation table changes that triple. Step 070 never pairs two triples a
person marked "not the same fact"; it counts every partial pair not yet
reviewed. The annotation tool writes the file (Partial pairs), for TUNING
records only: reviewing held-out pairs would mean looking at held-out
results. Triples are compared as common/text_match.norm_text evens them out.
"""
from __future__ import annotations

import csv
from pathlib import Path

from common.step import ANNOTATIONS_DIR
from common.text_match import norm_text

REVIEWS_PATH = ANNOTATIONS_DIR / "partial_pair_reviews.csv"
SLOTS = ("subject", "predicate", "object")
COLUMNS = (["record_id"] + [f"ground_truth_{s}" for s in SLOTS] + [f"translated_{s}" for s in SLOTS]
           + ["verdict"])
SAME, NOT_SAME = "same fact", "not the same fact"


def pair_key(record_id: str, gt: dict, translated: dict) -> tuple:
    """The key a verdict is filed under: the record and both triples' subject,
    predicate and object, evened out. gt and translated are triples with
    "subject", "predicate", "object"."""
    return (record_id.strip(),) + tuple(norm_text(gt.get(s)) for s in SLOTS) \
        + tuple(norm_text(translated.get(s)) for s in SLOTS)


def row_key(row: dict) -> tuple:
    """pair_key of a row of the file (or of matches.csv)."""
    return pair_key(row.get("record_id") or "",
                    {s: row.get(f"ground_truth_{s}") for s in SLOTS},
                    {s: row.get(f"translated_{s}") for s in SLOTS})


def read_reviews(path: Path = REVIEWS_PATH) -> dict:
    """{pair_key: verdict}, the last row winning if a pair was reviewed twice.
    A missing file means no reviews; a row with another verdict is ignored."""
    if not Path(path).exists():
        return {}
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return {row_key(r): r["verdict"].strip() for r in csv.DictReader(fh)
                if (r.get("verdict") or "").strip() in (SAME, NOT_SAME)}
