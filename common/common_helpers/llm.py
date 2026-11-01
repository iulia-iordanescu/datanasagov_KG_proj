"""
common/common_helpers/llm.py -- the one place a model is called.

Used by every step that asks a model something: 040 (inducing the schema),
050 (drafting ground truth), 060 (extracting), and 070 (translating component
classes). The Ask Sage client was
moved from archive/to_be_reshaped/llm_client.py, with its retries and re-asks now
logged through common.audit's log (so they reach the step's log file)
instead of printed.

It holds, in this order:

    THE RUN'S MODEL       MODEL, SERVICE, THINKING; describe and model_label
                          for the run's record and report; cache_identity;
                          the LiteLLM answer cache bypass (answer_cache_control)
    THE ASK SAGE CLIENT and THE LITELLM CLIENT: one request each
    EITHER SERVICE
        list_models       the model names the service lists (free; see py helpers/models.py)
        call_llm          send a prompt, get the reply text; retries rate
                          limits and server errors with backoff
        try_model         one one-line test call to a model: is it usable? (py helpers/models.py --try)
        classify_reply    what a reply is (complete, cut off, refused, empty, malformed), judged by
                          the service's finish reason AND the answer's content, the same for both
                          services: the one place that decides it
        call_llm_json     the same, parsed as a JSON object; re-asks once if
                          the reply is not one, or not of the shape the caller checks for
    PROMPT SAFETY
        fence_safe        keeps a record from ending its data block early
    A PAID RUN
        PaidCalls         asks once before a run's first paid call (showing
                          any notes about the run first), makes a one-line
                          test call and checks its token counts, counts the
                          calls, shows their progress, records each failed
                          call, and stops early when the first calls fail
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

import datetime as dt
import hashlib
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
from common.stop import Stop

#: The model the calls use: the default of every step's `model` setting,
#: which paid_calls() puts here for the run. `py helpers/models.py` lists the models
#: the service shows your account (a listed model may still refuse you: the
#: run's first call, a one-line test, finds out for the price of that call).
#: It is part of every cache key (common/common_helpers/cache.py), so changing it asks again.
#: The default of 040, 060, and 070 (a LiteLLM name: the default service is LiteLLM).
MODEL = "claude-opus-5.5"

#: The default model of step 050, which drafts the classed triples a person corrects into ground truth: from another maker than MODEL, so the facts one
#: model misses aren't missing from both the ground truth and the extraction (060 warns when they're the same maker).
DRAFTING_MODEL = "gemini-2.5-pro"

#: The service that reaches the model: the default of every step's `service` setting, which paid_calls() puts here
#: for the run. "asksage": NASA's Ask Sage (ASKSAGE_EMAIL and ASKSAGE_API_KEY in .env); "litellm": NASA's LiteLLM
#: proxy (LITELLM_API_KEY in .env). A model's name is the service's own: Ask Sage's "google-claude-sonnet-5" is
#: LiteLLM's "claude-sonnet-5".
SERVICE = "litellm"
SERVICES = {"asksage": "Ask Sage", "litellm": "LiteLLM"}

#: Every call to a model that takes it asks for the model's most likely answer (temperature 0), the same each time
#: as far as the model allows: only where temperature_sent says so. Anthropic's Claude Opus 5.5 takes no sampling
#: parameters ("Omit `temperature`, `top_p`, and `top_k`", and temperature 0 "never guaranteed identical outputs on
#: prior models": https://platform.claude.com/docs/en/models/opus-5-5/migration-guide); Google advises keeping
#: Gemini 3's temperature at its default 1.0 ("Setting temperature below 1.0 may lead to unexpected behavior, such as
#: looping or degraded performance": https://ai.google.dev/gemini-api/docs/gemini-3). Not part of the cache key.
TEMPERATURE = 0

#: How much a model that thinks before answering may think: the default of every step's `thinking` setting, which
#: paid_calls() puts here for the run. A model's thinking is hidden, billed as answer tokens, and counts against
#: MAX_ANSWER_TOKENS (Google's Gemini docs: the answer limit includes "thought tokens"), so uncapped thinking leaves
#: less room for the answer: on 2026-10-21, gemini-2.5-pro's answer for a 1,503-character record was cut off after
#: 10,623 characters, far fewer than 16,000 tokens hold. Sent as LiteLLM's `reasoning_effort`, only where LiteLLM
#: documents it (thinking_sent): for Gemini 2.5 Pro, LiteLLM turns "low" into a thinking budget of 1,024 tokens, so
#: the answer keeps about 15,000 of MAX_ANSWER_TOKENS; for Gemini 3, into its thinking level "low". "model_default"
#: sends nothing, so the model thinks as it would by default.
THINKING = "low"
THINKING_LEVELS = ("low", "medium", "high", "model_default")

#: Which repeat of the same recipe a run is (the setting `repeat` of every step that calls a model): 1, the default,
#: reuses the answers saved so far; 2, 3, ... are asked again, each into cache entries of its own, so repeats of one
#: recipe are independent answers of the model, and their spread is the model's own variation (the noise floor,
#: helpers/compare_runs.py). Part of the cache key (cache_identity) only from 2 on, so repeat 1's key is the key
#: answers were saved under before this setting existed, and they stay valid. Not sent to the model.
REPEAT = 1

#: The longest answer a call may get, in tokens, asked for explicitly so the service's own default doesn't apply: on
#: 2026-10-12 LiteLLM's default cut 040's longer extraction answers off at 7,500-11,000 characters, mid-JSON. With
#: 16,000, one answer was still cut off, at 25,658 characters: fewer than 16,000 tokens usually hold, so tokens the
#: model spends thinking may count too, or the model repeated itself. The log shows which (a cut-off answer is
#: written there whole, with the service's token counts). 32,000 since 2026-10-30: the limit includes the model's
#: thinking for both models used (Anthropic: "leave room in `max_tokens` for the thinking", What's new in Claude Opus
#: 5.5; Google: the limit includes "thought tokens"), and a cut-off text piece is left out whole, so a low limit loses
#: exactly the long, fact-rich records. Both models allow it: Claude Opus 5.5's max output is 128K tokens
#: (https://platform.claude.com/docs/en/models/opus-5-5/overview), Gemini 2.5 Pro's 65,536
#: (https://ai.google.dev/gemini-api/docs/models/gemini-2.5-pro). Not part of the cache key: answers that finished
#: stay valid; an answer stored as cut off at a lower limit is asked again (common/common_helpers/cache.py).
MAX_ANSWER_TOKENS = 32000

#: How long a call waits for its answer, in seconds, every call alike: long enough for an answer of
#: MAX_ANSWER_TOKENS, so a long answer isn't abandoned and asked again (each attempt may be billed). 1,200 s covers
#: 32,000 tokens at about 27 tokens a second, thinking included.
READ_TIMEOUT = 1200

#: The effort level a model runs at when none is sent, where its maker documents one: on Claude Opus 5.5 adaptive
#: thinking is always on (the model decides whether and how much to think, and effort is the main control of how
#: much), and "A request that omits `effort` runs at `medium`" (https://platform.claude.com/docs/en/models/opus-5-5/whats-new-opus-5-5;
#: https://platform.claude.com/docs/en/build-with-claude/effort). For the run's record only: no effort is sent.
DEFAULT_EFFORT = {"claude-opus-5.5": "medium", "claude-opus-5-5": "medium",
                  "claude-haiku-5.5": "medium", "claude-haiku-5-5": "medium"}

#: Every request sent to the service in this run, retries, re-asks, and failures included: what is billed, as far as
#: the service bills requests (reset by paid_calls; shown in each report's Model calls).
REQUESTS = {"sent": 0, "input_tokens": 0, "cache_read_tokens": 0, "cache_write_tokens": 0, "output_tokens": 0,
            "reasoning_tokens": 0}
#: Replies asked once more by call_llm_json because they weren't usable, this run: not_json and wrong_shape count
#: the first replies that weren't a JSON object or not of the shape asked for; fixed, those the second ask fixed;
#: still_failed, those still unusable (their records are left out). Reported by common/common_helpers/dropped.py.
REASKS = {"not_json": 0, "wrong_shape": 0, "fixed": 0, "still_failed": 0}
_requests_lock = threading.Lock()

#: The session id sent with each LiteLLM request of this run, as the header SESSION_HEADER, or None (no header):
#: set by paid_calls, only for the steps that ask for it (060, whose requests share a cached schema start). LiteLLM
#: routes the requests of one session id to one deployment when the proxy has session affinity on
#: (https://docs.litellm.ai/docs/routing: "The proxy reads it from the `x-litellm-session-id` header"; for "when the
#: deployments behind a model group do not share state, for example provider-side prompt caching"), so they can read
#: one prompt cache. It changes no word the model gets, nor the cache key (cache_identity), nor any setting sent.
SESSION_ID = None
SESSION_HEADER = "x-litellm-session-id"

#: What each LiteLLM request carries in its body when the proxy's own answer cache is to be bypassed: LiteLLM's
#: per-request cache controls (https://docs.litellm.ai/docs/proxy/caching_controls: `no-cache`, "Force a fresh
#: response, bypassing the cache"; `no-store`, "Will not cache the response"). A proxy with caching on answers a
#: repeated identical request from its cache (https://docs.litellm.ai/docs/proxy/caching: "The second response is
#: served from the cache"), which would make the runs of a recipe's repeats copies of one run; the pipeline's own
#: cache (common/common_helpers/cache.py) stays the only reuse. Sent only with LITELLM_BYPASS_ANSWER_CACHE=1 in .env
#: (answer_cache_bypassed): LiteLLM's docs don't say whether a proxy with caching off accepts the controls, so they
#: are sent once py helpers/check_answer_cache.py shows that NASA's proxy accepts them and answers from its cache.
#: It changes no word the model gets, nor the cache key (cache_identity), nor any fingerprint.
ANSWER_CACHE_CONTROL = {"cache": {"no-cache": True, "no-store": True}}
ANSWER_CACHE_SWITCH = "LITELLM_BYPASS_ANSWER_CACHE"


def answer_cache_bypassed() -> bool:
    """Whether LiteLLM requests carry ANSWER_CACHE_CONTROL: ANSWER_CACHE_SWITCH in .env set to 1, true or yes."""
    load_dotenv()
    return (os.getenv(ANSWER_CACHE_SWITCH) or "").strip().lower() in ("1", "true", "yes")


def answer_cache_control() -> dict:
    """What a LiteLLM request adds to its body for the proxy's answer cache: ANSWER_CACHE_CONTROL, or nothing."""
    return json.loads(json.dumps(ANSWER_CACHE_CONTROL)) if answer_cache_bypassed() else {}


def answer_cache_note(service: str | None = None) -> str | None:
    """LiteLLM's answer cache in the run record's words ("bypassed", or why not); None through Ask Sage."""
    if (service or SERVICE) != "litellm":
        return None
    return ("bypassed" if answer_cache_bypassed() else
            f"not bypassed ({ANSWER_CACHE_SWITCH} isn't set in .env; py helpers/check_answer_cache.py shows whether "
            f"the proxy answers repeated requests from its cache)")


#: The model names the service said it answered with in this run (LiteLLM's reply names the exact model version;
#: Ask Sage's doesn't), for the run's record (describe).
SERVED = set()


def describe() -> dict:
    """What answered this run's calls, for the run's record (each step's "made"): the service, the model as asked
    for, the exact model the service said answered (when it says), and the settings every call is sent with, as
    sent (call_settings)."""
    return {"service": SERVICE, "model": MODEL, "served_as": sorted(SERVED), **call_settings(),
            "service_note": SERVICE_NOTES.get(SERVICE), "repeat": REPEAT,
            **({"answer_cache": answer_cache_note()} if SERVICE == "litellm" else {}),
            **({"session_id": SESSION_ID} if SESSION_ID and SERVICE == "litellm" else {})}


#: What a service may do to a request that the run record can't see (prompt audit F19, 2026-10-30).
SERVICE_NOTES = {"litellm": "LiteLLM can drop a setting the model doesn't take without saying so (its drop_params "
                            "option), so a setting recorded as sent may not have reached the model"}


def call_settings(model: str | None = None, service: str | None = None) -> dict:
    """The settings a call to this model through this service is sent with, in the run record's words: a setting
    that isn't sent says so, and why, so the record never states a setting the model didn't get."""
    model = model or MODEL
    sent = thinking_sent(model, service)
    if sent:
        thinking = THINKING
    elif takes_thinking_cap(model, service):
        thinking = "not sent (model_default: the model thinks as it would by default)"
    else:
        thinking = f"not sent (the step's setting, {THINKING}, isn't sent to this model)"
    return {"temperature": TEMPERATURE if temperature_sent(model, service) else
            "not sent (the model does not accept it, or its maker advises against changing it)",
            "max_answer_tokens": max_tokens_sent(service) or
            "not sent (Ask Sage takes no answer limit, and gives no reason an answer ended, so a cut-off can't be "
            "detected)", "thinking": thinking, "thinking_sent": sent, "effort": effort_note(model)}


def max_tokens_sent(service: str | None = None) -> int | None:
    """The answer limit a call sends (MAX_ANSWER_TOKENS), or None when it sends none: LiteLLM takes it; Ask Sage's
    query has no such parameter (_ask_asksage)."""
    return MAX_ANSWER_TOKENS if (service or SERVICE) == "litellm" else None


def effort_note(model: str | None = None) -> str | None:
    """The effort a Claude model ran at, in words (None for other makers' models): the pipeline sends none, so it is
    the model's default (DEFAULT_EFFORT, where documented)."""
    model = model or MODEL
    if maker(model) != "Anthropic":
        return None
    default = DEFAULT_EFFORT.get(model.lower().removeprefix("google-"))
    return f"not sent (model default, {default})" if default else "not sent (model default)"


def temperature_sent(model: str | None = None, service: str | None = None) -> bool:
    """Whether calls to this model are sent TEMPERATURE: not to Anthropic's Claude models, which take no sampling
    parameters, nor to Google's Gemini 3 and later, whose maker advises keeping the default (TEMPERATURE cites
    both); to every other model, Gemini 2.5 among them. The same through either service."""
    model = model or MODEL
    if maker(model) == "Anthropic":
        return False
    version = re.search(r"gemini-(\d+(?:\.\d+)?)", model.lower())
    return not (maker(model) == "Google" and version and float(version.group(1)) >= 3)


def thinking_sent(model: str | None = None, service: str | None = None) -> str | None:
    """The `reasoning_effort` a call sends (THINKING), or None when it sends none. Sent only through LiteLLM, and only
    to the models LiteLLM documents it for: Google's Gemini 2.5 and later (https://docs.litellm.ai/docs/providers/gemini).
    Not to Anthropic's Claude models: on Claude Opus 5.5 adaptive thinking is always on, and the model decides whether
    and how much to think, at the effort sent, or at its default, medium, when none is sent (https://platform.claude.com/docs/en/models/opus-5-5/whats-new-opus-5-5), and whether LiteLLM
    passes an effort setting on to it isn't shown yet (py helpers/check_effort.py; docs/running_on_nasa_laptop.md,
    "Checking that LiteLLM passes Claude's effort on"). Not to other models either, which might refuse a parameter they don't take. Ask Sage's query takes
    no such parameter."""
    return None if THINKING == "model_default" or not takes_thinking_cap(model, service) else THINKING


def takes_thinking_cap(model: str | None = None, service: str | None = None) -> bool:
    """Whether the thinking cap is sent to this model through this service, whatever `thinking` is (thinking_sent
    says where, and why)."""
    model, service = model or MODEL, service or SERVICE
    if service != "litellm" or maker(model) != "Google":
        return False
    version = re.search(r"gemini-(\d+(?:\.\d+)?)", model.lower())
    return bool(version and float(version.group(1)) >= 2.5)


def model_label() -> str:
    """The model in words, for a report: "`claude-opus-5.5` through LiteLLM (answered as `…`)"."""
    served = [s for s in sorted(SERVED) if s != MODEL]
    return (f"`{MODEL}` through {SERVICES.get(SERVICE, SERVICE)}"
            + (f" (answered as {', '.join(f'`{s}`' for s in served)})" if served else ""))


def cache_identity() -> str:
    """The model as the cache key names it (common/common_helpers/cache.py). Ask Sage's is the model name alone, as
    it was before a second service existed, so answers already paid for stay valid; another service's names the
    service too, since two services may use one name for different models; and the thinking cap, when one is sent
    (thinking_sent), since it changes the answer; and the repeat, from 2 on (REPEAT), so each repeat has answers of
    its own."""
    sent = thinking_sent()
    return ((MODEL if SERVICE == "asksage" else f"{SERVICE}:{MODEL}") + (f"|thinking:{sent}" if sent else "")
            + (f"|repeat:{REPEAT}" if REPEAT > 1 else ""))


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


class WrongShape(BadReply):
    """A reply that is a JSON object, but not of the shape the caller asked for (call_llm_json's check), e.g. with
    no "triples" list. Its message says what is wrong."""


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
    """The answer was cut off: at the longest length allowed (MAX_ANSWER_TOKENS, which LiteLLM takes), or, where the
    service takes no limit and reports no finish reason (Ask Sage), at the model's own limit, seen in the answer
    stopping inside an unfinished JSON object (classify_reply). Not retried: asking again with the same settings
    gets the same cut. Carries what the service sent (answer, usage, finish_reason), for the failed-call record."""


class Refused(ApiError):
    """The model, or its service, declined to answer: a filter's finish reason (REFUSAL_REASONS), or an answer in
    prose declining the task (REFUSAL_WORDS) with no JSON object in it, sent as HTTP 200. Not retried: asking again
    gets the same answer; never stored as an answer (common/common_helpers/cache.py). Carries what the service sent."""


# ------------------------------ what a reply is -----------------------------

#: finish_reason values (the service's, or the model maker's own, compared lower-cased) that say the answer is
#: complete, was cut off at a length limit, or was withheld by a filter. A reason outside the three sets is judged by
#: the answer's content (classify_reply). One home: common/common_helpers/dropped.py reads these too.
COMPLETE_REASONS = {"stop", "end_turn", "eos", "stop_sequence", "completed"}
CUT_OFF_REASONS = {"length", "max_tokens", "max_output_tokens", "max_completion_tokens"}
REFUSAL_REASONS = {"content_filter", "refusal", "safety", "prohibited_content", "blocklist", "spii", "recitation"}
#: How an answer in prose declines the task, at its start (after fences or blank space): "I'm sorry, but …",
#: "I cannot …", "I can't help …", "As an AI …", "Unfortunately, I am unable …". Only an answer with NO JSON object in
#: it is read this way, so a preamble before the JSON object never counts.
REFUSAL_WORDS = re.compile(r"^\W*(?:(?:i['\u2019]?m|i am) (?:sorry|unable|not able|afraid i)|i apologi[sz]e|sorry[,.]|"
                           r"as an ai\b|i (?:can(?:no|')t|cannot|won['\u2019]t|will not|must decline|"
                           r"(?:do not|don['\u2019]t) feel comfortable)|unfortunately,? i (?:can|am))", re.I)
#: What classify_reply can say a reply is.
REPLY_KINDS = ("complete", "cut_off", "refused", "empty", "malformed")
#: A fence around the whole answer: ```json … ``` (the tag in any case, or none), only at the answer's start and end,
#: never inside a value.
_FENCE = re.compile(r"\A\s*```[A-Za-z]*[ \t]*\r?\n(.*?)\r?\n?[ \t]*```\s*\Z", re.S)


def find_json(text: str) -> tuple:
    """(data, state): the JSON the answer holds. state is "object" (data is the parsed value: the whole answer, with
    its fence removed, or the first {…} object in prose around it), "none" (no { at all), "unterminated" (an object
    begins and the answer ends inside it: a cut), "several" (more than one object, so which one was meant can't be
    told; data is None), or "invalid" (an object begins and ends but isn't JSON; data is None)."""
    cleaned = text or ""
    m = _FENCE.match(cleaned)
    if m:
        cleaned = m.group(1)
    cleaned = cleaned.strip()
    try:
        return json.loads(cleaned), "object"
    except json.JSONDecodeError:
        pass
    start = cleaned.find("{")
    if start == -1:
        return None, "none"
    decoder = json.JSONDecoder()
    try:
        data, end = decoder.raw_decode(cleaned, start)
    except json.JSONDecodeError:
        return None, "unterminated" if _open_at_end(cleaned, start) else "invalid"
    rest = cleaned[end:]
    nxt = rest.find("{")
    if nxt != -1:
        try:
            decoder.raw_decode(rest, nxt)
            return None, "several"
        except json.JSONDecodeError:
            pass
    return data, "object"


def _open_at_end(text: str, start: int) -> bool:
    """Whether the object beginning at start is still open (a brace, bracket or string not closed) when text ends."""
    depth, in_string, escaped = 0, False, False
    for ch in text[start:]:
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
        elif ch == '"':
            in_string = True
        elif ch in "{[":
            depth += 1
        elif ch in "}]":
            depth -= 1
            if depth <= 0:
                return False
    return True


def classify_reply(text, finish_reason=None, native_finish_reason=None, service: str | None = None) -> tuple:
    """(kind, detail): what a reply is, one of REPLY_KINDS, judged by the finish reason AND the content, the same
    way for every service (every prompt of the pipeline asks for a JSON object):

      cut_off    the service says so (CUT_OFF_REASONS), or the answer stops inside an unfinished JSON object and no
                 finish reason says the model stopped on its own (Ask Sage sends none)
      refused    a filter's finish reason (REFUSAL_REASONS), or prose declining the task (REFUSAL_WORDS) with no
                 JSON object in it, whatever the finish reason
      empty      nothing but blank space
      complete   a JSON value (a reason outside the known sets doesn't fail an answer whose content is complete)
      malformed  anything else: prose, a JSON object that isn't valid, several objects, or an unfinished object the
                 model stopped on its own (finish reason in COMPLETE_REASONS); worth asking once more
    """
    reasons = {str(r).strip().lower() for r in (finish_reason, native_finish_reason) if r not in (None, "")}
    text = text or ""
    chars = f"{len(text):,} characters"
    reason_words = f"finish_reason {finish_reason!r}" + (f", the model maker's {native_finish_reason!r}"
                                                         if native_finish_reason else "")
    if reasons & CUT_OFF_REASONS:
        return "cut_off", f"the service reports the answer was cut off ({reason_words}), after {chars}"
    if reasons & REFUSAL_REASONS:
        return "refused", f"the service's content filter withheld the answer ({reason_words}), {chars}"
    if not text.strip():
        return "empty", f"the model gave no usable answer ({reason_words}, 0 characters)"
    data, state = find_json(text)
    if state == "none" and REFUSAL_WORDS.match(text.strip().strip("`").strip()):
        first = " ".join(text.strip().split())[:160]
        return "refused", f"the model declined to answer, in prose ({reason_words}, {chars}): {first!r}"
    if state == "object":
        return "complete", ("" if reasons <= COMPLETE_REASONS else
                            f"complete answer under a finish reason the pipeline doesn't know ({reason_words})")
    if state == "unterminated" and not (reasons & COMPLETE_REASONS):
        where = ("Ask Sage takes no answer limit and reports no finish reason, so the model's own limit cut it"
                 if (service or SERVICE) == "asksage" and not reasons else
                 f"no finish reason says the model stopped on its own ({reason_words})")
        return "cut_off", f"the answer stops inside an unfinished JSON object after {chars}; {where}"
    what = {"none": "no JSON object in the answer", "unterminated": "a JSON object the model left unfinished",
            "several": "several JSON objects in one answer", "invalid": "a JSON object that isn't valid JSON"}[state]
    return "malformed", f"{what} ({reason_words}, {chars})"


def _raise_unless_complete(text, body: dict, service: str, reason=None, native=None) -> str:
    """text, when classify_reply finds it complete or malformed (call_llm_json then parses it, and asks once more
    for a malformed one); else the error for the kind, carrying what the service sent: CutOff, Refused, or ApiError
    (empty). Both service clients end here, so a reply is judged the same way whichever service sent it."""
    kind, detail = classify_reply(text, reason, native, service)
    _last.reply["reply_kind"] = kind
    if kind in ("complete", "malformed"):
        return text
    # The whole answer goes to the log file (DEBUG: not shown on screen), so a person can see why it ran long, or
    # what the model wrote instead of the answer.
    log.debug(f"{kind.replace('_', '-')} answer ({detail}), usage {body.get('usage')}:\n{text}")
    if kind == "cut_off":
        thought = reasoning_tokens(body.get("usage"))
        at_limit = max_tokens_sent(service) is not None and \
            {str(reason).lower(), str(native).lower()} & CUT_OFF_REASONS
        error = CutOff((f"the answer was cut off at the longest length allowed ({MAX_ANSWER_TOKENS:,} tokens, "
                        f"MAX_ANSWER_TOKENS in common/common_helpers/llm.py), after {len(text or ''):,} characters"
                        if at_limit else f"the answer was cut off: {detail}")
                       + (f"; the model spent {thought:,} of those tokens thinking" if thought else ""))
    elif kind == "refused":
        error = Refused(f"the model refused to answer: {detail}")
    else:
        error = ApiError(detail)
    raise _with_reply(error, text, body, reason, native)


def reasoning_tokens(usage) -> int:
    """The thinking tokens a reply's usage reports (OpenAI's shape, which LiteLLM uses:
    usage.completion_tokens_details.reasoning_tokens), 0 when it reports none."""
    details = usage.get("completion_tokens_details") if isinstance(usage, dict) else None
    return int(details.get("reasoning_tokens") or 0) if isinstance(details, dict) else 0


#: What the latest request in this thread sent and got back, for the test call's check (PaidCalls.start) and the
#: failed-call record (PaidCalls._record): settings_sent (every setting of the request but its prompt), request_bytes,
#: http_status, error_body (the service's error, up to ERROR_BODY_CHARS), usage (whole), finish_reason,
#: native_finish_reason (the model maker's own reason, when the service passes it on), served_as.
_last = threading.local()

#: How much of a service's error body the failed-call record keeps, in characters.
ERROR_BODY_CHARS = 4000


def _http_reply(resp) -> None:
    """Note a reply's HTTP status, and its body when it is an error, in _last.reply."""
    _last.reply["http_status"] = resp.status_code
    if resp.status_code >= 400:
        _last.reply["error_body"] = str(resp.text or "")[:ERROR_BODY_CHARS]


def _ask_asksage(prompt: str, model: str, read_timeout: int, cache_until: str | None = None) -> str:
    """One request to Ask Sage; the reply text.

    dataset/limit_references are set deliberately. Per the Ask Sage API docs
    dataset defaults to 'all' and limit_references defaults to None, meaning
    every call retrieves from the tenant's datasets and prepends the results.
    That is wrong here twice over: the extraction prompt orders the model to
    use nothing but the text in front of it, and retrieved references are
    billed input tokens on all N calls. There is no max-tokens parameter on
    this endpoint, so output length cannot be capped from here."""
    payload = {"message": prompt, "model": model, "dataset": "none", "limit_references": 0}
    if temperature_sent(model, "asksage"):
        payload["temperature"] = TEMPERATURE
    _last.reply = {"settings_sent": {k: v for k, v in payload.items() if k != "message"},
                   "request_bytes": len(json.dumps(payload).encode("utf-8"))}
    # Fetched for each request, not once per run: a 401 clears the cache
    # below, and the next attempt must log in again.
    resp = requests.post(f"{SERVER_BASE}/query",
                         headers={"x-access-tokens": _asksage_token()},
                         json=payload,
                         timeout=(5, read_timeout))
    _http_reply(resp)
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
    if err or str(body.get("status", "")).isdigit() and int(body["status"]) >= 400:
        _last.reply["error_body"] = json.dumps(body, ensure_ascii=False)[:ERROR_BODY_CHARS]
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
    # callers must never receive None and call .strip() on it. Ask Sage sends no finish reason and takes no answer
    # limit, so the answer is judged by its content alone (classify_reply): one stopping inside an unfinished JSON
    # object was cut off at the model's own limit; prose declining the task is a refusal.
    return _raise_unless_complete((body or {}).get("message") or "", body or {}, "asksage")


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
        REQUESTS["reasoning_tokens"] += reasoning_tokens(usage)


def _post(*args, **kwargs):
    """requests.post, looked up when called: the one place a LiteLLM request leaves (the tests' stand-in replaces it)."""
    return requests.post(*args, **kwargs)


def _ask_litellm(prompt: str, model: str, read_timeout: int, cache_until: str | None = None) -> str:
    """One request to LiteLLM (the OpenAI chat completions API); the reply text. The exact model that answered,
    when the reply names it, goes into SERVED for the run's record."""
    url, headers = _litellm("/v1/chat/completions")
    if SESSION_ID:
        headers[SESSION_HEADER] = SESSION_ID                # one deployment per run, where the proxy pins sessions
    payload = {"model": model, "messages": _messages(prompt, model, cache_until), "max_tokens": max_tokens_sent("litellm")}
    if temperature_sent(model, "litellm"):
        payload["temperature"] = TEMPERATURE
    if thinking_sent(model, "litellm"):
        payload["reasoning_effort"] = thinking_sent(model, "litellm")
    payload.update(answer_cache_control())                  # a fresh answer, where the proxy caches answers
    _last.reply = {"settings_sent": {k: v for k, v in payload.items() if k != "messages"},
                   "request_bytes": len(json.dumps(payload).encode("utf-8"))}
    resp = _post(url, headers=headers, json=payload, timeout=(5, read_timeout))
    _http_reply(resp)
    if resp.status_code in RETRY_STATUSES:
        raise RetryLater(_litellm_error(resp), _retry_after(resp))   # worth retrying
    if resp.status_code >= 400:
        raise ApiError(_litellm_error(resp))                # will not fix itself (key, model, request)
    body = resp.json()
    _count_tokens(body.get("usage"))
    _last.reply["usage"] = body.get("usage") if isinstance(body.get("usage"), dict) else {}
    try:
        choice = body["choices"][0]
        text = choice["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise RuntimeError(f"LiteLLM's reply has no answer in it: {str(body)[:300]}") from None
    if body.get("model"):
        SERVED.add(str(body["model"]))
        _last.reply["served_as"] = str(body["model"])
    reason = choice.get("finish_reason")
    _last.reply["finish_reason"] = reason
    # The model maker's own reason (e.g. Gemini's "MAX_TOKENS" or "SAFETY"), when LiteLLM passes it on: at the choice's
    # top level, or among its provider_specific_fields.
    extra = choice.get("provider_specific_fields") if isinstance(choice.get("provider_specific_fields"), dict) else {}
    _last.reply["native_finish_reason"] = choice.get("native_finish_reason") or extra.get("native_finish_reason")
    return _raise_unless_complete(text, body, "litellm", reason, _last.reply["native_finish_reason"])


def _with_reply(error: Exception, text, body: dict, reason, native=None) -> Exception:
    """error, carrying what the service sent (the answer, usage, finish_reason, the maker's own reason), for the
    failed-call record."""
    error.answer, error.usage, error.finish_reason = text or "", body.get("usage") or {}, reason
    error.native_finish_reason = native
    return error


def _with_call(error: Exception, attempts: int, began: float, cause: Exception | None = None) -> Exception:
    """error, carrying what its last request sent and got back (_last.reply), how many attempts were made, and how
    long they took, for the failed-call record. cause: the exception error replaces (e.g. requests' ReadTimeout)."""
    try:
        error.call = {**(getattr(_last, "reply", None) or {}), "attempts": attempts,
                      "seconds": round(time.monotonic() - began, 1),
                      **({"cause_type": type(cause).__name__} if cause is not None else {})}
    except AttributeError:                                  # an exception that takes no attributes
        pass
    return error


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
    began, _last.reply = time.monotonic(), {}
    for attempt in range(attempts):
        with _requests_lock:
            REQUESTS["sent"] += 1
        try:
            text = ask(prompt, model, read_timeout, cache_until)
            _last.timing = {"attempts": attempt + 1, "seconds": round(time.monotonic() - began, 1)}
            return text
        except requests.ReadTimeout as e:
            # Not asked again: the service may still be writing, and billing, the first answer.
            raise _with_call(ApiError(f"no answer within {read_timeout} s (READ_TIMEOUT in "
                                      f"common/common_helpers/llm.py); not asked again, since the service may still be "
                                      f"writing, and billing, the first answer"), attempt + 1, began, e) from e
        except Exception as e:                              # noqa: BLE001
            retry = isinstance(e, (RuntimeError, ValueError, requests.ConnectionError, requests.Timeout))
            if not retry or attempt == attempts - 1:
                _with_call(e, attempt + 1, began)
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


def call_llm_json(prompt, retries=1, read_timeout=READ_TIMEOUT, cache_until=None, check=None):
    """Return the JSON OBJECT the prompt asked for, or raise.

    Every caller immediately does .get() on the result, so a reply that
    parses into a list, a string, or a number is as useless as one that does
    not parse at all - and used to surface three frames away as an opaque
    AttributeError. Both failures are treated the same way here: re-ask once
    with a correction, then give up.

    check: the caller's shape check, check(answer) -> what is wrong with the
    answer's shape, or None when it is right (e.g. common/common_helpers/extraction.py,
    shape_error). An object of the wrong shape is treated like one that isn't
    JSON: asked once more, saying what was wrong, then BadReply."""
    seconds = 0.0
    for attempt in range(retries + 1):
        try:
            text = call_llm(prompt, read_timeout=read_timeout, cache_until=cache_until)
        except Exception as e:                              # noqa: BLE001
            if attempt and isinstance(getattr(e, "call", None), dict):
                e.call["seconds"] = round(e.call["seconds"] + seconds, 1)       # the first ask's time too
            raise
        seconds += (getattr(_last, "timing", None) or {}).get("seconds", 0)
        try:
            data, state = find_json(text)
            if state != "object":
                # One rule for both services (classify_reply): an unfinished object with no finish reason saying
                # the model stopped on its own is a cut-off (CutOff: kept in the cache as cut off, never asked again
                # with the same settings); prose declining the task is a refusal (Refused: never asked again, never
                # stored). The service clients raise these before the text gets here; this is the same rule, kept
                # here for an answer that reaches the parser another way (a cached or edited one).
                reply = getattr(_last, "reply", None) or {}
                kind, detail = classify_reply(text, reply.get("finish_reason"), reply.get("native_finish_reason"))
                if kind == "cut_off":
                    raise _with_reply(CutOff(f"the answer was cut off: {detail}"), text, reply, reply.get("finish_reason"))
                if kind == "refused":
                    raise _with_reply(Refused(f"the model refused to answer: {detail}"), text, reply,
                                      reply.get("finish_reason"))
                raise BadReply(detail)
            if not isinstance(data, dict):
                raise BadReply(f"expected a JSON object, got "
                               f"{type(data).__name__}")
            wrong = check(data) if check else None
            if wrong:
                raise WrongShape(wrong)
            if attempt:
                with _requests_lock:
                    REASKS["fixed"] += 1
            return data
        except (json.JSONDecodeError, BadReply) as e:
            # The whole answer goes to the log file (DEBUG: not shown on screen), so a person can see what broke it.
            log.debug(f"unusable answer from {MODEL} (attempt {attempt + 1} of {retries + 1}), "
                      f"{len(text):,} characters, {e}:\n{text}")
            shape = isinstance(e, WrongShape)
            with _requests_lock:
                if not attempt:
                    REASKS["wrong_shape" if shape else "not_json"] += 1
                if attempt == retries:
                    REASKS["still_failed"] += 1
            if attempt == retries:
                error = BadReply(f"the model's answer isn't "
                                 + ("a JSON object of the shape asked for" if shape else "a valid JSON object")
                                 + f", {retries + 1} times ({e}); each "
                                 f"answer is in this run's log (outputs/logs/<run id>.log), on a DEBUG line starting "
                                 f"\"unusable answer\"")
                reply = getattr(_last, "reply", None) or {}
                error.answer, error.usage, error.finish_reason = text, reply.get("usage") or {}, reply.get("finish_reason")
                error.call = {**reply, "attempts": (getattr(_last, "timing", None) or {}).get("attempts"),
                              "asks": retries + 1, "seconds": round(seconds, 1)}
                raise error from None
            if shape:
                log.warning(f"The model's reply is a JSON object of the wrong shape ({e}); asking once more, saying "
                            f"what was wrong. Nothing to do.")
                prompt += (f"\n\nYour last reply was not in the shape asked for: {e}. "
                           "Return ONLY the JSON object, in the shape asked for, no fences, no prose.")
                continue
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

#: The early stop: when EARLY_STOP_FAILURES of a run's first EARLY_STOP_WINDOW calls about records' text pieces
#: (common/common_helpers/extraction.py, ask_model: 040's extraction, 050, 060; the test call not counted) fail,
#: cut-offs included, the step stops before paying for more: a fault that hits that many of the first calls (a limit
#: too small for the model's thinking, a model that answers in the wrong shape) would most likely hit the rest too.
#: Later failures don't stop the run: by then most calls have worked, and the failed ones are left out and listed.
EARLY_STOP_WINDOW = 10
EARLY_STOP_FAILURES = 3

#: The test call's check (PaidCalls.start): a one-line answer whose thinking used this share of MAX_ANSWER_TOKENS or
#: more leaves a record's answer too little room, so the run asks again before paying for more.
THINKING_WARN_SHARE = 0.5

#: The progress lines while calls are made: at most one every PROGRESS_SECONDS seconds (the first and the last call
#: of a stage always shown), with the time left estimated once PROGRESS_ESTIMATE_AFTER calls have finished.
PROGRESS_SECONDS = 10
PROGRESS_ESTIMATE_AFTER = 3

#: This run's failed model calls: how many failed, how many of them were cut off, how many weren't made because of the
#: early stop, and the file that describes each (failed_calls_file), for the report and the run's last lines.
#: Reset by paid_calls.
OUTCOMES = {"failed": 0, "cut_off": 0, "not_sent": 0, "file": None}

#: Warnings found while the run paid (the test call's check), for the report's Warnings (common/common_helpers/step.py).
RUN_WARNINGS = []


class EarlyStop(SystemExit):
    """The early stop (EARLY_STOP_FAILURES of the first EARLY_STOP_WINDOW calls failed). A SystemExit, so the step
    stops with its report and log; run_parallel first lets the calls already under way finish and keeps their
    answers."""

    def __init__(self, message: str, paid):
        super().__init__(message)
        self.paid = paid


def _lower_thinking() -> str | None:
    """How to leave the answer more of MAX_ANSWER_TOKENS by thinking less, with this run's settings; None when the
    pipeline can't cap this model's thinking."""
    sent = thinking_sent()
    if sent and sent != "low":
        lower = " or ".join(f"`--thinking {t}`" for t in reversed(THINKING_LEVELS[:THINKING_LEVELS.index(sent)]))
        return f"set the step's thinking setting lower (it is {sent}; {lower})"
    if THINKING == "model_default" and takes_thinking_cap():
        return "give `--thinking low` (the thinking isn't capped: thinking is model_default)"
    return None


def cut_off_advice(usage=None) -> str:
    """What to change after an answer was cut off at MAX_ANSWER_TOKENS (or a test call thought too much), from the
    token counts the service reported, not from the settings: thinking took most of the tokens, the answer itself is
    long, or the service didn't say how many were thinking."""
    usage = usage if isinstance(usage, dict) else {}
    if max_tokens_sent() is None:
        return ("Ask Sage takes no answer limit (MAX_ANSWER_TOKENS isn't sent), so the model's own limit cut the "
                "answer: lower the step's max_chars so each text piece asks for fewer facts, choose another model "
                "(`--model`), or run through LiteLLM (`--service litellm`), which takes the limit")
    details = usage.get("completion_tokens_details")
    reported = isinstance(details, dict) and details.get("reasoning_tokens") is not None
    thought, total = reasoning_tokens(usage), usage.get("completion_tokens")
    limit = f"MAX_ANSWER_TOKENS in common/common_helpers/llm.py (now {MAX_ANSWER_TOKENS:,})"
    shorter = f"raise {limit}, or, when the text piece is long, lower the step's max_chars so each answer is shorter"
    if not reported:
        lower = _lower_thinking()
        got = f" (the answer got {total:,} tokens in all)" if isinstance(total, int) else ""
        return (f"Thinking tokens not reported; can't tell which used the {MAX_ANSWER_TOKENS:,} tokens, the model's "
                f"thinking or the answer itself{got}: "
                + (f"if the model thinks, {lower}, so more of the tokens are left for the answer; if not, " if lower
                   else "") + shorter)
    if thought >= THINKING_WARN_SHARE * MAX_ANSWER_TOKENS:
        sent = thinking_sent()
        if sent == "low":
            fix = (f"the thinking is already at its lowest cap (low): raise {limit} and give `--thinking "
                   f"model_default`, or choose another model (`--model`)")
        else:
            fix = _lower_thinking()
            fix = (f"{fix}, so more of the tokens are left for the answer" if fix else
                   f"the pipeline can't cap this model's thinking: raise {limit}, or choose another model (`--model`)")
        return (f"Thinking used most of the tokens: the model spent {thought:,} of the {MAX_ANSWER_TOKENS:,} tokens "
                f"thinking, leaving {MAX_ANSWER_TOKENS - thought:,} for the answer; {fix}")
    answer = f" and {total - thought:,} on the answer" if isinstance(total, int) else ""
    return (f"The answer itself is long: the model spent {thought:,} of the {MAX_ANSWER_TOKENS:,} tokens thinking"
            f"{answer}; {shorter}")


def advice(error) -> str:
    """What to do about one failed call, in words: the same advice the messages and the failed-call record give."""
    if isinstance(error, CutOff):
        return cut_off_advice(getattr(error, "usage", None))
    if isinstance(error, Refused):
        return ("Asking again gets the same answer. Look at the record's text; if refusals (the service's filter, or "
                "the model declining in prose) come often with this model, choose another (`--model`)")
    if "no answer within" in str(error):
        return "Run the step again later; if it keeps happening, lower the step's max_chars"
    if isinstance(error, BadReply):
        return ("Read the answer (in the failed-call record or the log) to see what the model wrote instead of the "
                "JSON object; if this model keeps doing it, choose another (`--model`)")
    return ("Read the error: rate limits and server errors usually pass, so run the step again; if it keeps failing, "
            "check the connection and the key in .env")


def failed_calls_file() -> Path | None:
    """outputs/logs/<run id>_failed_calls.jsonl, beside the run's log; None outside a run."""
    from common.audit import current_run_id
    from common.step import LOGS_DIR
    run_id = current_run_id()
    return LOGS_DIR / f"{run_id}_failed_calls.jsonl" if run_id else None


def _usage_counts(usage) -> dict:
    usage = usage if isinstance(usage, dict) else {}
    return {"prompt_tokens": usage.get("prompt_tokens"), "answer_tokens": usage.get("completion_tokens"),
            "reasoning_tokens": reasoning_tokens(usage) if usage else None}


def _duration(seconds: float) -> str:
    return f"{seconds:.0f} s" if seconds < 90 else f"{seconds / 60:.0f} min" if seconds < 5400 else f"{seconds / 3600:.1f} h"


class PaidCalls:
    """Asks once, just before a run's first paid call; checks the test call; counts the calls, shows their progress,
    records each failed one, and stops the run early when its first calls fail.

    A stage calls start(plan) before it makes any call a cache couldn't answer, expect(n) before n calls, and, as each
    call ends, made_call() (when it answered) and outcome(where, prompt, error). The first start() logs the plan,
    asks the person to press Enter (unless confirm is False, for runs with nobody at the keyboard), and makes one tiny
    test call, so a wrong model name or key fails once here instead of once per text; its token counts are checked
    (an answer cut off, or thinking that leaves too little room, is said before paying for more). A run whose every
    answer comes from the cache never asks and never pays. Declining exits the run having spent nothing.

    outcome() prints the progress (at most every PROGRESS_SECONDS), writes a failed call to the run's failed-call
    record (failed_calls_file), and raises EarlyStop when EARLY_STOP_FAILURES of the first EARLY_STOP_WINDOW calls
    failed.

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
        self.clock = time.monotonic         # replaced by the tests
        self.ended = 0                      # calls the early stop watches, ended this run, answered or failed
        self.failures = []                  # (where, error) of each of those that failed
        self.stopped = False
        self._batch = {"total": None, "done": 0, "failed": 0, "cut": 0, "began": 0.0, "shown": None}

    def start(self, plan: str) -> None:
        if self.started:
            return
        log.info(plan)
        log.info(f"model: {MODEL}, through {SERVICES.get(SERVICE, SERVICE)}"
                 + (f", thinking {thinking_sent()}" if thinking_sent() else ""))
        if self.notes:
            show_warnings(self.step, self.notes)
        if self.confirm:
            confirm("Press Enter to start (1 test call first), or anything else to cancel."
                    if not self.notes else
                    "Press Enter to go ahead anyway (1 test call first), or anything else to cancel.")
        again = f"`py {self.step}/run.py`" if self.step else "the step"
        service = SERVICES.get(SERVICE, SERVICE)
        try:
            call_llm(TEST_PROMPT, attempts=2)
        except Exception as e:                              # noqa: BLE001
            OUTCOMES["failed"] += 1
            OUTCOMES["cut_off"] += isinstance(e, CutOff)
            self._record({"stage": "test call"}, TEST_PROMPT, e)
            self._test_call_failed(e, again, service)
        self.started = True
        self.test_calls = 1
        self._check_test_call()

    def _test_call_failed(self, e: Exception, again: str, service: str) -> None:
        """Stop the run: the test call failed (e), so no other call is made."""
        file = f" The call is described in {OUTCOMES['file']}." if OUTCOMES["file"] else ""
        if isinstance(e, CutOff):
            sys.exit(f"Test call to {MODEL} through {service} was cut off at the longest length allowed "
                     f"({MAX_ANSWER_TOKENS:,} tokens) on a one-line answer, so no other model call was made: every "
                     f"answer of this run would be cut off too. {cut_off_advice(getattr(e, 'usage', None))}; then run "
                     f"{again} again.{file}")
        sys.exit(f"Test call to {MODEL} through {service} failed ({e}), so no other model "
                 f"call was made. If {service} says the model "
                 f"isn't allowed, give another with --model <name> (`py helpers/models.py --service {SERVICE} --try <name> ...` "
                 f"tells which you may use)"
                 + (f"; if it names reasoning_effort, give `--thinking model_default`, which sends no thinking cap"
                    if thinking_sent() else "")
                 + f"; otherwise check your key in .env and that you're on NASA's network. Then run {again} again.{file}")

    def _check_test_call(self) -> None:
        """One line on the test call's token counts, and a stop to think when its thinking leaves too little room."""
        reply = getattr(_last, "reply", None) or {}
        usage = reply.get("usage") or {}
        if not usage:
            log.info(f"  test call: ok ({SERVICES.get(SERVICE, SERVICE)} reports no token counts)")
            return
        thought = reasoning_tokens(usage)
        answer = (usage.get("completion_tokens") or 0) - thought
        log.info(f"  test call: ok (answer {answer:,} tokens, thinking "
                 + (f"{thought:,} tokens)" if "completion_tokens_details" in usage else "not reported)"))
        if thought < THINKING_WARN_SHARE * MAX_ANSWER_TOKENS:
            return
        note = (f"The test call's one-line answer used {thought:,} tokens thinking, {thought / MAX_ANSWER_TOKENS:.0%} "
                f"of the {MAX_ANSWER_TOKENS:,} tokens each answer may use (MAX_ANSWER_TOKENS in "
                f"common/common_helpers/llm.py), so a record's longer answer is likely to be cut off. "
                f"{cut_off_advice(usage)}.")
        RUN_WARNINGS.append(note)
        show_warnings(self.step, [note])
        if self.confirm:
            confirm("Press Enter to go ahead anyway, or anything else to cancel (only the test call was paid for).",
                    spent="Only the test call was paid for.")

    def expect(self, total: int) -> None:
        """The next total calls are one stage's: its progress lines count them."""
        with self._lock:
            self._batch = {"total": total, "done": 0, "failed": 0, "cut": 0, "began": self.clock(), "shown": None}

    def made_call(self) -> None:
        with self._lock:                    # stages may call from several threads
            self.made += 1

    def outcome(self, where: dict, prompt: str, error: Exception | None = None, watched: bool = True) -> None:
        """One paid call ended: answered (error None) or failed. Shows the progress, records a failed call, and
        raises EarlyStop when too many of the run's first calls failed. where: {"stage", "record", "text_piece"}, as
        much as the stage knows. watched: whether the early stop counts the call; False for the stages that ask one
        prompt at a time (common/common_helpers/cache.py, ask_cached), which are few, and where a failure is often
        expected and handled (040's labeling asks a refused batch again in halves, to find the item refused)."""
        with self._lock:
            b = self._batch
            if not b["began"]:
                b["began"] = self.clock()
            b["done"] += 1
            self.ended += watched
            if error is not None:
                b["failed"] += 1
                b["cut"] += isinstance(error, CutOff)
                if watched:
                    self.failures.append((where, error))
                OUTCOMES["failed"] += 1
                OUTCOMES["cut_off"] += isinstance(error, CutOff)
                self._record(where, prompt, error)
            self._progress()
            early = (watched and not self.stopped and self.ended <= EARLY_STOP_WINDOW
                     and len(self.failures) >= EARLY_STOP_FAILURES)
            if early:
                self.stopped = True
        if early:
            raise EarlyStop(self._early_stop_message(), self)

    def _progress(self) -> None:
        b, now = self._batch, self.clock()
        last = b["total"] is not None and b["done"] >= b["total"]
        if not (b["shown"] is None or last or now - b["shown"] >= PROGRESS_SECONDS):
            return
        b["shown"] = now
        failed = f"{b['failed']:,} failed" + (f" ({b['cut']:,} cut off)" if b["cut"] else "")
        if b["total"] is None:
            log.info(f"  model calls: {b['done']:,} done, {failed}")
            return
        if last:
            left = f"took {_duration(now - b['began'])}"
        elif b["done"] < PROGRESS_ESTIMATE_AFTER:
            left = "estimating the time left…"
        else:
            left = f"about {_duration((now - b['began']) / b['done'] * (b['total'] - b['done']))} left"
        log.info(f"  model calls: {b['done']:,} of {b['total']:,} done, {failed}, {left}")

    def _early_stop_message(self) -> str:
        what = [f"{w.get('record', w.get('stage', '?'))}"
                + (f" piece {w['text_piece']}" if w.get("text_piece") else "") + f": {e}" for w, e in self.failures]
        cut = [e for _, e in self.failures if isinstance(e, CutOff)]
        todo = cut_off_advice(max((getattr(e, "usage", None) or {} for e in cut), key=reasoning_tokens)) if cut \
            else advice(self.failures[-1][1])
        file = OUTCOMES["file"]
        return (f"Step {self.step.split('_')[0]} stopped early: {len(self.failures)} of the first {self.ended} model "
                f"calls of this run failed ({'; '.join(what)}), so it made no more: the rest would most likely fail "
                f"the same way and be paid for nothing (the early stop: {EARLY_STOP_FAILURES} failed among the first "
                f"{EARLY_STOP_WINDOW}, in common/common_helpers/llm.py). What to do: {todo}."
                + (f" Each failed call is described in {file}." if file else "")
                + f" Answers already received are kept in the cache, so the next run pays only for the rest: run "
                  f"`py {self.step}/run.py` again once that is changed.")

    def not_sent(self, jobs: list) -> None:
        """The calls the early stop prevented, [(where, prompt)]: one line each in the failed-call record."""
        with self._lock:
            for where, prompt in jobs:
                OUTCOMES["not_sent"] += 1
                self._record(where, prompt, None)

    def _record(self, where: dict, prompt: str, error: Exception | None) -> None:
        """One line of the failed-call record: everything needed to see why the call failed (never a key)."""
        path = failed_calls_file()
        if path is None:
            return
        usage = getattr(error, "usage", None)
        entry = {"time": dt.datetime.now().astimezone().isoformat(timespec="seconds"), "step": self.step,
                 "run_id": path.name.removesuffix("_failed_calls.jsonl"), **where,
                 "outcome": "not_sent" if error is None else "cut_off" if isinstance(error, CutOff) else "failed",
                 "service": SERVICE, "model": MODEL,
                 "call_settings": {**call_settings(), "read_timeout_s": READ_TIMEOUT},
                 "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                 "prompt_characters": len(prompt)}
        if error is None:
            entry["why"] = "not made: the early stop stopped the run before this call"
        else:
            call = getattr(error, "call", None) or {}
            usage = usage or call.get("usage")
            entry.update({"finish_reason": getattr(error, "finish_reason", None) or call.get("finish_reason"),
                          "native_finish_reason": call.get("native_finish_reason"), **_usage_counts(usage),
                          "usage": usage or None, "http_status": call.get("http_status"),
                          "error_body": call.get("error_body"), "error_type": type(error).__name__,
                          "cause_type": call.get("cause_type"), "error": str(error),
                          "settings_sent": call.get("settings_sent"), "request_bytes": call.get("request_bytes"),
                          "served_as": call.get("served_as"), "attempts": call.get("attempts"),
                          "asks": call.get("asks"), "seconds": call.get("seconds"),
                          "answer": getattr(error, "answer", None), "what_to_do": advice(error)})
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        OUTCOMES["file"] = path.relative_to(path.parents[2]).as_posix()


@dataclass
class Calls:
    """What a step's model-calling stages share: the confirmation-and-count
    (PaidCalls) and the folder that keeps every answer (common/common_helpers/cache.py)."""
    paid: PaidCalls
    cache_dir: Path


def paid_calls(settings: dict, output, notes: list = (), session_id: str | None = None) -> Calls:
    """The Calls of one run: uses the model the setting `model` names, through the service the setting `service`
    names, with the thinking cap the setting `thinking` gives; asks before paying (setting confirm_paid_calls),
    showing notes first; answers kept in cache/ inside the step's output folder. A setting it can't use stops the
    step (Stop: `stopped`, a problem the person can fix). session_id: sent with each LiteLLM request of the run
    (SESSION_ID); None sends none."""
    global MODEL, SERVICE, THINKING, REPEAT, SESSION_ID
    from common.step import check_settings                  # the one check of every setting (common.step.shared_specs)
    given = {"service": settings.get("service") if settings.get("service") is not None else SERVICE,
             "model": settings.get("model"), "thinking": settings.get("thinking") if settings.get("thinking") is not None else THINKING,
             "repeat": settings.get("repeat", 1)}
    check_settings({k: v for k, v in given.items() if k != "model" or v is not None}, {})
    service, thinking = str(given["service"]).strip().lower(), str(given["thinking"]).strip().lower()
    name = str(given["model"] or "").strip()
    if not name:
        raise Stop(f"The setting model must be a text (not empty), but is {given['model']!r}, so the step can't run. "
                   f"Give --model <name> (`py helpers/models.py` lists them), then run the step again.")
    repeat = given["repeat"]
    MODEL, SERVICE, THINKING, REPEAT, SESSION_ID = name, service, thinking, repeat, session_id
    SERVED.clear()
    for k in REQUESTS:
        REQUESTS[k] = 0
    for k in REASKS:
        REASKS[k] = 0
    OUTCOMES.update(failed=0, cut_off=0, not_sent=0, file=None)
    RUN_WARNINGS.clear()
    return Calls(paid=PaidCalls(confirm=settings["confirm_paid_calls"], notes=notes, step=Path(output).name),
                 cache_dir=Path(output) / "cache")


def run_parallel(fn, jobs: dict, workers: int, handle, stop_note: str, not_sent=None) -> None:
    """Run fn(*args) for every (key, args) in jobs, workers at a time, and
    call handle(n, key, result, error) in this thread as each finishes (n
    counts from 1; error is None on success, result None on failure).

    Ctrl+C cancels every call not yet started, so a stopped run spends
    nothing more than what is already in flight, then raises Interrupted with stop_note.
    Calls already in flight cannot be recalled; their results are not
    handled.

    When handle raises EarlyStop (PaidCalls.outcome), every call not yet started is cancelled, the calls already under
    way are waited for and handled (so their paid answers are kept), not_sent(keys of the cancelled jobs) is called,
    and the EarlyStop goes on."""
    pool = ThreadPoolExecutor(workers)
    futures, handled = {}, set()
    try:
        futures = {pool.submit(fn, *args): key for key, args in jobs.items()}
        for n, future in enumerate(as_completed(futures), 1):
            try:
                result, error = future.result(), None
            except Exception as e:                      # noqa: BLE001
                result, error = None, e
            handled.add(future)
            handle(n, futures[future], result, error)
    except EarlyStop:
        cancelled = [f for f in futures if f.cancel()]
        under_way = [f for f in futures if f not in handled and f not in cancelled]
        for n, future in enumerate(under_way, len(handled) + 1):
            try:
                result, error = future.result(), None
            except Exception as e:                      # noqa: BLE001
                result, error = None, e
            handle(n, futures[future], result, error)
        if not_sent is not None:
            not_sent([futures[f] for f in cancelled])
        raise
    except KeyboardInterrupt:
        pool.shutdown(wait=False, cancel_futures=True)
        raise Interrupted(f"Stopped with Ctrl+C. Model calls not yet started were cancelled, so they cost nothing. "
                          f"{stop_note}") from None
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


class Interrupted(KeyboardInterrupt):
    """Ctrl+C, with a message saying what it cost. A KeyboardInterrupt, so the step ends `interrupted` (exit code
    130: common/common_helpers/step.py), like a Ctrl+C anywhere else; every answer already received is in the cache."""


def confirm(question: str, spent: str = "Nothing was spent.") -> None:
    """Stop until the person presses Enter (or types y or yes, in any case, spaces around it ignored); exit on
    anything else (the answers, for a person: docs/running_on_nasa_laptop.md, section 5). spent: what was paid
    for before the question.

    The gate between reading a run's summary and paying for it. Any other
    answer and a closed input (a run with nothing attached to the keyboard)
    stop the step (`stopped`); Ctrl+C interrupts it (`interrupted`), so the
    expensive path is never taken by default."""
    try:
        answer = input(f"\n{question} ")
    except EOFError:
        sys.exit(f"\nCancelled. {spent}")
    except KeyboardInterrupt:
        raise Interrupted(f"Cancelled with Ctrl+C. {spent}") from None
    if answer.strip().lower() not in ("", "y", "yes"):
        sys.exit(f"Cancelled. {spent}")
