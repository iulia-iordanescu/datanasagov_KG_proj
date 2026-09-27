"""
common/report.py -- writes the Markdown report every step leaves behind.

    outputs/reports/<run id>.md      e.g. outputs/reports/010_harvest_2026-09-27_1016.md

The run id is shared with the run's log (outputs/logs/<run id>.log) and manifest.
Every report has the same sections: Run, Settings, Inputs, Outputs,
Timeline, Results, Warnings. Results is written by the step itself; the rest
comes from run_step.
"""
from __future__ import annotations

import os
from pathlib import Path


def _duration(seconds: float | None) -> str:
    if seconds is None:
        return "?"
    if seconds < 10:
        return f"{seconds:.1f} s"
    seconds = int(round(seconds))
    h, rest = divmod(seconds, 3600)
    m, s = divmod(rest, 60)
    if h:
        return f"{h} h {m} min"
    if m:
        return f"{m} min {s} s"
    return f"{s} s"


def _cell(value) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _link(target: str, report: Path) -> str:
    """A link from the report to a file elsewhere in the repo; target is a
    path relative to the repo root."""
    from common.step import ROOT
    relative = Path(os.path.relpath(ROOT / target, report.parent)).as_posix()
    return f"[`{target}`]({relative})"


def _size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:,.0f} {unit}" if unit == "B" else f"{n:,.1f} {unit}"
        n /= 1024


def write_step_report(path: Path, run: dict, settings: dict, input_rows: list,
                      output_rows: list, timeline: list, results, error) -> None:
    lines = [f"# {run['step']} — {run['status']}", ""]

    lines += ["## Run", "",
              "| | |", "|---|---|",
              f"| Run id | `{run['run_id']}` |",
              f"| Status | {run['status']} |",
              f"| Started | {run['started']} |",
              f"| Finished | {run['finished']} |",
              f"| Duration | {_duration(run['duration_s'])} |",
              f"| Git commit | {run['git_commit']} |",
              f"| Harvest date | {run['harvest_date'] or 'unknown'} |",
              f"| Log | {_link(run['log'], path)} |",
              f"| Lineage | {_link(run['lineage'], path)} (which input each output item came from) |",
              ""]

    lines += ["## Settings", ""]
    if settings:
        lines += ["| Setting | Value | |", "|---|---|---|"]
        for key, value in settings.items():
            note = "changed on the command line" if key in run.get("settings_changed", []) else "default"
            lines.append(f"| `{key}` | {_cell(value)} | {note} |")
    else:
        lines.append("None.")
    lines.append("")

    lines += ["## Inputs", ""]
    if input_rows:
        lines += ["| Input | Path | Files | Produced by run | sha256 |", "|---|---|---:|---|---|"]
        for row in input_rows:
            lines.append(f"| `{row['name']}` | {_cell(row['path'])} | {row['files']} | "
                         f"{_cell(row['origin'])} | `{row['sha256'][:12]}` |")
    else:
        lines.append("None." if not error else "None read: the run stopped first.")
    lines.append("")

    lines += ["## Outputs", ""]
    if output_rows:
        lines += [f"In `outputs/intermediate_results/{run['step']}/`. Full hashes in `_manifest.json`.", "",
                  "| File | Size | sha256 |", "|---|---:|---|"]
        for row in output_rows:
            lines.append(f"| {_cell(row['file'])} | {_size(row['bytes'])} | `{row['sha256'][:12]}` |")
    else:
        lines.append("None recorded: the run did not finish." if error else "None.")
    lines.append("")

    lines += ["## Timeline", ""]
    if timeline:
        lines += ["| Move | Duration | |", "|---|---:|---|"]
        for name, seconds, status in timeline:
            lines.append(f"| `{name}` | {_duration(seconds)} | {status} |")
    else:
        lines.append("No moves ran.")
    lines.append("")

    lines += ["## Results", ""]
    if results is not None:
        for key, value in results.headline.items():
            shown = f"{value:,}" if isinstance(value, int) else value
            lines.append(f"- **{key}:** {shown}")
        if results.headline:
            lines.append("")
        if results.details:
            lines += [results.details.rstrip(), ""]
    if error:
        lines += ["The run did not finish:", "", "```", error.summary.rstrip(), "```", ""]
        if error.traceback:
            lines += [f"The full traceback is in the log, {_link(run['log'], path)}.", ""]
    elif results is None or (not results.headline and not results.details):
        lines += ["Nothing to report.", ""]

    lines += ["## Warnings", ""]
    warnings = results.warnings if results is not None else []
    if warnings:
        lines += [f"- {w}" for w in warnings]
    else:
        lines.append("None.")
    lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
