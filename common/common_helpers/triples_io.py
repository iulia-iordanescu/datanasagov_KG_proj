"""
common/common_helpers/triples_io.py -- the one place a triple is defined, tidied and
keyed, and the describes triple is made.

Adapted from archive/to_be_reshaped/triple_io.py; the describes triple (at the end)
was added. Used by common/common_helpers/extraction.py (050 and 060: canonical_row,
clean_triple, triple_key, classed_key, component_class_key, describes_triple),
common/common_helpers/validate.py (passages), common/common_helpers/ground_truth.py,
the annotation tool, 040 (clean_triple, component_class_key), 050 and 060
(the describes triple's component classes, COLUMNS, component_class_key) and 070
(component_class_key, triple_key's SYMMETRIC_PREDICATES, the describes triple's component classes).

A triple row has the columns in COLUMNS. source_text is the passage that
states the fact. The ground truth and the drafted batches add three columns
(common/common_helpers/ground_truth.COLUMNS).

THE KEYS. "The same" is decided here, and in common/common_helpers/text_match.py, and
nowhere else (tests/key_variants.py holds the variants every key must even out, or
keep apart; the annotation page's own key, looseKey, is tested on the same table):
    component_class_key   a COMPONENT CLASS (entity class or predicate), loosely:
                letters and digits only, of any script, case folded, accents and
                Unicode variants (full-width, ligatures) evened out, invisible
                format characters removed ("physical quantity" == "PhysicalQuantity",
                "HAS_PART" == "HASPART", "Résolution" == "Resolution";
                "ΔT" is "δt", never "t").
    text_match.instance_key   a COMPONENT INSTANCE: evened out (text_match.even), edge
                punctuation and a leading article dropped, a quantity as a quantity
                ("1 km" == "1000 m").
    triple_key  the same FACT: subject and object by instance_key, the predicate by
                component_class_key, and a symmetric predicate's subject and object
                either way round (SYMMETRIC_PREDICATES). One key for the ground
                truth's repeat check (ground_truth.py), 050's and 060's duplicate
                check (extraction.py) and 070's exact pairs (pairing.py).
    classed_key the same CLASSED TRIPLE: triple_key and both entity classes.
    is_describes  the describes triple, by component_class_key.
    passages    the passages of a source text joined by " … " (rule 17 of
                *Writing a classed triple*), the join read in any of the ways
                it is written ("…", "...", with or without spaces).
All keep digits: "Level-2" and "Level 3" never become the same thing.

THE ROWS. canonical_row tidies every row before any check (a model's, 040's, 050's
and 060's, through clean_triple; the ground truth's, as read): each slot one line,
spaces evened out; a JSON number written as the record's text writes it.

Standard library only.
"""

from __future__ import annotations

import functools
import math
import re
import unicodedata
from decimal import Decimal

from common.text_match import drop_format, instance_key

REQUIRED = ("subject", "predicate", "object")
OPTIONAL = ("subject_class", "object_class", "source_text")
#: A triple row's columns. (The ground truth and drafted batches add
#: all_facts_extracted, flags, and origin: common/common_helpers/ground_truth.COLUMNS.)
COLUMNS = ["id", "subject", "subject_class", "predicate", "object",
           "object_class", "source_text"]

# ------------------------------ the keys -----------------------------------
#
# norm_text and instance_key (a component instance evened out for comparison) are defined once, in
# common/common_helpers/text_match.py, and shared with the fact checks in common/common_helpers/validate.py, so
# "the same" means one thing everywhere.


@functools.lru_cache(maxsize=65536)
def _name_key(s: str) -> str:
    s = unicodedata.normalize("NFKD", drop_format(s))
    s = unicodedata.normalize("NFKD", "".join(c for c in s if not unicodedata.category(c).startswith("M")).casefold())
    return "".join(c for c in s if c.isalnum())


def component_class_key(s) -> str:
    """The loosest key, for a COMPONENT CLASS the model (or a person) re-cased or
    re-spaced ("physical quantity" -> "physicalquantity"): letters and digits only,
    of any script (a Greek letter is a letter), digits kept; case folded (ß is ss),
    accents and Unicode variants evened out (NFKD: "Résolution" is "resolution", a
    full-width letter its plain one), invisible format characters removed
    (text_match.drop_format). Used wherever component classes are compared:
    040 (spelling folds, the comparison with the ground truth schema), the schema
    checks in common/common_helpers/validate.py, common/common_helpers/extraction.py
    (the conflicting_classes flag), 060 (merging the additions), 070 (translating
    component classes, matching entity classes), the annotation tool and its page
    (helpers/annotator/page.html, looseKey: the same rule, tested on the same table)."""
    return _name_key(str(s or ""))


#: Predicates of the ground truth schema that say the same fact either way round (subject and object may be swapped:
#: triple_key, and 070's pairing). The ground truth schema's file has no marker for this, so they are listed here.
SYMMETRIC_PREDICATES = frozenset({"ALSO_KNOWN_AS"})
_SYMMETRIC = frozenset(component_class_key(p) for p in SYMMETRIC_PREDICATES)


def is_symmetric(predicate) -> bool:
    """Whether the predicate says the same fact either way round (SYMMETRIC_PREDICATES)."""
    return component_class_key(predicate) in _SYMMETRIC


def classed_key(t: dict) -> tuple:
    """The key two classed triples share when they are the same classed triple: (triple_key, subject class key,
    object class key), the entity classes by component_class_key, swapped with subject and object when a
    symmetric predicate's are."""
    s, p, o = instance_key(t.get("subject")), component_class_key(t.get("predicate")), instance_key(t.get("object"))
    sc, oc = component_class_key(t.get("subject_class")), component_class_key(t.get("object_class"))
    if p in _SYMMETRIC and (o, oc) < (s, sc):
        s, o, sc, oc = o, s, oc, sc
    return (s, p, o), sc, oc


def triple_key(t: dict) -> tuple:
    """The tuple two triples must share to count as the same fact (see the top of this file). It
    ignores the entity classes: the same fact given twice with different entity classes
    is ONE fact here, and common/common_helpers/extraction.py flags that case
    (conflicting_classes); classed_key adds them."""
    return classed_key(t)[0]


#: Joins the passages of a source text made of several (rule 17 of "Writing a classed triple", annotations/
#: guidelines.md: a fact a test derives from the record's own statements in more than one place).
PASSAGES_JOIN = " … "
#: The join as it is written: "…" or "..." (or more dots), with or without spaces around it.
_JOIN = re.compile(r"\s*(?:…|\.{3,})\s*")


def passages(source) -> list:
    """The passages of a source text, each as written but without the join (PASSAGES_JOIN, in any of the ways it is
    written: _JOIN) and the spaces around it; [] for an empty one. A dot or two inside a passage ("2.5") never splits
    it; a source text of one passage is a list of one."""
    s = unicodedata.normalize("NFKC", str(source or ""))
    return [p.strip() for p in _JOIN.split(s) if p.strip()]


# ------------------------------ one row -------------------------------------

#: A number as a record's text writes it: digits, perhaps with thousands commas, a decimal part, an exponent.
_NUMBER_IN_TEXT = re.compile(r"(?<![\w.])\d[\d,]*(?:\.\d+)?(?:[eE][-+]?\d+)?(?![\w])")


def _number(v, text: str) -> str:
    """A JSON number as the record's text writes it (the first spelling there with the same value: 1.5 is "1.50" in
    "1.50 m", 1000 is "1,000"); without one, written out in full (1e-06 is "0.000001", 2020.0 is "2020")."""
    for m in _NUMBER_IN_TEXT.finditer(text or ""):
        try:
            if math.isclose(float(m.group(0).replace(",", "")), float(v), rel_tol=1e-12, abs_tol=0.0):
                return m.group(0)
        except ValueError:
            continue
    if isinstance(v, int) or float(v).is_integer():
        return str(int(v))
    return format(Decimal(repr(float(v))), "f")


def _scalar(v, text: str = ""):
    """A slot value as a string, or None if it cannot be one. Models return
    2020 as an int often enough to allow numbers (written as the text writes
    them: _number); lists and dicts are a malformed reply, not a value."""
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, (int, float)):
        return _number(v, text) if math.isfinite(v) else None
    if isinstance(v, str):
        v = re.sub(r"\s+", " ", v).strip()
        return v or None
    return None


def canonical_row(raw: dict, text: str = "", keys=REQUIRED + OPTIONAL) -> dict:
    """The row tidied, before any check: each of keys a string on one line, spaces evened out (None where it can't be
    one: a list, a dict, true or false, or nothing); a JSON number written as the record's text (text) writes it. The
    one tidying step every row goes through: a model's (clean_triple) and the ground truth's (as read). Other keys are
    kept as they are."""
    return {**raw, **{k: _scalar(raw.get(k), text) for k in keys if k in raw}}


def clean_triple(raw, text: str = "") -> dict | None:
    """A model's triple, tidied (canonical_row, with the record's text for its numbers), or None if any required slot
    is blank or not a scalar. Optional keys are kept only when usable; "flags" is always present so readers never
    need to check for it."""
    if not isinstance(raw, dict):
        return None
    tidy = canonical_row(raw, text)
    if any(tidy.get(k) is None for k in REQUIRED):
        return None
    out = {k: tidy[k] for k in REQUIRED}
    out.update({k: tidy[k] for k in OPTIONAL if tidy.get(k) is not None})
    flags = raw.get("flags")
    out["flags"] = [str(f) for f in flags] if isinstance(flags, list) else []
    return out


# ------------------------------ the describes triple --------------------------
#
# Every record's classed triples start with one row no text states, written
# in code (050, 060):
#
#     <record id> (CatalogEntry) DESCRIBES <the record's title> (<entity class>)
#
# It keeps the catalog entry apart from the thing the entry is about, so
# facts about one are not mistaken for facts about the other. The model's
# only part in it is naming the describes class;
# UNDECIDED ("X") means it named none, for the person to fill in.

#: The two kinds of component class (docs/terminology.md, *kind*), each with the key a schema, as
#: common/common_helpers/schema_io.py reads it, files its component classes under; KIND_OF_KEY goes the other way.
KIND_KEYS = {"entity class": "entity_classes", "predicate": "predicates"}
KIND_OF_KEY = {key: kind for kind, key in KIND_KEYS.items()}

ENTRY_CLASS = "CatalogEntry"
ENTRY_PREDICATE = "DESCRIBES"
ENTRY_SOURCE = "(record structure)"
UNDECIDED = "X"


def describes_triple(record_id: str, title: str, entity_class: str) -> dict:
    """The row, with the title's spacing tidied like every component
    instance's (clean_triple). 020 already makes titles one line; this keeps
    the row right for a title from anywhere else."""
    return {"id": record_id, "subject": record_id, "subject_class": ENTRY_CLASS,
            "predicate": ENTRY_PREDICATE, "object": " ".join(str(title or "").split()),
            "object_class": entity_class or UNDECIDED, "source_text": ENTRY_SOURCE}


def is_describes(row: dict) -> bool:
    """Whether the row is a describes triple: its subject class CatalogEntry and its predicate DESCRIBES, each in any
    spelling (component_class_key)."""
    return component_class_key(row.get("subject_class")) == component_class_key(ENTRY_CLASS) and \
        component_class_key(row.get("predicate")) == component_class_key(ENTRY_PREDICATE)


def is_undecided(entity_class) -> bool:
    """Whether a describes class is undecided: empty, or X in any spelling (component_class_key)."""
    return component_class_key(entity_class) in ("", component_class_key(UNDECIDED))
