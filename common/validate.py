"""
common/validate.py -- checks a triple instance against the text it was taken
from.

A triple instance comes with its source text: the passage of the text that
states it, copied word for word. What code can prove is an ERROR; what code
can't decide is a FLAG (often a sign of a mistake, often fine). Neither
changes the triple instance; the caller decides what to do with it.

    ERRORS (the triple instance is unverified)
    no_source_text          it has no source text
    source_not_in_text      its source text is not in the record's text: it
                            can't be verified, and may be invented

    FLAGS (the triple instance is verified, but worth a look)
    subject_not_in_text     the component instance in the subject (or
    object_not_in_text      object) slot is not in the record's text; often
                            reworded: "the instrument" for "MODIS"
    subject_not_in_source   the subject is not in the triple instance's own
                            source text; not raised when the subject is the
                            record's title, since a fact about the title
                            rarely names it ("This dataset contains …")
    object_not_in_source    the object is not in its own source text
    subject_equals_object   the subject and the object are the same

"In" and "the same" are as defined in common/text_match.py. Checks run
against the record's WHOLE text, so a triple instance from one piece of a
long text is checked against all of it.

    from common.validate import check_triple_instance
    errors, flags = check_triple_instance(instance, text, title)   # text: common.text_match.Text

Shared by every step that takes triple instances from texts (040, 050 and
060) and by the annotation tool. The checks against a schema and
of the DESCRIBES row are at the end of this file; 040 has no schema to check
against. Adapted from check_row in to_be_reshaped/validate_triples.py: the
same checks and names.
"""
from __future__ import annotations

from common.text_match import Text, norm_text

ERRORS = ("no_source_text", "source_not_in_text")
FLAGS = ("subject_not_in_text", "object_not_in_text", "subject_not_in_source",
         "object_not_in_source", "subject_equals_object")


def check_triple_instance(instance: dict, text: Text, title: str = "") -> tuple:
    """(errors, flags) for one triple instance, each a list of the names above."""
    errors, flags = [], []
    source = str(instance.get("source_text") or "")
    if not source.strip():
        errors.append("no_source_text")
    elif not text.contains(source):
        errors.append("source_not_in_text")

    for k in ("subject", "object"):
        if not text.contains(instance.get(k)):
            flags.append(f"{k}_not_in_text")
    if source.strip():
        passage = Text(source)
        if not passage.contains(instance.get("subject")) \
                and norm_text(instance.get("subject")) != norm_text(title):
            flags.append("subject_not_in_source")
        if not passage.contains(instance.get("object")):
            flags.append("object_not_in_source")
    if norm_text(instance.get("subject")) == norm_text(instance.get("object")):
        flags.append("subject_equals_object")
    return errors, flags


# --------------------------------------------------------------------------
# against a schema (050, 060, the annotation tool)
# --------------------------------------------------------------------------
#
#     FLAGS (a name the schema doesn't have: a new one, or a typo)
#     subject_class_not_in_schema    the subject's entity class isn't in it
#     object_class_not_in_schema     the object's entity class isn't in it
#     predicate_not_in_schema        the predicate isn't in it
#     pattern_not_in_schema          the predicate is in it, but never with
#                                    these two entity classes
#
#     ON THE DESCRIBES ROW (common/triples_io.py)
#     describes_undecided            ERROR: no entity class named for what
#                                    the title names
#     describes_class_not_in_schema  FLAG: that entity class isn't in it
#     describes_subject_not_id       ERROR: its subject isn't the record's id
#
# Names are compared loosely (triples_io.label_key: letters and digits only,
# case ignored), so "physical quantity" is PhysicalQuantity and has_version
# is HAS_VERSION. The schema is a dict as common/schema_io.py reads it.

SCHEMA_FLAGS = ("subject_class_not_in_schema", "object_class_not_in_schema",
                "predicate_not_in_schema", "pattern_not_in_schema")
DESCRIBES_ERRORS = ("describes_undecided", "describes_subject_not_id")
DESCRIBES_FLAGS = ("describes_class_not_in_schema",)


class SchemaNames:
    """A schema's names as they are compared (see above)."""

    def __init__(self, schema: dict):
        from common.triples_io import label_key
        self.key = label_key
        self.entity_classes = {label_key(n) for n in schema.get("entity_classes", {})}
        self.predicates = {label_key(n) for n in schema.get("predicates", {})}
        #: {kind: {loose key: the schema's own spelling}}, to write a name the way the schema does
        self.spelling = {kind: {label_key(n): n for n in schema.get(kind, {})}
                         for kind in ("entity_classes", "predicates")}
        self.patterns = {tuple(label_key(x) for x in p) for p in schema.get("patterns", [])}


def check_against_schema(instance: dict, names: SchemaNames) -> list:
    """The schema flags (above) of one triple instance."""
    k = names.key
    flags = [f"{slot}_not_in_schema" for slot in ("subject_class", "object_class")
             if k(instance.get(slot)) not in names.entity_classes]
    predicate = k(instance.get("predicate"))
    if predicate not in names.predicates:
        flags.append("predicate_not_in_schema")
    elif (k(instance.get("subject_class")), predicate, k(instance.get("object_class"))) not in names.patterns:
        flags.append("pattern_not_in_schema")
    return flags


def check_describes(row: dict, record_id: str, names: SchemaNames | None = None) -> tuple:
    """(errors, flags) of a record's DESCRIBES row (see above)."""
    from common.triples_io import UNDECIDED
    errors, flags = [], []
    if str(row.get("subject") or "").strip() != record_id:
        errors.append("describes_subject_not_id")
    entity_class = str(row.get("object_class") or "").strip()
    if entity_class in ("", UNDECIDED):
        errors.append("describes_undecided")
    elif names is not None and names.key(entity_class) not in names.entity_classes:
        flags.append("describes_class_not_in_schema")
    return errors, flags
