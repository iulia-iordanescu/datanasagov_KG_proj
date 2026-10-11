"""
common/common_helpers/report.py -- writes the Markdown report every step leaves behind.

    outputs/reports/<run id>.md      e.g. outputs/reports/010_harvest_2026-09-27_1016.md

The run id is shared with the run's log (outputs/logs/<run id>.log) and manifest.
Every report has the same sections: Run, Settings, Prompts, Inputs,
Outputs, Timeline, Results, Warnings. Results is written by the step itself; the rest
comes from run_step.
"""
from __future__ import annotations

import os
from pathlib import Path

from common.files import write_text


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


def cell(value) -> str:
    """A value as a Markdown table cell: | escaped, line breaks as spaces,
    nothing for None. Shared by every step's report details."""
    return "" if value is None else str(value).replace("|", "\\|").replace("\n", " ")


def named(items, show: int = 5, sep: str = ", ") -> str:
    """The first `show` items, then "and N more": "a, b, c and 4 more".
    Shared by every warning and note that names items."""
    items = [str(i) for i in items]
    return sep.join(items[:show]) + (f" and {len(items) - show} more" if len(items) > show else "")


def counted(counter: dict) -> str:
    """{"a": 3, "b": 1} as "a 3, b 1", sorted by name; "none" when empty."""
    return ", ".join(f"{k} {v:,}" for k, v in sorted(counter.items())) or "none"


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
              f"| Harvest date | {run['harvest_date'] or 'unknown'}"
              f"{' (a trial harvest: part of the catalog only)' if run.get('harvest_partial') else ''} |",
              f"| Log | {_link(run['log'], path)} |",
              "",
              "The run's full recipe: the Git commit above (the code), its Settings (the model among them), "
              "its Prompts and its Inputs (each with the run that made it), below.", ""]

    lines += ["## Settings", ""]
    if settings:
        lines += ["| Setting | Value | |", "|---|---|---|"]
        for key, value in settings.items():
            note = "changed on the command line" if key in run.get("settings_changed", []) else "default"
            lines.append(f"| `{key}` | {cell(value)} | {note} |")
    else:
        lines.append("None.")
    lines.append("")

    lines += ["## Prompts", ""]
    if run.get("prompts"):
        lines += ["Every prompt this run filled in: the model's answers came from exactly these texts, whether "
                  "paid for now or taken from the cache.", "",
                  "| Prompt file | sha256 of its text |", "|---|---|"]
        lines += [f"| {cell(p['file'])} | `{p['sha256'][:12]}` |" for p in run["prompts"]]
    else:
        lines.append("None: this run sent nothing to a model.")
    lines.append("")

    lines += ["## Inputs", ""]
    if input_rows:
        lines += ["| Input | Path | Files | Produced by run | sha256 |", "|---|---|---:|---|---|"]
        for row in input_rows:
            lines.append(f"| `{row['name']}` | {cell(row['path'])} | {row['files']} | "
                         f"{cell(row['origin'])} | `{row['sha256'][:12]}` |")
    else:
        lines.append("None." if not error else "None read: the run stopped first.")
    lines.append("")

    lines += ["## Outputs", ""]
    if output_rows:
        lines += [f"In `outputs/intermediate_results/{run['step']}/`. Full hashes in `_manifest.json`.", "",
                  "| File | Size | sha256 |", "|---|---:|---|"]
        for row in output_rows:
            lines.append(f"| {cell(row['file'])} | {_size(row['bytes'])} | `{row['sha256'][:12]}` |")
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
        # a warning's further lines (e.g. a ground truth problem's lines of a file) stay inside its item
        lines += ["- " + "\n".join(("  " + x) if x and j else x for j, x in enumerate(w.split("\n")))
                  for w in warnings]
    else:
        lines.append("None.")
    lines.append("")

    write_text(path, "\n".join(lines))


def model_calls(stages: list, test_calls: int, model: str) -> list:
    """The "### Model calls" section every step that calls the model ends its
    report details with, worded the same everywhere. stages: [(what the
    calls did, calls made, text pieces or batches answered from the cache
    or None)]."""
    lines = ["### Model calls", "", "| Calls to | Made | Answered from the cache |", "|---|---:|---:|"]
    lines += [f"| {what} | {made:,} | {'–' if reused is None else f'{reused:,}'} |" for what, made, reused in stages]
    total = sum(made for _, made, _ in stages) + test_calls
    lines += [f"| the one-line test (first paid call of a run) | {test_calls} | – |",
              f"| **total paid this run** | **{total:,}** | |", "",
              f"Model: `{model}`. Every answer is kept in the step's `cache/`, so a rerun pays only for "
              f"what isn't there yet.", ""]
    return lines
