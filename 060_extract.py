"""
060 · Extract

Extracts, from each record's text, the facts a schema can express: a model
lists them as triple instances in ONLY the schema's names; code checks every
one against the record's text and the schema, keeps it, or removes it with
a reason. The schema is 040's induced schema by default (or any schema given
with --schema), plus the entity classes and predicates added by hand in
annotations/schema_additions.txt. By default only the finished records of
the ground truth are extracted from, which is what 070 scores; every record
once the schema is final. Terms: docs/terminology.md.

Reads:   records.jsonl (020), the_schema.json (040),
         annotations/schema_additions.txt, annotations/ground_truth/
Writes:  extracted_triples.csv, extracted_triples_removed.csv,
         schema_used.json, extracted_triples_details.json
Details: instructions/060_extract.md
"""
from common.llm import MODEL
from common.step import run_step, helpers

INPUTS = {
    "records":      "020_clean/records.jsonl",
    "schema":       "040_induce_schema/the_schema.json",
    "additions":    "./annotations/schema_additions.txt",
    "ground_truth": "./annotations/ground_truth/batch_*.csv",
}

SETTINGS = {
    "extract_from":       "ground_truth",  # ground_truth (the finished records 070 scores) or all
    "ids":                "",              # or exactly these records: ids separated by commas, or a file with one per line
    "max_chars":          8000,            # a longer text is split into text pieces, one call each
    "workers":            4,               # model calls made at the same time
    "model":              MODEL,           # the AI model to ask (py models.py lists them)
    "confirm_paid_calls": True,            # stop and ask before the first model call; false for unattended runs
}

extract = helpers("060_extract")


def main(inputs, settings, output):
    chosen  = extract.pick_records(inputs, settings)                 # code: the finished ground truth records, by default
    schema  = extract.load_schema(inputs)                            # code: 040's schema plus your additions
    calls   = extract.paid_calls(chosen, schema, settings, output)   # code: asks before paying; keeps every answer in cache/
    replies = extract.ask_model(chosen, schema, calls, settings)     # LLM: "MODIS" (Instrument) ABOARD "Aqua" (Spacecraft)
    rows    = extract.sort_rows(chosen, schema, replies)             # code: checked; kept, or removed with a reason
    # writes the kept and removed rows, the schema used, the details; the report
    return extract.results(chosen, schema, replies, rows, calls, settings, output)


if __name__ == "__main__":
    run_step("060_extract", INPUTS, SETTINGS, main)
