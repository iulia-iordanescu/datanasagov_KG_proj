"""
common/common_helpers/files.py -- the one way every step, the manifest, the report, and the
annotation tool save a file. (The log is the one exception: it is written
line by line as a run goes, so a crash still leaves every line before it.)

Each function but append_csv (which adds rows to the end of a file in place)
writes under a temporary name (<name>.part) and then renames it, so a file is either the old one or the complete new one, never half
written, even after a crash or Ctrl+C. Every file is UTF-8 with plain line
endings ("\\n") on every computer, so its hash doesn't depend on whether it
was written on Windows (see .gitattributes).

    from common.files import write_text, write_json, write_jsonl, write_csv
    write_json(path, data)                     # indented, readable
    write_json(path, data, indent=None)        # one line, compact
    write_jsonl(path, items)                   # one JSON item per line
    write_csv(path, columns, rows)             # a header, then rows (dicts)
    read_csv(path)                             # every row, as dicts
    append_csv(path, columns, rows)            # add rows, never changing what is there
    with locked(path): ...                     # one process at a time reads and writes path (a lock file beside it)
    fingerprint(path)                          # the sha256 of the file's bytes as they are now (None: no file)
    text, fp = read_snapshot(path)             # the text (utf-8-sig, "\n" line endings) with the fingerprint it had
    write_if_unchanged(path, text, fp)         # writes only if the file still has fingerprint fp, else Changed

new=True refuses to replace an existing file (e.g. a drafted batch's file, which is
never overwritten).
"""
from __future__ import annotations

import contextlib
import csv
import hashlib
import io
import json
import os
import threading
import time
from pathlib import Path


class Changed(ValueError):
    """The file changed on disk since it was read, so writing it back would drop that change (write_if_unchanged)."""


def fingerprint(path) -> str | None:
    """The sha256 of the file's bytes as they are now; None when there is no file. What read_snapshot hands out and
    write_if_unchanged checks: any change on disk (another tab of the annotation tool, a hand edit, a step writing
    the file) changes it."""
    path = Path(path)
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_snapshot(path) -> tuple:
    """(text, fingerprint): the file's text (utf-8-sig: a byte-order mark dropped; "\r\n" read as "\n") and the
    fingerprint of the bytes it was read from, to give write_if_unchanged; (None, None) when there is no file."""
    path = Path(path)
    if not path.exists():
        return None, None
    raw = path.read_bytes()
    return raw.decode("utf-8-sig").replace("\r\n", "\n"), hashlib.sha256(raw).hexdigest()


def write_if_unchanged(path, text: str, expected: str | None) -> str:
    """Write text to path only if the file still has the fingerprint expected (None: no file yet), under locked(), so
    nothing written since it was read is lost; returns the new fingerprint. Otherwise raises Changed, saying what to
    do: the one rule for every file a person's program reads, changes and writes back (the annotation tool's saves).
    expected None with a file there, or a fingerprint for a file that is gone, is a change too."""
    path = Path(path)
    with locked(path):
        now = fingerprint(path)
        if now != expected:
            raise Changed(f"{path.name} changed on disk since it was loaded (another tab, a hand edit, or a step wrote "
                          f"it), so saving now would overwrite that change. Nothing was saved: reload, then make your "
                          f"last change again.")
        write_text(path, text)
        return fingerprint(path)

#: How long locked() waits for another process to let go of a file before giving up.
LOCK_WAIT_SECONDS = 30
_thread_locks, _thread_locks_guard = {}, threading.Lock()


@contextlib.contextmanager
def locked(path):
    """One process (and one thread of it) at a time, between reading a file and writing it back: a lock file
    <name>.lock beside it, made only if absent (the operating system makes that one step, so two processes can't
    both make it), and a lock within the process. For the files several programs may read, change and write at once
    (two steps or the annotation tool and a step): the counted held-out looks, the model answer caches, the files
    the annotation tool saves. Waits up to LOCK_WAIT_SECONDS, then raises TimeoutError naming the lock file, so a
    lock left by a crash is found, not waited on forever."""
    path = Path(path)
    lock = path.with_name(path.name + ".lock")
    with _thread_locks_guard:
        mine = _thread_locks.setdefault(str(path.resolve()) if path.parent.exists() else str(path), threading.Lock())
    with mine:
        path.parent.mkdir(parents=True, exist_ok=True)
        deadline = time.monotonic() + LOCK_WAIT_SECONDS
        while True:
            try:
                fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.close(fd)
                break
            except FileExistsError:
                if time.monotonic() >= deadline:
                    raise TimeoutError(f"{lock} has been held for {LOCK_WAIT_SECONDS} s: another program is writing "
                                       f"{path.name}, or crashed while doing so. If nothing else is running, delete "
                                       f"{lock}, then try again.") from None
                time.sleep(0.05)
        try:
            yield
        finally:
            try:
                os.unlink(lock)
            except FileNotFoundError:
                pass


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


def read_csv(path) -> list:
    """Every row of a CSV file, as a dict. utf-8-sig: a file saved by Excel
    may start with an invisible byte-order mark, which would stick to the
    first column's name."""
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def append_csv(path, columns: list, rows) -> None:
    """Add rows at the end of a CSV file, leaving every byte already in it as
    it is (the file is created with its header if missing). For the files a
    step may only ADD to, never change: 070's annotations/component_class_mapping.csv
    and annotations/held_out_looks.csv."""
    path = Path(path)
    if not path.exists():
        write_csv(path, columns, [])
    text = path.read_text(encoding="utf-8-sig")
    with open(path, "a", encoding="utf-8", newline="") as fh:
        if text and not text.endswith("\n"):
            fh.write("\n")
        csv.DictWriter(fh, columns, extrasaction="ignore", lineterminator="\n").writerows(rows)
