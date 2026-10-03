"""
common/name_mapping.py -- the translation table, annotations/name_mapping.csv:
which name of the ground truth vocabulary each name of the current schema
(the one step 060 used) means.

    kind,name_in_crt_schema,name_in_gtt,swap_subject_and_object,checked,definition_in_crt_schema_when_checked
    entity class,Satellite,Spacecraft,no,yes,A craft that orbits a body.
    predicate,CARRIES,ABOARD,yes,yes,Has on board.   <- "A CARRIES B" is "B ABOARD A"
    entity class,Gadget,(none),no,yes,A small device. <- nothing in the ground truth means this

    kind                     "entity class" or "predicate"
    name_in_crt_schema       the name in the current schema
    name_in_gtt              the name in the ground truth triples (the ground
                             truth vocabulary), or (none)
    swap_subject_and_object  predicates only: "yes" when the ground truth's
                             name states the relation the other way round
    checked                  "same name" (added by code: the names are equal),
                             "no" (proposed by the model, not checked yet),
                             "yes" (checked by a person)
    definition_in_crt_schema_when_checked
                             the current schema's definition of the name when
                             the row was written or last checked

A row is only as good as the meaning it was checked against: a later schema
may use the same name for something else. So a checked row whose stored
definition differs from the current schema's (spacing aside) is STALE:
step 070 won't score until a person checks it again, and the annotation tool
shows both definitions. Checking it again stores the current definition.

Step 070 adds rows and reads them; the annotation tool shows them and saves
a person's changes. Both use the definitions here.
"""
from __future__ import annotations

import csv
from pathlib import Path

from common.step import ANNOTATIONS_DIR
from common.triples_io import label_key

MAPPING_PATH = ANNOTATIONS_DIR / "name_mapping.csv"
COLUMNS = ["kind", "name_in_crt_schema", "name_in_gtt", "swap_subject_and_object", "checked",
           "definition_in_crt_schema_when_checked"]
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
    now = definitions.get(row["kind"], {}).get(label_key(row["name_in_crt_schema"]), "")
    return " ".join(row["definition_in_crt_schema_when_checked"].split()) != " ".join(now.split())


def read_mapping(path: Path = MAPPING_PATH) -> list:
    """Every row with a name_in_crt_schema, in the file's order, each value
    trimmed. Stops if a column is missing."""
    with open(path, encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        missing = [c for c in COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"{Path(path).name} lacks the column(s) {', '.join(missing)}")
        return [{c: (r.get(c) or "").strip() for c in COLUMNS} for r in reader
                if (r.get("name_in_crt_schema") or "").strip()]
