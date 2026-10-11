"""
schema.py -- stage 2: the schema this run extracts with.

The schema input (040's the_schema.json by default, or any file given with
--schema, in either shape common/common_helpers/schema_io.py reads) plus the additions
(annotations/schema_additions.txt): entity classes, predicates and patterns a
person added, e.g. on a mentor's advice (a pattern for a predicate the
schema already has goes in the file's PATTERNS section). They are merged into one schema, and each
entry remembers where it came from: "schema" (the schema input) or
"additions". An addition the schema (or an earlier addition) already has,
ignoring case and punctuation, is left out (the entry already there is
kept). Patterns are written in the merged schema's spelling,
compared the same loose way, so a left-out addition's patterns still apply
to the entry kept. A left-out addition, a line of the additions file that
isn't read, an addition without a "source:" line, an entry without a
definition and a component class in a pattern that the schema doesn't
have become notes shown
before paying.

An addition learned from the ground truth must come from TUNING records only
(a component class learned from a held-out record would let the schema see the final
exam). Its source line says so and names the records by pool position, as the
annotation tool shows them:

    source: ground truth tuning #12, #15

The word "tuning" is required too, as a check on the person: any source
mentioning "ground truth" is checked against splits.json (030), and an
addition that doesn't say "tuning", names a held-out record, a position not
in the pool, or no record at all is left out, with a note shown before
paying. The patterns written under such a predicate are left out with it;
a pattern of the PATTERNS section is checked by its own source line.

The schema input's own entries are never left out, but one whose "source:"
line fails the same check (e.g. a component class the annotation tool added to the
hand-built schema from a held-out record) becomes a note shown before
paying.

The merged schema is what the model is shown, what every row is checked
against, and what is written to schema_used.json, so 070 (and 080, once
built) read exactly the schema this run used.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from common.audit import log, ref_path
from common.ground_truth import read_pool
from common.report import named
from common.schema_io import ground_truth_source_problem, pattern_key, read_schema, schema_text
from common.step import repo_path
from common.stop import Stop
from common.triples_io import component_class_key
from common.validate import SchemaEntries

KINDS = ("entity_classes", "predicates")


@dataclass
class Schema:
    content: dict = field(default_factory=dict)    # as common/common_helpers/schema_io.py reads it, merged
    came_from: dict = field(default_factory=dict)  # {kind: {component class or pattern: "schema" | "additions"}}
    sources: dict = field(default_factory=dict)    # {kind: {component class: its source line}}, "patterns": {pattern: …}, for additions
    text: str = ""                                 # as the model sees it
    schema_entries: object = None  # common.validate.SchemaEntries
    files: dict = field(default_factory=dict)      # {"schema": path, "additions": path}
    notes: list = field(default_factory=list)      # shown before paying, and in the report
    left_out: list = field(default_factory=list)   # {"kind", "component_class", "kept"}: additions already there
    not_tuning: list = field(default_factory=list) # {"entry_type", "schema_entry", "source", "why"}: from ground truth, not tuning only


def _source(came_from: str | None) -> str:
    """Where a schema entry came from, for messages."""
    return "additions file" if came_from == "additions" else "schema input"


def load_schema(inputs: dict) -> Schema:
    base, extra = read_schema(inputs["schema"]), read_schema(inputs["additions"])
    result = Schema(files={"schema": ref_path(inputs["schema"]), "additions": ref_path(inputs["additions"])})
    if not base["entity_classes"] or not base["predicates"]:
        raise Stop(f"{repo_path(inputs['schema'])} has no entity classes or no predicates "
                   f"({len(base['entity_classes'])} entity classes, {len(base['predicates'])} predicates), so 060 "
                   f"can't extract with it. Check that it is a schema in one of the shapes in "
                   f"060_extract/060_extract.md (section The shape of a schema), or pass another with --schema, "
                   f"then run `py 060_extract/run.py` again.")

    parts = {r["position"]: r.get("part") for r in read_pool(inputs["splits"])}

    merged = {kind: dict(base[kind]) for kind in KINDS}
    result.came_from = {kind: {name: "schema" for name in base[kind]} for kind in KINDS}
    result.sources = {kind: {} for kind in KINDS}
    no_source = []
    for kind in KINDS:
        have = {component_class_key(n): n for n in merged[kind]}
        for name, definition in extra[kind].items():
            why = ground_truth_source_problem(extra["sources"][kind].get(name, ""), parts)
            if why:
                result.not_tuning.append({"entry_type": kind, "schema_entry": name,
                                          "source": extra["sources"][kind][name], "why": why})
                continue
            if component_class_key(name) in have:
                result.left_out.append({"kind": kind, "component_class": name, "kept": have[component_class_key(name)]})
                continue
            have[component_class_key(name)] = name
            merged[kind][name] = definition
            result.came_from[kind][name] = "additions"
            source = extra["sources"][kind].get(name)
            if source:
                result.sources[kind][name] = source
            else:
                no_source.append(name)
    spelling = {kind: {component_class_key(n): n for n in merged[kind]} for kind in KINDS}

    def spelled(pattern: tuple) -> tuple:
        return tuple(spelling[kind].get(component_class_key(x), x)
                     for x, kind in zip(pattern, ("entity_classes", "predicates", "entity_classes")))

    # The additions' patterns: those under a predicate share its source, so they
    # are left out with it; a pattern of the PATTERNS section has its own.
    result.sources["patterns"] = {}
    rejected = {component_class_key(x["schema_entry"]) for x in result.not_tuning if x["entry_type"] == "predicates"}
    standalone = {tuple(q) for q in extra.get("pattern_entries", [])}
    added_patterns = []
    for q in extra["patterns"]:
        if tuple(q) not in standalone:
            if component_class_key(q[1]) not in rejected:
                added_patterns.append(q)
            continue
        source = extra["sources"].get("patterns", {}).get(pattern_key(q), "")
        why = ground_truth_source_problem(source, parts)
        if why:
            result.not_tuning.append({"entry_type": "patterns", "schema_entry": pattern_key(q), "source": source,
                                      "why": why})
            continue
        added_patterns.append(q)
        if source:
            result.sources["patterns"][spelled(q)] = source
        else:
            no_source.append(pattern_key(q))
    in_base = {spelled(p) for p in base["patterns"]}
    patterns = list(dict.fromkeys(spelled(p) for p in base["patterns"] + added_patterns))
    merged["patterns"] = patterns
    result.came_from["patterns"] = {p: "schema" if p in in_base else "additions" for p in patterns}
    result.content = merged
    result.text = schema_text(merged)
    result.schema_entries = SchemaEntries(merged)

    schema_file, additions_file = repo_path(inputs["schema"]), repo_path(inputs["additions"])
    from_held_out = [f"{name} (schema input; {why})" for kind in KINDS for name, source in base["sources"][kind].items()
                     if (why := ground_truth_source_problem(source, parts))]
    if from_held_out:
        result.notes.append(f"Entries of {schema_file} whose source names ground truth records "
                            f"other than tuning ones ({len(from_held_out)}), e.g. component classes the annotation tool added "
                            f"from held-out records: " + named(from_held_out, 5, "; ") + ". They are kept (it's "
                            f"the schema you chose), but then evaluation's held-out numbers no longer measure "
                            f"records the pipeline was never adjusted to. Fine for tuning numbers; for held-out "
                            f"numbers, extract with a schema that didn't learn from held-out records: run "
                            f"`py 060_extract/run.py` without --schema (040's induced schema).")
    if result.not_tuning:
        result.notes.append(f"{len(result.not_tuning)} addition(s) in {additions_file} say they come "
                            f"from the ground truth but don't show they come from tuning records only, so they are "
                            f"left out (an addition from a held-out record would let held-out records influence the schema): "
                            + named([f"{x['schema_entry']} (additions file; {x['why']})" for x in result.not_tuning], 5, "; ")
                            + ". Take each out, or, if it really came from tuning records, list their pool positions "
                            "in its source line, e.g. `source: ground truth tuning #12`.")
    if result.left_out:
        result.notes.append(f"{len(result.left_out)} addition(s) in {additions_file} "
                            f"are already there (in the schema input, or an earlier addition, ignoring case and "
                            f"punctuation), so each is left out and the entry already there is used: "
                            + named([f"{x['component_class']} (additions file) = {x['kept']} "
                                     f"({_source(result.came_from[x['kind']].get(x['kept']))})"
                                     for x in result.left_out], 5, "; ") + f". Remove each from {additions_file}, "
                            f"or rename it if it means something else.")
    if extra["unread"]:
        result.notes.append(f"{len(extra['unread'])} line(s) of {additions_file} aren't read as an "
                            f"entry, a source or patterns (an entity class or predicate can't contain a space; two or more spaces go "
                            f"before the definition; patterns under a predicate are \"Subject -> Object\" separated by \";\"; "
                            f"in the PATTERNS section, one pattern per line, \"Subject PREDICATE Object\"): "
                            + named(extra["unread"], 5, "; ") + ". Such a line adds nothing to the schema; fix "
                            "each in " + additions_file + ".")
    if no_source:
        result.notes.append(f"{len(no_source)} addition(s) have no \"source:\" line saying where the idea "
                            f"came from: {named([f'{n} (additions file)' for n in no_source], 5, '; ')}. They are "
                            f"used, but where they came from isn't recorded. Add a `source:` line under each in "
                            f"{additions_file}.")
    undefined = [f"{n} ({_source(result.came_from[kind].get(n))})"
                 for kind in KINDS for n, d in merged[kind].items() if not d]
    if undefined:
        result.notes.append(f"{len(undefined)} schema entr{'ies have' if len(undefined) > 1 else 'y has'} "
                            f"no definition, so the model sees only the entity class or predicate itself: {named(undefined, 5, '; ')}. "
                            f"Add a one-line definition to each, in {schema_file} (schema input) or "
                            f"{additions_file} (additions file).")
    unknown = sorted({x for s, p, o in patterns for x, kind in ((s, "entity_classes"), (p, "predicates"),
                                                              (o, "entity_classes"))
                      if x not in merged[kind]})
    if unknown:
        result.notes.append(f"{len(unknown)} component class(es) used in patterns aren't in the schema: "
                            f"{named([f'{n} (in a pattern; not in the schema)' for n in unknown], 5, '; ')}. "
                            f"An extracted triple using one is removed (component_class_not_in_schema) though "
                            f"the pattern allows it. Fix the pattern (often a typo), or add the missing entity class "
                            f"or predicate, in {schema_file} or {additions_file}.")
    added = sum(v == "additions" for kind in KINDS for v in result.came_from[kind].values())
    log.info(f"  schema: {len(merged['entity_classes'])} entity classes, {len(merged['predicates'])} "
             f"predicates, {len(patterns)} patterns ({added} added from {Path(inputs['additions']).name})")
    return result
