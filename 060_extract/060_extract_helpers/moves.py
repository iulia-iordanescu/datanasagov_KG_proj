"""
moves.py -- the main moves of 060_extract, as called by 060_extract/run.py.

    stage 1  records.py  pick_records   code: which records this run extracts from; notes to show before paying
    stage 2  schema.py   load_schema    code: the schema file plus the schema additions, merged; notes
    -        (here)      paid_calls     code: asks before paying; keeps every answer in cache/
    stage 3  extract.py  ask_model      LLM: the facts each record states that the schema can express
    stage 4  extract.py  sort_rows      code: every row checked; kept, or removed with its reason
    -        (here)      results        writes extracted_triples.csv, extracted_triples_removed.csv, schema_used.json, and extracted_triples_details.json; the report

Every model answer is cached in cache/ inside the step's output folder
(common/common_helpers/cache.py), so a rerun pays only for what isn't there yet. Every file is
rewritten by each run: it holds that run's records only. Terms are as defined in docs/terminology.md.
"""
from __future__ import annotations

import extract as extract_stage
import records as records_stage
import schema as schema_stage
from common import audit, extraction, llm
from common.audit import ORIGIN_COLUMN, check_origins, log
from common.files import write_csv, write_json
from common.report import cell, counted, model_calls, named, per_text_headline, per_text_table
from common.step import Results
from common.triples_io import COLUMNS as TRIPLE_COLUMNS, ENTRY_PREDICATE
from common.ground_truth import HELD_OUT, TUNING

KEPT_NAME = "extracted_triples.csv"
REMOVED_NAME = "extracted_triples_removed.csv"
SCHEMA_NAME = "schema_used.json"
DETAILS_NAME = "extracted_triples_details.json"
KEPT_COLUMNS = TRIPLE_COLUMNS + ["flags", ORIGIN_COLUMN]
REMOVED_COLUMNS = ["reason"] + TRIPLE_COLUMNS + ["flags", "raw", ORIGIN_COLUMN]
SHOW = 20                        # rows listed in the report before "…"


# --------------------------------------------------------------------------

def pick_records(inputs, settings):
    return records_stage.pick_records(inputs, settings)


def load_schema(inputs):
    return schema_stage.load_schema(inputs)


def paid_calls(chosen, schema, settings, output) -> llm.Calls:
    return llm.paid_calls(settings, output, notes=chosen.notes + schema.notes)


def ask_model(chosen, schema, calls, settings):
    return extract_stage.ask_model(chosen, schema, calls, settings)


def sort_rows(chosen, schema, replies):
    return extract_stage.sort_rows(chosen, schema, replies)


# --------------------------------------------------------------------------

def _schema_used(schema) -> dict:
    content, came_from = schema.content, schema.came_from

    def entries(kind):
        out = []
        for name, definition in content[kind].items():
            entry = {"component_class": name, "definition": definition, "from": came_from[kind][name]}
            if name in schema.sources[kind]:
                entry["source"] = schema.sources[kind][name]
            out.append(entry)
        return out
    return {"entity_classes": entries("entity_classes"), "predicates": entries("predicates"),
            "patterns": [{"pattern": list(p), "from": came_from["patterns"][p],
                          **({"source": schema.sources["patterns"][p]} if p in schema.sources.get("patterns", {}) else {})}
                         for p in content["patterns"]],
            "pinned": {p: [list(pair) for pair in pins] for p, pins in content.get("pinned", {}).items()},
            "left_out_additions": schema.left_out,
            "left_out_not_tuning": schema.not_tuning,
            "learned_from": schema.learned_from,
            "made": {"run_id": audit.current_run_id(), "schema": schema.files["schema"],
                     "additions": schema.files["additions"]}}


def _new_component_classes(chosen, rows, settings) -> tuple:
    """The component classes outside the schema the model used, most used
    first, and in words where they come from: ones it is fair to add to
    annotations/schema_additions.txt. Never counted: a HELD-OUT record (one
    learned there would let held-out records influence the schema). On a run over
    every record, no ground truth record at all (ones learned from records
    outside it are fair as they are). Otherwise, tuning records are counted
    and named by pool position, for the "source: ground truth tuning #N" line a schema
    entry of annotations/schema_additions.txt learned from them needs."""
    all_records = settings["extract_from"] == "all" and not settings["ids"].strip()
    listed = []
    for (kind, name), v in rows.new_component_classes.items():
        part = {r: chosen.pool.get(r, (None, None))[1] for r in v["records"]}
        recs = [r for r in v["records"] if part[r] != HELD_OUT and not (all_records and r in chosen.ground_truth)]
        if not (recs and name):
            continue
        tuning = sorted(chosen.pool[r][0] for r in recs if r in chosen.ground_truth and part[r] == TUNING)
        source = ("ground truth tuning " + ", ".join(f"#{p}" for p in tuning) if tuning else
                  "extraction over records not annotated")
        listed.append({"kind": kind, "component_class": name, "records": len(recs), "source": source})
    listed.sort(key=lambda x: (-x["records"], x["kind"], x["component_class"]))
    where = ("records outside the ground truth" if all_records else
             "the tuning records of the ground truth" if settings["extract_from"] == "ground_truth"
             and not settings["ids"].strip() else "the records listed in ids, held-out ones left out")
    return listed, where


def results(chosen, schema, replies, rows, calls, settings, output) -> Results:
    origin_of = {i["id"]: audit.origin("records", i["id"]) for i in chosen.items}
    kept = [{**{c: r.get(c, "") for c in TRIPLE_COLUMNS}, "flags": " ".join(r["flags"]),
             ORIGIN_COLUMN: origin_of[rid]}
            for rid in rows.kept for r in rows.kept[rid]]
    removed = [{**{c: x.get(c, "") for c in TRIPLE_COLUMNS}, "id": rid, "reason": x["reason"],
                "flags": " ".join(x.get("errors", []) + x.get("flags", [])), "raw": x.get("raw", ""),
                ORIGIN_COLUMN: origin_of[rid]}
               for rid in rows.removed for x in rows.removed[rid]]
    new_component_classes, where = _new_component_classes(chosen, rows, settings)

    paths = {name: output / name for name in (KEPT_NAME, REMOVED_NAME, SCHEMA_NAME, DETAILS_NAME)}
    write_csv(paths[KEPT_NAME], KEPT_COLUMNS, kept)
    write_csv(paths[REMOVED_NAME], REMOVED_COLUMNS, removed)
    write_json(paths[SCHEMA_NAME], _schema_used(schema))
    write_json(paths[DETAILS_NAME], {
        "made": {"run_id": audit.current_run_id(), **llm.describe(), "settings": settings},
        "chosen": chosen.how,
        "records": [{"id": i["id"], "pieces": len(i["pieces"]),
                     "status": "extracted" if i["id"] in rows.kept else "failed",
                     "error": replies.failed.get(i["id"]),
                     "kept": len(rows.kept.get(i["id"], [])), "removed": len(rows.removed.get(i["id"], []))}
                    for i in chosen.items],
        "skipped_while_choosing": chosen.skipped,
        "new_component_classes": {"counted_over": where, "component_classes": new_component_classes},
    })
    log.info(f"  wrote {KEPT_NAME}, {REMOVED_NAME}, {SCHEMA_NAME}, {DETAILS_NAME}")

    warnings = list(chosen.notes) + list(schema.notes)       # shown before paying too, if the run paid
    if replies.failed:
        warnings.append(extraction.failed_note(replies, "the output"))
    missing = check_origins(kept + removed, "rows")
    if missing:
        warnings.append(missing)

    n_kept_facts = sum(1 for r in kept if r["predicate"] != ENTRY_PREDICATE)
    # per text: kept (extracted triples), and raw = kept + removed by a check (not extraction.NOT_BY_A_CHECK:
    # build_rows' removals, which weren't triple instances or were the same classed triple again)
    kept_of = {rid: sum(1 for r in rows.kept[rid] if r["predicate"] != ENTRY_PREDICATE)
               for rid in (i["id"] for i in chosen.items) if rid in rows.kept}
    checked_out = {rid: sum(1 for x in rows.removed.get(rid, []) if x["reason"] not in extraction.NOT_BY_A_CHECK)
                   for rid in kept_of}
    per_text = [("raw (everything the model listed: kept + removed by a check)",
                 [kept_of[rid] + checked_out[rid] for rid in kept_of]),
                ("kept (extracted triples)", list(kept_of.values()))]
    only_describes = sum(1 for rid, rs in rows.kept.items() if len(rs) == 1)
    added = {k: sum(v == "additions" for v in schema.came_from[k].values())
             for k in ("entity_classes", "predicates", "patterns")}
    c = schema.content
    lines = ["### What this run worked on", "",
             f"Chosen: {chosen.how}. Extracted: {len(rows.kept)}; failed: {len(replies.failed)}"
             + ("; skipped while choosing: " + "; ".join(f"{len(v)} {k}" for k, v in chosen.skipped.items())
                if chosen.skipped else "") + ".",
             f"{only_describes} record(s) state no fact the schema can express (only their describes triple).", "",
             "### Schema", "",
             f"`{schema.files['schema']}` plus `{schema.files['additions']}`: {len(c['entity_classes'])} entity "
             f"classes, {len(c['predicates'])} predicates, {len(c['patterns'])} patterns, of which added: "
             f"{added['entity_classes']} entity classes, {added['predicates']} predicates, {added['patterns']} "
             f"patterns. This run's schema, from now on the current schema, is in `{SCHEMA_NAME}`.", "",
             "### Extracted triples", "", *per_text_table("Classed triples per text", per_text), "",
             "One text is one record's text; its describes triple isn't counted. A classed triple two text pieces "
             "of a text both state counts once; items in the replies that weren't triple instances, and texts whose "
             "model call failed, aren't counted.", "",
             f"- Extracted triples: {n_kept_facts:,}, plus one describes triple per record, in `{KEPT_NAME}`.",
             f"- Flags on extracted triples (worth a look): {counted(rows.flags)}.",
             f"- Removed: {len(removed):,} ({counted(rows.reasons)}), in `{REMOVED_NAME}` with the reason. "
             f"`source_text`: its source text is missing or isn't in the record's text; "
             f"`component_class_not_in_schema`: it uses an entity class or predicate the schema doesn't have.", ""]
    if new_component_classes:
        lines += ["### Component classes outside the schema", "",
                  f"Component classes outside the schema (the current schema: the schema file plus "
                  f"the schema additions) the model used, counted over {where}, most used first (held-out records "
                  f"are never counted). One that keeps coming back, and that names a real type of thing or "
                  f"relationship, may be added to `annotations/schema_additions.txt`, with a one-line definition and "
                  f"the `source:` line given here: every component class listed is fair to add.", "",
                  "| Kind | Component class (used by the model; not in the current schema) | Records | source: line for "
                  "`annotations/schema_additions.txt` |", "|---|---|---:|---|"]
        lines += [f"| {x['kind']} | {cell(x['component_class'])} | {x['records']} | `source: {cell(x['source'])}` |"
                  for x in new_component_classes[:SHOW]]
        if len(new_component_classes) > SHOW:
            lines.append(f"| … {len(new_component_classes) - SHOW} more, in `{DETAILS_NAME}` | | | |")
        lines.append("")
    lines += model_calls([("stage 3: extract classed triples (one call per text piece)", replies.calls, replies.reused)],
                         calls.paid.test_calls, llm.model_label())

    return Results(
        files=list(paths.values()),
        headline={"records extracted": len(rows.kept),
                  **per_text_headline([("raw classed triples", per_text[0][1]),
                                       ("extracted triples", per_text[1][1])])},
        details="\n".join(lines),
        warnings=warnings,
    )
