"""
common/trace.py -- follows an item back through the pipeline's lineage.

Every step writes outputs/intermediate_results/<step>/_lineage.jsonl, one row per
output item, naming the input item(s) it came from. trace() starts from an
item in one step and follows those links upstream until it reaches the
catalog API, printing each hop with the run that made it and that run's
report and log.
"""
from __future__ import annotations

import json
from pathlib import Path

from common.audit import LINEAGE_NAME, sha256
from common.step import LOGS_DIR, REPORTS_DIR, RESULTS_DIR, ROOT


def _steps() -> list:
    """Step folders that have lineage, latest step first."""
    folders = [p.parent for p in RESULTS_DIR.glob(f"*/{LINEAGE_NAME}")]
    return sorted(folders, key=lambda p: p.name, reverse=True)


def _rows(step_folder: Path):
    with open(step_folder / LINEAGE_NAME, encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                yield json.loads(line)


def find(key=None, step=None, file=None, position=None) -> list:
    """Lineage rows matching a key (or a file and position), in the given
    step or, by default, in the latest step that has the key."""
    folders = [RESULTS_DIR / step] if step else _steps()
    for folder in folders:
        if not (folder / LINEAGE_NAME).exists():
            continue
        hits = []
        for row in _rows(folder):
            out = row["output"]
            if key is not None and str(out.get("key")) != str(key):
                continue
            if file is not None and out.get("file") != file:
                continue
            if position is not None and out.get("position") != position:
                continue
            hits.append((folder.name, row))
        if hits:
            return hits
    return []


def _run_links(run_id: str) -> str:
    links = []
    for folder, ext in ((REPORTS_DIR, "md"), (LOGS_DIR, "log")):
        path = folder / f"{run_id}.{ext}"
        if path.exists():
            links.append(path.relative_to(ROOT).as_posix())
    return ", ".join(links) if links else "report and log not found"


_hashes = {}


def _changed(file_path: str, recorded: str | None) -> str:
    """A note if the file on disk is no longer the one the item was made from."""
    if not recorded:
        return ""
    path = Path(file_path) if Path(file_path).is_absolute() else ROOT / file_path
    if not path.exists():
        return "  [file no longer exists]"
    if path not in _hashes:
        _hashes[path] = sha256([path])
    return "" if _hashes[path] == recorded else "  [file has changed since: hash differs]"


def _step_of(file_path: str) -> tuple:
    """(step folder name, file name inside it) for a source file path."""
    path = Path(file_path)
    if not path.is_absolute():
        path = ROOT / path
    return path.parent.name, path.name


def trace(step: str, row: dict, depth: int = 0, out=print) -> None:
    pad = "    " * depth
    o = row["output"]
    out(f"{pad}{step}  {o['file']} #{o['position']}  key={o.get('key')}")
    out(f"{pad}    made by run {row['run_id']}  ({_run_links(row['run_id'])})")
    for src in row.get("sources", []):
        if src.get("kind") == "api":
            out(f"{pad}    from the API: {src['request']}  item #{src.get('position')}, "
                f"fetched {src.get('fetched_at')}, HTTP {src.get('http_status')}")
        elif src.get("kind") == "file":
            src_step, src_file = _step_of(src["file"])
            note = _changed(src["file"], src.get("sha256"))
            if note:
                out(f"{pad}    from {src['file']}{note}")
            hits = find(step=src_step, file=src_file, position=src.get("position"))
            if hits:
                trace(src_step, hits[0][1], depth + 1, out)
            else:
                out(f"{pad}    from {src['file']} #{src.get('position')} key={src.get('key')} "
                    f"(no lineage found for it)")
        else:
            out(f"{pad}    from {src}")
