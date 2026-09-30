"""
common/llm.py -- the one place a model is called.

Used by every step that asks a model something: 040 (inducing the schema),
050 (drafting ground truth) and 060 (extracting). The Ask Sage client was
moved from to_be_reshaped/llm_client.py, with its retries and re-asks now
logged through common.audit's log (so they reach the step's log file)
instead of printed.

It holds, in this order:

    THE ASK SAGE CLIENT
        call_llm          send a prompt, get the reply text; retries rate
                          limits and server errors with backoff
        call_llm_json     the same, parsed as a JSON object; re-asks once if
                          the reply is not one
    PROMPT SAFETY
        fence_safe        keeps a record from ending its data block early
    A PAID RUN
        list_models       the model names Ask Sage lists (free; see py models.py)
        PaidCalls         asks once before a run's first paid call (showing
                          any notes about the run first), makes a one-line
                          test call, and counts the calls
        Calls, paid_calls what a step's stages share: PaidCalls and the
                          folder its answers are cached in (common/cache.py)
        run_parallel      runs jobs a few at a time; Ctrl-C cancels those
                          not yet started
        confirm           the stop itself

What the steps that extract triple instances with entity classes share
(the prompt's rules, the reply format, the BEGIN/END lines) is in
common/extraction.py and common/prompts/.

    from common import llm
    calls = llm.paid_calls(settings, output, notes)   # once per run
    calls.paid.start("plan in words")                 # before the first paid call
    data = llm.call_llm_json(prompt)                  # a dict, or raises

Needs a .env in the repository folder with ASKSAGE_EMAIL and
ASKSAGE_API_KEY, and the packages requests and python-dotenv.
"""

import json
import os
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

import requests
from dotenv import load_dotenv

from common.audit import log

#: The model the calls use: the default of every step's `model` setting,
#: which paid_calls() puts here for the run. `py models.py` lists the models
#: Ask Sage shows your account (a listed model may still refuse you: the
#: run's first call, a one-line test, finds out for the price of that call).
#: It is part of every cache key (common/cache.py), so changing it asks again.
MODEL = "google-claude-sonnet-5"

# ------------------------------ the Ask Sage client -------------------------

USER_BASE = "https://api.asksage.ai.nasa.gov/user"
SERVER_BASE = "https://api.asksage.ai.nasa.gov/server"
_token_cache = {}


def _asksage_token():
    if "token" not in _token_cache:
        load_dotenv()
        email, key = os.getenv("ASKSAGE_EMAIL"), os.getenv("ASKSAGE_API_KEY")
        if not (email and key):
            sys.exit("Set ASKSAGE_EMAIL and ASKSAGE_API_KEY (e.g. in .env).")
        login = requests.post(f"{USER_BASE}/get-token-with-api-key",
                              json={"email": email, "api_key": key},
                              timeout=(5, 60))
        login.raise_for_status()
        payload = login.json()["response"]
        _token_cache["token"] = (payload["access_token"]
                                 if isinstance(payload, dict) else payload)
    return _token_cache["token"]


def list_models() -> list:
    """The model names Ask Sage lists for your account. Free: listing is not a
    model call. Being listed doesn't guarantee access."""
    resp = requests.post(f"{SERVER_BASE}/get-models", headers={"x-access-tokens": _asksage_token()},
                         timeout=(5, 60))
    resp.raise_for_status()
    body = resp.json()
    items = body.get("response", body.get("models", body)) if isinstance(body, dict) else body
    if isinstance(items, dict):
        items = items.get("data", list(items))
    names = []
    for item in items if isinstance(items, list) else []:
        if isinstance(item, str):
            names.append(item)
        elif isinstance(item, dict):
            name = item.get("name") or item.get("id") or item.get("model")
            if name:
                names.append(str(name))
    if not names:
        raise ValueError(f"Ask Sage's model list came in a shape this code doesn't read: {str(body)[:300]}")
    return sorted(set(names))


def _as_list(v):
    """Model output shape guard. call_llm_json guarantees the TOP level is an
    object, but nothing guarantees the type of a field inside it: a model can
    answer {"triples": {...}} or {"entities": [...]}. Iterating the wrong type
    raises AttributeError deep in a loop, so every field read from a reply is
    coerced here and a wrong shape degrades to empty rather than crashing."""
    return v if isinstance(v, list) else []


def _as_dict(v):
    return v if isinstance(v, dict) else {}


class BadReply(ValueError):
    """A reply that arrived but is not usable as the JSON object we asked
    for. Kept separate from a transport error so it retries the PROMPT
    rather than the connection."""


class ApiError(Exception):
    """The gateway accepted the request and answered HTTP 200, but the body
    carries an error object instead of a completion.

    Deliberately NOT in call_llm's retry tuple. The observed cases are
    permission and validation failures (e.g. code "model_not_permitted",
    http_status 400), which will fail identically on every retry; retrying
    would burn four calls and then report the same thing. Only a 429 or a
    5xx inside the body is worth another attempt, and that case is converted
    to RuntimeError below so the normal backoff handles it."""


def call_llm(prompt, attempts=4, read_timeout=180):
    """Ask Sage gateway. Retries with exponential backoff on rate limits and
    transient server errors.

    dataset/limit_references are set deliberately. Per the Ask Sage API docs
    dataset defaults to 'all' and limit_references defaults to None, meaning
    every call retrieves from the tenant's datasets and prepends the results.
    That is wrong here twice over: the extraction prompt orders the model to
    use nothing but the text in front of it, and retrieved references are
    billed input tokens on all N calls. There is no max-tokens parameter on
    this endpoint, so output length cannot be capped from here."""
    for attempt in range(attempts):
        try:
            # Fetched inside the loop, not once before it: a 401 clears the
            # cache below, and the next attempt must log in again.
            resp = requests.post(f"{SERVER_BASE}/query",
                                 headers={"x-access-tokens": _asksage_token()},
                                 json={"message": prompt, "model": MODEL,
                                       "temperature": 0,
                                       "dataset": "none",
                                       "limit_references": 0},
                                 timeout=(5, read_timeout))
            if resp.status_code == 401:
                # The token is cached for the whole run, so one expiry would
                # otherwise fail every remaining call - and each failure still
                # costs a request. Drop it and log in again on the next try.
                _token_cache.pop("token", None)
                raise RuntimeError("HTTP 401 - token dropped, will re-login")
            if resp.status_code in (429, 500, 502, 503, 504):
                raise RuntimeError(f"HTTP {resp.status_code}")
            resp.raise_for_status()
            body = resp.json()
            # Ask Sage answers HTTP 200 with status 200 even when the request
            # was refused, putting the real outcome in an "error" object and
            # an apology in "message". Observed shape:
            #   {"status": 200,
            #    "error": {"code": "model_not_permitted", "http_status": 400,
            #              "requested_model": "..."},
            #    "message": "Sorry, this model is not authorized ..."}
            # Without this check the apology reaches the JSON parser and the
            # call fails as "Expecting value: line 1 column 1" - once per
            # text, with nothing naming the real cause.
            body = body if isinstance(body, dict) else {}
            err = body.get("error")
            if isinstance(err, dict) and (err.get("code")
                                          or err.get("http_status")):
                code = err.get("code") or "error"
                inner = err.get("http_status")
                detail = f"{code} (http_status {inner}): {body.get('message')}"
                if inner in (429, 500, 502, 503, 504):
                    raise RuntimeError(detail)      # worth retrying
                raise ApiError(detail)              # will not fix itself
            # A numeric top-level status of 400 or more is also a refusal.
            status = body.get("status")
            if isinstance(status, (int, str)) and str(status).isdigit() \
                    and int(status) >= 400:
                raise RuntimeError(f"API status {status}: "
                                   f"{str(body.get('message'))[:200]}")
            # .get("message") can be absent OR present-and-null; either way
            # callers must never receive None and call .strip() on it.
            return (body or {}).get("message") or ""
        except (RuntimeError, ValueError,
                requests.ConnectionError, requests.Timeout) as e:
            if attempt == attempts - 1:
                raise
            wait = 2 ** attempt * 5          # 5s, 10s, 20s
            log.warning(f"transient API error ({e}), retrying in {wait}s")
            time.sleep(wait)


def _best_effort_json(text):
    """Parse JSON from model output: strip fences, else take the largest
    {...} substring (models sometimes wrap JSON in prose)."""
    cleaned = re.sub(r"^```(json)?|```$", "", text.strip(),
                     flags=re.MULTILINE).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start != -1 and end > start:
            return json.loads(cleaned[start:end + 1])   # may raise; caller handles
        raise


def call_llm_json(prompt, retries=1, read_timeout=180):
    """Return the JSON OBJECT the prompt asked for, or raise.

    Every caller immediately does .get() on the result, so a reply that
    parses into a list, a string or a number is as useless as one that does
    not parse at all - and used to surface three frames away as an opaque
    AttributeError. Both failures are treated the same way here: re-ask once
    with a correction, then give up."""
    for attempt in range(retries + 1):
        try:
            data = _best_effort_json(call_llm(prompt, read_timeout=read_timeout))
            if not isinstance(data, dict):
                raise BadReply(f"expected a JSON object, got "
                               f"{type(data).__name__}")
            return data
        except (json.JSONDecodeError, BadReply) as e:
            if attempt == retries:
                raise
            log.warning(f"unusable reply ({e}); re-asking once")
            prompt += ("\n\nYour last reply was not a valid JSON object. "
                       "Return ONLY the JSON object, no fences, no prose.")


# ------------------------------ prompt safety ------------------------------

def fence_safe(text: str, end_line: str) -> str:
    """Defang end_line wherever it appears inside text.

    A prompt wraps each record between a BEGIN and an END line, and tells
    the model everything between them is data. A delimiter only delimits if
    the data cannot contain it, so any copy of end_line inside the record
    is spaced out ("-----" becomes "- - - - -"), and the record can never
    end the block early and have the rest of its text read as
    instructions."""
    return text.replace(end_line, " ".join(end_line.replace("-", " - ").split()))


# ------------------------------ a paid run ---------------------------------

class PaidCalls:
    """Asks once, just before a run's first paid call, and counts the calls.

    A stage calls start(plan) before it makes any call a cache couldn't
    answer, and made_call() for each call. The first start() logs the plan,
    asks the person to press Enter (unless confirm is False, for runs with
    nobody at the keyboard), and makes one tiny test call, so a wrong model
    name or key fails once here instead of once per text. A run whose every
    answer comes from the cache never asks and never pays. Declining exits
    the run having spent nothing.

    notes: what the step found, BEFORE any call, that differs from what the
    person asked for (an id that isn't in the catalog, fewer texts than
    asked, …), one sentence each. start() shows them above the question, so
    the person can cancel and fix the request before paying; the step also
    puts them in its report's warnings, where they're read on runs that
    needed no call or had nobody at the keyboard."""

    def __init__(self, confirm: bool, notes: list = ()):
        self.confirm = confirm
        self.notes = list(notes)
        self.started = False
        self.made = 0                       # calls made by the stages
        self.test_calls = 0                 # 1 once the run has started paying
        self._lock = threading.Lock()

    def start(self, plan: str) -> None:
        if self.started:
            return
        log.info(plan)
        log.info(f"model: {MODEL}")
        if self.notes:
            log.warning("Before you pay: this run can't do exactly what you asked:")
            for n in self.notes:
                log.warning(f"  - {n}")
        if self.confirm:
            confirm("Press Enter to start (1 test call first), anything else to cancel:"
                    if not self.notes else
                    "Press Enter to go ahead anyway (1 test call first), anything else to cancel "
                    "and fix the request:")
        try:
            call_llm('Reply with ONLY this JSON: {"ok": true}', attempts=2)
        except Exception as e:                              # noqa: BLE001
            sys.exit(f"Test call to {MODEL} failed, so nothing else was called: {e}")
        self.started = True
        self.test_calls = 1

    def made_call(self) -> None:
        with self._lock:                    # stages may call from several threads
            self.made += 1


@dataclass
class Calls:
    """What a step's model-calling stages share: the confirmation-and-count
    (PaidCalls) and the folder that keeps every answer (common/cache.py)."""
    paid: PaidCalls
    cache_dir: Path


def paid_calls(settings: dict, output, notes: list = ()) -> Calls:
    """The Calls of one run: uses the model the setting `model` names; asks
    before paying (setting confirm_paid_calls), showing notes first; answers
    kept in cache/ inside the step's output folder."""
    global MODEL
    name = str(settings.get("model") or "").strip()
    if not name:
        raise ValueError("model must name a model (py models.py lists them)")
    MODEL = name
    return Calls(paid=PaidCalls(confirm=settings["confirm_paid_calls"], notes=notes),
                 cache_dir=Path(output) / "cache")


def run_parallel(fn, jobs: dict, workers: int, handle, stop_note: str) -> None:
    """Run fn(*args) for every (key, args) in jobs, workers at a time, and
    call handle(n, key, result, error) in this thread as each finishes (n
    counts from 1; error is None on success, result None on failure).

    Ctrl-C cancels every call not yet started, so a stopped run spends
    nothing more than what is already in flight, then exits with stop_note.
    Calls already in flight cannot be recalled; their results are not
    handled."""
    pool = ThreadPoolExecutor(workers)
    try:
        futures = {pool.submit(fn, *args): key for key, args in jobs.items()}
        for n, future in enumerate(as_completed(futures), 1):
            try:
                result, error = future.result(), None
            except Exception as e:                      # noqa: BLE001
                result, error = None, e
            handle(n, futures[future], result, error)
    except KeyboardInterrupt:
        pool.shutdown(wait=False, cancel_futures=True)
        sys.exit(f"\nStopped. Calls not yet started were cancelled. "
                 f"{stop_note}")
    finally:
        pool.shutdown(wait=False, cancel_futures=True)


def confirm(question: str) -> None:
    """Stop until the person presses Enter (or types y); exit on anything
    else.

    The gate between reading a run's summary and paying for it. Ctrl-C and
    a closed input (a run with nothing attached to the keyboard) both stop,
    so the expensive path is never taken by default."""
    try:
        answer = input(f"\n{question} ")
    except (EOFError, KeyboardInterrupt):
        sys.exit("\nCancelled. Nothing was spent.")
    if answer.strip().lower() not in ("", "y", "yes"):
        sys.exit("Cancelled. Nothing was spent.")
