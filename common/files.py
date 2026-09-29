"""
common/files.py -- the one way every step, the manifest, the report and the
annotation tool save a file. (The log is the one exception: it is written
line by line as a run goes, so a crash still leaves every line before it.)

Each function writes under a temporary name (<name>.part) and then renames
it, so a file is either the old one or the complete new one, never half
written, even after a crash or Ctrl+C. Every file is UTF-8 with plain line
endings ("\\n") on every computer, so its hash doesn't depend on whether it
was written on Windows (see .gitattributes).

    from common.files import write_text, write_json, write_jsonl, write_csv
    write_json(path, data)                     # indented, readable
    write_json(path, data, indent=None)        # one line, compact
    write_jsonl(path, items)                   # one JSON item per line
    write_csv(path, columns, rows)             # a header, then rows (dicts)

new=True refuses to replace an existing file (e.g. a draft batch, which is
never overwritten).
"""
from __future__ import annotations

import csv
import io
import json
import os
from pathlib import Path


def write_text(path, text: str, new: bool = False) -> None:
    path = Path(path)
    if new and path.exists():
        raise FileExistsError(f"{path.name} already exists and is never overwritten")
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".part")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    os.replace(tmp, path)


def write_json(path, data, indent: int | None = 1, new: bool = False) -> None:
    write_text(path, json.dumps(data, indent=indent, ensure_ascii=False), new=new)


def write_jsonl(path, items, new: bool = False) -> None:
    write_text(path, "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in items), new=new)


def write_csv(path, columns: list, rows, new: bool = False) -> None:
    """rows are dicts; keys not in columns are left out."""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, columns, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    write_text(path, buf.getvalue(), new=new)
