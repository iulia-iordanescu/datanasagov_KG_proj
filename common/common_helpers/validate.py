"""
common/common_helpers/validate.py -- checks a triple instance against the text it was taken
from.

A triple instance comes with its source text: the passage of the text that
states it, copied word for word. What code can prove is an ERROR; what code
can't decide is a FLAG (often a sign of a mistake, often fine). Neither
changes the triple instance; the caller decides what to do with it.

Every check's code is defined once, below (the constants and the groups
ERRORS, FLAGS, SCHEMA_FLAGS, ..., ALL_CHECKS), and imported by every step,
the annotation tool and the tests. What each check means, and how the checks
relate, is written once, for people: 050_annotate/050_annotate.md, *Checks on
each row* (a test keeps its Check column equal to ALL_CHECKS).

"In" and "the same" are as defined in common/common_helpers/text_match.py. Checks run
against the record's WHOLE text, so a triple instance from one piece of a
long text is checked against all of it.

    from common.validate import check_triple_instance
    errors, flags = check_triple_instance(instance, text, title)   # text: common.text_match.Text

Shared by every step that takes triple instances from texts (040, 050 and
060) and by the annotation tool. The checks against a schema and
of the describes triple are at the end of this file; 040 has no schema to check
against. Adapted from check_row in archive/to_be_reshaped/validate_triples.py: the
same checks and names.
"""
from __future__ import annotations

from common.text_match import Text, norm_text
from common.triples_io import component_class_key, is_describes

# --------------------------------------------------------------------------
# the check codes
# --------------------------------------------------------------------------

# check_triple_instance
NO_SOURCE_TEXT = "no_source_text"
SOURCE_NOT_IN_TEXT = "source_not_in_text"
SUBJECT_NOT_IN_TEXT = "subject_not_in_text"
OBJECT_NOT_IN_TEXT = "object_not_in_text"
SUBJECT_NOT_IN_SOURCE = "subject_not_in_source"
OBJECT_NOT_IN_SOURCE = "object_not_in_source"
SUBJECT_EQUALS_OBJECT = "subject_equals_object"
DATASET_SUBJECT_NOT_TITLE = "dataset_subject_not_title"
# check_against_schema
SUBJECT_CLASS_NOT_IN_SCHEMA = "subject_class_not_in_schema"
OBJECT_CLASS_NOT_IN_SCHEMA = "object_class_not_in_schema"
PREDICATE_NOT_IN_SCHEMA = "predicate_not_in_schema"
PATTERN_NOT_IN_SCHEMA = "pattern_not_in_schema"
PATTERN_NOT_PINNED = "pattern_not_pinned"
# check_describes
DESCRIBES_UNDECIDED = "describes_undecided"
DESCRIBES_SUBJECT_NOT_ID = "describes_subject_not_id"
DESCRIBES_CLASS_NOT_IN_SCHEMA = "describes_class_not_in_schema"
# on rows together (common/common_helpers/extraction.py, 050 and 060)
CONFLICTING_CLASSES = "conflicting_classes"
# stage 4 of 050, on the ground truth's files (common/common_helpers/ground_truth.check_rows)
ID_NOT_IN_RECORDS = "id_not_in_records"
INCOMPLETE = "incomplete"
# the annotation tool's own (helpers/annotator/server.py)
EMPTY = "empty"
NOT_CONNECTED = "not_connected"
SEVERAL_QUALIFIERS = "several_qualifiers"
SLASH_LIST_SPLIT = "slash_list_split"

#: check_triple_instance's errors: the triple instance is unverified.
ERRORS = (NO_SOURCE_TEXT, SOURCE_NOT_IN_TEXT)
#: check_triple_instance's flags: the triple instance is verified, but worth a look.
FLAGS = (SUBJECT_NOT_IN_TEXT, OBJECT_NOT_IN_TEXT, SUBJECT_NOT_IN_SOURCE, OBJECT_NOT_IN_SOURCE, SUBJECT_EQUALS_OBJECT,
         DATASET_SUBJECT_NOT_TITLE)
#: check_against_schema's flags.
SCHEMA_FLAGS = (SUBJECT_CLASS_NOT_IN_SCHEMA, OBJECT_CLASS_NOT_IN_SCHEMA, PREDICATE_NOT_IN_SCHEMA, PATTERN_NOT_IN_SCHEMA,
                PATTERN_NOT_PINNED)
#: check_describes's errors, and its flag.
DESCRIBES_ERRORS = (DESCRIBES_SUBJECT_NOT_ID, DESCRIBES_UNDECIDED)
DESCRIBES_FLAGS = (DESCRIBES_CLASS_NOT_IN_SCHEMA,)
#: Flags raised on rows together, not on one row.
ROWS_FLAGS = (CONFLICTING_CLASSES,)
#: The errors only stage 4 of 050 raises (ground_truth.check_rows); its others are ERRORS and DESCRIBES_ERRORS.
GROUND_TRUTH_ERRORS = (ID_NOT_IN_RECORDS, INCOMPLETE)
#: The annotation tool's own checks: EMPTY an error, NOT_CONNECTED, SEVERAL_QUALIFIERS and SLASH_LIST_SPLIT flags.
TOOL_CHECKS = (EMPTY, NOT_CONNECTED, SEVERAL_QUALIFIERS, SLASH_LIST_SPLIT)
#: The predicates of the ground truth schema for the qualifiers rule 9 of "Writing a classed triple"
#: (annotations/guidelines.md) takes out of an instance: a temporal resolution, an area the data cover, a processing
#: level, a spatial resolution, a country, a time of day, a target body, in that order.
QUALIFIER_PREDICATES = ("HAS_TEMPORAL_RESOLUTION", "HAS_SPATIAL_COVERAGE", "HAS_PROCESSING_LEVEL",
                        "HAS_SPATIAL_RESOLUTION", "BASED_IN", "OBSERVED_AT_TIME_OF_DAY", "HAS_TARGET")
#: Every check code, each once.
ALL_CHECKS = (ERRORS + FLAGS + SCHEMA_FLAGS + DESCRIBES_ERRORS + DESCRIBES_FLAGS + ROWS_FLAGS + GROUND_TRUTH_ERRORS
              + TOOL_CHECKS)


#: Joins the passages of a source text made of several (rule 1 of "What counts as a fact", annotations/guidelines.md:
#: a fact that a test in a predicate's definition derives from the record's own statements, in more than one place).
PASSAGES_JOIN = " … "


def source_in_text(source: str, text: Text) -> bool:
    """Whether a source text is in the record's text: as one passage, or as passages joined by PASSAGES_JOIN, each
    in the text."""
    if text.contains(source):
        return True
    parts = [p for p in source.split(PASSAGES_JOIN) if p.strip()]
    return len(parts) > 1 and all(text.contains(p) for p in parts)


def check_triple_instance(instance: dict, text: Text, title: str = "") -> tuple:
    """(errors, flags) for one triple instance, each a list of the names above."""
    errors, flags = [], []
    source = str(instance.get("source_text") or "")
    if not source.strip():
        errors.append(NO_SOURCE_TEXT)
    elif not source_in_text(source, text):
        errors.append(SOURCE_NOT_IN_TEXT)

    for k in ("subject", "object"):
        if not text.contains(instance.get(k)):
            flags.append(SUBJECT_NOT_IN_TEXT if k == "subject" else OBJECT_NOT_IN_TEXT)
    if source.strip():
        passage = Text(source)
        if not passage.contains(instance.get("subject")) \
                and norm_text(instance.get("subject")) != norm_text(title):
            flags.append(SUBJECT_NOT_IN_SOURCE)
        if not passage.contains(instance.get("object")):
            flags.append(OBJECT_NOT_IN_SOURCE)
    if norm_text(instance.get("subject")) == norm_text(instance.get("object")):
        flags.append(SUBJECT_EQUALS_OBJECT)
    if title.strip() and component_class_key(instance.get("subject_class")) == "dataset"             and not is_describes(instance) and norm_text(instance.get("subject")) != norm_text(title):
        flags.append(DATASET_SUBJECT_NOT_TITLE)
    return errors, flags


# --------------------------------------------------------------------------
# against a schema (050, 060, the annotation tool)
# --------------------------------------------------------------------------
#
#     SCHEMA_FLAGS and the describes triple's checks (DESCRIBES_ERRORS, DESCRIBES_FLAGS; the describes triple:
#     common/common_helpers/triples_io.py); their meanings: 050's guide (see the top of this file).
#
# Component classes are compared by loose match (triples_io.component_class_key: letters and digits only,
# case ignored), so "physical quantity" is PhysicalQuantity and has_version
# is HAS_VERSION. The schema is a dict as common/common_helpers/schema_io.py reads it.


class SchemaEntries:
    """A schema's entries (entity classes, predicates, patterns) as they are compared (see above)."""

    def __init__(self, schema: dict):
        from common.triples_io import component_class_key
        self.key = component_class_key
        self.entity_classes = {component_class_key(n) for n in schema.get("entity_classes", {})}
        self.predicates = {component_class_key(n) for n in schema.get("predicates", {})}
        #: {kind: {loose key: the schema's own spelling}}, to write a component class the way the schema does
        self.spelling = {kind: {component_class_key(n): n for n in schema.get(kind, {})}
                         for kind in ("entity_classes", "predicates")}
        self.patterns = {tuple(component_class_key(x) for x in p) for p in schema.get("patterns", [])}
        #: {predicate: {(subject class, object class)}}: a pinned predicate joins only these ("any" for any)
        self.pinned = {component_class_key(p): {tuple(component_class_key(x) for x in pair) for pair in pins}
                       for p, pins in schema.get("pinned", {}).items()}


def check_against_schema(instance: dict, schema_entries: SchemaEntries) -> list:
    """The schema flags (above) of one triple instance."""
    k = schema_entries.key
    flags = [code for slot, code in (("subject_class", SUBJECT_CLASS_NOT_IN_SCHEMA), ("object_class", OBJECT_CLASS_NOT_IN_SCHEMA))
             if k(instance.get(slot)) not in schema_entries.entity_classes]
    predicate = k(instance.get("predicate"))
    s, o = k(instance.get("subject_class")), k(instance.get("object_class"))
    if predicate not in schema_entries.predicates:
        flags.append(PREDICATE_NOT_IN_SCHEMA)
    elif predicate in schema_entries.pinned:       # a pinned predicate: its pins, not the patterns seen, decide
        if not any(ps in (s, "any") and po in (o, "any") for ps, po in schema_entries.pinned[predicate]):
            flags.append(PATTERN_NOT_PINNED)
    elif (s, predicate, o) not in schema_entries.patterns:
        flags.append(PATTERN_NOT_IN_SCHEMA)
    return flags


def check_describes(row: dict, record_id: str, schema_entries: SchemaEntries | None = None) -> tuple:
    """(errors, flags) of a record's describes triple (see above)."""
    from common.triples_io import UNDECIDED
    errors, flags = [], []
    if str(row.get("subject") or "").strip() != record_id:
        errors.append(DESCRIBES_SUBJECT_NOT_ID)
    entity_class = str(row.get("object_class") or "").strip()
    if entity_class in ("", UNDECIDED):
        errors.append(DESCRIBES_UNDECIDED)
    elif schema_entries is not None and schema_entries.key(entity_class) not in schema_entries.entity_classes:
        flags.append(DESCRIBES_CLASS_NOT_IN_SCHEMA)
    return errors, flags
