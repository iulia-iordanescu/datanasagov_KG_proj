"""
names.py -- stage 2: translate the names of the schema 060 used into the
ground truth's names.

The ground truth uses YOUR names: the hand-built schema's, and any a person
coined while annotating. 060 uses the names of the schema it was given
(040's by default). Before comparing, each of 060's entity classes and
predicates is translated to one of yours, through the table a person checks:

    annotations/name_mapping.csv
    kind,name_in_crt_schema,name_in_gtt,swap_subject_and_object,checked
    entity class,Satellite,Spacecraft,no,yes
    predicate,CARRIES,ABOARD,yes,yes        <- "A CARRIES B" is "B ABOARD A"
    entity class,Gadget,(none),no,yes        <- nothing of yours means this

For every name of schema_used.json without a row:
  - a name equal to one of yours (ignoring case, spaces and punctuation)
    gets a row at once, checked "same name";
  - the others are proposed by the model (paid calls, after the usual
    confirmation), as rows with checked "no".
The new rows are ADDED at the end of the file; a row already there is never
changed or deleted. This is one of two narrow exceptions to "no step writes
into annotations/" (the other is held_out_looks.csv). After adding rows the
step stops, so the person can look at them; it scores only when every row it
needs is checked ("yes" or "same name") and names one of your names or
(none).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from common import llm
from common.cache import Cache, key
from common.files import append_csv
from common.ground_truth import vocabulary
from common.name_mapping import CHECKED, COLUMNS, KINDS, NONE, read_mapping
from common.prompt_files import fill, load
from common.report import named
from common.schema_io import read_hand_schema
from common.triples_io import label_key

PROMPT = load(Path(__file__).parent / "prompts" / "map_names.txt")


@dataclass
class Names:
    entity: dict = field(default_factory=dict)      # {label_key(schema name): your name or None}
    predicate: dict = field(default_factory=dict)   # {label_key(schema name): (your name or None, reversed)}
    reachable: dict = field(default_factory=dict)   # {"entity class": {label_key(yours)}, "predicate": {...}}
    yours: dict = field(default_factory=dict)       # {"entity class": {name: definition}, "predicate": {...}}
    rows_used: int = 0
    to_none: dict = field(default_factory=dict)     # {kind: [060's names whose row says (none)]}
    untranslated: dict = field(default_factory=dict)  # {kind: [your names no row translates to]}
    reversed_used: int = 0
    calls: int = 0


def your_vocabulary(hand_schema_path, ground_truth) -> dict:
    """Your names: the ground truth vocabulary (common/ground_truth.py), by
    kind, each with its definition; a coined name has none, so it gets a
    note saying so, for the model."""
    vocab = vocabulary(read_hand_schema(hand_schema_path), ground_truth)
    return {kind: {name: definition or "(used in the ground truth; not in the hand-built schema)"
                   for name, definition in vocab[key].items()}
            for kind, key in (("entity class", "entity_classes"), ("predicate", "predicates"))}


def _propose(missing: list, yours: dict, schema_used: dict, calls) -> tuple:
    """Rows proposed by the model for (kind, name) pairs, and notes."""
    definitions = {("entity class", e["name"]): e.get("definition", "") for e in schema_used["entity_classes"]}
    definitions.update({("predicate", e["name"]): e.get("definition", "") for e in schema_used["predicates"]})
    asked = [{"kind": k, "name": n, "definition": definitions.get((k, n), "")} for k, n in missing]
    prompt = fill(PROMPT, yours=json.dumps({k: [{"name": n, "definition": d} for n, d in v.items()]
                                            for k, v in yours.items()}, ensure_ascii=False, indent=0),
                  schema=json.dumps(asked, ensure_ascii=False, indent=0))
    cache = Cache(calls.cache_dir, "map_names")
    k = key(prompt)
    reply = cache.get(k)
    made = 0
    if reply is None:
        calls.paid.start(f"  070 will ask the model to propose translations for {len(missing)} name(s) of the "
                         f"schema 060 used: 1 model call")
        reply = llm.call_llm_json(prompt)
        calls.paid.made_call()
        made = 1
        cache.put(k, reply)
    answers = {}
    for item in reply.get("mapping", []) if isinstance(reply, dict) else []:
        if isinstance(item, dict) and item.get("kind") in KINDS and isinstance(item.get("schema"), str):
            answers[(item["kind"], label_key(item["schema"]))] = item
    by_key = {k: {label_key(n): n for n in v} for k, v in yours.items()}
    rows, strays = [], []
    for kind, name in missing:
        item = answers.get((kind, label_key(name)), {})
        mine = item.get("yours") if isinstance(item.get("yours"), str) else None
        gtt_name = by_key[kind].get(label_key(mine)) if mine else None
        if mine and gtt_name is None:
            strays.append(f"{name} → {mine}")
        rows.append({"kind": kind, "name_in_crt_schema": name, "name_in_gtt": gtt_name or NONE,
                     "swap_subject_and_object": "yes" if (kind == "predicate" and item.get("reversed") is True) else "no",
                     "checked": "no"})
    notes = [f"The model proposed {len(strays)} name(s) that aren't yours, written as (none): {named(strays)}."] \
        if strays else []
    return rows, notes, made


def translate_names(inputs: dict, scored, calls) -> Names:
    path = Path(inputs["name_mapping"])
    names = Names(yours=your_vocabulary(inputs["hand_schema"], scored.ground_truth))
    rows = read_mapping(path)
    have = {(r["kind"], label_key(r["name_in_crt_schema"])): r for r in rows}
    bad_kind = [r["name_in_crt_schema"] for r in rows if r["kind"] not in KINDS]
    if bad_kind:
        raise SystemExit(f"{path.name}: kind must be 'entity class' or 'predicate' for: {named(bad_kind)}.")

    needed = [("entity class", e["name"]) for e in scored.schema_used["entity_classes"]] + \
             [("predicate", e["name"]) for e in scored.schema_used["predicates"]]
    yours_key = {k: {label_key(n): n for n in v} for k, v in names.yours.items()}
    same, missing = [], []
    for kind, name in needed:
        if (kind, label_key(name)) in have:
            continue
        mine = yours_key[kind].get(label_key(name))
        if mine:
            same.append({"kind": kind, "name_in_crt_schema": name, "name_in_gtt": mine, "swap_subject_and_object": "no",
                         "checked": "same name"})
        else:
            missing.append((kind, name))
    proposed, notes = [], []
    if missing:
        proposed, notes, names.calls = _propose(missing, names.yours, scored.schema_used, calls)
    if same or proposed:
        append_csv(path, COLUMNS, same + proposed)
        raise SystemExit(f"Added {len(same) + len(proposed)} row(s) to {path.name}: {len(same)} with the same "
                         f"name as one of yours (nothing to check), {len(proposed)} proposed by the model "
                         f"(checked = no). Check those rows (fix name_in_gtt and swap_subject_and_object where wrong, then set "
                         f"checked to yes), then run 070 again. " + " ".join(notes))

    unchecked, unknown = [], []
    for kind, name in needed:
        r = have[(kind, label_key(name))]
        if r["checked"].lower() not in CHECKED:
            unchecked.append(name)
        elif r["name_in_gtt"] != NONE and label_key(r["name_in_gtt"]) not in yours_key[kind]:
            unknown.append(f"{name} → {r['name_in_gtt']}")
    if unchecked:
        raise SystemExit(f"{len(unchecked)} row(s) of {path.name} still need checking (set checked to yes once "
                         f"right): {named(unchecked)}. Scoring waits until all are checked.")
    if unknown:
        raise SystemExit(f"{len(unknown)} checked row(s) of {path.name} name something that isn't one of your "
                         f"names (a typo?): {named(unknown)}. Use one of your names, or (none).")

    names.reachable = {"entity class": set(), "predicate": set()}
    for kind, name in needed:
        r = have[(kind, label_key(name))]
        mine = None if r["name_in_gtt"] == NONE else yours_key[kind][label_key(r["name_in_gtt"])]
        if kind == "entity class":
            names.entity[label_key(name)] = mine
        else:
            flipped = r["swap_subject_and_object"].lower() == "yes"
            names.predicate[label_key(name)] = (mine, flipped)
            names.reversed_used += flipped
        if mine:
            names.reachable[kind].add(label_key(mine))
    names.rows_used = len(needed)
    # Your names grow as you annotate: a row checked as (none) may since have
    # gained a counterpart. Both lists go in the report, so such a row can be
    # spotted and fixed (rows are never changed by the step).
    def translates_to_none(kind: str, name: str) -> bool:
        if kind == "entity class":
            return names.entity.get(label_key(name), "") is None
        return names.predicate.get(label_key(name), ("", False))[0] is None

    for kind in KINDS:
        names.to_none[kind] = sorted(n for k, n in needed if k == kind and translates_to_none(kind, n))
        names.untranslated[kind] = sorted(n for n in names.yours[kind] if label_key(n) not in names.reachable[kind])
    return names
