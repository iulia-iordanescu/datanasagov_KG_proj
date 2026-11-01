"""
common/common_helpers/left_out.py -- annotations/left_out.md, the one home of the statements the ground truth
leaves out on purpose, read the same way by every reader (the annotation tool's record view and its Left out view).

    from common.left_out import read_left_out, LEFT_OUT_PATH, rule_ref
    sections = read_left_out()        # [section]; ValueError, naming the file and line, on a section not in the format

The file's format (annotations/README.md, row left_out.md; the file's own introduction says the same). Everything
before the first "## " heading is the introduction and isn't read. Each section is one record:

    ## "<title>" (pool position <n>, id <record id>)
    <prose: must say "<N> item(s)" and how many may matter ("<K> that may matter", "all <K> that may matter" or
    "none that may matter"); N and K are checked against the items>
    - **Left out:** <the exact words, with where they are in the text>
      - **Rule:** <the rule that excluded them, quoted>        (required)
      - **May matter because:** <why>                          (optional, at most once)
      - **Question:** <Q<n> ...>                               (optional, at most once)
      - <any other sentence>                                   (a note, any number)

rule_ref(item) is the rule an item names, "What counts as a fact, rule 4", or NO_RULE when the Rule line quotes none.

A section is a dict: title, position (int), id, line, intro (the prose), items. An item: line, words, rule,
may_matter (the text, or ""), question (the text, or ""), questions (the ids in it, "Q6", in order), notes.

THE FACTS THAT WAIT ON AN EXPERT: annotations/pending_triples.csv, read by read_pending (step 070 reads it, so that
an extracted triple matching such a fact isn't counted against precision: 070_evaluate/metrics/precision.md). An item
whose Rule line quotes rule 2's "or it waits on an expert's answer" (WAITS) states a fact that is left out only until
an expert answers; its would-be ground truth triple, when one is clear, is a row of that file:

    id,subject,subject_class,predicate,object,object_class,source_text,left_out,question

id is the record's id; the next six columns are as in a ground truth file; left_out is the item's words, exactly as
on its "- **Left out:**" line, in that record's section; question is the question that waits ("Q9 (d)"). An item
that waits but has no clear would-be triple says so in a note starting NO_TRIPLE ("No clear would-be triple: <why>").
read_pending checks, naming the file and line: the header; each row's record has a section here, and its left_out is
the words of an item of that section that waits; no row twice; every item that waits has a row or that note.
"""
from __future__ import annotations

import re
from pathlib import Path

from common.files import read_text
from common.step import ANNOTATIONS_DIR

LEFT_OUT_PATH = ANNOTATIONS_DIR / "left_out.md"
PENDING_PATH = ANNOTATIONS_DIR / "pending_triples.csv"
PENDING_COLUMNS = ["id", "subject", "subject_class", "predicate", "object", "object_class", "source_text", "left_out",
                   "question"]
#: The words of rule 2 an item's Rule line quotes when its fact waits on an expert's answer.
WAITS = "or it waits on an expert's answer"
#: How a note of an item that waits starts when the item has no clear would-be ground truth triple.
NO_TRIPLE = "No clear would-be triple:"
_HEADING = re.compile(r'^## "(?P<title>.+)" \(pool position (?P<pos>\d+), id (?P<id>[0-9A-Za-z-]+)\)\s*$')
_ITEM = re.compile(r"^- \*\*Left out:\*\* ?(?P<words>.*\S.*)$")
_SUB = re.compile(r"^  - (?P<text>.*\S.*)$")
_LABELLED = re.compile(r"^\*\*(?P<label>Rule|May matter because|Question):\*\* ?(?P<text>.*\S.*)$")
NO_RULE = "no rule to quote"
_RULE_REF = re.compile(r'^([^:"]+?, rule \d+)')
_COUNT = re.compile(r"\b(\d+) items?\b")
_MATTER = re.compile(r"\b(?:(?P<all>all) (?P<n_all>\d+)|(?P<none>none)|(?P<n>\d+)) that may matter\b")


def read_left_out(path: Path = LEFT_OUT_PATH) -> list:
    """The file's sections (see the module); ValueError naming the line of the first thing not in the format."""
    name = f"annotations/{path.name}" if path == LEFT_OUT_PATH else str(path)
    lines = read_text(path).split("\n")

    def bad(n: int, what: str) -> ValueError:
        return ValueError(f"{name}, line {n}: {what} (the format: annotations/README.md, row left_out.md)")

    sections, section, item = [], None, None
    for n, line in enumerate(lines, 1):
        line = line.rstrip("\r")
        if line.startswith("## "):
            m = _HEADING.match(line)
            if not m:
                raise bad(n, 'a heading must be: ## "<title>" (pool position <n>, id <record id>)')
            if any(s["id"] == m["id"] for s in sections):
                raise bad(n, f"the record {m['id']} has two sections")
            section = {"title": m["title"], "position": int(m["pos"]), "id": m["id"], "line": n, "intro": "", "items": []}
            sections.append(section)
            item = None
            continue
        if section is None or not line.strip():
            continue
        if line.startswith("- "):
            m = _ITEM.match(line)
            if not m:
                raise bad(n, 'an item must start with "- **Left out:** <the exact words>"')
            item = {"line": n, "words": m["words"], "rule": "", "may_matter": "", "question": "", "questions": [], "notes": []}
            section["items"].append(item)
        elif line.startswith("  - "):
            if item is None:
                raise bad(n, "an indented line must belong to an item (after a line starting with - **Left out:**)")
            text = _SUB.match(line)["text"]
            m = _LABELLED.match(text)
            if not m:
                item["notes"].append(text)
                continue
            key = {"Rule": "rule", "May matter because": "may_matter", "Question": "question"}[m["label"]]
            if item[key]:
                raise bad(n, f'an item has two "{m["label"]}:" lines')
            item[key] = m["text"]
            if key == "question":
                item["questions"] = re.findall(r"\bQ\d+\b", m["text"])
        elif line.startswith(" "):
            raise bad(n, 'an indented line must start with "  - " (two spaces, a dash)')
        else:
            if item is not None:
                raise bad(n, "prose after the items of a section (put it before the first item)")
            section["intro"] = (section["intro"] + " " + line).strip()
    for s in sections:
        _check_section(s, bad)
    return sections


def rule_ref(item: dict) -> str:
    """The rule an item's Rule line names ("Writing a classed triple, rule 23"), or NO_RULE."""
    m = _RULE_REF.match(item["rule"])
    return m[1] if m else NO_RULE


def _check_section(s: dict, bad) -> None:
    items = s["items"]
    for it in items:
        if not it["rule"]:
            raise bad(it["line"], 'an item needs a "  - **Rule:** …" line (write "none to quote. …" if no rule applies)')
    count = _COUNT.search(s["intro"])
    if not count:
        raise bad(s["line"], 'the section must say how many items it has ("<N> items" or "1 item") before its first item')
    if int(count[1]) != len(items):
        raise bad(s["line"], f"the section says {count[1]} item(s) but lists {len(items)}")
    matter = _MATTER.search(s["intro"])
    if not matter:
        raise bad(s["line"], 'the section must say how many items may matter ("<K> that may matter", "all <K> that may matter" or "none that may matter")')
    said = 0 if matter["none"] else int(matter["n_all"] or matter["n"])
    if said != sum(1 for it in items if it["may_matter"]):
        raise bad(s["line"], f"the section says {said} that may matter but {sum(1 for it in items if it['may_matter'])} items have a \"May matter because:\" line")


def waits(item: dict) -> bool:
    """Whether the item's fact is left out only until an expert answers (its Rule line quotes WAITS)."""
    return WAITS in item["rule"]


def read_pending(path: Path = PENDING_PATH, left_out_path: Path = LEFT_OUT_PATH) -> list:
    """The would-be ground truth triples of the facts that wait on an expert (see the module): [row dict, with
    "line"], in the file's order; ValueError naming the file and line of the first problem. Every row is checked
    against left_out.md (read_left_out), and every item there that waits must have a row or a NO_TRIPLE note."""
    import csv
    import io
    import io
    name = f"annotations/{path.name}" if path == PENDING_PATH else str(path)
    lo_name = f"annotations/{left_out_path.name}" if left_out_path == LEFT_OUT_PATH else str(left_out_path)
    if True:                                  # (the block's shape kept: the text through common.files.read_text)
        reader = csv.reader(io.StringIO(read_text(path), newline=""))
        header = next(reader, None)
        if header != PENDING_COLUMNS:
            raise ValueError(f"{name}, line 1: the header must be {','.join(PENDING_COLUMNS)}, not "
                             f"{','.join(header or [])} (the format: common/common_helpers/left_out.py)")
        raw = [(n, r) for n, r in enumerate(reader, 2) if any(c.strip() for c in r)]
    sections = {s["id"]: s for s in read_left_out(left_out_path)}
    rows, seen = [], {}
    for n, r in raw:
        if len(r) != len(PENDING_COLUMNS):
            raise ValueError(f"{name}, line {n}: {len(r)} columns, not {len(PENDING_COLUMNS)} "
                             f"({','.join(PENDING_COLUMNS)}); a value with a comma needs double quotes")
        row = dict(zip(PENDING_COLUMNS, (c.strip() for c in r)))
        empty = [c for c in PENDING_COLUMNS if not row[c]]
        if empty:
            raise ValueError(f"{name}, line {n}: no value in {', '.join(empty)}; every column needs one")
        section = sections.get(row["id"])
        if section is None:
            raise ValueError(f"{name}, line {n}: the record {row['id']} has no section in {lo_name}; write its "
                             f"left-out item there first, or fix the id")
        item = next((it for it in section["items"] if it["words"] == row["left_out"]), None)
        if item is None:
            raise ValueError(f"{name}, line {n}: no item of the section of {row['id']} in {lo_name} has the words "
                             f"{row['left_out']!r} on its \"- **Left out:**\" line; copy them exactly from there")
        if not waits(item):
            raise ValueError(f"{name}, line {n}: the item {row['left_out']!r} ({lo_name}, line {item['line']}) "
                             f"doesn't wait on an expert (its Rule line doesn't quote {WAITS!r}); delete the row, or "
                             f"fix the item's rule")
        key = tuple(row[c] for c in PENDING_COLUMNS)
        if key in seen:
            raise ValueError(f"{name}, line {n}: the same row as line {seen[key]}; delete one")
        seen[key] = n
        rows.append({**row, "line": n})
    having = {(r["id"], r["left_out"]) for r in rows}
    for s in sections.values():
        for it in s["items"]:
            if waits(it) and (s["id"], it["words"]) not in having and not any(x.startswith(NO_TRIPLE) for x in it["notes"]):
                raise ValueError(f"{lo_name}, line {it['line']}: the item {it['words']!r} waits on an expert but has "
                                 f"no row in {name} and no note \"{NO_TRIPLE} <why>\"; add one of the two")
    return rows
