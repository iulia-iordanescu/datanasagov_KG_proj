"""
common/common_helpers/schema_io.py -- reads a schema, in either of its two shapes, and
writes one out for a model to read.

A schema's content is always the same three things: entity classes and
predicates, each with a one-line definition, and patterns. It comes in two
shapes:

1. JSON, like 040's the_schema.json (read by 060 by default):

    {"entity_classes": [{"component_class": "Instrument", "definition": "A device that takes measurements."}, …],
     "predicates":     [{"component_class": "ABOARD", "definition": "Is carried on."}, …],
     "patterns":       [{"pattern": ["Instrument", "ABOARD", "Spacecraft"]}, …]}

   Only "component_class" is required in each entry ("definition" is strongly
   advised: the model reads it); "patterns" may be missing. Anything else
   (040's support, maintainers, texts, examples, deferred, made) is ignored.

2. Text, like the hand-built schema
   (annotations/schema_derived_from_manual_annotation.txt) and the additions
   file (annotations/schema_additions.txt):

    ENTITY CLASSES
    --------------
    Instrument        a device that takes measurements
    …

    PREDICATES
    ----------
    (a few lines of explanation, indented or not)

    ABOARD               is carried on
                         Instrument -> Spacecraft
    HAS_TIME_SPAN        covers the period
                         Dataset -> TimeSpan; MissionPhase -> TimeSpan
                         source: mentor, 2026-10-01

    PATTERNS
    --------
    Instrument ABOARD Mission
                         source: mentor, 2026-10-01

   An entity class or a predicate is a line starting with the component
   class, followed by two or more spaces and its definition. An indented
   line under a predicate lists the pairs of entity classes (subject ->
   object) it has been used with, separated by ";"; each pair is a pattern.
   A pattern can also stand on its own, in the PATTERNS section: subject
   class, predicate and object class on one line (used by the additions
   file, to add a pattern to a predicate the schema already has). An
   indented line starting "source:" under any entry (entity class,
   predicate or pattern) says where the idea for it came from (used by the
   additions file, and by the component classes the annotation tool adds to
   the hand-built schema). Lines starting with # are comments.

Several steps read it: 040 compares the induced schema with the hand-built
one; 050 shows the hand-built one to the model and checks every drafted row
against it (as does the annotation tool); 060 extracts with 040's schema, or
another given with --schema, plus the additions; 070 builds the ground truth
vocabulary from the hand-built one and the ground truth.

    from common.schema_io import read_schema, schema_text
    schema = read_schema(path)          # either shape, by the file's suffix
    schema["entity_classes"]  {"Instrument": "a device that takes measurements", …}
    schema["predicates"]      {"ABOARD": "is carried on", …}
    schema["patterns"]        [("Instrument", "ABOARD", "Spacecraft"), …]: every pattern, under a
                              predicate or in the PATTERNS section
    schema["pattern_entries"] the patterns of the PATTERNS section only (text shape only)
    schema["sources"]         {"entity_classes": {entity class: source}, "predicates": {…},
                              "patterns": {"Instrument ABOARD Mission": source}}  (text shape only)
    schema["unread"]          ["line 12: …"]: lines of a section that are neither an entry, a
                              source nor patterns, e.g. prose, or a repeated entry (the first
                              is kept) and the lines under it (text shape only)
    schema_text(schema)       the text shape, for a prompt
    additions_text(header, entries)       the additions file, written by the annotation tool
    ground_truth_source_problem(source, parts)   why an addition's source isn't fair, or None
    add_to_hand_schema(path, kind, name, definition, patterns, source)   one entry added (the annotation tool)
    add_pattern_to_hand_schema(path, predicate, subject_class, object_class)   one pattern added (same)

read_hand_schema(path) is read_schema for the hand-built text file.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

from common.triples_io import component_class_key

ENTRY = re.compile(r"^(\S+) {2,}(\S.*)$")         # "Instrument  definition"
PAIR = re.compile(r"^\s*(\S+)\s*->\s*(\S+)\s*$")   # "Subject -> Object"
PATTERN_LINE = re.compile(r"^(\S+)\s+(\S+)\s+(\S+)$")   # "Instrument ABOARD Mission", in a PATTERNS section
#: The text shape's section headings ("CLASSES" is the older heading of the
#: entity classes, still read).
SECTIONS = {"ENTITY CLASSES": "entity_classes", "CLASSES": "entity_classes", "PREDICATES": "predicates",
            "PATTERNS": "patterns"}


def _empty() -> dict:
    return {"entity_classes": {}, "predicates": {}, "patterns": [], "pattern_entries": [],
            "sources": {"entity_classes": {}, "predicates": {}, "patterns": {}}, "unread": []}


def pattern_key(pattern) -> str:
    """How a pattern is written in a PATTERNS section, and keyed in "sources"."""
    return " ".join(pattern)


def _read_text(path) -> dict:
    schema = _empty()
    sections = SECTIONS
    section, entry_name = None, None
    for number, line in enumerate(Path(path).read_text(encoding="utf-8-sig").splitlines(), 1):
        head = line.strip()
        if head in sections:
            section, entry_name = sections[head], None
            continue
        if not head or head.startswith("#") or set(head) == {"-"} or section is None:
            continue
        if section == "patterns" and not line[:1].isspace():
            triple = PATTERN_LINE.match(head)
            if triple and pattern_key(triple.groups()) in map(pattern_key, schema["pattern_entries"]):
                schema["unread"].append(f"line {number}: {head} (repeats an earlier entry; the first is kept)")
                entry_name = None
                continue
            if triple:
                schema["patterns"].append(triple.groups())
                schema["pattern_entries"].append(triple.groups())
                entry_name = pattern_key(triple.groups())
                continue
        entry = ENTRY.match(line) if section != "patterns" else None
        if entry:
            name, definition = entry.groups()
            if name in schema[section]:            # a repeat: the first entry is kept
                schema["unread"].append(f"line {number}: {head} (repeats an earlier entry; the first is kept)")
                entry_name = None
                continue
            schema[section][name] = definition.strip()
            entry_name = name
            continue
        if entry_name and line[:1].isspace():
            if head.lower().startswith("source:"):
                schema["sources"][section][entry_name] = head[len("source:"):].strip()
                continue
            if section == "predicates":
                pairs = [PAIR.match(p) for p in head.split(";")]
                if pairs and all(pairs):
                    schema["patterns"] += [(s, entry_name, o) for s, o in (p.groups() for p in pairs)]
                    continue
        # Anything else is not an entry: prose (the hand-built schema's
        # explanation under PREDICATES), or a mistake, e.g. a component class
        # with a space in it. Kept, so a reader that expects no prose can say so.
        schema["unread"].append(f"line {number}: {head}")
    return schema


def _read_json(path) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    where = Path(path).name
    if not isinstance(data, dict):
        raise ValueError(f"{where}: a JSON schema must be an object with entity_classes and predicates")
    schema = _empty()
    for kind in ("entity_classes", "predicates"):
        items = data.get(kind)
        if not isinstance(items, list):
            raise ValueError(f"{where}: \"{kind}\" must be a list of {{\"component_class\", \"definition\"}} entries")
        for i, item in enumerate(items):
            name = item.get("component_class") if isinstance(item, dict) else None
            if not isinstance(name, str) or not name.strip():
                raise ValueError(f"{where}: {kind} entry {i} has no \"component_class\"")
            definition = item.get("definition")
            schema[kind][name.strip()] = definition.strip() if isinstance(definition, str) else ""
    for i, item in enumerate(data.get("patterns") or []):
        triple = item.get("pattern") if isinstance(item, dict) else item
        if not (isinstance(triple, list) and len(triple) == 3 and all(isinstance(x, str) for x in triple)):
            raise ValueError(f"{where}: patterns entry {i} must be [subject class, predicate, object class]")
        schema["patterns"].append(tuple(x.strip() for x in triple))
    return schema


def read_schema(path) -> dict:
    """Either shape (above), chosen by the file's suffix: .json, else text."""
    return _read_json(path) if Path(path).suffix.lower() == ".json" else _read_text(path)


def read_hand_schema(path) -> dict:
    return _read_text(path)


def schema_text(schema: dict) -> str:
    """The schema in the text shape, for a model to read: every entity class
    and predicate with its definition, and each predicate's patterns."""
    width = max((len(n) for kind in ("entity_classes", "predicates") for n in schema[kind]), default=0) + 2
    lines = ["ENTITY CLASSES", "--------------"]
    lines += [f"{name.ljust(width)}{d}".rstrip() for name, d in schema["entity_classes"].items()]
    lines += ["", "PREDICATES", "----------",
              "Each entry reads subject -> object, with the entity class pairs it is used with.", ""]
    by_predicate = {}
    for s_, p_, o_ in schema["patterns"]:
        by_predicate.setdefault(p_, []).append(f"{s_} -> {o_}")
    for name, d in schema["predicates"].items():
        lines.append(f"{name.ljust(width)}{d}".rstrip())
        if by_predicate.get(name):
            lines.append(" " * width + "; ".join(by_predicate[name]))
    return "\n".join(lines)


# --------------------------------------------------------------------------
# the additions file (annotations/schema_additions.txt)
# --------------------------------------------------------------------------

def ground_truth_source_problem(source: str, parts: dict) -> str | None:
    """Why an addition whose source mentions the ground truth isn't fair to
    use, or None. Such a source must say "tuning" and name its records by
    pool position ("ground truth tuning #12, #15"), every one of them in the
    tuning part: a component class learned from a held-out record would let held-out
    records influence the schema, and the held-out numbers would no longer
    measure records the pipeline was never adjusted to. parts is {pool position: "tuning" | "held-out"}
    (030's splits.json). Shared by step 060 (which leaves such an addition
    out) and the annotation tool (which refuses to save it)."""
    if not re.search(r"ground[\s_-]*truth", source.lower()):    # any spelling: "ground-truth" too
        return None
    positions = [int(n) for n in re.findall(r"#(\d+)", source)]
    if not positions:
        return "says ground truth but names no record (write: ground truth tuning #12)"
    held = [p for p in positions if parts.get(p) == "held-out"]
    if held:
        return "comes from held-out record(s) " + ", ".join(f"#{p}" for p in held)
    if not re.search(r"\btuning\b", source.lower()):
        return "names ground truth records but doesn't say tuning (write: ground truth tuning #12)"
    unknown = [p for p in positions if p not in parts]
    if unknown:
        return "names " + ", ".join(f"#{p}" for p in unknown) + ", not a pool position"
    return None


def additions_header(path) -> str:
    """The comments at the top of the additions file (everything before its
    ENTITY CLASSES line), kept as they are when the tool rewrites the entries."""
    text = Path(path).read_text(encoding="utf-8-sig") if Path(path).exists() else ""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if SECTIONS.get(line.strip()) == "entity_classes":
            return "\n".join(lines[:i]).rstrip() + "\n"
    return text.rstrip() + "\n" if text.strip() else ""


def additions_text(header: str, entries: list) -> str:
    """The additions file: header, then the entries in the text shape.
    entries: [{"entry_type": "entity class" | "predicate", "component_class",
    "definition", "source", "patterns": [[subject class, object class], ...]}
    and {"entry_type": "pattern", "subject_class", "predicate",
    "object_class", "source"}]."""
    width = max([len(e["component_class"]) for e in entries if e["entry_type"] != "pattern"] + [16]) + 2
    pad = " " * width

    def block(entry_type):
        out = []
        for e in (e for e in entries if e["entry_type"] == entry_type):
            if entry_type == "pattern":
                out.append(pattern_key((e["subject_class"], e["predicate"], e["object_class"])))
            else:
                out.append(f"{e['component_class'].ljust(width)}{e['definition']}".rstrip())
            if entry_type == "predicate" and e.get("patterns"):
                out.append(pad + "; ".join(f"{s_} -> {o_}" for s_, o_ in e["patterns"]))
            out.append(f"{pad}source: {e['source']}")
        return out

    lines = ([header.rstrip(), ""] if header.strip() else []) + ["ENTITY CLASSES", "--------------"] + block("entity class") \
        + ["", "PREDICATES", "----------"] + block("predicate") + ["", "PATTERNS", "--------"] + block("pattern")
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------
# adding to the hand-built schema (the annotation tool)
# --------------------------------------------------------------------------
#
# Both functions change the file the same careful way (_edit_text): the
# lines are edited, the byte-order mark and line endings stay as they were,
# and the file is read back. If anything other than the one addition reads
# differently (an entry, definition, pattern, source or unread line), the
# file is put back byte for byte and a ValueError says so.

def _comparable(schema: dict) -> tuple:
    """A schema as read from text, in a form to compare: unread lines lose
    their line numbers, which shift when a line is added above them."""
    return (schema["entity_classes"], schema["predicates"], sorted(schema["patterns"]), schema["sources"],
            sorted(u.split(": ", 1)[-1] for u in schema["unread"]))


def _edit_text(path, edit, expected: dict, what: str) -> None:
    """edit(lines) -> lines; expected: the schema the file must read as after."""
    raw = Path(path).read_bytes()
    bom = "﻿" if raw.startswith(b"\xef\xbb\xbf") else ""
    newline = "\r\n" if b"\r\n" in raw else "\n"
    lines = edit(raw.decode("utf-8-sig").split(newline))
    tmp = Path(path).with_name(Path(path).name + ".part")
    tmp.write_bytes((bom + newline.join(lines)).encode("utf-8"))
    os.replace(tmp, path)
    if _comparable(_read_text(path)) != _comparable(expected):
        Path(path).write_bytes(raw)
        raise ValueError(f"adding {what} would have changed something else in {Path(path).name}; "
                         f"the file was left as it was")


def _section(lines: list, key: str, path) -> tuple:
    """(first line, end) of a section: from its heading to the next one."""
    heads = [i for i, line in enumerate(lines) if line.strip() in SECTIONS]
    start = next((i for i in heads if SECTIONS[lines[i].strip()] == key), None)
    if start is None:
        raise ValueError(f"{Path(path).name} has no {'ENTITY CLASSES' if key == 'entity_classes' else 'PREDICATES'} section")
    return start, next((i for i in heads if i > start), len(lines))


def _under(lines: list, i: int, end: int) -> int:
    """The last of the indented lines under the entry on line i (i if none).
    Blank lines between them are skipped, as the reader skips them."""
    j = i
    while j + 1 < end and (not lines[j + 1].strip() or lines[j + 1][:1].isspace()):
        j += 1
        if lines[j].strip():
            i = j
    return i


def _pairs_text(pairs) -> str:
    return "; ".join(f"{s} -> {o}" for s, o in pairs)


def add_to_hand_schema(path, kind: str, name: str, definition: str, patterns: list = (), source: str = "") -> None:
    """Add one entry to the hand-built schema (text shape): an entity class
    after the last entity class, a predicate after the last predicate and
    the lines under it, aligned like the entries of its section. A
    predicate's patterns, [(subject class, object class)], go on the line
    under it, then the source, if any, on a "source:" line. kind is "entity
    class" or "predicate"."""
    key = {"entity class": "entity_classes", "predicate": "predicates"}[kind]
    name, definition, source = str(name).strip(), " ".join(str(definition).split()), " ".join(str(source).split())
    patterns = [(str(s).strip(), str(o).strip()) for s, o in patterns] if key == "predicates" else []
    if not component_class_key(name) or any(c.isspace() for c in name) or name.startswith("#") or ";" in name or "->" in name:
        raise ValueError("the component class must be one word, with letters or digits, no spaces, and no ; or ->")
    if not definition:
        raise ValueError(f"{name} needs a one-line definition")
    if not all(PAIR.match(f"{s} -> {o}") for s, o in patterns):
        raise ValueError(f"{name}: each pattern is two entity classes, one word each")
    before = _read_text(path)
    same = [n for n in before[key] if component_class_key(n) == component_class_key(name)]
    if same:
        raise ValueError(f"{same[0]} is already in the hand-built schema")

    def edit(lines):
        start, end = _section(lines, key, path)
        entries = [i for i in range(start, end) if ENTRY.match(lines[i])]
        column = max(ENTRY.match(lines[entries[0]]).start(2) if entries else 18, len(name) + 2)
        new = [name.ljust(column) + definition] + ([" " * column + _pairs_text(patterns)] if patterns else []) \
            + ([" " * column + "source: " + source] if source else [])
        last = _under(lines, entries[-1], end) if entries else start + 1     # else under the heading's dashes
        return lines[:last + 1] + new + lines[last + 1:]

    expected = {**before, key: {**before[key], name: definition},
                "patterns": before["patterns"] + [(s, name, o) for s, o in patterns],
                "sources": {**before["sources"], key: {**before["sources"][key], **({name: source} if source else {})}}}
    _edit_text(path, edit, expected, name)


def add_pattern_to_hand_schema(path, predicate: str, subject_class: str, object_class: str) -> None:
    """Add one pattern to a predicate of the hand-built schema: to the end of
    its patterns line, or on a new line just under it if it has none. The
    predicate and both entity classes must be in the schema already, and are
    written in its spelling."""
    before = _read_text(path)
    name = next((n for n in before["predicates"] if component_class_key(n) == component_class_key(predicate)), None)
    if name is None:
        raise ValueError(f"{predicate} isn't a predicate of the hand-built schema: add it first")
    spelling = {component_class_key(n): n for n in before["entity_classes"]}
    missing = [c for c in (subject_class, object_class) if component_class_key(c) not in spelling]
    if missing:
        raise ValueError(f"{missing[0]} isn't an entity class of the hand-built schema: add it first")
    pair = (spelling[component_class_key(subject_class)], spelling[component_class_key(object_class)])
    if any(p == name and component_class_key(s) == component_class_key(pair[0]) and component_class_key(o) == component_class_key(pair[1])
           for s, p, o in before["patterns"]):
        raise ValueError(f"{pair[0]} -> {pair[1]} is already a pattern of {name}")

    def edit(lines):
        start, end = _section(lines, "predicates", path)
        i = next(j for j in range(start, end) if (m := ENTRY.match(lines[j])) and m.group(1) == name)
        for j in range(i + 1, _under(lines, i, end) + 1):
            if all(PAIR.match(p) for p in lines[j].split(";")):
                return lines[:j] + [lines[j].rstrip() + "; " + _pairs_text([pair])] + lines[j + 1:]
        indent = " " * ENTRY.match(lines[i]).start(2)
        return lines[:i + 1] + [indent + _pairs_text([pair])] + lines[i + 1:]

    _edit_text(path, edit, {**before, "patterns": before["patterns"] + [(pair[0], name, pair[1])]},
               f"{pair[0]} -> {pair[1]} to {name}")
