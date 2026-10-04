"""
moves.py -- the main moves of 070_evaluate, as called by 070_evaluate.py.

    stage 1  records.py  pick_records     code: which records are scored (finished, extracted, in the fair part)
    -        (here)      paid_calls       code: asks before paying; keeps every answer in cache/
    stage 2  names.py    translate_names  LLM: current schema's names → ground truth vocabulary, new names only; you check
    stage 3  match.py    compare          code: record by record, exact and partial matches, strict, within reach
    stage 4  stats.py    score            code: the numbers, each with its margin of error, per part and group
    -        (here)      results          writes scores.json, per_record.md and matches.csv; the report

Every model answer is cached in cache/ inside the step's output folder
(common/cache.py), so a rerun pays only for what isn't there yet.
Terms are as defined in docs/terminology.md.
"""
from __future__ import annotations

import datetime as dt

import match
import names as names_stage
import records as records_stage
import stats
from common import audit, llm
from common.audit import ORIGIN_COLUMN, check_origins, log
from common.files import append_csv, read_csv, write_csv, write_json, write_text
from common.report import cell, model_calls, named
from common.step import ANNOTATIONS_DIR, Results

SCORES_NAME = "scores.json"
PER_RECORD_NAME = "per_record.md"
MATCHES_NAME = "matches.csv"
LOOKS = ANNOTATIONS_DIR / "held_out_looks.csv"
LOOKS_COLUMNS = ["date", "run_id", "schema", "held_out_records"]
FACT = ("subject", "subject_class", "predicate", "object", "object_class")
SHOW = 20                        # rows listed in the report before "…"
MATCH_COLUMNS = (["record_id", "position", "part", "group", "status", "entity_classes_right", "within_reach"]
                 + [f"extracted_{c}" for c in FACT] + [f"translated_{c}" for c in FACT]
                 + [f"ground_truth_{c}" for c in FACT] + [ORIGIN_COLUMN])


# --------------------------------------------------------------------------

def pick_records(inputs, settings):
    return records_stage.pick_records(inputs, settings)


def paid_calls(scored, settings, output) -> llm.Calls:
    return llm.paid_calls(settings, output, notes=scored.notes)


def translate_names(inputs, scored, calls):
    return names_stage.translate_names(inputs, scored, calls)


def compare(scored, names):
    return match.compare_all(scored, names)


def score(scored, settings) -> dict:
    return stats.score(scored, settings)


# --------------------------------------------------------------------------

def _pct(x) -> str:
    return "–" if x is None else f"{100 * x:.0f}%"


def _with_margin(n: dict) -> str:
    if n is None or n.get("value") is None:
        return "–"
    if n.get("low") is None:
        return _pct(n["value"])
    return f"{_pct(n['value'])} ({_pct(n['low'])}–{_pct(n['high'])})"


def _fact(f: dict) -> str:
    return f"{f['subject']} ({f['subject_class']}) {f['predicate']} {f['object']} ({f['object_class']})"


def _log_look(scored, schema_file: str) -> int:
    """Add one line to annotations/held_out_looks.csv (never changing a line
    already there) and return how many looks it now holds."""
    held = sum(r["part"] == "held-out" for r in scored.records)
    append_csv(LOOKS, LOOKS_COLUMNS, [{"date": dt.date.today().isoformat(), "run_id": audit.current_run_id() or "",
                                       "schema": schema_file, "held_out_records": held}])
    return len(read_csv(LOOKS))


def _per_record(records: list, hidden: int) -> str:
    lines = ["# Per record", "",
             "Each scored record: its facts matched (✓ exact / ≈ partial, with both versions), extracted but not "
             "in the ground truth (count against precision), and in the ground truth but not extracted (count "
             "against recall). Extracted facts are shown translated into the ground truth vocabulary. Terms: "
             "docs/terminology.md, section *Scoring extraction*.", ""]
    if hidden:
        lines += [f"The {hidden} held-out record(s) are not listed: they are kept for the end "
                  f"(`--score_held_out true` lists them, and logs the look).", ""]
    for r in records:
        c = r["compared"]
        gt, ex = r["gt"], c["translated"]
        lines += [f"## {r['title'] or r['id']}", "",
                  f"Pool position {r['position']} · {r['part']} · group {r['group'] or '(none)'} · id `{r['id']}`", ""]
        d = c["describes"]
        mark = "✓" if d["right"] else "✗"
        lines += [f"Describes: {mark} extraction said `{d['said'] or '(none named)'}` (translated into the ground truth "
                  f"vocabulary); the ground truth says `{d['truth'] or '(none)'}` (ground truth vocabulary)", ""]
        paired_g = {gi for gi, _, _ in c["pairs"]}
        paired_e = {ei for _, ei, _ in c["pairs"]}
        if c["pairs"]:
            lines.append("**Matched**")
            lines.append("")
            for gi, ei, level in c["pairs"]:
                strict = match.classes_agree(gt[gi], ex[ei])
                lines.append(f"- {'✓ exact' if level == 'exact' else '≈ partial'}"
                             f"{'' if strict else ', entity classes differ'}: {_fact(ex[ei])}")
                if level == "partial" or not strict:
                    lines.append(f"  - ground truth: {_fact(gt[gi])}")
            lines.append("")
        extra = [ex[i] for i in range(len(ex)) if i not in paired_e]
        if extra:
            lines += ["**Extracted, but not in the ground truth** (against precision)", ""]
            lines += [f"- ✗ {_fact(f)}" for f in extra] + [""]
        missed = [(gt[i], c["within_reach"][i]) for i in range(len(gt)) if i not in paired_g]
        if missed:
            lines += ["**In the ground truth, but not extracted** (against recall)", ""]
            lines += [f"- ✗ {_fact(f)}" + ("" if reach else " — out of reach: the schema can't say it")
                      for f, reach in missed] + [""]
        if not (c["pairs"] or extra or missed):
            lines += ["No facts in the ground truth, and none extracted.", ""]
    return "\n".join(lines)


def _match_rows(records: list) -> list:
    rows = []
    for r in records:
        c = r["compared"]
        gt, ex = r["gt"], c["translated"]
        base = {"record_id": r["id"], "position": r["position"], "part": r["part"], "group": r["group"]}

        def row(status, gi=None, ei=None):
            out = {**base, "status": status}
            if ei is not None:
                raw = r["extracted"][ei]
                out.update({f"extracted_{k}": raw[k] for k in FACT})
                out.update({f"translated_{k}": ex[ei][k] for k in FACT})
                out[ORIGIN_COLUMN] = audit.origin("extracted_triples", raw["_position"])
            if gi is not None:
                out.update({f"ground_truth_{k}": gt[gi][k] for k in FACT})
                out["within_reach"] = "yes" if c["within_reach"][gi] else "no"
                origins = gt[gi].get(audit.ORIGIN_FIELD) or []
                out[ORIGIN_COLUMN] = "; ".join(filter(None, [out.get(ORIGIN_COLUMN), *origins]))
            if gi is not None and ei is not None:
                out["entity_classes_right"] = "yes" if match.classes_agree(gt[gi], ex[ei]) else "no"
            return out
        paired_g = {gi for gi, _, _ in c["pairs"]}
        paired_e = {ei for _, ei, _ in c["pairs"]}
        rows += [row(level, gi, ei) for gi, ei, level in c["pairs"]]
        rows += [row("wrong", ei=i) for i in range(len(ex)) if i not in paired_e]
        rows += [row("missed", gi=i) for i in range(len(gt)) if i not in paired_g]
    return rows


def _clue_lines(clues: list) -> list:
    """The report's list of name clues (match.name_clues)."""
    lines = ["### Possible translation errors", "",
             "Where extraction found the fact but a name differed: a paired fact with another entity class, or "
             "unpaired facts with the same subject and object but another predicate. Frequent pairs point at a row "
             "of `annotations/name_mapping.csv` to check (`py annotate.py`, Translation table); a single one may "
             "just be extraction choosing the wrong name.", ""]
    if not clues:
        return lines + ["None.", ""]
    lines += ["| Kind | Name in the current schema | Its translation (ground truth vocabulary) | Name in the ground "
              "truth vocabulary it met instead | Times | Check |", "|---|---|---|---|---:|---|"]
    for c in clues[:SHOW]:
        to = "(none)" if c["translated_to"].endswith(match.NO_TRANSLATION) else c["translated_to"]
        check = (f"swap_subject_and_object of {c['crt_name']} (current schema): subject and object were the "
                 f"other way round" if c["swapped"] else
                 f"should {c['crt_name']} (current schema) translate to {c['gtt_name']} (ground truth vocabulary)?")
        lines.append(f"| {c['kind']} | {cell(c['crt_name'])} | {cell(to)} | {cell(c['gtt_name'])} | {c['count']} "
                     f"| {cell(check)} |")
    if len(clues) > SHOW:
        lines.append(f"| … {len(clues) - SHOW} more, in `{SCORES_NAME}` | | | | | |")
    return lines + [""]


def results(scored, names, scores, calls, settings, output) -> Results:
    schema_file = scored.schema_used.get("made", {}).get("schema", "?")
    looks = _log_look(scored, schema_file) if settings["score_held_out"] else None
    per_record_path, matches_path, scores_path = (output / PER_RECORD_NAME, output / MATCHES_NAME,
                                                  output / SCORES_NAME)
    # Only the parts whose numbers are shown: the held-out records' facts stay
    # unseen too, unless --score_held_out true.
    shown = [r for r in scored.records if r["part"] in scores]
    clues = match.name_clues(shown)
    match_rows = _match_rows(shown)
    write_text(per_record_path, _per_record(shown, len(scored.records) - len(shown)))
    write_csv(matches_path, MATCH_COLUMNS, match_rows)
    write_json(scores_path, {
        "made": {"run_id": audit.current_run_id(), "model": llm.MODEL, "schema": schema_file, "settings": settings,
                 "min_records_for_margin": stats.MIN_RECORDS, "reshuffles": stats.RESHUFFLES, "seed": stats.SEED},
        "scored": {p: [r["id"] for r in scored.records if r["part"] == p] for p in ("tuning", "held-out")},
        "left_out": scored.left_out,
        "parts": {p: {"numbers": v["numbers"], "groups": v["groups"],
                      "describes_confusion": [{"truth": t, "said": s, "records": n}
                                              for (t, s), n in v["confusion"].items()]}
                  for p, v in scores.items() if p != "kept_aside"},
        "held_out_looks": looks,
        "name_clues": clues,
    })
    log.info(f"  wrote {SCORES_NAME}, {PER_RECORD_NAME}, {MATCHES_NAME}")

    warnings = list(scored.notes)
    for part, v in scores.items():
        if part == "kept_aside" or v["numbers"] is None:
            continue
        n = v["numbers"]
        if not n["margins"]:
            warnings.append(f"{part}: only {n['records']} record(s) scored, fewer than {stats.MIN_RECORDS}: the "
                            f"numbers are shown without a margin of error, and are too few to draw conclusions "
                            f"from.")
        elif any(g["share_scored"] is not None and abs(g["share_scored"] - g["share_pool"]) > stats.SHARE_GAP
                 for g in v["groups"]):
            warnings.append(f"{part}: some sampling group's share of the scored records differs from its share "
                            f"of the pool by more than {100 * stats.SHARE_GAP:.0f} points; see the group table.")
    frequent = [c for c in clues if c["count"] >= match.CLUE_WARN]
    if frequent:
        warnings.append(f"{len(frequent)} pair(s) of names met {match.CLUE_WARN} or more times where extraction "
                        f"found the fact but a name differed: a translation in name_mapping.csv may be wrong or "
                        f"missing. See Possible translation errors.")
    if looks is not None:
        warnings.append(f"The held-out part was looked at: {looks} time(s) so far "
                        f"(annotations/held_out_looks.csv; commit it). Each look is a chance to tune on it.")
    missing = check_origins(match_rows, "match rows")
    if missing:
        warnings.append(missing)

    lines = ["### What this run worked on", "",
             f"Current schema (the one 060 used): `{schema_file}`, translated to the ground truth vocabulary "
             f"through `annotations/name_mapping.csv` "
             f"({names.rows_used} names; {names.reversed_used} predicate(s) reversed).", "",
             "| Part | Records scored |", "|---|---:|"]
    for part in ("tuning", "held-out"):
        count = sum(r["part"] == part for r in scored.records)
        lines.append(f"| {part} | {count}{'' if part in scores else ' (numbers not shown: see below)'} |")
    lines.append("")
    if scores["kept_aside"]:
        lines += ["The held-out part's numbers are not shown: they are kept for the end, so the pipeline isn't "
                  "tuned on them. `--score_held_out true` shows them (and logs the look).", ""]
    lines += ["### The translation table", "",
              "Rows of `annotations/name_mapping.csv` that say `(none)`, and names of the ground truth vocabulary "
              "that no row translates to. The ground truth vocabulary grows as you annotate: if a `(none)` row "
              "should now point to one of its names, fix that row.", "",
              "| Kind | Current schema's names translated to (none) | Ground truth vocabulary's names nothing "
              "translates to |", "|---|---|---|"]
    lines += [f"| {kind} | {cell(named(names.to_none[kind], 20)) or '–'} | {cell(named(names.untranslated[kind], 20)) or '–'} |"
              for kind in ("entity class", "predicate")]
    lines.append("")
    merged = [(kind, mine, theirs) for kind in ("entity class", "predicate")
              for mine, theirs in names.merged[kind].items()]
    if merged:
        lines += ["Names of the ground truth vocabulary that two or more of the current schema's names translate "
                  "to: the ground truth doesn't tell those current-schema names apart, so neither can these scores "
                  "(a mix-up between them costs extraction nothing). If the difference matters, make it in the "
                  "ground truth.", "",
                  "| Kind | Name in the ground truth vocabulary | Current schema's names that translate to it |",
                  "|---|---|---|"]
        lines += [f"| {kind} | {cell(mine)} | {cell(', '.join(theirs))} |" for kind, mine, theirs in merged]
        lines.append("")
    lines += _clue_lines(clues)
    if scored.left_out:
        lines += ["Left out: " + "; ".join(f"{len(v)} {k}" for k, v in scored.left_out.items())
                  + f". Not finished yet in the ground truth: {scored.unfinished}.", ""]

    for part, v in scores.items():
        if part == "kept_aside" or v["numbers"] is None:
            continue
        n = v["numbers"]
        lines += [f"### Scores: {part} part ({n['records']} records, {n['gt_facts']} ground truth facts, "
                  f"{n['extracted']} extracted)", ""]
        if not n["margins"]:
            lines += [f"**Too few records ({n['records']}, fewer than {stats.MIN_RECORDS}) for a margin of "
                      f"error: these numbers could easily have come out very differently. Don't draw "
                      f"conclusions from them yet.**", ""]
        lines += ["| Names compared | | Precision | Recall |", "|---|---|---:|---:|"]
        for level in match.LEVELS:
            L = n[level]
            lines.append(f"| {level} | facts | {_with_margin(L['precision'])} | {_with_margin(L['recall'])} |")
            lines.append(f"| {level} | facts with entity classes (strict) | {_with_margin(L['strict_precision'])} "
                         f"| {_with_margin(L['strict_recall'])} |")
        lines += ["", "| Names compared | Entity-class accuracy | Recall within reach |", "|---|---:|---:|"]
        lines += [f"| {level} | {_with_margin(n[level]['entity_class_accuracy'])} | "
                  f"{_with_margin(n[level]['recall_within_reach'])} |" for level in match.LEVELS]
        d = n["describes"]
        lines += ["", f"- **Schema ceiling** (ground truth facts the schema can express at all): "
                      f"{_with_margin(n['schema_ceiling'])}.",
                  f"- **What the record describes**: right for {_with_margin(d['accuracy'])} of {d['records']} "
                  f"record(s). Always guessing the most common kind would score {_pct(d['majority_baseline'])}; "
                  f"averaged per kind: {_pct(d['per_kind_average'])}.", ""]
        if v["confusion"]:
            lines += ["| The ground truth says (ground truth vocabulary) | Extraction said (translated into the ground "
                      "truth vocabulary) | Records |", "|---|---|---:|"]
            lines += [f"| {cell(t)} | {cell(s)} | {k} |" for (t, s), k in sorted(v["confusion"].items())]
            lines.append("")
        lines += [f"Per sampling group (numbers once a group has {stats.MIN_RECORDS} records; with many groups, "
                  f"about 1 in 20 margins misses by chance, so one odd group is not a finding):", "",
                  "| Group | Records | Share scored | Share of pool | Precision (exact) | Recall (exact) |",
                  "|---|---:|---:|---:|---:|---:|"]
        for g in v["groups"]:
            gn = g["numbers"]
            lines.append(f"| {cell(g['group'])} | {g['records']} | {_pct(g['share_scored'])} | {_pct(g['share_pool'])} "
                         f"| {_with_margin(gn['exact']['precision']) if gn else 'too few'} "
                         f"| {_with_margin(gn['exact']['recall']) if gn else 'too few'} |")
        lines.append("")
    lines += ["A margin of error covers only which records happened to be scored: not mistakes in the ground "
              "truth, not the model answering differently on another run, and not tuning on these records. The "
              "ground truth was drafted by a model and corrected by a person, not written from scratch; a fact "
              "both missed is counted nowhere, so recall may be overstated.", "",
              f"Every record's facts, side by side: `{PER_RECORD_NAME}`; one row per fact: `{MATCHES_NAME}`; "
              f"every number: `{SCORES_NAME}`.", ""]
    lines += model_calls([("propose name translations", names.calls, None)], calls.paid.test_calls, llm.MODEL)

    tuning = scores.get("tuning", {}).get("numbers")
    headline = {}
    if tuning:
        headline = {"precision (tuning, exact)": _pct(tuning["exact"]["precision"]["value"]),
                    "recall (tuning, exact)": _pct(tuning["exact"]["recall"]["value"])}
    return Results(files=[scores_path, per_record_path, matches_path], headline=headline,
                   details="\n".join(lines), warnings=warnings)
