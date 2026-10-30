"""
extract.py -- stages 3 and 4: the model extracts each record's classed
triples with the schema; code checks them and sorts them into kept and
removed.

Stage 3, ask_model. One call per text piece (a long record is split:
common/common_helpers/chunking.py). The prompt (060_extract/060_extract_prompts/extract.txt) asks for ONLY the
facts the schema can express, with ONLY the schema's component classes; its rules and
reply format are 050's (common/common_prompts/), so what 060 extracts and the
ground truth 050 drafted are asked for the same way. The prompt asks the model
to work in two passes: first find every thing the record names, then state
the facts the record gives about each of them. This order of work is
TRACE-KG's (Abolhasani, Ba, He & Pan, "Traceable Context-Enriched Knowledge
Graph Generation with Induced Schemas", arXiv:2604.03496v3, sections 4.2 and
4.4), which first finds the things a text piece names and then, in a later
stage, the facts among them; here both passes are asked for in one call, and
the list isn't asked for in the reply, so the shared reply format is
unchanged. The calls are made by
common/common_helpers/extraction.ask_model: every answer is cached, a rerun pays only for
what it doesn't have, and a record with a failed call is left out whole.

Stage 4, sort_rows. common/common_helpers/extraction.build_rows turns each record's
replies into rows (the describes triple first; malformed items and repeats
removed) and checks every row against the record's whole text and the
schema. Then:

    REMOVED, with the reason (extracted_triples_removed.csv)
      source_text           its source text is missing, or isn't in the
                            record's text: it can't be verified and may be
                            invented (checks no_source_text, source_not_in_text)
      component_class_not_in_schema    an entity class or predicate the schema doesn't
                            have, though the prompt allows only the schema's
                            component classes (checks *_class_not_in_schema,
                            predicate_not_in_schema)
      duplicate, malformed  as in 050

    KEPT (extracted_triples.csv), with its flags, its entity classes and
    predicate in the schema's own spelling (each is compared by loose match, so
    "Space craft" is accepted as Spacecraft, and written Spacecraft)
      everything else, including a pattern the schema doesn't list
      (pattern_not_in_schema: the schema's patterns are what was seen, not
      all that is allowed) and a component class that is a loose match for one of the schema's

    The describes triple is always kept, so every record extracted has one
    (a record with nothing else "states no fact the schema can express").
    If the model named no describes class for it, or one the schema doesn't
    have, its describes class is X and the row is flagged.

Component classes outside the schema are counted (new_component_classes), so the report can list
the ones the model reaches for most: possible schema additions (schema_additions.txt).
"""
from __future__ import annotations

import collections
from dataclasses import dataclass, field
from pathlib import Path

from common import extraction
from common.audit import log
from common.prompt_files import load
from common.triples_io import UNDECIDED, is_describes
from common.validate import (DESCRIBES_CLASS_NOT_IN_SCHEMA, DESCRIBES_UNDECIDED, NO_SOURCE_TEXT, OBJECT_CLASS_NOT_IN_SCHEMA,
                             PREDICATE_NOT_IN_SCHEMA, SOURCE_NOT_IN_TEXT, SUBJECT_CLASS_NOT_IN_SCHEMA)

PROMPTS_DIR = Path(__file__).resolve().parents[1] / "060_extract_prompts"   # 060_extract/060_extract_prompts/
PROMPT = load(PROMPTS_DIR / "extract.txt")

#: Checks that remove a row, and the reason written for it.
REMOVE = {NO_SOURCE_TEXT: extraction.SOURCE_TEXT, SOURCE_NOT_IN_TEXT: extraction.SOURCE_TEXT,
          SUBJECT_CLASS_NOT_IN_SCHEMA: extraction.COMPONENT_CLASS_NOT_IN_SCHEMA,
          OBJECT_CLASS_NOT_IN_SCHEMA: extraction.COMPONENT_CLASS_NOT_IN_SCHEMA,
          PREDICATE_NOT_IN_SCHEMA: extraction.COMPONENT_CLASS_NOT_IN_SCHEMA}
SLOTS_OF = {SUBJECT_CLASS_NOT_IN_SCHEMA: ("entity class", "subject_class"),
            OBJECT_CLASS_NOT_IN_SCHEMA: ("entity class", "object_class"),
            PREDICATE_NOT_IN_SCHEMA: ("predicate", "predicate"),
            DESCRIBES_CLASS_NOT_IN_SCHEMA: ("entity class", "object_class")}


@dataclass
class Rows:
    kept: dict = field(default_factory=dict)       # {id: [rows]}, describes triple first
    removed: dict = field(default_factory=dict)    # {id: [removed items, each with "reason"]}
    flags: dict = field(default_factory=dict)      # {check: extracted triples that raised it}
    reasons: dict = field(default_factory=dict)    # {reason: rows removed for it}
    new_component_classes: dict = field(default_factory=dict)  # {(kind, component class): {"records": [ids]}}


def _in_schema_spelling(row: dict, schema_entries) -> dict:
    """An extracted triple with its entity classes and predicate written the way the
    schema writes them: they are compared loosely ("Space craft" is
    Spacecraft), but the output always uses the schema's spelling."""
    fixed = dict(row)
    for column, kind in (("subject_class", "entity_classes"), ("object_class", "entity_classes"),
                         ("predicate", "predicates")):
        fixed[column] = schema_entries.spelling[kind].get(schema_entries.key(row[column]), row[column])
    return fixed


def ask_model(chosen, schema, calls, settings: dict) -> extraction.Replies:
    def prompt_for(item, piece):
        return extraction.prompt(PROMPT, schema.text, chosen.records[item["id"]], piece)
    # Everything before the record (the instructions, the schema, the rules) is the same in every request, so it is
    # sent for prompt caching (common/common_helpers/llm.py, _messages).
    return extraction.ask_model(chosen.items, prompt_for, calls, settings["workers"], "extract",
                                f"060 will extract from {len(chosen.items)} record(s) ({chosen.how})",
                                "extracting", cache_until=extraction.BEGIN_LINE)


def sort_rows(chosen, schema, replies) -> Rows:
    rows = Rows()
    flags, reasons = collections.Counter(), collections.Counter()
    new_component_classes = collections.defaultdict(set)
    for item in chosen.items:
        rid = item["id"]
        if rid not in replies.of:
            continue
        built, removed = extraction.build_rows(rid, item["title"], item["text"], replies.of[rid], schema.schema_entries)
        kept = []
        for row in built:
            for check in row["errors"] + row["flags"]:
                if check in SLOTS_OF:
                    kind, column = SLOTS_OF[check]
                    new_component_classes[(kind, row[column])].add(rid)
            if is_describes(row):
                row = _in_schema_spelling(row, schema.schema_entries)
                if row["errors"] or DESCRIBES_CLASS_NOT_IN_SCHEMA in row["flags"]:
                    row["object_class"] = UNDECIDED           # no entity class of the schema named
                    row["flags"] = sorted(set(row["flags"]) | set(row["errors"]) | {DESCRIBES_UNDECIDED})
                    row["errors"] = []
                kept.append(row)
                continue
            why = [REMOVE[c] for c in row["errors"] + row["flags"] if c in REMOVE]
            if why:
                removed.append({"reason": extraction.joined_reason(why), **row})
            else:
                kept.append(_in_schema_spelling(row, schema.schema_entries))
        for r in kept:
            flags.update(r["flags"])
        reasons.update(x["reason"] for x in removed)
        rows.kept[rid], rows.removed[rid] = kept, removed
    rows.flags, rows.reasons = dict(flags), dict(reasons)
    rows.new_component_classes = {k: {"records": sorted(v)} for k, v in new_component_classes.items()}
    log.info(f"  kept {sum(len(v) for v in rows.kept.values()):,} extracted triples (describes triples included) for {len(rows.kept)} record(s); "
             f"removed {sum(len(v) for v in rows.removed.values()):,} ({', '.join(f'{k} {n}' for k, n in sorted(reasons.items())) or 'none'})")
    return rows
