"""
moves.py -- the main moves of 060_extract, as called by 060_extract.py.

    stage 1  records.py  pick_records   code: which records this run extracts from; notes to show before paying
    stage 2  schema.py   load_schema    code: the schema input plus the additions, merged; notes
    -        (here)      paid_calls     code: asks before paying; keeps every answer in cache/
    stage 3  extract.py  ask_model      LLM: the facts each record states that the schema can express
    stage 4  extract.py  sort_rows      code: every row checked; kept, or removed with its reason
    -        (here)      results        writes the kept and removed triple instances, the schema used; the report

Every model answer is cached in cache/ inside the step's output folder
(common/cache.py), so a rerun pays only for what isn't there yet. Every file is
rewritten by each run: it holds that run's records only. Terms are as defined in docs/terminology.md.
"""
from __future__ import annotations

import extract as extract_stage
import records as records_stage
import schema as schema_stage
from common import audit, llm
from common.audit import ORIGIN_COLUMN, check_origins, log
from common.files import write_csv, write_json
from common.report import cell, counted, model_calls, named
from common.step import Results
from common.triples_io import COLUMNS as TRIPLE_COLUMNS, ENTRY_PREDICATE

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
            entry = {"name": name, "definition": definition, "from": came_from[kind][name]}
            if name in schema.sources[kind]:
                entry["source"] = schema.sources[kind][name]
            out.append(entry)
        return out
    return {"entity_classes": entries("entity_classes"), "predicates": entries("predicates"),
            "patterns": [{"pattern": list(p), "from": came_from["patterns"][p]} for p in content["patterns"]],
            "left_out_additions": schema.left_out,
            "made": {"run_id": audit.current_run_id(), "schema": schema.files["schema"],
                     "additions": schema.files["additions"]}}


def _new_names(chosen, rows, settings) -> tuple:
    """The names outside the schema the model used, most used first, and in
    words where they come from. On a run over every record, records of the
    ground truth are left out of the counts: names seen only there would be
    learned from the records 070 scores (see instructions/060_extract.md)."""
    all_records = settings["extract_from"] == "all" and not settings["ids"].strip()
    listed = []
    for (kind, name), v in rows.new_names.items():
        recs = [r for r in v["records"] if not (all_records and r in chosen.ground_truth)]
        if recs and name:
            listed.append({"kind": kind, "name": name, "records": len(recs)})
    listed.sort(key=lambda x: (-x["records"], x["kind"], x["name"]))
    where = ("records outside the ground truth" if all_records else
             "the ground truth records" if settings["extract_from"] == "ground_truth" and not settings["ids"].strip()
             else "the records listed in ids")
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
    new_names, where = _new_names(chosen, rows, settings)

    paths = {name: output / name for name in (KEPT_NAME, REMOVED_NAME, SCHEMA_NAME, DETAILS_NAME)}
    write_csv(paths[KEPT_NAME], KEPT_COLUMNS, kept)
    write_csv(paths[REMOVED_NAME], REMOVED_COLUMNS, removed)
    write_json(paths[SCHEMA_NAME], _schema_used(schema))
    write_json(paths[DETAILS_NAME], {
        "made": {"run_id": audit.current_run_id(), "model": llm.MODEL, "settings": settings},
        "chosen": chosen.how,
        "records": [{"id": i["id"], "pieces": len(i["pieces"]),
                     "status": "extracted" if i["id"] in rows.kept else "failed",
                     "error": replies.failed.get(i["id"]),
                     "kept": len(rows.kept.get(i["id"], [])), "removed": len(rows.removed.get(i["id"], []))}
                    for i in chosen.items],
        "skipped_while_choosing": chosen.skipped,
        "new_names": {"counted_over": where, "names": new_names},
    })
    log.info(f"  wrote {KEPT_NAME}, {REMOVED_NAME}, {SCHEMA_NAME}, {DETAILS_NAME}")

    warnings = list(chosen.notes) + list(schema.notes)       # shown before paying too, if the run paid
    if replies.failed:
        warnings.append(f"{len(replies.failed)} record(s) failed and are not in the output: "
                        f"{named(list(replies.failed), 3)}. "
                        f"Run the step again: only those are asked again; every answer already paid for is reused.")
    missing = check_origins(kept + removed, "rows")
    if missing:
        warnings.append(missing)

    n_kept_facts = sum(1 for r in kept if r["predicate"] != ENTRY_PREDICATE)
    only_describes = sum(1 for rid, rs in rows.kept.items() if len(rs) == 1)
    added = {k: sum(v == "additions" for v in schema.came_from[k].values())
             for k in ("entity_classes", "predicates", "patterns")}
    c = schema.content
    lines = ["### What this run worked on", "",
             f"Chosen: {chosen.how}. Extracted: {len(rows.kept)}; failed: {len(replies.failed)}"
             + ("; skipped while choosing: " + "; ".join(f"{len(v)} {k}" for k, v in chosen.skipped.items())
                if chosen.skipped else "") + ".",
             f"{only_describes} record(s) state no fact the schema can express (only their DESCRIBES row).", "",
             "### Schema", "",
             f"`{schema.files['schema']}` plus `{schema.files['additions']}`: {len(c['entity_classes'])} entity "
             f"classes, {len(c['predicates'])} predicates, {len(c['patterns'])} patterns, of which added: "
             f"{added['entity_classes']} entity classes, {added['predicates']} predicates, {added['patterns']} "
             f"patterns. The schema used is in `{SCHEMA_NAME}`.", "",
             "### Triple instances", "",
             f"- Kept: {n_kept_facts:,} triple instances, plus one DESCRIBES row per record, in `{KEPT_NAME}`.",
             f"- Flags on kept rows (worth a look): {counted(rows.flags)}.",
             f"- Removed: {len(removed):,} ({counted(rows.reasons)}), in `{REMOVED_NAME}` with the reason. "
             f"`source_text`: its source text is missing or isn't in the record's text; "
             f"`name_not_in_schema`: it uses an entity class or predicate the schema doesn't have.", ""]
    if new_names:
        lines += [f"Names outside the schema the model used, counted over {where}, most used first. A name "
                  f"that keeps coming back may belong in `annotations/schema_additions.txt`"
                  + (" (names seen in ground truth records: see instructions/060_extract.md before adding "
                     "them)" if where != "records outside the ground truth" else "") + ":", "",
                  "| Kind | Name | Records |", "|---|---|---:|"]
        lines += [f"| {x['kind']} | {cell(x['name'])} | {x['records']} |" for x in new_names[:SHOW]]
        if len(new_names) > SHOW:
            lines.append(f"| … {len(new_names) - SHOW} more, in `{DETAILS_NAME}` | | |")
        lines.append("")
    lines += model_calls([("extract triple instances (one per text piece)", replies.calls, replies.reused)],
                         calls.paid.test_calls, llm.MODEL)

    return Results(
        files=list(paths.values()),
        headline={"records extracted": len(rows.kept), "triple instances kept": n_kept_facts},
        details="\n".join(lines),
        warnings=warnings,
    )
