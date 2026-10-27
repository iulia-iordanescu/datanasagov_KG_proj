"""
helpers/review_page.py -- a read-only page of the ground truth schema, the
translation table, and my questions for subject-matter experts, for them to
read and comment on, its publishing at one link, and the reader of the
comments they send back.

    py helpers/review_page.py                  writes outputs/review/review_<date>_<commit>.html
    py helpers/review_page.py --publish        puts it on the branch gh-pages and pushes it (PAGES_URL)
    py helpers/review_page.py --read           reads the comment files and emails in annotations/reviews/
    py helpers/review_page.py --read <folder or files ...>

The page is one HTML file with everything inside it (styles, typefaces,
script, data): it opens by double-click, from disk, in Chrome, Edge or
Firefox, and makes no network request (its Content-Security-Policy forbids
any). It shows annotations/ground_truth_schema.txt,
annotations/component_class_mapping.csv (read with
common.review_comments, which reads them with common.schema_io and
common.component_class_mapping) and annotations/questions_for_experts.md
(read with common.expert_questions, which checks every quote of a question
against its source, and refuses a held-out record), with the date it was
made, the Git commit, and each file's fingerprint. It can't change anything: a reviewer's comments
stay in their browser (localStorage) until they press "Email my comments to
Iulia" (a mailto: link per email, its body in common.review_comments'
EMAIL_FORMAT, split into numbered parts past 1,900 characters, at most 5) or
"Download my comments" (a CSV file, COMMENT_COLUMNS).

--publish puts the page, and only it, on the branch PAGES_BRANCH, which
GitHub Pages serves at PAGES_URL (publish()).

--read gathers the .csv, .eml and .txt files (common.review_comments.read_all)
and writes a summary, grouped by entry, to
outputs/review/comments_<date>_<time>.md, flagging each comment whose entry has
changed since the page it was written on, or is no longer in the files, and
each one whose sender isn't verified.

The Translation table view shows, at first, SAMPLE_SIZE checked rows chosen at random (sample_rows), with a
button to show every row; wrong_rows_bound says what finding none (or a few) wrong among them means.

The page's look is the annotation tool's: its style sheets are read from
helpers/annotator/page.html when the page is made (so the two never drift
apart) and its typefaces from helpers/annotator/fonts/; over it, the page's own palette and typefaces, the demo
deck's (page_fonts(), from helpers/review_page_fonts/). How to use it:
helpers/review_page.md.
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import html
import json
import math
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))                                                  # the repository folder, for common/

from common.component_class_mapping import MAPPING_PATH, NONE, is_checked     # noqa: E402
from common.expert_questions import (ANSWERED, GUIDELINES_PATH, OPEN, PRIORITIES, QUESTION_KIND_WORDS,  # noqa: E402
                                     QUESTIONS_PATH, RECORDS_PATH, WITHDRAWN,
                                     SPLITS_PATH, check_questions, read_questions)
from common.ground_truth import GROUND_TRUTH_DIR                               # noqa: E402
from common.records_io import load_records                                     # noqa: E402
from common.files import write_text                                            # noqa: E402
from common.review_comments import (ALLOWED_SENDER_DOMAINS, CHANGED, COMMENT_COLUMNS, GENERAL, GONE,  # noqa: E402,F401
                                    LEGACY_TOPIC, TOPIC_HEADINGS, TOPICS,
                                    NOT_VERIFIED, REVIEWS_DIR, SCHEMA_PATH, entry_texts, mapping_entries, read_all,
                                    schema_entries)
from common.step import OUTPUTS_DIR                                            # noqa: E402

TERMS_PATH = ROOT / "docs" / "terminology.md"
TEMPLATE = Path(__file__).with_name("review_page.html")
ANNOTATOR_PAGE = Path(__file__).with_name("annotator") / "page.html"
FONTS = Path(__file__).with_name("annotator") / "fonts"
#: The page's own typefaces, the demo deck's (SIL Open Font License, licences beside them): Archivo for headings,
#: Atkinson Hyperlegible (Braille Institute of America) for the text; put inside the page by page_fonts().
PAGE_FONTS_DIR = Path(__file__).with_name("review_page_fonts")
PAGE_FONTS = [("Archivo", "Archivo.woff2", "100 900", "normal"),
              ("Atkinson Hyperlegible", "AtkinsonHyperlegible-Regular.woff2", "400", "normal"),
              ("Atkinson Hyperlegible", "AtkinsonHyperlegible-Bold.woff2", "700", "normal"),
              ("Atkinson Hyperlegible", "AtkinsonHyperlegible-Italic.woff2", "400", "italic")]
OUT_DIR = OUTPUTS_DIR / "review"
#: Where --publish puts the page: a branch that holds only it (and .nojekyll), which GitHub Pages serves at PAGES_URL.
PAGES_BRANCH = "gh-pages"
PAGES_PATH = "review/index.html"
PAGES_URL = "https://iulia-iordanescu.github.io/datanasagov_KG_proj/review/"
#: What the page is made from: --publish stops while any of these has changes not yet committed.
PAGE_SOURCES = ["annotations/ground_truth_schema.txt", "annotations/component_class_mapping.csv",
                "annotations/questions_for_experts.md", "annotations/guidelines.md", "annotations/ground_truth",
                "docs/terminology.md", "helpers/review_page.py", "helpers/review_page.html", "helpers/annotator/page.html",
                "helpers/annotator/fonts", "helpers/review_page_fonts", "common/common_helpers/review_comments.py",
                "common/common_helpers/expert_questions.py"]
#: How many checked rows of the translation table the Translation table view shows at first, chosen at random (the
#: button below them shows every row). Why 30: with 164 checked rows, a reviewer who finds no wrong row among 30 chosen
#: at random can say, at 95% confidence, that at most 14 of the 164 (8.5%) are wrong (wrong_rows_bound).
SAMPLE_SIZE = 30
#: What chooses the sample (sample_rows): change it only to draw a new sample on purpose.
SAMPLE_SEED = "review sample 1"
#: The confidence wrong_rows_bound states its bound at.
CONFIDENCE = 0.95
#: The terms the page's Terms view shows, in this order, each as docs/terminology.md defines it (the first bold
#: words of an entry's first column).
GLOSSARY = ["schema", "schema entry", "entity class", "predicate", "kind", "component class", "pattern",
            "pinned predicate", "ground truth", "ground truth triple", "ground truth schema", "record", "classed triple",
            "subject instance", "object instance", "domain", "range", "current schema", "extracted triple",
            "translation table", "row state", "row", "step", "fingerprint", "text", "fact", "source text",
            "ground truth candidates pool", "tuning part", "annotation guidelines", "model", "knowledge graph",
            "qualifier", "describes triple", "metadata field", "component instance", "induced schema", "pair",
            "precision", "recall", "schema additions", "drafted triple"]
#: Terms an entry of docs/terminology.md defines inside another's definition (in bold there), and that entry.
ALIASES = {"pool position": "ground truth candidates pool", "tuning record": "tuning part",
           "subject class": "subject instance", "object class": "object instance"}
#: Terms the Questions view links only where a question links them (to docs/terminology.md): they are also
#: everyday words ("a kind of", "a range of"), so finding them by their words alone would link the wrong uses.
LINKED_ONLY_WHERE_MARKED = ["kind", "domain", "range", "row", "step", "text", "fact", "model", "pool", "pair"]


# ------------------------------ the terms ------------------------------------

def _inline(md: str) -> str:
    """One cell of docs/terminology.md as HTML: `code`, **bold**, *italic*, and a link's words (its target, a file of
    the repository, isn't on the reader's computer)."""
    text = re.sub(r"\[([^\[\]]*)\]\([^)]*\)", r"\1", md)
    parts = re.split(r"(`[^`]*`)", text)
    out = []
    for p in parts:
        if p.startswith("`") and p.endswith("`") and len(p) > 1:
            out.append(f"<code>{html.escape(p[1:-1])}</code>")
            continue
        p = html.escape(p, quote=False)
        p = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", p)
        p = re.sub(r"(?<![*\w])\*([^*]+)\*(?![*\w])", r"<em>\1</em>", p)
        out.append(p)
    return "".join(out)


def glossary(path: Path = TERMS_PATH, terms=GLOSSARY) -> list:
    """[{"term", "term_html", "meaning_html", "aliases"}]: each of `terms`, as docs/terminology.md defines it, in
    the order asked; aliases: the words its first column writes in bold (the term, and another name for it:
    "pool"), and those of ALIASES that point to it, lowercased. Stops (ValueError) if one isn't there, so the page
    never shows a definition retyped elsewhere."""
    found = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\| (\*\*.*?) \| (.*) \|$", line)
        if m:
            first = re.match(r"\*\*([^*]+)\*\*", m.group(1)).group(1).strip().lower()
            aliases = _unique([first] + [a.strip().lower() for a in re.findall(r"\*\*([^*]+)\*\*", m.group(1))]
                              + [a for a in ALIASES if ALIASES[a] == first])
            found.setdefault(first, {"term": first, "term_html": _inline(m.group(1)), "meaning_html": _inline(m.group(2)),
                                     "aliases": aliases})
    missing = [t for t in terms if t not in found]
    if missing:
        raise ValueError(f"docs/terminology.md has no entry for: {', '.join(missing)}. The page's Terms view shows "
                         f"each term of GLOSSARY in helpers/review_page.py as terminology.md defines it: add the "
                         f"entry there, or take the term out of GLOSSARY.")
    return [found[t] for t in terms]


# ------------------------------ the page -------------------------------------

def _git(*args) -> str:
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def fingerprint(path: Path) -> str:
    """The file's SHA-256, its first 12 hex digits."""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:12]


def light_only(css: str) -> str:
    """The style sheet without its dark version: every @media (prefers-color-scheme: dark) { ... } block left out,
    nested braces and all, so the page renders light whatever the computer's setting."""
    out, i = [], 0
    for m in re.finditer(r"@media\s*\(\s*prefers-color-scheme\s*:\s*dark\s*\)\s*\{", css):
        if m.start() < i:                                       # inside a block already left out
            continue
        depth, j = 1, m.end()
        while depth and j < len(css):
            depth += {"{": 1, "}": -1}.get(css[j], 0)
            j += 1
        if depth:
            raise ValueError("a @media (prefers-color-scheme: dark) block has no closing brace")
        out.append(css[i:m.start()])
        i = j + (css[j:j + 1] == "\n")                          # with its line's end
    return "".join(out) + css[i:]


def annotator_styles(page: Path = ANNOTATOR_PAGE, fonts: Path = FONTS) -> str:
    """The annotation tool's style sheets, as its page holds them but light only (light_only: the review page has no
    dark version), with each typeface it loads from /fonts/ put inside (a data: address), so the review page needs no
    server and no network."""
    styles = re.findall(r"<style>(.*?)</style>", page.read_text(encoding="utf-8"), re.S)
    if not styles:
        raise ValueError(f"{page.relative_to(ROOT).as_posix()} has no <style> block to take the look from")
    css = light_only("\n".join(styles))

    def font(m):
        data = base64.b64encode((fonts / m.group(1)).read_bytes()).decode("ascii")
        return f'url("data:font/woff2;base64,{data}")'
    return re.sub(r'url\("/fonts/([\w.-]+\.woff2)"\)', font, css)


def page_fonts(folder: Path = PAGE_FONTS_DIR, fonts=PAGE_FONTS) -> str:
    """The @font-face rules of the page's own typefaces (PAGE_FONTS), each file put inside (a data: address)."""
    rules = []
    for family, name, weight, style in fonts:
        data = base64.b64encode((folder / name).read_bytes()).decode("ascii")
        rules.append(f'@font-face {{ font-family: "{family}"; src: url("data:font/woff2;base64,{data}") format("woff2"); '
                     f'font-weight: {weight}; font-style: {style}; font-display: swap; }}')
    return "\n".join(rules)


def _script_json(data) -> str:
    """JSON safe inside a <script> element: no "</" can end it early."""
    return json.dumps(data, ensure_ascii=False).replace("</", "<\\/").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


def questions_data(questions_path: Path = QUESTIONS_PATH, records_path: Path = RECORDS_PATH,
                   splits_path: Path = SPLITS_PATH, ground_truth_dir: Path = GROUND_TRUTH_DIR,
                   schema_path: Path = SCHEMA_PATH, guidelines_path: Path = GUIDELINES_PATH, terms: list = (),
                   mapping_path: Path = MAPPING_PATH) -> list:
    """The questions, as the page shows them (common.expert_questions.read_questions). Stops (ValueError) on a
    question not in the file's format, on a quote that isn't what its source says now, on a record that isn't a
    tuning record, and on a link to docs/terminology.md whose words aren't a term of the Terms view."""
    questions = read_questions(questions_path)
    problems = check_questions(questions, records_path, splits_path, ground_truth_dir, schema_path, guidelines_path,
                               questions_path, mapping_path)
    aliases = {a: t["term"] for t in terms for a in t["aliases"]}
    for q in questions:
        for words in q["terms"]:
            if _term_of(words, aliases) is None:
                problems.append(f"{Path(questions_path).name} ({q['id']}): \"{words}\" links to docs/terminology.md, "
                                f"but isn't a term of the page's Terms view: add the term to GLOSSARY in "
                                f"helpers/review_page.py, or take the link out.")
    if problems:
        raise ValueError("the questions can't be shown as they are:\n- " + "\n- ".join(problems))
    if any(q["affects"]["records"] for q in questions):                 # each record's title, for the page's list
        records = load_records(records_path)
        for q in questions:
            for r in q["affects"]["records"]:
                r["title"] = (records.get(r["id"]) or {}).get("title", "")
    for q in questions:
        label_records(q)
    return questions


def label_records(q: dict) -> None:
    """A record's long title shown once per question, a short label after (helpers/review_page.md, *The questions
    file*). Each record the expert's part of `q` names gets a letter, A, B, …: its examples first, in order, then the
    other records in the order they first appear. An example shows its title in its own part ("Example 1: Record A");
    any other record is shown as Record B: “<title>” where it first appears. After that, everywhere in the expert's
    part, the title is "(Record B)", and an example's classed triple shows "(Record A)" for an instance that is the
    title (its Dataset dropped: the label says it). Where the text names an example before the example, it reads
    "(Record A, below)". Our bookkeeping (notes, quotes, Affects) keeps the full titles; the file is not changed."""
    examples = [r["title"] for r in q["records"]]
    titles = list(dict.fromkeys(examples + [n["title"] for n in q.get("named_records", [])]
                                + [r.get("title", "") for r in q["affects"]["records"]]))
    titles = [t for t in titles if t]
    if not titles:
        return
    # the expert's part, in the order the page shows it: the question, its context, the examples, the options, our
    # reading, the answer. Each slot: (container, key) of an HTML string; an example: ("example", record).
    slots = []

    def blocks(bs):
        for b in bs:
            if "p" in b:
                slots.append((b, "p"))
            elif "ul" in b:
                slots.extend((b["ul"], i) for i in range(len(b["ul"])))
            elif "table" in b:
                slots.extend((row, j) for row in b["table"] for j in range(len(row)))
    blocks(q["question"])
    blocks(q["context"])
    slots.extend(("example", r) for r in q["records"])
    for o in q["options"]:
        blocks(o["body"])
    blocks(q["reading"])
    blocks(q["answer"])
    escaped = {html.escape(t, quote=False): t for t in titles}
    rx = re.compile(r'(?:(?<!\w)(?:[Tt]he )?records? )?"(' + "|".join(re.escape(e) for e in sorted(escaped, key=len, reverse=True))
                    + r')"(?: \(Dataset\))?')
    order = list(dict.fromkeys(examples))
    for c, k in slots:
        if c != "example":
            order += [escaped[m.group(1)] for m in rx.finditer(c[k]) if escaped[m.group(1)] not in order]
    letter = {t: chr(ord("A") + i) if i < 26 else f"A{i - 25}" for i, t in enumerate(order)}
    shown = set()

    def label(m):
        t, s = escaped[m.group(1)], m.string
        bare = s[m.start() - 1:m.start()] == "(" and s[m.end():m.end() + 1] == ")"    # already in brackets
        if t in shown or t in examples:
            words = f"Record {letter[t]}" + ("" if t in shown else ", below")
            return words if bare else f"({words})"
        shown.add(t)
        return f"Record {letter[t]}: “{m.group(1)}”"
    for c, k in slots:
        if c == "example":
            shown.add(k["title"])
            k["label"] = f"Record {letter[k['title']]}"
            for t in k["triples"]:
                for side in ("subject", "object"):
                    if t[side] in letter:
                        t[side + "_label"] = f"Record {letter[t[side]]}"
        else:
            c[k] = rx.sub(label, c[k])


def _term_of(words: str, aliases: dict):
    """The Terms view's term that a link's words name, plurals folded ("tuning records" -> "tuning part")."""
    w = " ".join(words.lower().split())
    for form in (w, (w[:-2] if w.endswith("sses") else w), re.sub(r"ies$", "y", w), re.sub(r"es$", "", w), re.sub(r"s$", "", w)):
        if form in aliases:
            return aliases[form]
    return None


def sample_rows(rows: list, size: int = SAMPLE_SIZE, seed: str = SAMPLE_SEED) -> list | None:
    """The entries of the rows the Translation table view shows at first, in the rows' order: of the checked rows
    (is_checked), the `size` whose SHA-256 of `seed` and the row's entry (its kind and component class, as comments
    are filed) is smallest. Ordering the rows by a hash is a random order, the same on every computer and every
    Python version; and since each row's rank depends on that row alone, the sample stays the same as long as its
    rows are in the table: a row taken out of the sample's place is replaced by the next by rank, and a new row
    enters it only if its rank is among the `size` smallest. None when there are no more than `size` checked rows:
    the view then shows every row, with no button."""
    checked = [r for r in rows if is_checked(r)]
    if len(checked) <= size:
        return None
    rank = lambda r: hashlib.sha256(f"{seed}|{r['entry']}".encode("utf-8")).hexdigest()       # noqa: E731
    chosen = {r["entry"] for r in sorted(checked, key=rank)[:size]}
    return [r["entry"] for r in rows if r["entry"] in chosen]


def wrong_rows_bound(rows: int, sample: int, wrong: int = 0, confidence: float = CONFIDENCE) -> int:
    """The most of `rows` rows that can be wrong, at `confidence`, when `wrong` of `sample` rows chosen at random
    (without putting any back) were found wrong: the largest D for which finding at most `wrong` wrong rows in the
    sample still has a chance of at least 1 - `confidence` (the hypergeometric distribution: the sum over i <= wrong
    of C(D, i) C(rows - D, sample - i) / C(rows, sample)). That chance only falls as D grows, so the first D where it
    drops below 1 - `confidence` ends the search."""
    total = math.comb(rows, sample)
    best = wrong
    for d in range(wrong, rows - sample + wrong + 1):
        chance = sum(math.comb(d, i) * math.comb(rows - d, sample - i) for i in range(wrong + 1)) / total
        if chance < 1 - confidence:
            break
        best = d
    return best


def page_data(schema_path: Path = SCHEMA_PATH, mapping_path: Path = MAPPING_PATH, terms_path: Path = TERMS_PATH,
              questions_path: Path = QUESTIONS_PATH, records_path: Path = RECORDS_PATH, splits_path: Path = SPLITS_PATH,
              ground_truth_dir: Path = GROUND_TRUTH_DIR, guidelines_path: Path = GUIDELINES_PATH,
              when: dt.datetime | None = None) -> dict:
    """Everything the page shows: its version, the ground truth schema, the translation table, the questions, the
    terms."""
    when = when or dt.datetime.now()
    commit = _git("rev-parse", "--short", "HEAD") or "unknown"
    terms = glossary(terms_path)
    rows = mapping_entries(mapping_path, schema_path)
    questions = questions_data(questions_path, records_path, splits_path, ground_truth_dir, schema_path,
                               guidelines_path, terms, mapping_path)
    sample, checked = sample_rows(rows), sum(map(is_checked, rows))
    # what finding none wrong among the rows chosen at random means: at most `bound` of the checked rows are wrong
    bound = wrong_rows_bound(checked, len(sample)) if sample else None
    files = [schema_path, mapping_path] + ([questions_path] if Path(questions_path).exists() else [])
    rel = [Path(p).resolve().relative_to(ROOT).as_posix() if Path(p).resolve().is_relative_to(ROOT) else Path(p).name
           for p in files]
    edited = bool(_git("status", "--porcelain", "--", *rel)) if commit != "unknown" else False
    content = hashlib.sha256(b"".join(Path(p).read_bytes() for p in files)).hexdigest()[:8]
    version = f"review_{when:%Y-%m-%d}_{commit}" + (f"_edited-{content}" if edited else "")
    return {"version": {"id": version, "generated": when.isoformat(timespec="seconds"), "date": f"{when:%Y-%m-%d}",
                        "commit": commit, "edited": edited, "content": content,
                        "files": [{"path": r, "sha256": fingerprint(p)} for r, p in zip(rel, files)]},
            "schema": schema_entries(schema_path), "mapping": {"rows": rows, "none": NONE, "sample": sample,
                                                                "checked": checked, "bound": bound,
                                                                "confidence": CONFIDENCE},
            "questions": questions, "priorities": list(PRIORITIES), "glossary": terms,
            "statuses": {"OPEN": OPEN, "ANSWERED": ANSWERED, "WITHDRAWN": WITHDRAWN},
            "question_kinds": QUESTION_KIND_WORDS,
            # a comment's columns and topics (common/common_helpers/review_comments.py), and the name older copies
            # of the page gave the topic, read as the topic
            "comment_columns": COMMENT_COLUMNS, "topics": TOPICS, "legacy_topic": LEGACY_TOPIC,
            "linked_only_where_marked": LINKED_ONLY_WHERE_MARKED}


def build(data: dict) -> str:
    """The page's HTML, from the template, the annotation tool's look, and the data."""
    page = TEMPLATE.read_text(encoding="utf-8")
    for key, value in {"{{ANNOTATOR_STYLES}}": annotator_styles(), "{{PAGE_FONTS}}": page_fonts(), "{{DATA}}": _script_json(data),
                       "{{VERSION}}": html.escape(data["version"]["id"])}.items():
        if key not in page:
            raise ValueError(f"{TEMPLATE.name} lacks {key}")
        page = page.replace(key, value)
    return page


def generate(out_dir: Path = OUT_DIR, **paths) -> Path:
    data = page_data(**paths)
    out = Path(out_dir) / f"{data['version']['id']}.html"
    write_text(out, build(data))
    return out


# ------------------------------ publishing -----------------------------------

def _run(root: Path, *args, data: bytes | None = None) -> str:
    """A git command in `root`; its output. Stops (RuntimeError) with git's own message if it fails."""
    done = subprocess.run(["git", *args], cwd=root, input=data, capture_output=True)
    if done.returncode:
        raise RuntimeError(f"git {' '.join(args)} failed: {done.stderr.decode('utf-8', 'replace').strip()}")
    return done.stdout.decode("utf-8").strip()


def _published_version(root: Path, ref: str) -> dict:
    """The version (page_data()["version"]) of the page on `ref`, or {} if there is none or it can't be read."""
    try:
        page = _run(root, "show", f"{ref}:{PAGES_PATH}")
        found = re.search(r'<script type="application/json" id="data">(.*?)</script>', page, re.S)
        return json.loads(found.group(1))["version"] if found else {}
    except (RuntimeError, ValueError, KeyError):
        return {}


def publish(root: Path = ROOT, push: bool = True, check_clean: bool = True, **paths) -> dict:
    """Puts the page on the branch PAGES_BRANCH as PAGES_PATH, beside an empty .nojekyll (so GitHub Pages serves the
    files as they are), and pushes it: {"url", "version", "commit" (the branch's), "changed"}. The branch holds
    those two files and nothing else, ever: each publish is one commit whose files are exactly those, written with
    git's own plumbing, so the working folder, the checked-out branch and its files are never touched. Stops
    (RuntimeError) if a file the page is made from (PAGE_SOURCES) has changes not yet committed: the page at the
    link says which commit it shows, so it must be exactly that commit's. Publishes nothing if the page there
    already shows the same commit and the same two files."""
    data = page_data(**paths)
    dirty = _git("status", "--porcelain", "--", *PAGE_SOURCES) if check_clean else ""
    if data["version"]["edited"] or dirty:
        raise RuntimeError("these files the page is made from have changes not yet committed: "
                           + ", ".join(sorted({re.sub(r"^\s*\S+\s+", "", line) for line in dirty.splitlines()}) or
                                       ["annotations/ground_truth_schema.txt, annotations/component_class_mapping.csv "
                                        "or annotations/questions_for_experts.md"])
                           + ". Commit them (or undo them), then publish again: the page at the link shows the "
                             "files as they are in one commit.")
    if push:                                     # another computer may have published since: start from its commit
        subprocess.run(["git", "fetch", "-q", "origin", f"+{PAGES_BRANCH}:refs/remotes/origin/{PAGES_BRANCH}"],
                       cwd=root, capture_output=True)
    parent = ""
    for ref in (f"refs/remotes/origin/{PAGES_BRANCH}", f"refs/heads/{PAGES_BRANCH}"):
        try:
            parent = _run(root, "rev-parse", "--verify", "-q", f"{ref}^{{commit}}")
            break
        except RuntimeError:
            continue
    there = _published_version(root, parent) if parent else {}
    changed = (there.get("commit"), there.get("content")) != (data["version"]["commit"], data["version"]["content"])
    commit = parent
    if changed:
        page = _run(root, "hash-object", "-w", "--stdin", data=build(data).encode("utf-8"))
        empty = _run(root, "hash-object", "-w", "--stdin", data=b"")
        folder, name = PAGES_PATH.split("/")
        sub = _run(root, "mktree", data=f"100644 blob {page}\t{name}\n".encode())
        tree = _run(root, "mktree", data=f"100644 blob {empty}\t.nojekyll\n040000 tree {sub}\t{folder}\n".encode())
        commit = _run(root, "commit-tree", tree, *(["-p", parent] if parent else []),
                      "-m", f"Review page {data['version']['id']}")
    _run(root, "update-ref", f"refs/heads/{PAGES_BRANCH}", commit)
    if push and changed:
        _run(root, "push", "-q", "origin", f"{commit}:refs/heads/{PAGES_BRANCH}")
    return {"url": PAGES_URL, "version": data["version"]["id"] if changed else there.get("id", ""),
            "commit": commit[:7], "changed": changed}


# ------------------------------ reading comments -----------------------------

def _unique(items) -> list:
    out = []
    for x in items:
        if x not in out:
            out.append(x)
    return out


def _sender(c: dict) -> str:
    return f"from {c['sender']}" if c["sender"] != NOT_VERIFIED else NOT_VERIFIED


def summary(read: dict, schema_fp: str, mapping_fp: str, domains=ALLOWED_SENDER_DOMAINS, questions_fp: str = "") -> str:
    """The comments as markdown, grouped by topic and entry. read: common.review_comments.read_all()."""
    comments, files, problems = read["comments"], read["files"], read["problems"]
    reviewers = sorted({c["reviewer"] or "(no name)" for c in comments}, key=str.lower)
    lines = ["# Review comments", "",
             f"Read {dt.date.today():%Y-%m-%d} from {len(files)} file(s): {', '.join(f.name for f in files) or 'none'}.",
             f"{len(comments)} comment(s) from {len(reviewers)} reviewer(s): {', '.join(reviewers) or 'none'}.",
             f"Compared with the files as they are now: `annotations/ground_truth_schema.txt` (sha256 {schema_fp}), "
             f"`annotations/component_class_mapping.csv` (sha256 {mapping_fp})"
             + (f", `annotations/questions_for_experts.md` (sha256 {questions_fp})." if questions_fp else "."), ""]
    changed = sum(1 for c in comments if c["state"] == CHANGED)
    gone = sum(1 for c in comments if c["state"] == GONE)
    unverified = sum(1 for c in comments if c["sender"] == NOT_VERIFIED)
    lines += [f"⚑ {changed} comment(s) on an entry that changed since the page they were written on; "
              f"{gone} on an entry no longer in the files.",
              f"{unverified} comment(s) {NOT_VERIFIED} (from a .txt or .csv file, which has no sender to check); the "
              f"other {len(comments) - unverified} came in an email from an address of {' or '.join(domains)}. A From "
              f"address can be forged: read each comment before acting on it.", ""]
    if problems:
        lines += ["Files skipped, and what is missing:", ""] + [f"- {p}" for p in problems] + [""]
    unknown = [c for c in comments if c["topic"] not in TOPICS]
    for topic in TOPICS:
        mine = [c for c in comments if c["topic"] == topic]
        if not mine:
            continue
        lines += [f"## {TOPIC_HEADINGS[topic]}", ""]
        for entry in _unique(c["entry"] for c in sorted(mine, key=lambda c: c["entry"].lower())):
            if topic == "question":
                title = next((c["now"] for c in mine if c["entry"] == entry and c["now"]), "").split(" | ")[0]
                lines += [f"### {title or entry}", ""]
            elif topic != "general":
                lines += [f"### {entry}", ""]
            for c in sorted((c for c in mine if c["entry"] == entry), key=lambda c: c["timestamp"]):
                lines.append(f"- **{c['reviewer'] or '(no name)'}**, {c['timestamp'][:10]} "
                             f"(page {c['page_version']}; {_sender(c)}): {' '.join(c['comment'].split())}")
                if c["state"] == GONE:
                    lines.append(f"  - ⚑ No longer in the files. As the page showed it: {c['entry_text_shown']}")
                elif c["state"] == CHANGED:
                    lines.append(f"  - ⚑ Changed since that page. Then: {c['entry_text_shown']}")
                    lines.append(f"  - Now: {c['now']}")
            lines.append("")
    if unknown:
        lines += ["## Comments of an unknown topic", ""]
        lines += [f"- **{c['reviewer'] or '(no name)'}** ({c['file']}), topic '{c['topic']}', entry '{c['entry']}': "
                  f"{' '.join(c['comment'].split())}" for c in unknown] + [""]
    return "\n".join(lines)


def read_and_summarize(paths, out_dir: Path = OUT_DIR, schema_path: Path = SCHEMA_PATH,
                       mapping_path: Path = MAPPING_PATH, domains=ALLOWED_SENDER_DOMAINS,
                       questions_path: Path = QUESTIONS_PATH) -> tuple:
    """(the summary's path, its text)."""
    read = read_all(paths, schema_path, mapping_path, domains, questions_path)
    text = summary(read, fingerprint(schema_path), fingerprint(mapping_path), domains,
                   fingerprint(questions_path) if Path(questions_path).exists() else "")
    out = Path(out_dir) / f"comments_{dt.datetime.now():%Y-%m-%d_%H%M%S}.md"
    write_text(out, text)
    return out, text


def main() -> None:
    parser = argparse.ArgumentParser(prog="py helpers/review_page.py",
                                     description="Write a read-only review page of the ground truth schema, the "
                                                 "translation table and my questions for experts, publish it at its "
                                                 "link, or read the comments reviewers sent back.")
    parser.add_argument("--publish", action="store_true",
                        help=f"put the page on the branch {PAGES_BRANCH} and push it, for the link {PAGES_URL}")
    parser.add_argument("--read", nargs="*", metavar="FOLDER_OR_FILE",
                        help="read comment files and emails (default: the folder annotations/reviews) and write a "
                             "summary")
    args = parser.parse_args()
    if args.publish:
        try:
            done = publish()
        except (RuntimeError, ValueError) as e:
            sys.exit(f"Not published: {e}")
        print(f"Published {done['version']} (branch {PAGES_BRANCH}, commit {done['commit']})." if done["changed"] else
              f"The page at the link is already this version ({done['version']}): nothing new to publish.")
        print(f"The link: {PAGES_URL} (GitHub takes a minute or two to show a new version).")
        return
    if args.read is None:
        try:
            out = generate()
        except ValueError as e:
            sys.exit(f"Not made: {e}")
        print(f"Wrote {out.relative_to(ROOT).as_posix()}: open it to check it, then publish it "
              f"(py helpers/review_page.py --publish) and send the link, or send this one file.")
        return
    paths = args.read or [REVIEWS_DIR]
    missing = [p for p in paths if not Path(p).exists()]
    if missing:
        sys.exit(f"Not found: {', '.join(map(str, missing))}. Put the comment files and emails reviewers sent you in "
                 f"{REVIEWS_DIR.relative_to(ROOT).as_posix()}/ (or name the files or folder after --read).")
    out, text = read_and_summarize(paths)
    print(text)
    print(f"\nWrote {out.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
