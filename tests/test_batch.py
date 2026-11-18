"""Batch processing (common/common_helpers/llm_batch.py, the setting batch of 060): a stage's model calls sent as batch
jobs to each maker's batch API, with the batch APIs faked (FakeBatch) and the single requests (the test call, a second
ask) through tests/test_model_calls.py's FakeSDK. For each maker (anthropic, openai, google):

    submit and poll     one job; its requests built as a single request's (same model, answer limit, thinking level,
                        no temperature); the run waits while the job runs, and says so
    results             out of order, matched by key; an errored and an expired request each a failed call, recorded
                        in the failed-call record, their records left out, asked again on the next run
    resume              a run stopped while it waits (Ctrl+C) leaves its job id in the cache folder; the next run
                        collects it: no new job, no test call, nothing paid again
    cache               the answers stored under the single request's cache keys: a rerun asks nothing
    tokens              each answer's token counts and served model, as a single request's
    early stop          most requests failed: the answers received are stored, nothing asked again, the step stops
    second ask          an answer that isn't JSON is asked once more as a single request
    refusals            Ask Sage and LiteLLM take no batch; a batch job the maker refuses stops the step, saying so
    paying twice        a run with batch false stops while an uncollected job of its recipe holds a prompt it asks;
                        a job's creation that timed out isn't sent again; an error while polling (but a 404 seen
                        twice) leaves the job uncollected
    Google's order      inlined responses without their keys are matched to the requests by order
    queue caps          jobs cut under a cap of input tokens (OpenAI, Google) or requests (Google), each sent
                        after the one before ended; Ctrl+C between them, then a rerun, sends no prompt twice;
                        a job refused for the queue (at creation or after) is sent again; other runs' open
                        jobs count against the cap
    answer limits       a job sent at another answer limit is collected; its cut-offs are kept at its own limit
"""
import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest import mock

import support                                    # noqa: F401  (the repository on the import path)
import test_model_calls as tmc
from common import extraction, llm, report
from common import llm_batch
from common.stop import Stop

SERVICES = ("anthropic", "openai", "google")
ANSWER = '{"triples": [], "describes_class": "Instrument"}'


def _prompt_of(service: str, request) -> str:
    """The prompt's words in one batch request, as the fake receives it."""
    if service == "anthropic":
        params = request["params"]
        return "".join(b["text"] for b in params.get("system", [])) + "".join(m["content"] for m in params["messages"])
    if service == "openai":
        return "".join(m["content"] if isinstance(m["content"], str) else m["content"][0]["text"]
                       for m in request["body"]["messages"])
    return request["contents"]


class GoogleReply:
    """A GenerateContentResponse as the SDK gives it: model_dump and .text."""

    def __init__(self, body, text):
        self.body, self.text = body, text

    def model_dump(self, mode=None):
        return json.loads(json.dumps(self.body))


class FakeBatch:
    """One maker's batch API: records each job's requests, says "running" for `running` polls, then "ended", and
    answers each request by what the test set for the record its prompt names (#r00#): "ok", "cut", "bad" (not
    JSON), "errored", "expired". Results come in reverse order."""

    def __init__(self, service: str, running: int = 2):
        self.service, self.running = service, running
        self.jobs, self.polls, self.outcome, self.refuse = {}, 0, {}, None

    def _id(self):
        return {"anthropic": "msgbatch_", "openai": "batch_", "google": "batches/"}[self.service] + str(len(self.jobs) + 1)

    def _what(self, request) -> str:
        prompt = _prompt_of(self.service, request)
        return next((v for k, v in self.outcome.items() if f"#{k}#" in prompt), "ok")

    def _key(self, request):
        return request["metadata"]["key"] if self.service == "google" else request["custom_id"]

    def create(self, requests):
        if self.refuse:
            raise self.refuse
        job_id = self._id()
        self.jobs[job_id] = list(requests)
        return job_id

    def ended(self) -> bool:
        self.polls += 1
        return self.polls > self.running

    def results(self, job_id):
        out = []
        for r in reversed(self.jobs[job_id]):
            out.append((self._key(r), self._what(r)))
        return out


def anthropic_client(fake: FakeBatch):
    def result(cid, what):
        if what in ("errored", "expired"):
            return {"custom_id": cid, "result": {"type": what, **({"error": {"type": "error", "error": {
                "type": "invalid_request_error", "message": "stand-in: bad request"}}} if what == "errored" else {})}}
        text = '{"triples": [{"subj' if what == "cut" else "no JSON here" if what == "bad" else ANSWER
        message = {**tmc.ANTHROPIC_REPLY, "content": [{"type": "text", "text": text}],
                   "stop_reason": "max_tokens" if what == "cut" else "end_turn"}
        return {"custom_id": cid, "result": {"type": "succeeded", "message": message}}

    def retrieve(job_id):
        done = fake.ended()
        return {"id": job_id, "processing_status": "ended" if done else "in_progress",
                "request_counts": {"processing": 0 if done else len(fake.jobs[job_id]), "succeeded": 0, "errored": 0,
                                   "canceled": 0, "expired": 0}}
    batches = NS(create=lambda requests: NS(id=fake.create(requests)), retrieve=retrieve,
                 results=lambda job_id: iter([result(*x) for x in fake.results(job_id)]))
    return NS(messages=NS(batches=batches))


def openai_client(fake: FakeBatch):
    files, made = {}, {}

    def upload(file, purpose):
        assert purpose == "batch"
        name, data = file
        files[f"file-in-{len(files)}"] = [json.loads(line) for line in data.decode("utf-8").splitlines()]
        return NS(id=f"file-in-{len(files) - 1}")

    def create(input_file_id, endpoint, completion_window, output_expires_after):
        made["args"] = (endpoint, completion_window, output_expires_after)
        return NS(id=fake.create(files[input_file_id]))

    def retrieve(job_id):
        done = fake.ended()
        return {"id": job_id, "status": "completed" if done else "in_progress",
                "request_counts": {"completed": 0, "failed": 0, "total": len(fake.jobs[job_id])},
                "output_file_id": f"out-{job_id}" if done else None, "error_file_id": f"err-{job_id}" if done else None}

    def content(file_id):
        job_id = file_id.split("-", 1)[1]
        lines = []
        for cid, what in fake.results(job_id):
            if what in ("errored", "expired"):
                if file_id.startswith("err-"):
                    code = "batch_expired" if what == "expired" else "invalid_request"
                    lines.append({"custom_id": cid, "response": None, "error": {"code": code, "message": "stand-in"}})
                continue
            if file_id.startswith("out-"):
                text = '{"tri' if what == "cut" else "no JSON here" if what == "bad" else ANSWER
                body = {**tmc.OPENAI_REPLY, "choices": [{"finish_reason": "length" if what == "cut" else "stop",
                                                          "message": {"content": text}}]}
                lines.append({"custom_id": cid, "response": {"status_code": 200, "body": body}, "error": None})
        return NS(text="\n".join(json.dumps(x) for x in lines))
    client = NS(files=NS(create=upload, content=content), batches=NS(create=create, retrieve=retrieve))
    client.made = made
    return client


def google_client(fake: FakeBatch):
    made = {}

    def create(model, src, config):
        made["model"] = model
        return NS(name=fake.create([dict(r) for r in src]))

    def get(name):
        done = fake.ended()
        if not done:
            return NS(state=NS(value="JOB_STATE_RUNNING"), completion_stats=None, dest=None, error=None)
        if fake.outcome.get("*") == "expired":
            return NS(state=NS(value="JOB_STATE_EXPIRED"), completion_stats=None, dest=None, error=None)
        responses = []
        if getattr(fake, "no_keys", False):                     # in request order, no metadata (Google's documented order)
            for r in fake.jobs[name]:
                responses.append(NS(metadata=None, response=GoogleReply(
                    {**tmc.GOOGLE_REPLY[0], "candidates": [{"finish_reason": "STOP"}]},
                    ANSWER.replace("Instrument", r["contents"].rsplit("#", 2)[1])), error=None))
            return NS(state=NS(value="JOB_STATE_SUCCEEDED"), completion_stats=None,
                      dest=NS(inlined_responses=responses), error=None)
        for cid, what in fake.results(name):
            if what in ("errored", "expired"):
                responses.append(NS(metadata={"key": cid}, response=None,
                                    error=NS(code=400 if what == "errored" else 4, message=f"stand-in {what}")))
                continue
            text = '{"tri' if what == "cut" else "no JSON here" if what == "bad" else ANSWER
            body = {**tmc.GOOGLE_REPLY[0], "candidates": [{"finish_reason": "MAX_TOKENS" if what == "cut" else "STOP"}]}
            responses.append(NS(metadata={"key": cid}, response=GoogleReply(body, text), error=None))
        return NS(state=NS(value="JOB_STATE_SUCCEEDED"), completion_stats=None,
                  dest=NS(inlined_responses=responses), error=None)
    client = NS(batches=NS(create=create, get=get))
    client.made = made
    return client


SYNC_TEST_REPLY = {"anthropic": tmc.ANTHROPIC_REPLY, "openai": tmc.OPENAI_REPLY, "google": tmc.GOOGLE_REPLY}
#: Each answer's token counts in OpenAI's shape (tests/test_model_calls.py's replies): input not from the cache,
#: read from the cache, written to the cache, received, thinking.
TOKENS = {"anthropic": (10, 100, 20, 50, 40), "openai": (20, 10, 0, 25, 20), "google": (25, 15, 0, 65, 60)}


class Batch(unittest.TestCase):

    calls = tmc.Guards.calls
    entries = tmc.Guards.entries

    def setUp(self):
        tmc.DirectServices.setUp(self)
        self.sdk.modules["google.genai.types"].InlinedRequest = type("InlinedRequest", (dict,), {})
        self.fakes, self.clients, self.sleeps = {}, {}, []
        self.more = [mock.patch.object(llm_batch, "_sdk_client", self._client),
                     mock.patch.object(llm.time, "sleep", self.sleeps.append)]
        for p in self.more:
            p.start()

    def tearDown(self):
        for p in reversed(self.more):
            p.stop()
        llm.BATCH = False
        llm.BATCH_JOBS.clear()
        tmc.DirectServices.tearDown(self)

    def _client(self, service, timeout=None):
        if service not in self.clients:
            make = {"anthropic": anthropic_client, "openai": openai_client, "google": google_client}[service]
            self.clients[service] = make(self.fakes[service])
        return self.clients[service]

    def run_batch(self, service, ids, outcome=None, test_call=True, running=2, cache_until=None):
        """One 060-like run with batch true: ids' records, one text piece each; the test call answered by FakeSDK."""
        fake = self.fakes.setdefault(service, FakeBatch(service, running))
        fake.outcome = outcome or {}
        calls = self.calls(service=service, model=tmc.BASELINE[service], thinking="high", batch=True)
        if test_call:
            self.sdk.replies.append(SYNC_TEST_REPLY[service])
        items = [{"id": i, "pieces": ["text"]} for i in ids]
        replies = extraction.ask_model(items, lambda item, piece: f"RULES\n----- BEGIN RECORD -----\n#{item['id']}#",
                                       calls, 4, "extract", "060 will extract", "extracting", cache_until=cache_until)
        return calls, replies

    def state(self, service="anthropic"):
        return json.loads((self.tmp / "050_annotate" / "cache" / "extract.batch_jobs.json").read_text(encoding="utf-8"))

    def cached(self):
        return json.loads((self.tmp / "050_annotate" / "cache" / "extract.json").read_text(encoding="utf-8"))

    # ---------------------------------------------------------------- submit, poll, results

    def test_submit_poll_results_with_an_errored_and_an_expired_request(self):
        for service in SERVICES:
            with self.subTest(service=service):
                self.setUp_again()
                outcome = {"r02": "errored", "r03": "expired"}
                calls, replies = self.run_batch(service, ["r00", "r01", "r02", "r03"], outcome)
                fake = self.fakes[service]
                self.assertEqual(len(fake.jobs), 1)                             # one job, four requests
                (job_id, requests), = fake.jobs.items()
                self.assertEqual(len(requests), 4)
                self.assertGreater(fake.polls, 2)                               # polled while it ran
                self.assertEqual(self.sleeps.count(llm.BATCH_POLL_SECONDS), 2)
                # results came in reverse order and were matched by key
                self.assertEqual(sorted(replies.of), ["r00", "r01"])
                self.assertEqual(replies.of["r00"], [json.loads(ANSWER)])
                self.assertEqual(sorted(replies.failed), ["r02", "r03"])
                self.assertEqual({replies.kinds[r] for r in ("r02", "r03")}, {"service_error"})
                self.assertIn(job_id, replies.failed["r02"])
                # the failed-call record names the job
                entries = self.entries()
                self.assertEqual(len(entries), 2)
                self.assertTrue(all(e["outcome"] == "failed" for e in entries))
                self.assertEqual({e["batch_job"] for e in entries}, {job_id})
                # only the answers are cached; a rerun asks the two failed ones again
                self.assertEqual(len(self.cached()), 2)
                self.assertEqual(replies.calls, 2)
                # the test call was a single request, before the job
                self.assertEqual([s for s, _ in self.sdk.requests], [service])
                self.assertEqual(calls.paid.test_calls, 1)
                # tokens: the test call's and the two answers' counts; the failed requests carry none
                i, r, w, o, t = TOKENS[service]
                self.assertEqual(llm.REQUESTS, {"sent": 1 + 4, "input_tokens": 3 * i, "cache_read_tokens": 3 * r,
                                                "cache_write_tokens": 3 * w, "output_tokens": 3 * o,
                                                "reasoning_tokens": 3 * t})
                self.assertTrue(llm.SERVED)
                # the job is kept, collected, with its counts; the run's record and report say so
                (job,) = self.state()["jobs"]
                self.assertEqual((job["id"], job["answered"], job["failed"]), (job_id, 2, 2))
                self.assertTrue(job["collected"])
                self.assertEqual(llm.BATCH_JOBS[0]["how"], "submitted")
                self.assertEqual(llm.describe()["batch_jobs"][0]["id"], job_id)
                section = "\n".join(report.model_calls([("extract", replies.calls, replies.reused)], 1, "m"))
                self.assertIn(job_id, section)
                self.assertIn(llm.BATCH_API[service], section)

    def setUp_again(self):
        """A fresh run: a new temporary folder, fresh fakes and counts (each subtest is its own run)."""
        self.tearDown()
        self.setUp()

    def test_requests_are_the_single_requests(self):
        """Each batch request carries what the single request sends: the model, the answer limit and the thinking
        level under the maker's names, no temperature; the whole prompt."""
        for service in SERVICES:
            with self.subTest(service=service):
                self.setUp_again()
                self.run_batch(service, ["r00"], cache_until=extraction.BEGIN_LINE)
                (request,), = self.fakes[service].jobs.values()
                prompt = "RULES\n----- BEGIN RECORD -----\n#r00#"
                self.assertEqual(_prompt_of(service, request), prompt)
                if service == "anthropic":
                    params = request["params"]
                    single = llm._anthropic_params(prompt, "claude-opus-5-5", extraction.BEGIN_LINE)
                    self.assertEqual(params["system"][0]["cache_control"], {"type": "ephemeral", "ttl": "1h"})
                    params["system"][0]["cache_control"] = single["system"][0]["cache_control"]
                    self.assertEqual(params, single)                            # otherwise the same request
                    self.assertEqual(params["output_config"], {"effort": "high"})
                    self.assertEqual(request["custom_id"], next(iter(self.cached())))
                elif service == "openai":
                    self.assertEqual(request["body"], llm._chat_payload(prompt, "gpt-6.1-sol", extraction.BEGIN_LINE,
                                                                        "openai"))
                    self.assertEqual(request["body"]["reasoning_effort"], "high")
                    self.assertEqual((request["method"], request["url"]), ("POST", "/v1/chat/completions"))
                    self.assertEqual(self.clients["openai"].made["args"],
                                     ("/v1/chat/completions", "24h",
                                      {"anchor": "created_at", "seconds": 7 * 24 * 3600}))
                else:
                    self.assertEqual(dict(request["config"]), {"max_output_tokens": llm.MAX_ANSWER_TOKENS,
                                                               "thinking_config": {"thinking_level": "HIGH"}})
                    self.assertEqual(type(request["config"]["thinking_config"]).__name__, "ThinkingConfig")
                    self.assertEqual(self.clients["google"].made["model"], "gemini-4-argon")
                for body in (request.get("params"), request.get("body"), request.get("config")):
                    self.assertFalse({"temperature", "top_p", "top_k"} & set(body or {}))

    # ---------------------------------------------------------------- resume, cache

    def test_resume_from_the_saved_job_id(self):
        for service in SERVICES:
            with self.subTest(service=service):
                self.setUp_again()
                # first run: Ctrl+C while it waits
                with mock.patch.object(llm.time, "sleep", mock.Mock(side_effect=KeyboardInterrupt)):
                    with self.assertRaises(llm.Interrupted) as caught:
                        self.run_batch(service, ["r00", "r01"])
                (job_id,) = self.fakes[service].jobs
                self.assertIn(job_id, str(caught.exception))
                self.assertIn("extract.batch_jobs.json", str(caught.exception))
                (job,) = self.state()["jobs"]
                self.assertIsNone(job["collected"])
                # second run: collects the job; no new job, no test call, no question
                self.sdk.requests.clear()
                calls, replies = self.run_batch(service, ["r00", "r01"], test_call=False)
                self.assertEqual(list(self.fakes[service].jobs), [job_id])
                self.assertEqual(self.sdk.requests, [])
                self.assertFalse(calls.paid.started)
                self.assertEqual(sorted(replies.of), ["r00", "r01"])
                self.assertEqual(llm.BATCH_JOBS[0]["how"], "resumed")
                self.assertEqual(llm.REQUESTS["sent"], 0)                       # counted by the run that sent them
                self.assertEqual(llm.REQUESTS["output_tokens"], 2 * TOKENS[service][3])
                self.assertTrue(self.state()["jobs"][0]["collected"])
                # near-miss: a job of another recipe (thinking low) is left alone, with a warning
                self.state_with_other_recipe()

    def state_with_other_recipe(self):
        path = self.tmp / "050_annotate" / "cache" / "extract.batch_jobs.json"
        state = self.state()
        state["jobs"][0].update(collected=None, identity={**state["jobs"][0]["identity"], "cache_identity": "x"})
        path.write_text(json.dumps(state), encoding="utf-8")
        service = state["jobs"][0]["service"]
        jobs_before = len(self.fakes[service].jobs)
        self.run_batch(service, ["r09"])
        self.assertEqual(len(self.fakes[service].jobs), jobs_before + 1)          # r09 sent in a new job
        self.assertTrue(any(state["jobs"][0]["id"] in w for w in llm.RUN_WARNINGS))

    def test_a_rerun_reuses_the_cache(self):
        for service in SERVICES:
            with self.subTest(service=service):
                self.setUp_again()
                self.run_batch(service, ["r00", "r01"])
                self.sdk.requests.clear()
                calls, replies = self.run_batch(service, ["r00", "r01"], test_call=False)
                self.assertEqual((replies.reused, replies.calls), (2, 0))
                self.assertEqual(len(self.fakes[service].jobs), 1)               # no new job
                self.assertEqual(self.sdk.requests, [])
                # and the single-request path reuses the batch's answers: the same cache keys
                llm.BATCH = False
                calls = self.calls(service=service, model=tmc.BASELINE[service], thinking="high")
                items = [{"id": i, "pieces": ["text"]} for i in ("r00", "r01")]
                replies = extraction.ask_model(items, lambda item, piece: f"RULES\n----- BEGIN RECORD -----\n"
                                               f"#{item['id']}#", calls, 4, "extract", "060", "extracting")
                self.assertEqual(replies.reused, 2)
                self.assertEqual(self.sdk.requests, [])

    # ---------------------------------------------------------------- failures

    def test_cut_off_kept_and_second_ask_as_a_single_request(self):
        for service in SERVICES:
            with self.subTest(service=service):
                self.setUp_again()
                fix = {"anthropic": {**tmc.ANTHROPIC_REPLY, "content": [{"type": "text", "text": ANSWER}]},
                       "openai": {**tmc.OPENAI_REPLY, "choices": [{"finish_reason": "stop",
                                                                   "message": {"content": ANSWER}}]},
                       "google": (tmc.GOOGLE_REPLY[0], ANSWER)}[service]
                self.sdk.replies.append(SYNC_TEST_REPLY[service])
                self.sdk.replies.append(fix)                                    # the second ask's answer
                calls, replies = self.run_batch(service, ["r00", "r01", "r02"], {"r01": "cut", "r02": "bad"},
                                                test_call=False)
                self.assertEqual(sorted(replies.of), ["r00", "r02"])            # r02 fixed by the second ask
                self.assertEqual(replies.kinds, {"r01": "cut_off"})
                self.assertEqual(len(self.sdk.requests), 2)                     # the test call and the second ask
                self.assertIn("Your last reply was not a valid JSON object", str(self.sdk.requests[1][1]))
                self.assertEqual(llm.REASKS["fixed"], 1)
                stored = self.cached()
                self.assertEqual(sum(1 for v in stored.values() if "_pipeline_cut_off" in v), 1)

    def test_early_stop_when_most_requests_fail(self):
        for service in SERVICES:
            with self.subTest(service=service):
                self.setUp_again()
                with self.assertRaises(llm.EarlyStop) as caught:
                    self.run_batch(service, ["r00", "r01", "r02", "r03", "r04"],
                                   {"r01": "errored", "r02": "errored", "r03": "errored", "r04": "bad"})
                message = str(caught.exception)
                self.assertIn("3 of the 5 requests", message)
                self.assertIn(next(iter(self.fakes[service].jobs)), message)
                self.assertEqual(len(self.cached()), 1)                         # r00's answer is kept
                self.assertEqual(len(self.sdk.requests), 1)                     # the test call only: no second ask
                self.assertTrue(self.state()["jobs"][0]["collected"])
        # near-miss: 2 of 5 failed is no early stop
        self.setUp_again()
        _, replies = self.run_batch("anthropic", ["r00", "r01", "r02", "r03", "r04"],
                                    {"r01": "errored", "r02": "errored"})
        self.assertEqual(len(replies.of), 3)

    def test_google_job_that_expired_whole(self):
        _, replies = self.run_batch("google", ["r00", "r01"], {"*": "expired"})
        self.assertEqual(sorted(replies.failed), ["r00", "r01"])
        self.assertIn("JOB_STATE_EXPIRED", replies.failed["r00"])

    def test_service_without_batch_is_refused(self):
        for service in ("litellm", "asksage"):
            with self.subTest(service=service), self.assertRaises(Stop) as caught:
                self.calls(service=service, model="gemini-2.5-pro", batch=True)
            self.assertIn("--batch false", str(caught.exception))
        with self.assertRaises(Stop):                                           # not a true/false value
            self.calls(service="google", model="gemini-4-argon", batch="yes")
        self.calls(service="litellm", model="gemini-2.5-pro", batch=False)      # near-miss: false is fine
        self.assertFalse(llm.BATCH)

    def test_a_refused_batch_job_stops_the_step(self):
        fake = self.fakes.setdefault("google", FakeBatch("google"))
        fake.refuse = self.sdk.GoogleError(400, "FAILED_PRECONDITION. Precondition check failed.")
        with self.assertRaises(SystemExit) as caught:
            self.run_batch("google", ["r00"])
        message = str(caught.exception)
        self.assertIn("refused the batch job", message)
        self.assertIn("--batch false", message)
        self.assertNotIn("jobs", self.state_or_empty())
        # a rate limit is tried again, then the job is sent
        self.setUp_again()
        fake = self.fakes.setdefault("anthropic", FakeBatch("anthropic"))
        errors = [self.sdk.APIStatusError("overloaded", 529)]
        real = fake.create

        def create(requests):
            if errors:
                raise errors.pop()
            return real(requests)
        fake.create = create
        _, replies = self.run_batch("anthropic", ["r00"])
        self.assertEqual(list(replies.of), ["r00"])
        self.assertIn(llm_batch.BATCH_CREATE_WAIT, self.sleeps)

    # ---------------------------------------------------------------- never paying twice

    def stop_while_waiting(self, service, ids):
        with mock.patch.object(llm.time, "sleep", mock.Mock(side_effect=KeyboardInterrupt)):
            with self.assertRaises(llm.Interrupted):
                self.run_batch(service, ids)
        llm.BATCH_JOBS.clear()

    def single_run(self, service, ids):
        llm.BATCH = False
        calls = self.calls(service=service, model=tmc.BASELINE[service], thinking="high")
        items = [{"id": i, "pieces": ["text"]} for i in ids]
        return extraction.ask_model(items, lambda item, piece: f"RULES\n----- BEGIN RECORD -----\n#{item['id']}#",
                                    calls, 4, "extract", "060", "extracting")

    def test_single_requests_stop_while_a_job_holds_their_prompts(self):
        self.stop_while_waiting("anthropic", ["r00", "r01"])
        (job_id,) = self.fakes["anthropic"].jobs
        self.sdk.requests.clear()
        with self.assertRaises(SystemExit) as caught:
            self.single_run("anthropic", ["r01", "r02"])
        message = str(caught.exception)
        for words in (job_id, "1 of these prompts", "--batch true", "pay for them twice"):
            self.assertIn(words, message)
        self.assertEqual(self.sdk.requests, [])                                 # nothing sent, not even the test call
        # near-misses: prompts no job holds are asked; a job of another recipe doesn't stop the run
        self.sdk.replies += [SYNC_TEST_REPLY["anthropic"],
                             {**tmc.ANTHROPIC_REPLY, "content": [{"type": "text", "text": ANSWER}]}]
        replies = self.single_run("anthropic", ["r02"])
        self.assertEqual((list(replies.of), len(self.sdk.requests)), (["r02"], 2))   # the test call and r02
        path = self.tmp / "050_annotate" / "cache" / "extract.batch_jobs.json"
        state = self.state()
        self.assertEqual(llm_batch.jobs_holding(path.parent, "extract", {"a key no job holds"}), [])
        # a job is found by the cache keys it holds, which name the model, thinking level and repeat: a job sent at
        # another answer limit still holds this run's prompts
        state["jobs"][0]["identity"] = {**state["jobs"][0]["identity"], "max_answer_tokens": 32000}
        path.write_text(json.dumps(state), encoding="utf-8")
        held = llm_batch.jobs_holding(path.parent, "extract", {state["jobs"][0]["keys"][0]})
        self.assertEqual([(j["id"], j["held"]) for j in held], [(job_id, 1)])

    def test_a_job_sent_at_another_answer_limit_is_collected(self):
        """A job sent at limit A and collected by a run at limit B: no new job, nothing paid again; a cut-off in it is
        kept with limit A, so the cache asks it again at B but not at A; a cut-off held by the job for a prompt this
        run doesn't ask is kept as a cut-off too."""
        from common.cache import Cache
        with mock.patch.object(llm, "MAX_ANSWER_TOKENS", 32000):
            self.stop_while_waiting("anthropic", ["r00", "r01", "r02"])
        (job_id,) = self.fakes["anthropic"].jobs
        self.assertEqual(self.state()["jobs"][0]["identity"]["max_answer_tokens"], 32000)
        self.sdk.requests.clear()
        _, replies = self.run_batch("anthropic", ["r00", "r01"], {"r01": "cut", "r02": "cut"}, test_call=False)
        self.assertEqual(list(self.fakes["anthropic"].jobs), [job_id])           # collected, not sent again
        self.assertEqual(self.sdk.requests, [])
        self.assertEqual((list(replies.of), replies.kinds), (["r00"], {"r01": "cut_off"}))
        for words in (job_id, "answer limit 32000", f"this run's limit is {llm.MAX_ANSWER_TOKENS}"):
            self.assertIn(words, replies.failed["r01"])
        markers = {k: v["_pipeline_cut_off"] for k, v in self.cached().items() if "_pipeline_cut_off" in v}
        self.assertEqual(len(markers), 2)                                       # r01 and r02, not asked by this run
        self.assertEqual({m["max_answer_tokens"] for m in markers.values()}, {32000})
        cache = Cache(self.tmp / "050_annotate" / "cache", "extract")
        self.assertTrue(all(cache.cut_off(k) is None for k in markers))          # asked again at this run's limit
        with mock.patch.object(llm, "MAX_ANSWER_TOKENS", 32000):                # near-miss: at the job's limit, not
            self.assertTrue(all(cache.cut_off(k) for k in markers))
        # near-miss: a cut-off at this run's own limit carries no note about another limit
        self.setUp_again()
        _, replies = self.run_batch("anthropic", ["r00", "r01"], {"r01": "cut"})
        self.assertNotIn("answer limit", replies.failed["r01"])
        (marker,) = [v["_pipeline_cut_off"] for v in self.cached().values() if "_pipeline_cut_off" in v]
        self.assertEqual(marker["max_answer_tokens"], llm.MAX_ANSWER_TOKENS)

    def test_a_create_that_timed_out_is_not_sent_again(self):
        from common.llm_errors import NoAnswerInTime
        read_error = type("ReadError", (Exception,), {})                       # httpx's, which _sdk_error doesn't place
        for raised in (NoAnswerInTime("APITimeoutError: timed out"), RuntimeError("no connection"),
                       read_error("connection closed while reading")):
            with self.subTest(raised=type(raised).__name__):
                self.setUp_again()
                fake = self.fakes.setdefault("anthropic", FakeBatch("anthropic"))
                tries = []

                def create(requests, raised=raised):
                    tries.append(1)
                    raise raised
                fake.create = create
                with self.assertRaises(SystemExit) as caught:
                    self.run_batch("anthropic", ["r00"])
                self.assertEqual(tries, [1])                                    # one try only
                self.assertNotIn(llm_batch.BATCH_CREATE_WAIT, self.sleeps)
                self.assertIn("whether the job was made isn't known", str(caught.exception))

    def test_an_error_while_polling_leaves_the_job_uncollected(self):
        from common.llm_errors import ApiError
        real = llm_batch._poll
        for errors, given_up in (([ApiError("HTTP 401: invalid x-api-key")], False),
                                 ([ApiError("HTTP 404: not found"), ApiError("HTTP 404: not found")], True)):
            with self.subTest(errors=[str(e) for e in errors]):
                self.setUp_again()
                queue = list(errors)

                def poll(service, job_id):
                    if queue:
                        raise queue.pop(0)
                    return real(service, job_id)
                with mock.patch.object(llm_batch, "_poll", poll), self.assertRaises(SystemExit) as caught:
                    self.run_batch("anthropic", ["r00"])
                (job,) = self.state()["jobs"]
                self.assertEqual(bool(job["collected"]), given_up)
                self.assertIn("given up" if given_up else "stays uncollected", str(caught.exception))
        # near-miss: one 404 and then the job is found again: it is collected as usual
        self.setUp_again()
        queue = [ApiError("HTTP 404: not found")]

        def poll_once(service, job_id):
            if queue:
                raise queue.pop(0)
            return real(service, job_id)
        with mock.patch.object(llm_batch, "_poll", poll_once):
            _, replies = self.run_batch("anthropic", ["r00"])
        self.assertEqual(list(replies.of), ["r00"])

    def test_google_answers_without_keys_matched_by_order(self):
        fake = self.fakes.setdefault("google", FakeBatch("google"))
        fake.no_keys = True
        _, replies = self.run_batch("google", ["r00", "r01", "r02"])
        self.assertEqual({r: replies.of[r][0]["describes_class"] for r in replies.of},
                         {"r00": "r00", "r01": "r01", "r02": "r02"})       # each answer under its own request
        # near-misses: a count that differs, or some keys present, is never matched by order
        item = NS(metadata=None)
        self.assertEqual(llm_batch._google_keys([item, item], ["a", "b", "c"], "j"), ["None", "None"])
        self.assertEqual(llm_batch._google_keys([NS(metadata={"key": "b"}), item], ["a", "b"], "j"), ["b", "None"])

    def state_or_empty(self):
        path = self.tmp / "050_annotate" / "cache" / "extract.batch_jobs.json"
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}

    def test_jobs_cut_at_the_makers_limits(self):
        with mock.patch.dict(llm.BATCH_LIMITS, {"openai": (2, 10_000_000)}):
            _, replies = self.run_batch("openai", ["r00", "r01", "r02"])
        self.assertEqual([len(r) for r in self.fakes["openai"].jobs.values()], [2, 1])
        self.assertEqual(len(replies.of), 3)
        self.assertEqual(len(self.state()["jobs"]), 2)

    # ---------------------------------------------------------------- the makers' batch queue caps

    def watch_creates(self, service):
        """The fake's poll count at each job's creation, so a test can see each job sent after the one before ended
        (the fake ends every job once it has been polled more than `running` times)."""
        fake = self.fakes.setdefault(service, FakeBatch(service))
        at, real = [], fake.create

        def create(requests):
            at.append(fake.polls)
            return real(requests)
        fake.create = create
        return fake, at

    def test_jobs_cut_under_the_token_cap_and_sent_one_after_another(self):
        """OpenAI's cap on the input tokens queued per model: 5 prompts of about 33 estimated tokens each under a cap
        of 70 go as 3 jobs (2, 2, 1), each sent after the one before ended; every prompt answered once."""
        prompt = "RULES\n----- BEGIN RECORD -----\n#r00#"
        self.assertEqual(llm_batch.estimated_tokens(prompt), -(-len(prompt) // 3) + 20)
        fake, at = self.watch_creates("openai")
        with mock.patch.dict(llm.BATCH_QUEUE_TOKENS, {"openai": {"gpt-6.1-sol": 70}}):
            _, replies = self.run_batch("openai", ["r00", "r01", "r02", "r03", "r04"])
        self.assertEqual([len(r) for r in fake.jobs.values()], [2, 2, 1])
        self.assertEqual(at[0], 0)
        self.assertTrue(all(b > a for a, b in zip(at, at[1:])))          # each job sent after a later poll
        self.assertEqual(len(replies.of), 5)
        self.assertEqual(llm.REQUESTS["sent"], 1 + 5)                     # the test call and each prompt once
        self.assertTrue(all(j.get("input_tokens") for j in self.state()["jobs"]))
        # near-misses: a model without a cap, and a cap through another service, send every job at once
        for service, caps in (("openai", {"openai": {"gpt-6-luna": 70}}), ("anthropic", {"openai": {"claude-opus-5-5": 70}})):
            with self.subTest(service=service):
                self.setUp_again()
                fake, at = self.watch_creates(service)
                with mock.patch.dict(llm.BATCH_QUEUE_TOKENS, caps):
                    self.run_batch(service, ["r00", "r01", "r02"])
                self.assertEqual([len(r) for r in fake.jobs.values()], [3])

    def test_jobs_cut_under_the_requests_cap(self):
        """Google's concurrent batch requests: with a cap of 2, 5 prompts go as jobs of 2, 2 and 1, one after
        another."""
        fake, at = self.watch_creates("google")
        with mock.patch.dict(llm.BATCH_QUEUE_REQUESTS, {"google": 2}):
            _, replies = self.run_batch("google", ["r00", "r01", "r02", "r03", "r04"])
        self.assertEqual([len(r) for r in fake.jobs.values()], [2, 2, 1])
        self.assertTrue(all(b > a for a, b in zip(at, at[1:])))
        self.assertEqual(len(replies.of), 5)

    def test_stopped_while_jobs_wait_for_the_queue(self):
        """Ctrl+C after the first of 3 jobs was sent: the message says how many requests weren't sent; the next run
        collects the first job and sends the rest, so no prompt is sent twice."""
        with mock.patch.dict(llm.BATCH_QUEUE_TOKENS, {"openai": {"gpt-6.1-sol": 70}}):
            with mock.patch.object(llm.time, "sleep", mock.Mock(side_effect=KeyboardInterrupt)):
                with self.assertRaises(llm.Interrupted) as caught:
                    self.run_batch("openai", ["r00", "r01", "r02", "r03", "r04"])
            self.assertIn("3 request(s) waited for room", str(caught.exception))
            self.assertEqual(len(self.state()["jobs"]), 1)
            llm.BATCH_JOBS.clear()
            _, replies = self.run_batch("openai", ["r00", "r01", "r02", "r03", "r04"])
        sent = [r["custom_id"] for job in self.fakes["openai"].jobs.values() for r in job]
        self.assertEqual(len(sent), 5)
        self.assertEqual(len(set(sent)), 5)                               # each prompt in one job only
        self.assertEqual(len(replies.of), 5)
        self.assertEqual([j["how"] for j in llm.BATCH_JOBS], ["resumed", "submitted", "submitted"])

    def test_a_job_refused_for_the_queue_is_sent_again(self):
        """The maker refuses a job for its queue: when creating it (no job made) or after making it (OpenAI: status
        failed, token_limit_exceeded). Either way the requests are sent again once the queue has room, nothing is
        lost or counted twice."""
        fake = self.fakes.setdefault("openai", FakeBatch("openai"))
        refusals, real = [self.sdk.APIStatusError("token_limit_exceeded: Enqueued token limit reached", 400)], fake.create

        def create(requests):
            if refusals:
                raise refusals.pop()
            return real(requests)
        fake.create = create
        _, replies = self.run_batch("openai", ["r00", "r01"])
        self.assertEqual((len(fake.jobs), len(replies.of)), (1, 2))
        self.assertIn(llm.BATCH_POLL_SECONDS, self.sleeps)
        # after making it: the first job fails for the queue; its requests go again in a second job
        self.setUp_again()
        real_poll, failed = llm_batch._poll, []

        def poll(service, job_id):
            if job_id.endswith("_1") and not failed:
                failed.append(job_id)
                return {"ended": True, "state": "failed", "counts": "",
                        "error": "token_limit_exceeded: Enqueued token limit reached for gpt-6.1-sol"}
            return real_poll(service, job_id)
        with mock.patch.object(llm_batch, "_poll", poll):
            _, replies = self.run_batch("openai", ["r00", "r01"])
        self.assertEqual(len(self.fakes["openai"].jobs), 2)
        self.assertEqual(len(replies.of), 2)
        first, second = self.state()["jobs"]
        self.assertIn("refused for the batch queue cap", first["state"])
        self.assertTrue(second["collected"])
        self.assertEqual(llm.REQUESTS["sent"], 1 + 2)
        # near-miss: a job failed for another reason is not sent again: its requests fail
        self.setUp_again()

        def poll_other(service, job_id):
            return {"ended": True, "state": "failed", "counts": "", "error": "invalid_request: bad file"}
        with mock.patch.object(llm_batch, "_poll", poll_other), \
                mock.patch.object(llm_batch, "_results", lambda *a, **k: {}):
            _, replies = self.run_batch("openai", ["r00"])
        self.assertEqual((len(self.fakes["openai"].jobs), list(replies.failed)), (1, ["r00"]))

    def test_other_runs_open_jobs_count_against_the_cap(self):
        """An uncollected job of another run of the same model holds most of the cap: this run's job waits until a
        check says that job ended."""
        with mock.patch.dict(llm.BATCH_QUEUE_TOKENS, {"openai": {"gpt-6.1-sol": 1000}}):
            self.stop_while_waiting("openai", ["r50"])
            path = self.tmp / "050_annotate" / "cache" / "extract.batch_jobs.json"
            state = self.state()
            state["jobs"][0].update(identity={**state["jobs"][0]["identity"], "cache_identity": "x"},
                                    input_tokens=990)
            path.write_text(json.dumps(state), encoding="utf-8")
            fake, at = self.watch_creates("openai")
            fake.polls, fake.running = 0, 2
            _, replies = self.run_batch("openai", ["r00"])
        self.assertEqual(len(replies.of), 1)
        self.assertGreater(at[0], 0)                                      # sent only after the other job ended
        # near-miss: a model with no cap doesn't wait for it
        self.assertEqual(llm_batch.queue_cap("openai", "gpt-6-luna-x"), None)

    def test_only_060_has_the_setting(self):
        from common import step
        with self.assertRaises(SystemExit), mock.patch.object(sys, "stderr"):
            step._parse_command_line("070_evaluate", {}, {"model": "m"}, ["--batch", "true"])
        _, settings, _ = step._parse_command_line("060_extract", {}, {"batch": False}, ["--batch", "true"])
        self.assertIs(settings["batch"], True)
        run = (Path(support.ROOT) / "060_extract" / "run.py").read_text(encoding="utf-8")
        self.assertIn('"batch":              False', run)


if __name__ == "__main__":
    unittest.main()
