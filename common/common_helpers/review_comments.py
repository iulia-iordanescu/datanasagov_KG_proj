"""
common/common_helpers/review_comments.py -- the comments subject-matter experts send back from the review page
(helpers/review_page.py), read the same way by `py helpers/review_page.py --read` and by the annotation tool's
Reviewer comments view, so the two never disagree.

The entries a comment can be on, each with the one line the review page shows for it (schema_entries,
mapping_entries, entry_texts): the entity classes and predicates of annotations/ground_truth_schema.txt, the
rows of the translation table, annotations/component_class_mapping.csv, and the questions of
annotations/questions_for_experts.md (common/common_helpers/expert_questions.py; a question's entry is its id, Q1,
and its line its short title and the fingerprint of its words, so a comment on a question that changed since is
marked changed).

The files a reviewer's comments arrive in, all in annotations/reviews/ (kept on this computer only: .gitignore
keeps everything there but its README out of Git, since reviewers' names and words are theirs, and the
repository is public):

    comments_<reviewer>_<YYYY-MM-DD>.csv   the page's "Download my comments" (COMMENT_COLUMNS)
    <anything>.eml                         an email the page's "Email my comments" button wrote, saved whole
                                           (Gmail: "Download message"); a .csv attached to it is read too
    <anything>.txt                         the body of such an email, pasted

An email's body is in EMAIL_FORMAT (below), which survives what email clients do to plain text: lines wrapped
at any space, "> " quoting in a reply, a signature or a note before or after, lines merged back together.
An .eml file is read only when its From address is in ALLOWED_SENDER_DOMAINS (or a subdomain of one); every
other is skipped and reported, with its sender. A .txt or .csv file has no sender to check: its comments are
read, marked "sender not verified". A From address can be forged, so this is a filter, not proof.

Each reviewer's latest comment on each entry is kept (one who sends twice sends the same comments twice; an
edited comment replaces the older one), and each gets a state against the files as they are now
(comment_state, COMMENT_STATES). What each state means, the order they're decided in, and every problem a file
can have: helpers/review_page.md, *What --read reports* (the home).
"""
from __future__ import annotations

import csv
import email
import email.policy
import email.utils
import html
import io
import re
from pathlib import Path

from common.component_class_mapping import MAPPING_PATH, NONE, gtt_definition, gtt_definitions, is_stale_gtt, read_mapping
from common.expert_questions import QUESTIONS_PATH, read_questions
from common.schema_io import read_ground_truth_schema
from common.step import ANNOTATIONS_DIR

SCHEMA_PATH = ANNOTATIONS_DIR / "ground_truth_schema.txt"
REVIEWS_DIR = ANNOTATIONS_DIR / "reviews"
#: The columns of a reviewer's comment file, in order.
COMMENT_COLUMNS = ["reviewer", "page_version", "git_commit", "topic", "entry", "entry_text_shown", "comment", "timestamp"]
#: A comment's topic (docs/terminology.md, *topic*): what it is about, in the order the summary lists them.
TOPICS = ["general", "question", "entity class", "predicate", "translation row"]
#: What copies of the page made before 2026-10-26 called the topic, as a column and an email field: still read as
#: the topic, since reviewers may send comments written on such a copy.
LEGACY_TOPIC = "kind"
#: Each topic's heading, in the summary of --read and in the annotation tool's Reviewer comments view.
TOPIC_HEADINGS = {"general": "General comments",
                 "question": "Questions for experts (annotations/questions_for_experts.md)",
                 "entity class": "Entity classes (ground truth schema)",
                 "predicate": "Predicates (ground truth schema)",
                 "translation row": "Rows of the translation table"}
#: A comment's state against the files now (comment_state), in the order they're decided: general (a general
#: comment), gone (its entry is no longer in the files), changed (its entry reads differently from the page the
#: comment was written on), unchanged.
GENERAL_STATE, GONE, CHANGED, UNCHANGED = "general", "gone", "changed", "unchanged"
COMMENT_STATES = (GENERAL_STATE, GONE, CHANGED, UNCHANGED)
GENERAL = "(general)"
#: The email domains an .eml file's From address may have (or be a subdomain of: ndc.nasa.gov) to be read.
ALLOWED_SENDER_DOMAINS = ("nasa.gov",)
#: What a file without a checked sender (.txt, .csv) is marked with.
NOT_VERIFIED = "sender not verified"
#: The file types read, by suffix.
SUFFIXES = (".csv", ".eml", ".txt")

#: The email's body, as the review page writes it (helpers/review_page.html, emailParts):
EMAIL_FORMAT = """
REVIEW COMMENTS (format 1): please send this email as it is
[reviewer] Jane Smith
[page_version] review_2026-10-24_abc1234
[git_commit] abc1234
[sent] 2026-10-24T14:05:09-04:00
[part] 1 of 2
=== start of part 1 of 2 ===

=== comment ===
[topic] entity class
[entry] Instrument
[page_version] review_2026-10-24_abc1234
[git_commit] abc1234
[timestamp] 2026-10-24T10:00:00-04:00
[entry_text_shown] Instrument: a device that takes measurements
[comment] Also "sensor", maybe.
[comment] (a second line of the same comment)

=== end of part 1 of 2 ===
"""
# Each field is one line "[name] value"; a line that starts with none of the names continues the line before it
# (an email client wrapped it), joined with one space. A comment's own line breaks are its [comment] lines.
# Everything before the first line and after the last is ignored (a note, a signature); "> " quoting is taken off
# as deep as the first line's. A long send is split into parts at line ends (or, inside a long line, at a space):
# the parts of one send ([reviewer] and [sent] the same) are put back together in order, from any files.
HEADER = "REVIEW COMMENTS (format 1)"
HEADER_FIELDS = ("reviewer", "page_version", "git_commit", "sent", "part")
BLOCK_FIELDS = ("topic", "entry", "page_version", "git_commit", "timestamp", "entry_text_shown", "comment")
BLOCK = "=== comment ==="
# [kind] (LEGACY_TOPIC) is read as [topic]
_FIELD = re.compile(r"^\[(" + "|".join(sorted(set(HEADER_FIELDS + BLOCK_FIELDS + (LEGACY_TOPIC,)))) + r")\] ?(.*)$")
_START = re.compile(r"^=== start of part (\d+) of (\d+) ===$")
_END = re.compile(r"^=== end of part (\d+) of (\d+) ===$")
_SPLIT = re.compile(r"\s+(?=(?:\[(?:" + "|".join(sorted(set(HEADER_FIELDS + BLOCK_FIELDS + (LEGACY_TOPIC,)))) + r")\] |=== (?:comment|start of part|end of part) ))")


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
                     "gtt_now": gtt_definition(r, gtt), "line": r["_line"],
                     "stale_gtt": r["checked"] != "no" and r["component_class_in_gtt"] != NONE and is_stale_gtt(r, gtt),
                     "shown": shown})
    return rows


def entry_texts(schema_path: Path = SCHEMA_PATH, mapping_path: Path = MAPPING_PATH,
                questions_path: Path = QUESTIONS_PATH) -> dict:
    """{(topic, entry): shown} for every entry the page would show now (an entity class's or predicate's topic is its
    kind): what a comment is compared with. Every question counts, whatever its status. ValueError if the questions
    file isn't in its format."""
    s = schema_entries(schema_path)
    out = {(e["kind"], e["entry"]): e["shown"] for e in s["entity_classes"] + s["predicates"]}
    out.update({("translation row", r["entry"]): r["shown"] for r in mapping_entries(mapping_path, schema_path)})
    out.update({("question", q["id"]): q["shown"] for q in read_questions(questions_path)})
    return out


def comment_state(comment: dict, now: dict) -> str:
    """One of COMMENT_STATES, the first that applies, in their order: the comment's entry, now (entry_texts())
    against as the page showed it. Spaces don't count: an email client may have wrapped the line at one, or at a
    hyphen."""
    if comment["topic"] == "general":
        return GENERAL_STATE
    key = (comment["topic"], comment["entry"])
    if key not in now:
        return GONE
    squeeze = lambda s: re.sub(r"\s+", "", s or "")                                  # noqa: E731
    return UNCHANGED if squeeze(now[key]) == squeeze(comment["entry_text_shown"]) else CHANGED


# ------------------------------ the files ------------------------------------

def comment_files(paths) -> list:
    """The .csv, .eml and .txt files named, and those in each folder named (not its subfolders), sorted, without
    repeats."""
    files = []
    for p in map(Path, paths):
        files += sorted(f for f in p.iterdir() if f.is_file() and f.suffix.lower() in SUFFIXES) if p.is_dir() else [p]
    return _unique(f.resolve() for f in files)


def sender_allowed(address: str, domains=ALLOWED_SENDER_DOMAINS) -> bool:
    """Whether an email address's domain is one of `domains` or a subdomain of one: x@nasa.gov and x@ndc.nasa.gov
    are, x@notnasa.gov and x@nasa.gov.evil.com aren't."""
    domain = address.rpartition("@")[2].strip().strip(".").lower() if "@" in address else ""
    return bool(domain) and any(domain == d or domain.endswith("." + d) for d in (d.lower() for d in domains))


def _csv_rows(text: str, name: str) -> tuple:
    """(rows, problem or None) of a comment file's text. A file with the column kind (LEGACY_TOPIC) in place of topic
    is read with it as the topic."""
    reader = csv.DictReader(io.StringIO(text.lstrip("﻿"), newline=""))
    if reader.fieldnames and "topic" not in reader.fieldnames and LEGACY_TOPIC in reader.fieldnames:
        reader.fieldnames = ["topic" if c == LEGACY_TOPIC else c for c in reader.fieldnames]
    missing = [c for c in COMMENT_COLUMNS if c not in (reader.fieldnames or [])]
    if missing:
        return [], (f"{name}: lacks the column(s) {', '.join(missing)}, so it isn't a comment file the review page "
                    f"saved; skipped")
    return [{c: (r.get(c) or "").strip() for c in COMMENT_COLUMNS} for r in reader], None


def _html_text(markup: str) -> str:
    """An HTML email body as plain text: a line break for <br>, and at the end of each paragraph or block."""
    markup = re.sub(r"(?is)<(script|style)\b.*?</\1>", "", markup)
    markup = re.sub(r"(?i)<br\s*/?>|</(p|div|li|tr|h\d|blockquote)>", "\n", markup)
    return html.unescape(re.sub(r"<[^>]+>", "", markup))


def _unquote(line: str, depth: int) -> str:
    for _ in range(depth):
        m = re.match(r"^[ \t]*>[ \t]?", line)
        if not m:
            break
        line = line[m.end():]
    return line


def email_parts(text: str, name: str) -> list:
    """Every part in a text (one email's body, or several pasted together): [{"fields": header fields, "lines":
    the part's lines below its header, "ended": whether its end line was there, "file": name}]."""
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    parts, i = [], 0
    while i < len(lines):
        at = lines[i].find(HEADER)
        if at < 0 or lines[i][:at].replace(">", "").strip():
            i += 1
            continue
        depth = lines[i][:at].count(">")
        part = {"fields": {}, "lines": [], "ended": False, "file": name}
        body = [p.strip() for p in _SPLIT.split(lines[i][at + len(HEADER):])[1:]]   # fields merged onto its line
        i += 1
        while i < len(lines):
            line = _unquote(lines[i], depth)
            if HEADER in line:
                break
            i += 1
            for piece in _SPLIT.split(line.strip()):          # lines a client merged, apart again
                end = _END.match(piece.strip())
                if end:
                    part["ended"] = True
                    break
                body.append(piece.strip())
            if part["ended"]:
                break
        # the header's fields: from its first line to its start line (or, if that was lost, to the first block or
        # field of a block)
        last = None
        for j, line in enumerate(body):
            m = _FIELD.match(line)
            if _START.match(line) or line == BLOCK or (m and m.group(1) not in HEADER_FIELDS):
                part["lines"] = body[j + 1:] if _START.match(line) else body[j:]
                break
            if m:
                last = m.group(1)
                part["fields"][last] = m.group(2).strip()
            elif line and last:
                part["fields"][last] = (part["fields"][last] + " " + line).strip()
        parts.append(part)
    return parts


def _blocks(lines: list) -> tuple:
    """(comments, broken): the blocks of a send's lines, put back together; a gap (a missing part) breaks the block
    it falls in."""
    comments, broken, block, last = [], 0, None, None

    def close():
        nonlocal block
        if block is not None:
            if block.get("_broken") or not block.get("topic") or not block.get("entry"):
                return 1
            comments.append({"topic": block["topic"], "entry": block["entry"],
                             "page_version": block.get("page_version", ""), "git_commit": block.get("git_commit", ""),
                             "timestamp": block.get("timestamp", ""),
                             "entry_text_shown": block.get("entry_text_shown", ""),
                             "comment": "\n".join(block.get("comment", [])).strip()})
        return 0
    for line in lines:
        if line is None:                                     # a missing part
            if block is not None:
                block["_broken"] = True
            continue
        if line == BLOCK:
            broken += close()
            block, last = {}, None
            continue
        if block is None or not line:
            continue
        m = _FIELD.match(line)
        if m and (m.group(1) in BLOCK_FIELDS or m.group(1) == LEGACY_TOPIC):
            last = "topic" if m.group(1) == LEGACY_TOPIC else m.group(1)
            if last == "comment":
                block.setdefault("comment", []).append(m.group(2).rstrip())
            else:
                block[last] = m.group(2).strip()
        elif last == "comment":
            block["comment"][-1] = (block["comment"][-1] + " " + line).strip()
        elif last:
            block[last] = (block[last] + " " + line).strip()
    broken += close()
    return comments, broken


def sends(parts: list) -> tuple:
    """(rows, problems): the parts put together by send (reviewer and sent time), each in order of its part
    number, each row with the send's sender (NOT_VERIFIED unless every part came from the same checked address);
    a missing part is named, and the comment it cut is left out."""
    groups, problems, rows = {}, [], []
    for p in parts:
        f = p["fields"]
        m = re.match(r"^(\d+) of (\d+)$", f.get("part", "1 of 1"))
        k, n = (int(m.group(1)), int(m.group(2))) if m else (1, 1)
        key = (f.get("reviewer", "").lower(), f.get("sent", ""), n)
        groups.setdefault(key, {})[k] = p
    for (_, sent, n), got in groups.items():
        first = got[min(got)]
        who, files = first["fields"].get("reviewer", ""), _unique(p["file"] for p in got.values())
        senders = {p.get("sender", NOT_VERIFIED) for p in got.values()}     # verified only if every part is
        sender = next(iter(senders)) if len(senders) == 1 else NOT_VERIFIED
        missing = [k for k in range(1, n + 1) if k not in got]
        unended = [k for k, p in got.items() if not p["ended"]]
        lines = []
        for k in range(1, n + 1):
            if k in got and k not in unended:
                lines += got[k]["lines"]
            elif k in got:
                lines += got[k]["lines"] + [None]                      # cut short: its last block may be too
            else:
                lines.append(None)
        comments, broken = _blocks(lines)
        what = f"{who or '(no name)'}'s comments sent {sent or '(no time)'} ({', '.join(files)})"
        if missing:
            problems.append(f"{what}: part(s) {', '.join(map(str, missing))} of {n} missing, so the comments in them "
                            f"aren't read. Ask {who or 'the reviewer'} to press Email my comments again, or save the "
                            f"missing email(s) in annotations/reviews/ too.")
        if unended:
            problems.append(f"{what}: part(s) {', '.join(map(str, unended))} end without their line \"=== end of part "
                            f"... ===\" (cut short, or not copied whole), so a comment there may be incomplete.")
        if broken:
            problems.append(f"{what}: {broken} comment(s) incomplete (cut by a missing or cut-short part); left out.")
        for c in comments:
            rows.append({"reviewer": who, **c, "file": ", ".join(files), "sender": sender})
    return rows, problems


def _email(path: Path, domains) -> tuple:
    """(rows, problems, sender, body): an .eml file's .csv attachments, its body as plain text, and its From address;
    no rows and no body (and a problem) when that address isn't of an allowed domain."""
    msg = email.message_from_bytes(path.read_bytes(), policy=email.policy.default)
    sender = email.utils.parseaddr(str(msg.get("From", "")))[1]
    if not sender_allowed(sender, domains):
        return [], [f"{path.name}: sent from {sender or '(no From address)'}, not from an address of "
                    f"{' or '.join(domains)} (or a subdomain of it); skipped. If you know the sender, paste the "
                    f"email's text into a .txt file instead: it is read, marked \"{NOT_VERIFIED}\"."], sender, ""
    rows, problems, texts = [], [], []
    for part in msg.walk():
        if part.is_multipart():
            continue
        name, kind = part.get_filename() or "", part.get_content_type()
        if name.lower().endswith(".csv"):
            content = part.get_content()
            got, problem = _csv_rows(content if isinstance(content, str) else content.decode("utf-8-sig"),
                                     f"{path.name} ({name})")
            rows += [{**r, "file": f"{path.name} ({name})"} for r in got]
            problems += [problem] if problem else []
        elif kind in ("text/plain", "text/html") and not name:
            texts.append((kind, part.get_content()))
    plain = [t for k, t in texts if k == "text/plain"]
    return rows, problems, sender, "\n".join(plain) if plain else "\n".join(_html_text(t) for _, t in texts)


def read_comments(files, domains=ALLOWED_SENDER_DOMAINS) -> tuple:
    """(comments, problems). comments: every comment, keeping, for one reviewer and one entry, only the latest; each
    with COMMENT_COLUMNS, file, and sender (the From address of the .eml file it came in, or NOT_VERIFIED).
    problems: ["file: why it was skipped, or what is missing"]."""
    rows, problems, parts = [], [], []
    for f in map(Path, files):
        try:
            suffix = f.suffix.lower()
            if suffix == ".csv":
                got, problem = _csv_rows(f.read_text(encoding="utf-8-sig"), f.name)
                rows += [{**r, "file": f.name, "sender": NOT_VERIFIED} for r in got]
                problems += [problem] if problem else []
            elif suffix == ".eml":
                got, more, sender, body = _email(f, domains)
                rows += [{**r, "sender": sender} for r in got]
                problems += more
                found = [{**p, "sender": sender} for p in email_parts(body, f.name)]
                parts += found
                if body and not found and not got:
                    problems.append(f"{f.name}: an email from {sender} with no review comments in it (no line "
                                    f"\"{HEADER}\", and no .csv attached); skipped")
            else:
                found = email_parts(f.read_text(encoding="utf-8-sig", errors="replace"), f.name)
                parts += [{**p, "sender": NOT_VERIFIED} for p in found]
                if not found:
                    problems.append(f"{f.name}: no line \"{HEADER}\", so it isn't the text of an email the review "
                                    f"page wrote; skipped")
        except (OSError, UnicodeDecodeError, csv.Error) as e:
            problems.append(f"{f.name}: can't be read ({e}); skipped")
    got, more = sends(parts)
    rows += got
    problems += more
    latest = {}
    for r in rows:
        r = {**{c: (r.get(c) or "").strip() for c in COMMENT_COLUMNS}, "file": r["file"], "sender": r["sender"]}
        if not r["comment"]:
            continue
        key = (r["reviewer"].lower(), r["topic"], r["entry"])
        if key not in latest or r["timestamp"] >= latest[key]["timestamp"]:
            latest[key] = r
    return list(latest.values()), problems


def read_all(paths=(REVIEWS_DIR,), schema_path: Path = SCHEMA_PATH, mapping_path: Path = MAPPING_PATH,
             domains=ALLOWED_SENDER_DOMAINS, questions_path: Path = QUESTIONS_PATH) -> dict:
    """Everything a reader of the comments needs: {"files": [names], "problems": [...], "comments": [each with
    state (comment_state) and now (the entry as the files have it now, "" if gone)]}, sorted by topic, entry, time.
    A questions file not in its format is a problem (named), and the comments on questions then read as gone."""
    files = comment_files([p for p in paths if Path(p).exists()])
    comments, problems = read_comments(files, domains)
    try:
        now = entry_texts(schema_path, mapping_path, questions_path)
    except ValueError as e:
        problems.append(f"The questions can't be read, so each comment on a question is marked as no longer in the "
                        f"files: {e}")
        now = entry_texts(schema_path, mapping_path, questions_path=Path("(none)"))
    for c in comments:
        c["state"] = comment_state(c, now)
        c["now"] = now.get((c["topic"], c["entry"]), "")
    order = {k: i for i, k in enumerate(TOPICS)}
    comments.sort(key=lambda c: (order.get(c["topic"], len(TOPICS)), c["entry"].lower(), c["timestamp"]))
    return {"files": files, "problems": problems, "comments": comments}
