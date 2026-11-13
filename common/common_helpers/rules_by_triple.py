"""
common/common_helpers/rules_by_triple.py -- which rules of the annotation guidelines each ground truth triple uses:
the column `rules` of the ground truth files, and the generated doc annotations/rules_by_triple.md.

    from common.rules_by_triple import parse_rules, rules_problem, doc_text, write_doc, merge_drafts
    parse_rules("1, 19")        # [1, 19]; ValueError saying what the format is, on anything else
    rules_problem(row)          # why a row's `rules` value is wrong, or None
    write_doc()                 # annotations/rules_by_triple.md from the ground truth files, the guidelines and
                                # left_out.md (written only when its content changes); doc_text() is the text
    merge_drafts(folder)        # the drafted values of a folder of CSV files into the ground truth files

THE COLUMN. `rules` holds the numbers of the rules of annotations/guidelines.md (1 to the highest numbered rule the
file has, RULE_COUNT) that decided the ground truth triple's wording, ascending, separated by ", " (FORMAT), or
nothing when none is recorded yet. The rules' words have one home, annotations/guidelines.md: nothing copies them by
hand. Rules ALWAYS (2, 11, 13, 14 and 17) apply to every ground truth triple; the doc quotes them once at its top.
A describes triple (common/common_helpers/triples_io.is_describes) follows the guidelines' section DESCRIBES_SECTION
instead of rules, and the row of a record that states no facts is no triple: on both, the value must be empty.

THE DOC. annotations/rules_by_triple.md (DOC_PATH) is generated, never edited by hand: by COMMAND, and by the
annotation tool each time it saves a batch. One section per record, in the order and under the heading of
annotations/left_out.md (the records with no section there come after, in the ground truth files' order, under a
heading of the same shape); under it, each ground truth triple with its rule numbers, then each rule those triples
use quoted once in full, with the heading "Rule N (part of the guidelines)". Quoting a rule under every triple would
make the file far too long (rule 20 alone is about 850 words), so each rule is quoted once per record. A test
(tests/test_rules_by_triple.py) fails when the doc differs from what the files give now, naming COMMAND.

THE DRAFTS. merge_drafts reads every *.csv of a folder with the columns DRAFT_COLUMNS (file, row, id, subject,
predicate, object, rules): file is the ground truth file's name (batch_003.csv), row the data row's number in it,
counted from 1 after the header, and id, subject, predicate and object are the batch row's, as a check that the
rules go on the row meant. Nothing is written unless every draft row matches its batch row at that position (id,
subject, predicate and object compared as written, spaces evened out), its value parses, the row is neither a
describes triple nor a record that states no facts, and no (file, row) is drafted twice; the problems are all
listed. Each ground truth file is then written through the annotation tool's own writer (the same rows and values,
only the `rules` cells changed), and the doc is written again.
"""
from __future__ import annotations

import collections
import csv
import io
import re
from pathlib import Path

from common.expert_questions import GUIDELINES_PATH, guideline_rule_lines
from common.files import read_csv, read_csv_table, read_text, write_text
from common.ground_truth import FILE_COLUMNS, FINISHED, GROUND_TRUTH_DIR, PATTERN, RULES, marks_state
from common.left_out import LEFT_OUT_PATH, read_left_out
from common.step import ANNOTATIONS_DIR
from common.triples_io import is_describes

DOC_PATH = ANNOTATIONS_DIR / "rules_by_triple.md"
COMMAND = "py helpers/rules_by_triple.py"
#: The rules that apply to every ground truth triple: quoted once at the top of the doc, never repeated per record.
ALWAYS = (2, 11, 13, 14, 17)
#: The guidelines' section a describes triple follows instead of rules.
DESCRIBES_SECTION = "The describes triple"
#: How the numbers are written in the column: ascending, separated by ", ".
FORMAT = 'the numbers of the rules, ascending, separated by a comma and a space ("1, 19"), or nothing'
#: Who drafted the rule numbers, and when: said at the top of the doc until a person has reviewed them in the tool.
DRAFTED_BY = "Claude Fable 5.1, 2026-11-11"
#: The columns of a file of drafted values (merge_drafts).
DRAFT_COLUMNS = ["file", "row", "id", "subject", "predicate", "object", "rules"]
_NUMBERS = re.compile(r"^\d+(, \d+)*$")


# --------------------------------------------------------------------------
# the column
# --------------------------------------------------------------------------

def rule_count(path: Path = GUIDELINES_PATH) -> int:
    """The highest rule number annotations/guidelines.md has (24 on 2026-11-11)."""
    return max(n for _, n in guideline_rule_lines(path))


def parse_rules(value: str, highest: int | None = None) -> list:
    """The rule numbers a `rules` value holds, in order ([] for empty); ValueError saying what the format is when it
    isn't FORMAT: not numbers, not ascending, a number twice, or one above `highest` (rule_count() when not given)."""
    text = (value or "").strip()
    if not text:
        return []
    if not _NUMBERS.match(text):
        raise ValueError(f'"{text}" isn\'t {FORMAT}')
    numbers = [int(n) for n in text.split(", ")]
    highest = rule_count() if highest is None else highest
    for n in numbers:
        if not 1 <= n <= highest:
            raise ValueError(f'"{text}" names rule {n}, and annotations/guidelines.md has rules 1 to {highest}: write '
                             f"only those")
    if numbers != sorted(set(numbers)):
        raise ValueError(f'"{text}" isn\'t ascending with each rule once: write {FORMAT}')
    return numbers


def format_rules(numbers) -> str:
    """The column's value for these rule numbers: each once, ascending, FORMAT."""
    return ", ".join(str(n) for n in sorted(set(int(n) for n in numbers)))


def rules_problem(row: dict, highest: int | None = None) -> str | None:
    """Why a ground truth row's `rules` value is wrong, with what to do, or None: a value that isn't FORMAT, a
    rule number the guidelines don't have, or any value on a describes triple or on the row of a record that states
    no facts (common.ground_truth: an id with an empty subject, predicate and object)."""
    value = str(row.get(RULES) or "").strip()
    try:
        numbers = parse_rules(value, highest)
    except ValueError as e:
        return f"The rules value {e}."
    if not numbers:
        return None
    if is_describes(row):
        return (f'The describes triple has rules "{value}", but it follows the guidelines\' section "{DESCRIBES_SECTION}" '
                f"instead of rules: clear its rules value.")
    if not (str(row.get("subject") or "").strip() or str(row.get("predicate") or "").strip()
            or str(row.get("object") or "").strip()):
        return (f'The row of a record that states no facts has rules "{value}", but it is no ground truth triple: clear '
                f"its rules value.")
    return None


def file_problems(folder: Path = GROUND_TRUTH_DIR, highest: int | None = None) -> list:
    """Every problem of the column in the ground truth files, each naming the file and line: a file without the
    column, and each row whose value rules_problem refuses. Empty when all is well."""
    highest = rule_count() if highest is None else highest
    problems = []
    for path in sorted(Path(folder).glob(PATTERN)):
        columns, rows = read_csv_table(path)
        if RULES not in columns:
            problems.append(f"annotations/ground_truth/{path.name} lacks the column {RULES}: add it, empty, after "
                            f"{columns[-1]} (the annotation tool adds it when it saves the file).")
            continue
        for row in rows:
            if not (row.get("id") or "").strip():
                continue
            why = rules_problem(row, highest)
            if why:
                problems.append(f"annotations/ground_truth/{path.name}, line {row['_line']}: {why}")
    return problems


# --------------------------------------------------------------------------
# the guidelines' words
# --------------------------------------------------------------------------

def _title(first_line: str) -> str:
    m = re.search(r"\*\*(.+?)\*\*", first_line)
    return m.group(1).strip() if m else ""


def _markdown(lines: list) -> str:
    """A rule as Markdown without its number: its line's words, then its continuation lines, each a list item."""
    first = re.match(r"^\d+\. (.*)", lines[0]).group(1)
    return "\n".join([first] + [re.sub(r"^\s+", "", l) for l in lines[1:]])


def rule_texts(path: Path = GUIDELINES_PATH) -> dict:
    """{rule number: {"section", "title", "markdown"}}: each numbered rule of annotations/guidelines.md, its section's
    heading, its bold title, and its words as Markdown (common.expert_questions.guideline_rule_lines). Links stay
    relative to annotations/, where the doc and the guidelines both are."""
    return {n: {"section": section, "title": _title(lines[0]), "markdown": _markdown(lines)}
            for (section, n), lines in guideline_rule_lines(path).items()}


def guideline_section(heading: str, path: Path = GUIDELINES_PATH) -> str:
    """The Markdown under a "## heading" of annotations/guidelines.md, to the next heading; "" when there is none."""
    text = read_text(path)
    m = re.search(rf"^## {re.escape(heading)}\s*$", text, re.M)
    if not m:
        return ""
    rest = text[m.end():]
    nxt = re.search(r"^#{1,6} ", rest, re.M)
    return (rest[:nxt.start()] if nxt else rest).strip()


# --------------------------------------------------------------------------
# the doc
# --------------------------------------------------------------------------

def _read_rows(path: Path) -> list:
    """The file's rows with an id, as the annotation tool reads them (every column of FILE_COLUMNS, stripped)."""
    return [{c: (row.get(c) or "").strip() for c in FILE_COLUMNS} for row in read_csv(path)
            if (row.get("id") or "").strip()]


def _records(folder: Path) -> list:
    """[(file name, id, [rows])] of every ground truth file, in the files' and the rows' order."""
    out = []
    for path in sorted(Path(folder).glob(PATTERN)):
        grouped = collections.OrderedDict()
        for row in _read_rows(path):
            grouped.setdefault(row["id"], []).append(row)
        out.extend((path.name, rid, rows) for rid, rows in grouped.items())
    return out


def _triple_line(row: dict, highest: int) -> str:
    """One ground truth triple as text: "subject" (SubjectClass) PREDICATE "object" (ObjectClass), with its rules."""
    classed = (f'"{row["subject"]}" ({row["subject_class"] or "no entity class"}) {row["predicate"]} '
               f'"{row["object"]}" ({row["object_class"] or "no entity class"})')
    if is_describes(row):
        return f"- Describes triple: {classed}: the section *{DESCRIBES_SECTION}*, quoted above."
    try:
        numbers = parse_rules(row[RULES], highest)
    except ValueError:
        return f'- {classed}: rules "{row[RULES]}" (not a valid value: the test names the line to fix).'
    if not numbers:
        return f"- {classed}: no rules recorded yet."
    return f"- {classed}: rule{'s' if len(numbers) > 1 else ''} {', '.join(str(n) for n in numbers)}."


def _rule_block(n: int, texts: dict) -> list:
    return [f"### Rule {n} (part of the guidelines)", "", texts[n]["markdown"], ""]


def doc_text(folder: Path = GROUND_TRUTH_DIR, guidelines_path: Path = GUIDELINES_PATH,
             left_out_path: Path = LEFT_OUT_PATH) -> str:
    """The doc's text, from the ground truth files, the guidelines and left_out.md as they are now (the module's
    docstring says its shape)."""
    texts = rule_texts(guidelines_path)
    highest = max(texts)
    try:
        sections = read_left_out(left_out_path) if Path(left_out_path).exists() else []
        left_out_note = ""
    except ValueError as e:
        sections, left_out_note = [], f" (annotations/left_out.md couldn't be read: {e}; every record is in the files' order)"
    by_id = {s["id"]: s for s in sections}
    records = _records(folder)
    rows_of = {rid: rows for _, rid, rows in records}
    ordered = [(s["id"], f'## "{s["title"]}" (pool position {s["position"]}, id {s["id"]})') for s in sections
               if s["id"] in rows_of]
    for _, rid, rows in records:
        if rid not in by_id:
            describes = next((r for r in rows if is_describes(r)), None)
            title = describes["object"] if describes else "(no title)"
            ordered.append((rid, f'## "{title}" (id {rid}; no section in left_out.md yet)'))
    always = ", ".join(str(n) for n in ALWAYS[:-1]) + f" and {ALWAYS[-1]}"
    out = [
        "# Rules by ground truth triple", "",
        f"Generated by `{COMMAND}`, and by the annotation tool each time it saves a batch, from the column `rules` of "
        f"`annotations/ground_truth/batch_*.csv`, the rules' wording in `annotations/guidelines.md`, and the records' "
        f"order and headings in `annotations/left_out.md`{left_out_note}. Don't edit it by hand: the next generation "
        f"would undo the edit. The rule numbers were drafted by a model ({DRAFTED_BY}) and are preliminary, still to "
        f"be reviewed by a person, until reviewed in the annotation tool (*Rules*, under each ground truth triple; "
        f"`annotations/README.md`, *Annotating ground truth: the annotation tool*). Terms: `docs/terminology.md`.", "",
        "Each section is one record, in the order and under the heading of `annotations/left_out.md`; the records with "
        "no section there come after, in the ground truth files' order. Under the record: each ground truth triple as "
        "subject instance (its entity class), predicate, object instance (its entity class), then the numbers of the "
        "rules it uses; then each of those rules quoted once in full, from `annotations/guidelines.md` as it is now. "
        "When a rule's wording changes, the ground truth triples that cite it are the ones to check again.", "",
        "## Rules every ground truth triple follows", "",
        f"Rules {always} of the guidelines apply to every ground truth triple, so they are quoted here once and not "
        f"again under the records.", "",
    ]
    for n in ALWAYS:
        if n in texts:
            out += _rule_block(n, texts)
    out += [f"## {DESCRIBES_SECTION}", "",
            f'A record\'s describes triple (predicate DESCRIBES, source text "(record structure)") follows the '
            f"guidelines' section *{DESCRIBES_SECTION}*, quoted here, instead of rules.", "",
            guideline_section(DESCRIBES_SECTION, guidelines_path), ""]
    for rid, heading in ordered:
        rows = rows_of[rid]
        out += [heading, ""]
        if marks_state(r["all_facts_extracted"] for r in rows) != FINISHED:
            out += ["Not finished: its ground truth triples may still change.", ""]
        triples = [r for r in rows if r["subject"] or r["predicate"] or r["object"]]
        if not triples:
            out += ["This record states no facts.", ""]
            continue
        out += [_triple_line(r, highest) for r in triples] + [""]
        used = set()
        for r in triples:
            if not is_describes(r):
                try:
                    used |= set(parse_rules(r[RULES], highest))
                except ValueError:
                    pass
        for n in sorted(used - set(ALWAYS)):
            if n in texts:
                out += _rule_block(n, texts)
    return "\n".join(out).rstrip("\n") + "\n"


def write_doc(path: Path = DOC_PATH, **kw) -> bool:
    """Write the doc (doc_text(**kw)) to `path` only when its content changes; True when it was written."""
    text = doc_text(**kw)
    if Path(path).exists() and read_text(path) == text:
        return False
    write_text(path, text)
    return True


# --------------------------------------------------------------------------
# the drafted values
# --------------------------------------------------------------------------

def _same(a: str, b: str) -> bool:
    return " ".join((a or "").split()) == " ".join((b or "").split())


def _csv_text(rows: list) -> str:
    """A ground truth file's text as the annotation tool writes it (the same writer: common.files.write_csv)."""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, FILE_COLUMNS, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()


def merge_drafts(folder: Path, ground_truth_dir: Path = GROUND_TRUTH_DIR, doc_path: Path = DOC_PATH,
                 highest: int | None = None, **doc_kw) -> dict:
    """Put the drafted values of every *.csv of `folder` (DRAFT_COLUMNS; the module's docstring) into the `rules`
    column of the ground truth files, then write the doc again. Returns {"problems": [...], "written": {file name:
    rows changed}}; when there is any problem, nothing is written and every problem is listed, naming the draft
    file and line."""
    highest = rule_count() if highest is None else highest
    drafts = sorted(Path(folder).glob("*.csv"))
    problems, wanted, seen = [], collections.defaultdict(dict), {}
    if not drafts:
        return {"problems": [f"{folder} holds no .csv file of drafted values (columns: {', '.join(DRAFT_COLUMNS)})"],
                "written": {}}
    files = {p.name: _read_rows(p) for p in sorted(Path(ground_truth_dir).glob(PATTERN))}
    for draft in drafts:
        columns, rows = read_csv_table(draft)
        missing = [c for c in DRAFT_COLUMNS if c not in columns]
        if missing:
            problems.append(f"{draft.name} lacks the column(s) {', '.join(missing)}: a file of drafted values has "
                            f"the columns {', '.join(DRAFT_COLUMNS)}")
            continue
        for d in rows:
            at = f"{draft.name}, line {d['_line']}"
            name = (d.get("file") or "").strip()
            if name not in files:
                problems.append(f"{at}: no ground truth file {name!r} (the files: {', '.join(files) or 'none'})")
                continue
            try:
                position = int((d.get("row") or "").strip())
                if not 1 <= position <= len(files[name]):
                    raise ValueError
            except ValueError:
                problems.append(f"{at}: row {d.get('row')!r} isn't a data row of {name} (1 to {len(files[name])}, "
                                f"counted after the header)")
                continue
            target = files[name][position - 1]
            differs = [c for c in ("id", "subject", "predicate", "object") if not _same(d.get(c), target[c])]
            if differs:
                problems.append(f"{at}: the {', '.join(differs)} given ({'; '.join(repr(d.get(c) or '') for c in differs)}) "
                                f"differ from row {position} of {name} ({'; '.join(repr(target[c]) for c in differs)}): "
                                f"the rules would go on the wrong row. Nothing is written.")
                continue
            why = rules_problem({**target, RULES: d.get(RULES) or ""}, highest)
            if why:
                problems.append(f"{at}: {why}")
                continue
            if (name, position) in seen:
                problems.append(f"{at}: row {position} of {name} is drafted twice (also at {seen[(name, position)]})")
                continue
            seen[(name, position)] = at
            wanted[name][position] = format_rules(parse_rules(d.get(RULES) or "", highest))
    if problems:
        return {"problems": problems, "written": {}}
    written = {}
    for name, by_position in wanted.items():
        rows = files[name]
        changed = 0
        for position, value in by_position.items():
            if rows[position - 1][RULES] != value:
                rows[position - 1][RULES] = value
                changed += 1
        if changed:
            write_text(Path(ground_truth_dir) / name, _csv_text(rows))
            written[name] = changed
    write_doc(doc_path, folder=ground_truth_dir, **doc_kw)
    return {"problems": [], "written": written}
