"""
helpers/annotator/server.py -- the annotation tool's local server (started by
helpers/annotate.py).

It serves one page (page.html) and a small JSON API, on this computer only
(127.0.0.1): nothing leaves the laptop, no model is called, and only
Python's standard library is used.

What it reads
    outputs/intermediate_results/050_annotate/drafted_triples_batch<N>.csv   step 050's draft batches
    annotations/ground_truth/batch_<NNN>.csv                                  the ground truth files
    outputs/intermediate_results/020_clean/records.jsonl                     each record's text
    outputs/intermediate_results/030_split/splits.json                       each record's pool position and part
    annotations/schema_derived_from_manual_annotation.txt                   the hand-built schema
    annotations/name_mapping.csv                                             the translation table
    outputs/intermediate_results/060_extract/schema_used.json                the current schema's definitions
    outputs/intermediate_results/060_extract/extracted_triples.csv           an example triple per predicate
    outputs/intermediate_results/070_evaluate/scores.json                    evaluation's suggestions for (none) rows
    outputs/intermediate_results/070_evaluate/matches.csv                    evaluation's partial pairs
    annotations/partial_pair_reviews.csv                                     your verdicts on them
    annotations/schema_additions.txt                                         the schema additions
    annotations/README.md                                                    the Help shown on the page
    outputs/intermediate_results/060_extract/extracted_triples_details.json  extraction's names outside the schema

What it writes: ONLY annotations/ground_truth/batch_<NNN>.csv,
annotations/name_mapping.csv, annotations/partial_pair_reviews.csv and
annotations/schema_additions.txt.
    - Opening draft batch N for the first time copies it to
      annotations/ground_truth/batch_<NNN>.csv (N with three digits); from
      then on that copy is what's shown and edited. The draft in outputs/ is
      never changed.
    - Every edit is saved to that file at once (the page sends the batch, the
      server writes it under a temporary name and renames it).
    - The draft's flags column isn't kept: the checks are recomputed live.

The translation table (step 070's, common/common_helpers/name_mapping.py) is shown row by
row, each name with its definition, and a person's choices are saved to it
at once: name_in_gtt (a name of the ground truth vocabulary, or (none)),
swap_subject_and_object (predicates only) and checked. Rows can't be added
or reordered here, and the only rows that can be removed are a name's
repeated ones (common/common_helpers/name_mapping.repeats), and a save keeps any rows step 070 added since
the page was loaded; if the rows the page shows have changed in the file, the
save is refused, so nothing is overwritten.

Schema additions: the entries of annotations/schema_additions.txt, to add,
edit or delete through a form, so the file's layout can't go wrong; the
comments at its top are kept. Every entry needs a definition and a source;
a source naming the ground truth must say "tuning" and name tuning records
only (common/common_helpers/schema_io.ground_truth_source_problem, the same check step 060
applies). A file with lines the layout can't read is not rewritten (fix it
by hand first). Extraction's last list of names outside the schema is shown
alongside, each name ready to add with its source.

Help: the page's Help button shows the section of annotations/README.md
about the view you're on (HELP_SECTIONS), so the tool's explanation lives in
one place.

Partial pairs (common/common_helpers/partial_reviews.py): evaluation's last run's partial
pairs of TUNING records, each with both triples and the record's text, for a
person to mark "same fact" or "not the same fact"; pairs ruled out earlier
are shown too, so a verdict can be changed. Held-out records are never
shown or accepted (reviewing them would mean looking at held-out results).

The checks are step 050's own, all from common/common_helpers/validate.py (source texts,
"is it in the text", and whether each entity class, predicate and pattern
is in the hand-built schema), shown in plain words (MESSAGES). The names
suggested as you type are the ground truth vocabulary
(common/common_helpers/ground_truth.vocabulary): the hand-built schema's, plus those
coined in the ground truth, so a coined name is offered for reuse. A coined
name stays flagged until it is added to the hand-built schema, since it
could be a typo, and the page lists every coined name as a reminder.
"""
from __future__ import annotations

import csv
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from common.chunking import full_text
from common.files import write_csv, write_text
from common.ground_truth import (COLUMNS, DRAFT_NUMBERED, DRAFT_PATTERN, GROUND_TRUTH_DIR, NUMBERED, PATTERN,
                                 draft_name, file_name, read_ground_truth, vocabulary)
from common.name_mapping import (CHECKED, COLUMNS as MAPPING_COLUMNS, MAPPING_PATH, NONE, crt_definitions,
                                 is_stale, read_mapping, repeats)
from common.partial_reviews import COLUMNS as REVIEW_COLUMNS, NOT_SAME, REVIEWS_PATH, SAME, row_key
from common.records_io import load_records
from common.schema_io import additions_header, additions_text, ground_truth_source_problem, read_hand_schema, \
    read_schema
from common.step import ANNOTATIONS_DIR, RESULTS_DIR
from common.text_match import Text
from common.triples_io import ENTRY_SOURCE, is_describes, label_key
from common.validate import SchemaNames, check_against_schema, check_describes, check_triple_instance

DRAFTS_DIR = RESULTS_DIR / "050_annotate"
RECORDS = RESULTS_DIR / "020_clean" / "records.jsonl"
SCHEMA_USED = RESULTS_DIR / "060_extract" / "schema_used.json"
EXTRACTED = RESULTS_DIR / "060_extract" / "extracted_triples.csv"
SCORES = RESULTS_DIR / "070_evaluate" / "scores.json"
MATCHES = RESULTS_DIR / "070_evaluate" / "matches.csv"
ADDITIONS = ANNOTATIONS_DIR / "schema_additions.txt"
README = ANNOTATIONS_DIR / "README.md"
#: The heading of annotations/README.md that explains each view of the page.
HELP_SECTIONS = {"batch": "## Annotating ground truth: the annotation tool",
                 "mapping": "### Checking the translation table",
                 "partial": "### Reviewing partial pairs",
                 "additions": "### Adding to the schema additions"}
EXTRACTION_DETAILS = RESULTS_DIR / "060_extract" / "extracted_triples_details.json"
SPLITS = RESULTS_DIR / "030_split" / "splits.json"
HAND_SCHEMA = ANNOTATIONS_DIR / "schema_derived_from_manual_annotation.txt"
PAGE = Path(__file__).with_name("page.html")

#: Each check (common/common_helpers/validate.py, the same checks step 050 runs), in plain
#: words for the page; {name} is filled with the name concerned.
MESSAGES = {
    "no_source_text": "No source text: select the passage in the record's text that states this, then press \"Use selection\".",
    "source_not_in_text": "The source text isn't in the record's text: check it was copied exactly.",
    "subject_not_in_text": "The subject isn't in the record's text (fine if it's reworded on purpose).",
    "object_not_in_text": "The object isn't in the record's text (fine if it's reworded on purpose).",
    "subject_not_in_source": "The subject isn't in its source text.",
    "object_not_in_source": "The object isn't in its source text.",
    "subject_equals_object": "The subject and the object are the same.",
    "subject_class_not_in_schema": "\"{subject_class}\" isn't an entity class of the hand-built schema: a new one, "
                                   "or a typo. Keep it only if none of the schema's fits. "
                                   "If it's new, add it, with a definition, to the hand-built schema.",
    "object_class_not_in_schema": "\"{object_class}\" isn't an entity class of the hand-built schema: a new one, "
                                  "or a typo. Keep it only if none of the schema's fits. "
                                  "If it's new, add it, with a definition, to the hand-built schema.",
    "predicate_not_in_schema": "\"{predicate}\" isn't a predicate of the hand-built schema: a new one, or a typo. "
                               "Keep it only if none of the schema's fits. "
                               "If it's new, add it, with a definition, to the hand-built schema.",
    "pattern_not_in_schema": "The hand-built schema never uses {predicate} between {subject_class} and "
                             "{object_class}: a new pattern, or a wrong entity class.",
    "empty": "Subject, predicate and object must all be filled in.",
    "describes_undecided": "Choose the entity class of what the title names.",
    "describes_class_not_in_schema": "\"{object_class}\" isn't an entity class of the hand-built schema: a new "
                                     "one, or a typo. Keep it only if none of the schema's fits. "
                                     "If it's new, add it, with a definition, to the hand-built schema.",
    "describes_subject_not_id": "This row's subject should be the record's id.",
}


# --------------------------------------------------------------------------
# reading
# --------------------------------------------------------------------------

class Data:
    """Everything the page needs besides the batch itself, loaded once."""

    def __init__(self):
        self.records = load_records(RECORDS) if RECORDS.exists() else {}
        self.positions, self.parts = {}, {}
        if SPLITS.exists():
            splits = json.loads(SPLITS.read_text(encoding="utf-8"))
            pool = splits["ground_truth_candidates"]["records"]
            self.positions = {r["id"]: r["position"] for r in pool}
            self.parts = {r["id"]: r.get("part") for r in pool}            # "tuning" or "held-out"
        self.hand = read_hand_schema(HAND_SCHEMA) if HAND_SCHEMA.exists() else \
            {"entity_classes": {}, "predicates": {}, "patterns": []}
        self.names = SchemaNames(self.hand)
        self._texts = {}

    def text(self, rid: str) -> Text | None:
        if rid not in self.records:
            return None
        if rid not in self._texts:
            self._texts[rid] = Text(full_text(self.records[rid]))
        return self._texts[rid]


def _read_rows(path: Path) -> list:
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return [{c: (row.get(c) or "").strip() for c in COLUMNS} for row in csv.DictReader(fh)
                if (row.get("id") or "").strip()]


def _group(rows: list) -> list:
    """[(id, [rows])], in the file's order."""
    order, grouped = [], {}
    for row in rows:
        if row["id"] not in grouped:
            order.append(row["id"])
            grouped[row["id"]] = []
        grouped[row["id"]].append(row)
    return [(rid, grouped[rid]) for rid in order]


def check_row(data: Data, row: dict, title: str) -> list:
    """The row's problems, as {"code", "message", "kind": "error" | "flag"}."""
    if is_describes(row):
        errors, flags = check_describes(row, row["id"], data.names)
    elif not (row["subject"] and row["predicate"] and row["object"]):
        errors, flags = ["empty"], []
    else:
        text = data.text(row["id"])
        errors, flags = check_triple_instance(row, text, title) if text is not None else ([], [])
        flags = flags + check_against_schema(row, data.names)
    return [{"code": c, "kind": kind, "message": MESSAGES[c].format(**{k: row.get(k) or "(none)" for k in COLUMNS})}
            for kind, codes in (("error", errors), ("flag", flags)) for c in codes]


def _is_blank(row: dict) -> bool:
    """A row with no subject, predicate and object: in a file, the one row of
    a record that states no facts; on the page, a row not filled in yet."""
    return not (row["subject"] or row["predicate"] or row["object"])


def record_view(data: Data, rid: str, rows: list, finished: bool) -> dict:
    record = data.records.get(rid) or {}
    title = record.get("title") or ""
    return {
        "id": rid,
        "maintainer": record.get("maintainer"),
        "position": data.positions.get(rid),
        "part": data.parts.get(rid),
        "title": title,
        "text": full_text(record) if record else None,
        "finished": finished,
        "rows": [{**r, "problems": check_row(data, r, title)} for r in rows],
    }


def batch_view(data: Data, n: int, path: Path) -> dict:
    """The batch as the page shows it: one entry per record, in the file's order."""
    records = [record_view(data, rid, [r for r in rows if not _is_blank(r)],
                           all(r["all_facts_extracted"] == "1" for r in rows))
               for rid, rows in _group(_read_rows(path))]
    vocab = vocabulary(data.hand, read_ground_truth())
    return {"n": n, "file": path.name, "records": records,
            "entity_classes": sorted(vocab["entity_classes"]), "predicates": sorted(vocab["predicates"])}


def coined_reminder(data: Data, gt) -> list:
    """A line naming the names used in the ground truth but not in the
    hand-built schema, or none."""
    coined = vocabulary(data.hand, gt)["coined"]
    names = coined["entity_classes"] + coined["predicates"]
    if not names:
        return []
    return [f"{len(names)} name(s) used in the ground truth aren't in the hand-built schema "
            f"({HAND_SCHEMA.name}): {'; '.join(f'{n} (ground truth vocabulary)' for n in names)}. "
            f"Add each one you mean to keep, with a one-line "
            f"definition; fix any typo where it's used."]


def list_batches() -> list:
    """Every draft batch and ground truth file, newest draft first."""
    out, gt_files = [], {int(m.group(1)): p for p in sorted(GROUND_TRUTH_DIR.glob(PATTERN))
                         if (m := NUMBERED.fullmatch(p.name))}
    drafts = {int(m.group(1)): p for p in DRAFTS_DIR.glob(DRAFT_PATTERN)
              if (m := DRAFT_NUMBERED.fullmatch(p.name))} if DRAFTS_DIR.exists() else {}
    for n in sorted(set(gt_files) | set(drafts), reverse=True):
        gt = gt_files.get(n)
        rows = _read_rows(gt) if gt else []
        grouped = _group(rows)
        out.append({"n": n, "draft": drafts[n].name if n in drafts else None,
                    "ground_truth": gt.name if gt else None,
                    "records": len(grouped),
                    "finished": sum(all(r["all_facts_extracted"] == "1" for r in rs) for _, rs in grouped)})
    return out


def open_batch(n: int) -> Path:
    """The ground truth file of batch n, copied from its draft the first time."""
    gt = GROUND_TRUTH_DIR / file_name(n)
    if not gt.exists():
        draft = DRAFTS_DIR / draft_name(n)
        if not draft.exists():
            raise FileNotFoundError(f"no draft batch {n} and no {gt.name}")
        write_csv(gt, COLUMNS, _read_rows(draft))
    return gt


def save_batch(data: Data, n: int, records: list) -> list:
    """Write the page's records to batch n's ground truth file, in the page's
    order, and return each row's problems (as the page sent them, so they
    line up with its rows). "finished" sets all_facts_extracted on every row
    of the record. Rows not filled in aren't written; a record left with no
    rows is written as one row holding only its id ("states no facts")."""
    out, problems = [], []
    for rec in records:
        mark = "1" if rec.get("finished") else "0"
        title = (data.records.get(rec["id"]) or {}).get("title") or ""
        written, found = [], []
        for r in rec.get("rows", []):
            row = {c: str(r.get(c) or "").strip() for c in COLUMNS}
            row["id"], row["all_facts_extracted"] = rec["id"], mark
            if is_describes(row):
                row["subject"], row["source_text"] = rec["id"], ENTRY_SOURCE
            found.append(check_row(data, row, title))
            if not _is_blank(row):
                written.append(row)
        out.extend(written or [{c: "" for c in COLUMNS} | {"id": rec["id"], "all_facts_extracted": mark}])
        problems.append(found)
    write_csv(GROUND_TRUTH_DIR / file_name(n), COLUMNS, out)
    return problems


# --------------------------------------------------------------------------
# the translation table
# --------------------------------------------------------------------------

def _gtt(data: Data) -> dict:
    """The ground truth vocabulary by kind: {kind: {name: definition}}."""
    vocab = vocabulary(data.hand, read_ground_truth())
    return {"entity class": vocab["entity_classes"], "predicate": vocab["predicates"]}


def _crt() -> dict | None:
    """The current schema's definitions (common/common_helpers/name_mapping.crt_definitions),
    or None if extraction's schema_used.json isn't there."""
    if not SCHEMA_USED.exists():
        return None
    return crt_definitions(json.loads(SCHEMA_USED.read_text(encoding="utf-8")))


def mapping_view(data: Data) -> dict:
    """The table as the page shows it: every row, with the current schema's
    definition, whether the row is stale (checked against another
    definition), an example triple for a predicate (the first one extraction
    kept with it), and the ground truth vocabulary to choose from."""
    if not MAPPING_PATH.exists():
        return {"found": False, "rows": [], "gtt": {}}
    crt = _crt()
    examples = {}
    if EXTRACTED.exists():
        with open(EXTRACTED, encoding="utf-8-sig", newline="") as fh:
            for r in csv.DictReader(fh):
                if not is_describes(r):
                    examples.setdefault(label_key(r.get("predicate")),
                                        {"subject": r.get("subject") or "", "object": r.get("object") or ""})
    gtt = _gtt(data)
    table = read_mapping(MAPPING_PATH)
    repeated = repeats(table)
    extra = {line for r in repeated for line in r["lines"]}
    same_name = {kind: {label_key(n): n for n in names} for kind, names in gtt.items()}
    suggested = {}                                    # evaluation's last suggestions for (none) rows
    if SCORES.exists():
        for s in json.loads(SCORES.read_text(encoding="utf-8")).get("translation_suggestions", []):
            suggested[(s["kind"], label_key(s["name_from_past_or_crt_schema"]))] = s["name_in_gtt"]
    rows = [{**r, "repeated": r["_line"] in extra,
             "same_name_in_gtt": same_name.get(r["kind"], {}).get(label_key(r["name_from_past_or_crt_schema"])),
             "suggested_gtt": suggested.get((r["kind"], label_key(r["name_from_past_or_crt_schema"]))),
             "in_crt": crt is not None and label_key(r["name_from_past_or_crt_schema"]) in crt.get(r["kind"], {}), "crt_definition": (crt or {}).get(r["kind"], {}).get(label_key(r["name_from_past_or_crt_schema"])),
             "stale": bool(crt) and r["checked"] in CHECKED and is_stale(r, crt),
             "example": examples.get(label_key(r["name_from_past_or_crt_schema"])) if r["kind"] == "predicate" else None}
            for r in table]
    return {"found": True, "file": f"annotations/{MAPPING_PATH.name}", "schema_found": SCHEMA_USED.exists(),
            "rows": rows, "none": NONE, "repeats": repeated,
            "gtt": {kind: [{"name": n, "definition": d} for n, d in sorted(names.items())]
                    for kind, names in gtt.items()}}


def save_mapping(data: Data, sent: list) -> None:
    """Write the person's choices for the rows the page showed. The rows'
    kinds and current-schema names must still be the file's first rows, in
    order; rows added after them (by step 070) are kept as they are. A row
    saved as checked stores the current schema's definition of its name
    (the page sends a stale row as unchecked until the person ticks it)."""
    rows = read_mapping(MAPPING_PATH)
    crt = _crt()
    if [(r["kind"], r["name_from_past_or_crt_schema"]) for r in rows[:len(sent)]] != \
            [(r.get("kind"), r.get("name_from_past_or_crt_schema")) for r in sent]:
        raise ValueError(f"{MAPPING_PATH.name} has changed since the page was loaded: reload the page")
    gtt = {kind: {label_key(n): n for n in names} for kind, names in _gtt(data).items()}
    for row, s in zip(rows, sent):
        name = str(s.get("name_in_gtt") or "").strip()
        if name != NONE:
            if label_key(name) not in gtt.get(row["kind"], {}):
                raise ValueError(f"\"{name}\" isn't {'an' if row['kind'] == 'entity class' else 'a'} {row['kind']} "
                                 f"of the ground truth vocabulary")
            name = gtt[row["kind"]][label_key(name)]
        row["name_in_gtt"] = name
        swap = row["kind"] == "predicate" and s.get("swap_subject_and_object") == "yes"
        row["swap_subject_and_object"] = "yes" if swap else "no"
        checked = str(s.get("checked") or "no")
        row["checked"] = checked if checked in ("yes", "no", "same name") else "no"
        if row["checked"] in CHECKED and crt is not None:
            row["definition_from_past_or_crt_schema"] = \
                crt.get(row["kind"], {}).get(label_key(row["name_from_past_or_crt_schema"]), "")
    write_csv(MAPPING_PATH, MAPPING_COLUMNS, rows)


def delete_mapping_row(line: int, kind: str, name: str) -> None:
    """Delete one row, only if it is one of a name's repeated rows and is
    still at that line (so nothing else can be deleted, even by mistake)."""
    rows = read_mapping(MAPPING_PATH)
    target = next((r for r in rows if r["_line"] == line), None)
    if target is None or (target["kind"], target["name_from_past_or_crt_schema"]) != (kind, name):
        raise ValueError(f"{MAPPING_PATH.name} has changed since the page was loaded: reload the page")
    if not any(line in r["lines"] for r in repeats(rows)):
        raise ValueError("only a name's extra rows can be deleted here")
    write_csv(MAPPING_PATH, MAPPING_COLUMNS, [r for r in rows if r is not target])


# --------------------------------------------------------------------------
# help
# --------------------------------------------------------------------------

def help_text(view: str) -> dict:
    """The README's section for a view, as Markdown: from its heading to the
    next heading."""
    head = HELP_SECTIONS.get(view)
    if head is None:
        raise ValueError(f"no help for {view!r}")
    text = README.read_text(encoding="utf-8")
    i = text.index(head)
    nxt = [j for j in (text.find("\n## ", i + len(head)), text.find("\n### ", i + len(head))) if j != -1]
    return {"file": f"annotations/{README.name}", "markdown": text[i:min(nxt) if nxt else len(text)].strip()}


# --------------------------------------------------------------------------
# schema additions
# --------------------------------------------------------------------------

KIND_KEYS = {"entity class": "entity_classes", "predicate": "predicates"}


def _additions() -> tuple:
    """(entries, unread lines) of the additions file."""
    if not ADDITIONS.exists():
        return [], []
    schema = read_schema(ADDITIONS)
    entries = []
    for kind, key in KIND_KEYS.items():
        for name, definition in schema[key].items():
            entries.append({"kind": kind, "name": name, "definition": definition,
                            "source": schema["sources"][key].get(name, ""),
                            "patterns": [[s_, o_] for s_, p_, o_ in schema["patterns"] if p_ == name]})
    return entries, schema["unread"]


def additions_view(data: Data) -> dict:
    entries, unread = _additions()
    used = {}
    if SCHEMA_USED.exists():
        for kind, key in KIND_KEYS.items():
            used[kind] = {label_key(e["name"]): e["name"]
                          for e in json.loads(SCHEMA_USED.read_text(encoding="utf-8")).get(key, [])
                          if e.get("from") != "additions"}
    names = []
    if EXTRACTION_DETAILS.exists():
        details = json.loads(EXTRACTION_DETAILS.read_text(encoding="utf-8"))
        have = {(e["kind"], label_key(e["name"])) for e in entries}
        names = [{**n, "added": (n["kind"], label_key(n["name"])) in have}
                 for n in (details.get("new_names") or {}).get("names", [])]
    return {"file": f"annotations/{ADDITIONS.name}", "entries": entries, "unread": unread,
            "names": names, "counted_over": (json.loads(EXTRACTION_DETAILS.read_text(encoding="utf-8"))
                                             .get("new_names") or {}).get("counted_over")
            if EXTRACTION_DETAILS.exists() else None,
            "schema_names": {k: sorted(v.values()) for k, v in used.items()}}


def check_addition(data: Data, e: dict) -> str | None:
    """What's wrong with one entry, or None."""
    if e.get("kind") not in KIND_KEYS:
        return "kind must be entity class or predicate"
    name = str(e.get("name") or "").strip()
    if not name or any(c.isspace() for c in name):
        return "the name must be one word, with no spaces (e.g. SpaceMission, PART_OF_MISSION)"
    if not str(e.get("definition") or "").strip():
        return f"{name} (additions file) needs a one-line definition"
    source = str(e.get("source") or "").strip()
    if not source:
        return f"{name} (additions file) needs a source: where the idea came from"
    parts = {data.positions[i]: part for i, part in data.parts.items() if i in data.positions}
    problem = ground_truth_source_problem(source, parts)
    if problem:
        return f"{name} (additions file): its source {problem}"
    for pair in e.get("patterns") or []:
        if len(pair) != 2 or not all(str(x).strip() and not any(c.isspace() for c in str(x).strip()) for x in pair):
            return f"{name} (additions file): each pattern is two entity classes, one word each (Subject -> Object)"
    return None


def save_additions(data: Data, entries: list) -> None:
    """Rewrite the additions file with these entries, keeping its comments."""
    _, unread = _additions()
    if unread:
        raise ValueError(f"{ADDITIONS.name} has line(s) its layout can't read ({'; '.join(unread[:3])}): fix them "
                         f"by hand first, so saving here doesn't lose them")
    seen = set()
    clean = []
    for e in entries:
        problem = check_addition(data, e)
        if problem:
            raise ValueError(problem)
        key = (e["kind"], label_key(e["name"]))
        if key in seen:
            raise ValueError(f"{e['name']} (additions file) is there twice")
        seen.add(key)
        clean.append({"kind": e["kind"], "name": e["name"].strip(), "definition": " ".join(e["definition"].split()),
                      "source": " ".join(e["source"].split()),
                      "patterns": [[str(a).strip(), str(b).strip()] for a, b in e.get("patterns") or []]
                      if e["kind"] == "predicate" else []})
    write_text(ADDITIONS, additions_text(additions_header(ADDITIONS), clean))


# --------------------------------------------------------------------------
# partial pairs
# --------------------------------------------------------------------------

def _read_reviews_rows() -> list:
    if not REVIEWS_PATH.exists():
        return []
    with open(REVIEWS_PATH, encoding="utf-8-sig", newline="") as fh:
        return [{c: (r.get(c) or "").strip() for c in REVIEW_COLUMNS} for r in csv.DictReader(fh)]


def partial_view(data: Data) -> dict:
    """Evaluation's last run's partial pairs of tuning records, plus pairs
    ruled out by an earlier review (no longer paired, so not in matches.csv),
    each with the verdict so far and the record's title, position and text."""
    reviews = {row_key(r): r["verdict"] for r in _read_reviews_rows()}
    items, seen = [], set()

    def add(row: dict, verdict):
        rid = row["record_id"]
        if data.parts.get(rid) != "tuning" or row_key(row) in seen:
            return
        seen.add(row_key(row))
        record = data.records.get(rid) or {}
        items.append({**{c: row.get(c, "") for c in REVIEW_COLUMNS if c != "verdict"},
                      "verdict": verdict, "position": data.positions.get(rid),
                      "title": record.get("title") or rid,
                      "text": full_text(record) if record else None})

    if MATCHES.exists():
        with open(MATCHES, encoding="utf-8-sig", newline="") as fh:
            for r in csv.DictReader(fh):
                if r.get("status") == "partial":
                    add(r, reviews.get(row_key(r)))
    for r in _read_reviews_rows():
        if r["verdict"] == NOT_SAME:
            add(r, NOT_SAME)
    return {"found": MATCHES.exists(), "file": f"annotations/{REVIEWS_PATH.name}", "items": items}


def save_review(data: Data, item: dict) -> None:
    """File a verdict ("same fact", "not the same fact", or "" to take one
    back) for one pair of a tuning record, replacing any earlier one."""
    if data.parts.get(item.get("record_id")) != "tuning":
        raise ValueError("only tuning records' pairs can be reviewed (held-out results stay unseen)")
    verdict = item.get("verdict") or ""
    if verdict not in (SAME, NOT_SAME, ""):
        raise ValueError(f"verdict must be '{SAME}' or '{NOT_SAME}'")
    row = {c: str(item.get(c) or "").strip() for c in REVIEW_COLUMNS}
    rows = [r for r in _read_reviews_rows() if row_key(r) != row_key(row)]
    if verdict:
        rows.append(row)
    write_csv(REVIEWS_PATH, REVIEW_COLUMNS, rows)


# --------------------------------------------------------------------------
# the server
# --------------------------------------------------------------------------

def make_handler(data: Data):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):                    # quiet: the page shows what happened
            pass

        def _send(self, status: int, body: bytes, kind: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", kind)
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, value, status: int = 200) -> None:
            self._send(status, json.dumps(value, ensure_ascii=False).encode("utf-8"),
                       "application/json; charset=utf-8")

        def do_GET(self):
            url = urlsplit(self.path)
            q = parse_qs(url.query)
            try:
                if url.path == "/":
                    self._send(200, PAGE.read_bytes(), "text/html; charset=utf-8")
                elif url.path == "/api/batches":
                    gt = read_ground_truth()
                    self._json({"batches": list_batches(), "records_found": bool(data.records),
                                "problems": gt.problems, "reminders": coined_reminder(data, gt)})
                elif url.path == "/api/mapping":
                    self._json(mapping_view(data))
                elif url.path == "/api/partial":
                    self._json(partial_view(data))
                elif url.path == "/api/help":
                    self._json(help_text(q["view"][0]))
                elif url.path == "/api/additions":
                    self._json(additions_view(data))
                elif url.path == "/api/batch":
                    n = int(q["n"][0])
                    self._json(batch_view(data, n, open_batch(n)))
                else:
                    self._json({"error": "not found"}, 404)
            except Exception as e:                          # noqa: BLE001 -- shown on the page
                self._json({"error": str(e)}, 400)

        def do_POST(self):
            url = urlsplit(self.path)
            try:
                body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
                if url.path == "/api/save":
                    self._json({"problems": save_batch(data, int(body["n"]), body["records"])})
                elif url.path == "/api/mapping/save":
                    save_mapping(data, body["rows"])
                    self._json({"saved": True})
                elif url.path == "/api/additions/save":
                    save_additions(data, body["entries"])
                    self._json({"saved": True})
                elif url.path == "/api/additions/check":
                    self._json({"problem": check_addition(data, body)})
                elif url.path == "/api/partial/review":
                    save_review(data, body)
                    self._json({"saved": True})
                elif url.path == "/api/mapping/delete":
                    delete_mapping_row(int(body["line"]), body["kind"], body["name"])
                    self._json({"deleted": True})
                else:
                    self._json({"error": "not found"}, 404)
            except Exception as e:                          # noqa: BLE001 -- shown on the page
                self._json({"error": str(e)}, 400)
    return Handler


def serve(port: int) -> ThreadingHTTPServer:
    return ThreadingHTTPServer(("127.0.0.1", port), make_handler(Data()))
