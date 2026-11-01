"""
compare_runs · Is one version of the pipeline better than another?

Compares step 070's evaluations of two or more runs on the same tuning
records: for each number (precision, recall, F1, ...), the difference from
the first run (the baseline), with a 95% range from a paired bootstrap
(Koehn 2004, "Statistical Significance Tests for Machine Translation
Evaluation", EMNLP, https://aclanthology.org/W04-3250/) with Hesterberg's
expanded percentile quantiles, and each number's spread across the runs (for
repeats of one recipe, setting `repeat`: the model's own variation, and the
number pooled over the repeats with its clustered Wilson range). Free: no
model calls. Writes a report and prints where it is.

    py helpers/compare_runs.py                          list the evaluations kept so far
    py helpers/compare_runs.py <run id> <run id> ...    compare them; the first is the baseline
    py helpers/compare_runs.py --across_schemas true <run id> <run id> ...
                                                        the same, for runs whose current schemas differ
                                                        (the ground truth schema, by identity, against an
                                                        induced schema, through the translation table)

Details: helpers/compare_runs.md
"""
import argparse
import collections
import datetime as dt
import json
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))                                                  # the repository folder, for common/
sys.path.insert(0, str(ROOT / "070_evaluate" / "070_evaluate_helpers"))       # 070's numbers, computed as 070 does

import pairing                                                                 # noqa: E402
from component_classes import IDENTITY, TABLE_TRANSLATION                      # noqa: E402
import stats                                                                   # noqa: E402
from moves import EVALUATIONS_DIR                                              # noqa: E402
from common import console  # noqa: E402
from common import audit                                                      # noqa: E402
from common.files import read_json, write_text                                            # noqa: E402
from common.step import REPORTS_DIR, RESULTS_DIR, repo_path                    # noqa: E402

EVALUATIONS = RESULTS_DIR / "070_evaluate" / EVALUATIONS_DIR
LABELS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

#: What a difference in the numbers can come from that the recipe doesn't record (so "What differs" can't show it),
#: and what the comparison can't see: one text, the report's and helpers/compare_runs.md's (a test keeps them equal).
UNRECORDED = [
    "- **The records' text:** 020's `records.jsonl` (the text the model read) isn't in the recipe; a new harvest "
    "between the runs changes it unseen.",
    "- **Code not committed:** the code version is the Git commit; a change not committed when a run was made is "
    "invisible.",
    "- **070's model call settings:** of 070's settings, only the service and the model are recorded (not its "
    "thinking cap); its translation is recorded by fingerprint, so a different translation shows anyway.",
    "- **The partial-pair verdicts** (`annotations/partial_pair_reviews.csv`): review no partial pairs between the "
    "runs you compare.",
    "- **The model's own variation:** the same recipe can answer differently on another run (no setting makes a "
    "model answer the same every time), and a cached answer is reused, so two runs of one recipe usually agree; "
    "repeats of one recipe (060's setting `repeat`: 2, 3, ...) are asked again, so their *Spread across the runs* "
    "measures it.",
]
LIMITS = [
    "- **Many comparisons:** about 1 in 20 ranges misses by chance, so among many rows, one *higher* or *lower* "
    "alone is not a finding; a change that shows on several related numbers is.",
    "- **Only these records:** the range covers which records happened to be evaluated, not mistakes in the ground "
    "truth, nor a model answering differently on another run of the same recipe.",
    "- **Tuning records only:** compare and choose on the tuning part; evaluate the recipe you report once on the "
    "held-out part, at the end (`py 070_evaluate/run.py --evaluate_held_out true`).",
]
#: The verdicts, in the order they are tried: the first that applies is the row's.
VERDICTS = ("not comparable (a number is missing)", "the same", "no range (one record)", "<run> higher",
            "<run> lower", "can't tell apart")
#: The paired bootstrap of the differences: how many redraws (Hesterberg 2015, section 3.6: "r = 10000 for routine
#: use"; it runs on kept counts, so it is cheap), and the seed, so a rerun gives the same ranges. A second method in a
#: second place, on purpose: a difference of two ratios is not a proportion, so 070's clustered Wilson interval
#: (stats.clustered_wilson) doesn't apply to it (helpers/compare_runs.md).
REDRAWS = 10000
SEED = 70


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
    return read_json(path)


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


#: What a kept evaluation records about each record besides its counts, and what a difference in it means: a record
#: differing in any of these between the runs is left out, since the difference could come from there rather than
#: from the pipeline. A run before 2026-11-01 recorded the ground truth only.
PER_RECORD = {"ground_truth_sha256": "ground truth changed between the runs",
              "pending_sha256": "facts waiting on an expert changed between the runs (annotations/pending_triples.csv)",
              "translation": "translation changed between the runs, for a shape of classed triple the record has in "
                             "every run (annotations/component_class_mapping.csv)"}
NOT_A_PREFIX = "after a record left out, so no longer the first records of the pool (not a fair sample)"


def _same(key: str, values: list) -> bool:
    """Whether a record's per-record value is the same in every run. The translation is compared on the shapes the
    record has in every run (its extraction differing is the thing compared, not a change of translation)."""
    if key != "translation":
        return len({json.dumps(v, sort_keys=True) for v in values}) == 1
    shared = set.intersection(*(set(v) for v in values))
    return all(len({v[s] for v in values}) == 1 for s in shared)


def common_records(runs: list, across_schemas: bool = False) -> tuple:
    """(ids compared, {why left out: [ids]}, notes): the tuning records evaluated in every run, with the same ground
    truth, the same facts waiting on an expert and the same translation of their classed triples' shapes in every
    run (PER_RECORD); a record differing in any of them is left out, since a difference there could come from it
    rather than from the pipeline. The records kept must still be each part's fair sample, the first records of the
    pool: the compared set ends before the first record left out (in pool order), and the records after it are left
    out too (NOT_A_PREFIX). notes: what couldn't be checked (a run before 2026-11-01 records the ground truth only).
    across_schemas: the translation is not compared (ACROSS_SCHEMAS: it differs by design)."""
    by_run = [{r["id"]: r for r in run["records"]} for run in runs]
    everywhere = set(by_run[0]).intersection(*by_run[1:])
    every_id = set().union(*by_run)
    left, notes = {"not evaluated in every run": sorted(every_id - everywhere)}, []
    changed = set()
    for key, why in PER_RECORD.items():
        if across_schemas and key == "translation":
            continue
        lacking = [run["run_id"] for run, b in zip(runs, by_run) if any(key not in r for r in b.values())]
        if lacking:
            notes.append(f"{why.split(' changed')[0]}: not recorded per record by {', '.join(f'`{r}`' for r in lacking)} "
                         f"(a run before 2026-11-01), so a change in it between the runs can't be seen here.")
            continue
        differ = sorted(i for i in everywhere if not _same(key, [b[i][key] for b in by_run]))
        left[why] = differ
        changed.update(differ)
    position = {}
    for b in by_run:
        for i, r in b.items():
            position.setdefault(i, r.get("position"))
    if any(position[i] is None for i in every_id):
        notes.append("A run records no pool positions, so whether the records compared are still the first records "
                     "of the pool (a fair sample) can't be checked.")
        cut = set()
    else:
        order = sorted(every_id, key=lambda i: position[i])
        first_out = next((n for n, i in enumerate(order) if i not in everywhere or i in changed), len(order))
        cut = {i for i in order[first_out + 1:] if i in everywhere and i not in changed}
    left[NOT_A_PREFIX] = sorted(cut, key=lambda i: position.get(i) or 0)
    kept = [r["id"] for r in runs[0]["records"] if r["id"] in everywhere and r["id"] not in changed and r["id"] not in cut]
    return kept, {k: v for k, v in left.items() if v}, notes


def evaluation_versions_differ(runs: list) -> str | None:
    """Why the runs can't be compared when they were evaluated under different versions of what 070 counts
    (pairing.EVALUATION_VERSION, in the recipe's evaluation (070) / evaluation_version), else None. Why a stop and not
    a warning: the numbers here are recomputed from each run's kept counts by today's stats.numbers, and a count a
    later version subtracts (e.g. version 3's untranslatable occurrences) is missing from an older run's counts (read
    as 0), so that run would be recomputed under the old formula while labelled with the new one."""
    versions = [str(r.get("recipe", {}).get("evaluation (070)", {}).get("evaluation_version", "(not recorded)"))
                for r in runs]
    if len(set(versions)) == 1:
        return None
    named = " vs ".join(f"{v} (`{r['run_id']}`)" for v, r in zip(versions, runs))
    return (f"These runs were evaluated under different versions of what 070 counts (evaluation_version {named}), so "
            f"their numbers aren't comparable: a kept evaluation holds counts, and version 3 subtracts a count "
            f"(untranslatable occurrences) that version 2 never recorded. Re-run `py 070_evaluate/run.py` on the same "
            f"060 output to get a version-{pairing.EVALUATION_VERSION} evaluation, then compare.")


def translation_of(run: dict) -> str:
    """How 070 translated the run (component_classes.IDENTITY or TABLE_TRANSLATION); a run before 2026-11-01 records
    nothing, and always used the translation table."""
    return run.get("recipe", {}).get("evaluation (070)", {}).get("translation") or TABLE_TRANSLATION


def translations_mixed(runs: list, across_schemas: bool) -> str | None:
    """Why the runs can't be compared as they are: some were evaluated by identity (060 used the ground truth schema)
    and some through the translation table (another current schema), and --across_schemas true wasn't given; else
    None. Such a difference measures the schema and its translation together, not extraction alone, so it is
    compared only when asked for, and labelled so (ACROSS_SCHEMAS)."""
    if across_schemas or len({translation_of(r) for r in runs}) == 1:
        return None
    named = "; ".join(f"`{r['run_id']}`: {translation_of(r)}" for r in runs)
    return (f"These runs were translated differently ({named}): a run of 060 with the ground truth schema is "
            f"evaluated by identity, the others through the translation table, so a difference between them comes "
            f"from the schema and its translation together, not from extraction alone. To compare them anyway, as "
            f"a comparison across schemas (labelled so in the report), add `--across_schemas true`; to compare "
            f"repeats or versions of one recipe, give runs translated the same way.")


#: The label of a comparison across schemas, at the top of its report.
ACROSS_SCHEMAS = ("**A comparison across schemas.** Some of these runs extracted with the ground truth schema and "
                  "were evaluated by identity (translation: identity (060 used the ground truth schema)); the others "
                  "extracted with another schema, translated through the translation table. So each difference "
                  "below measures the schema and its translation together, not extraction alone; the ground truth "
                  "schema was shaped while annotating these very tuning records, so its run is a reference, not a "
                  "competitor. Records are not left out for a different translation here: that difference is what "
                  "is compared.")


def as_records(run: dict, ids: list) -> list:
    """The run's records, in the order of ids, in the shape stats.numbers reads."""
    by_id = {r["id"]: r for r in run["records"]}
    return [{"compared": {"counts": collections.Counter(by_id[i]["counts"]), "describes": by_id[i]["describes"]}}
            for i in ids]


# ------------------------------ comparing -----------------------------------

def expanded_alpha(n: int) -> float:
    """Hesterberg's expanded percentile interval (2015, sections 1.1 and 5.3): the lower quantile α′/2 =
    Φ(−√(n/(n − 1)) · t_{0.975, n − 1}) instead of 0.025, for n records, so the range makes up for the bootstrap's
    narrowness in small samples (Φ: the standard normal distribution function, by math.erf)."""
    x = -math.sqrt(n / (n - 1)) * stats.t_quantile(0.975, n - 1)
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def interval(values: list, n: int, redraws: int = REDRAWS) -> dict:
    """The bootstrap's expanded percentile range of the values: {"low", "high", "used", "skipped"}. The values are
    sorted; low is the one at position α′/2 · (k − 1), rounded down, and high the one at (1 − α′/2) · (k − 1), rounded
    up (expanded_alpha(n); k values), so as many values lie below the range as above it. used: how many redraws gave
    a value; skipped: how many didn't (the number was undefined there) and so aren't in the range."""
    vals = sorted(values)
    k = len(vals)
    if not k or n < 2:
        return {"low": None, "high": None, "used": k, "skipped": redraws - k}
    q = expanded_alpha(n)
    return {"low": vals[math.floor(q * (k - 1))], "high": vals[math.ceil((1 - q) * (k - 1))],
            "used": k, "skipped": redraws - k}


def paired(base: list, other: list) -> list:
    """For each number of stats.WITH_MARGIN: {"label", "a", "b", "diff", "low", "high"}. The range is a paired
    bootstrap: the records are drawn at random with repeats, the SAME draw for both runs, REDRAWS times, and the
    expanded percentile range of the differences is kept (interval). From 2 records on; one record: no range."""
    n = len(base)
    a_point, b_point = stats.numbers(base), stats.numbers(other)
    samples = {path: [] for path, _ in stats.WITH_MARGIN}
    if n >= 2:
        rng = random.Random(SEED)
        for _ in range(REDRAWS):
            draw = [rng.randrange(n) for _ in range(n)]
            na, nb = stats.numbers([base[i] for i in draw]), stats.numbers([other[i] for i in draw])
            for path, _ in stats.WITH_MARGIN:
                va, vb = stats._get(na, path), stats._get(nb, path)
                if va is not None and vb is not None:
                    samples[path].append(vb - va)
    rows = []
    for path, label in stats.WITH_MARGIN:
        va, vb = stats._get(a_point, path), stats._get(b_point, path)
        r = interval(samples[path], n) if samples[path] else {"low": None, "high": None, "used": 0, "skipped": 0}
        rows.append({"label": label, "a": va, "b": vb, "diff": None if va is None or vb is None else vb - va,
                     "low": r["low"], "high": r["high"], "redraws": r["used"]})
    return rows


def verdict(row: dict, name: str) -> str:
    """The row's verdict: the first of VERDICTS that applies, in that order."""
    missing, same, no_range, higher, lower, apart = VERDICTS
    if row["diff"] is None:
        return missing
    if row["diff"] == 0 and row["low"] in (0, None) and row["high"] in (0, None):
        return same
    if row["low"] is None:
        return no_range
    if row["low"] > 0:
        return higher.replace("<run>", name)
    if row["high"] < 0:
        return lower.replace("<run>", name)
    return apart


def pct(v) -> str:
    return "–" if v is None else f"{100 * v:.1f}%"


def _var(v) -> str:
    return "–" if v is None else f"{v:.4f}"


def points(v) -> str:
    return "–" if v is None else f"{100 * v:+.1f} points"


def only_repeats(diffs: list) -> bool:
    """True when the runs' recipes differ only in the repeat (060's setting repeat, and the same number in its model
    calls' record): repeats of one recipe, whose spread is the model's own variation."""
    return bool(diffs) and all(path.rsplit(" / ", 1)[-1] == "repeat" or path.endswith(" / run_id")
                               for path, _ in diffs) and any(path.endswith(" / repeat") for path, _ in diffs)


def spread(runs: list, ids: list) -> list:
    """For each number of stats.WITH_MARGIN: {"label", "values" (one per run), "low", "high", "mean", "width"}: the
    lowest, the highest and the mean across the runs, and the width, highest − lowest. None where a run lacks it."""
    points = [stats.numbers(as_records(run, ids)) for run in runs]
    rows = []
    for path, label in stats.WITH_MARGIN:
        values = [stats._get(p, path) for p in points]
        have = [v for v in values if v is not None]
        rows.append({"label": label, "values": values,
                     "low": min(have) if have else None, "high": max(have) if have else None,
                     "mean": sum(have) / len(have) if have else None,
                     "width": max(have) - min(have) if len(have) == len(values) and have else None})
    return rows


def pooled(runs: list, ids: list) -> list:
    """For repeats of one recipe (only_repeats), each number of stats.WITH_MARGIN pooled over the repeats, the record
    staying the cluster (Miller 2024, sections 2.2 and 3.1: record × repeat is never taken as more clusters): {"label",
    "value", "low", "high", "between", "within"}. Each record's parts are its means over the K runs, ā_r and b̄_r, and
    the range is stats.clustered_wilson over them, so repeats narrow it as much as the answer-sampling variance they
    average away, and no more. between: the variance, across the records, of each record's proportion ā_r / b̄_r;
    within: the mean, over the records, of the variance across the runs of a_rk / b_rk (each record with a value in
    every run). A between much larger than within means more records narrow the range more than more repeats would
    (reasonable practice, no source gives a threshold)."""
    per_run = [as_records(run, ids) for run in runs]
    k = len(runs)
    rows = []
    for path, label in stats.WITH_MARGIN:
        parts = [stats.record_parts(recs, path) for recs in per_run]
        means = [(sum(p[i][0] for p in parts) / k, sum(p[i][1] for p in parts) / k) for i in range(len(ids))]
        ci = stats.clustered_wilson(means)
        props = [a / b for a, b in means if b > 0]
        between = _variance(props) if len(props) > 1 else None
        within = [_variance([p[i][0] / p[i][1] for p in parts]) for i in range(len(ids))
                  if all(p[i][1] > 0 for p in parts)] if k > 1 else []
        rows.append({"label": label, "value": ci["value"], "low": ci["low"], "high": ci["high"],
                     "between": between, "within": sum(within) / len(within) if within else None})
    return rows


def _variance(xs: list) -> float:
    """The sample variance (n − 1 in the denominator)."""
    m = sum(xs) / len(xs)
    return sum((x - m) ** 2 for x in xs) / (len(xs) - 1)


# ------------------------------ the report ----------------------------------

def _range(r: dict) -> str:
    """A row's 95% range, with how many redraws it comes from when fewer than all of them gave a value."""
    if r["low"] is None:
        return "–"
    return (f"{points(r['low'])} to {points(r['high'])}"
            + (f" (from {r['redraws']:,} of {REDRAWS:,} redraws: the number was undefined in the others)"
               if 0 < r.get("redraws", REDRAWS) < REDRAWS else ""))


def report(runs: list, ids: list, left: dict, notes: list = (), across_schemas: bool = False) -> str:
    names = [LABELS[i] for i in range(len(runs))]
    across = across_schemas and len({translation_of(r) for r in runs}) > 1
    lines = ["# Comparing evaluations" + (" across schemas" if across else ""), "",
             f"Made {dt.datetime.now():%Y-%m-%d %H:%M} by `py helpers/compare_runs.py` (helpers/compare_runs.md). "
             f"Step 070's numbers of each run, on the same {len(ids)} tuning records; {names[0]} is the baseline, and "
             f"each other run is compared with it. Held-out records are never compared.", ""]
    if across:
        lines += [ACROSS_SCHEMAS, ""]
    lines += ["## The runs", "", "| Run | 070's run id | Tuning records it evaluated | Translation |", "|---|---|---:|---|"]
    lines += [f"| {n} | `{r['run_id']}` | {len(r['records'])} | {translation_of(r)} |" for n, r in zip(names, runs)]
    diffs = differences(runs)
    lines += ["", "## What differs between the runs", "",
              "Every part of each run's recipe that isn't the same in every run: 060's run (its code version, settings, "
              "how its model calls were sent (the exact model that answered, the answer limit, temperature, thinking "
              "and effort), prompts by fingerprint, and the schema files it read, by fingerprint) and 070's run (its code version, "
              "its matching version (what counts as the same subject instance or object instance; `(not recorded)` "
              "for a run before 2026-10-24, which compared words only), the translation, by fingerprint, the "
              "facts that wait on an expert (`facts_waiting_on_an_expert`: that occurrences matching them were left "
              "out of precision, how many there were, and their rows by fingerprint; `(not recorded)` for a run "
              "before 2026-10-31, which counted those occurrences against precision), and the service and model it "
              "asked). A difference in numbers comes from one of these, or from what the "
              "recipe doesn't record:", ""] + UNRECORDED + [""]
    if diffs:
        lines += ["| Part of the recipe | " + " | ".join(names) + " |", "|---|" + "---|" * len(names)]
        lines += [f"| {k} | " + " | ".join(f"`{v}`" for v in vals) + " |" for k, vals in diffs]
    else:
        lines.append("Nothing recorded differs.")
    lines += ["", "## The records compared", "",
              f"{len(ids)} tuning records, evaluated in every run, with the same ground truth, the same facts waiting "
              f"on an expert and the same translation of their classed triples' shapes in every run, and still the "
              f"first records of the pool (a fair sample: the set ends before the first record left out)."]
    for why, which in left.items():
        lines.append(f"Left out, {why}: {len(which)} ({', '.join(f'`{i}`' for i in which[:20])}"
                     f"{', …' if len(which) > 20 else ''}).")
    for note in notes:
        lines.append(f"Not checked: {note}")
    if len(ids) < 2:
        lines += ["", "**One record only, so no difference gets a range: the numbers below could easily have come "
                      "out the other way. Don't draw conclusions from them yet.**"]
    elif len(ids) < stats.FEW_RECORDS:
        lines += ["", f"**From {len(ids)} records only (fewer than {stats.FEW_RECORDS}): each range is itself "
                      f"estimated from few records, so it may still be too narrow; read it as a rough width, not a "
                      f"bound.**"]
    rows = spread(runs, ids)
    lines += ["", "## Spread across the runs", "",
              ("These runs are repeats of one recipe: only the repeat differs (060's setting `repeat`), so each was "
               "answered by the model anew, and this spread is the model's own variation on these records, the noise "
               "floor. A later change shows a real difference only where it moves a number by more than this width."
               if only_repeats(diffs) else
               "Each number's lowest, highest and mean value across the runs, and the width (highest − lowest). "
               "When the runs are repeats of one recipe (060's setting `repeat`), the width is the model's own "
               "variation; these runs differ in more than the repeat (*What differs*), so it isn't."), "",
              "| Number | " + " | ".join(names) + " | Lowest | Highest | Mean | Width |",
              "|---|" + "---:|" * (len(names) + 4)]
    lines += [f"| {r['label']} | " + " | ".join(pct(v) for v in r["values"])
              + f" | {pct(r['low'])} | {pct(r['high'])} | {pct(r['mean'])} | "
              + ("–" if r["width"] is None else f"{100 * r['width']:.1f} points") + " |" for r in rows]
    if only_repeats(diffs):
        lines += ["", "## Pooled over the repeats", "",
                  f"Each number over all {len(runs)} repeats, each record's counts averaged over the runs, with a 95% "
                  f"range by 070's clustered Wilson interval over these {len(ids)} records "
                  f"(`070_evaluate/metrics/approximately.md`, *Sampling error*, *Repeats*): the record stays the "
                  f"cluster, so the repeats narrow the range only as much as the model's own variation they average "
                  f"away. *Between records*: the variance, across the records, of each record's own proportion; "
                  f"*Within a record*: the mean variance of a record's proportion across the repeats. A between much "
                  f"larger than within means more records would narrow the range more than more repeats.", "",
                  "| Number | Pooled | 95% range | Between records | Within a record (repeats) |",
                  "|---|---:|---|---:|---:|"]
        lines += [f"| {r['label']} | {pct(r['value'])} | "
                  + ("–" if r["low"] is None else f"{pct(r['low'])} to {pct(r['high'])}")
                  + f" | {_var(r['between'])} | {_var(r['within'])} |" for r in pooled(runs, ids)]
    first = None
    base = as_records(runs[0], ids)
    for n, run in zip(names[1:], runs[1:]):
        rows = paired(base, as_records(run, ids))
        first = first or (n, rows[0])
        lines += ["", f"## {n} compared with {names[0]}", "",
                  f"| Number | {names[0]} | {n} | {n} − {names[0]} | 95% range of the difference | Verdict |",
                  "|---|---:|---:|---:|---|---|"]
        lines += [f"| {r['label']} | {pct(r['a'])} | {pct(r['b'])} | {points(r['diff'])} | {_range(r)} | "
                  f"{verdict(r, n)} |" for r in rows]
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
                    f"{REDRAWS:,} times, with repeats, the same draw for both runs, and the difference "
                    f"recomputed each time; the 95% range is the expanded percentile range of those differences "
                    f"(Hesterberg 2015: the values at positions α′/2·(k − 1), rounded down, and (1 − α′/2)·(k − 1), "
                    f"rounded up, of the k sorted differences, with α′/2 = Φ(−√(n/(n − 1))·t_{{0.975, n − 1}}) = "
                    f"{expanded_alpha(len(ids)) if len(ids) > 1 else 0.025:.4f} for these {len(ids)} records, wider than "
                    f"the plain 0.025 to make up for the bootstrap's narrowness in small samples; a redraw where a "
                    f"number is undefined in either run is skipped, and the range then says from how many it comes). "
                    f"A range all "
                    f"above 0 means {n} is higher by more than chance; all below 0, lower; a range that includes 0, "
                    f"the two runs can't be told apart on these records.",
                  "",
                  "## What this can't see", ""] + LIMITS
    return "\n".join(lines) + "\n"


def main() -> int:
    console.setup()                                   # what the console can't show is replaced, never a crash
    ap = argparse.ArgumentParser(prog="py helpers/compare_runs.py", description=__doc__.split("\n\n")[1])
    ap.add_argument("runs", nargs="*", help="070's run ids (or evaluation files), the baseline first")
    ap.add_argument("--across_schemas", choices=("true", "false"), default="false",
                    help="true: compare runs translated differently (the ground truth schema, by identity, against "
                         "another schema), labelled as a comparison across schemas")
    args = ap.parse_args()
    across = args.across_schemas == "true"
    if not args.runs:
        kept = available()
        if not kept:
            print(f"No evaluation kept yet ({repo_path(EVALUATIONS)}/ is empty): each run of "
                  f"`py 070_evaluate/run.py` keeps one.")
            return 0
        print(f"Evaluations kept ({repo_path(EVALUATIONS)}/), oldest first:")
        for p in kept:
            run = read_json(p)
            ex = run.get("recipe", {}).get("extraction (060)", {}).get("settings", {})
            print(f"  {run['run_id']}   {len(run['records'])} tuning records   060: "
                  f"{ex.get('service', '?')} {ex.get('model', '?')}   translation: {translation_of(run)}")
        print("\nCompare two or more: `py helpers/compare_runs.py <run id> <run id> ...` (the first is the baseline).")
        return 0
    if len(args.runs) < 2:
        sys.exit("Give two or more run ids: the baseline first, then the runs to compare with it. "
                 "`py helpers/compare_runs.py` lists them.")
    runs = [load(r) for r in args.runs]
    twice = sorted({r["run_id"] for r in runs if [x["run_id"] for x in runs].count(r["run_id"]) > 1})
    if twice:
        sys.exit(f"The same run is given more than once ({', '.join(twice)}), and a run compared with itself shows "
                 f"nothing (every row would be \"the same\"). Give each run once: `py helpers/compare_runs.py` lists them.")
    problem = evaluation_versions_differ(runs) or translations_mixed(runs, across)
    if problem:
        sys.exit(problem)
    ids, left, notes = common_records(runs, across)
    if not ids:
        sys.exit("No tuning record was evaluated in every one of these runs with the same ground truth, the same facts "
                 "waiting on an expert and the same translation, so there is nothing to compare. Compare runs made on "
                 "the same finished records (`py 060_extract/run.py`, then `py 070_evaluate/run.py`, for each version)."
                 + "".join(f"\nLeft out, {why}: {len(which)} ({', '.join(which[:10])})." for why, which in left.items()))
    path = REPORTS_DIR / f"compare_runs_{dt.datetime.now():%Y-%m-%d_%H%M%S}.md"
    write_text(path, report(runs, ids, left, notes, across))
    print(f"Compared {len(runs)} runs on {len(ids)} tuning records: {repo_path(path)}"
          + "".join(f"\n  left out, {why}: {len(which)}" for why, which in left.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
