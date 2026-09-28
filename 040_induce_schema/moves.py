"""
moves.py -- the main moves of 040_induce_schema, as called by
040_induce_schema.py. Each stage lives in its own file:

    stage 1  texts.py    pick_texts         the texts to learn from (030's induction candidates)
    -        (here)      paid_calls         asks before the first paid call; the answer cache
    stage 2  extract.py  extract_facts      LLM: the facts each text states, no schema imposed
    stage 3  label.py    label_names        LLM: one label per name, reusing the labels chosen so far
    stage 4  merge.py    merge_labels       LLM: one call over all labels, merging synonyms
    stage 5  count.py    count_support      code: the texts and maintainers behind every entry
    stage 6  define.py   write_definitions  LLM: one sentence per class and predicate
    stage 7  check.py    check_schema       code: builds the schema from the evidence, checks the words
    -        compare.py  compare_with_hand_schema  code: beside the hand-built schema, for the report
    -        (here)      results            writes the_schema.json, induction_evidence.json; report

Every model answer is cached in cache/ inside the step's output folder (see
cache.py), so a rerun pays only for what changed.
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
    paid: llm.PaidCalls          # asks before the first call, counts the calls
    cache_dir: Path              # where every answer is kept


# --------------------------------------------------------------------------

def pick_texts(inputs, settings):
    return texts_stage.pick_texts(inputs, settings)


def paid_calls(settings, output) -> Calls:
    return Calls(paid=llm.PaidCalls(confirm=settings["confirm_paid_calls"]), cache_dir=output / "cache")


def extract_facts(texts, calls, settings):
    return extract.extract_facts(texts, calls, settings)


def label_names(facts, calls):
    return label.label_names(facts, calls)


def merge_labels(labels, facts, calls):
    return merge.merge_labels(labels, facts, calls)


def count_support(facts, labels):
    return count.count_support(facts, labels)


def write_definitions(counts, settings, calls):
    return define.write_definitions(counts, settings, calls)


def check_schema(counts, definitions, settings):
    return check.check_schema(counts, definitions, settings)


def compare_with_hand_schema(inputs, schema) -> dict:
    hand = read_hand_schema(inputs["hand_schema"])
    comparison = compare.compare(hand, schema)
    comparison["hand_schema"] = ref_path(inputs["hand_schema"])
    c = comparison["classes"]
    log.info(f"  beside the hand-built schema: {len(c['both'])} classes in both, "
             f"{len(c['only_hand'])} only there, {len(c['only_induced'])} only induced")
    return comparison


# --------------------------------------------------------------------------

def _write_json(path: Path, data) -> None:
    tmp = path.with_suffix(".json.part")
    tmp.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8", newline="\n")
    os.replace(tmp, path)


def _cell(value) -> str:
    return "" if value is None else str(value).replace("|", "\\|").replace("\n", " ")


def results(texts, facts, labels, counts, definitions, schema, comparison, calls, settings, output) -> Results:
    made = {"run_id": audit.current_run_id(), "model": llm.MODEL, "settings": settings,
            "texts": len(texts.items), "maintainers": [m["maintainer"] for m in texts.maintainers]}
    schema_path, evidence_path = output / SCHEMA_NAME, output / EVIDENCE_NAME
    _write_json(schema_path, {"classes": schema.classes, "predicates": schema.predicates,
                              "patterns": schema.patterns, "deferred": schema.deferred, "made": made})
    calls_made = {"extract": facts.calls, "label": labels.calls, "merge": labels.merge_calls,
                  "define": definitions.calls, "test": calls.paid.test_calls}
    _write_json(evidence_path, {
        "made": made,
        "texts": [{**t, "pieces": len(next(x for x in texts.items if x["id"] == t["id"])["pieces"])}
                  for t in facts.texts],
        "labels": labels.of, "vocabulary": labels.vocabulary, "label_batches": labels.batches,
        "unlabeled": labels.unlabeled, "merges": labels.merges, "merge_issues": labels.merge_issues,
        "spelling_folds": counts.spelling_folds, "unlabeled_slots": counts.unlabeled_slots,
        "counts": {"classes": counts.classes, "predicates": counts.predicates, "patterns": counts.patterns},
        "definitions": definitions.of, "too_vague": definitions.too_vague,
        "unknown_names": definitions.unknown, "missing_definitions": schema.missing_definitions,
        "calls": {**calls_made, "reused_extractions": facts.reused},
        "compared_with_hand_schema": comparison,
    })
    log.info(f"  wrote {SCHEMA_NAME} and {EVIDENCE_NAME}")

    warnings = []
    failed = [(t["id"], p) for t in facts.texts for p in t["failed_pieces"]]
    if failed:
        warnings.append(f"{len(failed)} text piece(s) failed extraction, so their facts are missing "
                        f"({', '.join(f'{i} piece {p + 1}' for i, p in failed[:3])}"
                        f"{' …' if len(failed) > 3 else ''}). Rerun: only those are asked again.")
    no_facts = [t["id"] for t in facts.texts if not t["triples"] and not t["failed_pieces"]]
    if no_facts:
        warnings.append(f"{len(no_facts)} text(s) gave no facts at all: {', '.join(no_facts[:3])}"
                        f"{' …' if len(no_facts) > 3 else ''}.")
    unlabeled = sum(len(v) for v in labels.unlabeled.values())
    if unlabeled:
        warnings.append(f"{unlabeled} name(s) were left unlabeled even after a second try; they count "
                        f"toward no class or predicate. Listed in {EVIDENCE_NAME} under unlabeled.")
    issues = {k: sum(len(v[k]) for v in labels.merge_issues.values())
              for k in ("into_not_a_label", "not_sent", "merged_twice")}
    if any(issues.values()):
        warnings.append(f"The merge reply had items code ignored: {issues['into_not_a_label']} merge(s) "
                        f"into a name that isn't a label, {issues['not_sent']} label(s) that weren't sent, "
                        f"{issues['merged_twice']} label(s) merged twice (the first merge kept). Listed in "
                        f"{EVIDENCE_NAME} under merge_issues.")
    if schema.missing_definitions:
        warnings.append(f"{len(schema.missing_definitions)} schema entr{'ies have' if len(schema.missing_definitions) != 1 else 'y has'} "
                        f"no definition (the model didn't return one); they stay in the schema. "
                        f"Rerun to ask again after deleting cache/define.json.")
    if definitions.unknown:
        warnings.append(f"The definition replies named {len(definitions.unknown)} entr(ies) that weren't "
                        f"sent; ignored. Listed in {EVIDENCE_NAME} under unknown_names.")
    for items, what in ((schema.classes, "classes"), (schema.predicates, "predicates"),
                        (schema.patterns, "patterns")):
        missing = check_origins(items, what)
        if missing:
            warnings.append(missing)

    total_calls = sum(calls_made.values())
    n_facts = sum(len(t["triples"]) for t in facts.texts)
    split = sum(len(t["pieces"]) > 1 for t in texts.items)
    lines = [
        "### Texts", "",
        f"{len(texts.items)} texts: the first {settings['texts_per_maintainer']} induction candidates of "
        f"each of the {len(texts.maintainers)} largest maintainers"
        + (f"; {split} were split into pieces" if split else "") + ".", "",
        "| Maintainer | Records | Texts used |", "|---|---:|---:|"]
    lines += [f"| {_cell(m['maintainer'])} | {m['records']:,} | {m['taken']} |" for m in texts.maintainers]
    lines += ["", "### Model calls", "",
              "| Stage | Calls |", "|---|---:|",
              f"| 2 extract facts | {facts.calls} (+{facts.reused} answered from the cache) |",
              f"| 3 label names | {labels.calls} |", f"| 4 merge labels | {labels.merge_calls} |",
              f"| 6 write definitions | {definitions.calls} |", f"| test call | {calls.paid.test_calls} |",
              f"| **total paid this run** | **{total_calls}** |", "",
              f"Model: `{llm.MODEL}`. Answers are kept in `cache/`; a rerun pays only for what changed.", "",
              "### Facts and labels", "",
              f"- {n_facts:,} verified facts from {counts.texts_with_facts} texts: each one's passage is "
              f"in its record's text (checked in code, `common/validate.py`).",
              f"- Left out as unverified: {sum(facts.errors.values()):,} "
              f"({', '.join(f'{k} {v:,}' for k, v in sorted(facts.errors.items())) or 'none'}); "
              f"listed in `{EVIDENCE_NAME}` under each text's `unverified`.",
              f"- Kept, with flags worth a look: "
              f"{', '.join(f'{k} {v:,}' for k, v in sorted(facts.flags.items())) or 'none'}.",
              f"- {facts.malformed:,} item(s) in the replies weren't complete facts and were dropped.",
              f"- Names labeled: {len(labels.of.get('entities', {})):,} names with "
              f"{len(labels.vocabulary.get('entities', [])):,} class labels; "
              f"{len(labels.of.get('predicates', {})):,} predicates with "
              f"{len(labels.vocabulary.get('predicates', [])):,} predicate labels.",
              f"- Merged in stage 4: {len(labels.merges)} label(s) (all listed below).",
              f"- Folded by spelling in stage 5: {len(counts.spelling_folds)} group(s).", ""]
    if labels.merges:
        lines += ["Merges (check these: a wrong merge makes two ideas one):", "",
                  "| Kind | Label | Merged into | Names | Texts |", "|---|---|---|---:|---:|"]
        lines += [f"| {m['kind']} | {_cell(m['label'])} | {_cell(m['into'])} | {m['names']} | {m['texts']} |"
                  for m in labels.merges]
        lines.append("")
    if counts.spelling_folds:
        lines += ["Spelling folds: " + "; ".join(f"{' · '.join(f['folded'])} → {f['into']}"
                                                  for f in counts.spelling_folds[:SHOW])
                  + (" …" if len(counts.spelling_folds) > SHOW else ""), ""]
    by_reason = {}
    for d in schema.deferred:
        reason = d["reason"].split(":")[0] if d["reason"].startswith("too vague") else \
            ("below min_support" if d["reason"].startswith("support") else "through an entry not in the schema")
        by_reason[(d["kind"], reason)] = by_reason.get((d["kind"], reason), 0) + 1
    lines += ["### Schema", "",
              f"min_support = {settings['min_support']}: an entry enters the schema if it appears in at "
              f"least that many texts.", "",
              "| | In the schema | Found |", "|---|---:|---:|",
              f"| Classes | {len(schema.classes):,} | {len(counts.classes):,} |",
              f"| Predicates | {len(schema.predicates):,} | {len(counts.predicates):,} |",
              f"| Patterns | {len(schema.patterns):,} | {len(counts.patterns):,} |", ""]
    if by_reason:
        lines += ["Deferred:", "", "| Kind | Reason | Entries |", "|---|---|---:|"]
        lines += [f"| {k} | {r} | {n:,} |" for (k, r), n in sorted(by_reason.items())]
        lines.append("")
    lines += compare.report_lines(comparison, comparison["hand_schema"], SHOW)
    lines += [f"Entries in the schema backed by one maintainer only (may be that maintainer's house "
              f"style): {len(schema.single_maintainer):,}.", "",
              "Most supported classes:", "", "| Class | Texts | Maintainers | Examples |", "|---|---:|---:|---|"]
    lines += [f"| {_cell(c['name'])} | {c['support']} | {len(c['maintainers'])} | "
              f"{_cell(', '.join(c['examples']))} |" for c in schema.classes[:15]]

    return Results(
        files=[schema_path, evidence_path],
        headline={"classes": len(schema.classes), "predicates": len(schema.predicates),
                  "patterns": len(schema.patterns)},
        details="\n".join(lines),
        warnings=warnings,
    )
