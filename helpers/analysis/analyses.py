"""
analyses · The numbers of docs/analysis/rescore_2026-11-13.md, recall_by_rule.md and by_record_kind.md.

Produces: outputs/analysis/results.json: the reported runs' numbers and the re-scored runs' numbers (pooled over the
repeats, per repeat, and the decision rule across schemas, by helpers/compare_runs.py's own functions), the partial
pairs with no verdict, recall by guideline rule, and each evaluated record's counts with its stratum.

    py helpers/analysis/analyses.py          after py helpers/analysis/rescore_runs.py

No model call (llm.forbid_model_calls first): it reads step 070's kept evaluations
(outputs/intermediate_results/070_evaluate/evaluations/), the six runs' files in outputs/analysis/runs/, the ground
truth files, annotations/partial_pair_reviews.csv, annotations/guidelines.md and docs/reported_numbers.json.
"""
import collections
import re
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "outputs" / "analysis"                                         # the working folder (not in Git)
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "helpers"))
import compare_runs as c                                                       # noqa: E402
from common import llm                                                         # noqa: E402
from common.partial_reviews import read_reviews, row_key                       # noqa: E402
from common.triples_io import canonical_row
from common.files import read_csv, read_json, read_jsonl, read_text, write_json                                    # noqa: E402

llm.forbid_model_calls("py helpers/analysis/analyses.py is free: it reads saved files only")
RECIPES = ("induced schema", "ground truth schema")
SAVED = ["1816", "1816-2", "1816-3", "1817", "1817-2", "1817-3"]              # outputs/analysis/runs/<name>/
OLD = read_json(ROOT / "docs" / "reported_numbers.json")["runs"]
_made = read_json(HERE / "runs.json")
NEW = {RECIPES[0]: [_made[n] for n in SAVED[:3]], RECIPES[1]: [_made[n] for n in SAVED[3:]]}
RECIPE_OF = dict(zip(SAVED, ["induced schema"] * 3 + ["ground truth schema"] * 3))


def numbers(ids: dict) -> dict:
    induced = [c.load(e) for e in ids["induced schema"]]
    reference = [c.load(e) for e in ids["ground truth schema"]]
    common, left, _ = c.common_records(induced, False)
    out = {"records": len(common), "left": left,
           "gt_triples": [sum(r["counts"]["gt"] for r in run["records"]) for run in induced + reference],
           "occurrences": [sum(r["counts"]["extracted"] for r in run["records"]) for run in induced + reference],
           "pooled": {r["label"]: (r["value"], r["low"], r["high"]) for r in c.pooled(induced, common)},
           "repeats": {r["label"]: r["values"] for r in c.spread(induced, common)}}
    common_ref, _, _ = c.common_records(reference, False)
    out["pooled_reference"] = {r["label"]: (r["value"], r["low"], r["high"]) for r in c.pooled(reference, common_ref)}
    out["repeats_reference"] = {r["label"]: r["values"] for r in c.spread(reference, common_ref)}
    both, _, _ = c.common_records(induced + reference, True)
    base, other = c.paired_parts(induced, reference, both)
    test = c.sign_flip(base, other)
    out["decision"] = {"records": len(both), "f1_reference": c._f(test["changed"]), "D": c._f(test["diff"]), "p": float(test["p"])}
    return out


def saved_rows(name: str) -> list:
    return read_csv(HERE / "runs" / name / "compared_triples.csv")


def unjudged() -> tuple:
    """(pairs, per run and record counts): the partial pairs of the six new runs with no verdict."""
    reviews = read_reviews()
    found, per = {}, collections.defaultdict(lambda: collections.Counter())
    for name in SAVED:
        for row in saved_rows(name):
            if row["status"] == "partial pair" and row_key(row) not in reviews:
                k = row_key(row)
                e = found.setdefault(k, {"record_id": row["record_id"],
                                         "ground_truth": [row[f"ground_truth_{s}"] for s in ("subject", "predicate", "object")],
                                         "translated": [row[f"translated_{s}"] for s in ("subject", "predicate", "object")],
                                         "within_reach": row["within_reach"], "runs": []})
                e["runs"].append(name)
                per[name][row["record_id"]] += 1
    return list(found.values()), per


def pooled_partial(ids: list, minus: dict) -> dict:
    """Partial precision, recall and F1 pooled over the runs' records, with `minus` pairs taken off per (run, record)."""
    pairs = counted = gt = 0
    for name, run_id in ids:
        for r in c.load(run_id)["records"]:
            k = r["counts"]
            pairs += k["partial_pairs"] - minus.get(name, {}).get(r["id"], 0)
            counted += k["extracted"] - k["untranslatable"] - k["partial_pending_pairs"]
            gt += k["gt"]
    return {"pairs": pairs, "counted_occurrences": counted, "gt": gt, "precision": pairs / counted, "recall": pairs / gt,
            "f1": 2 * pairs / (counted + gt)}


def rule_titles() -> dict:
    text = read_text(ROOT / "annotations" / "guidelines.md")
    return {int(n): re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t).strip()
            for n, t in re.findall(r"^(\d+)\. \*\*(.+?)\*\*", text, re.M)}


SLOTS = ("subject", "subject_class", "predicate", "object", "object_class")


def ground_truth_rules() -> dict:
    """{(record id, the classed triple tidied as 070 tidies it): [rule numbers]} for every ground truth row."""
    out = {}
    for path in sorted((ROOT / "annotations" / "ground_truth").glob("batch_*.csv")):
        for raw in read_csv(path):
            row = canonical_row(raw, blank="")
            key = (row["id"].strip(),) + tuple(" ".join(str(row[s]).split()) for s in SLOTS)
            out[key] = [int(x) for x in re.findall(r"\d+", raw.get("rules") or "")]
    return out


def by_rule() -> dict:
    rules = ground_truth_rules()
    groups = collections.defaultdict(lambda: {n: {"n": 0, "exact": 0, "partial": 0, "within_reach": 0} for n in SAVED})
    unmatched = 0
    for name in SAVED:
        for row in saved_rows(name):
            if row["status"] not in ("exact pair", "partial pair", "ground truth only"):
                continue
            key = (row["record_id"].strip(),) + tuple(" ".join(row[f"ground_truth_{s}"].split()) for s in SLOTS)
            if key not in rules:
                unmatched += 1
                continue
            for g in ["all"] + (rules[key] or ["none listed"]):
                e = groups[g][name]
                e["n"] += 1
                e["exact"] += row["status"] == "exact pair"
                e["partial"] += row["status"] != "ground truth only"
                e["within_reach"] += row["within_reach"] == "yes"
    return {"unmatched": unmatched, "groups": {str(g): v for g, v in groups.items()}}


def by_kind() -> dict:
    records = {}
    for _, r in read_jsonl(ROOT / "outputs/intermediate_results/020_clean/records.jsonl"):
        records[r["id"]] = r
    per = {}
    for name in SAVED:
        m = read_json(HERE / "runs" / name / "metrics.json")
        ev = {r["id"]: r for r in c.load(dict(zip(SAVED, NEW["induced schema"] + NEW["ground truth schema"]))[name])["records"]}
        for x in m["parts"]["tuning"]["per_record"]:
            r = records[x["id"]]
            words = len(f"{r.get('title') or ''} {r.get('notes') or ''}".split())
            e = per.setdefault(x["id"], {"title": x["title"], "position": x["position"], "stratum": ev[x["id"]]["stratum"],
                                         "maintainer": r.get("maintainer"), "words": words, "runs": {}})
            k = ev[x["id"]]["counts"]
            e["runs"][name] = {"pairs": k["partial_pairs"], "gt": k["gt"],
                               "counted": k["extracted"] - k["untranslatable"] - k["partial_pending_pairs"],
                               "f1": x["partial"]["f1"], "precision": x["partial"]["precision"], "recall": x["partial"]["recall"]}
    catalog_words = sorted(len(f"{r.get('title') or ''} {r.get('notes') or ''}".split()) for r in records.values())
    return {"records": per, "catalog": {"records": len(records), "median_words": statistics.median(catalog_words),
                                        "mean_words": statistics.mean(catalog_words)}}


def main():
    pairs, per = unjudged()
    new_ids = list(zip(SAVED, NEW["induced schema"] + NEW["ground truth schema"]))
    minus = {n: dict(v) for n, v in per.items()}
    out = {"old": numbers(OLD), "new": numbers(NEW), "unjudged": pairs, "unjudged_per_run": minus,
           "what_if": {"induced, as scored": pooled_partial(new_ids[:3], {}),
                       "induced, unjudged pairs taken off": pooled_partial(new_ids[:3], minus),
                       "ground truth schema, as scored": pooled_partial(new_ids[3:], {}),
                       "ground truth schema, unjudged pairs taken off": pooled_partial(new_ids[3:], minus)},
           "rule_titles": rule_titles(), "by_rule": by_rule(), "by_kind": by_kind()}
    write_json(HERE / "results.json", out)
    print("wrote", HERE / "results.json")


if __name__ == "__main__":
    main()
