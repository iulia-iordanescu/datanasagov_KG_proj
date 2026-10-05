"""
batches.py -- the batch files the harvest writes, one per page.

    outputs/intermediate_results/010_harvest/batch_00000.json   records 0-999
    outputs/intermediate_results/010_harvest/batch_01000.json   records 1000-1999
    ...

Each file wraps one page's raw CKAN records, exactly as the API returned
them, with the request that returned them. This request block is where every
item's origin starts (see common/common_helpers/audit.py):

    {"request": "GET https://data.nasa.gov/api/3/action/package_search?rows=1000&start=0&sort=metadata_created+asc%2C+id+asc",
     "fetched_at": "2026-09-27T10:16:03-07:00", "http_status": 200,
     "catalog_count": 36388, "run_id": "010_harvest_2026-09-27_1016",
     "records": [ ...raw CKAN records... ]}

A file is written under a temporary name and renamed when complete, so a
crash never leaves a half-written batch that a rerun would mistake for a
finished one.
"""
from __future__ import annotations

import json
from pathlib import Path

from common.files import write_text

PATTERN = "batch_*.json"


def batch_path(folder: Path, start: int) -> Path:
    return folder / f"batch_{start:05d}.json"


def save_batch(path: Path, header: dict, records: list) -> None:
    """header: request, fetched_at, http_status, catalog_count, run_id."""
    write_text(path, json.dumps({**header, "records": records}))   # compact, non-ASCII escaped, as always


def load_batch(path: Path) -> dict:
    """The batch as {request block..., "records": [...]}. A file in the old
    format (a bare list of records, no request block) comes back as
    {"records": [...]} alone."""
    data = json.loads(path.read_text(encoding="utf-8"))
    return {"records": data} if isinstance(data, list) else data


def all_batches(folder: Path) -> list:
    return sorted(folder.glob(PATTERN))


def leftover_parts(folder: Path) -> list:
    """Temporary files from an interrupted write. Safe to delete."""
    return sorted(folder.glob("batch_*.json.part"))
