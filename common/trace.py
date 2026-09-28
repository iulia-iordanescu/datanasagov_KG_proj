"""
common/trace.py -- follows an item back through the pipeline by its origin.

Every output item names the input item(s) it came from, in its "_origin"
field (JSON) or "origin" column (CSV); see common/audit.py. trace() starts
from an item in one step and follows those references upstream until it
reaches either a 010 batch file, whose request block says which API call
returned the record, or a file kept in Git (annotations/), made by a person.
Each hop shows the run that made it, with that run's report and log.

A step's output files are the ones its _manifest.json lists. An item is
found by its key (the "id" field, e.g. a CKAN record id) or by its position
in the file, counting from 0. A JSON file holding several lists, each under
its own name ({"<name>": {"records": [...]}}), is searched in all of them.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from common.audit import ORIGIN_COLUMN, ORIGIN_FIELD, ref_path, sha256
from common.step import LOGS_DIR, MANIFEST_NAME, REPORTS_DIR, RESULTS_DIR, ROOT

KEY_FIELD = "id"            # the field that names an item, in every step's output

_items_cache, _hash_cache = {}, {}


# --------------------------------------------------------------------------
# reading steps and files
# --------------------------------------------------------------------------

def _manifest(folder: Path) -> dict:
    path = folder / MANIFEST_NAME
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except ValueError:
        return {}


def _steps() -> list:
    """Step folders with a manifest, latest step first."""
    return sorted((p.parent for p in RESULTS_DIR.glob(f"*/{MANIFEST_NAME}")),
                  key=lambda p: p.name, reverse=True)


def _output_files(folder: Path) -> list:
    return [folder / row["file"] for row in _manifest(folder).get("outputs", [])
            if (folder / row["file"]).is_file()]


def _read(path: Path):
    """(header, items) of a file. header is a 010 batch file's request
    block, else None; items are dicts."""
    if path in _items_cache:
        return _items_cache[path]
    header, items = None, []
    if path.suffix == ".csv":
        with open(path, encoding="utf-8-sig", newline="") as fh:
            items = list(csv.DictReader(fh))
    elif path.suffix == ".jsonl":
        with open(path, encoding="utf-8") as fh:
            items = [json.loads(line) for line in fh if line.strip()]
    elif path.suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and isinstance(data.get("records"), list):
            items = data["records"]
            header = {k: v for k, v in data.items() if k != "records"}
        elif isinstance(data, dict):
            # Several lists in one file, each under its own name, e.g. the two
            # samples in 030's splits.json: {"<name>": {"records": [...]}, ...}
            for value in data.values():
                if isinstance(value, dict) and isinstance(value.get("records"), list):
                    items.extend(value["records"])
        elif isinstance(data, list):
            items = data
    _items_cache[path] = (header, items)
    return header, items


def _locate(path: Path, fragment: str):
    """(position, item) of the item a reference fragment names: its key,
    else, for a fragment of digits, its position."""
    _, items = _read(path)
    for position, item in enumerate(items):
        if str(item.get(KEY_FIELD)) == fragment:
            return position, item
    if fragment.isdigit() and int(fragment) < len(items):
        return int(fragment), items[int(fragment)]
    return None, None


def _resolve(ref_file: str) -> Path:
    """The file an origin reference names: a step's output first, else a
    path from the repo root (files kept in Git)."""
    in_results = RESULTS_DIR / ref_file
    return in_results if in_results.exists() else ROOT / ref_file


def _origins(item: dict) -> list:
    value = item.get(ORIGIN_FIELD) or item.get(ORIGIN_COLUMN) or []
    if isinstance(value, str):
        value = [part.strip() for part in value.split(";")]
    return [ref for ref in value if ref]


# --------------------------------------------------------------------------
# finding an item
# --------------------------------------------------------------------------

def find(key=None, step=None, file=None, position=None) -> list:
    """Items matching a key (or a file and position), as (step, file,
    position, item), in the given step or, by default, in the latest step
    that has one."""
    folders = [RESULTS_DIR / step] if step else _steps()
    for folder in folders:
        hits = []
        for path in _output_files(folder):
            if file is not None and path.name != file:
                continue
            _, items = _read(path)
            for pos, item in enumerate(items):
                if key is not None and str(item.get(KEY_FIELD)) != str(key):
                    continue
                if position is not None and pos != position:
                    continue
                hits.append((folder.name, path, pos, item))
        if hits:
            return hits
    return []


# --------------------------------------------------------------------------
# following it upstream
# --------------------------------------------------------------------------

def _run_links(run_id: str | None) -> str:
    if not run_id:
        return "unknown"
    links = []
    for folder, ext in ((REPORTS_DIR, "md"), (LOGS_DIR, "log")):
        path = folder / f"{run_id}.{ext}"
        if path.exists():
            links.append(path.relative_to(ROOT).as_posix())
    return f"{run_id}  ({', '.join(links) if links else 'report and log not found'})"


def _recorded_hash(step_folder: Path, ref_file: str) -> str | None:
    """The hash the step's manifest recorded for one of its input files."""
    for row in _manifest(step_folder).get("inputs", []):
        if ref_file in row.get("file_hashes", {}):
            return row["file_hashes"][ref_file]
    return None


def _changed(path: Path, recorded: str | None) -> str:
    """A note if the file on disk is no longer the one the item was made from."""
    if not path.exists():
        return "  [file no longer exists]"
    if not recorded:
        return ""
    if path not in _hash_cache:
        _hash_cache[path] = sha256([path])
    return "" if _hash_cache[path] == recorded else "  [file has changed since: hash differs]"


def trace(step: str, path: Path, position: int, item: dict, depth: int = 0, out=print) -> None:
    pad = "    " * depth
    folder = path.parent
    header, _ = _read(path)
    key = item.get(KEY_FIELD)
    out(f"{pad}{step}  {path.name}#{key if key is not None else position}"
        + (f"  (item {position})" if key is not None else ""))

    if not path.resolve().is_relative_to(RESULTS_DIR.resolve()):
        # A file kept in Git (annotations/): made by a person, not by a run.
        out(f"{pad}    kept in Git, made by a person: {ref_path(path)}")
        return

    # A kept 010 batch file names the run that fetched it; otherwise the
    # step's manifest names the run that wrote the file.
    run_id = (header or {}).get("run_id") or _manifest(folder).get("run_id")
    out(f"{pad}    made by run {_run_links(run_id)}")

    refs = _origins(item)
    if not refs:
        if header and header.get("request"):
            out(f"{pad}    from the API: {header['request']}, fetched {header.get('fetched_at')}, "
                f"HTTP {header.get('http_status')}")
        else:
            out(f"{pad}    no origin recorded")
        return

    for ref in refs:
        ref_file, _, fragment = ref.partition("#")
        source = _resolve(ref_file)
        note = _changed(source, _recorded_hash(folder, ref_path(source)))
        src_position, src_item = _locate(source, fragment) if source.exists() else (None, None)
        if src_item is None:
            out(f"{pad}    from {ref}{note}  (item not found there)")
            continue
        if note:
            out(f"{pad}    from {ref}{note}")
        trace(source.parent.name, source, src_position, src_item, depth + 1, out)
