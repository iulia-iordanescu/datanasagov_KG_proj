"""
partial_pairs · The partial pairs of several 070 runs, to review in a file that travels through Git.

Step 070's partial pairs need a person's verdict (annotations/partial_pair_reviews.csv), and the annotation tool's
*Partial pairs* view shows only the latest 070 run's. Repeats of one recipe each pair differently, and their outputs
stay on the computer that ran them, so this collects the partial pairs of the tuning records of the runs given that
have no verdict yet (each pair once, filed under the key step 070 matches a verdict by:
common/common_helpers/partial_reviews.py, pair_key) into annotations/partial_pairs_to_review.csv, in Git, with an
empty column verdict to fill on any computer; then moves the filled verdicts into annotations/partial_pair_reviews.csv:

    py helpers/partial_pairs.py                                      list the 070 runs whose pairs are kept
    py helpers/partial_pairs.py --runs <070 run id> <070 run id> ... collect their partial pairs with no verdict
    py helpers/partial_pairs.py --apply true                         move the filled verdicts into partial_pair_reviews.csv
    py helpers/partial_pairs.py --delete_stale true --runs <070 run id> ...
                                                                     delete the verdicts that match no partial pair
                                                                     of those runs (step 070's warning "no longer match")

Each run's pairs are read from its compared_triples.csv (070_evaluate/070_evaluate.md, Outputs): the live one, or the
earlier version kept in previous_runs/ (common/common_helpers/step.py, PREVIOUS_RUNS), found by the sha256 its
run's manifest records, so the file read is the run's own. Free: no model calls. Writes only the files named above.

Reads:   outputs/intermediate_results/070_evaluate/ (each run's _manifest.json and compared_triples.csv),
         020's records.jsonl (the records' titles), annotations/partial_pair_reviews.csv
Writes:  annotations/partial_pairs_to_review.csv; with --apply true or --delete_stale true,
         annotations/partial_pair_reviews.csv
Details: helpers/partial_pairs.md
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))                                                  # the repository folder, for common/
sys.path.insert(0, str(ROOT / "070_evaluate" / "070_evaluate_helpers"))       # 070's pairing, as 070 pairs

import pairing                                                                 # noqa: E402
from moves import COMPARED_NAME, _triple                                       # noqa: E402
from common import audit, console                                              # noqa: E402
from common.files import locked, read_csv, read_csv_table, read_json, write_csv  # noqa: E402
from common.ground_truth import TUNING                                         # noqa: E402
from common.latest import latest_by_key                                        # noqa: E402
from common.partial_reviews import (COLUMNS as REVIEW_COLUMNS, GROUND_TRUTH_ONLY, NOT_SAME, PARTIAL_PAIR,  # noqa: E402
                                    REVIEWS_PATH, SAME, SLOTS, read_reviews, row_key, verdict_of)
from common.records_io import load_records                                     # noqa: E402
from common.step import ANNOTATIONS_DIR, MANIFEST_NAME, PREVIOUS_RUNS, RESULTS_DIR, repo_path  # noqa: E402

COMMAND = "py helpers/partial_pairs.py"
OUTPUT = RESULTS_DIR / "070_evaluate"
RECORDS = RESULTS_DIR / "020_clean" / "records.jsonl"
TO_REVIEW_PATH = ANNOTATIONS_DIR / "partial_pairs_to_review.csv"
CLASSED = ("subject", "subject_class", "predicate", "object", "object_class")
KEY_COLUMNS = [c for c in REVIEW_COLUMNS if c not in ("record_id", "verdict")]
#: The review file's columns: what to read first, the verdict, then the cells the verdict is filed under (copied
#: as they are into partial_pair_reviews.csv) and their fingerprint, which tells a hand edit of those cells.
TO_REVIEW_COLUMNS = (["record_id", "record_title", "predicate", "ground_truth_triple", "extracted_triple", "runs",
                      "verdict"] + KEY_COLUMNS + ["pair_fingerprint"])
ALLOWED = f'"{SAME}" or "{NOT_SAME}"'


class Problem(Exception):
    """Something to fix before anything is written: the message says what and how."""


# ------------------------------ finding a run's pairs ------------------------------

def _manifests(output: Path) -> dict:
    """{run id: (its folder, its manifest)} of the live run and of every run kept in previous_runs/."""
    found = {}
    for path in [output / MANIFEST_NAME, *sorted((output / PREVIOUS_RUNS).glob(f"*/{MANIFEST_NAME}"))]:
        try:
            m = read_json(path)
        except (OSError, ValueError):
            continue
        if m.get("run_id"):
            found.setdefault(m["run_id"], (path.parent, m))
    return found


def kept_runs(output: Path = OUTPUT) -> list:
    """The 070 run ids whose compared_triples.csv can still be read, oldest first."""
    found = _manifests(output)
    return sorted((r for r in found if _compared_file(r, found, output)), key=audit.run_order)


def _compared_file(run_id: str, found: dict, output: Path) -> Path | None:
    """The run's own compared_triples.csv: a file of that name, live or in previous_runs/, with the sha256 the run's
    manifest records for it (a later run that left the file unchanged keeps one copy only)."""
    folder, manifest = found[run_id]
    want = next((o.get("sha256") for o in manifest.get("outputs", []) if o.get("file") == COMPARED_NAME), None)
    if not want:
        return None
    for path in [folder / COMPARED_NAME, output / COMPARED_NAME, *(output / PREVIOUS_RUNS).glob(f"*/{COMPARED_NAME}")]:
        if path.is_file() and audit.sha256([path]) == want:
            return path
    return None


def compared_rows(run_ids: list, output: Path = OUTPUT) -> dict:
    """{run id: its compared_triples.csv rows}. Problem when a run is given twice, or its file can't be found."""
    twice = sorted({r for r in run_ids if run_ids.count(r) > 1})
    if twice:
        raise Problem(f"The same run is given more than once ({', '.join(twice)}): give each run once.")
    found = _manifests(output)
    out, missing = {}, []
    for r in run_ids:
        path = _compared_file(r, found, output) if r in found else None
        if path is None:
            missing.append(r)
        else:
            out[r] = read_csv(path)
    if missing:
        kept = kept_runs(output)
        raise Problem(f"No {COMPARED_NAME} is kept for {', '.join(missing)} in {repo_path(output)}/ (live, or under "
                      f"{PREVIOUS_RUNS}/ with the sha256 the run's manifest records), so its pairs can't be read. "
                      + (f"The runs kept: {', '.join(kept)}. Copy the run ids from there (or from the top of each "
                         f"070 report), then run the command again." if kept else
                         "No run's file is kept: run `py 070_evaluate/run.py` first."))
    return out


def _gt(row: dict) -> dict:
    return {k: row.get(f"ground_truth_{k}") or "" for k in CLASSED}


def _translated(row: dict) -> dict:
    return {k: row.get(f"translated_{k}") or "" for k in CLASSED}


def tuning_records(rows: list) -> dict:
    """{record id: (its ground truth triples, its translated extracted triples)} of the run's tuning records, as
    compared_triples.csv lists them (every ground truth triple is in a pair or ground truth only; every occurrence
    in a pair or on a row of its own)."""
    out = {}
    for r in rows:
        if r.get("part") != TUNING:
            continue
        gt, ex = out.setdefault(r["record_id"], ([], []))
        if r.get("ground_truth_predicate"):
            gt.append(_gt(r))
        if r.get("status") != GROUND_TRUTH_ONLY and r.get("translated_predicate"):
            ex.append(_translated(r))
    return out


# ------------------------------ collecting ------------------------------

def fingerprint(row: dict) -> str:
    """A short sha256 of the cells a verdict is filed under (the record id and both triples), as written."""
    text = json.dumps([(row.get(c) or "") for c in ["record_id"] + KEY_COLUMNS], ensure_ascii=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def collect(runs: dict, reviews: dict, titles: dict) -> list:
    """The review file's rows: each partial pair of a tuning record in any of the runs ({run id: rows}) whose
    pair_key has no verdict in reviews, once per key (the first run's spelling), with the runs that had it."""
    by_key = {}
    for run_id in sorted(runs, key=audit.run_order):
        for r in runs[run_id]:
            if r.get("status") != PARTIAL_PAIR or r.get("part") != TUNING:
                continue
            k = row_key(r)
            if k in reviews:
                continue
            if k not in by_key:
                row = {"record_id": r["record_id"], "record_title": titles.get(r["record_id"], ""),
                       "predicate": r.get("ground_truth_predicate", ""),
                       "ground_truth_triple": _triple(_gt(r)), "extracted_triple": _triple(_translated(r)),
                       "verdict": "", "_runs": [],
                       **{f"ground_truth_{s}": r.get(f"ground_truth_{s}", "") for s in SLOTS},
                       **{f"translated_{s}": r.get(f"translated_{s}", "") for s in SLOTS}}
                row["pair_fingerprint"] = fingerprint(row)
                by_key[k] = row
            if run_id not in by_key[k]["_runs"]:
                by_key[k]["_runs"].append(run_id)
    rows = sorted(by_key.values(), key=lambda x: (x["record_title"] or x["record_id"], x["record_id"],
                                                 x["ground_truth_triple"], x["extracted_triple"]))
    for row in rows:
        row["runs"] = "; ".join(row.pop("_runs"))
    return rows


def _filled(path: Path) -> list:
    """The review file's rows with something in verdict."""
    if not path.exists():
        return []
    return [r for r in read_csv_table(path)[1] if (r.get("verdict") or "").strip()]


def write_to_review(run_ids: list, output: Path = OUTPUT, to_review: Path = TO_REVIEW_PATH,
                    reviews_path: Path = REVIEWS_PATH, records: Path = RECORDS) -> list:
    """Collect and write the review file; returns its rows. Problem when the file still holds filled verdicts (they
    would be lost)."""
    filled = _filled(to_review)
    if filled:
        raise Problem(f"{repo_path(to_review)} still holds {len(filled)} filled verdict(s) not yet moved into "
                      f"{repo_path(reviews_path)} (e.g. line {filled[0]['_line']}), and collecting again would "
                      f"replace them. Run `{COMMAND} --apply true` first, then this command again.")
    runs = compared_rows(run_ids, output)
    titles = {rid: str(rec.get("title") or "") for rid, rec in load_records(records).items()} if records.exists() else {}
    rows = collect(runs, read_reviews(reviews_path), titles)
    write_csv(to_review, TO_REVIEW_COLUMNS, rows)
    return rows


# ------------------------------ applying ------------------------------

def _where(r: dict, path: Path) -> str:
    return f"{repo_path(path)} line {r['_line']} ({(r.get('record_id') or '').strip() or 'no record id'})"


def plan_apply(to_review: Path = TO_REVIEW_PATH, reviews_path: Path = REVIEWS_PATH) -> tuple:
    """(the rows to add to partial_pair_reviews.csv, the review file's lines to take out of it, the verdicts already
    there). Problem, naming every line, when a verdict isn't one of the two, a row's triples were edited since it was
    collected (its fingerprint), or two verdicts on one pair differ (in the review file, or with one already in
    partial_pair_reviews.csv: common/common_helpers/latest.py, the one rule)."""
    filled = _filled(to_review)
    problems = []
    for r in filled:
        if verdict_of(r) not in (SAME, NOT_SAME):
            problems.append(f"{_where(r, to_review)}: the verdict {(r.get('verdict') or '').strip()!r} is neither "
                            f"{ALLOWED} (case and spacing aside): write one of the two, or empty the cell")
        elif (r.get("pair_fingerprint") or "").strip() != fingerprint(r):
            problems.append(f"{_where(r, to_review)}: the cells it is filed under (record_id, ground_truth_subject "
                            f"to translated_object) were changed since it was collected, so it may no longer name a "
                            f"partial pair: put them back (`git diff {repo_path(to_review)}`), or collect again")
    good = [r for r in filled if verdict_of(r) in (SAME, NOT_SAME) and (r.get("pair_fingerprint") or "").strip() == fingerprint(r)]
    chosen, conflicts = latest_by_key(good, row_key, verdict_of, where=lambda r: _where(r, to_review))
    problems += conflicts
    existing = {}
    if reviews_path.exists():
        for r in read_csv_table(reviews_path)[1]:
            if verdict_of(r) in (SAME, NOT_SAME):
                existing.setdefault(row_key(r), []).append(r)
    add, already = [], []
    for k, r in chosen.items():
        there = existing.get(k, [])
        other = [e for e in there if verdict_of(e) != verdict_of(r)]
        if other:
            problems.append(f"conflict: {_where(r, to_review)} ({verdict_of(r)!r}) and "
                            + " and ".join(f"{_where(e, reviews_path)} ({verdict_of(e)!r})" for e in other)
                            + f" are about the same pair, and differ: keep one verdict (empty the cell here, or "
                              f"delete the row there)")
        elif there:
            already.append(r)
        else:
            add.append({**{c: (r.get(c) or "").strip() for c in REVIEW_COLUMNS}, "verdict": verdict_of(r)})
    if problems:
        raise Problem(f"Nothing was moved: {len(problems)} problem(s) to fix first, in the file named:\n  - "
                      + "\n  - ".join(problems))
    return add, {r["_line"] for r in filled}, already


def apply(to_review: Path = TO_REVIEW_PATH, reviews_path: Path = REVIEWS_PATH) -> tuple:
    """Move the filled verdicts: add them to partial_pair_reviews.csv (a pair already there with the same verdict
    once), and take their rows out of the review file. Returns (added, already there)."""
    add, lines, already = plan_apply(to_review, reviews_path)
    if not lines:
        return [], []
    with locked(reviews_path):                       # as the annotation tool saves: one writer at a time
        rows = read_csv(reviews_path) if reviews_path.exists() else []
        write_csv(reviews_path, REVIEW_COLUMNS, rows + add)
    columns, rows = read_csv_table(to_review)
    write_csv(to_review, columns or TO_REVIEW_COLUMNS, [r for r in rows if r["_line"] not in lines])
    return add, already


# ------------------------------ stale verdicts ------------------------------

def stale_verdicts(runs: dict, reviews: dict) -> list:
    """The keys of the verdicts that step 070 lists as "no longer match a partial pair", over all the runs given: a
    verdict on a tuning record evaluated in some run whose key can pair at the partial level in none of them
    (pairing.verdict_keys, computed from each run's triples). A verdict on a record no run evaluated is kept."""
    evaluated, live = set(), set()
    for rows in runs.values():
        for rid, (gt, ex) in tuning_records(rows).items():
            evaluated.add(rid.strip())
            live |= pairing.verdict_keys(rid, gt, ex)
    return sorted(k for k in reviews if k[0] in evaluated and k not in live)


def delete_stale(run_ids: list, output: Path = OUTPUT, reviews_path: Path = REVIEWS_PATH) -> list:
    """Delete the rows of partial_pair_reviews.csv filed under a stale key; returns those rows."""
    stale = set(stale_verdicts(compared_rows(run_ids, output), read_reviews(reviews_path)))
    if not stale:
        return []
    with locked(reviews_path):
        rows = read_csv(reviews_path)
        gone = [r for r in rows if row_key(r) in stale]
        write_csv(reviews_path, REVIEW_COLUMNS, [r for r in rows if row_key(r) not in stale])
    return gone


# ------------------------------ the command ------------------------------

def main(argv=None) -> int:
    console.setup()                                   # what the console can't show is replaced, never a crash
    ap = argparse.ArgumentParser(prog=COMMAND, description=__doc__.split("\n\n")[1])
    ap.add_argument("--runs", nargs="+", metavar="RUN_ID", help="070's run ids: collect their partial pairs with no verdict")
    ap.add_argument("--apply", choices=("true", "false"), default="false",
                    help=f"true: move the filled verdicts of {repo_path(TO_REVIEW_PATH)} into {repo_path(REVIEWS_PATH)}")
    ap.add_argument("--delete_stale", choices=("true", "false"), default="false",
                    help="true, with --runs: delete the verdicts that match no partial pair of those runs")
    args = ap.parse_args(argv)
    try:
        if args.apply == "true":
            if args.runs or args.delete_stale == "true":
                raise Problem(f"--apply true takes nothing else: `{COMMAND} --apply true`.")
            if not _filled(TO_REVIEW_PATH):
                print(f"No verdict is filled in {repo_path(TO_REVIEW_PATH)}: nothing to move.")
                return 0
            add, already = apply()
            print(f"Moved {len(add) + len(already)} verdict(s) out of {repo_path(TO_REVIEW_PATH)}: {len(add)} added to "
                  f"{repo_path(REVIEWS_PATH)}" + (f", {len(already)} already there with the same verdict" if already else "")
                  + ". Then run `py 070_evaluate/run.py` again.")
            return 0
        if args.delete_stale == "true":
            if not args.runs:
                raise Problem(f"Give the runs whose pairs the verdicts must still match: `{COMMAND} --delete_stale true "
                              f"--runs <070 run id> ...` (`{COMMAND}` lists them).")
            gone = delete_stale(args.runs)
            print(f"Deleted {len(gone)} verdict(s) of {repo_path(REVIEWS_PATH)} that match no partial pair of "
                  f"{', '.join(args.runs)}" + (":" if gone else "."))
            for r in gone:
                print(f"  {r['record_id']}: {' '.join(r[f'ground_truth_{s}'] for s in SLOTS)} / "
                      f"{' '.join(r[f'translated_{s}'] for s in SLOTS)} ({r['verdict']})")
            return 0
        if not args.runs:
            kept = kept_runs()
            if not kept:
                print(f"No 070 run's {COMPARED_NAME} is kept in {repo_path(OUTPUT)}/: run `py 070_evaluate/run.py` first.")
                return 0
            print(f"070 runs whose partial pairs can be collected, oldest first:\n  " + "\n  ".join(kept)
                  + f"\n\nCollect: `{COMMAND} --runs <run id> <run id> ...`")
            return 0
        rows = write_to_review(args.runs)
        print(f"{len(rows)} partial pair(s) of tuning records with no verdict, from {len(args.runs)} run(s), written to "
              f"{repo_path(TO_REVIEW_PATH)}. Fill its column verdict with {ALLOWED}, then "
              f"`{COMMAND} --apply true`.")
        return 0
    except Problem as e:
        sys.exit(str(e))


if __name__ == "__main__":
    sys.exit(main())
