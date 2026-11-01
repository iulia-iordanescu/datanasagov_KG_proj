"""
second_opinion · Second, independent drafts of every finished record, matched against the ground truth.

Many ground truth triples were first drafted by a model (step 050) and corrected by a person; others were written by a
person. Whichever model drafted a record, the facts that model misses are the facts the person had to add alone, so
a second annotator from another source is the standard way to find what a single annotation misses (Tan et al.,
"Revisiting DocRED", EMNLP 2022: a re-annotation found the benchmark's labels incomplete). Here the
second annotator is another model: it drafts every FINISHED record again, exactly the way step 050 drafts (050's
prompt, the ground truth schema as 050 shows it, 050's parsing and checks), and each ground truth triple of the
record is matched against that fresh draft with step 070's pairing (exact and partial pairs; no translation, since
both use the ground truth schema). One draft is noisy (a model doesn't answer the same twice), so it drafts every
record in several runs (setting runs, 3 by default), each a repeat of the recipe (repeat 1, 2, ..., N: answers of
its own, cache keys of their own), and combines them: each ground truth triple found in k of the N runs; the draft's
facts the ground truth lacks, the union over the runs, each with the runs that proposed it. The ground truth is never
changed:

    py helpers/second_opinion.py                       draft every finished record in 3 runs (asks once before paying), match, report
    py helpers/second_opinion.py --apply true          the same, and record what was found in annotations/second_opinion.csv
    py helpers/second_opinion.py --runs <n>            another number of runs
    py helpers/second_opinion.py --ids <id>,<id>       only these finished records
    py helpers/second_opinion.py --model <name>        another model (the default: SECOND_OPINION_MODEL, below)

It runs in the frame every step runs in (common/common_helpers/step.py, run_step): its run id, log, report and
manifest (the model, its settings, the prompts' fingerprints), and the answers cached in its own output folder, so a
rerun with the same runs pays nothing. It writes no drafted batch, and nothing in annotations/ unless --apply true,
which writes only annotations/second_opinion.csv (common/common_helpers/second_opinion.py: for each ground truth
triple and model, in how many runs it was found). Step 070 then reports recall and partial F1 for the ground truth
triples found in at least one run and for those found in none, and how many were found in 0, 1, ..., N runs.

Held-out records are drafted too (so step 070 can group their triples), but the draft's facts the ground truth lacks
are listed, for review, for TUNING records only: reviewing a held-out record's would let it shape the ground truth
and the rules (annotations/guidelines.md, Before you start). For held-out records the report gives counts only.

Reads:   records.jsonl (020), splits.json (030), annotations/ground_truth_schema.txt, annotations/ground_truth/
Writes:  second_opinion_triples.csv (every run's draft, in a drafted batch's columns and the column run),
         second_opinion_matches.csv (each ground truth triple with the runs that found it; the draft's facts the
         ground truth lacks, tuning records only), second_opinion_details.json; with --apply true,
         annotations/second_opinion.csv
Details: helpers/second_opinion.md
"""
from __future__ import annotations

import collections
import importlib.util
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))                                                  # the repository folder, for common/

from common import audit, dropped, extraction, llm                            # noqa: E402
from common.audit import ORIGIN_COLUMN, check_origins, log                    # noqa: E402
from common.files import write_csv, write_json                                # noqa: E402
from common.ground_truth import DRAFTED_BY, EVALUABLE, HELD_OUT, TO_FIX, TUNING  # noqa: E402
from common.records_io import NOT_IN_CATALOG, WITHOUT_TEXT, WITHOUT_TEXT_TO_DO, has_text, read_ids  # noqa: E402
from common.report import cell, model_calls, named                            # noqa: E402
from common.second_opinion import FOUND, NOT_FOUND, PATH as TABLE_PATH, TRIPLE, counts, key_of, read_table, write_table  # noqa: E402
from common.step import Results, Spec, check_settings, load_moves, repo_path, run_step  # noqa: E402
from common.stop import Stop                                                   # noqa: E402
from common.triples_io import classed_key, is_describes                       # noqa: E402

#: The output folder's and the run id's name (outputs/intermediate_results/second_opinion/, second_opinion_<date>).
STEP = "second_opinion"
COMMAND, GUIDE = "py helpers/second_opinion.py", "helpers/second_opinion.md"
#: The default model: Google's flagship, gemini-4-argon (released 2026-09-30; usable through NASA's LiteLLM on
#: 2026-11-01; gemini-3.1-pro-preview is usable too). From another maker than 060's model (claude-opus-5-5), and a
#: later model than 050's (gemini-2.5-pro), so a fact missed by both of those still has a chance here. A setting
#: (--model), not fixed. Through LiteLLM, Gemini 4 is sent no temperature (its maker says it is ignored) and its
#: thinking level as `reasoning_effort` (common/common_helpers/llm.py, TEMPERATURE and THINKING).
SECOND_OPINION_MODEL = "gemini-4-argon"
#: The runs by default (decided on 2026-11-01; docs/improvements.md, section 050_annotate, says why 3): enough to
#: tell a triple the model finds every time from one it finds now and then, at three times one run's cost.
RUNS = 3

INPUTS = {
    "records":             "020_clean/records.jsonl",
    "splits":              "030_split/splits.json",
    "ground_truth_schema": "./annotations/ground_truth_schema.txt",
    "ground_truth":        "./annotations/ground_truth/batch_*.csv",
}

SETTINGS = {
    "ids":                "",    # only these finished records: ids separated by commas, or a file with one per line; empty: every finished record
    "max_chars":          8000,  # a longer text is split into text pieces, one call each (050's setting)
    "workers":            4,     # model calls made at the same time
    "service":            llm.SERVICE,  # the service that reaches the model: asksage or litellm
    "model":              SECOND_OPINION_MODEL,  # the model that gives the second opinion (py helpers/models.py lists them)
    "thinking":           "medium",  # how much a model that thinks may think: low, medium, high, or model_default (050's setting)
    "runs":               RUNS,  # how many runs draft each record: repeats 1, 2, ..., runs, each with answers of its own
    "confirm_paid_calls": True,  # stop and ask before the first model call; false for unattended runs
    "apply":              False,  # also write what was found into annotations/second_opinion.csv (the only write to annotations/)
}

#: This helper's own settings' rules (common.step.Spec); the shared ones come with check_settings.
SPECS = {"apply": Spec(bool), "runs": Spec(int, 1, 20)}

annotate = load_moves("050_annotate")                 # 050's moves: the records' inputs, its prompt, its parsing and checks
records_stage = sys.modules["records"]                # 050's records.py, loaded by its moves: read_inputs, items_for


def _load_pairing():
    """070's pairing.py by its path (its folder holds a records.py and a moves.py too, which 050's already occupy)."""
    path = ROOT / "070_evaluate" / "070_evaluate_helpers" / "pairing.py"
    spec = importlib.util.spec_from_file_location("pairing_070", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


pairing = _load_pairing()

DRAFT_NAME = "second_opinion_triples.csv"
MATCHES_NAME = "second_opinion_matches.csv"
DETAILS_NAME = "second_opinion_details.json"
#: second_opinion_matches.csv's statuses: a ground truth triple found in at least one run, found in none; a draft
#: triple that paired with no ground truth triple, in any run that proposed it.
FOUND_STATUS, NOT_FOUND_STATUS, DRAFT_ONLY = FOUND, NOT_FOUND, "draft only"
MATCH_COLUMNS = (["record_id", "position", "part", "status", "runs", "found_in_runs", "found_exact_in_runs",
                  "entity_classes_agree_in_runs", "proposed_in_runs"]
                 + [f"ground_truth_{c}" for c in TRIPLE] + [f"ground_truth_{DRAFTED_BY}"]
                 + [f"draft_{c}" for c in TRIPLE] + ["draft_source_text", "draft_run", ORIGIN_COLUMN])
NOT_FINISHED = "not finished in the ground truth (only finished records get a second opinion)"


@dataclass
class Matched:
    """One run's matching: {id: {"gt": [(row, level or None, entity classes agree)], "partners": [the draft triple
    paired with each, or None], "draft_only": [rows]}}, and the ids whose model call failed."""
    per_record: dict = field(default_factory=dict)
    not_drafted: list = field(default_factory=list)


@dataclass
class Run:
    """One run: its repeat (1, 2, ...), the model's replies, 050's rows from them, and their matching."""
    repeat: int
    replies: object
    drafts: object
    matched: Matched


@dataclass
class Combined:
    """The runs combined, per record drafted in at least one run: {id: {"runs": [the repeats that drafted it],
    "failed": [those that didn't], "gt": [{"triple", "found", "exact", "agree", "partner": (repeat, draft triple) or
    None}], "draft_only": [{"triple", "runs": [repeats that proposed it]}]}}; the rows of second_opinion_matches.csv."""
    runs: int
    per_record: dict = field(default_factory=dict)
    rows: list = field(default_factory=list)


# --------------------------------------------------------------------------

def pick_records(inputs: dict, settings: dict, output: Path):
    """Every finished record of the ground truth (EVALUABLE: every part), in pool order, records outside the pool last;
    with `ids`, those of them listed. Anything that differs from what was asked becomes a note shown before paying."""
    check_settings(settings, SPECS)
    chosen, _ = records_stage.read_inputs(inputs)
    gt = chosen.ground_truth
    finished = gt.select(EVALUABLE)
    ids = read_ids(settings["ids"])
    skipped = {NOT_IN_CATALOG: [], WITHOUT_TEXT: [], NOT_FINISHED: []}

    def usable(rid: str) -> bool:
        reason = (NOT_IN_CATALOG if rid not in chosen.records else
                  WITHOUT_TEXT if not has_text(chosen.records[rid]) else
                  NOT_FINISHED if rid not in finished.ids else None)
        if reason:
            skipped[reason].append(rid)
        return reason is None

    order = sorted(finished.ids, key=lambda r: (chosen.positions.get(r) is None, chosen.positions.get(r, 0), r))
    if ids:
        picked = [i for i in ids if usable(i)]
        chosen.how = f"the {len(ids)} id(s) given in the setting ids"
    else:
        picked = [i for i in order if usable(i)]
        chosen.how = "every finished record of the ground truth"
    chosen.skipped = {k: v for k, v in skipped.items() if v}
    to_do = {NOT_IN_CATALOG: f"Check these ids in the setting ids for typos: each must be a record id in "
                             f"{repo_path(inputs['records'])}.",
             WITHOUT_TEXT: WITHOUT_TEXT_TO_DO,
             NOT_FINISHED: "Finish them in `py helpers/annotate.py` (tick All facts extracted), then run this again; "
                           "a record that isn't in the ground truth at all is drafted by `py 050_annotate/run.py`."}
    for reason, rids in chosen.skipped.items():
        if ids or reason != WITHOUT_TEXT:
            chosen.notes.append(f"{len(rids)} record(s) {'you listed ' if ids else ''}{'are' if len(rids) > 1 else 'is'} "
                                f"{reason}, so skipped: {named(rids)}. {to_do[reason]}")
    chosen.items = records_stage.items_for(chosen, picked, settings["max_chars"])
    parts = collections.Counter(chosen.parts.get(r, "outside the pool") for r in picked)
    runs = settings["runs"]
    chosen.notes.append(f"This run drafts {len(picked)} finished record(s) again ("
                        + ", ".join(f"{n} {p}" for p, n in sorted(parts.items())) + f") with {settings['model']}, "
                        f"in {runs} run(s) (repeats 1 to {runs}), to match the drafts against the ground truth. It "
                        f"writes no drafted batch and changes nothing in annotations/"
                        + (" except annotations/second_opinion.csv (--apply true)." if settings["apply"] else "."))
    same = [r for r in finished.rows if r["id"] in set(picked) and r.get(DRAFTED_BY, "").strip().lower()
            == settings["model"].strip().lower()]
    if same:
        chosen.notes.append(f"{len(same)} ground truth triple(s) of these records were drafted by {settings['model']} "
                            f"itself (column {DRAFTED_BY}), so for them this isn't an independent second opinion. "
                            f"Nothing to do unless you want one: give another model with --model <name>.")
    if runs > 1 and str(settings["service"]).strip().lower() == "litellm" and not llm.answer_cache_bypassed():
        chosen.notes.append(f"The {runs} runs may get the same answers: {llm.ANSWER_CACHE_SWITCH}=1 isn't set in .env, so "
                            f"LiteLLM may answer a repeated request from its own cache, and then the runs are copies of "
                            f"one run. Set {llm.ANSWER_CACHE_SWITCH}=1 in .env (`py helpers/check_answer_cache.py` "
                            f"tells whether the proxy caches), then run this again.")
    unfinished = len(gt.select(TO_FIX).ids)
    if unfinished and not ids:
        chosen.notes.append(f"{unfinished} record(s) of the ground truth aren't finished, so they get no second opinion "
                            f"until they are (finish them in `py helpers/annotate.py`, then run this again).")
    if not chosen.items:
        raise Stop("Nothing to draft: no finished record can be drafted again, so no second opinion is made. "
                   + " ".join(chosen.notes))
    return chosen


def paid_calls(chosen, settings, output) -> llm.Calls:
    return llm.paid_calls(settings, output, notes=chosen.notes, command=COMMAND)


def draft_runs(chosen, calls, settings) -> list:
    """The runs, repeats 1 to `runs` (llm.REPEAT: each repeat's answers are its own, under cache keys of their own),
    each drafted with 050's prompt, parsing and checks, and matched. Asks once, before the first paid call of any run,
    for all of them: the plan counts runs × text pieces, less those already in the cache."""
    n = settings["runs"]
    prompt_for = annotate.draft.prompt_for(chosen)
    pieces = sum(len(i["pieces"]) for i in chosen.items)
    to_ask = []
    try:
        for r in range(1, n + 1):
            llm.REPEAT = r
            to_ask.append(extraction.pieces_to_ask(chosen.items, prompt_for, calls.cache_dir, annotate.draft.STAGE))
        if sum(to_ask):
            calls.paid.start(f"  the second opinion will draft {len(chosen.items)} finished record(s) again in {n} "
                             f"run(s): {n} run(s) × {pieces} text piece(s) = {n * pieces} model call(s), "
                             f"{n * pieces - sum(to_ask)} of them already in the cache, so {sum(to_ask)} to pay for ("
                             + ", ".join(f"run {r}: {k}" for r, k in enumerate(to_ask, 1)) + ")")
        runs = []
        for r in range(1, n + 1):
            llm.REPEAT = r
            log.info(f"  run {r} of {n} (repeat {r})")
            replies = annotate.ask_model(chosen, calls, settings,
                                         plan=f"the second opinion will draft {len(chosen.items)} finished record(s) "
                                              f"again, run {r} of {n}")
            drafts = annotate.build_rows(chosen, replies)
            runs.append(Run(r, replies, drafts, match(chosen, drafts)))
    finally:
        llm.REPEAT = 1                                   # the runs are this helper's; nothing after them is a repeat
    return runs


# --------------------------------------------------------------------------

def _ground_truth_triples(chosen) -> dict:
    """{id: [ground truth triples]} of the finished records: rows with subject, predicate and object, the describes
    triple left out (code writes it in both)."""
    out = {}
    for r in chosen.ground_truth.select(EVALUABLE).rows:
        if r["subject"] and r["predicate"] and r["object"] and not is_describes(r):
            out.setdefault(r["id"], []).append(r)
    return out


def match(chosen, drafts) -> Matched:
    """One run: each drafted record's ground truth triples paired with its fresh draft's classed triples (070's
    pairing, pairing.pair_triples: exact then partial, no translation): each ground truth triple found (exact or
    partial) or not; each draft triple left unpaired is a fact the ground truth lacks."""
    matched = Matched()
    gt_of = _ground_truth_triples(chosen)
    for item in chosen.items:
        rid = item["id"]
        if rid not in drafts.rows:
            matched.not_drafted.append(rid)
            continue
        gt = gt_of.get(rid, [])
        ex = [r for r in drafts.rows[rid] if not is_describes(r)]
        pairs = pairing.pair_triples(gt, ex)
        partner = {gi: (ei, level) for gi, ei, level in pairs}
        paired_e = {ei for _, ei, _ in pairs}
        entry = {"gt": [], "partners": [], "draft_only": [t for ei, t in enumerate(ex) if ei not in paired_e]}
        for gi, g in enumerate(gt):
            ei, level = partner.get(gi, (None, None))
            entry["gt"].append((g, level, pairing.classes_agree(g, ex[ei]) if ei is not None else None))
            entry["partners"].append(ex[ei] if ei is not None else None)
        matched.per_record[rid] = entry
    found = sum(1 for e in matched.per_record.values() for _, level, _ in e["gt"] if level)
    total = sum(len(e["gt"]) for e in matched.per_record.values())
    log.info(f"  {found} of {total} ground truth triple(s) found by this run in {len(matched.per_record)} record(s)")
    return matched


def combine(chosen, runs: list, n: int) -> Combined:
    """The runs combined, for each record drafted by at least one of them: each ground truth triple found in k of
    the runs that drafted it (exact or partial pair; and exactly; and with the entity classes agreeing), its partner
    taken from the first run that paired it exactly, else partially; the draft triples no ground truth triple paired
    with, the union over the runs (one classed triple as step 070's exact pairs compare it: triples_io.classed_key),
    each with the runs that proposed it (a run stating it twice counts once). Draft-only rows go to the matches file
    for tuning records only."""
    combined = Combined(runs=n)
    for item in chosen.items:
        rid = item["id"]
        done = [run for run in runs if rid in run.matched.per_record]
        if not done:
            continue
        part = chosen.parts.get(rid) or ""
        base = {"record_id": rid, "position": item["position"], "part": part, "runs": len(done),
                ORIGIN_COLUMN: audit.origin("records", rid)}
        gt_rows = [g for g, _, _ in done[0].matched.per_record[rid]["gt"]]
        entry = {"runs": [run.repeat for run in done], "failed": [run.repeat for run in runs if rid not in run.matched.per_record],
                 "gt": [], "draft_only": []}
        for gi, g in enumerate(gt_rows):
            seen = [(run.repeat, *run.matched.per_record[rid]["gt"][gi][1:], run.matched.per_record[rid]["partners"][gi])
                    for run in done]
            found = [s for s in seen if s[1]]
            exact = [s for s in found if s[1] == "exact"]
            best = (exact or found or [None])[0]
            e = {"triple": g, "found": len(found), "exact": len(exact), "agree": sum(1 for s in found if s[2]),
                 "partner": (best[0], best[3]) if best else None}
            entry["gt"].append(e)
            row = {**base, "status": FOUND_STATUS if found else NOT_FOUND_STATUS, "found_in_runs": e["found"],
                   "found_exact_in_runs": e["exact"], "entity_classes_agree_in_runs": e["agree"],
                   **{f"ground_truth_{c}": g[c] for c in TRIPLE}, f"ground_truth_{DRAFTED_BY}": g.get(DRAFTED_BY, "")}
            if best:
                row.update({f"draft_{c}": best[3][c] for c in TRIPLE}, draft_source_text=best[3]["source_text"],
                           draft_run=best[0])
            combined.rows.append(row)
        union = {}
        for run in done:
            for t in run.matched.per_record[rid]["draft_only"]:
                u = union.setdefault(classed_key(t), {"triple": t, "runs": [], "first_run": run.repeat})
                if run.repeat not in u["runs"]:
                    u["runs"].append(run.repeat)
        entry["draft_only"] = [{"triple": u["triple"], "runs": u["runs"], "first_run": u["first_run"]}
                               for u in union.values()]
        if part == TUNING:                               # a held-out record's are counted, never listed
            combined.rows += [{**base, "status": DRAFT_ONLY, "proposed_in_runs": len(u["runs"]),
                               **{f"draft_{c}": u["triple"][c] for c in TRIPLE},
                               "draft_source_text": u["triple"]["source_text"], "draft_run": u["first_run"]}
                              for u in entry["draft_only"]]
        combined.per_record[rid] = entry
    found = sum(1 for e in combined.per_record.values() for g in e["gt"] if g["found"])
    total = sum(len(e["gt"]) for e in combined.per_record.values())
    log.info(f"  {found} of {total} ground truth triple(s) found in at least one of the {n} run(s)")
    return combined


def apply(chosen, combined: Combined, settings: dict, path: Path = TABLE_PATH) -> dict | None:
    """With --apply true: annotations/second_opinion.csv gets, for every record drafted this run, one row per ground
    truth triple for this run's model, with its runs, found_in_runs and found_exact_in_runs (replacing that model's
    earlier row, keeping every other model's); rows of those records that match no ground truth triple any more are
    dropped; every other record's rows are kept as they are. Returns what was written, or None."""
    if not settings["apply"]:
        return None
    model = llm.MODEL
    table = read_table(path)
    drafted = set(combined.per_record)
    order = {k: i for i, k in enumerate(table)}
    kept = {k: r for k, r in table.items() if r["id"] not in drafted}
    dropped_rows = [r for k, r in table.items() if r["id"] in drafted]
    rebuilt = {}
    for rid, entry in combined.per_record.items():
        for g in entry["gt"]:
            k = key_of(rid, g["triple"])
            old = table.get(k) or {"id": rid, **{c: g["triple"][c] for c in TRIPLE}, "by": {}}
            by = {m: c for m, c in old["by"].items() if m != model}
            by[model] = counts(len(entry["runs"]), g["found"], g["exact"])
            rebuilt[k] = {**old, "by": by}
    dropped_rows = [r for r in dropped_rows if key_of(r["id"], r) not in rebuilt]
    rows = {**kept, **rebuilt}

    def place(k):                                        # pool position, then the file's order, then the triple
        row = rows[k]
        pos = chosen.positions.get(row["id"])
        return (pos is None, pos or 0, row["id"], order.get(k, len(order)), k)
    ordered = [rows[k] for k in sorted(rows, key=place)]
    write_table(path, ordered)
    lines = sum(len(r["by"]) for r in ordered)
    log.info(f"  wrote {repo_path(path)}: {lines} row(s), {len(rebuilt)} of them for {model} on the "
             f"{len(drafted)} record(s) drafted now")
    return {"path": repo_path(path), "rows": lines, "triples": len(ordered), "rebuilt": len(rebuilt),
            "dropped": len(dropped_rows), "kept_other_records": len(kept)}


# --------------------------------------------------------------------------

def _triple(t: dict) -> str:
    return f"{t['subject']} ({t['subject_class']}) {t['predicate']} {t['object']} ({t['object_class']})"


def _left_out(runs: list, items: list) -> list:
    """The records a model call failed for in at least one run, one entry each (dropped.left_out's, its why naming
    the runs)."""
    out = []
    for item in items:
        whys = [(run.repeat, e) for run in runs for e in dropped.left_out(run.replies, [item])]
        if whys:
            out.append({**whys[0][1], "why": "; ".join(f"run {r}: {e['why']}" for r, e in whys),
                        "runs": [r for r, _ in whys]})
    return out


def results(chosen, runs: list, combined: Combined, applied, calls, settings, output) -> Results:
    n = combined.runs
    draft_path, matches_path, details_path = output / DRAFT_NAME, output / MATCHES_NAME, output / DETAILS_NAME
    left_out = _left_out(runs, chosen.items)
    draft_rows = [{**{c: r.get(c, "") for c in annotate.GROUND_TRUTH_COLUMNS}, "all_facts_extracted": "0",
                   DRAFTED_BY: llm.MODEL, "flags": " ".join(r["errors"] + r["flags"]),
                   ORIGIN_COLUMN: audit.origin("records", item["id"]), "run": run.repeat}
                  for run in runs for item in chosen.items for r in run.drafts.rows.get(item["id"], [])]
    files = []
    if combined.per_record:
        write_csv(draft_path, annotate.COLUMNS + ["run"], draft_rows)
        write_csv(matches_path, MATCH_COLUMNS, combined.rows)
        per_record = []
        for item in chosen.items:
            e = combined.per_record.get(item["id"])
            gts = e["gt"] if e else []
            per_record.append({"id": item["id"], "pool_position": item["position"], "part": chosen.parts.get(item["id"]),
                               "title": item["title"], "pieces": len(item["pieces"]),
                               "runs_drafted": e["runs"] if e else [],
                               "runs_failed": e["failed"] if e else [run.repeat for run in runs],
                               "errors": {run.repeat: run.replies.failed[item["id"]] for run in runs
                                          if item["id"] in run.replies.failed},
                               "ground_truth_triples": len(gts),
                               "found_in_runs": ([sum(1 for g in gts if g["found"] == k) for k in range(len(e["runs"]) + 1)]
                                                 if e else None),     # ground truth triples found in 0, 1, ... runs
                               "found_in_at_least_one_run": sum(1 for g in gts if g["found"]),
                               "found_in_none": sum(1 for g in gts if not g["found"]),
                               "draft_only": len(e["draft_only"]) if e else None,
                               "removed": {run.repeat: run.drafts.removed.get(item["id"], []) for run in runs
                                           if run.drafts.removed.get(item["id"])}})
        made = {"run_id": audit.current_run_id(), **llm.describe(), "settings": settings}
        made.pop("repeat", None)
        made["repeats"] = [run.repeat for run in runs]
        write_json(details_path, {
            "made": made, "chosen": chosen.how, "runs": n, "records": per_record,
            "skipped_while_choosing": chosen.skipped, "left_out": dropped.details(left_out), "applied": applied,
        })
        files = [draft_path, matches_path, details_path]
        if applied:
            files.append(TABLE_PATH)
        log.info(f"  wrote {DRAFT_NAME}, {MATCHES_NAME} and {DETAILS_NAME}")

    warnings = list(chosen.notes)
    for run in runs:
        if run.replies.failed:
            warnings.append(f"Run {run.repeat} of {n}: " + extraction.failed_note(
                run.replies, f"run {run.repeat} of the second opinion (its other runs still count for it)"))
    if not combined.per_record:
        warnings.append(f"No record was drafted, so nothing was matched and nothing written: the model calls for all "
                        f"{len(chosen.items)} record(s) failed in every run (the warnings before this one say why). "
                        f"Fix the cause if it's yours, then run `py helpers/second_opinion.py` again.")
    coined = [name for kind in ("entity_classes", "predicates") for name in chosen.coined[kind]]
    if coined:
        warnings.append(f"{len(coined)} component class(es) used in the ground truth's finished tuning records aren't in "
                        f"the ground truth schema, so the model saw them without a definition: "
                        f"{named([f'{c} (coined in the ground truth)' for c in coined], 5, '; ')}. Add each one you mean "
                        f"to keep to annotations/ground_truth_schema.txt (`py helpers/annotate.py`).")
    missing = check_origins(combined.rows, "rows of the matches file")
    if missing:
        warnings.append(missing)

    # the counts
    by_part = collections.defaultdict(collections.Counter)
    by_drafter = collections.defaultdict(collections.Counter)
    spread = collections.Counter()                       # found in k of n runs, for records every run drafted
    fewer = 0                                            # ground truth triples of records some run failed for
    for rid, e in combined.per_record.items():
        part = chosen.parts.get(rid) or "outside the pool"
        for g in e["gt"]:
            drafter = g["triple"].get(DRAFTED_BY, "").strip() or "(a person: drafted_by empty)"
            for c in (by_part[part], by_drafter[drafter]):
                c["gt"] += 1
                c["found"] += bool(g["found"])
                c["exact"] += bool(g["exact"])
                c["every"] += g["found"] == len(e["runs"])
            if len(e["runs"]) == n:
                spread[g["found"]] += 1
            else:
                fewer += 1
    draft_only = {TUNING: 0, HELD_OUT: 0, "outside the pool": 0}
    for rid, e in combined.per_record.items():
        draft_only[chosen.parts.get(rid) or "outside the pool"] += len(e["draft_only"])
    total = collections.Counter()
    for c in by_part.values():
        total.update(c)

    def share(k: int, of: int) -> str:
        return f"{k} of {of}" + (f" ({100 * k / of:.0f}%)" if of else "")

    lines = ["### What this run worked on", "",
             f"{len(combined.per_record)} finished record(s) drafted again by `{llm.MODEL}` ({chosen.how}) in {n} "
             f"run(s), each a repeat with answers of its own (repeats 1 to {n}), with step 050's prompt, schema view, "
             f"parsing and checks; each run's draft matched against the record's ground truth triples with step 070's "
             f"pairing (exact, then partial; no translation: both use the ground truth schema; no partial pair review "
             f"applies). A ground truth triple is *found* when at least one run paired it, *found in none* otherwise. "
             f"The ground truth is unchanged.", "",
             "| Pool position | Part | Record | Runs that drafted it | Ground truth triples | Found in at least one run "
             "| Found in every run | Found in none | Draft only (over the runs) |",
             "|---:|---|---|---:|---:|---:|---:|---:|---:|"]
    for item in chosen.items:
        e = combined.per_record.get(item["id"])
        pos = item["position"] if item["position"] is not None else "–"
        if e is None:
            lines.append(f"| {pos} | {chosen.parts.get(item['id']) or '–'} | {cell(item['title'])} | 0 of {n} "
                         f"(failed) | | | | | |")
            continue
        g = e["gt"]
        lines.append(f"| {pos} | {chosen.parts.get(item['id']) or '–'} | {cell(item['title'])} | {len(e['runs'])} of {n} | "
                     f"{len(g)} | {sum(1 for x in g if x['found'])} | {sum(1 for x in g if x['found'] == len(e['runs']))} | "
                     f"{sum(1 for x in g if not x['found'])} | {len(e['draft_only'])} |")
    lines += ["", "### Found by the second opinion", "",
              f"Ground truth triples a fresh draft also stated (an exact or partial pair) in at least one run: "
              f"**{share(total['found'], total['gt'])}**; in every run that drafted the record: {total['every']}; "
              f"exactly in at least one run: {total['exact']}; found in none: {total['gt'] - total['found']}. A ground "
              f"truth triple found in none was stated by one annotator only: a fact the second model misses, or one "
              f"the ground truth's rules state and the drafts don't; it is not thereby wrong.", "",
              "| Group | Ground truth triples | Found in at least one run | Found exactly in at least one run | "
              "Found in every run | Found in none |", "|---|---:|---|---:|---:|---:|"]
    for part in (TUNING, HELD_OUT, "outside the pool"):
        if part in by_part:
            c = by_part[part]
            lines.append(f"| {part} part | {c['gt']} | {share(c['found'], c['gt'])} | {c['exact']} | {c['every']} | "
                         f"{c['gt'] - c['found']} |")
    for drafter, c in sorted(by_drafter.items()):
        lines.append(f"| drafted by {cell(drafter)} | {c['gt']} | {share(c['found'], c['gt'])} | {c['exact']} | "
                     f"{c['every']} | {c['gt'] - c['found']} |")
    lines += ["", f"The rows *drafted by* split the ground truth triples by their `{DRAFTED_BY}` column: a row a model "
                  f"drafted and a person corrected, or a row a person wrote (empty). Every ground truth triple of every "
                  f"drafted record is in `{repo_path(matches_path)}` (columns `status`, `found_in_runs`), one row each.", ""]
    if combined.per_record:
        lines += [f"How many of the {n} run(s) found each ground truth triple (records every run drafted"
                  + (f"; the {fewer} triple(s) of records some run failed for are left out here" if fewer else "")
                  + "): a triple found in some runs and not others is one the model states on some answers only.", "",
                  "| Found in | " + " | ".join(f"{k} of {n}" for k in range(n + 1)) + " |",
                  "|---|" + "---:|" * (n + 1),
                  "| Ground truth triples | " + " | ".join(str(spread[k]) for k in range(n + 1)) + " |", ""]
    lines += ["### The second opinion's facts the ground truth lacks (tuning records)", "",
              f"Classed triples of the fresh drafts that pair with no ground truth triple, the union over the runs (one "
              f"classed triple once, however many runs proposed it; each with the number of runs that did): "
              f"{draft_only[TUNING]} in the tuning records, listed below with the record and the draft's source text, "
              f"for review (a fact the ground truth missed, a fact its rules leave out on purpose, or a wrong one). "
              + (f"The {draft_only[HELD_OUT]} of the held-out records are counted here and nowhere else: they are not "
                 f"listed, in this report or in `{MATCHES_NAME}`, since reviewing them would let the held-out records "
                 f"shape the ground truth and its rules (annotations/guidelines.md, Before you start)."
                 if HELD_OUT in by_part else "")
              + (f" Records outside the pool: {draft_only['outside the pool']}." if draft_only["outside the pool"] else ""), ""]
    for item in chosen.items:
        e = combined.per_record.get(item["id"])
        if not e or chosen.parts.get(item["id"]) != TUNING or not e["draft_only"]:
            continue
        lines += [f"**{item['title']}** (pool position {item['position']}, `{item['id']}`)", ""]
        lines += [f"- {_triple(u['triple'])}, in {len(u['runs'])} of {len(e['runs'])} run(s) — source text: "
                  f"{cell(u['triple']['source_text']) or '(none)'}"
                  for u in sorted(e["draft_only"], key=lambda u: -len(u["runs"]))]
        lines.append("")
    lines += ["### Provenance recorded", ""]
    if applied:
        lines += [f"`{applied['path']}` now has {applied['rows']} row(s) for {applied['triples']} ground truth triple(s): "
                  f"{applied['rebuilt']} rewritten for `{llm.MODEL}` on the {len(combined.per_record)} record(s) drafted "
                  f"now (`runs`, `found_in_runs`, `found_exact_in_runs`), other models' rows kept, {applied['dropped']} "
                  f"triple(s) dropped (their classed triple is no longer in the ground truth), "
                  f"{applied['kept_other_records']} of other records kept as they were. Commit it. Step 070 now reports "
                  f"recall by the group found in at least one run / found in none / not checked.", ""]
    else:
        lines += ["Nothing written to `annotations/`. To record which ground truth triples this second opinion found "
                  "(`annotations/second_opinion.csv`, read by step 070), run `py helpers/second_opinion.py --apply "
                  "true` with the same runs: it pays nothing for the answers already cached.", ""]
    lines += dropped.section(left_out, chosen.items, "at least one run (each record is matched on the runs that "
                             "drafted it)", repo_path(details_path) if files else None)
    lines += dropped.reasks_lines(llm.REASKS)
    lines += model_calls([(f"draft classed triples, run {run.repeat} of {n} (one call per text piece; step 050's "
                           f"prompt)", run.replies.calls, run.replies.reused) for run in runs],
                         calls.paid.test_calls, llm.model_label())
    headline = {"records drafted again": len(combined.per_record), "runs": n, "ground truth triples": total["gt"],
                "found in at least one run": total["found"], "found in every run": total["every"],
                "draft's facts the ground truth lacks (tuning, over the runs)": draft_only[TUNING],
                **dropped.reasks_headline(llm.REASKS)}
    return Results(files=files, headline=headline, details="\n".join(lines), warnings=warnings)


def main(inputs, settings, output):
    chosen   = pick_records(inputs, settings, output)   # code: every finished record (or the ids given), 050's view of the schema
    calls    = paid_calls(chosen, settings, output)     # code: asks once before paying, for every run; keeps every answer in cache/
    runs     = draft_runs(chosen, calls, settings)      # LLM + code: each run's facts with 050's prompt, parsing and checks; 070's pairing
    combined = combine(chosen, runs, settings["runs"])  # code: each ground truth triple found in k of the runs; the draft-only union
    applied  = apply(chosen, combined, settings)        # code: annotations/second_opinion.csv, only with --apply true
    return results(chosen, runs, combined, applied, calls, settings, output)


if __name__ == "__main__":
    run_step(STEP, INPUTS, SETTINGS, main, specs=SPECS, command=COMMAND, guide=GUIDE)
