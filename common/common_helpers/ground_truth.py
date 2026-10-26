"""
common/common_helpers/ground_truth.py -- reads the ground truth: every file in

    annotations/ground_truth/batch_000.csv     classed triples annotated before the pipeline
    annotations/ground_truth/batch_001.csv     corrected from step 050's drafted batch 1
    annotations/ground_truth/batch_002.csv     … batch 2, and so on

taken together. Each file is a batch of records a person has corrected; the
ground truth is all of them. A file is added, never edited by a step: no
step writes into annotations/ground_truth/ (the annotation tool does, for the
person).

Every file has the columns

    id, subject, subject_class, predicate, object, object_class, source_text,
    all_facts_extracted

one row per classed triple, grouped by record (id). A file may also have the
column drafted_by: the model that drafted the row (step 050 writes it; the
annotation tool keeps it, and leaves it empty on a row a person adds);
batch_000.csv, annotated before the pipeline, has it too (the model on the rows
a model drafted, empty on the rest). A file without the column reads as
written by a person. Any other column (e.g. the `flags` column of a drafted batch) is
ignored, so a corrected drafted batch can be saved as it is. all_facts_extracted is 1 on every row of a record the
person has finished (every fact of its text is there), 0 while it is in
progress (FINISHED_MARKS; any other value is a problem, and the record isn't finished). A row with an id but an empty subject, predicate, and object says
"this record was annotated and states no facts".

    from common.ground_truth import read_ground_truth
    gt = read_ground_truth()                 # or read_ground_truth(folder)
    gt.rows        [{..., "_origin": ["annotations/ground_truth/batch_000.csv#4"]}, …]
    gt.records     {record id: {"file", "rows", "finished"}}
    gt.problems    ["…"]: what a person must fix (see below)
    gt.repeats     [{"message", "copies"}]: the problems that stop 070 (a classed triple twice in a record)
    fair_sample, fair_prefix  whether ids are the first records of a pool order (below)
    pool_parts(pool_rows)     the pool's ids in order, split into its parts: {"tuning": […], "held-out": […]}
    read_pool(splits_path)    the pool, from 030's splits.json: [{"id", "position", "part", …}]
    with_coined(ground_truth_schema, gt)  the ground truth schema's component classes
                              plus those coined in the ground truth (not in it yet)
    check_rows(gt, records)   rows with an error to fix: an id not in the
                              catalog, a source text not in the record's
                              text, a describes triple with no describes class, …
                              (ROW_ERRORS, at the end of this file)

Problems, each listed, none silently resolved:
  - a record in more than one file: annotated twice, and code can't tell
    which is right (both are kept out of gt.records until fixed);
  - a record whose rows disagree on all_facts_extracted (some 1, some 0);
  - the same classed triple twice in a record: the same subject instance,
    predicate and object instance (compared as
    common/common_helpers/triples_io.triple_key does) and the same subject
    class and object class (as triples_io.component_class_key does). Only
    one copy can be paired, so 070 would count the other as ground truth only. Also in
    gt.repeats: 070 refuses to run while there is one;
  - a record with an all_facts_extracted value other than 0 and 1 (FINISHED_MARKS) on some row (reported
    instead of the disagreement above);
  - the same subject instance, predicate, and object instance twice in a
    record, with different entity classes: one fact given two entity
    classes by mistake, or two facts that differ only in them;
  - a file missing one of the columns above.
A problem about lines of a file shows each of them on a line of its own
(the message has several lines). For a person, all six: docs/running_on_nasa_laptop.md, section 7.
040, 050, 060, and 070 list them in their report's warnings; 050 and 060 also before paying, and 070 before
it evaluates, asking whether to go ahead (040 reads the ground truth only after its model calls); the
annotation tool shows them on its page.

Shared by the steps that read ground truth (040, to compare its schema and report
the problems; 050, to know which records are done and to check the files; 060,
which records are finished; 070, to evaluate against it) and by the annotation tool (helpers/annotate.py), which writes the
files.
"""
from __future__ import annotations

import collections
import csv
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from common.audit import ORIGIN_FIELD, ref_path
from common.step import ANNOTATIONS_DIR
from common.triples_io import component_class_key, is_describes, triple_key

GROUND_TRUTH_DIR = ANNOTATIONS_DIR / "ground_truth"
PATTERN = "batch_*.csv"
#: The files' names, by batch number: the ground truth's batch_<NNN>.csv, and
#: step 050's drafted batches, drafted_triples_batch<N>.csv, which the
#: annotation tool copies to the ground truth file of the same number.
NUMBERED = re.compile(r"batch_(\d{3,})\.csv")
DRAFT_PATTERN = "drafted_triples_batch*.csv"
DRAFT_NUMBERED = re.compile(r"drafted_triples_batch(\d+)\.csv")
GROUND_TRUTH_SCHEMA = ANNOTATIONS_DIR / "ground_truth_schema.txt"
#: The ground truth schema was written while annotating the pool's first records, positions 0 to GROUND_TRUTH_SCHEMA_FROM - 1:
#: so they are always tuning (030), and they are the records it was learned from (060's learned_from).
GROUND_TRUTH_SCHEMA_FROM = 6


#: The twin kinds (docs/terminology.md, twin): what a twin shares with one record the schema was learned from, the kind
#: that shares the most text first. A record with two kinds (with two different records) gets the one listed first.
TWIN_KINDS = ("whole text", "notes only", "title only")


def twin_kinds(records: dict, learned: list) -> dict:
    """{id: its twin kind (TWIN_KINDS), or "" when it isn't a twin} for each of records ({id: record}), against
    learned (the records the schema was learned from). Title and `notes` are compared evened out
    (common/common_helpers/text_match.py); an empty one is never the same as another.

    >>> learned = [{"title": "Snow, Aqua", "notes": "Daily snow."}, {"title": "Fire", "notes": "Burned area."}]
    >>> twin_kinds({"a": {"title": "snow,  AQUA", "notes": "Daily snow."}, "b": {"title": "Snow, Terra", "notes": "Daily snow."},
    ...              "c": {"title": "Fire", "notes": "Fire counts."}, "d": {"title": "Fire", "notes": "Daily snow."},
    ...              "e": {"title": "Ice", "notes": ""}}, learned)
    {'a': 'whole text', 'b': 'notes only', 'c': 'title only', 'd': 'notes only', 'e': ''}
    """
    from common.text_match import even

    def keys(r):
        return even(r.get("title") or "").strip(), even(r.get("notes") or "").strip()

    pairs = {keys(r) for r in learned}
    titles = {t for t, _ in pairs} - {""}
    descriptions = {d for _, d in pairs} - {""}
    out = {}
    for rid, r in records.items():
        t, d = keys(r)
        out[rid] = ("whole text" if t and d and (t, d) in pairs else "notes only" if d in descriptions
                    else "title only" if t in titles else "")
    return out


#: The rows of the twin table (twin_table): each twin kind, as the table names it.
TWIN_ROWS = {"whole text": "whole text (same title and same `notes`)",
             "notes only": "notes only (same `notes`, different title)",
             "title only": "title only (same title, different `notes`)"}


def twin_table(pool: dict, columns: list) -> list:
    """Report lines: how many pool records are twins of each kind (twin_kinds), against the records of each column.
    pool: {id: record}; columns: [(heading, what, [records])], e.g. ("the 150 texts this run learned from",
    "the 150 texts this run of step 040 learned from", [...]). Shared by 030, 040, and 070, so the table reads the
    same in every report."""
    counts = [collections.Counter(twin_kinds(pool, learned).values()) for _, _, learned in columns]
    lines = ["| Twin kind | " + " | ".join(f"Pool records, compared with {heading}" for heading, _, _ in columns) + " |",
             "|---|" + "---:|" * len(columns)]
    for kind, label in TWIN_ROWS.items():
        lines.append(f"| {label} | " + " | ".join(f"{c[kind]:,}" for c in counts) + " |")
    lines.append("| **all twins** | " + " | ".join(f"**{sum(c[k] for k in TWIN_ROWS):,}**" for c in counts) + " |")
    lines.append("| not a twin | " + " | ".join(f"{c['']:,}" for c in counts) + " |")
    heading, what, _ = columns[0]
    n = counts[0]["notes only"]
    lines += ["", f"*How to read a cell, e.g. row \"notes only\", column \"Pool records, compared with {heading}\", {n:,}:* "
                  f"{n:,} of the {len(pool):,} pool records each have the same `notes` as one of {what}, and a "
                  f"different title. Each pool record is counted in one row only. A pool record that shares text in two "
                  f"ways (with two different records) is counted under the twin kind that shares more text: whole "
                  f"text, then notes only, then title only. Titles and `notes` are compared evened out "
                  f"(docs/terminology.md, section *Triples*); twins: docs/terminology.md, section *Evaluating "
                  f"extraction*; why they matter: 070_evaluate/070_evaluate.md, section *How it works*, subsection "
                  f"*Twins*.", ""]
    return lines


def file_name(n: int) -> str:
    return f"batch_{n:03d}.csv"


def draft_name(n: int) -> str:
    return f"drafted_triples_batch{n}.csv"

#: The columns every ground truth file has, in this order.
COLUMNS = ["id", "subject", "subject_class", "predicate", "object", "object_class",
           "source_text", "all_facts_extracted"]
#: The model that drafted a row (050's drafted batches; the annotation tool keeps it); empty when a person wrote it.
#: Optional: a file without it reads as written by a person.
DRAFTED_BY = "drafted_by"
#: The two values of the column all_facts_extracted ("0": not finished, "1": finished), the only ones the annotation
#: tool writes; any other value is a problem of the ground truth (read_ground_truth), and the record isn't finished.
FINISHED_MARKS = ("0", "1")
#: Every column a ground truth file may have, in this order.
FILE_COLUMNS = COLUMNS + [DRAFTED_BY]


@dataclass
class GroundTruth:
    rows: list = field(default_factory=list)       # every row of every file, with its origin
    records: dict = field(default_factory=dict)    # {id: {"file", "rows", "finished"}}
    files: list = field(default_factory=list)      # the files read, in order
    problems: list = field(default_factory=list)   # what a person must fix
    repeats: list = field(default_factory=list)    # of those, a classed triple twice in a record: stops 070


#: Each row's line in its file, as read (blank lines and source texts spanning lines counted).
LINE_FIELD = "_line"


def read_ground_truth(folder: Path = GROUND_TRUTH_DIR) -> GroundTruth:
    gt = GroundTruth()
    in_files = {}                                  # {id: [files it appears in]}
    by_record = {}                                 # {id: [its rows]}
    for path in sorted(Path(folder).glob(PATTERN)):
        gt.files.append(path)
        with open(path, encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh)
            missing = [c for c in COLUMNS if c not in (reader.fieldnames or [])]
            if missing:
                gt.problems.append(f"{ref_path(path)} lacks the column(s) {', '.join(missing)}, so none of its rows "
                                   f"were read. Restore its header line, which names the columns: "
                                   f"{', '.join(COLUMNS)}.")
                continue
            for position, raw in enumerate(reader):
                row = {c: (raw.get(c) or "").strip() for c in FILE_COLUMNS}
                if not row["id"]:
                    continue                       # a blank line
                row[ORIGIN_FIELD] = [f"{ref_path(path)}#{position}"]
                row[LINE_FIELD] = reader.line_num          # the file line the row ends on (blank lines counted)
                gt.rows.append(row)
                by_record.setdefault(row["id"], []).append(row)
                files = in_files.setdefault(row["id"], [])
                if path.name not in files:
                    files.append(path.name)

    for rid, rows in by_record.items():
        if len(in_files[rid]) > 1:
            gt.problems.append(f"record {rid} is in {' and '.join(in_files[rid])}: annotated twice, and which "
                               f"annotation is right can't be told, so the record is left out until fixed. Delete its "
                               f"rows from all files but one (by hand: the annotation tool can't remove a record).")
            continue
        marks = {r["all_facts_extracted"] for r in rows}
        other = sorted(marks - set(FINISHED_MARKS))
        if other:
            gt.problems.append(f"record {rid} ({in_files[rid][0]}): all_facts_extracted is "
                               f"{', '.join(repr(m) for m in other)} on {sum(r['all_facts_extracted'] in other for r in rows)} "
                               f"row(s), which is neither 0 nor 1, so the record counts as not finished. In the "
                               f"annotation tool (`py helpers/annotate.py`), tick All facts extracted on the record if "
                               f"every fact is there (untick it again if not): saving sets every row to 1 or 0.")
        elif len(marks) > 1:
            gt.problems.append(f"record {rid} ({in_files[rid][0]}): all_facts_extracted is "
                               f"{' on some rows, '.join(sorted(marks))} on others, so the record counts as not "
                               f"finished. In the annotation tool (`py helpers/annotate.py`), tick All facts extracted on "
                               f"the record if every fact is there (untick it again if not): saving sets every row.")
        gt.records[rid] = {"file": in_files[rid][0], "rows": len(rows), "finished": marks == {"1"}}
        groups = {}                                # triple key -> {(subject class, object class) keys: [rows]}
        for row in rows:
            if not (row["subject"] and row["predicate"] and row["object"]) or is_describes(row):
                continue
            entity_classes = (component_class_key(row["subject_class"]), component_class_key(row["object_class"]))
            groups.setdefault(triple_key(row), {}).setdefault(entity_classes, []).append(row)
        where = f"record {rid} ({in_files[rid][0]})"
        for by_classes in groups.values():
            for same in by_classes.values():
                if len(same) > 1:
                    message = (f"{where}: {_lines(same)} are the same classed triple.\n{_shown(same)}\n\n"
                               + ("Delete one of the two lines" if len(same) == 2 else "Delete all but one of these lines")
                               + " (py helpers/annotate.py), then rerun.")
                    gt.problems.append(message)
                    gt.repeats.append({"message": message, "copies": len(same)})
            if len(by_classes) > 1:
                different = [r for same in by_classes.values() for r in same]
                different.sort(key=lambda r: r[LINE_FIELD])
                gt.problems.append(f"{where}: {_lines(different)} state the same subject instance, predicate, and "
                                   f"object instance, with different entity classes.\n{_shown(different)}\n\n"
                                   f"If they state one fact, delete the line with the wrong entity classes.")
    return gt


def _lines(rows: list) -> str:
    """'lines 7 and 9', 'lines 7, 9, and 12'."""
    n = [str(r[LINE_FIELD]) for r in rows]
    return "lines " + (" and ".join(n) if len(n) == 2 else ", ".join(n[:-1]) + ", and " + n[-1])


def _shown(rows: list) -> str:
    """One line per row: '- Line 7: MODIS (Instrument) ABOARD Aqua (Spacecraft)'."""
    return "\n".join(f"- Line {r[LINE_FIELD]}: {r['subject']} ({r['subject_class']}) {r['predicate']} "
                     f"{r['object']} ({r['object_class']})" for r in rows)


# --------------------------------------------------------------------------
# checking the rows against the records' texts (050, on every run)
# --------------------------------------------------------------------------

#: What check_rows reports: errors a person must fix, never
#: matters of judgment (a reworded subject or object instance is fine in
#: ground truth).
ROW_ERRORS = {
    "id_not_in_records": "its id isn't a record of the catalog (a typo, or a record since removed): correct the id, "
                         "or delete the row",
    "incomplete": "subject, predicate, or object is empty, but not all three: fill in the empty ones, or delete the row",
    "no_source_text": "it has no source text: in the annotation tool, select the passage that states it and press "
                      "\"Use selection\"",
    "source_not_in_text": "its source text isn't in the record's text: in the annotation tool, select the passage and "
                          "press \"Use selection\" to copy it exactly",
    "describes_subject_not_id": "the describes triple's subject isn't the record's id: write the record's id there",
    "describes_undecided": "the describes triple has no describes class (X): choose its object class, the entity class of its object instance",
}


def check_rows(gt: GroundTruth, records: dict) -> list:
    """Every row with something to fix, as {"where": "batch_000.csv line 6",
    "id", "errors": [names of ROW_ERRORS]}. records is {id: record} (020's
    records.jsonl, read by common.records_io.load_records)."""
    from common.chunking import full_text
    from common.text_match import Text
    from common.triples_io import is_describes
    from common.validate import check_describes, check_triple_instance

    texts, out = {}, []
    for row in gt.rows:
        rid = row["id"]
        filled = [bool(row[k]) for k in ("subject", "predicate", "object")]
        if rid not in records:
            errors = ["id_not_in_records"]
        elif not any(filled):
            errors = []                            # "annotated, states no facts"
        elif not all(filled):
            errors = ["incomplete"]
        elif is_describes(row):
            errors = check_describes(row, rid)[0]
        else:
            if rid not in texts:
                texts[rid] = Text(full_text(records[rid]))
            errors = check_triple_instance(row, texts[rid], records[rid].get("title") or "")[0]
        if errors:
            file = row[ORIGIN_FIELD][0].rsplit("/", 1)[-1].split("#")[0]
            out.append({"where": f"{file} line {row[LINE_FIELD]}", "id": rid, "errors": errors})
    return out


# --------------------------------------------------------------------------
# the ground truth schema (050, the annotation tool, 070)
# --------------------------------------------------------------------------

def with_coined(ground_truth_schema: dict, gt: GroundTruth) -> dict:
    """The ground truth schema's entity classes and predicates
    (ground_truth_schema, as common.schema_io.read_ground_truth_schema reads it),
    plus every one the ground truth triples use that it lacks. Component
    classes are compared as common.triples_io.component_class_key does (ignoring case and
    punctuation), keeping the first spelling met; the describes triple's own
    component classes (CatalogEntry, DESCRIBES), the undecided X and anything
    without a letter or digit (e.g. "-") are not counted.

    Returned in the schema shape, plus "coined": {"entity_classes": [...],
    "predicates": [...]}, the component classes used in the ground truth but
    not in the ground truth schema, in the order first used. A coined component
    class has an empty definition: only the ground truth schema has definitions.
    The annotation tool marks a coined one as an error, and step 070 stops while
    a finished record uses one.

    "patterns" is the file's patterns, then every other pattern the ground truth
    triples use ("used_patterns", in the order first used): the file's say
    "where a predicate has been used", which the ground truth itself says, so
    nobody keeps them up to date by hand."""
    from common.triples_io import ENTRY_CLASS, ENTRY_PREDICATE, UNDECIDED, component_class_key

    out = {"entity_classes": dict(ground_truth_schema["entity_classes"]), "predicates": dict(ground_truth_schema["predicates"]),
           "patterns": list(ground_truth_schema.get("patterns", [])),
           "coined": {"entity_classes": [], "predicates": []}, "used_patterns": []}
    in_file = {tuple(component_class_key(x) for x in p) for p in out["patterns"]}
    for key, spelled in used_patterns(gt.rows).items():   # patterns: the file's, then every other one used
        if key not in in_file:
            out["patterns"].append(spelled)
            out["used_patterns"].append(spelled)
    known = {kind: {component_class_key(n) for n in out[kind]} for kind in ("entity_classes", "predicates")}
    for row in gt.rows:
        for kind, name in (("entity_classes", row["subject_class"]), ("entity_classes", row["object_class"]),
                           ("predicates", row["predicate"])):
            if component_class_key(name) and name not in (ENTRY_CLASS, ENTRY_PREDICATE, UNDECIDED) \
                    and component_class_key(name) not in known[kind]:
                out[kind][name] = ""
                out["coined"][kind].append(name)
                known[kind].add(component_class_key(name))
    return out


def coined_uses(gt: GroundTruth, coined: dict) -> list:
    """Where each coined component class is used, for messages: ["Instrumnet (entity class): batch_000.csv lines
    4, 9", ...], in with_coined()'s order. coined is with_coined()["coined"]."""
    from common.triples_io import component_class_key
    where = {}
    for row in gt.rows:
        file = row[ORIGIN_FIELD][0].rsplit("/", 1)[-1].split("#")[0]
        for kind, column in (("entity_classes", "subject_class"), ("entity_classes", "object_class"),
                             ("predicates", "predicate")):
            key = (kind, component_class_key(row[column]))
            where.setdefault(key, {}).setdefault(file, []).append(str(row[LINE_FIELD]))
    out = []
    for kind, word in (("entity_classes", "entity class"), ("predicates", "predicate")):
        for name in coined[kind]:
            files = where.get((kind, component_class_key(name)), {})
            out.append(f"{name} ({word}): " + "; ".join(f"{f} line{'s' if len(set(ls)) > 1 else ''} "
                                                        f"{', '.join(sorted(set(ls), key=int))}" for f, ls in files.items()))
    return out



#: The kinds of component class, as messages name them, and their key in a schema dict.
KIND_KEYS = {"entity class": "entity_classes", "predicate": "predicates"}


def uses_of(gt: GroundTruth, kind: str, name: str) -> list:
    """The ground truth triples and describes triples that use a component class (compared as component_class_key does); kind is
    "entity class" or "predicate"."""
    columns = ("subject_class", "object_class") if kind == "entity class" else ("predicate",)
    return [r for r in gt.rows if any(component_class_key(r[c]) == component_class_key(name) for c in columns)]


def pattern_of(row: dict) -> tuple | None:
    """A ground truth triple's pattern as compared (component_class_key of its subject class, predicate, and
    object class), or None for the describes triple or a row missing one of them."""
    key = tuple(component_class_key(row.get(c)) for c in ("subject_class", "predicate", "object_class"))
    return None if is_describes(row) or not all(key) else key


def used_patterns(rows) -> dict:
    """{pattern key: (subject class, predicate, object class) as first spelled}, in the order first used: every
    pattern the ground truth triples use."""
    out = {}
    for r in rows:
        key = pattern_of(r)
        if key and key not in out:
            out[key] = (r["subject_class"].strip(), r["predicate"].strip(), r["object_class"].strip())
    return out


def ground_truth_schema_gaps(ground_truth_schema: dict, gt: GroundTruth) -> dict:
    """What the ground truth uses that the ground truth schema lacks: the entity classes and predicates coined in
    the ground truth, each with how many rows use it. (Patterns are never missing: the ground truth schema's
    patterns are those of its file plus every one the ground truth uses; see with_coined.) Shared by the annotation
    tool and the project's status (common/common_helpers/status.py)."""
    coined = with_coined(ground_truth_schema, gt)["coined"]
    return {"component_classes": [{"entry_type": kind, "component_class": n, "uses": len(uses_of(gt, kind, n))}
                                  for kind, key in KIND_KEYS.items() for n in coined[key]]}


# --------------------------------------------------------------------------
# the fair sample (050, 070)
# --------------------------------------------------------------------------
#
# The ground truth candidates pool is shuffled, so its first N records are a
# fair sample of the catalog, for any N. Results about the whole catalog may
# only be drawn from such a sample. pool is the pool's ids in order
# (030's splits.json); taken is a set of ids.
#
# The same holds for each PART of the pool (tuning, held-out) taken alone: the
# pool's order restricted to one part is still a random order, so its first N
# records are a fair sample of that part, and an unfinished record of one part
# never holds back the other. pool_parts() gives each part's ids in pool order;
# fair_sample / fair_prefix are then applied to one part's list.

def read_pool(splits_path) -> list:
    """The ground truth candidates pool, in pool order, from 030's
    splits.json: [{"id", "position", "part" ("tuning" or "held-out"), …}]."""
    return json.loads(Path(splits_path).read_text(encoding="utf-8"))["ground_truth_candidates"]["records"]


PARTS = ("tuning", "held-out")


def pool_parts(pool_rows: list) -> dict:
    """The pool's ids in pool order, split by part: {"tuning": [ids], "held-out": [ids]}.
    pool_rows are read_pool()'s rows (each with an "id" and a "part")."""
    return {part: [r["id"] for r in pool_rows if r["part"] == part] for part in PARTS}


def fair_sample(pool: list, taken: set) -> dict:
    """Whether the records taken are exactly the first N of the pool, and if
    not, why."""
    in_pool = [i for i in pool if i in taken]
    n = len(in_pool)
    first = set(pool[:n])
    gaps = [i for i in pool[:max((pool.index(i) for i in in_pool), default=-1) + 1] if i not in taken]
    outside = sorted(taken - set(pool))
    return {"fair": first == set(in_pool) and not outside, "first_n": n,
            "skipped_in_pool": len(gaps), "first_skipped": gaps[0] if gaps else None,
            "outside_pool": len(outside)}


def fair_prefix(pool: list, taken: set) -> list:
    """The longest run of the first records of `pool` (the whole pool's ids, or one part's from pool_parts())
    that are all taken: the part of `taken` that is a fair sample of it."""
    out = []
    for rid in pool:
        if rid not in taken:
            break
        out.append(rid)
    return out


def fair_words(fair: dict, positions: dict, what: str = "The ground truth and the drafted batches", part: str = "") -> str:
    """fair_sample()'s answer in words (for one part of the pool when `part` is given)."""
    of = f"the {part} part of the pool" if part else "the pool"
    if fair["fair"]:
        return f"{what} are the first {fair['first_n']} records of {of}: a fair sample."
    parts = []
    if fair["skipped_in_pool"]:
        parts.append(f"{fair['skipped_in_pool']} record(s) of {of} before the last one taken are not taken "
                     f"(the first at pool position {positions.get(fair['first_skipped'])})")
    if fair["outside_pool"]:
        parts.append(f"{fair['outside_pool']} record(s) taken are not in the pool")
    return "; ".join(parts) + "."
