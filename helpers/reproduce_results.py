"""
reproduce_results · The numbers a report quotes, made again from the saved extractions, free by code.

A report (the NASA TM of 2026-11-03) quotes numbers of six runs: three repeats of extraction (step 060) with the
induced schema and three with the ground truth schema, each evaluated by step 070. This command makes those six
runs again, each step exactly as `py <step>/run.py` would run it, in its own process: every extraction answer comes
from 060's cache, and 070 runs with --suggest false, so no model is called. It then compares the induced schema's
repeats (py helpers/compare_runs.py), applies the decision rule across schemas, and writes one report: the six run
ids, and each number the report quotes beside its value now, the same or different.

    py helpers/reproduce_results.py                                    the numbers of docs/reported_numbers.json
    py helpers/reproduce_results.py --expected <file>                  another report's numbers, in the same form

Free by code: llm.forbid_model_calls first, which reaches the processes of the steps too, so a step that would
need a model call (an answer missing from 060's cache) stops before asking or paying, naming what is missing.
Afterwards 060 is run once more with --repeat 1, so the outputs are left as a normal run leaves them.

Reads:   docs/reported_numbers.json (or --expected), 060's cache, 070's kept evaluations
Writes:  what each step's run writes; outputs/reports/reproduce_results_<date>_<time>.md and its log
Details: helpers/reproduce_results.md
"""
from __future__ import annotations

import argparse
import datetime as dt
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))                                                  # the repository folder, for common/
sys.path.insert(0, str(ROOT / "helpers"))                                      # compare_runs, as it compares

import compare_runs                                                            # noqa: E402
import stats                                                                   # noqa: E402  (070's, via compare_runs)
from common import console, llm                                                # noqa: E402
from common.audit import new_run_id                                            # noqa: E402
from common.files import append_text, read_json, write_text                    # noqa: E402
from common.step import LOGS_DIR, MANIFEST_NAME, REPORTS_DIR, RESULTS_DIR, repo_path  # noqa: E402

COMMAND = "py helpers/reproduce_results.py"
EXPECTED = ROOT / "docs" / "reported_numbers.json"
GROUND_TRUTH_SCHEMA = "annotations/ground_truth_schema.txt"
#: The two recipes, in the order they are run: (name in the expected file, 060's extra options).
RECIPES = (("induced schema", []), ("ground truth schema", ["--schema", GROUND_TRUTH_SCHEMA]))
WHY_FREE = (f"{COMMAND} is free: it re-scores the extractions already saved in 060's cache, and 070 runs with "
            f"--suggest false")
ADVICE = ("The answers this needs aren't in 060's cache on this computer (outputs/intermediate_results/060_extract/"
          "cache/), so these runs can't be made again for free here. The report's runs were made on the NASA laptop: "
          "run this command there, or copy that computer's outputs/ folder here first. To make new runs instead, "
          "which pays, run the step itself (`py 060_extract/run.py --repeat <n>`), not this command.")


def step_command(target: str, args: list) -> list:
    """The command that runs a step's run.py or a helper as a person would (the tests run them with the stand-ins)."""
    return [sys.executable, str(ROOT / target), *args]


def _run_id(step: str) -> str:
    """The run id of a step's latest run, from its manifest."""
    return read_json(RESULTS_DIR / step / MANIFEST_NAME)["run_id"]


def run(target: str, args: list, say) -> None:
    """Run one step or helper in its own process; stop this command when it doesn't finish."""
    shown = " ".join([f"py {target}", *args])
    say(f"--- {shown}")
    code = subprocess.run(step_command(target, args), cwd=ROOT).returncode
    if code:
        sys.exit(f"`{shown}` didn't finish (exit code {code}), so {COMMAND} stopped there: the runs after it need "
                 f"what it would have written. Its messages above say why, and what to do; then run {COMMAND} again.")


def make_runs(repeats: int, say) -> dict:
    """{recipe: [(060 run id, 070 run id)] per repeat}: each repeat extracted again from 060's cache and evaluated."""
    made = {}
    for name, schema in RECIPES:
        for n in range(1, repeats + 1):
            run("060_extract/run.py", [*schema, "--repeat", str(n)], say)
            extract = _run_id("060_extract")
            run("070_evaluate/run.py", ["--suggest", "false"], say)
            made.setdefault(name, []).append((extract, _run_id("070_evaluate")))
    run("060_extract/run.py", ["--repeat", "1"], say)                         # leave the outputs as a normal run does
    return made


def numbers_now(made: dict) -> dict:
    """{(number, kind, repeat): value now} for every number docs/reported_numbers.json can name: pooled over the
    induced schema's repeats (with its range), each repeat's own, and the decision rule's across schemas; values as
    fractions of 1, D in fractions of 1, p as it is."""
    induced = [compare_runs.load(e) for _, e in made["induced schema"]]
    reference = [compare_runs.load(e) for _, e in made["ground truth schema"]]
    ids, _, _ = compare_runs.common_records(induced, False)
    now = {}
    for row in compare_runs.pooled(induced, ids):
        now[(row["label"], "pooled", None)] = (row["value"], row["low"], row["high"])
    for row in compare_runs.spread(induced, ids):
        for n, v in enumerate(row["values"], 1):
            now[(row["label"], "repeat", n)] = (v, None, None)
    both, _, _ = compare_runs.common_records(induced + reference, True)
    base, other = compare_runs.paired_parts(induced, reference, both)
    test = compare_runs.sign_flip(base, other)
    now[("partial F1 with the ground truth schema", "decision", None)] = (compare_runs._f(test["changed"]), None, None)
    now[("D", "decision", None)] = (compare_runs._f(test["diff"]), None, None)
    now[("p", "decision", None)] = (test["p"], None, None)
    return now


def shown(number: str, value) -> str:
    """A value as the report quotes it: a percentage (or D, in points) with one decimal; p with 4 significant digits."""
    if value is None:
        return "–"
    return f"{float(value):.4g}" if number == "p" else f"{100 * float(value):.1f}"


def quoted(number: str, value) -> str:
    """A value of the expected file as written there, in the form shown() gives."""
    if value is None:
        return "–"
    return f"{float(value):.4g}" if number == "p" else f"{float(value):.1f}"


def compared(expected: dict, now: dict) -> list:
    """[(row label, reported, now, same?)] for every number of the expected file, its range on its own row."""
    rows = []
    for e in expected["numbers"]:
        key = (e["number"], e["kind"], e.get("repeat"))
        if key not in now:
            sys.exit(f"{repo_path(EXPECTED)} names a number {COMMAND} doesn't make ({e['number']!r}, kind "
                     f"{e['kind']!r}): the numbers it makes are every number of `py helpers/compare_runs.py` "
                     f"({', '.join(label for _, label in stats.WITH_MARGIN)}), pooled or per repeat (kind \"pooled\" "
                     f"or \"repeat\" with a repeat number), and, of kind \"decision\", \"partial F1 with the ground truth "
                     f"schema\", \"D\" and \"p\". Correct that entry, then run {COMMAND} again.")
        value, low, high = now[key]
        label = {"pooled": f"{e['number']}, pooled over the repeats", "repeat": f"{e['number']}, repeat {e.get('repeat')}",
                 "decision": f"{e['number']} (decision rule, across schemas)"}[e["kind"]]
        rows.append((label, quoted(e["number"], e["value"]), shown(e["number"], value)))
        if "low" in e:
            rows.append((f"{label}: 95% range", f"{quoted(e['number'], e['low'])} to {quoted(e['number'], e['high'])}",
                         f"{shown(e['number'], low)} to {shown(e['number'], high)}"))
    return [(label, was, is_, was == is_) for label, was, is_ in rows]


def report_text(expected: dict, made: dict, rows: list, minutes: float) -> str:
    same = sum(1 for *_, s in rows if s)
    lines = ["# Reproducing the numbers of a report", "",
             f"Made {dt.datetime.now():%Y-%m-%d %H:%M} by `{COMMAND}` (helpers/reproduce_results.md) in "
             f"{minutes:.1f} min, with no model call: the report is {expected['report']}, its numbers as of "
             f"{expected['as_of']} (annotations at commit `{expected['annotations_at']}`), from "
             f"`{repo_path(EXPECTED)}`.", "",
             f"**{same} of {len(rows)} numbers are the same as the report's**"
             + ("." if same == len(rows) else
                f"; {len(rows) - same} differ (below). A difference comes from something the runs read that changed "
                f"since: the annotations (the ground truth, the translation table, the partial-pair verdicts), the "
                f"code, or 060's cache. `git log` since commit `{expected['annotations_at']}` shows what changed."), "",
             "## The runs", "", "| Recipe | Repeat | 060's run | 070's run | The report's 070 run |", "|---|---:|---|---|---|"]
    for name, _ in RECIPES:
        theirs = expected.get("runs", {}).get(name, [])
        for n, (extract, evaluate) in enumerate(made[name], 1):
            lines.append(f"| {name} | {n} | `{extract}` | `{evaluate}` | "
                         f"{f'`{theirs[n - 1]}`' if n <= len(theirs) else '–'} |")
    lines += ["", "## The numbers", "",
              "Percentages with one decimal, as the report quotes them; *D* in percentage points; *p* with four "
              "significant digits. Pooled numbers and their 95% ranges: `py helpers/compare_runs.py` on the induced "
              "schema's repeats (*Pooled over the repeats*); the decision rule: `py helpers/compare_runs.py "
              "--across_schemas true --baseline … --changed …`. Both reports are in outputs/reports/, made by this run.",
              "", "| Number | The report | Now | Same? |", "|---|---:|---:|---|"]
    lines += [f"| {label} | {was} | {is_} | {'same' if s else '**differs**'} |" for label, was, is_, s in rows]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    llm.forbid_model_calls(WHY_FREE, ADVICE)          # first: no model call, in this process or the steps'
    console.setup()                                   # what the console can't show is replaced, never a crash
    ap = argparse.ArgumentParser(prog=COMMAND, description=__doc__.split("\n\n")[1])
    ap.add_argument("--expected", default=str(EXPECTED),
                    help="the numbers a report quotes, in the form of docs/reported_numbers.json")
    args = ap.parse_args(argv)
    path = Path(args.expected)
    if not path.is_file():
        sys.exit(f"{args.expected} doesn't exist, so there are no numbers to reproduce. Give the file of the report's "
                 f"numbers, in the form of {repo_path(EXPECTED)}, then run {COMMAND} again.")
    expected = read_json(path)
    started, clock = dt.datetime.now(), time.monotonic()
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    run_id = new_run_id("reproduce_results", started, [REPORTS_DIR, LOGS_DIR])
    log_path, report_path = LOGS_DIR / f"{run_id}.log", REPORTS_DIR / f"{run_id}.md"

    def say(text):
        print(text, flush=True)
        append_text(log_path, f"{dt.datetime.now():%Y-%m-%d %H:%M:%S}  {text}\n")

    say(f"{COMMAND}: run {run_id} started: {expected['report']}, {expected['repeats']} repeat(s) per recipe")
    made = make_runs(int(expected["repeats"]), say)
    induced = [e for _, e in made["induced schema"]]
    reference = [e for _, e in made["ground truth schema"]]
    run("helpers/compare_runs.py", induced, say)
    run("helpers/compare_runs.py", ["--across_schemas", "true", "--baseline", *induced, "--changed", *reference], say)
    rows = compared(expected, numbers_now(made))
    write_text(report_path, report_text(expected, made, rows, (time.monotonic() - clock) / 60))
    same = sum(1 for *_, s in rows if s)
    say(f"{same} of {len(rows)} numbers are the same as the report's"
        + ("" if same == len(rows) else f"; {len(rows) - same} differ") + f". Report: {repo_path(report_path)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
