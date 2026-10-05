"""
020 · Clean

Turns the raw catalog records into clean ones: each catalog entry is kept
once (a record fetched twice, because the catalog changed mid-harvest, keeps
its first copy; a record with no id is dropped); HTML in the text fields
becomes plain text, checked so that no word, number or URL is lost; the
spellings of one maintainer are joined into one name; and each field is kept
under its own key, so later steps never have to guess where a title ends and
a description begins. Terms: docs/terminology.md.

Reads:   batch_*.json (010)
Writes:  records.jsonl
Details: 020_clean/020_clean.md
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # the repository folder, for common/

from common.step import load_moves, run_step

INPUTS = {
    "batches": "010_harvest/batch_*.json",
}

SETTINGS = {
    "extra_text_fields": "",     # free-text fields to clean and save besides title and notes, e.g. "author"
    "join_maintainers":  True,   # join spellings of one maintainer into one name
}

clean = load_moves("020_clean")


def main(inputs, settings, output):
    records = clean.load_raw(inputs, settings)           # code: batch files → one list; id-less and repeated records dropped
    records = clean.keep_fields(records)                 # code: each field under its own key: title, notes, maintainer, tags…
    records = clean.clean_text(records)                  # code: "&lt;b&gt;Aqua&lt;/b&gt;" → "Aqua", nothing lost
    records = clean.join_maintainers(records, settings)  # code: "KRISTAN MORGAN" = "Kristan Morgan"
    # writes records.jsonl; the report
    return clean.results(records, output)


if __name__ == "__main__":
    run_step("020_clean", INPUTS, SETTINGS, main)
