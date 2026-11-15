"""
common/common_helpers/llm_errors.py -- what can go wrong with a model call, and the two stops no call gets past.

A part of common/common_helpers/llm.py: the errors a call raises (BadReply, WrongShape, ApiError, RetryLater, CutOff,
Refused, NoAnswerInTime), and the two guards every request passes first: a used-up budget (budget_exhausted,
stop_if_budget_gone: BudgetExhausted) and a command that promised to call no model (forbid_model_calls,
stop_if_forbidden: ModelCallForbidden). Import these names from common.llm, as every caller does (llm.py's
docstring says why), never from this file.
"""

import json
import os
import re

from common.llm import ERROR_BODY_CHARS, SERVICES, _requests_lock


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


#: How a service says the account's money is used up: the budget its administrators set, or the provider's quota or
#: credit. Never retried, whatever the HTTP status (LiteLLM sends 400, 401 or 429 for it): asking again fails the same
#: way until someone raises or resets the budget. The forms, compared lower-cased:
#:   LiteLLM's BudgetExceededError, "Budget has been exceeded! … Current cost: …, Max budget: …" (NASA's proxy sends
#:   it as HTTP 429: "Budget has been exceeded! User=… in Team=… Current cost: 25.0, Max budget: 25.0"); its error
#:   type budget_exceeded; "ExceededBudget: User=… over budget. Spend=…, Budget=…", "ExceededTokenBudget: …",
#:   "… exceeded budget for model=…" (https://docs.litellm.ai/docs/proxy/users);
#:   OpenAI's insufficient_quota, "You exceeded your current quota, please check your plan and billing details"
#:   (https://platform.openai.com/docs/guides/error-codes); Anthropic's "Your credit balance is too low to access the
#:   Anthropic API" (https://docs.anthropic.com/en/api/errors).
#: Ask Sage's API documentation gives no form for a used-up monthly token allowance, so its errors are read with the
#: same words, and its answers with ANSWER_BUDGET_WORDS. "budget" alone is not enough: a rate limit's "token budget per
#: minute" or Anthropic's thinking "budget_tokens" is something else.
BUDGET_WORDS = re.compile(r"budget has been exceeded|budget_exceeded|exceeded[ _]?(?:token)?budget(?!_tokens)|"
                          r"\bover budget\b|insufficient_quota|exceeded your current quota|credit balance is too low",
                          re.I)


#: How Ask Sage says the account's monthly token allowance is used up: not as an error but as an answer, HTTP 200 with
#: status 200, in prose (seen on 2026-11-03, through gpt-5.6-sol-gov: "Sorry, if we executed this query (up to 4096
#: tokens), you would be above your monthly token limit (1003014 out of 1000000), please contact your organization
#: admin to get it increased." and "Sorry, you are above your monthly token limit (1011372 out of 1000000), please
#: contact your organization admin to get it increased."). Read only in a short answer that isn't JSON
#: (budget_answer), so a model's answer quoting such words, inside its JSON, is not taken for it.
ANSWER_BUDGET_WORDS = re.compile(r"\babove\b[^.]{0,80}?\bmonthly token limit\b", re.I)


#: The numbers Ask Sage's answer reports: "monthly token limit (1003014 out of 1000000)", tokens used and the limit.
ANSWER_BUDGET_NUMBERS = re.compile(r"monthly token limit\s*\(\s*([0-9][0-9,]*)\s+out of\s+([0-9][0-9,]*)\s*\)", re.I)


#: The longest answer read for ANSWER_BUDGET_WORDS: Ask Sage's two forms have 131 and 183 characters.
ANSWER_BUDGET_CHARS = 600


#: The numbers a budget answer reports: LiteLLM's "Current cost: 25.0, Max budget: 25.0" or "Spend=…, Budget=…".
BUDGET_NUMBERS = re.compile(r"(?:current cost|spend)\s*[:=]\s*([0-9][0-9.eE+-]*?)[,;\s]+(?:max budget|budget)\s*[:=]\s*"
                            r"([0-9][0-9.eE+-]*?)(?=[,;\s]|\.?$|\.\s)", re.I)


def budget_answer(text) -> bool:
    """Whether an answer's whole text is a service saying the account's token allowance is used up
    (ANSWER_BUDGET_WORDS, Ask Sage's form): a short answer, not JSON, with those words."""
    words = str(text or "").strip()
    return (0 < len(words) <= ANSWER_BUDGET_CHARS and not words.startswith(("{", "[", "`"))
            and bool(ANSWER_BUDGET_WORDS.search(words)))


def budget_exhausted(status: int, text) -> bool:
    """Whether a service's answer (HTTP status, its text) says the account's budget or quota is used up: an error
    with BUDGET_WORDS, or, whatever the status, an answer that is only the service saying so (budget_answer). Never
    retried, it stops the run (stop_if_budget_gone). The one place that decides it, beside RETRY_STATUSES."""
    return status >= 400 and bool(BUDGET_WORDS.search(str(text or ""))) or budget_answer(text)


class BudgetExhausted(SystemExit):
    """The service answered that the account's budget or quota is used up. A SystemExit, like EarlyStop, so no
    `except Exception` takes it for one failed call: the whole run stops at once with its message. Once one is
    raised, every later request of this process is refused before it is sent (call_llm, litellm_post), so no worker
    sends another; run_parallel keeps the answers of the calls already under way."""

    def __init__(self, message: str, status: int | None = None, body: str = "", answered: bool = False):
        super().__init__(message)
        self.status, self.body = status, body
        self.answered = answered            # True: this request got the budget answer; False: it was never sent


#: The first BudgetExhausted of this process, or None: no request is sent after it (reset only by the tests).
BUDGET_GONE = {"error": None}


def budget_message(service: str, status: int, text) -> str:
    """The one message for a used-up budget: the service, its words and the numbers they report, what to do."""
    words = " ".join(str(text or "").split())[:400]
    found, tokens = BUDGET_NUMBERS.search(words), ANSWER_BUDGET_NUMBERS.search(words)
    numbers = f" It reports a cost of {found.group(1)} against a budget of {found.group(2)}." if found else ""
    if tokens:
        used, limit = (int(n.replace(",", "")) for n in tokens.groups())
        numbers = f" It reports {used:,} tokens used against this account's monthly limit of {limit:,}."
    where = SERVICES.get(service, service)
    said = f"HTTP {status}: {words}" if status >= 400 else f"in its answer: {words}"
    return (f"{where} answered that the budget for this account is used up ({said}).{numbers} The run "
            f"stopped at once: no other model call was sent, and none will be until the budget changes. Answers "
            f"already received are kept in the cache, so nothing is paid for twice. What to do: ask the {where} "
            f"administrators to raise or reset the budget (docs/running_on_nasa_laptop.md, *The budget is used up*); "
            f"there is nothing to retry before that. Then run the same command again: it pays only for the calls not "
            f"yet answered.")


def stop_if_budget_gone(service: str, status: int | None = None, text=None, said=None) -> None:
    """Raise BudgetExhausted when an earlier answer of this process said the budget is used up, or when this one
    (HTTP status, its whole text) says so (budget_exhausted); else nothing. said: the error's own words for the
    message (e.g. LiteLLM's error message, out of its JSON body); text when None."""
    answered = status is not None and budget_exhausted(status, text)
    with _requests_lock:
        gone = BUDGET_GONE["error"]
        if gone is None and answered:
            gone = BUDGET_GONE["error"] = BudgetExhausted(budget_message(service, status, said or text), status,
                                                          str(text or "")[:ERROR_BODY_CHARS])
    if gone is not None:
        raise BudgetExhausted(gone.code, gone.status, gone.body, answered)


class ModelCallForbidden(SystemExit):
    """A model call in a run that promised to call none (forbid_model_calls). A SystemExit, like BudgetExhausted, so
    no `except Exception` takes it for one failed call: the run stops at once, before the request is sent."""


#: The environment variable that carries forbid_model_calls into the processes a free command starts (py
#: helpers/reproduce_results.py runs the steps, each in its own process): JSON {"why", "advice"}.
FORBID_ENV = "KG_NO_MODEL_CALLS"


def _forbidden_from_env() -> dict:
    """forbid_model_calls as a parent process set it (FORBID_ENV), or nothing forbidden."""
    try:
        got = json.loads(os.environ.get(FORBID_ENV) or "null")
    except ValueError:
        got = None
    return {"why": got.get("why"), "advice": got.get("advice")} if isinstance(got, dict) else {"why": None, "advice": None}


#: Why this process may send no model call (forbid_model_calls), or None: model calls are allowed; and advice, what
#: to do when a step would need one (None: such a call is a mistake in the code).
FORBIDDEN = _forbidden_from_env()


def forbid_model_calls(why: str, advice: str | None = None) -> None:
    """From now on, this process and every process it starts send no model call: PaidCalls.start, call_llm and
    litellm_post stop the run (ModelCallForbidden) before a request leaves. Called first by every command whose docs
    say it is free (py helpers/second_opinion.py --apply true, py helpers/partial_pairs.py, py helpers/compare_runs.py,
    py helpers/review_page.py, py helpers/reproduce_results.py, the listing of py helpers/models.py), so "free" is
    guaranteed by code, not only by how the command is written. why: the command and why it is free, for the message.
    advice: what to do when a step it runs would need a model call (an answer missing from a cache); None when no call
    can be meant, so one is a mistake in the code."""
    FORBIDDEN.update(why=why, advice=advice)
    os.environ[FORBID_ENV] = json.dumps({"why": why, "advice": advice})


def allow_model_calls() -> None:
    """Undo forbid_model_calls (only the tests, which run several commands in one process)."""
    FORBIDDEN.update(why=None, advice=None)
    os.environ.pop(FORBID_ENV, None)


def _forbidden_message(what: str) -> str:
    """Why the run stopped before a model call: what (the call, or the calls a stage was about to pay for), why the
    command calls no model, and what to do."""
    return (f"{what}, but this command calls no model ({FORBIDDEN['why']}), so the run stopped before any request "
            f"left: nothing was sent and nothing was paid. "
            + (FORBIDDEN["advice"] or "This is a mistake in the code, not in your files: report it with this message."))


def stop_if_forbidden() -> None:
    """Raise ModelCallForbidden when this process may send no model call (forbid_model_calls); else nothing."""
    if FORBIDDEN["why"] is not None:
        raise ModelCallForbidden(_forbidden_message("A model call was about to be sent"))


class CutOff(ApiError):
    """The answer was cut off: at the longest length allowed (MAX_ANSWER_TOKENS, which LiteLLM takes), or, where the
    service takes no limit and reports no finish reason (Ask Sage), at the model's own limit, seen in the answer
    stopping inside an unfinished JSON object (classify_reply). Not retried: asking again with the same settings
    gets the same cut. Carries what the service sent (answer, usage, finish_reason), for the failed-call record."""


class Refused(ApiError):
    """The model, or its service, declined to answer: a filter's finish reason (REFUSAL_REASONS), or an answer in
    prose declining the task (REFUSAL_WORDS) with no JSON object in it, sent as HTTP 200. Not retried: asking again
    gets the same answer; never stored as an answer (common/common_helpers/cache.py). Carries what the service sent."""


class NoAnswerInTime(Exception):
    """A maker's SDK gave up waiting for the answer (its read timeout, READ_TIMEOUT): call_llm treats it as it treats
    requests' ReadTimeout, never asking again, since the service may still be writing, and billing, the first answer."""
