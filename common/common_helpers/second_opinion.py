"""
common/common_helpers/second_opinion.py -- the second opinion's record of which ground truth triples it found:

    annotations/second_opinion.csv

One row per ground truth triple of each finished record the second opinion (py helpers/second_opinion.py: fresh
drafts by another model, one per run, matched against the ground truth with step 070's pairing) has drafted, and per
model that drafted it, keyed by the record's id and the classed triple as the ground truth writes it. Columns:

    id, subject, subject_class, predicate, object, object_class    the ground truth triple (the key, not a second
                                                                   home: the ground truth file stays the one home of
                                                                   the fact; a row whose triple is no longer there is
                                                                   stale, and step 070 says so)
    model                  the model whose drafts were matched against this record
    runs                   how many of its runs drafted the record (each run a repeat: answers of its own)
    found_in_runs          in how many of those runs its draft paired with this triple (an exact or partial pair)
    found_exact_in_runs    in how many of them the pair was exact

A ground truth triple's GROUP by the second opinion (groups_of): FOUND when a model found it in at least one run,
NOT_FOUND when its record was drafted and no model found it in any run, NOT_CHECKED when the triple has no row (the
record wasn't drafted, or the triple was reworded since). Step 070 reports recall and partial F1 for each group, and
how many triples were found in 0, 1, ..., N runs (runs_of). The file starts with its header only;
`py helpers/second_opinion.py --apply true` writes it, and nothing else does.

    from common.second_opinion import read_table, groups_of, runs_of, write_table
    table = read_table(path)                 {(id, classed_key): entry}, entry["by"] = {model: its counts}
    groups_of(rid, gt_triples, table)        [group per ground truth triple]
    runs_of(rid, gt_triples, table)          [{model: (found_in_runs, runs)} per ground truth triple]
    write_table(path, entries)               the entries, one row per model
"""
from __future__ import annotations

from pathlib import Path

from common.files import read_csv_table, write_csv
from common.step import ANNOTATIONS_DIR
from common.triples_io import classed_key

PATH = ANNOTATIONS_DIR / "second_opinion.csv"
TRIPLE = ("subject", "subject_class", "predicate", "object", "object_class")
COUNT_COLUMNS = ("runs", "found_in_runs", "found_exact_in_runs")
COLUMNS = ["id", *TRIPLE, "model", *COUNT_COLUMNS]
FOUND, NOT_FOUND, NOT_CHECKED = "found", "not found", "not checked"
GROUPS = (FOUND, NOT_FOUND, NOT_CHECKED)


def key_of(rid: str, triple: dict) -> tuple:
    """The key a row is filed under: the record's id and the classed triple as step 070's exact pairs compare it
    (common.triples_io.classed_key: instances evened out, component classes by loose match)."""
    return (rid.strip(), classed_key(triple))


def counts(runs: int, found: int, exact: int) -> dict:
    """One model's counts for one ground truth triple, as an entry's "by" holds them."""
    return {"runs": runs, "found_in_runs": found, "found_exact_in_runs": exact}


def _counts_of(r: dict, path: Path) -> dict:
    """A row's three counts, checked: whole numbers, runs at least 1, found_in_runs at most runs, found_exact_in_runs
    at most found_in_runs. Anything else raises ValueError naming the line."""
    where = f"{path}, line {r.get('_line')}"
    try:
        n, k, j = (int((r.get(c) or "").strip()) for c in COUNT_COLUMNS)
    except ValueError:
        raise ValueError(f"{where}: {', '.join(COUNT_COLUMNS)} must be whole numbers, but are "
                         f"{', '.join(repr(r.get(c)) for c in COUNT_COLUMNS)}") from None
    if not (n >= 1 and 0 <= j <= k <= n):
        raise ValueError(f"{where}: the counts must satisfy runs >= 1 and 0 <= found_exact_in_runs <= found_in_runs "
                         f"<= runs, but are runs {n}, found_in_runs {k}, found_exact_in_runs {j}")
    return counts(n, k, j)


def read_table(path: Path = PATH) -> dict:
    """{key_of(...): entry} of the file: each entry has the id, the triple's columns, "_line" (its first line in the
    file) and "by", {model: counts(...) with "_line"}, models in the file's order. A missing file, or one with its
    header only, reads as empty. A file lacking a column, a row without a model, a count that isn't a whole number in
    bounds, or two rows of one model for one triple raise ValueError naming the line."""
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
        model = (r.get("model") or "").strip()
        if not model:
            raise ValueError(f"{path}, line {r.get('_line')}: the column model is empty; each row names the model "
                             f"whose runs it counts")
        row = {c: (r.get(c) or "").strip() for c in ("id", *TRIPLE)}
        entry = out.setdefault(key_of(row["id"], row), {**row, "_line": r.get("_line"), "by": {}})
        if model in entry["by"]:
            raise ValueError(f"{path}, lines {entry['by'][model]['_line']} and {r.get('_line')}: two rows of the model "
                             f"{model} for one ground truth triple of record {row['id']}; keep one")
        entry["by"][model] = {**_counts_of(r, path), "_line": r.get("_line")}
    return out


def group_of(entry: dict | None) -> str:
    """A ground truth triple's group from its entry (None: no row): found in at least one run of any model, else
    found in none."""
    if entry is None or not entry["by"]:
        return NOT_CHECKED
    return FOUND if any(c["found_in_runs"] for c in entry["by"].values()) else NOT_FOUND


def groups_of(rid: str, gt_triples: list, table: dict) -> list:
    """Each ground truth triple's group (GROUPS), in order."""
    return [group_of(table.get(key_of(rid, t))) for t in gt_triples]


def runs_of(rid: str, gt_triples: list, table: dict) -> list:
    """Each ground truth triple's {model: (found_in_runs, runs)}, in order ({} for one not checked)."""
    out = []
    for t in gt_triples:
        entry = table.get(key_of(rid, t))
        out.append({m: (c["found_in_runs"], c["runs"]) for m, c in (entry["by"] if entry else {}).items()})
    return out


def stale_rows(table: dict, finished_rows: list) -> list:
    """The entries whose key matches no row of the finished ground truth (finished_rows: the rows of
    GroundTruth.select(EVALUABLE)): the triple was reworded or deleted, or its record isn't finished any more."""
    keys = {key_of(r["id"], r) for r in finished_rows}
    return [entry for k, entry in table.items() if k not in keys]


def write_table(path: Path, entries: list) -> None:
    """Write the entries ({id, the triple's columns, "by": {model: counts}}), one row per model, with COLUMNS."""
    rows = [{**{c: e.get(c, "") for c in ("id", *TRIPLE)}, "model": model, **{c: n[c] for c in COUNT_COLUMNS}}
            for e in entries for model, n in e["by"].items()]
    write_csv(path, COLUMNS, rows)
