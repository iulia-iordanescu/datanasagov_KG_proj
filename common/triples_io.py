"""
common/triples_io.py -- the one place a triple is defined, read, written and
normalised.

Adapted from to_be_reshaped/triple_io.py; the DESCRIBES row (at the end)
was added. Used today by common/extraction.py (050, and 060 when built),
common/validate.py and the annotation tool: triple_key, label_key,
clean_triple and the DESCRIBES row. The file-reading and -writing half
(load_triples, write_triples, dedupe) is kept for 070, the evaluator, which
will COMPARE ground truth with extracted triple instances. That is the
whole point of one module: precision and recall are only meaningful if both
sides are parsed and normalised by the same code. If the extractor
lowercased and the evaluator did not, every mismatch in case would count as
a false positive AND a false negative, and the numbers would describe the
bookkeeping rather than the extraction.

FILE FORMAT  (FORMAT = "triples/v1")
-----------
The canonical JSON form, written by write_triples (no step writes it at
present; 050 writes the CSV form below):

    {"format": "triples/v1",
     "run": {... who/what produced this file ...},
     "documents": [
        {"id": "<record id>",
         "status": "ok" | "failed",
         "triples": [
            {"subject": "MODIS", "predicate": "is aboard", "object": "Aqua",
             "subject_class": "Instrument",        # optional
             "object_class": "Spacecraft",         # optional
             "source_text": "MODIS aboard Aqua",   # optional
             "flags": []}                          # optional
         ],
         ... any other keys are kept but ignored here ...}
     ]}

source_text is the passage that states the fact. It was once called
"evidence"; files using that name are still read, into source_text.

Documents are the unit of evaluation. A document with status "ok" and an
empty "triples" list is a real statement ("this text holds no facts"), which
matters for precision: anything predicted there is a false positive. A
document with status "failed" was never extracted and should be EXCLUDED
from scoring, not scored as zero recall.

Two flat forms are accepted too. The CSV one is what step 050 writes
(drafted_triples_batch<N>.csv) and what the ground truth is kept in
(annotations/ground_truth/batch_<NNN>.csv, columns in
common/ground_truth.COLUMNS):

  * CSV with a header row: id,subject,predicate,object
    (subject_class, object_class, source_text columns optional)
  * JSON list of rows: [{"id": ..., "subject": ..., ...}, ...]

In both flat forms a row carrying an id but a blank subject, predicate AND
object declares "this document was annotated and has no facts". Without it
a zero-fact document cannot be expressed, and false positives on it would go
uncounted.

Reading a draft batch or ground truth CSV back with load_triples:
  * every row is read, errors included: to score only rows without errors,
    filter the CSV first
  * the DESCRIBES row is read like any triple
  * other columns (flags, all_facts_extracted, origin) are ignored
  * the flat forms have no "status": a record missing from the file was not
    extracted (not run yet, or its call failed) and is simply absent

MATCH MODES  (triple_key)
-----------
    exact       the three strings, only outer whitespace trimmed
    normalized  Unicode-folded, case-folded, whitespace collapsed, edge
                punctuation and a leading article dropped; predicates also
                treat "_", "-" and spaces alike ("IS_ABOARD" == "is aboard")
    schema      (subject_class, predicate, object_class), all normalised:
                did the extractor get the KIND of fact right, whatever
                names it used

Normalisation keeps digits and inner punctuation: "Level-2" and "Level 3"
must never become the same thing. Fuzzier matching (synonyms, acronym
expansion, embedding similarity) belongs in the evaluator as an explicit,
reported choice, not hidden in here.

Standard library only.
"""

from __future__ import annotations

import csv
import json
import re
import unicodedata
from pathlib import Path

from common.text_match import norm_text

FORMAT = "triples/v1"

REQUIRED = ("subject", "predicate", "object")
OPTIONAL = ("subject_class", "object_class", "source_text")
#: A triple row's columns. (The ground truth and draft batches add
#: all_facts_extracted, flags and origin: common/ground_truth.COLUMNS.)
COLUMNS = ["id", "subject", "subject_class", "predicate", "object",
           "object_class", "source_text"]
#: Older names still read, as {old: current}.
RENAMED = {"evidence": "source_text"}
MATCH_MODES = ("exact", "normalized", "schema")

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
    digits only, digits kept. Used wherever names are compared loosely
    (040's spelling folds and its comparison with the hand-built schema,
    the schema checks in common/validate.py)."""
    return re.sub(r"[^a-z0-9]", "", unicodedata.normalize(
        "NFKC", str(s or "")).casefold())


def triple_key(t: dict, mode: str = "normalized") -> tuple:
    """The tuple two triples must share to count as the same triple.

    exact and normalized ignore the classes: the same fact given twice with
    different classes is ONE triple here. common/extraction.py flags that
    case (conflicting_classes); scoring does not see it."""
    if mode == "exact":
        return tuple(str(t.get(k) or "").strip() for k in REQUIRED)
    if mode == "normalized":
        return (norm_text(t.get("subject")), norm_predicate(t.get("predicate")),
                norm_text(t.get("object")))
    if mode == "schema":
        return (label_key(t.get("subject_class")),
                norm_predicate(t.get("predicate")),
                label_key(t.get("object_class")))
    raise ValueError(f"unknown match mode {mode!r}; use one of {MATCH_MODES}")


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
    for old, new in RENAMED.items():
        if raw.get(new) is None and raw.get(old) is not None:
            raw = dict(raw, **{new: raw[old]})
    for k in OPTIONAL:
        v = _scalar(raw.get(k))
        if v is not None:
            out[k] = v
    flags = raw.get("flags")
    out["flags"] = [str(f) for f in flags] if isinstance(flags, list) else []
    return out


def dedupe(triples: list[dict], mode: str = "normalized"):
    """Drop repeats under `mode`, keeping the first. Returns (kept, dropped).

    Needed before scoring: a document that states one fact twice would
    otherwise earn two true positives for one piece of knowledge."""
    seen, kept = set(), []
    for t in triples:
        k = triple_key(t, mode)
        if k in seen:
            continue
        seen.add(k)
        kept.append(t)
    return kept, len(triples) - len(kept)


# ------------------------------ files --------------------------------------

def _doc(doc_id, status="ok"):
    return {"id": str(doc_id), "status": status, "triples": []}


def _from_rows(rows, source) -> dict:
    docs: dict[str, dict] = {}
    bad = 0
    for n, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            bad += 1
            continue
        doc_id = str(row.get("id") or "").strip()
        if not doc_id:
            raise ValueError(f"{source}: row {n} has no id")
        doc = docs.setdefault(doc_id, _doc(doc_id))
        if not any(str(row.get(k) or "").strip() for k in REQUIRED):
            continue                      # "annotated, no facts" marker
        t = clean_triple(row)
        if t is None:
            bad += 1
            continue
        doc["triples"].append(t)
    return {"format": FORMAT, "run": {"source": str(source),
                                      "malformed_rows": bad},
            "documents": list(docs.values())}


def load_triples(path) -> dict:
    """Read any accepted form and return the canonical structure, with
    "documents" as a dict keyed by id (for lookup) and every triple passed
    through clean_triple. Malformed triples are counted in
    run["malformed_rows"] rather than raising."""
    path = Path(path)
    if path.suffix.lower() == ".csv":
        with path.open(newline="", encoding="utf-8-sig") as fh:
            blob = _from_rows(list(csv.DictReader(fh)), path)
    else:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        if isinstance(data, list):
            blob = _from_rows(data, path)
        elif isinstance(data, dict) and isinstance(data.get("documents"), list):
            if data.get("format") not in (None, FORMAT):
                raise ValueError(f"{path}: format {data.get('format')!r}, "
                                 f"expected {FORMAT!r}")
            blob, bad = dict(data), 0
            docs = []
            for d in data["documents"]:
                if not isinstance(d, dict) or not str(d.get("id") or ""):
                    bad += 1
                    continue
                d = dict(d, id=str(d["id"]),
                         status=d.get("status") or "ok")
                cleaned = [clean_triple(t) for t in d.get("triples") or []]
                bad += sum(t is None for t in cleaned)
                d["triples"] = [t for t in cleaned if t is not None]
                docs.append(d)
            blob["documents"] = docs
            blob["run"] = dict(blob.get("run") or {}, malformed_rows=bad)
        else:
            raise ValueError(f"{path}: not a triples file (need a "
                             f"'documents' list, a list of rows, or a CSV)")
    by_id: dict[str, dict] = {}
    for d in blob["documents"]:
        if d["id"] in by_id:                          # merge split listings
            by_id[d["id"]]["triples"].extend(d["triples"])
        else:
            by_id[d["id"]] = d
    blob["documents"] = by_id
    return blob


def write_triples(path, run: dict, documents: list[dict]) -> None:
    """Write the canonical form atomically (write, then rename), so a killed
    process never leaves a half-written file that a later step trusts."""
    from common.files import write_json
    write_json(path, {"format": FORMAT, "run": run, "documents": documents})


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
    return {"id": record_id, "subject": record_id, "subject_class": ENTRY_CLASS,
            "predicate": ENTRY_PREDICATE, "object": title,
            "object_class": entity_class or UNDECIDED, "source_text": ENTRY_SOURCE}


def is_describes(row: dict) -> bool:
    return label_key(row.get("subject_class")) == label_key(ENTRY_CLASS) and \
        norm_predicate(row.get("predicate")) == norm_predicate(ENTRY_PREDICATE)
