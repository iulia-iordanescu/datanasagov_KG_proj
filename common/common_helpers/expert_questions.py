"""
common/common_helpers/expert_questions.py -- the questions I ask subject-matter experts, read from their one home,
annotations/questions_for_experts.md (a person-made file), for the review page's Questions view
(helpers/review_page.py) and for the readers of the comments sent back (common/common_helpers/review_comments.py).

    from common.expert_questions import read_questions, check_questions
    questions = read_questions()          # [question]; ValueError, naming the line, on a question not in the format
    problems = check_questions(questions) # ["…"]: each quote that isn't what its source says now (empty: all agree)

The file's format, what each status, priority and question kind means, what the expert reads, and every check
check_questions makes: helpers/review_page.md, *The questions file* (their one home). Here, each value is defined
once (STATUSES, PRIORITIES, QUESTION_KINDS, AFFECTS, the subsections) and used by the review page, the annotation
tool and the tests.
"""
from __future__ import annotations

import hashlib
import html
import re
from pathlib import Path

from common.component_class_mapping import MAPPING_PATH, read_mapping
from common.ground_truth import GROUND_TRUTH_DIR, TUNING, read_ground_truth, read_pool
from common.records_io import load_records
from common.schema_io import read_ground_truth_schema
from common.step import ANNOTATIONS_DIR, RESULTS_DIR

QUESTIONS_PATH = ANNOTATIONS_DIR / "questions_for_experts.md"
GUIDELINES_PATH = ANNOTATIONS_DIR / "guidelines.md"
SCHEMA_PATH = ANNOTATIONS_DIR / "ground_truth_schema.txt"
RECORDS_PATH = RESULTS_DIR / "020_clean" / "records.jsonl"
SPLITS_PATH = RESULTS_DIR / "030_split" / "splits.json"
#: A question's status (what each means: helpers/review_page.md, *The questions file*).
OPEN, ANSWERED, WITHDRAWN = "open", "answered", "withdrawn"
STATUSES = (OPEN, ANSWERED, WITHDRAWN)
#: How much a question's answer matters now, most first: the order the page shows them in.
PRIORITIES = ("high", "medium", "low")
#: What a question is about: the records and their classed triples; an entity class or predicate of the ground truth
#: schema; a rule of the annotation guidelines; rows of the translation table; a method of the pipeline; or general
#: (a question about an idea, with no record or classed triple of its own).
QUESTION_KINDS = ("records and triples", "schema entry", "rule", "translation table rows", "pipeline method", "general")
#: Each question kind in words, as the review page says what a question is about.
QUESTION_KIND_WORDS = {"records and triples": "records and their classed triples",
                       "schema entry": "an entity class or predicate of the ground truth schema",
                       "rule": "a rule of the annotation guidelines",
                       "translation table rows": "rows of the translation table",
                       "pipeline method": "a method of the pipeline",
                       "general": "an idea, in general"}
assert tuple(QUESTION_KIND_WORDS) == QUESTION_KINDS
#: The fields of "### Affects": what an answer may change.
AFFECTS = ("record at pool position", "classed triple of the record at pool position", "translation table row",
           "ground truth schema entry", "rule", "pipeline method")
#: The subsections of a question, in the order they must come: (heading, how many: "1" or "?"). The first ones
#: (EXPERT_SECTIONS) are what the expert needs to answer; the rest are my bookkeeping, which the page folds away.
SECTIONS = [("The question", "1"), ("Context", "?"), ("Example record", "?"), ("Ground truth schema", "?"),
            ("Translation table", "?"), ("Annotation guidelines", "?"), ("Options", "?"), ("My current reading", "1"),
            ("The answer", "?"), ("My notes", "?"), ("Consequences", "?"), ("Affects", "1"), ("Pipeline method", "?")]
EXPERT_SECTIONS = tuple(name for name, _ in SECTIONS[:SECTIONS.index(("My notes", "?"))])
#: What the expert reads never names a record this way: by its pool position, or by its id.
NOT_FOR_THE_EXPERT = re.compile(r"pool\s+positions?|\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.I)
#: A record named by its title in what the expert reads: 'the record "<title>"' (or 'records "<a>" and "<b>"').
NAMED_RECORDS = re.compile(r'\brecords?\s+((?:"[^"\n]+"(?:,\s+(?:and\s+|or\s+)?|\s+(?:and|or)\s+)?)+)')
RECORD_FIELDS = ("record id", "pool position", "title", "notes", "in the ground truth", "source text", "classed triple")
TRIPLE = re.compile(r'^"(.+)" \((\w+)\) ([A-Z][A-Z0-9_]*) "(.+)" \((\w+)\)$')
FORMAT = "the format: helpers/review_page.md, *The questions file*"


def _rel(path: Path) -> str:
    try:
        return Path(path).resolve().relative_to(ANNOTATIONS_DIR.parent.resolve()).as_posix()
    except ValueError:
        return Path(path).name


def squeeze(text: str) -> str:
    """The words, one space between each: what two quotes are compared by (an email client or an editor may wrap
    a line, and a record's text may hold runs of spaces)."""
    return " ".join((text or "").split())


# ------------------------------ prose ----------------------------------------

def _inline(md: str, terms: list) -> str:
    """One paragraph's text as HTML: `code`, **bold**, *italic*; a link to docs/terminology.md becomes a link to
    the page's Terms view (its words added to `terms`); any other link, its words and its address as text."""
    out, pos = [], 0
    for m in re.finditer(r"`([^`]*)`|\[([^\[\]]+)\]\(([^)\s]+)\)", md):
        out.append(_marks(md[pos:m.start()]))
        if m.group(1) is not None:
            out.append(f"<code>{html.escape(m.group(1))}</code>")
        elif "terminology.md" in m.group(3):
            terms.append(m.group(2))
            out.append(f'<a class="term" data-term="{html.escape(m.group(2).lower())}" href="#terms">'
                       f"{_marks(m.group(2))}</a>")
        else:
            words = _marks(m.group(2))
            out.append(words if not m.group(3).startswith("http") or m.group(3) == m.group(2)
                       else f"{words} ({html.escape(m.group(3))})")
        pos = m.end()
    out.append(_marks(md[pos:]))
    return "".join(out)


def _marks(text: str) -> str:
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    return re.sub(r"(?<![*\w])\*([^*]+)\*(?![*\w])", r"<em>\1</em>", text)


def _prose(lines: list, terms: list) -> list:
    """[{"p": html} or {"ul": [html]}]: paragraphs (split at blank lines) and "- " lists."""
    blocks, para = [], []

    def close():
        if not para:
            return
        if para[0].startswith("|"):
            rows = [[c.strip() for c in l.strip().strip("|").split("|")] for l in para]
            if len(rows) < 3 or not all(re.fullmatch(r":?-+:?", c) for c in rows[1]) or not all(len(r) == len(rows[0]) for r in rows):
                raise ValueError("a table is a header line, a line of dashes (|---|---|), then its rows, each with as "
                                 "many cells as the header")
            blocks.append({"table": [[_inline(c, terms) for c in r] for r in [rows[0]] + rows[2:]]})
        elif para[0].startswith("- "):
            items = []
            for line in para:
                if line.startswith("- "):
                    items.append(line[2:].strip())
                else:
                    items[-1] += " " + line.strip()
            blocks.append({"ul": [_inline(i, terms) for i in items]})
        else:
            blocks.append({"p": _inline(" ".join(l.strip() for l in para), terms)})
        para.clear()
    for line in lines:
        if not line.strip():
            close()
        elif (line.startswith("- ") and para and not para[0].startswith("- ")) or \
                (line.startswith("|") != para[0].startswith("|") if para else False):
            close()
            para.append(line)
        else:
            para.append(line)
    close()
    return blocks


def _text(blocks: list) -> str:
    """Prose blocks as plain words (for search and the fingerprint)."""
    words = [b["p"] if "p" in b else " ".join(b["ul"]) if "ul" in b else " ".join(" ".join(r) for r in b["table"])
             for b in blocks]
    return squeeze(html.unescape(re.sub(r"<[^>]+>", "", " ".join(words))))


# ------------------------------ reading the file -----------------------------

class _Lines:
    def __init__(self, path: Path, qid: str = ""):
        self.path, self.qid = path, qid

    def error(self, number: int, what: str) -> ValueError:
        where = f"{_rel(self.path)}, line {number}" + (f" ({self.qid})" if self.qid else "")
        return ValueError(f"{where}: {what}. Fix it there ({FORMAT}), then make the page again.")


def _fields(lines: list, at: list, err, allowed=None) -> list:
    """[(label, value, line number)] of a list of fields; a value's continuation lines (indented by 2 spaces)
    joined, a blank line between two of them kept as a paragraph break ("\n\n")."""
    out = []
    for line, n in zip(lines, at):
        if not line.strip():
            if out:
                out[-1][1].append("")
            continue
        if line.startswith("  ") and out:
            out[-1][1].append(line.strip())
            continue
        m = re.match(r"^- ([^:]+?): (.*)$", line)
        if not m:
            raise err(n, f'"{line.strip()[:60]}" isn\'t a field: each line here is "- <label>: <value>", and a '
                         f"line indented by two spaces continues the one before")
        label = m.group(1).strip()
        if allowed is not None and label not in allowed:
            raise err(n, f'"{label}" isn\'t a field here; the fields are: {", ".join(allowed)}')
        out.append([label, [m.group(2).strip()], n])
    result = []
    for label, parts, n in out:
        while parts and not parts[-1]:
            parts.pop()
        paragraphs, cur = [], []
        for part in parts + [""]:
            if part:
                cur.append(part)
            elif cur:
                paragraphs.append(" ".join(cur))
                cur = []
        result.append((label, "\n\n".join(paragraphs), n))
    return result


def _fingerprint(lines: list) -> str:
    return hashlib.sha256(squeeze("\n".join(lines)).encode("utf-8")).hexdigest()[:12]


def _question(qid: str, title: str, lines: list, at: list, path: Path) -> dict:
    err = _Lines(path, qid).error
    head_end = next((i for i, l in enumerate(lines) if l.startswith("### ")), len(lines))
    head = dict((label, (value, n)) for label, value, n in _fields(lines[:head_end], at[:head_end], err,
                                                                  ("status", "priority", "question kind", "in short")))
    for need in ("status", "priority", "question kind", "in short"):
        if need not in head:
            raise err(at[0] - 1, f'the question has no "- {need}: …" line under its heading')
    status = head["status"][0]
    if status not in STATUSES:
        raise err(head["status"][1], f'its status is "{status}"; it must be one of {", ".join(STATUSES)}')
    priority = head["priority"][0]
    if priority not in PRIORITIES:
        raise err(head["priority"][1], f'its priority is "{priority}"; it must be one of {", ".join(PRIORITIES)}')
    qkind = head["question kind"][0]
    if qkind not in QUESTION_KINDS:
        raise err(head["question kind"][1], f'its question kind is "{qkind}"; it must be one of {", ".join(QUESTION_KINDS)}')
    # the subsections, in order
    subs, cur = [], None
    for i in range(head_end, len(lines)):
        line = lines[i]
        if line.startswith("### "):
            cur = {"heading": line[4:].strip(), "lines": [], "at": [], "line": at[i]}
            subs.append(cur)
        elif line.startswith("#") and not line.startswith("#### "):
            raise err(at[i], f'"{line.strip()}" isn\'t a heading a question may have here (a question\'s parts are '
                             f'"### " headings; options are "#### Option <k>: …" under "### Options")')
        else:
            cur["lines"].append(line)
            cur["at"].append(at[i])
    names = [s for s, _ in SECTIONS]

    def kind(h):
        return h
    order = 0
    for s in subs:
        k = kind(s["heading"])
        if k not in names:
            raise err(s["line"], f'"### {s["heading"]}" isn\'t one of a question\'s parts: {", ".join(names)}')
        if names.index(k) < order:
            raise err(s["line"], f'"### {s["heading"]}" is out of order: a question\'s parts come in the order '
                                 f'{", ".join(names)}')
        if [kind(o["heading"]) for o in subs[:subs.index(s)]].count(k):
            raise err(s["line"], f'"### {s["heading"]}" is there twice' + (
                ': a question shows one record, the clearest example for its decision, and lists every other '
                'record and classed triple it affects under "### Affects"' if k == "Example record" else ""))
        order = names.index(k)
    have = [kind(s["heading"]) for s in subs]
    for name, many in SECTIONS:
        if many == "1" and name not in have:
            raise err(at[0] - 1, f'the question has no "### {name}" part')
    if (status == ANSWERED) != ("The answer" in have):
        raise err(at[0] - 1, 'an answered question has a "### The answer" part, and only an answered one'
                             + (f' (its status is "{status}")' if status != ANSWERED else ""))
    if ("Options" in have) != ("Consequences" in have):
        raise err(at[0] - 1, 'a question with "### Options" has "### Consequences" (what each option changes, for me), '
                             'and only one with options')
    terms = []
    q = {"id": qid, "number": int(qid[1:]), "title": title, "status": status, "priority": priority,
         "question_kind": qkind, "in_short": head["in short"][0], "line": at[0] - 1, "records": [], "schema": [], "rows": [],
         "rules": [], "methods": [], "options": [], "context": [], "answer": [], "notes": [],
         "affects": {"records": [], "triples": [], "rows": [], "entries": [], "rules": [], "methods": []}}
    for s in subs:
        k = kind(s["heading"])
        if k in ("The question", "Context", "My current reading", "The answer", "My notes"):
            try:
                blocks = _prose(s["lines"], terms)
            except ValueError as e:
                raise err(s["line"], f'in "### {s["heading"]}", {e}') from None
            if not blocks:
                raise err(s["line"], f'"### {s["heading"]}" is empty')
            q[{"The question": "question", "Context": "context", "My current reading": "reading",
               "The answer": "answer", "My notes": "notes"}[k]] = blocks
        elif k == "Example record":
            got = _fields(s["lines"], s["at"], err, RECORD_FIELDS)
            rec = {"line": s["line"], "source_texts": [], "triples": [],
                   "in_ground_truth": True, "not_yet": ""}
            for label, value, n in got:
                if label in ("record id", "pool position", "title", "notes", "in the ground truth") and label in rec:
                    raise err(n, f'"{label}" is there twice in this record')
                if label == "record id":
                    if not re.fullmatch(r"[0-9a-f-]{8,}", value):
                        raise err(n, f'"{value}" isn\'t a record id (the catalog\'s id, e.g. 6cfafd07-40f1-46da-9d92-36c2bb319f0b)')
                    rec["record id"] = value
                elif label == "pool position":
                    if not value.isdigit():
                        raise err(n, f'the pool position "{value}" isn\'t a number')
                    rec["pool position"] = int(value)
                elif label in ("title", "notes"):
                    rec[label] = value
                elif label == "in the ground truth":
                    if not value.startswith("not yet"):
                        raise err(n, '"in the ground truth" is written only for a record not in it yet: "- in the '
                                     'ground truth: not yet (…why…)"')
                    rec["in the ground truth"] = value
                    rec["in_ground_truth"], rec["not_yet"] = False, value
                elif label == "source text":
                    rec["source_texts"].append({"text": value, "line": n})
                else:
                    t = TRIPLE.match(value)
                    if not t:
                        raise err(n, f'"{value[:80]}" isn\'t a classed triple written "subject instance" '
                                     f'(SubjectClass) PREDICATE "object instance" (ObjectClass)')
                    rec["triples"].append({"subject": t.group(1), "subject_class": t.group(2), "predicate": t.group(3),
                                           "object": t.group(4), "object_class": t.group(5), "line": n})
            for need in ("record id", "pool position", "title", "notes"):
                if need not in rec:
                    raise err(s["line"], f'this record has no "- {need}: …" field')
            if not rec["source_texts"]:
                raise err(s["line"], 'a record has at least one "- source text: …": the passage the question is about')
            q["records"].append(rec)
        elif k == "Ground truth schema":
            for label, value, n in _fields(s["lines"], s["at"], err):
                m = re.fullmatch(r"(entity class|predicate) (\S+)", label)
                if not m:
                    raise err(n, f'"{label}": a definition\'s field is "- entity class <EntityClass>: …" or '
                                 f'"- predicate <PREDICATE>: …"')
                q["schema"].append({"kind": m.group(1), "entry": m.group(2), "definition": value, "line": n})
        elif k == "Translation table":
            for label, value, n in _fields(s["lines"], s["at"], err):
                m = re.fullmatch(r"(entity class|predicate) (\S+) -> (\S+)( \(swap subject and object\))?", label)
                if not m:
                    raise err(n, f'"{label}": a row\'s field is "- <entity class or predicate> <component class> -> '
                                 f'<component class of the ground truth schema, or (none)>", then " (swap subject and '
                                 f'object)" if the row swaps, then ": <its definition, current or past schema>"')
                q["rows"].append({"kind": m.group(1), "crt": m.group(2), "gtt": m.group(3), "swap": bool(m.group(4)),
                                  "definition": value, "line": n})
        elif k == "Annotation guidelines":
            for label, value, n in _fields(s["lines"], s["at"], err):
                m = re.fullmatch(r"(.+), rule (\d+)", label)
                if not m:
                    raise err(n, f'"{label}": a rule\'s field is "- <section of the guidelines>, rule <n>: <its words>"')
                q["rules"].append({"section": m.group(1).strip(), "rule": int(m.group(2)), "words": value, "line": n})
        elif k == "Options":
            q["options"] = _options(s, err, terms)
        elif k == "Consequences":
            _consequences(q, s, err, terms)
        elif k == "Affects":
            _affects(q, _fields(s["lines"], s["at"], err), err)
            if not any(q["affects"].values()):
                raise err(s["line"], '"### Affects" names nothing: list what an answer may change')
        elif k == "Pipeline method":
            for label, value, n in _fields(s["lines"], s["at"], err):
                q["methods"].append({"path": label, "words": value, "line": n})
    q["terms"] = terms
    _for_the_expert(q, subs, title, err)
    answer_at = next((x["line"] for x in subs if x["heading"] == "The answer"), at[-1] + 1 if at else 0)
    body = [l for l, n in zip(lines, at) if n < answer_at and not re.match(r"^- (status|priority): ", l)]
    q["fingerprint"] = _fingerprint([f"## {qid}: {title}"] + body)
    q["shown"] = f"{qid}: {title} | fingerprint {q['fingerprint']}"
    q["search"] = squeeze(" ".join([qid, title, q["in_short"], _text(q["question"]), _text(q["context"]),
                                    _text(q["reading"]), _text(q["answer"])]
                                   + [f"{r['title']} {r['notes']} {r['record id']}" for r in q["records"]]
                                   + [f"{e['entry']} {e['definition']}" for e in q["schema"]]
                                   + [f"{r['crt']} {r['gtt']} {r['definition']}" for r in q["rows"]]
                                   + [f"{m['path']} {m['words']}" for m in q["methods"]]
                                   + [f"{o['title']} {_text(o['body'])}" for o in q["options"]]))
    return q


def _affects(q: dict, fields: list, err) -> None:
    a = q["affects"]
    for label, value, n in fields:
        if label == "record at pool position":
            raise err(n, 'a record is "- record at pool position <n>: <record id>"')
        m = re.fullmatch(r"record at pool position (\d+)", label)
        t = re.fullmatch(r"classed triple of the record at pool position (\d+)", label)
        if m:
            a["records"].append({"position": int(m.group(1)), "id": value, "line": n})
        elif t:
            tm = TRIPLE.match(value)
            if not tm:
                raise err(n, f'"{value[:80]}" isn\'t a classed triple written "subject instance" (SubjectClass) '
                             f'PREDICATE "object instance" (ObjectClass)')
            a["triples"].append({"position": int(t.group(1)), "subject": tm.group(1), "subject_class": tm.group(2),
                                 "predicate": tm.group(3), "object": tm.group(4), "object_class": tm.group(5),
                                 "line": n})
        elif label == "translation table row":
            r = re.fullmatch(r"(entity class|predicate) (\S+)", value)
            if not r:
                raise err(n, f'"{value}": a row is "<entity class or predicate> <component class, current or past schema>"')
            a["rows"].append({"kind": r.group(1), "crt": r.group(2), "line": n})
        elif label == "ground truth schema entry":
            r = re.fullmatch(r"(entity class|predicate) (\S+)", value)
            if not r:
                raise err(n, f'"{value}": an entry is "<entity class or predicate> <component class>"')
            a["entries"].append({"kind": r.group(1), "entry": r.group(2), "line": n})
        elif label == "rule":
            r = re.fullmatch(r"(.+), rule (\d+)", value)
            if not r:
                raise err(n, f'"{value}": a rule is "<section of the guidelines>, rule <n>"')
            a["rules"].append({"section": r.group(1).strip(), "rule": int(r.group(2)), "line": n})
        elif label == "pipeline method":
            r = re.fullmatch(r"(\S+): (.+)", value)
            if not r:
                raise err(n, f'"{value}": a pipeline method is "<path in the repository>: <what of it>"')
            a["methods"].append({"path": r.group(1), "what": r.group(2), "line": n})
        else:
            raise err(n, f'"{label}" isn\'t a field of "### Affects"; they are: record at pool position <n>, '
                         f'classed triple of the record at pool position <n>, translation table row, ground truth '
                         f'schema entry, rule, pipeline method')


def _numbered(s: dict, err, what: str) -> list:
    """[{number, title, lines: [(line, n)], line}]: the "#### Option <k>: <title>" parts of a subsection."""
    opts, cur = [], None
    for line, n in zip(s["lines"], s["at"]):
        if line.startswith("#### "):
            m = re.fullmatch(r"#### Option (\d+): (.+)", line.strip())
            if not m:
                raise err(n, f'"{line.strip()}": an option\'s heading is "#### Option <k>: <short title>"')
            if int(m.group(1)) != len(opts) + 1:
                raise err(n, f"option {m.group(1)} comes where option {len(opts) + 1} should: number them 1, 2, 3, …")
            cur = {"number": int(m.group(1)), "title": m.group(2).strip(), "lines": [], "line": n}
            opts.append(cur)
        elif cur is None:
            if line.strip():
                raise err(n, f'under "### {what}", each option starts with "#### Option <k>: <short title>"')
        else:
            cur["lines"].append((line, n))
    return opts


def _options(s: dict, err, terms: list) -> list:
    opts = _numbered(s, err, "Options")
    if len(opts) < 2:
        raise err(s["line"], '"### Options" has fewer than two options ("#### Option <k>: …")')
    out = []
    for o in opts:
        said = next((n for l, n in o["lines"] if l.strip() == "Consequences:"), None)
        if said is not None:
            raise err(said, f'option {o["number"]}: its consequences go under "### Consequences", for me, not here '
                            f'(the expert reads the options as plain choices)')
        body = _prose([l for l, _ in o["lines"]], terms)
        if not body:
            raise err(o["line"], f"option {o['number']} says nothing: what the option is, in plain words")
        out.append({"number": o["number"], "title": o["title"], "body": body, "consequences": [], "line": o["line"]})
    return out


def _consequences(q: dict, s: dict, err, terms: list) -> None:
    """Each option's consequences, from "### Consequences": the same options, in the same order, with the same titles."""
    opts = _numbered(s, err, "Consequences")
    if [(o["number"], o["title"]) for o in opts] != [(o["number"], o["title"]) for o in q["options"]]:
        raise err(s["line"], '"### Consequences" has one "#### Option <k>: <title>" per option of "### Options", '
                             'the same numbers and titles, in the same order')
    for o, option in zip(opts, q["options"]):
        cons = _prose([l for l, _ in o["lines"]], terms)
        if len(cons) != 1 or "ul" not in cons[0]:
            raise err(o["line"], f'option {o["number"]}\'s consequences are one "- " item each, and nothing else')
        option["consequences"] = cons[0]["ul"]


def _for_the_expert(q: dict, subs: list, title: str, err) -> None:
    """What the expert reads never says "pool position" or a record id (NOT_FOR_THE_EXPERT); q["named_records"]:
    each record it names by its title, with the line, for check_questions."""
    q["named_records"] = []
    texts = [(q["line"], title)]
    for s in subs:
        if s["heading"] in EXPERT_SECTIONS:
            texts += [(n, l) for l, n in zip(s["lines"], s["at"])
                      if not (s["heading"] == "Example record" and re.match(r"^- (record id|pool position): ", l))]
    for n, line in texts:
        m = NOT_FOR_THE_EXPERT.search(line)
        if m:
            raise err(n, f'"{m.group(0)}" is in what the expert reads: name a record by its title, in quotes '
                         f'(the record "<title>"), and write a triple out; pool positions and ids go under "### My '
                         f'notes" or "### Affects"')
        for names in NAMED_RECORDS.finditer(line):
            q["named_records"] += [{"title": t, "line": n} for t in re.findall(r'"([^"\n]+)"', names.group(1))]


def read_questions(path: Path = QUESTIONS_PATH) -> list:
    """Every question of the file, in its order; [] if there is no file. ValueError, naming the line, at the first
    thing not in the format."""
    path = Path(path)
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n").replace("\r", "\n").split("\n")
    err = _Lines(path).error
    starts = [i for i, l in enumerate(lines) if l.startswith("## ")]
    out, seen = [], {}
    for k, i in enumerate(starts):
        m = re.fullmatch(r"## (Q(\d+)): (.+)", lines[i].strip())
        if not m:
            raise err(i + 1, f'"{lines[i].strip()}" isn\'t a question\'s heading: "## Q<n>: <short title>"')
        qid = m.group(1)
        if qid in seen:
            raise err(i + 1, f"{qid} is there twice (also line {seen[qid]}): each question has its own number")
        if out and int(m.group(2)) <= out[-1]["number"]:
            raise err(i + 1, f"{qid} comes after {out[-1]['id']}: number the questions in the file's order")
        seen[qid] = i + 1
        end = starts[k + 1] if k + 1 < len(starts) else len(lines)
        out.append(_question(qid, m.group(3).strip(), lines[i + 1:end], list(range(i + 2, end + 1)), path))
    return out


# ------------------------------ checking the quotes --------------------------

def _plain_md(text: str) -> str:
    text = re.sub(r"\[([^\[\]]*)\]\([^)]*\)", r"\1", text)
    return squeeze(text.replace("**", "").replace("`", "").replace("*", ""))


def guideline_rules(path: Path = GUIDELINES_PATH) -> dict:
    """{(section heading, rule number): the rule's words, markup and links taken out}: each numbered rule of
    annotations/guidelines.md, with the indented lines that continue it."""
    rules, section, cur = {}, "", None
    for line in Path(path).read_text(encoding="utf-8").split("\n"):
        h = re.match(r"^#{2,3} (.+)", line)
        m = re.match(r"^(\d+)\. (.*)", line)
        if h:
            section, cur = h.group(1).strip(), None
        elif m:
            cur = (section, int(m.group(1)))
            rules[cur] = [m.group(2)]
        elif cur and line.startswith(" ") and line.strip():
            rules[cur].append(line.strip())
        elif line.strip():
            cur = None
    return {k: _plain_md(" ".join(v)) for k, v in rules.items()}


def check_questions(questions: list, records_path: Path = RECORDS_PATH, splits_path: Path = SPLITS_PATH,
                    ground_truth_dir: Path = GROUND_TRUTH_DIR, schema_path: Path = SCHEMA_PATH,
                    guidelines_path: Path = GUIDELINES_PATH, questions_path: Path = QUESTIONS_PATH,
                    mapping_path: Path = MAPPING_PATH) -> list:
    """["…"]: every quote of the questions that isn't what its source says now, and every record that isn't a
    tuning record; empty when all agree."""
    problems, pool, gt, records = [], {}, None, None
    where = lambda q, n: f"{_rel(questions_path)}, line {n} ({q['id']})"           # noqa: E731
    if any(q["records"] for q in questions):
        missing = [p for p in (records_path, splits_path) if not Path(p).exists()]
        if missing:
            return [f"{', '.join(_rel(p) for p in missing)} not found: the questions quote records, and their text "
                    f"and pool positions are checked against 020's records.jsonl and 030's splits.json. Run "
                    f"`py 020_clean/run.py` and `py 030_split/run.py` first, then make the page again."]
        records = load_records(records_path)
        pool = {r["id"]: r for r in read_pool(splits_path)}
        gt = read_ground_truth(ground_truth_dir)
    schema = read_ground_truth_schema(schema_path)
    rules = guideline_rules(guidelines_path) if any(q["rules"] for q in questions) else {}
    mapping = read_mapping(mapping_path)
    if any(q["affects"]["rules"] for q in questions) and not rules:
        rules = guideline_rules(guidelines_path)
    if not pool and any(q["affects"]["records"] or q["affects"]["triples"] or q["affects"]["entries"] for q in questions):
        if not Path(splits_path).exists():
            return [f"{_rel(splits_path)} not found: the questions name records, whose pool positions are checked "
                    f"against 030's splits.json. Run `py 030_split/run.py` first, then make the page again."]
        pool = {r["id"]: r for r in read_pool(splits_path)}
        gt = read_ground_truth(ground_truth_dir)
    for q in questions:
        for rec in q["records"]:
            rid, at = rec["record id"], where(q, rec["line"])
            if rid not in pool:
                problems.append(f"{at}: record {rid} isn't in the ground truth candidates pool (030's splits.json), "
                                f"so it can't be a tuning record. The page shows only tuning records: take it out.")
                continue
            p = pool[rid]
            if p["part"] != TUNING:
                problems.append(f"{at}: record {rid} (pool position {p['position']}) is a held-out record. The page "
                                f"shows only tuning records: showing a held-out record, and changing the guidelines "
                                f"or the ground truth schema from what an expert says about it, would let it "
                                f"influence the pipeline, so its metrics would flatter it. Take it out of {q['id']}, "
                                f"or ask about a tuning record instead.")
                continue
            if p["position"] != rec["pool position"]:
                problems.append(f"{at}: record {rid} is at pool position {p['position']}, not {rec['pool position']}: "
                                f"correct the heading and the field.")
            r = records.get(rid)
            if r is None:
                problems.append(f"{at}: record {rid} isn't in 020's records.jsonl.")
                continue
            for field in ("title", "notes"):
                if squeeze(r.get(field)) != squeeze(rec[field]):
                    problems.append(f"{at}: the {field} quoted isn't the record's {field} (020's records.jsonl), "
                                    f"spaces aside. The record's {field}: {squeeze(r.get(field))}")
            text = squeeze(f"{r.get('title') or ''} {r.get('notes') or ''}")
            for s in rec["source_texts"]:
                if squeeze(s["text"]) not in text:
                    problems.append(f"{where(q, s['line'])}: the source text \"{s['text']}\" isn't in record {rid}'s "
                                    f"title or notes, word for word.")
            rows = [row for row in gt.rows if row["id"] == rid]
            if rec["in_ground_truth"] and rid not in gt.records:
                problems.append(f"{at}: record {rid} isn't in the ground truth (annotations/ground_truth/): write "
                                f"\"- in the ground truth: not yet (…)\" in its part, or annotate it first.")
            elif not rec["in_ground_truth"] and rid in gt.records:
                problems.append(f"{at}: record {rid} is in the ground truth now ({gt.records[rid]['file']}): take "
                                f"out the line \"in the ground truth: not yet\", so its classed triples are checked "
                                f"against it.")
            elif rec["in_ground_truth"]:
                sources = {squeeze(s["text"]) for s in rec["source_texts"]}
                for t in rec["triples"]:
                    same = [row for row in rows if all(row[k] == t[k] for k in
                                                       ("subject", "subject_class", "predicate", "object", "object_class"))]
                    if not same:
                        problems.append(f"{where(q, t['line'])}: the classed triple isn't one of record {rid}'s ground "
                                        f"truth triples (annotations/ground_truth/), word for word.")
                    elif not any(squeeze(row["source_text"]) in sources for row in same):
                        problems.append(f"{where(q, t['line'])}: its ground truth triple's source text, "
                                        f"\"{same[0]['source_text']}\", isn't among the record's \"source text\" "
                                        f"fields: add it.")
        for e in q["schema"]:
            key = "entity_classes" if e["kind"] == "entity class" else "predicates"
            now = schema[key].get(e["entry"])
            if now is None:
                problems.append(f"{where(q, e['line'])}: the ground truth schema has no {e['kind']} {e['entry']}.")
            elif squeeze(now) != squeeze(e["definition"]):
                problems.append(f"{where(q, e['line'])}: the ground truth schema's definition of {e['kind']} "
                                f"{e['entry']} is now \"{now}\": quote it as it is.")
        for row in q["rows"]:
            same = [r for r in mapping if r["kind"] == row["kind"] and r["component_class_from_past_or_crt_schema"] == row["crt"]]
            if not same:
                problems.append(f"{where(q, row['line'])}: the translation table has no row for {row['kind']} "
                                f"{row['crt']} (current or past schema).")
                continue
            r = same[0]
            if r["component_class_in_gtt"] != row["gtt"] or (r["swap_subject_and_object"] == "yes") != row["swap"]:
                problems.append(f"{where(q, row['line'])}: the translation table's row for {row['kind']} {row['crt']} "
                                f"(current or past schema) translates it to {r['component_class_in_gtt']}"
                                + (" (swap subject and object)" if r["swap_subject_and_object"] == "yes" else "")
                                + ": quote it as it is.")
            elif squeeze(r["definition_from_past_or_crt_schema"]) != squeeze(row["definition"]):
                problems.append(f"{where(q, row['line'])}: the row for {row['kind']} {row['crt']} stores the "
                                f"definition \"{r['definition_from_past_or_crt_schema']}\": quote it as it is.")
        for meth in q["methods"]:
            f = ANNOTATIONS_DIR.parent / meth["path"]
            if not f.is_file():
                problems.append(f"{where(q, meth['line'])}: {meth['path']} isn't a file of the repository.")
            elif _plain_md(meth["words"]) not in _plain_md(f.read_text(encoding="utf-8", errors="replace")):
                problems.append(f"{where(q, meth['line'])}: these words aren't in {meth['path']} as it is now: "
                                f"quote them exactly.")
        problems += _check_affects(q, where, pool, gt, schema, mapping, rules, ground_truth_dir)
        if q["named_records"]:
            if records is None:
                records = load_records(records_path) if Path(records_path).exists() else {}
            titles = {squeeze((records.get(r["id"]) or {}).get("title")) for r in q["affects"]["records"]}
            for r in q["named_records"]:
                if squeeze(r["title"]) not in titles:
                    problems.append(f"{where(q, r['line'])}: \"{r['title']}\" follows the word \"record\", but isn't "
                                    f"the title of a record \"Affects\" names (020's records.jsonl, spaces aside): quote "
                                    f"the title exactly, and name the record in \"Affects\".")
        for rule in q["rules"]:
            now = rules.get((rule["section"], rule["rule"]))
            if now is None:
                problems.append(f"{where(q, rule['line'])}: annotations/guidelines.md has no rule {rule['rule']} in a "
                                f"section \"{rule['section']}\".")
            elif _plain_md(rule["words"]) not in now:
                problems.append(f"{where(q, rule['line'])}: these aren't the words of rule {rule['rule']} of "
                                f"\"{rule['section']}\" (annotations/guidelines.md) as it is now: quote them exactly.")
    return problems


def _check_affects(q: dict, where, pool: dict, gt, schema: dict, mapping: list, rules: dict, ground_truth_dir) -> list:
    """What "### Affects" names that doesn't exist, and what it leaves out (see the module's docstring)."""
    problems, a = [], q["affects"]
    if gt is None:
        gt = read_ground_truth(ground_truth_dir)
    if not pool and (a["records"] or a["triples"] or a["entries"]):
        return [f"{where(q, q['line'])}: 030's splits.json isn't there to check the records \"Affects\" names. Run "
                f"`py 030_split/run.py` first, then make the page again."]
    by_position = {r["position"]: r for r in pool.values()}
    tuning = {r["id"] for r in pool.values() if r["part"] == TUNING}
    listed_records = {r["position"] for r in a["records"]}
    for r in a["records"]:
        p = pool.get(r["id"])
        if p is None:
            problems.append(f"{where(q, r['line'])}: record {r['id']} isn't in the ground truth candidates pool.")
        elif p["part"] != TUNING:
            problems.append(f"{where(q, r['line'])}: record {r['id']} (pool position {p['position']}) is a held-out "
                            f"record: the page names only tuning records. Take it out.")
        elif p["position"] != r["position"]:
            problems.append(f"{where(q, r['line'])}: record {r['id']} is at pool position {p['position']}, not "
                            f"{r['position']}.")
    keys = ("subject", "subject_class", "predicate", "object", "object_class")
    listed = set()
    for t in a["triples"]:
        listed.add((t["position"],) + tuple(t[k] for k in keys))
        if t["position"] not in listed_records:
            problems.append(f"{where(q, t['line'])}: the record at pool position {t['position']} isn't named in "
                            f"\"Affects\" itself: add \"- record at pool position {t['position']}: <its id>\".")
            listed_records.add(t["position"])
        rec = by_position.get(t["position"])
        t["draft"] = rec is None or rec["id"] not in gt.records
        if t["draft"]:
            continue                                         # a record not in the ground truth yet: a draft
        if not any(row["id"] == rec["id"] and all(row[k] == t[k] for k in keys) for row in gt.rows):
            problems.append(f"{where(q, t['line'])}: this isn't one of the ground truth triples of the record at "
                            f"pool position {t['position']}, word for word.")
    positions = {r["id"]: r["position"] for r in pool.values()} if pool else {}
    for e in a["entries"]:
        key = "entity_classes" if e["kind"] == "entity class" else "predicates"
        if e["entry"] not in schema[key]:
            problems.append(f"{where(q, e['line'])}: the ground truth schema has no {e['kind']} {e['entry']}.")
            continue
        field = ("predicate",) if e["kind"] == "predicate" else ("subject_class", "object_class")
        for row in gt.rows:
            if row["id"] in tuning and any(row[f] == e["entry"] for f in field) and row["predicate"]:
                k = (positions[row["id"]],) + tuple(row[x] for x in keys)
                if k not in listed:
                    problems.append(f"{where(q, e['line'])}: {e['kind']} {e['entry']} (ground truth schema) is used by "
                                    f"the ground truth triple \"{row['subject']}\" ({row['subject_class']}) "
                                    f"{row['predicate']} \"{row['object']}\" ({row['object_class']}) of the record at "
                                    f"pool position {k[0]}, which \"Affects\" doesn't name: add it.")
        for r in mapping:
            if r["kind"] == e["kind"] and r["component_class_in_gtt"] == e["entry"] and not any(
                    x["kind"] == r["kind"] and x["crt"] == r["component_class_from_past_or_crt_schema"] for x in a["rows"]):
                problems.append(f"{where(q, e['line'])}: the translation table's row {r['kind']} "
                                f"{r['component_class_from_past_or_crt_schema']} (current or past schema) translates to "
                                f"{e['entry']}, and \"Affects\" doesn't name it: add it.")
    for r in a["rows"]:
        if not any(m["kind"] == r["kind"] and m["component_class_from_past_or_crt_schema"] == r["crt"] for m in mapping):
            problems.append(f"{where(q, r['line'])}: the translation table has no row for {r['kind']} {r['crt']}.")
    for r in a["rules"]:
        if (r["section"], r["rule"]) not in rules:
            problems.append(f"{where(q, r['line'])}: annotations/guidelines.md has no rule {r['rule']} in a section "
                            f"\"{r['section']}\".")
    for m in a["methods"]:
        if not (ANNOTATIONS_DIR.parent / m["path"]).exists():
            problems.append(f"{where(q, m['line'])}: {m['path']} isn't in the repository.")
    return problems
