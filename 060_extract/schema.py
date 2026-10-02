"""
schema.py -- stage 2: the schema this run extracts with.

The schema input (040's the_schema.json by default, or any file given with
--schema, in either shape common/schema_io.py reads) plus the additions
(annotations/schema_additions.txt): entity classes and predicates a person
added, e.g. on a mentor's advice. They are merged into one schema, and each
entry remembers where it came from: "schema" (the schema input) or
"additions". An addition whose name the schema (or an earlier addition)
already has, ignoring case and punctuation, is left out (the entry already
there is kept). Pattern names are written in the merged schema's spelling,
compared the same loose way, so a left-out addition's patterns still apply
to the entry kept. A left-out addition, a line of the additions file that
isn't read, an addition without a "source:" line, an entry without a
definition and a pattern name the schema doesn't have become notes shown
before paying.

The merged schema is what the model is shown, what every row is checked
against, and what is written to schema_used.json, so 070 (and 080, once
built) read exactly the schema this run used.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from common.audit import log, ref_path
from common.report import named
from common.schema_io import read_schema, schema_text
from common.triples_io import label_key
from common.validate import SchemaNames

KINDS = ("entity_classes", "predicates")


@dataclass
class Schema:
    content: dict = field(default_factory=dict)    # as common/schema_io reads it, merged
    came_from: dict = field(default_factory=dict)  # {kind: {name or pattern: "schema" | "additions"}}
    sources: dict = field(default_factory=dict)    # {kind: {name: its source line}} for additions
    text: str = ""                                 # as the model sees it
    names: object = None                           # common.validate.SchemaNames
    files: dict = field(default_factory=dict)      # {"schema": path, "additions": path}
    notes: list = field(default_factory=list)      # shown before paying, and in the report
    left_out: list = field(default_factory=list)   # {"kind", "name", "kept"}: additions whose name is already there


def load_schema(inputs: dict) -> Schema:
    base, extra = read_schema(inputs["schema"]), read_schema(inputs["additions"])
    result = Schema(files={"schema": ref_path(inputs["schema"]), "additions": ref_path(inputs["additions"])})
    if not base["entity_classes"] or not base["predicates"]:
        raise ValueError(f"{Path(inputs['schema']).name} has no entity classes or no predicates: "
                         f"is it a schema? (see instructions/060_extract.md for the shapes it can have)")

    merged = {kind: dict(base[kind]) for kind in KINDS}
    result.came_from = {kind: {name: "schema" for name in base[kind]} for kind in KINDS}
    result.sources = {kind: {} for kind in KINDS}
    no_source = []
    for kind in KINDS:
        have = {label_key(n): n for n in merged[kind]}
        for name, definition in extra[kind].items():
            if label_key(name) in have:
                result.left_out.append({"kind": kind, "name": name, "kept": have[label_key(name)]})
                continue
            have[label_key(name)] = name
            merged[kind][name] = definition
            result.came_from[kind][name] = "additions"
            source = extra["sources"][kind].get(name)
            if source:
                result.sources[kind][name] = source
            else:
                no_source.append(name)
    spelling = {kind: {label_key(n): n for n in merged[kind]} for kind in KINDS}

    def spelled(pattern: tuple) -> tuple:
        return tuple(spelling[kind].get(label_key(x), x)
                     for x, kind in zip(pattern, ("entity_classes", "predicates", "entity_classes")))

    in_base = {spelled(p) for p in base["patterns"]}
    patterns = list(dict.fromkeys(spelled(p) for p in base["patterns"] + extra["patterns"]))
    merged["patterns"] = patterns
    result.came_from["patterns"] = {p: "schema" if p in in_base else "additions" for p in patterns}
    result.content = merged
    result.text = schema_text(merged)
    result.names = SchemaNames(merged)

    if result.left_out:
        result.notes.append(f"{len(result.left_out)} addition(s) in {Path(inputs['additions']).name} "
                            f"have a name already there (in the schema, or an earlier addition), so that entry "
                            f"is kept: "
                            + named([x["name"] for x in result.left_out]) + ".")
    if extra["unread"]:
        result.notes.append(f"{len(extra['unread'])} line(s) of {Path(inputs['additions']).name} aren't read as an "
                            f"entry, a source or patterns (a name can't contain a space; two or more spaces go "
                            f"before the definition; patterns are \"Subject -> Object\" separated by \";\"): "
                            + named(extra["unread"], 5, "; ") + ".")
    if no_source:
        result.notes.append(f"{len(no_source)} addition(s) have no \"source:\" line saying where the idea "
                            f"came from: {named(no_source)}.")
    undefined = [n for kind in KINDS for n, d in merged[kind].items() if not d]
    if undefined:
        result.notes.append(f"{len(undefined)} schema entr{'ies have' if len(undefined) > 1 else 'y has'} "
                            f"no definition, so the model sees only the name: {named(undefined)}.")
    unknown = sorted({x for s, p, o in patterns for x, kind in ((s, "entity_classes"), (p, "predicates"),
                                                              (o, "entity_classes"))
                      if x not in merged[kind]})
    if unknown:
        result.notes.append(f"{len(unknown)} name(s) used in patterns aren't entity classes or predicates "
                            f"of the schema: {named(unknown)}.")
    added = sum(v == "additions" for kind in KINDS for v in result.came_from[kind].values())
    log.info(f"  schema: {len(merged['entity_classes'])} entity classes, {len(merged['predicates'])} "
             f"predicates, {len(patterns)} patterns ({added} added from {Path(inputs['additions']).name})")
    return result
