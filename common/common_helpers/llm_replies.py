"""
common/common_helpers/llm_replies.py -- what a reply is, and what each request records of itself.

A part of common/common_helpers/llm.py: classify_reply (complete, cut off, refused, empty, malformed: the one place
that decides it), the JSON a reply holds (find_json), the judgment every service client ends with
(_raise_unless_complete), and what the clients record in llm._last, the request's record: its settings
(_note_request), its HTTP status (_http_reply), its token counts (_count_tokens, into llm.REQUESTS), and, on an
error, what the service sent (_with_reply, _with_call). Import these names from common.llm, never from this file.
"""

import json
import re
import time

from common import llm
from common.audit import log
from common.llm import ERROR_BODY_CHARS, REQUESTS, SERVED, _last, _requests_lock, max_tokens_sent
from common.llm_errors import ApiError, CutOff, Refused


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
                 if (service or llm.SERVICE) == "asksage" and not reasons else
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
        error = CutOff((f"the answer was cut off at the longest length allowed ({llm.MAX_ANSWER_TOKENS:,} tokens, "
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


def _http_reply(resp) -> None:
    """Note a reply's HTTP status, and its body when it is an error, in _last.reply."""
    _last.reply["http_status"] = resp.status_code
    if resp.status_code >= 400:
        _last.reply["error_body"] = str(resp.text or "")[:ERROR_BODY_CHARS]


def _count_tokens(usage: dict) -> None:
    """Add a reply's token counts to REQUESTS, for the report's Model calls, and to llm.TOKENS_BY_PRICE, by the price
    they are billed at (llm_costs.count_priced). Cache writes: Anthropic's cache_creation_input_tokens, or OpenAI's
    prompt_tokens_details.cache_write_tokens (openai's CompletionUsage: "The unadjusted number of prompt tokens written
    to cache"; OpenAI's prompt caching guide: "`cached_tokens` counts billed reads and excludes tokens charged as
    writes", https://developers.openai.com/api/docs/guides/prompt-caching, read 2026-11-18), so a write is counted
    once, not also as input."""
    if not isinstance(usage, dict):
        return
    details = usage.get("prompt_tokens_details") if isinstance(usage.get("prompt_tokens_details"), dict) else {}
    read = usage.get("cache_read_input_tokens") or details.get("cached_tokens") or 0
    write = usage.get("cache_creation_input_tokens") or details.get("cache_write_tokens") or 0
    output, thinking = usage.get("completion_tokens") or 0, reasoning_tokens(usage)
    with _requests_lock:
        REQUESTS["input_tokens"] += (usage.get("prompt_tokens") or 0) - read - write
        REQUESTS["cache_read_tokens"] += read
        REQUESTS["cache_write_tokens"] += write
        REQUESTS["output_tokens"] += output
        REQUESTS["reasoning_tokens"] += thinking
    llm.count_priced(usage, read, write, output, thinking)


def _note_request(params: dict, words: tuple) -> None:
    """Start this request's _last.reply: every setting sent but the words of the prompt (the keys in words), and the
    request's size."""
    _last.reply = {"settings_sent": {k: v for k, v in params.items() if k not in words},
                   "request_bytes": len(json.dumps(params, default=str).encode("utf-8"))}


def _finish_reply(service: str, text, usage, reason, native, served) -> str:
    """What every service client but Ask Sage's does with a reply: count its tokens (usage in OpenAI's shape, which
    LiteLLM uses and the makers' own replies are put into: _count_tokens), note the served model (SERVED), the finish
    reasons and the usage in _last.reply, and judge it (_raise_unless_complete)."""
    usage = usage if isinstance(usage, dict) else {}
    _count_tokens(usage)
    _last.reply["usage"] = usage
    if served:
        SERVED.add(str(served))
        _last.reply["served_as"] = str(served)
    _last.reply["finish_reason"], _last.reply["native_finish_reason"] = reason, native
    return _raise_unless_complete(text, {"usage": usage}, service, reason, native)


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
