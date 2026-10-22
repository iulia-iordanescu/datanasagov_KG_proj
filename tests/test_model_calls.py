"""The guards around paid model calls (common/common_helpers/llm.py, cache.py, extraction.py), with the stand-in
model behind LiteLLM's reply shape (tests/stand_ins.py, stand_in_post):

    the thinking cap      sent as reasoning_effort only to the models LiteLLM documents it for; part of the cache key
    the test call         its token counts in one line; cut off: the run stops; thinking that leaves too little
                          room: a warning, and a second question before paying for more
    the early stop        3 failed among the first 10 calls stop the run; calls under way are kept, the rest not made
    no resend             an answer cut off is kept as a cut-off; a rerun with the same limit doesn't pay for it again
    the failed-call record   one line per failed, cut-off, or not-made call, in outputs/logs/<run id>_failed_calls.jsonl
    progress              one line per finished call at most every 10 s; the first and the last always
    the report            the Model calls section's thinking tokens, failed calls, and cut-offs
"""
import json
import logging
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import support                                    # noqa: F401  (the repository on the import path)
import stand_ins
from common import audit, cache as cache_module, extraction, llm, report, step

SETTINGS = {"service": "litellm", "model": "gemini-2.5-pro", "thinking": "low", "confirm_paid_calls": False}


class Clock:
    """A clock the test moves by hand."""

    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


class Guards(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.saved = (llm.MODEL, llm.SERVICE, llm.THINKING, llm.MAX_ANSWER_TOKENS)
        self.patches = [mock.patch.object(llm, "_post", stand_ins.stand_in_post),
                        mock.patch.object(llm, "load_dotenv", lambda *a, **k: None),
                        mock.patch.object(llm.time, "sleep", lambda s: None),
                        mock.patch.object(step, "LOGS_DIR", self.tmp / "outputs" / "logs"),
                        mock.patch.dict(os.environ, {"LITELLM_API_KEY": "stand-in", "LITELLM_BASE_URL": "http://x.invalid",
                                                     "KG_STAND_IN_CUT_OFF": "", "KG_STAND_IN_FAIL": "",
                                                     "KG_STAND_IN_REASONING": ""})]
        for p in self.patches:
            p.start()
        stand_ins.PAYLOADS.clear()
        stand_ins.CALLS.clear()
        audit.begin_run("050_annotate_2026-10-22_1200", {})

    def tearDown(self):
        audit.end_run()
        for p in reversed(self.patches):
            p.stop()
        llm.MODEL, llm.SERVICE, llm.THINKING, llm.MAX_ANSWER_TOKENS = self.saved
        shutil.rmtree(self.tmp)

    def calls(self, **settings):
        calls = llm.paid_calls({**SETTINGS, **settings}, self.tmp / "050_annotate")
        calls.paid.clock = self.clock = Clock()
        return calls

    def entries(self):
        path = self.tmp / "outputs" / "logs" / "050_annotate_2026-10-22_1200_failed_calls.jsonl"
        if not path.exists():
            return None
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

    def ask(self, calls, ids, workers=1):
        items = [{"id": i, "pieces": ["text"]} for i in ids]
        return extraction.ask_model(items, lambda item, piece: f'{llm.TEST_PROMPT} #{item["id"]}#', calls, workers,
                                    "draft", "050 will draft", "drafting")

    # ---------------------------------------------------------------- the thinking cap

    def test_thinking_sent_only_where_documented(self):
        self.calls()
        for model, service, thinking, sent in (("gemini-2.5-pro", "litellm", "low", "low"),
                                               ("gemini-3.1-pro-preview", "litellm", "medium", "medium"),
                                               ("gemini-2.5-pro", "litellm", "model_default", None),
                                               ("gemini-2.0-flash", "litellm", "low", None),      # doesn't think
                                               ("claude-opus-5.5", "litellm", "low", None),       # thinks only when asked
                                               ("gpt-4o", "litellm", "low", None),
                                               ("google-gemini-2.5-pro", "asksage", "low", None)):
            llm.THINKING = thinking
            self.assertEqual(llm.thinking_sent(model, service), sent, (model, service, thinking))
        llm.THINKING = "low"
        for model, sent in (("gemini-2.5-pro", "low"), ("claude-opus-5.5", None)):
            stand_ins.PAYLOADS.clear()
            llm.call_llm(llm.TEST_PROMPT, model=model, service="litellm")
            self.assertEqual(stand_ins.PAYLOADS[0].get("reasoning_effort"), sent, model)
            self.assertEqual("reasoning_effort" in stand_ins.PAYLOADS[0], sent is not None, model)

    def test_thinking_in_the_cache_key_only_when_sent(self):
        self.calls(model="claude-opus-5.5")
        self.assertEqual(llm.cache_identity(), "litellm:claude-opus-5.5")              # answers already paid stay valid
        self.calls(model="gemini-2.5-pro")
        low = llm.cache_identity()
        self.assertEqual(low, "litellm:gemini-2.5-pro|thinking:low")
        self.calls(model="gemini-2.5-pro", thinking="high")
        self.assertNotEqual(llm.cache_identity(), low)                                   # another cap asks again
        self.calls(model="gemini-2.5-pro", thinking="model_default")
        self.assertEqual(llm.cache_identity(), "litellm:gemini-2.5-pro")

    def test_unknown_thinking_level(self):
        with self.assertRaisesRegex(ValueError, "low, medium, high, model_default"):
            self.calls(thinking="none")

    # ---------------------------------------------------------------- the test call

    def test_test_call_line_and_thinking_warning(self):
        calls = self.calls()
        with self.assertLogs("pipeline", logging.INFO) as seen:
            calls.paid.start("plan")
        self.assertIn("  test call: ok (answer 3 tokens, thinking 0 tokens)", "\n".join(seen.output))
        self.assertEqual(llm.RUN_WARNINGS, [])

        calls = self.calls(thinking="model_default")
        os.environ["KG_STAND_IN_REASONING"] = "9000"
        with self.assertLogs("pipeline", logging.INFO) as seen:
            calls.paid.start("plan")
        text = "\n".join(seen.output)
        self.assertIn("thinking 9,000 tokens", text)
        self.assertEqual(len(llm.RUN_WARNINGS), 1)
        self.assertIn("used 9,000 tokens thinking, 56% of the 16,000 tokens", llm.RUN_WARNINGS[0])
        self.assertIn("`--thinking low`", llm.RUN_WARNINGS[0])                          # which setting to change

        calls = self.calls(thinking="model_default", confirm_paid_calls=True)            # asked again before paying more
        with mock.patch("builtins.input", lambda q: "n"), self.assertRaises(SystemExit) as stop:
            calls.paid.start("plan")
        self.assertIn("Nothing was spent", str(stop.exception.code))

    def test_test_call_cut_off_stops(self):
        calls = self.calls(thinking="high")
        os.environ["KG_STAND_IN_CUT_OFF"] = '{"ok": true}'
        with self.assertRaises(SystemExit) as stop:
            calls.paid.start("plan")
        message = str(stop.exception.code)
        self.assertIn("Test call to gemini-2.5-pro through LiteLLM was cut off", message)
        self.assertIn("`--thinking low`", message)
        self.assertIn("050_annotate_2026-10-22_1200_failed_calls.jsonl", message)
        self.assertEqual([e["stage"] for e in self.entries()], ["test call"])

    # ---------------------------------------------------------------- the early stop

    def test_early_stop(self):
        calls = self.calls()
        os.environ["KG_STAND_IN_FAIL"] = "#r02#|#r04#|#r05#"
        ids = [f"r{i:02d}" for i in range(12)]
        with self.assertRaises(llm.EarlyStop) as stop:
            self.ask(calls, ids)
        message = str(stop.exception.code)
        self.assertIn("Step 050 stopped early: 3 of the first 6 model calls of this run failed", message)
        self.assertIn("r02 piece 1: HTTP 400", message)
        self.assertIn("Each failed call is described in outputs/logs/050_annotate_2026-10-22_1200_failed_calls.jsonl",
                      message)
        made = len(stand_ins.PAYLOADS) - 1                                              # less the test call
        entries = self.entries()
        self.assertEqual([e["outcome"] for e in entries], ["failed"] * 3 + ["not_sent"] * (12 - made))
        self.assertEqual([e["record"] for e in entries if e["outcome"] == "not_sent"], ids[made:])
        # answered calls are kept, those still under way at the stop too: the rerun pays only for the rest
        os.environ["KG_STAND_IN_FAIL"] = ""
        replies = self.ask(self.calls(), ids)
        self.assertEqual((replies.reused, replies.calls, len(replies.of)), (made - 3, 12 - made + 3, 12))

    def test_early_stop_while_calls_are_under_way(self):
        """In parallel: the calls already under way when the stop comes are waited for, and their answers kept."""
        calls = self.calls()
        os.environ["KG_STAND_IN_FAIL"] = "#r00#|#r01#|#r02#"

        def slow(*args, **kwargs):                                                      # a call takes a while
            import threading
            threading.Event().wait(0.05)                                                # (time.sleep is stubbed out)
            return stand_ins.stand_in_post(*args, **kwargs)
        with mock.patch.object(llm, "_post", slow), self.assertRaises(llm.EarlyStop):
            self.ask(calls, [f"r{i:02d}" for i in range(40)], workers=4)
        kept = cache_module.Cache(self.tmp / "050_annotate" / "cache", "draft").answers
        made = len(stand_ins.PAYLOADS) - 1                                              # less the test call
        self.assertEqual(len(kept) + 3, made)                                           # every answered call kept
        self.assertEqual(len(self.entries()), 3 + 40 - made)                            # failed, and not made
        self.assertGreater(40 - made, 20)                                               # most were never paid for

    def test_one_prompt_stages_not_watched(self):
        """ask_cached's failures (040's labeling splits a refused batch on purpose) don't trigger the early stop."""
        cache = cache_module.Cache(self.tmp / "cache", "label")
        os.environ["KG_STAND_IN_FAIL"] = "#bad"
        calls = self.calls()
        for i in range(4):
            with self.assertRaises(llm.ApiError):
                cache_module.ask_cached(cache, calls, f"{llm.TEST_PROMPT} #bad{i}#", "plan")
        self.assertEqual(len(self.entries()), 4)                                        # each still recorded

    def test_no_early_stop_after_the_first_calls(self):
        calls = self.calls()
        os.environ["KG_STAND_IN_FAIL"] = "#r10#|#r11#|#r12#"
        replies = self.ask(calls, [f"r{i:02d}" for i in range(14)])
        self.assertEqual((len(replies.of), len(replies.failed)), (11, 3))

    # ---------------------------------------------------------------- no resend; the failed-call record

    def test_cut_off_not_paid_for_twice(self):
        calls = self.calls()
        os.environ["KG_STAND_IN_CUT_OFF"] = "#r01#"
        os.environ["KG_STAND_IN_REASONING"] = "200"
        replies = self.ask(calls, ["r00", "r01"])
        self.assertEqual((sorted(replies.of), list(replies.failed)), (["r00"], ["r01"]))
        note = extraction.failed_note(replies, "the drafted batch")
        self.assertIn("doesn't ask them again", note)
        self.assertNotIn("Run the step again: only the failed pieces", note)            # all failed ones were cut off
        stand_ins.PAYLOADS.clear()
        again = self.ask(self.calls(), ["r00", "r01"])                                  # the same settings
        self.assertEqual(stand_ins.PAYLOADS, [])                                        # nothing paid
        self.assertIn("not asked again", again.failed["r01"])
        self.assertEqual(list(again.cut_off), ["r01"])
        llm.MAX_ANSWER_TOKENS = 32000                                                   # a higher limit: asked again
        os.environ["KG_STAND_IN_CUT_OFF"] = ""
        third = self.ask(self.calls(), ["r00", "r01"])
        self.assertEqual((sorted(third.of), third.calls), (["r00", "r01"], 1))

    def test_ask_cached_cut_off_not_paid_for_twice(self):
        cache = cache_module.Cache(self.tmp / "cache", "label")
        os.environ["KG_STAND_IN_CUT_OFF"] = "#a#"
        for attempt in range(2):
            stand_ins.PAYLOADS.clear()
            with self.assertRaises(llm.CutOff) as cut:
                cache_module.ask_cached(cache, self.calls(), f"{llm.TEST_PROMPT} #a#", "plan")
            self.assertEqual(len(stand_ins.PAYLOADS), 2 if attempt == 0 else 0)          # test call and the call; none
        self.assertIn("not asked again", str(cut.exception))

    def test_failed_call_record(self):
        calls = self.calls()
        os.environ["KG_STAND_IN_CUT_OFF"] = "#r01#"
        os.environ["KG_STAND_IN_FAIL"] = "#r02#"
        os.environ["KG_STAND_IN_REASONING"] = "300"
        self.ask(calls, ["r00", "r01", "r02"])
        cut, failed = self.entries()
        self.assertEqual((cut["outcome"], cut["record"], cut["text_piece"], cut["stage"]), ("cut_off", "r01", 1, "draft"))
        self.assertEqual(cut["finish_reason"], "length")
        self.assertEqual(cut["reasoning_tokens"], 16000 - len(cut["answer"]) // 4)
        self.assertTrue(cut["answer"].startswith('{"ok"'))                              # the partial answer, whole
        self.assertEqual(cut["call_settings"], {"temperature": 0, "max_answer_tokens": 16000, "thinking": "low",
                                                "thinking_sent": "low", "read_timeout_s": llm.READ_TIMEOUT})
        self.assertEqual(len(cut["prompt_sha256"]), 64)
        self.assertIn("thinking", cut["what_to_do"])
        self.assertEqual((failed["outcome"], failed["error_type"]), ("failed", "ApiError"))
        self.assertIn("HTTP 400", failed["error"])
        self.assertEqual((cut["run_id"], cut["step"], cut["model"]),
                         ("050_annotate_2026-10-22_1200", "050_annotate", "gemini-2.5-pro"))
        text = json.dumps(self.entries())
        self.assertNotIn("stand-in\"", text.replace("-stand-in", ""))                  # no key
        self.assertEqual((llm.OUTCOMES["failed"], llm.OUTCOMES["cut_off"]), (2, 1))

    def test_failed_call_record_root_cause(self):
        """Each failed call's line holds what settles its cause: the HTTP status and the service's error body, the
        settings sent, the request's size, the attempts and their time, the whole usage, and the maker's own reason."""
        calls = self.calls()
        os.environ["KG_STAND_IN_CUT_OFF"] = "#r01#"
        os.environ["KG_STAND_IN_FAIL"] = "#r02#"

        def post(url, headers=None, json=None, timeout=None, **_):
            prompt = json["messages"][0]["content"]
            if "#r03#" in prompt:                                                       # rate limited every time
                return stand_ins.StandInReply(429, {"error": {"message": "stand-in: too many requests", "code": 429}})
            reply = stand_ins.stand_in_post(url, headers=headers, json=json, timeout=timeout)
            if "#r01#" in prompt:                                                       # the maker's own reason
                reply._body["choices"][0]["provider_specific_fields"] = {"native_finish_reason": "MAX_TOKENS"}
            return reply

        with mock.patch.object(llm, "_post", post), self.assertRaises(llm.EarlyStop):   # 3 of the first 4 failed
            self.ask(calls, ["r00", "r01", "r02", "r03"])
        cut, refused, limited = sorted(self.entries(), key=lambda e: e["record"])
        self.assertEqual((cut["finish_reason"], cut["native_finish_reason"], cut["http_status"]),
                         ("length", "MAX_TOKENS", 200))
        self.assertEqual(cut["usage"]["completion_tokens_details"]["reasoning_tokens"], cut["reasoning_tokens"])
        self.assertEqual(cut["served_as"], "gemini-2.5-pro-stand-in")
        self.assertEqual(cut["settings_sent"], {"model": "gemini-2.5-pro", "temperature": 0, "max_tokens": 16000,
                                                "reasoning_effort": "low"})
        self.assertEqual((refused["http_status"], refused["error_type"], refused["attempts"]), (400, "ApiError", 1))
        self.assertIn("stand-in: the service refuses this request", refused["error_body"])
        self.assertEqual((limited["http_status"], limited["error_type"], limited["attempts"]), (429, "RetryLater", 4))
        self.assertIn("too many requests", limited["error_body"])
        for entry in (cut, refused, limited):
            self.assertGreater(entry["request_bytes"], entry["prompt_characters"])
            self.assertIsInstance(entry["seconds"], float)
        self.assertNotIn("Bearer", json.dumps(self.entries()))                         # no key

    def test_failed_call_record_timeout(self):
        calls = self.calls()

        def post(url, headers=None, json=None, timeout=None, **_):
            if "#r01#" in json["messages"][0]["content"]:
                raise llm.requests.ReadTimeout("stand-in: read timed out")
            return stand_ins.stand_in_post(url, headers=headers, json=json, timeout=timeout)

        with mock.patch.object(llm, "_post", post):
            self.ask(calls, ["r00", "r01"])
        [entry] = self.entries()
        self.assertEqual((entry["error_type"], entry["cause_type"], entry["attempts"], entry["http_status"]),
                         ("ApiError", "ReadTimeout", 1, None))
        self.assertIn("no answer within", entry["error"])

    def test_no_record_without_failures(self):
        self.ask(self.calls(), ["r00", "r01"])
        self.assertIsNone(self.entries())
        self.assertIsNone(step._failed_calls())

    # ---------------------------------------------------------------- progress

    def test_progress_lines(self):
        calls = self.calls()
        calls.paid.start("plan")
        calls.paid.expect(5)
        with self.assertLogs("pipeline", logging.INFO) as seen:
            for i in range(5):
                self.clock.now += 4                                     # a call every 4 s: shown at most every 10 s
                calls.paid.outcome({"stage": "draft", "record": f"r{i}"}, "p",
                                   llm.CutOff("cut") if i == 1 else None)
        lines = [r.getMessage() for r in seen.records]
        self.assertEqual(lines, ["  model calls: 1 of 5 done, 0 failed, estimating the time left…",
                                 "  model calls: 4 of 5 done, 1 failed (1 cut off), about 4 s left",
                                 "  model calls: 5 of 5 done, 1 failed (1 cut off), took 20 s"])

    def test_two_calls_show_each(self):
        calls = self.calls()
        calls.paid.start("plan")
        with self.assertLogs("pipeline", logging.INFO) as seen:
            self.ask(calls, ["r00", "r01"])
        lines = [r.getMessage() for r in seen.records if "model calls:" in r.getMessage()]
        self.assertEqual(len(lines), 2)
        self.assertTrue(lines[1].startswith("  model calls: 2 of 2 done, 0 failed, took"))

    # ---------------------------------------------------------------- the report

    def test_report_section(self):
        calls = self.calls()
        os.environ["KG_STAND_IN_CUT_OFF"] = "#r01#"
        os.environ["KG_STAND_IN_REASONING"] = "100"
        self.ask(calls, ["r00", "r01"])
        text = "\n".join(report.model_calls([("drafting", 1, 0)], 1, llm.model_label()))
        self.assertIn("| received as thinking (reasoning tokens, where the service reports them) | ", text)
        self.assertIn("| failed (after the model client's own retries), cut-offs included | 1 |", text)
        self.assertIn("| cut off at the answer length limit (16,000 tokens) | 1 |", text)
        self.assertIn("sent as `reasoning_effort` `low`", text)
        self.assertIn("_failed_calls.jsonl", text)
        self.assertEqual(step._failed_calls()["entries"], 1)


if __name__ == "__main__":
    unittest.main()
