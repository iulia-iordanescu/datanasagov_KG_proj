"""
schema.py -- stage 2: the schema this run extracts with.

The schema input (040's the_schema.json by default, or any file given with
--schema, in either shape common/common_helpers/schema_io.py reads) plus the additions
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

An addition learned from the ground truth must come from TUNING records only
(a name learned from a held-out record would let the schema see the final
exam). Its source line says so and names the records by pool position, as the
annotation tool shows them:

    source: ground truth tuning #12, #15

The word "tuning" is required too, as a check on the person: any source
mentioning "ground truth" is checked against splits.json (030), and an
addition that doesn't say "tuning", names a held-out record, a position not
in the pool, or no record at all is left out, with a note shown before
paying.

The merged schema is what the model is shown, what every row is checked
against, and what is written to schema_used.json, so 070 (and 080, once
built) read exactly the schema this run used.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from common.audit import log, ref_path
from common.report import named
from common.schema_io import ground_truth_source_problem, read_schema, schema_text
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
    not_tuning: list = field(default_factory=list) # {"kind", "name", "source", "why"}: from ground truth, not tuning only


def _source(came_from: str | None) -> str:
    """Where a schema entry came from, for messages."""
    return "additions file" if came_from == "additions" else "schema input"


def load_schema(inputs: dict) -> Schema:
    base, extra = read_schema(inputs["schema"]), read_schema(inputs["additions"])
    result = Schema(files={"schema": ref_path(inputs["schema"]), "additions": ref_path(inputs["additions"])})
    if not base["entity_classes"] or not base["predicates"]:
        raise ValueError(f"{Path(inputs['schema']).name} has no entity classes or no predicates: "
                         f"is it a schema? (see 060_extract/060_extract.md for the shapes it can have)")

    splits = json.loads(Path(inputs["splits"]).read_text(encoding="utf-8"))
    parts = {r["position"]: r.get("part") for r in splits["ground_truth_candidates"]["records"]}

    merged = {kind: dict(base[kind]) for kind in KINDS}
    result.came_from = {kind: {name: "schema" for name in base[kind]} for kind in KINDS}
    result.sources = {kind: {} for kind in KINDS}
    no_source = []
    for kind in KINDS:
        have = {label_key(n): n for n in merged[kind]}
        for name, definition in extra[kind].items():
            why = ground_truth_source_problem(extra["sources"][kind].get(name, ""), parts)
            if why:
                result.not_tuning.append({"kind": kind, "name": name,
                                          "source": extra["sources"][kind][name], "why": why})
                continue
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

    if result.not_tuning:
        result.notes.append(f"{len(result.not_tuning)} addition(s) in {Path(inputs['additions']).name} say they come "
                            f"from the ground truth but don't show they come from tuning records only, so they are "
                            f"left out (a name from a held-out record would let the schema see the final exam): "
                            + named([f"{x['name']} (additions file; {x['why']})" for x in result.not_tuning], 5, "; ")
                            + ".")
    if result.left_out:
        result.notes.append(f"{len(result.left_out)} addition(s) in {Path(inputs['additions']).name} "
                            f"have a name already there (in the schema, or an earlier addition), so that entry "
                            f"is kept: "
                            + named([f"{x['name']} (additions file) = {x['kept']} "
                                     f"({_source(result.came_from[x['kind']].get(x['kept']))})"
                                     for x in result.left_out], 5, "; ") + ".")
    if extra["unread"]:
        result.notes.append(f"{len(extra['unread'])} line(s) of {Path(inputs['additions']).name} aren't read as an "
                            f"entry, a source or patterns (a name can't contain a space; two or more spaces go "
                            f"before the definition; patterns are \"Subject -> Object\" separated by \";\"): "
                            + named(extra["unread"], 5, "; ") + ".")
    if no_source:
        result.notes.append(f"{len(no_source)} addition(s) have no \"source:\" line saying where the idea "
                            f"came from: {named([f'{n} (additions file)' for n in no_source], 5, '; ')}.")
    undefined = [f"{n} ({_source(result.came_from[kind].get(n))})"
                 for kind in KINDS for n, d in merged[kind].items() if not d]
    if undefined:
        result.notes.append(f"{len(undefined)} schema entr{'ies have' if len(undefined) > 1 else 'y has'} "
                            f"no definition, so the model sees only the name: {named(undefined, 5, '; ')}.")
    unknown = sorted({x for s, p, o in patterns for x, kind in ((s, "entity_classes"), (p, "predicates"),
                                                              (o, "entity_classes"))
                      if x not in merged[kind]})
    if unknown:
        result.notes.append(f"{len(unknown)} name(s) used in patterns aren't entity classes or predicates "
                            f"of the schema: {named([f'{n} (in a pattern; not in the schema)' for n in unknown], 5, '; ')}.")
    added = sum(v == "additions" for kind in KINDS for v in result.came_from[kind].values())
    log.info(f"  schema: {len(merged['entity_classes'])} entity classes, {len(merged['predicates'])} "
             f"predicates, {len(patterns)} patterns ({added} added from {Path(inputs['additions']).name})")
    return result
