"""
common/common_helpers/llm_calls.py -- every service: send a prompt, get the reply.

A part of common/common_helpers/llm.py: call_llm (the reply text; retries rate limits and server errors with
backoff), call_llm_json (the JSON object the prompt asked for; asks once more when the reply isn't one, or not of
the shape the caller checks for), try_model (one one-line test call), list_models (free), and fence_safe (keeps a
record from ending its data block early). Import these names from common.llm, never from this file.
"""

import json
import random
import time

import requests

from common import llm
from common.audit import log
from common.llm import DIRECT_SERVICES, READ_TIMEOUT, REASKS, REQUESTS, _last, _requests_lock
from common.llm_errors import (
    ApiError, BadReply, CutOff, NoAnswerInTime, Refused, WrongShape, stop_if_budget_gone, stop_if_forbidden)
from common.llm_replies import _with_call, _with_reply, classify_reply, find_json
from common.llm_asksage import _asksage_models
from common.llm_litellm import _litellm_models
from common.llm_makers import _direct_models


def list_models(service: str | None = None) -> list:
    """The model names the service lists for your account. Free: listing is not a model call. Being listed doesn't
    guarantee access."""
    service = service or llm.SERVICE
    if service in DIRECT_SERVICES:
        return _direct_models(service)
    return _litellm_models() if service == "litellm" else _asksage_models()


#: The client of each service: one request, the reply text (call_llm).
_ASK = {"asksage": lambda *a: llm._ask_asksage(*a), "litellm": lambda *a: llm._ask_litellm(*a),
        "anthropic": lambda *a: llm._ask_anthropic(*a), "openai": lambda *a: llm._ask_openai(*a),
        "google": lambda *a: llm._ask_google(*a)}


def call_llm(prompt, attempts=4, read_timeout=READ_TIMEOUT, model=None, service=None, cache_until=None):
    """Send prompt to the model, through the service; the reply text. Retries with exponential backoff on rate
    limits, server errors, and lost connections; a refusal that will not fix itself (ApiError) is raised at once; a
    used-up budget (BudgetExhausted) stops the whole run.
    model, service: MODEL and SERVICE (the run's) when None."""
    model, service = model or llm.MODEL, service or llm.SERVICE
    # cache_until: where the prompt's identical start ends, for prompt caching (_messages); Ask Sage doesn't use it
    ask = _ASK[service]
    began, _last.reply = time.monotonic(), {}
    for attempt in range(attempts):
        stop_if_forbidden()                                 # a free command sends nothing (forbid_model_calls)
        stop_if_budget_gone(service)                        # none after a used-up budget, retries included
        with _requests_lock:
            REQUESTS["sent"] += 1
        try:
            text = ask(prompt, model, read_timeout, cache_until)
            _last.timing = {"attempts": attempt + 1, "seconds": round(time.monotonic() - began, 1)}
            return text
        except (requests.ReadTimeout, NoAnswerInTime) as e:
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
        llm.call_llm(TEST_PROMPT, attempts=2, model=name, service=service)
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
            text = llm.call_llm(prompt, read_timeout=read_timeout, cache_until=cache_until)
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
            log.debug(f"unusable answer from {llm.MODEL} (attempt {attempt + 1} of {retries + 1}), "
                      f"{len(text):,} characters, {e}:\n{text}")
            shape = isinstance(e, WrongShape)
            from common import dropped
            dropped.discard("model calls", "reply", ("a JSON object of the wrong shape" if shape else "not a JSON "
                            "object") + f" ({e}), " + ("so the call fails" if attempt == retries else "asked once more"),
                            {"model": llm.MODEL, "attempt": attempt + 1, "answer": text})
            with _requests_lock:
                if not attempt:
                    REASKS["wrong_shape" if shape else "not_json"] += 1
                if attempt == retries:
                    REASKS["still_failed"] += 1
            if attempt == retries:
                error = BadReply("the model's answer isn't "
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


def fence_safe(text: str, end_line: str) -> str:
    """Defang end_line wherever it appears inside text.

    A prompt wraps each record between a BEGIN and an END line, and tells
    the model everything between them is data. A delimiter only delimits if
    the data cannot contain it, so any copy of end_line inside the record
    is spaced out ("-----" becomes "- - - - -"), and the record can never
    end the block early and have the rest of its text read as
    instructions."""
    return text.replace(end_line, " ".join(end_line.replace("-", " - ").split()))
