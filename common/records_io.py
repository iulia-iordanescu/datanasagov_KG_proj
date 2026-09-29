"""
common/records_io.py -- reads the cleaned records 020_clean writes.

    outputs/intermediate_results/020_clean/records.jsonl   one record per line

Every step after 020 reads that file; this is the one place that does, so
they all read it the same way. The record format is described in
instructions/020_clean.md.

    from common.records_io import load_records, has_text, read_ids
    records = load_records(inputs["records"])      # {id: record}, in file order
    ids = read_ids(settings["ids"])                # a step's "ids" setting (050, 060)
"""
from __future__ import annotations

import json
import re
from pathlib import Path

#: The free-text fields every record has (020 always writes them).
TEXT_FIELDS = ("title", "notes")


def load_records(path) -> dict:
    """{id: record}, in the file's order. A repeated id stops the step: 020
    keeps each catalog entry once, so a repeat means the file was edited or
    is not 020's output."""
    records = {}
    with open(Path(path), encoding="utf-8") as fh:
        for number, line in enumerate(fh, 1):
            if not line.strip():
                continue
            record = json.loads(line)
            rid = record["id"]
            if rid in records:
                raise ValueError(f"{Path(path).name} line {number}: id {rid} appears twice")
            records[rid] = record
    return records


def has_text(record: dict) -> bool:
    """Whether the record has any title or notes text for a model to read."""
    return any((record.get(name) or "").strip() for name in TEXT_FIELDS)


def read_ids(value: str) -> list:
    """The ids setting: ids separated by commas or spaces, or the path of a
    text file with one id per line (a CSV whose first column is the id works
    too; a header line "id", blank lines and lines starting with # are
    skipped). An id listed twice counts once."""
    value = value.strip()
    if not value:
        return []
    looks_like_file = value.lower().endswith((".txt", ".csv")) or "/" in value or "\\" in value
    if looks_like_file:
        path = Path(value)
        if not path.is_file():
            raise ValueError(f"ids names the file {value}, which doesn't exist")
        ids = []
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            first = line.split(",")[0].strip().strip('"')
            if first and not first.startswith("#") and first.lower() != "id":
                ids.append(first)
    else:
        ids = [i for i in re.split(r"[,\s]+", value) if i]
    return list(dict.fromkeys(ids))
