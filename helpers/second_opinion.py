"""
second_opinion · A second, independent draft of every finished record, matched against the ground truth.

Many ground truth triples were first drafted by a model (step 050) and corrected by a person; others were written by a
person. Whichever model drafted a record, the facts that model misses are the facts the person had to add alone, so
a second annotator from another source is the standard way to find what a single annotation misses (Tan et al.,
"Revisiting DocRED", EMNLP 2022: a re-annotation found the benchmark's labels incomplete). Here the
second annotator is another model: it drafts every FINISHED record again, exactly the way step 050 drafts (050's
prompt, the ground truth schema as 050 shows it, 050's parsing and checks), and each ground truth triple of the
record is matched against that fresh draft with step 070's pairing (exact and partial pairs; no translation, since
both use the ground truth schema). The ground truth is never changed:

    py helpers/second_opinion.py                       draft every finished record (asks before paying), match, report
    py helpers/second_opinion.py --apply true          the same, and record what was found in annotations/second_opinion.csv
    py helpers/second_opinion.py --ids <id>,<id>       only these finished records
    py helpers/second_opinion.py --model <name>        another model (the default: SECOND_OPINION_MODEL, below)

It runs in the frame every step runs in (common/common_helpers/step.py, run_step): its run id, log, report and
manifest (the model, its settings, the prompts' fingerprints), and the answers cached in its own output folder, so a
rerun pays nothing. It writes no drafted batch, and nothing in annotations/ unless --apply true, which writes only
annotations/second_opinion.csv (common/common_helpers/second_opinion.py: which models checked each ground truth
triple and which found it). Step 070 then reports recall and partial F1 for the ground truth triples found by the
second opinion and for those not found.

Held-out records are drafted too (so step 070 can group their triples), but the draft's facts the ground truth lacks
are listed, for review, for TUNING records only: reviewing a held-out record's would let it shape the ground truth
and the rules (annotations/guidelines.md, Before you start). For held-out records the report gives counts only.

Reads:   records.jsonl (020), splits.json (030), annotations/ground_truth_schema.txt, annotations/ground_truth/
Writes:  second_opinion_triples.csv (the draft, in a drafted batch's columns), second_opinion_matches.csv (each
         ground truth triple with what the draft did about it; the draft's facts the ground truth lacks, tuning
         records only), second_opinion_details.json; with --apply true, annotations/second_opinion.csv
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
from common.second_opinion import PATH as TABLE_PATH, TRIPLE, key_of, read_table, write_table   # noqa: E402
from common.step import Results, Spec, check_settings, load_moves, repo_path, run_step  # noqa: E402
from common.stop import Stop                                                   # noqa: E402
from common.triples_io import is_describes                                     # noqa: E402

#: The output folder's and the run id's name (outputs/intermediate_results/second_opinion/, second_opinion_<date>).
STEP = "second_opinion"
COMMAND, GUIDE = "py helpers/second_opinion.py", "helpers/second_opinion.md"
#: The default model: Google's flagship, gemini-4-argon (released 2026-09-30; usable through NASA's LiteLLM on
#: 2026-11-01; gemini-3.1-pro-preview is usable too). From another maker than 060's model (claude-opus-5-5), and a
#: later model than 050's (gemini-2.5-pro), so a fact missed by both of those still has a chance here. A setting
#: (--model), not fixed. Through LiteLLM, Gemini 4 is sent no temperature (its maker says it is ignored) and its
#: thinking level as `reasoning_effort` (common/common_helpers/llm.py, TEMPERATURE and THINKING).
SECOND_OPINION_MODEL = "gemini-4-argon"

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
    "repeat":             1,     # which repeat of this recipe: 1 reuses saved answers; 2, 3, ... ask again, each into answers of its own
    "confirm_paid_calls": True,  # stop and ask before the first model call; false for unattended runs
    "apply":              False,  # also write what was found into annotations/second_opinion.csv (the only write to annotations/)
}

#: This helper's own settings' rules (common.step.Spec); the shared ones come with check_settings.
SPECS = {"apply": Spec(bool)}

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
#: second_opinion_matches.csv's statuses.
FOUND_EXACT, FOUND_PARTIAL, NOT_FOUND_STATUS, DRAFT_ONLY = "found (exact)", "found (partial)", "not found", "draft only"
MATCH_COLUMNS = (["record_id", "position", "part", "status", "entity_classes_agree"]
                 + [f"ground_truth_{c}" for c in TRIPLE] + [f"ground_truth_{DRAFTED_BY}"]
                 + [f"draft_{c}" for c in TRIPLE] + ["draft_source_text", ORIGIN_COLUMN])
NOT_FINISHED = "not finished in the ground truth (only finished records get a second opinion)"


@dataclass
class Matched:
    per_record: dict = field(default_factory=dict)  # {id: {"gt": [(row, level or None, classes agree)], "draft_only": [rows]}}
    rows: list = field(default_factory=list)        # second_opinion_matches.csv's rows
    not_drafted: list = field(default_factory=list)  # ids whose model call failed


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
    chosen.notes.append(f"This run drafts {len(picked)} finished record(s) again ("
                        + ", ".join(f"{n} {p}" for p, n in sorted(parts.items())) + f") with {settings['model']}, "
                        f"to match the draft against the ground truth. It writes no drafted batch and changes "
                        f"nothing in annotations/" + (" except annotations/second_opinion.csv (--apply true)."
                                                       if settings["apply"] else "."))
    same = [r for r in finished.rows if r["id"] in set(picked) and r.get(DRAFTED_BY, "").strip().lower()
            == settings["model"].strip().lower()]
    if same:
        chosen.notes.append(f"{len(same)} ground truth triple(s) of these records were drafted by {settings['model']} "
                            f"itself (column {DRAFTED_BY}), so for them this isn't an independent second opinion. "
                            f"Nothing to do unless you want one: give another model with --model <name>.")
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


def ask_model(chosen, calls, settings):
    return annotate.ask_model(chosen, calls, settings,
                              plan=f"the second opinion will draft {len(chosen.items)} finished record(s) again")


def build_rows(chosen, replies):
    return annotate.build_rows(chosen, replies)


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
    """Each drafted record's ground truth triples paired with its fresh draft's classed triples (070's pairing,
    pairing.pair_triples: exact then partial, no translation): each ground truth triple found (exact or partial) or
    not; each draft triple left unpaired is a fact the ground truth lacks, listed for tuning records only."""
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
        part = chosen.parts.get(rid) or ""
        entry = {"gt": [], "draft_only": []}
        base = {"record_id": rid, "position": item["position"], "part": part,
                ORIGIN_COLUMN: audit.origin("records", rid)}
        for gi, g in enumerate(gt):
            ei, level = partner.get(gi, (None, None))
            agree = pairing.classes_agree(g, ex[ei]) if ei is not None else None
            entry["gt"].append((g, level, agree))
            row = {**base, "status": {None: NOT_FOUND_STATUS, "exact": FOUND_EXACT, "partial": FOUND_PARTIAL}[level],
                   "entity_classes_agree": "" if agree is None else ("yes" if agree else "no"),
                   **{f"ground_truth_{c}": g[c] for c in TRIPLE}, f"ground_truth_{DRAFTED_BY}": g.get(DRAFTED_BY, "")}
            if ei is not None:
                row.update({f"draft_{c}": ex[ei][c] for c in TRIPLE}, draft_source_text=ex[ei]["source_text"])
            matched.rows.append(row)
        for ei, t in enumerate(ex):
            if ei in paired_e:
                continue
            entry["draft_only"].append(t)
            if part == TUNING:                           # a held-out record's are counted, never listed
                matched.rows.append({**base, "status": DRAFT_ONLY, **{f"draft_{c}": t[c] for c in TRIPLE},
                                     "draft_source_text": t["source_text"]})
        matched.per_record[rid] = entry
    found = sum(1 for e in matched.per_record.values() for _, level, _ in e["gt"] if level)
    total = sum(len(e["gt"]) for e in matched.per_record.values())
    log.info(f"  {found} of {total} ground truth triple(s) found by the second opinion in {len(matched.per_record)} record(s)")
    return matched


def apply(chosen, matched: Matched, settings: dict, path: Path = TABLE_PATH) -> dict | None:
    """With --apply true: annotations/second_opinion.csv gets, for every record drafted this run, one row per ground
    truth triple with this run's model added to checked_by, to found_by when found, to found_exact_by when found
    exactly (and removed from the two it no longer earns); rows of those records that match no ground truth triple
    any more are dropped; every other record's rows are kept as they are. Returns what was written, or None."""
    if not settings["apply"]:
        return None
    model = llm.MODEL
    table = read_table(path)
    drafted = set(matched.per_record)
    order = {k: i for i, k in enumerate(table)}
    kept = {k: r for k, r in table.items() if r["id"] not in drafted}
    dropped_rows = [r for k, r in table.items() if r["id"] in drafted]
    rebuilt = {}
    for rid, entry in matched.per_record.items():
        for g, level, _ in entry["gt"]:
            k = key_of(rid, g)
            row = dict(table.get(k) or {"id": rid, **{c: g[c] for c in TRIPLE},
                                        "checked_by": [], "found_by": [], "found_exact_by": []})
            for column, earns in (("checked_by", True), ("found_by", level is not None), ("found_exact_by", level == "exact")):
                names = [m for m in row[column] if m != model]
                row[column] = names + ([model] if earns else [])
            rebuilt[k] = row
    dropped_rows = [r for r in dropped_rows if key_of(r["id"], r) not in rebuilt]
    rows = {**kept, **rebuilt}

    def place(k):                                        # pool position, then the file's order, then the triple
        row = rows[k]
        pos = chosen.positions.get(row["id"])
        return (pos is None, pos or 0, row["id"], order.get(k, len(order)), k)
    ordered = [rows[k] for k in sorted(rows, key=place)]
    write_table(path, ordered)
    log.info(f"  wrote {repo_path(path)}: {len(ordered)} row(s), {len(rebuilt)} of them for the {len(drafted)} record(s) drafted now")
    return {"path": repo_path(path), "rows": len(ordered), "rebuilt": len(rebuilt), "dropped": len(dropped_rows),
            "kept_other_records": len(kept)}


# --------------------------------------------------------------------------

def _triple(t: dict) -> str:
    return f"{t['subject']} ({t['subject_class']}) {t['predicate']} {t['object']} ({t['object_class']})"


def results(chosen, replies, drafts, matched: Matched, applied, calls, settings, output) -> Results:
    draft_path, matches_path, details_path = output / DRAFT_NAME, output / MATCHES_NAME, output / DETAILS_NAME
    left_out = dropped.left_out(replies, chosen.items)
    draft_rows = [{**{c: r.get(c, "") for c in annotate.GROUND_TRUTH_COLUMNS}, "all_facts_extracted": "0",
                   DRAFTED_BY: llm.MODEL, "flags": " ".join(r["errors"] + r["flags"]),
                   ORIGIN_COLUMN: audit.origin("records", item["id"])}
                  for item in chosen.items for r in drafts.rows.get(item["id"], [])]
    files = []
    if matched.per_record:
        write_csv(draft_path, annotate.COLUMNS, draft_rows)
        write_csv(matches_path, MATCH_COLUMNS, matched.rows)
        per_record = []
        for item in chosen.items:
            e = matched.per_record.get(item["id"])
            levels = [level for _, level, _ in e["gt"]] if e else []
            per_record.append({"id": item["id"], "pool_position": item["position"], "part": chosen.parts.get(item["id"]),
                               "title": item["title"], "pieces": len(item["pieces"]),
                               "status": "drafted" if e else "failed", "error": replies.failed.get(item["id"]),
                               "ground_truth_triples": len(levels), "found_exact": levels.count("exact"),
                               "found_partial": levels.count("partial"), "not_found": levels.count(None),
                               "draft_only": len(e["draft_only"]) if e else None,
                               "removed": drafts.removed.get(item["id"], [])})
        write_json(details_path, {
            "made": {"run_id": audit.current_run_id(), **llm.describe(), "settings": settings},
            "chosen": chosen.how, "records": per_record, "skipped_while_choosing": chosen.skipped,
            "left_out": dropped.details(left_out), "applied": applied,
        })
        files = [draft_path, matches_path, details_path]
        if applied:
            files.append(TABLE_PATH)
        log.info(f"  wrote {DRAFT_NAME}, {MATCHES_NAME} and {DETAILS_NAME}")

    warnings = list(chosen.notes)
    if replies.failed:
        warnings.append(extraction.failed_note(replies, "the second opinion"))
    if not matched.per_record:
        warnings.append(f"No record was drafted, so nothing was matched and nothing written: the model calls for all "
                        f"{len(chosen.items)} record(s) failed (the warning before this one says why). Fix the cause "
                        f"if it's yours, then run `py helpers/second_opinion.py` again.")
    coined = [n for kind in ("entity_classes", "predicates") for n in chosen.coined[kind]]
    if coined:
        warnings.append(f"{len(coined)} component class(es) used in the ground truth's finished tuning records aren't in "
                        f"the ground truth schema, so the model saw them without a definition: "
                        f"{named([f'{n} (coined in the ground truth)' for n in coined], 5, '; ')}. Add each one you mean "
                        f"to keep to annotations/ground_truth_schema.txt (`py helpers/annotate.py`).")
    missing = check_origins(matched.rows, "rows of the matches file")
    if missing:
        warnings.append(missing)

    # the counts
    gt_all = [(rid, g, level) for rid, e in matched.per_record.items() for g, level, _ in e["gt"]]
    by_part = collections.defaultdict(collections.Counter)
    by_drafter = collections.defaultdict(collections.Counter)
    for rid, g, level in gt_all:
        part = chosen.parts.get(rid) or "outside the pool"
        drafter = g.get(DRAFTED_BY, "").strip() or "(a person: drafted_by empty)"
        for c in (by_part[part], by_drafter[drafter]):
            c["gt"] += 1
            c[level or "none"] += 1
    draft_only = {TUNING: 0, HELD_OUT: 0, "outside the pool": 0}
    for rid, e in matched.per_record.items():
        draft_only[chosen.parts.get(rid) or "outside the pool"] += len(e["draft_only"])

    def share(c: collections.Counter) -> str:
        found = c["exact"] + c["partial"]
        return f"{found} of {c['gt']}" + (f" ({100 * found / c['gt']:.0f}%)" if c["gt"] else "")

    lines = ["### What this run worked on", "",
             f"{len(matched.per_record)} finished record(s) drafted again by `{llm.MODEL}` ({chosen.how}), with step "
             f"050's prompt, schema view, parsing and checks; each record's ground truth triples matched against the "
             f"fresh draft with step 070's pairing (exact, then partial; no translation: both use the ground truth "
             f"schema; no partial pair review applies). The ground truth is unchanged.", "",
             "| Pool position | Part | Record | Ground truth triples | Found (exact) | Found (partial) | Not found | Draft only |",
             "|---:|---|---|---:|---:|---:|---:|---:|"]
    for item in chosen.items:
        e = matched.per_record.get(item["id"])
        pos = item["position"] if item["position"] is not None else "–"
        if e is None:
            lines.append(f"| {pos} | {chosen.parts.get(item['id']) or '–'} | {cell(item['title'])} | failed | | | | |")
            continue
        levels = [level for _, level, _ in e["gt"]]
        lines.append(f"| {pos} | {chosen.parts.get(item['id']) or '–'} | {cell(item['title'])} | {len(levels)} | "
                     f"{levels.count('exact')} | {levels.count('partial')} | {levels.count(None)} | {len(e['draft_only'])} |")
    total = collections.Counter()
    for c in by_part.values():
        total.update(c)
    lines += ["", "### Found by the second opinion", "",
              f"Ground truth triples the fresh draft also stated (an exact or partial pair): **{share(total)}**, "
              f"{total['exact']} exact and {total['partial']} partial; not found: {total['none']}. A ground truth "
              f"triple not found was stated by one annotator only: a fact the second model misses, or one the "
              f"ground truth's rules state and the draft doesn't; it is not thereby wrong.", "",
              "| Group | Ground truth triples | Found | Exact | Partial | Not found |", "|---|---:|---|---:|---:|---:|"]
    for part in (TUNING, HELD_OUT, "outside the pool"):
        if part in by_part:
            c = by_part[part]
            lines.append(f"| {part} part | {c['gt']} | {share(c)} | {c['exact']} | {c['partial']} | {c['none']} |")
    for drafter, c in sorted(by_drafter.items()):
        lines.append(f"| drafted by {cell(drafter)} | {c['gt']} | {share(c)} | {c['exact']} | {c['partial']} | {c['none']} |")
    lines += ["", f"The rows *drafted by* split the ground truth triples by their `{DRAFTED_BY}` column: a row a model "
                  f"drafted and a person corrected, or a row a person wrote (empty). Every row of every drafted "
                  f"record is in `{repo_path(matches_path)}` (column `status`), one per ground truth triple.", ""]
    lines += ["### The second opinion's facts the ground truth lacks (tuning records)", "",
              f"Classed triples of the fresh draft that pair with no ground truth triple: {draft_only[TUNING]} in the "
              f"tuning records, listed below with the record and the draft's source text, for review (a fact the "
              f"ground truth missed, a fact its rules leave out on purpose, or a wrong one). "
              + (f"The {draft_only[HELD_OUT]} of the held-out records are counted here and nowhere else: they are not "
                 f"listed, in this report or in `{MATCHES_NAME}`, since reviewing them would let the held-out records "
                 f"shape the ground truth and its rules (annotations/guidelines.md, Before you start)."
                 if HELD_OUT in by_part else "")
              + (f" Records outside the pool: {draft_only['outside the pool']}." if draft_only["outside the pool"] else ""), ""]
    for item in chosen.items:
        e = matched.per_record.get(item["id"])
        if not e or chosen.parts.get(item["id"]) != TUNING or not e["draft_only"]:
            continue
        lines += [f"**{item['title']}** (pool position {item['position']}, `{item['id']}`)", ""]
        lines += [f"- {_triple(t)} — source text: {cell(t['source_text']) or '(none)'}" for t in e["draft_only"]]
        lines.append("")
    lines += ["### Provenance recorded", ""]
    if applied:
        lines += [f"`{applied['path']}` now has {applied['rows']} row(s): {applied['rebuilt']} rewritten for the "
                  f"{len(matched.per_record)} record(s) drafted now (`checked_by` names `{llm.MODEL}`; `found_by` and "
                  f"`found_exact_by` where it found the triple), {applied['dropped']} dropped (their classed triple is "
                  f"no longer in the ground truth), {applied['kept_other_records']} of other records kept as they were. "
                  f"Commit it. Step 070 now reports recall by the group found / not found / not checked.", ""]
    else:
        lines += ["Nothing written to `annotations/`. To record which ground truth triples this second opinion found "
                  "(`annotations/second_opinion.csv`, read by step 070), run `py helpers/second_opinion.py --apply "
                  "true`: it pays nothing for the answers already cached.", ""]
    lines += dropped.section(left_out, chosen.items, "the second opinion", repo_path(details_path) if files else None)
    lines += dropped.reasks_lines(llm.REASKS)
    lines += model_calls([("draft classed triples (one call per text piece; step 050's prompt)", replies.calls, replies.reused)],
                         calls.paid.test_calls, llm.model_label())
    headline = {"records drafted again": len(matched.per_record), "ground truth triples": total["gt"],
                "found by the second opinion": total["exact"] + total["partial"],
                "draft's facts the ground truth lacks (tuning)": draft_only[TUNING],
                **dropped.reasks_headline(llm.REASKS)}
    return Results(files=files, headline=headline, details="\n".join(lines), warnings=warnings)


def main(inputs, settings, output):
    chosen  = pick_records(inputs, settings, output)   # code: every finished record (or the ids given), 050's view of the schema
    calls   = paid_calls(chosen, settings, output)     # code: asks before paying; keeps every answer in cache/
    replies = ask_model(chosen, calls, settings)       # LLM: every fact each record states, with 050's prompt
    drafts  = build_rows(chosen, replies)              # code: 050's parsing and checks
    matched = match(chosen, drafts)                    # code: 070's pairing of each ground truth triple with the draft
    applied = apply(chosen, matched, settings)         # code: annotations/second_opinion.csv, only with --apply true
    return results(chosen, replies, drafts, matched, applied, calls, settings, output)


if __name__ == "__main__":
    run_step(STEP, INPUTS, SETTINGS, main, specs=SPECS, command=COMMAND, guide=GUIDE)
