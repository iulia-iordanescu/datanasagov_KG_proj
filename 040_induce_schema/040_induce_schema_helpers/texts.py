"""
texts.py -- stage 1 (selection): pick the texts the schema is learned from.

A stratified draw over the same strata as the ground truth candidates pool
(annotations/ground_truth_candidates.json, its "strata": each maintainer large
enough to have a stratum of its own in the pool, plus one stratum,
"(small maintainers)", for every other maintainer), with EQUAL allocation:
texts_per_stratum texts from each stratum. The purpose is discovery (finding
the entity classes and predicates the catalog's texts use), not estimation:
a stratum's few texts can show a predicate only its maintainer uses, while
proportional allocation would give the small strata almost no texts. So
every stratum gets the same number, as the design of the Technical
Memorandum had it.

Only induction candidates are drawn (030: records outside the pool, with
text). Within a stratum, the texts are taken in a fixed random order: for a
maintainer's own stratum, 030's order of that maintainer's candidates; for
"(small maintainers)", the stratum's candidates shuffled the way 030 shuffles
each maintainer's (random.Random(f"{seed}/{stratum}").sample over the sorted
ids, with 030's induction_seed from splits.json). The strata are drawn in
rounds, one text from each stratum per round, so taking more texts later
(a higher texts_per_stratum) keeps every text taken before: their model calls
stay valid.

While drawing, a text that is a twin of a text already drawn is skipped and
the next in its stratum's order taken: a "whole text" twin (the same title and
the same notes) or a "notes only" twin (the same notes, another title), as
common/common_helpers/ground_truth.twin_kinds defines them (title and notes
compared evened out). A "title only" twin (the same title, other notes) is
kept: its text differs. Every skip, and every title-only twin kept, is
counted, per stratum.

The texts are then read in a random order fixed by 030's seed
(random.Random(f"{seed}/reading order")), so no stratum comes first.

Each text is the record's text fields, split into pieces of at most
max_chars (common/common_helpers/chunking.py): almost always one piece.
"""
from __future__ import annotations

import collections
import random
from dataclasses import dataclass, field

from common.audit import log
from common.chunking import full_text, pieces
from common.files import read_json
from common.ground_truth import twin_kinds
from common.records_io import load_records
from common.report import named
from common.step import Spec, check_settings, repo_path
from common.stop import Stop

#: The pool's stratum for every maintainer without one of its own (annotations/ground_truth_candidates.json).
SMALL = "(small maintainers)"
#: The twin kinds skipped while drawing (common.ground_truth.TWIN_KINDS): those that share the notes, so most of
#: the text. A "title only" twin is kept, since its text differs.
SKIPPED = ("whole text", "notes only")
KEPT_TWIN = "title only"
#: What the reading order's random generator is seeded with, after 030's seed.
READING_ORDER = "reading order"


@dataclass
class Texts:
    items: list = field(default_factory=list)        # {"id", "maintainer", "stratum", "record", "title", "text", "pieces"}
    strata: list = field(default_factory=list)       # {"stratum", "maintainers", "candidates", "taken",
                                                     #  "skipped": {twin kind: n}, "title_only_kept": n}
    skipped: list = field(default_factory=list)      # {"id", "stratum", "twin_kind", "twin_of"}: the twins skipped
    notes: list = field(default_factory=list)        # where the texts differ from what the settings ask for
    pool: dict = field(default_factory=dict)         # {id: record}: the ground truth candidates pool, for the twin table
    candidates: dict = field(default_factory=dict)   # {id: record}: every induction candidate, for the twin table
    seed: int | None = None                          # 030's induction_seed

    @property
    def maintainers(self) -> list:
        """The maintainers of the texts drawn, most texts first."""
        n = collections.Counter(t["maintainer"] for t in self.items)
        return sorted(n, key=lambda m: (-n[m], m))


#: The step's settings' rules (common.step.Spec); run_step checks them before any input is read, and so does
#: pick_texts, with the same table (the shared settings' rules: common.step.shared_specs).
SPECS = {"texts_per_stratum": Spec(int, 1, 10_000), "min_support": Spec(int, 1, 10_000),
         "max_new_predicates": Spec(int, 0, 10_000)}

#: The settings of the earlier design (the 10 largest maintainers, 15 texts each; the schema of 2026-10-12 was made
#: with it), refused with this message so that no run mixes the two designs up (common.step.run_step, retired).
RETIRED = {name: (f"--{name} was a setting of step 040's earlier sample design (the first texts_per_maintainer "
                  f"induction candidates of each of the induction_maintainers largest maintainers; the schema of "
                  f"2026-10-12 was made with it). Since 2026-11-14, 040 draws texts_per_stratum texts from each "
                  f"stratum of the ground truth candidates pool instead (040_induce_schema/040_induce_schema.md, "
                  f"How it works, stage 1). Run with --texts_per_stratum <n> (default 8) instead.")
           for name in ("induction_maintainers", "texts_per_maintainer")}


def read_strata(path) -> tuple:
    """(the pool's strata, largest first, and {maintainer: stratum} for every maintainer the design names), from the
    pool's design file (annotations/ground_truth_candidates.json): its "places_per_stratum" names every stratum,
    "stratum_sizes" their sizes, and "collapsed_maintainers" the maintainers of the stratum SMALL."""
    design = read_json(path)
    places, sizes = design.get("places_per_stratum"), design.get("stratum_sizes") or {}
    collapsed = design.get("collapsed_maintainers")
    if not isinstance(places, dict) or not isinstance(collapsed, list) or SMALL not in places \
            or design.get("strata") != len(places):
        raise Stop(f"{repo_path(path)} doesn't describe the pool's strata as 040 reads them (a \"places_per_stratum\" "
                   f"object naming every stratum, {SMALL!r} among them, a \"strata\" count equal to their number, and a "
                   f"\"collapsed_maintainers\" list), so 040 can't draw its texts by stratum. Give the pool's design "
                   f"file with --pool_design (the file the pool was drawn with), then run "
                   f"`py 040_induce_schema/run.py` again.")
    strata = sorted(places, key=lambda s: (-sizes.get(s, 0), s))
    of = {m: m for m in places if m != SMALL}
    of.update({m: SMALL for m in collapsed if m not in of})
    return strata, of


def _small_order(ids: list, seed: int) -> list:
    """The stratum SMALL's induction candidates in a fixed random order, drawn as 030 draws each maintainer's
    (030_split/030_split_helpers/moves.py, induction_candidates): the stratum's name in place of the maintainer's."""
    return random.Random(f"{seed}/{SMALL}").sample(sorted(ids), len(ids))


def draw(orders: dict, strata: list, records: dict, per: int) -> tuple:
    """(taken {stratum: [ids]}, skipped [{"id", "stratum", "twin_kind", "twin_of"}], title-only twins kept
    {stratum: n}): per texts from each stratum, in rounds (one text from each stratum, in the order of strata, per
    round), each taken in its stratum's order; a whole-text or notes-only twin of a text already drawn is skipped.

    >>> recs = {"a": {"title": "Snow", "notes": "Daily snow."}, "b": {"title": "Ice", "notes": "Daily snow."},
    ...         "c": {"title": "Snow", "notes": "Weekly snow."}, "d": {"title": "Fire", "notes": "Burned area."}}
    >>> draw({"S1": ["a", "c"], "S2": ["b", "d"]}, ["S1", "S2"], recs, 2)
    ({'S1': ['a', 'c'], 'S2': ['d']}, [{'id': 'b', 'stratum': 'S2', 'twin_kind': 'notes only', 'twin_of': 'a'}], {'S1': 1, 'S2': 0})
    """
    taken = {s: [] for s in strata}
    drawn, skipped, title_only = {}, [], collections.Counter()
    queues = {s: iter(orders.get(s, [])) for s in strata}
    for _ in range(per):
        for s in strata:
            for rid in queues[s]:
                kind = twin_kinds({rid: records[rid]}, drawn)[rid]
                if kind in SKIPPED:
                    skipped.append({"id": rid, "stratum": s, "twin_kind": kind,
                                    "twin_of": _twin_of(records[rid], drawn, kind)})
                    continue
                title_only[s] += kind == KEPT_TWIN
                taken[s].append(rid)
                drawn[rid] = records[rid]
                break
    return taken, skipped, {s: title_only[s] for s in strata}


def _twin_of(record: dict, drawn: dict, kind: str) -> str:
    """The first text drawn that record is a twin of, of that kind (for the evidence file)."""
    return next(lid for lid, r in drawn.items() if twin_kinds({"x": record}, {lid: r})["x"] == kind)


def pick_texts(inputs: dict, settings: dict) -> Texts:
    check_settings(settings, SPECS)
    records = load_records(inputs["records"])
    splits = read_json(inputs["splits"])
    induction = splits["induction_candidates"]
    seed = (splits.get("drawn") or {}).get("settings", {}).get("induction_seed")
    if not isinstance(seed, int):
        raise Stop(f"{repo_path(inputs['splits'])} doesn't record the seed 030 drew its induction candidates' order "
                   f"with (drawn, settings, induction_seed), so 040 can't order the stratum {SMALL!r} and the texts "
                   f"the same way every time. Delete {repo_path(inputs['splits'])}, run `py 030_split/run.py`, then "
                   f"run `py 040_induce_schema/run.py` again.")
    strata, stratum_of = read_strata(inputs["pool_design"])
    per = settings["texts_per_stratum"]

    texts = Texts(seed=seed)
    texts.pool = {r["id"]: records[r["id"]] for r in splits["ground_truth_candidates"]["records"] if r["id"] in records}
    orders, maintainers, unknown = collections.defaultdict(list), collections.defaultdict(set), collections.Counter()
    small = []
    for row in induction["records"]:                  # grouped by maintainer, each in 030's order
        if row["id"] not in records:
            raise Stop(f"Induction candidate {row['id']} is not in 020's records ({repo_path(inputs['records'])}): "
                       f"{repo_path(inputs['splits'])} and the records are out of step (for example, 020 was run again "
                       f"on another harvest after 030 wrote its file; every cause: docs/running_on_nasa_laptop.md, "
                       f"section 7), so 040 can't pick its texts. Delete {repo_path(inputs['splits'])}, "
                       f"run `py 030_split/run.py`, then run `py 040_induce_schema/run.py` again.")
        texts.candidates[row["id"]] = records[row["id"]]
        m = row["maintainer"]
        if m not in stratum_of:
            unknown[m] += 1                           # not in the pool's design: counted with the small maintainers
        s = stratum_of.get(m, SMALL)
        maintainers[s].add(m)
        if s == SMALL:
            small.append(row["id"])
        else:
            orders[s].append(row["id"])
    orders[SMALL] = _small_order(small, seed)

    taken, texts.skipped, title_only = draw(orders, strata, records, per)
    skipped = collections.defaultdict(collections.Counter)
    for k in texts.skipped:
        skipped[k["stratum"]][k["twin_kind"]] += 1
    texts.strata = [{"stratum": s, "maintainers": len(maintainers[s]), "candidates": len(orders[s]),
                     "taken": len(taken[s]), "skipped": {k: skipped[s][k] for k in SKIPPED},
                     "title_only_kept": title_only[s]} for s in strata]
    chosen = [rid for s in strata for rid in taken[s]]
    in_stratum = {rid: s for s in strata for rid in taken[s]}
    for rid in random.Random(f"{seed}/{READING_ORDER}").sample(sorted(chosen), len(chosen)):
        record = records[rid]
        texts.items.append({"id": rid, "maintainer": record["maintainer"], "stratum": in_stratum[rid],
                            "record": record,                                  # record: for the prompt's field names
                            "title": " ".join((record.get("title") or "").split()),   # as a component instance
                            "text": full_text(record), "pieces": pieces(record, settings["max_chars"])})

    if unknown:
        texts.notes.append(f"{len(unknown)} maintainer(s) with induction candidates aren't named in "
                           f"{repo_path(inputs['pool_design'])} (the pool's design), so 040 counts them with the "
                           f"stratum {SMALL!r}: " + named([f"{m} ({n:,} candidates)" for m, n in unknown.most_common()],
                                                          5, "; ")
                           + ". They joined the catalog (or changed their name) after the pool was drawn. Nothing to "
                             "do if they are small; the report's section *What this run worked on* lists every "
                             "stratum.")
    short = [r for r in texts.strata if r["taken"] < per]
    if short:
        texts.notes.append(f"You asked for {per} texts from each stratum (texts_per_stratum), but {len(short)} "
                           f"stratum(s) have fewer induction candidates that aren't twins of a text already drawn, so "
                           f"they give fewer: " + named([f"{r['stratum']} gives {r['taken']}" for r in short], 5, "; ")
                           + f". This run learns from {len(texts.items)} texts instead of {per * len(strata)}. Nothing "
                             f"to do if that's enough; to take the same number from every stratum, run with "
                             f"`--texts_per_stratum {max(1, min(r['taken'] for r in short))}`.")
    split = sum(len(t["pieces"]) > 1 for t in texts.items)
    log.info(f"  {len(texts.items)} texts from {len(strata)} strata ({len(texts.skipped)} twins skipped)"
             + (f"; {split} split into pieces" if split else ""))
    return texts
