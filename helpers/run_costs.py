"""
run_costs · What did each run of step 060 cost, and how long did it take?

Reads the kept run records of step 060 (outputs/intermediate_results/060_extract/previous_runs/*/
extracted_triples_details.json and the current one) and writes one table of every run: its run id, model, service,
thinking, schema (induced or ground truth), records, repeat, tokens (input not from the cache, cache read, cache
write, output, thinking), cost in US dollars, each batch job's processing time at the maker, and the run's wall time.
A run recorded before its record kept these (no "spent" in its record) gets what can be computed from its report and
manifest, and "not recorded" for the rest. Free: no model calls. Writes a Markdown table and a CSV file and prints
where they are.

    py helpers/run_costs.py                       the table, from what the records and reports keep
    py helpers/run_costs.py --fetch_times true    the same, and the maker's times of each batch job whose record
                                                  doesn't keep them, read by the job's id (free metadata requests:
                                                  never a job's results, never a model call)

Details: helpers/run_costs.md
"""
import argparse
import datetime as dt
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))                                                  # the repository folder, for common/

from common import console, llm                                                # noqa: E402
from common.files import read_json, write_csv, write_text                     # noqa: E402
from common.report import _duration, cell                                      # noqa: E402
from common.step import REPORTS_DIR, RESULTS_DIR, repo_path                    # noqa: E402

STEP = "060_extract"
DETAILS = "extracted_triples_details.json"
NOT_RECORDED = "not recorded"

#: The table's columns: (the CSV column, the Markdown header).
COLUMNS = (("run_id", "Run id"), ("model", "Model"), ("service", "Service"), ("thinking", "Thinking"),
           ("schema", "Schema"), ("records", "Records"), ("repeat", "Repeat"), ("input_tokens", "Input tokens"),
           ("cache_read_tokens", "Cache read"), ("cache_write_tokens", "Cache write"),
           ("output_tokens", "Output tokens"), ("reasoning_tokens", "Thinking tokens"), ("cost_usd", "Cost $"),
           ("job_processing", "Job processing time"), ("wall_time", "Run wall time"), ("notes", "Notes"))

#: The rows of a report's tokens table (common/common_helpers/report.py, model_calls), by the count they hold.
REPORT_TOKEN_ROWS = {"input_tokens": "sent, not from the cache", "cache_read_tokens": "sent, read from the cache",
                     "cache_write_tokens": "sent, written to the cache", "output_tokens": "received",
                     "reasoning_tokens": "received as thinking"}


def run_folders(results_dir: Path) -> list:
    """The folders holding a kept run record of step 060: every previous_runs/<run id>/ that has one, and the output
    folder itself (the latest run)."""
    out = RESULTS_DIR if results_dir is None else results_dir
    step = Path(out) / STEP
    folders = sorted(p.parent for p in (step / "previous_runs").glob(f"*/{DETAILS}"))
    if (step / DETAILS).exists():
        folders.append(step)
    return folders


def _read(path: Path):
    try:
        return read_json(path) if path.exists() else None
    except (ValueError, OSError):
        return None


def report_numbers(report: Path) -> dict:
    """What an old run's report says that its record doesn't keep: the token counts of its *Model calls* tokens
    table, the one-line test calls, and the replies asked again; {} when the report is missing."""
    if not report.exists():
        return {}
    text = report.read_text(encoding="utf-8")
    out = {}
    for count, words in REPORT_TOKEN_ROWS.items():
        m = re.search(r"^\| " + re.escape(words) + r"[^|]*\| ([\d,]+) \|", text, re.M)
        if m:
            out[count] = int(m.group(1).replace(",", ""))
    m = re.search(r"^\| the one-line test \(first paid call of a run\) \| (\d+) \|", text, re.M)
    if m:
        out["test_calls"] = int(m.group(1))
    m = re.search(r"^- \*\*replies asked again:\*\* ([\d,]+)", text, re.M)
    if m:
        out["asked_again"] = int(m.group(1).replace(",", ""))
    return out


def schema_of(folder: Path, manifest: dict | None) -> str:
    """Which schema the run extracted with: "ground truth" or "induced", from its schema_used.json (made:
    ground_truth_schema, by content) or, failing that, from the schema input in its manifest; the schema file's path
    when neither says; "not recorded" when nothing does."""
    used = _read(folder / "schema_used.json") or {}
    made = used.get("made") or {}
    path = made.get("schema") or next((i.get("path") for i in (manifest or {}).get("inputs", [])
                                       if i.get("name") == "schema"), None)
    if made.get("ground_truth_schema") is True:
        return "ground truth"
    if path:
        if "ground_truth_schema" in path:
            return "ground truth"
        if "040_induce_schema" in path or "induced_schema" in path:
            return "induced"
        return path
    return NOT_RECORDED


def _seconds_between(a: str | None, b: str | None) -> float | None:
    try:
        return (dt.datetime.fromisoformat(b) - dt.datetime.fromisoformat(a)).total_seconds()
    except (TypeError, ValueError):
        return None


def _old_cost(made: dict, numbers: dict, day: str | None) -> tuple:
    """(cost or None, "unknown" (no price) or "not recorded" (what it needs isn't kept) or None, why not or how it was
    computed) of a run recorded before its record kept its tokens by price, from its report's totals:
    exact only when every token was billed at one price (no batch: every request single; batch: no test call, no
    reply asked again and no answer asked again singly, so every request was a batch request) and every prompt was
    priced at the model's base tier (one price at every prompt length, or the run's input tokens, all its prompts
    together, no more than the length above which the higher price applies, so no single prompt was longer)."""
    service, model = made.get("service"), made.get("model")
    if service not in llm.DIRECT_SERVICES or llm.price_entry(model, service) is None:
        return None, "unknown", llm.run_cost([], model, service)["unknown"]
    entry = llm.price_entry(model, service)
    sent = sum(numbers.get(k) or 0 for k in ("input_tokens", "cache_read_tokens", "cache_write_tokens"))
    if entry["long_above"] is not None and sent > entry["long_above"]:
        return None, NOT_RECORDED, (f"{model}'s price depends on each prompt's length (over {entry['long_above']:,} "
                                    f"tokens), and this run's record doesn't keep its requests' lengths (its "
                                    f"{sent:,} input tokens together are more than that)")
    if not day:
        return None, NOT_RECORDED, "the run's date isn't recorded"
    batch = bool(made.get("batch"))
    if batch:
        again = sum(len(j.get("asked_again_singly") or []) for j in made.get("batch_jobs") or [])
        if numbers.get("test_calls") is None or numbers.get("asked_again") is None:
            return None, NOT_RECORDED, "its report doesn't say whether single requests were made beside the batch jobs"
        if numbers["test_calls"] or numbers["asked_again"] or again:
            return None, NOT_RECORDED, ("its batch and single requests' tokens weren't kept apart (the run made "
                                        f"{numbers['test_calls']} test call(s), asked {numbers['asked_again']} "
                                        f"reply(ies) again and {again} cut answer(s) again as single requests)")
    write = numbers.get("cache_write_tokens") or 0
    one_hour = batch and service == "anthropic"           # the 1-hour cache in every batch request (ANTHROPIC_CACHE_TTL)
    row = {"kind": "batch" if batch else "single", "tier": "base", "day": day, "answers": 0,
           "input_tokens": numbers.get("input_tokens") or 0, "cache_read_tokens": numbers.get("cache_read_tokens") or 0,
           "cache_write_tokens": 0 if one_hour else write, "cache_write_1h_tokens": write if one_hour else 0,
           "output_tokens": numbers.get("output_tokens") or 0, "reasoning_tokens": numbers.get("reasoning_tokens") or 0}
    cost = llm.run_cost([row], model, service)
    if cost["usd"] is None:
        return None, "unknown", cost["unknown"]
    return cost["usd"], None, (f"from the report's totals, every request {'a batch request' if batch else 'a single '
                               f'request'}, at the prices of {day}")


def run_row(folder: Path, reports_dir: Path, fetch=None) -> dict | None:
    """One run's row of the table, from its record (folder/extracted_triples_details.json), its manifest and, for a
    run recorded before its record kept them, its report (reports_dir/<run id>.md). fetch(service, job id): the
    maker's times of a batch job whose record doesn't keep them (llm.job_times), or None not to ask."""
    details = _read(folder / DETAILS)
    if not isinstance(details, dict) or not isinstance(details.get("made"), dict):
        return None
    made = details["made"]
    manifest = _read(folder / "_manifest.json") or {}
    run_id = made.get("run_id") or manifest.get("run_id") or folder.name
    records = details.get("records") or []
    extracted = sum(1 for r in records if r.get("status") == "extracted")
    notes = []
    row = {"run_id": run_id, "model": made.get("model"), "service": made.get("service"),
           "thinking": made.get("thinking") if made.get("thinking") is not None else
           (made.get("settings") or {}).get("thinking", NOT_RECORDED),
           "schema": schema_of(folder, manifest), "records": f"{len(records):,} ({extracted:,} extracted)",
           "repeat": made.get("repeat", (made.get("settings") or {}).get("repeat", NOT_RECORDED))}
    spent = made.get("spent")
    day = (manifest.get("started") or "")[:10] or None
    if isinstance(spent, dict):
        tokens = spent.get("tokens") or {}
        for count in REPORT_TOKEN_ROWS:
            row[count] = tokens.get(count, NOT_RECORDED)
        cost = spent.get("cost") or {}
        row["cost_usd"] = cost.get("usd") if cost.get("usd") is not None else "unknown"
        if cost.get("usd") is None and cost.get("unknown"):
            notes.append(f"cost unknown: {cost['unknown']}")
    else:
        numbers = report_numbers(Path(reports_dir) / f"{run_id}.md")
        for count in REPORT_TOKEN_ROWS:
            row[count] = numbers.get(count, NOT_RECORDED)
        if not any(count in numbers for count in REPORT_TOKEN_ROWS):
            row["cost_usd"] = NOT_RECORDED
            notes.append("tokens not recorded (no report with a tokens table)")
        else:
            notes.append("tokens from the run's report")
            usd, status, words = _old_cost(made, numbers, day)
            row["cost_usd"] = usd if usd is not None else status
            notes.append(f"cost {words}" if usd is not None else f"cost {status}: {words}")
    # each batch job's processing time at the maker
    jobs = made.get("batch_jobs") or []
    if not made.get("batch"):
        row["job_processing"] = "–"
    else:
        each, seconds = [], []
        for j in jobs:
            service = j.get("service") or made.get("service")
            p = j.get("processing") or llm.job_processing(service, j.get("maker_times"))
            if p is None and fetch is not None and j.get("id"):
                try:
                    got = fetch(service, j["id"])
                    p = llm.job_processing(service, got.get("times")) if got.get("ended") else None
                    if p:
                        notes.append(f"{j['id']}'s times read from the maker")
                except Exception as e:                      # noqa: BLE001  one job's failure leaves the rest
                    notes.append(f"{j['id']}'s times couldn't be read from the maker ({type(e).__name__}: {e})")
            if p:
                each.append(f"{j['id']}: {_duration(p['seconds'])}")
                seconds.append(p["seconds"])
            else:
                each.append(f"{j['id']}: {NOT_RECORDED}")
        row["job_processing"] = "; ".join(each) if each else "– (no batch job)"
        row["job_processing_seconds"] = ";".join(f"{s:g}" for s in seconds)
    # the run's wall time: its record's, else its manifest's start and end
    wall = (spent or {}).get("wall_time") if isinstance(spent, dict) else None
    if isinstance(wall, dict) and wall.get("seconds") is not None:
        row["wall_time_seconds"] = wall["seconds"]
    else:
        between = _seconds_between(manifest.get("started"), manifest.get("finished"))
        row["wall_time_seconds"] = between
        if between is not None:
            notes.append("wall time from the manifest's start and end")
    row["wall_time"] = (_duration(row["wall_time_seconds"]) if row["wall_time_seconds"] is not None
                        else NOT_RECORDED)
    row["notes"] = "; ".join(notes)
    return row


def collect(results_dir: Path | None = None, reports_dir: Path | None = None, fetch=None) -> list:
    """Every kept run's row, oldest first (by run id, as runs are named), each run once."""
    reports_dir = REPORTS_DIR if reports_dir is None else reports_dir
    rows, seen = [], set()
    for folder in run_folders(results_dir):
        row = run_row(folder, reports_dir, fetch)
        if row is None or row["run_id"] in seen:
            continue
        seen.add(row["run_id"])
        rows.append(row)
    from common.audit import run_order
    return sorted(rows, key=lambda r: run_order(r["run_id"]))


def _shown(value) -> str:
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, int):
        return f"{value:,}"
    if isinstance(value, float):
        return llm.money(value)
    return cell(value)


def markdown(rows: list, fetched: bool) -> str:
    lines = ["# Step 060's runs: tokens, cost and time", "",
             f"Made {dt.datetime.now().astimezone():%Y-%m-%d %H:%M} by `py helpers/run_costs.py`"
             + (" --fetch_times true" if fetched else "") + f", from {len(rows)} kept run record(s) of step 060.", "",
             "Tokens: as the service counted them (`Input tokens`: sent, not from the cache; `Thinking tokens`: of the "
             "output tokens, those the model spent thinking). `Cost $`: computed from those token counts and the "
             "makers' list prices (`PRICES` in `common/common_helpers/llm.py`), each batch request at the batch price "
             "and each single request at the standard price; not the maker's invoice. `Job processing time`: each "
             "batch job's end minus its creation, as the maker reported them. `Run wall time`: from the run's start to "
             "when its record was written (for a run recorded before that was kept, its manifest's start and end). "
             f"`{NOT_RECORDED}`: the run's record and report don't keep it (helpers/run_costs.md).", "",
             "| " + " | ".join(h for _, h in COLUMNS) + " |",
             "|" + "|".join("---:" if c in ("records", "repeat", "input_tokens", "cache_read_tokens",
                                            "cache_write_tokens", "output_tokens", "reasoning_tokens", "cost_usd",
                                            "wall_time") else "---" for c, _ in COLUMNS) + "|"]
    for r in rows:
        lines.append("| " + " | ".join(_shown(r.get(c)) for c, _ in COLUMNS) + " |")
    return "\n".join(lines) + "\n"


CSV_COLUMNS = [c for c, _ in COLUMNS if c not in ("job_processing", "wall_time")] + [
    "job_processing", "job_processing_seconds", "wall_time_seconds"]


def write(rows: list, reports_dir: Path, fetched: bool = False) -> tuple:
    """The table as outputs/reports/run_costs_<date>_<time>.md and .csv; the two paths."""
    stamp = f"{dt.datetime.now():%Y-%m-%d_%H%M%S}"
    md, csv_path = Path(reports_dir) / f"run_costs_{stamp}.md", Path(reports_dir) / f"run_costs_{stamp}.csv"
    write_text(md, markdown(rows, fetched))
    write_csv(csv_path, CSV_COLUMNS, [{k: ("" if v is None else v) for k, v in r.items()} for r in rows])
    return md, csv_path


def main(argv=None) -> int:
    console.setup()
    ap = argparse.ArgumentParser(prog="py helpers/run_costs.py", description=__doc__.split("\n\n")[1])
    ap.add_argument("--fetch_times", default="false", nargs="?", const="true", choices=("true", "false"),
                    help="read the maker's times of each batch job whose record doesn't keep them (free metadata "
                         "requests by the job's id)")
    args = ap.parse_args(argv)
    fetch = llm.job_times if args.fetch_times == "true" else None
    rows = collect(fetch=fetch)
    if not rows:
        print(f"No kept run record of step 060 yet ({repo_path(RESULTS_DIR / STEP)}/{DETAILS} and its "
              f"previous_runs/): run step 060 first.")
        return 1
    md, csv_path = write(rows, REPORTS_DIR, fetch is not None)
    print(f"{len(rows)} run(s) of step 060: {repo_path(md)} (and {repo_path(csv_path)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
