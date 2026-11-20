"""
export_results · Every number of the Technical Publication's runs, as CSV files kept in Git.

The runs' evaluations live in outputs/, which Git leaves out, so the numbers
behind a publication exist only on the laptop that made them. This helper
reads the runs a run list names (step 060's run, step 070's evaluation of its
tuning records, and step 070's held-out looks) and writes their numbers into
a folder that is committed: pooled over the repeats with their 95% ranges,
each run's own values and their spread, each run's extraction figures from
060's report, each record's numbers, the numbers by who drafted the ground
truth, and the records that stand out. It computes no number of its own: each
comes from the functions helpers/compare_runs.py, helpers/held_out_results.py
and 070's stats.py use for their reports. Beside the numbers, it writes every
record's role and text, every triple instance of schema induction, every
extracted triple and ground truth triple with what came of it on scoring, the
model calls, and each model's roles, settings and prompt files, each read from
the files the runs wrote (common/common_helpers/step.py, output_of_run). Free:
no model calls.

    py helpers/export_results.py                                  the run list results/technical_publication/runs.tsv
    py helpers/export_results.py --runs <list.tsv> --out <folder> another run list, into another folder

Details: helpers/export_results.md
"""
import argparse
import json
import re
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))                                                  # the repository folder, for common/
sys.path.insert(0, str(ROOT / "070_evaluate" / "070_evaluate_helpers"))       # 070's numbers, computed as 070 does
sys.path.insert(0, str(ROOT / "helpers"))                                      # compare_runs and held_out_results

import compare_runs                                                            # noqa: E402
import held_out_results                                                        # noqa: E402
import stats                                                                   # noqa: E402
from common import console, llm                                                # noqa: E402
from common.files import read_csv, read_json, read_jsonl, read_text, write_csv, write_text   # noqa: E402
from common.ground_truth import EVALUABLE, read_ground_truth, read_pool, twin_kinds   # noqa: E402
from common.step import REPORTS_DIR, RESULTS_DIR, output_of_run, repo_path, run_manifests   # noqa: E402

FOLDER = ROOT / "results" / "technical_publication"
RUN_LIST = FOLDER / "runs.tsv"
CATALOG = RESULTS_DIR / "020_clean" / "records.jsonl"
TUNING, HELD_OUT = "tuning", "held-out"
#: The numbers of stats.numbers() given besides those of stats.WITH_MARGIN: point values with no range of their own.
EXTRA = [(("describes", "majority_baseline"), "describes majority baseline"),
         (("describes", "per_entity_class_average"), "describes per entity class average")]
#: Decimals: proportions, and variances (which are small, so they keep more).
P, V = 4, 6
GROUP_COLUMNS = ["part", "schema", "thinking", "model"]
#: How many records each ranked criterion of notable_records.csv lists.
TOP = 5


# ------------------------------ the run list --------------------------------

def read_run_list(text: str) -> tuple:
    """(tuning rows, held-out 070 run ids) from the run list: a tab-separated file whose lines starting with # are
    comments. A tuning line has six fields (schema, thinking, model, repeat, 070's run id of its tuning records,
    060's run id); a held-out line has two (held-out, 070's run id of the look)."""
    tuning, held_out = [], []
    for n, line in enumerate(text.splitlines(), 1):
        if not line.strip() or line.startswith("#"):
            continue
        cells = [c.strip() for c in line.split("\t")]
        if len(cells) == 6:
            schema, thinking, model, repeat, run070, run060 = cells
            tuning.append({"schema": schema, "thinking": thinking, "model": model, "repeat": int(repeat),
                           "run_070": run070, "run_060": run060})
        elif len(cells) == 2 and cells[0] == HELD_OUT:
            held_out.append(cells[1])
        else:
            sys.exit(f"Line {n} of the run list is neither a tuning line (six fields separated by tabs: schema, "
                     f"thinking, model, repeat, 070's run id, 060's run id) nor a held-out line (held-out, then 070's "
                     f"run id): {line!r}. Correct the line, then run the command again.")
    return tuning, held_out


def groups(tuning: list, held_out_runs: list, load_tuning) -> list:
    """The groups, in the run list's order: the repeats of one schema, thinking and model on the tuning records, then
    the same on the held-out records. [{"part", "schema", "thinking", "model", "runs": [{"repeat", "run_070",
    "run_060", "run"}]}]. A held-out look finds its schema, thinking, model and repeat through its 060 run id, which
    must be a tuning line's."""
    out, at = [], {}
    for row in tuning:
        key = (TUNING, row["schema"], row["thinking"], row["model"])
        if key not in at:
            at[key] = len(out)
            out.append(dict(zip(GROUP_COLUMNS, key), runs=[]))
        out[at[key]]["runs"].append({**row, "run": load_tuning(row["run_070"])})
    by_060 = {row["run_060"]: row for row in tuning}
    for run in held_out_runs:
        ex = compare_runs.extraction_run_id(run)
        if ex not in by_060:
            sys.exit(f"The held-out look {run['run_id']} scored the run {ex} of step 060, which no tuning line of the "
                     f"run list names, so its model and repeat aren't known. Add that run's tuning line, then run the "
                     f"command again.")
        row = by_060[ex]
        key = (HELD_OUT, row["schema"], row["thinking"], row["model"])
        if key not in at:
            at[key] = len(out)
            out.append(dict(zip(GROUP_COLUMNS, key), runs=[]))
        out[at[key]]["runs"].append({"repeat": row["repeat"], "run_070": run["run_id"], "run_060": ex, "run": run})
    return out


# ------------------------------ formatting ----------------------------------

def num(v, decimals: int = P) -> str:
    """A number for a cell: empty for None, a whole number as it is, others rounded."""
    if v is None:
        return ""
    if isinstance(v, int) and not isinstance(v, bool):
        return str(v)
    return f"{v:.{decimals}f}"


def head(g: dict) -> dict:
    return {k: g[k] for k in GROUP_COLUMNS}


def records_of(run: dict, ids: list, titles: dict) -> list:
    """compare_runs.as_records, with each record's id, pool position and title, as stats.per_record reads them."""
    by_id = {r["id"]: r for r in run["records"]}
    return [{**rec, "id": i, "position": by_id[i].get("position"), "title": titles.get(i, "")}
            for i, rec in zip(ids, compare_runs.as_records(run, ids))]


# ------------------------------ the files -----------------------------------

POOLED_COLUMNS = GROUP_COLUMNS + ["runs", "records_pooled", "records_left_out", "metric", "value", "low_95",
                                  "high_95", "bootstrap_low_95", "bootstrap_high_95", "between_record_variance",
                                  "within_record_variance"]


def pooled_rows(g: dict, ids: list, left: dict) -> list:
    """metrics_pooled.csv: each number of stats.WITH_MARGIN pooled over the group's repeats (compare_runs.pooled),
    then the EXTRA numbers over every record of every repeat taken together (stats.numbers), with no range."""
    runs = [r["run"] for r in g["runs"]]
    base = {**head(g), "runs": len(runs), "records_pooled": len(ids),
            "records_left_out": sum(len(v) for v in left.values())}
    rows = [{**base, "metric": r["label"], "value": num(r["value"]), "low_95": num(r["low"]), "high_95": num(r["high"]),
             "bootstrap_low_95": num(r["boot_low"]), "bootstrap_high_95": num(r["boot_high"]),
             "between_record_variance": num(r["between"], V), "within_record_variance": num(r["within"], V)}
            for r in compare_runs.pooled(runs, ids)]
    together = stats.numbers([rec for run in runs for rec in compare_runs.as_records(run, ids)])
    rows += [{**base, "metric": label, "value": num(stats._get(together, path))} for path, label in EXTRA]
    return rows


def per_run_columns(k: int) -> list:
    return (GROUP_COLUMNS + ["metric"] + [f"{x}_{i}" for i in range(1, k + 1) for x in ("run_070", "value")]
            + ["mean", "sd", "min", "max", "width"])


def per_run_rows(g: dict, ids: list, k: int) -> list:
    """metrics_per_run.csv: one row per number, each run's own value (compare_runs.spread over the pooled records,
    and stats.numbers for the EXTRA numbers), then the mean, sample standard deviation, lowest, highest and width
    (highest − lowest) across the runs; sd and width are empty for one run."""
    runs = [r["run"] for r in g["runs"]]
    rows = [(r["label"], r["values"]) for r in compare_runs.spread(runs, ids)]
    points = [stats.numbers(compare_runs.as_records(run, ids)) for run in runs]
    rows += [(label, [stats._get(p, path) for p in points]) for path, label in EXTRA]
    out = []
    for label, values in rows:
        have = [v for v in values if v is not None]
        row = {**head(g), "metric": label,
               "mean": num(statistics.mean(have)) if have else "",
               "sd": num(statistics.stdev(have)) if len(have) > 1 else "",
               "min": num(min(have)) if have else "", "max": num(max(have)) if have else "",
               "width": num(max(have) - min(have)) if len(have) > 1 and len(have) == len(values) else ""}
        for i, (r, v) in enumerate(zip(g["runs"], values), 1):
            row[f"run_070_{i}"], row[f"value_{i}"] = r["run_070"], num(v)
        out.append(row)
    return out


PER_RECORD_COLUMNS = GROUP_COLUMNS + ["repeat", "run_070", "run_060", "position", "record_id", "title",
                                      "extraction_failed", "ground_truth_triples", "within_reach",
                                      "within_strict_reach", "occurrences", "untranslatable", "pending_pairs",
                                      "exact_pairs", "exact_strict_pairs", "partial_pairs", "partial_strict_pairs",
                                      "exact_precision", "exact_recall", "exact_f1",
                                      "partial_precision", "partial_recall", "partial_f1"]


def per_record_rows(g: dict, titles: dict) -> list:
    """per_record.csv: every record of every run, by stats.per_record (each record's own counts, by the formulas of
    stats.numbers; empty where there is nothing to divide by), in pool order."""
    out = []
    for r in g["runs"]:
        run = r["run"]
        ids = [x["id"] for x in run["records"]]
        failed = {x["id"]: x.get("extraction_failed") for x in run["records"]}
        for x in sorted(stats.per_record(records_of(run, ids, titles)), key=lambda x: x["position"]):
            out.append({**head(g), "repeat": r["repeat"], "run_070": r["run_070"], "run_060": r["run_060"],
                        "position": x["position"], "record_id": x["id"], "title": x["title"],
                        "extraction_failed": "yes" if failed[x["id"]] else "no",
                        "ground_truth_triples": x["ground_truth_triples"], "within_reach": x["within_reach"],
                        "within_strict_reach": x["within_strict_reach"], "occurrences": x["occurrences"],
                        "untranslatable": x["untranslatable"], "pending_pairs": x["pending_pairs"],
                        **{f"{level}_{k}": x[level][k] for level in ("exact", "partial")
                           for k in ("pairs", "strict_pairs")},
                        **{f"{level}_{k}": num(x[level][k]) for level in ("exact", "partial")
                           for k in ("precision", "recall", "f1")}})
    return out


DRAFTED_COLUMNS = GROUP_COLUMNS + ["runs", "records_pooled", "drafted_by", "spellings", "ground_truth_triples",
                                   "records_with_one", "metric", "value", "low_95", "high_95",
                                   "between_record_variance", "within_record_variance"]
DRAFTED_LABELS = {path: label for path, label in held_out_results.DRAFTED_BY_NUMBERS}


def drafted_rows(g: dict, ids: list) -> list:
    """by_drafting_model.csv: the group's numbers split by who drafted the ground truth triples
    (held_out_results.by_drafting_model, pooled over the repeats as the other numbers are)."""
    runs = [r["run"] for r in g["runs"]]
    by = held_out_results.by_drafting_model(runs, ids)
    if by["groups"] is None:
        print(f"  no numbers by drafting model for {g['part']} {g['schema']} {g['thinking']} {g['model']}: {by['why']}")
        return []
    out = []
    for model, e in by["groups"].items():
        for path, r in e["numbers"].items():
            out.append({**head(g), "runs": len(runs), "records_pooled": len(ids), "drafted_by": model,
                        "spellings": "; ".join(e["spellings"]), "ground_truth_triples": e["gt_triples"],
                        "records_with_one": e["records"], "metric": DRAFTED_LABELS[path], "value": num(r["value"]),
                        "low_95": num(r["low"]), "high_95": num(r["high"]),
                        "between_record_variance": num(r["between"], V), "within_record_variance": num(r["within"], V)})
    return out


# ------------------------------ 060's reports -------------------------------

RUN_COLUMNS = ["schema", "thinking", "model", "repeat", "run_060", "run_070_tuning", "run_070_held_out",
               "model_served", "thinking_sent", "records_extracted", "records_failed"] + \
              [f"{which}_{x}" for which in ("classed_triples_in_answer", "extracted_triples")
               for x in ("texts", "min", "max", "mean", "median", "sd", "total", "texts_with_none")] + \
              ["removed_total"]
#: The reasons 060's checks remove a classed triple for (docs/terminology.md, *extracted triple*: their home), each
#: with its column; "component_class_not_in_schema source_text" is one classed triple removed for both.
REASONS = {"component_class_not_in_schema": "removed_component_class_not_in_schema",
           "source_text": "removed_source_text",
           "component_class_not_in_schema source_text": "removed_component_class_not_in_schema_and_source_text",
           "duplicate": "removed_duplicate", "describes_triple": "removed_describes_triple",
           "malformed": "removed_malformed"}
#: The columns after the reasons for removal.
RUN_COLUMNS_END = ["model_calls_failed", "model_calls_cut_off", "answer_limit_tokens"]
#: The rows of the report's table *Classed triples per text*, and the names their columns take here.
DIST_ROWS = {"listed": "classed_triples_in_answer", "kept": "extracted_triples"}
DIST_KEYS = ("texts", "min", "max", "mean", "median", "sd", "total", "texts_with_none")


def _n(s: str):
    s = s.replace(",", "")
    return float(s) if "." in s else int(s)


def parse_060_report(text: str) -> dict:
    """The numbers of one 060 report that runs.csv keeps (none about payment or tokens): records extracted and
    failed, the table *Classed triples per text* (its rows listed and kept), the classed triples removed by each
    reason, and the model calls that failed or were cut off at the answer limit. Numbers may carry thousands
    commas. A reason of two words ("component_class_not_in_schema source_text") is one classed triple removed for
    both; a reason REASONS doesn't name stops it (ValueError), so no removal is left without its column."""
    def need(pattern):
        m = re.search(pattern, text, re.M)
        if not m:
            raise ValueError(f"the report has no line matching {pattern}")
        return m

    out = {}
    m = need(r"Extracted: ([\d,]+); failed: ([\d,]+)")
    out["records_extracted"], out["records_failed"] = _n(m.group(1)), _n(m.group(2))
    for which, name in DIST_ROWS.items():
        m = need(r"^\| " + which + r"\b[^|]*" + r"".join(r"\| ([\d,.]+) " for _ in DIST_KEYS) + r"\|")
        out.update({f"{name}_{k}": _n(v) for k, v in zip(DIST_KEYS, m.groups())})
    m = need(r"^- Removed: ([\d,]+) \(([^)]*)\)")
    out["removed_total"], reasons = _n(m.group(1)), {}
    if m.group(2) != "none":
        for part in m.group(2).split(", "):
            reason, count = part.rsplit(" ", 1)
            if reason not in REASONS:
                raise ValueError(f"the report names a reason for removal no column holds: {reason}")
            reasons[reason] = _n(count)
    out["reasons"] = reasons
    m = need(r"^\| failed \(after the model client's own retries\), cut-offs included \| ([\d,]+) \|")
    out["model_calls_failed"] = _n(m.group(1))
    m = need(r"^\| cut off at the answer length limit \(([\d,]+) tokens\) \| ([\d,]+) \|")
    out["answer_limit_tokens"], out["model_calls_cut_off"] = _n(m.group(1)), _n(m.group(2))
    return out


def run_rows(gs: list, report_of) -> tuple:
    """(runs.csv's columns, rows): one row per run of step 060, in the run list's order."""
    held = {r["run_060"]: r["run_070"] for g in gs if g["part"] == HELD_OUT for r in g["runs"]}
    rows = []
    for g in gs:
        if g["part"] != TUNING:
            continue
        for r in g["runs"]:
            calls = compare_runs.recipe_of(r["run"]).get("extraction (060)", {}).get("model_calls") or {}
            parsed = parse_060_report(report_of(r["run_060"]))
            reasons = parsed.pop("reasons")
            rows.append({"schema": g["schema"], "thinking": g["thinking"], "model": g["model"], "repeat": r["repeat"],
                         "run_060": r["run_060"], "run_070_tuning": r["run_070"],
                         "run_070_held_out": held.get(r["run_060"], ""),
                         "model_served": "; ".join(calls.get("served_as") or []),
                         "thinking_sent": calls.get("thinking_sent") or "", **parsed,
                         **{column: reasons.get(reason, 0) for reason, column in REASONS.items()}})
    return RUN_COLUMNS + list(REASONS.values()) + RUN_COLUMNS_END, rows


# ------------------------------ notable records -----------------------------

NOTABLE_COLUMNS = ["part", "criterion", "definition", "rank", "position", "record_id", "title", "ground_truth_triples",
                   "within_reach", "not_within_reach", "models", "mean_partial_f1", "min_partial_f1",
                   "max_partial_f1", "models_at_0"]
CRITERIA = {
    "lowest mean partial F1": f"the {TOP} records with the lowest mean, over the models, of each model's partial F1 "
                              f"on the record pooled over its repeats (records with a value only; ties by pool "
                              f"position)",
    "highest mean partial F1": f"the {TOP} records with the highest such mean (ties by pool position)",
    "no ground truth triple": "every record whose ground truth has no triple besides its describes triple",
    "every model at 0": "every record with a ground truth triple on which each model's partial F1, pooled over its "
                        "repeats, is 0",
    "most not within reach": f"the {TOP} records with the most ground truth triples not within reach (ground truth "
                             f"triples less those within reach, the fewest in any run), at least 1 (ties by pool "
                             f"position)",
}


def notable_rows(gs: list, titles: dict, schema: str = "induced", thinking: str = "lowest") -> list:
    """notable_records.csv: for each part, over the groups of one schema and thinking (every model), each record's
    partial F1 per model pooled over its repeats (compare_runs.group_parts: Σ 2 × pairs ÷ Σ (counted occurrences +
    ground truth triples)), and the records each CRITERIA picks."""
    out = []
    for part in (TUNING, HELD_OUT):
        chosen = [g for g in gs if g["part"] == part and g["schema"] == schema and g["thinking"] == thinking]
        if not chosen:
            continue
        runs_of = [[r["run"] for r in g["runs"]] for g in chosen]
        ids = [i for i in (x["id"] for x in runs_of[0][0]["records"])
               if all(i in {x["id"] for x in run["records"]} for runs in runs_of for run in runs)]
        f1 = {}
        for runs in runs_of:
            for i, (a, b) in zip(ids, compare_runs.group_parts(runs, ids, ("partial", "f1"))):
                f1.setdefault(i, []).append(a / b if b else None)
        counts = [{x["id"]: x["counts"] for x in run["records"]} for runs in runs_of for run in runs]
        position = {x["id"]: x.get("position") for x in runs_of[0][0]["records"]}
        info = {}
        for i in ids:
            gt = max(c[i]["gt"] for c in counts)
            reach = min(c[i]["within_reach"] for c in counts)
            have = [v for v in f1[i] if v is not None]
            info[i] = {"position": position[i], "record_id": i, "title": titles.get(i, ""), "ground_truth_triples": gt,
                       "within_reach": reach, "not_within_reach": gt - reach, "models": len(have),
                       "mean_partial_f1": statistics.mean(have) if have else None,
                       "min_partial_f1": min(have) if have else None, "max_partial_f1": max(have) if have else None,
                       "models_at_0": sum(v == 0 for v in have)}
        rated = [x for x in info.values() if x["mean_partial_f1"] is not None]
        picks = {
            "lowest mean partial F1": sorted(rated, key=lambda x: (x["mean_partial_f1"], x["position"]))[:TOP],
            "highest mean partial F1": sorted(rated, key=lambda x: (-x["mean_partial_f1"], x["position"]))[:TOP],
            "no ground truth triple": [x for x in info.values() if x["ground_truth_triples"] == 0],
            "every model at 0": [x for x in rated if x["ground_truth_triples"] > 0 and x["models_at_0"] == x["models"]
                                 == len(chosen)],
            "most not within reach": sorted([x for x in info.values() if x["not_within_reach"] > 0],
                                            key=lambda x: (-x["not_within_reach"], x["position"]))[:TOP],
        }
        for criterion, found in picks.items():
            for rank, x in enumerate(found, 1):
                out.append({"part": part, "criterion": criterion, "definition": CRITERIA[criterion], "rank": rank,
                            **{k: num(v) if k.endswith("partial_f1") else v for k, v in x.items()}})
    return out


# ------------------------------ records, triples, calls ---------------------

def slug(s: str) -> str:
    return re.sub(r"[^\w.-]+", "_", s.strip().lower())


def group_slug(g: dict) -> str:
    """A group's name inside a column name: ground_truth_lowest_claude-opus-5-5."""
    return f"{slug(g['schema'])}_{slug(g['thinking'])}_{g['model']}"


def record_rows(gs: list, catalog: dict, evidence: dict, twins: dict) -> tuple:
    """(records.csv's columns, rows): the induction texts of step 040 (evidence: induction_evidence.json), then the
    finished records the runs evaluated, in pool order. twins: {record id: its induction-duplicate kind against the
    induction texts} (common.ground_truth.twin_kinds). For each finished record and each group of runs that
    evaluated it, the partial F1 from its counts summed over the group's runs (compare_runs.group_parts: the same
    as from their mean over the runs) and the mean of its partial pairs over the runs."""
    columns = ["record_id", "title", "maintainer", "stratum", "role", "pool_position", "induction_duplicate_kind",
               "induction_triple_instances", "ground_truth_triples", "ground_truth_triples_by_drafting_model",
               "within_reach_ground_truth_schema", "within_reach_induced_schema", "not_within_reach_induced_schema"]
    rows = []
    for t in evidence.get("texts", []):
        rows.append({"record_id": t["id"], "title": t.get("title") or catalog.get(t["id"], {}).get("title", ""),
                     "maintainer": t.get("maintainer", ""), "stratum": t.get("stratum", ""), "role": "induction text",
                     "induction_triple_instances": len(t.get("triple_instances") or [])})
    info = {}
    for g in gs:
        for r in g["runs"]:
            for x in r["run"]["records"]:
                e = info.setdefault(x["id"], {"part": g["part"], "position": x.get("position"),
                                              "stratum": x.get("stratum", ""), "gt": x["counts"]["gt"],
                                              "drafted": {}, "reach": {}})
                for model, c in ((x.get("groups") or {}).get("drafted_by") or {}).items():
                    e["drafted"][model] = c.get("gt", 0)
                e["reach"].setdefault(g["schema"], []).append(x["counts"]["within_reach"])
    for g in gs:
        runs = [r["run"] for r in g["runs"]]
        ids = [x["id"] for x in runs[0]["records"] if all(x["id"] in {y["id"] for y in run["records"]} for run in runs)]
        f1 = compare_runs.group_parts(runs, ids, ("partial", "f1"))
        k = len(runs)
        for i, (a, b) in zip(ids, f1):
            info[i][f"partial_f1_{group_slug(g)}"] = num(a / b) if b else ""
            info[i][f"partial_pairs_{group_slug(g)}"] = num(a / 2 / k, 2)
        for name in (f"partial_f1_{group_slug(g)}", f"partial_pairs_{group_slug(g)}"):
            if name not in columns:
                columns.append(name)
    for i, e in sorted(info.items(), key=lambda kv: kv[1]["position"]):
        gt_reach = e["reach"].get("ground truth")
        ind_reach = e["reach"].get("induced")
        rows.append({"record_id": i, "title": catalog.get(i, {}).get("title", ""),
                     "maintainer": catalog.get(i, {}).get("maintainer", ""), "stratum": e["stratum"],
                     "role": e["part"], "pool_position": e["position"], "induction_duplicate_kind": twins.get(i, ""),
                     "ground_truth_triples": e["gt"],
                     "ground_truth_triples_by_drafting_model": "; ".join(f"{m}: {n}" for m, n in sorted(e["drafted"].items())),
                     "within_reach_ground_truth_schema": min(gt_reach) if gt_reach else "",
                     "within_reach_induced_schema": min(ind_reach) if ind_reach else "",
                     "not_within_reach_induced_schema": e["gt"] - min(ind_reach) if ind_reach else "",
                     **{k: v for k, v in e.items() if k.startswith("partial_")}})
    return columns, rows


def text_rows(record_rows_: list, catalog: dict) -> list:
    """record_texts.jsonl: each record's id, role, title and notes as step 020 wrote them."""
    return [{"id": r["record_id"], "role": r["role"], "title": catalog.get(r["record_id"], {}).get("title", ""),
             "notes": catalog.get(r["record_id"], {}).get("notes", "")} for r in record_rows_]


INSTANCE_COLUMNS = ["text_id", "instance", "subject", "predicate", "object", "source_text"]


def instance_rows(evidence: dict) -> list:
    """induction_triple_instances.csv: every triple instance step 040 found, by induction text, in its order."""
    return [{"text_id": t["id"], "instance": n, **{k: x.get(k, "") for k in INSTANCE_COLUMNS[2:]}}
            for t in evidence.get("texts", []) for n, x in enumerate(t.get("triple_instances") or [])]


RUN_KEY_COLUMNS = ["model", "schema", "thinking", "repeat", "run_060", "run_070"]
EXTRACTED_COLUMNS = RUN_KEY_COLUMNS + ["part", "record_id", "position", "extracted_ref", "status",
                                       "entity_classes_right", "subject_and_object_swapped",
                                       "extracted_subject", "extracted_subject_class", "extracted_predicate",
                                       "extracted_object", "extracted_object_class", "source_text", "flags",
                                       "translated_subject_class", "translated_predicate", "translated_object_class",
                                       "ground_truth_ref"]
OUTCOME_COLUMNS = RUN_KEY_COLUMNS + ["part", "record_id", "ground_truth_ref", "outcome", "entity_classes_right",
                                     "within_reach", "within_strict_reach", "extracted_ref"]
GT_COLUMNS = ["ground_truth_ref", "record_id", "part", "position", "subject", "subject_class", "predicate", "object",
              "object_class", "source_text", "drafted_by"]
REMOVED_COLUMNS = RUN_KEY_COLUMNS[:5] + ["reason", "record_id", "subject", "subject_class", "predicate", "object",
                                         "object_class", "source_text", "flags"]
#: compared_triples.csv's statuses that pair a ground truth triple with an occurrence.
PAIRED = ("exact pair", "partial pair")


def _refs(origin: str) -> tuple:
    """(the extracted triple's reference, the ground truth triple's) of a compared_triples.csv row's origin: the 060
    file and its row (0-based, after the header) as `extracted_triples.csv#N`, and the ground truth file and row as
    annotations/ground_truth/batch_NNN.csv#M."""
    ex = gt = ""
    for o in (origin or "").split("; "):
        if o.startswith("annotations/"):
            gt = o
        elif o:
            ex = "extracted_triples.csv#" + o.rsplit("#", 1)[1]
    return ex, gt


def compared_rows(key: dict, part: str, compared: list, extracted: list) -> tuple:
    """(extracted_triples.csv rows, ground_truth_outcomes.csv rows) of one run's compared_triples.csv rows of one
    part. extracted: the 060 run's extracted_triples.csv rows, for each occurrence's source text and flags (a row's
    index is the N of its reference). An occurrence's translated entity classes and predicate are given only when
    they differ from the extracted ones (an induced schema)."""
    ex_rows, gt_rows = [], []
    for c in compared:
        if c.get("part") != part:
            continue
        ex, gt = _refs(c.get("origin", ""))
        base = {**key, "part": part, "record_id": c["record_id"]}
        if ex:
            src = extracted[int(ex.rsplit("#", 1)[1])] if extracted else {}
            row = {**base, "position": c.get("position", ""), "extracted_ref": ex, "status": c["status"],
                   "entity_classes_right": c.get("entity_classes_right", ""),
                   "subject_and_object_swapped": c.get("subject_and_object_swapped", ""),
                   **{f"extracted_{k}": c.get(f"extracted_{k}", "") for k in
                      ("subject", "subject_class", "predicate", "object", "object_class")},
                   "source_text": src.get("source_text", ""), "flags": src.get("flags", ""),
                   "ground_truth_ref": gt}
            for k in ("subject_class", "predicate", "object_class"):
                t = c.get(f"translated_{k}", "")
                row[f"translated_{k}"] = t if t != c.get(f"extracted_{k}", "") else ""
            ex_rows.append(row)
        if gt:
            gt_rows.append({**base, "ground_truth_ref": gt,
                            "outcome": c["status"] if c["status"] in PAIRED else "missed",
                            "entity_classes_right": c.get("entity_classes_right", ""),
                            "within_reach": c.get("within_reach", ""), "within_strict_reach": c.get("within_strict_reach", ""),
                            "extracted_ref": ex})
    return ex_rows, gt_rows


def ground_truth_rows(gt_rows: list, parts: dict) -> list:
    """ground_truth_triples.csv: every ground truth triple of the evaluated records (their describes triples left
    out, as step 070 compares those apart), by its reference annotations/ground_truth/batch_NNN.csv#M."""
    out = []
    for r in gt_rows:
        if r["id"] not in parts or r["predicate"] == "DESCRIBES":
            continue
        out.append({"ground_truth_ref": r["_origin"][0], "record_id": r["id"], "part": parts[r["id"]][0],
                    "position": parts[r["id"]][1], **{k: r.get(k, "") for k in GT_COLUMNS[4:]}})
    return out


CALL_COLUMNS = ["step", "run", "model", "thinking", "thinking_sent", "call", "record_id", "calls", "outcome",
                "error", "triple_instances", "malformed_items", "extracted_triples", "removed_classed_triples"]


def induction_call_rows(evidence: dict) -> list:
    """model_calls.csv's rows of step 040: one per induction text (its extraction calls, one per text piece), then one
    per other kind of call with how many were made (induction_evidence.json, calls)."""
    made = evidence.get("made") or {}
    base = {"step": "040_induce_schema", "run": made.get("run_id", ""), "model": made.get("model", ""),
            "thinking": made.get("thinking", ""), "thinking_sent": made.get("thinking_sent", "")}
    failed = evidence.get("failed_texts") or {}
    rows = [{**base, "call": "extract", "record_id": t["id"], "calls": t.get("pieces", ""),
             "outcome": "failed" if t["id"] in failed else "answered",
             "error": failed.get(t["id"], "") if isinstance(failed, dict) else "",
             "triple_instances": len(t.get("triple_instances") or []), "malformed_items": t.get("malformed", "")}
            for t in evidence.get("texts", [])]
    rows += [{**base, "call": kind, "calls": n} for kind, n in (evidence.get("calls") or {}).items()
             if kind not in ("extract", "reused_extractions")]
    return rows


def extraction_call_rows(key: dict, details: dict) -> list:
    """model_calls.csv's rows of one run of step 060: one per record chosen (its calls, one per text piece, and what
    came of them), from extracted_triples_details.json."""
    made = details.get("made") or {}
    return [{"step": "060_extract", "run": key["run_060"], "model": key["model"], "thinking": key["thinking"],
             "thinking_sent": made.get("thinking_sent", ""), "call": "extract", "record_id": r["id"],
             "calls": r.get("pieces", ""), "outcome": r.get("status", ""), "error": r.get("error") or "",
             "extracted_triples": r.get("kept", ""), "removed_classed_triples": r.get("removed", "")}
            for r in details.get("records", [])]


TOKEN_COLUMNS = ["step", "run", "model", "thinking", "sent_not_from_cache", "sent_read_from_cache",
                 "sent_written_to_cache", "received", "received_as_thinking", "model_calls_failed",
                 "model_calls_cut_off"]
TOKEN_LINES = {"sent_not_from_cache": "sent, not from the cache", "sent_read_from_cache": "sent, read from the cache",
               "sent_written_to_cache": "sent, written to the cache", "received_as_thinking": "received as thinking",
               "received": "received"}


def parse_tokens(text: str) -> dict:
    """A report's table *Tokens (as the service counted them)*: the run's totals (no count per call is recorded)."""
    out = {}
    for key, label in TOKEN_LINES.items():
        m = re.search(r"^\| " + re.escape(label) + r"(?: \([^|]*\))? \| ([\d,]+) \|", text, re.M)
        out[key] = _n(m.group(1)) if m else ""
    m = re.search(r"^\| failed \(after the model client's own retries\), cut-offs included \| ([\d,]+) \|", text, re.M)
    out["model_calls_failed"] = _n(m.group(1)) if m else ""
    m = re.search(r"^\| cut off at the answer length limit \([\d,]+ tokens\) \| ([\d,]+) \|", text, re.M)
    out["model_calls_cut_off"] = _n(m.group(1)) if m else ""
    return out


def guide_prompts(step: str) -> list:
    """The prompt files a step's guide lists in its section *Prompts*, as paths from the repository folder."""
    text = read_text(ROOT / step / f"{step}.md")
    section = text.split("\n## Prompts", 1)[1].split("\n## ", 1)[0] if "\n## Prompts" in text else ""
    out = []
    for name in re.findall(r"^\| `([^`]+\.txt)` \|", section, re.M):
        out.append(name if "/" in name else f"{step}/{step}_prompts/{name}")
    return out


MODEL_COLUMNS = ["model", "role", "where", "count", "count_of", "thinking", "thinking_sent", "temperature",
                 "answer_limit_tokens", "prompt_files"]


def model_rows(gs: list, evidence: dict, gt_rows: list, second_opinion: list, second_judge: list) -> list:
    """models.csv: each model and each role it had, with the settings its calls recorded and the prompt files it was
    sent (from the runs' recipes where they record them; else from the guide of the step or helper)."""
    rows = []
    made = evidence.get("made") or {}
    if made:
        prompts = [p for p in guide_prompts("040_induce_schema")]
        rows.append({"model": made.get("model", ""), "role": "schema induction", "where": "040_induce_schema",
                     "count": len(evidence.get("texts", [])), "count_of": "induction texts",
                     "thinking": made.get("thinking", ""), "thinking_sent": made.get("thinking_sent", ""),
                     "temperature": made.get("temperature", ""), "answer_limit_tokens": made.get("max_answer_tokens", ""),
                     "prompt_files": "; ".join(prompts)})
    seen = {}
    for g in gs:
        if g["part"] != TUNING:
            continue
        for r in g["runs"]:
            ex = compare_runs.recipe_of(r["run"]).get("extraction (060)", {})
            calls = ex.get("model_calls") or {}
            e = seen.setdefault((g["model"], g["thinking"]), {"runs": 0, "sent": set(), "temp": set(), "limit": set(),
                                                              "prompts": set()})
            e["runs"] += 1
            e["sent"].add(str(calls.get("thinking_sent", "")))
            e["temp"].add(str(calls.get("temperature", "")))
            e["limit"].add(str(calls.get("max_answer_tokens", "")))
            e["prompts"] |= set(ex.get("prompts") or {})
    for (model, thinking), e in seen.items():
        rows.append({"model": model, "role": "extraction", "where": "060_extract", "count": e["runs"],
                     "count_of": "runs of step 060", "thinking": thinking, "thinking_sent": "; ".join(sorted(e["sent"])),
                     "temperature": "; ".join(sorted(e["temp"])), "answer_limit_tokens": "; ".join(sorted(e["limit"])),
                     "prompt_files": "; ".join(sorted(e["prompts"]))})
    # the drafting model's name as step 070 groups it, from the spellings the ground truth files use
    named = {s: model for g in gs for r in g["runs"] for x in r["run"]["records"]
             for model, spellings in (x.get("drafted_by_spellings") or {}).items() for s in spellings}
    drafted, spelled = {}, {}
    for r in gt_rows:
        if r["predicate"] != "DESCRIBES":
            raw = r.get("drafted_by") or ""
            model = named.get(raw, raw) or "(none recorded)"
            drafted[model] = drafted.get(model, 0) + 1
            spelled.setdefault(model, set()).add(raw)
    for model, n in sorted(drafted.items(), key=lambda kv: -kv[1]):
        rows.append({"model": model, "role": "drafting the ground truth (corrected by a person)", "where": "050_annotate",
                     "count": n, "count_of": "ground truth triples of the evaluated records it drafted, written "
                                             + " or ".join(sorted(spelled[model])) + " in their drafted_by column",
                     "prompt_files": "; ".join(guide_prompts("050_annotate")) if model != "(none recorded)" else ""})
    for model, n in sorted(_count(second_opinion, "model").items()):
        rows.append({"model": model, "role": "second opinion on the ground truth", "where": "helpers/second_opinion.py",
                     "count": n, "count_of": "rows of annotations/second_opinion.csv",
                     "prompt_files": "; ".join(guide_prompts("050_annotate"))})
    for (task, model), n in sorted(_count(second_judge, "task", "model").items()):
        rows.append({"model": model, "role": f"second judge ({task})", "where": "helpers/second_judge.py", "count": n,
                     "count_of": "rows of annotations/second_judge.csv",
                     "prompt_files": f"helpers/helpers_prompts/second_judge_{task}.txt"})
    return rows


def _count(rows: list, *keys) -> dict:
    out = {}
    for r in rows:
        k = tuple(r.get(x, "") for x in keys)
        k = k[0] if len(keys) == 1 else k
        out[k] = out.get(k, 0) + 1
    return out


#: A file above this size is written in parts, one per schema and part.
MAX_BYTES = 20_000_000


def write_split(out: Path, name: str, columns: list, rows: list) -> dict:
    """Writes rows as out/name, or, when that would pass MAX_BYTES, as one file per schema and part
    (name_<schema>_<part>.csv). {file name: rows}."""
    write_csv(out / name, columns, rows)
    if (out / name).stat().st_size <= MAX_BYTES:
        return {name: len(rows)}
    (out / name).unlink()
    found = {}
    for r in rows:
        found.setdefault((slug(r.get("schema", "")), r.get("part", "")), []).append(r)
    written = {}
    for (schema, part), rs in found.items():
        part_name = f"{name[:-4]}_{schema}_{slug(part)}.csv"
        write_csv(out / part_name, columns, rs)
        written[part_name] = len(rs)
    return written


def export_details(gs: list, out: Path, catalog: dict, evidence: dict, twins: dict, gt_rows: list, file_of,
                   report_of, second_opinion: list, second_judge: list) -> tuple:
    """Writes the files of every record, triple and model call into out. file_of(step, run id, name): the path of
    the output file as that run wrote it, or None. ({file name: rows written}, [what is missing, for the README])."""
    written, missing = {}, []
    columns, recs = record_rows(gs, catalog, evidence, twins)
    write_csv(out / "records.csv", columns, recs)
    written["records.csv"] = len(recs)
    texts = text_rows(recs, catalog)
    write_text(out / "record_texts.jsonl", "".join(json.dumps(t, ensure_ascii=False) + "\n" for t in texts))
    written["record_texts.jsonl"] = len(texts)
    inst = instance_rows(evidence)
    write_csv(out / "induction_triple_instances.csv", INSTANCE_COLUMNS, inst)
    written["induction_triple_instances.csv"] = len(inst)
    parts = {r["record_id"]: (r["role"], r["pool_position"]) for r in recs if r["role"] in (TUNING, HELD_OUT)}
    gts = ground_truth_rows(gt_rows, parts)
    write_csv(out / "ground_truth_triples.csv", GT_COLUMNS, gts)
    written["ground_truth_triples.csv"] = len(gts)
    ex_all, out_all, removed, calls, tokens = [], [], [], induction_call_rows(evidence), []
    made = evidence.get("made") or {}
    if made.get("run_id"):
        tokens.append({"step": "040_induce_schema", "run": made["run_id"], "model": made.get("model", ""),
                       "thinking": made.get("thinking", ""), **parse_tokens(report_of(made["run_id"]))})
    for g in gs:
        for r in g["runs"]:
            key = {"model": g["model"], "schema": g["schema"], "thinking": g["thinking"], "repeat": r["repeat"],
                   "run_060": r["run_060"], "run_070": r["run_070"]}
            ex_path = file_of("060_extract", r["run_060"], "extracted_triples.csv")
            cmp_path = file_of("070_evaluate", r["run_070"], "compared_triples.csv")
            if cmp_path is None:
                missing.append(f"{r['run_070']}: compared_triples.csv")
                continue
            if ex_path is None:
                missing.append(f"{r['run_060']}: extracted_triples.csv")
            e, o = compared_rows(key, g["part"], read_csv(cmp_path), read_csv(ex_path) if ex_path else [])
            ex_all += e
            out_all += o
            if g["part"] != TUNING:
                continue
            rem = file_of("060_extract", r["run_060"], "extracted_triples_removed.csv")
            if rem is None:
                missing.append(f"{r['run_060']}: extracted_triples_removed.csv")
            else:
                removed += [{**{k: key[k] for k in REMOVED_COLUMNS[:5]}, "record_id": x.get("id", ""),
                             **{k: x.get(k, "") for k in REMOVED_COLUMNS[6:] + ["reason"]}} for x in read_csv(rem)]
            det = file_of("060_extract", r["run_060"], "extracted_triples_details.json")
            if det is None:
                missing.append(f"{r['run_060']}: extracted_triples_details.json")
            else:
                calls += extraction_call_rows(key, read_json(det))
            tokens.append({"step": "060_extract", "run": r["run_060"], "model": g["model"], "thinking": g["thinking"],
                           **parse_tokens(report_of(r["run_060"]))})
    written.update(write_split(out, "extracted_triples.csv", EXTRACTED_COLUMNS, ex_all))
    written.update(write_split(out, "ground_truth_outcomes.csv", OUTCOME_COLUMNS, out_all))
    for name, columns, rows in (("extracted_triples_removed.csv", REMOVED_COLUMNS, removed),
                                ("model_calls.csv", CALL_COLUMNS, calls), ("model_tokens.csv", TOKEN_COLUMNS, tokens),
                                ("models.csv", MODEL_COLUMNS,
                                 model_rows(gs, evidence, gt_rows, second_opinion, second_judge))):
        write_csv(out / name, columns, rows)
        written[name] = len(rows)
    return written, missing


# ------------------------------ the export ----------------------------------

def export(gs: list, out: Path, titles: dict, report_of) -> dict:
    """Writes the six CSV files of numbers into out; {file name: rows written}."""
    pooled, per_run, per_rec, drafted = [], [], [], []
    k = max(len(g["runs"]) for g in gs)
    for g in gs:
        runs = [r["run"] for r in g["runs"]]
        ids, left, notes = compare_runs.common_records(runs)
        for why, which in left.items():
            print(f"  {g['part']} {g['schema']} {g['thinking']} {g['model']}: {len(which)} record(s) left out: {why}")
        for note in notes:
            print(f"  {g['part']} {g['schema']} {g['thinking']} {g['model']}: {note}")
        pooled += pooled_rows(g, ids, left)
        per_run += per_run_rows(g, ids, k)
        per_rec += per_record_rows(g, titles)
        drafted += drafted_rows(g, ids)
    run_columns, runs = run_rows(gs, report_of)
    notable = notable_rows(gs, titles)
    files = {"metrics_pooled.csv": (POOLED_COLUMNS, pooled), "metrics_per_run.csv": (per_run_columns(k), per_run),
             "runs.csv": (run_columns, runs), "per_record.csv": (PER_RECORD_COLUMNS, per_rec),
             "by_drafting_model.csv": (DRAFTED_COLUMNS, drafted), "notable_records.csv": (NOTABLE_COLUMNS, notable)}
    for name, (columns, rows) in files.items():
        write_csv(out / name, columns, rows)
    return {name: len(rows) for name, (_, rows) in files.items()}


def main(argv=None) -> int:
    console.setup()                                   # what the console can't show is replaced, never a crash
    llm.forbid_model_calls("py helpers/export_results.py is free: it reads the runs 060 and 070 kept")
    ap = argparse.ArgumentParser(prog="py helpers/export_results.py", description=__doc__.split("\n\n")[1])
    ap.add_argument("--runs", default=str(RUN_LIST), help="the run list (default: results/technical_publication/runs.tsv)")
    ap.add_argument("--out", default="", help="the folder the CSV files go into (default: the run list's folder)")
    args = ap.parse_args(argv)
    run_list = Path(args.runs)
    out = Path(args.out) if args.out else run_list.parent
    tuning, held_out_ids = read_run_list(read_text(run_list))
    print(f"Reading {len(tuning)} tuning evaluation(s) and {len(held_out_ids)} held-out look(s) ...")
    gs = groups(tuning, [held_out_results.load(i) for i in held_out_ids], compare_runs.load)
    catalog = {r["id"]: r for _, r in read_jsonl(CATALOG)} if CATALOG.exists() else {}
    if not catalog:
        print(f"  {repo_path(CATALOG)} is missing, so the records' titles and texts are left empty")
    titles = {i: r.get("title") or "" for i, r in catalog.items()}
    report_of = lambda run_id: read_text(REPORTS_DIR / f"{run_id}.md")          # noqa: E731
    written = export(gs, out, titles, report_of)
    manifests = {step: run_manifests(RESULTS_DIR / step) for step in ("040_induce_schema", "060_extract", "070_evaluate")}

    def file_of(step, run_id, name):
        return output_of_run(RESULTS_DIR / step, run_id, name, manifests[step])
    induced = [r["run_060"] for g in gs if g["schema"] == "induced" for r in g["runs"]]
    used = {i.get("run_id") for r in induced if r in manifests["060_extract"]
            for i in manifests["060_extract"][r][1].get("inputs", []) if i.get("name") == "schema"}
    evidence, missing = {}, []
    if len(used) == 1 and (path := file_of("040_induce_schema", next(iter(used)), "induction_evidence.json")):
        evidence = read_json(path)
    else:
        missing.append(f"the induction evidence of the schema induction run(s) {', '.join(sorted(map(str, used)))}")
    gt = read_ground_truth(pool=read_pool(RESULTS_DIR / "030_split" / "splits.json"))
    gt_rows = list(gt.select(EVALUABLE).rows)
    finished = {r["id"] for g in gs for run in g["runs"] for r in run["run"]["records"]}
    learned = {t["id"]: catalog.get(t["id"], t) for t in evidence.get("texts", [])}
    twins = twin_kinds({i: catalog.get(i, {}) for i in finished}, learned) if learned else {}
    annotations = ROOT / "annotations"
    more, gone = export_details(gs, out, catalog, evidence, twins, gt_rows, file_of, report_of,
                                read_csv(annotations / "second_opinion.csv"), read_csv(annotations / "second_judge.csv"))
    written.update(more)
    missing += gone
    print(f"Wrote {len(written)} files into {repo_path(out)}/:")
    for name, n in written.items():
        print(f"  {name}: {n} rows, {(out / name).stat().st_size:,} bytes")
    for m in missing:
        print(f"  not exported, no copy left: {m}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
