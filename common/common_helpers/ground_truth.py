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

    from common.ground_truth import read_ground_truth, read_pool, SCHEMA_EVIDENCE
    gt = read_ground_truth(folder, read_pool(splits_path))   # the pool gives each record its part
    gt.records     {record id: {"file", "files", "rows", "state", "finished", "part"}}: every record in a file
    gt.state(id)   its one state: absent, in two files, bad mark, unfinished, or finished (STATES)
    gt.select(SCHEMA_EVIDENCE)   the rows and ids one purpose takes (PURPOSES): SCHEMA_EVIDENCE (finished tuning
                   records: all that may shape the ground truth schema a model or a check sees), EVALUABLE
                   (finished records, of a part with parts=), ANNOTATED (every record in a file), TO_FIX
                   (in two files, a bad mark, or unfinished). No consumer filters the rows itself: they are
                   handed out only by purpose, each row {..., "_origin": ["annotations/ground_truth/batch_000.csv#4"]}
    gt.with_file(name, rows)     the ground truth as it will be once a file holds these rows (the annotation tool)
    gt.problems    ["…"]: what a person must fix (see below)
    gt.repeats     [{"message", "copies"}]: the problems that stop 070 (a classed triple twice in a record)
    fair_sample, fair_prefix  whether ids are the first records of a pool order (below)
    pool_parts(pool_rows)     the pool's ids in order, split into its parts: {"tuning": […], "held-out": […]}
    read_pool(splits_path)    the pool, from 030's splits.json: [{"id", "position", "part", …}]
    ground_truth_schema_view(ground_truth_schema, gt)  the ground truth schema as every model and check sees it:
                              its file, plus the component classes coined and the patterns used in the finished
                              tuning records (with_coined over SCHEMA_EVIDENCE)
    with_coined(ground_truth_schema, selection)  the same over any selection
    check_rows(selection, records)   rows with an error to fix: an id not in the
                              catalog, a source text not in the record's
                              text, a describes triple with no describes class, …
                              (ROW_ERRORS, at the end of this file)

Problems, each listed, none silently resolved:
  - a record in more than one file: annotated twice, and code can't tell
    which is right (its state is "in two files": only ANNOTATED and TO_FIX take it, until fixed);
  - a record whose rows disagree on all_facts_extracted (some 1, some 0);
  - the same classed triple twice in a record: the same subject instance,
    predicate and object instance and the same subject class and object class,
    compared by the key step 070's exact pairs use (common/common_helpers/
    triples_io.classed_key: instances by text_match.instance_key, so "1 km" and
    "1000 m" are the same; component classes by component_class_key; a
    symmetric predicate's subject and object either way round). Only
    one copy can be paired, so 070 would count the other as ground truth only. Also in
    gt.repeats: 070 refuses to run while there is one;
  - a record with an all_facts_extracted value other than 0 and 1 (FINISHED_MARKS) on some row (reported
    instead of the disagreement above);
  - the same subject instance, predicate, and object instance twice in a
    record, with different entity classes: one fact given two entity
    classes by mistake, or two facts that differ only in them;
  - a file missing one of the columns above;
  - a file named batch_*.csv whose name isn't batch_<NNN>.csv (NUMBERED): not read, so that reading the ground
    truth and numbering the next drafted batch (050) agree.
A problem about lines of a file shows each of them on a line of its own
(the message has several lines). For a person, all seven: docs/running_on_nasa_laptop.md, section 7.
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
from common.triples_io import KIND_KEYS, canonical_row, classed_key, component_class_key, is_describes
from common.validate import (DESCRIBES_SUBJECT_NOT_ID, DESCRIBES_UNDECIDED, ID_NOT_IN_RECORDS, INCOMPLETE, NO_SOURCE_TEXT,
                             SEVERAL_DESCRIBES, SOURCE_NOT_IN_TEXT)

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


#: Each record's one state in the ground truth (GroundTruth.state). Every consumer asks for rows by purpose
#: (GroundTruth.select, PURPOSES), never filters the rows itself.
ABSENT = "absent"                # in no ground truth file
IN_TWO_FILES = "in two files"    # annotated twice: which annotation is right can't be told
BAD_MARK = "bad mark"            # an all_facts_extracted value other than 0 and 1 (FINISHED_MARKS) on some row
UNFINISHED = "unfinished"        # in progress: 0 on some row (or on every row)
FINISHED = "finished"            # 1 on every row: a person checked that every fact of its text is there
STATES = (IN_TWO_FILES, BAD_MARK, UNFINISHED, FINISHED)

#: What the rows are for (GroundTruth.select), each with the states and the parts of the pool it takes (None: every
#: part, and records outside the pool):
#:   SCHEMA_EVIDENCE  what may shape the ground truth schema as any model or check sees it (the component classes
#:                    coined, the patterns used, a "source:" line naming ground truth records): finished tuning
#:                    records only, so neither a model's uncorrected draft nor a held-out record reaches a prompt or
#:                    a check;
#:   EVALUABLE        what step 070 evaluates against and step 060 extracts from: finished records (of a part, when
#:                    asked);
#:   ANNOTATED        every record in a ground truth file, whatever its state: what 050 never drafts again, and what
#:                    the annotation tool renames, merges, counts and guards (a held-out record's use);
#:   TO_FIX           what a person still has to finish or fix before the record can be evaluated.
SCHEMA_EVIDENCE, EVALUABLE, ANNOTATED, TO_FIX = "schema evidence", "evaluable", "annotated", "to fix"
PURPOSES = {SCHEMA_EVIDENCE: ({FINISHED}, ("tuning",)),
            EVALUABLE: ({FINISHED}, None),
            ANNOTATED: (set(STATES), None),
            TO_FIX: ({IN_TWO_FILES, BAD_MARK, UNFINISHED}, None)}


@dataclass(frozen=True)
class Selection:
    """The rows of the records one purpose takes (GroundTruth.select), in file order, and those records' ids in the
    order first met."""
    purpose: str
    rows: tuple
    ids: tuple


@dataclass
class GroundTruth:
    _rows: list = field(default_factory=list)      # every row of every file, with its origin: only select() hands them out
    records: dict = field(default_factory=dict)    # {id: {"file", "files", "rows", "state", "finished", "part"}}
    files: list = field(default_factory=list)      # the files read, in order
    problems: list = field(default_factory=list)   # what a person must fix
    repeats: list = field(default_factory=list)    # of those, a classed triple twice in a record: stops 070
    parts: dict | None = None                      # {id: "tuning" | "held-out"}, from the pool; None: no pool given
    _files_rows: list = field(default_factory=list)  # [(file name, [rows])]: what with_file() and with_pool() rebuild from
    _file_problems: list = field(default_factory=list)  # the problems of the files themselves (a name, a column)

    def state(self, rid: str) -> str:
        """The record's one state: ABSENT, or one of STATES."""
        return self.records[rid]["state"] if rid in self.records else ABSENT

    def part(self, rid: str) -> str | None:
        """The record's part of the pool ("tuning" or "held-out"), or None when it isn't in the pool."""
        if self.parts is None:
            raise ValueError("the ground truth was read without the pool (030's splits.json), so a record's part "
                             "isn't known: read it with read_ground_truth(folder, pool), or call with_pool(pool)")
        return self.parts.get(rid)

    def select(self, purpose: str, parts=None) -> Selection:
        """The rows and ids of the records `purpose` (PURPOSES) takes. parts ("tuning", "held-out", or a list of
        them) narrows them to those parts of the pool; it never widens SCHEMA_EVIDENCE beyond tuning."""
        states, own = PURPOSES[purpose]
        asked = (parts,) if isinstance(parts, str) else tuple(parts) if parts is not None else None
        keep = own if asked is None else tuple(p for p in asked if own is None or p in own)
        if keep is not None and self.parts is None:
            self.part("")                          # raises: the part isn't known
        ids = [rid for rid, r in self.records.items()
               if r["state"] in states and (keep is None or self.parts.get(rid) in keep)]
        taken = set(ids)
        return Selection(purpose, tuple(r for r in self._rows if r["id"] in taken), tuple(ids))

    def with_pool(self, pool_rows: list) -> "GroundTruth":
        """The same ground truth, each record with its part from the pool (read_pool()'s rows)."""
        return _build(self._files_rows, self.files, self._file_problems, pool_rows)

    def with_file(self, name: str, rows: list) -> "GroundTruth":
        """The ground truth as it will be once the file `name` (e.g. "batch_004.csv") holds `rows` (dicts with the
        columns of FILE_COLUMNS), the other files as they are: what the annotation tool checks a save against."""
        ref = ref_path(GROUND_TRUTH_DIR / name)
        files_rows = sorted([(n, rs) for n, rs in self._files_rows if n != name]
                            + [(name, [_as_read(r, ref, i) for i, r in enumerate(rows) if str(r.get("id") or "").strip()])])
        pool = None if self.parts is None else [{"id": i, "part": p} for i, p in self.parts.items()]
        return _build(files_rows, self.files, self._file_problems, pool)


#: Each row's line in its file, as read (blank lines and source texts spanning lines counted).
LINE_FIELD = "_line"


def _as_read(raw: dict, ref: str, position: int, line: int | None = None) -> dict:
    """A row as read_ground_truth keeps it: every column of FILE_COLUMNS, tidied as every row is
    (common.triples_io.canonical_row: one line, spaces evened out; "" for an empty one), with its origin and its line
    in the file (the line it ends on; without one, as a file written from these rows would have it)."""
    row = canonical_row({c: str(raw.get(c) or "") for c in FILE_COLUMNS}, keys=FILE_COLUMNS, blank="")
    row[ORIGIN_FIELD] = [f"{ref}#{position}"]
    row[LINE_FIELD] = line if line is not None else position + 2          # the header is line 1
    return row


def marks_state(marks) -> str:
    """The state a record's all_facts_extracted values in one file give (its rows' marks): FINISHED when every one is
    "1", BAD_MARK when one is neither "0" nor "1" (FINISHED_MARKS), else UNFINISHED. The one rule, for the ground
    truth (read_ground_truth) and for one file's view of it (the annotation tool's tick box and batch counts)."""
    marks = set(marks)
    return BAD_MARK if marks - set(FINISHED_MARKS) else FINISHED if marks == {"1"} else UNFINISHED


def read_ground_truth(folder: Path = GROUND_TRUTH_DIR, pool=None) -> GroundTruth:
    """Every ground truth file of `folder` (NUMBERED), taken together. pool: read_pool()'s rows (030's splits.json),
    which give each record its part; without them, select() refuses what needs a part (SCHEMA_EVIDENCE, parts=)."""
    files, files_rows, problems = [], [], []
    for path in sorted(Path(folder).glob(PATTERN)):
        if not NUMBERED.fullmatch(path.name):
            problems.append(f"{ref_path(path)} isn't read: a ground truth file is named batch_, its batch number "
                            f"in three digits or more, then .csv (e.g. {file_name(6)}), so that reading the ground "
                            f"truth and numbering the next drafted batch agree. Rename it to that shape (a number no "
                            f"other file has), then rerun.")
            continue
        files.append(path)
        with open(path, encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh)
            missing = [c for c in COLUMNS if c not in (reader.fieldnames or [])]
            if missing:
                problems.append(f"{ref_path(path)} lacks the column(s) {', '.join(missing)}, so none of its rows "
                                f"were read. Restore its header line, which names the columns: "
                                f"{', '.join(COLUMNS)}.")
                continue
            rows = []
            for position, raw in enumerate(reader):
                if (raw.get("id") or "").strip():                      # else a blank line
                    rows.append(_as_read(raw, ref_path(path), position, reader.line_num))
            files_rows.append((path.name, rows))
    return _build(files_rows, files, problems, pool)


def _build(files_rows: list, files: list, file_problems: list, pool) -> GroundTruth:
    """The ground truth of these files' rows: each record's state and part, and every problem."""
    gt = GroundTruth(files=list(files), parts=None if pool is None else {r["id"]: r.get("part") for r in pool},
                     _files_rows=list(files_rows), _file_problems=list(file_problems), problems=list(file_problems))
    in_files = {}                                  # {id: [files it appears in]}
    by_record = {}                                 # {id: [its rows]}
    for name, rows in files_rows:
        for row in rows:
            gt._rows.append(row)
            by_record.setdefault(row["id"], []).append(row)
            names = in_files.setdefault(row["id"], [])
            if name not in names:
                names.append(name)

    for rid, rows in by_record.items():
        entry = {"file": in_files[rid][0], "files": list(in_files[rid]), "rows": len(rows),
                 "part": None if gt.parts is None else gt.parts.get(rid)}
        if len(in_files[rid]) > 1:
            gt.problems.append(f"record {rid} is in {' and '.join(in_files[rid])}: annotated twice, and which "
                               f"annotation is right can't be told, so the record is left out until fixed. Delete its "
                               f"rows from all files but one (by hand: the annotation tool can't remove a record).")
            gt.records[rid] = {**entry, "state": IN_TWO_FILES, "finished": False}
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
        state = marks_state(marks)
        gt.records[rid] = {**entry, "state": state, "finished": state == FINISHED}
        groups = {}                                # triple key -> {(subject class, object class) keys: [rows]}
        for row in rows:
            if not (row["subject"] and row["predicate"] and row["object"]) or is_describes(row):
                continue
            fact, subject_class, object_class = classed_key(row)       # the key 070's exact pairs use
            groups.setdefault(fact, {}).setdefault((subject_class, object_class), []).append(row)
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

#: What check_rows reports, in the report's words: errors a person must fix, never
#: matters of judgment (a reworded subject or object instance is fine in
#: ground truth). The codes: common/common_helpers/validate.py.
ROW_ERRORS = {
    ID_NOT_IN_RECORDS: "its id isn't a record of the catalog (a typo, or a record since removed): correct the id, "
                         "or delete the row",
    INCOMPLETE: "subject, predicate, or object is empty, but not all three: fill in the empty ones, or delete the row",
    NO_SOURCE_TEXT: "it has no source text: in the annotation tool, select the passage that states it and press "
                      "\"Use selection\"",
    SOURCE_NOT_IN_TEXT: "its source text isn't in the record's text: in the annotation tool, select the passage and "
                          "press \"Use selection\" to copy it exactly",
    DESCRIBES_SUBJECT_NOT_ID: "the describes triple's subject isn't the record's id: write the record's id there",
    DESCRIBES_UNDECIDED: "the describes triple has no describes class (X): choose its object class, the entity class of its object instance",
    SEVERAL_DESCRIBES: "the record has another describes triple before this one, and a record has one: delete this one "
                       "(or the other, if this one's describes class is the right one)",
}


def check_rows(selection: Selection, records: dict) -> list:
    """Every row of the selection (GroundTruth.select) with something to fix, as {"where": "batch_000.csv line 6",
    "id", "errors": [names of ROW_ERRORS]}. records is {id: record} (020's
    records.jsonl, read by common.records_io.load_records)."""
    from common.chunking import full_text
    from common.text_match import Text
    from common.triples_io import is_describes
    from common.validate import check_describes, check_triple_instance

    texts, out, described = {}, [], set()
    for row in _rows_of(selection):
        rid = row["id"]
        filled = [bool(row[k]) for k in ("subject", "predicate", "object")]
        if rid not in records:
            errors = [ID_NOT_IN_RECORDS]
        elif not any(filled):
            errors = []                            # "annotated, states no facts"
        elif not all(filled):
            errors = [INCOMPLETE]
        elif is_describes(row):
            errors = check_describes(row, rid)[0] + ([SEVERAL_DESCRIBES] if rid in described else [])
            described.add(rid)
        else:
            if rid not in texts:
                texts[rid] = Text(full_text(records[rid]))
            errors = check_triple_instance(row, texts[rid], records[rid].get("title") or "")[0]
        if errors:
            file = row[ORIGIN_FIELD][0].rsplit("/", 1)[-1].split("#")[0]
            out.append({"where": f"{file} line {row[LINE_FIELD]}", "id": rid, "errors": errors})
    return out


# --------------------------------------------------------------------------
# what step 070 evaluates against must be clean (070, the status)
# --------------------------------------------------------------------------

def evaluable_problems(gt: GroundTruth, records: dict, ground_truth_schema: dict, schema_path: str = "",
                       pending: list = (), pending_path: str = "annotations/pending_triples.csv") -> list:
    """Every reason the finished records (EVALUABLE, every part), or the facts that wait on an expert (pending:
    common.left_out.read_pending's rows), aren't fit to evaluate against, each one line naming the file and line, the
    record, the problem, and what to do. Step 070 stops while there is one (a finished record says every fact is
    there, but nobody checked its rows: the annotation tool lets a record be ticked finished only without an error,
    and a hand edit can still leave one); the status lists them. Checked, in this order:
      - every row error of check_rows (ROW_ERRORS: an id not in the catalog, an incomplete row, no source text or one
        not in the record's text, the describes triple's subject not the record's id, an undecided describes class,
        a second describes triple);
      - every entity class or predicate the finished records use that the ground truth schema lacks (a coined one:
        step 070 translates only into the ground truth schema);
      - each pending row's entity classes and predicate, which must be the ground truth schema's too: one it lacks
        could never equal a translated extracted triple's, so the occurrence it waits for would count against
        precision instead of being left out.
    records: 020's records.jsonl by id; schema_path: the ground truth schema's file, for messages."""
    finished = gt.select(EVALUABLE)
    lines = [f"{r['where']} (record {r['id']}): " + "; ".join(ROW_ERRORS[e] for e in r["errors"])
             for r in check_rows(finished, records)]
    coined = with_coined(ground_truth_schema, finished)["coined"]
    where = f" ({schema_path})" if schema_path else ""
    lines += [f"{use}: not in the ground truth schema{where}, so step 070 can't translate into it: add it with a one-line "
              f"definition (`py helpers/annotate.py`, view *Ground truth*: the ✖ under it has a button), or fix the "
              f"typo where it's used" for use in coined_uses(finished, coined)]
    from common.left_out import NO_TRIPLE
    known = {kind: {component_class_key(n) for n in ground_truth_schema[kind]} for kind in ("entity_classes", "predicates")}
    for row in pending:
        missing = [f"its {slot.replace('_', ' ')} {row[slot]}" for slot, kind in (
                       ("subject_class", "entity_classes"), ("predicate", "predicates"), ("object_class", "entity_classes"))
                   if component_class_key(row[slot]) not in known[kind]]
        if missing:
            lines.append(f"{pending_path} line {row.get('line', '?')} (record {row['id']}): {' and '.join(missing)} "
                         f"{'is' if len(missing) == 1 else 'are'}n't in the ground truth schema{where}, so no "
                         f"extracted triple could ever match the fact that waits, and it would count against "
                         f"precision: write the ground truth schema's entity class or predicate the fact would have "
                         f"(or fix the typo); if none fits, delete the row and write \"{NO_TRIPLE} <why>\" under its "
                         f"item in annotations/left_out.md")
    return lines


# --------------------------------------------------------------------------
# the ground truth schema (040, 050, 060, 070, the annotation tool, the status)
# --------------------------------------------------------------------------

def _rows_of(selection: Selection) -> tuple:
    """A selection's rows. A GroundTruth is refused: which records count is GroundTruth.select's to say."""
    if not isinstance(selection, Selection):
        raise TypeError("pass the rows of one purpose, gt.select(...) (common/common_helpers/ground_truth.py, "
                        "PURPOSES), not the whole ground truth")
    return selection.rows


def ground_truth_schema_view(ground_truth_schema: dict, gt: GroundTruth) -> dict:
    """The ground truth schema as every model and check sees it: with_coined over the finished tuning records only
    (SCHEMA_EVIDENCE). The one view 040 (its comparison), 050 (its prompt and its checks), 060 (when it extracts
    with the ground truth schema) and the annotation tool (its suggestions, pattern buttons and pattern flags) use, so
    a model's uncorrected draft or a held-out record never shapes it."""
    return with_coined(ground_truth_schema, gt.select(SCHEMA_EVIDENCE))


def with_coined(ground_truth_schema: dict, selection: Selection) -> dict:
    """The ground truth schema's entity classes and predicates
    (ground_truth_schema, as common.schema_io.read_ground_truth_schema reads it),
    plus every one the selection's ground truth triples use that it lacks. Component
    classes are compared as common.triples_io.component_class_key does (ignoring case and
    punctuation), keeping the first spelling met; the describes triple's own
    component classes (the entity class CatalogEntry, the predicate DESCRIBES), the undecided
    entity class X (each in any spelling, as component_class_key compares them) and anything
    without a letter or digit (e.g. "-") are not counted.

    Returned in the schema shape, plus "coined": {"entity_classes": [...],
    "predicates": [...]}, the component classes used in the selection but
    not in the ground truth schema, in the order first used. A coined component
    class has an empty definition: only the ground truth schema has definitions.

    "patterns" is the file's patterns, then every other pattern the selection's ground truth
    triples use ("used_patterns", in the order first used): the file's say
    "where a predicate has been used", which the ground truth itself says, so
    nobody keeps them up to date by hand. Which rows count is the caller's
    selection: ground_truth_schema_view takes the finished tuning records (SCHEMA_EVIDENCE)."""
    from common.triples_io import ENTRY_CLASS, ENTRY_PREDICATE, UNDECIDED, component_class_key

    rows = _rows_of(selection)
    # written by code (the describes triple), never coined, in any spelling (component_class_key), each in its own kind
    fixed = {"entity_classes": {component_class_key(ENTRY_CLASS), component_class_key(UNDECIDED)},
             "predicates": {component_class_key(ENTRY_PREDICATE)}}
    out = {"entity_classes": dict(ground_truth_schema["entity_classes"]), "predicates": dict(ground_truth_schema["predicates"]),
           "patterns": list(ground_truth_schema.get("patterns", [])),
           "coined": {"entity_classes": [], "predicates": []}, "used_patterns": []}
    in_file = {tuple(component_class_key(x) for x in p) for p in out["patterns"]}
    for key, spelled in used_patterns(selection).items():   # patterns: the file's, then every other one used
        if key not in in_file:
            out["patterns"].append(spelled)
            out["used_patterns"].append(spelled)
    known = {kind: {component_class_key(n) for n in out[kind]} for kind in ("entity_classes", "predicates")}
    for row in rows:
        for kind, name in (("entity_classes", row["subject_class"]), ("entity_classes", row["object_class"]),
                           ("predicates", row["predicate"])):
            key = component_class_key(name)
            if key and key not in fixed[kind] and key not in known[kind]:
                out[kind][name] = ""
                out["coined"][kind].append(name)
                known[kind].add(key)
    return out


def coined_uses(selection: Selection, coined: dict) -> list:
    """Where each coined component class is used in the selection, for messages: ["Instrumnet (entity class):
    batch_000.csv lines 4, 9", ...], in with_coined()'s order. coined is with_coined()["coined"]."""
    from common.triples_io import component_class_key
    where = {}
    for row in _rows_of(selection):
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
# KIND_KEYS ({kind: the schema's key}) is common/common_helpers/triples_io.py's, imported above; status.py and
# the annotation tool import it from here too.


def uses_of(selection: Selection, kind: str, name: str) -> list:
    """The selection's ground truth triples and describes triples that use a component class (compared as
    component_class_key does); kind is "entity class" or "predicate"."""
    columns = ("subject_class", "object_class") if kind == "entity class" else ("predicate",)
    return [r for r in _rows_of(selection) if any(component_class_key(r[c]) == component_class_key(name) for c in columns)]


def pattern_of(row: dict) -> tuple | None:
    """A ground truth triple's pattern as compared (component_class_key of its subject class, predicate, and
    object class), or None for the describes triple or a row missing one of them."""
    key = tuple(component_class_key(row.get(c)) for c in ("subject_class", "predicate", "object_class"))
    return None if is_describes(row) or not all(key) else key


def used_patterns(selection: Selection) -> dict:
    """{pattern key: (subject class, predicate, object class) as first spelled}, in the order first used: every
    pattern the selection's ground truth triples use."""
    out = {}
    for r in _rows_of(selection):
        key = pattern_of(r)
        if key and key not in out:
            out[key] = (r["subject_class"].strip(), r["predicate"].strip(), r["object_class"].strip())
    return out


def pattern_uses(selection: Selection) -> collections.Counter:
    """How many of the selection's ground truth triples use each pattern (pattern_of)."""
    return collections.Counter(k for r in _rows_of(selection) if (k := pattern_of(r)))


def ground_truth_schema_gaps(ground_truth_schema: dict, gt: GroundTruth) -> dict:
    """What the finished records (EVALUABLE, every part: step 070 stops while one uses a component class the ground
    truth schema lacks) use that the ground truth schema lacks: the entity classes and predicates coined there, each
    with how many of those rows use it and the parts of the records using it ("tuning", "held-out", or None for a
    record outside the pool; a held-out one can't be added, since the ground truth schema is frozen for held-out
    records). (Patterns are never missing: the ground truth schema's patterns are those of its file plus every one
    the finished tuning records use; see ground_truth_schema_view.) Shared by the annotation tool and the project's
    status (common/common_helpers/status.py)."""
    finished = gt.select(EVALUABLE)
    coined = with_coined(ground_truth_schema, finished)["coined"]
    out = []
    for kind, key in KIND_KEYS.items():
        for n in coined[key]:
            uses = uses_of(finished, kind, n)
            parts = sorted({str(gt.records[r["id"]]["part"]) for r in uses})
            out.append({"entry_type": kind, "component_class": n, "uses": len(uses), "parts": parts})
    return {"component_classes": out}


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


#: The two parts of the pool (docs/terminology.md, *held-out part*), each value as 030's splits.json writes it.
TUNING, HELD_OUT = "tuning", "held-out"
PARTS = (TUNING, HELD_OUT)


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
