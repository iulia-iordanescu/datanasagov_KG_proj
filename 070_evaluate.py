"""
070 · Evaluate

Scores what step 060 extracted against the ground truth: precision (when
060 says something, how often it is right) and recall (of the facts in the
ground truth, how many 060 found), each with its margin of error. 060's
names are first translated into the ground truth's names, through a table a
person checks. Only the fair part of the ground truth is scored, and only
its tuning part by default; the held-out part is kept for the end. Terms:
docs/terminology.md, section "Scoring extraction".

Reads:   060's extracted_triples.csv, extraction_details.json and
         schema_used.json; splits.json (030); records.jsonl (020);
         annotations/ground_truth/, ground_truth_candidates.csv, the
         hand-built schema, name_mapping.csv
Writes:  scores.json, per_record.md, matches.csv; adds rows to
         annotations/name_mapping.csv and, with --score_held_out true, a line
         to annotations/held_out_looks.csv (never changing an existing one)
Details: instructions/070_evaluate.md
"""
from common.step import run_step, helpers

INPUTS = {
    "extracted":          "060_extract/extracted_triples.csv",
    "extraction_details": "060_extract/extraction_details.json",
    "schema_used":        "060_extract/schema_used.json",
    "splits":             "030_split/splits.json",
    "records":            "020_clean/records.jsonl",
    "ground_truth":       "./annotations/ground_truth/batch_*.csv",
    "candidates":         "./annotations/ground_truth_candidates.csv",
    "hand_schema":        "./annotations/schema_derived_from_manual_annotation.txt",
    "name_mapping":       "./annotations/name_mapping.csv",
}

SETTINGS = {
    "score_held_out":     False,  # also show the held-out part's numbers (for the end; each look is logged)
    "confirm_paid_calls": True,   # stop and ask before a model call (only to propose name translations)
}

evaluate = helpers("070_evaluate")


def main(inputs, settings, output):
    scored = evaluate.pick_records(inputs, settings)                  # finished, extracted, in the fair part
    calls  = evaluate.paid_calls(scored, settings, output)            # asks before paying; answers in cache/
    names  = evaluate.translate_names(inputs, scored, calls)          # 060's names -> yours: Satellite -> Spacecraft
    scored = evaluate.compare(scored, names)                          # per record: exact / partial / wrong / missed
    scores = evaluate.score(scored, settings)                         # the numbers, with margins, per part and group
    return evaluate.results(scored, names, scores, calls, settings, inputs, output)


if __name__ == "__main__":
    run_step("070_evaluate", INPUTS, SETTINGS, main)
