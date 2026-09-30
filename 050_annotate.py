"""
050 · Annotate

Drafts ground truth for a person to correct. A model reads the next records
of the ground truth candidates pool and lists every fact each one states, as
triple instances with entity classes, using the hand-built schema's names
where they fit and new ones where they don't; code adds each record's
DESCRIBES row and checks every row against the record's text and the schema.
Each run writes one numbered draft batch. The person corrects it with the
annotation tool (py annotate.py), which saves it into annotations/ground_truth/;
no step writes there. Terms: docs/terminology.md.

Reads:   records.jsonl (020), splits.json (030),
         annotations/schema_derived_from_manual_annotation.txt,
         annotations/ground_truth/ (to skip records already done, and to check it)
Writes:  drafted_triples_batch<N>.csv, drafted_triples_batch<N>_details.json
Details: instructions/050_annotate.md
"""
from common.step import run_step, helpers

INPUTS = {
    "records":      "020_clean/records.jsonl",
    "splits":       "030_split/splits.json",
    "hand_schema":  "./annotations/schema_derived_from_manual_annotation.txt",
    "ground_truth": "./annotations/ground_truth/batch_*.csv",
}

SETTINGS = {
    "records_per_batch":  10,    # how many records to draft this run
    "start_position":     0,     # the pool position to start from (records already done are skipped)
    "ids":                "",    # or exactly these records: ids separated by commas, or a file with one per line
    "max_chars":          8000,  # a longer text is split into pieces, one call each
    "workers":            4,     # model calls made at the same time
    "confirm_paid_calls": True,  # stop and ask before the first model call; false for unattended runs
}

annotate = helpers("050_annotate")


def main(inputs, settings, output):
    chosen  = annotate.pick_records(inputs, settings, output)     # code: the next 10 of the pool, skipping done ones
    calls   = annotate.paid_calls(chosen, settings, output)       # asks before paying; keeps every answer in cache/
    replies = annotate.ask_model(chosen, calls, settings)         # LLM: every fact each record states
    drafts  = annotate.build_rows(chosen, replies)                # code: DESCRIBES row, duplicates out, checks
    typos   = annotate.check_ground_truth(chosen)                 # code: rows of your ground truth to fix
    # writes the draft batch; the report
    return annotate.results(chosen, replies, drafts, typos, calls, settings, output)


if __name__ == "__main__":
    run_step("050_annotate", INPUTS, SETTINGS, main)
