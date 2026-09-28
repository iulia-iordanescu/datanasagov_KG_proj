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

Shared by every step that takes triple instances from texts (040; 050 and
060 will add their schema checks when they are built). Adapted from
check_row in to_be_reshaped/validate_triples.py: the same checks and names,
with the schema checks left to the steps that have a schema.
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
