"""
tables · The tables of docs/analysis/recall_by_rule.md and by_record_kind.md, and docs/analysis/recall_by_rule.csv.

Produces: docs/analysis/recall_by_rule.csv (one row per guideline rule: its ground truth triples and their recall,
per schema and over the six runs) and outputs/analysis/tables.json (the same rows and the tables by stratum, by
length of text and per record, as Markdown, which write_docs.py places in the docs).

    py helpers/analysis/tables.py            after analyses.py and prompt_sizes.py

No model call: it reads outputs/analysis/results.json and prompt_sizes.json only.
"""
import json, statistics, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from common.files import read_json, write_csv, write_json                      # noqa: E402
HERE = ROOT / "outputs" / "analysis"                                         # the working folder (not in Git)
r = read_json(HERE / "results.json")
sizes = read_json(HERE / "prompt_sizes.json")
IND, REF = ["1816", "1816-2", "1816-3"], ["1817", "1817-2", "1817-3"]
pc = lambda v: f"{100 * v:.1f}%"
out = {}

# ---- by rule
titles = {int(k): v for k, v in r["rule_titles"].items()}
groups = r["by_rule"]["groups"]
order = sorted((g for g in groups if g.isdigit()), key=int) + ["none listed", "all"]
rows, md = [], []
for g in order:
    v = groups[g]
    n = v["1816"]["n"]
    assert all(e["n"] == n for e in v.values())
    def rec(runs, level): return statistics.mean(v[x][level] / n for x in runs)
    title = titles.get(int(g), "") if g.isdigit() else {"none listed": "(no rule recorded)", "all": "(all ground truth triples, for reference)"}[g]
    row = {"rule": g, "title": title, "ground_truth_triples": n, "within_reach_induced_schema": v["1816"]["within_reach"],
           "partial_recall_induced_schema": rec(IND, "partial"), "exact_recall_induced_schema": rec(IND, "exact"),
           "partial_recall_ground_truth_schema": rec(REF, "partial"), "exact_recall_ground_truth_schema": rec(REF, "exact"),
           "partial_recall_six_runs": rec(IND + REF, "partial"), "exact_recall_six_runs": rec(IND + REF, "exact"),
           "too_small": "yes" if n < 10 else "no"}
    rows.append(row)
    md.append(f"| {g} | {title} | {n}{' (too small)' if n < 10 else ''} | {row['within_reach_induced_schema']} | {pc(row['partial_recall_induced_schema'])} | "
              f"{pc(row['partial_recall_ground_truth_schema'])} | {pc(row['partial_recall_six_runs'])} | {pc(row['exact_recall_six_runs'])} |")
write_csv(ROOT / "docs/analysis/recall_by_rule.csv", list(rows[0]),
          [{k: (f"{x:.4f}" if isinstance(x, float) else x) for k, x in row.items()} for row in rows])
out["by_rule_md"] = "\n".join(md)

# ---- by kind of record
recs = r["by_kind"]["records"]
chars = {}
for q in sizes["induced schema"]["requests"]:
    chars[q["id"]] = chars.get(q["id"], 0) + q["piece_chars"]
median = statistics.median(chars.values())
def pooled(ids, runs):
    vals = []
    for x in runs:
        p = sum(recs[i]["runs"][x]["pairs"] for i in ids); q = sum(recs[i]["runs"][x]["counted"] + recs[i]["runs"][x]["gt"] for i in ids)
        vals.append(2 * p / q)
    return vals
def own(ids, runs):
    return statistics.mean(statistics.mean((recs[i]["runs"][x]["f1"] or 0.0) for x in runs) for i in ids)
def table(kinds):
    lines = []
    for name, ids in kinds:
        a, b = pooled(ids, IND), pooled(ids, REF)
        lines.append(f"| {name} | {len(ids)} | {sum(recs[i]['runs']['1816']['gt'] for i in ids)} | {pc(statistics.mean(a))} ({pc(min(a))} to {pc(max(a))}) | "
                     f"{pc(own(ids, IND))} | {pc(statistics.mean(b))} ({pc(min(b))} to {pc(max(b))}) |")
    return "\n".join(lines)
strata = {}
for i, e in recs.items():
    strata.setdefault(e["stratum"], []).append(i)
out["strata_md"] = table(sorted(strata.items(), key=lambda kv: -len(kv[1])) + [("all evaluated records", list(recs))])
short = [i for i in recs if chars[i] <= median]; long_ = [i for i in recs if chars[i] > median]
out["length_md"] = table([(f"at most {median:g} characters", short), (f"more than {median:g} characters", long_), ("all evaluated records", list(recs))])
out["median_chars"] = median
out["none_f1"] = sum(1 for e in recs.values() for x in e["runs"].values() if x["f1"] is None)
per = []
for i, e in sorted(recs.items(), key=lambda kv: kv[1]["position"]):
    a = [e["runs"][x]["f1"] or 0.0 for x in IND]
    per.append(f"| {e['position']} | {e['title']} | {e['stratum']} | {chars[i]} | {e['runs']['1816']['gt']} | {pc(statistics.mean(a))} |")
out["per_record_md"] = "\n".join(per)
write_json(HERE / "tables.json", out)
print("wrote docs/analysis/recall_by_rule.csv and outputs/analysis/tables.json")
