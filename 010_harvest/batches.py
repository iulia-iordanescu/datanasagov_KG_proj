"""
batches.py -- the batch files the harvest writes, one per page.

    outputs/intermediate_results/010_harvest/batch_00000.json   records 0-999
    outputs/intermediate_results/010_harvest/batch_01000.json   records 1000-1999
    ...

Each file is a JSON list of raw CKAN records, exactly as the API returned
them. A file is written under a temporary name and renamed when complete, so
a crash never leaves a half-written batch that a rerun would mistake for a
finished one.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

PATTERN = "batch_*.json"


def batch_path(folder: Path, start: int) -> Path:
    return folder / f"batch_{start:05d}.json"


def batch_start(path: Path) -> int:
    return int(path.stem.split("_")[1])


def save_batch(path: Path, records: list) -> None:
    tmp = path.with_suffix(".json.part")
    tmp.write_text(json.dumps(records), encoding="utf-8")
    os.replace(tmp, path)


def load_batch(path: Path) -> list:
    return json.loads(path.read_text(encoding="utf-8"))


def all_batches(folder: Path) -> list:
    return sorted(folder.glob(PATTERN))


def leftover_parts(folder: Path) -> list:
    """Temporary files from an interrupted write. Safe to delete."""
    return sorted(folder.glob("batch_*.json.part"))
