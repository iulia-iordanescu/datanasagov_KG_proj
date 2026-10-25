"""
moves.py -- the main moves of 070_evaluate, as called by 070_evaluate/run.py.

    stage 1  records.py            pick_records                 code: which records are evaluated (finished, extracted, in the fair sample)
    -        (here)                paid_calls                   code: asks before paying; keeps every answer in cache/
    stage 2  component_classes.py  translate_component_classes  LLM: current schema's component classes → ground truth schema, new ones only (+ suggestions for (none) rows); you check
    stage 3  pairing.py            compare                      code: record by record, exact and partial pairs, strict, within reach
    stage 4  stats.py              compute_metrics              code: the numbers, each with its margin of error, per part and stratum
    -        (here)                results                      writes metrics.json, per_record.md, and compared_triples.csv, and with --evaluate_held_out true a line of annotations/held_out_looks.csv; the report
                                                                 keeps this run's tuning records' counts in evaluations/<run id>.json, for py helpers/compare_runs.py

Every model answer is cached in cache/ inside the step's output folder
(common/common_helpers/cache.py), so a rerun pays only for what isn't there yet.
Terms are as defined in docs/terminology.md.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json

import pairing
import readings
import component_classes as component_classes_stage
import records as records_stage
import stats
from common import audit, llm
from common.audit import ORIGIN_COLUMN, check_origins, log
from common.files import append_csv, read_csv, write_csv, write_json, write_text
from common.report import cell, model_calls, named, per_text_table, this_report
from common.stop import Stop
from common.step import ANNOTATIONS_DIR, Results, git_commit, repo_path

METRICS_NAME = "metrics.json"
PER_RECORD_NAME = "per_record.md"
COMPARED_NAME = "compared_triples.csv"
#: Each run's tuning records' counts and recipe, one file per run, never overwritten: what py helpers/compare_runs.py
#: compares (helpers/compare_runs.md).
EVALUATIONS_DIR = "evaluations"
LOOKS = ANNOTATIONS_DIR / "held_out_looks.csv"
LOOKS_COLUMNS = ["date", "run_id", "schema", "held_out_records", "extraction_run_id", "translation_sha256",
                 "held_out_ground_truth_sha256"]
TRIPLE = ("subject", "subject_class", "predicate", "object", "object_class")
SHOW = 20                        # rows listed in the report before "…"
TABLE = "`py helpers/annotate.py`, view *Translation table*"     # where a person checks the translation table
AGAIN = "then run `py 070_evaluate/run.py` again."
COMPARED_COLUMNS = (["record_id", "position", "part", "stratum", "status", "entity_classes_right", "subject_and_object_swapped", "within_reach", "within_strict_reach"]
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
        return readings.NO_VALUE
    if n.get("low") is None:
        return readings.pct(n["value"])
    return f"{readings.pct(n['value'])} ({readings.pct(n['low'])}–{readings.pct(n['high'])})"


def _margin_check_lines(checks: dict | None) -> list:
    """The margin of error's assumptions, each with its check (070_evaluate/metrics/approximately.md, Sampling error)."""
    if not checks:
        return []
    ok = lambda good: "holds" if good else "**doesn't hold**"           # noqa: E731
    bound = checks["at_bound"]
    big = checks["largest_record"]
    share = checks["catalog_proportion"] or 0
    return ["#### The margin of error's assumptions, checked", "",
            "| Assumption | Check | Result |", "|---|---|---|",
            "| The evaluated records are a random sample of the catalog | only the fair sample is evaluated | holds (by design) |",
            "| Whole records vary, independently of each other | records are redrawn whole | holds (by design) |",
            f"| Enough records | at least {stats.MIN_RECORDS} evaluated | holds |",
            "| The redraws vary as other samples would | records are redrawn from all strata together, since "
            "how many evaluated records come from each stratum is itself random | holds (by design) |",
            f"| The range isn't at 0% or 100% | metrics whose range reaches 0% or 100%: "
            f"{named(bound, 5) if bound else 'none'} | {ok(not bound)}: there, a percentile range is too narrow"
            f"{'; more evaluated records make this rarer' if bound else ''} |",
            f"| No one record dominates | the largest record's proportion of the occurrences: "
            f"{readings.pct(big['extracted triples']['proportion'])} (`{big['extracted triples']['record']}`); of the "
            f"ground truth triples: {readings.pct(big['ground truth triples']['proportion'])} "
            f"(`{big['ground truth triples']['record']}`) | for reading: no established threshold |",
            f"| A small proportion of the catalog is evaluated | {readings.pct(share)} | "
            f"{ok(share <= stats.FINITE_NEGLIGIBLE)} (below {100 * stats.FINITE_NEGLIGIBLE:.0f}%, its effect is "
            f"negligible; above, the ranges come out somewhat too wide) |", ""]



def _too_few(n: dict) -> str:
    """The warning above a part's numbers when there are too few records for a margin of error."""
    return (f"**Too few records ({n['records']}, fewer than {stats.MIN_RECORDS}) for a margin of error: these "
            f"numbers could easily have come out very differently. Don't draw conclusions from them yet.**")


#: What each of 060's reasons for removing an item means (their list: docs/terminology.md, *extracted triple*; the
#: checks behind them: 060_extract/060_extract.md, *How it works*). A removal for two reasons is written as both, joined
#: by a space ("component_class_not_in_schema source_text").
REMOVED_REASONS = {"source_text": "its source text is missing, or isn't in the record's text",
                   "component_class_not_in_schema": "an entity class or predicate the current schema doesn't have",
                   "duplicate": "the same classed triple twice in the record (one copy is kept)",
                   "malformed": "not a classed triple at all"}


def _removed_lines(records: int, removed: list) -> list:
    """The report's table of what 060's checks removed from the evaluated records, per reason
    (stats.removed_by_reason)."""
    lines = ["#### Removed by 060", "",
             f"Before 070 sees them, 060's checks remove every item its model listed for these {records} "
             f"record(s) that fails one of them: each item a classed triple, except those removed as `malformed`. Removed ones are never "
             f"evaluated: they count neither for nor against precision, and can't pair with a ground truth triple. "
             f"Each, with its reason: `060_extract/extracted_triples_removed.csv`; the checks: "
             f"`060_extract/060_extract.md`, *How it works*.", ""]
    if not removed:
        return lines + ["None: 060 removed nothing from these records.", ""]
    lines += ["| Reason (as 060 wrote it) | What it means | Items removed | Records with any item removed for it |",
              "|---|---|---:|---:|"]
    for x in removed:
        means = " and ".join(REMOVED_REASONS.get(w, "a reason 070 doesn't know: not one of those in "
                                                     "`docs/terminology.md`, *extracted triple*") for w in x["reason"].split())
        lines.append(f"| `{cell(x['reason'])}` | {cell(means)} | {x['removed']} | {x['records']} |")
    return lines + [f"| all | | {sum(x['removed'] for x in removed)} | |", ""]


def _reach_cell(r: dict) -> str:
    """A row's Reach mark (070_evaluate.md, *Per predicate and per entity class*)."""
    if r["within_reach"] is None:
        return "none: translates to (none), so not in the ground truth schema"
    n = r["ground_truth_triples"]
    return (f"{'within' if r['within_reach'] else 'out of'} reach; {r['within_strict_reach']} of {n} ground truth "
            f"triple{'' if n == 1 else 's'} within strict reach")


#: The numbers of each level in a row of the report's tables per predicate and per entity class, in column order.
PER_COMPONENT_CLASS_NUMBERS = (("precision", "Precision"), ("recall", "Recall"), ("f1", "F1"),
                               ("strict_precision", "Precision"), ("strict_recall", "Recall"), ("strict_f1", "F1"),
                               ("strict_recall_within_reach", "Recall within reach"))
NONE_WITHIN_STRICT_REACH = "no value (0 to divide by: no ground truth triple within strict reach)"
#: The column counting occurrences whose element has multiplicity above 1 in its record's multiset of translated
#: extracted triples (070_evaluate/metrics/pairs.md, Example, *A multiset of translated extracted triples*).
MULTIPLIED = "Occurrences with multiplicity > 1"
MULTIPLIED_NOTE = ("*Occurrences with multiplicity > 1*: of the row's occurrences, the ones whose element of their "
                   "record's multiset of translated extracted triples has multiplicity above 1, i.e. two or more "
                   "extracted triples of the record translate to the same translated extracted triple; at most one of "
                   "those copies can pair with a given ground truth triple (`070_evaluate/metrics/pairs.md`, Example, "
                   "*A multiset of translated extracted triples*).")


def _per_component_class_lines(n: dict, tables: dict) -> list:
    """The report's tables of precision and recall per predicate, per subject class, and per object class
    (stats.per_component_class)."""
    lines = ["#### Per predicate and per entity class", "",
             "Precision and recall for each predicate, subject class, and object class of the ground truth schema "
             f"(a component class of the current schema whose row of the translation table says (none) has a row "
             f"of its own, under its own name followed by *{pairing.NO_TRANSLATION.strip()}*). An occurrence counts for its translated predicate, subject class, and object "
             "class; a ground truth triple for its own. A pair counts for the predicate of its two triples, and for "
             "a subject class (or object class) only when both its triples have that one there: so a wrong entity "
             "class counts against the precision of the one extraction named, and against the recall of the one the "
             "ground truth has. Rows are sorted by *Counted against it (exact)*: the occurrences with no exact pair that "
             "counts for it (each against its precision) plus the ground truth triples with no such pair (each "
             "against its recall), most first, so the rows that cost the most come first; a row with 1 occurrence "
             "and 1 ground truth triple costs at most 2. The strict versions count only the strict pairs: those "
             "whose two triples also have the same subject class and the same object class "
             "(`070_evaluate/metrics/pairs.md`, Definition). *Reach* says whether some checked row of the "
             "translation table translates a component class of the current schema to the row's predicate or entity "
             "class (within reach) or none does (out of reach), and how many of the row's ground truth triples are "
             "within strict reach (checked rows translate to their predicate and to both their entity classes; "
             "both terms: `070_evaluate/metrics/recall_upper_bound.md`, Definition). *Strict recall upper bound* "
             "is that number ÷ the row's ground truth triples, and *Recall within reach* (strict) is the row's "
             "strict pairs ÷ that number. " + MULTIPLIED_NOTE + " Details: "
             "`070_evaluate/070_evaluate.md`, *Per predicate and per entity class*.", ""]
    lines += [_too_few(n), ""] if not n["margins"] else         ["With many rows, about 1 in 20 of their margins of error misses the true value by chance (each is a "
          "95% range), so one row that looks unusually good or bad is not, alone, a finding.", ""]
    for table, head in (("predicate", "Predicate"), ("subject class", "Subject class"), ("object class", "Object class")):
        rows = tables[table]
        numbers = [f"{label} ({'strict ' if key.startswith('strict') else ''}{level})"
                   for level in pairing.LEVELS for key, label in PER_COMPONENT_CLASS_NUMBERS]
        heads = ([f"{head} (ground truth schema)", "Reach", "Strict recall upper bound", "Occurrences",
                  MULTIPLIED, "Ground truth triples", "Counted against it (exact)", "Exact pairs that count for it"]
                 + numbers[:7] + ["Pairs that count for it (partial level)"] + numbers[7:])
        lines += ["| " + " | ".join(heads) + " |", "|---|---|" + "---:|" * (len(heads) - 2)]
        empty = " |" * (len(heads) - 1)
        for r in rows[:SHOW]:
            values = [NONE_WITHIN_STRICT_REACH if key == "strict_recall_within_reach" and not r["within_strict_reach"]
                      else _with_margin(r[level][key]) for level in pairing.LEVELS for key, _ in PER_COMPONENT_CLASS_NUMBERS]
            cells = ([cell(r["component_class"]), _reach_cell(r), _with_margin(r["strict_recall_upper_bound"]),
                      r["occurrences"], r["occurrences_multiplicity_above_1"], r["ground_truth_triples"], r["counted_against"], r["exact"]["pairs"]]
                     + values[:7] + [r["partial"]["pairs"]] + values[7:])
            lines.append("| " + " | ".join(str(x) for x in cells) + " |")
        if len(rows) > SHOW:
            lines.append(f"| … {len(rows) - SHOW} more, in `{METRICS_NAME}` |{empty}")
        if not rows:
            lines.append(f"| none |{empty}")
        lines.append("")
        if rows:
            lines += readings.row_readings([readings.component_class_reading(r, table) for r in rows[:SHOW]])
    return lines


NO_VALUE = readings.NO_VALUE
POOLED = "`070_evaluate/metrics.md`, *Pooled, not averaged*"
ID_SHOWN, TITLE_SHOWN = 8, 50                 # characters of a record's id and title in the report's table per record


def _no_value(x) -> str:
    """A proportion of a record's own, or "no value" when its denominator is 0."""
    return NO_VALUE if x is None else readings.pct(x)


def _short(text: str, n: int) -> str:
    return text if len(text) <= n else text[:n] + "…"


#: A record's numbers at each level, as (key in stats.per_record, column label), the version named in brackets.
PER_RECORD_COLUMNS = (("pairs", "Pairs ({})"), ("strict_pairs", "Strict pairs ({})"),
                      ("precision", "Precision ({})"), ("recall", "Recall ({})"), ("f1", "F1 ({})"),
                      ("strict_precision", "Precision (strict {})"), ("strict_recall", "Recall (strict {})"),
                      ("strict_f1", "F1 (strict {})"), ("recall_within_reach", "Recall within reach ({})"),
                      ("strict_recall_within_reach", "Recall within reach (strict {})"))


def _per_record_lines(rows: list) -> list:
    """The report's table of each evaluated record's own numbers (stats.per_record)."""
    lines = ["#### Per record", "",
             "Each evaluated record's own precision, recall, and F1, and their strict versions, recall upper bound, and "
             "recall within reach, by the same formulas as the part's numbers above, for finding the records "
             "extraction does worst on. The part's numbers above add up all its records' counts before dividing "
             f"(pooled), and are never an average of these (why: {POOLED}). No margin of error: it needs at least "
             f"{stats.MIN_RECORDS} records (`070_evaluate/metrics/approximately.md`), and each row is one record. "
             f"*{NO_VALUE}*: e.g. precision of a record with no occurrences. Rows are sorted by *Counted against it (exact)*: the record's occurrences with no "
             "exact pair (each against its precision) plus its ground truth triples with no exact pair (each against "
             "its recall), most first, then by pool position. " + MULTIPLIED_NOTE + " Each record's pairs: "
             f"`{PER_RECORD_NAME}`.", ""]
    heads = (["Pool position", f"Record id (first {ID_SHOWN} characters)", f"Title (first {TITLE_SHOWN} characters)",
              "Occurrences", MULTIPLIED, "Ground truth triples", "Counted against it (exact)", "Recall upper bound",
              "Strict recall upper bound"]
             + [label.format(level) for level in pairing.LEVELS for _, label in PER_RECORD_COLUMNS])
    lines += ["| " + " | ".join(heads) + " |", "|---:|---|---|" + "---:|" * (len(heads) - 3)]
    empty = " |" * (len(heads) - 1)
    for r in rows[:SHOW]:
        cells = ([r["position"], f"`{r['id'][:ID_SHOWN]}`", cell(_short(r["title"] or "", TITLE_SHOWN)),
                  r["occurrences"], r["occurrences_multiplicity_above_1"], r["ground_truth_triples"],
                  r["counted_against"], _no_value(r["recall_upper_bound"]), _no_value(r["strict_recall_upper_bound"])]
                 + [r[level][key] if key.endswith("pairs") else _no_value(r[level][key])
                    for level in pairing.LEVELS for key, _ in PER_RECORD_COLUMNS])
        lines.append("| " + " | ".join(str(x) for x in cells) + " |")
    if len(rows) > SHOW:
        lines.append(f"| … {len(rows) - SHOW} more, in `{METRICS_NAME}` and `{PER_RECORD_NAME}` |{empty}")
    if not rows:
        lines.append(f"| none |{empty}")
    lines.append("")
    return lines + (readings.row_readings([readings.record_reading(r) for r in rows[:SHOW]]) if rows else [])


def _record_block(r: dict) -> list:
    """A record's own numbers (stats.per_record), at the top of its section of per_record.md."""
    lines = [f"Occurrences {r['occurrences']} (with multiplicity > 1: {r['occurrences_multiplicity_above_1']}) · "
             f"ground truth triples {r['ground_truth_triples']} · counted against it "
             f"(exact) {r['counted_against']} · recall upper bound {_no_value(r['recall_upper_bound'])} · strict "
             f"recall upper bound {_no_value(r['strict_recall_upper_bound'])}", "",
             "| | exact | partial | strict exact | strict partial |", "|---|---:|---:|---:|---:|"]
    for label, key, strict_key in (("Pairs", "pairs", "strict_pairs"), ("Precision", "precision", "strict_precision"),
                                   ("Recall", "recall", "strict_recall"), ("F1", "f1", "strict_f1"),
                                   ("Recall within reach", "recall_within_reach", "strict_recall_within_reach")):
        show = (lambda x: x) if key == "pairs" else _no_value
        lines.append(f"| {label} | " + " | ".join(str(show(r[level][k])) for k in (key, strict_key)
                                                  for level in pairing.LEVELS) + " |")
    return lines + ["", f"Reading: {readings.record_reading(r)}", ""]


def _twin_lines(part: str, v: dict, recs: list, learned: dict) -> list:
    """The report's table of the numbers without the twins (docs/terminology.md; stats.twins)."""
    lines = ["#### Twins", "",
             "A twin is an evaluated record with the same title, the same `notes`, or both as a record the current "
             "schema was learned from (docs/terminology.md, section *Evaluating extraction*), so the schema has seen "
             "some or most of its text. Its twin kind says what it shares with one such record: whole text (title and "
             "`notes`), notes only, or title only. Learned from: "
             + ("; ".join(learned.get("how") or []) or "not known") + ".", ""]
    t = v["twins"]
    if t is None:
        return lines + ["Not known: which records the current schema was learned from isn't known, so no record "
                        "is marked (the warning at the top of this report says why, and what to do).", ""]
    if not t["records"]:
        return lines + [f"None of the {len(recs)} evaluated {part} records is a twin, so the numbers above are "
                        f"all on records the schema wasn't learned from.", ""]
    position = {r["id"]: r["position"] for r in recs}
    lines += [f"{len(t['records'])} of the {len(recs)} evaluated {part} records are twins:", "",
              "| Pool position | Record id | Twin kind |", "|---:|---|---|"]
    lines += [f"| {position[x['id']]} | `{x['id']}` | {x['kind']} |" for x in t["records"]]
    lines.append("")
    w = t["without"]
    if w is None:
        return lines + ["Every evaluated record is a twin, so there are no numbers without them.", ""]
    n = v["numbers"]
    lines += [f"| Pair level | Number | All {len(recs)} records | Without the twins, every kind ({w['records']} records) |",
              "|---|---|---:|---:|"]
    for level in pairing.LEVELS:
        for key, label in (("precision", "Precision"), ("recall", "Recall"), ("f1", "F1")):
            lines.append(f"| {level} | {label} | {_with_margin(n[level][key])} | {_with_margin(w[level][key])} |")
    return lines + ["", "If the two columns differ by more than their margins, the numbers above flatter extraction "
                        "on text the schema wasn't learned from; report the column without the twins.", ""]


def _triple(f: dict) -> str:
    return f"{f['subject']} ({f['subject_class']}) {f['predicate']} {f['object']} ({f['object_class']})"


def _multiplied(r: dict, ei: int) -> str:
    """per_record.md's mark on an occurrence whose element has multiplicity above 1 in the record's multiset of
    translated extracted triples: the extracted triples that translate to it, as extracted (current schema)."""
    c = r["compared"]
    m = c["multiplicity"][ei]
    if m < 2:
        return ""
    same = [r["extracted"][i] for i, t in enumerate(c["translated"])
            if pairing.multiset_element(t) == pairing.multiset_element(c["translated"][ei])]
    return (f" — ×{m}: {m} extracted triples translate to this (as extracted, current schema): "
            + "; ".join(_triple(f) for f in same))


def _fingerprint(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def _ground_truth_rows(r: dict) -> list:
    """A record's ground truth as it is compared: each triple's components and source text, then its describes triple."""
    return [{k: t.get(k, "") for k in TRIPLE + ("source_text",)} for t in r["gt"] + [r["gt_describes"] or {}]]


def _translation_fingerprint(translation) -> str:
    return _fingerprint({"entity class": sorted(translation.entity.items()),
                         "predicate": sorted(translation.predicate.items())})


def _recipe(evaluated, translation, inputs_manifest: dict) -> dict:
    """What made this run's numbers, for py helpers/compare_runs.py to show what differs between runs: 060's run
    (code version, settings, prompts, and the schema files it read, by fingerprint) and this run (code version, the
    translation, and the model that proposed it)."""
    extraction = {"run_id": evaluated.extraction_made.get("run_id") or inputs_manifest.get("run_id"),
                  "git_commit": inputs_manifest.get("git_commit"), "settings": inputs_manifest.get("settings", {}),
                  "prompts": {p["file"]: p["sha256"] for p in inputs_manifest.get("prompts", [])},
                  "schema": evaluated.schema_used.get("made", {}).get("schema"),
                  "inputs": {i.get("name"): i.get("sha256") for i in inputs_manifest.get("inputs", [])
                             if i.get("name") in ("schema", "additions")}}
    return {"extraction (060)": extraction,
            "evaluation (070)": {"git_commit": git_commit(), "translation_sha256": _translation_fingerprint(translation),
                                 **{k: v for k, v in llm.describe().items() if k in ("service", "model")}}}


def _keep_evaluation(evaluated, translation, output, tuning: list, inputs_manifest: dict):
    """Write this run's tuning records' counts and recipe to evaluations/<run id>.json (never overwritten, one file
    per run), for py helpers/compare_runs.py. Held-out records are never kept: comparing runs is tuning."""
    run_id = audit.current_run_id() or dt.datetime.now().strftime("070_evaluate_%Y-%m-%d_%H%M%S")
    path = output / EVALUATIONS_DIR / f"{run_id}.json"
    write_json(path, {
        "run_id": run_id, "recipe": _recipe(evaluated, translation, inputs_manifest),
        "records": [{"id": r["id"], "position": r["position"], "stratum": r["stratum"], "twin": r.get("twin"),
                     "ground_truth_sha256": _fingerprint(_ground_truth_rows(r)),
                     "counts": dict(r["compared"]["counts"]),
                     "describes": {k: r["compared"]["describes"][k] for k in ("truth", "said", "right")}}
                    for r in tuning]})
    return path


def _log_look(evaluated, translation, schema_file: str) -> dict:
    """Add one line to annotations/held_out_looks.csv (never changing a line already there): what the look saw (the
    current schema, 060's run, fingerprints of the translation used and of the held-out records' ground truth).
    Returns {"count": looks so far, "changed": [what differs from the previous look, as readings.LOOK_INPUTS names
    it] or None for a first look, "previous": that look's row or None}."""
    held = sorted((r for r in evaluated.records if r["part"] == "held-out"), key=lambda r: r["id"])
    rows = [_ground_truth_rows(r) for r in held]
    look = {"date": dt.date.today().isoformat(), "run_id": audit.current_run_id() or "", "schema": schema_file,
            "held_out_records": str(len(held)),
            "extraction_run_id": str(evaluated.schema_used.get("made", {}).get("run_id") or ""),
            "translation_sha256": _translation_fingerprint(translation),
            "held_out_ground_truth_sha256": _fingerprint([[r["id"] for r in held], rows])}
    if LOOKS.exists():
        header = LOOKS.read_text(encoding="utf-8-sig").split("\n", 1)[0].strip()
        if header != ",".join(LOOKS_COLUMNS):
            raise Stop(f"{repo_path(LOOKS)} has the columns {header}, not the ones 070 writes "
                       f"({','.join(LOOKS_COLUMNS)}), so a look added now would land in the wrong columns. Its first "
                       f"line was probably edited: restore it from Git (`git diff {repo_path(LOOKS)}`), {AGAIN}")
    before = read_csv(LOOKS) if LOOKS.exists() else []
    append_csv(LOOKS, LOOKS_COLUMNS, [look])
    previous = before[-1] if before else None
    changed = None if previous is None else [why for k, why in readings.LOOK_INPUTS.items()
                                             if (previous.get(k) or "") != look[k]]
    return {"count": len(before) + 1, "changed": changed, "previous": previous}


def _per_record(records: list, hidden: int) -> str:
    lines = ["# Per record", "",
             "Each evaluated record: its pairs (✓ exact / ≈ partial), each with its ground truth triple and its "
             "occurrence; its occurrences left extracted only (each counts against precision); and its ground "
             "truth triples left ground truth only (each counts against recall). Occurrences are shown translated "
             "into the ground truth schema. Terms: docs/terminology.md, section *Evaluating extraction*; "
             "pairs: 070_evaluate/metrics/pairs.md. Above each record's pairs, its own numbers, by the same formulas "
             f"as the report's (*{NO_VALUE}*: the formula's denominator is 0; *counted against it (exact)*: its "
             f"occurrences with no exact pair plus its ground truth triples with no exact pair), and its reading (the "
             f"rules: {readings.RULES}). The report's numbers add up all the records' counts before dividing "
             f"(pooled), and are never an average of these (why: {POOLED}).", ""]
    own = {x["id"]: x for x in stats.per_record(records)}
    if hidden:
        lines += [f"The {hidden} held-out record(s) are not listed: they are kept for the end "
                  f"(`--evaluate_held_out true` lists them, and logs the look).", ""]
    for r in records:
        c = r["compared"]
        gt, ex = r["gt"], c["translated"]
        lines += [f"## {r['title'] or r['id']}", "",
                  f"Pool position {r['position']} · {r['part']} · stratum {r['stratum'] or '(none)'} · id `{r['id']}`", ""]
        lines += _record_block(own[r["id"]])
        d = c["describes"]
        mark = "✓" if d["right"] else "✗"
        lines += [f"Describes class: {mark} extraction named `{d['said'] or '(none named)'}` (translated into the ground truth "
                  f"schema); the ground truth says `{d['truth'] or '(none)'}` (ground truth schema)", ""]
        paired_g = {gi for gi, _, _ in c["pairs"]}
        paired_e = {ei for _, ei, _ in c["pairs"]}
        if c["pairs"]:
            lines.append("**Pairs**")
            lines.append("")
            for gi, ei, level in c["pairs"]:
                turned = (gi, ei) in c["swapped"]
                strict = pairing.classes_agree(gt[gi], pairing.as_paired(c, gi, ei))
                lines.append(f"- {'✓ exact' if level == 'exact' else '≈ partial'}"
                             f"{', matched with subject and object swapped' if turned else ''}"
                             f"{'' if strict else ', entity classes differ'}: {_triple(ex[ei])}{_multiplied(r, ei)}")
                if level == "partial" or not strict or turned:
                    lines.append(f"  - ground truth: {_triple(gt[gi])}")
            lines.append("")
        extra = [i for i in range(len(ex)) if i not in paired_e]
        if extra:
            lines += ["**Extracted only** (occurrences without a partner; against precision)", ""]
            lines += [f"- ✗ {_triple(ex[i])}{_multiplied(r, i)}" for i in extra] + [""]
        missed = [(gt[i], c["within_reach"][i]) for i in range(len(gt)) if i not in paired_g]
        if missed:
            lines += ["**Ground truth only** (ground truth triples without a partner; against recall)", ""]
            lines += [f"- ✗ {_triple(f)}" + ("" if reach else " — out of reach: no predicate of the current schema translates to this one")
                      for f, reach in missed] + [""]
        if not (c["pairs"] or extra or missed):
            lines += ["No ground truth triples, and no occurrences.", ""]
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
                out["entity_classes_right"] = "yes" if pairing.classes_agree(gt[gi], pairing.as_paired(c, gi, ei)) else "no"
                out["subject_and_object_swapped"] = "yes" if (gi, ei) in c["swapped"] else "no"
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
             "Counted over the tuning records only: held-out records never say what to change.", "",
             "A component class mismatch: extraction stated the fact, but a component class didn't line up with the ground truth's, which may mean a translation error. A row of the "
             "table below seen often means a row of the translation table (`annotations/component_class_mapping.csv`) is "
             "likely wrong: check that row (`py helpers/annotate.py`, view *Translation table*). Seen once, it may just be "
             "extraction choosing the wrong component class.", "",
             "How to read a row of the table below, e.g. *entity class, subject | Body | Spacecraft | CelestialBody | 9*: "
             "these component class "
             "mismatches, counted together, happened 9 times:", "",
             "- **entity class, subject:** extraction used `Body` (current schema) as the subject class of an "
             "extracted triple, translated to `Spacecraft` (ground truth schema), while the ground truth triple paired with its "
             "occurrence (a pair, exact or partial) had `CelestialBody` (ground truth schema) as its subject class;",
             "- **entity class, object:** extraction used a component class of the current schema as the object "
             "class of an extracted triple, translated to one component class of the ground truth "
             "schema, while the ground truth triple paired with its occurrence had another as its object class. "
             "One pair can count twice: once for the subject classes, once for the object classes;",
             "- **predicate:** an extracted only occurrence and a ground truth only triple had the same subject instance and "
             "object instance, but extraction's predicate (current schema), once translated, wasn't the ground truth's "
             "predicate (ground truth schema). With subject and object the other way round, the "
             "swap_subject_and_object of that predicate's row in the translation table may be wrong.", "",
             "Component classes are compared after translation. All 9 share one cause: the translation table's row "
             "`Body` (current schema) --> `Spacecraft` (ground truth schema). Had that row said `Body` --> `CelestialBody` (ground truth "
             "schema), none of the 9 would have happened. So that row of the translation table is the "
             "likely mistake, and the one to check.", ""]
    if not mismatches:
        return lines + ["None.", ""]
    lines += ["| Kind | Component class in the current schema | Translated to (ground truth schema) | What the ground truth "
              "triple says instead (ground truth schema) | Times | Check |", "|---|---|---|---|---:|---|"]
    for c in mismatches[:SHOW]:
        to = "(none)" if c["translated_to"].endswith(pairing.NO_TRANSLATION) else c["translated_to"]
        check = (f"swap_subject_and_object of {c['crt_component_class']} (current schema): subject and object were the "
                 f"other way round" if c["swapped"] else
                 f"should {c['crt_component_class']} (current schema) translate to {c['gtt_component_class']} (ground truth schema)?")
        lines.append(f"| {c['kind']} | {cell(c['crt_component_class'])} | {cell(to)} | {cell(c['gtt_component_class'])} | {c['count']} "
                     f"| {cell(check)} |")
    if len(mismatches) > SHOW:
        lines.append(f"| … {len(mismatches) - SHOW} more, in `{METRICS_NAME}` | | | | | |")
    return lines + [""]


def results(evaluated, translation, metrics, calls, settings, output) -> Results:
    schema_file = evaluated.schema_used.get("made", {}).get("schema", "?")
    looks = _log_look(evaluated, translation, schema_file) if settings["evaluate_held_out"] else None
    per_record_path, compared_path, metrics_path = (output / PER_RECORD_NAME, output / COMPARED_NAME,
                                                  output / METRICS_NAME)
    # Only the parts whose numbers are shown: the held-out records' triples stay
    # unseen too, unless --evaluate_held_out true.
    shown = [r for r in evaluated.records if r["part"] in metrics]
    tuning = [r for r in shown if r["part"] == "tuning"]
    # Mismatches say which rows of the translation table to change, so they come from tuning records only: changing
    # a row because of a held-out record would let the held-out records influence the pipeline.
    mismatches = pairing.component_class_mismatches(tuning)
    unreviewed = sum(r["compared"]["partial_review"]["unreviewed"] for r in tuning)
    rejected = sum(r["compared"]["partial_review"]["rejected"] for r in tuning)
    compared_rows = _compared_rows(shown)
    write_text(per_record_path, _per_record(shown, len(evaluated.records) - len(shown)))
    write_csv(compared_path, COMPARED_COLUMNS, compared_rows)
    write_json(metrics_path, {
        "made": {"run_id": audit.current_run_id(), **llm.describe(), "schema": schema_file, "settings": settings,
                 "min_records_for_margin": stats.MIN_RECORDS, "redraws": stats.REDRAWS, "seed": stats.SEED},
        "evaluated": {p: [r["id"] for r in evaluated.records if r["part"] == p] for p in ("tuning", "held-out")},
        "left_out": evaluated.left_out,
        "learned_from": evaluated.learned_from,
        "parts": {p: {"numbers": v["numbers"], "strata": v["strata"], "margin_checks": v["margin_checks"],
                      "per_component_class": v["per_component_class"], "per_record": v["per_record"],
                      "removed_by_060": v["removed_by_060"],
                      "twins": v["twins"],
                      "describes_confusion": [{"truth": t, "said": s, "records": n}
                                              for (t, s), n in v["confusion"].items()]}
                  for p, v in metrics.items() if p != "kept_aside"},
        "held_out_looks": looks and {"count": looks["count"], "changed_since_previous": looks["changed"]},
        "component_class_mismatches": mismatches,
        "translation_suggestions": translation.suggested,
        "partial_pairs_tuning": {"unreviewed": unreviewed, "rejected_by_review": rejected},
    })
    log.info(f"  wrote {METRICS_NAME}, {PER_RECORD_NAME}, {COMPARED_NAME}")
    kept_path = _keep_evaluation(evaluated, translation, output, tuning, evaluated.extraction_manifest)
    log.info(f"  kept this run's tuning counts in {EVALUATIONS_DIR}/{kept_path.name}")

    warnings = list(evaluated.notes)
    for part, v in metrics.items():
        if part == "kept_aside" or v["numbers"] is None:
            continue
        n = v["numbers"]
        drifted = [g for g in v["strata"]
                   if g["share_evaluated"] is not None and abs(g["share_evaluated"] - g["share_pool"]) > stats.SHARE_GAP]
        if not n["margins"]:
            warnings.append(f"The {part} part: only {n['records']} record(s) evaluated, fewer than {stats.MIN_RECORDS}, "
                            f"so its numbers are shown without a margin of error, and are too few to draw conclusions "
                            f"from. Draft (`py 050_annotate/run.py`) and finish (`py helpers/annotate.py`) more "
                            f"records of the pool, in order, run "
                            f"`py 060_extract/run.py`, {AGAIN} Until then, read {repo_path(per_record_path)} rather "
                            f"than the numbers.")
        elif drifted:
            warnings.append(f"The {part} part: {len(drifted)} stratum(s) whose proportion of the evaluated records differs "
                            f"from its proportion of the pool by more than {100 * stats.SHARE_GAP:.0f} points: "
                            + named([f"{g['stratum']} ({readings.pct(g['share_evaluated'])} of the evaluated records, "
                                     f"{readings.pct(g['share_pool'])} of the pool)" for g in drifted], 5, "; ")
                            + ". The numbers lean toward the strata whose proportion of the evaluated records is above their proportion of the pool, by chance (the fair "
                              "sample is random). Nothing to do: the gap usually shrinks as more records are "
                              f"evaluated; read the numbers with it in mind ({this_report()}, section *Results*, "
                              f"subsection *Metrics: {part} part*, table *Per stratum*).")
        checks = v["margin_checks"]
        if checks and (checks["at_bound"]
                       or (checks["catalog_proportion"] or 0) > stats.FINITE_NEGLIGIBLE):
            share = checks["catalog_proportion"] or 0
            why = []
            if checks["at_bound"]:
                why.append(f"the range of {named(checks['at_bound'], 5)} reaches 0% or 100%, where a percentile range "
                           f"is too narrow (more evaluated records make this rarer)")
            if share > stats.FINITE_NEGLIGIBLE:
                why.append(f"{readings.pct(share)} of the catalog is evaluated, above "
                           f"{100 * stats.FINITE_NEGLIGIBLE:.0f}%, so the ranges come out somewhat too wide (nothing "
                           f"to do: they err on the safe side)")
            warnings.append(f"The {part} part: an assumption of the margin of error doesn't hold, so some ranges are "
                            f"less trustworthy: {'; and '.join(why)}. Details: {this_report()}, section *Results*, subsection *Metrics: {part} part*, table *The margin of error's "
                            f"assumptions, checked*.")
    if translation.suggested:
        warnings.append(f"The model suggests {len(translation.suggested)} row(s) of annotations/component_class_mapping.csv that say (none) may "
                        f"now have a counterpart in the ground truth schema: "
                        + named([f"{s['component_class_from_past_or_crt_schema']} (current schema) --> {s['component_class_in_gtt']} "
                                 f"(ground truth schema)" for s in translation.suggested], 5, "; ")
                        + f". While a row says (none), the occurrences of extracted triples that use its component class can't form "
                          f"pairs (a predicate) or strict pairs (an entity class). Rows aren't changed: check them "
                          f"({TABLE}, shows the suggestion), take the suggestion if right, else keep (none); {AGAIN}")
    if translation.outdated:
        warnings.append(f"{len(translation.outdated)} row(s) of annotations/component_class_mapping.csv translate to (none) though the ground "
                        f"truth schema now has the same component class: {named(translation.outdated, 5, '; ')}. Probably out of "
                        f"date, and the occurrences of extracted triples that use those component classes can't form pairs (a predicate) "
                        f"or strict pairs (an entity class). Check them ({TABLE}, marked *now exists*); keep (none) "
                        f"only if the ground truth schema's component class means something else; {AGAIN}")
    if unreviewed:
        waiting = [r["id"] for r in tuning if r["compared"]["partial_review"]["unreviewed"]]
        warnings.append(f"{unreviewed} partial pair(s) of the tuning part aren't reviewed yet, in {len(waiting)} "
                        f"record(s): {named(waiting)}. So the partial level may count pairs that aren't the same fact "
                        f"(e.g. MODIS vs MODIS Terra). Review them (`py helpers/annotate.py`, view *Partial pairs*), "
                        f"{AGAIN}")
    if evaluated.review_problems:
        warnings.append(f"{len(evaluated.review_problems)} row(s) of annotations/partial_pair_reviews.csv have a "
                        f"verdict that is neither \"same fact\" nor \"not the same fact\" (case aside), so they are "
                        f"ignored: {named(evaluated.review_problems, 5, '; ')}. Fix each verdict in that file, or delete "
                        f"the row and review the pair again (`py helpers/annotate.py`, view *Partial pairs*), {AGAIN}")
    not_applying = [(r["id"], k) for r in tuning for k in r["compared"]["partial_review"]["not_applying"]]
    if not_applying:
        warnings.append(f"{len(not_applying)} verdict(s) of annotations/partial_pair_reviews.csv, on tuning records "
                        f"evaluated now, no longer match a partial pair (a ground truth triple, an extracted triple, or "
                        f"a row of the translation table changed since), so they apply to nothing: "
                        + named([f"record {rid}: {k[1]} {k[2]} {k[3]} / {k[4]} {k[5]} {k[6]}" for rid, k in not_applying],
                                5, "; ")
                        + ". Nothing to do if that change was meant: any pair it made is counted as not reviewed. "
                          "To tidy the file, delete those rows.")
    frequent = [c for c in mismatches if c["count"] >= pairing.MISMATCH_WARN]
    if frequent:
        warnings.append(f"{len(frequent)} component class mismatch(es) seen {pairing.MISMATCH_WARN} or more times where extraction "
                        f"stated the fact but a component class differed: "
                        + named([f"{c['kind']} {c['crt_component_class']} (current schema) --> "
                                 + ("(none)" if c["translated_to"].endswith(pairing.NO_TRANSLATION)
                                    else f"{c['translated_to']} (ground truth schema)")
                                 + f", where the ground truth triple says {c['gtt_component_class']} (ground truth "
                                   f"schema), {c['count']} times" for c in frequent], 5, "; ")
                        + f". A row of annotations/component_class_mapping.csv may translate wrong, to (none) when a "
                          f"component class fits, or with the wrong swap_subject_and_object, which leaves stated facts "
                          f"ground truth only. Check those rows ({TABLE}), keep a row that is right, {AGAIN} Details: {this_report()}, section *Results*, subsection "
                          f"*Component class mismatches*.")
    if looks is not None:
        warnings.append(f"The held-out part was looked at: {looks['count']} time(s) so far, each logged in "
                        f"annotations/held_out_looks.csv. {readings.since_previous(looks)} A change made after a look "
                        f"lets the held-out records influence the pipeline, and then their numbers flatter it. Commit "
                        f"annotations/held_out_looks.csv, so every look stays counted.")
    missing = check_origins(compared_rows, "compared triples")
    if missing:
        warnings.append(missing)

    lines = ["### What this run worked on", "",
             f"Current schema (the one 060 used): `{schema_file}`, translated to the ground truth schema "
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
              "Rows of `annotations/component_class_mapping.csv` that say `(none)`, and component classes of the ground truth schema "
              "that no row translates to. The ground truth schema grows as you annotate: if a `(none)` row "
              "should now point to one of its component classes, fix that row (`py helpers/annotate.py`, view "
              "*Translation table*).", "",
              "| Kind | Current schema's component classes translated to (none) | Ground truth schema's component classes nothing "
              "translates to |", "|---|---|---|"]
    lines += [f"| {kind} | {cell(named(translation.to_none[kind], 20)) or '–'} | {cell(named(translation.untranslated[kind], 20)) or '–'} |"
              for kind in ("entity class", "predicate")]
    lines.append("")
    merged = [(kind, mine, theirs) for kind in ("entity class", "predicate")
              for mine, theirs in translation.merged[kind].items()]
    if merged:
        lines += ["Component classes of the ground truth schema that two or more of the current schema's component classes translate "
                  "to: the ground truth doesn't tell those component classes of the current schema apart, so neither can these metrics "
                  "(a mix-up between them costs extraction nothing). If the difference matters, make it in the "
                  "ground truth.", "",
                  "| Kind | Component class in the ground truth schema | Current schema's component classes that translate to it |",
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
                  f"{n['extracted']} occurrences)", ""]
        if not n["margins"]:
            lines += [_too_few(n), ""]
        part_records = [r for r in evaluated.records if r["part"] == part]
        lines += per_text_table("Per text", [("ground truth triples", [len(r["gt"]) for r in part_records]),
                                             ("occurrences (translated extracted triples)",
                                              [len(r["compared"]["translated"]) for r in part_records])])
        lines += ["", "One text is one evaluated record's text; describes triples aren't counted.", ""]
        lines += ["| Pair level | | Precision | Recall | F1 |", "|---|---|---:|---:|---:|"]
        for level in pairing.LEVELS:
            L = n[level]
            lines.append(f"| {level} | all pairs | {_with_margin(L['precision'])} | {_with_margin(L['recall'])} "
                         f"| {_with_margin(L['f1'])} |")
            lines.append(f"| {level} | strict pairs (entity classes too) | {_with_margin(L['strict_precision'])} "
                         f"| {_with_margin(L['strict_recall'])} | {_with_margin(L['strict_f1'])} |")
        recs = [r for r in evaluated.records if r["part"] == part]
        pr = {k: sum(r["compared"]["partial_review"][k] for r in recs) for k in ("unreviewed", "rejected")}
        lines += ["", (f"Partial pairs in these numbers not reviewed yet: {pr['unreviewed']}; pairs your review "
                       f"ruled out (\"not the same fact\"): {pr['rejected']}. Review them in `py helpers/annotate.py`, view "
                       f"*Partial pairs*." if part == "tuning" else
                       "Partial pairs of the held-out part are never reviewed (that would mean looking at it), "
                       "so its partial level may count pairs that aren't the same fact.")]
        lines += ["", "| Pair level | Entity-class accuracy | Subject-class accuracy | Object-class accuracy | "
                      "Recall within reach | Strict recall within strict reach |", "|---|---:|---:|---:|---:|---:|"]
        lines += [f"| {level} | {_with_margin(n[level]['entity_class_accuracy'])} | "
                  f"{_with_margin(n[level]['subject_class_accuracy'])} | "
                  f"{_with_margin(n[level]['object_class_accuracy'])} | "
                  f"{_with_margin(n[level]['recall_within_reach'])} | "
                  f"{_with_margin(n[level]['strict_recall_within_reach'])} |" for level in pairing.LEVELS]
        d = n["describes"]
        lines += ["", f"- **Recall upper bound** (the ground truth triples within reach: the most recall "
                      f"can be): {_with_margin(n['recall_upper_bound'])}. **Strict recall upper bound** (the ground "
                      f"truth triples within strict reach: the most strict recall can be): "
                      f"{_with_margin(n['strict_recall_upper_bound'])}.",
                  f"- **Describes accuracy**: right for {_with_margin(d['accuracy'])} of {d['records']} "
                  f"record(s). **Describes baseline** (always naming the most common describes class): "
                  f"{readings.pct(d['majority_baseline'])}; **describes per-entity-class average**: "
                  f"{readings.pct(d['per_entity_class_average'])}.", ""]
        if v["confusion"]:
            lines += ["| The ground truth says (ground truth schema) | Extraction said (translated into the ground "
                      "truth schema) | Records |", "|---|---|---:|"]
            lines += [f"| {cell(t)} | {cell(s)} | {k} |" for (t, s), k in sorted(v["confusion"].items())]
            lines.append("")
        lines += readings.readings(part, n, recs, evaluated, translation, looks, v["confusion"])
        lines += ["#### Per stratum", "", f"Numbers once a stratum has {stats.MIN_RECORDS} records; with many strata, "
                  f"about 1 in 20 margins misses by chance, so one odd stratum is not a finding.", "",
                  "| Stratum | Records | Proportion of the evaluated records | Proportion of the pool | Precision (exact) | Recall (exact) |",
                  "|---|---:|---:|---:|---:|---:|"]
        for g in v["strata"]:
            gn = g["numbers"]
            lines.append(f"| {cell(g['stratum'])} | {g['records']} | {readings.pct(g['share_evaluated'])} | {readings.pct(g['share_pool'])} "
                         f"| {_with_margin(gn['exact']['precision']) if gn else 'too few'} "
                         f"| {_with_margin(gn['exact']['recall']) if gn else 'too few'} |")
        lines.append("")
        lines += _per_component_class_lines(n, v["per_component_class"])
        lines += _per_record_lines(v["per_record"])
        lines += _removed_lines(n["records"], v["removed_by_060"])
        lines += _twin_lines(part, v, recs, evaluated.learned_from)
        lines += _margin_check_lines(v["margin_checks"])
    lines += ["A margin of error covers only which records happened to be evaluated: not mistakes in the ground "
              "truth, not the model answering differently on another run, and not changes made while looking at "
              "these records. The metrics assume the ground truth lists every fact the records state.", "",
              f"Every record's ground truth triples and occurrences, side by side: `{PER_RECORD_NAME}`; one row per "
              f"pair, per occurrence left extracted only, and per ground truth triple left ground truth only: "
              f"`{COMPARED_NAME}`; "
              f"every number: `{METRICS_NAME}`.", ""]
    lines += model_calls([("stage 2: propose component class translations (one call)", translation.calls,
                           translation.reused),
                          ("stage 2: suggest counterparts for (none) rows (one call)", translation.suggest_calls,
                           translation.suggest_reused)],
                         calls.paid.test_calls, llm.model_label())

    tuning = metrics.get("tuning", {}).get("numbers")
    headline = {}
    if tuning:
        headline = {"precision (tuning, exact)": readings.pct(tuning["exact"]["precision"]["value"]),
                    "recall (tuning, exact)": readings.pct(tuning["exact"]["recall"]["value"]),
                    "pooled over": f"{tuning['records']} records ({POOLED})"}
        twins = metrics["tuning"]["twins"]
        headline["twins (tuning)"] = ("not known" if twins is None else
                                      f"{len(twins['records'])} of {tuning['records']} evaluated")
    return Results(files=[metrics_path, per_record_path, compared_path, kept_path], headline=headline,
                   details="\n".join(lines), warnings=warnings)
