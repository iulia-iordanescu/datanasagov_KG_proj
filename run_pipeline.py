"""
run_pipeline.py -- runs the pipeline's steps in order, each in its own process.

    py run_pipeline.py                         every step, 010 to 070
    py run_pipeline.py --from 040              040 onward
    py run_pipeline.py --from 040 --to 060     a range
    py run_pipeline.py --only 070              one step
    py run_pipeline.py --confirm_paid_calls false   for runs with nobody at the keyboard
    py run_pipeline.py --status                where the project stands, and what to do next (runs nothing)

How it runs:

- In order, one step after the other, each exactly as `py <step>/run.py` would
  run it, in the same terminal: a step that asks before paying still asks
  (unless --confirm_paid_calls false, passed to every step that pays).
- It stops at the first step that doesn't finish: one that fails, is stopped
  on purpose (e.g. you declined the paid calls, or step 070 added rows to the
  translation table for you to check), or is interrupted (Ctrl+C). Later
  steps need what that step would have written.
- Human gates, never failures:
    050 drafts the next batch only when no batch is waiting for you: a drafted
        batch not opened yet in the annotation tool, or a ground truth file
        with a record not finished. Otherwise it is "kept" (nothing drafted).
    060 and 070 are "skipped" until the ground truth has a finished record:
        by default 060 extracts only finished ground truth records, and 070
        evaluates them.
  A step named with --only runs whatever the gates say.
- Its own report and log: outputs/reports/000_pipeline_<date>_<time>.md and
  outputs/logs/000_pipeline_<date>_<time>.log. The report shows every step's
  status, duration, headline numbers, warnings, and report, and what needs
  attention. It never repeats the step reports.
- What to do next: at the end of every run (in the report, counted in the
  terminal), and alone with --status, the project's status
  (common/common_helpers/status.py): what each step needs, what the ground
  truth, the schema additions, the translation table, and the partial pairs
  need from a person, and what isn't committed yet, each with the section of
  docs/upkeep.md that explains it.

Step 080 (building the graph) isn't built yet.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from common.audit import new_run_id                                                    # noqa: E402
from common.ground_truth import GROUND_TRUTH_DIR, read_ground_truth                    # noqa: E402
from common import status as project                                                   # noqa: E402
from common.step import LOGS_DIR, MANIFEST_NAME, PIPELINE_STEPS, REPORTS_DIR, RESULTS_DIR, git_commit  # noqa: E402

STEPS = list(PIPELINE_STEPS)
#: The steps that call the model, and so have the setting confirm_paid_calls.
PAYING = {"040_induce_schema", "050_annotate", "060_extract", "070_evaluate"}
#: run_step's exit codes (common/common_helpers/step.py): anything else is a failure.
EXIT = {0: "ran", 2: "stopped", 130: "interrupted"}


def chosen_steps(args) -> list:
    """The steps --from/--to/--only pick, in order. A step is named by its number ("040") or its folder."""
    def find(name):
        hit = [s for s in STEPS if s == name or s.split("_")[0] == name]
        if not hit:
            raise SystemExit(f"There is no step {name!r}, so run_pipeline.py can't tell which steps to run: the "
                             f"steps are {', '.join(s.split('_')[0] for s in STEPS)}. Name one of them (e.g. "
                             f"--from 040), then run `py run_pipeline.py` again.")
        return STEPS.index(hit[0])

    if args.only:
        if args.start or args.to:
            raise SystemExit("--only can't be combined with --from or --to: --only runs one step, --from and --to "
                             "a range. Give one or the other, then run `py run_pipeline.py` again.")
        return [STEPS[find(args.only)]]
    first = find(args.start) if args.start else 0
    last = find(args.to) if args.to else len(STEPS) - 1
    if first > last:
        raise SystemExit(f"--from {args.start} comes after --to {args.to}, so no step is in that range. Swap them "
                         f"(--from {args.to} --to {args.start}), then run `py run_pipeline.py` again.")
    return STEPS[first:last + 1]


def batch_waiting() -> str | None:
    """Why 050 shouldn't draft another batch yet, or None (common/common_helpers/status.py)."""
    return project.batch_waiting(RESULTS_DIR / "050_annotate", GROUND_TRUTH_DIR, read_ground_truth())


def any_finished() -> bool:
    return any(r["finished"] for r in read_ground_truth().records.values())


def gate(step: str, forced: bool) -> tuple:
    """(status, why) when a step shouldn't run now: ("kept" | "skipped", reason); (None, None) to run it."""
    if forced:
        return None, None
    if step == "050_annotate":
        why = batch_waiting()
        if why:
            return "kept", (f"no new batch drafted: {why}. Finish it in the annotation tool (`py helpers/annotate.py`); "
                           f"050 drafts the next batch once it's done. To draft one anyway: "
                           f"`py run_pipeline.py --only 050`")
    if step in ("060_extract", "070_evaluate") and not any_finished():
        return "skipped", ("the ground truth has no finished record yet, and by default 060 extracts and 070 "
                           "evaluates only finished records. Finish one in the annotation tool "
                           "(`py helpers/annotate.py`, tick All facts extracted), then run `py run_pipeline.py` "
                           "again")
    return None, None


def command(step: str, confirm: str | None) -> list:
    cmd = [sys.executable, str(ROOT / step / "run.py")]
    if confirm is not None and step in PAYING:
        cmd += ["--confirm_paid_calls", confirm]
    return cmd


def _new_report(step: str, before: set) -> Path | None:
    """The step's report written by this run: its newest report not there before."""
    new = [p for p in REPORTS_DIR.glob(f"{step}_*.md") if p not in before]
    return max(new, key=lambda p: p.stat().st_mtime) if new else None


def run_one(step: str, confirm: str | None, say) -> dict:
    """Run one step in its own process; its status, duration, report, headline, and warnings."""
    before = set(REPORTS_DIR.glob(f"{step}_*.md")) if REPORTS_DIR.exists() else set()
    say(f"--- {step}: started")
    clock = time.monotonic()
    code = subprocess.run(command(step, confirm), cwd=ROOT).returncode
    out = {"step": step, "status": EXIT.get(code, "failed"), "exit_code": code,
           "duration_s": round(time.monotonic() - clock, 1), "report": _new_report(step, before),
           "headline": {}, "warnings": None, "why": ""}
    manifest = RESULTS_DIR / step / MANIFEST_NAME
    if out["status"] == "ran" and manifest.exists():
        m = json.loads(manifest.read_text(encoding="utf-8"))
        out["headline"], out["warnings"] = m.get("headline") or {}, m.get("warnings")
    say(f"--- {step}: {out['status']} in {out['duration_s']} s" + (f" (exit code {code})" if code else ""))
    return out


def _duration(seconds: float) -> str:
    return f"{seconds / 60:.1f} min" if seconds >= 90 else f"{seconds:.0f} s"


def report_text(run: dict, rows: list, next_up: list | None = None) -> str:
    """The pipeline report: Run, Pipeline at a glance, Needs attention (this run's steps, then what to do next:
    next_up, the project's status as Markdown lines)."""
    lines = [f"# Pipeline run {run['run_id']}", "",
             "## Run", "", "| | |", "|---|---|",
             f"| Started | {run['started']} |", f"| Finished | {run['finished']} |",
             f"| Duration | {_duration(run['duration_s'])} |", f"| Git commit | {run['git_commit']} |",
             f"| Steps requested | {run['requested']} |",
             f"| Paid calls | {'asked before paying, step by step' if run['confirm'] != 'false' else 'not asked (--confirm_paid_calls false)'} |",
             f"| Log | [{run['log'].name}](../logs/{run['log'].name}) |", "",
             "## Pipeline at a glance", "",
             "| Step | Status | Duration | Headline | Warnings | Report |", "|---|---|---|---|---:|---|"]
    for r in rows:
        headline = "; ".join(f"{k}: {v}" for k, v in r["headline"].items()) or "–"
        report = f"[{r['report'].name}]({r['report'].name})" if r["report"] else "–"
        warnings = "–" if r["warnings"] is None else str(r["warnings"])
        duration = _duration(r["duration_s"]) if r["duration_s"] is not None else "–"
        lines.append(f"| {r['step']} | {r['status']} | {duration} | {headline} | {warnings} | {report} |")
    lines += ["", "Statuses: **ran** (finished); **kept** (not run: nothing to do yet, see below); **skipped** "
              "(not run: it would have nothing to work on, see below); **stopped** (stopped on purpose, e.g. paid "
              "calls declined, or rows for you to check); **interrupted** (Ctrl+C); **failed**; **not run** (a step "
              "before it didn't finish).", "", "## Needs attention", ""]
    attention = []
    for r in rows:
        report = f" ([{r['report'].name}]({r['report'].name}))" if r["report"] else ""
        if r["status"] in ("failed", "stopped", "interrupted"):
            why = ("it was interrupted (Ctrl+C)" if r["status"] == "interrupted" else
                   "its report (linked), section *Results*, says why, and what to do" if r["report"] else
                   f"the terminal and its log (outputs/logs/{r['step']}_<date>_<time>.log) show why")
            attention.append(f"- **{r['step']} {r['status']}**{report}: {why}. The steps after it didn't run: once "
                             f"it's solved, run `py run_pipeline.py --from {r['step'].split('_')[0]}`.")
        elif r["status"] in ("kept", "skipped"):
            attention.append(f"- **{r['step']} {r['status']}:** {r['why']}.")
        elif r["warnings"]:
            attention.append(f"- **{r['step']}** has {r['warnings']} warning(s){report}: each is explained, with what "
                             f"to do, in its guide (`{r['step']}/{r['step']}.md`, section *Checks and warnings*).")
    lines += attention or ["Nothing from this run's steps."]
    if next_up is not None:
        lines += ["", "### What to do next", "", "Where the project stands now (also `py run_pipeline.py --status`):",
                  ""] + next_up
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Run the pipeline's steps in order (each as py <step>/run.py would).")
    p.add_argument("--from", dest="start", help="the first step to run, e.g. 040")
    p.add_argument("--to", help="the last step to run, e.g. 060")
    p.add_argument("--only", help="run just this step, whatever the gates say")
    p.add_argument("--confirm_paid_calls", choices=["true", "false"],
                   help="passed to every step that pays (040-070); false for runs with nobody at the keyboard")
    p.add_argument("--status", action="store_true",
                   help="where the project stands, and what to do next; runs nothing and pays nothing")
    args = p.parse_args(argv)
    if args.status:
        if args.start or args.to or args.only or args.confirm_paid_calls:
            sys.exit("--status runs nothing, so it can't be combined with --from, --to, --only, or "
                     "--confirm_paid_calls: give it alone, `py run_pipeline.py --status`.")
        print(project.status_text(project.project_status()))
        return 0
    steps = chosen_steps(args)

    started = dt.datetime.now().astimezone()
    clock = time.monotonic()
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    run_id = new_run_id("000_pipeline", started, [REPORTS_DIR, LOGS_DIR])
    log_path, report_path = LOGS_DIR / f"{run_id}.log", REPORTS_DIR / f"{run_id}.md"

    def say(text):
        print(text, flush=True)
        with open(log_path, "a", encoding="utf-8") as fh:
            fh.write(f"{dt.datetime.now():%Y-%m-%d %H:%M:%S}  {text}\n")

    say(f"pipeline run {run_id}: {', '.join(steps)}")
    rows, stopped = [], False
    for step in steps:
        if stopped:
            rows.append({"step": step, "status": "not run", "duration_s": None, "report": None, "headline": {},
                         "warnings": None, "why": ""})
            continue
        status, why = gate(step, forced=bool(args.only))
        if status:
            say(f"--- {step}: {status}: {why}")
            rows.append({"step": step, "status": status, "duration_s": None, "report": None, "headline": {},
                         "warnings": None, "why": why})
            continue
        row = run_one(step, args.confirm_paid_calls, say)
        rows.append(row)
        stopped = row["status"] != "ran"

    run = {"run_id": run_id, "started": started.isoformat(timespec="seconds"),
           "finished": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
           "duration_s": time.monotonic() - clock, "git_commit": git_commit(),
           "requested": " ".join(a for a in (f"--from {args.start}" if args.start else "", f"--to {args.to}" if args.to else "",
                                            f"--only {args.only}" if args.only else "") if a) or "all",
           "confirm": args.confirm_paid_calls, "log": log_path}
    try:
        st = project.project_status()
        next_up = project.status_markdown(st, docs_prefix="../../")
        counts = {level: sum(i["level"] == level for i in st["items"]) for level in (project.TO_DO, project.LOOK)}
        summary = (f"what to do next: {counts[project.TO_DO]} to do, {counts[project.LOOK]} worth a look "
                   f"(the report's *What to do next*, or `py run_pipeline.py --status`)")
    except Exception as e:                                 # the status never costs the run its report
        next_up = [f"The project's status couldn't be worked out ({type(e).__name__}: {e}); "
                   f"`py run_pipeline.py --status` shows the error in full."]
        summary = f"the project's status couldn't be worked out ({type(e).__name__}: {e})"
    report_path.write_text(report_text(run, rows, next_up), encoding="utf-8")
    shown = report_path.relative_to(ROOT).as_posix() if report_path.is_relative_to(ROOT) else report_path
    say(f"pipeline report: {shown}")
    say(summary)
    bad = next((r for r in rows if r["status"] in ("failed", "stopped", "interrupted")), None)
    return 0 if bad is None else (bad["exit_code"] or 1)


if __name__ == "__main__":
    sys.exit(main())
