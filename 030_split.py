"""
030 · Split

Sets the two samples of records the later steps work on, and keeps them
apart: the ground truth candidates pool, 1,000 records a person annotates in
order (only a subset ever is), and the induction sample, the records the
schema is learned from. No record is ever in both, so the extraction is
scored on text the schema was not learned from.

The pool is not drawn here: it was drawn once, on 2026-09-21, and is kept in
annotations/. The induction sample is drawn here. Both are written to
splits.json once, and kept after that.

Reads:   records.jsonl (020), annotations/ground_truth_candidates.csv
Writes:  splits.json
Details: instructions/030_split.md
"""
from common.step import run_step, helpers

INPUTS = {
    "records":    "020_clean/records.jsonl",
    "candidates": "./annotations/ground_truth_candidates.csv",
}

SETTINGS = {
    "induction_maintainers": 10,  # the induction sample comes from this many of the largest maintainers
    "texts_per_maintainer":  15,  # records sampled from each of them
    "induction_seed":        7,   # fixes the random draw, so a rerun draws the same records
}

split = helpers("030_split")


def main(inputs, settings, output):
    records   = split.load_records(inputs)                              # 36,375 cleaned records, by id
    pool      = split.ground_truth_candidates(inputs, records)          # the 1,000 candidates, in order; gone ones dropped
    induction = split.induction_sample(records, pool, settings)         # 15 each from the 10 largest maintainers, none from the pool
    split.check_disjoint(pool, induction)                               # no record in both samples
    return split.results(pool, induction, inputs, settings, output)     # splits.json (kept if it exists); report


if __name__ == "__main__":
    run_step("030_split", INPUTS, SETTINGS, main)
