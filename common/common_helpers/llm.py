"""
common/common_helpers/llm.py -- the one place a model is called.

Used by every step that asks a model something: 040 (inducing the schema),
050 (drafting ground truth), 060 (extracting), and 070 (translating component
classes). The Ask Sage client was
moved from to_be_reshaped/llm_client.py, with its retries and re-asks now
logged through common.audit's log (so they reach the step's log file)
instead of printed.

It holds, in this order:

    THE RUN'S MODEL       MODEL, SERVICE; describe and model_label for the
                          run's record and report; cache_identity
    THE ASK SAGE CLIENT and THE LITELLM CLIENT: one request each
    EITHER SERVICE
        list_models       the model names the service lists (free; see py helpers/models.py)
        call_llm          send a prompt, get the reply text; retries rate
                          limits and server errors with backoff
        try_model         one one-line test call to a model: is it usable? (py helpers/models.py --try)
        call_llm_json     the same, parsed as a JSON object; re-asks once if
                          the reply is not one
    PROMPT SAFETY
        fence_safe        keeps a record from ending its data block early
    A PAID RUN
        PaidCalls         asks once before a run's first paid call (showing
                          any notes about the run first), makes a one-line
                          test call, and counts the calls
        Calls, paid_calls what a step's stages share: PaidCalls and the
                          folder its answers are cached in (common/common_helpers/cache.py)
        run_parallel      runs jobs a few at a time; Ctrl-C cancels those
                          not yet started
        confirm           the stop itself

What the steps that extract triple instances with entity classes share
(the prompt's rules, the reply format, the BEGIN/END lines) is in
common/common_helpers/extraction.py and common/common_prompts/.

    from common import llm
    calls = llm.paid_calls(settings, output, notes)   # once per run
    calls.paid.start("plan in words")                 # before the first paid call
    data = llm.call_llm_json(prompt)                  # a dict, or raises

Needs a .env in the repository folder with ASKSAGE_EMAIL and
ASKSAGE_API_KEY (Ask Sage) or LITELLM_API_KEY (LiteLLM), and the packages
requests and python-dotenv.
"""

import json
import os
import random
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
#: which paid_calls() puts here for the run. `py helpers/models.py` lists the models
#: the service shows your account (a listed model may still refuse you: the
#: run's first call, a one-line test, finds out for the price of that call).
#: It is part of every cache key (common/common_helpers/cache.py), so changing it asks again.
#: The default of 040, 060, and 070 (a LiteLLM name: the default service is LiteLLM).
MODEL = "claude-opus-5.5"

#: The default model of step 050, which drafts the ground truth: from another maker than MODEL, so the facts one
#: model misses aren't missing from both the ground truth and the extraction (060 warns when they're the same maker).
DRAFTING_MODEL = "gemini-2.5-pro"

#: The service that reaches the model: the default of every step's `service` setting, which paid_calls() puts here
#: for the run. "asksage": NASA's Ask Sage (ASKSAGE_EMAIL and ASKSAGE_API_KEY in .env); "litellm": NASA's LiteLLM
#: proxy (LITELLM_API_KEY in .env). A model's name is the service's own: Ask Sage's "google-claude-sonnet-5" is
#: LiteLLM's "claude-sonnet-5".
SERVICE = "litellm"
SERVICES = {"asksage": "Ask Sage", "litellm": "LiteLLM"}

#: Every call asks for the model's most likely answer, the same each time as far as the model allows.
TEMPERATURE = 0

#: The longest answer a call may get, in tokens, asked for explicitly so the service's own default doesn't apply: on
#: 2026-10-12 LiteLLM's default cut 040's longer extraction answers off at 7,500-11,000 characters, mid-JSON. With
#: 16,000, one answer was still cut off, at 25,658 characters: fewer than 16,000 tokens usually hold, so tokens the
#: model spends thinking may count too, or the model repeated itself. The log shows which (a cut-off answer is
#: written there whole, with the service's token counts).
MAX_ANSWER_TOKENS = 16000

#: How long a call waits for its answer, in seconds, every call alike: long enough for an answer of
#: MAX_ANSWER_TOKENS, so a long answer isn't abandoned and asked again (each attempt may be billed).
READ_TIMEOUT = 600

#: Every request sent to the service in this run, retries, re-asks, and failures included: what is billed, as far as
#: the service bills requests (reset by paid_calls; shown in each report's Model calls).
REQUESTS = {"sent": 0, "input_tokens": 0, "cache_read_tokens": 0, "cache_write_tokens": 0, "output_tokens": 0}
_requests_lock = threading.Lock()

#: The model names the service said it answered with in this run (LiteLLM's reply names the exact model version;
#: Ask Sage's doesn't), for the run's record (describe).
SERVED = set()


def describe() -> dict:
    """What answered this run's calls, for the run's record (each step's "made"): the service, the model as asked
    for, the exact model the service said answered (when it says), and the settings every call is sent with."""
    return {"service": SERVICE, "model": MODEL, "served_as": sorted(SERVED), "temperature": TEMPERATURE,
            "max_answer_tokens": MAX_ANSWER_TOKENS}


def model_label() -> str:
    """The model in words, for a report: "`claude-opus-5.5` through LiteLLM (answered as `…`)"."""
    served = [s for s in sorted(SERVED) if s != MODEL]
    return (f"`{MODEL}` through {SERVICES.get(SERVICE, SERVICE)}"
            + (f" (answered as {', '.join(f'`{s}`' for s in served)})" if served else ""))


def cache_identity() -> str:
    """The model as the cache key names it (common/common_helpers/cache.py). Ask Sage's is the model name alone, as
    it was before a second service existed, so answers already paid for stay valid; another service's names the
    service too, since two services may use one name for different models."""
    return MODEL if SERVICE == "asksage" else f"{SERVICE}:{MODEL}"


def _env(name: str, why: str) -> str:
    load_dotenv()
    value = (os.getenv(name) or "").strip()
    if not value:
        sys.exit(f"{name} isn't set, so {why}. Put {name}=<your key> in the file .env in the repository folder "
                 f"(docs/running_on_nasa_laptop.md), then run the command again.")
    return value


# ------------------------------ the Ask Sage client -------------------------

USER_BASE = "https://api.asksage.ai.nasa.gov/user"
SERVER_BASE = "https://api.asksage.ai.nasa.gov/server"
_token_cache = {}


def _asksage_token():
    if "token" not in _token_cache:
        load_dotenv()
        email, key = os.getenv("ASKSAGE_EMAIL"), os.getenv("ASKSAGE_API_KEY")
        if not (email and key):
            unset = " and ".join(n for n, v in (("ASKSAGE_EMAIL", email), ("ASKSAGE_API_KEY", key)) if not v)
            sys.exit(f"{unset} {'are' if ' and ' in unset else 'is'}n't set, so no model can be called. Put "
                     f"ASKSAGE_EMAIL and ASKSAGE_API_KEY in the file .env in the repository folder "
                     f"(docs/running_on_nasa_laptop.md), then run the command again.")
        login = requests.post(f"{USER_BASE}/get-token-with-api-key",
                              json={"email": email, "api_key": key},
                              timeout=(5, 60))
        login.raise_for_status()
        payload = login.json()["response"]
        _token_cache["token"] = (payload["access_token"]
                                 if isinstance(payload, dict) else payload)
    return _token_cache["token"]


def _asksage_models() -> list:
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


class BadReply(ValueError):
    """A reply that arrived but is not usable as the JSON object we asked
    for. Kept separate from a transport error so it retries the PROMPT
    rather than the connection."""


class ApiError(Exception):
    """The service refused the request in a way that will not fix itself:
    a permission or validation failure (e.g. Ask Sage's "model_not_permitted",
    or LiteLLM's HTTP 400, 401, 403, or 404).

    Deliberately NOT in call_llm's retry tuple: it would fail identically on
    every retry, burning four calls to report the same thing. A rate limit or
    a server error is raised as RuntimeError instead, so the normal backoff
    handles it."""


class RetryLater(RuntimeError):
    """A rate limit or a server error: worth asking again, after `wait` seconds when the service says how long."""

    def __init__(self, message: str, wait: float | None = None):
        super().__init__(message)
        self.wait = wait


#: HTTP statuses worth asking again: rate limited (429), server errors, overloaded (529).
RETRY_STATUSES = (429, 500, 502, 503, 504, 529)


def _retry_after(resp) -> float | None:
    try:
        return float(resp.headers.get("Retry-After"))
    except (TypeError, ValueError):
        return None


class CutOff(ApiError):
    """The answer reached the longest length allowed (MAX_ANSWER_TOKENS) and was cut off. Not retried: asking again
    with the same limit gets the same cut."""


def _ask_asksage(prompt: str, model: str, read_timeout: int, cache_until: str | None = None) -> str:
    """One request to Ask Sage; the reply text.

    dataset/limit_references are set deliberately. Per the Ask Sage API docs
    dataset defaults to 'all' and limit_references defaults to None, meaning
    every call retrieves from the tenant's datasets and prepends the results.
    That is wrong here twice over: the extraction prompt orders the model to
    use nothing but the text in front of it, and retrieved references are
    billed input tokens on all N calls. There is no max-tokens parameter on
    this endpoint, so output length cannot be capped from here."""
    # Fetched for each request, not once per run: a 401 clears the cache
    # below, and the next attempt must log in again.
    resp = requests.post(f"{SERVER_BASE}/query",
                         headers={"x-access-tokens": _asksage_token()},
                         json={"message": prompt, "model": model,
                               "temperature": TEMPERATURE,
                               "dataset": "none",
                               "limit_references": 0},
                         timeout=(5, read_timeout))
    if resp.status_code == 401:
        # The token is cached for the whole run, so one expiry would
        # otherwise fail every remaining call - and each failure still
        # costs a request. Drop it and log in again on the next try.
        _token_cache.pop("token", None)
        raise RuntimeError("HTTP 401 - token dropped, will re-login")
    if resp.status_code in RETRY_STATUSES:
        raise RetryLater(f"HTTP {resp.status_code}", _retry_after(resp))
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


# ------------------------------ the LiteLLM client --------------------------

#: NASA's LiteLLM proxy, which speaks the OpenAI API; LITELLM_BASE_URL in .env overrides it.
LITELLM_BASE = "https://proxy.fast.luna.nasa.gov"


def _litellm(path: str) -> tuple:
    """(address, headers) of a LiteLLM request."""
    load_dotenv()
    base = (os.getenv("LITELLM_BASE_URL") or LITELLM_BASE).rstrip("/")
    key = _env("LITELLM_API_KEY", "no model can be called through LiteLLM")
    return f"{base}{path}", {"Authorization": f"Bearer {key}"}


def _litellm_error(resp) -> str:
    """The error LiteLLM sent, in words: its message when the body has one, else the start of the body."""
    try:
        err = resp.json().get("error")
        text = err.get("message") if isinstance(err, dict) else err
    except (ValueError, AttributeError):
        text = None
    return f"HTTP {resp.status_code}: {str(text or resp.text)[:300]}"


def _litellm_models() -> list:
    url, headers = _litellm("/v1/models")
    resp = requests.get(url, headers=headers, timeout=(5, 60))
    if resp.status_code >= 400:
        raise ApiError(_litellm_error(resp))
    names = [str(m.get("id")) for m in resp.json().get("data", []) if isinstance(m, dict) and m.get("id")]
    if not names:
        raise ValueError(f"LiteLLM's model list came in a shape this code doesn't read: {resp.text[:300]}")
    return sorted(set(names))


def _messages(prompt: str, model: str, cache_until: str | None) -> list:
    """The request's messages. With cache_until (a line of the prompt, e.g. "----- BEGIN RECORD -----") and a model
    by Anthropic, everything before that line is sent as a system block marked for Anthropic's prompt caching, and
    the rest as the user message: the same words, so a later request that starts the same way reads that part from
    the cache at a fraction of the price (060_extract/060_extract.md, *The schema in the prompt*)."""
    at = prompt.find(cache_until) if cache_until else -1
    if at <= 0 or maker(model) != "Anthropic":
        return [{"role": "user", "content": prompt}]
    return [{"role": "system", "content": [{"type": "text", "text": prompt[:at], "cache_control": {"type": "ephemeral"}}]},
            {"role": "user", "content": prompt[at:]}]


def _count_tokens(usage: dict) -> None:
    """Add a reply's token counts to REQUESTS, for the report's Model calls."""
    if not isinstance(usage, dict):
        return
    read = usage.get("cache_read_input_tokens") or (usage.get("prompt_tokens_details") or {}).get("cached_tokens") or 0
    write = usage.get("cache_creation_input_tokens") or 0
    with _requests_lock:
        REQUESTS["input_tokens"] += (usage.get("prompt_tokens") or 0) - read - write
        REQUESTS["cache_read_tokens"] += read
        REQUESTS["cache_write_tokens"] += write
        REQUESTS["output_tokens"] += usage.get("completion_tokens") or 0


def _ask_litellm(prompt: str, model: str, read_timeout: int, cache_until: str | None = None) -> str:
    """One request to LiteLLM (the OpenAI chat completions API); the reply text. The exact model that answered,
    when the reply names it, goes into SERVED for the run's record."""
    url, headers = _litellm("/v1/chat/completions")
    resp = requests.post(url, headers=headers,
                         json={"model": model, "messages": _messages(prompt, model, cache_until),
                               "temperature": TEMPERATURE, "max_tokens": MAX_ANSWER_TOKENS},
                         timeout=(5, read_timeout))
    if resp.status_code in RETRY_STATUSES:
        raise RetryLater(_litellm_error(resp), _retry_after(resp))   # worth retrying
    if resp.status_code >= 400:
        raise ApiError(_litellm_error(resp))                # will not fix itself (key, model, request)
    body = resp.json()
    _count_tokens(body.get("usage"))
    try:
        choice = body["choices"][0]
        text = choice["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise RuntimeError(f"LiteLLM's reply has no answer in it: {str(body)[:300]}") from None
    if body.get("model"):
        SERVED.add(str(body["model"]))
    reason = choice.get("finish_reason")
    if reason == "length":
        # The whole answer goes to the log file (DEBUG: not shown on screen), so a person can see why it ran long:
        # many facts, or the model repeating itself.
        log.debug(f"cut-off answer from {model}, {len(text or ''):,} characters, usage {body.get('usage')}:\n{text}")
        raise CutOff(f"the answer was cut off at the longest length allowed ({MAX_ANSWER_TOKENS:,} tokens, "
                     f"MAX_ANSWER_TOKENS in common/common_helpers/llm.py), after {len(text or ''):,} characters")
    if reason not in (None, "stop") or not (text or "").strip():
        # e.g. "content_filter": a safety or recitation filter withheld the answer. Asking again gets the same. What
        # came before the stop goes to the log file (DEBUG), so a person can see where it stopped.
        log.debug(f"answer stopped by the service from {model} (finish_reason {reason!r}), {len(text or ''):,} "
                  f"characters, usage {body.get('usage')}:\n{text}")
        raise ApiError(f"the model gave no usable answer (finish_reason {reason!r}, {len(text or ''):,} characters"
                       + (": the service's content filter withheld it" if reason == "content_filter" else "") + ")")
    return text


# ------------------------------ either service ------------------------------

def list_models(service: str | None = None) -> list:
    """The model names the service lists for your account. Free: listing is not a model call. Being listed doesn't
    guarantee access."""
    return _litellm_models() if (service or SERVICE) == "litellm" else _asksage_models()


def call_llm(prompt, attempts=4, read_timeout=READ_TIMEOUT, model=None, service=None, cache_until=None):
    """Send prompt to the model, through the service; the reply text. Retries with exponential backoff on rate
    limits, server errors, and lost connections; a refusal that will not fix itself (ApiError) is raised at once.
    model, service: MODEL and SERVICE (the run's) when None."""
    model, service = model or MODEL, service or SERVICE
    # cache_until: where the prompt's identical start ends, for prompt caching (_messages); only LiteLLM uses it
    ask = _ask_litellm if service == "litellm" else _ask_asksage
    for attempt in range(attempts):
        with _requests_lock:
            REQUESTS["sent"] += 1
        try:
            return ask(prompt, model, read_timeout, cache_until)
        except requests.ReadTimeout:
            # Not asked again: the service may still be writing, and billing, the first answer.
            raise ApiError(f"no answer within {read_timeout} s (READ_TIMEOUT in common/common_helpers/llm.py); not "
                           f"asked again, since the service may still be writing, and billing, the first answer")
        except (RuntimeError, ValueError,
                requests.ConnectionError, requests.Timeout) as e:
            if attempt == attempts - 1:
                raise
            # 5, 10, 20 s, or longer when the service says so, plus up to 2 s so parallel calls don't retry together
            wait = max(2 ** attempt * 5, getattr(e, "wait", None) or 0) + random.uniform(0, 2)
            log.warning(f"Model call to {model} failed ({e}); trying again in {wait:.0f} s (attempt {attempt + 2} of "
                        f"{attempts}). Nothing to do: rate limits and server errors usually pass.")
            time.sleep(wait)


#: The one-line test request: a step's first paid call (PaidCalls.start), and each try of py helpers/models.py --try.
TEST_PROMPT = 'Reply with ONLY this JSON: {"ok": true}'


def try_model(name: str, service: str | None = None) -> tuple:
    """(usable, why): one test call to the model name, through the service. usable is True when the model answered;
    why is the reason when it didn't (e.g. Ask Sage's "model_not_permitted"). One tiny paid call."""
    try:
        call_llm(TEST_PROMPT, attempts=2, model=name, service=service)
        return True, ""
    except Exception as e:                                  # noqa: BLE001
        return False, str(e)


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


def call_llm_json(prompt, retries=1, read_timeout=READ_TIMEOUT, cache_until=None):
    """Return the JSON OBJECT the prompt asked for, or raise.

    Every caller immediately does .get() on the result, so a reply that
    parses into a list, a string, or a number is as useless as one that does
    not parse at all - and used to surface three frames away as an opaque
    AttributeError. Both failures are treated the same way here: re-ask once
    with a correction, then give up."""
    for attempt in range(retries + 1):
        text = call_llm(prompt, read_timeout=read_timeout, cache_until=cache_until)
        try:
            data = _best_effort_json(text)
            if not isinstance(data, dict):
                raise BadReply(f"expected a JSON object, got "
                               f"{type(data).__name__}")
            return data
        except (json.JSONDecodeError, BadReply) as e:
            # The whole answer goes to the log file (DEBUG: not shown on screen), so a person can see what broke it.
            log.debug(f"unusable answer from {MODEL} (attempt {attempt + 1} of {retries + 1}), "
                      f"{len(text):,} characters, {e}:\n{text}")
            if attempt == retries:
                raise BadReply(f"the model's answer isn't a valid JSON object, {retries + 1} times ({e}); each answer "
                               f"is in this run's log (outputs/logs/<run id>.log), on a DEBUG line starting "
                               f"\"unusable answer\"") from None
            log.warning(f"The model's reply isn't a JSON object ({e}); asking once more, reminding it to reply with "
                        f"the JSON object only. Nothing to do.")
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

    def __init__(self, confirm: bool, notes: list = (), step: str = ""):
        self.confirm = confirm
        self.notes = list(notes)
        self.step = step                    # the step's folder name, e.g. 070_evaluate
        self.started = False
        self.made = 0                       # calls made by the stages
        self.test_calls = 0                 # 1 once the run has started paying
        self._lock = threading.Lock()

    def start(self, plan: str) -> None:
        if self.started:
            return
        log.info(plan)
        log.info(f"model: {MODEL}, through {SERVICES.get(SERVICE, SERVICE)}")
        if self.notes:
            show_warnings(self.step, self.notes)
        if self.confirm:
            confirm("Press Enter to start (1 test call first), or anything else to cancel."
                    if not self.notes else
                    "Press Enter to go ahead anyway (1 test call first), or anything else to cancel.")
        try:
            call_llm(TEST_PROMPT, attempts=2)
        except Exception as e:                              # noqa: BLE001
            again = f"`py {self.step}/run.py`" if self.step else "the step"
            sys.exit(f"Test call to {MODEL} through {SERVICES.get(SERVICE, SERVICE)} failed ({e}), so no other model "
                     f"call was made. If {SERVICES.get(SERVICE, SERVICE)} says the model "
                     f"isn't allowed, give another with --model <name> (`py helpers/models.py --service {SERVICE} --try <name> ...` "
                     f"tells which you may use); otherwise "
                     f"check your key in .env and that you're on NASA's network. Then run {again} again.")
        self.started = True
        self.test_calls = 1

    def made_call(self) -> None:
        with self._lock:                    # stages may call from several threads
            self.made += 1


@dataclass
class Calls:
    """What a step's model-calling stages share: the confirmation-and-count
    (PaidCalls) and the folder that keeps every answer (common/common_helpers/cache.py)."""
    paid: PaidCalls
    cache_dir: Path


def paid_calls(settings: dict, output, notes: list = ()) -> Calls:
    """The Calls of one run: uses the model the setting `model` names, through the service the setting `service`
    names; asks before paying (setting confirm_paid_calls), showing notes first; answers kept in cache/ inside the
    step's output folder."""
    global MODEL, SERVICE
    service = str(settings.get("service") or SERVICE).strip().lower()
    if service not in SERVICES:
        raise ValueError(f"The setting service is {service!r}, which isn't a service the pipeline can reach, so no "
                         f"model can be called. Give one of {', '.join(SERVICES)} with --service <name>, then run "
                         f"`py {Path(output).name}/run.py` again.")
    name = str(settings.get("model") or "").strip()
    if not name:
        raise ValueError(f"The setting model is empty, so no model can be called. Give one with --model <name> "
                         f"(`py helpers/models.py` lists them), then run `py {Path(output).name}/run.py` again.")
    MODEL, SERVICE = name, service
    SERVED.clear()
    for k in REQUESTS:
        REQUESTS[k] = 0
    return Calls(paid=PaidCalls(confirm=settings["confirm_paid_calls"], notes=notes, step=Path(output).name),
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
        sys.exit(f"\nStopped with Ctrl+C. Model calls not yet started were cancelled, so they cost nothing. "
                 f"{stop_note}")
    finally:
        pool.shutdown(wait=False, cancel_futures=True)


def warning_list(step: str, notes: list) -> str:
    """'Step 070 found 2 warnings:', then the notes numbered; a note's further
    lines are indented under it."""
    head = f"Step {step.split('_')[0]} found {len(notes)} warning{'s' if len(notes) != 1 else ''}:"
    return head + "\n" + numbered(notes)


def numbered(notes: list) -> str:
    """'1. …', '2. …'; a note's further lines indented under it."""
    return "\n".join(f"{i}. " + "\n".join(("   " + x) if x and j else x for j, x in enumerate(n.split("\n")))
                     for i, n in enumerate(notes, 1))


def show_warnings(step: str, notes: list) -> None:
    log.warning(warning_list(step, notes), extra={"as_written": True})


#: Who makes a model, by a word of its family in the model's name. Ask Sage's names start with the host
#: ("google-claude-sonnet-5" is Anthropic's Claude served through Google), so the family word decides.
MAKERS = (("Anthropic", ("claude",)), ("OpenAI", ("gpt", "o1", "o3", "o4")), ("Google", ("gemini", "gemma")),
          ("Meta", ("llama",)), ("Mistral", ("mistral", "mixtral", "codestral")), ("Amazon", ("nova", "titan")),
          ("Cohere", ("command",)))


def maker(model: str) -> str | None:
    """The maker of a model, from its name ("google-claude-sonnet-5" -> "Anthropic"); None when the name says no
    family this table knows."""
    words = re.split(r"[-_./: ]+", (model or "").lower())
    for name, families in MAKERS:
        if any(w.startswith(f) for w in words for f in families):
            return name
    return None


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
