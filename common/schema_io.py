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

An entry is a line starting with a name, followed by two or more spaces and
its description. An indented line under a predicate lists the class pairs
(subject -> object) it has been used with, separated by ";".

    from common.schema_io import read_hand_schema
    hand = read_hand_schema(path)
    hand["classes"]      {"Instrument": "a device that takes measurements", …}
    hand["predicates"]   {"ABOARD": "is carried on", …}
    hand["patterns"]     [("Instrument", "ABOARD", "Spacecraft"), …]
"""
from __future__ import annotations

import re
from pathlib import Path

ENTRY = re.compile(r"^(\S+) {2,}(\S.*)$")         # "Name  description"
PAIR = re.compile(r"^\s*(\S+)\s*->\s*(\S+)\s*$")   # "Subject -> Object"


def read_hand_schema(path) -> dict:
    schema = {"classes": {}, "predicates": {}, "patterns": []}
    section, predicate = None, None
    for line in Path(path).read_text(encoding="utf-8-sig").splitlines():
        head = line.strip()
        if head in ("CLASSES", "PREDICATES"):
            section, predicate = head.lower(), None
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
