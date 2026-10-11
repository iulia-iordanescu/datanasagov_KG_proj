"""
texts.py -- stage 1: pick the texts the schema is learned from.

From 030's induction candidates, take the first texts_per_maintainer records
of each of the induction_maintainers largest maintainers. 030 keeps each
maintainer's candidates in a fixed random order, so these are a random
sample of each maintainer, and taking more later keeps these.

Each text is the record's text fields, split into pieces of at most
max_chars (common/common_helpers/chunking.py): almost always one piece.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from common.audit import log
from common.chunking import full_text, pieces
from common.records_io import load_records
from common.report import named
from common.step import check_settings
from common.step import repo_path
from common.stop import Stop


@dataclass
class Texts:
    items: list = field(default_factory=list)        # {"id", "maintainer", "record", "title", "text", "pieces"}
    maintainers: list = field(default_factory=list)  # {"maintainer", "rank", "records", "eligible", "taken"}
    notes: list = field(default_factory=list)        # where the texts differ from what the settings ask for
    pool: dict = field(default_factory=dict)         # {id: record}: the ground truth candidates pool, for the twin table
    candidates: list = field(default_factory=list)   # every induction candidate's record, for the twin table


def pick_texts(inputs: dict, settings: dict) -> Texts:
    check_settings(settings, {"induction_maintainers": 1, "texts_per_maintainer": 1, "min_support": 1})
    records = load_records(inputs["records"])
    splits = json.loads(Path(inputs["splits"]).read_text(encoding="utf-8"))
    induction = splits["induction_candidates"]
    chosen = induction["maintainers"][:settings["induction_maintainers"]]
    wanted = {m["maintainer"] for m in chosen}
    per = settings["texts_per_maintainer"]

    texts = Texts()
    texts.pool = {r["id"]: records[r["id"]] for r in splits["ground_truth_candidates"]["records"] if r["id"] in records}
    texts.candidates = [records[r["id"]] for r in induction["records"] if r["id"] in records]
    taken = {m: 0 for m in wanted}
    for row in induction["records"]:                  # grouped by maintainer, each in its order
        m = row["maintainer"]
        if m in wanted and row["position"] < per:
            record = records.get(row["id"])
            if record is None:
                raise Stop(f"Induction candidate {row['id']} is not in 020's records ({repo_path(inputs['records'])}): "
                           f"{repo_path(inputs['splits'])} and the records are out of step (020 was likely run again "
                           f"after 030 wrote its file), so 040 can't pick its texts. Delete {repo_path(inputs['splits'])}, "
                           f"run `py 030_split/run.py`, then run `py 040_induce_schema/run.py` again.")
            texts.items.append({"id": row["id"], "maintainer": m, "record": record,   # record: for the prompt's field names
                                "title": " ".join((record.get("title") or "").split()),   # as a component instance
                                "text": full_text(record), "pieces": pieces(record, settings["max_chars"])})
            taken[m] += 1
    texts.maintainers = [{**m, "taken": taken[m["maintainer"]]} for m in chosen]
    if len(chosen) < settings["induction_maintainers"]:
        texts.notes.append(f"You asked for {settings['induction_maintainers']} maintainers "
                           f"(induction_maintainers), but only {len(chosen)} have records to learn from, "
                           f"so this run learns from all {len(chosen)}. Nothing to do; to ask for exactly what there "
                           f"is, run with `--induction_maintainers {len(chosen)}`.")
    short = [m for m in texts.maintainers if m["taken"] < per]
    if short:
        texts.notes.append(f"You asked for {per} texts from each maintainer (texts_per_maintainer), but "
                           f"{len(short)} maintainer(s) don't have that many, so they give fewer: "
                           + named([f"{m['maintainer']} gives {m['taken']}" for m in short], 5, "; ")
                           + f". This run learns from {len(texts.items)} texts instead of {per * len(chosen)}. Nothing "
                           f"to do if that's enough; to take the same number from every maintainer, run with "
                           f"`--texts_per_maintainer {max(1, min(m['taken'] for m in short))}`.")
    split = sum(len(t["pieces"]) > 1 for t in texts.items)
    log.info(f"  {len(texts.items)} texts from {len(chosen)} maintainers"
             + (f"; {split} split into pieces" if split else ""))
    return texts
