"""
helpers/review_page.py -- a read-only page of the ground truth schema and the
translation table, for subject-matter experts to read and comment on, and the
reader of the comments they send back.

    py helpers/review_page.py                  writes outputs/review/review_<date>_<commit>.html
    py helpers/review_page.py --read           reads the comment files in annotations/reviews/
    py helpers/review_page.py --read <folder or files ...>

The page is one HTML file with everything inside it (styles, typefaces,
script, data): it opens by double-click, from disk, in Chrome, Edge or
Firefox, and makes no network request (its Content-Security-Policy forbids
any). It shows annotations/ground_truth_schema.txt (read with
common.schema_io) and annotations/component_class_mapping.csv (read with
common.component_class_mapping), with the date it was made, the Git commit,
and each file's fingerprint. It can't change anything: a reviewer's comments
stay in their browser (localStorage) until they press "Download my comments",
which saves a CSV file (COMMENT_COLUMNS) for them to send back.

--read gathers those CSV files and writes a summary, grouped by entry, to
outputs/review/comments_<date>_<time>.md, flagging each comment whose entry has
changed since the page it was written on, or is no longer in the files.

The page's look is the annotation tool's: its style sheets are read from
helpers/annotator/page.html when the page is made (so the two never drift
apart) and its typefaces from helpers/annotator/fonts/. How to use it:
helpers/review_page.md.
"""
from __future__ import annotations

import argparse
import base64
import csv
import datetime as dt
import hashlib
import html
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))                                                  # the repository folder, for common/

from common.component_class_mapping import MAPPING_PATH, NONE, gtt_definitions, is_stale_gtt, read_mapping, gtt_definition  # noqa: E402
from common.files import write_text                                            # noqa: E402
from common.schema_io import read_ground_truth_schema                         # noqa: E402
from common.step import ANNOTATIONS_DIR, OUTPUTS_DIR                           # noqa: E402

SCHEMA_PATH = ANNOTATIONS_DIR / "ground_truth_schema.txt"
TERMS_PATH = ROOT / "docs" / "terminology.md"
TEMPLATE = Path(__file__).with_name("review_page.html")
ANNOTATOR_PAGE = Path(__file__).with_name("annotator") / "page.html"
FONTS = Path(__file__).with_name("annotator") / "fonts"
OUT_DIR = OUTPUTS_DIR / "review"
REVIEWS_DIR = ANNOTATIONS_DIR / "reviews"
#: The columns of a reviewer's comment file, in order.
COMMENT_COLUMNS = ["reviewer", "page_version", "git_commit", "kind", "entry", "entry_text_shown", "comment", "timestamp"]
#: The kinds of comment, in the order the summary lists them.
KINDS = ["general", "entity class", "predicate", "translation row"]
GENERAL = "(general)"
#: The terms the page's Terms view shows, in this order, each as docs/terminology.md defines it (the first bold
#: words of an entry's first column).
GLOSSARY = ["schema", "schema entry", "entity class", "predicate", "kind", "component class", "pattern",
            "pinned predicate", "ground truth", "ground truth triple", "ground truth schema", "record", "classed triple",
            "subject instance", "object instance", "domain", "range", "current schema", "extracted triple",
            "translation table", "row state", "row", "step", "fingerprint"]


# ------------------------------ the entries ----------------------------------

def _pairs(pairs) -> str:
    return "; ".join(f"{s} -> {o}" for s, o in pairs)


def _unique(items) -> list:
    out = []
    for x in items:
        if x not in out:
            out.append(x)
    return out


def schema_entries(path: Path = SCHEMA_PATH) -> dict:
    """{"entity_classes": [entry], "predicates": [entry], "notes": [the file's lines of explanation]}, in the file's
    order. Each entry: kind, entry (its component class), definition, source, (predicates) patterns and pins as
    [[subject class, object class]], and shown: the entry as the page shows it, one line, which a comment keeps."""
    schema = read_ground_truth_schema(path)
    out = {"entity_classes": [], "predicates": [],
           "notes": [re.sub(r"^line \d+: ", "", u) for u in schema["unread"]]}
    for name, definition in schema["entity_classes"].items():
        source = schema["sources"]["entity_classes"].get(name, "")
        out["entity_classes"].append({"kind": "entity class", "entry": name, "definition": definition, "source": source,
                                      "shown": f"{name}: {definition}" + (f" | source: {source}" if source else "")})
    for name, definition in schema["predicates"].items():
        source = schema["sources"]["predicates"].get(name, "")
        patterns = _unique([s, o] for s, p, o in schema["patterns"] if p == name)
        pins = [list(p) for p in schema["pinned"].get(name, [])]
        shown = f"{name}: {definition}"
        shown += f" | patterns: {_pairs(patterns)}" if patterns else ""
        shown += f" | only: {_pairs(pins)}" if pins else ""
        shown += f" | source: {source}" if source else ""
        out["predicates"].append({"kind": "predicate", "entry": name, "definition": definition, "source": source,
                                  "patterns": patterns, "pins": pins, "shown": shown})
    return out


def mapping_entries(path: Path = MAPPING_PATH, schema_path: Path = SCHEMA_PATH) -> list:
    """Every row of the translation table, in the file's order: kind, entry ("<kind> <component class of the current
    or a past schema>", plus " (line N)" for a second row of the same one), the row's values, gtt_now (the ground
    truth schema's definition now of the component class it translates to), stale_gtt, and shown: the row as the
    page shows it, one line."""
    gtt = gtt_definitions(read_ground_truth_schema(schema_path))
    rows, seen = [], set()
    for r in read_mapping(path):
        entry = f"{r['kind']} {r['component_class_from_past_or_crt_schema']}"
        if entry in seen:
            entry += f" (line {r['_line']})"
        seen.add(entry)
        shown = (f"{entry} -> {r['component_class_in_gtt']}"
                 + (f" | swap subject and object: {r['swap_subject_and_object']}" if r["kind"] == "predicate" else "")
                 + f" | checked: {r['checked']}"
                 + f" | definition, current or past schema: {r['definition_from_past_or_crt_schema']}"
                 + f" | definition, ground truth schema: {r['definition_in_gtt']}")
        rows.append({"kind": r["kind"], "entry": entry, "crt": r["component_class_from_past_or_crt_schema"],
                     "gtt": r["component_class_in_gtt"], "swap": r["swap_subject_and_object"], "checked": r["checked"],
                     "crt_def": r["definition_from_past_or_crt_schema"], "gtt_def": r["definition_in_gtt"],
                     "gtt_now": gtt_definition(r, gtt),
                     "stale_gtt": r["checked"] != "no" and r["component_class_in_gtt"] != NONE and is_stale_gtt(r, gtt),
                     "shown": shown})
    return rows


def entry_texts(schema_path: Path = SCHEMA_PATH, mapping_path: Path = MAPPING_PATH) -> dict:
    """{(kind, entry): shown} for every entry the page would show now: what --read compares comments with."""
    s = schema_entries(schema_path)
    out = {(e["kind"], e["entry"]): e["shown"] for e in s["entity_classes"] + s["predicates"]}
    out.update({("translation row", r["entry"]): r["shown"] for r in mapping_entries(mapping_path, schema_path)})
    return out


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
    """[{"term", "term_html", "meaning_html"}]: each of `terms`, as docs/terminology.md defines it, in the order
    asked. Stops (ValueError) if one isn't there, so the page never shows a definition retyped elsewhere."""
    found = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\| (\*\*.*?) \| (.*) \|$", line)
        if m:
            first = re.match(r"\*\*([^*]+)\*\*", m.group(1)).group(1).strip().lower()
            found.setdefault(first, {"term": first, "term_html": _inline(m.group(1)), "meaning_html": _inline(m.group(2))})
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


def annotator_styles(page: Path = ANNOTATOR_PAGE, fonts: Path = FONTS) -> str:
    """The annotation tool's style sheets, as its page holds them, with each typeface it loads from /fonts/ put
    inside (a data: address), so the review page needs no server and no network."""
    styles = re.findall(r"<style>(.*?)</style>", page.read_text(encoding="utf-8"), re.S)
    if not styles:
        raise ValueError(f"{page.relative_to(ROOT).as_posix()} has no <style> block to take the look from")
    css = "\n".join(styles)

    def font(m):
        data = base64.b64encode((fonts / m.group(1)).read_bytes()).decode("ascii")
        return f'url("data:font/woff2;base64,{data}")'
    return re.sub(r'url\("/fonts/([\w.-]+\.woff2)"\)', font, css)


def _script_json(data) -> str:
    """JSON safe inside a <script> element: no "</" can end it early."""
    return json.dumps(data, ensure_ascii=False).replace("</", "<\\/").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


def page_data(schema_path: Path = SCHEMA_PATH, mapping_path: Path = MAPPING_PATH, terms_path: Path = TERMS_PATH,
              when: dt.datetime | None = None) -> dict:
    """Everything the page shows: its version, the ground truth schema, the translation table, the terms."""
    when = when or dt.datetime.now()
    commit = _git("rev-parse", "--short", "HEAD") or "unknown"
    files = [schema_path, mapping_path]
    rel = [Path(p).resolve().relative_to(ROOT).as_posix() if Path(p).resolve().is_relative_to(ROOT) else Path(p).name
           for p in files]
    edited = bool(_git("status", "--porcelain", "--", *rel)) if commit != "unknown" else False
    content = hashlib.sha256(b"".join(Path(p).read_bytes() for p in files)).hexdigest()[:8]
    version = f"review_{when:%Y-%m-%d}_{commit}" + (f"_edited-{content}" if edited else "")
    return {"version": {"id": version, "generated": when.isoformat(timespec="seconds"), "date": f"{when:%Y-%m-%d}",
                        "commit": commit, "edited": edited, "content": content,
                        "files": [{"path": r, "sha256": fingerprint(p)} for r, p in zip(rel, files)]},
            "schema": schema_entries(schema_path), "mapping": {"rows": mapping_entries(mapping_path, schema_path),
                                                                "none": NONE},
            "glossary": glossary(terms_path)}


def build(data: dict) -> str:
    """The page's HTML, from the template, the annotation tool's look, and the data."""
    page = TEMPLATE.read_text(encoding="utf-8")
    for key, value in {"{{ANNOTATOR_STYLES}}": annotator_styles(), "{{DATA}}": _script_json(data),
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


# ------------------------------ reading comments -----------------------------

def comment_files(paths) -> list:
    """The CSV files named, and those in each folder named (not its subfolders), sorted, without repeats."""
    files = []
    for p in map(Path, paths):
        files += sorted(p.glob("*.csv")) if p.is_dir() else [p]
    return _unique(f.resolve() for f in files)


def read_comments(files) -> tuple:
    """(comments, problems). comments: every row with a comment, keeping, for one reviewer and one entry, only the
    latest (a reviewer who downloads twice sends the same comments twice; an edited comment replaces the older one).
    problems: ["file: why it was skipped"]."""
    latest, problems = {}, []
    for f in files:
        try:
            with open(f, encoding="utf-8-sig", newline="") as fh:
                reader = csv.DictReader(fh)
                missing = [c for c in COMMENT_COLUMNS if c not in (reader.fieldnames or [])]
                if missing:
                    problems.append(f"{f.name}: lacks the column(s) {', '.join(missing)}, so it isn't a comment file "
                                    f"the review page saved; skipped")
                    continue
                for row in reader:
                    row = {c: (row.get(c) or "").strip() for c in COMMENT_COLUMNS}
                    if not row["comment"]:
                        continue
                    row["file"] = f.name
                    key = (row["reviewer"].lower(), row["kind"], row["entry"])
                    if key not in latest or row["timestamp"] >= latest[key]["timestamp"]:
                        latest[key] = row
        except (OSError, UnicodeDecodeError, csv.Error) as e:
            problems.append(f"{f.name}: can't be read ({e}); skipped")
    return list(latest.values()), problems


def summary(comments: list, now: dict, files: list, problems: list, schema_fp: str, mapping_fp: str) -> str:
    """The comments as markdown, grouped by kind and entry. now: entry_texts(), what the files hold today."""
    heads = {"general": "General comments", "entity class": "Entity classes (ground truth schema)",
             "predicate": "Predicates (ground truth schema)", "translation row": "Translation table rows"}
    reviewers = sorted({c["reviewer"] or "(no name)" for c in comments}, key=str.lower)
    lines = ["# Review comments", "",
             f"Read {dt.date.today():%Y-%m-%d} from {len(files)} file(s): {', '.join(f.name for f in files) or 'none'}.",
             f"{len(comments)} comment(s) from {len(reviewers)} reviewer(s): {', '.join(reviewers) or 'none'}.",
             f"Compared with the files as they are now: `annotations/ground_truth_schema.txt` (sha256 {schema_fp}), "
             f"`annotations/component_class_mapping.csv` (sha256 {mapping_fp}).", ""]
    changed = sum(1 for c in comments if c["kind"] != "general" and (c["kind"], c["entry"]) in now
                  and now[(c["kind"], c["entry"])] != c["entry_text_shown"])
    gone = sum(1 for c in comments if c["kind"] != "general" and (c["kind"], c["entry"]) not in now)
    lines += [f"⚑ {changed} comment(s) on an entry that changed since the page they were written on; "
              f"{gone} on an entry no longer in the files.", ""]
    if problems:
        lines += ["Files skipped:", ""] + [f"- {p}" for p in problems] + [""]
    unknown = [c for c in comments if c["kind"] not in KINDS]
    for kind in KINDS:
        mine = [c for c in comments if c["kind"] == kind]
        if not mine:
            continue
        lines += [f"## {heads[kind]}", ""]
        entries = _unique(c["entry"] for c in sorted(mine, key=lambda c: c["entry"].lower()))
        for entry in entries:
            if kind != "general":
                lines += [f"### {entry}", ""]
            for c in sorted((c for c in mine if c["entry"] == entry), key=lambda c: c["timestamp"]):
                lines.append(f"- **{c['reviewer'] or '(no name)'}**, {c['timestamp'][:10]} "
                             f"(page {c['page_version']}): {' '.join(c['comment'].split())}")
                if kind == "general":
                    continue
                if (kind, entry) not in now:
                    lines.append(f"  - ⚑ No longer in the files. As the page showed it: {c['entry_text_shown']}")
                elif now[(kind, entry)] != c["entry_text_shown"]:
                    lines.append(f"  - ⚑ Changed since that page. Then: {c['entry_text_shown']}")
                    lines.append(f"  - Now: {now[(kind, entry)]}")
            lines.append("")
    if unknown:
        lines += ["## Comments of an unknown kind", ""]
        lines += [f"- **{c['reviewer'] or '(no name)'}** ({c['file']}), kind '{c['kind']}', entry '{c['entry']}': "
                  f"{' '.join(c['comment'].split())}" for c in unknown] + [""]
    return "\n".join(lines)


def read_and_summarize(paths, out_dir: Path = OUT_DIR, schema_path: Path = SCHEMA_PATH,
                       mapping_path: Path = MAPPING_PATH) -> tuple:
    """(the summary's path, its text)."""
    files = comment_files(paths)
    comments, problems = read_comments(files)
    text = summary(comments, entry_texts(schema_path, mapping_path), files, problems, fingerprint(schema_path),
                   fingerprint(mapping_path))
    out = Path(out_dir) / f"comments_{dt.datetime.now():%Y-%m-%d_%H%M%S}.md"
    write_text(out, text)
    return out, text


def main() -> None:
    parser = argparse.ArgumentParser(prog="py helpers/review_page.py",
                                     description="Write a read-only review page of the ground truth schema and the "
                                                 "translation table, or read the comments reviewers sent back.")
    parser.add_argument("--read", nargs="*", metavar="FOLDER_OR_FILE",
                        help="read comment files (default: the folder annotations/reviews) and write a summary")
    args = parser.parse_args()
    if args.read is None:
        out = generate()
        print(f"Wrote {out.relative_to(ROOT).as_posix()}: send this one file to the reviewers.")
        return
    paths = args.read or [REVIEWS_DIR]
    missing = [p for p in paths if not Path(p).exists()]
    if missing:
        sys.exit(f"Not found: {', '.join(map(str, missing))}. Put the comment files reviewers sent you in "
                 f"{REVIEWS_DIR.relative_to(ROOT).as_posix()}/ (or name the files or folder after --read).")
    out, text = read_and_summarize(paths)
    print(text)
    print(f"\nWrote {out.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
