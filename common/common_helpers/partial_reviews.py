"""
common/common_helpers/partial_reviews.py -- a person's verdicts on partial pairs,
annotations/partial_pair_reviews.csv.

A partial pair (step 070, pairing.py) is a ground truth triple and an extracted
triple whose predicates agree and whose subjects and objects agree only
loosely: one contained in the other as whole words ("MODIS" in "Moderate
Resolution Imaging Spectroradiometer (MODIS)"). That can be fooled ("MODIS"
in "MODIS Terra"), so a person can review each one:

    record_id,ground_truth_subject,ground_truth_predicate,ground_truth_object,
    translated_subject,translated_predicate,translated_object,verdict

    verdict   "same fact" or "not the same fact" (read ignoring case and spacing, as
              the translation table's fixed values are; any other verdict is
              ignored, and step 070 warns about it: review_problems)

The extracted triple is written as translated into the ground truth
schema (as compared_triples.csv shows it), so a verdict stops applying if the
translation table changes that triple. Step 070 never pairs two triples a
person marked "not the same fact"; it counts every partial pair not yet
reviewed. The annotation tool writes the file (Partial pairs), for TUNING
records only: reviewing held-out pairs would mean looking at held-out
results. Triples are compared as common/common_helpers/text_match.norm_text evens them out.
"""
from __future__ import annotations

import csv
from pathlib import Path

from common.step import ANNOTATIONS_DIR
from common.text_match import norm_text
from common.triples_io import REQUIRED

REVIEWS_PATH = ANNOTATIONS_DIR / "partial_pair_reviews.csv"
#: The status of a row of 070's compared_triples.csv (070_evaluate/070_evaluate.md, *Outputs*; the pairs and what
#: pairing leaves without a partner: 070_evaluate/metrics/pairs.md), defined once for step 070, which writes them,
#: and for the status and the annotation tool, which read them.
EXACT_PAIR, PARTIAL_PAIR, EXTRACTED_ONLY, GROUND_TRUTH_ONLY = "exact pair", "partial pair", "extracted only", "ground truth only"
COMPARED_STATUSES = (EXACT_PAIR, PARTIAL_PAIR, EXTRACTED_ONLY, GROUND_TRUTH_ONLY)
#: A pair's status by its pair level (070_evaluate/070_evaluate_helpers/pairing.py, LEVELS).
PAIR_STATUS = {"exact": EXACT_PAIR, "partial": PARTIAL_PAIR}
SLOTS = REQUIRED                                  # subject, predicate, object
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
    """pair_key of a row of the file (or of compared_triples.csv)."""
    return pair_key(row.get("record_id") or "",
                    {s: row.get(f"ground_truth_{s}") for s in SLOTS},
                    {s: row.get(f"translated_{s}") for s in SLOTS})


def verdict_of(row: dict) -> str:
    """A row's verdict, case and spacing aside."""
    return " ".join((row.get("verdict") or "").lower().split())


def _rows(path: Path) -> list:
    """The file's rows, each with "_line" (its line in the file; the header is line 1)."""
    if not Path(path).exists():
        return []
    with open(path, encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        return [{**r, "_line": reader.line_num} for r in reader]


def read_reviews(path: Path = REVIEWS_PATH) -> dict:
    """{pair_key: verdict}, the last row winning if a pair was reviewed twice.
    A missing file means no reviews; a row with another verdict is ignored
    (review_problems lists it)."""
    return {row_key(r): verdict_of(r) for r in _rows(path) if verdict_of(r) in (SAME, NOT_SAME)}


def review_problems(path: Path = REVIEWS_PATH) -> list:
    """Each row whose verdict is neither SAME nor NOT_SAME (case and spacing aside), as "line N (record id): 'verdict'"."""
    return [f"line {r['_line']} ({(r.get('record_id') or '').strip() or 'no record id'}): '{(r.get('verdict') or '').strip()}'"
            for r in _rows(path) if verdict_of(r) not in (SAME, NOT_SAME)]
