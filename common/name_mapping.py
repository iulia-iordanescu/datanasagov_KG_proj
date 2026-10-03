"""
common/name_mapping.py -- the translation table, annotations/name_mapping.csv:
which name of the ground truth vocabulary each name of the current schema
(the one step 060 used) means.

    kind,name_in_crt_schema,name_in_gtt,swap_subject_and_object,checked
    entity class,Satellite,Spacecraft,no,yes
    predicate,CARRIES,ABOARD,yes,yes        <- "A CARRIES B" is "B ABOARD A"
    entity class,Gadget,(none),no,yes        <- nothing in the ground truth means this

    kind                     "entity class" or "predicate"
    name_in_crt_schema       the name in the current schema
    name_in_gtt              the name in the ground truth triples (the ground
                             truth vocabulary), or (none)
    swap_subject_and_object  predicates only: "yes" when the ground truth's
                             name states the relation the other way round
    checked                  "same name" (added by code: the names are equal),
                             "no" (proposed by the model, not checked yet),
                             "yes" (checked by a person)

Step 070 adds rows and reads them; the annotation tool shows them and saves
a person's changes. Both use the definitions here.
"""
from __future__ import annotations

import csv
from pathlib import Path

from common.step import ANNOTATIONS_DIR

MAPPING_PATH = ANNOTATIONS_DIR / "name_mapping.csv"
COLUMNS = ["kind", "name_in_crt_schema", "name_in_gtt", "swap_subject_and_object", "checked"]
KINDS = {"entity class": "entity_classes", "predicate": "predicates"}   # {kind: the schema's key}
NONE = "(none)"
CHECKED = ("yes", "same name")                                          # what 070 accepts as checked


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
