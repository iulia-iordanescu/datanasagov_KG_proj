"""
moves.py -- the main moves of 040_induce_schema, as called by
040_induce_schema/run.py.

    stage 1  texts.py    pick_texts                 code: selection: the same number of texts from each stratum of the pool
    -        (here)      paid_calls                 code: asks before paying; keeps every answer in cache/
    stage 2  extract.py  extract_triple_instances   LLM: the triple instances each text states, checked
    stage 3  label.py    label_component_instances  LLM: a label for each component instance, read with its source text
    stage 4  merge.py    merge_labels               LLM: one call over all labels, merging synonyms; code: spelling folds
    stage 5  split.py    split_predicates           LLM: splitting a predicate by its subject's or object's entity class or both; code checks; merging again
    stage 6  count.py    count_support              code: the texts and maintainers behind every schema entry
    stage 7  define.py   write_definitions          LLM: one sentence per entity class and predicate
    stage 8  check.py    check_schema               code: builds the schema from the evidence
    -        compare.py  compare_with_ground_truth_schema   code: beside the ground truth schema, for the report
    -        saturation.py  (in results)            code: would more texts have added schema entries? for the report
    -        tally.py    (in results)               code: the run's statistics, for the report
    -        (here)      results                    writes the_schema.json and induction_evidence.json; the report

Every model answer is cached in cache/ inside the step's output folder
(common/common_helpers/cache.py), so a rerun pays only for what isn't there yet.
Terms are as defined in docs/terminology.md.
"""
from __future__ import annotations

from pathlib import Path

import check
import compare
import count
import define
import extract
import label
import merge
import saturation
import split
import tally
import texts as texts_stage
from texts import RETIRED, SPECS                        # noqa: F401  (the control panel passes them to run_step)
from common import audit, dropped, llm
from common.audit import check_origins, log, ref_path
from common.files import write_json
from common.ground_truth import (ground_truth_schema_view, read_ground_truth, read_pool, record_skipped, twin_kinds,
                                 twin_table)
from common.schema_io import (read_ground_truth_schema, record_left_out_of_view, record_unread, schema_text,
                              without_held_out_only)
from common.report import cell, counted, listed_label, model_calls, named, per_text_headline, per_text_table
from common.step import Results, repo_path

SCHEMA_NAME = "the_schema.json"
EVIDENCE_NAME = "induction_evidence.json"
SHOW = 20                        # rows listed in the report before "…"
#: The model calls that failed, and those cut off, in each stage that calls the model, counted around the stage
#: (watch): {stage: {"failed": n, "cut_off": n}}. Emptied by paid_calls, at the start of each run.
FAILED = {}
#: The stages that call the model, as the report names them.
STAGE_NAMES = {"extract": "stage 2: extraction of triple instances", "label": "stage 3: labeling",
               "merge": "stage 4: merging", "split": "stage 5: splitting", "define": "stage 7: defining"}


# --------------------------------------------------------------------------

def pick_texts(inputs, settings):
    return texts_stage.pick_texts(inputs, settings)


def paid_calls(texts, settings, output) -> llm.Calls:
    FAILED.clear()
    return llm.paid_calls(settings, output, notes=texts.notes)


def watch(stage: str, work, *args):
    """work(*args), counting the model calls of this stage that failed or were cut off (llm.OUTCOMES, counted for
    the whole run) into FAILED[stage]."""
    before = dict(llm.OUTCOMES)
    try:
        return work(*args)
    finally:
        FAILED[stage] = {k: llm.OUTCOMES[k] - before[k] for k in ("failed", "cut_off")}


def extract_triple_instances(texts, calls, settings):
    return watch("extract", extract.extract_triple_instances, texts, calls, settings)


def label_component_instances(triples, calls):
    return watch("label", label.label_component_instances, triples, calls)


def merge_labels(labels, triples, calls):
    return watch("merge", merge.merge_labels, labels, triples, calls)


def split_predicates(triples, labels, settings, calls):
    return watch("split", split.split_predicates, triples, labels, settings, calls)


def count_support(triples, labels, splits):
    return count.count_support(triples, labels, splits)


def write_definitions(counts, settings, calls):
    return watch("define", define.write_definitions, counts, settings, calls)


def check_schema(counts, definitions, settings):
    return check.check_schema(counts, definitions, settings)


def compare_with_ground_truth_schema(inputs, schema) -> dict:
    hand = read_ground_truth_schema(inputs["ground_truth_schema"])
    whole = hand
    # the file without its held-out-only entries, and as patterns the file's and every one the finished tuning
    # records use (the one view of the ground truth schema every step and the annotation tool use:
    # common/common_helpers/ground_truth.ground_truth_schema_view)
    gt = read_ground_truth(Path(inputs["ground_truth"]).parent, read_pool(inputs["splits"]))
    hand = {**without_held_out_only(hand), "patterns": ground_truth_schema_view(hand, gt)["patterns"]}
    stage = "compare_with_ground_truth_schema (for the report)"
    record_unread(stage, whole, ref_path(inputs["ground_truth_schema"]))
    record_skipped(stage, gt)
    record_left_out_of_view(stage, whole, hand, where=ref_path(inputs["ground_truth_schema"]))
    comparison = compare.compare(hand, schema)
    # the ground truth's own problems (a record annotated twice, a file missing a column, ...), shown as warnings
    # like every other step that reads it; results() takes them out before writing the evidence file
    comparison["ground_truth_problems"] = list(gt.problems)
    comparison["ground_truth_schema"] = ref_path(inputs["ground_truth_schema"])
    c = comparison["entity_classes"]
    log.info(f"  beside the ground truth schema: {len(c['both'])} entity classes in both, "
             f"{len(c['only_ground_truth_schema'])} only there, {len(c['only_induced'])} only induced")
    return comparison


# --------------------------------------------------------------------------

def _schema_shape(schema) -> dict:
    """The schema in the shape common/common_helpers/schema_io.schema_text reads, to measure the text 060 sends."""
    return {"entity_classes": {c["component_class"]: c["definition"] for c in schema.entity_classes},
            "predicates": {p["component_class"]: p["definition"] for p in schema.predicates},
            "patterns": [tuple(p["pattern"]) for p in schema.patterns]}


def schema_length(schema, splits) -> dict:
    """How long the schema's text is as step 060 sends it (common/common_helpers/schema_io.schema_text), and how much
    of it the predicates splitting added take: {"characters", "predicates", "added", "added_characters",
    "per_added"}. A predicate's own share is its name-and-definition line and its line break (the text shows no
    patterns, decided 2026-11-15)."""
    shape = _schema_shape(schema)
    text = schema_text(shape)
    width = max((len(n) for kind in ("entity_classes", "predicates") for n in shape[kind]), default=0) + 2
    new = {s["into"] for s in splits.kept} & set(shape["predicates"])
    own = sum(len(f"{n.ljust(width)}{shape['predicates'][n]}".rstrip()) + 1 for n in new)
    return {"characters": len(text), "predicates": len(shape["predicates"]), "added": splits.net_added,
            "added_characters": own, "per_added": round(own / len(new)) if new else None}


def _rows(items: list) -> str:
    """Texts as "record id (stratum)"."""
    return named([f"{t['id']} ({t['stratum']})" for t in items], SHOW, "; ")


def results(texts, triples, labels, splits, counts, definitions, schema, comparison, calls, settings,
            output) -> Results:
    ground_truth_problems = comparison.pop("ground_truth_problems", [])
    strata = [r["stratum"] for r in texts.strata]
    made = {"run_id": audit.current_run_id(), **llm.describe(), "settings": settings,
            "texts": len(texts.items), "strata": strata, "maintainers": texts.maintainers}
    schema_path, evidence_path = output / SCHEMA_NAME, output / EVIDENCE_NAME
    write_json(schema_path, {"entity_classes": schema.entity_classes, "predicates": schema.predicates,
                              "patterns": schema.patterns, "pinned": schema.pinned,
                              "deferred": [{k: d[k] for k in check.DEFERRED_FIELDS} for d in schema.deferred],
                              "made": made})
    calls_made = {"extract": triples.calls, "label": labels.calls, "merge": labels.merge_calls,
                  "split": splits.calls + splits.merge_calls, "define": definitions.calls,
                  "test": calls.paid.test_calls}
    pieces = {t["id"]: len(t["pieces"]) for t in texts.items}
    # Would more texts have added schema entries? (saturation.py: code only, from the counts)
    sat = saturation.curve(counts, len(triples.texts), settings["min_support"])
    wide = saturation.breadth(counts, settings["min_support"])
    # The run's statistics (tally.py: code only)
    per_text = tally.per_text(triples)
    by_stratum = tally.per_stratum(triples, strata)
    empty = tally.no_triple_instances(triples)
    removed = tally.removed_by_checks(triples, counts, schema)
    others = tally.other_checks(labels, splits, definitions, schema, check.DEFERRED_REASONS)
    failed = {stage: {**FAILED.get(stage, {"failed": 0, "cut_off": 0}), "made": calls_made[stage]}
              for stage in STAGE_NAMES}
    failed["extract"]["cut_off_before"] = triples.cut_reused
    length = schema_length(schema, splits)
    statistics = {
        "sampling": {"texts_per_stratum": settings["texts_per_stratum"], "strata": texts.strata,
                     "skipped_twins": texts.skipped, "reading_order_seed": f"{texts.seed}/{texts_stage.READING_ORDER}"},
        "triple_instances_per_text": {k: tally.stats(v) for k, v in per_text.items()},
        "verified_per_text_by_stratum": {s: tally.stats(v) for s, v in by_stratum.items()},
        "texts_with_no_triple_instance": empty,
        "removed_by_checks": removed, "other_checks": others,
        "model_calls_failed": failed, "schema_length": length}
    write_json(evidence_path, {
        "made": made,
        "texts": [{**t, "pieces": pieces[t["id"]]} for t in triples.texts],
        "failed_texts": triples.failed,
        "left_out": dropped.details(triples.left_out),
        "labels": labels.of, "vocabulary": labels.vocabulary, "label_batches": labels.batches,
        "unlabeled": labels.unlabeled, "merges": labels.merges, "merge_issues": labels.merge_issues,
        "spelling_folds": labels.spelling_folds,
        "splits": {"sent": splits.sent, "kept": splits.kept, "dropped": splits.dropped,
                   "rejected": splits.rejected, "refused": splits.refused, "undone": splits.undone,
                   "into": splits.into, "merged_again": splits.merges, "merge_again_issues": splits.merge_issues,
                   "merge_again_spelling_folds": splits.spelling_folds, "final": splits.final,
                   "pinned": {p: [list(x) for x in pins] for p, pins in splits.pinned.items()},
                   "added": splits.added, "net_added": splits.net_added, "max_new_predicates": splits.cap,
                   "min_split_texts": splits.min_texts},
        "unlabeled_slots": counts.unlabeled_slots,
        "counts": {"entity_classes": counts.entity_classes, "predicates": counts.predicates,
                   "patterns": counts.patterns},
        "definitions": definitions.of, "too_vague": definitions.too_vague,
        "refused": {"labels": labels.refused, "definitions": definitions.refused, "splits": splits.refused},
        "unknown_schema_entries": definitions.unknown, "missing_definitions": schema.missing_definitions,
        "definitions_asked_again": definitions.asked_again,
        "definitions_naming_no_entity_class": definitions.not_entity_classes,
        "definitions_not_naming_their_pin": definitions.pins_not_named,
        "calls": {**calls_made, "reused_extractions": triples.reused},
        "compared_with_ground_truth_schema": comparison,
        "saturation": {"curve": sat, "breadth": wide},
        "statistics": statistics,
    })
    log.info(f"  wrote {SCHEMA_NAME} and {EVIDENCE_NAME}")

    warnings = list(calls.paid.notes)          # shown before paying too, if the run paid
    warnings += [f"Ground truth, {p}" for p in ground_truth_problems]
    evidence_shown = repo_path(evidence_path)
    if triples.failed_note:
        warnings.append(triples.failed_note)
    if empty["verified"]:
        warnings.append(f"{len(empty['verified'])} text(s) gave no verified triple instance: "
                        f"{named([t['id'] for t in empty['verified']], 3)}. They add no support to any schema entry. "
                        f"Nothing to do if they are very short records; otherwise look at each one's `unverified` "
                        f"list in {evidence_shown}.")
    refused = [f"{r['component_instance']} ({label.BECOMES[kind]})" for kind, rows in labels.refused.items() for r in rows]
    refused += [f"{r['predicate']} (predicate, splitting)" for r in splits.refused]
    refused += [f"{r['component_class']} ({r['kind']}, definition)" for r in definitions.refused]
    if refused:
        why = next(iter([r["why"] for rows in labels.refused.values() for r in rows]
                        + [r["why"] for r in splits.refused] + [r["why"] for r in definitions.refused]))
        warnings.append(f"The service refused to answer about {len(refused)} item(s), even asked alone ({why}): "
                        f"{named(refused, 10)}. A refused component instance stays unlabeled and counts toward no "
                        f"schema entry; a refused predicate isn't split; a refused schema entry gets no definition. "
                        f"Everything else in their batches was answered (each refused batch was asked again in "
                        f"halves). Each one, with the reason, is in {evidence_shown} under `refused`; what the model "
                        f"wrote before the stop is in this run's log (outputs/logs/<run id>.log), on DEBUG lines "
                        f"starting \"answer stopped by the service\". Nothing to do if few; if many, try another "
                        f"model (`--model`).")
    unlabeled = sum(len(v) for v in labels.unlabeled.values())
    if unlabeled:
        left = [v for kind in label.KINDS for v in labels.unlabeled.get(kind, [])]
        warnings.append(f"{unlabeled} component instance(s) were left unlabeled even after a second try: "
                        f"{named(left, 5)}. They count toward no schema entry. Nothing to do if few; all are "
                        f"listed in {evidence_shown} under `unlabeled`.")
    issues = {k: sum(len(v[k]) for v in labels.merge_issues.values())
              for k in ("into_not_a_label", "not_sent", "merged_twice", "cycle")}
    if any(issues.values()):
        warnings.append(f"The merge reply had items code ignored: {issues['into_not_a_label']} merge(s) "
                        f"into something that isn't a label, {issues['not_sent']} label(s) that weren't "
                        f"sent, {issues['merged_twice']} label(s) merged twice, and {issues['cycle']} merge(s) that "
                        f"would close a cycle (the first merge kept each time). An ignored merge can leave two "
                        f"labels that mean the same thing as two schema entries. Nothing to do; all are listed in "
                        f"{evidence_shown} under `merge_issues`.")
    if splits.rejected:
        warnings.append(f"The splitting replies had {len(splits.rejected)} predicate split(s) code rejected: "
                        + named([f"{r['predicate']} into {r['into']} by {r['by']} ({r['why']})"
                                 for r in splits.rejected], 3, "; ")
                        + f". A rejected predicate split leaves its predicate as it was. Nothing to do; each is listed, with "
                          f"why, in this report's section *Splitting* and in {evidence_shown} under `splits`.")
    if splits.dropped:
        warnings.append(f"{len(splits.dropped)} predicate split(s) passed every check but were left out because the "
                        f"predicate splits kept already add max_new_predicates ({splits.cap}) predicates: "
                        + named([f"{s['predicate']} into {s['into']} ({s['texts']} texts)" for s in splits.dropped],
                                3, "; ")
                        + ". Their predicates keep those triple instances. To keep more, raise `--max_new_predicates` "
                          "(each added predicate makes every step 060 prompt longer: the report's section "
                          "*Splitting* gives by how much).")
    if schema.missing_definitions:
        n = len(schema.missing_definitions)
        warnings.append(f"{n} schema entr{'ies have' if n != 1 else 'y has'} no definition (the model "
                        f"didn't return one): "
                        + named([f"{d['component_class']} ({d['kind']})" for d in schema.missing_definitions], 5)
                        + f". They stay in the schema, marked \"no definition\", so when step 060 extracts with "
                        f"this schema, its model sees only the entity class or predicate itself. To ask again, delete "
                        f"{repo_path(calls.cache_dir / 'define.json')}, then run `py 040_induce_schema/run.py` again.")
    if definitions.unknown:
        warnings.append(f"The definition replies named {len(definitions.unknown)} schema entr(ies) that "
                        f"weren't sent: "
                        + named([f"{d['component_class']} ({d['kind']})" for d in definitions.unknown], 5)
                        + f". They were ignored, so they change nothing in the schema. Nothing to do; all are "
                        f"listed in {evidence_shown} under `unknown_schema_entries`.")
    if definitions.not_entity_classes:
        n = len(definitions.not_entity_classes)
        warnings.append(f"{n} definition(s) name a word shaped like an entity class (CamelCase) that is no entity "
                        f"class of this schema, even when asked once more: "
                        + named([f"{d['component_class']} ({d['kind']}): {', '.join(d['words'])}"
                                 for d in definitions.not_entity_classes], 5, "; ")
                        + f". Each definition is kept as written (a definition is words only). Read each: a proper "
                        f"noun (e.g. a place) is fine; a word meant as an entity class is the name of none in this "
                        f"schema, so a model reading the definition in step 060 may look for an entity class that "
                        f"isn't there. All are listed in {evidence_shown} under `definitions_naming_no_entity_class`.")
    if definitions.pins_not_named:
        n = len(definitions.pins_not_named)
        warnings.append(f"{n} definition(s) of a pinned predicate (a new predicate of a predicate split, stage 5) "
                        f"don't name every entity class its pin allows, even when asked once more: "
                        + named([f"{d['component_class']}: {', '.join(d['entity_classes'])}"
                                 for d in definitions.pins_not_named], 5, "; ")
                        + f". Each definition is kept as written, and the pin is kept in {SCHEMA_NAME}. No prompt "
                        f"shows a pin, so a model reading the schema in step 060 learns it only from the definition, "
                        f"and may use the predicate with other entity classes; step 060 flags each such triple "
                        f"(pattern_not_pinned). Nothing to do if few; to ask again, delete "
                        f"{repo_path(calls.cache_dir / 'define.json')}, then run `py 040_induce_schema/run.py` again "
                        f"(every definition is asked again). All are listed in {evidence_shown} under "
                        f"`definitions_not_naming_their_pin`.")
    for items, what in ((schema.entity_classes, "entity classes"), (schema.predicates, "predicates"),
                        (schema.patterns, "patterns")):
        missing = check_origins(items, what)
        if missing:
            warnings.append(missing)

    table = [(listed_label("verified + unverified"), per_text["listed"]), ("verified (kept)", per_text["verified"])]
    split_pieces = sum(n > 1 for n in pieces.values())
    skipped = {k: sum(r["skipped"][k] for r in texts.strata) for k in texts_stage.SKIPPED}
    title_only = sum(r["title_only_kept"] for r in texts.strata)
    lines = [
        "### What this run worked on", "",
        f"{len(texts.items)} texts: up to {settings['texts_per_stratum']} induction candidates from each of the "
        f"{len(strata)} strata of the ground truth candidates pool, taken in each stratum's fixed random order, "
        f"read in a random order fixed by 030's seed"
        + (f"; {split_pieces} were split into text pieces" if split_pieces else "") + ". While drawing, a text that "
        "is a whole-text twin (the same title and `notes`) or a notes-only twin (the same `notes`) of a text already "
        "drawn was skipped and the next in its stratum taken; a title-only twin (the same title, other `notes`) was "
        "kept, since its text differs (040_induce_schema/040_induce_schema.md, *How it works*, stage 1).", "",
        "| Stratum | Maintainers | Induction candidates | Texts drawn | Skipped: whole-text twins | "
        "Skipped: notes-only twins | Title-only twins kept |", "|---|---:|---:|---:|---:|---:|---:|"]
    lines += [f"| {cell(r['stratum'])} | {r['maintainers']:,} | {r['candidates']:,} | {r['taken']} | "
              f"{r['skipped']['whole text']} | {r['skipped']['notes only']} | {r['title_only_kept']} |"
              for r in texts.strata]
    lines += [f"| **all strata** | {sum(r['maintainers'] for r in texts.strata):,} | "
              f"{sum(r['candidates'] for r in texts.strata):,} | **{len(texts.items)}** | {skipped['whole text']} | "
              f"{skipped['notes only']} | {title_only} |", ""]
    if texts.skipped:
        lines += ["Twins skipped (record id, stratum, twin kind, the text drawn it is a twin of): "
                  + named([f"{k['id']} ({k['stratum']}, {k['twin_kind']}, of {k['twin_of']})" for k in texts.skipped],
                          SHOW, "; ") + ".", ""]
    lines += [*dropped.section(triples.left_out, texts.items, "the evidence the schema is induced from",
                               repo_path(evidence_path))]
    learned = {t["id"]: t["record"] for t in texts.items if t["id"] in {x["id"] for x in triples.texts}}
    lines += ["", "### Twins in the pool", "",
              f"A pool record with the same title, the same `notes`, or both as one of the {len(learned)} texts this run "
              f"learned from is a twin (docs/terminology.md, section *Evaluating extraction*): the schema has seen "
              f"some or most of its text, so step 070 gives its numbers with and without the twins. The second "
              f"column, against every induction candidate, is the most there can be (as in step 030's report).", ""]
    lines += twin_table(texts.pool, [(f"the {len(learned)} texts this run learned from",
                                      f"the {len(learned)} texts this run of step 040 learned from", learned),
                                     (f"all {len(texts.candidates):,} induction candidates",
                                      f"the {len(texts.candidates):,} induction candidates", texts.candidates)])
    twins = sum(1 for k in twin_kinds(texts.pool, learned).values() if k)
    lines += ["", "### Triple instances and labels", ""]
    lines += per_text_table("Triple instances per text", table) + [
              "",
              "One text is one record's text. A triple instance two text pieces of a text both state counts once; "
              "items in the replies that weren't triple instances, and texts whose model call failed, aren't "
              "counted. SD: the sample standard deviation.", ""]
    lines += per_text_table("Verified triple instances per text, by stratum", list(by_stratum.items())) + [""]
    lines += [f"Texts whose replies listed no triple instance: {len(empty['listed'])}"
              + (f" ({_rows(empty['listed'])})" if empty["listed"] else "") + f". Texts with no verified triple "
              f"instance: {len(empty['verified'])}" + (f" ({_rows(empty['verified'])})" if empty["verified"] else "")
              + ".", "",
              "- Verified: each one's source text is in its record's text (checked in code, "
              "`common/common_helpers/validate.py`).",
              f"- Describes class (`describes_class`, the entity class of what the title names): named for "
              f"{counts.texts_with_describes_class} of {len(triples.texts)} texts.",
              f"- Left out as unverified: {sum(triples.errors.values()):,} ({counted(triples.errors)}); "
              f"listed in `{repo_path(output / EVIDENCE_NAME)}` under each text's `unverified`.",
              f"- Verified, with flags worth a look: {counted(triples.flags)}.",
              f"- {triples.malformed:,} item(s) in the replies weren't triple instances and were dropped.",
              f"- Labeled: {len(labels.of.get('entity', {})):,} subject instances and object instances "
              f"with {len(labels.vocabulary.get('entity', [])):,} entity class labels; "
              f"{len(labels.of.get('predicate', {})):,} predicate instances with "
              f"{len(labels.vocabulary.get('predicate', [])):,} predicate labels (each judged by its shortest triple "
              f"instance and that triple instance's source text).",
              f"- Merged in stage 4: {len(labels.merges)} label(s), all listed below.",
              f"- Folded by spelling in stage 4: {len(labels.spelling_folds)} group(s).", ""]
    if labels.merges:
        lines += ["Merges (check these: a wrong merge makes two ideas one):", "",
                  "| Kind | Label | Merged into | Component instances | Texts |", "|---|---|---|---:|---:|"]
        lines += [f"| {m['kind']} | {cell(m['label'])} | {cell(m['into'])} | {m['component_instances']} | "
                  f"{m['texts']} |" for m in labels.merges]
        lines.append("")
    if labels.spelling_folds:
        lines += ["Spelling folds: " + named([f"{' · '.join(f['folded'])} --> {f['into']}"
                                              for f in labels.spelling_folds], SHOW, "; ") + ".", ""]
    lines += _splitting_lines(splits, length, settings)
    lines += _check_lines(removed, others)
    by_reason = {}
    for d in schema.deferred:
        reason = check.DEFERRED_REASONS[d["reason_code"]]
        kind = d["entry_type"]
        by_reason[(kind, reason)] = by_reason.get((kind, reason), 0) + 1
    lines += ["### Schema", "",
              f"min_support = {settings['min_support']}: a schema entry enters the schema if its support "
              f"(the number of texts it was found in) is at least that.", "",
              "| | In the schema | Found |", "|---|---:|---:|",
              f"| Entity classes | {len(schema.entity_classes):,} | {len(counts.entity_classes):,} |",
              f"| Predicates | {len(schema.predicates):,} | {len(counts.predicates):,} |",
              f"| Patterns | {len(schema.patterns):,} | {len(counts.patterns):,} |", ""]
    if by_reason:
        lines += ["Deferred:", "", "| Entry type | Reason | Schema entries |", "|---|---|---:|"]
        lines += [f"| {k} | {r} | {n:,} |" for (k, r), n in sorted(by_reason.items())]
        lines.append("")
    lines += saturation.report_lines(sat, wide, len(triples.texts), settings["min_support"])
    lines += compare.report_lines(comparison, comparison["ground_truth_schema"], SHOW)
    lines += [f"Schema entries backed by one maintainer only (may be that maintainer's house style): "
              f"{len(schema.single_maintainer):,}.", "",
              "Entity classes with the most support:", "",
              "| Entity class | Support | Maintainers | Examples |", "|---|---:|---:|---|"]
    lines += [f"| {cell(c['component_class'])} | {c['support']} | {len(c['maintainers'])} | "
              f"{cell(', '.join(c['examples']))} |" for c in schema.entity_classes[:15]]
    lines += [""] + dropped.reasks_lines(llm.REASKS)
    lines += model_calls([("stage 2: extract triple instances (one call per text piece)", triples.calls, triples.reused),
                          (f"stage 3: label component instances ({label.LABEL_BATCH} per call)", labels.calls, labels.reused),
                          ("stage 4: merge labels (one call per kind)", labels.merge_calls, labels.merge_reused),
                          (f"stage 5: split predicates ({split.SPLIT_BATCH} per call)", splits.calls, splits.reused),
                          ("stage 5: merge predicates again (one call)", splits.merge_calls, splits.merge_reused),
                          (f"stage 7: write definitions ({define.DEFINE_BATCH} per call)", definitions.calls,
                           definitions.reused)],
                         calls.paid.test_calls, llm.model_label())
    lines += ["Calls that failed or were cut off, by stage (after the model client's own retries; a cut-off is also "
              "a failure):", "",
              "| Stage | Calls made | Failed | Of which cut off | Cut off in an earlier run, not asked again |",
              "|---|---:|---:|---:|---:|"]
    lines += [f"| {STAGE_NAMES[stage]} | {f['made']:,} | {f['failed']:,} | {f['cut_off']:,} | "
              f"{f.get('cut_off_before', 0) if stage == 'extract' else '–'} |" for stage, f in failed.items()]
    lines.append("")

    return Results(
        files=[schema_path, evidence_path],
        headline={"entity classes": len(schema.entity_classes), "predicates": len(schema.predicates),
                  "patterns": len(schema.patterns), "twins in the pool": f"{twins} of {len(texts.pool):,}",
                  "twins skipped while drawing": len(texts.skipped),
                  "predicates added by splitting": splits.net_added,
                  **per_text_headline([("raw triple instances", per_text["listed"]),
                                       ("verified triple instances", per_text["verified"])]),
                  "texts with no verified triple instance": len(empty["verified"]),
                  "model calls failed": sum(f["failed"] for f in failed.values()),
                  **dropped.reasks_headline(llm.REASKS)},
        details="\n".join(lines),
        warnings=warnings,
    )


def _splitting_lines(splits, length: dict, settings: dict) -> list:
    """The report's subsection *Splitting* (stage 5)."""
    lines = ["### Splitting", "",
             f"Stage 5 sent {len(splits.sent)} predicate(s) whose triple instances have several subject entity "
             f"classes or several object entity classes; the model proposed "
             f"{len(splits.kept) + len(splits.undone) + len(splits.dropped) + len(splits.rejected)} predicate "
             f"split(s), each a new predicate with its grouping (subject, object or pattern) and the groups it takes. "
             f"Kept by the checks and the cap: {len(splits.kept) + len(splits.undone)}, adding {splits.added} "
             f"predicate(s) (max_new_predicates = {settings['max_new_predicates']}); dropped by that cap: "
             f"{len(splits.dropped)}; rejected by code: {len(splits.rejected)} (min_split_texts = "
             f"{settings['min_split_texts']}). Then the predicates were merged again: "
             f"{len(splits.merges)} predicate(s) merged into others, {len(splits.undone)} predicate split(s) undone "
             f"(every part of their predicate ended in one predicate). In all, splitting changed the number of "
             f"predicates by {splits.net_added:+d}; {len(splits.pinned)} predicate(s) are pinned.", ""]
    if settings["max_new_predicates"] == 0:
        lines += ["max_new_predicates is 0, so no predicate was sent and none was split.", ""]
    for rows, title in ((splits.kept, "Predicate splits kept"),
                        (splits.dropped, "Predicate splits dropped by max_new_predicates (fewest texts)")):
        if rows:
            lines += [f"{title}:", "", "| Predicate | Grouped by | New predicate | Takes | Pin | Texts | Triple instances |",
                      "|---|---|---|---|---|---:|---:|"]
            lines += [f"| {cell(s['predicate'])} | {s['by']} | {cell(s['into'])} | {cell(', '.join(s['takes']))} | "
                      f"{cell('; '.join(' -> '.join(x) for x in s['only']))} | {s['texts']} | {s['triple_instances']} |"
                      for s in rows]
            lines.append("")
    if splits.undone:
        lines += ["Predicate splits undone by merging again (each predicate is whole again, or merged into the "
                  "predicate every part of it ended in):", "",
                  "| Predicate | Grouped by | New predicate | Takes | Every part ended in | The predicate now |",
                  "|---|---|---|---|---|---|"]
        lines += [f"| {cell(s['predicate'])} | {s['by']} | {cell(s['into'])} | {cell(', '.join(s['takes']))} | "
                  f"{cell(s['ends_in'])} | {cell(s['goes_to'])} |" for s in splits.undone]
        lines.append("")
    if splits.merges:
        lines += ["Predicates merged again (check these: a wrong merge makes two ideas one):", "",
                  "| Predicate | Merged into | Predicate instances | Texts |", "|---|---|---:|---:|"]
        lines += [f"| {cell(m['label'])} | {cell(m['into'])} | {m['component_instances']} | {m['texts']} |"
                  for m in splits.merges]
        lines.append("")
    set_aside = sum(len(v) for v in splits.merge_issues.values())
    if set_aside:
        lines += [f"Merges of the model's set aside while merging again: {set_aside} (each with why in "
                  f"`discarded.jsonl`, stage {split.MERGE_AGAIN_STAGE.split(' ', 1)[1]}).", ""]
    if splits.rejected:
        lines += ["Predicate splits rejected by code:", "", "| Predicate | Grouped by | New predicate | Takes | Why |",
                  "|---|---|---|---|---|"]
        lines += [f"| {cell(str(r['predicate']))} | {cell(str(r['by']))} | {cell(str(r['into']))} | "
                  f"{cell(', '.join(map(str, r['takes'])))} | {cell(r['why'])} |" for r in splits.rejected]
        lines.append("")
    per = (f"{length['per_added']:,} characters per added predicate" if length["per_added"] is not None
           else "no predicate was added")
    lines += [f"Schema text, as step 060 sends it in every prompt (`common/common_helpers/schema_io.py`, "
              f"`schema_text`): {length['characters']:,} characters for {length['predicates']} predicates. The "
              f"predicates splitting added take {length['added_characters']:,} of them ({per}: each one's name and "
              f"definition line; the text shows no patterns and no pins). A predicate split away entirely gives its "
              f"own line back. What share of a step 060 "
              f"prompt that is: 040_induce_schema/040_induce_schema.md, *Settings*, `max_new_predicates`.", ""]
    return lines


def _check_lines(removed: list, others: list) -> list:
    """The report's subsection *Code checks*: what each code check of stages 2 to 8 removed."""
    lines = ["### Code checks", "",
             "What each code check removed, in the order the checks run. A check removes a text wholly when the text "
             "had at least one triple instance just before the check and none after it (a text whose model call "
             "failed is in none of these: it is counted under *Model calls*).", "",
             "| Stage | Check | What it removes | Triple instances removed | Texts removed wholly |",
             "|---:|---|---|---:|---:|"]
    lines += [f"| {r['stage']} | {r['check']} | {r['what']} | {r['removed']:,} | {len(r['texts_wholly']):,} |"
              for r in removed]
    lines.append("")
    for r in removed:
        if r["texts_wholly"]:
            lines.append(f"- Removed wholly by *{r['check']}* (record id, stratum): {_rows(r['texts_wholly'])}.")
    lines += ["", "The model's other answers that code ignored, or that had no effect:", "",
              "| Stage | Check | Removed | Of |", "|---:|---|---:|---|"]
    lines += [f"| {r['stage']} | {r['check']} | {r['removed']:,} | {r['unit']} |" for r in others]
    return lines + [""]
