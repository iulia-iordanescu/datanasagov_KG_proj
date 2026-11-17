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
                   in each request, the same model, answer limit and thinking level, no temperature where none is sent.
                   One change, which changes no word the model gets: Anthropic's cached prompt start is marked for
                   the 1-hour cache (ANTHROPIC_CACHE_TTL)
    the answer     judged by the code that judges a single request's (_read_anthropic_reply, _read_chat_reply,
                   _read_google_reply, then llm.call_llm_json): the finish reason (a cut-off, a refusal), the token
                   counts (llm.REQUESTS), the served model (llm.SERVED), the JSON object and its shape
    the cache      each answer stored under the cache key of the same prompt asked as a single request
                   (common/common_helpers/cache.py)

What a batch run does that a run of single requests doesn't:

    job ids        every job is written to <the step's output folder>/cache/<stage>.batch_jobs.json the moment it is
                   created (batch_state_file). A run stopped while it waits (Ctrl+C, a closed window) leaves its jobs
                   running at the maker; the next run with the same model and settings collects them instead of paying
                   again, and sends only the prompts no job holds
    failures       a request the maker reports as errored, expired or canceled is a failed call, as a single request's
                   error is: recorded in the run's failed-call record, its record left out, asked again on the next run
                   (in a new job). Anthropic bills none of these ("You aren't billed for these requests"); OpenAI bills
                   "tokens consumed from any completed requests" of an expired job; Google's batch page says nothing
                   on it. A malformed answer is asked once more as a single request, as llm.call_llm_json does with
                   any answer
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
    _last, _requests_lock, cache_identity, max_tokens_sent)
from common.llm_errors import ApiError, NoAnswerInTime, RetryLater
from common.llm_litellm import _chat_payload, _read_chat_reply
from common.llm_makers import (
    _anthropic_params, _as_dict, _google_config, _google_typed_config, _read_anthropic_reply, _read_google_reply,
    _sdk_client, _sdk_send)
from common.llm_paid import EarlyStop, Interrupted, advice
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


#: A batch job's creation is tried this many times when the service answers with a rate limit or a server error
#: (e.g. Google's 503 "high demand"), BATCH_CREATE_WAIT seconds apart.
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
            f"object of the shape asked for, went as single requests, at the full price.")


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
    failed-call record)."""
    if service == "anthropic":
        params = _anthropic_params(prompt, model, cache_until)
        if "system" in params:
            params["system"][0]["cache_control"] = {"type": "ephemeral", "ttl": ANTHROPIC_CACHE_TTL}
        sent = {k: v for k, v in params.items() if k not in ("messages", "system")}
        if "system" in params:
            sent["system"] = f"the prompt's start, marked cache_control ephemeral, ttl {ANTHROPIC_CACHE_TTL}"
        return {"custom_id": custom_id, "params": params}, sent
    if service == "openai":
        body = _chat_payload(prompt, model, cache_until, "openai")
        return ({"custom_id": custom_id, "method": "POST", "url": "/v1/chat/completions", "body": body},
                {k: v for k, v in body.items() if k != "messages"})
    config = _google_config(model)
    return {"contents": prompt, "metadata": {"key": custom_id}, "config": config}, {"model": model, **config}


def _chunks(service: str, entries: list) -> list:
    """The requests cut into jobs within the maker's limits (BATCH_LIMITS: requests and bytes per job)."""
    most, most_bytes = BATCH_LIMITS[service]
    chunks, size = [[]], 0
    for entry in entries:
        n = len(json.dumps(entry, ensure_ascii=False).encode("utf-8")) + 1
        if chunks[-1] and (len(chunks[-1]) >= most or size + n > most_bytes):
            chunks.append([])
            size = 0
        chunks[-1].append(entry)
        size += n
    return [c for c in chunks if c]


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
        return {"ended": job.get("status") in _ENDED["openai"], "state": str(job.get("status")),
                "counts": f"{c.get('completed') or 0:,} of {c.get('total') or 0:,} answered, {c.get('failed') or 0:,} "
                          f"failed" if c else ""}
    job = _sdk_send(service, lambda: client.batches.get(name=job_id))
    state = _state_name(getattr(job, "state", None))
    stats = _as_dict(getattr(job, "completion_stats", None)) if getattr(job, "completion_stats", None) else {}
    return {"ended": state in _ENDED["google"], "state": state,
            "counts": (f"{stats.get('successful_count') or 0:,} answered, {stats.get('failed_count') or 0:,} failed"
                       if stats else "")}


def _job_error(service: str, job_id: str, said: str) -> ApiError:
    return ApiError(f"batch job {job_id} at {SERVICES[service]} ended without this request's answer: {said}; it is "
                    f"asked again on the next run")


def _results(service: str, job_id: str, state: str) -> dict:
    """{custom_id: ("answer", the maker's reply) | ("error", ApiError)}: what the ended job holds, by request. Results
    may come in any order (Anthropic, OpenAI: matched by custom_id; Google: by the metadata key each request carried)."""
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
    for item in responses:
        key = str((getattr(item, "metadata", None) or {}).get("key"))
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
    """What a job's answers depend on besides the prompt: a job is collected only by a run whose identity is the same."""
    return {"service": llm.SERVICE, "model": llm.MODEL, "cache_identity": cache_identity(),
            "max_answer_tokens": max_tokens_sent()}


def ask_batch(todo: dict, cache, check, cache_until, start, handle, paid, stage: str) -> int:
    """Ask every prompt of todo, {where: (cache key, prompt)}, through the maker's batch API (llm.SERVICE, llm.MODEL),
    and call handle(n, where, (cache key, answer) or None, error or None) in this thread for each, as
    common/common_helpers/llm_paid.py's run_parallel does for single requests. Prompts with one cache key are sent
    once. start(n): called before the first new job is sent, with how many requests it pays for (PaidCalls.start: the
    question, then the test call). A job of an earlier run with the same model and settings that wasn't collected is
    collected instead of sending its prompts again; an answer it holds for a prompt this run doesn't ask, and that
    isn't in the cache yet, is stored too (it was paid for). cache: the stage's Cache; check: the stage's shape check.
    The number of answers handed to the stage."""
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
    resumed = [j for j in open_jobs if j.get("identity") == identity]
    others = [j for j in open_jobs if j.get("identity") != identity]
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
        log.info(f"  collecting batch job {j['id']} at {SERVICES[service]}, sent by an earlier run on {j.get('created')} "
                 f"({j.get('requests', len(j.get('keys', []))):,} request(s)): its answers are not paid for again")
        jobs.append(j)
        BATCH_JOBS.append({"service": service, "id": j["id"], "requests": j.get("requests", len(j.get("keys", []))),
                           "how": "resumed"})
    try:
        if new_keys:
            start(len(new_keys))
            built = {k: _request(service, k, prompt_of[k], model, cache_until) for k in new_keys}
            chunks = _chunks(service, [built[k][0] for k in new_keys])
            keys_of = {id(e): k for k, (e, _) in built.items()}
            for i, chunk in enumerate(chunks, 1):
                label = f"{paid.step or 'pipeline'}-{stage}-{dt.datetime.now():%Y%m%d-%H%M%S}-{i}"
                job_id = _create_with_retries(service, model, chunk, label, jobs, path)
                keys = [keys_of[id(e)] for e in chunk]
                job = {"id": job_id, "service": service, "model": model, "identity": identity, "keys": keys,
                       "requests": len(keys), "created": _now(), "settings_sent": built[keys[0]][1],
                       "step": paid.step, "stage": stage, "collected": None}
                _save_job(path, job)
                with _requests_lock:
                    REQUESTS["sent"] += len(keys)
                BATCH_JOBS.append({"service": service, "id": job_id, "requests": len(keys), "how": "submitted"})
                jobs.append(job)
                log.info(f"  sent {len(keys):,} request(s) as batch job {job_id} to {BATCH_API[service]} "
                         f"(job {i} of {len(chunks)}); its id is kept in {_repo(path)}")
        if not jobs:
            return 0
        _wait(service, jobs, path)
        results = {}
        for job in jobs:
            got = _results(service, job["id"], job.get("state", ""))
            everyone = got.pop("*", None)
            for k in job.get("keys", []):
                results[k] = got.pop(k, None) or everyone or ("error", _job_error(
                    service, job["id"], "its results hold no answer for this request"))
                results[k] = (*results[k], job)
            for k, value in got.items():                    # an answer under a key the job didn't list
                results.setdefault(k, (*value, job))
    except KeyboardInterrupt:
        ids = ", ".join(j["id"] for j in jobs) or "none yet"
        raise Interrupted(f"Stopped with Ctrl+C while the batch job(s) ran ({ids}). They keep running at "
                          f"{SERVICES[service]}, and their ids are kept in {_repo(path)}: run the same command again "
                          f"(same model and settings) and it collects their answers instead of paying for them again. "
                          f"{SERVICES[service]} keeps a job's results for {RESULTS_KEPT[service]}. A job being created "
                          f"at the moment of Ctrl+C may exist at {SERVICES[service]} without its id kept; its "
                          f"prompts would be sent again.") from None
    return _hand_over(service, results, by_key, prompt_of, cache, check, cache_until, handle, paid, jobs, path)


def _create_with_retries(service: str, model: str, chunk: list, label: str, sent: list, path: Path) -> str:
    """_create, tried again on a rate limit or a server error; any other refusal stops the step, saying so."""
    for attempt in range(BATCH_CREATE_ATTEMPTS):
        try:
            return _create(service, model, chunk, label)
        except (RetryLater, RuntimeError, NoAnswerInTime) as e:
            if attempt == BATCH_CREATE_ATTEMPTS - 1:
                error = e
                break
            log.warning(f"Sending a batch job to {SERVICES[service]} failed ({e}); trying again in "
                        f"{BATCH_CREATE_WAIT} s (attempt {attempt + 2} of {BATCH_CREATE_ATTEMPTS}). Nothing to do: "
                        f"rate limits and server errors usually pass.")
            llm.time.sleep(BATCH_CREATE_WAIT)
        except ApiError as e:
            error = e
            break
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


def _wait(service: str, jobs: list, path: Path) -> None:
    """Ask each job's state every BATCH_POLL_SECONDS until every job has ended; a line when a job's state or counts
    change, and at least every BATCH_PROGRESS_SECONDS. A failed check is tried again at the next one; a job the
    service no longer knows stops the step (its requests are then sent again by the next run)."""
    clock, began = llm.time.monotonic, llm.time.monotonic()
    pending, said, shown = list(jobs), {}, None
    log.info(f"  waiting for {len(jobs)} batch job(s) at {SERVICES[service]}: most end within an hour, every one "
             f"within 24 hours. The run may be left running; Ctrl+C stops the waiting, not the job(s), and the next "
             f"run collects them.")
    while pending:
        for job in list(pending):
            try:
                status = _poll(service, job["id"])
            except (RetryLater, RuntimeError, NoAnswerInTime) as e:
                log.warning(f"Checking batch job {job['id']} at {SERVICES[service]} failed ({e}); checking again in "
                            f"{llm.BATCH_POLL_SECONDS} s. Nothing to do.")
                continue
            except ApiError as e:
                job.update(collected=_now(), state=f"not found: {e}")
                _save_job(path, job)
                sys.exit(f"{SERVICES[service]} answered about batch job {job['id']} with an error ({e}), so its answers "
                         f"can't be collected. The job is marked as given up in {_repo(path)}: run the step again, and "
                         f"its prompts are sent in a new job (paid again, unless the old job never ran).")
            job["state"] = status["state"]
            words = f"{status['state']}" + (f", {status['counts']}" if status["counts"] else "")
            if said.get(job["id"]) != words:
                said[job["id"]] = words
                shown = None
            if status["ended"]:
                pending.remove(job)
        now = clock()
        if shown is None or now - shown >= llm.BATCH_PROGRESS_SECONDS:
            shown = now
            minutes = (now - began) / 60
            log.info(f"  batch job(s) after {minutes:.0f} min: " + "; ".join(f"{j['id']}: {said.get(j['id'], '?')}"
                                                                         for j in jobs))
        if pending:
            llm.time.sleep(llm.BATCH_POLL_SECONDS)


def _hand_over(service, results, by_key, prompt_of, cache, check, cache_until, handle, paid, jobs, path) -> int:
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
            judged[k] = (None, e, None)
    asked = [k for k in judged if k in by_key]
    failed = [k for k in asked if judged[k][1] is not None]
    early = len(failed) >= EARLY_STOP_FAILURES and len(failed) * EARLY_STOP_WINDOW >= EARLY_STOP_FAILURES * len(asked)
    n, later = 0, []
    job_of = {k: results[k][2]["id"] for k in results}
    for k in asked:                                         # first every answer that needs no second ask: none lost
        text, error, _ = judged[k]
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
        if k in by_key or error is not None:
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
