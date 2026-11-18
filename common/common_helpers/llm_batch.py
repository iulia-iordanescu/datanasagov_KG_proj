"""
common/common_helpers/llm_batch.py -- batch processing: a stage's model calls sent as batch jobs to a maker's batch API.

A part of common/common_helpers/llm.py, used when the setting `batch` is true (llm.BATCH): ask_batch sends the prompts
of a stage that asks many independent prompts (common/common_helpers/extraction.py, ask_model) as one batch job (or
several, past a maker's limits: llm.BATCH_LIMITS) to the maker's own batch API, waits for the job to end, and hands
each answer to the stage as a single request's answer is handed to it. Only through a maker's own API
(llm.DIRECT_SERVICES): Anthropic's Message Batches API, OpenAI's Batch API and Google's Gemini Batch API, each at 50%
of the price of single requests (the makers' pages cited at llm.BATCH). Ask Sage and LiteLLM have none here
(batch_refusal). Import these names from common.llm, never from this file.

What makes a batch answer the same as a single request's:

    the request    built by the code that builds a single request (llm_makers.py: _anthropic_params; llm_litellm.py:
                   _chat_payload, OpenAI's; llm_makers.py: _google_config and _google_typed_config): the whole prompt
                   in each request, the same model, answer limit and thinking level (with Anthropic's `thinking` field
                   where one is sent: llm.thinking_field), no temperature where none is sent.
                   Two changes, which change no word the model gets: Anthropic's cached prompt start is marked for
                   the 1-hour cache (ANTHROPIC_CACHE_TTL); the answer limit is lowered where a maker's batch API takes
                   less (llm.BATCH_MAX_ANSWER_TOKENS: Google's, 32,768), and an answer cut off at that lower limit is
                   asked again in the same run as a single request at the run's limit, at the full price (_hand_over)
    the answer     judged by the code that judges a single request's (_read_anthropic_reply, _read_chat_reply,
                   _read_google_reply, then llm.call_llm_json): the finish reason (a cut-off, a refusal), the token
                   counts (llm.REQUESTS), the served model (llm.SERVED), the JSON object and its shape
    the cache      each answer stored under the cache key of the same prompt asked as a single request
                   (common/common_helpers/cache.py)

What a batch run does that a run of single requests doesn't:

    job ids        every job is written to <the step's output folder>/cache/<stage>.batch_jobs.json the moment it is
                   created (batch_state_file). A run stopped while it waits (Ctrl+C, a closed window) leaves its jobs
                   running at the maker; the next run whose prompts they hold (the same service, model, thinking
                   level and repeat, at any answer limit) collects them instead of paying again, and sends only the
                   prompts no job holds. A cut-off in a job sent at another answer limit is kept with that limit
                   (common/common_helpers/cache.py, Cache.put_cut_off), so a run at a new limit asks it again
    failures       a request the maker reports as errored, expired or canceled is a failed call, as a single request's
                   error is: recorded in the run's failed-call record, its record left out, asked again on the next run
                   (in a new job). Anthropic bills none of these ("You aren't billed for these requests"); OpenAI bills
                   "tokens consumed from any completed requests" of an expired job; Google's batch page says nothing
                   on it. A malformed answer is asked once more as a single request, as llm.call_llm_json does with
                   any answer
    single requests  a run with the setting batch false stops before any model call when an uncollected job holds
                   a prompt it would ask, at any answer limit (jobs_holding, called by
                   common/common_helpers/extraction.py, ask_model): asking it again as a single request would pay
                   for it twice, so the message says to run with --batch true, which collects the job
    queue caps     OpenAI and Google cap the input tokens waiting in their batch queue per model, Google and
                   Anthropic the requests (llm.BATCH_QUEUE_TOKENS, llm.BATCH_QUEUE_REQUESTS): a run's requests are
                   cut into jobs within them, and each job is sent once the jobs before it (this run's and other
                   runs' uncollected ones) leave room (_Queue); a job the maker refuses for its queue is sent again
                   when there is room. Jobs not sent yet are kept nowhere: the next run sends their prompts
    early stop     when the share of failed requests in the stage's jobs is at least llm.EARLY_STOP_FAILURES of
                   llm.EARLY_STOP_WINDOW (and at least EARLY_STOP_FAILURES of them failed), every answer received is
                   stored, nothing is asked again, and the step stops with a message saying what failed
"""

import datetime as dt
import json
import sys
from pathlib import Path

from common import llm
from common.audit import log
from common.files import locked, read_json, write_json
from common.llm import (
    BATCH_JOBS, BATCH_LIMITS, DIRECT_SERVICES, EARLY_STOP_FAILURES, EARLY_STOP_WINDOW, REQUESTS, RUN_WARNINGS, SERVICES,
    _last, _requests_lock, batch_tokens_sent, cache_identity, max_tokens_sent)
from common.llm_errors import ApiError, NoAnswerInTime, RetryLater
from common.llm_litellm import _chat_payload, _read_chat_reply
from common.llm_makers import (
    _anthropic_params, _as_dict, _google_config, _google_typed_config, _read_anthropic_reply, _read_google_reply,
    _sdk_client, _sdk_send)
from common.llm_paid import EarlyStop, Interrupted, advice, run_parallel
from common.llm_replies import find_json


#: Each maker's batch page (read 2026-11-17), for messages and the report.
BATCH_DOCS = {"anthropic": "https://platform.claude.com/docs/en/build-with-claude/batch-processing",
              "openai": "https://developers.openai.com/api/docs/guides/batch",
              "google": "https://aistudio.google.com/docs/batch-api"}


#: Each maker's batch API by its own name, for messages and the report.
BATCH_API = {"anthropic": "Anthropic's Message Batches API", "openai": "OpenAI's Batch API",
             "google": "Google's Gemini Batch API"}


#: How long a maker keeps a job's results after the job is made (the makers' batch pages): Anthropic 29 days, OpenAI
#: the time this code asks for (OPENAI_OUTPUT_SECONDS), Google not stated. A message about a stopped run says it.
RESULTS_KEPT = {"anthropic": "29 days", "openai": "7 days", "google": "a time its batch page doesn't state"}


#: Anthropic's cached prompt start is marked for the 1-hour cache in a batch request, not the 5-minute one a single
#: request uses. Its batch page advises it: "Because batches can take longer than 5 minutes to process, consider using
#: the 1-hour cache duration with prompt caching for better cache hit rates when processing batches with shared
#: context". The prices decide it too: a 1-hour cache write costs 2 times the base input price, a 5-minute one 1.25
#: times, and a cache read 0.05 times on Claude Opus 5.5 (0.1 times on most other models); these multipliers "stack
#: with other pricing modifiers such as the Batch API discount" (https://platform.claude.com/docs/en/build-with-claude/
#: prompt-caching, read 2026-11-17). A batch's requests run in an order and at times the maker chooses, so with the
#: 5-minute cache any two that run more than 5 minutes apart write the start again; one such second write (1.25)
#: already costs more than the 1-hour write's surplus (2 - 1.25 = 0.75). The answer is the same either way.
ANTHROPIC_CACHE_TTL = "1h"


#: How long OpenAI keeps a job's output and error files, in seconds, from the file's creation: 7 days. OpenAI's
#: default is 30 days, and `output_expires_after` takes "1 hour to 30 days" (its batch page). The files hold the
#: model's answers, which this run stores in its cache as soon as the job ends; they are needed after that only when
#: the run stopped before collecting them. A job ends within its 24-hour window, so 7 days leaves a person who
#: stopped a run (or whose computer was off over a weekend) several days to run the step again and collect the
#: answers, without the answers staying at OpenAI longer than that.
OPENAI_OUTPUT_SECONDS = 7 * 24 * 3600


#: How long a request to a batch API itself (create, state, results) may take, in seconds.
BATCH_API_TIMEOUT = 600


#: A batch job's creation is tried this many times when the service refuses it with a rate limit or a server error
#: (RetryLater: e.g. Google's 503 "high demand"), BATCH_CREATE_WAIT seconds apart. Never after a timeout, a lost
#: connection (NoAnswerInTime, RuntimeError) or an error of no known kind (e.g. httpx.ReadError while the answer was
#: read): the service may have made the job before the answer was lost, and a
#: second job would pay for the same prompts twice, so the step stops instead, as call_llm stops asking a single
#: request after a timeout (common/common_helpers/llm_calls.py).
BATCH_CREATE_ATTEMPTS = 4


BATCH_CREATE_WAIT = 60


def batch_refusal(service: str) -> str | None:
    """Why the setting batch can't be used through this service, in a message's words; None when it can."""
    if service in DIRECT_SERVICES:
        return None
    return (f"The setting batch is true, but the setting service is {service} ({SERVICES.get(service, service)}), "
            f"which the pipeline sends no batch jobs through: batch processing goes only through a maker's own API "
            f"(--service anthropic, openai or google), so the step can't run. Give --batch false to send one request "
            f"per prompt through {SERVICES.get(service, service)}, or a maker's own API with --service, then run the "
            f"step again.")


def batch_state_file(cache_dir: Path, stage: str) -> Path:
    """Where a stage's batch jobs are kept: <the step's output folder>/cache/<stage>.batch_jobs.json."""
    return Path(cache_dir) / f"{stage}.batch_jobs.json"


def batch_note() -> str | None:
    """The report's words on this run's batch jobs, or None when the run sent none and collected none."""
    if not llm.BATCH:
        return None
    service = llm.SERVICE
    if not BATCH_JOBS:
        return (f"Batch: the setting `batch` was true, but no prompt needed a model call, so no batch job was sent "
                f"to {BATCH_API.get(service, service)}.")
    jobs = "; ".join(f"`{j['id']}` ({j['how']}, {j['requests']:,} request(s), ended {j.get('state') or '?'}: "
                     f"{j.get('answered', 0):,} answered, {j.get('failed', 0):,} failed)" for j in BATCH_JOBS)
    return (f"Batch: the calls of this run went through {BATCH_API.get(service, service)} (setting `batch` "
            f"true; {BATCH_DOCS.get(service, '')}), billed at half the price of single requests, as batch job(s) "
            f"{jobs}. A job \"resumed\" was submitted by an earlier run and collected by this one; its requests were "
            f"counted as sent by that run. The one-line test call, and a second ask of an answer that wasn't a JSON "
            f"object of the shape asked for, went as single requests, at the full price.{_asked_again_note()}")


def _asked_again_note() -> str:
    """The report's words on the answers cut off at the batch API's lower answer limit and asked again as single
    requests (_ask_again_singly), with their token counts; "" when the service's batch requests carry the run's own
    limit."""
    short, full = batch_tokens_sent(), max_tokens_sent()
    if short is None or full is None or short >= full:
        return ""
    service = llm.SERVICE
    again = [a for j in BATCH_JOBS for a in j.get("asked_again_singly", [])]
    head = (f" {BATCH_API.get(service, service)} takes an answer limit of at most {short:,} tokens "
            f"(BATCH_MAX_ANSWER_TOKENS in common/common_helpers/llm.py), so its batch requests were sent {short:,}, "
            f"not this run's {full:,}; an answer cut off at {short:,} was asked again in this run as a single request "
            f"at {full:,}, billed at the full price, and that answer is the one kept.")
    if not again:
        return head + f" No answer of this run's batch jobs was cut off at {short:,} tokens, so none was asked again."

    def count(n):
        return "not reported" if n is None else f"{n:,}"
    each = "; ".join(f"{', '.join(a['records'])}: cut off at {count(a['cut_tokens'])} tokens received "
                     f"({count(a['cut_thinking_tokens'])} thinking), asked again: {a['outcome']}, "
                     f"{count(a['tokens'])} tokens received ({count(a['thinking_tokens'])} thinking)" for a in again)
    return head + (f" {len(again):,} answer(s) were cut off at {short:,} tokens and asked again as single requests, "
                   f"at the full price: {each}.")


# ------------------------------ the state file ----------------------------------

def _load(path: Path) -> dict:
    if not path.exists():
        return {"jobs": []}
    try:
        state = read_json(path)
    except (ValueError, OSError) as e:
        sys.exit(f"{path} can't be read ({e}), and it holds the ids of batch jobs this step sent, so the step "
                 f"stops rather than pay for those prompts again. Repair the file (each job is "
                 f"{{\"id\", \"service\", \"keys\", ...}}), or delete it if every job in it has been collected, then "
                 f"run the step again.")
    return state if isinstance(state, dict) and isinstance(state.get("jobs"), list) else {"jobs": []}


def _save_job(path: Path, job: dict) -> None:
    """Add or update one job in the state file, under its lock, keeping what another process wrote."""
    with locked(path):
        state = _load(path)
        jobs = [j for j in state["jobs"] if j.get("id") != job["id"]] + [job]
        write_json(path, {"jobs": jobs})


def _now() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


# ------------------------------ each maker's batch API -------------------------

def _request(service: str, custom_id: str, prompt: str, model: str, cache_until: str | None) -> tuple:
    """(one request of the batch, in the maker's shape; the settings it carries but the prompt's words, for the
    failed-call record). Its answer limit is batch_tokens_sent: a single request's, lowered where the maker's batch
    API takes less (llm.BATCH_MAX_ANSWER_TOKENS)."""
    limit_name, limit = DIRECT_SERVICES[service]["answer_limit"], batch_tokens_sent(service)
    if service == "anthropic":
        params = {**_anthropic_params(prompt, model, cache_until), limit_name: limit}
        if "system" in params:
            params["system"][0]["cache_control"] = {"type": "ephemeral", "ttl": ANTHROPIC_CACHE_TTL}
        sent = {k: v for k, v in params.items() if k not in ("messages", "system")}
        if "system" in params:
            sent["system"] = f"the prompt's start, marked cache_control ephemeral, ttl {ANTHROPIC_CACHE_TTL}"
        return {"custom_id": custom_id, "params": params}, sent
    if service == "openai":
        body = {**_chat_payload(prompt, model, cache_until, "openai"), limit_name: limit}
        return ({"custom_id": custom_id, "method": "POST", "url": "/v1/chat/completions", "body": body},
                {k: v for k, v in body.items() if k != "messages"})
    config = {**_google_config(model), limit_name: limit}
    return {"contents": prompt, "metadata": {"key": custom_id}, "config": config}, {"model": model, **config}


def _chunks(service: str, entries: list, tokens: list | None = None, most_tokens: int | None = None) -> list:
    """The requests cut into jobs within the maker's limits (BATCH_LIMITS: requests and bytes per job, and no more
    requests than llm.BATCH_QUEUE_REQUESTS lets wait in the queue) and, when
    most_tokens is given (llm.BATCH_QUEUE_TOKENS), within that many estimated input tokens per job (tokens: each
    entry's estimate, estimated_tokens)."""
    most, most_bytes = BATCH_LIMITS[service]
    most = min(most, llm.BATCH_QUEUE_REQUESTS.get(service) or most)     # a job never more than the queue takes
    chunks, size, held = [[]], 0, 0
    for i, entry in enumerate(entries):
        n = len(json.dumps(entry, ensure_ascii=False).encode("utf-8")) + 1
        t = tokens[i] if tokens else 0
        if chunks[-1] and (len(chunks[-1]) >= most or size + n > most_bytes
                           or (most_tokens is not None and held + t > most_tokens)):
            chunks.append([])
            size = held = 0
        chunks[-1].append(entry)
        size += n
        held += t
    return [c for c in chunks if c]


#: Characters per token assumed when a prompt's input tokens are estimated for OpenAI's queue cap
#: (llm.BATCH_QUEUE_TOKENS), and the tokens added for each request's framing (its role markers and the like). OpenAI's
#: rule of thumb for English text is about 4 characters per token (its help article "What are tokens and how to count
#: them?"); a prompt of this pipeline also holds identifiers, schema lists and JSON, which take more tokens per
#: character, so 3 is assumed: about a third more tokens than English prose has, which errs on the side of sending
#: smaller jobs. The estimate decides only how the requests are cut into jobs, never what a request holds.
CHARS_PER_TOKEN = 3
TOKENS_PER_REQUEST = 20


def estimated_tokens(prompt: str) -> int:
    """A conservative estimate of a prompt's input tokens (CHARS_PER_TOKEN, TOKENS_PER_REQUEST), rounded up."""
    return -(-len(prompt) // CHARS_PER_TOKEN) + TOKENS_PER_REQUEST


def queue_cap(service: str, model: str) -> int | None:
    """The most estimated input tokens this run lets wait in the maker's batch queue for the model
    (llm.BATCH_QUEUE_TOKENS), or None when there is no cap."""
    return llm.BATCH_QUEUE_TOKENS.get(service, {}).get(model)


def queue_requests(service: str) -> int | None:
    """The most requests this run lets wait or run in the maker's batch queue, over every model
    (llm.BATCH_QUEUE_REQUESTS), or None when there is no cap."""
    return llm.BATCH_QUEUE_REQUESTS.get(service)


#: Words of a maker's refusal that its batch queue is full, matched without case: OpenAI's error code
#: "token_limit_exceeded" and its words "Enqueued token limit" (not stated on its rate limits page, read 2026-11-17,
#: which names no error for the batch queue cap; OpenAI's batch jobs report it in their `errors`), and Google's
#: "RESOURCE_EXHAUSTED", the status of its HTTP 429 (https://aistudio.google.com/docs/rate-limits names it for the
#: spend-based limits and no error for the batch limits). A job refused so is never processed (nothing is billed),
#: so its requests are sent again in a new job when the queue has room (_Queue), at most QUEUE_FULL_WAITS times in a
#: row while no job of this run is running.
QUEUE_FULL_WORDS = ("token_limit_exceeded", "enqueued token limit", "resource_exhausted")
QUEUE_FULL_WAITS = 60


def _queue_full(said) -> bool:
    """Whether an error or a failed job's words say the maker's batch queue is full (QUEUE_FULL_WORDS)."""
    text = str(said or "").lower()
    return any(w in text for w in QUEUE_FULL_WORDS)


class QueueFull(Exception):
    """The maker refused a batch job because its batch queue is full (_queue_full): no job was made."""


class _Queue:
    """The jobs of a run not sent yet, each sent when the maker's batch queue has room for it: the jobs still waiting
    or running (this run's, and the jobs other runs left uncollected in the state file, until a check says they
    ended) plus the job itself must stay within the caps: llm.BATCH_QUEUE_TOKENS (estimated input tokens, of jobs of
    the same model) and llm.BATCH_QUEUE_REQUESTS (requests, of jobs of any model of the service). Without a cap, every
    job is sent at once. Nothing not yet sent is kept anywhere, on purpose: a run stopped before sending a job leaves
    its prompts unanswered in the cache and held by no kept job, so the next run sends them, once; a kept list of
    unsent jobs could only go stale against the cache."""

    def __init__(self, service: str, model: str, chunks: list, send, others: list, path: Path):
        self.service, self.model, self.chunks, self.send, self.path = service, model, chunks, send, path
        self.tokens_cap, self.requests_cap = queue_cap(service, model), queue_requests(service)
        self.others = [j for j in others if j.get("service") == service]     # chunks: [{"entries", "keys", "tokens"}]
        self.ended_others, self.of_job, self.said, self.refusals = set(), {}, None, 0

    def left(self) -> bool:
        return bool(self.chunks)

    def requests_left(self) -> int:
        return sum(len(c["keys"]) for c in self.chunks)

    def _queued(self, running: list) -> tuple:
        """(estimated input tokens of the model, requests of any model) waiting or running in the maker's queue: this
        run's jobs not ended (running) and other runs' open jobs, each with the estimate kept with it (0 for a job
        kept before 2026-11-17, which kept none). An other run's job is asked about (free) until it has ended; one
        whose state can't be read is counted as still queued."""
        for j in self.others:
            if j["id"] in self.ended_others:
                continue
            try:
                if _poll(self.service, j["id"])["ended"]:
                    self.ended_others.add(j["id"])
            except Exception as e:                          # noqa: BLE001  unknown: counted as still queued
                log.debug(f"checking batch job {j['id']} of another run failed ({e}); counted as still queued")
        live = list(running) + [j for j in self.others if j["id"] not in self.ended_others]
        tokens = sum(j.get("input_tokens") or 0 for j in live if j.get("model") == self.model)
        requests = sum(j.get("requests") or len(j.get("keys", [])) for j in live)
        return tokens, requests

    def _full(self, chunk: dict, running: list) -> str | None:
        """Why the chunk can't be sent now (the queue would pass a cap), or None."""
        if self.tokens_cap is None and self.requests_cap is None:
            return None
        tokens, requests = self._queued(running)
        if self.tokens_cap is not None and tokens and tokens + chunk["tokens"] > self.tokens_cap:
            return (f"about {tokens:,} input tokens of {self.model} are in {SERVICES[self.service]}'s batch queue, and "
                    f"the cap is {self.tokens_cap:,} (llm.BATCH_QUEUE_TOKENS)")
        if self.requests_cap is not None and requests and requests + len(chunk["keys"]) > self.requests_cap:
            return (f"{requests:,} requests are in {SERVICES[self.service]}'s batch queue, and the cap is "
                    f"{self.requests_cap:,} (llm.BATCH_QUEUE_REQUESTS)")
        return None

    def submit(self, running: list) -> list:
        """Send the jobs that fit now, in order; the jobs sent."""
        sent = []
        while self.chunks:
            chunk = self.chunks[0]
            why = self._full(chunk, running + sent)
            if why:
                self._say(f"  the next batch job ({len(chunk['keys']):,} request(s), about {chunk['tokens']:,} input "
                          f"tokens) waits: {why}; it is sent when an earlier job ends")
                break
            try:
                job = self.send(chunk)
            except QueueFull as e:
                if not running and not sent:
                    self.refusals += 1
                    if self.refusals >= QUEUE_FULL_WAITS:
                        sys.exit(f"{SERVICES[self.service]} refused a batch job {self.refusals} times in a row, "
                                 f"{llm.BATCH_POLL_SECONDS} s apart, saying its batch queue is full ({e}), while no "
                                 f"batch job of this run was running, so jobs of other work on the account fill the "
                                 f"queue, or the refusal means another limit. No job was made for those requests, "
                                 f"and none was paid for. The jobs already sent keep running, their ids kept in "
                                 f"{_repo(self.path)}. Wait for the account's other batch jobs to end (or check its "
                                 f"limits: {BATCH_DOCS[self.service]}), then run the same command again: it collects "
                                 f"the jobs kept and sends the rest.")
                self._say(f"  {SERVICES[self.service]} refused the next batch job for now, its batch queue being full "
                          f"({e}); no job was made, and it is sent again once an earlier job ends, or in "
                          f"{llm.BATCH_POLL_SECONDS} s. Nothing to do; Ctrl+C is safe: the next run sends the jobs "
                          f"not sent yet")
                break
            self.refusals = 0
            self.chunks.pop(0)
            self.of_job[job["id"]] = chunk
            sent.append(job)
        return sent

    def rejected(self, job: dict, status: dict) -> bool:
        """Whether an ended job was refused for the queue cap after it was made (OpenAI: status failed, error
        token_limit_exceeded): then it is marked given up in the state file, its requests no longer counted as sent,
        and its chunk is put first in line again."""
        if job["id"] not in self.of_job or "fail" not in status["state"].lower() or not _queue_full(status.get("error")):
            return False
        job.update(collected=_now(), state=f"refused for the batch queue cap: {status.get('error')}")
        _save_job(self.path, job)
        with _requests_lock:
            REQUESTS["sent"] -= len(job.get("keys", []))
        for j in BATCH_JOBS:
            if j["id"] == job["id"]:
                j.update(how="refused for the queue cap, its requests sent again", state="failed", answered=0,
                         failed=0)
        self.chunks.insert(0, self.of_job.pop(job["id"]))
        self._say(f"  {SERVICES[self.service]} refused batch job {job['id']} after making it, its batch queue being "
                  f"full ({status.get('error')}); no request of it was processed, and its "
                  f"{len(job.get('keys', [])):,} request(s) are sent again in a new job once an earlier job ends")
        return True

    def _say(self, words: str) -> None:
        if words != self.said:
            self.said = words
            log.info(words)


def _create(service: str, model: str, entries: list, label: str) -> str:
    """Send one batch job; its id. Anthropic: messages.batches.create(requests=...); OpenAI: the requests uploaded as a
    JSONL file (files.create, purpose "batch"), then batches.create on /v1/chat/completions with the 24-hour window
    (the only one) and OPENAI_OUTPUT_SECONDS; Google: batches.create with the requests inlined, each its config typed
    as a single request's."""
    client = _sdk_client(service, BATCH_API_TIMEOUT)
    if service == "anthropic":
        return str(_sdk_send(service, lambda: client.messages.batches.create(requests=entries)).id)
    if service == "openai":
        data = ("\n".join(json.dumps(e, ensure_ascii=False) for e in entries) + "\n").encode("utf-8")
        upload = _sdk_send(service, lambda: client.files.create(file=(f"{label}.jsonl", data), purpose="batch"))
        job = _sdk_send(service, lambda: client.batches.create(
            input_file_id=upload.id, endpoint="/v1/chat/completions", completion_window="24h",
            output_expires_after={"anchor": "created_at", "seconds": OPENAI_OUTPUT_SECONDS}))
        return str(job.id)
    from google.genai import types
    src = [types.InlinedRequest(contents=e["contents"], metadata=e["metadata"],
                                config=_google_typed_config(e["config"])) for e in entries]
    job = _sdk_send(service, lambda: client.batches.create(model=model, src=src, config={"display_name": label}))
    return str(job.name)


#: The job states after which nothing more happens, by service.
_ENDED = {"openai": {"completed", "failed", "expired", "cancelled"},
          "google": {"JOB_STATE_SUCCEEDED", "JOB_STATE_FAILED", "JOB_STATE_CANCELLED", "JOB_STATE_EXPIRED",
                     "JOB_STATE_PARTIALLY_SUCCEEDED"}}


def _state_name(state) -> str:
    return str(getattr(state, "value", None) or getattr(state, "name", None) or state or "")


def _poll(service: str, job_id: str) -> dict:
    """{"ended": bool, "state": the maker's word, "counts": in words, or ""}: the job's state, asked once (free)."""
    client = _sdk_client(service, BATCH_API_TIMEOUT)
    if service == "anthropic":
        job = _as_dict(_sdk_send(service, lambda: client.messages.batches.retrieve(job_id)))
        c = job.get("request_counts") or {}
        failed = sum(c.get(k) or 0 for k in ("errored", "canceled", "expired"))
        return {"ended": job.get("processing_status") == "ended", "state": str(job.get("processing_status")),
                "counts": f"{c.get('succeeded') or 0:,} answered, {failed:,} failed, {c.get('processing') or 0:,} "
                          f"still being processed"}
    if service == "openai":
        job = _as_dict(_sdk_send(service, lambda: client.batches.retrieve(job_id)))
        c = job.get("request_counts") or {}
        errors = [e for e in ((job.get("errors") or {}).get("data") or []) if isinstance(e, dict)]
        return {"ended": job.get("status") in _ENDED["openai"], "state": str(job.get("status")),
                "counts": f"{c.get('completed') or 0:,} of {c.get('total') or 0:,} answered, {c.get('failed') or 0:,} "
                          f"failed" if c else "",
                "error": "; ".join(f"{e.get('code') or ''}: {e.get('message') or ''}".strip(": ") for e in errors)}
    job = _sdk_send(service, lambda: client.batches.get(name=job_id))
    state = _state_name(getattr(job, "state", None))
    stats = _as_dict(getattr(job, "completion_stats", None)) if getattr(job, "completion_stats", None) else {}
    error = getattr(job, "error", None)
    return {"ended": state in _ENDED["google"], "state": state,
            "error": str(getattr(error, "message", None) or error or ""),
            "counts": (f"{stats.get('successful_count') or 0:,} answered, {stats.get('failed_count') or 0:,} failed"
                       if stats else "")}


def _job_error(service: str, job_id: str, said: str) -> ApiError:
    return ApiError(f"batch job {job_id} at {SERVICES[service]} ended without this request's answer: {said}; it is "
                    f"asked again on the next run")


def _google_keys(responses: list, sent_keys: list, job_id: str) -> list:
    """The cache key of each of a Google job's inlined responses: the metadata key the request carried, which the
    response carries back (google-genai's InlinedResponse.metadata). When no response carries a key but the job
    returned as many responses as it was sent requests, the responses are matched to the requests by order: Google's
    API reference says of InlinedResponses, "The responses will be in the same order as the input requests"
    (https://aistudio.google.com/api-reference/batch-api, read 2026-11-17). When some carry a key and some don't, or
    the numbers differ, a response without a key can't be placed: "None", so its request counts as unanswered (asked
    again by the next run)."""
    keys = [(getattr(item, "metadata", None) or {}).get("key") for item in responses]
    if any(keys) or len(responses) != len(sent_keys) or not responses:
        return [str(k) for k in keys]
    log.info(f"  Google's batch job {job_id} returned its {len(responses):,} answers without the key each request "
             f"carried, so they are matched to the requests by order, the order Google's API reference states for "
             f"inlined responses")
    return list(sent_keys)


def _results(service: str, job_id: str, state: str, sent_keys: list = ()) -> dict:
    """{custom_id: ("answer", the maker's reply) | ("error", ApiError)}: what the ended job holds, by request. Results
    may come in any order (Anthropic, OpenAI: matched by custom_id; Google: by the metadata key each request carried,
    or by order when none carries it: _google_keys). sent_keys: the job's requests' keys, in the order sent."""
    client = _sdk_client(service, BATCH_API_TIMEOUT)
    out = {}
    if service == "anthropic":
        for item in _sdk_send(service, lambda: list(client.messages.batches.results(job_id))):
            d = _as_dict(item)
            result = d.get("result") or {}
            kind = result.get("type")
            if kind == "succeeded":
                out[str(d.get("custom_id"))] = ("answer", result.get("message") or {})
                continue
            error = (result.get("error") or {}).get("error") or result.get("error") or {}
            said = (f"errored ({error.get('type')}: {error.get('message')})" if kind == "errored" else
                    "expired (the job reached its 24-hour limit before this request was sent to the model)"
                    if kind == "expired" else f"{kind}")
            out[str(d.get("custom_id"))] = ("error", _job_error(service, job_id, said))
        return out
    if service == "openai":
        job = _as_dict(_sdk_send(service, lambda: client.batches.retrieve(job_id)))
        for field in ("output_file_id", "error_file_id"):
            file_id = job.get(field)
            if not file_id:
                continue
            text = _sdk_send(service, lambda f=file_id: client.files.content(f).text)
            for line in str(text).splitlines():
                if not line.strip():
                    continue
                d = json.loads(line)
                response = d.get("response") or {}
                if response.get("status_code") == 200 and not d.get("error"):
                    out[str(d.get("custom_id"))] = ("answer", response.get("body") or {})
                    continue
                error = d.get("error") or ((response.get("body") or {}).get("error")) or {}
                said = (f"{error.get('code') or ''}: {error.get('message') or ''}".strip(": ")
                        + (f" (HTTP {response.get('status_code')})" if response.get("status_code") else ""))
                out[str(d.get("custom_id"))] = ("error", _job_error(service, job_id, said or "no answer"))
        if not out and job.get("errors"):
            said = "; ".join(str(e.get("message")) for e in (job["errors"].get("data") or []) if isinstance(e, dict))
            out["*"] = ("error", _job_error(service, job_id, f"the job {state}: {said}"))
        return out
    job = _sdk_send(service, lambda: client.batches.get(name=job_id))
    dest = getattr(job, "dest", None)
    responses = getattr(dest, "inlined_responses", None) or []
    keys = _google_keys(responses, sent_keys, job_id)
    for item, key in zip(responses, keys):
        error = getattr(item, "error", None)
        if getattr(item, "response", None) is not None and error is None:
            out[key] = ("answer", item.response)
        else:
            said = f"{getattr(error, 'code', '')}: {getattr(error, 'message', '') or error}".strip(": ")
            out[key] = ("error", _job_error(service, job_id, said or "no answer"))
    if not responses:
        error = getattr(job, "error", None)
        said = f"the job ended {state}" + (f" ({getattr(error, 'message', None) or error})" if error else "")
        out["*"] = ("error", _job_error(service, job_id, said))
    return out


def _read(service: str, reply) -> str:
    """The answer of one batch result, judged as a single request's (raises CutOff, Refused, ApiError as it does)."""
    if service == "anthropic":
        return _read_anthropic_reply(_as_dict(reply))
    if service == "openai":
        return _read_chat_reply(_as_dict(reply), "openai")
    return _read_google_reply(reply)


# ------------------------------ asking through batch jobs ----------------------

def _identity() -> dict:
    """What a job's answers depend on besides the prompt, kept with the job: the service, the model, the cache identity
    (llm.cache_identity: the service, the model, the thinking level sent and the repeat) and the answer limit its
    requests were sent (batch_tokens_sent: 32,768 to Google's Gemini Batch API)."""
    return {"service": llm.SERVICE, "model": llm.MODEL, "cache_identity": cache_identity(),
            "max_answer_tokens": batch_tokens_sent()}


#: The parts of a job's identity that make its answers this run's answers. The answer limit isn't one of them: an
#: answer that ended within one limit is the same answer under another, and a cut-off is kept with the limit the job
#: was sent at (_job_limit), so a run at another limit asks that prompt again.
_RECIPE = ("service", "model", "cache_identity")


def _is_ours(job: dict, identity: dict, keys) -> bool:
    """Whether a job's answers belong to this run: it holds one of this run's cache keys (a cache key names the service,
    the model, the thinking level sent and the repeat: common/common_helpers/cache.py, key), or it was sent with this
    run's service, model and cache identity, at any answer limit."""
    theirs = job.get("identity") or {}
    return bool(set(keys) & set(job.get("keys", []))) or all(theirs.get(k) == identity[k] for k in _RECIPE)


def _job_limit(job: dict):
    """The answer limit a job was sent with (its identity's max_answer_tokens); the limit this run's batch requests are
    sent (batch_tokens_sent) when the job doesn't say."""
    identity = job.get("identity") or {}
    return identity["max_answer_tokens"] if "max_answer_tokens" in identity else batch_tokens_sent()


def jobs_holding(cache_dir: Path, stage: str, keys) -> list:
    """The uncollected batch jobs that hold a request for one of these cache keys, whatever answer limit they were sent
    with: [{"id", "created", "held": how many of the keys}]. A cache key already names the service, the model, the
    thinking level sent and the repeat, so a job holding one of the keys holds a prompt of this run. A run with the
    setting batch false that asked these keys as single requests would pay for them twice."""
    path = batch_state_file(cache_dir, stage)
    if not path.exists():
        return []
    wanted = set(keys)
    return [{"id": j.get("id"), "created": j.get("created"), "held": len(wanted & set(j.get("keys", [])))}
            for j in _load(path)["jobs"]
            if not j.get("collected") and wanted & set(j.get("keys", []))]


def ask_batch(todo: dict, cache, check, cache_until, start, handle, paid, stage: str, workers: int) -> int:
    """Ask every prompt of todo, {where: (cache key, prompt)}, through the maker's batch API (llm.SERVICE, llm.MODEL),
    and call handle(n, where, (cache key, answer) or None, error or None) in this thread for each, as
    common/common_helpers/llm_paid.py's run_parallel does for single requests. Prompts with one cache key are sent
    once. start(n): called before the first new job is sent, with how many requests it pays for (PaidCalls.start: the
    question, then the test call). A job of an earlier run with the same model and settings that wasn't collected is
    collected instead of sending its prompts again, whatever answer limit it was sent with (_is_ours); an answer it
    holds for a prompt this run doesn't ask, and that isn't in the cache yet, is stored too (it was paid for), a
    cut-off as a cut-off. cache: the stage's Cache; check: the stage's shape check. workers: how many single requests
    (the re-asks of answers cut off at the batch API's lower answer limit, _ask_again_singly) are made at the same time,
    the step's setting workers. The number of answers handed to the stage."""
    service, model = llm.SERVICE, llm.MODEL
    refusal = batch_refusal(service)
    if refusal:
        sys.exit(refusal)
    path = batch_state_file(cache.path.parent, stage)
    by_key, prompt_of = {}, {}
    for where, (k, prompt) in todo.items():
        by_key.setdefault(k, []).append(where)
        prompt_of[k] = prompt
    identity = _identity()
    state = _load(path)
    open_jobs = [j for j in state["jobs"] if not j.get("collected")]
    resumed = [j for j in open_jobs if _is_ours(j, identity, by_key)]
    others = [j for j in open_jobs if not _is_ours(j, identity, by_key)]
    if others:
        listed = ", ".join(f"{j.get('id')} ({(j.get('identity') or {}).get('cache_identity')})" for j in others)
        note = (f"{len(others)} batch job(s) sent by an earlier run of this step with another model or settings "
                f"haven't been collected ({listed}), "
                f"so this run leaves them alone. Their answers can still be stored: run the step again with that model "
                f"and those settings (and --batch true) while the maker keeps the results ({RESULTS_KEPT[service]} "
                f"at {SERVICES[service]}). The jobs are listed in {_repo(path)}.")
        RUN_WARNINGS.append(note)
        log.warning(note)
    covered = {k for j in resumed for k in j.get("keys", [])}
    new_keys = [k for k in by_key if k not in covered]
    jobs = []
    for j in resumed:
        other_limit = (f", at the answer limit {_job_limit(j)} (this run's batch requests are sent {batch_tokens_sent()}: "
                       f"an answer it cut off is asked again by the next run, at that limit)"
                       if _job_limit(j) != batch_tokens_sent() else "")
        log.info(f"  collecting batch job {j['id']} at {SERVICES[service]}, sent by an earlier run on {j.get('created')} "
                 f"({j.get('requests', len(j.get('keys', []))):,} request(s){other_limit}): its answers are not paid "
                 f"for again")
        jobs.append(j)
        BATCH_JOBS.append({"service": service, "id": j["id"], "requests": j.get("requests", len(j.get("keys", []))),
                           "how": "resumed"})
    queue = None
    try:
        if new_keys:
            start(len(new_keys))
            built = {k: _request(service, k, prompt_of[k], model, cache_until) for k in new_keys}
            tokens = {k: estimated_tokens(prompt_of[k]) for k in new_keys}
            chunks = _chunks(service, [built[k][0] for k in new_keys], [tokens[k] for k in new_keys],
                             queue_cap(service, model))
            keys_of = {id(e): k for k, (e, _) in built.items()}
            made = []

            def send(chunk: dict) -> dict:
                label = f"{paid.step or 'pipeline'}-{stage}-{dt.datetime.now():%Y%m%d-%H%M%S}-{len(made) + 1}"
                job_id = _create_with_retries(service, model, chunk["entries"], label, jobs, path)
                made.append(job_id)
                keys = chunk["keys"]
                job = {"id": job_id, "service": service, "model": model, "identity": identity, "keys": keys,
                       "requests": len(keys), "input_tokens": chunk["tokens"], "created": _now(),
                       "settings_sent": built[keys[0]][1], "step": paid.step, "stage": stage, "collected": None}
                _save_job(path, job)
                with _requests_lock:
                    REQUESTS["sent"] += len(keys)
                BATCH_JOBS.append({"service": service, "id": job_id, "requests": len(keys), "how": "submitted"})
                log.info(f"  sent {len(keys):,} request(s) as batch job {job_id} to {BATCH_API[service]} (about "
                         f"{chunk['tokens']:,} input tokens; the run's requests are cut into {len(chunks)} job(s)); "
                         f"its id is kept in {_repo(path)}")
                return job
            queue = _Queue(service, model, [{"entries": c, "keys": [keys_of[id(e)] for e in c],
                                             "tokens": sum(tokens[keys_of[id(e)]] for e in c)} for c in chunks],
                           send, others, path)
            jobs.extend(queue.submit(list(jobs)))
        if not jobs and not (queue and queue.left()):
            return 0
        _wait(service, jobs, path, queue)
        results = {}
        for job in jobs:
            got = _results(service, job["id"], job.get("state", ""), job.get("keys", []))
            everyone = got.pop("*", None)
            for k in job.get("keys", []):
                results[k] = got.pop(k, None) or everyone or ("error", _job_error(
                    service, job["id"], "its results hold no answer for this request"))
                results[k] = (*results[k], job)
            for k, value in got.items():                    # an answer under a key the job didn't list
                results.setdefault(k, (*value, job))
    except KeyboardInterrupt:
        ids = ", ".join(j["id"] for j in jobs) or "none yet"
        unsent = (f" {queue.requests_left():,} request(s) waited for room in {SERVICES[service]}'s batch queue and "
                  f"were not sent: the next run sends them." if queue and queue.left() else "")
        raise Interrupted(f"Stopped with Ctrl+C while the batch job(s) ran ({ids}). They keep running at "
                          f"{SERVICES[service]}, and their ids are kept in {_repo(path)}: run the same command again "
                          f"(same model and settings) and it collects their answers instead of paying for them again."
                          f"{unsent} "
                          f"{SERVICES[service]} keeps a job's results for {RESULTS_KEPT[service]}. A job being created "
                          f"at the moment of Ctrl+C may exist at {SERVICES[service]} without its id kept; its "
                          f"prompts would be sent again.") from None
    return _hand_over(service, results, by_key, prompt_of, cache, check, cache_until, handle, paid, jobs, path,
                      workers)


def _create_with_retries(service: str, model: str, chunk: list, label: str, sent: list, path: Path) -> str:
    """_create, tried again on a rate limit or a server error (RetryLater: the service refused, so no job was made);
    a timeout, a lost connection or an error of no known kind (one that carries no HTTP status, such as
    httpx.ReadError) stops the step without trying again, since the job may exist (BATCH_CREATE_ATTEMPTS); any other
    refusal (ApiError) stops the step, saying so."""
    for attempt in range(BATCH_CREATE_ATTEMPTS):
        try:
            return _create(service, model, chunk, label)
        except RetryLater as e:                         # before RuntimeError, its parent: a refusal, so no job
            if _queue_full(e):
                raise QueueFull(str(e)) from None
            if attempt == BATCH_CREATE_ATTEMPTS - 1:
                error = e
                break
            log.warning(f"Sending a batch job to {SERVICES[service]} was refused for now ({e}); trying again in "
                        f"{BATCH_CREATE_WAIT} s (attempt {attempt + 2} of {BATCH_CREATE_ATTEMPTS}). Nothing to do: "
                        f"rate limits and server errors usually pass.")
            llm.time.sleep(BATCH_CREATE_WAIT)
        except ApiError as e:                           # a refusal with an HTTP status: no job
            if _queue_full(e):
                raise QueueFull(str(e)) from None
            error = e
            break
        except Exception as e:                          # noqa: BLE001  no answer, or an error of no known kind: the job may exist
            # NoAnswerInTime (a timeout), RuntimeError (a lost connection), or an error _sdk_error doesn't place (e.g.
            # httpx.ReadError while the answer was read): none says the service refused, so the job may have been made
            already = (f" The batch job(s) sent before it ({', '.join(j['id'] for j in sent)}) keep running; their ids "
                       f"are kept in {_repo(path)}, and the next run collects them." if sent else "")
            said = e if isinstance(e, (NoAnswerInTime, RuntimeError)) else f"{type(e).__name__}: {e}"
            sys.exit(f"Sending a batch job of {len(chunk):,} request(s) to {BATCH_API[service]} got no answer ({said}), "
                     f"so whether the job was made isn't known: {SERVICES[service]} may have made it before the answer "
                     f"was lost. It isn't sent again, which could pay for the same prompts twice.{already} What to do: "
                     f"look at the account's batch jobs ({BATCH_DOCS[service]} says where); if a job named {label} "
                     f"exists, wait for it to end and cancel or ignore its results, since its id isn't kept and no run "
                     f"collects it; then run the step again, which sends the prompts no kept job holds.")
    already = (f" The batch job(s) already sent ({', '.join(j['id'] for j in sent)}) keep running; their ids are kept "
               f"in {_repo(path)}, and the next run collects them." if sent else "")
    sys.exit(f"{BATCH_API[service]} refused the batch job ({error}), so none of its requests were sent, and nothing "
             f"was paid for them.{already} If the account or project can't use batch processing (a Google project "
             f"without billing gets \"400 FAILED_PRECONDITION. Precondition check failed.\" for every batch job, "
             f"with any model), give --batch false to send one request per prompt, or use an account that can; if "
             f"the message names a setting, see {BATCH_DOCS[service]}. Then run the step again.")


def _repo(path: Path) -> str:
    from common.step import repo_path
    try:
        return repo_path(path)
    except ValueError:
        return str(path)


def _wait(service: str, jobs: list, path: Path, queue=None) -> None:
    """Ask each job's state every BATCH_POLL_SECONDS until every job has ended; a line when a job's state or counts
    change, and at least every BATCH_PROGRESS_SECONDS. A failed check is tried again at the next one. Any other error
    stops the step and leaves the job uncollected, so the next run asks about it again; only a job the service says it
    doesn't know (HTTP 404) at two checks BATCH_POLL_SECONDS apart is marked as given up, and its requests are then
    sent again by the next run. queue (_Queue): the jobs not sent yet, each sent as soon as the maker's batch queue has
    room for it, and a job the maker refused for its queue cap after making it sent again; jobs grows by each job
    sent."""
    clock, began = llm.time.monotonic, llm.time.monotonic()
    pending, said, shown, not_found = list(jobs), {}, None, {}
    log.info(f"  waiting for {len(jobs)} batch job(s) at {SERVICES[service]}: most end within an hour, every one "
             f"within 24 hours. The run may be left running; Ctrl+C stops the waiting, not the job(s), and the next "
             f"run collects them.")
    while pending or (queue and queue.left()):
        if queue and queue.left():
            new = queue.submit(list(pending))
            jobs.extend(new)
            pending.extend(new)
            if new:
                shown = None
        for job in list(pending):
            try:
                status = _poll(service, job["id"])
            except (RetryLater, RuntimeError, NoAnswerInTime) as e:
                log.warning(f"Checking batch job {job['id']} at {SERVICES[service]} failed ({e}); checking again in "
                            f"{llm.BATCH_POLL_SECONDS} s. Nothing to do.")
                continue
            except ApiError as e:
                if _not_found(e) and not_found.get(job["id"]):
                    job.update(collected=_now(), state=f"not found: {e}")
                    _save_job(path, job)
                    sys.exit(f"{SERVICES[service]} doesn't know batch job {job['id']} (HTTP 404 at two checks "
                             f"{llm.BATCH_POLL_SECONDS} s apart: {e}), so its answers can't be collected. The job is "
                             f"marked as given up in {_repo(path)}: run the step again, and its prompts are sent in a "
                             f"new job (paid again, unless the old job never ran).")
                if _not_found(e):
                    not_found[job["id"]] = True
                    log.warning(f"{SERVICES[service]} doesn't know batch job {job['id']} ({e}); asking again in "
                                f"{llm.BATCH_POLL_SECONDS} s before giving it up.")
                    continue
                sys.exit(f"{SERVICES[service]} answered about batch job {job['id']} with an error ({e}), so this run "
                         f"can't collect its answers now. The job stays uncollected in {_repo(path)}, so nothing is "
                         f"paid twice: run the same command again (same model and settings, --batch true) to collect "
                         f"it. If the error names the account or the key (HTTP 401 or 403), fix that first; if it "
                         f"keeps coming, see {BATCH_DOCS[service]}.")
            not_found.pop(job["id"], None)
            job["state"] = status["state"]
            words = f"{status['state']}" + (f", {status['counts']}" if status["counts"] else "")
            if said.get(job["id"]) != words:
                said[job["id"]] = words
                shown = None
            if status["ended"]:
                pending.remove(job)
                if queue and queue.rejected(job, status):
                    jobs.remove(job)
        now = clock()
        if shown is None or now - shown >= llm.BATCH_PROGRESS_SECONDS:
            shown = now
            minutes = (now - began) / 60
            log.info(f"  batch job(s) after {minutes:.0f} min: " + "; ".join(f"{j['id']}: {said.get(j['id'], '?')}"
                                                                         for j in jobs)
                     + (f"; {queue.requests_left():,} request(s) not sent yet, waiting for room in the batch queue"
                        if queue and queue.left() else ""))
        if pending or (queue and queue.left()):
            llm.time.sleep(llm.BATCH_POLL_SECONDS)


def _not_found(error: ApiError) -> bool:
    """Whether the service answered HTTP 404 (it doesn't know the job): the status the error carries, or its words."""
    status = getattr(error, "status", None) or getattr(error, "status_code", None)
    return status == 404 or "HTTP 404" in str(error)


def _with_job_limit(error, job: dict):
    """A cut-off (llm.CutOff) of a job's answer, carrying the answer limit the job was sent with (max_answer_tokens,
    which common/common_helpers/cache.py, Cache.put_cut_off, keeps with the cut-off), so a run at another limit asks
    the prompt again; when that limit isn't the one this run's batch requests are sent (batch_tokens_sent), the error's
    words say so. Any other error as it is."""
    if not isinstance(error, llm.CutOff):
        return error
    limit = _job_limit(job)
    error.max_answer_tokens = limit
    if limit != batch_tokens_sent():
        error.args = (f"{error} (in batch job {job['id']}, sent at the answer limit {limit}; this run's limit is "
                      f"{batch_tokens_sent()}, so the next run asks it again at that limit)",)
    return error


def _cut_below_limit(error) -> bool:
    """Whether error is a cut-off at the lower answer limit of this service's batch requests
    (llm.BATCH_MAX_ANSWER_TOKENS), below the run's own limit (max_tokens_sent): such an answer is asked again in the
    same run, as a single request at the run's limit (_ask_again_singly)."""
    short, full = batch_tokens_sent(), max_tokens_sent()
    return (isinstance(error, llm.CutOff) and short is not None and full is not None and short < full
            and getattr(error, "max_answer_tokens", None) == short)


def _tokens(usage) -> tuple:
    """(tokens received, of them thinking) from a usage in OpenAI's shape; (None, None) when it has none."""
    if not isinstance(usage, dict) or not usage:
        return None, None
    return usage.get("completion_tokens"), llm.reasoning_tokens(usage)


def _hand_over(service, results, by_key, prompt_of, cache, check, cache_until, handle, paid, jobs, path,
               workers: int) -> int:
    """Judge every result as a single request's answer, hand each to the stage (handle), store answers to prompts
    this run didn't ask, mark the jobs collected, and stop early when too many failed. The number handed over."""
    judged, counts = {}, {j["id"]: {"answered": 0, "failed": 0} for j in jobs}
    for k, (kind, payload, job) in results.items():
        if k not in by_key and k in cache.answers:
            continue                                        # stored by an earlier run that collected this job
        _last.reply = {"settings_sent": job.get("settings_sent"), "batch_job": job["id"], "custom_id": k}
        _last.timing = {"attempts": 1, "seconds": 0}
        if kind == "error":
            payload.call = dict(_last.reply)
            judged[k] = (None, payload, None)
            continue
        try:
            text = _read(service, payload)
            _last.reply["http_status"] = 200
            judged[k] = (text, None, dict(_last.reply))
        except Exception as e:                              # noqa: BLE001  (CutOff, Refused, ApiError: as a single request's)
            e.call = {**dict(_last.reply), **(getattr(e, "call", None) or {})}
            judged[k] = (None, _with_job_limit(e, job), None)
    asked = [k for k in judged if k in by_key]
    short = [k for k in asked if _cut_below_limit(judged[k][1])]       # asked again singly below: no failures yet
    failed = [k for k in asked if judged[k][1] is not None and k not in short]
    early = len(failed) >= EARLY_STOP_FAILURES and len(failed) * EARLY_STOP_WINDOW >= EARLY_STOP_FAILURES * len(asked)
    n, later = 0, []
    job_of = {k: results[k][2]["id"] for k in results}
    for k in asked:                                         # first every answer that needs no second ask: none lost
        text, error, _ = judged[k]
        if k in short and not early:                        # asked again singly, after the second asks
            continue
        if error is None:
            data, state = find_json(text)
            if state == "object" and isinstance(data, dict) and not (check and check(data)):
                for where in by_key[k]:
                    n += 1
                    handle(n, where, (k, data), None)
                paid.made_call()
                counts[job_of[k]]["answered"] += 1
            else:
                later.append(k)
            continue
        for where in by_key[k]:
            n += 1
            handle(n, where, None, error)
        counts[job_of[k]]["failed"] += 1
    for k, (text, error, _) in judged.items():               # answers to prompts this run doesn't ask (paid for)
        if k in by_key:
            continue
        if isinstance(error, llm.CutOff):                   # a cut-off is kept as one, at its job's limit
            cache.put_cut_off(k, error)
            continue
        if error is not None:
            continue
        data, state = find_json(text)
        if state == "object" and isinstance(data, dict) and not (check and check(data)):
            cache.put(k, data)
    for k in later:                                         # a second ask as a single request, as call_llm_json does
        _last.reply = judged[k][2]
        _last.timing = {"attempts": 1, "seconds": 0}
        try:
            data, error = llm.call_llm_json(prompt_of[k], retries=0 if early else 1, cache_until=cache_until,
                                            check=check, first=judged[k][0]), None
            paid.made_call()
            counts[job_of[k]]["answered"] += 1
        except Exception as e:                              # noqa: BLE001
            data, error = None, e
            counts[job_of[k]]["failed"] += 1
        for where in by_key[k]:
            n += 1
            handle(n, where, (k, data) if error is None else None, error)
    if short and not early:
        n = _ask_again_singly(short, judged, by_key, prompt_of, check, cache_until, handle, paid, job_of, counts, n,
                              workers)
    for job in jobs:
        job["collected"] = _now()
        job.update(counts[job["id"]])
        _save_job(path, job)
        for j in BATCH_JOBS:
            if j["id"] == job["id"]:
                j.update(state=job.get("state"), **counts[job["id"]])
    if early:
        first = judged[failed[0]][1]
        raise EarlyStop(
            f"Step {paid.step.split('_')[0]} stopped: {len(failed)} of the {len(asked)} requests of batch job(s) "
            f"{', '.join(j['id'] for j in jobs)} failed (the first: {first}), so no answer was asked again and the "
            f"run ends here: the rest would most likely fail the same way (the early stop: {EARLY_STOP_FAILURES} "
            f"failed among {EARLY_STOP_WINDOW}, as a share, in common/common_helpers/llm.py). What to do: "
            f"{advice(first)}." + (f" Each failed request is described in {llm.OUTCOMES['file']}."
                                   if llm.OUTCOMES["file"] else "")
            + f" Every answer received is kept in the cache, so the next run sends only the rest: run "
              f"`{paid.command}` again once that is changed.", paid)
    return n


def _ask_again_singly(short, judged, by_key, prompt_of, check, cache_until, handle, paid, job_of, counts, n,
                      workers: int) -> int:
    """Ask each prompt whose batch answer was cut off at the batch API's lower answer limit (short: _cut_below_limit)
    again, as a single request at the run's limit (max_tokens_sent), billed at the full price, and hand its answer or
    its error to the stage, as a batch answer is handed (a cut-off at the run's limit is kept as one, at that limit).
    The requests are made workers at a time, as single requests are (common/common_helpers/llm_paid.py, run_parallel),
    and each answer is handed over in this thread as it arrives, so the stage caches it at once.
    Each is listed in its job's counts (asked_again_singly: the records, the cut answer's tokens and the new
    answer's, in the order of short), for the batch state file, the run's record and the report (batch_note). The
    number handed over so far."""
    service = llm.SERVICE
    log.info(f"  {len(short):,} answer(s) of the batch job(s) were cut off at {batch_tokens_sent():,} tokens, the most "
             f"{BATCH_API[service]} takes, so each is asked again now as a single request at {max_tokens_sent():,} "
             f"tokens, billed at the full price, {workers:,} at a time")
    entries = {}

    def ask(k):                                             # in a worker thread: _last is the thread's own
        _last.reply, _last.timing = {}, {}
        data = llm.call_llm_json(prompt_of[k], cache_until=cache_until, check=check)
        return data, (getattr(_last, "reply", None) or {}).get("usage")

    def handed(_, k, result, error):                        # in this thread, as each request ends
        nonlocal n
        if error is None:
            data, usage = result
            paid.made_call()
            counts[job_of[k]]["answered"] += 1
        else:
            data, usage = None, getattr(error, "usage", None) or (getattr(error, "call", None) or {}).get("usage")
            counts[job_of[k]]["failed"] += 1
        cut_tokens, cut_thinking = _tokens(getattr(judged[k][1], "usage", None))
        tokens, thinking = _tokens(usage)
        entries[k] = {
            "records": sorted({str(w[0] if isinstance(w, tuple) else w) for w in by_key[k]}), "custom_id": k,
            "cut_at": batch_tokens_sent(), "cut_tokens": cut_tokens, "cut_thinking_tokens": cut_thinking,
            "asked_at": max_tokens_sent(), "outcome": "answered" if error is None else
            "cut off" if isinstance(error, llm.CutOff) else "failed", "tokens": tokens, "thinking_tokens": thinking}
        for where in by_key[k]:
            n += 1
            handle(n, where, (k, data) if error is None else None, error)

    run_parallel(ask, {k: (k,) for k in short}, workers, handed,
                 "Every answer already received is kept in the cache, so it isn't paid for again. The batch job(s) "
                 "stay uncollected: run the same command again and it collects them and asks again only what isn't in "
                 "the cache.")
    for k in short:                                         # in the order of short, whatever order they ended in
        counts[job_of[k]].setdefault("asked_again_singly", []).append(entries[k])
    return n
