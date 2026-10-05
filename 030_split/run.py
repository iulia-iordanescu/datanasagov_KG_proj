"""
030 · Split

Sets the two lists of records the later steps work on, and keeps them
apart: the ground truth candidates pool, 1,000 records a person annotates in
order (only a subset ever is), and the induction candidates, the records the
schema may be learned from. No record is ever in both, so the extraction is
scored on text the schema was not learned from. Each pool record is also marked
tuning or held-out, for scoring in 070 (a fixed rule by pool position: from
position 6 on, every third is held-out). Terms: docs/terminology.md.

Both lists are in a fixed random order, and later steps take from the top,
so taking more later keeps what was already taken (and paid for).

The pool is not drawn here: it was drawn once, on 2026-09-21, and is kept in
annotations/. The induction candidates are ordered here. Both are written to
splits.json once, and kept after that.

Reads:   records.jsonl (020), annotations/ground_truth_candidates.csv
Writes:  splits.json
Details: 030_split/030_split.md
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # the repository folder, for common/

from common.step import load_moves, run_step

INPUTS = {
    "records":    "020_clean/records.jsonl",
    "candidates": "./annotations/ground_truth_candidates.csv",
}

SETTINGS = {
    "induction_seed": 7,   # fixes the random order of the induction candidates
}

split = load_moves("030_split")


def main(inputs, settings, output):
    records   = split.load_records(inputs)                            # code: 020's cleaned records, by id
    pool      = split.ground_truth_candidates(inputs, records)        # code: the 1,000 candidates, in order, tuning or held-out
    induction = split.induction_candidates(records, pool, settings)   # code: each maintainer's other records, shuffled
    split.check_disjoint(pool, induction)                             # code: no record in both
    # writes splits.json (once); the report
    return split.results(pool, induction, inputs, settings, output)


if __name__ == "__main__":
    run_step("030_split", INPUTS, SETTINGS, main)
