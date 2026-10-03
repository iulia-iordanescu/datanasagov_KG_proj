"""
annotator/server.py -- the annotation tool's local server (started by
annotate.py).

It serves one page (page.html) and a small JSON API, on this computer only
(127.0.0.1): nothing leaves the laptop, no model is called, and only
Python's standard library is used.

What it reads
    outputs/intermediate_results/050_annotate/drafted_triples_batch<N>.csv   step 050's draft batches
    annotations/ground_truth/batch_<NNN>.csv                                  the ground truth files
    outputs/intermediate_results/020_clean/records.jsonl                     each record's text
    outputs/intermediate_results/030_split/splits.json                       each record's pool position
    annotations/schema_derived_from_manual_annotation.txt                   the hand-built schema
    annotations/name_mapping.csv                                             the translation table
    outputs/intermediate_results/060_extract/schema_used.json                the current schema's definitions
    outputs/intermediate_results/060_extract/extracted_triples.csv           an example triple per predicate

What it writes: ONLY annotations/ground_truth/batch_<NNN>.csv and
annotations/name_mapping.csv.
    - Opening draft batch N for the first time copies it to
      annotations/ground_truth/batch_<NNN>.csv (N with three digits); from
      then on that copy is what's shown and edited. The draft in outputs/ is
      never changed.
    - Every edit is saved to that file at once (the page sends the batch, the
      server writes it under a temporary name and renames it).
    - The draft's flags column isn't kept: the checks are recomputed live.

The translation table (step 070's, common/name_mapping.py) is shown row by
row, each name with its definition, and a person's choices are saved to it
at once: name_in_gtt (a name of the ground truth vocabulary, or (none)),
swap_subject_and_object (predicates only) and checked. Rows can't be added,
removed or reordered here, and a save keeps any rows step 070 added since
the page was loaded; if the rows the page shows have changed in the file, the
save is refused, so nothing is overwritten.

The checks are step 050's own, all from common/validate.py (source texts,
"is it in the text", and whether each entity class, predicate and pattern
is in the hand-built schema), shown in plain words (MESSAGES). The names
suggested as you type are the ground truth vocabulary
(common/ground_truth.vocabulary): the hand-built schema's, plus those
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
from common.files import write_csv
from common.ground_truth import (COLUMNS, DRAFT_NUMBERED, DRAFT_PATTERN, GROUND_TRUTH_DIR, NUMBERED, PATTERN,
                                 draft_name, file_name, read_ground_truth, vocabulary)
from common.name_mapping import COLUMNS as MAPPING_COLUMNS, MAPPING_PATH, NONE, read_mapping
from common.records_io import load_records
from common.schema_io import read_hand_schema
from common.step import ANNOTATIONS_DIR, RESULTS_DIR
from common.text_match import Text
from common.triples_io import ENTRY_SOURCE, is_describes, label_key
from common.validate import SchemaNames, check_against_schema, check_describes, check_triple_instance

DRAFTS_DIR = RESULTS_DIR / "050_annotate"
RECORDS = RESULTS_DIR / "020_clean" / "records.jsonl"
SCHEMA_USED = RESULTS_DIR / "060_extract" / "schema_used.json"
EXTRACTED = RESULTS_DIR / "060_extract" / "extracted_triples.csv"
SPLITS = RESULTS_DIR / "030_split" / "splits.json"
HAND_SCHEMA = ANNOTATIONS_DIR / "schema_derived_from_manual_annotation.txt"
PAGE = Path(__file__).with_name("page.html")

#: Each check (common/validate.py, the same checks step 050 runs), in plain
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
        self.positions = {}
        if SPLITS.exists():
            splits = json.loads(SPLITS.read_text(encoding="utf-8"))
            self.positions = {r["id"]: r["position"] for r in splits["ground_truth_candidates"]["records"]}
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
            f"({HAND_SCHEMA.name}): {', '.join(names)}. Add each one you mean to keep, with a one-line "
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


def mapping_view(data: Data) -> dict:
    """The table as the page shows it: every row, with the current schema's
    definition, an example triple for a predicate (the first one extraction
    kept with it), and the ground truth vocabulary to choose from."""
    if not MAPPING_PATH.exists():
        return {"found": False, "rows": [], "gtt": {}}
    crt = {"entity class": {}, "predicate": {}}
    if SCHEMA_USED.exists():
        used = json.loads(SCHEMA_USED.read_text(encoding="utf-8"))
        for kind, key in (("entity class", "entity_classes"), ("predicate", "predicates")):
            crt[kind] = {label_key(e["name"]): e.get("definition") or "" for e in used.get(key, [])}
    examples = {}
    if EXTRACTED.exists():
        with open(EXTRACTED, encoding="utf-8-sig", newline="") as fh:
            for r in csv.DictReader(fh):
                if not is_describes(r):
                    examples.setdefault(label_key(r.get("predicate")),
                                        {"subject": r.get("subject") or "", "object": r.get("object") or ""})
    gtt = _gtt(data)
    rows = [{**r, "crt_definition": crt.get(r["kind"], {}).get(label_key(r["name_in_crt_schema"])),
             "example": examples.get(label_key(r["name_in_crt_schema"])) if r["kind"] == "predicate" else None}
            for r in read_mapping(MAPPING_PATH)]
    return {"found": True, "file": f"annotations/{MAPPING_PATH.name}", "schema_found": SCHEMA_USED.exists(),
            "rows": rows, "none": NONE,
            "gtt": {kind: [{"name": n, "definition": d} for n, d in sorted(names.items())]
                    for kind, names in gtt.items()}}


def save_mapping(data: Data, sent: list) -> None:
    """Write the person's choices for the rows the page showed. The rows'
    kinds and current-schema names must still be the file's first rows, in
    order; rows added after them (by step 070) are kept as they are."""
    rows = read_mapping(MAPPING_PATH)
    if [(r["kind"], r["name_in_crt_schema"]) for r in rows[:len(sent)]] !=             [(r.get("kind"), r.get("name_in_crt_schema")) for r in sent]:
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
    write_csv(MAPPING_PATH, MAPPING_COLUMNS, rows)


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
                else:
                    self._json({"error": "not found"}, 404)
            except Exception as e:                          # noqa: BLE001 -- shown on the page
                self._json({"error": str(e)}, 400)
    return Handler


def serve(port: int) -> ThreadingHTTPServer:
    return ThreadingHTTPServer(("127.0.0.1", port), make_handler(Data()))
