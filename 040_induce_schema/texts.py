"""
texts.py -- stage 1: pick the texts the schema is learned from.

From 030's induction candidates, take the first texts_per_maintainer records
of each of the induction_maintainers largest maintainers. 030 keeps each
maintainer's candidates in a fixed random order, so these are a random
sample of each maintainer, and taking more later keeps these.

Each text is the record's text fields, split into pieces of at most
max_chars (common/chunking.py): almost always one piece.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from common.audit import log
from common.chunking import full_text, pieces
from common.records_io import load_records
from common.step import check_settings


@dataclass
class Texts:
    items: list = field(default_factory=list)        # {"id", "maintainer", "title", "text", "pieces"}
    maintainers: list = field(default_factory=list)  # {"maintainer", "rank", "records", "eligible", "taken"}
    notes: list = field(default_factory=list)        # where the texts differ from what the settings ask for


def pick_texts(inputs: dict, settings: dict) -> Texts:
    check_settings(settings, {"induction_maintainers": 1, "texts_per_maintainer": 1, "min_support": 1})
    records = load_records(inputs["records"])
    splits = json.loads(Path(inputs["splits"]).read_text(encoding="utf-8"))
    induction = splits["induction_candidates"]
    chosen = induction["maintainers"][:settings["induction_maintainers"]]
    wanted = {m["maintainer"] for m in chosen}
    per = settings["texts_per_maintainer"]

    texts = Texts()
    taken = {m: 0 for m in wanted}
    for row in induction["records"]:                  # grouped by maintainer, each in its order
        m = row["maintainer"]
        if m in wanted and row["position"] < per:
            record = records.get(row["id"])
            if record is None:
                raise ValueError(f"induction candidate {row['id']} is not in 020's records; "
                                 f"splits.json and records.jsonl are out of step (rerun 030)")
            texts.items.append({"id": row["id"], "maintainer": m, "title": record.get("title") or "",
                                "text": full_text(record), "pieces": pieces(record, settings["max_chars"])})
            taken[m] += 1
    texts.maintainers = [{**m, "taken": taken[m["maintainer"]]} for m in chosen]
    if len(chosen) < settings["induction_maintainers"]:
        texts.notes.append(f"You asked for {settings['induction_maintainers']} maintainers "
                           f"(induction_maintainers), but only {len(chosen)} have records to learn from, "
                           f"so all {len(chosen)} are used.")
    short = [m for m in texts.maintainers if m["taken"] < per]
    if short:
        texts.notes.append(f"You asked for {per} texts from each maintainer (texts_per_maintainer), but "
                           f"{len(short)} maintainer(s) don't have that many, so they give fewer: "
                           + "; ".join(f"{m['maintainer']} gives {m['taken']}" for m in short[:5])
                           + (f" and {len(short) - 5} more" if len(short) > 5 else "") + ".")
    split = sum(len(t["pieces"]) > 1 for t in texts.items)
    log.info(f"  {len(texts.items)} texts from {len(chosen)} maintainers"
             + (f"; {split} split into pieces" if split else ""))
    return texts
