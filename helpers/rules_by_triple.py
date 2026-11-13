"""
rules_by_triple · Which rules of the annotation guidelines each ground truth triple uses, as a doc.

The column `rules` of annotations/ground_truth/batch_*.csv holds, per ground truth triple, the numbers of the rules
of annotations/guidelines.md it uses ("1, 19"). This writes annotations/rules_by_triple.md from it: one section
per record, each ground truth triple with its rule numbers, and each rule those triples use quoted once in full
from the guidelines (their one home). The annotation tool writes the same doc each time it saves a batch.

    py helpers/rules_by_triple.py                      write annotations/rules_by_triple.md
    py helpers/rules_by_triple.py --merge <folder>     put a folder of drafted values into the column, then the doc

A folder of drafted values holds CSV files with the columns file, row, id, subject, predicate, object, rules: file
is the ground truth file's name (batch_003.csv), row the data row's number in it (counted from 1 after the header),
and id, subject, predicate and object the batch row's, checked before anything is written: a row whose id, subject,
predicate or object differ from the batch row at that position is refused, and nothing is written while any row is.
Free: no model calls. Writes only the files named above.

Reads:   annotations/ground_truth/batch_*.csv, annotations/guidelines.md, annotations/left_out.md
Writes:  annotations/rules_by_triple.md; with --merge, annotations/ground_truth/batch_*.csv (the rules cells only)
Details: common/common_helpers/rules_by_triple.py
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))                                                  # the repository folder, for common/

from common import console                                                     # noqa: E402
from common.rules_by_triple import COMMAND, DOC_PATH, file_problems, merge_drafts, write_doc   # noqa: E402
from common.step import repo_path                                              # noqa: E402


def main() -> int:
    console.setup()
    parser = argparse.ArgumentParser(prog=COMMAND, description="Write annotations/rules_by_triple.md: which rules of "
                                     "the annotation guidelines each ground truth triple uses.")
    parser.add_argument("--merge", metavar="FOLDER", help="a folder of CSV files of drafted values (columns file, row, "
                        "id, subject, predicate, object, rules) to put into the ground truth files' rules column first")
    args = parser.parse_args()
    if args.merge:
        done = merge_drafts(Path(args.merge))
        if done["problems"]:
            print(f"Nothing was written: {len(done['problems'])} problem(s) in the drafted values, each to fix first:")
            for p in done["problems"]:
                print(f"  - {p}")
            return 1
        for name, n in done["written"].items():
            print(f"annotations/ground_truth/{name}: {n} rules cell(s) changed")
        if not done["written"]:
            print("The ground truth files already held every drafted value: nothing changed in them.")
    problems = file_problems()
    if problems:
        print(f"{len(problems)} problem(s) in the rules column, each to fix first (the doc is still written):")
        for p in problems:
            print(f"  - {p}")
    print(f"{repo_path(DOC_PATH)}: {'written' if write_doc() else 'already up to date'}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
