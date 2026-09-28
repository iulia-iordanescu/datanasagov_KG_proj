"""
common/validate.py -- checks a fact against the text it was taken from.

A fact is a subject, a predicate, an object, and its source_text: the
passage of the text that states it, copied word for word. What code can
prove is an ERROR; what code can't decide is a FLAG (often a sign of a
mistake, often fine). Neither changes the fact; the caller decides what to
do with it.

    ERRORS
    no_source_text          the fact has no passage
    source_not_in_text      its passage is not in the record's text: the
                            fact can't be verified, and may be invented

    FLAGS
    subject_not_in_text     the subject is not in the record's text (often a
    object_not_in_text      reworded name: "the instrument" for "MODIS")
    subject_not_in_source   the subject is not in its own passage; not raised
                            when the subject is the record's title, since a
                            fact about the title rarely names it ("This
                            dataset contains …")
    object_not_in_source    the object is not in its own passage
    subject_equals_object   the subject and the object are the same name

"In" and "the same" are as defined in common/text_match.py. Checks run
against the record's WHOLE text, so a fact from one piece of a long record
is checked against all of it.

    from common.validate import check_fact
    errors, flags = check_fact(fact, text, title)     # text: common.text_match.Text

Shared by every step that takes facts from texts (040; 050 and 060 will add
their schema checks when they are built). Adapted from check_row in
to_be_reshaped/validate_triples.py: the same checks and names, with the
schema checks left to the steps that have a schema.
"""
from __future__ import annotations

from common.text_match import Text, norm_text

ERRORS = ("no_source_text", "source_not_in_text")
FLAGS = ("subject_not_in_text", "object_not_in_text", "subject_not_in_source",
         "object_not_in_source", "subject_equals_object")


def check_fact(fact: dict, text: Text, title: str = "") -> tuple:
    """(errors, flags) for one fact, each a list of the names above."""
    errors, flags = [], []
    source = str(fact.get("source_text") or "")
    if not source.strip():
        errors.append("no_source_text")
    elif not text.contains(source):
        errors.append("source_not_in_text")

    for k in ("subject", "object"):
        if not text.contains(fact.get(k)):
            flags.append(f"{k}_not_in_text")
    if source.strip():
        passage = Text(source)
        if not passage.contains(fact.get("subject")) and norm_text(fact.get("subject")) != norm_text(title):
            flags.append("subject_not_in_source")
        if not passage.contains(fact.get("object")):
            flags.append("object_not_in_source")
    if norm_text(fact.get("subject")) == norm_text(fact.get("object")):
        flags.append("subject_equals_object")
    return errors, flags
