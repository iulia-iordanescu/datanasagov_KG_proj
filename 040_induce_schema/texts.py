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


@dataclass
class Texts:
    items: list = field(default_factory=list)        # {"id", "maintainer", "title", "text", "pieces"}
    maintainers: list = field(default_factory=list)  # {"maintainer", "rank", "records", "eligible", "taken"}


def check_settings(settings: dict) -> None:
    for name in ("induction_maintainers", "texts_per_maintainer", "min_support", "workers"):
        if settings[name] < 1:
            raise ValueError(f"{name} must be at least 1 (got {settings[name]})")
    if settings["max_chars"] < 1000:
        raise ValueError(f"max_chars must be at least 1000 (got {settings['max_chars']})")


def pick_texts(inputs: dict, settings: dict) -> Texts:
    check_settings(settings)
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
    split = sum(len(t["pieces"]) > 1 for t in texts.items)
    log.info(f"  {len(texts.items)} texts from {len(chosen)} maintainers"
             + (f"; {split} split into pieces" if split else ""))
    return texts
