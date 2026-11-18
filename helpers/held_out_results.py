"""
held_out_results · The held-out results of several runs, by recipe, pooled over the repeats.

Summarizes the held-out looks that step 070 kept (one file per run that looked,
held_out_evaluations/<run id>.json: the held-out records' counts, the run's
recipe, and the look's line of annotations/held_out_looks.csv). The runs given
are grouped by recipe: runs whose recipes differ only in the repeat (060's
setting `repeat`) are one group, the repeats of one recipe, so with one recipe
per extraction model each group is one model. For each group: every number
pooled over its repeats, with its 95% range by 070's clustered Wilson interval
(the record stays the cluster, as in py helpers/compare_runs.py: Miller 2024,
"Adding Error Bars to Evals", arXiv:2411.00640, sections 2.2 and 3.1), each
repeat's own value, and, with --leave_out, the same numbers without the
records named; the same for the ground truth triples split by the model that
drafted their rows (070's subsection *By who drafted the ground truth*:
stats.group_parts, pooled as the other numbers). It also says how many looks the log holds for each run's
extraction, and whether the translation and the held-out records' ground
truth had the same fingerprints in every look.

It reads stored results only: it runs no step, makes no new look (it adds no
line to annotations/held_out_looks.csv) and calls no model. Writes a report
and prints where it is.

    py helpers/held_out_results.py                          list the held-out looks kept so far
    py helpers/held_out_results.py <run id> <run id> ...    summarize them, by recipe, pooled over the repeats
    py helpers/held_out_results.py --leave_out 101,119,125 <run id> ...
                                                            also without these records (pool positions or record ids)

Details: helpers/held_out_results.md
"""
import argparse
import datetime as dt
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))                                                  # the repository folder, for common/
sys.path.insert(0, str(ROOT / "070_evaluate" / "070_evaluate_helpers"))       # 070's numbers, computed as 070 does
sys.path.insert(0, str(ROOT / "helpers"))                                      # compare_runs: the one pooling over repeats

import compare_runs                                                            # noqa: E402
import stats                                                                   # noqa: E402
from moves import DRAFTED_BY_SECTION, GROUP_FORMULA, HELD_OUT_EVALUATIONS_DIR, LOOKS   # noqa: E402
from pairing import NO_DRAFTING_MODEL                                          # noqa: E402
from common import audit, console, llm                                         # noqa: E402
from common.files import read_csv, read_json, write_text                       # noqa: E402
from common.step import REPORTS_DIR, RESULTS_DIR, repo_path                    # noqa: E402

KEPT = RESULTS_DIR / "070_evaluate" / HELD_OUT_EVALUATIONS_DIR
#: The two fingerprints a look's line of the log carries, each with what it is a fingerprint of.
FINGERPRINTS = {"translation_sha256": "the translation", "held_out_ground_truth_sha256": "the held-out records' ground truth"}
#: What the summary can't see: the report's list and helpers/held_out_results.md's (a test keeps them equal).
LIMITS = [
    "- **Only the looks kept on this computer:** a look's counts are in `outputs/`, which isn't in Git; a look made "
    "on another computer, or before 2026-11-16, has a line in `annotations/held_out_looks.csv` and no counts here.",
    "- **Only these records:** a range covers which records happened to be evaluated, not mistakes in the ground "
    "truth. Pooling over the repeats averages away part of the model's own variation and nothing else.",
    "- **Partial pairs of the held-out part are never reviewed** (that would mean looking at it), so the partial "
    "level may count pairs that aren't the same fact.",
    "- **The groups share their records:** two recipes' ranges that overlap don't show the recipes alike, and "
    "ranges apart don't prove them different; this helper tests no difference between recipes.",
    "- **Leaving records out is a second reading, not a new sample:** the records left are no longer the first "
    "records of the held-out part of the pool, so their numbers are shown beside the full ones, never instead.",
]


# ------------------------------ reading -------------------------------------

def available(kept: Path = KEPT) -> list:
    """The held-out looks kept so far, oldest first."""
    return sorted(kept.glob("*.json"), key=lambda p: audit.run_order(p.stem)) if kept.is_dir() else []


def load(run_id: str, kept: Path = KEPT) -> dict:
    path = Path(run_id) if run_id.endswith(".json") else kept / f"{run_id}.json"
    if not path.is_file():
        sys.exit(f"No held-out look is kept for {run_id} ({repo_path(path)} doesn't exist), so it can't be "
                 f"summarized. Step 070 keeps one only for a run with --evaluate_held_out true that evaluated a "
                 f"held-out record (since 2026-11-16). `py helpers/held_out_results.py` lists the looks kept so far: "
                 f"copy a run id from there, then run the command again.")
    run = read_json(path)
    if run.get("part") != "held-out" or "look" not in run:
        sys.exit(f"{repo_path(path)} isn't a held-out look kept by step 070 (it has no look, or its part isn't "
                 f"held-out): give run ids listed by `py helpers/held_out_results.py`.")
    return run


def extraction_of(run: dict) -> dict:
    """What names a run's extraction: 060's run id (as the look's line records it: compare_runs.extraction_run_id),
    and its service, model, repeat and current schema (from the recipe)."""
    ex = compare_runs.recipe_of(run).get("extraction (060)", {})
    settings = ex.get("settings") or {}
    return {"run_id": compare_runs.extraction_run_id(run),
            "service": settings.get("service", "?"), "model": settings.get("model", "?"),
            "repeat": settings.get("repeat", "?"), "schema": ex.get("schema") or "?"}


def recipe_key(run: dict) -> tuple:
    """A run's recipe without what differs between repeats of one recipe: runs with the same key are repeats."""
    flat = compare_runs.flatten(compare_runs.recipe_of(run))
    return tuple(sorted((k, v) for k, v in flat.items() if not compare_runs.repeat_only(k)))


def groups_of(runs: list) -> list:
    """The runs grouped by recipe, repeats together: [[run, ...], ...], groups and runs in the order given."""
    found = {}
    for run in runs:
        found.setdefault(recipe_key(run), []).append(run)
    return list(found.values())


def leave_out_ids(given: str, runs: list) -> tuple:
    """(ids to leave out, [what was given that names no held-out record of these runs]). given: pool positions
    (101 or #101) or record ids, separated by commas."""
    by_position = {}
    every_id = set()
    for run in runs:
        for r in run["records"]:
            every_id.add(r["id"])
            if r.get("position") is not None:
                by_position[str(r["position"])] = r["id"]
    ids, unknown = [], []
    for item in (x.strip() for x in given.split(",")):
        if not item:
            continue
        rid = item if item in every_id else by_position.get(item.lstrip("#"))
        if rid is None:
            unknown.append(item)
        elif rid not in ids:
            ids.append(rid)
    return ids, unknown


# ------------------------------ the looks -----------------------------------

def looks_of(runs: list, log: list) -> list:
    """For each run: {"run", "extraction" (extraction_of), "in_log" (lines of the log with this run's id: 1 when its
    look is logged), "looks" (the log's lines for the same 060 run: every look at that extraction, this one
    included), "same" ({fingerprint: whether those looks all carry the same one})}. log: the rows of
    annotations/held_out_looks.csv."""
    out = []
    for run in runs:
        ex = extraction_of(run)
        looks = [row for row in log if ex["run_id"] and row.get("extraction_run_id") == ex["run_id"]]
        every = looks + [run["look"]]                  # the kept look counts even if its line is gone from the log
        out.append({"run": run, "extraction": ex,
                    "in_log": sum(row.get("run_id") == run["run_id"] for row in log), "looks": looks,
                    "same": {k: len({row.get(k) or "" for row in every}) == 1 for k in FINGERPRINTS}})
    return out


def same_everywhere(runs: list) -> dict:
    """{fingerprint: whether every run's look carries the same one}."""
    return {k: len({run["look"].get(k) or "" for run in runs}) == 1 for k in FINGERPRINTS}


# ------------------------------ the numbers ---------------------------------

#: The numbers by drafting model, as 070's report gives them (subsection *By who drafted the ground truth*), each a
#: path into stats.group_parts' parts, with its column's heading. Recall, the exact share and entity-class accuracy
#: are numbers of the group's own ground truth triples and pairs; precision and F1 are attributed (stats.group_parts).
DRAFTED_BY_NUMBERS = [(("exact", "recall"), "Recall (exact)"), (("partial", "recall"), "Recall (partial)"),
                      (("exact_share",), "Exact share of pairs"),
                      (("partial", "entity_class_accuracy"), "Entity-class accuracy (partial)"),
                      (("partial", "precision"), "Precision, attributed (partial)"),
                      (("partial", "f1"), "F1, attributed (partial)")]


def by_drafting_model(group: list, ids: list) -> dict:
    """The ground truth triples of the records ids split by who drafted their rows, each group's numbers pooled over
    the repeats as the other numbers are (compare_runs.pooled_parts over stats.group_parts' parts, the record
    staying the cluster). {"groups": {drafting model: {"gt_triples", "records", "spellings", "numbers": {path of
    DRAFTED_BY_NUMBERS: {"value", "low", "high", ...}}}} or None, "why": why there are none, or None}. None when no
    record is pooled, when a look was kept without the split (before 2026-11-16), or when a record's ground truth
    triples fall into the groups differently in two runs (its `drafted_by` changed between them, which the ground
    truth fingerprint doesn't cover)."""
    if not ids:
        return {"groups": None, "why": "no record is pooled"}
    per_run = [stats.group_parts(compare_runs.as_records(run, ids), "drafted_by") for run in group]
    if any(p is None for p in per_run):
        return {"groups": None, "why": "a look of this group was kept without the counts by drafting model (070 "
                                       "keeps them since 2026-11-16)"}
    shape = [{k: [b for _, b in g["parts"][("exact", "recall")]] for k, g in p.items()} for p in per_run]
    if any(x != shape[0] for x in shape[1:]):
        return {"groups": None, "why": "the ground truth triples of a pooled record fall into the drafting models "
                                       "differently in two runs (a `drafted_by` cell changed between the looks)"}
    out = {}
    for k, g in per_run[0].items():
        out[k] = {"gt_triples": g["gt_triples"], "records": g["records"],
                  "spellings": sorted({x for p in per_run for x in p[k].get("spellings", [])}),
                  "numbers": {path: compare_runs.pooled_parts([p[k]["parts"][path] for p in per_run])
                              for path, _ in DRAFTED_BY_NUMBERS}}
    return {"groups": out, "why": None}


def summary(group: list, leave_out: list) -> dict:
    """One group's numbers: {"ids" (the records pooled: compare_runs.common_records, so evaluated in every repeat
    with the same ground truth, facts waiting on an expert and translation, and the first of the held-out part with
    none skipped), "left", "notes", "pooled" (compare_runs.pooled over ids), "spread" (each repeat's own value:
    compare_runs.spread), "without_ids" (ids less leave_out), "left_out_here" (the records of leave_out among ids),
    "pooled_without" (None when nothing is left out here, or nothing remains), "drafted_by" (by_drafting_model over
    ids), "drafted_by_without" (the same over without_ids; None when pooled_without is)}."""
    ids, left, notes = compare_runs.common_records(group)
    here = [i for i in leave_out if i in set(ids)]
    without = [i for i in ids if i not in set(here)]
    return {"ids": ids, "left": left, "notes": notes,
            "pooled": compare_runs.pooled(group, ids) if ids else [],
            "spread": compare_runs.spread(group, ids) if ids else [],
            "without_ids": without, "left_out_here": here,
            "pooled_without": compare_runs.pooled(group, without) if here and without else None,
            "drafted_by": by_drafting_model(group, ids),
            "drafted_by_without": by_drafting_model(group, without) if here and without else None}


def _range(r: dict) -> str:
    return "–" if r["low"] is None else f"{compare_runs.pct(r['low'])} to {compare_runs.pct(r['high'])}"


def _cell(r: dict) -> str:
    """A pooled number and its 95% range, in one cell."""
    return compare_runs.pct(r["value"]) + ("" if r["low"] is None else f" ({_range(r)})")


def _drafted_by_lines(by: dict, model: str, k: int, without: dict | None, left_out: int, kept: int) -> list:
    """The subsection of one group on the ground truth triples by who drafted their rows: one table over all the
    pooled records, and one without the records left out on request (without: by_drafting_model over them)."""
    lines = ["", f"### {DRAFTED_BY_SECTION}, pooled over the {k} repeat(s)", "",
             "Each ground truth triple by who drafted its row (the ground truth's column `drafted_by`, every spelling "
             "of one name together; `070_evaluate/070_evaluate.md`, *Shared-model bias*), pooled over the repeats "
             f"as the numbers above. {GROUP_FORMULA} The groups split the same records, so their ranges aren't "
             "independent of each other."]
    if by["groups"] is None:
        return lines + ["", f"No numbers by drafting model: {by['why']}."]

    def label(group, e):
        if group == NO_DRAFTING_MODEL:
            return "no drafting model recorded (`drafted_by` empty)"
        same = " (the extraction model's name)" if llm.same_model_name(group, model) else ""
        return "drafted by " + " or ".join(f"`{x}`" for x in e["spellings"] or [group]) + same

    def table(groups):
        rows = ["| Ground truth triples | Count | Records | " + " | ".join(h for _, h in DRAFTED_BY_NUMBERS) + " |",
                "|---|---:|---:|" + "---:|" * len(DRAFTED_BY_NUMBERS)]
        return rows + [f"| {label(g, e)} | {e['gt_triples']} | {e['records']} | "
                       + " | ".join(_cell(e["numbers"][path]) for path, _ in DRAFTED_BY_NUMBERS) + " |"
                       for g, e in groups.items()]
    lines += [""] + table(by["groups"])
    if without is not None:
        lines += ["", f"Without the {left_out} record(s) left out on request ({kept} records):", ""]
        lines += table(without["groups"]) if without["groups"] is not None else [f"No numbers: {without['why']}."]
    return lines


def _short(sha: str) -> str:
    return f"`{sha[:12]}`" if sha else "(none)"


def _ground_truth_triples(group: list, ids: list) -> int:
    by_id = {r["id"]: r for r in group[0]["records"]}
    return sum(by_id[i]["counts"].get("gt", 0) for i in ids)


# ------------------------------ the report ----------------------------------

def report(runs: list, log: list, leave_out: list = (), positions: dict | None = None) -> str:
    leave_out = list(leave_out)
    positions = positions or {r["id"]: r.get("position") for run in runs for r in run["records"]}
    name = lambda i: f"#{positions[i]} (`{i}`)" if positions.get(i) is not None else f"`{i}`"      # noqa: E731
    groups = groups_of(runs)
    looks = looks_of(runs, log)
    label = {run["run_id"]: f"{g + 1}.{k + 1}" for g, group in enumerate(groups) for k, run in enumerate(group)}
    lines = ["# Held-out results", "",
             f"Made {dt.datetime.now():%Y-%m-%d %H:%M} by `py helpers/held_out_results.py` "
             f"(helpers/held_out_results.md), from the held-out looks step 070 kept. No step was run, no model was "
             f"called, and no look was added: every number below was already seen in its run's own report.", "",
             "## The looks", "",
             f"{len(runs)} run(s) of step 070, each a look at the held-out part, in {len(groups)} group(s): runs "
             f"whose recipes differ only in the repeat (060's setting `repeat`) are one group. *Looks at this "
             f"extraction*: how many lines of `annotations/held_out_looks.csv` name the same run of step 060, this "
             f"look included; more than 1 means that extraction's held-out numbers were shown more than once.", "",
             "| Run | 070's run id | 060's run id | Service and model | Repeat | Date | Look number in the log | "
             "Looks at this extraction | Held-out records | Translation fingerprint | Ground truth fingerprint |",
             "|---|---|---|---|---:|---|---:|---:|---:|---|---|"]
    for entry in sorted(looks, key=lambda e: [int(x) for x in label[e["run"]["run_id"]].split(".")]):
        run, ex, look = entry["run"], entry["extraction"], entry["run"]["look"]
        lines.append(f"| {label[run['run_id']]} | `{run['run_id']}` | `{ex['run_id'] or '(not recorded)'}` | "
                     f"{ex['service']} {ex['model']} | {ex['repeat']} | {look.get('date', '')} | "
                     f"{look.get('number', '')} | {len(entry['looks'])} | {len(run['records'])} | "
                     f"{_short(look.get('translation_sha256') or '')} | "
                     f"{_short(look.get('held_out_ground_truth_sha256') or '')} |")
    lines.append("")
    everywhere = same_everywhere(runs)
    for key, what in FINGERPRINTS.items():
        lines.append(f"- **Fingerprint of {what}** (`{key}`): "
                     + (f"the same in all {len(runs)} looks." if everywhere[key] else
                        f"NOT the same in all {len(runs)} looks (the table above shows each look's): the looks "
                        f"didn't all evaluate against the same {what.split(' (')[0]}."
                        + (" The fingerprint covers which held-out records were evaluated and every row of their "
                           "ground truth, so it also differs when one run evaluated fewer records."
                           if key == "held_out_ground_truth_sha256" else
                           " The fingerprint covers the rows of the translation used, so runs with different "
                           "current schemas differ in it by design.")))
    not_logged = [e for e in looks if e["in_log"] != 1]
    if not_logged:
        lines.append("- **Looks not in the log as kept:** "
                     + "; ".join(f"`{e['run']['run_id']}` has {e['in_log']} line(s) in "
                                 f"`annotations/held_out_looks.csv`" for e in not_logged)
                     + ". Each look adds exactly one line, so the log was edited, or isn't the one these looks "
                       "were logged in (`git log -p annotations/held_out_looks.csv` shows its history).")
    again = [e for e in looks if len(e["looks"]) > 1]
    for e in again:
        differ = [what for k, what in FINGERPRINTS.items() if not e["same"][k]]
        lines.append(f"- **Looked at more than once:** 060's run `{e['extraction']['run_id']}` has "
                     f"{len(e['looks'])} looks in the log (070's runs "
                     + ", ".join(f"`{row.get('run_id')}`" for row in e["looks"]) + "); between them, "
                     + ("the two fingerprints are the same." if not differ else
                        f"{' and '.join(differ)} changed, so a change was made after a look.")
                     + f" The numbers below are those of `{e['run']['run_id']}`.")
    if not again:
        lines.append("- **Looks per extraction:** every extraction summarized here has one look in the log"
                     + ("." if not not_logged else ", apart from what is said above."))
    summarized = {e["run"]["run_id"] for e in looks}
    others = [row for row in log if row.get("run_id") not in summarized]
    lines.append(f"- **The log:** `annotations/held_out_looks.csv` holds {len(log)} look(s) in all; "
                 + (f"{len(others)} of them are not summarized here (070's runs "
                    + ", ".join(f"`{row.get('run_id')}`" for row in others[:10])
                    + (", …" if len(others) > 10 else "") + ")." if others else "all are summarized here."))
    if len(groups) > 1:
        firsts = [group[0] for group in groups]
        diffs = [(k, v) for k, v in compare_runs.differences(firsts) if not compare_runs.repeat_only(k)]
        lines += ["", "## What differs between the groups", "",
                  "Every part of the recipes that isn't the same in every group (the first run of each), apart from "
                  "the repeat and the parts that change neither what the model is asked nor how its answers are "
                  "scored (run ids, code versions, how the calls were sent and paid for). Groups meant to differ only in the extraction model differ only in "
                  "the rows that name it.", "",
                  "| Part of the recipe | " + " | ".join(f"Group {g + 1}" for g in range(len(groups))) + " |",
                  "|---|" + "---|" * len(groups)]
        lines += [f"| {k} | " + " | ".join(f"`{v}`" for v in vals) + " |" for k, vals in diffs]
        models = [extraction_of(group[0])["model"] for group in groups]
        twice = sorted({m for m in models if models.count(m) > 1})
        if twice:
            lines += ["", f"**More than one group extracts with {', '.join(twice)}:** their recipes differ in "
                          f"something other than the repeat (the table above), so their runs are not repeats of one "
                          f"recipe and are not pooled together."]
    if leave_out:
        lines += ["", "## The records left out on request", "",
                  f"{len(leave_out)} record(s), named with `--leave_out`: " + ", ".join(name(i) for i in leave_out)
                  + ". Each group's numbers are given with them and without them."]
    for g, group in enumerate(groups):
        ex = extraction_of(group[0])
        s = summary(group, leave_out)
        ids, k = s["ids"], len(group)
        lines += ["", f"## Group {g + 1}: {ex['service']} {ex['model']}, {k} repeat(s)", "",
                  f"Current schema: `{ex['schema']}`; translation: {compare_runs.translation_of(group[0])}. "
                  f"Runs: " + ", ".join(f"{label[r['run_id']]} (repeat {extraction_of(r)['repeat']})" for r in group)
                  + ".", "",
                  f"**The records pooled:** {len(ids)} held-out record(s) with "
                  f"{_ground_truth_triples(group, ids) if ids else 0} ground truth triples, evaluated in every run of "
                  f"the group with the same ground truth, the same facts waiting on an expert and the same "
                  f"translation of their classed triples' shapes, and still the first records of the held-out part "
                  f"of the pool (the set ends before the first record left out)."]
        for why, which in s["left"].items():
            lines.append(f"Left out, {why}: {len(which)} ({', '.join(name(i) for i in which[:20])}"
                         f"{', …' if len(which) > 20 else ''}).")
        for note in s["notes"]:
            lines.append(f"Not checked: {note}")
        if not ids:
            lines += ["", "No record is left to pool, so this group has no numbers."]
            continue
        if len(ids) < stats.FEW_RECORDS:
            lines += ["", f"**From {len(ids)} record(s) only (fewer than {stats.FEW_RECORDS}): each range is a rough "
                          f"width, not a bound, and with one record there is none.**"]
        without = s["pooled_without"]
        if leave_out:
            missing = [i for i in leave_out if i not in set(s["left_out_here"])]
            lines += ["", f"**Without the records left out on request:** {len(s['without_ids'])} record(s) with "
                          f"{_ground_truth_triples(group, s['without_ids']) if s['without_ids'] else 0} ground truth "
                          f"triples"
                          + (f"; {', '.join(name(i) for i in missing)} "
                             f"{'is' if len(missing) == 1 else 'are'} not among this group's pooled records, so "
                             f"leaving {'it' if len(missing) == 1 else 'them'} out changes nothing here"
                             if missing else "")
                          + (". These records are not the first records of the held-out part any more (the records "
                             "left out lie between them), so their column is a second reading beside the first, not "
                             "a fair sample of its own." if s["left_out_here"] else ".")]
        head = f"Pooled over the {k} repeat(s), all {len(ids)} records"
        lines += ["", f"### Pooled over the {k} repeat(s)", "",
                  f"Each record's counts are averaged over the {k} run(s), and the 95% range is 070's clustered "
                  f"Wilson interval over the records (`070_evaluate/metrics/approximately.md`, *Sampling error*, "
                  f"*Repeats*): the record stays the cluster, so repeats narrow the range only as much as the "
                  f"model's own variation they average away. For precision, recall and F1, a second range, a "
                  f"record-level bootstrap: the records drawn at random with repeats, each record with all its "
                  f"repeats (`helpers/compare_runs.md`, *Pooled over the repeats*).", ""]
        if without is not None:
            lines += [f"| Number | {head} | 95% range | Bootstrap 95% range | Without the "
                      f"{len(s['left_out_here'])} left out ({len(s['without_ids'])} records) | 95% range | "
                      f"Bootstrap 95% range |", "|---|---:|---|---|---:|---|---|"]
            lines += [f"| {r['label']} | {compare_runs.pct(r['value'])} | {_range(r)} | {compare_runs.boot_range(r)} | "
                      f"{compare_runs.pct(w['value'])} | {_range(w)} | {compare_runs.boot_range(w)} |"
                      for r, w in zip(s["pooled"], without)]
        else:
            lines += [f"| Number | {head} | 95% range | Bootstrap 95% range |", "|---|---:|---|---|"]
            lines += [f"| {r['label']} | {compare_runs.pct(r['value'])} | {_range(r)} | {compare_runs.boot_range(r)} |"
                      for r in s["pooled"]]
        lines += _drafted_by_lines(s["drafted_by"], ex["model"], k, s["drafted_by_without"],
                                   len(s["left_out_here"]), len(s["without_ids"]))
        if k > 1:
            lines += ["", "### Each repeat", "",
                      f"Each run's own value on the same {len(ids)} records, and the lowest, the highest, the mean "
                      f"and the width (highest − lowest) across the repeats: the model's own variation on these "
                      f"records.", "",
                      "| Number | " + " | ".join(label[r["run_id"]] for r in group)
                      + " | Lowest | Highest | Mean | Width |", "|---|" + "---:|" * (k + 4)]
            lines += [f"| {r['label']} | " + " | ".join(compare_runs.pct(v) for v in r["values"])
                      + f" | {compare_runs.pct(r['low'])} | {compare_runs.pct(r['high'])} | "
                        f"{compare_runs.pct(r['mean'])} | "
                      + ("–" if r["width"] is None else f"{100 * r['width']:.1f} points") + " |" for r in s["spread"]]
    lines += ["", "## What this can't see", ""] + LIMITS
    return "\n".join(lines) + "\n"


def check(runs: list) -> str | None:
    """Why these runs can't be summarized together, or None: a run given twice, or two looks at one extraction (its
    repeat would count twice in its group's pooled numbers)."""
    ids = [r["run_id"] for r in runs]
    twice = sorted({i for i in ids if ids.count(i) > 1})
    if twice:
        return (f"The same run is given more than once ({', '.join(twice)}), and its repeat would count twice in the "
                f"pooled numbers. Give each run once: `py helpers/held_out_results.py` lists them.")
    return compare_runs.same_extraction(runs, "py helpers/held_out_results.py")


def main(argv=None) -> int:
    console.setup()                                   # what the console can't show is replaced, never a crash
    llm.forbid_model_calls("py helpers/held_out_results.py is free: it reads the held-out looks 070 kept")
    ap = argparse.ArgumentParser(prog="py helpers/held_out_results.py", description=__doc__.split("\n\n")[1])
    ap.add_argument("runs", nargs="*", help="070's run ids (or kept files) of the held-out looks to summarize")
    ap.add_argument("--leave_out", default="", metavar="RECORDS",
                    help="also give each group's numbers without these held-out records: pool positions (101 or "
                         "#101) or record ids, separated by commas")
    args = ap.parse_args(argv)
    if not args.runs:
        kept = available(KEPT)
        if not kept:
            print(f"No held-out look kept yet ({repo_path(KEPT)}/ is empty): each run of "
                  f"`py 070_evaluate/run.py --evaluate_held_out true` that evaluates a held-out record keeps one.")
            return 0
        print(f"Held-out looks kept ({repo_path(KEPT)}/), oldest first:")
        for p in kept:
            run = read_json(p)
            ex = extraction_of(run)
            print(f"  {run['run_id']}   {len(run['records'])} held-out records   060: {ex['run_id']} "
                  f"{ex['service']} {ex['model']} repeat {ex['repeat']}   look {run['look'].get('number', '?')} of "
                  f"the log, {run['look'].get('date', '?')}")
        print("\nSummarize them: `py helpers/held_out_results.py <run id> <run id> ...` "
              "(add `--leave_out <pool positions or record ids>` for the numbers without some records).")
        return 0
    runs = [load(r, KEPT) for r in args.runs]
    problem = check(runs)
    if problem:
        sys.exit(problem)
    leave_out, unknown = leave_out_ids(args.leave_out, runs)
    if unknown:
        sys.exit(f"--leave_out names {len(unknown)} record(s) that are not held-out records of these runs "
                 f"({', '.join(unknown)}), so nothing was summarized. Give pool positions (101 or #101) or record "
                 f"ids of held-out records these runs evaluated (each run's report lists them, section *Results*), "
                 f"then run the command again.")
    log = read_csv(LOOKS) if LOOKS.exists() else []
    path = REPORTS_DIR / f"held_out_results_{dt.datetime.now():%Y-%m-%d_%H%M%S}.md"
    write_text(path, report(runs, log, leave_out))
    groups = groups_of(runs)
    print(f"Summarized {len(runs)} held-out look(s) in {len(groups)} group(s)"
          + (f", with and without {len(leave_out)} record(s)" if leave_out else "") + f": {repo_path(path)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
