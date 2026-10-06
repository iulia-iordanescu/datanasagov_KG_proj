"""
common/common_helpers/step.py -- the frame every pipeline step runs in.

A control panel ends with

    run_step("040_induce_schema", INPUTS, SETTINGS, main)

and run_step does everything that is the same for every step, so the panel
only has to show the step's main moves:

    1. command line   --<input> PATH replaces an input file,
                      --<setting> VALUE replaces a setting
    2. run id         one name for everything this run leaves behind,
                      e.g. 010_harvest_2026-09-27_1016
    3. log            outputs/logs/<run id>.log, from the first line to the last
    4. input check    every input file must exist; if one is missing the
                      step stops and says which step produces it (except
                      the inputs a panel names in may_be_empty, which may
                      have no files yet, e.g. 050's ground truth on a
                      first run)
    5. output folder  outputs/intermediate_results/<step>/
    6. main           calls main(inputs, settings, output); every move is
                      timed and logged. The helpers give each output item
                      its origin (see common/common_helpers/audit.py)
    7. bookkeeping    _manifest.json: input and output files with hashes (each
                      input file's own hash too, so helpers/audit.py can tell which
                      one changed); outputs/reports/<run id>.md for people
    8. failure        on an error, Ctrl+C or a stop on purpose (e.g. paid
                      calls declined), the log says why (with the full
                      traceback on an error), the report is marked failed,
                      interrupted or stopped, the
                      previous manifest is put back if every output file it lists
                      is unchanged, and the step exits with a non-zero code

Everything a run produces goes under outputs/, which is gitignored and can be
deleted and rebuilt by rerunning the pipeline. Work that can't be rebuilt
(hand-corrected annotations) lives in annotations/, in Git.

Paths in INPUTS are relative to outputs/intermediate_results/, except paths
that start with "./", which are relative to the repo root (for files kept in
Git, e.g. "./annotations/ground_truth/batch_*.csv"; an input may be a
pattern like this one, standing for every file it matches). Paths given on the
command line are ordinary paths.
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import importlib.util
import json
import platform
import subprocess
import sys
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path

from common import audit, prompt_files
from common.files import write_text
from common.audit import log

ROOT = Path(__file__).resolve().parents[2]      # common/common_helpers/step.py -> the repository folder
OUTPUTS_DIR = ROOT / "outputs"                      # everything a run produces; gitignored
RESULTS_DIR = OUTPUTS_DIR / "intermediate_results"  # each step's output folder
REPORTS_DIR = OUTPUTS_DIR / "reports"               # one report per run, for people
LOGS_DIR = OUTPUTS_DIR / "logs"                     # one log per run
ANNOTATIONS_DIR = ROOT / "annotations"              # human work; in Git, never regenerated
MANIFEST_NAME = "_manifest.json"


@dataclass
class Results:
    """What a step's main() returns."""
    files: list = field(default_factory=list)       # files the step wrote
    headline: dict = field(default_factory=dict)    # the run's few key numbers, at the top of its report
    details: str = ""                               # Markdown for the report's Results section
    warnings: list = field(default_factory=list)    # one sentence each
    harvest_date: str | None = None                 # set by 010; later steps inherit it


#: The lowest allowed value of settings several steps share, so a setting
#: with one name is checked the same way everywhere.
SHARED_MINIMUMS = {"workers": 1, "max_chars": 1000}


def check_settings(settings: dict, minimums: dict) -> None:
    """Stop with a plain message if a setting is below its minimum: the
    step's own minimums, plus SHARED_MINIMUMS for the shared settings it has."""
    wanted = {**{k: v for k, v in SHARED_MINIMUMS.items() if k in settings}, **minimums}
    for name, lowest in wanted.items():
        if settings[name] < lowest:
            raise ValueError(f"{name} must be at least {lowest} (got {settings[name]})")


class InputMissing(Exception):
    pass


# --------------------------------------------------------------------------
# load_moves(): load a step's moves.py
# --------------------------------------------------------------------------

def load_moves(step_name: str):
    """Load <step_name>/<step_name>_helpers/moves.py and let the files in that folder import each
    other by plain name. A folder whose name starts with a digit can't be
    imported with a normal import statement, hence this function. Every move
    called through the returned object is timed and logged."""
    folder = ROOT / step_name / f"{step_name}_helpers"
    moves_file = folder / "moves.py"
    if not moves_file.exists():
        raise SystemExit(f"{moves_file} not found: every step's {step_name}_helpers/ folder needs a moves.py")
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))
    spec = importlib.util.spec_from_file_location(f"moves_{step_name}", moves_file)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module          # dataclasses and pickling look the module up here
    spec.loader.exec_module(module)
    return audit.TimedMoves(module)


# --------------------------------------------------------------------------
# command line
# --------------------------------------------------------------------------

def _parse_bool(text: str) -> bool:
    t = text.strip().lower()
    if t in ("1", "true", "yes", "on"):
        return True
    if t in ("0", "false", "no", "off"):
        return False
    raise argparse.ArgumentTypeError(f"expected true or false, got {text!r}")


def _parse_command_line(step_name, inputs, settings, argv):
    shared = sorted(set(inputs) & set(settings))
    if shared:
        raise ValueError(f"{step_name}: an input and a setting can't share a name, since both are given "
                         f"on the command line as --<name>: {', '.join(shared)}")
    ap = argparse.ArgumentParser(
        prog=f"py {step_name}/run.py",
        description=f"Run {step_name}. Instructions: {step_name}/{step_name}.md",
    )
    for key, default in inputs.items():
        ap.add_argument(f"--{key}", f"--{key.replace('_', '-')}", dest=f"in_{key}",
                        metavar="PATH", help=f"input file (default: {default})")
    for key, default in settings.items():
        kind = type(default)
        parse = _parse_bool if kind is bool else kind
        ap.add_argument(f"--{key}", f"--{key.replace('_', '-')}", dest=f"set_{key}",
                        type=parse, metavar=kind.__name__.upper(),
                        help=f"setting (default: {default})")
    args = ap.parse_args(argv)

    chosen_inputs = {}
    for key, default in inputs.items():
        given = getattr(args, f"in_{key}")
        chosen_inputs[key] = Path(given) if given else _default_input_path(default)

    chosen_settings = dict(settings)
    changed = []
    for key in settings:
        given = getattr(args, f"set_{key}")
        if given is not None:
            chosen_settings[key] = given
            changed.append(key)
    return chosen_inputs, chosen_settings, changed


def _default_input_path(default: str) -> Path:
    if default.startswith("./"):
        return ROOT / default[2:]
    return RESULTS_DIR / default


# --------------------------------------------------------------------------
# inputs
# --------------------------------------------------------------------------

def _is_pattern(path: Path) -> bool:
    return any(ch in str(path) for ch in "*?[")


def input_files(path: Path) -> list:
    """The files behind one input: the file itself, or every match of a pattern."""
    if _is_pattern(path):
        return [Path(p) for p in sorted(glob.glob(str(path)))]
    return [path] if path.is_file() else []


def _check_inputs(inputs: dict, defaults: dict, may_be_empty=()) -> None:
    missing = []
    for key, path in inputs.items():
        if not input_files(path) and key not in may_be_empty:
            producer = defaults[key].split("/")[0]
            hint = f"run {producer} first, or pass --{key}" if producer[:3].isdigit() else f"pass --{key}"
            missing.append(f"  {key}: {_rel(path)}  ({hint})")
    if missing:
        raise InputMissing("missing input files:\n" + "\n".join(missing))


def _describe_inputs(inputs: dict) -> tuple:
    """For each input: its files, their hash, and the run that produced them
    (from the manifest beside them, if any). Returns (rows, warnings,
    harvest_dates)."""
    rows, warnings, harvest_dates = [], [], set()
    for key, path in inputs.items():
        files = input_files(path)
        where = files[0] if files else path          # an input allowed to have no files yet: its pattern
        manifest_path = where.parent / MANIFEST_NAME
        run_id, origin = None, "unknown (no manifest beside it)"
        in_git = not where.resolve().is_relative_to(RESULTS_DIR.resolve())
        if not files:
            origin = "no files yet"
        elif in_git:
            # A file kept in Git (e.g. annotations/) is made by a person, not by
            # a run, so it has no manifest and none is expected.
            origin = "kept in Git, made by a person"
        elif manifest_path.exists():
            try:
                m = json.loads(manifest_path.read_text(encoding="utf-8"))
                run_id = m.get("run_id")
                origin = run_id or f"{m.get('step', '?')}, finished {m.get('finished', '?')}"
                if m.get("harvest_date"):
                    harvest_dates.add(m["harvest_date"])
            except (ValueError, OSError):
                origin = "unknown (manifest unreadable)"
        if run_id is None and not in_git and files:
            warnings.append(f"Input `{key}` ({_rel(path)}) has no readable manifest, so the run "
                            f"that produced it is not recorded.")
        row = {"name": key, "path": _rel(path), "files": len(files),
               "sha256": audit.sha256(files), "run_id": run_id, "origin": origin,
               "file_hashes": {audit.ref_path(f): audit.sha256([f]) for f in files}}
        rows.append(row)
        log.info(f"input {key}: {row['path']} ({len(files)} file{'s' if len(files) != 1 else ''}), "
                 f"from {origin}")
        log.debug(f"input {key}: sha256 {row['sha256']}")
    return rows, warnings, harvest_dates


def _name_in(folder: Path, f) -> str:
    f = Path(f).resolve()
    return f.relative_to(folder.resolve()).as_posix() if f.is_relative_to(folder.resolve()) else _rel(f)


def _rel(path) -> str:
    path = Path(path).resolve()
    return path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else path.as_posix()


# --------------------------------------------------------------------------
# run bookkeeping
# --------------------------------------------------------------------------

def git_commit() -> str:
    try:
        commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                                capture_output=True, text=True, check=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT,
                               capture_output=True, text=True, check=True).stdout.strip()
        return commit + (" (plus uncommitted changes)" if dirty else "")
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _describe_outputs(output: Path, results: Results) -> list:
    rows = []
    for f in results.files:
        f = Path(f)
        if not f.exists():
            continue
        name = _name_in(output, f)
        rows.append({"file": name, "bytes": f.stat().st_size, "sha256": audit.sha256([f])})
        log.debug(f"output {name}: {rows[-1]['bytes']:,} bytes, sha256 {rows[-1]['sha256']}")
    return rows


def _write_manifest(output: Path, run: dict, settings: dict, input_rows: list,
                    output_rows: list, results: Results) -> None:
    manifest = {
        "run_id": run["run_id"],
        "step": run["step"],
        "started": run["started"],
        "finished": run["finished"],
        "git_commit": run["git_commit"],
        "harvest_date": run["harvest_date"],
        "settings": settings,
        "prompts": run.get("prompts", []),
        "inputs": input_rows,
        "outputs": output_rows,
        "headline": results.headline,
        "warnings": len(results.warnings),
        "report": run["report"],
        "log": run["log"],
    }
    write_text(output / MANIFEST_NAME, json.dumps(manifest, indent=2))


def _take_manifest(output: Path) -> str | None:
    """Remove the step's manifest, returning its text (None if there was none)."""
    path = output / MANIFEST_NAME
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    path.unlink()
    return text


def _restore_manifest(output: Path, text: str | None) -> None:
    """After a failed run, put the previous manifest back if it still tells
    the truth: every output file it lists exists with the hash it recorded.
    A run that failed before writing anything (e.g. a bad setting) thus
    leaves the step as it was; one that changed a file leaves no manifest."""
    if text is None:
        return
    try:
        manifest = json.loads(text)
        unchanged = all((output / row["file"]).is_file()
                        and audit.sha256([output / row["file"]]) == row["sha256"]
                        for row in manifest.get("outputs", []))
    except (ValueError, KeyError, TypeError, OSError):
        unchanged = False
    if unchanged:
        write_text(output / MANIFEST_NAME, text)
        log.debug("previous manifest restored: every output file it lists is unchanged")
    else:
        log.debug("previous manifest not restored: files it lists changed or are gone")


def _stamp(t: dt.datetime) -> str:
    return t.isoformat(timespec="seconds")


@dataclass
class RunError:
    summary: str                    # the one line people need
    traceback: str | None = None    # the full story, for the log


# --------------------------------------------------------------------------
# run_step
# --------------------------------------------------------------------------

def run_step(step_name: str, inputs: dict, settings: dict, main, argv=None, may_be_empty=()) -> None:
    from common.report import write_step_report

    argv = sys.argv[1:] if argv is None else argv
    chosen_inputs, chosen_settings, changed = _parse_command_line(step_name, inputs, settings, argv)

    started = dt.datetime.now().astimezone()
    clock = time.monotonic()
    output = RESULTS_DIR / step_name
    run_id = audit.new_run_id(step_name, started, [REPORTS_DIR, LOGS_DIR])
    report = REPORTS_DIR / f"{run_id}.md"
    log_file = LOGS_DIR / f"{run_id}.log"
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    audit.start_log(log_file, step_name)

    run = {"run_id": run_id, "step": step_name, "started": _stamp(started), "finished": None,
           "duration_s": None, "git_commit": git_commit(), "harvest_date": None,
           "status": "running", "report": _rel(report), "log": _rel(log_file),
           "settings_changed": changed}

    log.info(f"{step_name}: run {run_id} started")
    log.debug(f"command: {' '.join([f'py {step_name}/run.py'] + argv)}")
    log.debug(f"git commit: {run['git_commit']}; python {platform.python_version()} on {platform.system()}")
    for key, value in chosen_settings.items():
        log.debug(f"setting {key} = {value!r}" + (" (command line)" if key in changed else ""))

    input_rows, output_rows, results, error = [], [], None, None
    old_manifest = None                  # nothing to restore if the run stops before taking it
    try:
        _check_inputs(chosen_inputs, inputs, may_be_empty)
        input_rows, input_warnings, harvest_dates = _describe_inputs(chosen_inputs)
        output.mkdir(parents=True, exist_ok=True)
        # The old manifest may no longer describe this folder once the run
        # starts writing, so it is removed; if the run fails, it is put back
        # only if every output file it lists is still unchanged (see _restore_manifest).
        old_manifest = _take_manifest(output)
        log.debug(f"output folder: {_rel(output)}")
        audit.begin_run(run_id, chosen_inputs)
        prompt_files.reset_prompts()

        results = main(chosen_inputs, chosen_settings, output)
        if not isinstance(results, Results):
            raise TypeError(f"main() must return common.step.Results, got {type(results).__name__}")
        results.warnings = input_warnings + list(results.warnings)
        run["harvest_date"] = results.harvest_date or (
            ", ".join(sorted(harvest_dates)) if harvest_dates else None)
        output_rows = _describe_outputs(output, results)
        run["status"] = "done"
    except InputMissing as exc:
        run["status"], error = "failed", RunError(str(exc))
    except KeyboardInterrupt:
        run["status"], error = "interrupted", RunError("stopped with Ctrl+C", traceback.format_exc())
    except SystemExit as exc:
        # A helper that stops the run on purpose (e.g. the person declined the
        # paid calls) must still leave a report and a log.
        run["status"], error = "stopped", RunError(str(exc.code or "stopped"))
    except Exception as exc:  # noqa: BLE001 -- any failure must still produce a report
        run["status"], error = "failed", RunError(f"{type(exc).__name__}: {exc}", traceback.format_exc())
    finally:
        audit.end_run()
        run["prompts"] = prompt_files.prompts_used()      # also for a stopped or failed run

    finished = dt.datetime.now().astimezone()
    run["finished"] = _stamp(finished)
    run["duration_s"] = round(time.monotonic() - clock, 1)

    if results is not None:
        for w in results.warnings:
            log.warning(w)
    if error:
        log.error(f"{run['status']}: {error.summary}")
        if error.traceback:
            log.debug("full traceback:\n" + error.traceback.rstrip())

    if run["status"] == "done":
        _write_manifest(output, run, chosen_settings, input_rows, output_rows, results)
    else:
        _restore_manifest(output, old_manifest)
    write_step_report(report, run, chosen_settings, input_rows, output_rows,
                      audit.timeline(), results, error)

    log.info(f"{step_name}: {run['status']} in {run['duration_s']} s")
    log.info(f"  report: {run['report']}")
    log.info(f"  log:    {run['log']}")
    audit.stop_log()
    if error:
        sys.exit({"interrupted": 130, "stopped": 2}.get(run["status"], 1))
