"""
common/extraction.py -- what the steps that ask a model for a record's
triple instances WITH entity classes share: 050 (drafting ground truth) and
060 (extracting with a schema), so the one is scored against the other on
equal terms.

    rules_for(record)          the shared rules (prompts/extraction_rules.txt),
                               with the record's field names filled in
    REPLY                      the reply format (prompts/extraction_reply.txt)
    wrap(piece)                a text piece between BEGIN/END RECORD lines
    build_rows(...)            a record's replies -> checked rows + removed items

Each step keeps only what is its own: the top of its prompt and how it
chooses records. (040's extraction asks for no entity classes, since it
learns them; its prompt is its own.)

What build_rows does with a record's replies (one per text piece):

  1. the DESCRIBES row first (common/triples_io.py), with the first entity
     class a reply named for what the title names ("X" if none did);
  2. every item of every reply's "triples", cleaned by triples_io.clean_triple;
     one that can't be a triple instance (a missing subject, predicate or
     object, a list where text belongs, …) is removed as "malformed";
  3. the same subject, predicate, object and entity classes again (e.g.
     stated in two pieces) is removed as "duplicate"; the same triple
     instance with OTHER entity classes is kept, and both rows are flagged
     conflicting_classes;
  4. every row checked (common/validate.py) against the record's WHOLE
     text: errors (no_source_text, source_not_in_text, describes_*) and
     flags (reworded names, names not in the schema, …).

Nothing is dropped for an error or a flag: that's for the person (050) or
the step (060) to decide. Terms: docs/terminology.md.
"""
from __future__ import annotations

import json
from pathlib import Path

from common import llm
from common.chunking import text_fields
from common.prompt_files import fill, load
from common.text_match import Text
from common.triples_io import (clean_triple, describes_row, label_key, triple_key)
from common.validate import SchemaNames, check_against_schema, check_describes, check_triple_instance

PROMPTS = Path(__file__).parent / "prompts"
RULES = load(PROMPTS / "extraction_rules.txt")
REPLY = load(PROMPTS / "extraction_reply.txt")
BEGIN_LINE, END_LINE = "----- BEGIN RECORD -----", "----- END RECORD -----"
ROW_KEYS = ("subject", "subject_class", "predicate", "object", "object_class", "source_text")


def rules_for(record: dict) -> str:
    return fill(RULES, field_names=", ".join(f'"{n}:"' for n in text_fields(record)))


def wrap(piece: str) -> str:
    """A text piece as the prompt's $text: any line that copies END_LINE is
    defanged, so the record can't close its own fence."""
    return llm.fence_safe(piece, END_LINE)


def build_rows(record_id: str, title: str, text: str, replies: list, names: SchemaNames) -> tuple:
    """(rows, removed). rows: the DESCRIBES row, then one per triple
    instance, each {"id", ROW_KEYS…, "errors": [...], "flags": [...]}.
    removed: {"reason": "malformed" | "duplicate", "raw" or the row}."""
    removed = []
    named = [str(r.get("describes_class") or "").strip() for r in replies if isinstance(r, dict)]
    head = describes_row(record_id, title, next((c for c in named if c), ""))
    errors, flags = check_describes(head, record_id, names)
    rows = [{**head, "errors": errors, "flags": flags}]

    whole = Text(text)
    seen = {}                                   # triple key -> (first row, {entity class pairs})
    for reply in replies:
        items = reply.get("triples") if isinstance(reply, dict) else None
        if not isinstance(items, list):
            removed.append({"reason": "malformed", "raw": json.dumps(reply, ensure_ascii=False)})
            continue
        for item in items:
            t = clean_triple(item)
            if t is None:
                removed.append({"reason": "malformed", "raw": json.dumps(item, ensure_ascii=False)})
                continue
            row = {"id": record_id, **{k: t.get(k, "") for k in ROW_KEYS}}
            k = triple_key(row)
            pair = (label_key(row["subject_class"]), label_key(row["object_class"]))
            if k in seen and pair in seen[k][1]:
                removed.append({"reason": "duplicate", **row})
                continue
            errors, flags = check_triple_instance(row, whole, title)
            flags = flags + check_against_schema(row, names)
            if k in seen:                       # same triple instance, other entity classes
                flags.append("conflicting_classes")
                first = seen[k][0]
                if "conflicting_classes" not in first["flags"]:
                    first["flags"].append("conflicting_classes")
                seen[k][1].add(pair)
            else:
                seen[k] = (None, {pair})
            row.update(errors=errors, flags=flags)
            seen[k] = (seen[k][0] or row, seen[k][1])
            rows.append(row)
    return rows, removed
