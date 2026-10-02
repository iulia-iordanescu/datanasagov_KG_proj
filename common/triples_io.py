"""
common/triples_io.py -- the one place a triple is defined, cleaned and
keyed, and the DESCRIBES row is made.

Adapted from to_be_reshaped/triple_io.py; the DESCRIBES row (at the end)
was added. Used by common/extraction.py (050 and 060: clean_triple,
triple_key, label_key, describes_row), common/validate.py,
common/ground_truth.py, the annotation tool, 040 (label_key), 050 and 060
(the DESCRIBES row's names, COLUMNS, label_key) and 070 (label_key, the
DESCRIBES row's names).

A triple row has the columns in COLUMNS. source_text is the passage that
states the fact. The ground truth and the draft batches add three columns
(common/ground_truth.COLUMNS).

Names are evened out in two ways:
    triple_key  (subject, predicate, object) as common/text_match.norm_text
                gives them (case, spacing, quote marks, dashes, edge
                punctuation, a leading article); predicates also treat
                "_", "-" and spaces alike ("IS_ABOARD" == "is aboard").
                Two rows with the same key are the same fact.
    label_key   letters and digits only, for schema names the model
                re-cased or re-spaced ("physical quantity" ==
                "PhysicalQuantity").

Both keep digits: "Level-2" and "Level 3" never become the same thing.

Standard library only.
"""

from __future__ import annotations

import re
import unicodedata

from common.text_match import norm_text

REQUIRED = ("subject", "predicate", "object")
OPTIONAL = ("subject_class", "object_class", "source_text")
#: A triple row's columns. (The ground truth and draft batches add
#: all_facts_extracted, flags and origin: common/ground_truth.COLUMNS.)
COLUMNS = ["id", "subject", "subject_class", "predicate", "object",
           "object_class", "source_text"]

# ------------------------------ normalisation ------------------------------
#
# norm_text (a name or free text, evened out for comparison) is defined once,
# in common/text_match.py, and shared with the fact checks in
# common/validate.py, so "the same name" means one thing everywhere.


def norm_predicate(s) -> str:
    """Normalise a predicate: as norm_text, and _ - space are equivalent."""
    return re.sub(r"[\s_\-]+", " ", norm_text(s)).strip()


def label_key(s) -> str:
    """Loosest key, for looking up a SCHEMA name the model re-cased or
    re-spaced ("physical quantity" -> "PhysicalQuantity"): letters and
    digits only, digits kept. Used wherever schema names are compared
    loosely: 040 (spelling folds, the comparison with the hand-built
    schema), the schema checks in common/validate.py, common/extraction.py
    (conflicting classes), 060 (merging the additions) and 070 (translating
    names, matching classes)."""
    return re.sub(r"[^a-z0-9]", "", unicodedata.normalize(
        "NFKC", str(s or "")).casefold())


def triple_key(t: dict) -> tuple:
    """The tuple two triples must share to count as the same fact. It
    ignores the classes: the same fact given twice with different classes
    is ONE fact here, and common/extraction.py flags that case
    (conflicting_classes)."""
    return (norm_text(t.get("subject")), norm_predicate(t.get("predicate")),
            norm_text(t.get("object")))


# ------------------------------ one triple ---------------------------------

def _scalar(v):
    """A slot value as a string, or None if it cannot be one. Models return
    2020 as an int often enough to allow numbers; lists and dicts are a
    malformed reply, not a value."""
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, str):
        v = re.sub(r"\s+", " ", v).strip()
        return v or None
    return None


def clean_triple(raw) -> dict | None:
    """Return a well-formed triple dict, or None if any required slot is
    blank or not a scalar. Optional keys are kept only when usable; "flags"
    is always present so readers never need to check for it."""
    if not isinstance(raw, dict):
        return None
    out = {}
    for k in REQUIRED:
        v = _scalar(raw.get(k))
        if v is None:
            return None
        out[k] = v
    for k in OPTIONAL:
        v = _scalar(raw.get(k))
        if v is not None:
            out[k] = v
    flags = raw.get("flags")
    out["flags"] = [str(f) for f in flags] if isinstance(flags, list) else []
    return out


# ------------------------------ the DESCRIBES row --------------------------
#
# Every record's triple instances start with one row no text states, written
# in code (050, 060):
#
#     <record id> (CatalogEntry) DESCRIBES <the record's title> (<entity class>)
#
# It keeps the catalog entry apart from the thing the entry is about, so
# facts about one are not mistaken for facts about the other. The model's
# only part in it is naming the entity class of what the title names;
# UNDECIDED ("X") means it named none, for the person to fill in.

ENTRY_CLASS = "CatalogEntry"
ENTRY_PREDICATE = "DESCRIBES"
ENTRY_SOURCE = "(record structure)"
UNDECIDED = "X"


def describes_row(record_id: str, title: str, entity_class: str) -> dict:
    """The row, with the title's spacing tidied like every component
    instance's (clean_triple). 020 already makes titles one line; this keeps
    the row right for a title from anywhere else."""
    return {"id": record_id, "subject": record_id, "subject_class": ENTRY_CLASS,
            "predicate": ENTRY_PREDICATE, "object": " ".join(str(title or "").split()),
            "object_class": entity_class or UNDECIDED, "source_text": ENTRY_SOURCE}


def is_describes(row: dict) -> bool:
    return label_key(row.get("subject_class")) == label_key(ENTRY_CLASS) and \
        norm_predicate(row.get("predicate")) == norm_predicate(ENTRY_PREDICATE)
