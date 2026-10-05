"""
common/common_helpers/name_mapping.py -- the translation table, annotations/name_mapping.csv:
which name of the ground truth vocabulary each name of the current schema
(the one step 060 used) means.

    kind,name_from_past_or_crt_schema,name_in_gtt,swap_subject_and_object,checked,definition_from_past_or_crt_schema
    entity class,Satellite,Spacecraft,no,yes,A craft that orbits a body.
    predicate,CARRIES,ABOARD,yes,yes,Has on board.   <- "A CARRIES B" is "B ABOARD A"
    entity class,Gadget,(none),no,yes,A small device. <- nothing in the ground truth means this

    kind                     "entity class" or "predicate"
    name_from_past_or_crt_schema
                             a name of a schema step 060 used, in this run or
                             an earlier one (crt: current): one table serves
                             every schema, so rows accumulate
    name_in_gtt              the name in the ground truth triples (gtt: the
                             ground truth vocabulary), or (none)
    swap_subject_and_object  predicates only: "yes" when the ground truth's
                             name states the relation the other way round
    checked                  "same name" (added by code: the names are equal),
                             "no" (proposed by the model, not checked yet),
                             "yes" (checked by a person)
    definition_from_past_or_crt_schema
                             that schema's definition of the name when the row
                             was written or last checked

A row is only as good as the meaning it was checked against: a later schema
may use the same name for something else. So a checked row whose stored
definition differs from the current schema's (spacing aside) is STALE:
step 070 won't score until a person checks it again, and the annotation tool
shows both definitions. Checking it again stores the current definition.

One name, one row: two rows with the same kind and the same
name_from_past_or_crt_schema (compared like every name, ignoring case and
punctuation) would leave it open which translation counts. Step 070 never
writes such a pair; a hand edit can. repeats() finds them: step 070 stops
until they're gone, and the annotation tool lets a person delete the extra
ones (the only rows it can delete).

Step 070 adds rows and reads them; the annotation tool shows them and saves
a person's changes. Both use the definitions here.
"""
from __future__ import annotations

import csv
from pathlib import Path

from common.step import ANNOTATIONS_DIR
from common.triples_io import label_key

MAPPING_PATH = ANNOTATIONS_DIR / "name_mapping.csv"
COLUMNS = ["kind", "name_from_past_or_crt_schema", "name_in_gtt", "swap_subject_and_object", "checked",
           "definition_from_past_or_crt_schema"]
KINDS = {"entity class": "entity_classes", "predicate": "predicates"}   # {kind: the schema's key}
NONE = "(none)"
CHECKED = ("yes", "same name")                                          # what 070 accepts as checked


def crt_definitions(schema_used: dict) -> dict:
    """{kind: {label_key(name): definition}} of the current schema
    (step 060's schema_used.json, as read with json)."""
    return {kind: {label_key(e["name"]): e.get("definition") or "" for e in schema_used.get(key, [])}
            for kind, key in KINDS.items()}


def is_stale(row: dict, definitions: dict) -> bool:
    """True if the row's stored definition differs from the current
    schema's definition of its name (spacing aside)."""
    now = definitions.get(row["kind"], {}).get(label_key(row["name_from_past_or_crt_schema"]), "")
    return " ".join(row["definition_from_past_or_crt_schema"].split()) != " ".join(now.split())


def repeats(rows: list) -> list:
    """Names with more than one row: [{"kind", "name", "lines": [file line
    numbers]}], in the order first met."""
    found = {}
    for r in rows:
        key = (r["kind"], label_key(r["name_from_past_or_crt_schema"]))
        found.setdefault(key, {"kind": r["kind"], "name": r["name_from_past_or_crt_schema"], "lines": []})
        found[key]["lines"].append(r["_line"])
    return [v for v in found.values() if len(v["lines"]) > 1]


def read_mapping(path: Path = MAPPING_PATH) -> list:
    """Every row with a name_from_past_or_crt_schema, in the file's order, each
    value trimmed, plus "_line": its line in the file (the header is line 1;
    never written back). Stops if a column is missing."""
    with open(path, encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        missing = [c for c in COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"{Path(path).name} lacks the column(s) {', '.join(missing)}")
        rows = []
        for r in reader:
            if (r.get("name_from_past_or_crt_schema") or "").strip():
                rows.append({**{c: (r.get(c) or "").strip() for c in COLUMNS}, "_line": reader.line_num})
        return rows
