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
record several times (setting repeats, 3 by default), each a repeat of the recipe (repeat 1, 2, ..., N: answers of
its own, cache keys of their own), and combines them: each ground truth triple found in k of the N repeats; the draft's
facts the ground truth lacks, the union over the repeats, each with the repeats that proposed it. The ground truth is never
changed:

    py helpers/second_opinion.py                       draft every finished record in 3 repeats (asks once before paying), match, report
    py helpers/second_opinion.py --apply true          the same, and record what was found in annotations/second_opinion.csv
    py helpers/second_opinion.py --repeats <n>         another number of repeats
    py helpers/second_opinion.py --ids <id>,<id>       only these finished records
    py helpers/second_opinion.py --model <name>        another model (the default: SECOND_OPINION_MODEL, below)

It runs in the frame every step runs in (common/common_helpers/step.py, run_step): its run id, log, report and
manifest (the model, its settings, the prompts' fingerprints), and the answers cached in its own output folder, so a
rerun with the same repeats pays nothing. It writes no drafted batch, and nothing in annotations/ unless --apply true,
which writes only annotations/second_opinion.csv (common/common_helpers/second_opinion.py: for each ground truth
triple and model, in how many repeats it was found) and annotations/second_opinion_candidates.csv (the draft's facts
the ground truth lacks, tuning records only, each with an empty column decision for the reviewer; a rerun keeps
every decision already filled). Step 070 then reports recall and partial F1 for the ground truth
triples found in at least one repeat and for those found in none, and how many were found in 0, 1, ..., N repeats.

Held-out records are drafted too (so step 070 can group their triples), but the draft's facts the ground truth lacks
are listed, for review, for TUNING records only: reviewing a held-out record's would let it shape the ground truth
and the rules (annotations/guidelines.md, Before you start). For held-out records the report gives counts only.

Reads:   records.jsonl (020), splits.json (030), annotations/ground_truth_schema.txt, annotations/ground_truth/
Writes:  second_opinion_triples.csv (every repeat's draft, in a drafted batch's columns and the column repeat),
         second_opinion_matches.csv (each ground truth triple with the repeats that found it; the draft's facts the
         ground truth lacks, tuning records only), second_opinion_details.json; with --apply true,
         annotations/second_opinion.csv and annotations/second_opinion_candidates.csv
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
from common.second_opinion import (CANDIDATES_PATH, FOUND, NOT_FOUND, PATH as TABLE_PATH, TRIPLE, candidate_key,  # noqa: E402
                                   candidates_path_for, counts, key_of, read_candidates, read_table, write_candidates, write_table)
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
#: The repeats by default (decided on 2026-11-01; docs/improvements.md, section 050_annotate, says why 3): enough to
#: tell a triple the model finds every time from one it finds now and then, at three times the cost of one.
REPEATS = 3

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
    "repeats":            REPEATS,  # how many times each record is drafted: repeats 1, 2, ..., N, each with answers of its own
    "confirm_paid_calls": True,  # stop and ask before the first model call; false for unattended runs
    "apply":              False,  # also write annotations/second_opinion.csv and second_opinion_candidates.csv (the only writes to annotations/)
}

#: This helper's own settings' rules (common.step.Spec); the shared ones come with check_settings.
SPECS = {"apply": Spec(bool), "repeats": Spec(int, 1, 20)}

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
#: second_opinion_matches.csv's statuses: a ground truth triple found in at least one repeat, found in none; a draft
#: triple that paired with no ground truth triple, in any repeat that proposed it.
FOUND_STATUS, NOT_FOUND_STATUS, DRAFT_ONLY = FOUND, NOT_FOUND, "draft only"
MATCH_COLUMNS = (["record_id", "position", "part", "status", "repeats", "found_in_repeats", "found_exact_in_repeats",
                  "entity_classes_agree_in_repeats", "proposed_in_repeats"]
                 + [f"ground_truth_{c}" for c in TRIPLE] + [f"ground_truth_{DRAFTED_BY}"]
                 + [f"draft_{c}" for c in TRIPLE] + ["draft_source_text", "draft_repeat", ORIGIN_COLUMN])
NOT_FINISHED = "not finished in the ground truth (only finished records get a second opinion)"


@dataclass
class Matched:
    """One repeat's matching: {id: {"gt": [(row, level or None, entity classes agree)], "partners": [the draft triple
    paired with each, or None], "draft_only": [rows]}}, and the ids whose model call failed."""
    per_record: dict = field(default_factory=dict)
    not_drafted: list = field(default_factory=list)


@dataclass
class Repeat:
    """One repeat: its number (1, 2, ...), the model's replies, 050's rows from them, and their matching."""
    number: int
    replies: object
    drafts: object
    matched: Matched


@dataclass
class Combined:
    """The repeats combined, per record drafted in at least one repeat: {id: {"repeats": [the repeats that drafted it],
    "failed": [those that didn't], "gt": [{"triple", "found", "exact", "agree", "partner": (repeat, draft triple) or
    None}], "draft_only": [{"triple", "repeats": [repeats that proposed it]}]}}; the rows of second_opinion_matches.csv."""
    repeats: int
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
    repeats = settings["repeats"]
    chosen.notes.append(f"This run drafts {len(picked)} finished record(s) again ("
                        + ", ".join(f"{n} {p}" for p, n in sorted(parts.items())) + f") with {settings['model']}, "
                        f"in {repeats} repeat(s) (repeats 1 to {repeats}), to match the drafts against the ground truth. It "
                        f"writes no drafted batch and changes nothing in annotations/"
                        + (" except annotations/second_opinion.csv and annotations/second_opinion_candidates.csv "
                           "(--apply true)." if settings["apply"] else "."))
    if settings["apply"]:
        try:                                             # a mistake in the files stops here, before any paid call
            read_table(TABLE_PATH)
            read_candidates(CANDIDATES_PATH)
        except ValueError as e:
            raise Stop(f"{e}. --apply true rewrites this file, so fix it first, then run this again.") from None
    same = [r for r in finished.rows if r["id"] in set(picked) and r.get(DRAFTED_BY, "").strip().lower()
            == settings["model"].strip().lower()]
    if same:
        chosen.notes.append(f"{len(same)} ground truth triple(s) of these records were drafted by {settings['model']} "
                            f"itself (column {DRAFTED_BY}), so for them this isn't an independent second opinion. "
                            f"Nothing to do unless you want one: give another model with --model <name>.")
    if repeats > 1 and str(settings["service"]).strip().lower() == "litellm" and not llm.answer_cache_bypassed():
        chosen.notes.append(f"The {repeats} repeats may get the same answers: {llm.ANSWER_CACHE_SWITCH}=1 isn't set in .env, so "
                            f"LiteLLM may answer a repeated request from its own cache, and then the repeats are copies of "
                            f"one repeat. Set {llm.ANSWER_CACHE_SWITCH}=1 in .env (`py helpers/check_answer_cache.py` "
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


def draft_repeats(chosen, calls, settings) -> list:
    """Repeats 1 to `repeats` (llm.REPEAT: each repeat's answers are its own, under cache keys of their own),
    each drafted with 050's prompt, parsing and checks, and matched. Asks once, before the first paid call of any repeat,
    for all of them: the plan counts repeats × text pieces, less those already in the cache."""
    n = settings["repeats"]
    prompt_for = annotate.draft.prompt_for(chosen)
    pieces = sum(len(i["pieces"]) for i in chosen.items)
    to_ask = []
    try:
        for r in range(1, n + 1):
            llm.REPEAT = r
            to_ask.append(extraction.pieces_to_ask(chosen.items, prompt_for, calls.cache_dir, annotate.draft.STAGE))
        if sum(to_ask):
            calls.paid.start(f"  the second opinion will draft {len(chosen.items)} finished record(s) again in {n} "
                             f"repeat(s): {n} repeat(s) × {pieces} text piece(s) = {n * pieces} model call(s), "
                             f"{n * pieces - sum(to_ask)} of them already in the cache, so {sum(to_ask)} to pay for ("
                             + ", ".join(f"repeat {r}: {k}" for r, k in enumerate(to_ask, 1)) + ")")
        repeats = []
        for r in range(1, n + 1):
            llm.REPEAT = r
            log.info(f"  repeat {r} of {n}")
            replies = annotate.ask_model(chosen, calls, settings,
                                         plan=f"the second opinion will draft {len(chosen.items)} finished record(s) "
                                              f"again, repeat {r} of {n}")
            drafts = annotate.build_rows(chosen, replies)
            repeats.append(Repeat(r, replies, drafts, match(chosen, drafts)))
    finally:
        llm.REPEAT = 1                                   # the repeats are this helper's; nothing after them is a repeat
    return repeats


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
    """One repeat: each drafted record's ground truth triples paired with its fresh draft's classed triples (070's
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
    log.info(f"  {found} of {total} ground truth triple(s) found by this repeat in {len(matched.per_record)} record(s)")
    return matched


def combine(chosen, repeats: list, n: int) -> Combined:
    """The repeats combined, for each record drafted by at least one of them: each ground truth triple found in k of
    the repeats that drafted it (exact or partial pair; and exactly; and with the entity classes agreeing), its partner
    taken from the first repeat that paired it exactly, else partially; the draft triples no ground truth triple paired
    with, the union over the repeats (one classed triple as step 070's exact pairs compare it: triples_io.classed_key),
    each with the repeats that proposed it (a repeat stating it twice counts once). Draft-only rows go to the matches file
    for tuning records only."""
    combined = Combined(repeats=n)
    for item in chosen.items:
        rid = item["id"]
        done = [repeat for repeat in repeats if rid in repeat.matched.per_record]
        if not done:
            continue
        part = chosen.parts.get(rid) or ""
        base = {"record_id": rid, "position": item["position"], "part": part, "repeats": len(done),
                ORIGIN_COLUMN: audit.origin("records", rid)}
        gt_rows = [g for g, _, _ in done[0].matched.per_record[rid]["gt"]]
        entry = {"repeats": [repeat.number for repeat in done], "failed": [repeat.number for repeat in repeats if rid not in repeat.matched.per_record],
                 "gt": [], "draft_only": []}
        for gi, g in enumerate(gt_rows):
            seen = [(repeat.number, *repeat.matched.per_record[rid]["gt"][gi][1:], repeat.matched.per_record[rid]["partners"][gi])
                    for repeat in done]
            found = [s for s in seen if s[1]]
            exact = [s for s in found if s[1] == "exact"]
            best = (exact or found or [None])[0]
            e = {"triple": g, "found": len(found), "exact": len(exact), "agree": sum(1 for s in found if s[2]),
                 "partner": (best[0], best[3]) if best else None}
            entry["gt"].append(e)
            row = {**base, "status": FOUND_STATUS if found else NOT_FOUND_STATUS, "found_in_repeats": e["found"],
                   "found_exact_in_repeats": e["exact"], "entity_classes_agree_in_repeats": e["agree"],
                   **{f"ground_truth_{c}": g[c] for c in TRIPLE}, f"ground_truth_{DRAFTED_BY}": g.get(DRAFTED_BY, "")}
            if best:
                row.update({f"draft_{c}": best[3][c] for c in TRIPLE}, draft_source_text=best[3]["source_text"],
                           draft_repeat=best[0])
            combined.rows.append(row)
        union = {}
        for repeat in done:
            for t in repeat.matched.per_record[rid]["draft_only"]:
                u = union.setdefault(classed_key(t), {"triple": t, "repeats": [], "first_repeat": repeat.number})
                if repeat.number not in u["repeats"]:
                    u["repeats"].append(repeat.number)
        entry["draft_only"] = [{"triple": u["triple"], "repeats": u["repeats"], "first_repeat": u["first_repeat"]}
                               for u in union.values()]
        if part == TUNING:                               # a held-out record's are counted, never listed
            combined.rows += [{**base, "status": DRAFT_ONLY, "proposed_in_repeats": len(u["repeats"]),
                               **{f"draft_{c}": u["triple"][c] for c in TRIPLE},
                               "draft_source_text": u["triple"]["source_text"], "draft_repeat": u["first_repeat"]}
                              for u in entry["draft_only"]]
        combined.per_record[rid] = entry
    found = sum(1 for e in combined.per_record.values() for g in e["gt"] if g["found"])
    total = sum(len(e["gt"]) for e in combined.per_record.values())
    log.info(f"  {found} of {total} ground truth triple(s) found in at least one of the {n} repeat(s)")
    return combined


def apply(chosen, combined: Combined, settings: dict, path: Path = TABLE_PATH) -> dict | None:
    """With --apply true: annotations/second_opinion.csv gets, for every record drafted this run, one row per ground
    truth triple for this run's model, with its repeats, found_in_repeats and found_exact_in_repeats (replacing that model's
    earlier row, keeping every other model's); rows of those records that match no ground truth triple any more are
    dropped; every other record's rows are kept as they are. Then the draft's facts the ground truth lacks go to the
    candidates file beside it, annotations/second_opinion_candidates.csv (apply_candidates). Returns what was written,
    or None."""
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
            by[model] = counts(len(entry["repeats"]), g["found"], g["exact"])
            rebuilt[k] = {**old, "by": by}
    dropped_rows = [r for r in dropped_rows if key_of(r["id"], r) not in rebuilt]
    rows = {**kept, **rebuilt}

    def place(k):                                        # pool position, then the file's order, then the triple
        row = rows[k]
        pos = chosen.positions.get(row["id"])
        return (pos is None, pos or 0, row["id"], order.get(k, len(order)), k)
    ordered = [rows[k] for k in sorted(rows, key=place)]
    candidates = read_candidates(candidates_path_for(path))    # read before writing anything: a mistake stops both
    write_table(path, ordered)
    lines = sum(len(r["by"]) for r in ordered)
    log.info(f"  wrote {repo_path(path)}: {lines} row(s), {len(rebuilt)} of them for {model} on the "
             f"{len(drafted)} record(s) drafted now")
    return {"path": repo_path(path), "rows": lines, "triples": len(ordered), "rebuilt": len(rebuilt),
            "dropped": len(dropped_rows), "kept_other_records": len(kept),
            "candidates": apply_candidates(chosen, combined, model, candidates, candidates_path_for(path))}


def apply_candidates(chosen, combined: Combined, model: str, old: list, path: Path) -> dict:
    """annotations/second_opinion_candidates.csv (old: its rows as read): for every TUNING record drafted this run,
    this model's rows are replaced by its draft-only classed triples (the union over the repeats), each with the
    decision already filled for the same record and classed triple (by any model), else an empty one; a row of this
    model on those records with a decision filled whose classed triple this run no longer proposes is kept as it was,
    so that no decision is lost; every other model's rows, and every other record's, are kept. A held-out record's
    draft-only triples are never written (counted only), and a row of a record now in the held-out part is dropped.
    Rows are ordered by pool position, then the file's order. Returns what was written."""
    drafted = set(combined.per_record)
    held_out = {rid for rid, part in chosen.parts.items() if part == HELD_OUT}
    decisions = {candidate_key(r): r["decision"] for r in old if r["decision"]}
    titles = {item["id"]: item["title"] for item in chosen.items}
    new = []
    for item in chosen.items:
        rid, e = item["id"], combined.per_record.get(item["id"])
        if e is None or chosen.parts.get(rid) != TUNING:
            continue
        for u in sorted(e["draft_only"], key=lambda u: -len(u["repeats"])):
            t = u["triple"]
            row = {"id": rid, "title": titles.get(rid, ""), **{c: t[c] for c in TRIPLE}, "source_text": t["source_text"],
                   "model": model, "proposed_in_repeats": len(u["repeats"]), "repeats": len(e["repeats"])}
            row["decision"] = decisions.get(candidate_key(row), "")
            new.append(row)
    proposed = {candidate_key(r) for r in new}
    kept, kept_decided, dropped_held_out = [], 0, 0
    for r in old:
        if r["id"] in held_out:
            dropped_held_out += 1
        elif r["model"] == model and r["id"] in drafted:
            if r["decision"] and candidate_key(r) not in proposed:
                kept.append(r)
                kept_decided += 1
        else:
            kept.append(r)
    rows = kept + new

    def place(i):                                        # pool position, then the file's order, then this run's
        pos = chosen.positions.get(rows[i]["id"])
        return (pos is None, pos or 0, rows[i]["id"], i)
    ordered = [rows[i] for i in sorted(range(len(rows)), key=place)]
    write_candidates(path, ordered)
    held_out_count = sum(len(e["draft_only"]) for rid, e in combined.per_record.items() if rid in held_out)
    log.info(f"  wrote {repo_path(path)}: {len(ordered)} row(s), {len(new)} of them for {model} on the tuning "
             f"record(s) drafted now, {sum(1 for r in new if r['decision'])} with a decision kept")
    return {"path": repo_path(path), "rows": len(ordered), "written": len(new),
            "decisions_kept": sum(1 for r in new if r["decision"]), "kept_decided": kept_decided,
            "undecided": sum(1 for r in ordered if not r["decision"]), "held_out_not_written": held_out_count,
            "dropped_held_out": dropped_held_out}


# --------------------------------------------------------------------------

def _triple(t: dict) -> str:
    return f"{t['subject']} ({t['subject_class']}) {t['predicate']} {t['object']} ({t['object_class']})"


def _left_out(repeats: list, items: list) -> list:
    """The records a model call failed for in at least one repeat, one entry each (dropped.left_out's, its why naming
    the repeats)."""
    out = []
    for item in items:
        whys = [(repeat.number, e) for repeat in repeats for e in dropped.left_out(repeat.replies, [item])]
        if whys:
            out.append({**whys[0][1], "why": "; ".join(f"repeat {r}: {e['why']}" for r, e in whys),
                        "repeats": [r for r, _ in whys]})
    return out


def results(chosen, repeats: list, combined: Combined, applied, calls, settings, output) -> Results:
    n = combined.repeats
    draft_path, matches_path, details_path = output / DRAFT_NAME, output / MATCHES_NAME, output / DETAILS_NAME
    left_out = _left_out(repeats, chosen.items)
    draft_rows = [{**{c: r.get(c, "") for c in annotate.GROUND_TRUTH_COLUMNS}, "all_facts_extracted": "0",
                   DRAFTED_BY: llm.MODEL, "flags": " ".join(r["errors"] + r["flags"]),
                   ORIGIN_COLUMN: audit.origin("records", item["id"]), "repeat": repeat.number}
                  for repeat in repeats for item in chosen.items for r in repeat.drafts.rows.get(item["id"], [])]
    files = []
    if combined.per_record:
        write_csv(draft_path, annotate.COLUMNS + ["repeat"], draft_rows)
        write_csv(matches_path, MATCH_COLUMNS, combined.rows)
        per_record = []
        for item in chosen.items:
            e = combined.per_record.get(item["id"])
            gts = e["gt"] if e else []
            per_record.append({"id": item["id"], "pool_position": item["position"], "part": chosen.parts.get(item["id"]),
                               "title": item["title"], "pieces": len(item["pieces"]),
                               "repeats_drafted": e["repeats"] if e else [],
                               "repeats_failed": e["failed"] if e else [repeat.number for repeat in repeats],
                               "errors": {repeat.number: repeat.replies.failed[item["id"]] for repeat in repeats
                                          if item["id"] in repeat.replies.failed},
                               "ground_truth_triples": len(gts),
                               "found_in_repeats": ([sum(1 for g in gts if g["found"] == k) for k in range(len(e["repeats"]) + 1)]
                                                 if e else None),     # ground truth triples found in 0, 1, ... repeats
                               "found_in_at_least_one_repeat": sum(1 for g in gts if g["found"]),
                               "found_in_none": sum(1 for g in gts if not g["found"]),
                               "draft_only": len(e["draft_only"]) if e else None,
                               "removed": {repeat.number: repeat.drafts.removed.get(item["id"], []) for repeat in repeats
                                           if repeat.drafts.removed.get(item["id"])}})
        made = {"run_id": audit.current_run_id(), **llm.describe(), "settings": settings}
        made.pop("repeat", None)
        made["repeats"] = [repeat.number for repeat in repeats]
        write_json(details_path, {
            "made": made, "chosen": chosen.how, "repeats": n, "records": per_record,
            "skipped_while_choosing": chosen.skipped, "left_out": dropped.details(left_out), "applied": applied,
        })
        files = [draft_path, matches_path, details_path]
        if applied:
            files += [TABLE_PATH, CANDIDATES_PATH]
        log.info(f"  wrote {DRAFT_NAME}, {MATCHES_NAME} and {DETAILS_NAME}")

    warnings = list(chosen.notes)
    for repeat in repeats:
        if repeat.replies.failed:
            warnings.append(f"Repeat {repeat.number} of {n}: " + extraction.failed_note(
                repeat.replies, f"repeat {repeat.number} of the second opinion (its other repeats still count for it)"))
    if not combined.per_record:
        warnings.append(f"No record was drafted, so nothing was matched and nothing written: the model calls for all "
                        f"{len(chosen.items)} record(s) failed in every repeat (the warnings before this one say why). "
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
    spread = collections.Counter()                       # found in k of n repeats, for records every repeat drafted
    fewer = 0                                            # ground truth triples of records some repeat failed for
    for rid, e in combined.per_record.items():
        part = chosen.parts.get(rid) or "outside the pool"
        for g in e["gt"]:
            drafter = g["triple"].get(DRAFTED_BY, "").strip() or "(a person: drafted_by empty)"
            for c in (by_part[part], by_drafter[drafter]):
                c["gt"] += 1
                c["found"] += bool(g["found"])
                c["exact"] += bool(g["exact"])
                c["every"] += g["found"] == len(e["repeats"])
            if len(e["repeats"]) == n:
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
             f"repeat(s), each with answers of its own (repeats 1 to {n}), with step 050's prompt, schema view, "
             f"parsing and checks; each repeat's draft matched against the record's ground truth triples with step 070's "
             f"pairing (exact, then partial; no translation: both use the ground truth schema; no partial pair review "
             f"applies). A ground truth triple is *found* when at least one repeat paired it, *found in none* otherwise. "
             f"The ground truth is unchanged.", "",
             "| Pool position | Part | Record | Repeats that drafted it | Ground truth triples | Found in at least one repeat "
             "| Found in every repeat | Found in none | Draft only (over the repeats) |",
             "|---:|---|---|---:|---:|---:|---:|---:|---:|"]
    for item in chosen.items:
        e = combined.per_record.get(item["id"])
        pos = item["position"] if item["position"] is not None else "–"
        if e is None:
            lines.append(f"| {pos} | {chosen.parts.get(item['id']) or '–'} | {cell(item['title'])} | 0 of {n} "
                         f"(failed) | | | | | |")
            continue
        g = e["gt"]
        lines.append(f"| {pos} | {chosen.parts.get(item['id']) or '–'} | {cell(item['title'])} | {len(e['repeats'])} of {n} | "
                     f"{len(g)} | {sum(1 for x in g if x['found'])} | {sum(1 for x in g if x['found'] == len(e['repeats']))} | "
                     f"{sum(1 for x in g if not x['found'])} | {len(e['draft_only'])} |")
    lines += ["", "### Found by the second opinion", "",
              f"Ground truth triples a fresh draft also stated (an exact or partial pair) in at least one repeat: "
              f"**{share(total['found'], total['gt'])}**; in every repeat that drafted the record: {total['every']}; "
              f"exactly in at least one repeat: {total['exact']}; found in none: {total['gt'] - total['found']}. A ground "
              f"truth triple found in none was stated by one annotator only: a fact the second model misses, or one "
              f"the ground truth's rules state and the drafts don't; it is not thereby wrong.", "",
              "| Group | Ground truth triples | Found in at least one repeat | Found exactly in at least one repeat | "
              "Found in every repeat | Found in none |", "|---|---:|---|---:|---:|---:|"]
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
                  f"drafted record is in `{repo_path(matches_path)}` (columns `status`, `found_in_repeats`), one row each.", ""]
    if combined.per_record:
        lines += [f"How many of the {n} repeat(s) found each ground truth triple (records every repeat drafted"
                  + (f"; the {fewer} triple(s) of records some repeat failed for are left out here" if fewer else "")
                  + "): a triple found in some repeats and not others is one the model states on some answers only.", "",
                  "| Found in | " + " | ".join(f"{k} of {n}" for k in range(n + 1)) + " |",
                  "|---|" + "---:|" * (n + 1),
                  "| Ground truth triples | " + " | ".join(str(spread[k]) for k in range(n + 1)) + " |", ""]
    lines += ["### The second opinion's facts the ground truth lacks (tuning records)", "",
              f"Classed triples of the fresh drafts that pair with no ground truth triple, the union over the repeats (one "
              f"classed triple once, however many repeats proposed it; each with the number of repeats that did): "
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
        lines += [f"- {_triple(u['triple'])}, in {len(u['repeats'])} of {len(e['repeats'])} repeat(s) — source text: "
                  f"{cell(u['triple']['source_text']) or '(none)'}"
                  for u in sorted(e["draft_only"], key=lambda u: -len(u["repeats"]))]
        lines.append("")
    lines += ["### Provenance recorded", ""]
    if applied:
        lines += [f"`{applied['path']}` now has {applied['rows']} row(s) for {applied['triples']} ground truth triple(s): "
                  f"{applied['rebuilt']} rewritten for `{llm.MODEL}` on the {len(combined.per_record)} record(s) drafted "
                  f"now (`repeats`, `found_in_repeats`, `found_exact_in_repeats`), other models' rows kept, {applied['dropped']} "
                  f"triple(s) dropped (their classed triple is no longer in the ground truth), "
                  f"{applied['kept_other_records']} of other records kept as they were. Commit it. Step 070 now reports "
                  f"recall by the group found in at least one repeat / found in none / not checked.", ""]
        c = applied["candidates"]
        lines += [f"`{c['path']}` now has {c['rows']} row(s), the draft's facts the ground truth lacks, to review: "
                  f"{c['written']} written for `{llm.MODEL}` on the tuning record(s) drafted now, {c['decisions_kept']} of "
                  f"them with the decision already filled for the same record and classed triple"
                  + (f"; {c['kept_decided']} decided row(s) kept although this run no longer proposes their classed "
                     f"triple" if c["kept_decided"] else "")
                  + (f"; {c['dropped_held_out']} row(s) of records now in the held-out part dropped"
                     if c["dropped_held_out"] else "")
                  + f". {c['undecided']} row(s) have no decision yet: fill the column `decision` of each with `added`, "
                  f"`left out (<section>, rule <n>)` or `already in the ground truth in other words` "
                  f"(helpers/second_opinion.md, *The draft's facts to review*). The {c['held_out_not_written']} of the "
                  f"held-out records are not written. Commit both files.", ""]
    else:
        lines += ["Nothing written to `annotations/`. To record which ground truth triples this second opinion found "
                  "(`annotations/second_opinion.csv`, read by step 070), and the draft's facts the ground truth lacks "
                  "for review (`annotations/second_opinion_candidates.csv`), run `py helpers/second_opinion.py --apply "
                  "true` with the same repeats: it pays nothing for the answers already cached.", ""]
    lines += dropped.section(left_out, chosen.items, "at least one repeat (each record is matched on the repeats that "
                             "drafted it)", repo_path(details_path) if files else None)
    lines += dropped.reasks_lines(llm.REASKS)
    lines += model_calls([(f"draft classed triples, repeat {repeat.number} of {n} (one call per text piece; step 050's "
                           f"prompt)", repeat.replies.calls, repeat.replies.reused) for repeat in repeats],
                         calls.paid.test_calls, llm.model_label())
    headline = {"records drafted again": len(combined.per_record), "repeats": n, "ground truth triples": total["gt"],
                "found in at least one repeat": total["found"], "found in every repeat": total["every"],
                "draft's facts the ground truth lacks (tuning, over the repeats)": draft_only[TUNING],
                **dropped.reasks_headline(llm.REASKS)}
    return Results(files=files, headline=headline, details="\n".join(lines), warnings=warnings)


def main(inputs, settings, output):
    chosen   = pick_records(inputs, settings, output)   # code: every finished record (or the ids given), 050's view of the schema
    calls    = paid_calls(chosen, settings, output)     # code: asks once before paying, for every repeat; keeps every answer in cache/
    repeats  = draft_repeats(chosen, calls, settings)   # LLM + code: each repeat's facts with 050's prompt, parsing and checks; 070's pairing
    combined = combine(chosen, repeats, settings["repeats"])   # code: each ground truth triple found in k of the repeats; the draft-only union
    applied  = apply(chosen, combined, settings)        # code: annotations/second_opinion.csv, only with --apply true
    return results(chosen, repeats, combined, applied, calls, settings, output)


if __name__ == "__main__":
    run_step(STEP, INPUTS, SETTINGS, main, specs=SPECS, command=COMMAND, guide=GUIDE)
