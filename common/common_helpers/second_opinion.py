"""
common/common_helpers/second_opinion.py -- the second opinion's record of which ground truth triples it found:

    annotations/second_opinion.csv

One row per ground truth triple of each finished record the second opinion (py helpers/second_opinion.py: fresh
drafts by another model, one per repeat, matched against the ground truth with step 070's pairing) has drafted, and per
model that drafted it, keyed by the record's id and the classed triple as the ground truth writes it. Columns:

    id, subject, subject_class, predicate, object, object_class    the ground truth triple (the key, not a second
                                                                   home: the ground truth file stays the one home of
                                                                   the fact; a row whose triple is no longer there is
                                                                   stale, and step 070 says so)
    model                     the model whose drafts were matched against this record
    repeats                   how many of its repeats drafted the record (each with answers of its own)
    found_in_repeats          in how many of those repeats its draft paired with this triple (an exact or partial pair)
    found_exact_in_repeats    in how many of them the pair was exact

A ground truth triple's GROUP by the second opinion (groups_of): FOUND when a model found it in at least one repeat,
NOT_FOUND when its record was drafted and no model found it in any repeat, NOT_CHECKED when the triple has no row (the
record wasn't drafted, or the triple was reworded since). Step 070 reports recall and partial F1 for each group, and
how many triples were found in 0, 1, ..., N repeats (repeats_of). The file starts with its header only;
`py helpers/second_opinion.py --apply true` writes it, and nothing else does.

    from common.second_opinion import read_table, groups_of, repeats_of, write_table
    table = read_table(path)                 {(id, classed_key): entry}, entry["by"] = {model: its counts}
    groups_of(rid, gt_triples, table)        [group per ground truth triple]
    repeats_of(rid, gt_triples, table)       [{model: (found_in_repeats, repeats)} per ground truth triple]
    write_table(path, entries)               the entries, one row per model

The second opinion's facts the ground truth lacks, for review:

    annotations/second_opinion_candidates.csv

One row per draft-only classed triple (a fresh draft's classed triple that paired with no ground truth triple, the
union over the repeats) of each TUNING record and per model, keyed by the record's id, the classed triple (as key_of
compares it) and the model. A held-out record's are never written: reviewing them would let the held-out part shape
the ground truth and its rules (annotations/guidelines.md, Before you start). Columns:

    id, title                 the record and its title
    subject, subject_class, predicate, object, object_class, source_text    the draft's classed triple and its source text
    model                     the model whose repeats proposed it
    proposed_in_repeats       in how many of its repeats a draft proposed it (1 to repeats)
    repeats                   how many of its repeats drafted the record
    decision                  the reviewer's, empty until reviewed: one of DECISIONS (below)

`py helpers/second_opinion.py --apply true` writes it beside second_opinion.csv, and nothing else does; a rerun
replaces the model's rows on the records drafted again, and keeps every decision already filled for the same record
and classed triple.

    from common.second_opinion import read_candidates, write_candidates, decision_problem
    rows = read_candidates(path)             [row] in the file's order, each with "_line"; ValueError naming the line
    decision_problem(text, rules)            why a decision isn't allowed, or None
    write_candidates(path, rows)             the rows, with CANDIDATE_COLUMNS
"""
from __future__ import annotations

import re
from pathlib import Path

from common.files import read_csv_table, write_csv
from common.step import ANNOTATIONS_DIR
from common.triples_io import classed_key

PATH = ANNOTATIONS_DIR / "second_opinion.csv"
TRIPLE = ("subject", "subject_class", "predicate", "object", "object_class")
COUNT_COLUMNS = ("repeats", "found_in_repeats", "found_exact_in_repeats")
#: The counts' names before 2026-11-01, when "run" became "repeat" (a run is one execution of a step; these are
#: repeats within one): a header with them is refused, naming its line.
OLD_COUNT_COLUMNS = ("runs", "found_in_runs", "found_exact_in_runs")
COLUMNS = ["id", *TRIPLE, "model", *COUNT_COLUMNS]
FOUND, NOT_FOUND, NOT_CHECKED = "found", "not found", "not checked"
GROUPS = (FOUND, NOT_FOUND, NOT_CHECKED)



def candidates_path_for(table_path: Path) -> Path:
    """The candidates file beside a table file: annotations/second_opinion.csv -> second_opinion_candidates.csv."""
    table_path = Path(table_path)
    return table_path.with_name(f"{table_path.stem}_candidates.csv")


CANDIDATES_PATH = candidates_path_for(PATH)
CANDIDATE_COLUMNS = ["id", "title", *TRIPLE, "source_text", "model", "proposed_in_repeats", "repeats", "decision"]
#: The reviewer's decisions on a draft-only classed triple (the column decision; empty: not reviewed yet): ADDED, the
#: fact is now in the ground truth; LEFT_OUT, the annotation guidelines leave it out, naming the rule as
#: "left out (<section of annotations/guidelines.md>, rule <n>)", e.g. "left out (Writing a classed triple, rule 21)";
#: IN_OTHER_WORDS, the ground truth already states the same fact in other words (the pairing couldn't match them).
ADDED, IN_OTHER_WORDS = "added", "already in the ground truth in other words"
LEFT_OUT = "left out (<section>, rule <n>)"
DECISIONS = (ADDED, LEFT_OUT, IN_OTHER_WORDS)
_LEFT_OUT = re.compile(r"^left out \((?P<section>[^()]+), rule (?P<rule>\d+)\)$")


def key_of(rid: str, triple: dict) -> tuple:
    """The key a row is filed under: the record's id and the classed triple as step 070's exact pairs compare it
    (common.triples_io.classed_key: instances evened out, component classes by loose match)."""
    return (rid.strip(), classed_key(triple))


def counts(repeats: int, found: int, exact: int) -> dict:
    """One model's counts for one ground truth triple, as an entry's "by" holds them."""
    return {"repeats": repeats, "found_in_repeats": found, "found_exact_in_repeats": exact}


def _counts_of(r: dict, path: Path) -> dict:
    """A row's three counts, checked: whole numbers, repeats at least 1, found_in_repeats at most repeats, found_exact_in_repeats
    at most found_in_repeats. Anything else raises ValueError naming the line."""
    where = f"{path}, line {r.get('_line')}"
    try:
        n, k, j = (int((r.get(c) or "").strip()) for c in COUNT_COLUMNS)
    except ValueError:
        raise ValueError(f"{where}: {', '.join(COUNT_COLUMNS)} must be whole numbers, but are "
                         f"{', '.join(repr(r.get(c)) for c in COUNT_COLUMNS)}") from None
    if not (n >= 1 and 0 <= j <= k <= n):
        raise ValueError(f"{where}: the counts must satisfy repeats >= 1 and 0 <= found_exact_in_repeats <= found_in_repeats "
                         f"<= repeats, but are repeats {n}, found_in_repeats {k}, found_exact_in_repeats {j}")
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
    old = [c for c in OLD_COUNT_COLUMNS if c in columns]
    if old:
        raise ValueError(f"{path}, line 1: the header names {', '.join(old)}, the old names of the counts; rename "
                         f"them {', '.join(COUNT_COLUMNS[OLD_COUNT_COLUMNS.index(c)] for c in old)}, so that the "
                         f"header is {','.join(COLUMNS)}")
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
                             f"whose repeats it counts")
        row = {c: (r.get(c) or "").strip() for c in ("id", *TRIPLE)}
        entry = out.setdefault(key_of(row["id"], row), {**row, "_line": r.get("_line"), "by": {}})
        if model in entry["by"]:
            raise ValueError(f"{path}, lines {entry['by'][model]['_line']} and {r.get('_line')}: two rows of the model "
                             f"{model} for one ground truth triple of record {row['id']}; keep one")
        entry["by"][model] = {**_counts_of(r, path), "_line": r.get("_line")}
    return out


def group_of(entry: dict | None) -> str:
    """A ground truth triple's group from its entry (None: no row): found in at least one repeat of any model, else
    found in none."""
    if entry is None or not entry["by"]:
        return NOT_CHECKED
    return FOUND if any(c["found_in_repeats"] for c in entry["by"].values()) else NOT_FOUND


def groups_of(rid: str, gt_triples: list, table: dict) -> list:
    """Each ground truth triple's group (GROUPS), in order."""
    return [group_of(table.get(key_of(rid, t))) for t in gt_triples]


def repeats_of(rid: str, gt_triples: list, table: dict) -> list:
    """Each ground truth triple's {model: (found_in_repeats, repeats)}, in order ({} for one not checked)."""
    out = []
    for t in gt_triples:
        entry = table.get(key_of(rid, t))
        out.append({m: (c["found_in_repeats"], c["repeats"]) for m, c in (entry["by"] if entry else {}).items()})
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


# --------------------------------------------------------------------------
# annotations/second_opinion_candidates.csv: the draft-only facts, for review

def candidate_key(row: dict) -> tuple:
    """The key a decision is kept under: the record's id and the classed triple (key_of), whichever model proposed it."""
    return key_of(row.get("id") or "", row)


def decision_problem(text: str, rules: dict) -> str | None:
    """Why a decision isn't one of DECISIONS, or None (empty is allowed: not reviewed yet). rules: {(section, rule
    number): words} of annotations/guidelines.md (common.expert_questions.guideline_rules), so that a left-out
    decision names a rule the guidelines have."""
    text = text.strip()
    if text in ("", ADDED, IN_OTHER_WORDS):
        return None
    m = _LEFT_OUT.match(text)
    if not m:
        return (f"the decision {text!r} isn't one of: {ADDED!r}; {LEFT_OUT!r}, e.g. 'left out (Writing a classed "
                f"triple, rule 21)'; {IN_OTHER_WORDS!r}; or empty (not reviewed yet)")
    section, rule = m.group("section").strip(), int(m.group("rule"))
    if (section, rule) not in rules:
        return (f"the decision {text!r} names rule {rule} of a section {section!r}, which annotations/guidelines.md "
                f"doesn't have: write the section's heading as the guidelines write it, and the rule's number")
    return None


def read_candidates(path: Path = CANDIDATES_PATH, rules: dict | None = None) -> list:
    """Every row of the file, in its order, each with "_line" (a missing file, or one with its header only, reads as
    empty). A file lacking a column, a row without an id or a model, counts that aren't whole numbers with
    1 <= proposed_in_repeats <= repeats, a decision that isn't allowed (decision_problem; rules: guideline_rules(),
    read from annotations/guidelines.md when not given), two rows of one model for one classed triple of a record,
    or two different decisions on one classed triple of a record raise ValueError naming the line(s)."""
    path = Path(path)
    if not path.is_file():
        return []
    columns, raw = read_csv_table(path)
    missing = [c for c in CANDIDATE_COLUMNS if c not in columns]
    if missing:
        raise ValueError(f"{path} lacks the column(s) {', '.join(missing)}; its header must name "
                         f"{', '.join(CANDIDATE_COLUMNS)}")
    if rules is None and any((r.get("decision") or "").strip() for r in raw):
        from common.expert_questions import guideline_rules       # only when there is a decision to check
        rules = guideline_rules()
    rows, seen, decided = [], {}, {}
    for r in raw:
        row = {c: (r.get(c) or "").strip() for c in CANDIDATE_COLUMNS}
        line = r.get("_line")
        if not any(row.values()):
            continue
        at = f"{path}, line {line}"
        for c in ("id", "model"):
            if not row[c]:
                raise ValueError(f"{at}: the column {c} is empty; each row names the record and the model that "
                                 f"proposed its classed triple")
        try:
            k, n = int(row["proposed_in_repeats"]), int(row["repeats"])
        except ValueError:
            raise ValueError(f"{at}: proposed_in_repeats and repeats must be whole numbers, but are "
                             f"{row['proposed_in_repeats']!r} and {row['repeats']!r}") from None
        if not 1 <= k <= n:
            raise ValueError(f"{at}: the counts must satisfy 1 <= proposed_in_repeats <= repeats, but are "
                             f"proposed_in_repeats {k}, repeats {n}")
        problem = decision_problem(row["decision"], rules or {})
        if problem:
            raise ValueError(f"{at}: {problem}")
        key = candidate_key(row)
        if (key, row["model"]) in seen:
            raise ValueError(f"{path}, lines {seen[key, row['model']]} and {line}: two rows of the model "
                             f"{row['model']} for one classed triple of record {row['id']}; keep one")
        seen[key, row["model"]] = line
        if row["decision"]:
            if key in decided and decided[key][1] != row["decision"]:
                raise ValueError(f"{path}, lines {decided[key][0]} and {line}: two decisions on one classed triple of "
                                 f"record {row['id']} ({decided[key][1]!r} and {row['decision']!r}); a decision is "
                                 f"about the fact, whichever model proposed it: keep one")
            decided.setdefault(key, (line, row["decision"]))
        rows.append({**row, "_line": line})
    return rows


def write_candidates(path: Path, rows: list) -> None:
    """Write the rows with CANDIDATE_COLUMNS."""
    write_csv(path, CANDIDATE_COLUMNS, rows)
