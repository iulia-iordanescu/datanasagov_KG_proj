"""
common/audit.py -- observability and audit for every step.

Each run of a step gets one RUN ID, e.g. 010_harvest_2026-09-27_1016, shared
by everything the run leaves behind:

    outputs/logs/<run id>.log                what happened, line by line, in time order
    outputs/reports/<run id>.md              what came out, for people
    outputs/intermediate_results/<step>/_manifest.json      what came out, for code:
                                             input and output files with hashes

Helpers use these:

    from common.audit import log, origin, check_origins
    log.info("saved batch_01000.json")               goes to the console and the log file
    log.debug("GET ... 200 in 1.3 s")                goes to the log file only
    record["_origin"] = [origin(batch_file, "abc-123")]

ORIGIN. The audit trail has two halves. The manifest is the per-file half:
each input's hash and the run that produced it, recorded once per file. The
origin is the per-item half: each output item names the input item(s) it
came from, inside the output file itself. There is no separate lineage file.

    JSON output   an "_origin" field
    CSV output    an "origin" column, references joined with "; "

A reference is "<step>/<file>#<key>", or "#<position>" (counting from 0)
when the item has no key:

    "_origin": ["010_harvest/batch_00000.json#a1b2c3"]

Files kept in Git are referenced from the repo root instead, e.g.
"annotations/ground_truth/batch_000.csv#17". Paths always use forward slashes.

010 is where origin starts: each batch file wraps its records with the
request that returned them, so its records carry no _origin of their own.
"""
from __future__ import annotations

import datetime as dt
import functools
import hashlib
import logging
import sys
import time
from pathlib import Path

ORIGIN_FIELD = "_origin"        # in JSON output
ORIGIN_COLUMN = "origin"        # in CSV output

log = logging.getLogger("pipeline")
_run = {"run_id": None, "inputs": {}}       # the run in progress, set by run_step


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
# the run in progress
# --------------------------------------------------------------------------

def begin_run(run_id: str, inputs: dict) -> None:
    """Called by run_step before main(): the run id, and the step's inputs
    as {name: path}, so helpers can write origin("records", key)."""
    _run["run_id"], _run["inputs"] = run_id, dict(inputs)


def end_run() -> None:
    _run["run_id"], _run["inputs"] = None, {}


def current_run_id() -> str | None:
    return _run["run_id"]


# --------------------------------------------------------------------------
# origin
# --------------------------------------------------------------------------

@functools.lru_cache(maxsize=4096)
def ref_path(path) -> str:
    """How an origin reference names a file: "<step>/<file>" for a file in
    outputs/intermediate_results/, else its path from the repo root, with
    forward slashes either way. Cached: resolving a path is slow on Windows,
    and origin() asks once per item."""
    from common.step import RESULTS_DIR, ROOT
    path = Path(path).resolve()
    for base in (RESULTS_DIR, ROOT):
        if path.is_relative_to(base.resolve()):
            return path.relative_to(base.resolve()).as_posix()
    return path.as_posix()


def origin(source, key_or_position) -> str:
    """A reference to one item of an input: "<step>/<file>#<key>".

    source is the name of one of the step's INPUTS, when that input is a
    single file, or the path of the input file the item was read from (an
    input like 010_harvest/batch_*.json has many files, so pass the file).
    key_or_position is the item's own key (a record id), or its position in
    the file, counting from 0, when it has none."""
    if isinstance(source, str) and source in _run["inputs"]:
        from common.step import input_files
        files = input_files(Path(_run["inputs"][source]))
        if len(files) != 1:
            raise ValueError(f"input {source!r} has {len(files)} files; "
                             f"pass the path of the file the item came from")
        source = files[0]
    return f"{ref_path(source)}#{key_or_position}"


def check_origins(items, what: str) -> str | None:
    """A warning if any item lacks an origin, else None. items are dicts
    (JSON items or CSV rows); what names them in the message, e.g. "records"."""
    items = list(items)
    missing = sum(1 for item in items
                  if not (item.get(ORIGIN_FIELD) or item.get(ORIGIN_COLUMN)))
    if not missing:
        return None
    return (f"{missing:,} of {len(items):,} {what} have no origin, so they can't be "
            f"traced to the input they came from.")
