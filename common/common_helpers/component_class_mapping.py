"""
common/common_helpers/component_class_mapping.py -- the translation table, annotations/component_class_mapping.csv:
which component class of the ground truth schema each component class of
the current schema (the one step 060 used) means.

    kind,component_class_from_past_or_crt_schema,component_class_in_gtt,swap_subject_and_object,checked,definition_from_past_or_crt_schema,definition_in_gtt
    entity class,Satellite,Spacecraft,no,yes,A craft that orbits a body.,A vehicle in space.
    predicate,CARRIES,ABOARD,yes,yes,Has on board.,Is carried on.   <- "A CARRIES B" is "B ABOARD A"
    entity class,Gadget,(none),no,yes,A small device.,            <- nothing in the ground truth schema to translate it to

    kind                     "entity class" or "predicate"
    component_class_from_past_or_crt_schema
                             a component class of the current schema or of a
                             past schema (crt: current): one
                             table serves every schema, so rows accumulate
    component_class_in_gtt   a component class of the ground truth schema
                             (gtt: ground truth triples), or (none)
    swap_subject_and_object  predicates only: "yes" when the ground truth's
                             predicate states the relationship the other way round
    checked                  "same component class" (added by code: the two
                             component classes are equal),
                             "no" (proposed by the model, not checked yet),
                             "yes" (checked by a person)
    definition_from_past_or_crt_schema
                             that schema's definition of the component class
                             when the row was written or last checked
    definition_in_gtt        the ground truth schema's definition of
                             component_class_in_gtt when the row was written or
                             last checked (empty for (none))

The three columns of fixed values (kind, swap_subject_and_object, checked) are read ignoring case and spaces at
either end, here (read_mapping), so step 070, the annotation tool and the status read them alike; any other
value (value_problems) stops step 070, naming the line. swap_subject_and_object is "no" for an entity class.
The values, for a person: docs/terminology.md, *translation table*.

A row is only as good as the meanings it was checked against: a later schema
may give the same component class another meaning, and the ground truth schema
may give the component class it translates to another one. So a
checked row is STALE when (its definition_from_past_or_crt_schema differs from
the current schema's definition) or (its definition_in_gtt differs from the
ground truth schema's definition now), spacing aside. Step
070 won't evaluate until a person checks a stale row again, and the annotation
tool shows the old and new definitions. Checking it again stores both
definitions as they are then.

A row whose component_class_in_gtt (not (none)) is no longer, or never was, in the
ground truth schema file has a MISSING TARGET (is_missing_target): there is no
definition to compare, so it is never stale_gtt; step 070 stops on it, and the
annotation tool marks it. The full list of its causes: docs/terminology.md, *row state*.

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

from common.audit import ref_path
from common.step import ANNOTATIONS_DIR
from common.stop import Stop
from common.triples_io import KIND_KEYS, component_class_key

MAPPING_PATH = ANNOTATIONS_DIR / "component_class_mapping.csv"
COLUMNS = ["kind", "component_class_from_past_or_crt_schema", "component_class_in_gtt", "swap_subject_and_object", "checked",
           "definition_from_past_or_crt_schema", "definition_in_gtt"]
KINDS = KIND_KEYS                                                       # {kind: the schema's key}
NONE = "(none)"
CHECKED = ("yes", "same component class")                                          # what 070 accepts as checked
#: Every value each column of fixed values may hold (read_mapping lowercases them first).
VALUES = {"kind": tuple(KINDS), "swap_subject_and_object": ("yes", "no"), "checked": ("no",) + CHECKED}


def crt_definitions(schema_used: dict) -> dict:
    """{kind: {component_class_key(component class): definition}} of the current schema
    (step 060's schema_used.json, as read with json)."""
    return {kind: {component_class_key(e["component_class"]): e.get("definition") or "" for e in schema_used.get(key, [])}
            for kind, key in KINDS.items()}


def gtt_definitions(vocab: dict) -> dict:
    """{kind: {component_class_key(component class): definition}} of the ground truth
    schema (common.schema_io.read_ground_truth_schema's result)."""
    return {kind: {component_class_key(n): d or "" for n, d in vocab.get(key, {}).items()} for kind, key in KINDS.items()}


def _same(a: str, b: str) -> bool:
    return " ".join(a.split()) == " ".join(b.split())


def is_stale(row: dict, definitions: dict) -> bool:
    """True if the row's stored definition differs from the current
    schema's definition of its component class (spacing aside)."""
    now = definitions.get(row["kind"], {}).get(component_class_key(row["component_class_from_past_or_crt_schema"]), "")
    return not _same(row["definition_from_past_or_crt_schema"], now)


def gtt_definition(row: dict, gtt: dict) -> str:
    """The ground truth schema's definition, now, of the component class the row
    translates to ("" for (none), or for one the ground truth schema lacks)."""
    if row["component_class_in_gtt"] == NONE:
        return ""
    return gtt.get(row["kind"], {}).get(component_class_key(row["component_class_in_gtt"]), "")


def is_missing_target(row: dict, gtt: dict) -> bool:
    """True if the row translates to a component class (not (none)) that the ground truth schema (gtt:
    gtt_definitions' result) doesn't have: a missing target."""
    return row["component_class_in_gtt"] != NONE and \
        component_class_key(row["component_class_in_gtt"]) not in gtt.get(row["kind"], {})


def is_stale_gtt(row: dict, gtt: dict) -> bool:
    """True if the row's stored definition_in_gtt differs from the ground truth
    schema's definition now of the component class the row translates to
    (spacing aside). Never for a missing target (is_missing_target): it has no
    definition now to compare with."""
    return not is_missing_target(row, gtt) and not _same(row["definition_in_gtt"], gtt_definition(row, gtt))


#: The row states, in the order of their home, docs/terminology.md, *row state* (what each means, how they relate,
#: and which step 070 stops on in which order).
REPEATED, STALE, MISSING_TARGET, NOW_EXISTS, SUGGESTED, SHARED = (
    "repeated", "stale", "missing target", "now exists", "suggested", "shared")
ROW_STATES = (REPEATED, STALE, MISSING_TARGET, NOW_EXISTS, SUGGESTED, SHARED)
#: Whose definition changed, for a stale row: the current schema's (of its component class), or the ground truth
#: schema's (of the one it translates to).
IN_CRT, IN_GTT = "current schema", "ground truth schema"


def is_checked(row: dict) -> bool:
    """True if a person checked the row, or it was accepted automatically (CHECKED)."""
    return row["checked"] in CHECKED


def stale_in(row: dict, crt: dict | None, gtt: dict) -> list:
    """Whose definition changed since the row was checked, in this order: IN_CRT (only for a row of the current
    schema: crt, crt_definitions' result, given and holding its component class; is_stale), IN_GTT (is_stale_gtt;
    never for a missing target). [] for a row not checked: only a checked row is stale."""
    if not is_checked(row):
        return []
    mine = component_class_key(row["component_class_from_past_or_crt_schema"])
    return ([IN_CRT] if crt and mine in crt.get(row["kind"], {}) and is_stale(row, crt) else []) + \
        ([IN_GTT] if is_stale_gtt(row, gtt) else [])


def sharing(rows: list, crt: dict | None) -> dict:
    """{a row's line: the other component classes of the current schema translated to the same one}, for each row of
    the current schema not translated to (none) that shares its translation; a row sharing nothing isn't listed."""
    if not crt:
        return {}
    current = [r for r in rows if r["component_class_in_gtt"] != NONE
               and component_class_key(r["component_class_from_past_or_crt_schema"]) in crt.get(r["kind"], {})]
    out = {}
    for r in current:
        others = [o["component_class_from_past_or_crt_schema"] for o in current
                  if o is not r and o["kind"] == r["kind"] and o["component_class_in_gtt"] == r["component_class_in_gtt"]]
        if others:
            out[r["_line"]] = others
    return out


def row_states(row: dict, crt: dict | None, gtt: dict, repeated: bool = False, same_in_gtt: str | None = None,
               suggested: str | None = None, shared: list = ()) -> list:
    """The row's states, in ROW_STATES' order (docs/terminology.md, *row state*). crt: crt_definitions' result (None
    without one); gtt: gtt_definitions' result; repeated: the row is one of repeats(); same_in_gtt: the ground truth
    schema's component class spelled like the row's, if any; suggested: the model's suggestion for a (none) row, if
    any; shared: sharing()'s list for the row. now exists replaces suggested."""
    none = row["component_class_in_gtt"] == NONE
    found = {REPEATED: repeated, STALE: bool(stale_in(row, crt, gtt)), MISSING_TARGET: is_missing_target(row, gtt),
             NOW_EXISTS: none and bool(same_in_gtt), SUGGESTED: none and bool(suggested) and not same_in_gtt,
             SHARED: bool(shared)}
    return [state for state in ROW_STATES if found[state]]


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
            raise Stop(f"{ref_path(path)} lacks the column(s) {', '.join(missing)}, so the translation table can't "
                       f"be read. Restore its header line, which names the columns: {', '.join(COLUMNS)}.")
        rows = []
        for r in reader:
            if (r.get("component_class_from_past_or_crt_schema") or "").strip():
                row = {c: (r.get(c) or "").strip() for c in COLUMNS}
                row.update({c: " ".join(row[c].lower().split()) for c in VALUES})
                rows.append({**row, "_line": reader.line_num})
        return rows


def value_problems(rows: list) -> list:
    """Each row whose column of fixed values holds a value outside VALUES (or "yes" in swap_subject_and_object for an
    entity class), as "line N (component class): column 'value'", in the file's order."""
    out = []
    for r in rows:
        bad = [c for c, allowed in VALUES.items() if r[c] not in allowed]
        if r["kind"] == "entity class" and r["swap_subject_and_object"] == "yes":
            bad.append("swap_subject_and_object")
        out += [f"line {r['_line']} ({r['component_class_from_past_or_crt_schema']}): {c} '{r[c]}'" for c in bad]
    return out


def values_text() -> str:
    """The allowed values, for messages."""
    return ("kind: entity class or predicate; swap_subject_and_object: yes or no (no for an entity class); checked: "
            "no, yes, or same component class")
