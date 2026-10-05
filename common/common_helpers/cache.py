"""
common/common_helpers/cache.py -- keeps every model answer a step has paid for, so a rerun
reuses it.

    outputs/intermediate_results/<step>/cache/<stage>.json

Shared by the steps that call a model (040, 050 and 060).

Each file maps a KEY to an answer. The key is a fingerprint of everything
that decides the answer: the model, the exact prompt text, and what was sent
(a text piece, a batch of component instances and the labels in use before
it, ...). Change any of them, e.g. edit a prompt file, and the key changes,
so that answer is asked again; everything else is still reused. A call that failed is never
stored, so the next run asks it again.

The cache holds paid work: deleting it (or all of outputs/) means paying for
those calls again.
"""
from __future__ import annotations

import hashlib
import json
import threading
from pathlib import Path

from common import llm
from common.files import write_json


def key(*parts) -> str:
    """A fingerprint of the model and everything else that decides an answer."""
    blob = json.dumps([llm.MODEL, *parts], sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:24]


class Cache:
    """One stage's answers, in one JSON file, written after every new answer
    (under a temporary name, renamed when complete), so a crash or Ctrl+C
    keeps every answer already paid for."""

    def __init__(self, folder: Path, stage: str):
        self.path = Path(folder) / f"{stage}.json"
        self._lock = threading.Lock()
        self.answers = {}
        if self.path.exists():
            try:
                self.answers = json.loads(self.path.read_text(encoding="utf-8"))
            except (ValueError, OSError):
                self.answers = {}                 # unreadable: ask again
        self.reused = 0

    def get(self, k: str):
        if k in self.answers:
            self.reused += 1
            return self.answers[k]
        return None

    def put(self, k: str, answer) -> None:
        with self._lock:                          # extraction stores from several threads
            self.answers[k] = answer
            write_json(self.path, self.answers, indent=None)
