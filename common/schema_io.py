"""
common/schema_io.py -- reads the hand-built schema.

    annotations/schema_derived_from_manual_annotation.txt

written by a person while annotating ground truth. Several steps read it:
040 compares the induced schema with it, and 050, 060 and 070 will use it.
Its layout:

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

A schema entry is a line starting with its name, followed by two or more
spaces and its description. An indented line under a predicate lists the
pairs of entity classes (subject -> object) it has been used with, separated
by ";"; each pair is a pattern.

    from common.schema_io import read_hand_schema
    hand = read_hand_schema(path)
    hand["entity_classes"]  {"Instrument": "a device that takes measurements", …}
    hand["predicates"]      {"ABOARD": "is carried on", …}
    hand["patterns"]        [("Instrument", "ABOARD", "Spacecraft"), …]

The file's CLASSES section holds entity classes.
"""
from __future__ import annotations

import re
from pathlib import Path

ENTRY = re.compile(r"^(\S+) {2,}(\S.*)$")         # "Name  description"
PAIR = re.compile(r"^\s*(\S+)\s*->\s*(\S+)\s*$")   # "Subject -> Object"


def read_hand_schema(path) -> dict:
    schema = {"entity_classes": {}, "predicates": {}, "patterns": []}
    sections = {"CLASSES": "entity_classes", "PREDICATES": "predicates"}
    section, predicate = None, None
    for line in Path(path).read_text(encoding="utf-8-sig").splitlines():
        head = line.strip()
        if head in sections:
            section, predicate = sections[head], None
            continue
        if not head or set(head) == {"-"} or section is None:
            continue
        entry = ENTRY.match(line)
        if entry:
            name, description = entry.groups()
            schema[section][name] = description.strip()
            predicate = name if section == "predicates" else None
            continue
        if section == "predicates" and predicate and line[:1].isspace():
            pairs = [PAIR.match(p) for p in head.split(";")]
            if pairs and all(pairs):
                schema["patterns"] += [(s, predicate, o) for s, o in (p.groups() for p in pairs)]
        # Anything else (the explanation under PREDICATES) is prose, not an entry.
    return schema
