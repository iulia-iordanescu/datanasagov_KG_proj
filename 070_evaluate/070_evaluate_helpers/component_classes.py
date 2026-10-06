"""
component_classes.py -- stage 2: translate the component classes of the current
schema (the one 060 used) into the ground truth vocabulary.

The ground truth triples use the GROUND TRUTH VOCABULARY: the hand-built
schema's component classes, plus any a person coined while annotating
(common/common_helpers/ground_truth.vocabulary). 060 uses the component classes of the schema it was
given (040's by default): the current schema. Before comparing, each of the
current schema's entity classes and predicates is translated to a component class of
the ground truth vocabulary, through the table a person checks:

    annotations/component_class_mapping.csv
    kind,component_class_from_past_or_crt_schema,component_class_in_gtt,swap_subject_and_object,checked,definition_from_past_or_crt_schema
    entity class,Satellite,Spacecraft,no,yes,A craft that orbits a body.
    predicate,CARRIES,ABOARD,yes,yes,Has on board.   <- "A CARRIES B" is "B ABOARD A"
    entity class,Gadget,(none),no,yes,A small device. <- nothing in the ground truth means this

(columns: common/common_helpers/component_class_mapping.py)

For every component class of schema_used.json without a row:
  - a component class equal to one of the ground truth vocabulary (ignoring
    case and punctuation) gets a row at once, checked "same component class";
  - the others are proposed by the model (paid calls, after the usual
    confirmation), as rows with checked "no".
The new rows are ADDED at the end of the file; a row already there is never
changed or deleted. This is one of two narrow exceptions to "no step writes
into annotations/" (the other is held_out_looks.csv). After adding rows the
step stops, so the person can look at them; it evaluates only when every row it
needs is checked ("yes" or "same component class"), was checked against the
current schema's definition of its component class (else it is stale: a later
schema may mean something else by it), and names a component class of the
ground truth vocabulary or (none).

Every message names where each component class comes from: the current schema, the
ground truth vocabulary, or a row of the table (a past or the current
schema).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from common import llm
from common.cache import Cache, key
from common.files import append_csv
from common.ground_truth import vocabulary
from common.component_class_mapping import CHECKED, COLUMNS, KINDS, NONE, crt_definitions, is_stale, read_mapping, repeats
from common.prompt_files import fill, load
from common.report import named
from common.schema_io import read_hand_schema
from common.triples_io import component_class_key

PROMPTS_DIR = Path(__file__).resolve().parents[1] / "070_evaluate_prompts"   # 070_evaluate/070_evaluate_prompts/
PROMPT = load(PROMPTS_DIR / "map_component_classes.txt")
SUGGEST_PROMPT = load(PROMPTS_DIR / "suggest_component_classes.txt")


@dataclass
class Translation:
    entity: dict = field(default_factory=dict)      # {component_class_key(current schema's component class): gtt component class or None}
    predicate: dict = field(default_factory=dict)   # {component_class_key(current schema's component class): (gtt component class or None, reversed)}
    reachable: dict = field(default_factory=dict)   # {"entity class": {component_class_key(gtt component class)}, "predicate": {...}}
    gtt: dict = field(default_factory=dict)         # the ground truth vocabulary: {kind: {component class: definition}}
    rows_used: int = 0
    to_none: dict = field(default_factory=dict)     # {kind: [060's component classes whose row says (none)]}
    untranslated: dict = field(default_factory=dict)  # {kind: [ground truth vocabulary's component classes nothing translates to]}
    merged: dict = field(default_factory=dict)      # {kind: {gtt component class: [current schema's component classes that translate to it]}}, 2+ only
    outdated: list = field(default_factory=list)    # current schema's component classes whose row says (none), though the
                                                    # ground truth vocabulary has the same component class
    suggested: list = field(default_factory=list)   # {"kind", "component_class_from_past_or_crt_schema", "component_class_in_gtt"}: the
                                                    # model thinks a (none) row may now have a counterpart
    suggest_calls: int = 0
    reversed_used: int = 0
    calls: int = 0


def gtt_vocabulary(hand_schema_path, ground_truth) -> dict:
    """The ground truth vocabulary (common/common_helpers/ground_truth.py), by kind, each
    component class with its definition; a coined one has none, so it gets a note
    saying so, for the model."""
    vocab = vocabulary(read_hand_schema(hand_schema_path), ground_truth)
    return {kind: {name: definition or "(used in the ground truth; not in the hand-built schema)"
                   for name, definition in vocab[key].items()}
            for kind, key in (("entity class", "entity_classes"), ("predicate", "predicates"))}


def _propose(missing: list, gtt: dict, schema_used: dict, calls) -> tuple:
    """Rows proposed by the model for (kind, component class) pairs, and notes."""
    definitions = {("entity class", e["component_class"]): e.get("definition", "") for e in schema_used["entity_classes"]}
    definitions.update({("predicate", e["component_class"]): e.get("definition", "") for e in schema_used["predicates"]})
    asked = [{"kind": k, "component_class": n, "definition": definitions.get((k, n), "")} for k, n in missing]
    prompt = fill(PROMPT, ground_truth=json.dumps({k: [{"component_class": n, "definition": d} for n, d in v.items()]
                                                   for k, v in gtt.items()}, ensure_ascii=False, indent=0),
                  schema=json.dumps(asked, ensure_ascii=False, indent=0))
    cache = Cache(calls.cache_dir, "map_component_classes")
    k = key(prompt)
    reply = cache.get(k)
    made = 0
    if reply is None:
        calls.paid.start(f"  070 will ask the model to propose translations for {len(missing)} component class(es) of the "
                         f"current schema: 1 model call")
        reply = llm.call_llm_json(prompt)
        calls.paid.made_call()
        made = 1
        cache.put(k, reply)
    answers = {}
    for item in reply.get("mapping", []) if isinstance(reply, dict) else []:
        if isinstance(item, dict) and item.get("kind") in KINDS and isinstance(item.get("schema"), str):
            answers[(item["kind"], component_class_key(item["schema"]))] = item
    by_key = {k: {component_class_key(n): n for n in v} for k, v in gtt.items()}
    rows, strays = [], []
    for kind, name in missing:
        item = answers.get((kind, component_class_key(name)), {})
        mine = item.get("ground_truth") if isinstance(item.get("ground_truth"), str) else None
        gtt_name = by_key[kind].get(component_class_key(mine)) if mine else None
        if mine and gtt_name is None:
            strays.append(f"{name} (current schema) --> {mine} (not in the ground truth vocabulary)")
        rows.append({"kind": kind, "component_class_from_past_or_crt_schema": name, "component_class_in_gtt": gtt_name or NONE,
                     "definition_from_past_or_crt_schema": definitions.get((kind, name), ""),
                     "swap_subject_and_object": "yes" if (kind == "predicate" and item.get("reversed") is True) else "no",
                     "checked": "no"})
    notes = [f"The model proposed {len(strays)} component class(es) that aren't in the ground truth vocabulary, written as "
             f"(none): {named(strays, 5, '; ')}."] \
        if strays else []
    return rows, notes, made


def translate_component_classes(inputs: dict, evaluated, calls) -> Translation:
    path = Path(inputs["component_class_mapping"])
    translation = Translation(gtt=gtt_vocabulary(inputs["hand_schema"], evaluated.ground_truth))
    rows = read_mapping(path)
    repeated = repeats(rows)
    if repeated:
        raise SystemExit(f"{path.name} has {len(repeated)} component class(es) with more than one row: "
                         + named([f"{r['kind']} {r['component_class']} (a past or the current schema; lines "
                                  f"{', '.join(map(str, r['lines']))})" for r in repeated], 5, "; ")
                         + ". Keep one row per component class (py helpers/annotate.py, Translation table, can delete the extra "
                           "ones), then run 070 again.")
    have = {(r["kind"], component_class_key(r["component_class_from_past_or_crt_schema"])): r for r in rows}
    bad_kind = [r["component_class_from_past_or_crt_schema"] for r in rows if r["kind"] not in KINDS]
    if bad_kind:
        raise SystemExit(f"{path.name}: kind must be 'entity class' or 'predicate' for: "
                         f"{named([f'{n} (a past or the current schema)' for n in bad_kind], 5, '; ')}.")

    needed = [("entity class", e["component_class"]) for e in evaluated.schema_used["entity_classes"]] + \
             [("predicate", e["component_class"]) for e in evaluated.schema_used["predicates"]]
    gtt_key = {k: {component_class_key(n): n for n in v} for k, v in translation.gtt.items()}
    now = crt_definitions(evaluated.schema_used)
    same, missing = [], []
    handled = set(have)                     # a component class spelled two ways in the schema gets one row
    for kind, name in needed:
        if (kind, component_class_key(name)) in handled:
            continue
        handled.add((kind, component_class_key(name)))
        mine = gtt_key[kind].get(component_class_key(name))
        if mine:
            same.append({"kind": kind, "component_class_from_past_or_crt_schema": name, "component_class_in_gtt": mine, "swap_subject_and_object": "no",
                         "checked": "same component class",
                         "definition_from_past_or_crt_schema": now[kind].get(component_class_key(name), "")})
        else:
            missing.append((kind, name))
    proposed, notes = [], []
    if missing:
        proposed, notes, translation.calls = _propose(missing, translation.gtt, evaluated.schema_used, calls)
    if same or proposed:
        append_csv(path, COLUMNS, same + proposed)
        raise SystemExit(f"Added {len(same) + len(proposed)} row(s) to {path.name} for component classes of the current "
                         f"schema: {len(same)} with the same component class in the ground truth vocabulary (nothing to "
                         f"check), {len(proposed)} proposed by the model (checked = no): "
                         + named([f"{r['component_class_from_past_or_crt_schema']} (current schema) --> {r['component_class_in_gtt']} "
                                  f"(ground truth vocabulary)" for r in proposed], 5, "; ")
                         + ". Check those rows (py helpers/annotate.py, Translation table), then run 070 again. "
                         + " ".join(notes))

    unchecked, stale, unknown = [], [], []
    for kind, name in needed:
        r = have[(kind, component_class_key(name))]
        if r["checked"].lower() not in CHECKED:
            unchecked.append(name)
        elif is_stale(r, now):
            stale.append(name)
        elif r["component_class_in_gtt"] != NONE and component_class_key(r["component_class_in_gtt"]) not in gtt_key[kind]:
            unknown.append(f"{name} (current schema) --> {r['component_class_in_gtt']} (not in the ground truth vocabulary)")
    if unchecked:
        raise SystemExit(f"{len(unchecked)} row(s) of {path.name} still need checking (py helpers/annotate.py, "
                         f"Translation table): {named([f'{n} (current schema)' for n in unchecked], 5, '; ')}. "
                         f"Evaluation waits until all are checked.")
    if stale:
        raise SystemExit(f"{len(stale)} checked row(s) of {path.name} were checked when the current schema defined "
                         f"the component class differently, so they may no longer be right: "
                         f"{named([f'{n} (current schema)' for n in stale], 5, '; ')}. Check them again "
                         f"(py helpers/annotate.py, Translation table, shows both definitions), then run 070 again.")
    if unknown:
        raise SystemExit(f"{len(unknown)} checked row(s) of {path.name} translate to a component class that isn't in the "
                         f"ground truth vocabulary (a typo, or one since renamed): {named(unknown, 5, '; ')}. "
                         f"Choose a component class of the ground truth vocabulary, or (none).")

    translation.reachable = {"entity class": set(), "predicate": set()}
    for kind, name in needed:
        r = have[(kind, component_class_key(name))]
        mine = None if r["component_class_in_gtt"] == NONE else gtt_key[kind][component_class_key(r["component_class_in_gtt"])]
        if kind == "entity class":
            translation.entity[component_class_key(name)] = mine
        else:
            flipped = r["swap_subject_and_object"].lower() == "yes"
            translation.predicate[component_class_key(name)] = (mine, flipped)
            translation.reversed_used += flipped
        if mine:
            translation.reachable[kind].add(component_class_key(mine))
    translation.rows_used = len(needed)
    # A row checked as (none) before the same component class joined the ground
    # truth vocabulary is almost surely out of date. Warned about (not a stop: (none)
    # may still be right if the ground truth's component class means something else).
    translation.outdated = [f"{name} (current schema) --> (none), but {gtt_key[kind][component_class_key(name)]} (ground truth "
                      f"vocabulary) now exists" for kind, name in needed
                      if have[(kind, component_class_key(name))]["component_class_in_gtt"] == NONE and component_class_key(name) in gtt_key[kind]]
    # The ground truth vocabulary grows as you annotate: a row checked as (none) may since have
    # gained a counterpart. Both lists go in the report, so such a row can be
    # spotted and fixed (rows are never changed by the step).
    def translates_to_none(kind: str, name: str) -> bool:
        if kind == "entity class":
            return translation.entity.get(component_class_key(name), "") is None
        return translation.predicate.get(component_class_key(name), ("", False))[0] is None

    # Two or more of the current schema's component classes translated to one
    # component class of the ground truth vocabulary: evaluation can't
    # tell them apart (a mix-up between them costs nothing), so they're listed.
    def translated(kind: str, name: str):
        if kind == "entity class":
            return translation.entity.get(component_class_key(name))
        return translation.predicate.get(component_class_key(name), (None, False))[0]

    for kind in KINDS:
        into = {}
        for k, n in needed:
            if k == kind and translated(kind, n):
                into.setdefault(translated(kind, n), []).append(n)
        translation.merged[kind] = {mine: sorted(theirs) for mine, theirs in sorted(into.items()) if len(theirs) > 1}

    for kind in KINDS:
        translation.to_none[kind] = sorted(n for k, n in needed if k == kind and translates_to_none(kind, n))
        translation.untranslated[kind] = sorted(n for n in translation.gtt[kind] if component_class_key(n) not in translation.reachable[kind])
    translation.suggested, translation.suggest_calls = _suggest(translation, evaluated.schema_used, calls)
    return translation


def _suggest(translation: Translation, schema_used: dict, calls) -> tuple:
    """Rows that say (none) whose component class may since have gained a
    counterpart in the ground truth vocabulary: a DIFFERENT component class
    (the same one is caught by `outdated`, free). One model call, only when
    there are both (none) rows of the current schema and component classes of
    the ground truth vocabulary nothing translates
    to; the answer is cached by the lists asked about, so the same lists are
    never paid for twice. Rows are never changed: these are suggestions for
    the person (report warnings; the annotation tool reads them from
    metrics.json). Returns (suggestions, calls made)."""
    same = {kind: {component_class_key(n) for n in translation.gtt[kind]} for kind in KINDS}
    schema_side = [(k, n) for k in KINDS for n in translation.to_none[k] if component_class_key(n) not in same[k]]
    gtt_side = {k: [n for n in translation.untranslated[k]] for k in KINDS}
    kinds = {k for k, _ in schema_side if gtt_side[k]}
    schema_side = [(k, n) for k, n in schema_side if k in kinds]
    if not schema_side:
        return [], 0
    now = crt_definitions(schema_used)
    prompt = fill(SUGGEST_PROMPT,
                  ground_truth=json.dumps({k: [{"component_class": n, "definition": translation.gtt[k][n]} for n in gtt_side[k]]
                                           for k in kinds}, ensure_ascii=False, indent=0),
                  schema=json.dumps([{"kind": k, "component_class": n, "definition": now[k].get(component_class_key(n), "")}
                                     for k, n in schema_side], ensure_ascii=False, indent=0))
    cache = Cache(calls.cache_dir, "suggest_component_classes")
    k = key(prompt)
    reply = cache.get(k)
    made = 0
    if reply is None:
        calls.paid.start(f"  070 will ask the model whether {len(schema_side)} component class(es) of the current schema "
                         f"translated to (none) now have a counterpart in the ground truth vocabulary: 1 model call")
        reply = llm.call_llm_json(prompt)
        calls.paid.made_call()
        made = 1
        cache.put(k, reply)
    asked = {(kind, component_class_key(n)): n for kind, n in schema_side}
    offered = {kind: {component_class_key(n): n for n in gtt_side[kind]} for kind in kinds}
    out = []
    for item in reply.get("suggestions", []) if isinstance(reply, dict) else []:
        if not isinstance(item, dict) or item.get("kind") not in kinds:
            continue
        kind = item["kind"]
        crt = asked.get((kind, component_class_key(item.get("schema"))))
        gtt = offered[kind].get(component_class_key(item.get("ground_truth")))
        if crt and gtt:                                   # only component classes that were asked about
            out.append({"kind": kind, "component_class_from_past_or_crt_schema": crt, "component_class_in_gtt": gtt})
    return out, made
