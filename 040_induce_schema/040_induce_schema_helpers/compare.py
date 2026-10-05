"""
compare.py -- the induced schema beside the hand-built one, for the report.

The hand-built schema (annotations/schema_derived_from_manual_annotation.txt,
read by common/common_helpers/schema_io.py) was written by a person while annotating ground
truth. Putting the two side by side is a quick sanity check on what the data
taught the model: which entity classes, predicates and patterns both have,
which only the hand-built one has, and which only the induced one has.

It is not a metric. Component classes are matched when they are equal once
case, spaces, underscores and punctuation are ignored ("PhysicalQuantity" =
"Physical Quantity"); a concept named differently in the two ("Instrument", "Sensor")
counts as unmatched here. Measuring how much of the ground truth the induced
schema can express, across different component classes, is 070's job.
"""
from __future__ import annotations

from common.triples_io import label_key


def _side_by_side(hand: list, induced: list) -> dict:
    """{"both": [(hand-built spelling, induced spelling)], "only_hand": [...], "only_induced": [...]}"""
    by_norm = {label_key(n): n for n in induced}
    both, only_hand = [], []
    for name in hand:
        match = by_norm.get(label_key(name))
        (both.append((name, match)) if match else only_hand.append(name))
    matched = {label_key(h) for h, _ in both}
    return {"both": both, "only_hand": only_hand,
            "only_induced": [n for n in induced if label_key(n) not in matched]}


def compare(hand: dict, schema) -> dict:
    pattern = lambda p: " ".join(p)                       # noqa: E731
    return {
        "entity_classes": _side_by_side(list(hand["entity_classes"]), [c["component_class"] for c in schema.entity_classes]),
        "predicates": _side_by_side(list(hand["predicates"]), [p["component_class"] for p in schema.predicates]),
        "patterns": _side_by_side([pattern(p) for p in hand["patterns"]],
                                  [pattern(p["pattern"]) for p in schema.patterns]),
    }


def report_lines(comparison: dict, hand_path: str, show: int) -> list:
    lines = ["### Compared with the hand-built schema", "",
             f"`{hand_path}`, written while annotating ground truth. Component classes match when equal "
             f"ignoring case, spaces and punctuation; a concept named differently in the two "
             f"counts as unmatched. A sanity check, not a metric (070 evaluates the schema).", "",
             "| | In both | Only hand-built | Only induced |", "|---|---:|---:|---:|"]
    for kind in ("entity_classes", "predicates", "patterns"):
        c = comparison[kind]
        lines.append(f"| {kind.replace('_', ' ').capitalize()} | {len(c['both'])} | {len(c['only_hand'])} | "
                     f"{len(c['only_induced'])} |")
    lines.append("")
    for kind in ("entity_classes", "predicates", "patterns"):
        c = comparison[kind]
        what = kind.replace("_", " ").capitalize()
        lines.append(f"- **{what} in both:** "
                     + (", ".join(h if h == i else f"{h} = {i}" for h, i in c["both"]) or "none"))
        lines.append(f"- **{what} only in the hand-built schema:** "
                     + (", ".join(c["only_hand"]) or "none"))
        shown = c["only_induced"][:show]
        lines.append(f"- **{what} only in the induced schema:** "
                     + (", ".join(shown) or "none")
                     + (f" … ({len(c['only_induced']) - show:,} more)" if len(c["only_induced"]) > show else ""))
    lines.append("")
    return lines
