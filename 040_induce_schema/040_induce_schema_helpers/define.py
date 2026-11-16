"""
define.py -- stage 7: one sentence defining each entity class and each
predicate.

Every entity class and predicate whose support reaches min_support is sent
to the model, DEFINE_BATCH at a time, with its support and its examples (an
entity class's component instances; a predicate's triple instances, which show
its subject and object) (prompts/define_entity_classes.txt,
define_predicates.txt). A predicate is also sent with its patterns that counting
(stage 6) holds: the entity classes of its subject and object, each pair with the
number of texts it was found in, through entity classes being defined, so its
definition can say what it joins. Both prompts list the entity classes being
defined, and a definition MAY name any of them, in their spelling ("was collected
during this Mission"), as the ground truth schema's definitions do; it never has
to. No prompt shows a schema's patterns or pins (common/common_helpers/
schema_io.schema_text), so a predicate's definition is the one place a model
learns what it joins. A predicate stage 5 pinned (a new predicate of a
predicate split: counting's "pinned") is also sent with "must_name", the entity
classes of its pin that are being defined, and its definition must name each of
them (an unpinned predicate's definition still may name entity classes, or not):
the prompt shows those entity classes, never the pin line itself, so a model
reading the schema later (step 060) learns the pin from the definition alone,
as with the ground truth schema's pinned predicates. The model writes one
sentence for each, or, for a schema entry too vague to tell anything apart
("Thing", "RELATED_TO"), says so with a reason.

Checked in code, then asked once more, as labeling (stage 3) asks once more for a
component instance left unlabeled:
  - an entry sent that the reply neither defines nor calls too vague;
  - a definition that names a word shaped like an entity class (looks_like_an_entity_class:
    CamelCase, two or more capitalised parts each followed by lowercase letters,
    "PhysicalQuantity") that is no entity class being defined (not_entity_classes:
    the spelling must be exact; a plural "s" or "es" is allowed). Words such as
    "MODIS" (capitals only), "SeaWiFS", "GeoTIFF" or "NetCDF" (a part without
    lowercase letters after its capital) and "Instrument" (one part) are never taken
    for one, so a domain's proper nouns aren't; a CamelCase proper noun ("McMurdo")
    is, and then only listed. An entity class a merge (stage 4) removed, or one
    below min_support, is no entity class being defined;
  - a pinned predicate's definition that doesn't name every entity class of
    its "must_name" (common/common_helpers/schema_io.unnamed_pinned, the check
    tests/test_schema_io.py applies to the ground truth schema's pins).
The second reply's definition replaces the first (recorded as replaced in the record
of discarded items, common/common_helpers/dropped.py); when the second reply gives
none, or still names such a word, the definition kept is recorded as replaced too
(its value unchanged when the first is kept), with those words, and listed in the
report (a pinned predicate's still not naming its pin: pins_not_named): a definition
is words only, never a reason to leave a schema entry out. An
entry still neither defined nor called too vague gets stage 8's missing-definition
mark, as before.

This stage only writes words. It merges nothing (merging is stage 4's job,
done once, over all labels at a time) and chooses nothing: the examples are
picked by code (stage 6): the component instances that most often got each
entity class, the triple instances that most often state each predicate. Stage 8 checks what the model sent back.

Adapted from assemble() in archive/to_be_reshaped/best_induce_schema.py, which also
merged near-duplicates here, a second merge in batches of 40 where synonyms
could miss each other, and asked the model to pick examples.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from common.cache import Cache, ask_cached, ask_split, needs
from common.audit import log
from common import dropped
from common.prompt_files import fill, load
from common.schema_io import unnamed_pinned
from common.triples_io import KIND_OF_KEY

#: The two kinds of schema entry that get a definition.
KINDS = tuple(KIND_OF_KEY)                  # ("entity_classes", "predicates")
#: The words for KINDS in the output files ("kind", "entry_type").
WORD = KIND_OF_KEY

PROMPTS_DIR = Path(__file__).resolve().parents[1] / "040_induce_schema_prompts"   # 040_induce_schema/040_induce_schema_prompts/
PROMPTS = {"entity_classes": load(PROMPTS_DIR / "define_entity_classes.txt"),
           "predicates": load(PROMPTS_DIR / "define_predicates.txt")}

#: Schema entries per call. The reply holds one sentence per entry, so this
#: bounds its length.
DEFINE_BATCH = 40
#: The stage name its discarded items carry (common/common_helpers/dropped.py).
STAGE = "stage 7 (write_definitions)"
#: A word shaped like an entity class: two or more parts, each a capital followed by lowercase letters
#: ("PhysicalQuantity", "SpatialResolutions"); not "MODIS", "SeaWiFS", "GeoTIFF", "Instrument" or "Level-2".
ENTITY_CLASS_SHAPE = re.compile(r"(?<![\w-])(?:[A-Z][a-z]+){2,}(?![\w-])")


@dataclass
class Definitions:
    of: dict = field(default_factory=dict)          # {"entity_classes": {entity class: sentence}, "predicates": {...}}
    too_vague: dict = field(default_factory=dict)   # {"entity_classes": {entity class: reason}, ...}
    unknown: list = field(default_factory=list)     # schema entries in replies that weren't sent
    refused: list = field(default_factory=list)     # {"kind", "component_class", "why"}: the service wouldn't define
                                                    # them (e.g. its content filter), so they get no definition
    asked_again: list = field(default_factory=list) # {"kind", "component_class", "why"}: asked once more
    not_entity_classes: list = field(default_factory=list)  # {"kind", "component_class", "definition", "words"}: a
                                                    # definition kept that still names words shaped like an
                                                    # entity class that aren't one being defined
    pins_not_named: list = field(default_factory=list)  # {"kind", "component_class", "definition", "entity_classes"}:
                                                    # a pinned predicate's definition kept that still doesn't name
                                                    # every entity class of its pin being defined
    calls: int = 0                                  # model calls made by this stage
    reused: int = 0                                 # batches answered from the cache


#: The shape of a defining answer (the prompts' reply format): a "definitions" object ("too_vague" may be left out
#: when none is). One of another shape is asked again, never kept (common/common_helpers/cache.py, ask_cached).
SHAPE = needs(definitions=dict)


def not_entity_classes(definition: str, entity_classes) -> list:
    """The words of a definition shaped like an entity class (ENTITY_CLASS_SHAPE) that are no entity class of
    entity_classes, spelled exactly; a plural "s" or "es" after one is allowed. Each once, in the order written."""
    known = set(entity_classes)
    out = []
    for word in ENTITY_CLASS_SHAPE.findall(definition or ""):
        if word in known or (word.endswith("s") and word[:-1] in known) or (word.endswith("es") and word[:-2] in known):
            continue
        if word not in out:
            out.append(word)
    return out


def _patterns_of(counts, defined_classes: set) -> dict:
    """{predicate: [{"subject", "object", "texts"}]}: the patterns counting holds whose two entity classes are being
    defined, most texts first (counting's order)."""
    out = {}
    for e in counts.patterns:
        s, p, o = e["pattern"]
        if s in defined_classes and o in defined_classes:
            out.setdefault(p, []).append({"subject": s, "object": o, "texts": e["support"]})
    return out


def write_definitions(counts, settings: dict, calls) -> Definitions:
    cache = Cache(calls.cache_dir, "define")
    result = Definitions()
    before = calls.paid.made
    entity_classes = [e["component_class"] for e in counts.entity_classes if e["support"] >= settings["min_support"]]
    for kind in KINDS:
        result.of[kind], result.too_vague[kind] = {}, {}
        # the entity classes being defined: for predicates, those not called too vague (defined first, KINDS' order)
        defined_classes = [c for c in entity_classes if c not in result.too_vague.get("entity_classes", {})]
        patterns = _patterns_of(counts, set(defined_classes)) if kind == "predicates" else {}
        wanted = [e for e in getattr(counts, kind) if e["support"] >= settings["min_support"]]
        # a pinned predicate's definition must name its pin's entity classes, those being defined (stage 5's pins)
        must = {} if kind != "predicates" else {
            p: [c for c in dict.fromkeys(x for pair in pins for x in pair) if c in defined_classes]
            for p, pins in getattr(counts, "pinned", {}).items()}
        must = {p: m for p, m in must.items() if m}
        entries = {e["component_class"]: {"component_class": e["component_class"], "texts": e["support"],
                                          "examples": e["examples"],
                                          **({"patterns": patterns.get(e["component_class"], [])}
                                             if kind == "predicates" else {}),
                                          **({"must_name": must[e["component_class"]]}
                                             if e["component_class"] in must else {})} for e in wanted}
        listing = json.dumps(defined_classes, ensure_ascii=False)

        def ask(names: list, again: bool = False) -> dict:
            """{name: (field, text)} from the replies about these entries, asked DEFINE_BATCH at a time; every
            item a reply gives that isn't taken is recorded (_take)."""
            got = {}
            for start in range(0, len(names), DEFINE_BATCH):
                batch = [entries[n] for n in names[start:start + DEFINE_BATCH]]
                refused = []
                # A batch the service refuses is asked in halves; an entry it still refuses alone gets no definition,
                # with the reason (common.cache.ask_split).
                replies = ask_split(lambda part: ask_cached(
                    cache, calls, fill(PROMPTS[kind], entity_classes=listing,
                                       entries=json.dumps(part, ensure_ascii=False, indent=0)),
                    f"  040 will ask the model to define the schema's entries, {DEFINE_BATCH} per call", check=SHAPE),
                    batch, refused)
                for e, why in refused:
                    if e["component_class"] in result.of[kind] or e["component_class"] in result.too_vague[kind]:
                        continue                # asked again, refused now: the first reply's answer stands
                    result.refused.append({"kind": WORD[kind], "component_class": e["component_class"], "why": why})
                    dropped.discard(STAGE, "schema entry", f"refused by the model's service, so it gets no "
                                    f"definition: {why}", {"kind": WORD[kind], **e})
                _take(kind, {e["component_class"] for e in batch}, replies, got, result, again)
            return got

        first = ask(list(entries))
        for name, (field_name, text) in first.items():
            (result.of if field_name == "definitions" else result.too_vague)[kind][name] = text
        refused_now = {r["component_class"] for r in result.refused if r["kind"] == WORD[kind]}
        known = [c for c in entity_classes if c not in result.too_vague.get("entity_classes", {})]
        missing = [n for n in entries if n not in first and n not in refused_now]

        def problems(n: str, d: str) -> tuple:
            """(the words of a definition shaped like an entity class that are none being defined, the entity classes
            of its predicate's must_name it doesn't name)."""
            return not_entity_classes(d, known), unnamed_pinned(d, [(c, c) for c in must.get(n, [])])
        wrong = {n: problems(n, d) for n, d in result.of[kind].items()}
        wrong = {n: w for n, w in wrong.items() if w[0] or w[1]}
        for n in missing:
            result.asked_again.append({"kind": WORD[kind], "component_class": n,
                                       "why": "neither defined nor called too vague"})
        for n, (w, u) in wrong.items():
            result.asked_again.append({"kind": WORD[kind], "component_class": n, "why": "; ".join(
                (["its definition names " + ", ".join(w) + ", which " + ("is" if len(w) == 1 else "are")
                  + " no entity class being defined"] if w else [])
                + (["its definition doesn't name " + ", ".join(u) + ", which its pin allows (it must name each)"]
                   if u else []))})
        if missing or wrong:
            # One more try for those, as labeling does (stage 3), with the same prompt
            second = ask(missing + list(wrong), again=True)
            for n in missing:
                if n in second:
                    field_name, text = second[n]
                    (result.of if field_name == "definitions" else result.too_vague)[kind][n] = text
            for n, (words, unnamed) in wrong.items():
                old = result.of[kind][n]
                field_name, text = second.get(n, (None, None))
                kept = text if field_name == "definitions" else old
                if field_name == "too_vague":
                    dropped.discard(STAGE, "definition", "in the model's reply (too_vague, asked once more), but not "
                                    "taken: the first reply defined the schema entry, and its definition is kept",
                                    {"kind": WORD[kind], "component_class": n, "text": text})
                still, still_unnamed = problems(n, kept)
                result.of[kind][n] = kept
                why = ("; ".join(([f"names {', '.join(words)}, shaped like an entity class but no entity class being "
                                   f"defined"] if words else [])
                                 + ([f"doesn't name {', '.join(unnamed)}, which its pin allows"] if unnamed else []))
                       + ": asked once more, " + ("the second reply's definition is kept" if kept is text else
                                                  "the second reply gave no definition, so the first is kept")
                       + (f", which still names {', '.join(still)} (listed in the report)" if still else "")
                       + (f"; it still doesn't name {', '.join(still_unnamed)} (listed in the report)"
                          if still_unnamed else ""))
                dropped.replace(STAGE, "definition", why, {"kind": WORD[kind], "component_class": n, "definition": old,
                                                           "not_entity_classes": words, "pinned_not_named": unnamed},
                                {"definition": kept, "not_entity_classes": still, "pinned_not_named": still_unnamed})
                if still:
                    result.not_entity_classes.append({"kind": WORD[kind], "component_class": n, "definition": kept,
                                                      "words": still})
                if still_unnamed:
                    result.pins_not_named.append({"kind": WORD[kind], "component_class": n, "definition": kept,
                                                  "entity_classes": still_unnamed})
        log.info(f"  {kind.replace('_', ' ')}: {len(result.of[kind]):,} defined, "
                 f"{len(result.too_vague[kind])} too vague"
                 + (f"; {len(missing) + len(wrong)} asked once more" if missing or wrong else ""))
    result.calls, result.reused = calls.paid.made - before, cache.reused
    return result


def _take(kind: str, sent: set, replies: list, got: dict, result: Definitions, again: bool) -> None:
    """Each item of the replies' "definitions" and "too_vague" objects: taken into got ({name: (field, text)}) when
    its entry was sent, its text non-empty, and the entry has no answer from these replies yet; every other one
    recorded in the record of discarded items, with why. again: the replies are the second ask's."""
    for reply in replies:
        for field_name in ("definitions", "too_vague"):
            given = reply.get(field_name) if isinstance(reply.get(field_name), dict) else {}
            for name, text in given.items():
                if name not in sent:
                    result.unknown.append({"kind": WORD[kind], "component_class": name})
                    why = "for a schema entry that wasn't sent"
                elif isinstance(text, str) and text.strip() and name not in got:
                    got[name] = (field_name, " ".join(text.split()))
                    continue
                elif not (isinstance(text, str) and text.strip()):
                    why = "empty, or not text"
                else:
                    why = ("the schema entry already has a definition, or a reason it is too vague, from the "
                           "replies: the first is kept")
                dropped.discard(STAGE, "definition", f"in the model's reply ({field_name}"
                                + (", asked once more" if again else "") + f"), but not taken: {why}",
                                {"kind": WORD[kind], "component_class": name, "text": text})
