"""
common/common_helpers/llm_asksage.py -- the Ask Sage client: one request, the reply text.

A part of common/common_helpers/llm.py: the log-in token (_asksage_token), the model list (_asksage_models), and one
query (_ask_asksage). Import these names from common.llm, never from this file.
"""

import json
import os
import sys

import requests

from common import llm
from common.llm import ERROR_BODY_CHARS, TEMPERATURE, _last, temperature_sent
from common.llm_errors import ApiError, RETRY_STATUSES, RetryLater, _retry_after, stop_if_budget_gone
from common.llm_replies import _http_reply, _raise_unless_complete


USER_BASE = "https://api.asksage.ai.nasa.gov/user"


SERVER_BASE = "https://api.asksage.ai.nasa.gov/server"


_token_cache = {}


def _asksage_token():
    if "token" not in _token_cache:
        llm.load_dotenv()
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
    resp = requests.post(f"{SERVER_BASE}/get-models", headers={"x-access-tokens": llm._asksage_token()},
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
                         headers={"x-access-tokens": llm._asksage_token()},
                         json=payload,
                         timeout=(5, read_timeout))
    _http_reply(resp)
    stop_if_budget_gone("asksage", resp.status_code, resp.text)
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
        stop_if_budget_gone("asksage", inner if isinstance(inner, int) else 400, f"{code}: {body.get('message')}")
        if inner in (429, 500, 502, 503, 504):
            raise RuntimeError(detail)      # worth retrying
        raise ApiError(detail)              # will not fix itself
    # A numeric top-level status of 400 or more is also a refusal.
    status = body.get("status")
    if isinstance(status, (int, str)) and str(status).isdigit() \
            and int(status) >= 400:
        stop_if_budget_gone("asksage", int(status), body.get("message"))
        raise RuntimeError(f"API status {status}: "
                           f"{str(body.get('message'))[:200]}")
    # .get("message") can be absent OR present-and-null; either way
    # callers must never receive None and call .strip() on it. Ask Sage sends no finish reason and takes no answer
    # limit, so the answer is judged by its content alone (classify_reply): one stopping inside an unfinished JSON
    # object was cut off at the model's own limit; prose declining the task is a refusal. Before that: an answer that
    # is Ask Sage saying the monthly token limit is reached stops the run (budget_answer), never a refusal.
    message = (body or {}).get("message") or ""
    stop_if_budget_gone("asksage", 200, message)
    return _raise_unless_complete(message, body or {}, "asksage")
