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

Adapted from verify_against_evidence() in to_be_reshaped/best_induce_schema.py.
Stage 6 no longer merges or picks examples, so the checks that repaired
those (support bounds of merged entries, invented examples, restored
entries) are no longer needed: the schema can't contain anything the
evidence doesn't.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from common.audit import ORIGIN_FIELD, log, origin
from define import KINDS

MISSING_DEFINITION = "(no definition: the model didn't return one for this schema entry)"


@dataclass
class Schema:
    entity_classes: list = field(default_factory=list)
    predicates: list = field(default_factory=list)
    patterns: list = field(default_factory=list)
    deferred: list = field(default_factory=list)            # {"kind", "name", "reason", "support"}
    missing_definitions: list = field(default_factory=list) # {"kind", "name"}
    single_maintainer: list = field(default_factory=list)   # {"kind", "name"}


def _origin(texts: list) -> list:
    return [origin("records", tid) for tid in texts]


def check_schema(counts, definitions, settings: dict) -> Schema:
    cut = settings["min_support"]
    schema = Schema()
    for kind in KINDS:
        vague = definitions.too_vague.get(kind, {})
        target = getattr(schema, kind)
        for e in getattr(counts, kind):
            if e["support"] < cut:
                schema.deferred.append({"kind": kind, "name": e["name"], "support": e["support"],
                                        "reason": f"support {e['support']} < min_support {cut}"})
                continue
            if e["name"] in vague:
                schema.deferred.append({"kind": kind, "name": e["name"], "support": e["support"],
                                        "reason": f"too vague: {vague[e['name']]}"})
                continue
            definition = definitions.of.get(kind, {}).get(e["name"])
            if definition is None:
                definition = MISSING_DEFINITION
                schema.missing_definitions.append({"kind": kind, "name": e["name"]})
            row = {"name": e["name"], "definition": definition}
            if kind == "entity_classes":
                row["examples"] = e["examples"][:3]
            row.update({"support": e["support"], "maintainers": e["maintainers"],
                        "texts": e["texts"], ORIGIN_FIELD: _origin(e["texts"])})
            target.append(row)
            if len(e["maintainers"]) == 1:
                schema.single_maintainer.append({"kind": kind, "name": e["name"]})

    kept_classes = {c["name"] for c in schema.entity_classes}
    kept_predicates = {p["name"] for p in schema.predicates}
    for e in counts.patterns:
        s, p, o = e["pattern"]
        if e["support"] < cut:
            reason = f"support {e['support']} < min_support {cut}"
        elif not (s in kept_classes and o in kept_classes and p in kept_predicates):
            missing = [x for x in (s, p, o) if x not in kept_classes | kept_predicates]
            reason = f"{missing[0]} is not in the schema"
        else:
            schema.patterns.append({"pattern": e["pattern"], "support": e["support"],
                                    "maintainers": e["maintainers"], "texts": e["texts"],
                                    ORIGIN_FIELD: _origin(e["texts"])})
            continue
        schema.deferred.append({"kind": "patterns", "name": " ".join(e["pattern"]),
                                "support": e["support"], "reason": reason})
    log.info(f"  schema: {len(schema.entity_classes):,} entity classes, {len(schema.predicates):,} "
             f"predicates, {len(schema.patterns):,} patterns; {len(schema.deferred):,} deferred")
    return schema
