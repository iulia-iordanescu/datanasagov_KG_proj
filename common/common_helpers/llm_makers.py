"""
common/common_helpers/llm_makers.py -- the makers' own APIs: Anthropic's, OpenAI's and Google's, each through its
maker's official Python SDK: one request, the reply text.

A part of common/common_helpers/llm.py: the SDK, imported only when its service is used (_sdk), one client per
process (_sdk_client), the SDKs' errors made the pipeline's own (_sdk_error), each maker's request and reply
(_ask_anthropic, _ask_openai, _ask_google), and the model list (_direct_models). What each service reads from .env
and calls its settings is llm.DIRECT_SERVICES. Import these names from common.llm, never from this file.
"""

import json
import sys

from common.llm import (
    DIRECT_SERVICES, ERROR_BODY_CHARS, READ_TIMEOUT, SERVICES, TEMPERATURE, _env, _last, _requests_lock,
    max_tokens_sent, temperature_sent, thinking_sent)
from common.llm_errors import (
    ApiError, NoAnswerInTime, RETRY_STATUSES, RetryLater, _retry_after, stop_if_budget_gone, stop_if_forbidden)
from common.llm_replies import _finish_reply, _note_request
from common.llm_litellm import _chat_payload, _messages, _read_chat_reply


#: The SDK clients made so far in this process, by (service, read timeout): one client serves every thread.
_clients = {}


def _sdk(service: str):
    """The SDK module of a maker's own API, imported only here, when the service is used: every other service and
    command runs without these packages installed. A missing package stops the run with what to install."""
    try:
        if service == "anthropic":
            import anthropic
            return anthropic
        if service == "openai":
            import openai
            return openai
        from google import genai
        return genai
    except ImportError:
        package = DIRECT_SERVICES[service]["package"]
        sys.exit(f"The package {package} isn't installed, so no model can be called through {SERVICES[service]} (the "
                 f"setting service is {service}). Run `pip install -r requirements.txt` in the repository folder "
                 f"(docs/running_on_nasa_laptop.md), then run the command again.")


def _new_client(service: str, api_key: str, read_timeout: int):
    """A client of the maker's SDK, with its own retries turned off (call_llm retries, and counts every request sent),
    and a timeout of read_timeout seconds. Anthropic's and OpenAI's clients take `api_key`, `max_retries` (0 turns
    retries off) and `timeout` in seconds (Anthropic: the claude-api reference, "Client Configuration"; OpenAI: its
    SDK's README). Google's takes `api_key` and `http_options`, whose `timeout` is "in milliseconds" and whose
    `retry_options` attempts are the "Maximum number of attempts, including the original request ... If 0 or 1, it
    means no retries. If not specified, default to 5" (google-genai's google/genai/types.py, HttpOptions and
    HttpRetryOptions, read 2026-11-14)."""
    sdk = _sdk(service)
    if service == "anthropic":
        return sdk.Anthropic(api_key=api_key, max_retries=0, timeout=float(read_timeout))
    if service == "openai":
        return sdk.OpenAI(api_key=api_key, max_retries=0, timeout=float(read_timeout))
    from google.genai import types
    return sdk.Client(api_key=api_key, http_options=types.HttpOptions(
        timeout=int(read_timeout * 1000), retry_options=types.HttpRetryOptions(attempts=1)))


def _sdk_client(service: str, read_timeout: int = READ_TIMEOUT):
    """The process's client of the maker's own API (made once, _new_client), with the key from .env: a missing key
    stops the run, saying which key and where to put it (_env)."""
    with _requests_lock:
        client = _clients.get((service, read_timeout))
    if client is None:
        key = _env(DIRECT_SERVICES[service]["key"], f"no model can be called through {SERVICES[service]}")
        client = _new_client(service, key, read_timeout)
        with _requests_lock:
            client = _clients.setdefault((service, read_timeout), client)
    return client


def _as_dict(obj) -> dict:
    """An SDK's reply object as plain JSON data (the SDKs' objects are pydantic models: model_dump)."""
    if isinstance(obj, dict):
        return obj
    dump = getattr(obj, "model_dump", None)
    if callable(dump):
        try:
            return dump(mode="json")  # pyright: ignore[reportReturnType]  (the SDKs' model_dump returns a dict)
        except TypeError:
            return dump()  # pyright: ignore[reportReturnType]  (the SDKs' model_dump returns a dict)
    return {}


def _sdk_status(error) -> int | None:
    """The HTTP status an SDK's error carries, or None when it carries none (a timeout, a lost connection, a fault in
    the code). Anthropic's and OpenAI's APIStatusError have `status_code` (their SDKs' README); google-genai's
    errors.APIError has `code` ("print(e.code)  # 404": https://googleapis.github.io/python-genai/)."""
    for name in ("status_code", "code"):
        status = getattr(error, name, None)
        if isinstance(status, int) and not isinstance(status, bool) and 100 <= status < 600:
            return status
    return None


def _sdk_said(error) -> str:
    """An SDK's error in words: its message, and the error body the service sent when the SDK keeps it."""
    message = str(getattr(error, "message", None) or error)
    body = getattr(error, "body", None)
    if body and str(body) not in message:
        message += f" {json.dumps(body, ensure_ascii=False, default=str) if isinstance(body, (dict, list)) else body}"
    return message


def _sdk_error(service: str, error: Exception, paid: bool = True) -> Exception:
    """The pipeline's own error for an SDK's error, judged as LiteLLM's are: a used-up budget stops the run (paid
    calls only: stop_if_budget_gone); a rate limit or server error is worth asking again (RetryLater, after the
    retry-after the service sent); any other HTTP status will not fix itself (ApiError); a timeout is NoAnswerInTime;
    a lost connection is worth asking again (RuntimeError). Which of the last two an error without a status is, is
    read from its Python type's name (anthropic.APITimeoutError and openai.APITimeoutError, each a subtype of
    APIConnectionError; google-genai's transport errors come from httpx2, whose type names are not verified here).
    Anything else is returned unchanged: a fault in the code, not the service's answer."""
    status = _sdk_status(error)
    name = type(error).__name__
    if status is not None:
        said = _sdk_said(error)
        if paid and isinstance(getattr(_last, "reply", None), dict):
            _last.reply["http_status"], _last.reply["error_body"] = status, said[:ERROR_BODY_CHARS]
        if paid:
            stop_if_budget_gone(service, status, said)
        response = getattr(error, "response", None)
        message = f"HTTP {status}: {' '.join(said.split())[:300]}"
        if status in RETRY_STATUSES:
            return RetryLater(message, _retry_after(response) if hasattr(response, "headers") else None)
        return ApiError(message)
    if isinstance(error, TimeoutError) or "Timeout" in name:
        return NoAnswerInTime(f"{name}: {error}")
    if any(w in name for w in ("Connection", "Connect", "Network", "Transport", "Protocol")):
        return RuntimeError(f"no connection to {SERVICES[service]} ({name}: {error})")
    return error


def _sdk_send(service: str, send):
    """send() (one request through a maker's SDK), as every such request is sent: none in a free command
    (stop_if_forbidden) or after a used-up budget (stop_if_budget_gone), and its errors made the pipeline's own
    (_sdk_error)."""
    stop_if_forbidden()
    stop_if_budget_gone(service)
    try:
        return send()
    except Exception as e:                                  # noqa: BLE001
        mine = _sdk_error(service, e)
        if mine is e:
            raise
        raise mine from e


def _anthropic_params(prompt: str, model: str, cache_until: str | None) -> dict:
    """The request to Anthropic's Messages API: the model, `max_tokens` (MAX_ANSWER_TOKENS), the prompt split as
    _messages splits it for Anthropic's models (the start before cache_until as a system block marked
    `cache_control` ephemeral, for prompt caching: "system ... array of TextBlockParam ... cache_control: Create a cache
    control breakpoint at this content block", https://platform.claude.com/docs/en/api/messages), and
    `output_config.effort` where a thinking level is sent (thinking_sent). No `thinking` (adaptive thinking is always
    on, on Claude Opus 5.5: DIRECT_SERVICES) and no `temperature`, `top_p` or `top_k` (TEMPERATURE). Not sent either:
    the server-side refusal `fallbacks`, which would let another model answer a refused request and so mix models in
    one run's answers; a refusal is recorded as one (Refused)."""
    messages = _messages(prompt, model, cache_until)
    params = {"model": model, "max_tokens": max_tokens_sent("anthropic")}
    if messages[0]["role"] == "system":
        params["system"] = messages[0]["content"]
        messages = messages[1:]
    params["messages"] = messages
    if temperature_sent(model, "anthropic"):
        params["temperature"] = TEMPERATURE
    if thinking_sent(model, "anthropic"):
        params["output_config"] = {"effort": thinking_sent(model, "anthropic")}
    return params


def _anthropic_usage(usage) -> dict:
    """Anthropic's token counts in OpenAI's shape, the one _count_tokens and the test call's check read: prompt_tokens
    = input_tokens (those not read from or written to the cache) + cache_read_input_tokens +
    cache_creation_input_tokens; completion_tokens = output_tokens ("the inclusive, authoritative total used for
    billing"); reasoning_tokens = output_tokens_details.thinking_tokens ("Number of output tokens the model generated
    as internal reasoning"), only when the reply reports it (https://platform.claude.com/docs/en/api/messages, the
    Usage object, read 2026-11-14). The reply's own counts are kept beside them (maker_usage)."""
    usage = usage if isinstance(usage, dict) else {}
    read, write = usage.get("cache_read_input_tokens") or 0, usage.get("cache_creation_input_tokens") or 0
    out = {"prompt_tokens": (usage.get("input_tokens") or 0) + read + write,
           "completion_tokens": usage.get("output_tokens") or 0,
           "cache_read_input_tokens": read, "cache_creation_input_tokens": write, "maker_usage": usage}
    details = usage.get("output_tokens_details")
    if isinstance(details, dict) and details.get("thinking_tokens") is not None:
        out["completion_tokens_details"] = {"reasoning_tokens": details["thinking_tokens"]}
    return out


def _ask_anthropic(prompt: str, model: str, read_timeout: int, cache_until: str | None = None) -> str:
    """One request to Anthropic's own API (Messages, through the anthropic SDK); the reply text. Streamed, as the
    claude-api reference advises ("Defaults": "default to streaming for any request that may involve long input, long
    output, or high `max_tokens` - it prevents hitting request timeouts"), and read whole with
    `get_final_message()`."""
    params = _anthropic_params(prompt, model, cache_until)
    _note_request(params, ("messages", "system"))
    if "system" in params:
        _last.reply["settings_sent"]["system"] = "the prompt's start, marked cache_control ephemeral"
    client = _sdk_client("anthropic", read_timeout)

    def send():
        with client.messages.stream(**params) as stream:
            return stream.get_final_message()
    body = _as_dict(_sdk_send("anthropic", send))
    _last.reply["http_status"] = 200
    text = "".join(b.get("text") or "" for b in body.get("content") or [] if isinstance(b, dict)
                   and b.get("type") == "text")
    return _finish_reply("anthropic", text, _anthropic_usage(body.get("usage")), body.get("stop_reason"), None,
                         body.get("model"))


def _ask_openai(prompt: str, model: str, read_timeout: int, cache_until: str | None = None) -> str:
    """One request to OpenAI's own API (Chat Completions, through the openai SDK); the reply text. The request is
    LiteLLM's (_chat_payload), the reply read as LiteLLM's (_read_chat_reply): the same API."""
    params = _chat_payload(prompt, model, cache_until, "openai")
    _note_request(params, ("messages",))
    client = _sdk_client("openai", read_timeout)
    body = _as_dict(_sdk_send("openai", lambda: client.chat.completions.create(**params)))
    _last.reply["http_status"] = 200
    return _read_chat_reply(body, "openai")


def _google_config(model: str) -> dict:
    """The `config` of a request to Google's Gemini API, as plain data: `max_output_tokens` (MAX_ANSWER_TOKENS),
    `thinking_config` {"thinking_level": the level in ThinkingLevel's spelling, e.g. "HIGH"} where a thinking level is
    sent (thinking_sent), `temperature` only where temperature_sent says so (not to Gemini 3 and later: TEMPERATURE)."""
    config = {"max_output_tokens": max_tokens_sent("google")}
    if temperature_sent(model, "google"):
        config["temperature"] = TEMPERATURE
    if thinking_sent(model, "google"):
        config["thinking_config"] = {"thinking_level": thinking_sent(model, "google").upper()}
    return config


def _google_usage(usage) -> dict:
    """Google's token counts (usage_metadata) in OpenAI's shape: prompt_tokens = prompt_token_count, of which
    cached_content_token_count were read from the cache (Gemini 4 Argon's caching is "Implicit only":
    https://aistudio.google.com/docs/models/gemini-4-argon); completion_tokens = candidates_token_count +
    thoughts_token_count, reasoning_tokens = thoughts_token_count, only when the reply reports it (Google's reference
    lists thoughts apart from the candidates: totalTokenCount is "prompt + tool-use prompt + thoughts + response
    candidates", https://aistudio.google.com/api-reference/generate-content, read 2026-11-14; that the prompt count
    includes the cached part, as OpenAI's prompt_tokens includes cached_tokens, is not verified). The reply's own counts
    are kept beside them (maker_usage)."""
    usage = usage if isinstance(usage, dict) else {}
    thoughts = usage.get("thoughts_token_count")
    out = {"prompt_tokens": usage.get("prompt_token_count") or 0,
           "completion_tokens": (usage.get("candidates_token_count") or 0) + (thoughts or 0),
           "cache_read_input_tokens": usage.get("cached_content_token_count") or 0, "maker_usage": usage}
    if thoughts is not None:
        out["completion_tokens_details"] = {"reasoning_tokens": thoughts}
    return out


def _ask_google(prompt: str, model: str, read_timeout: int, cache_until: str | None = None) -> str:
    """One request to Google's Gemini API (generate_content, through the google-genai SDK); the reply text
    (`response.text`: "If there are multiple candidates, returns the text from only the first one"). The finish reason
    is the first candidate's `finish_reason` (STOP, MAX_TOKENS, SAFETY, ...), or, when the prompt itself was blocked
    and no candidate came, `prompt_feedback.block_reason`; the served model is `model_version` ("The model version
    used to generate the response"; google-genai's types.py and the REST reference, read 2026-11-14)."""
    config = _google_config(model)
    _note_request({"model": model, **config}, ())
    client = _sdk_client("google", read_timeout)             # first: a missing key or package stops here, said plainly
    from google.genai import types
    typed = {**config, **({"thinking_config": types.ThinkingConfig(**config["thinking_config"])}
                          if "thinking_config" in config else {})}
    reply = _sdk_send("google", lambda: client.models.generate_content(
        model=model, contents=prompt, config=types.GenerateContentConfig(**typed)))
    _last.reply["http_status"] = 200
    body = _as_dict(reply)
    candidates = body.get("candidates") or []
    first = candidates[0] if candidates and isinstance(candidates[0], dict) else {}
    reason = first.get("finish_reason") or ((body.get("prompt_feedback") or {}).get("block_reason")
                                            if isinstance(body.get("prompt_feedback"), dict) else None)
    try:
        text = reply.text or ""
    except (AttributeError, ValueError):
        text = ""
    return _finish_reply("google", text, _google_usage(body.get("usage_metadata")), reason, None,
                         body.get("model_version"))


def _direct_models(service: str) -> list:
    """The model names a maker's own API lists for the key (free: listing is not a model call): Anthropic's and
    OpenAI's `client.models.list()` (Anthropic's auto-paginates: the claude-api reference, "Models API"; OpenAI's: its
    Models API, not read for this), each model's `id`; Google's `client.models.list()`
    (https://googleapis.github.io/python-genai/), each model's `name` without a leading "models/"."""
    client = _sdk_client(service, 60)
    try:
        models = list(client.models.list())
    except Exception as e:                                  # noqa: BLE001
        mine = _sdk_error(service, e, paid=False)
        if mine is e:
            raise
        raise (mine if isinstance(mine, ApiError) else ApiError(str(mine))) from e
    names = [str(getattr(m, "name", "") or "").removeprefix("models/") if service == "google"
             else str(getattr(m, "id", "") or "") for m in models]
    names = [n for n in names if n]
    if not names:
        raise ValueError(f"{SERVICES[service]}'s model list is empty or came in a shape this code doesn't read")
    return sorted(set(names))
