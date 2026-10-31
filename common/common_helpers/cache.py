"""
common/common_helpers/cache.py -- keeps every model answer a step has paid for, so a rerun
reuses it.

    outputs/intermediate_results/<step>/cache/<stage>.json

Shared by the steps that call a model (040, 050, 060, and 070).

Each file maps a KEY to an answer. The key is a fingerprint of everything
that decides the answer: the model, the exact prompt text, and what was sent
(a text piece, a batch of component instances, and the labels in use before
it, ...). Change any of them, e.g. edit a prompt file, and the key changes,
so that answer is asked again; everything else is still reused. A call that failed is not
stored, so the next run asks it again, with one exception: an answer cut off at the length limit
(llm.CutOff) is stored as a cut-off marker, and while MAX_ANSWER_TOKENS (common/common_helpers/llm.py)
is unchanged, a rerun reuses the failure instead of paying for the same cut again. Raising
MAX_ANSWER_TOKENS asks again; so does a new thinking setting, for a model it is sent to (it is part
of the key: llm.cache_identity). So does the setting repeat from 2 on (llm.REPEAT): each repeat of a
recipe has answers of its own, so repeats are independent answers of the model; repeat 1, the default,
uses the answers saved before the setting existed.

Only an answer of the shape the stage reads is stored: each stage passes its shape check (check(answer)
-> what is wrong, or None), and an answer of the wrong shape is asked once more, then fails like one
that isn't JSON (llm.call_llm_json). An answer stored before, of the wrong shape (by an older version
of the code, or an edited file), is ignored and asked again, and the run's warnings name the file.

A file that can't be read (not JSON, or not readable) is treated as empty, so its answers are asked again: it is
first copied aside, as <stage>.unreadable.json (then -2, -3, ...), and the run warns, naming both files.

The cache holds paid work: deleting it (or all of outputs/) means paying for
those calls again. What a saved answer depends on, for a person: docs/running_on_nasa_laptop.md, section 5.
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
        self.stage = stage
        self.path = Path(folder) / f"{stage}.json"
        self._lock = threading.Lock()
        self.answers = {}
        if self.path.exists():
            try:
                self.answers = json.loads(self.path.read_text(encoding="utf-8"))
            except (ValueError, OSError) as e:
                self.answers = {}                 # unreadable: ask again, but keep a copy and say so
                self._unreadable(e)
        self.reused = 0
        self.wrong_shape = []                     # what was wrong with each stored answer ignored for its shape

    def _unreadable(self, error) -> None:
        """The file can't be read: copy it aside (never lost: it may hold paid answers), and warn."""
        import shutil
        from common.step import repo_path
        aside, n = self.path.with_name(f"{self.stage}.unreadable.json"), 2
        while aside.exists():
            aside, n = self.path.with_name(f"{self.stage}.unreadable-{n}.json"), n + 1
        try:
            shutil.copy2(self.path, aside)
            kept = f"a copy of it is kept as {repo_path(aside)}"
        except OSError as e:
            kept = f"it couldn't be copied aside either ({e}): copy it yourself before this run writes over it"
        note = (f"{repo_path(self.path)} couldn't be read ({error}), so its saved answers are treated as none: the "
                f"model is asked them again (paid for again), and the file is written over with the new answers; "
                f"{kept}. Usually a file cut short (a full disk) or edited by hand. If the old answers matter, stop "
                f"the run (Ctrl+C), repair that copy, and put it back as {self.path.name}.")
        llm.RUN_WARNINGS.append(note)
        llm.log.warning(note)

    def get(self, k: str, check=None):
        """The answer stored under k, or None (a cut-off marker is no answer: see cut_off). With check (the stage's
        shape check), an answer of the wrong shape is None too, so it is asked again, and the run's warnings say so."""
        if k in self.answers and not _is_cut_off(self.answers[k]):
            wrong = check(self.answers[k]) if check else None
            if wrong:
                self._ignored(wrong)
                return None
            self.reused += 1
            return self.answers[k]
        return None

    def _ignored(self, wrong: str) -> None:
        """One more stored answer of the wrong shape ignored: the run's warning about this file, kept up to date."""
        from common.step import repo_path
        with self._lock:
            note = self._note()
            self.wrong_shape.append(wrong)
            if note in llm.RUN_WARNINGS:
                llm.RUN_WARNINGS.remove(note)
            llm.RUN_WARNINGS.append(self._note())
        llm.log.warning(f"An answer saved in {repo_path(self.path)} is JSON of the wrong shape ({wrong}), so it is "
                        f"ignored and the model is asked again. Nothing to do.")

    def _note(self) -> str:
        from common.step import repo_path
        n = len(self.wrong_shape)
        return (f"{n} answer(s) saved in {repo_path(self.path)} were JSON of the wrong shape (the first: "
                f"{self.wrong_shape[0] if n else ''}), so they were ignored and the model was asked again; the new "
                f"answers replace them in that file. Nothing to do.")

    def cut_off(self, k: str) -> str | None:
        """Why the answer under k was cut off in an earlier run, when it was cut off with the MAX_ANSWER_TOKENS of
        this run (asking again would get the same cut); else None."""
        stored = self.answers.get(k)
        if _is_cut_off(stored) and stored[CUT_OFF].get("max_answer_tokens") == llm.MAX_ANSWER_TOKENS:
            return stored[CUT_OFF].get("why") or "the answer was cut off at the longest length allowed"
        return None

    def cut_off_usage(self, k: str) -> dict:
        """The service's token counts of the cut-off answer under k ({} when none were kept)."""
        stored = self.answers.get(k)
        return (stored[CUT_OFF].get("usage") or {}) if _is_cut_off(stored) else {}

    def put_cut_off(self, k: str, error) -> None:
        """Keep that the answer under k was cut off (llm.CutOff), so a rerun with the same limit doesn't pay again."""
        self.put(k, {CUT_OFF: {"why": str(error), "max_answer_tokens": llm.MAX_ANSWER_TOKENS,
                               "thinking": llm.THINKING, "usage": getattr(error, "usage", None) or {}}})

    def put(self, k: str, answer) -> None:
        with self._lock:                          # extraction stores from several threads
            self.answers[k] = answer
            write_json(self.path, self.answers, indent=None)


#: The key of a cut-off marker: {CUT_OFF: {"why", "max_answer_tokens", "thinking", "usage"}} stored in place of an answer.
CUT_OFF = "_pipeline_cut_off"


def _is_cut_off(stored) -> bool:
    return isinstance(stored, dict) and CUT_OFF in stored


#: The words a failure reused from the cache ends with.
NOT_ASKED_AGAIN = "(cut off in an earlier run with the same settings, so not asked again)"


def ask_cached(cache: Cache, calls, prompt: str, plan: str, read_timeout: int = llm.READ_TIMEOUT,
               check=None) -> dict:
    """The model's answer to one filled prompt, from this stage's cache if it
    holds it, else from one model call (the run's first paid call shows plan
    and asks first: common/common_helpers/llm.py, PaidCalls), stored at once.
    The key is the prompt exactly as sent, so every value filled into it
    counts. Shared by every stage that asks one prompt at a time: 040's
    labeling, merging, and defining, and 070's translation table. (Extraction
    asks many text pieces at once: common/common_helpers/extraction.ask_model.)
    An answer cut off in an earlier run with the same limit raises llm.CutOff again without a call (Cache.cut_off).
    check: the stage's shape check, check(answer) -> what is wrong with it, or None; an answer of the wrong shape
    is never stored (asked once more, then llm.BadReply), and one stored before is asked again (Cache.get).
    Each call's end goes to calls.paid.outcome (progress, the failed-call record; not the early stop)."""
    k = key(prompt)
    reply = cache.get(k, check)
    if reply is None:
        cut = cache.cut_off(k)
        if cut:
            raise llm.CutOff(f"{cut} {NOT_ASKED_AGAIN}: {llm.cut_off_advice(cache.cut_off_usage(k))}")
        calls.paid.start(plan)
        try:
            reply = llm.call_llm_json(prompt, read_timeout=read_timeout, check=check)
        except Exception as e:
            if isinstance(e, llm.CutOff):
                cache.put_cut_off(k, e)
            calls.paid.outcome({"stage": cache.stage}, prompt, e, watched=False)
            raise
        calls.paid.made_call()
        cache.put(k, reply)
        calls.paid.outcome({"stage": cache.stage}, prompt, watched=False)
    return reply


def needs(**fields):
    """A shape check (ask_cached's check) for an answer that must hold each of fields with its type, e.g.
    needs(labels=dict): check(answer) says which field is missing or of another type, or None when none is."""
    def check(answer: dict) -> str | None:
        if not isinstance(answer, dict):                  # only in a cache file edited by hand
            return f"the answer should be a JSON object, but is a JSON {_json_name(type(answer))}"
        for name, kind in fields.items():
            value = answer.get(name)
            if not isinstance(value, kind):
                got = "missing" if name not in answer else f"a JSON {_json_name(type(value))}"
                return f'"{name}" should be a JSON {_json_name(kind)}, but is {got}'
        return None
    return check


def _json_name(kind: type) -> str:
    """What JSON calls a Python type: dict -> "object", list -> "list", str -> "string", None -> "null", ..."""
    return {dict: "object", list: "list", str: "string", bool: "true or false", int: "number", float: "number",
            type(None): "null"}.get(kind, kind.__name__)


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
