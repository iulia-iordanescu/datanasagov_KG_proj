"""
check.py -- stage 7: build the schema from the evidence, and check what the
model wrote. Code only, no model.

The schema is built from stage 5's counts, never from the model's replies:

  - an entity class or predicate is IN the schema if its support reaches
    min_support and the model didn't call it too vague;
  - a pattern (entity class, predicate, entity class) is in the schema if
    its support reaches min_support and its two entity classes and its
    predicate are all in the schema;
  - every other schema entry found is DEFERRED, with its reason: support
    below min_support, too vague (with the model's reason), or a pattern
    through a schema entry that isn't in the schema.

What the model wrote is only the definitions. Checked here:
  - a schema entry in the schema with no definition gets MISSING_DEFINITION,
    and is listed (it stays in: its evidence doesn't depend on the words);
  - a schema entry named in a reply but not sent is ignored and listed
    (stage 6).

Every schema entry keeps its evidence (support, the texts, the maintainers)
and its origin: the records whose texts it was found in.

Adapted from verify_against_evidence() in archive/to_be_reshaped/best_induce_schema.py.
Stage 6 no longer merges or picks examples, so the checks that repaired
those (support bounds of merged entries, invented examples, restored
entries) are no longer needed: the schema can't contain anything the
evidence doesn't.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from common.audit import ORIGIN_FIELD, log, origin
from define import KINDS, WORD

MISSING_DEFINITION = "(no definition: the model didn't return one for this schema entry)"


@dataclass
class Schema:
    entity_classes: list = field(default_factory=list)
    predicates: list = field(default_factory=list)
    patterns: list = field(default_factory=list)
    deferred: list = field(default_factory=list)            # {DEFERRED_FIELDS…, "reason_code": a DEFERRED_REASONS key}
    missing_definitions: list = field(default_factory=list) # {"kind", "component_class"}
    single_maintainer: list = field(default_factory=list)   # {"kind", "component_class"}


def _origin(texts: list) -> list:
    return [origin("records", tid) for tid in texts]


#: Why a schema entry is deferred, each reason's code with its words in the report; each entry has one, the first
#: that applies, in this order (docs/terminology.md, *deferred*, their home): low support, then too vague
#: (entity classes and predicates) or a component class not in the schema (patterns).
LOW_SUPPORT, TOO_VAGUE, NOT_IN_SCHEMA = "low support", "too vague", "a component class not in the schema"
DEFERRED_REASONS = {LOW_SUPPORT: "support below min_support", TOO_VAGUE: "too vague",
                    NOT_IN_SCHEMA: "through a schema entry not in the schema"}
#: A deferred entry's fields as the_schema.json writes them ("reason": the reason in detail).
DEFERRED_FIELDS = ("entry_type", "schema_entry", "support", "reason")


def _deferred(entry_type: str, schema_entry: str, support: int, code: str, detail: str) -> dict:
    return {"entry_type": entry_type, "schema_entry": schema_entry, "support": support, "reason": detail,
            "reason_code": code}


def check_schema(counts, definitions, settings: dict) -> Schema:
    cut = settings["min_support"]
    schema = Schema()
    for kind in KINDS:
        vague = definitions.too_vague.get(kind, {})
        target = getattr(schema, kind)
        for e in getattr(counts, kind):
            if e["support"] < cut:
                schema.deferred.append(_deferred(WORD[kind], e["component_class"], e["support"], LOW_SUPPORT,
                                                 f"support {e['support']} < min_support {cut}"))
                continue
            if e["component_class"] in vague:
                schema.deferred.append(_deferred(WORD[kind], e["component_class"], e["support"], TOO_VAGUE,
                                                 f"too vague: {vague[e['component_class']]}"))
                continue
            definition = definitions.of.get(kind, {}).get(e["component_class"])
            if definition is None:
                definition = MISSING_DEFINITION
                schema.missing_definitions.append({"kind": WORD[kind], "component_class": e["component_class"]})
            row = {"component_class": e["component_class"], "definition": definition, "examples": e["examples"][:3]}
            row.update({"support": e["support"], "maintainers": e["maintainers"],
                        "texts": e["texts"], ORIGIN_FIELD: _origin(e["texts"])})
            target.append(row)
            if len(e["maintainers"]) == 1:
                schema.single_maintainer.append({"kind": WORD[kind], "component_class": e["component_class"]})

    kept_classes = {c["component_class"] for c in schema.entity_classes}
    kept_predicates = {p["component_class"] for p in schema.predicates}
    for e in counts.patterns:
        s, p, o = e["pattern"]
        if e["support"] < cut:
            code, reason = LOW_SUPPORT, f"support {e['support']} < min_support {cut}"
        elif not (s in kept_classes and o in kept_classes and p in kept_predicates):
            missing = [x for x, kept in ((s, kept_classes), (p, kept_predicates), (o, kept_classes)) if x not in kept]
            code, reason = NOT_IN_SCHEMA, f"{missing[0]} is not in the schema"
        else:
            schema.patterns.append({"pattern": e["pattern"], "support": e["support"],
                                    "maintainers": e["maintainers"], "texts": e["texts"],
                                    ORIGIN_FIELD: _origin(e["texts"])})
            continue
        schema.deferred.append(_deferred("pattern", " ".join(e["pattern"]), e["support"], code, reason))
    log.info(f"  schema: {len(schema.entity_classes):,} entity classes, {len(schema.predicates):,} "
             f"predicates, {len(schema.patterns):,} patterns; {len(schema.deferred):,} deferred")
    return schema
