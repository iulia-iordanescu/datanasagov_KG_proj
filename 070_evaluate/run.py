"""
070 · Evaluate

Evaluates what 060 extracted against the ground truth: precision (when
060 says something, how often it is right) and recall (of the triples in the
ground truth, how many 060 found), each with its margin of error. 060's
component classes are first translated into the ground truth vocabulary,
through a table a person checks. Only the fair part of the ground truth is evaluated, and only
its tuning part by default; the held-out part is kept for the end. Terms:
docs/terminology.md, section "Evaluating extraction".

Reads:   records.jsonl (020), splits.json (030), extracted_triples.csv,
         extracted_triples_details.json and schema_used.json (060),
         annotations/ground_truth_candidates.csv,
         annotations/schema_derived_from_manual_annotation.txt,
         annotations/ground_truth/, annotations/component_class_mapping.csv,
         annotations/partial_pair_reviews.csv
Writes:  metrics.json, per_record.md, compared_triples.csv; adds rows to
         annotations/component_class_mapping.csv and, with --evaluate_held_out true, a line
         to annotations/held_out_looks.csv (never changing an existing one)
Details: 070_evaluate/070_evaluate.md
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # the repository folder, for common/

from common.llm import MODEL
from common.step import load_moves, run_step

INPUTS = {
    "records":            "020_clean/records.jsonl",
    "splits":             "030_split/splits.json",
    "extracted_triples":  "060_extract/extracted_triples.csv",
    "extracted_triples_details": "060_extract/extracted_triples_details.json",
    "schema_used":        "060_extract/schema_used.json",
    "candidates":         "./annotations/ground_truth_candidates.csv",
    "hand_schema":        "./annotations/schema_derived_from_manual_annotation.txt",
    "ground_truth":       "./annotations/ground_truth/batch_*.csv",
    "component_class_mapping":       "./annotations/component_class_mapping.csv",
    "partial_reviews":    "./annotations/partial_pair_reviews.csv",
}

SETTINGS = {
    "evaluate_held_out":     False,  # also show the held-out part's numbers (for the end; each look is logged)
    "model":              MODEL,  # the AI model to ask (py helpers/models.py lists them)
    "confirm_paid_calls": True,   # stop and ask before the first model call; false for unattended runs
}

evaluate = load_moves("070_evaluate")


def main(inputs, settings, output):
    evaluated = evaluate.pick_records(inputs, settings)              # code: finished, extracted, in the fair part
    calls     = evaluate.paid_calls(evaluated, settings, output)     # code: asks before paying; keeps every answer in cache/
    translation     = evaluate.translate_component_classes(inputs, evaluated, calls)   # LLM: Satellite → Spacecraft, new component classes only (+ suggestions for (none) rows); you check
    evaluated = evaluate.compare(evaluated, translation)                   # code: per record, exact pairs / partial pairs / extracted only / ground truth only
    metrics   = evaluate.compute_metrics(evaluated, settings)        # code: the numbers, with margins, per part and group
    # writes metrics.json, per_record.md, compared_triples.csv; the report
    return evaluate.results(evaluated, translation, metrics, calls, settings, output)


if __name__ == "__main__":
    run_step("070_evaluate", INPUTS, SETTINGS, main)
