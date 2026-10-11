"""
common/common_helpers/component_class_mapping.py -- the translation table, annotations/component_class_mapping.csv:
which component class of the ground truth vocabulary each component class of
the current schema (the one step 060 used) means.

    kind,component_class_from_past_or_crt_schema,component_class_in_gtt,swap_subject_and_object,checked,definition_from_past_or_crt_schema,definition_in_gtt
    entity class,Satellite,Spacecraft,no,yes,A craft that orbits a body.,A vehicle in space.
    predicate,CARRIES,ABOARD,yes,yes,Has on board.,Is carried on.   <- "A CARRIES B" is "B ABOARD A"
    entity class,Gadget,(none),no,yes,A small device.,            <- nothing in the ground truth means this

    kind                     "entity class" or "predicate"
    component_class_from_past_or_crt_schema
                             a component class of the current schema or of a
                             past schema (crt: current): one
                             table serves every schema, so rows accumulate
    component_class_in_gtt   a component class of the ground truth vocabulary
                             (gtt: ground truth triples), or (none)
    swap_subject_and_object  predicates only: "yes" when the ground truth's
                             predicate states the relation the other way round
    checked                  "same component class" (added by code: the two
                             component classes are equal),
                             "no" (proposed by the model, not checked yet),
                             "yes" (checked by a person)
    definition_from_past_or_crt_schema
                             that schema's definition of the component class
                             when the row was written or last checked
    definition_in_gtt        the hand-built schema's definition of
                             component_class_in_gtt when the row was written or
                             last checked (empty for (none), and for a
                             component class coined in the ground truth that
                             had no definition yet)

A row is only as good as the meanings it was checked against: a later schema
may give the same component class another meaning, and the hand-built schema
may give the ground truth vocabulary's component class another one. So a
checked row is STALE when (its definition_from_past_or_crt_schema differs from
the current schema's definition) or (its definition_in_gtt differs from the
hand-built schema's definition now), spacing aside; a coined component class
that has since been given its first definition counts as differing too. Step
070 won't evaluate until a person checks a stale row again, and the annotation
tool shows the old and new definitions. Checking it again stores both
definitions as they are then.

One component class, one row: two rows with the same kind and the same
component_class_from_past_or_crt_schema (compared like every component class,
ignoring case and punctuation) would leave it open which translation counts.
Step 070 never writes such a pair; a hand edit can. repeats() finds them: step 070 stops
until they're gone, and the annotation tool lets a person delete the extra
ones (the only rows it can delete).

Step 070 adds rows and reads them; the annotation tool shows them and saves
a person's changes. Both use the definitions here.
"""
from __future__ import annotations

import csv
from pathlib import Path

from common.step import ANNOTATIONS_DIR
from common.triples_io import component_class_key

MAPPING_PATH = ANNOTATIONS_DIR / "component_class_mapping.csv"
COLUMNS = ["kind", "component_class_from_past_or_crt_schema", "component_class_in_gtt", "swap_subject_and_object", "checked",
           "definition_from_past_or_crt_schema", "definition_in_gtt"]
KINDS = {"entity class": "entity_classes", "predicate": "predicates"}   # {kind: the schema's key}
NONE = "(none)"
CHECKED = ("yes", "same component class")                                          # what 070 accepts as checked


def crt_definitions(schema_used: dict) -> dict:
    """{kind: {component_class_key(component class): definition}} of the current schema
    (step 060's schema_used.json, as read with json)."""
    return {kind: {component_class_key(e["component_class"]): e.get("definition") or "" for e in schema_used.get(key, [])}
            for kind, key in KINDS.items()}


def gtt_definitions(vocab: dict) -> dict:
    """{kind: {component_class_key(component class): definition}} of the ground truth
    vocabulary (common.ground_truth.vocabulary's result; a coined component class
    has an empty definition)."""
    return {kind: {component_class_key(n): d or "" for n, d in vocab.get(key, {}).items()} for kind, key in KINDS.items()}


def _same(a: str, b: str) -> bool:
    return " ".join(a.split()) == " ".join(b.split())


def is_stale(row: dict, definitions: dict) -> bool:
    """True if the row's stored definition differs from the current
    schema's definition of its component class (spacing aside)."""
    now = definitions.get(row["kind"], {}).get(component_class_key(row["component_class_from_past_or_crt_schema"]), "")
    return not _same(row["definition_from_past_or_crt_schema"], now)


def gtt_definition(row: dict, gtt: dict) -> str:
    """The hand-built schema's definition, now, of the row's component class of the
    ground truth vocabulary ("" for (none) or a coined one without a definition)."""
    if row["component_class_in_gtt"] == NONE:
        return ""
    return gtt.get(row["kind"], {}).get(component_class_key(row["component_class_in_gtt"]), "")


def is_stale_gtt(row: dict, gtt: dict) -> bool:
    """True if the row's stored definition_in_gtt differs from the hand-built
    schema's definition now of its component class of the ground truth
    vocabulary (spacing aside)."""
    return not _same(row["definition_in_gtt"], gtt_definition(row, gtt))


def repeats(rows: list) -> list:
    """Component classes with more than one row: [{"kind", "component_class", "lines": [file line
    numbers]}], in the order first met."""
    found = {}
    for r in rows:
        key = (r["kind"], component_class_key(r["component_class_from_past_or_crt_schema"]))
        found.setdefault(key, {"kind": r["kind"], "component_class": r["component_class_from_past_or_crt_schema"], "lines": []})
        found[key]["lines"].append(r["_line"])
    return [v for v in found.values() if len(v["lines"]) > 1]


def read_mapping(path: Path = MAPPING_PATH) -> list:
    """Every row with a component_class_from_past_or_crt_schema, in the file's order, each
    value trimmed, plus "_line": its line in the file (the header is line 1;
    never written back). Stops if a column is missing."""
    with open(path, encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        missing = [c for c in COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"{Path(path).name} lacks the column(s) {', '.join(missing)}")
        rows = []
        for r in reader:
            if (r.get("component_class_from_past_or_crt_schema") or "").strip():
                rows.append({**{c: (r.get(c) or "").strip() for c in COLUMNS}, "_line": reader.line_num})
        return rows
