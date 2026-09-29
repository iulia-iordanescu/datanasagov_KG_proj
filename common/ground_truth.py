"""
common/ground_truth.py -- reads the ground truth: every file in

    annotations/ground_truth/batch_000.csv     triple instances annotated before the pipeline
    annotations/ground_truth/batch_001.csv     corrected from step 050's draft batch 1
    annotations/ground_truth/batch_002.csv     … batch 2, and so on

taken together. Each file is a batch of records a person has corrected; the
ground truth is all of them. A file is added, never edited by a step: no
step writes into annotations/.

Every file has the columns

    id, subject, subject_class, predicate, object, object_class, source_text,
    all_facts_extracted

one row per triple instance, grouped by record (id). Any other column (e.g.
the `flags` column of a draft batch) is ignored, so a corrected draft batch
can be saved as it is. all_facts_extracted is 1 on every row of a record the
person has finished (every fact of its text is there), 0 while it is in
progress. A row with an id but an empty subject, predicate and object says
"this record was annotated and states no facts".

    from common.ground_truth import read_ground_truth
    gt = read_ground_truth()                 # or read_ground_truth(folder)
    gt.rows        [{..., "_origin": ["annotations/ground_truth/batch_000.csv#4"]}, …]
    gt.records     {record id: {"file", "rows", "finished"}}
    gt.problems    ["…"]: what a person must fix (see below)
    check_rows(gt, records)   rows with a typo to fix: an id not in the
                              catalog, a source text not in the record's
                              text, a DESCRIBES row with no entity class, …
                              (ROW_ERRORS, at the end of this file)

Problems, each listed, none silently resolved:
  - a record in more than one file: annotated twice, and code can't tell
    which is right (both are kept out of gt.records until fixed);
  - a record whose rows disagree on all_facts_extracted (some 1, some 0);
  - a file missing one of the columns above.

Shared by the steps that read ground truth (050, to know which records are
done and to check the files; 070, to score against it) and by the annotation
tool (annotate.py), which writes the files.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path

from common.audit import ORIGIN_FIELD, ref_path
from common.step import ANNOTATIONS_DIR

GROUND_TRUTH_DIR = ANNOTATIONS_DIR / "ground_truth"
PATTERN = "batch_*.csv"

#: The columns every ground truth file has, in this order.
COLUMNS = ["id", "subject", "subject_class", "predicate", "object", "object_class",
           "source_text", "all_facts_extracted"]


@dataclass
class GroundTruth:
    rows: list = field(default_factory=list)       # every row of every file, with its origin
    records: dict = field(default_factory=dict)    # {id: {"file", "rows", "finished"}}
    files: list = field(default_factory=list)      # the files read, in order
    problems: list = field(default_factory=list)   # what a person must fix


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
                gt.problems.append(f"{path.name} lacks the column(s) {', '.join(missing)}; not read")
                continue
            for position, raw in enumerate(reader):
                row = {c: (raw.get(c) or "").strip() for c in COLUMNS}
                if not row["id"]:
                    continue                       # a blank line
                row[ORIGIN_FIELD] = [f"{ref_path(path)}#{position}"]
                gt.rows.append(row)
                by_record.setdefault(row["id"], []).append(row)
                files = in_files.setdefault(row["id"], [])
                if path.name not in files:
                    files.append(path.name)

    for rid, rows in by_record.items():
        if len(in_files[rid]) > 1:
            gt.problems.append(f"record {rid} is in {' and '.join(in_files[rid])}: annotated twice; "
                               f"keep it in one file")
            continue
        marks = {r["all_facts_extracted"] for r in rows}
        if len(marks) > 1:
            gt.problems.append(f"record {rid} in {in_files[rid][0]}: all_facts_extracted is "
                               f"{' on some rows, '.join(sorted(marks))} on others; set it the same on every row")
        gt.records[rid] = {"file": in_files[rid][0], "rows": len(rows), "finished": marks == {"1"}}
    return gt


# --------------------------------------------------------------------------
# checking the rows against the records' texts (050 on every run; 070)
# --------------------------------------------------------------------------

#: What check_rows reports: things a person must fix, i.e. typos, never
#: matters of judgement (a reworded name is fine in ground truth).
ROW_ERRORS = {
    "id_not_in_records": "its id isn't a record of the catalog (a typo, or a record since removed)",
    "incomplete": "subject, predicate or object is empty, but not all three",
    "no_source_text": "it has no source text",
    "source_not_in_text": "its source text isn't in the record's text",
    "describes_subject_not_id": "the DESCRIBES row's subject isn't the record's id",
    "describes_undecided": "the DESCRIBES row has no entity class (X)",
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
            ref = row[ORIGIN_FIELD][0]
            file, position = ref.rsplit("/", 1)[-1].split("#")
            out.append({"where": f"{file} line {int(position) + 2}", "id": rid, "errors": errors})
    return out
