"""
moves.py -- the main moves of 040_induce_schema, as called by
040_induce_schema.py. Each stage lives in its own file:

    stage 1  texts.py    pick_texts                 the texts to learn from (030's induction candidates)
    -        (here)      paid_calls                 asks before the first model call; the answer cache
    stage 2  extract.py  extract_triple_instances   LLM: the triple instances each text states, checked
    stage 3  label.py    label_component_instances  LLM: a label for each component instance, reusing labels
    stage 4  merge.py    merge_labels               LLM: one call over all labels, merging synonyms
    stage 5  count.py    count_support              code: the texts and maintainers behind every schema entry
    stage 6  define.py   write_definitions          LLM: one sentence per entity class and predicate
    stage 7  check.py    check_schema               code: builds the schema from the evidence
    -        compare.py  compare_with_hand_schema   code: beside the hand-built schema, for the report
    -        (here)      results                    writes the_schema.json, induction_evidence.json; report

Every model answer is cached in cache/ inside the step's output folder (see
cache.py), so a rerun pays only for what changed. Terms are as defined in
docs/terminology.md.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

import check
import compare
import count
import define
import extract
import label
import merge
import texts as texts_stage
from common import audit, llm
from common.audit import check_origins, log, ref_path
from common.schema_io import read_hand_schema
from common.step import Results

SCHEMA_NAME = "the_schema.json"
EVIDENCE_NAME = "induction_evidence.json"
SHOW = 20                        # rows listed in the report before "…"


@dataclass
class Calls:
    paid: llm.PaidCalls          # asks before the first model call, counts the calls
    cache_dir: Path              # where every answer is kept


# --------------------------------------------------------------------------

def pick_texts(inputs, settings):
    return texts_stage.pick_texts(inputs, settings)


def paid_calls(settings, output) -> Calls:
    return Calls(paid=llm.PaidCalls(confirm=settings["confirm_paid_calls"]), cache_dir=output / "cache")


def extract_triple_instances(texts, calls, settings):
    return extract.extract_triple_instances(texts, calls, settings)


def label_component_instances(triples, calls):
    return label.label_component_instances(triples, calls)


def merge_labels(labels, triples, calls):
    return merge.merge_labels(labels, triples, calls)


def count_support(triples, labels):
    return count.count_support(triples, labels)


def write_definitions(counts, settings, calls):
    return define.write_definitions(counts, settings, calls)


def check_schema(counts, definitions, settings):
    return check.check_schema(counts, definitions, settings)


def compare_with_hand_schema(inputs, schema) -> dict:
    hand = read_hand_schema(inputs["hand_schema"])
    comparison = compare.compare(hand, schema)
    comparison["hand_schema"] = ref_path(inputs["hand_schema"])
    c = comparison["entity_classes"]
    log.info(f"  beside the hand-built schema: {len(c['both'])} entity classes in both, "
             f"{len(c['only_hand'])} only there, {len(c['only_induced'])} only induced")
    return comparison


# --------------------------------------------------------------------------

def _write_json(path: Path, data) -> None:
    tmp = path.with_suffix(".json.part")
    tmp.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8", newline="\n")
    os.replace(tmp, path)


def _cell(value) -> str:
    return "" if value is None else str(value).replace("|", "\\|").replace("\n", " ")


def _counted(counter: dict) -> str:
    return ", ".join(f"{k} {v:,}" for k, v in sorted(counter.items())) or "none"


def results(texts, triples, labels, counts, definitions, schema, comparison, calls, settings, output) -> Results:
    made = {"run_id": audit.current_run_id(), "model": llm.MODEL, "settings": settings,
            "texts": len(texts.items), "maintainers": [m["maintainer"] for m in texts.maintainers]}
    schema_path, evidence_path = output / SCHEMA_NAME, output / EVIDENCE_NAME
    _write_json(schema_path, {"entity_classes": schema.entity_classes, "predicates": schema.predicates,
                              "patterns": schema.patterns, "deferred": schema.deferred, "made": made})
    calls_made = {"extract": triples.calls, "label": labels.calls, "merge": labels.merge_calls,
                  "define": definitions.calls, "test": calls.paid.test_calls}
    pieces = {t["id"]: len(t["pieces"]) for t in texts.items}
    _write_json(evidence_path, {
        "made": made,
        "texts": [{**t, "pieces": pieces[t["id"]]} for t in triples.texts],
        "labels": labels.of, "vocabulary": labels.vocabulary, "label_batches": labels.batches,
        "unlabeled": labels.unlabeled, "merges": labels.merges, "merge_issues": labels.merge_issues,
        "spelling_folds": counts.spelling_folds, "unlabeled_slots": counts.unlabeled_slots,
        "counts": {"entity_classes": counts.entity_classes, "predicates": counts.predicates,
                   "patterns": counts.patterns},
        "definitions": definitions.of, "too_vague": definitions.too_vague,
        "unknown_schema_entries": definitions.unknown, "missing_definitions": schema.missing_definitions,
        "calls": {**calls_made, "reused_extractions": triples.reused},
        "compared_with_hand_schema": comparison,
    })
    log.info(f"  wrote {SCHEMA_NAME} and {EVIDENCE_NAME}")

    warnings = []
    failed = [(t["id"], p) for t in triples.texts for p in t["failed_pieces"]]
    if failed:
        warnings.append(f"{len(failed)} text piece(s) failed extraction, so their triple instances are "
                        f"missing ({', '.join(f'{i} piece {p + 1}' for i, p in failed[:3])}"
                        f"{' …' if len(failed) > 3 else ''}). Rerun: only those are asked again.")
    empty = [t["id"] for t in triples.texts if not t["triple_instances"] and not t["failed_pieces"]]
    if empty:
        warnings.append(f"{len(empty)} text(s) gave no verified triple instance: {', '.join(empty[:3])}"
                        f"{' …' if len(empty) > 3 else ''}.")
    unlabeled = sum(len(v) for v in labels.unlabeled.values())
    if unlabeled:
        warnings.append(f"{unlabeled} component instance(s) were left unlabeled even after a second try; "
                        f"they count toward no schema entry. Listed in {EVIDENCE_NAME} under unlabeled.")
    issues = {k: sum(len(v[k]) for v in labels.merge_issues.values())
              for k in ("into_not_a_label", "not_sent", "merged_twice")}
    if any(issues.values()):
        warnings.append(f"The merge reply had items code ignored: {issues['into_not_a_label']} merge(s) "
                        f"into something that isn't a label, {issues['not_sent']} label(s) that weren't "
                        f"sent, {issues['merged_twice']} label(s) merged twice (the first merge kept). "
                        f"Listed in {EVIDENCE_NAME} under merge_issues.")
    if schema.missing_definitions:
        n = len(schema.missing_definitions)
        warnings.append(f"{n} schema entr{'ies have' if n != 1 else 'y has'} no definition (the model "
                        f"didn't return one); they stay in the schema. Delete cache/define.json and rerun "
                        f"to ask again.")
    if definitions.unknown:
        warnings.append(f"The definition replies named {len(definitions.unknown)} schema entr(ies) that "
                        f"weren't sent; ignored. Listed in {EVIDENCE_NAME} under unknown_schema_entries.")
    for items, what in ((schema.entity_classes, "entity classes"), (schema.predicates, "predicates"),
                        (schema.patterns, "patterns")):
        missing = check_origins(items, what)
        if missing:
            warnings.append(missing)

    total_calls = sum(calls_made.values())
    n_verified = sum(len(t["triple_instances"]) for t in triples.texts)
    split = sum(n > 1 for n in pieces.values())
    lines = [
        "### Texts", "",
        f"{len(texts.items)} texts: the first {settings['texts_per_maintainer']} induction candidates of "
        f"each of the {len(texts.maintainers)} largest maintainers"
        + (f"; {split} were split into text pieces" if split else "") + ".", "",
        "| Maintainer | Records | Texts used |", "|---|---:|---:|"]
    lines += [f"| {_cell(m['maintainer'])} | {m['records']:,} | {m['taken']} |" for m in texts.maintainers]
    lines += ["", "### Model calls", "",
              "| Stage | Calls |", "|---|---:|",
              f"| 2 extract triple instances | {triples.calls} (+{triples.reused} answered from the cache) |",
              f"| 3 label component instances | {labels.calls} |",
              f"| 4 merge labels | {labels.merge_calls} |",
              f"| 6 write definitions | {definitions.calls} |", f"| test call | {calls.paid.test_calls} |",
              f"| **total this run** | **{total_calls}** |", "",
              f"Model: `{llm.MODEL}`. Answers are kept in `cache/`; a rerun pays only for what changed.", "",
              "### Triple instances and labels", "",
              f"- {n_verified:,} verified triple instances from {counts.texts_with_triple_instances} texts: "
              f"each one's source text is in its record's text (checked in code, `common/validate.py`).",
              f"- Left out as unverified: {sum(triples.errors.values()):,} ({_counted(triples.errors)}); "
              f"listed in `{EVIDENCE_NAME}` under each text's `unverified`.",
              f"- Verified, with flags worth a look: {_counted(triples.flags)}.",
              f"- {triples.malformed:,} item(s) in the replies weren't triple instances and were dropped.",
              f"- Labeled: {len(labels.of.get('entity', {})):,} component instances of subjects and objects "
              f"with {len(labels.vocabulary.get('entity', [])):,} entity class labels; "
              f"{len(labels.of.get('predicate', {})):,} of predicates with "
              f"{len(labels.vocabulary.get('predicate', [])):,} predicate labels.",
              f"- Merged in stage 4: {len(labels.merges)} label(s), all listed below.",
              f"- Folded by spelling in stage 5: {len(counts.spelling_folds)} group(s).", ""]
    if labels.merges:
        lines += ["Merges (check these: a wrong merge makes two ideas one):", "",
                  "| Kind | Label | Merged into | Component instances | Texts |", "|---|---|---|---:|---:|"]
        lines += [f"| {m['kind']} | {_cell(m['label'])} | {_cell(m['into'])} | {m['component_instances']} | "
                  f"{m['texts']} |" for m in labels.merges]
        lines.append("")
    if counts.spelling_folds:
        lines += ["Spelling folds: " + "; ".join(f"{' · '.join(f['folded'])} → {f['into']}"
                                                  for f in counts.spelling_folds[:SHOW])
                  + (" …" if len(counts.spelling_folds) > SHOW else ""), ""]
    by_reason = {}
    for d in schema.deferred:
        reason = "too vague" if d["reason"].startswith("too vague") else \
            ("support below min_support" if d["reason"].startswith("support")
             else "through a schema entry not in the schema")
        kind = d["kind"].replace("_", " ")
        by_reason[(kind, reason)] = by_reason.get((kind, reason), 0) + 1
    lines += ["### Schema", "",
              f"min_support = {settings['min_support']}: a schema entry enters the schema if its support "
              f"(the number of texts it was found in) is at least that.", "",
              "| | In the schema | Found |", "|---|---:|---:|",
              f"| Entity classes | {len(schema.entity_classes):,} | {len(counts.entity_classes):,} |",
              f"| Predicates | {len(schema.predicates):,} | {len(counts.predicates):,} |",
              f"| Patterns | {len(schema.patterns):,} | {len(counts.patterns):,} |", ""]
    if by_reason:
        lines += ["Deferred:", "", "| Kind | Reason | Schema entries |", "|---|---|---:|"]
        lines += [f"| {k} | {r} | {n:,} |" for (k, r), n in sorted(by_reason.items())]
        lines.append("")
    lines += compare.report_lines(comparison, comparison["hand_schema"], SHOW)
    lines += [f"Schema entries backed by one maintainer only (may be that maintainer's house style): "
              f"{len(schema.single_maintainer):,}.", "",
              "Entity classes with the most support:", "",
              "| Entity class | Support | Maintainers | Examples |", "|---|---:|---:|---|"]
    lines += [f"| {_cell(c['name'])} | {c['support']} | {len(c['maintainers'])} | "
              f"{_cell(', '.join(c['examples']))} |" for c in schema.entity_classes[:15]]

    return Results(
        files=[schema_path, evidence_path],
        headline={"entity classes": len(schema.entity_classes), "predicates": len(schema.predicates),
                  "patterns": len(schema.patterns)},
        details="\n".join(lines),
        warnings=warnings,
    )
