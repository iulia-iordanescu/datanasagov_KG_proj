"""
split.py -- stage 5 (splitting): split a predicate that stands for different
relationships, by the entity class of its subject, of its object, or of both
(its pattern), checked by code; then merge the predicates again.

After stage 4, a predicate label can still stand for several relationships that
differ by what its subject is, by what its object is, or by the two together.
The test, as the prompt states it once: group the predicate's triple instances
by the entity class of their subject, of their object, or of both (their
pattern); if describing what the subject and object have to do with each other
takes a different verb for each group, the predicate stands for different
relationships, and is split, one new predicate per relationship; if one verb
fits every group, it stays whole, since the entity classes already record the
difference. Suppose SOURCED_FROM has triple instances with Mission objects
("data from the Apollo 11 mission": the mission produced the data) and with
Spacecraft objects ("images from the Cassini spacecraft": the spacecraft
carried the instrument). Then the two groups take two verbs, one predicate for
each says more, and each can translate to its own ground truth schema
predicate.

What a split can move. Only a triple instance whose subject, predicate and
object all have a final label (stage 4) has a pattern, so only such triple
instances are grouped, shown, counted toward a split's support, and moved; a
triple instance with an unlabeled subject or object stays with its predicate
whichever grouping is used. So a new predicate holds exactly the triple
instances its groups describe, and its pin (below) is true of every one of them.

Every predicate whose triple instances (those with a pattern) have more than one
subject entity class or more than one object entity class (equivalently, more
than one pattern) goes to the model, SPLIT_BATCH at a time
(040_induce_schema_prompts/split_predicates.txt), with each of its patterns, the
number of texts it was found in, and up to EXAMPLES triple instances (chosen by
count.representative: each from another text and, where possible, another
maintainer, the triple instance found in the most texts first), the number
of texts of each of its subject entity classes and object entity classes (so the
three groupings can be read off at once), and the names of every predicate found
(the final labels of stage 4), which a new predicate may not take: the check
below rejects any of them, so the prompt shows them all. A predicate split is a
new predicate with its grouping ("by": subject, object or pattern) and the
groups it takes ("takes": entity classes, or patterns written "Subject ->
Object"). A group no predicate split takes stays with the predicate.

One grouping per predicate. All the predicate splits of one predicate in one run
use one grouping, the one of its first predicate split that passes the checks.
Two groupings of one predicate would let one triple instance belong to two new
predicates (a subject split taking Dataset and an object split taking Mission
both claim Dataset -> Mission), which no rule could settle without overriding
one of the model's answers, and each new predicate's pin would then be broken by
triple instances it holds. Nothing is lost: any mix of subject and object groups
is a set of patterns, so the pattern grouping can say it.

What code checks in each proposed predicate split, in this order (the first
that fails rejects it, and the reason is listed):
  - it is a JSON object;
  - its predicate is one of the predicates sent;
  - its new predicate is non-empty text;
  - its new predicate is one UPPER_SNAKE_CASE word, as the prompt asks
    (label.well_formed, stage 3's check of a predicate label);
  - the new predicate isn't the name of a predicate found (the one split
    included), and no earlier split took the same name (names compared by
    common/common_helpers/triples_io.component_class_key, as spelling folds
    compare them);
  - its grouping is subject, object or pattern;
  - it is the grouping of the earlier predicate splits of the predicate that
    passed (one grouping per predicate, above);
  - it names at least one group;
  - every group it names is the predicate's own: one of its subject entity
    classes (subject), object entity classes (object), or patterns (pattern);
    an entity class the predicate has only on the other side is not;
  - no earlier split of the same predicate took any of them (the first split
    stands, as the first merge does in stage 4);
  - it doesn't take every group of the predicate (that would rename the
    predicate, not split it);
  - its supporting texts (the texts with a triple instance it would take)
    number at least min_split_texts.

Then the cap, max_new_predicates. A predicate split into n new predicates adds
n predicates, or n - 1 when its splits take every group (the predicate itself is
then left with no triple instance that has a pattern). If the splits that passed
the checks would add more than the cap, they are kept one by one, the split with
the most supporting texts first, each kept only if the total stays within the
cap; the others are dropped (their predicate keeps those triple instances) and
listed. max_new_predicates 0 asks the model nothing.

Then merging again (merge_again), after the cap: the cap bounds the predicates
the kept splits add, and a merge can only lower that number, so capping first
never lets a merge make room for a split the cap left out. Every predicate after
splitting (old and new) goes to the model in one call, with stage 4's predicate merge prompt, read
and checked by stage 4's code (merge.ask_merges), each predicate shown as stage 4
shows one (merge.predicate_examples: example triple instances with their
entity classes; a new predicate's are the triple instances its split took, so
the parts of one split arrive with different examples), cached apart from stage 4's
answers (cache/merge_again.json); spelling folds apply first, as in stage 4 (today
they find nothing to fold: stage 4 left no two predicates that match loosely, and
the name checks above keep a new predicate from matching any name loosely; the
fold stays so the stage remains right if a check changes). A merge between two predicates that were both there at stage 4 is set
aside and recorded: stage 4's call already judged that pair, and a second answer
to the same question is not more evidence. So a new predicate merges with a
synonym among the existing predicates, or two new predicates of one split merge.

A split undone. When, after merging again, every part of a split predicate (its
new predicates, and the predicate itself if it kept any triple instance) ends in
one predicate X, the split is undone: its new predicates are dropped, and the
predicate, whole again, goes to X, or stays itself when X is one of its own
parts (a split whose parts all merge back into one is a renaming, which the
checks reject). Undoing a split can make another split undone in turn; this is
repeated until nothing changes. Every undone split, merge and fold is recorded.

Pins. A new predicate is pinned to the groups its split took ("any" for the side
not grouped by): a subject split taking Dataset gives "Dataset -> any"; an
object split taking Mission gives "any -> Mission"; a pattern split gives its
patterns. A predicate that a merge made of several predicates is pinned to the
union of their pins when every one of them is pinned, and is unpinned when any
one of them is not: an unpinned predicate may join whatever entity classes its
meaning fits, so the union of its triple instances with a pinned predicate's has
no bound either. The schema writes the pins (stage 8, "pinned", the shape
common/common_helpers/schema_io.py reads), so step 060's check
pattern_not_pinned flags an extracted triple that breaks one; no prompt shows
them (schema_io.schema_text), and stage 7 asks each pinned predicate's
definition to name its pinned entity classes.

Stage 6 (counting) then gives each triple instance of a split predicate, with a
pattern in a group a kept split took, that split's new predicate, then the
predicate that merging again made of it (Splits.predicate). Splitting reads
only the induced schema's own labels and triple instances, never the ground
truth or the translation table.

From TRACE-KG (Abolhasani, Ba, He & Pan, "Traceable Context-Enriched Knowledge
Graph Generation with Induced Schemas", arXiv:2604.03496v3): its model may
split an entity class into several (split_class, appendix B.4.2), and its code
keeps only the split entity class's own members, each in one split only
(execute_split_class, TKG_Main.py, line 4796); it sets each triple instance's
predicate with its subject's and object's entity classes in view (section
4.5); and its code carries out only actions it has checked (section 4.6). Here
the split is of a predicate, by its subject's or object's entity class or both.
"""
from __future__ import annotations

import collections
import json
from dataclasses import dataclass, field
from pathlib import Path

import count
import label
import merge
from common import dropped
from common.audit import log
from common.cache import Cache, ask_cached, ask_split, needs
from common.prompt_files import fill, load
from common.schema_io import ANY
from common.stop import Stop
from common.triples_io import component_class_key

PROMPTS_DIR = Path(__file__).resolve().parents[1] / "040_induce_schema_prompts"   # 040_induce_schema/040_induce_schema_prompts/
PROMPT = load(PROMPTS_DIR / "split_predicates.txt")

#: Predicates per call. Each comes with every pattern it has and their examples.
SPLIT_BATCH = 20
#: The stage names its discarded items carry (common/common_helpers/dropped.py): the splits, and merging again.
STAGE = "stage 5 (split_predicates)"
MERGE_AGAIN_STAGE = "stage 5 (merge_predicates_again)"
#: Example triple instances shown for each pattern of a predicate.
EXAMPLES = 3
#: The three groupings, as the reply names them ("by").
GROUPINGS = ("subject", "object", "pattern")
#: How a pattern group is written, in the prompt, the reply and the files: "Dataset -> Mission".
ARROW = " -> "
#: Each grouping in words, for the report and the messages.
GROUPED_BY = {"subject": "its subject's entity class", "object": "its object's entity class",
              "pattern": "its pattern (subject and object entity classes)"}

#: The shape of a splitting answer (the prompt's reply format): a "splits" list. One of another shape is asked again,
#: never kept (common/common_helpers/cache.py, ask_cached).
SHAPE = needs(splits=list)

#: Why a proposed split is rejected, in the order code checks (see above).
NOT_AN_OBJECT = "not a JSON object"
NOT_SENT = "its predicate wasn't sent"
NO_NAME = "no new predicate named"
NOT_ONE_WORD = ("its new predicate isn't one UPPER_SNAKE_CASE word (letters, digits and single underscores only), "
                "the format the prompt asks for")
NAME_TAKEN = "its new predicate is the name of a predicate found"
NAME_TWICE = "its new predicate is the name an earlier predicate split took"
NO_GROUPING = "names no grouping (by must be subject, object or pattern)"
OTHER_GROUPING = "groups the predicate otherwise than its earlier predicate splits (one grouping per predicate)"
NO_GROUPS = "names no entity class or pattern"
NOT_ITS_GROUP = "names an entity class or pattern that isn't among the predicate's"
GROUP_TWICE = "names an entity class or pattern an earlier predicate split of the predicate took"
EVERY_GROUP = "takes every group of the predicate (a renaming, not a split)"
TOO_FEW_TEXTS = "its triple instances were found in fewer texts than min_split_texts"
REASONS = (NOT_AN_OBJECT, NOT_SENT, NO_NAME, NOT_ONE_WORD, NAME_TAKEN, NAME_TWICE, NO_GROUPING, OTHER_GROUPING, NO_GROUPS,
           NOT_ITS_GROUP, GROUP_TWICE, EVERY_GROUP, TOO_FEW_TEXTS)

@dataclass
class Splits:
    into: dict = field(default_factory=dict)       # {predicate: {"by": grouping, "to": {group: new predicate}}}: the
                                                   # splits kept (not undone)
    sent: list = field(default_factory=list)       # the predicates sent: {"predicate", "texts", "subject_classes",
                                                   # "object_classes", "patterns"}
    kept: list = field(default_factory=list)       # {"predicate", "by", "into", "takes", "only", "texts",
                                                   # "triple_instances"}: kept, not undone
    dropped: list = field(default_factory=list)    # passed the checks, left unsplit by the cap: the same fields
    rejected: list = field(default_factory=list)   # {"predicate", "by", "into", "takes", "why"}
    refused: list = field(default_factory=list)    # {"predicate", "why"}: the service wouldn't answer about them
    undone: list = field(default_factory=list)     # kept by the cap, undone by merging again: the kept fields, and
                                                   # "ends_in" (where every part ended), "goes_to" (the predicate now)
    merges: list = field(default_factory=list)     # merging again: {"label", "into", "texts", "component_instances"}
    merge_issues: dict = field(default_factory=dict)  # merging again: the merges set aside, by code (merge.ISSUE_WHY)
    merge_fallback: dict | None = None             # merging again: merge.ask_merges' fallback, None when answered
    spelling_folds: list = field(default_factory=list)  # merging again: {"kind", "into", "folded"}
    final: dict = field(default_factory=dict)      # {predicate after splitting: its predicate after merging again}
    pinned: dict = field(default_factory=dict)     # {predicate after merging again: [(subject class or "any",
                                                   #  object class or "any")]}
    added: int = 0                                 # predicates the kept splits add (what the cap bounds)
    net_added: int = 0                             # predicates after merging again, less those before splitting
    cap: int = 0                                   # max_new_predicates
    min_texts: int = 1                             # min_split_texts
    calls: int = 0                                 # model calls made by this stage's splitting
    reused: int = 0                                # batches answered from the cache
    merge_calls: int = 0                           # model calls made by merging again
    merge_reused: int = 0                          # merging again answered from the cache

    def split_to(self, predicate, subject_class, object_class):
        """A triple instance's predicate after splitting: the new predicate of the kept split whose group holds its
        pattern, else its predicate as it was (always so when its subject or object has no label)."""
        spec = self.into.get(predicate)
        if not spec or not subject_class or not object_class:
            return predicate
        return spec["to"].get(group_of(spec["by"], subject_class, object_class), predicate)

    def predicate(self, predicate, subject_class, object_class):
        """A triple instance's predicate after splitting and merging again."""
        after = self.split_to(predicate, subject_class, object_class)
        return self.final.get(after, after)


def group_of(by: str, subject_class: str, object_class: str) -> str:
    """The group a pattern is in under a grouping: its subject class, its object class, or "Subject -> Object"."""
    return subject_class if by == "subject" else object_class if by == "object" else subject_class + ARROW + object_class


def pin_of(by: str, group: str) -> tuple:
    """The (subject class, object class) pin of one group ("any" for the side not grouped by)."""
    if by == "subject":
        return group, ANY
    if by == "object":
        return ANY, group
    s, o = group.split(ARROW, 1)
    return s, o


def patterns_of(triples, labels) -> dict:
    """{predicate: {(subject class, object class): {"texts": ids, "examples": Counter of "subject -- predicate --
    object", "candidates": [(pattern, example, text id, maintainer)] for count.representative()}}} from the verified
    triple instances whose three component instances have a final label."""
    found = collections.defaultdict(lambda: collections.defaultdict(
        lambda: {"texts": set(), "examples": collections.Counter(), "candidates": []}))
    for t in triples.texts:
        for ti in t["triple_instances"]:
            p = labels.final["predicate"].get(ti["predicate"])
            sc = labels.final["entity"].get(ti["subject"])
            oc = labels.final["entity"].get(ti["object"])
            if p and sc and oc:
                shown = f"{ti['subject']} -- {ti['predicate']} -- {ti['object']}"
                found[p][(sc, oc)]["texts"].add(t["id"])
                found[p][(sc, oc)]["examples"][shown] += 1
                found[p][(sc, oc)]["candidates"].append(((sc, oc), shown, t["id"], t["maintainer"]))
    return found


def groups(patterns: dict, by: str) -> dict:
    """{group: {"texts": ids, "triple_instances": n}}: a predicate's patterns (patterns_of()[predicate]) grouped."""
    out = collections.defaultdict(lambda: {"texts": set(), "triple_instances": 0})
    for (sc, oc), e in patterns.items():
        g = out[group_of(by, sc, oc)]
        g["texts"] |= e["texts"]
        g["triple_instances"] += sum(e["examples"].values())
    return out


def several(patterns: dict) -> bool:
    """Whether a predicate goes to the model: more than one subject entity class or more than one object entity class
    (so more than one pattern)."""
    return len({s for s, _ in patterns}) > 1 or len({o for _, o in patterns}) > 1


def _loose(by: str, group):
    """A group named in a reply, as compared (component_class_key on each entity class), or None if it can't be one."""
    if not isinstance(group, str) or not group.strip():
        return None
    if by != "pattern":
        return component_class_key(group)
    if "->" not in group:
        return None
    s, o = group.split("->", 1)
    return component_class_key(s), component_class_key(o)


def added_by(splits: list, found: dict) -> int:
    """The predicates these splits add: per predicate, one per split, less one when its splits take every group it has
    under their grouping (found: patterns_of())."""
    by = collections.defaultdict(list)
    for s in splits:
        by[s["predicate"]].append(s)
    return sum(len(ss) - (set().union(*(set(s["takes"]) for s in ss)) == set(groups(found[p], ss[0]["by"])))
               for p, ss in by.items())


def check(replies: list, found: dict, predicates: set, min_texts: int = 1) -> tuple:
    """(splits that passed every check, splits rejected with why), from the replies' "splits" items in order.
    found: patterns_of(); only its predicates with several() patterns were sent. predicates: every predicate found
    (the final labels), whose names a new predicate may not take. min_texts: min_split_texts."""
    sent = {component_class_key(p): p for p, pats in found.items() if several(pats)}
    taken_names = {component_class_key(p) for p in predicates}
    grouping = {}                                       # {predicate: the grouping of its first split that passed}
    taken = collections.defaultdict(set)                # {predicate: the groups its splits that passed took}
    passed, rejected = [], []
    for item in (i for reply in replies for i in reply["splits"]):
        if not isinstance(item, dict):
            rejected.append({"predicate": None, "by": None, "into": None, "takes": [], "why": NOT_AN_OBJECT})
            dropped.discard(STAGE, "predicate split", f"proposed by the model, rejected by code: {NOT_AN_OBJECT}",
                            {"raw": item})
            continue
        named, into, by, takes = item.get("predicate"), item.get("into"), item.get("by"), item.get("takes")
        row = {"predicate": named, "by": by, "into": into, "takes": takes if isinstance(takes, list) else []}
        p = sent.get(component_class_key(named)) if isinstance(named, str) else None
        by = by.strip().lower() if isinstance(by, str) else by
        why, setting, mapped = None, None, []
        if p is None:
            why = NOT_SENT
        elif not (isinstance(into, str) and into.strip()):
            why = NO_NAME
        elif not label.well_formed("predicate", into):
            why = NOT_ONE_WORD
        elif component_class_key(into) in taken_names:
            why = NAME_TAKEN
        elif component_class_key(into) in {component_class_key(s["into"]) for s in passed}:
            why = NAME_TWICE
        elif by not in GROUPINGS:
            why = NO_GROUPING
        elif grouping.get(p, by) != by:
            why = f"{OTHER_GROUPING}: its earlier ones group it by {grouping[p]}, this one by {by}"
        elif not (isinstance(takes, list) and any(isinstance(c, str) and c.strip() for c in takes)):
            why = NO_GROUPS
        if why is None:
            own = groups(found[p], by)
            loose = {_loose(by, g): g for g in own}
            mapped = [loose.get(_loose(by, c)) for c in takes]
            if None in mapped:
                why = NOT_ITS_GROUP + ": " + ", ".join(_not_its_own(c, by, found[p]) for c, m in zip(takes, mapped)
                                                       if m is None)
            elif set(mapped) & taken[p]:
                why = GROUP_TWICE + ": " + ", ".join(sorted(set(mapped) & taken[p]))
            elif set(mapped) == set(own):
                why = EVERY_GROUP
            else:
                texts = set().union(*(own[g]["texts"] for g in mapped))
                if len(texts) < min_texts:
                    why = f"{TOO_FEW_TEXTS}: {len(texts)} text(s), fewer than {min_texts}"
                    setting = {"min_split_texts": min_texts}
        if why is not None:
            rejected.append({**row, "why": why})
            dropped.discard(STAGE, "predicate split", f"proposed by the model, rejected by code: {why}",
                            {"raw": item}, setting=setting)
            continue
        chosen = list(dict.fromkeys(mapped))
        for i, (c, m) in enumerate(zip(row["takes"], mapped)):
            if mapped.index(m) != i:
                dropped.replace(STAGE, "entity class" if by != "pattern" else "pattern",
                                "named again in the same predicate split: counted once",
                                {"predicate": p, "into": into, "group": c}, {"group": m})
        own = groups(found[p], by)
        grouping[p] = by
        taken[p] |= set(chosen)
        passed.append({"predicate": p, "by": by, "into": into.strip(), "takes": chosen,
                       "only": [list(pin_of(by, g)) for g in chosen],
                       "texts": len(set().union(*(own[g]["texts"] for g in chosen))),
                       "triple_instances": sum(own[g]["triple_instances"] for g in chosen)})
    return passed, rejected


def _not_its_own(named, by: str, patterns: dict) -> str:
    """A group named that isn't the predicate's, in words, saying so when it is an entity class the predicate has on
    the other side only."""
    if by == "pattern" or not isinstance(named, str):
        return str(named)
    other = {component_class_key(o if by == "subject" else s) for s, o in patterns}
    side = "object" if by == "subject" else "subject"
    return named + (f" (among its {side} entity classes only)" if component_class_key(named) in other else "")


def capped(passed: list, found: dict, cap: int) -> tuple:
    """(kept, dropped): the splits that passed the checks, kept the one with the most supporting texts first (ties:
    by predicate, then new predicate), each only if the predicates added stay within cap."""
    order = sorted(passed, key=lambda s: (-s["texts"], s["predicate"], s["into"]))
    kept, dropped = [], []
    for s in order:
        (kept if added_by(kept + [s], found) <= cap else dropped).append(s)
    return kept, dropped


def split_predicates(triples, labels, settings: dict, calls) -> Splits:
    result = Splits(cap=settings["max_new_predicates"], min_texts=settings["min_split_texts"])
    found = patterns_of(triples, labels)
    texts_of = lambda p: set().union(*(e["texts"] for e in found[p].values()))         # noqa: E731
    for p in sorted((p for p, pats in found.items() if several(pats)), key=lambda p: (-len(texts_of(p)), p)):
        pats = sorted(found[p].items(), key=lambda kv: (-len(kv[1]["texts"]), kv[0]))
        side = {by: sorted(((g, len(e["texts"])) for g, e in groups(found[p], by).items()), key=lambda x: (-x[1], x[0]))
                for by in ("subject", "object")}
        result.sent.append({"predicate": p, "texts": len(texts_of(p)),
                            "subject_classes": dict(side["subject"]), "object_classes": dict(side["object"]),
                            "patterns": [{"subject": s, "object": o, "texts": len(e["texts"]),
                                          "examples": count.representative(e["candidates"], EXAMPLES)}
                                         for (s, o), e in pats]})
    if result.cap == 0 or not result.sent:
        log.info(f"  splitting: {len(result.sent)} predicate(s) have several subject or object entity classes; "
                 + ("max_new_predicates is 0, so none is sent" if result.sent else "nothing to ask"))
        if result.cap == 0:
            for e in result.sent:
                dropped.discard(STAGE, "predicate", "has several subject or object entity classes, but splitting is "
                                "off, so it isn't sent", e, setting={"max_new_predicates": 0})
            result.sent = []
        merge_again(triples, labels, result, calls)
        return result

    cache = Cache(calls.cache_dir, "split")
    before = calls.paid.made
    replies, refused = [], []
    found_names = json.dumps(sorted(set(labels.final["predicate"].values())), ensure_ascii=False)
    for start in range(0, len(result.sent), SPLIT_BATCH):
        batch = result.sent[start:start + SPLIT_BATCH]
        # A batch the service refuses is asked in halves; a predicate it still refuses alone isn't split, with the
        # reason (common.cache.ask_split).
        replies += ask_split(lambda part: ask_cached(
            cache, calls, fill(PROMPT, found=found_names, predicates=json.dumps(part, ensure_ascii=False, indent=0),
                               min_split_texts=result.min_texts),
            f"  040 will ask the model which predicates to split by their subject's or object's entity class or "
            f"both, {SPLIT_BATCH} per call", check=SHAPE), batch, refused)
    result.refused = [{"predicate": e["predicate"], "why": why} for e, why in refused]
    for e, why in refused:
        dropped.discard(STAGE, "predicate", f"refused by the model's service, so not split: {why}", e)
    since = dropped.mark()
    result.calls, result.reused = calls.paid.made - before, cache.reused

    passed, result.rejected = check(replies, found, set(labels.final["predicate"].values()), result.min_texts)
    result.kept, result.dropped = capped(passed, found, result.cap)
    for d in result.dropped:
        dropped.discard(STAGE, "predicate split", "passed the checks, but keeping it would add more predicates than "
                        "max_new_predicates allows (the splits with the most texts are kept first)", d,
                        setting={"max_new_predicates": result.cap})
    for s in result.kept:
        result.into.setdefault(s["predicate"], {"by": s["by"], "to": {}})["to"].update({g: s["into"] for g in s["takes"]})
    result.added = added_by(result.kept, found)
    merge_again(triples, labels, result, calls)
    dropped.account(STAGE, "predicate splits the model proposed", sum(len(r["splits"]) for r in replies),
                    len(result.kept), since=since, item_type="predicate split")
    log.info(f"  splitting: {len(result.sent)} predicate(s) sent; {len(result.kept) + len(result.undone)} split(s) "
             f"kept, adding {result.added} predicate(s); {len(result.undone)} undone by merging again; "
             f"{len(result.dropped)} dropped by max_new_predicates; {len(result.rejected)} rejected; "
             f"{result.net_added} predicate(s) more than before splitting")
    return result


def merge_again(triples, labels, result: Splits, calls) -> None:
    """Merging again (see above): result.final, result.merges, result.undone, result.pinned, result.net_added; the
    model is asked only when a kept split added a predicate."""
    new_of = {s["into"]: s["predicate"] for s in result.kept}          # {new predicate: the predicate split}
    entity = labels.final["entity"].get

    def after_split(ti):
        """A triple instance's predicate after splitting, or None when its predicate instance has no label."""
        p = labels.final["predicate"].get(ti["predicate"])
        return None if p is None else result.split_to(p, entity(ti["subject"]), entity(ti["object"]))
    before = {p for t in triples.texts for ti in t["triple_instances"]
              if (p := labels.final["predicate"].get(ti["predicate"])) is not None}
    # each predicate after splitting with the triple instances it holds: a new predicate's are those its split took
    examples, instances_of, texts_with = merge.predicate_examples(triples, after_split, entity)
    sent = sorted(instances_of)
    final = {q: q for q in sent}
    if not new_of or len(sent) < 2:
        result.final = final
        result.net_added = len(set(final.values())) - len(before)
        return
    if len(sent) > merge.MAX_LABELS_ONE_CALL:
        raise Stop(f"{len(sent)} predicates after splitting are more than one call takes "
                   f"({merge.MAX_LABELS_ONE_CALL}), so 040 can't merge them again: merging them in separate groups "
                   f"would let synonyms miss each other. Lower `--max_new_predicates` or learn from fewer texts (lower "
                   f"`--texts_per_stratum`), then run `py 040_induce_schema/run.py` again.")
    since = dropped.mark()
    counted = collections.Counter({q: sum(instances_of[q].values()) for q in sent})
    folded = merge._folding(counted, "predicate", result.spelling_folds)      # as in stage 4, before the call
    shown, _, texts_of = merge.predicate_examples(
        triples, lambda ti: None if (q := after_split(ti)) is None else folded[q], entity)
    listing = [{"label": lbl, "texts": len(texts_of[lbl]),
                "examples": count.representative(shown[lbl], merge.EXAMPLES)} for lbl in sorted(shown)]
    cache = Cache(calls.cache_dir, "merge_again")
    made = calls.paid.made
    mapping, result.merge_issues, result.merge_fallback = merge.ask_merges(
        "predicate", listing, cache, calls, MERGE_AGAIN_STAGE,
        "  040 will ask the model to merge the predicates again after splitting, in one call",
        takes_part=lambda label, into: label in new_of or into in new_of)
    result.merge_calls, result.merge_reused = calls.paid.made - made, cache.reused
    final = {q: mapping[folded[q]] for q in sent}

    # Splits undone: every part of a split predicate ends in one predicate (see above); repeated until nothing changes
    parts_of = collections.defaultdict(list)
    for s in result.kept:
        parts_of[s["predicate"]].append(s["into"])
    for p in parts_of:
        if p in final:
            parts_of[p].append(p)
    restored, undone = [], {}
    changed = True
    while changed:
        changed = False
        for p in sorted(parts_of):
            if p in undone:
                continue
            parts = parts_of[p]
            ends = {final[x] for x in parts}
            if len(ends) != 1:
                continue
            x = ends.pop()
            goes_to = p if x in parts else x
            if x in parts:                                 # the predicate's own part: everything merged into it is p's
                for y in final:
                    if final[y] == x:
                        final[y] = p
            if p not in final:
                restored.append(p)
            final[p] = goes_to
            for n in parts:
                if n != p:
                    del final[n]
            undone[p] = {"ends_in": x, "goes_to": goes_to}
            changed = True
    result.final = final

    gone = {n for p in undone for n in parts_of[p] if n != p}
    for s in [s for s in result.kept if s["predicate"] in undone]:
        u = undone[s["predicate"]]
        result.undone.append({**s, **u})
        dropped.discard(STAGE, "predicate split", f"undone by merging again: every part of {s['predicate']} ended in "
                        f"{u['ends_in']}, so {s['predicate']} is whole again"
                        + (f" and merged into {u['goes_to']}" if u["goes_to"] != s["predicate"] else ""), s)
    result.kept = [s for s in result.kept if s["predicate"] not in undone]
    for p in undone:
        result.into.pop(p, None)

    for q in sent:
        if q in gone:
            dropped.fold(MERGE_AGAIN_STAGE, "label", "a new predicate of a predicate split that merging again undid",
                         {"kind": "predicate", "label": q, "texts": len(texts_with[q])},
                         {"label": final[new_of[q]]})
        elif folded[q] != q:
            dropped.fold(MERGE_AGAIN_STAGE, "label", "a loose match of another predicate (spelling fold): the most "
                         "used spelling is kept", {"kind": "predicate", "label": q}, {"label": folded[q]})
        elif final[q] != q:
            result.merges.append({"kind": "predicate", "label": q, "into": final[q],
                                  "component_instances": len(instances_of[q]), "texts": len(texts_with[q])})
            dropped.fold(MERGE_AGAIN_STAGE, "label", "merged again by the model into a synonym", {
                "kind": "predicate", "label": q, "component_instances": len(instances_of[q]),
                "texts": len(texts_with[q])}, {"label": final[q]})
    for p in restored:
        if final[p] != p:
            result.merges.append({"kind": "predicate", "label": p, "into": final[p], "component_instances": 0,
                                  "texts": 0})
            dropped.fold(MERGE_AGAIN_STAGE, "label", "a predicate whose split was undone, merged into the predicate "
                         "every part of it ended in", {"kind": "predicate", "label": p}, {"label": final[p]})
    dropped.account(MERGE_AGAIN_STAGE, "predicates after splitting", len(sent) + len(restored),
                    len(set(final.values())), since=since, item_type="label")

    # Pins: each new predicate's, then, for a predicate made of several, their union when each is pinned
    own = {s["into"]: [tuple(x) for x in s["only"]] for s in result.kept}
    members = collections.defaultdict(list)
    for y, x in sorted(final.items()):
        members[x].append(y)
    for x, ys in members.items():
        pinned = [y for y in ys if y in own]
        if pinned and len(pinned) == len(ys):
            result.pinned[x] = list(dict.fromkeys(pair for y in pinned for pair in own[y]))
            for y in pinned:
                if y != x:
                    for pair in own[y]:
                        dropped.fold(MERGE_AGAIN_STAGE, "pinned predicate", "merged again into another pinned "
                                     "predicate: its pin joins that predicate's (the union of their pins)",
                                     {"predicate": y, "only": list(pair)}, {"predicate": x, "only": list(pair)})
        else:
            unpinned = [y for y in ys if y not in own]
            for y in pinned:
                for pair in own[y]:
                    dropped.discard(MERGE_AGAIN_STAGE, "pinned predicate", f"merged again with {', '.join(unpinned)}, "
                                    f"which has no pin, into {x}: a predicate with no pin may join any entity classes "
                                    f"its meaning fits, so {x} has no pin", {"predicate": y, "only": list(pair)})
    result.net_added = len(set(final.values())) - len(before)
    log.info(f"  merging again: {len(result.merges)} predicate(s) merged into others; {len(undone)} split "
             f"predicate(s) whole again; {len(result.pinned)} pinned predicate(s)")
