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

import re

from common.text_match import Text, instance_key, norm_text
from common.triples_io import PASSAGES_JOIN, component_class_key, is_describes, is_undecided, passages  # noqa: F401

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
# check_abbreviations (rule 20's abbreviation test, common/common_helpers/abbreviations.py)
ABBREVIATION_FAILS_TEST = "abbreviation_fails_test"
ALSO_KNOWN_AS_FAILS_TEST = "also_known_as_fails_test"
IDENTIFIER_PASSES_TEST = "identifier_passes_test"
ABBREVIATION_SPELLED_OUT = "abbreviation_spelled_out"
# check_against_schema
SUBJECT_CLASS_NOT_IN_SCHEMA = "subject_class_not_in_schema"
OBJECT_CLASS_NOT_IN_SCHEMA = "object_class_not_in_schema"
PREDICATE_NOT_IN_SCHEMA = "predicate_not_in_schema"
PATTERN_NOT_IN_SCHEMA = "pattern_not_in_schema"
PATTERN_NOT_PINNED = "pattern_not_pinned"
# the annotation tool, on a tuning record's row: an entity class or predicate marked held-out only in the ground truth
# schema (docs/terminology.md, *held-out-only entry*), which no tuning record may use
SUBJECT_CLASS_HELD_OUT_ONLY = "subject_class_held_out_only"
OBJECT_CLASS_HELD_OUT_ONLY = "object_class_held_out_only"
PREDICATE_HELD_OUT_ONLY = "predicate_held_out_only"
# check_describes
DESCRIBES_UNDECIDED = "describes_undecided"
DESCRIBES_SUBJECT_NOT_ID = "describes_subject_not_id"
DESCRIBES_CLASS_NOT_IN_SCHEMA = "describes_class_not_in_schema"
# on rows together (common/common_helpers/extraction.py, 050 and 060)
CONFLICTING_CLASSES = "conflicting_classes"
DESCRIBES_CLASSES_DIFFER = "describes_classes_differ"
# stage 4 of 050, on the ground truth's files (common/common_helpers/ground_truth.check_rows)
ID_NOT_IN_RECORDS = "id_not_in_records"
INCOMPLETE = "incomplete"
SEVERAL_DESCRIBES = "several_describes"
# the annotation tool's own (helpers/annotator/server.py)
EMPTY = "empty"
NOT_CONNECTED = "not_connected"
SEVERAL_QUALIFIERS = "several_qualifiers"
SLASH_LIST_SPLIT = "slash_list_split"
RULES_NOT_VALID = "rules_not_valid"

#: check_triple_instance's errors: the triple instance is unverified.
ERRORS = (NO_SOURCE_TEXT, SOURCE_NOT_IN_TEXT)
#: check_triple_instance's flags: the triple instance is verified, but worth a look.
FLAGS = (SUBJECT_NOT_IN_TEXT, OBJECT_NOT_IN_TEXT, SUBJECT_NOT_IN_SOURCE, OBJECT_NOT_IN_SOURCE, SUBJECT_EQUALS_OBJECT,
         DATASET_SUBJECT_NOT_TITLE)
#: check_abbreviations's flags: a model's reply that disagrees with rule 20's abbreviation test (040, 050, 060).
ABBREVIATION_FLAGS = (ABBREVIATION_FAILS_TEST, ALSO_KNOWN_AS_FAILS_TEST, IDENTIFIER_PASSES_TEST, ABBREVIATION_SPELLED_OUT)
#: check_against_schema's flags.
SCHEMA_FLAGS = (SUBJECT_CLASS_NOT_IN_SCHEMA, OBJECT_CLASS_NOT_IN_SCHEMA, PREDICATE_NOT_IN_SCHEMA, PATTERN_NOT_IN_SCHEMA,
                PATTERN_NOT_PINNED)
#: The annotation tool's errors on a tuning record's row using a held-out-only entry, one per slot.
HELD_OUT_ONLY_ERRORS = (SUBJECT_CLASS_HELD_OUT_ONLY, OBJECT_CLASS_HELD_OUT_ONLY, PREDICATE_HELD_OUT_ONLY)
#: check_describes's errors, and its flag.
DESCRIBES_ERRORS = (DESCRIBES_SUBJECT_NOT_ID, DESCRIBES_UNDECIDED)
DESCRIBES_FLAGS = (DESCRIBES_CLASS_NOT_IN_SCHEMA,)
#: Flags raised on rows together, not on one row.
ROWS_FLAGS = (CONFLICTING_CLASSES, DESCRIBES_CLASSES_DIFFER)
#: The errors only stage 4 of 050 raises (ground_truth.check_rows; SEVERAL_DESCRIBES the annotation tool too); its
#: others are ERRORS and DESCRIBES_ERRORS.
GROUND_TRUTH_ERRORS = (ID_NOT_IN_RECORDS, INCOMPLETE, SEVERAL_DESCRIBES)
#: The annotation tool's own checks: EMPTY and RULES_NOT_VALID errors, NOT_CONNECTED, SEVERAL_QUALIFIERS and
#: SLASH_LIST_SPLIT flags.
TOOL_CHECKS = (EMPTY, NOT_CONNECTED, SEVERAL_QUALIFIERS, SLASH_LIST_SPLIT, RULES_NOT_VALID)
# The qualifier predicates of rule 19 of "Writing a classed triple" (annotations/guidelines.md) have one home: their
# "rule 19: qualifier, …" lines in annotations/ground_truth_schema.txt (schema_io.qualifier_predicates).
#: Every check code, each once.
ALL_CHECKS = (ERRORS + FLAGS + ABBREVIATION_FLAGS + SCHEMA_FLAGS + DESCRIBES_ERRORS + DESCRIBES_FLAGS + ROWS_FLAGS + GROUND_TRUTH_ERRORS
              + TOOL_CHECKS + HELD_OUT_ONLY_ERRORS)


# PASSAGES_JOIN (" … ", the join of a source text of several passages) and passages() live in
# common/common_helpers/triples_io.py, with every other key (imported above).


def source_in_text(source: str, text: Text) -> bool:
    """Whether a source text is in the record's text: as one passage, or as passages joined by " … " (written in any
    of its ways: common.triples_io.passages), each in the text."""
    if text.contains(source):
        return True
    parts = passages(source)
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
                and instance_key(instance.get("subject")) != instance_key(title):
            flags.append(SUBJECT_NOT_IN_SOURCE)
        if not passage.contains(instance.get("object")):
            flags.append(OBJECT_NOT_IN_SOURCE)
    if instance_key(instance.get("subject")) == instance_key(instance.get("object")):
        flags.append(SUBJECT_EQUALS_OBJECT)
    if title.strip() and component_class_key(instance.get("subject_class")) == "dataset"             and not is_describes(instance) and instance_key(instance.get("subject")) != instance_key(title):
        flags.append(DATASET_SUBJECT_NOT_TITLE)
    return errors, flags


# --------------------------------------------------------------------------
# rule 20's abbreviation test (040, 050, 060: a model's replies)
# --------------------------------------------------------------------------
#
# The test is implemented once (common/common_helpers/abbreviations.py, after Schwartz and Hearst, 2003). Each flag
# says that a reply disagrees with it; nothing is changed. "Disagrees", for each use:
#
#   abbreviation_fails_test   rules 20 and 22, commas: a subject or object instance holds a short form shaped like an
#                             acronym set off by commas right after words ("Greenbelt, MD, USA"), and the short form
#                             fails the test against the words before it (back to the instance's start or the previous
#                             comma). Rule 20 then reads the commas as separating the items of a list, which rule 22
#                             splits, one triple per item; the reply kept them in one instance.
#   also_known_as_fails_test  rule 20, the title's short name: the subject is the title's instance, the predicate says
#   identifier_passes_test    "also known as" (its key holds alsoknownas) or names an identifier (its key holds
#                             identifier, or the object's entity class is Identifier), and the object is a short form
#                             the record's text gives in parentheses right after words. Rule 20: when the short form
#                             passes the test against those words (at any of its places), it is also known as; when it
#                             fails at every place, it is a code, the identifier. The flag names the reply that took the
#                             other one.
#   abbreviation_spelled_out  rule 23, test 1 (with rule 20's one instance, as written): the record spells a short
#                             form out ("Ocean Biology Processing Group (OBPG)", "Heliographic Inertial, HGI,"), the test
#                             passing, and an instance other than the title's is the short form alone ("OBPG"), or the
#                             spelled-out words alone, the short form dropped ("Ocean Biology Processing Group" where
#                             the text has it right before "(OBPG)"). The wording that spells the abbreviation out is
#                             the one to use; the other appears only in an also-known-as triple, which is not flagged,
#                             and the title's short name is judged by the flags above, not by this one.


def _ends_with(words: str, value: str) -> bool:
    """Whether value, evened out (text_match.norm_text), is the end of words, cut between two words."""
    w, v = norm_text(words), norm_text(value)
    return bool(v) and (w == v or (w.endswith(v) and not w[-len(v) - 1].isalnum()))


def _holds(value: str, short: str) -> bool:
    """Whether value holds short as a whole word (case ignored)."""
    return re.search(r"(?<![^\W_])" + re.escape(short) + r"(?![^\W_])", value, re.I) is not None


def check_abbreviations(instance: dict, forms: list, title: str = "") -> list:
    """The flags above for one triple instance (its predicate free words in 040, a schema's predicate in 050 and 060).
    forms: abbreviations.short_forms(the record's whole text), found once per record."""
    from common.abbreviations import is_short_form, passes
    flags = []
    predicate = component_class_key(instance.get("predicate"))
    also_known_as = "alsoknownas" in predicate
    identifier = not also_known_as and ("identifier" in predicate
                                        or component_class_key(instance.get("object_class")) == "identifier")
    title_key = instance_key(title) if str(title or "").strip() else None
    values = {k: str(instance.get(k) or "").strip() for k in ("subject", "object")}
    for value in values.values():
        parts = value.split(",")
        if any(is_short_form(parts[i], commas=True) and parts[i - 1].strip() and not passes(parts[i].strip(), parts[i - 1])
               for i in range(1, len(parts))):
            flags.append(ABBREVIATION_FAILS_TEST)
            break
    places = []                                 # the title's short name: its places in parentheses
    if title_key and instance_key(values["subject"]) == title_key and (also_known_as or identifier):
        places = [f for f in forms if not f.commas and instance_key(f.short) == instance_key(values["object"])]
        if places and also_known_as and not any(f.passes for f in places):
            flags.append(ALSO_KNOWN_AS_FAILS_TEST)
        if places and identifier and any(f.passes for f in places):
            flags.append(IDENTIFIER_PASSES_TEST)
    if not also_known_as:
        for slot, value in values.items():
            if not value or (title_key and instance_key(value) == title_key) or (slot == "object" and places):
                continue                        # the title's instance; the title's short name (judged above)
            if any(f.passes and (instance_key(value) == instance_key(f.short)
                                 or (not _holds(value, f.short) and _ends_with(f.words, value) and passes(f.short, value)))
                   for f in forms):
                flags.append(ABBREVIATION_SPELLED_OUT)
                break
    return flags


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
    errors, flags = [], []
    if str(row.get("subject") or "").strip() != record_id:
        errors.append(DESCRIBES_SUBJECT_NOT_ID)
    entity_class = str(row.get("object_class") or "").strip()
    if is_undecided(entity_class):                 # empty, or X in any spelling
        errors.append(DESCRIBES_UNDECIDED)
    elif schema_entries is not None and schema_entries.key(entity_class) not in schema_entries.entity_classes:
        flags.append(DESCRIBES_CLASS_NOT_IN_SCHEMA)
    return errors, flags
