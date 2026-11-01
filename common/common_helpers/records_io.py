"""
common/common_helpers/records_io.py -- reads the cleaned records 020_clean writes.

    outputs/intermediate_results/020_clean/records.jsonl   one record per line

Every step after 020 reads that file; this is the one place that does, so
they all read it the same way. The record format is described in
020_clean/020_clean.md.

    from common.records_io import load_records, text_fields, full_text, has_text, read_ids
    records = load_records(inputs["records"])      # {id: record}, in file order
    ids = read_ids(settings["ids"])                # a step's "ids" setting (050, 060)

It also finds a record elsewhere: its saved copy from step 010's harvest
(saved_copy, harvest_date), and its web page in the live catalog
(catalog_page_link).
"""
from __future__ import annotations

import functools
import json
import re
from pathlib import Path

from common.step import MANIFEST_NAME, RESULTS_DIR, repo_path
from common.stop import Stop
from common.text_match import even

#: Why 050 or 060 skips a record it was asked for, the two reasons both steps share (each step adds its own), and
#: what to do about a record without text.
NOT_IN_CATALOG, WITHOUT_TEXT = "not in the catalog", "without text"
WITHOUT_TEXT_TO_DO = "Nothing to do: a record without text has nothing for the model to read."

#: The free-text fields every record has (020 always writes them).
TEXT_FIELDS = ("title", "notes")
#: The field 020 writes with which method cleaned each text field: its keys are the record's text fields (TEXT_FIELDS,
#: then the extra_text_fields setting's), in the order 020 wrote them.
CLEANING_FIELD = "_cleaning"

#: A record's web page in the live catalog, by its id (the catalog also
#: answers /dataset/<name>, but the name can change and the id doesn't).
CATALOG_PAGE_URL = "https://data.nasa.gov/dataset/{id}"


def catalog_page_link(rid: str) -> str:
    """The address of the record's web page in the live catalog. Only built,
    never fetched: the page may since have been removed or moved."""
    return CATALOG_PAGE_URL.format(id=rid)


#: Step 010's folder: the harvest's batch_*.json files and its manifest.
HARVEST_DIR = RESULTS_DIR / "010_harvest"
#: How a cleaned record's _origin names its entry in the harvest (common/common_helpers/audit.py).
HARVEST_REF = re.compile(r"010_harvest/(batch_\d+\.json)#(.+)")


def harvest_file(record: dict, harvest_dir: Path = HARVEST_DIR) -> Path | None:
    """The harvest's batch file that holds the record, from its _origin, or
    None when the record names none or the file isn't on this computer. Only
    a batch_<digits>.json name in harvest_dir is ever returned."""
    for ref in record.get("_origin") or []:
        m = HARVEST_REF.fullmatch(ref)
        if m and m.group(2) == record.get("id") and (harvest_dir / m.group(1)).is_file():
            return harvest_dir / m.group(1)
    return None


@functools.lru_cache(maxsize=2)
def _harvest_batch(path: Path, mtime: float) -> dict:
    """{id: raw record} of one batch file (each about 7 MB); the last two read are kept."""
    return {r["id"]: r for r in json.loads(path.read_text(encoding="utf-8"))["records"]}


def saved_copy(record: dict, harvest_dir: Path = HARVEST_DIR) -> dict | None:
    """The record's entry exactly as step 010 saved it from the catalog, or
    None when its batch file isn't on this computer or doesn't hold it."""
    path = harvest_file(record, harvest_dir)
    return _harvest_batch(path, path.stat().st_mtime).get(record["id"]) if path else None


def harvest_date(harvest_dir: Path = HARVEST_DIR) -> str | None:
    """The saved harvest's date, from step 010's manifest (e.g. "2026-10-01"),
    or None when the manifest isn't on this computer or has none."""
    try:
        return json.loads((harvest_dir / MANIFEST_NAME).read_text(encoding="utf-8")).get("harvest_date")
    except (OSError, ValueError):
        return None


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
                raise Stop(f"{repo_path(path)} line {number}: id {rid} appears twice, so the step can't tell which "
                           f"record is right (020_clean writes each record once: the file was edited, or isn't "
                           f"020_clean's output). Run `py 020_clean/run.py` again, then run the step again.")
            records[rid] = record
    return records


def text_fields(record: dict) -> list:
    """The record's text fields, in the order 020 wrote them: the ones its CLEANING_FIELD lists (title, notes, then
    the extra ones), else title and notes."""
    return list(record.get(CLEANING_FIELD) or TEXT_FIELDS)


def full_text(record: dict) -> str:
    """The record's whole text, what a model reads (common/common_helpers/chunking.py cuts it into text pieces):
    each non-empty text field, preceded by its field name."""
    return "\n\n".join(f"{name}: {record[name].strip()}" for name in text_fields(record)
                       if (record.get(name) or "").strip())


def has_text(record: dict) -> bool:
    """Whether the record has any text for a model to read: the same fields as full_text (so a record whose only text
    is in an extra text field has text), and blank once evened out (common.text_match.even: an invisible format
    character such as a zero-width space or a byte-order mark, or a no-break space, is no text). The one
    definition: 020's count, 030's induction candidates, 050, 060 and 070 use it."""
    return bool(even(" ".join((record.get(name) or "") for name in text_fields(record))).strip())


def read_ids(value: str) -> list:
    """The ids setting: ids separated by commas or spaces, or the path of a
    text file with one id per line (a CSV whose first column is the id works
    too; a header line "id", blank lines, and lines starting with # are
    skipped). An id listed twice counts once. A value ending in .txt or .csv, or
    holding a / or \\, is a path. Written once for a person in
    docs/running_on_nasa_laptop.md, *Settings several steps share*."""
    value = value.strip()
    if not value:
        return []
    looks_like_file = value.lower().endswith((".txt", ".csv")) or "/" in value or "\\" in value
    if looks_like_file:
        path = Path(value)
        if not path.is_file():
            raise Stop(f"The setting ids names the file {value}, which doesn't exist, so the step can't tell which "
                       f"records to take. Give the file's path from the repository folder, or the ids themselves "
                       f"separated by commas, with --ids, then run the step again.")
        ids = []
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            first = line.split(",")[0].strip().strip('"')
            if first and not first.startswith("#") and first.lower() != "id":
                ids.append(first)
    else:
        ids = [i for i in re.split(r"[,\s]+", value) if i]
    return list(dict.fromkeys(ids))
