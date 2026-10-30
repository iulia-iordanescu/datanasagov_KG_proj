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
"""
from __future__ import annotations

import re
from pathlib import Path

from common.step import ANNOTATIONS_DIR

LEFT_OUT_PATH = ANNOTATIONS_DIR / "left_out.md"
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
    lines = path.read_text(encoding="utf-8").split("\n")

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
