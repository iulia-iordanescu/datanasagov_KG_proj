"""
common/common_helpers/cache.py -- keeps every model answer a step has paid for, so a rerun
reuses it.

    outputs/intermediate_results/<step>/cache/<stage>.json

Shared by the steps that call a model (040, 050, 060 and 070).

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
    blob = json.dumps([llm.cache_identity(), *parts], sort_keys=True, ensure_ascii=False, default=str)
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


def ask_cached(cache: Cache, calls, prompt: str, plan: str, read_timeout: int = llm.READ_TIMEOUT) -> dict:
    """The model's answer to one filled prompt, from this stage's cache if it
    holds it, else from one model call (the run's first paid call shows plan
    and asks first: common/common_helpers/llm.py, PaidCalls), stored at once.
    The key is the prompt exactly as sent, so every value filled into it
    counts. Shared by every stage that asks one prompt at a time: 040's
    labeling, merging and defining, and 070's translation table. (Extraction
    asks many text pieces at once: common/common_helpers/extraction.ask_model.)"""
    k = key(prompt)
    reply = cache.get(k)
    if reply is None:
        calls.paid.start(plan)
        reply = llm.call_llm_json(prompt, read_timeout=read_timeout)
        calls.paid.made_call()
        cache.put(k, reply)
    return reply


def ask_split(ask, batch: list, refused: list) -> list:
    """The answers to a batch, asked with ask(batch) -> answer. When the service refuses the batch (llm.ApiError: a
    content filter, a cut-off, no usable answer) or its answer is twice not JSON (llm.BadReply), each half is asked
    instead, and so on down to single items: so one item the service won't answer about costs that item alone, not
    its whole batch, and the step goes on. A single item still refused is added to refused as (item, why).
    One refused item in a batch of 80 costs about 2 x log2(80), some 13, extra calls, each smaller."""
    try:
        return [ask(batch)]
    except (llm.ApiError, llm.BadReply) as e:
        if len(batch) == 1:
            refused.append((batch[0], str(e)))
            return []
        llm.log.warning(f"The model's answer to a batch of {len(batch)} was refused ({e}); asking for each half "
                        f"separately, to find the item(s) it won't answer about. Nothing to do.")
        mid = len(batch) // 2
        return ask_split(ask, batch[:mid], refused) + ask_split(ask, batch[mid:], refused)
