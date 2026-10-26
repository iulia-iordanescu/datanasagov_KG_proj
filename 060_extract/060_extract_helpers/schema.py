"""
schema.py -- stage 2: the schema this run extracts with.

The schema file (the induced schema, 040's the_schema.json, by default, or any
file given with --schema, in either shape common/common_helpers/schema_io.py reads) plus the additions
(annotations/schema_additions.txt): entity classes, predicates, and patterns a
person added, e.g. on a mentor's advice (a pattern for a predicate the
schema already has goes in the file's PATTERNS section). They are merged into one schema, and each
entry remembers where it came from: "schema" (the schema file) or
"additions". A schema entry of the additions file that the schema (or an
earlier entry of that file) already has, ignoring case and punctuation, is
left out (the entry already there is kept). Patterns are written in the merged
schema's spelling, compared the same loose way, so a left-out entry's patterns
still apply to the entry kept. A left-out entry, a line of the additions file
that isn't read, an entry of that file without a "source:" line, an entry without a
definition and a component class in a pattern that the schema doesn't
have become notes shown
before paying.

A schema entry of the additions file learned from the ground truth must come
from TUNING records only
(a component class learned from a held-out record would let the schema see the final
exam). Its source line says so and names the records by pool position, as the
annotation tool shows them:

    source: ground truth tuning #12, #15

The word "tuning" is required too, as a check on the person: any source
mentioning "ground truth" is checked against splits.json (030), and an
entry that doesn't say "tuning", names a held-out record, a position not
in the pool, or no record at all is left out, with a note shown before
paying. The patterns written under such a predicate are left out with it;
a pattern of the PATTERNS section is checked by its own source line.

The schema file's own entries are never left out, but one whose "source:"
line fails the same check (e.g. a component class the annotation tool added to the
ground truth schema from a held-out record) becomes a note shown before
paying.

The merged schema is what the model is shown, what every row is checked
against, and what is written to schema_used.json, so 070 (and 080, once
built) read exactly the schema this run used. schema_used.json also says which
records the schema was learned from (learned_from, below), so 070 can find the
twins (docs/terminology.md): evaluated records with the same title, the same
`notes`, or both as one of them.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from common.audit import log, ref_path
from common.ground_truth import GROUND_TRUTH_SCHEMA, GROUND_TRUTH_SCHEMA_FROM, read_pool
from common.report import named
from common.schema_io import ANY, ground_truth_source_problem, pattern_key, read_schema, schema_text
from common.step import repo_path
from common.stop import Stop
from common.triples_io import KIND_OF_KEY, component_class_key
from common.validate import SchemaEntries

KINDS = tuple(KIND_OF_KEY)                  # the schema's keys: ("entity_classes", "predicates")
#: entry_type, as every output file writes it (docs/terminology.md, *schema entry*).
ENTRY_TYPE = {**KIND_OF_KEY, "patterns": "pattern"}


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
    learned_from: dict = field(default_factory=dict)  # the records the schema was learned from (learned_from, below)

#: 040's file of the texts it learned from, written beside its schema (040_induce_schema/040_induce_schema_helpers/moves.py).
EVIDENCE_NAME = "induction_evidence.json"


def _made(path: Path) -> dict:
    """A JSON file's "made" block (the run that wrote it), or {}."""
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("made") or {}
    except (OSError, ValueError, AttributeError):
        return {}


def learned_from(inputs: dict, base: dict, result: Schema, pool: list) -> dict:
    """The records the schema was learned from, for 070's twins (docs/terminology.md): {"known", "ids", "how":
    [sentences]}.
      - the induced schema: the texts the same run of 040 learned from, in its induction_evidence.json, beside the schema;
      - the ground truth schema: pool positions 0 to GROUND_TRUTH_SCHEMA_FROM - 1, which it was written while annotating;
      - either way, also the pool records an entry's source line names ("source: ground truth tuning #12").
    Any other schema file: not known ("known": False), unless an induction_evidence.json of the same run is beside it."""
    path = Path(inputs["schema"])
    by_position = {r["position"]: r["id"] for r in pool}
    ids, how = set(), []
    if path.resolve() == GROUND_TRUTH_SCHEMA.resolve():
        ids |= {by_position[p] for p in range(GROUND_TRUTH_SCHEMA_FROM) if p in by_position}
        how.append(f"the ground truth schema was written while annotating pool positions 0 to {GROUND_TRUTH_SCHEMA_FROM - 1}")
    else:
        evidence = path.with_name(EVIDENCE_NAME)
        run = _made(path).get("run_id")
        if not (run and evidence.is_file() and _made(evidence).get("run_id") == run):
            return {"known": False, "ids": [],
                    "how": [f"{repo_path(path)} has no {EVIDENCE_NAME} beside it written by the same run, so which "
                            f"texts the schema was learned from isn't known"]}
        texts = json.loads(evidence.read_text(encoding="utf-8")).get("texts", [])
        ids |= {t["id"] for t in texts}
        how.append(f"040's run {run} learned it from {len(texts)} texts ({repo_path(evidence)}, key texts)")
    named_positions = set()
    for sources in (base.get("sources", {}), result.sources):
        for of_kind in sources.values():
            for source in of_kind.values():
                if re.search(r"ground[\s_-]*truth", source.lower()):
                    named_positions |= {int(n) for n in re.findall(r"#(\d+)", source)}
    found = sorted(p for p in named_positions if p in by_position)
    if found:
        ids |= {by_position[p] for p in found}
        how.append("source lines of its entries name pool positions " + ", ".join(f"#{p}" for p in found))
    return {"known": True, "ids": sorted(ids), "how": how}


def _source(came_from: str | None) -> str:
    """Where a schema entry came from, for messages."""
    return "additions file" if came_from == "additions" else "schema file"


def load_schema(inputs: dict) -> Schema:
    base, extra = read_schema(inputs["schema"]), read_schema(inputs["additions"])
    result = Schema(files={"schema": ref_path(inputs["schema"]), "additions": ref_path(inputs["additions"])})
    if not base["entity_classes"] or not base["predicates"]:
        raise Stop(f"{repo_path(inputs['schema'])} has no entity classes or no predicates "
                   f"({len(base['entity_classes'])} entity classes, {len(base['predicates'])} predicates), so 060 "
                   f"can't extract with it. Check that it is a schema in one of the shapes in "
                   f"060_extract/060_extract.md (section The shape of a schema), or pass another with --schema, "
                   f"then run `py 060_extract/run.py` again.")

    pool = read_pool(inputs["splits"])
    parts = {r["position"]: r.get("part") for r in pool}

    merged = {kind: dict(base[kind]) for kind in KINDS}
    result.came_from = {kind: {name: "schema" for name in base[kind]} for kind in KINDS}
    result.sources = {kind: {} for kind in KINDS}
    no_source = []
    for kind in KINDS:
        have = {component_class_key(n): n for n in merged[kind]}
        for name, definition in extra[kind].items():
            why = ground_truth_source_problem(extra["sources"][kind].get(name, ""), parts)
            if why:
                result.not_tuning.append({"entry_type": ENTRY_TYPE[kind], "schema_entry": name,
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
    rejected = {component_class_key(x["schema_entry"]) for x in result.not_tuning if x["entry_type"] == "predicate"}
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
            result.not_tuning.append({"entry_type": "pattern", "schema_entry": pattern_key(q), "source": source,
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
    # The pins ("only:" lines, text shape only): the schema file's, then the additions file's, under the merged
    # schema's spelling, so a pin under a left-out entry still applies to the entry kept; a predicate left out for
    # not coming from tuning records takes its pins with it. Both files pinning one predicate: either's pairs fit.
    pinned = {}
    for source_schema, skip in ((base, set()), (extra, rejected)):
        for predicate, pins in source_schema.get("pinned", {}).items():
            if component_class_key(predicate) in skip:
                continue
            name = spelling["predicates"].get(component_class_key(predicate), predicate)
            for s, o in pins:
                pair = tuple(ANY if component_class_key(x) == ANY
                             else spelling["entity_classes"].get(component_class_key(x), x) for x in (s, o))
                if pair not in pinned.setdefault(name, []):
                    pinned[name].append(pair)
    merged["pinned"] = pinned
    result.content = merged
    result.text = schema_text(merged)
    result.schema_entries = SchemaEntries(merged)
    result.learned_from = learned_from(inputs, base, result, pool)

    schema_file, additions_file = repo_path(inputs["schema"]), repo_path(inputs["additions"])
    from_held_out = [f"{name} (schema file; {why})" for kind in KINDS + ("patterns",)
                     for name, source in base["sources"].get(kind, {}).items()
                     if (why := ground_truth_source_problem(source, parts))]
    if from_held_out:
        result.notes.append(f"Entries of {schema_file} whose source names ground truth records "
                            f"other than tuning ones ({len(from_held_out)}), e.g. component classes the annotation tool added "
                            f"from held-out records: " + named(from_held_out, 5, "; ") + ". They are kept (it's "
                            f"the schema you chose), but then evaluation's held-out numbers no longer measure "
                            f"records the pipeline was never adjusted to. Fine for tuning numbers; for held-out "
                            f"numbers, extract with a schema that didn't learn from held-out records: run "
                            f"`py 060_extract/run.py` without --schema (the induced schema).")
    if result.not_tuning:
        result.notes.append(f"{len(result.not_tuning)} schema entr(ies) of {additions_file} say they come "
                            f"from the ground truth but don't show they come from tuning records only, so they are "
                            f"left out (a schema entry learned from a held-out record would let held-out records influence the schema): "
                            + named([f"{x['schema_entry']} (additions file; {x['why']})" for x in result.not_tuning], 5, "; ")
                            + ". Take each out, or, if it really came from tuning records, list their pool positions "
                            "in its source line, e.g. `source: ground truth tuning #12`.")
    if result.left_out:
        result.notes.append(f"{len(result.left_out)} schema entr(ies) of {additions_file} "
                            f"are already there (in the schema file, or earlier in the same file, ignoring case and "
                            f"punctuation), so each is left out and the entry already there is used: "
                            + named([f"{x['component_class']} (additions file) = {x['kept']} "
                                     f"({_source(result.came_from[x['kind']].get(x['kept']))})"
                                     for x in result.left_out], 5, "; ") + f". Remove each from {additions_file}, "
                            f"or rename it if it means something else.")
    if extra["unread"]:
        result.notes.append(f"{len(extra['unread'])} line(s) of {additions_file} aren't read as an "
                            f"entry, a source, or patterns (an entity class or predicate can't contain a space; two or more spaces go "
                            f"before the definition; patterns under a predicate are \"Subject -> Object\" separated by \";\"; "
                            f"in the PATTERNS section, one pattern per line, \"Subject PREDICATE Object\"): "
                            + named(extra["unread"], 5, "; ") + ". Such a line adds nothing to the schema; fix "
                            "each in " + additions_file + ".")
    if no_source:
        result.notes.append(f"{len(no_source)} schema entr(ies) of {additions_file} have no \"source:\" line saying where the idea "
                            f"came from: {named([f'{n} (additions file)' for n in no_source], 5, '; ')}. They are "
                            f"used, but where they came from isn't recorded. Add a `source:` line under each in "
                            f"{additions_file}.")
    undefined = [f"{n} ({_source(result.came_from[kind].get(n))})"
                 for kind in KINDS for n, d in merged[kind].items() if not d]
    if undefined:
        result.notes.append(f"{len(undefined)} schema entr{'ies have' if len(undefined) > 1 else 'y has'} "
                            f"no definition, so the model sees only the entity class or predicate itself: {named(undefined, 5, '; ')}. "
                            f"Add a one-line definition to each, in {schema_file} (schema file) or "
                            f"{additions_file} (additions file).")
    pin_patterns = [(s, p, o) for p, pins in pinned.items() for s, o in pins]
    unknown = sorted({x for s, p, o in patterns + pin_patterns
                      for x, kind in ((s, "entity_classes"), (p, "predicates"), (o, "entity_classes"))
                      if x not in merged[kind] and not (kind == "entity_classes" and x == ANY)})
    if unknown:
        result.notes.append(f"{len(unknown)} component class(es) used in patterns or \"only:\" lines aren't in the schema: "
                            f"{named([f'{n} (in a pattern or an \"only:\" line; not in the schema)' for n in unknown], 5, '; ')}. "
                            f"An extracted triple using one is removed (component_class_not_in_schema) though "
                            f"the pattern or \"only:\" line allows it. Fix the pattern or line (often a typo), or add the missing entity class "
                            f"or predicate, in {schema_file} or {additions_file}.")
    added = sum(v == "additions" for kind in KINDS for v in result.came_from[kind].values())
    log.info(f"  schema: {len(merged['entity_classes'])} entity classes, {len(merged['predicates'])} "
             f"predicates, {len(patterns)} patterns ({added} added from {Path(inputs['additions']).name})")
    return result
