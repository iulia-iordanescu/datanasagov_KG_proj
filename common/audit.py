"""
common/audit.py -- observability and audit for every step.

Each run of a step gets one RUN ID, e.g. 010_harvest_2026-09-27_1016, shared
by everything the run leaves behind:

    outputs/logs/<run id>.log                what happened, line by line, in time order
    outputs/reports/<run id>.md              what came out, for people
    outputs/intermediate_results/<step>/_manifest.json      what came out, for code:
                                             input and output files with hashes
    outputs/intermediate_results/<step>/_lineage.jsonl      which input produced each output item

Helpers use two things from here:

    from common.audit import log, lineage, file_source
    log.info("saved batch_01000.json")               goes to the console and the log file
    log.debug("GET ... 200 in 1.3 s")                goes to the log file only
    lineage().add("records.jsonl", 412, "abc-123",
                  [file_source(batch_file, 17, "abc-123")])

LINEAGE ROWS. One JSON object per line, one line per output item:

    {"run_id": "010_harvest_2026-09-27_1016",
     "output": {"file": "batch_01000.json", "position": 17, "key": "abc-123"},
     "sources": [ {...}, ... ]}

A source is where the item came from. Two kinds:

    {"kind": "api",  "request": "GET https://...?rows=1000&start=1000",
     "position": 17, "fetched_at": "2026-09-27T10:16:04-07:00", "http_status": 200}

    {"kind": "file", "file": "outputs/intermediate_results/020_clean/records.jsonl",
     "sha256": "...", "run_id": "020_clean_2026-09-27_1030",
     "position": 412, "key": "abc-123"}

"position" counts from 0. "key" is the item's own identifier (a CKAN record
id, a triple id); audit.py follows keys from step to step.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import logging
import sys
import time
from collections import OrderedDict
from pathlib import Path

LINEAGE_NAME = "_lineage.jsonl"

log = logging.getLogger("pipeline")
_current_lineage = None


# --------------------------------------------------------------------------
# run ids and file names
# --------------------------------------------------------------------------

def new_run_id(step_name: str, started: dt.datetime, folders: list) -> str:
    """<step>_<YYYY-MM-DD_HHMM>, plus -2, -3, ... if that minute is taken in
    any of the given folders, so a log and its report always share a name."""
    base = f"{step_name}_{started:%Y-%m-%d_%H%M}"
    run_id, n = base, 2
    while any(any(folder.glob(f"{run_id}.*")) for folder in folders):
        run_id, n = f"{base}-{n}", n + 1
    return run_id


def sha256(files) -> str:
    """One hash over one or more files, in the order given."""
    h = hashlib.sha256()
    for f in files:
        with open(f, "rb") as fh:
            for block in iter(lambda: fh.read(1 << 20), b""):
                h.update(block)
    return h.hexdigest()


# --------------------------------------------------------------------------
# log file
# --------------------------------------------------------------------------

class _Console(logging.Formatter):
    def format(self, record):
        msg = record.getMessage()
        return msg if record.levelno < logging.WARNING else f"{record.levelname}: {msg}"


def start_log(path: Path, step_name: str) -> logging.FileHandler:
    """Send the pipeline logger to the console (INFO and up, message only)
    and to the run's log file (DEBUG and up, with time and level)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(path, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        f"%(asctime)s.%(msecs)03d  %(levelname)-7s  {step_name}  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"))

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(_Console())

    log.handlers[:] = [file_handler, console]
    log.setLevel(logging.DEBUG)
    log.propagate = False

    # The requests library's connections, retries and waits, file only:
    # "Incremented Retry for (url=...)", "Retrying (...) after ...".
    network = logging.getLogger("urllib3")
    network.handlers[:] = [file_handler]
    network.setLevel(logging.DEBUG)
    network.propagate = False
    return file_handler


def stop_log() -> None:
    for logger in (log, logging.getLogger("urllib3")):
        for handler in list(logger.handlers):
            handler.close()
            logger.removeHandler(handler)


# --------------------------------------------------------------------------
# moves: timed and logged without touching the control panel
# --------------------------------------------------------------------------

_all_moves = []          # every TimedMoves made by helpers(), for the report timeline


def timeline() -> list:
    return [entry for moves in _all_moves for entry in moves.timeline]


class TimedMoves:
    """Wraps a step's moves.py. Every call from the control panel is logged
    with its duration, and the durations go into the report's timeline."""

    def __init__(self, module):
        self._module = module
        self.timeline = []          # (move, seconds, status)
        _all_moves.append(self)

    def __getattr__(self, name):
        target = getattr(self._module, name)
        if not callable(target) or name.startswith("_"):
            return target

        def timed(*args, **kwargs):
            log.info(f"-- {name}")
            t0 = time.monotonic()
            try:
                value = target(*args, **kwargs)
            except BaseException:
                seconds = time.monotonic() - t0
                self.timeline.append((name, seconds, "failed"))
                log.debug(f"-- {name} failed after {seconds:.1f} s")
                raise
            seconds = time.monotonic() - t0
            self.timeline.append((name, seconds, "done"))
            log.debug(f"-- {name} done in {seconds:.1f} s")
            return value

        return timed


# --------------------------------------------------------------------------
# lineage
# --------------------------------------------------------------------------

class Lineage:
    """Writes _lineage.jsonl in a step's output folder.

    Rows are appended as they are produced, so a crash keeps the lineage of
    everything already saved. When a step keeps an output file from an
    earlier run (010 resuming), it calls keep(file) and that file's rows from
    the earlier run are carried over. finish(files) rewrites the file with
    exactly one run's rows per output file: the latest run that wrote it."""

    def __init__(self, folder: Path, run_id: str):
        self.path = folder / LINEAGE_NAME
        self.run_id = run_id
        self.kept, self.kept_without_lineage = [], []
        self._rows_by_file = self._read_existing()
        self._written = set()                    # files this run has written rows for
        self.finished = False
        self._fh = open(self.path, "a", encoding="utf-8")

    def _read_existing(self) -> dict:
        """{output file: rows of the latest run that wrote it}"""
        latest = OrderedDict()
        if not self.path.exists():
            return latest
        with open(self.path, encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except ValueError:
                    continue                    # a line cut short by a crash
                name = row["output"]["file"]
                run = row["run_id"]
                if name not in latest or latest[name][0] != run:
                    latest[name] = (run, [])
                latest[name][1].append(row)
        return OrderedDict((name, rows) for name, (_, rows) in latest.items())

    def add(self, output_file: str, position: int, key, sources: list) -> None:
        row = {"run_id": self.run_id,
               "output": {"file": output_file, "position": position, "key": key},
               "sources": sources}
        self._fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        if output_file not in self._written:     # this run rewrites the file: drop older rows
            self._written.add(output_file)
            self._rows_by_file[output_file] = []
        self._rows_by_file[output_file].append(row)

    def flush(self) -> None:
        self._fh.flush()

    def keep(self, output_file: str) -> None:
        if self._rows_by_file.get(output_file):
            self.kept.append(output_file)
        else:
            self.kept_without_lineage.append(output_file)

    def finish(self, output_files: list) -> dict:
        """Rewrite the lineage for exactly these output files. Returns
        {file: number of rows} so a step can check every item is covered.
        run_step calls this with the step's output files if the step didn't."""
        self._fh.close()
        self.finished = True
        counts = {}
        tmp = self.path.with_suffix(".jsonl.part")
        with open(tmp, "w", encoding="utf-8") as fh:
            for name in output_files:
                rows = self._rows_by_file.get(name, [])
                counts[name] = len(rows)
                for row in rows:
                    fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        tmp.replace(self.path)
        return counts

    def close(self) -> None:
        if not self._fh.closed:
            self._fh.close()


_source_cache = {}


def file_source(path, position: int, key=None) -> dict:
    """A lineage source pointing at item <position> of an input file, with
    the file's hash and the run that produced it (from the manifest beside
    it). Hashes are cached, so calling this once per item is cheap."""
    path = Path(path).resolve()
    if path not in _source_cache:
        run_id = None
        manifest = path.parent / "_manifest.json"
        if manifest.exists():
            try:
                run_id = json.loads(manifest.read_text(encoding="utf-8")).get("run_id")
            except ValueError:
                pass
        from common.step import ROOT
        name = path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else path.as_posix()
        _source_cache[path] = {"kind": "file", "file": name, "sha256": sha256([path]),
                               "run_id": run_id}
    return {**_source_cache[path], "position": position, "key": key}


def begin_lineage(folder: Path, run_id: str) -> Lineage:
    global _current_lineage
    _current_lineage = Lineage(folder, run_id)
    return _current_lineage


def lineage() -> Lineage:
    """The lineage writer of the step that is running."""
    if _current_lineage is None:
        raise RuntimeError("lineage() is only available while a step runs under run_step")
    return _current_lineage


def end_lineage() -> None:
    global _current_lineage
    if _current_lineage is not None:
        _current_lineage.close()
    _current_lineage = None
