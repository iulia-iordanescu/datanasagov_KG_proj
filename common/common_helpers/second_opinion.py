"""
common/common_helpers/second_opinion.py -- the second opinion's record of which ground truth triples it found:

    annotations/second_opinion.csv

One row per ground truth triple of each finished record the second opinion (py helpers/second_opinion.py: a fresh
draft by another model, matched against the ground truth with step 070's pairing) has drafted, keyed by the record's
id and the classed triple as the ground truth writes it. Columns:

    id, subject, subject_class, predicate, object, object_class    the ground truth triple (the key, not a second
                                                                   home: the ground truth file stays the one home of
                                                                   the fact; a row whose triple is no longer there is
                                                                   stale, and step 070 says so)
    checked_by        the models whose draft was matched against this record, comma-separated
    found_by          of those, the models whose draft paired with this triple (exact or partial pair)
    found_exact_by    of those, the models whose draft paired with it exactly

A ground truth triple's GROUP by the second opinion (groups_of): FOUND when found_by names a model, NOT_FOUND when
checked_by names one and found_by none, NOT_CHECKED when the triple has no row (the record wasn't drafted, or the
triple was reworded since). Step 070 reports recall and partial F1 for each group. The file starts with its header
only; `py helpers/second_opinion.py --apply true` writes it, and nothing else does.

    from common.second_opinion import read_table, groups_of, write_table
    table = read_table(path)                 {(id, classed_key): row}, every row with its models as lists
    groups_of(rid, gt_triples, table)        [group per ground truth triple]
    write_table(path, rows)                  the rows, the models joined again
"""
from __future__ import annotations

from pathlib import Path

from common.files import read_csv_table, write_csv
from common.step import ANNOTATIONS_DIR
from common.triples_io import classed_key

PATH = ANNOTATIONS_DIR / "second_opinion.csv"
TRIPLE = ("subject", "subject_class", "predicate", "object", "object_class")
MODEL_COLUMNS = ("checked_by", "found_by", "found_exact_by")
COLUMNS = ["id", *TRIPLE, *MODEL_COLUMNS]
SEPARATOR = ", "
FOUND, NOT_FOUND, NOT_CHECKED = "found", "not found", "not checked"
GROUPS = (FOUND, NOT_FOUND, NOT_CHECKED)


def key_of(rid: str, triple: dict) -> tuple:
    """The key a row is filed under: the record's id and the classed triple as step 070's exact pairs compare it
    (common.triples_io.classed_key: instances evened out, component classes by loose match)."""
    return (rid.strip(), classed_key(triple))


def models(value) -> list:
    """The model names a cell lists, each once, in order."""
    return list(dict.fromkeys(m.strip() for m in str(value or "").split(",") if m.strip()))


def read_table(path: Path = PATH) -> dict:
    """{key_of(...): row} of the file; each row has every column of COLUMNS, the model columns as lists, and "_line"
    (its line in the file). A missing file, or one with its header only, reads as empty. A file lacking a column
    raises ValueError naming it."""
    path = Path(path)
    if not path.is_file():
        return {}
    columns, raw = read_csv_table(path)
    missing = [c for c in COLUMNS if c not in columns]
    if missing:
        raise ValueError(f"{path} lacks the column(s) {', '.join(missing)}; its header must name {', '.join(COLUMNS)}")
    out = {}
    for r in raw:
        if not (r.get("id") or "").strip():
            continue
        row = {c: (r.get(c) or "").strip() for c in COLUMNS}
        for c in MODEL_COLUMNS:
            row[c] = models(row[c])
        row["_line"] = r.get("_line")
        out[key_of(row["id"], row)] = row
    return out


def group_of(row: dict | None) -> str:
    """A ground truth triple's group from its row (None: no row)."""
    if row is None or not row["checked_by"]:
        return NOT_CHECKED
    return FOUND if row["found_by"] else NOT_FOUND


def groups_of(rid: str, gt_triples: list, table: dict) -> list:
    """Each ground truth triple's group (GROUPS), in order."""
    return [group_of(table.get(key_of(rid, t))) for t in gt_triples]


def stale_rows(table: dict, finished_rows: list) -> list:
    """The rows whose key matches no row of the finished ground truth (finished_rows: the rows of
    GroundTruth.select(EVALUABLE)): the triple was reworded or deleted, or its record isn't finished any more."""
    keys = {key_of(r["id"], r) for r in finished_rows}
    return [row for k, row in table.items() if k not in keys]


def write_table(path: Path, rows: list) -> None:
    """Write the rows (model columns as lists or as text) with COLUMNS."""
    out = []
    for r in rows:
        row = {c: r.get(c, "") for c in COLUMNS}
        for c in MODEL_COLUMNS:
            v = r.get(c, "")
            row[c] = SEPARATOR.join(v) if isinstance(v, (list, tuple)) else str(v or "")
        out.append(row)
    write_csv(path, COLUMNS, out)
