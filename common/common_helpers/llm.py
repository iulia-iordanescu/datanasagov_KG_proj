"""
common/common_helpers/llm.py -- the one place a model is called.

Used by every step that asks a model something: 040 (inducing the schema),
050 (drafting ground truth), 060 (extracting), and 070 (translating component
classes). The Ask Sage client was
moved from archive/to_be_reshaped/llm_client.py, with its retries and re-asks now
logged through common.audit's log (so they reach the step's log file)
instead of printed.

This file holds the run's model and every setting a person may change. The code that calls the model is in its
parts, each a file of its own beside this one, and every name of a part is imported from here, as every caller
does (`from common import llm`, `from common.llm import confirm`):

    llm.py            THE RUN'S MODEL: MODEL, SERVICE, THINKING, REPEAT and the other settings; describe and
                      model_label for the run's record and report; cache_identity; the LiteLLM answer cache bypass
                      (answer_cache_control); the settings a call is sent with (call_settings); this run's requests
                      (REQUESTS) and what the latest one sent and got back (_last); the services (SERVICES,
                      DIRECT_SERVICES); the early stop's numbers; who makes a model (maker, same_model_name)
    llm_errors.py     the errors a call raises, and the two stops: a used-up budget (budget_exhausted) stops the
                      whole run; forbid_model_calls, a free command's guarantee: from then on, no request is sent,
                      in its processes too
    llm_replies.py    classify_reply: what a reply is (complete, cut off, refused, empty, malformed), judged by
                      the service's finish reason AND the answer's content, the same for every service: the one
                      place that decides it; and what each request records of itself
    llm_asksage.py, llm_litellm.py, llm_makers.py
                      THE ASK SAGE CLIENT, THE LITELLM CLIENT, and THE MAKERS' OWN APIS (Anthropic's, OpenAI's,
                      Google's, each through its maker's official Python SDK): one request each
    llm_calls.py      EVERY SERVICE: list_models (the model names the service lists; free: py helpers/models.py);
                      call_llm (send a prompt, get the reply text; retries rate limits and server errors with
                      backoff); try_model (one one-line test call to a model: is it usable? py helpers/models.py
                      --try); call_llm_json (the same, parsed as a JSON object; re-asks once if the reply is not
                      one, or not of the shape the caller checks for); fence_safe (keeps a record from ending its
                      data block early)
    llm_paid.py       A PAID RUN: PaidCalls (asks once before a run's first paid call, showing any notes about the
                      run first, makes a one-line test call and checks its token counts, counts the calls, shows
                      their progress, records each failed call, and stops early when the first calls fail); Calls,
                      paid_calls (what a step's stages share: PaidCalls and the folder its answers are cached in,
                      common/common_helpers/cache.py); run_parallel (runs jobs a few at a time; Ctrl-C cancels
                      those not yet started); confirm (the stop itself)
    llm_batch.py      BATCH PROCESSING (the setting batch): a stage's model calls sent as batch jobs to a maker's
                      batch API (Anthropic's, OpenAI's, Google's), at half the price of single requests; each request
                      built and each answer judged by the same code as a single request's; the job ids kept in the
                      step's cache folder, so a stopped run collects its jobs instead of paying again (ask_batch)

The parts are loaded at the end of this file and need it loaded first, so they are imported only through it. A part
reads the settings set at run time (MODEL, SERVICE, THINKING, REPEAT, SESSION_ID, MAX_ANSWER_TOKENS) and calls the
functions a test may replace (load_dotenv, _post, _asksage_token, _litellm, each service's _ask_ function, call_llm,
call_llm_json, confirm, list_models) as llm.NAME, looked up here when used: paid_calls sets a run's settings here,
a test replaces a function here, and every part sees it (tests/test_model_calls.py checks that each part does so).

What the steps that extract triple instances with entity classes share
(the prompt's rules, the reply format, the BEGIN/END lines) is in
common/common_helpers/extraction.py and common/common_prompts/.

    from common import llm
    calls = llm.paid_calls(settings, output, notes)   # once per run
    calls.paid.start("plan in words")                 # before the first paid call
    data = llm.call_llm_json(prompt)                  # a dict, or raises

Needs a .env in the repository folder with ASKSAGE_EMAIL and
ASKSAGE_API_KEY (Ask Sage), LITELLM_API_KEY (LiteLLM), ANTHROPIC_API_KEY
(Anthropic), OPENAI_API_KEY (OpenAI) or GEMINI_API_KEY (Google), and the
packages requests and python-dotenv; a maker's own API also needs its SDK
(requirements.txt: anthropic, openai, google-genai), imported only when that
service is used.
"""

import json
import os
import re
import sys
import threading
import time as time                                       # the tests replace llm.time.sleep

import requests as requests                               # the tests replace llm.requests.post
from dotenv import load_dotenv

from common.audit import log as log                       # common/common_helpers/cache.py logs through llm.log


# ------------------------------ the run's model and its settings ----------------

#: The model the calls use: the default of every step's `model` setting,
#: which paid_calls() puts here for the run. `py helpers/models.py` lists the models
#: the service shows your account (a listed model may still refuse you: the
#: run's first call, a one-line test, finds out for the price of that call).
#: It is part of every cache key (common/common_helpers/cache.py), so changing it asks again.
#: The default of 040, 060, and 070 (a LiteLLM name: the default service is LiteLLM), spelled as LiteLLM lists it.
#: LiteLLM also accepts the spelling "claude-opus-5.5", the default until 2026-11-01, without listing it; both
#: answered on 2026-11-01, and whether they reach the same deployment is a question for LiteLLM's administrators
#: (docs/findings.md, 2026-11-01). The two are compared as the same model (same_model_name), but as a different
#: cache key: answers saved under one spelling aren't reused under the other.
MODEL = "claude-opus-5-5"


#: The default model of step 050, which drafts the classed triples a person corrects into ground truth: from another maker than MODEL, so the facts one
#: model misses aren't missing from both the ground truth and the extraction (060 warns when they're the same maker).
DRAFTING_MODEL = "gemini-2.5-pro"


#: The service that reaches the model: the default of every step's `service` setting, which paid_calls() puts here
#: for the run. "asksage": NASA's Ask Sage (ASKSAGE_EMAIL and ASKSAGE_API_KEY in .env); "litellm": NASA's LiteLLM
#: proxy (LITELLM_API_KEY in .env); "anthropic", "openai", "google": the model maker's own API, reached directly
#: through the maker's official Python SDK (DIRECT_SERVICES: ANTHROPIC_API_KEY, OPENAI_API_KEY or GEMINI_API_KEY in
#: .env), for the baseline of three makers' models (docs/improvements.md, 2026-11-14). A model's name is the
#: service's own: Ask Sage's "google-claude-sonnet-5" is LiteLLM's "claude-sonnet-5".
SERVICE = "litellm"


SERVICES = {"asksage": "Ask Sage", "litellm": "LiteLLM", "anthropic": "Anthropic's API", "openai": "OpenAI's API",
            "google": "Google's Gemini API"}


#: Every call to a model that takes it asks for the model's most likely answer (temperature 0), the same each time
#: as far as the model allows: only where temperature_sent says so. Anthropic's Claude Opus 5.5 takes no sampling
#: parameters ("Omit `temperature`, `top_p`, and `top_k`", and temperature 0 "never guaranteed identical outputs on
#: prior models": https://platform.claude.com/docs/en/models/opus-5-5/migration-guide); Google advises keeping
#: Gemini 3's temperature at its default 1.0 ("Setting temperature below 1.0 may lead to unexpected behavior, such as
#: looping or degraded performance": https://ai.google.dev/gemini-api/docs/gemini-3), and for Gemini 4 Argon says
#: "Remove `temperature`, `top_p`, and `top_k` from your requests. If provided, they are ignored"
#: (https://ai.google.dev/gemini-api/docs/latest-model, read 2026-11-01). OpenAI says of its GPT-6 models (GPT-6 Astra,
#: GPT-6.1 Sol, ...): "When reasoning effort is not `none`, remove `temperature`, `top_p`, and `top_logprobs`", and
#: "GPT-6 Astra and GPT-6.1 Sol do not support the `none` reasoning effort"
#: (https://developers.openai.com/api/docs/guides/latest-model, read 2026-11-02), so they are sent none either.
#: Not part of the cache key.
TEMPERATURE = 0


#: How much a model that thinks before answering may think: the default of every step's `thinking` setting, which
#: paid_calls() puts here for the run. A model's thinking is hidden, billed as answer tokens, and counts against
#: MAX_ANSWER_TOKENS (Google's Gemini docs: the answer limit includes "thought tokens"), so uncapped thinking leaves
#: less room for the answer: on 2026-10-21, gemini-2.5-pro's answer for a 1,503-character record was cut off after
#: 10,623 characters, far fewer than 16,000 tokens hold. Sent as LiteLLM's `reasoning_effort`, only where LiteLLM
#: documents it (thinking_sent): for Gemini 2.5 Pro, LiteLLM turns "low" into a thinking budget of 1,024 tokens, so
#: the answer keeps about 15,000 of MAX_ANSWER_TOKENS; for Gemini 3 and 4, into its thinking level of the same name
#: (https://docs.litellm.ai/docs/providers/gemini, "Mapping for Gemini 3+ models"; Gemini 4 Argon takes low, medium
#: and high, medium being its default: https://ai.google.dev/gemini-api/docs/thinking). For OpenAI's GPT-6 models, as
#: the same level: OpenAI's Chat Completions take `reasoning_effort` ("Use `reasoning.effort` in Responses or
#: `reasoning_effort` in Chat Completions": https://developers.openai.com/api/docs/guides/latest-model), GPT-6 Astra
#: supports "`low`, `medium`, `high`, `xhigh`, and `max`" (https://developers.openai.com/api/docs/models/gpt-6-astra),
#: GPT-6.1 Sol low, medium (its default), high, xhigh and max; LiteLLM passes it on for gpt-6-astra
#: (https://docs.litellm.ai/blog/gpt_6_astra; all read 2026-11-02). "model_default" sends nothing, so the model
#: thinks as it would by default.
THINKING = "low"


THINKING_LEVELS = ("low", "medium", "high", "model_default")


#: Which repeat of the same recipe a run is (the setting `repeat` of every step that calls a model): 1, the default,
#: reuses the answers saved so far; 2, 3, ... are asked again, each into cache entries of its own, so repeats of one
#: recipe are independent answers of the model, and their spread is the model's own variation (the noise floor,
#: helpers/compare_runs.py). Part of the cache key (cache_identity) only from 2 on, so repeat 1's key is the key
#: answers were saved under before this setting existed, and they stay valid. Not sent to the model.
REPEAT = 1


#: Whether a stage that asks many independent prompts at once (common/common_helpers/extraction.py, ask_model) sends
#: them as batch jobs to the maker's batch API instead of one request each: the setting `batch`, which only 060 has
#: (common/common_helpers/step.py refuses --batch for every other step), and which paid_calls() puts here for the run. Only through a maker's own API
#: (DIRECT_SERVICES): Anthropic's Message Batches API (https://platform.claude.com/docs/en/build-with-claude/batch-processing),
#: OpenAI's Batch API (https://developers.openai.com/api/docs/guides/batch) and Google's Gemini Batch API
#: (https://aistudio.google.com/docs/batch-api), each at 50% of the price of single requests (all read 2026-11-17).
#: Each request carries its whole prompt, the same model and the same settings as a single request
#: (common/common_helpers/llm_batch.py), so it changes neither the words the model gets nor the cache key
#: (cache_identity): answers saved by single requests are reused by a batch run, and the other way round.
BATCH = False


#: How often a batch job's state is asked for while the run waits for it, in seconds (asking is free), and how often
#: the waiting run writes a line when nothing changed. Anthropic: "most batches finishing in less than 1 hour"; each
#: maker ends a job within 24 hours (Google: a job "running or pending for more than 48 hours" expires).
BATCH_POLL_SECONDS = 60


BATCH_PROGRESS_SECONDS = 600


#: The most requests, and bytes of requests, one batch job takes, by service; a stage with more is sent as several
#: jobs. Anthropic: "limited to either 100,000 Message requests or 256 MB in size, whichever is reached first";
#: OpenAI: "up to 50,000 requests, and a batch input file can be up to 200 MB in size"; Google, for requests sent
#: inline (as here): "keep the total request size under 20MB" (the makers' batch pages cited at BATCH, read
#: 2026-11-17). The byte limits here are set a little lower, since a request's size on the wire is not exactly the
#: size of its JSON text as counted here.
BATCH_LIMITS = {"anthropic": (100_000, 240_000_000), "openai": (50_000, 190_000_000), "google": (100_000, 18_000_000)}


#: The most input tokens this pipeline lets wait in a maker's batch queue for one model at one time, by service and
#: model; a model not listed has no cap here. A run whose requests hold more is sent as several jobs, each sent once
#: the jobs before it have left the queue (common/common_helpers/llm_batch.py, _Queue). The values leave a margin of
#: about 10% below the account's caps for the estimate of a prompt's tokens (llm_batch.py, estimated_tokens).
#:   openai  "The Batch/Background Rate Limit caps the total input tokens queued for a model. Once a batch job
#:           completes, its tokens no longer count toward the limit. The API counts input tokens at submission"
#:           (https://developers.openai.com/api/docs/guides/rate-limits, read 2026-11-17). The account's caps (its usage
#:           tier, Build, on its limits page, read 2026-11-17): gpt-6.1-sol and gpt-6.1-terra 1,350,000 tokens,
#:           gpt-6-luna 20,000,000
#:   google  "Enqueued tokens per model": "the maximum number of tokens that can be enqueued for batch processing
#:           across all your active batch jobs for a given model" (https://aistudio.google.com/docs/rate-limits, read
#:           2026-11-17). Tier 1: gemini-4-argon 5,000,000, gemini-3.8-flash 3,000,000, gemini-3.5-flash-lite
#:           10,000,000
#: Anthropic's batch pages state no token cap (BATCH_QUEUE_REQUESTS has its cap on requests).
BATCH_QUEUE_TOKENS = {"openai": {"gpt-6.1-sol": 1_200_000, "gpt-6.1-terra": 1_200_000, "gpt-6-luna": 18_000_000},
                      "google": {"gemini-4-argon": 4_500_000, "gemini-3.8-flash": 2_700_000,
                                 "gemini-3.5-flash-lite": 9_000_000}}


#: The most requests this pipeline lets wait or run in a maker's batch queue at one time, by service, counted over
#: every uncollected job of the service, whatever its model; a job also holds no more than this many requests.
#:   google     "Concurrent batch requests": 100 for every model (https://aistudio.google.com/docs/rate-limits, read
#:              2026-11-17). The page doesn't define the term, and its batch page (https://aistudio.google.com/docs/
#:              batch-api) uses "request" for one item of a job. Read as 100 requests, it also holds if Google means
#:              100 jobs (a run sends far fewer than 100 jobs), so the narrower reading is the one applied: a run of
#:              more than 100 requests is sent as jobs of at most 100, one after another.
#:   anthropic  the Start tier's "Batch requests in processing queue": 200,000, with at most 100,000 per batch (its
#:              rate limits page, https://platform.claude.com/docs/en/api/rate-limits, read 2026-11-17; the 100,000 per
#:              job is BATCH_LIMITS)
#: OpenAI caps tokens, not requests in the queue (BATCH_QUEUE_TOKENS).
BATCH_QUEUE_REQUESTS = {"google": 100, "anthropic": 200_000}


#: The batch jobs this run submitted or collected (common/common_helpers/llm_batch.py), for the run's record
#: (describe) and the report's Model calls: {"service", "id", "requests", "how": "submitted" | "resumed", "state",
#: "answered", "failed"}. Reset by paid_calls.
BATCH_JOBS = []


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
#: Sent as `max_tokens`, except to OpenAI's GPT-6 models, which get `max_completion_tokens` (answer_limit_name).
#: GPT-6 Astra's max output is 128,000 tokens (https://developers.openai.com/api/docs/models/gpt-6-astra).
#: 64,000 since 2026-11-17 (the code review of that day): thinking counts against the limit, and one record cut off
#: leaves the record unextracted, so 070 stops evaluating at it. 64,000 is the largest round value every model
#: planned for the runs accepts as a synchronous request (all read 2026-11-17): Claude Opus 5.5, Sonnet 5.5 and
#: Haiku 5.5, 128K tokens each (https://platform.claude.com/docs/en/about-claude/models/overview, "Max output");
#: GPT-6.1 Sol, GPT-6.1 Terra and GPT-6 Luna, "128,000 max output tokens" each
#: (https://developers.openai.com/api/docs/models/gpt-6.1-sol, .../gpt-6.1-terra, .../gpt-6-luna); Gemini 4 Argon
#: 65,536 ("default synchronous"), Gemini 3.8 Flash and Gemini 3.5 Flash-Lite 65,536 each
#: (https://aistudio.google.com/docs/models/gemini-4-argon, .../gemini-3.8-flash, .../gemini-3.5-flash-lite).
#: A batch job keeps the limit its requests were sent at (llm_batch._identity: batch_tokens_sent), so that a cut-off
#: in it is kept with that limit (common/common_helpers/cache.py, Cache.put_cut_off).
MAX_ANSWER_TOKENS = 64000


#: The highest answer limit a maker's batch API takes, by service, where it is below MAX_ANSWER_TOKENS: a batch request
#: to that service is sent this limit instead (batch_tokens_sent), and a single request still MAX_ANSWER_TOKENS.
#:   google  Google's Gemini Batch API refused a job of step 060 sent at 64,000 with "HTTP 400: Error on line 1:
#:           Decoding continuation is not supported for batch requests, so max_output_tokens cannot exceed 32768"
#:           (its answer of 2026-11-17, in outputs/reports/060_extract_2026-11-17_2020.md); its batch page,
#:           https://aistudio.google.com/docs/batch-api, gives the batch API's limits. A single request to Google takes
#:           65,536 (MAX_ANSWER_TOKENS).
#: An answer that ends within this limit is kept as it is: the limit is where the service stops an answer. That a
#: lower limit changes nothing else in how the model answers (its thinking included) is assumed; no maker's page
#: says so. An answer a batch job cuts off at this limit is asked again in the same run, as a single request at
#: MAX_ANSWER_TOKENS, billed at the full price (common/common_helpers/llm_batch.py, _hand_over); the run keeps that
#: answer, and the report says how many were asked again (llm_batch.batch_note). The new answer is a second answer to
#: the prompt, not the cut one continued.
BATCH_MAX_ANSWER_TOKENS = {"google": 32768}


#: How long a call waits for its answer, in seconds, every call alike: long enough for an answer of
#: MAX_ANSWER_TOKENS, so a long answer isn't abandoned and asked again (each attempt may be billed). 2,400 s covers
#: 64,000 tokens at about 27 tokens a second, thinking included (1,200 s for 32,000 tokens before 2026-11-17).
READ_TIMEOUT = 2400


#: The effort level a model runs at when none is sent, where its maker documents one: on Claude Opus 5.5 adaptive
#: thinking is always on (the model decides whether and how much to think, and effort is the main control of how
#: much), and "A request that omits `effort` runs at `medium`" (https://platform.claude.com/docs/en/models/opus-5-5/whats-new-opus-5-5;
#: https://platform.claude.com/docs/en/build-with-claude/effort). For the run's record only, where no effort is sent
#: (every service but Anthropic's own, which sends the step's thinking level as the effort: effort_note).
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
            **({"session_id": SESSION_ID} if SESSION_ID and SERVICE == "litellm" else {}),
            **({"batch": True, "batch_jobs": [dict(j) for j in BATCH_JOBS]} if BATCH else {})}


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
            "detected)", "thinking": thinking, "thinking_sent": sent, "effort": effort_note(model, service)}


def answer_limit_name(model: str | None = None, service: str | None = None) -> str:
    """The name the answer limit is sent under. Through LiteLLM: `max_completion_tokens` for OpenAI's GPT-6 models
    (OpenAI's Chat Completions reference: `max_tokens` "is now deprecated in favor of `max_completion_tokens`, and is
    not compatible with o-series models", and `max_completion_tokens` includes the reasoning tokens; LiteLLM: for
    gpt-6-astra, "`max_completion_tokens` instead of `max_tokens`", and a LiteLLM version before its fix sends
    `max_tokens` on unchanged, which OpenAI rejects: https://docs.litellm.ai/blog/gpt_6_astra, read 2026-11-02);
    `max_tokens` for every other model, as before. Through a maker's own API, the maker's name for it: OpenAI's
    `max_completion_tokens` for every model (the deprecation above;
    https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create, read
    2026-11-14), Anthropic's `max_tokens` (https://platform.claude.com/docs/en/api/messages), Google's
    `max_output_tokens` (GenerateContentConfig in google-genai's google/genai/types.py; maxOutputTokens in
    https://aistudio.google.com/api-reference/generate-content; both read 2026-11-14)."""
    service = service or SERVICE
    if service in DIRECT_SERVICES:
        return DIRECT_SERVICES[service]["answer_limit"]
    return "max_completion_tokens" if _gpt_version(model or MODEL) >= 6 else "max_tokens"


def _gpt_version(model: str) -> float:
    """The version of an OpenAI GPT model from its name ("gpt-6-astra" -> 6, "gpt-6.1-sol" -> 6.1); 0 for any other
    model."""
    if maker(model) != "OpenAI":
        return 0
    version = re.search(r"gpt-(\d+(?:\.\d+)?)", model.lower())
    return float(version.group(1)) if version else 0


def max_tokens_sent(service: str | None = None) -> int | None:
    """The answer limit a call sends (MAX_ANSWER_TOKENS), or None when it sends none: LiteLLM and the makers' own APIs
    take it (answer_limit_name); Ask Sage's query has no such parameter (_ask_asksage)."""
    return None if (service or SERVICE) == "asksage" else MAX_ANSWER_TOKENS


def batch_tokens_sent(service: str | None = None) -> int | None:
    """The answer limit a batch request sends: max_tokens_sent, lowered to the service's BATCH_MAX_ANSWER_TOKENS where
    it has one (Google's Gemini Batch API: 32,768)."""
    service = service or SERVICE
    limit, cap = max_tokens_sent(service), BATCH_MAX_ANSWER_TOKENS.get(service)
    return min(limit, cap) if limit is not None and cap is not None else limit


def effort_note(model: str | None = None, service: str | None = None) -> str | None:
    """The effort a Claude model ran at, in words (None for other makers' models): the level sent, through Anthropic's
    own API (thinking_sent); else none is sent, so it is the model's default (DEFAULT_EFFORT, where documented)."""
    model = model or MODEL
    if maker(model) != "Anthropic":
        return None
    sent = thinking_sent(model, service)
    if sent:
        return f"sent as {thinking_parameter(model, service)} {sent}"
    default = DEFAULT_EFFORT.get(model.lower().removeprefix("google-"))
    return f"not sent (model default, {default})" if default else "not sent (model default)"


def temperature_sent(model: str | None = None, service: str | None = None) -> bool:
    """Whether calls to this model are sent TEMPERATURE: not to Anthropic's Claude models, which take no sampling
    parameters, nor to Google's Gemini 3 and later (Gemini 4 Argon ignores it; Gemini 3's maker advises keeping the
    default), nor to OpenAI's GPT-6 models (their maker says to remove it when reasoning, which they always do:
    TEMPERATURE cites all three); to every other model, Gemini 2.5 among them. The same through either service."""
    model = model or MODEL
    if maker(model) == "Anthropic" or _gpt_version(model) >= 6:
        return False
    version = re.search(r"gemini-(\d+(?:\.\d+)?)", model.lower())
    return not (maker(model) == "Google" and version and float(version.group(1)) >= 3)


def thinking_sent(model: str | None = None, service: str | None = None) -> str | None:
    """The thinking level a call sends (THINKING), under the service's name for it (thinking_parameter), or None when
    it sends none.
    Through LiteLLM, as `reasoning_effort`, only to the models LiteLLM documents it for: Google's Gemini 2.5 and later
    (https://docs.litellm.ai/docs/providers/gemini), and OpenAI's GPT-6 models (THINKING cites OpenAI's and LiteLLM's
    pages). Not to Anthropic's Claude models through LiteLLM: on Claude Opus 5.5 adaptive thinking is always on, and the
    model decides whether and how much to think, at the effort sent, or at its default, medium, when none is sent
    (https://platform.claude.com/docs/en/models/opus-5-5/whats-new-opus-5-5), and whether LiteLLM passes an effort
    setting on to it isn't shown yet (py helpers/check_effort.py; docs/running_on_nasa_laptop.md, "Checking that
    LiteLLM passes Claude's effort on"). Not to other models either, which might refuse a parameter they don't take.
    Through a maker's own API, as the maker's own setting (takes_thinking_cap says to which models): Anthropic's
    `output_config.effort`, OpenAI's `reasoning_effort`, Google's `thinking_config.thinking_level` (DIRECT_SERVICES
    cites each). Ask Sage's query takes no such parameter."""
    return None if THINKING == "model_default" or not takes_thinking_cap(model, service) else THINKING


def thinking_parameter(model: str | None = None, service: str | None = None) -> str:
    """The name the thinking level is sent under through this service (thinking_sent), for messages and the report."""
    service = service or SERVICE
    return DIRECT_SERVICES[service]["thinking"] if service in DIRECT_SERVICES else "reasoning_effort"


def takes_thinking_cap(model: str | None = None, service: str | None = None) -> bool:
    """Whether the thinking cap is sent to this model through this service, whatever `thinking` is (thinking_sent
    says where, and why). Through a maker's own API: to Anthropic's Claude models (effort: every current Claude model
    takes it, https://platform.claude.com/docs/en/build-with-claude/effort; an older one that doesn't refuses the test
    call, whose message says to give `--thinking model_default`), to OpenAI's GPT-6 models, and to Google's Gemini 3
    and later (thinkingLevel: "Recommended for Gemini 3 or later models", and "Use with earlier models results in an
    error": https://aistudio.google.com/api-reference/generate-content, read 2026-11-14)."""
    model, service = model or MODEL, service or SERVICE
    version = re.search(r"gemini-(\d+(?:\.\d+)?)", model.lower())
    gemini = float(version.group(1)) if version and maker(model) == "Google" else 0
    if service == "anthropic":
        return maker(model) == "Anthropic"
    if service in ("litellm", "openai") and _gpt_version(model) >= 6:
        return True
    if service == "google":
        return gemini >= 3
    return service == "litellm" and gemini >= 2.5


def model_label() -> str:
    """The model in words, for a report: "`claude-opus-5-5` through LiteLLM (answered as `…`)"."""
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


# ------------------------------ what each request records (llm_replies.py) ------

#: What the latest request in this thread sent and got back, for the test call's check (PaidCalls.start) and the
#: failed-call record (PaidCalls._record): settings_sent (every setting of the request but its prompt), request_bytes,
#: http_status, error_body (the service's error, up to ERROR_BODY_CHARS), usage (whole), finish_reason,
#: native_finish_reason (the model maker's own reason, when the service passes it on), served_as.
_last = threading.local()


#: How much of a service's error body the failed-call record keeps, in characters.
ERROR_BODY_CHARS = 4000


# ------------------------------ the makers' own APIs (llm_makers.py) -----------

#: The services that reach a model maker's own API directly, through the maker's official Python SDK: the key each
#: reads from .env, the SDK's package (requirements.txt; imported only when the service is used, _sdk), the maker
#: whose models it serves, and the names its request gives the answer limit and the thinking level. Each parameter
#: name is the maker's documented one:
#:   Anthropic (https://platform.claude.com/docs/en/build-with-claude/effort, read 2026-11-14): "Set
#:     `output_config.effort` on the request", values low, medium, high, xhigh, max; on Claude Opus 5.5 "Adaptive
#:     thinking is always on and can't be turned off, so effort is the primary control", and `medium` is its default,
#:     so `thinking` is never sent and the effort always is (unless the step's thinking is model_default).
#:     ANTHROPIC_API_KEY is the key the SDK reads first (the claude-api reference, "Authentication"); it is passed to
#:     the client explicitly, like the other two.
#:   OpenAI (https://developers.openai.com/api/docs/guides/latest-model; the Chat Completions reference,
#:     https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create, read
#:     2026-11-14): `reasoning_effort` and `max_completion_tokens`; GPT-6.1 Sol takes "`low`, `medium` (default),
#:     `high`, `xhigh`, and `max`" and Chat Completions (https://developers.openai.com/api/docs/models/gpt-6.1-sol,
#:     read 2026-11-14). OPENAI_API_KEY is the key the SDK reads (https://github.com/openai/openai-python, README).
#:   Google (google-genai's google/genai/types.py: GenerateContentConfig's `max_output_tokens` and `thinking_config`,
#:     ThinkingConfig's `thinking_level`, ThinkingLevel's values LOW, MEDIUM, HIGH; the REST reference,
#:     https://aistudio.google.com/api-reference/generate-content; both read 2026-11-14): Gemini 4 Argon takes the
#:     levels "low, medium, high", medium its default (https://aistudio.google.com/docs/models/gemini-4-argon).
#:     GEMINI_API_KEY is the name Google's docs use ("Set the GEMINI_API_KEY or GOOGLE_API_KEY. It will automatically
#:     be picked up by the client", and "if both are set, GOOGLE_API_KEY takes precedence":
#:     https://googleapis.github.io/python-genai/); the key is passed to the client explicitly, so a GOOGLE_API_KEY
#:     set elsewhere on the computer doesn't take its place.
#: No sampling parameter is sent where temperature_sent says not (TEMPERATURE cites the three makers).
DIRECT_SERVICES = {
    "anthropic": {"key": "ANTHROPIC_API_KEY", "package": "anthropic", "maker": "Anthropic",
                  "answer_limit": "max_tokens", "thinking": "output_config.effort"},
    "openai": {"key": "OPENAI_API_KEY", "package": "openai", "maker": "OpenAI",
               "answer_limit": "max_completion_tokens", "thinking": "reasoning_effort"},
    "google": {"key": "GEMINI_API_KEY", "package": "google-genai", "maker": "Google",
               "answer_limit": "max_output_tokens", "thinking": "thinking_config.thinking_level"},
}


# ------------------------------ a paid run's settings (llm_paid.py) ------------

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


# ------------------------------ who makes a model --------------------------------

#: Who makes a model, by a word of its family in the model's name. Ask Sage's names start with the host
#: ("google-claude-sonnet-5" is Anthropic's Claude served through Google), so the family word decides.
MAKERS = (("Anthropic", ("claude",)), ("OpenAI", ("gpt", "o1", "o3", "o4")), ("Google", ("gemini", "gemma")),
          ("Meta", ("llama",)), ("Mistral", ("mistral", "mixtral", "codestral")), ("Amazon", ("nova", "titan")),
          ("Cohere", ("command",)))


def maker(model: str) -> str | None:
    """The maker of a model, from its name ("google-claude-sonnet-5" -> "Anthropic"); None when the name says no
    family this table knows."""
    words = _name_words(model)
    for name, families in MAKERS:
        if any(w.startswith(f) for w in words for f in families):
            return name
    return None


def same_model_name(a: str, b: str) -> bool:
    """Whether two model names name the same model, spelling aside: the same words in the same order, in any case,
    whatever separates them ("claude-opus-5.5" and "claude-opus-5-5": LiteLLM lists the second and accepts both,
    MODEL). Not the same: another version ("claude-opus-5", "claude-opus-4-5"), another host's name for it
    ("google-claude-opus-5-5"), or a dated version ("claude-opus-5-5-20260101"). Says nothing about whether the
    service runs both names on one deployment."""
    return bool(a) and bool(b) and _name_words(a) == _name_words(b)


def model_name_key(model: str) -> str:
    """One key for every spelling of a model name, as same_model_name compares them: its words joined by "-"
    ("claude-opus-5.5" and "Claude-Opus-5-5" -> "claude-opus-5-5"); "" for an empty name."""
    return "-".join(_name_words(model))


def _name_words(model: str) -> list:
    """The words of a model name: cut at - _ . / : and spaces, lowercased, empty words dropped."""
    return [w for w in re.split(r"[-_./: ]+", (model or "").lower()) if w]



# ------------------------------ the parts, loaded last: they import their settings from here --------
from common.llm_errors import (
    BadReply as BadReply, WrongShape as WrongShape, ApiError as ApiError, RetryLater as RetryLater, RETRY_STATUSES
    as RETRY_STATUSES, _retry_after as _retry_after, BUDGET_WORDS as BUDGET_WORDS, ANSWER_BUDGET_WORDS as
    ANSWER_BUDGET_WORDS, ANSWER_BUDGET_NUMBERS as ANSWER_BUDGET_NUMBERS, ANSWER_BUDGET_CHARS as ANSWER_BUDGET_CHARS,
    BUDGET_NUMBERS as BUDGET_NUMBERS, budget_answer as budget_answer, budget_exhausted as budget_exhausted,
    BudgetExhausted as BudgetExhausted, BUDGET_GONE as BUDGET_GONE, budget_message as budget_message,
    stop_if_budget_gone as stop_if_budget_gone, ModelCallForbidden as ModelCallForbidden, FORBID_ENV as FORBID_ENV,
    _forbidden_from_env as _forbidden_from_env, FORBIDDEN as FORBIDDEN, forbid_model_calls as forbid_model_calls,
    allow_model_calls as allow_model_calls, _forbidden_message as _forbidden_message, stop_if_forbidden as
    stop_if_forbidden, CutOff as CutOff, Refused as Refused, NoAnswerInTime as NoAnswerInTime)
from common.llm_replies import (
    COMPLETE_REASONS as COMPLETE_REASONS, CUT_OFF_REASONS as CUT_OFF_REASONS, REFUSAL_REASONS as REFUSAL_REASONS,
    REFUSAL_WORDS as REFUSAL_WORDS, REPLY_KINDS as REPLY_KINDS, _FENCE as _FENCE, find_json as find_json,
    _open_at_end as _open_at_end, classify_reply as classify_reply, _raise_unless_complete as
    _raise_unless_complete, reasoning_tokens as reasoning_tokens, _http_reply as _http_reply, _count_tokens as
    _count_tokens, _note_request as _note_request, _finish_reply as _finish_reply, _with_reply as _with_reply,
    _with_call as _with_call)
from common.llm_asksage import (
    USER_BASE as USER_BASE, SERVER_BASE as SERVER_BASE, _token_cache as _token_cache, _asksage_token as
    _asksage_token, _asksage_models as _asksage_models, _ask_asksage as _ask_asksage)
from common.llm_litellm import (
    LITELLM_BASE as LITELLM_BASE, _litellm as _litellm, _litellm_said as _litellm_said, _litellm_error as
    _litellm_error, _litellm_models as _litellm_models, _messages as _messages, _post as _post, litellm_post as
    litellm_post, _ask_litellm as _ask_litellm, _chat_payload as _chat_payload, _read_chat_reply as _read_chat_reply)
from common.llm_makers import (
    _clients as _clients, _sdk as _sdk, _new_client as _new_client, _sdk_client as _sdk_client, _as_dict as
    _as_dict, _sdk_status as _sdk_status, _sdk_said as _sdk_said, _sdk_error as _sdk_error, _sdk_send as _sdk_send,
    _anthropic_params as _anthropic_params, _anthropic_usage as _anthropic_usage, _ask_anthropic as _ask_anthropic,
    _ask_openai as _ask_openai, _google_config as _google_config, _google_usage as _google_usage, _ask_google as
    _ask_google, _direct_models as _direct_models, _read_anthropic_reply as _read_anthropic_reply,
    _google_typed_config as _google_typed_config, _read_google_reply as _read_google_reply)
from common.llm_calls import (
    list_models as list_models, _ASK as _ASK, call_llm as call_llm, TEST_PROMPT as TEST_PROMPT, try_model as
    try_model, call_llm_json as call_llm_json, fence_safe as fence_safe)
from common.llm_paid import (
    OUTCOMES as OUTCOMES, RUN_WARNINGS as RUN_WARNINGS, EarlyStop as EarlyStop, _lower_thinking as _lower_thinking,
    cut_off_advice as cut_off_advice, advice as advice, failed_calls_file as failed_calls_file, _usage_counts as
    _usage_counts, _duration as _duration, PaidCalls as PaidCalls, Calls as Calls, paid_calls as paid_calls,
    run_parallel as run_parallel, warning_list as warning_list, numbered as numbered, show_warnings as
    show_warnings, Interrupted as Interrupted, confirm as confirm)
from common.llm_batch import (
    BATCH_API as BATCH_API, BATCH_DOCS as BATCH_DOCS, batch_refusal as batch_refusal, batch_note as batch_note, ask_batch as ask_batch, batch_state_file as
    batch_state_file, jobs_holding as jobs_holding)
