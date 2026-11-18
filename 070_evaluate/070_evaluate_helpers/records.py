"""
records.py -- stage 1: which records are evaluated, and what is known about
each.

Evaluation refuses to run while the ground truth has the same classed triple
twice in a record (common/common_helpers/ground_truth.py, gt.repeats, compared by
the key the exact pairs use), or while a finished record, or a fact that waits on
an expert, isn't fit to evaluate against (common.ground_truth.evaluable_problems:
a row error of its own, such as a source text not in the record's text or a second
describes triple; an entity class or predicate the ground truth schema lacks, which
stage 2 can't translate into). Both stop before anything is shown or asked, naming
each file and line, and what to do. Every
other warning found here (ground truth problems, records left out, …) is
shown before anything is evaluated, and the person is asked whether to go
ahead (unless confirm_paid_calls is false).

A record is evaluated when a person has finished it in the ground truth
(all_facts_extracted = 1 on every row) AND step 060's last run chose it: it
extracted from it, or its model calls failed for it (cut off, refused, a failed
call: its details file says so). A failed record is scored as extracting
nothing (FAILED_TO_DO): its ground truth triples count against recall, it adds
no occurrence, and its describes triple counts as not named, as an evaluation
of extraction counts a system's missing output (docs/improvements.md,
2026-11-17). Of those, only the FAIR SAMPLE is evaluated: for EACH PART of the
pool (tuning, held-out) separately, the longest run of that part's first
records (in pool order) that are all evaluated. The pool is shuffled, so its order restricted to
one part is still random, and that run is a fair sample of the part (and the two
runs together of the catalog), which the margins of error require (see stats.py).
An unfinished record of one part never holds back the other part. A record after
a gap in its own part (an unfinished record, or one 060's run didn't choose,
before it) or not in the pool at all (hand-picked) is left out and listed, with
what to do. With evaluate_held_out true, the step stops before anything is
evaluated when a finished held-out record is missing from 060's run for any
reason but a recorded failure (held_out_gap), unless the setting
evaluate_held_out_incomplete is true.

For each evaluated record: its pool position, its part (tuning or held-out,
from 030), its stratum (from the pool file), its title, its ground
truth triples and describes triple, 060's extracted triples and describes triple,
how many items 060's checks removed from it, per reason (extracted_triples_removed.csv),
and its twin kind (docs/terminology.md, twin): what it shares with a record
the current schema was learned from (060's schema_used.json, learned_from),
"" when it isn't a twin, None when that isn't known; and its facts that wait on
an expert (annotations/pending_triples.csv, read and checked against
annotations/left_out.md by common.left_out.read_pending): pairing.py pairs
what is left of its occurrences with them, so that an occurrence matching one
isn't counted against precision.
"""
from __future__ import annotations

import collections
from dataclasses import dataclass, field
from pathlib import Path

from common.audit import ref_path
from common.files import read_csv, read_json
from common.ground_truth import (ANNOTATED, BAD_MARK, EVALUABLE, HELD_OUT, IN_TWO_FILES, TO_FIX, TUNING, UNFINISHED,
                                 evaluable_problems, fair_prefix, pool_parts, read_ground_truth, read_pool,
                                 record_skipped, twin_kinds)
from common.left_out import read_pending
from common.llm import confirm, numbered, show_warnings
from common.partial_reviews import read_reviews, record_unused, review_problems
from common.records_io import has_text, load_records
from common.second_opinion import groups_of, key_of, read_table as read_second_opinion, repeats_of
from common import dropped
from common.report import named
from common.schema_io import parse_source, read_ground_truth_schema
from common.step import MANIFEST_NAME, Spec, check_settings, input_files, repo_path
from common.stop import Stop
from common.triples_io import canonical_row, is_describes

AGAIN = "then run `py 070_evaluate/run.py` again."
#: The stage name its discarded items carry (common/common_helpers/dropped.py).
STAGE = "stage 1 (pick_records)"


@dataclass
class Evaluated:
    records: list = field(default_factory=list)    # see pick_records
    left_out: dict = field(default_factory=dict)   # {reason: [ids]}
    notes: list = field(default_factory=list)      # shown (and asked about) before evaluating, and in the report
    pool: list = field(default_factory=list)       # the pool's ids, in order
    pool_strata: dict = field(default_factory=dict)  # {stratum: pool records in it}
    ground_truth: object = None                    # common.ground_truth.GroundTruth
    schema_used: dict = field(default_factory=dict)  # 060's schema_used.json
    unfinished: int = 0                            # ground truth records not finished yet
    reviews: dict = field(default_factory=dict)    # a person's verdicts on partial pairs (common/common_helpers/partial_reviews.py)
    review_problems: list = field(default_factory=list)  # rows of that file whose verdict is neither of the two
    extraction_made: dict = field(default_factory=dict)  # 060's run: run id, model, settings (from its details file)
    catalog_records: int = 0                       # records in 020's records.jsonl: the whole catalog
    learned_from: dict = field(default_factory=dict)  # the records the current schema was learned from (060's schema_used.json)
    extraction_manifest: dict = field(default_factory=dict)  # 060's _manifest.json: its run's code version, settings, prompts, inputs
    extraction_failed: list = field(default_factory=list)  # evaluated records 060's model calls failed for, with why,
                                                   # reason and maintainer (common/common_helpers/dropped.py); each
                                                   # scored as extracting nothing
    chosen_by_060: int = 0                         # finished ground truth records 060's run chose (extracted or failed)
    finished: list = field(default_factory=list)   # the finished ground truth records, {"id", "maintainer"}
    held_out_only: dict = field(default_factory=dict)  # the ground truth schema's held-out-only entries, by kind
                                                   # (schema_io: {"entity_classes": set, "predicates": set})
    pending: list = field(default_factory=list)    # every row of annotations/pending_triples.csv (read_pending): the
                                                   # facts that wait on an expert, of every record, evaluated or not
    second_opinion_models: list = field(default_factory=list)  # the models whose second opinion checked an evaluated
                                                   # record (annotations/second_opinion.csv, column model)


def _triples(rows: list) -> tuple:
    """(triples, describes triple or None): rows with subject, predicate, and object, each tidied as every row is
    (common.triples_io.canonical_row). A ground truth record has one describes triple at most (a second one is an
    error that stops 070: common.ground_truth.evaluable_problems); 060 writes one for each record."""
    triples, describes = [], None
    for r in (canonical_row(r, blank="") for r in rows):
        if not (r.get("subject") and r.get("predicate") and r.get("object")):
            continue                                   # "annotated, states no triples"
        if is_describes(r):
            describes = describes or r
        else:
            triples.append(r)
    return triples, describes


def _record_rows(rid: str, rows: list, side: str) -> None:
    """One entry per row of a record that _triples doesn't keep, with _triples' own tests: a row with some but not all
    of subject, predicate and object (a row with none is a record's "states no triples" row, no triple), or a second
    describes triple (folded into the first); then the record's accounting check. side: "ground truth" or
    "extracted"."""
    since, describes, kept, empty = dropped.mark(), None, 0, 0
    for r in (canonical_row(r, blank="") for r in rows):
        filled = [k for k in ("subject", "predicate", "object") if r.get(k)]
        if len(filled) < 3:
            if filled:
                dropped.discard(STAGE, "classed triple", f"a row of the {side} triples without its "
                                + ", ".join(k for k in ("subject", "predicate", "object") if k not in filled)
                                + ": not a triple, so not evaluated", _row_item(r), record_id=rid,
                                where=r.get("origin") or f"#{r.get('_position', '')}")
            else:
                empty += 1
        elif is_describes(r) and describes is not None:
            dropped.fold(STAGE, "describes triple", f"a second describes triple among the {side} triples: the first "
                         "is the one evaluated", _row_item(r), _row_item(describes), record_id=rid)
        else:
            describes = describes or (r if is_describes(r) else None)
            kept += 1
    dropped.account(STAGE, f"{side} rows of record {rid}", len(rows), kept + empty, since=since)


def _row_item(r: dict) -> dict:
    """A row as a discarded item: its classed triple and source text."""
    return {k: r.get(k, "") for k in ("subject", "subject_class", "predicate", "object", "object_class", "source_text")}


def refusal(repeats: list) -> str:
    """Why evaluation can't run: every classed triple that appears more than
    once in a record (common.ground_truth's gt.repeats), numbered."""
    n = len(repeats)
    how_often = "twice" if all(r["copies"] == 2 for r in repeats) else "more than once"
    head = (f"Step 070 can't evaluate: {n} classed triple{'s' if n != 1 else ''} "
            f"{'appear' if n != 1 else 'appears'} {how_often} in a record of the ground truth, and only one "
            f"copy could be paired.")
    return head + "\n" + numbered([r["message"][0].upper() + r["message"][1:] for r in repeats])



def check_evaluable(gt, catalog: dict, ground_truth_schema_path, pending: list = (), pool_rows: list = ()) -> None:
    """Stop unless every finished record (EVALUABLE, every part) and every fact that waits on an expert is fit to
    evaluate against (common.ground_truth.evaluable_problems), and the held-out-only entries keep their rule
    (common.ground_truth.held_out_only_problems; pool_rows give each pool position its part): each problem named with
    its file and line, the record, and what to do. Only the finished records are evaluated, so only theirs are
    checked."""
    path = ref_path(Path(ground_truth_schema_path))
    parts = {r["position"]: r.get("part") for r in pool_rows} if pool_rows else None
    problems = evaluable_problems(gt, catalog, read_ground_truth_schema(ground_truth_schema_path), path, pending,
                                  parts=parts)
    if problems:
        raise Stop(f"Step 070 can't evaluate: the finished records of the ground truth, or the facts that wait on an "
                   f"expert, have {len(problems)} problem(s), each of which would make a number wrong:\n"
                   + numbered(problems) + f"\nFix each one, {AGAIN}")


def held_out_sources(ground_truth_schema_path, pool_rows: list) -> list:
    """The ground truth schema's entity classes and predicates whose "source:" line names a held-out record without
    the held-out only mark, i.e. that were added from held-out records unmarked, so they reach every model and check
    (annotations/guidelines.md, Before you start): [(kind, component class, source, [(pool position, record id)])]. A
    held-out-only entry is skipped: its source names held-out records on purpose (docs/terminology.md); one unmarked
    since keeps its held-out records in its source too, so it is listed, for its definition to be read again.
    Read by common.schema_io.parse_source: a position counts as held-out by its part in the pool, whatever word stands
    before it ("ground truth tuning #12, #8" names held-out #8 when #8 is held-out)."""
    held = {r["position"]: r["id"] for r in pool_rows if r.get("part") == HELD_OUT}
    parts = {r["position"]: r.get("part") for r in pool_rows}
    schema = read_ground_truth_schema(ground_truth_schema_path)
    sources, marked = schema["sources"], schema["held_out_only"]
    found = []
    for section, kind in (("entity_classes", "entity class"), ("predicates", "predicate")):
        for name, source in sources[section].items():
            if name in marked[section]:
                continue
            records = [(n, held[n]) for n in parse_source(source, parts)["held_out"]]
            if records:
                found.append((kind, name, source, records))
    return found


def _mark_twins(evaluated: Evaluated, catalog: dict, inputs: dict) -> None:
    """Each evaluated record's "twin": its twin kind against the records the current schema was learned from
    (common.ground_truth.twin_kinds), "" when it isn't a twin, None when that isn't known (a note says why, and
    what to do)."""
    learned = evaluated.schema_used.get("learned_from") or {}
    evaluated.learned_from = learned
    if not learned.get("known"):
        why = (learned.get("how") or [f"{repo_path(inputs['schema_used'])} doesn't say (an older step 060 wrote it)"])[0]
        evaluated.notes.append(f"Which records the current schema was learned from isn't known: {why}. So 070 can't "
                               f"tell which evaluated records are twins (the same title, the same `notes`, or both as a record"
                               f"the schema was learned from; docs/terminology.md, section *Evaluating extraction*), and gives no "
                               f"numbers without them. To get them, extract with the induced schema or the ground truth schema "
                               f"(`py 060_extract/run.py`), then run `py 070_evaluate/run.py` again.")
        for r in evaluated.records:
            r["twin"] = None
        return
    kind = twin_kinds({r["id"]: catalog.get(r["id"], {}) for r in evaluated.records},
                       {i: catalog[i] for i in learned["ids"] if i in catalog})
    for i in learned["ids"]:
        if i not in catalog:
            dropped.discard(STAGE, "record", "the current schema was learned from it, but it isn't in 020's records, so "
                            "no evaluated record is compared with it for twins", {"id": i}, record_id=i)
    for r in evaluated.records:
        r["twin"] = kind[r["id"]]


def _first_gap(order: list, part: str, positions: dict, taken: set, gt, without_text=frozenset()) -> str:
    """The first record of one part (`order`: that part's ids in pool order) that is not taken, why (its state in the
    ground truth, gt.state; or no text: without_text, the pool records common.records_io.has_text is false for, which
    050 and 060 skip, so it can never be finished or extracted), and what brings it in (for messages); "" if none."""
    gap = next((rid for rid in order if rid not in taken), None)
    if gap is None:
        return ""
    where = f"pool position #{positions[gap]} (`{gap}`)"
    head = f"The first {part} record missing from the fair sample of the {part} part is {where}"
    if gap in without_text:
        return (f"{head}: it has no text (no title, notes or other text field), so 050 and 060 skip it and it can "
                f"never be finished or extracted: it ends the fair sample of the {part} part for good, and the {part} "
                f"records after it can't be evaluated. Nothing to do here; 020's report counts such records")
    state = gt.state(gap)
    if gt.records.get(gap, {}).get("finished"):
        return (f"{head}: finished, but not chosen by 060's last run (it neither extracted from it nor recorded a "
                f"failure for it). Run `py 060_extract/run.py` so that it chooses that record (its setting ids, or "
                f"extract_from)")
    if state == IN_TWO_FILES:
        return (f"{head}: in {' and '.join(gt.records[gap]['files'])}, annotated twice. Delete its rows from all "
                f"files but one (by hand), finish it in `py helpers/annotate.py`, run `py 060_extract/run.py`")
    if state == BAD_MARK:
        return (f"{head}: its all_facts_extracted is neither 0 nor 1 on some row. Tick *All facts extracted* on it in "
                f"`py helpers/annotate.py` if every fact is there, run `py 060_extract/run.py`")
    if state == UNFINISHED:
        return f"{head}: not finished in the ground truth. Finish it in `py helpers/annotate.py` (tick *All facts extracted*), run `py 060_extract/run.py`"
    return (f"{head}: not in the ground truth yet. Draft it with "
            f"`py 050_annotate/run.py` (set --part {part}), correct and finish it in `py helpers/annotate.py`, run `py 060_extract/run.py`")


#: What a failed extraction means for this evaluation, and what to do, by its reason (a key of common.dropped.KINDS):
#: the 070 counterpart of dropped.TO_DO, which speaks of the step whose call failed. A record 060's model calls failed
#: for is scored as extracting nothing (module docstring); whether running 060 again can change that depends on why.
FAILED_TO_DO = {
    "cut_off": "the answer reached the answer limit 060's run sent ({limit}). Running `py 060_extract/run.py` again "
               "at that limit only repeats the cut (060 keeps the cut-off in its cache and doesn't ask again), so "
               "these records stay scored as extracting nothing for this recipe. A higher answer limit "
               "(MAX_ANSWER_TOKENS in common/common_helpers/llm.py) or a lower thinking setting (--thinking) asks "
               "them again, and is then a different recipe, to be compared as one",
    "refused": "the model or its service declined to answer. Asking again gets the same answer, so these records "
               "stay scored as extracting nothing: the refusal is part of what this model does with them",
    "malformed": "the reply wasn't in the required shape, even when asked again. Run `py 060_extract/run.py` again "
                 "(only these records are asked again; every other answer comes from its cache), then "
                 "`py 070_evaluate/run.py`",
    "service_error": "the model's service returned an error. Run `py 060_extract/run.py` again (only these records "
                     "are asked again; every other answer comes from its cache), then `py 070_evaluate/run.py`",
    "other": "another error (060's run log gives it). Run `py 060_extract/run.py` again (only these records are "
             "asked again), then `py 070_evaluate/run.py`",
}


def failed_note(failed: list, evaluated_count: int, limit) -> str:
    """The warning on the evaluated records whose extraction failed: how many of the records evaluated, by reason,
    which, how they are scored, and what to do for each reason (FAILED_TO_DO). failed: entries {"id", "reason",
    "maintainer"}; limit: the answer limit 060's run sent (its details file), or None."""
    by_reason = {}
    for e in failed:
        by_reason.setdefault(e["reason"], []).append(e["id"])
    reasons = "; ".join(f"{dropped.KINDS[k].split(':')[0]}: {len(ids)} ({named(ids, 5)}): "
                        + FAILED_TO_DO[k].format(limit=f"{limit:,} tokens" if isinstance(limit, int) else "not recorded")
                        for k, ids in by_reason.items())
    return (f"060's model calls failed for {len(failed)} of the {evaluated_count} record(s) evaluated, so each of "
            f"those {len(failed)} is scored as extracting nothing: its ground truth triples count against recall, it "
            f"adds no occurrence (so nothing to precision), and its describes triple counts as not named. By reason: "
            f"{reasons}. The report's section *Records whose extraction failed* lists them by reason and by "
            f"maintainer.")


def held_out_gap(order: list, finished: set, chosen: set, fair: set, positions: dict, forced, notes: list) -> str | None:
    """With evaluate_held_out true: why the step stops before a look at the held-out part, or None. It stops when a
    held-out record would be evaluated (a look would be logged) while a finished held-out record is missing from
    060's run for a reason other than a recorded failure (not chosen: a failure is scored, as extracting nothing),
    since such a look would count against the held-out part with fewer records than it has. forced (the setting
    evaluate_held_out_incomplete): the look goes ahead, and a note in notes names the records missing."""
    if not any(rid in fair for rid in order):
        return None
    missing = [rid for rid in order if rid in finished and rid not in chosen]
    if not missing:
        return None
    which = named([f"pool position #{positions[rid]} (`{rid}`)" for rid in missing], 10, "; ")
    if forced:
        notes.append(f"evaluate_held_out_incomplete is true, so this look at the held-out part goes ahead without "
                     f"{len(missing)} finished held-out record(s) that 060's last run didn't choose: {which}. The "
                     f"held-out numbers of this look cover only the held-out records before the first of them (the "
                     f"fair sample), and the look is logged as any other.")
        return None
    return (f"Step 070 stopped before looking at the held-out part: {len(missing)} finished held-out record(s) are "
            f"missing from 060's last run (it neither extracted from them nor recorded a failure for them): {which}. "
            f"A look now would be logged in annotations/held_out_looks.csv and count against the held-out part, while "
            f"its numbers lack those records (each look counts: docs/upkeep.md, *At the end: the held-out "
            f"part*). Nothing was evaluated and no look was "
            f"logged. Run `py 060_extract/run.py` so that it chooses every finished held-out record (e.g. "
            f"`--extract_from ground_truth`), then run `py 070_evaluate/run.py --evaluate_held_out true` again; or, to "
            f"look with those records missing on purpose, add `--evaluate_held_out_incomplete true`.")


def _read_pending(inputs: dict) -> list:
    """annotations/pending_triples.csv, checked against annotations/left_out.md (common.left_out.read_pending); a
    Stop naming the problem when either can't be read. No such input given (a caller other than run.py): none."""
    if "pending_triples" not in inputs:
        return []
    path, left_out = Path(inputs["pending_triples"]), Path(inputs["left_out"])
    for f in (path, left_out):
        if not f.is_file():
            raise Stop(f"{repo_path(f)} is missing, so 070 can't tell which extracted triples match facts that wait on "
                       f"an expert (they are left out of precision's denominator: "
                       f"070_evaluate/metrics/precision.md). Restore it from Git (`git checkout -- {repo_path(f)}`); "
                       f"a file with only its header line means no fact waits; {AGAIN}")
    try:
        return read_pending(path, left_out)
    except ValueError as e:
        raise Stop(f"The facts that wait on an expert can't be read, so 070 can't tell which extracted triples "
                   f"match them: {e}. Fix that line, {AGAIN}")


def _read_second_opinion(inputs: dict) -> dict:
    """annotations/second_opinion.csv (common.second_opinion.read_table): which ground truth triples a second,
    independent draft found. No such input given (a caller other than run.py), or no file: none, so every ground truth
    triple is "not checked". A file lacking a column stops the step, naming it."""
    if "second_opinion" not in inputs:
        return {}
    path = Path(inputs["second_opinion"])
    try:
        return read_second_opinion(path, stage=STAGE)    # a row with values but no id: recorded as discarded
    except ValueError as e:
        raise Stop(f"{repo_path(path)} can't be read, so 070 can't tell which ground truth triples the second opinion "
                   f"found: {e}. Restore its header line (`git checkout -- {repo_path(path)}` gives the file with its "
                   f"header only), or run `py helpers/second_opinion.py --apply true` to write it again, {AGAIN}")


def _note_second_opinion(evaluated: Evaluated, table: dict, inputs: dict) -> None:
    """The models whose second opinion checked an evaluated record, and a note on the rows of
    annotations/second_opinion.csv about evaluated records that match none of their ground truth triples (the triple
    was reworded or deleted since the second opinion was applied), so they count for nothing."""
    evaluated_ids = {r["id"] for r in evaluated.records}
    live = {key_of(r["id"], g) for r in evaluated.records for g in r["gt"]}
    stale = [row for k, row in table.items() if row["id"] in evaluated_ids and k not in live]
    evaluated.second_opinion_models = sorted({m for k, row in table.items() if row["id"] in evaluated_ids
                                              for m in row["by"]})
    for row in stale:
        dropped.discard(STAGE, "row of the second opinion table", "names a classed triple that is no longer a ground truth triple of "
                        "its record, so it counts for nothing", {k: v for k, v in row.items() if k != "_line"},
                        record_id=row["id"], where=f"{repo_path(Path(inputs['second_opinion']))}, line {row['_line']}")
    if stale:
        path = repo_path(Path(inputs["second_opinion"]))
        evaluated.notes.append(f"{len(stale)} row(s) of {path} name a classed triple that is no longer a ground truth "
                               f"triple of its record (reworded or deleted since the second opinion was applied), so "
                               f"they count for nothing, and the triple that replaced it counts as not checked: "
                               + named([f"line {r['_line']} (record {r['id']})" for r in stale], 5, "; ")
                               + ". Run `py helpers/second_opinion.py --apply true` (free: it calls no model; it matches the "
                                 "drafts already saved) to rewrite those records' rows, " + AGAIN)


#: The step's settings' rules (common.step.Spec); run_step checks them before any input is read, and so does
#: pick_records, with the same table (the shared settings' rules: common.step.shared_specs).
SPECS = {"evaluate_held_out": Spec(bool), "evaluate_held_out_incomplete": Spec(bool), "suggest": Spec(bool),
         "extraction_run": Spec(str)}

#: Step 070's four inputs from step 060: the files the setting extraction_run takes from one kept run of 060.
FROM_060 = ("extracted_triples", "extracted_triples_removed", "extracted_triples_details", "schema_used")
#: Where a kept run's four files are gathered beside its manifest when they aren't all in its own folder (in 070's
#: output folder): extractions/<060 run id>/.
EXTRACTIONS_DIR = "extractions"


def _check_named_run(settings: dict, said: dict) -> None:
    """With extraction_run set: Stop when a file read names another run of 060 as the one that wrote it (said: {file:
    the run id it records}; a file that records none is passed over), so a look and a recipe never name the wrong
    run. Found by the sha256 that run's manifest records, the files can't differ unless one was edited by hand."""
    named = str(settings.get("extraction_run") or "").strip()
    other = {f: r for f, r in said.items() if named and r and r != named}
    if other:
        raise Stop(f"--extraction_run {named} names the run of 060 to score, but "
                   + "; ".join(f"{f} says run {r} wrote it" for f, r in other.items())
                   + ". The files of one run name that run, so one of them was edited or copied by hand. Nothing was "
                     "evaluated. Restore 060's folder (outputs/intermediate_results/060_extract/) from a backup, or "
                     f"run `py 060_extract/run.py` again, {AGAIN}")


def extraction_inputs(inputs: dict, settings: dict, given: set) -> dict:
    """The inputs with 060's four files (FROM_060) taken from the run of 060 that the setting extraction_run names,
    each as that run wrote it (common.step.gather_run: by the sha256 its manifest records, in 060's live folder or
    previous_runs/), beside that run's own manifest, which pick_records reads from the folder of the extracted
    triples. An empty setting leaves the inputs as they are (060's latest run, or the files given). Stop when the
    run or one of its files isn't kept, or when one of the four files is also given on the command line (two
    answers to one question). given: the inputs given on the command line (run_step)."""
    run_id = str(settings.get("extraction_run") or "").strip()
    if not run_id:
        return inputs
    both = [k for k in FROM_060 if k in given]
    if both:
        raise Stop(f"--extraction_run {run_id} names the run of 060 to score, and "
                   f"{', '.join(f'--{k}' for k in both)} also give{'s' if len(both) == 1 else ''} "
                   f"{'one of its files' if len(both) == 1 else 'some of its files'}, so which to score is unclear. "
                   f"Nothing was evaluated. Give the run alone (its four files are found by the sha256 its manifest "
                   f"records), or the four files alone, without --extraction_run, {AGAIN}")
    from common.step import RESULTS_DIR, gather_run
    output = Path(inputs[FROM_060[0]]).parent                    # 060's output folder (the four inputs' default)
    files = gather_run(output, run_id, [Path(inputs[k]).name for k in FROM_060],
                       RESULTS_DIR / "070_evaluate" / EXTRACTIONS_DIR, again=AGAIN)
    return {**inputs, **{k: files[Path(inputs[k]).name] for k in FROM_060}}


def _record_not_evaluated(gt, evaluated: Evaluated, not_chosen: list, outside: list, extracted: dict, catalog: dict,
                          since: int) -> None:
    """One entry per record of the ground truth this run doesn't evaluate, with why (not finished; finished, but
    060's last run didn't choose it; outside the fair sample), and per record
    060 extracted from that isn't in the ground truth; then the accounting check: records in the ground truth =
    records evaluated + records recorded here."""
    annotated = set(gt.select(ANNOTATED).ids)
    for rid in gt.select(TO_FIX).ids:
        dropped.discard(STAGE, "record", f"not finished in the ground truth (its state: {gt.state(rid)}), so not "
                        "evaluated", {"id": rid, "title": (catalog.get(rid) or {}).get("title")}, record_id=rid)
    for rid in not_chosen:
        dropped.discard(STAGE, "record", "finished, but not chosen by 060's last run, so not evaluated",
                        {"id": rid, "title": (catalog.get(rid) or {}).get("title")}, record_id=rid)
    for rid in outside:
        dropped.discard(STAGE, "record", "outside the fair sample (after an unfinished record, or one 060's last run "
                        "didn't choose, of its own part of the pool, or not in the pool), so not evaluated",
                        {"id": rid, "title": (catalog.get(rid) or {}).get("title")}, record_id=rid)
    dropped.account(STAGE, "records in the ground truth", len(annotated), len(evaluated.records), since=since,
                    item_type="record", only=lambda e: e.get("record_id") in annotated)
    for rid, rows in extracted.items():
        if rid not in annotated:
            dropped.discard(STAGE, "record", "060 extracted from it, but it isn't in the ground truth, so its "
                            "extracted triples aren't evaluated", {"id": rid, "extracted triples": len(rows)},
                            record_id=rid)


def _record_repeated_candidates(inputs: dict) -> None:
    """One entry per row of the pool file whose id a later row lists again: the stratum of the last row is the one
    used."""
    rows = read_csv(Path(inputs["candidates"]))
    last = {r["id"].strip(): i for i, r in enumerate(rows)}
    for i, r in enumerate(rows):
        if last[r["id"].strip()] != i:
            dropped.fold(STAGE, "record", "listed again in the pool file: the stratum of its last row is used",
                         {"id": r["id"].strip(), "stratum": r.get("stratum")},
                         {"where": f"{repo_path(inputs['candidates'])}#{last[r['id'].strip()]}"},
                         record_id=r["id"].strip(), where=f"{repo_path(inputs['candidates'])}#{i}")


def pick_records(inputs: dict, settings: dict) -> Evaluated:
    check_settings(settings, SPECS)
    evaluated = Evaluated()
    gt_files = input_files(Path(inputs["ground_truth"]))
    pool_rows = read_pool(inputs["splits"])
    gt = evaluated.ground_truth = read_ground_truth(gt_files[0].parent, pool_rows)   # run_step made sure there is one
    evaluated.notes += [f"Ground truth, {p}" for p in gt.problems]
    record_skipped(STAGE, gt)
    if gt.repeats:
        raise Stop(refusal(gt.repeats))
    catalog = load_records(inputs["records"])
    evaluated.pending = _read_pending(inputs)
    check_evaluable(gt, catalog, inputs["ground_truth_schema"], evaluated.pending, pool_rows)
    if any("part" not in r for r in pool_rows):
        splits = repo_path(inputs["splits"])
        raise Stop(f"{splits} has no tuning / held-out part for its records (an older step 030 wrote it), so 070 "
                   f"can't keep the held-out part apart. Delete {splits}, run `py 030_split/run.py`, then run "
                   f"`py 070_evaluate/run.py` again.")
    evaluated.pool = [r["id"] for r in pool_rows]
    evaluated.held_out_only = read_ground_truth_schema(inputs["ground_truth_schema"])["held_out_only"]
    frozen = held_out_sources(inputs["ground_truth_schema"], pool_rows)
    if frozen:
        evaluated.notes.append(
            f"{len(frozen)} entity class(es) or predicate(s) of the ground truth schema "
            f"({ref_path(Path(inputs['ground_truth_schema']))}) were added from held-out records without the held-out "
            f"only mark, so every model and check sees them (annotations/guidelines.md, Before you start): "
            + named([f"{name} ({kind}; source: {source}; held-out "
                     + ", ".join(f"pool position {n} ({rid})" for n, rid in records) + ")"
                     for kind, name, source, records in frozen], 10, "; ")
            + ". So those held-out records shaped the ground truth schema, and their numbers may flatter the pipeline. "
              "If no tuning record uses the entry, mark it held-out only (a line \"held-out only\" under it in the "
              "file); if one does (it was unmarked for it), read its definition again, so that it says what the tuning "
              "record needs, not what the held-out record said; " + AGAIN)
    by_id = {r["id"]: r for r in pool_rows}
    strata = {r["id"].strip(): (r.get("stratum") or "").strip() for r in read_csv(Path(inputs["candidates"]))}
    _record_repeated_candidates(inputs)
    for r in pool_rows:
        g = strata.get(r["id"], "")
        evaluated.pool_strata[g] = evaluated.pool_strata.get(g, 0) + 1
    details = read_json(inputs["extracted_triples_details"])
    evaluated.extraction_made = details.get("made") or {}
    manifest = Path(inputs["extracted_triples"]).parent / MANIFEST_NAME
    evaluated.extraction_manifest = read_json(manifest) if manifest.is_file() else {}
    extracted_ids = {r["id"] for r in details["records"] if r["status"] == "extracted"}
    evaluated.schema_used = read_json(inputs["schema_used"])
    _check_named_run(settings, {"extracted_triples_details": evaluated.extraction_made.get("run_id"),
                                "schema_used": (evaluated.schema_used.get("made") or {}).get("run_id"),
                                MANIFEST_NAME: evaluated.extraction_manifest.get("run_id")})
    removed = {}
    for row in read_csv(Path(inputs["extracted_triples_removed"])):
        removed.setdefault(row["id"], collections.Counter())[row["reason"]] += 1
    pending_of = {}
    for row in evaluated.pending:
        pending_of.setdefault(row["id"], []).append(row)
    extracted = {}
    for position, row in enumerate(read_csv(Path(inputs["extracted_triples"]))):
        extracted.setdefault(row["id"], []).append({**row, "_position": position})
    evaluated.catalog_records = len(catalog)
    titles = {rid: (r.get("title") or "") for rid, r in catalog.items()}

    finished = set(gt.select(EVALUABLE).ids)
    evaluated.unfinished = len(gt.select(TO_FIX).ids)
    not_extracted = sorted(finished - extracted_ids)
    # Why each was not extracted: 060's model calls failed for it (its details file, key left_out, or for an older
    # 060 its records' status), or 060's last run didn't choose it.
    failed_by_060 = {e["id"]: e for e in (details.get("left_out") or {}).get("records", [])}
    for r in details["records"]:
        if r.get("status") == "failed" and r["id"] not in failed_by_060:
            why = r.get("error") or ""
            failed_by_060[r["id"]] = {"id": r["id"], "maintainer": (catalog.get(r["id"]) or {}).get("maintainer")
                                      or dropped.UNDEFINED, "why": why,
                                      "reason": dropped.kind_from_text(why)}
    evaluated.finished = [{"id": rid, "maintainer": (catalog.get(rid) or {}).get("maintainer") or dropped.UNDEFINED}
                          for rid in sorted(finished)]
    failed_ids = {rid for rid in not_extracted if rid in failed_by_060}
    not_chosen = [rid for rid in not_extracted if rid not in failed_by_060]
    # A record whose extraction failed was chosen by 060 and is scored as extracting nothing: it stays in the fair
    # sample (module docstring).
    taken = finished & (extracted_ids | failed_ids)
    evaluated.chosen_by_060 = len(taken)
    parts = pool_parts(pool_rows)                  # each part is a fair sample on its own: its own run from its own first record
    fair = {rid for order in parts.values() for rid in fair_prefix(order, taken)}
    outside = sorted(taken - fair)
    evaluated.extraction_failed = [failed_by_060[rid] for rid in sorted(failed_ids & fair)]
    evaluated.left_out = {k: v for k, v in {
        "finished, but not chosen by 060's last run": not_chosen,
        "outside the fair sample (after an unfinished record, or one 060's last run didn't choose, of their own part "
        "of the pool, or not in the pool)": outside,
    }.items() if v}
    positions = {r["id"]: r["position"] for r in pool_rows}
    part_of = {r["id"]: r["part"] for r in pool_rows}
    without_text = {rid for rid in by_id if rid in catalog and not has_text(catalog[rid])}

    def gaps_of(only=None) -> str:      # the first gap of each part (of those with a record in `only`, if given), as sentences
        found = [_first_gap(order, name, positions, taken, gt, without_text) for name, order in parts.items()
                 if only is None or any(part_of.get(rid) == name for rid in only)]
        return "; ".join(g for g in found if g)

    gap = gaps_of()
    if evaluated.extraction_failed:
        evaluated.notes.append(failed_note(evaluated.extraction_failed, len(fair),
                                           evaluated.extraction_made.get("max_answer_tokens")))
    if settings.get("evaluate_held_out"):
        problem = held_out_gap(parts.get(HELD_OUT, []), finished, extracted_ids | failed_ids, fair, positions,
                               settings.get("evaluate_held_out_incomplete"), evaluated.notes)
        if problem:
            raise Stop(problem)
    # 060's run may have extracted from the tuning records only (its setting extract_from, with no ids): then the
    # finished records of the other part were left out on purpose, and running 060 the same way again wouldn't
    # bring them in.
    made_settings = evaluated.extraction_made.get("settings") or evaluated.extraction_manifest.get("settings") or {}
    tuning_only = (str(made_settings.get("extract_from") or "").strip().lower() == TUNING
                   and not str(made_settings.get("ids") or "").strip())
    by_setting = [rid for rid in not_chosen if tuning_only and part_of.get(rid) != TUNING]
    others = [rid for rid in not_chosen if rid not in set(by_setting)]
    if by_setting:
        held = sum(part_of.get(rid) == HELD_OUT for rid in by_setting)
        evaluated.notes.append(f"060's last run extracted from the tuning records only (its setting extract_from was "
                            f"tuning), so {len(by_setting)} finished ground truth record(s) that aren't tuning records "
                            f"({held} held-out, {len(by_setting) - held} outside the pool) weren't extracted and this "
                            f"run leaves them out: {named(by_setting)}. Nothing to do if you meant it: the tuning "
                            f"part's numbers lack no record for this reason, and no held-out number can come from "
                            f"this extraction. To evaluate those records, run `py 060_extract/run.py --extract_from "
                            f"ground_truth`, then run `py 070_evaluate/run.py` again.")
    if others:
        evaluated.notes.append(f"{len(others)} finished ground truth record(s) weren't chosen by 060's last run (it "
                            f"neither extracted from them nor recorded a failure for them), so this run leaves them "
                            f"out: {named(others)}. To evaluate them, run `py 060_extract/run.py` so that it chooses "
                            f"them, then run `py 070_evaluate/run.py` again.")
    if outside:
        not_in_pool = [rid for rid in outside if rid not in positions]
        evaluated.notes.append(f"{len(outside)} record(s) are left out because they aren't in the fair sample (the "
                            f"first records of their own part of the pool, with none skipped), so this run doesn't evaluate them: "
                            f"{named(outside)}."
                            + (f" {gaps_of(outside)}, then run `py 070_evaluate/run.py` again." if len(not_in_pool) < len(outside) else "")
                            + (f" {len(not_in_pool)} of them aren't in the pool at all (hand-picked): {named(not_in_pool)}. "
                               f"Nothing to do for those: only pool records can form a fair sample." if not_in_pool else ""))

    rows_of = {}
    for r in gt.select(EVALUABLE).rows:
        rows_of.setdefault(r["id"], []).append(r)
    second_opinion = _read_second_opinion(inputs)
    since = dropped.mark()
    for rid in evaluated.pool:
        if rid not in fair:
            continue
        failure = failed_by_060.get(rid) if rid in failed_ids else None
        ex_rows = [] if failure else extracted.get(rid, [])     # a failed record: scored as extracting nothing
        gt_triples, gt_describes = _triples(rows_of.get(rid, []))
        ex_triples, ex_describes = _triples(ex_rows)
        _record_rows(rid, rows_of.get(rid, []), "ground truth")
        _record_rows(rid, ex_rows, "extracted")
        evaluated.records.append({
            "id": rid, "position": by_id[rid]["position"], "part": by_id[rid]["part"],
            "stratum": strata.get(rid, ""), "title": titles.get(rid, ""),
            "gt": gt_triples, "gt_describes": gt_describes, "extracted": ex_triples, "extracted_describes": ex_describes,
            "removed": dict(removed.get(rid, {})), "pending": pending_of.get(rid, []),
            "second_opinion": groups_of(rid, gt_triples, second_opinion),
            "second_opinion_repeats": repeats_of(rid, gt_triples, second_opinion),
            # why 060's model calls failed for it (a key of common.dropped.KINDS), or None: extracted
            "extraction_failed": failure["reason"] if failure else None,
        })
    _record_not_evaluated(gt, evaluated, not_chosen, outside, extracted, catalog, since)
    _note_second_opinion(evaluated, second_opinion, inputs)
    _mark_twins(evaluated, catalog, inputs)
    missing_stratum = [r["id"] for r in evaluated.records if not r["stratum"]]
    if missing_stratum:
        candidates = repo_path(inputs["candidates"])
        evaluated.notes.append(f"{len(missing_stratum)} evaluated record(s) have no stratum in the pool file "
                            f"({candidates}, column stratum), so the per-stratum numbers show them as the stratum "
                            f"\"(no stratum)\"; the other numbers count them as usual: {named(missing_stratum)}. That "
                            f"file was written with a stratum for every pool record, so it was probably edited: "
                            f"compare it with Git's copy (`git diff {candidates}`).")
    if not evaluated.records:
        raise Stop("Nothing to evaluate yet: no finished ground truth record that 060's last run chose is in the "
                   "fair sample, so 070 can't evaluate. "
                   + (f"{gap}, then run `py 070_evaluate/run.py` again. " if gap else "")
                   + " ".join(evaluated.notes))
    if evaluated.notes:                            # before anything is evaluated, even on a run that pays nothing
        show_warnings("070", evaluated.notes)
        if settings["confirm_paid_calls"]:
            confirm("Press Enter to evaluate anyway, or anything else to cancel.")
    evaluated.reviews = read_reviews(Path(inputs["partial_reviews"]))
    evaluated.review_problems = review_problems(Path(inputs["partial_reviews"]))
    record_unused(STAGE, Path(inputs["partial_reviews"]))
    return evaluated
