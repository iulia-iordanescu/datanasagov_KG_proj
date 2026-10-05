"""
extract.py -- stages 3 and 4: the model extracts each record's triple
instances with the schema; code checks them and sorts them into kept and
removed.

Stage 3, ask_model. One call per text piece (a long record is split:
common/common_helpers/chunking.py). The prompt (prompts/extract.txt) asks for ONLY the
facts the schema can express, in ONLY the schema's names; its rules and
reply format are 050's (common/common_prompts/), so what 060 extracts and the
ground truth 050 drafted are asked for the same way. The calls are made by
common/common_helpers/extraction.ask_model: every answer is cached, a rerun pays only for
what it doesn't have, and a record with a failed call is left out whole.

Stage 4, sort_rows. common/common_helpers/extraction.build_rows turns each record's
replies into rows (the DESCRIBES row first; malformed items and repeats
removed) and checks every row against the record's whole text and the
schema. Then:

    REMOVED, with the reason (extracted_triples_removed.csv)
      source_text           its source text is missing, or isn't in the
                            record's text: it can't be verified and may be
                            invented (checks no_source_text, source_not_in_text)
      name_not_in_schema    an entity class or predicate the schema doesn't
                            have, though the prompt allows only the schema's
                            names (checks *_class_not_in_schema,
                            predicate_not_in_schema)
      duplicate, malformed  as in 050

    KEPT (extracted_triples.csv), with its flags, its entity classes and
    predicate in the schema's own spelling (a name is compared loosely, so
    "Space craft" is accepted as Spacecraft, and written Spacecraft)
      everything else, including a pattern the schema doesn't list
      (pattern_not_in_schema: the schema's patterns are what was seen, not
      all that is allowed) and a reworded name

    The DESCRIBES row is always kept, so every record extracted has one
    (a record with nothing else "states no fact the schema can express").
    If the model named no entity class for it, or one the schema doesn't
    have, its class is X and the row is flagged.

Names outside the schema are counted (new_names), so the report can list
the ones the model reaches for most: candidates for schema_additions.txt.
"""
from __future__ import annotations

import collections
from dataclasses import dataclass, field
from pathlib import Path

from common import extraction, prompt_files
from common.audit import log
from common.prompt_files import fill, load
from common.triples_io import UNDECIDED, is_describes

PROMPTS_DIR = Path(__file__).resolve().parents[1] / "060_extract_prompts"   # 060_extract/060_extract_prompts/
PROMPT = load(PROMPTS_DIR / "extract.txt")

#: Checks that remove a row, and the reason written for it.
REMOVE = {"no_source_text": "source_text", "source_not_in_text": "source_text",
          "subject_class_not_in_schema": "name_not_in_schema", "object_class_not_in_schema": "name_not_in_schema",
          "predicate_not_in_schema": "name_not_in_schema"}
SLOTS_OF = {"subject_class_not_in_schema": ("entity class", "subject_class"),
            "object_class_not_in_schema": ("entity class", "object_class"),
            "predicate_not_in_schema": ("predicate", "predicate"),
            "describes_class_not_in_schema": ("entity class", "object_class")}


@dataclass
class Rows:
    kept: dict = field(default_factory=dict)       # {id: [rows]}, DESCRIBES row first
    removed: dict = field(default_factory=dict)    # {id: [removed items, each with "reason"]}
    flags: dict = field(default_factory=dict)      # {check: kept rows that raised it}
    reasons: dict = field(default_factory=dict)    # {reason: rows removed for it}
    new_names: dict = field(default_factory=dict)  # {(kind, name): {"records": [ids]}}


def _in_schema_spelling(row: dict, names) -> dict:
    """A kept row with its entity classes and predicate written the way the
    schema writes them: names are compared loosely ("Space craft" is
    Spacecraft), but the output always uses the schema's spelling."""
    fixed = dict(row)
    for column, kind in (("subject_class", "entity_classes"), ("object_class", "entity_classes"),
                         ("predicate", "predicates")):
        fixed[column] = names.spelling[kind].get(names.key(row[column]), row[column])
    return fixed


def ask_model(chosen, schema, calls, settings: dict) -> extraction.Replies:
    def prompt_for(item, piece):
        return fill(PROMPT, schema=schema.text, rules=extraction.rules_for(chosen.records[item["id"]]),
                    reply=prompt_files.text(extraction.REPLY).strip(), text=extraction.wrap(piece))
    return extraction.ask_model(chosen.items, prompt_for, calls, settings["workers"], "extract",
                                f"060 will extract from {len(chosen.items)} record(s) ({chosen.how})",
                                "extracting")


def sort_rows(chosen, schema, replies) -> Rows:
    rows = Rows()
    flags, reasons = collections.Counter(), collections.Counter()
    new_names = collections.defaultdict(set)
    for item in chosen.items:
        rid = item["id"]
        if rid not in replies.of:
            continue
        built, removed = extraction.build_rows(rid, item["title"], item["text"], replies.of[rid], schema.names)
        kept = []
        for row in built:
            for check in row["errors"] + row["flags"]:
                if check in SLOTS_OF:
                    kind, column = SLOTS_OF[check]
                    new_names[(kind, row[column])].add(rid)
            if is_describes(row):
                row = _in_schema_spelling(row, schema.names)
                if row["errors"] or "describes_class_not_in_schema" in row["flags"]:
                    row["object_class"] = UNDECIDED           # no class of the schema named
                    row["flags"] = sorted(set(row["flags"]) | set(row["errors"]) | {"describes_undecided"})
                    row["errors"] = []
                kept.append(row)
                continue
            why = sorted({REMOVE[c] for c in row["errors"] + row["flags"] if c in REMOVE})
            if why:
                removed.append({"reason": " ".join(why), **row})
            else:
                kept.append(_in_schema_spelling(row, schema.names))
        for r in kept:
            flags.update(r["flags"])
        reasons.update(x["reason"] for x in removed)
        rows.kept[rid], rows.removed[rid] = kept, removed
    rows.flags, rows.reasons = dict(flags), dict(reasons)
    rows.new_names = {k: {"records": sorted(v)} for k, v in new_names.items()}
    log.info(f"  kept {sum(len(v) for v in rows.kept.values()):,} rows for {len(rows.kept)} record(s); "
             f"removed {sum(len(v) for v in rows.removed.values()):,} ({', '.join(f'{k} {n}' for k, n in sorted(reasons.items())) or 'none'})")
    return rows
