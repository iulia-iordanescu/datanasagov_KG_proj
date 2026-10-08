"""
moves.py -- the main moves of 070_evaluate, as called by 070_evaluate/run.py.

    stage 1  records.py  pick_records     code: which records are evaluated (finished, extracted, in the fair sample)
    -        (here)      paid_calls       code: asks before paying; keeps every answer in cache/
    stage 2  component_classes.py  translate_component_classes  LLM: current schema's component classes → ground truth vocabulary, new ones only (+ suggestions for (none) rows); you check
    stage 3  pairing.py    compare          code: record by record, exact and partial pairs, strict, within reach
    stage 4  stats.py    compute_metrics  code: the numbers, each with its margin of error, per part and stratum
    -        (here)      results          writes metrics.json, per_record.md and compared_triples.csv; the report

Every model answer is cached in cache/ inside the step's output folder
(common/common_helpers/cache.py), so a rerun pays only for what isn't there yet.
Terms are as defined in docs/terminology.md.
"""
from __future__ import annotations

import datetime as dt

import pairing
import readings
import component_classes as component_classes_stage
import records as records_stage
import stats
from common import audit, llm
from common.audit import ORIGIN_COLUMN, check_origins, log
from common.files import append_csv, read_csv, write_csv, write_json, write_text
from common.report import cell, model_calls, named
from common.step import ANNOTATIONS_DIR, Results

METRICS_NAME = "metrics.json"
PER_RECORD_NAME = "per_record.md"
COMPARED_NAME = "compared_triples.csv"
LOOKS = ANNOTATIONS_DIR / "held_out_looks.csv"
LOOKS_COLUMNS = ["date", "run_id", "schema", "held_out_records"]
TRIPLE = ("subject", "subject_class", "predicate", "object", "object_class")
SHOW = 20                        # rows listed in the report before "…"
COMPARED_COLUMNS = (["record_id", "position", "part", "stratum", "status", "entity_classes_right", "within_reach", "within_strict_reach"]
                 + [f"extracted_{c}" for c in TRIPLE] + [f"translated_{c}" for c in TRIPLE]
                 + [f"ground_truth_{c}" for c in TRIPLE] + [ORIGIN_COLUMN])


# --------------------------------------------------------------------------

def pick_records(inputs, settings):
    return records_stage.pick_records(inputs, settings)


def paid_calls(evaluated, settings, output) -> llm.Calls:
    return llm.paid_calls(settings, output)         # evaluated.notes were shown, and asked about, by pick_records


def translate_component_classes(inputs, evaluated, calls):
    return component_classes_stage.translate_component_classes(inputs, evaluated, calls)


def compare(evaluated, translation):
    return pairing.compare_all(evaluated, translation)


def compute_metrics(evaluated, settings) -> dict:
    return stats.compute_metrics(evaluated, settings)


# --------------------------------------------------------------------------

def _with_margin(n: dict) -> str:
    if n is None or n.get("value") is None:
        return "–"
    if n.get("low") is None:
        return readings.pct(n["value"])
    return f"{readings.pct(n['value'])} ({readings.pct(n['low'])}–{readings.pct(n['high'])})"


def _margin_check_lines(checks: dict | None) -> list:
    """The margin of error's assumptions, each with its check (070_evaluate/metrics/approximately.md, Sampling error)."""
    if not checks:
        return []
    ok = lambda good: "holds" if good else "**doesn't hold**"           # noqa: E731
    alone, bound = checks["single_record_strata"], checks["at_bound"]
    big = checks["largest_record"]
    share = checks["catalog_proportion"] or 0
    return ["#### The margin of error's assumptions, checked", "",
            "| Assumption | Check | Result |", "|---|---|---|",
            "| The evaluated records are a random sample of the catalog | only the fair sample is evaluated | holds (by design) |",
            "| Whole records vary, independently of each other | records are redrawn whole | holds (by design) |",
            f"| Enough records | at least {stats.MIN_RECORDS} evaluated | holds |",
            f"| Every stratum adds spread | strata with only 1 evaluated record: "
            f"{len(alone)}{' (' + named(alone, 5) + ')' if alone else ''} | {ok(not alone)}: such a stratum's "
            f"record is in every redraw, so the ranges come out too narrow |",
            f"| The range isn't at 0% or 100% | metrics whose range reaches 0% or 100%: "
            f"{named(bound, 5) if bound else 'none'} | {ok(not bound)}: there, a percentile range is too narrow |",
            f"| No one record dominates | the largest record's proportion of the extracted triples: "
            f"{readings.pct(big['extracted triples']['proportion'])} (`{big['extracted triples']['record']}`); of the "
            f"ground truth triples: {readings.pct(big['ground truth triples']['proportion'])} "
            f"(`{big['ground truth triples']['record']}`) | for reading: no established threshold |",
            f"| A small proportion of the catalog is evaluated | {readings.pct(share)} | "
            f"{ok(share <= stats.FINITE_NEGLIGIBLE)} (below {100 * stats.FINITE_NEGLIGIBLE:.0f}%, its effect is "
            f"negligible; above, the ranges come out somewhat too wide) |", ""]


def _triple(f: dict) -> str:
    return f"{f['subject']} ({f['subject_class']}) {f['predicate']} {f['object']} ({f['object_class']})"


def _log_look(evaluated, schema_file: str) -> int:
    """Add one line to annotations/held_out_looks.csv (never changing a line
    already there) and return how many looks it now holds."""
    held = sum(r["part"] == "held-out" for r in evaluated.records)
    append_csv(LOOKS, LOOKS_COLUMNS, [{"date": dt.date.today().isoformat(), "run_id": audit.current_run_id() or "",
                                       "schema": schema_file, "held_out_records": held}])
    return len(read_csv(LOOKS))


def _per_record(records: list, hidden: int) -> str:
    lines = ["# Per record", "",
             "Each evaluated record: its pairs (✓ exact / ≈ partial, with both triples), extracted but not "
             "in the ground truth (count against precision), and in the ground truth but not extracted (count "
             "against recall). Extracted triples are shown translated into the ground truth vocabulary. Terms: "
             "docs/terminology.md, section *Evaluating extraction*.", ""]
    if hidden:
        lines += [f"The {hidden} held-out record(s) are not listed: they are kept for the end "
                  f"(`--evaluate_held_out true` lists them, and logs the look).", ""]
    for r in records:
        c = r["compared"]
        gt, ex = r["gt"], c["translated"]
        lines += [f"## {r['title'] or r['id']}", "",
                  f"Pool position {r['position']} · {r['part']} · stratum {r['stratum'] or '(none)'} · id `{r['id']}`", ""]
        d = c["describes"]
        mark = "✓" if d["right"] else "✗"
        lines += [f"Describes: {mark} extraction said `{d['said'] or '(none named)'}` (translated into the ground truth "
                  f"vocabulary); the ground truth says `{d['truth'] or '(none)'}` (ground truth vocabulary)", ""]
        paired_g = {gi for gi, _, _ in c["pairs"]}
        paired_e = {ei for _, ei, _ in c["pairs"]}
        if c["pairs"]:
            lines.append("**Pairs**")
            lines.append("")
            for gi, ei, level in c["pairs"]:
                strict = pairing.classes_agree(gt[gi], ex[ei])
                lines.append(f"- {'✓ exact' if level == 'exact' else '≈ partial'}"
                             f"{'' if strict else ', entity classes differ'}: {_triple(ex[ei])}")
                if level == "partial" or not strict:
                    lines.append(f"  - ground truth: {_triple(gt[gi])}")
            lines.append("")
        extra = [ex[i] for i in range(len(ex)) if i not in paired_e]
        if extra:
            lines += ["**Extracted, but not in the ground truth** (against precision)", ""]
            lines += [f"- ✗ {_triple(f)}" for f in extra] + [""]
        missed = [(gt[i], c["within_reach"][i]) for i in range(len(gt)) if i not in paired_g]
        if missed:
            lines += ["**In the ground truth, but not extracted** (against recall)", ""]
            lines += [f"- ✗ {_triple(f)}" + ("" if reach else " — out of reach: no predicate of the current schema translates to this one")
                      for f, reach in missed] + [""]
        if not (c["pairs"] or extra or missed):
            lines += ["No triples in the ground truth, and none extracted.", ""]
    return "\n".join(lines)


def _compared_rows(records: list) -> list:
    rows = []
    for r in records:
        c = r["compared"]
        gt, ex = r["gt"], c["translated"]
        base = {"record_id": r["id"], "position": r["position"], "part": r["part"], "stratum": r["stratum"]}

        def row(status, gi=None, ei=None):
            out = {**base, "status": status}
            if ei is not None:
                raw = r["extracted"][ei]
                out.update({f"extracted_{k}": raw[k] for k in TRIPLE})
                out.update({f"translated_{k}": ex[ei][k] for k in TRIPLE})
                out[ORIGIN_COLUMN] = audit.origin("extracted_triples", raw["_position"])
            if gi is not None:
                out.update({f"ground_truth_{k}": gt[gi][k] for k in TRIPLE})
                out["within_reach"] = "yes" if c["within_reach"][gi] else "no"
                out["within_strict_reach"] = "yes" if c["within_strict_reach"][gi] else "no"
                origins = gt[gi].get(audit.ORIGIN_FIELD) or []
                out[ORIGIN_COLUMN] = "; ".join(filter(None, [out.get(ORIGIN_COLUMN), *origins]))
            if gi is not None and ei is not None:
                out["entity_classes_right"] = "yes" if pairing.classes_agree(gt[gi], ex[ei]) else "no"
            return out
        paired_g = {gi for gi, _, _ in c["pairs"]}
        paired_e = {ei for _, ei, _ in c["pairs"]}
        rows += [row(f"{level} pair", gi, ei) for gi, ei, level in c["pairs"]]
        rows += [row("extracted only", ei=i) for i in range(len(ex)) if i not in paired_e]
        rows += [row("ground truth only", gi=i) for i in range(len(gt)) if i not in paired_g]
    return rows


def _mismatch_lines(mismatches: list) -> list:
    """The report's list of component class mismatches (pairing.component_class_mismatches)."""
    lines = ["### Component class mismatches", "",
             "A mismatch: extraction found the triple, but a component class didn't line up with the ground truth's, which may mean a translation error. A row of the "
             "table below seen often means a row of the translation table (`annotations/component_class_mapping.csv`) is "
             "likely wrong: check that row (`py helpers/annotate.py`, Translation table). Seen once, it may just be "
             "extraction choosing the wrong component class.", "",
             "How to read a row of the table below, e.g. *entity class | Body | Spacecraft | CelestialBody | 9*: "
             "these events, "
             "counted together, happened 9 times:", "",
             "- **entity class, subject:** extraction used `Body` (current schema) as the entity class of a "
             "triple's subject, translated to `Spacecraft` (ground truth vocabulary), while the ground truth triple paired with it (a pair, "
             "exact or partial) had `CelestialBody` (ground truth vocabulary) as its subject's entity class;",
             "- **entity class, object:** the same, for the object's entity class. One triple can count twice, "
             "once per slot;",
             "- **predicate:** an extracted triple and a ground truth triple left unpaired had the same subject and "
             "object, but extraction's predicate (current schema), once translated, wasn't the ground truth's "
             "predicate (ground truth vocabulary). With subject and object the other way round, the "
             "swap_subject_and_object of that predicate's row in the translation table may be wrong.", "",
             "Component classes are compared after translation. All 9 events share one cause: the translation table's row "
             "`Body` (current schema) --> `Spacecraft` (ground truth vocabulary). Had that row said `Body` --> `CelestialBody` (ground truth "
             "vocabulary), none of the 9 would have happened. So that row of the translation table is the "
             "likely mistake, and the one to check.", ""]
    if not mismatches:
        return lines + ["None.", ""]
    lines += ["| Kind | Component class in the current schema | Translated to (ground truth vocabulary) | What the ground truth "
              "triple says instead (ground truth vocabulary) | Times | Check |", "|---|---|---|---|---:|---|"]
    for c in mismatches[:SHOW]:
        to = "(none)" if c["translated_to"].endswith(pairing.NO_TRANSLATION) else c["translated_to"]
        check = (f"swap_subject_and_object of {c['crt_component_class']} (current schema): subject and object were the "
                 f"other way round" if c["swapped"] else
                 f"should {c['crt_component_class']} (current schema) translate to {c['gtt_component_class']} (ground truth vocabulary)?")
        lines.append(f"| {c['kind']} | {cell(c['crt_component_class'])} | {cell(to)} | {cell(c['gtt_component_class'])} | {c['count']} "
                     f"| {cell(check)} |")
    if len(mismatches) > SHOW:
        lines.append(f"| … {len(mismatches) - SHOW} more, in `{METRICS_NAME}` | | | | | |")
    return lines + [""]


def results(evaluated, translation, metrics, calls, settings, output) -> Results:
    schema_file = evaluated.schema_used.get("made", {}).get("schema", "?")
    looks = _log_look(evaluated, schema_file) if settings["evaluate_held_out"] else None
    per_record_path, compared_path, metrics_path = (output / PER_RECORD_NAME, output / COMPARED_NAME,
                                                  output / METRICS_NAME)
    # Only the parts whose numbers are shown: the held-out records' triples stay
    # unseen too, unless --evaluate_held_out true.
    shown = [r for r in evaluated.records if r["part"] in metrics]
    mismatches = pairing.component_class_mismatches(shown)
    tuning = [r for r in shown if r["part"] == "tuning"]
    unreviewed = sum(r["compared"]["partial_review"]["unreviewed"] for r in tuning)
    rejected = sum(r["compared"]["partial_review"]["rejected"] for r in tuning)
    compared_rows = _compared_rows(shown)
    write_text(per_record_path, _per_record(shown, len(evaluated.records) - len(shown)))
    write_csv(compared_path, COMPARED_COLUMNS, compared_rows)
    write_json(metrics_path, {
        "made": {"run_id": audit.current_run_id(), "model": llm.MODEL, "schema": schema_file, "settings": settings,
                 "min_records_for_margin": stats.MIN_RECORDS, "redraws": stats.REDRAWS, "seed": stats.SEED},
        "evaluated": {p: [r["id"] for r in evaluated.records if r["part"] == p] for p in ("tuning", "held-out")},
        "left_out": evaluated.left_out,
        "parts": {p: {"numbers": v["numbers"], "strata": v["strata"], "margin_checks": v["margin_checks"],
                      "describes_confusion": [{"truth": t, "said": s, "records": n}
                                              for (t, s), n in v["confusion"].items()]}
                  for p, v in metrics.items() if p != "kept_aside"},
        "held_out_looks": looks,
        "component_class_mismatches": mismatches,
        "translation_suggestions": translation.suggested,
        "partial_pairs_tuning": {"unreviewed": unreviewed, "rejected_by_review": rejected},
    })
    log.info(f"  wrote {METRICS_NAME}, {PER_RECORD_NAME}, {COMPARED_NAME}")

    warnings = list(evaluated.notes)
    for part, v in metrics.items():
        if part == "kept_aside" or v["numbers"] is None:
            continue
        n = v["numbers"]
        if not n["margins"]:
            warnings.append(f"{part}: only {n['records']} record(s) evaluated, fewer than {stats.MIN_RECORDS}: the "
                            f"numbers are shown without a margin of error, and are too few to draw conclusions "
                            f"from.")
        elif any(g["share_evaluated"] is not None and abs(g["share_evaluated"] - g["share_pool"]) > stats.SHARE_GAP
                 for g in v["strata"]):
            warnings.append(f"{part}: some stratum's share of the evaluated records differs from its share "
                            f"of the pool by more than {100 * stats.SHARE_GAP:.0f} points; see the strata table.")
        checks = v["margin_checks"]
        if checks and (checks["single_record_strata"] or checks["at_bound"]
                       or (checks["catalog_proportion"] or 0) > stats.FINITE_NEGLIGIBLE):
            warnings.append(f"{part}: an assumption of the margin of error doesn't hold, so some ranges are less "
                            f"trustworthy; see the report's section on the margin of error's assumptions.")
    if translation.suggested:
        warnings.append(f"The model suggests {len(translation.suggested)} row(s) of component_class_mapping.csv that say (none) may "
                        f"now have a counterpart in the ground truth vocabulary: "
                        + named([f"{s['component_class_from_past_or_crt_schema']} (current schema) --> {s['component_class_in_gtt']} "
                                 f"(ground truth vocabulary)" for s in translation.suggested], 5, "; ")
                        + ". Rows aren't changed: check them (py helpers/annotate.py, Translation table, shows the "
                          "suggestion).")
    if translation.outdated:
        warnings.append(f"{len(translation.outdated)} row(s) of component_class_mapping.csv translate to (none) though the ground "
                        f"truth vocabulary now has the same component class: {named(translation.outdated, 5, '; ')}. Probably out of "
                        f"date: check them (py helpers/annotate.py, Translation table); keep (none) only if the ground "
                        f"truth's component class means something else.")
    if unreviewed:
        warnings.append(f"{unreviewed} partial pair(s) of the tuning part aren't reviewed yet, so the partial "
                        f"level may count pairs that aren't the same fact (e.g. MODIS vs MODIS Terra). Review "
                        f"them: py helpers/annotate.py, Partial pairs.")
    frequent = [c for c in mismatches if c["count"] >= pairing.MISMATCH_WARN]
    if frequent:
        warnings.append(f"{len(frequent)} component class mismatch(es) seen {pairing.MISMATCH_WARN} or more times where extraction "
                        f"found the triple but a component class differed: a translation in component_class_mapping.csv may be wrong or "
                        f"missing. See Component class mismatches.")
    if looks is not None:
        warnings.append(f"The held-out part was looked at: {looks} time(s) so far "
                        f"(annotations/held_out_looks.csv; commit it). Each look is a chance to tune on it.")
    missing = check_origins(compared_rows, "compared triples")
    if missing:
        warnings.append(missing)

    lines = ["### What this run worked on", "",
             f"Current schema (the one 060 used): `{schema_file}`, translated to the ground truth vocabulary "
             f"through `annotations/component_class_mapping.csv` "
             f"({translation.rows_used} component classes; {translation.reversed_used} predicate(s) reversed).", "",
             "| Part | Records evaluated |", "|---|---:|"]
    for part in ("tuning", "held-out"):
        count = sum(r["part"] == part for r in evaluated.records)
        lines.append(f"| {part} | {count}{'' if part in metrics else ' (numbers not shown: see below)'} |")
    lines.append("")
    if metrics["kept_aside"]:
        lines += ["The held-out part's numbers are not shown: they are kept for the end, so the pipeline isn't "
                  "tuned on them. `--evaluate_held_out true` shows them (and logs the look).", ""]
    lines += ["### The translation table", "",
              "Rows of `annotations/component_class_mapping.csv` that say `(none)`, and component classes of the ground truth vocabulary "
              "that no row translates to. The ground truth vocabulary grows as you annotate: if a `(none)` row "
              "should now point to one of its component classes, fix that row.", "",
              "| Kind | Current schema's component classes translated to (none) | Ground truth vocabulary's component classes nothing "
              "translates to |", "|---|---|---|"]
    lines += [f"| {kind} | {cell(named(translation.to_none[kind], 20)) or '–'} | {cell(named(translation.untranslated[kind], 20)) or '–'} |"
              for kind in ("entity class", "predicate")]
    lines.append("")
    merged = [(kind, mine, theirs) for kind in ("entity class", "predicate")
              for mine, theirs in translation.merged[kind].items()]
    if merged:
        lines += ["Component classes of the ground truth vocabulary that two or more of the current schema's component classes translate "
                  "to: the ground truth doesn't tell those component classes of the current schema apart, so neither can these metrics "
                  "(a mix-up between them costs extraction nothing). If the difference matters, make it in the "
                  "ground truth.", "",
                  "| Kind | Component class in the ground truth vocabulary | Current schema's component classes that translate to it |",
                  "|---|---|---|"]
        lines += [f"| {kind} | {cell(mine)} | {cell(', '.join(theirs))} |" for kind, mine, theirs in merged]
        lines.append("")
    lines += _mismatch_lines(mismatches)
    if evaluated.left_out:
        lines += ["Left out: " + "; ".join(f"{len(v)} {k}" for k, v in evaluated.left_out.items())
                  + f". Not finished yet in the ground truth: {evaluated.unfinished}.", ""]

    for part, v in metrics.items():
        if part == "kept_aside" or v["numbers"] is None:
            continue
        n = v["numbers"]
        lines += [f"### Metrics: {part} part ({n['records']} records, {n['gt_triples']} ground truth triples, "
                  f"{n['extracted']} extracted)", ""]
        if not n["margins"]:
            lines += [f"**Too few records ({n['records']}, fewer than {stats.MIN_RECORDS}) for a margin of "
                      f"error: these numbers could easily have come out very differently. Don't draw "
                      f"conclusions from them yet.**", ""]
        lines += ["| Pair level | | Precision | Recall | F1 |", "|---|---|---:|---:|---:|"]
        for level in pairing.LEVELS:
            L = n[level]
            lines.append(f"| {level} | triples | {_with_margin(L['precision'])} | {_with_margin(L['recall'])} "
                         f"| {_with_margin(L['f1'])} |")
            lines.append(f"| {level} | triples with entity classes (strict) | {_with_margin(L['strict_precision'])} "
                         f"| {_with_margin(L['strict_recall'])} | {_with_margin(L['strict_f1'])} |")
        recs = [r for r in evaluated.records if r["part"] == part]
        pr = {k: sum(r["compared"]["partial_review"][k] for r in recs) for k in ("unreviewed", "rejected")}
        lines += ["", (f"Partial pairs in these numbers not reviewed yet: {pr['unreviewed']}; pairs your review "
                       f"ruled out (\"not the same fact\"): {pr['rejected']}." if part == "tuning" else
                       "Partial pairs of the held-out part are never reviewed (that would mean looking at it), "
                       "so its partial level may count pairs that aren't the same fact.")]
        lines += ["", "| Pair level | Entity-class accuracy | Recall within reach | Strict recall within "
                      "strict reach |", "|---|---:|---:|---:|"]
        lines += [f"| {level} | {_with_margin(n[level]['entity_class_accuracy'])} | "
                  f"{_with_margin(n[level]['recall_within_reach'])} | "
                  f"{_with_margin(n[level]['strict_recall_within_reach'])} |" for level in pairing.LEVELS]
        d = n["describes"]
        lines += ["", f"- **Recall upper bound** (ground truth triples whose predicate the schema has, the most recall "
                      f"can be): {_with_margin(n['recall_upper_bound'])}. **Strict recall upper bound** (predicate and both "
                      f"entity classes, the most strict recall can be): {_with_margin(n['strict_recall_upper_bound'])}.",
                  f"- **What the record describes**: right for {_with_margin(d['accuracy'])} of {d['records']} "
                  f"record(s). Always guessing the most common entity class would get {readings.pct(d['majority_baseline'])}; "
                  f"averaged per entity class: {readings.pct(d['per_entity_class_average'])}.", ""]
        if v["confusion"]:
            lines += ["| The ground truth says (ground truth vocabulary) | Extraction said (translated into the ground "
                      "truth vocabulary) | Records |", "|---|---|---:|"]
            lines += [f"| {cell(t)} | {cell(s)} | {k} |" for (t, s), k in sorted(v["confusion"].items())]
            lines.append("")
        lines += readings.readings(part, n, recs, evaluated, translation, looks, v["confusion"])
        lines += [f"Per stratum (numbers once a stratum has {stats.MIN_RECORDS} records; with many strata, "
                  f"about 1 in 20 margins misses by chance, so one odd stratum is not a finding):", "",
                  "| Stratum | Records | Share evaluated | Share of pool | Precision (exact) | Recall (exact) |",
                  "|---|---:|---:|---:|---:|---:|"]
        for g in v["strata"]:
            gn = g["numbers"]
            lines.append(f"| {cell(g['stratum'])} | {g['records']} | {readings.pct(g['share_evaluated'])} | {readings.pct(g['share_pool'])} "
                         f"| {_with_margin(gn['exact']['precision']) if gn else 'too few'} "
                         f"| {_with_margin(gn['exact']['recall']) if gn else 'too few'} |")
        lines.append("")
        lines += _margin_check_lines(v["margin_checks"])
    lines += ["A margin of error covers only which records happened to be evaluated: not mistakes in the ground "
              "truth, not the model answering differently on another run, and not changes made while looking at "
              "these records. The metrics assume the ground truth lists every fact the records state.", "",
              f"Every record's triples, side by side: `{PER_RECORD_NAME}`; one row per triple: `{COMPARED_NAME}`; "
              f"every number: `{METRICS_NAME}`.", ""]
    lines += model_calls([("propose component class translations", translation.calls, None),
                          ("suggest counterparts for (none) rows", translation.suggest_calls, None)],
                         calls.paid.test_calls, llm.MODEL)

    tuning = metrics.get("tuning", {}).get("numbers")
    headline = {}
    if tuning:
        headline = {"precision (tuning, exact)": readings.pct(tuning["exact"]["precision"]["value"]),
                    "recall (tuning, exact)": readings.pct(tuning["exact"]["recall"]["value"])}
    return Results(files=[metrics_path, per_record_path, compared_path], headline=headline,
                   details="\n".join(lines), warnings=warnings)
