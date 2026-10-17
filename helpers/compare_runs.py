"""
compare_runs · Is one version of the pipeline better than another?

Compares step 070's evaluations of two or more runs on the same tuning
records: for each number (precision, recall, F1, ...), the difference from
the first run (the baseline), with a 95% range from a paired bootstrap. Free:
no model calls. Writes a report and prints where it is.

    py helpers/compare_runs.py                          list the evaluations kept so far
    py helpers/compare_runs.py <run id> <run id> ...    compare them; the first is the baseline

Details: helpers/compare_runs.md
"""
import argparse
import collections
import datetime as dt
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))                                                  # the repository folder, for common/
sys.path.insert(0, str(ROOT / "070_evaluate" / "070_evaluate_helpers"))       # 070's numbers, computed as 070 does

import stats                                                                   # noqa: E402
from moves import EVALUATIONS_DIR                                              # noqa: E402
from common import audit                                                      # noqa: E402
from common.files import write_text                                            # noqa: E402
from common.step import REPORTS_DIR, RESULTS_DIR, repo_path                    # noqa: E402

EVALUATIONS = RESULTS_DIR / "070_evaluate" / EVALUATIONS_DIR
LABELS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


# ------------------------------ reading -------------------------------------

def available() -> list:
    """The evaluations kept so far, oldest first."""
    return sorted(EVALUATIONS.glob("*.json"), key=lambda p: audit.run_order(p.stem)) if EVALUATIONS.is_dir() else []


def load(run_id: str) -> dict:
    path = Path(run_id) if run_id.endswith(".json") else EVALUATIONS / f"{run_id}.json"
    if not path.is_file():
        sys.exit(f"No evaluation kept for {run_id} ({repo_path(path)} doesn't exist), so it can't be compared. "
                 f"`py helpers/compare_runs.py` lists the evaluations kept so far: copy a run id from there, then run "
                 f"the command again.")
    return json.loads(path.read_text(encoding="utf-8"))


def flatten(d, prefix="") -> dict:
    """{"extraction (060) / settings / model": value, ...}: every leaf of a run's recipe, by its path."""
    if not isinstance(d, dict):
        return {prefix: json.dumps(d, ensure_ascii=False) if isinstance(d, (list, dict)) else str(d)}
    out = {}
    for k, v in d.items():
        out.update(flatten(v, f"{prefix} / {k}" if prefix else str(k)))
    return out


def differences(runs: list) -> list:
    """[(path, [value in each run])] of every part of the recipes that isn't the same in every run."""
    flat = [flatten(r.get("recipe", {})) for r in runs]
    keys = sorted(set().union(*flat))
    return [(k, [f.get(k, "(not recorded)") for f in flat]) for k in keys
            if len({f.get(k, "(not recorded)") for f in flat}) > 1]


def common_records(runs: list) -> tuple:
    """(ids compared, {why left out: [ids]}): the tuning records evaluated in every run, with the same ground truth
    in every run; a record whose ground truth changed between the runs is left out, since a difference there could
    come from the ground truth rather than the pipeline."""
    by_run = [{r["id"]: r for r in run["records"]} for run in runs]
    everywhere = set(by_run[0]).intersection(*by_run[1:])
    every_id = set().union(*by_run)
    changed = sorted(i for i in everywhere if len({b[i]["ground_truth_sha256"] for b in by_run}) > 1)
    kept = [r["id"] for r in runs[0]["records"] if r["id"] in everywhere and r["id"] not in changed]
    left = {"not evaluated in every run": sorted(every_id - everywhere),
            "ground truth changed between the runs": changed}
    return kept, {k: v for k, v in left.items() if v}


def as_records(run: dict, ids: list) -> list:
    """The run's records, in the order of ids, in the shape stats.numbers reads."""
    by_id = {r["id"]: r for r in run["records"]}
    return [{"compared": {"counts": collections.Counter(by_id[i]["counts"]), "describes": by_id[i]["describes"]}}
            for i in ids]


# ------------------------------ comparing -----------------------------------

def paired(base: list, other: list) -> list:
    """For each number of stats.WITH_MARGIN: {"label", "a", "b", "diff", "low", "high"}. The range is a paired
    bootstrap: the records are drawn at random with repeats, the SAME draw for both runs, REDRAWS times, and the
    middle 95% of the differences is kept. Fewer than MIN_RECORDS records: no range."""
    n = len(base)
    a_point, b_point = stats.numbers(base), stats.numbers(other)
    samples = {path: [] for path, _ in stats.WITH_MARGIN}
    if n >= stats.MIN_RECORDS:
        rng = random.Random(stats.SEED)
        for _ in range(stats.REDRAWS):
            draw = [rng.randrange(n) for _ in range(n)]
            na, nb = stats.numbers([base[i] for i in draw]), stats.numbers([other[i] for i in draw])
            for path, _ in stats.WITH_MARGIN:
                va, vb = stats._get(na, path), stats._get(nb, path)
                if va is not None and vb is not None:
                    samples[path].append(vb - va)
    rows = []
    for path, label in stats.WITH_MARGIN:
        va, vb = stats._get(a_point, path), stats._get(b_point, path)
        vals = sorted(samples[path])
        low = high = None
        if vals:
            low, high = vals[int(0.025 * (len(vals) - 1))], vals[int(round(0.975 * (len(vals) - 1)))]
        rows.append({"label": label, "a": va, "b": vb,
                     "diff": None if va is None or vb is None else vb - va, "low": low, "high": high})
    return rows


def verdict(row: dict, name: str) -> str:
    if row["diff"] is None:
        return "not comparable (a number is missing)"
    if row["diff"] == 0 and row["low"] in (0, None) and row["high"] in (0, None):
        return "the same"
    if row["low"] is None:
        return "no range (too few records)"
    if row["low"] > 0:
        return f"{name} higher"
    if row["high"] < 0:
        return f"{name} lower"
    return "can't tell apart"


def pct(v) -> str:
    return "–" if v is None else f"{100 * v:.1f}%"


def points(v) -> str:
    return "–" if v is None else f"{100 * v:+.1f} points"


# ------------------------------ the report ----------------------------------

def report(runs: list, ids: list, left: dict) -> str:
    names = [LABELS[i] for i in range(len(runs))]
    lines = ["# Comparing evaluations", "",
             f"Made {dt.datetime.now():%Y-%m-%d %H:%M} by `py helpers/compare_runs.py` (helpers/compare_runs.md). "
             f"Step 070's numbers of each run, on the same {len(ids)} tuning records; {names[0]} is the baseline, and "
             f"each other run is compared with it. Held-out records are never compared.", "",
             "## The runs", "", "| Run | 070's run id | Tuning records it evaluated |", "|---|---|---:|"]
    lines += [f"| {n} | `{r['run_id']}` | {len(r['records'])} |" for n, r in zip(names, runs)]
    diffs = differences(runs)
    lines += ["", "## What differs between the runs", "",
              "Every part of each run's recipe that isn't the same in every run: 060's run (its code version, settings, "
              "prompts by fingerprint, and the schema files it read, by fingerprint) and 070's run (its code version, "
              "and the translation, by fingerprint). A difference in numbers comes from one of these.", ""]
    if diffs:
        lines += ["| Part of the recipe | " + " | ".join(names) + " |", "|---|" + "---|" * len(names)]
        lines += [f"| {k} | " + " | ".join(f"`{v}`" for v in vals) + " |" for k, vals in diffs]
    else:
        lines.append("Nothing recorded differs.")
    lines += ["", "## The records compared", "",
              f"{len(ids)} tuning records, evaluated in every run, with the same ground truth in every run."]
    for why, which in left.items():
        lines.append(f"Left out, {why}: {len(which)} ({', '.join(f'`{i}`' for i in which[:20])}"
                     f"{', …' if len(which) > 20 else ''}).")
    if len(ids) < stats.MIN_RECORDS:
        lines += ["", f"**Fewer than {stats.MIN_RECORDS} records, so no difference gets a range: the numbers below "
                      f"could easily have come out the other way. Don't draw conclusions from them yet.**"]
    first = None
    base = as_records(runs[0], ids)
    for n, run in zip(names[1:], runs[1:]):
        rows = paired(base, as_records(run, ids))
        first = first or (n, rows[0])
        lines += ["", f"## {n} compared with {names[0]}", "",
                  f"| Number | {names[0]} | {n} | {n} − {names[0]} | 95% range of the difference | Verdict |",
                  "|---|---:|---:|---:|---|---|"]
        lines += [f"| {r['label']} | {pct(r['a'])} | {pct(r['b'])} | {points(r['diff'])} | "
                  + ("–" if r["low"] is None else f"{points(r['low'])} to {points(r['high'])}")
                  + f" | {verdict(r, n)} |" for r in rows]
        counts = collections.Counter(verdict(r, n) for r in rows)
        lines += ["", "In short: " + "; ".join(f"{k}: {v}" for k, v in counts.most_common()) + "."]
    if first:
        n, r = first
        lines += ["", "## How to read a row", "",
                  f"*Suppose* the row *{r['label']}* of *{n} compared with {names[0]}* reads {pct(r['a'])}, "
                  f"{pct(r['b'])}, {points(r['diff'])}, "
                  + ("–" if r["low"] is None else f"{points(r['low'])} to {points(r['high'])}")
                  + f". *Then:* on the same {len(ids)} tuning records, run {names[0]} scored {pct(r['a'])} and run "
                    f"{n} {pct(r['b'])}, a difference of {points(r['diff'])}. The records were then drawn at random "
                    f"{stats.REDRAWS:,} times, with repeats, the same draw for both runs, and the difference "
                    f"recomputed each time; the 95% range holds the middle 95% of those differences. A range all "
                    f"above 0 means {n} is higher by more than chance; all below 0, lower; a range that includes 0, "
                    f"the two runs can't be told apart on these records.",
                  "",
                  "## What this can't see", "",
                  "- **Many comparisons:** about 1 in 20 ranges misses by chance, so among many rows one \"higher\" "
                  "or \"lower\" alone is not a finding; a change that shows on several related numbers is.",
                  "- **Only these records:** the range covers which records happened to be evaluated, not mistakes "
                  "in the ground truth, nor the model answering differently on another run of the same version.",
                  "- **Tuning records only:** the version finally reported is evaluated once on the held-out part "
                  "(`py 070_evaluate/run.py --evaluate_held_out true`)."]
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(prog="py helpers/compare_runs.py", description=__doc__.split("\n\n")[1])
    ap.add_argument("runs", nargs="*", help="070's run ids (or evaluation files), the baseline first")
    args = ap.parse_args()
    if not args.runs:
        kept = available()
        if not kept:
            print(f"No evaluation kept yet ({repo_path(EVALUATIONS)}/ is empty): each run of "
                  f"`py 070_evaluate/run.py` keeps one.")
            return 0
        print(f"Evaluations kept ({repo_path(EVALUATIONS)}/), oldest first:")
        for p in kept:
            run = json.loads(p.read_text(encoding="utf-8"))
            ex = run.get("recipe", {}).get("extraction (060)", {}).get("settings", {})
            print(f"  {run['run_id']}   {len(run['records'])} tuning records   060: "
                  f"{ex.get('service', '?')} {ex.get('model', '?')}")
        print("\nCompare two or more: `py helpers/compare_runs.py <run id> <run id> ...` (the first is the baseline).")
        return 0
    if len(args.runs) < 2:
        sys.exit("Give two or more run ids: the baseline first, then the runs to compare with it. "
                 "`py helpers/compare_runs.py` lists them.")
    runs = [load(r) for r in args.runs]
    ids, left = common_records(runs)
    if not ids:
        sys.exit("No tuning record was evaluated in every one of these runs with the same ground truth, so there is "
                 "nothing to compare. Compare runs made on the same finished records (`py 060_extract/run.py`, then "
                 "`py 070_evaluate/run.py`, for each version).")
    path = REPORTS_DIR / f"compare_runs_{dt.datetime.now():%Y-%m-%d_%H%M%S}.md"
    write_text(path, report(runs, ids, left))
    print(f"Compared {len(runs)} runs on {len(ids)} tuning records: {repo_path(path)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
