"""
common/schema_io.py -- reads a schema, in either of its two shapes, and
writes one out for a model to read.

A schema's content is always the same three things: entity classes and
predicates, each with a one-line definition, and patterns. It comes in two
shapes:

1. JSON, like 040's the_schema.json (read by 060 by default):

    {"entity_classes": [{"name": "Instrument", "definition": "A device that takes measurements."}, …],
     "predicates":     [{"name": "ABOARD", "definition": "Is carried on."}, …],
     "patterns":       [{"pattern": ["Instrument", "ABOARD", "Spacecraft"]}, …]}

   Only "name" is required in each entry ("definition" is strongly
   advised: the model reads it); "patterns" may be missing. Anything else
   (040's support, maintainers, texts, examples, deferred, made) is ignored.

2. Text, like the hand-built schema
   (annotations/schema_derived_from_manual_annotation.txt) and the additions
   file (annotations/schema_additions.txt):

    CLASSES
    -------
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

   A schema entry is a line starting with its name, followed by two or more
   spaces and its definition. An indented line under a predicate lists the
   pairs of entity classes (subject -> object) it has been used with,
   separated by ";"; each pair is a pattern. An indented line starting
   "source:" under any entry says where the idea for it came from (used by
   the additions file). Lines starting with # are comments.

Several steps read it: 040 compares the induced schema with the hand-built
one; 050 shows the hand-built one to the model and checks every drafted row
against it (as does the annotation tool); 060 extracts with 040's schema, or
another given with --schema, plus the additions; 070 builds the ground truth
vocabulary from the hand-built one and the ground truth.

    from common.schema_io import read_schema, schema_text
    schema = read_schema(path)          # either shape, by the file's suffix
    schema["entity_classes"]  {"Instrument": "a device that takes measurements", …}
    schema["predicates"]      {"ABOARD": "is carried on", …}
    schema["patterns"]        [("Instrument", "ABOARD", "Spacecraft"), …]
    schema["sources"]         {"entity_classes": {name: source}, "predicates": {…}}  (text shape only)
    schema["unread"]          ["line 12: …"]: lines of a section that are neither an entry, a
                              source nor patterns, e.g. prose, or a repeated entry (the first
                              is kept) and the lines under it (text shape only)
    schema_text(schema)       the text shape, for a prompt
    additions_text(header, entries)       the additions file, written by the annotation tool
    ground_truth_source_problem(source, parts)   why an addition's source isn't fair, or None

read_hand_schema(path) is read_schema for the hand-built text file.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ENTRY = re.compile(r"^(\S+) {2,}(\S.*)$")         # "Name  description"
PAIR = re.compile(r"^\s*(\S+)\s*->\s*(\S+)\s*$")   # "Subject -> Object"


def _empty() -> dict:
    return {"entity_classes": {}, "predicates": {}, "patterns": [],
            "sources": {"entity_classes": {}, "predicates": {}}, "unread": []}


def _read_text(path) -> dict:
    schema = _empty()
    sections = {"CLASSES": "entity_classes", "PREDICATES": "predicates"}
    section, entry_name = None, None
    for number, line in enumerate(Path(path).read_text(encoding="utf-8-sig").splitlines(), 1):
        head = line.strip()
        if head in sections:
            section, entry_name = sections[head], None
            continue
        if not head or head.startswith("#") or set(head) == {"-"} or section is None:
            continue
        entry = ENTRY.match(line)
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
        # explanation under PREDICATES), or a mistake, e.g. a name with a
        # space in it. Kept, so a reader that expects no prose can say so.
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
            raise ValueError(f"{where}: \"{kind}\" must be a list of {{\"name\", \"definition\"}} entries")
        for i, item in enumerate(items):
            name = item.get("name") if isinstance(item, dict) else None
            if not isinstance(name, str) or not name.strip():
                raise ValueError(f"{where}: {kind} entry {i} has no \"name\"")
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
    lines = ["CLASSES", "-------"]
    lines += [f"{name.ljust(width)}{d}".rstrip() for name, d in schema["entity_classes"].items()]
    lines += ["", "PREDICATES", "----------",
              "Each entry reads subject -> object, with the class pairs it is used with.", ""]
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
    tuning part: a name learned from a held-out record would let the schema
    see the final exam. parts is {pool position: "tuning" | "held-out"}
    (030's splits.json). Shared by step 060 (which leaves such an addition
    out) and the annotation tool (which refuses to save it)."""
    if "ground truth" not in source.lower():
        return None
    positions = [int(n) for n in re.findall(r"#(\d+)", source)]
    if not positions:
        return "says ground truth but names no record (write: ground truth tuning #12)"
    if not re.search(r"\btuning\b", source.lower()):
        return "names ground truth records but doesn't say tuning (write: ground truth tuning #12)"
    unknown = [p for p in positions if p not in parts]
    held = [p for p in positions if parts.get(p) == "held-out"]
    if unknown:
        return "names " + ", ".join(f"#{p}" for p in unknown) + ", not a pool position"
    if held:
        return "comes from held-out record(s) " + ", ".join(f"#{p}" for p in held)
    return None


def additions_header(path) -> str:
    """The comments at the top of the additions file (everything before its
    CLASSES line), kept as they are when the tool rewrites the entries."""
    text = Path(path).read_text(encoding="utf-8-sig") if Path(path).exists() else ""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.strip() == "CLASSES":
            return "\n".join(lines[:i]).rstrip() + "\n"
    return text.rstrip() + "\n" if text.strip() else ""


def additions_text(header: str, entries: list) -> str:
    """The additions file: header, then the entries in the text shape.
    entries: [{"kind": "entity class" | "predicate", "name", "definition",
    "source", "patterns": [[subject class, object class], ...]}]."""
    width = max([len(e["name"]) for e in entries] + [16]) + 2
    pad = " " * width

    def block(kind):
        out = []
        for e in (e for e in entries if e["kind"] == kind):
            out.append(f"{e['name'].ljust(width)}{e['definition']}".rstrip())
            if kind == "predicate" and e.get("patterns"):
                out.append(pad + "; ".join(f"{s_} -> {o_}" for s_, o_ in e["patterns"]))
            out.append(f"{pad}source: {e['source']}")
        return out

    lines = ([header.rstrip(), ""] if header.strip() else []) + ["CLASSES", "-------"] + block("entity class") \
        + ["", "PREDICATES", "----------"] + block("predicate")
    return "\n".join(lines) + "\n"
