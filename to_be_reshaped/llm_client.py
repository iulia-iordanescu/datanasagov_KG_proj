"""
llm_client.py -- the one place a model is called.

Every script that asks a model something imports it from here:

    best_induce_schema.py           induces the schema
    draft_ground_truth_triples.py   drafts ground truth triples
    extract_triples_for_kg.py       extracts triples that fit the schema

It holds, in this order:

    THE ASK SAGE CLIENT
        call_llm          send a prompt, get the reply text; retries rate
                          limits and server errors with backoff
        call_llm_json     the same, parsed as a JSON object; re-asks once if
                          the reply is not one
    PROMPT SAFETY
        fence_safe        keeps a record from ending its data block early
    A PAID RUN
        start_paid_calls  the confirmation stop, then a one-line test call
        run_parallel      runs jobs a few at a time; Ctrl-C cancels those
                          not yet started
        confirm           the stop itself

What the drafter and the extractor alone share (their prompt's rules, the
BEGIN/END lines, one call per chunk) is in extraction_run.py.

The client was lifted unchanged out of best_induce_schema.py, which imports
it from here. MODEL kept its value, so the schema inducer's cached stages,
which fold MODEL into their signatures, stay valid.

    import llm_client as llm
    llm.MODEL = "..."                 # optional override, before any call
    data = llm.call_llm_json(prompt)  # a dict, or raises

Needs a .env beside it with ASKSAGE_EMAIL and ASKSAGE_API_KEY, and the
packages requests and python-dotenv.
"""

import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from dotenv import load_dotenv

#: The model every call uses. For the full list of options, run
#: list_models.py. A script may override it (llm.MODEL = ...) before its
#: first call.
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
            print(f"    transient API error ({e}), retrying in {wait}s...")
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
            print(f"    unusable reply ({e}); re-asking once")
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

def start_paid_calls(calls: int, skip_confirm: bool = False) -> None:
    """The step between a run's free part and its paid part.

    Stops for confirmation (unless skip_confirm, for --yes), then makes one
    tiny test call, so a wrong model name or key fails once here instead of
    once per record. Returns only if both pass; exits otherwise, having
    spent at most the test call."""
    if not skip_confirm:
        confirm(f"Press Enter to start the {calls:,} call(s) plus 1 test "
                f"call. Press anything else to cancel:")
    try:
        call_llm('Reply with ONLY this JSON: {"ok": true}', attempts=2)
    except Exception as e:                              # noqa: BLE001
        sys.exit(f"Test call to {MODEL} failed, so nothing else was "
                 f"called: {e}")


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
