"""
common/common_helpers/llm_litellm.py -- the LiteLLM client: one request, the reply text.

A part of common/common_helpers/llm.py: NASA's LiteLLM proxy, which speaks the OpenAI API: the request's address and
key (_litellm), the one place a LiteLLM request leaves (_post, through litellm_post), the chat completions request
(_chat_payload, _messages) and reply (_read_chat_reply), which OpenAI's own API reuses (common/common_helpers/
llm_makers.py), and the model list (_litellm_models). Import these names from common.llm, never from this file.
"""

import os

import requests

from common import llm
from common.llm import (
    SERVICES, SESSION_HEADER, TEMPERATURE, _env, _last, answer_cache_control, answer_limit_name, maker,
    max_tokens_sent, temperature_sent, thinking_sent)
from common.llm_errors import ApiError, RETRY_STATUSES, RetryLater, _retry_after, stop_if_budget_gone, stop_if_forbidden
from common.llm_replies import _count_tokens, _finish_reply, _http_reply, _note_request


#: NASA's LiteLLM proxy, which speaks the OpenAI API; LITELLM_BASE_URL in .env overrides it.
LITELLM_BASE = "https://proxy.fast.luna.nasa.gov"


def _litellm(path: str) -> tuple:
    """(address, headers) of a LiteLLM request."""
    llm.load_dotenv()
    base = (os.getenv("LITELLM_BASE_URL") or LITELLM_BASE).rstrip("/")
    key = _env("LITELLM_API_KEY", "no model can be called through LiteLLM")
    return f"{base}{path}", {"Authorization": f"Bearer {key}"}


def _litellm_said(resp) -> str:
    """The error LiteLLM sent, in words: its message when the body has one, else the body."""
    try:
        err = resp.json().get("error")
        text = err.get("message") if isinstance(err, dict) else err
    except (ValueError, AttributeError):
        text = None
    return str(text or resp.text)


def _litellm_error(resp) -> str:
    """The error LiteLLM sent, in words, after its HTTP status: its message, or the start of the body."""
    return f"HTTP {resp.status_code}: {_litellm_said(resp)[:300]}"


def _litellm_models() -> list:
    url, headers = llm._litellm("/v1/models")
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


def _post(*args, **kwargs):
    """requests.post, looked up when called: the one place a LiteLLM request leaves (the tests' stand-in replaces it)."""
    return requests.post(*args, **kwargs)


def litellm_post(url, headers, json, timeout):
    """One LiteLLM request, as every LiteLLM request is sent (the steps', and those of py helpers/check_effort.py and
    py helpers/check_answer_cache.py): none after a used-up budget, and an answer saying the budget is used up stops
    the run (stop_if_budget_gone)."""
    stop_if_forbidden()                                     # a free command sends nothing
    stop_if_budget_gone("litellm")
    resp = llm._post(url, headers=headers, json=json, timeout=timeout)
    if resp.status_code >= 400:
        if isinstance(getattr(_last, "reply", None), dict):
            _http_reply(resp)                               # for the failed-call record
        stop_if_budget_gone("litellm", resp.status_code, resp.text, _litellm_said(resp))
    return resp


def _ask_litellm(prompt: str, model: str, read_timeout: int, cache_until: str | None = None) -> str:
    """One request to LiteLLM (the OpenAI chat completions API); the reply text. The exact model that answered,
    when the reply names it, goes into SERVED for the run's record."""
    url, headers = llm._litellm("/v1/chat/completions")
    if llm.SESSION_ID:
        headers[SESSION_HEADER] = llm.SESSION_ID                # one deployment per run, where the proxy pins sessions
    payload = _chat_payload(prompt, model, cache_until, "litellm")
    payload.update(answer_cache_control())                  # a fresh answer, where the proxy caches answers
    _note_request(payload, ("messages",))
    resp = litellm_post(url, headers=headers, json=payload, timeout=(5, read_timeout))
    _http_reply(resp)
    if resp.status_code in RETRY_STATUSES:
        raise RetryLater(_litellm_error(resp), _retry_after(resp))   # worth retrying
    if resp.status_code >= 400:
        raise ApiError(_litellm_error(resp))                # will not fix itself (key, model, request)
    return _read_chat_reply(resp.json(), "litellm")


def _chat_payload(prompt: str, model: str, cache_until: str | None, service: str) -> dict:
    """The body of a chat completions request (the OpenAI API, which LiteLLM speaks too): the messages, the answer
    limit under its name (answer_limit_name), the temperature and the thinking level only where they are sent
    (temperature_sent, thinking_sent). The one builder of LiteLLM's requests and OpenAI's own."""
    payload = {"model": model, "messages": _messages(prompt, model, cache_until),
               answer_limit_name(model, service): max_tokens_sent(service)}
    if temperature_sent(model, service):
        payload["temperature"] = TEMPERATURE
    if thinking_sent(model, service):
        payload["reasoning_effort"] = thinking_sent(model, service)
    return payload


def _read_chat_reply(body: dict, service: str) -> str:
    """The answer of a chat completions reply (LiteLLM's, or OpenAI's own as its SDK returns it, model_dump'ed):
    the text, judged by _finish_reply with the reply's finish reason, token counts and served model."""
    try:
        choice = body["choices"][0]
        text = choice["message"]["content"]
    except (KeyError, IndexError, TypeError):
        usage = body.get("usage") if isinstance(body, dict) and isinstance(body.get("usage"), dict) else {}
        _count_tokens(usage)                                # billed all the same
        _last.reply["usage"] = usage
        raise RuntimeError(f"{SERVICES.get(service, service)}'s reply has no answer in it: {str(body)[:300]}") from None
    # The model maker's own reason (e.g. Gemini's "MAX_TOKENS" or "SAFETY"), when LiteLLM passes it on: at the choice's
    # top level, or among its provider_specific_fields.
    extra = choice.get("provider_specific_fields") if isinstance(choice.get("provider_specific_fields"), dict) else {}
    return _finish_reply(service, text, body.get("usage"), choice.get("finish_reason"),
                         choice.get("native_finish_reason") or extra.get("native_finish_reason"), body.get("model"))
