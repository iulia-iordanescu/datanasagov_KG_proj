"""The guards around paid model calls (common/common_helpers/llm.py, cache.py, extraction.py), with the stand-in
model behind LiteLLM's reply shape (tests/stand_ins.py, stand_in_post):

    the thinking cap      sent as reasoning_effort only to the models LiteLLM documents it for; part of the cache key
    the repeat            part of the cache key from 2 on (repeat 1 keeps the answers saved before); 0, a negative, a
                          fraction or a true/false value stops the step; recorded in the run's record and report
    the test call         its token counts in one line; cut off: the run stops; thinking that leaves too little
                          room: a warning, and a second question before paying for more
    the early stop        3 failed among the first 10 calls stop the run; calls under way are kept, the rest not made
    no resend             an answer cut off is kept as a cut-off; a rerun with the same limit doesn't pay for it again
    the failed-call record   one line per failed, cut-off, or not-made call, in outputs/logs/<run id>_failed_calls.jsonl
    progress              one line per finished call at most every 10 s; the first and the last always
    the report            the Model calls section's thinking tokens, failed calls, and cut-offs
    the session id        060 sends one LiteLLM session header per run, its run id; no other step sends one; the
                          words sent, the settings and the cache key are the same either way
    the answer cache      with LITELLM_BYPASS_ANSWER_CACHE=1, every LiteLLM call of 040 to 070 carries LiteLLM's
                          cache control, never one through Ask Sage; the words sent, the other settings and the
                          cache key are the same either way; recorded in the run's record and report
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
        self.saved = (llm.MODEL, llm.SERVICE, llm.THINKING, llm.MAX_ANSWER_TOKENS, llm.REPEAT)
        llm.MAX_ANSWER_TOKENS = 16000                       # the checks below are written for this limit, not the default
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
        llm.MODEL, llm.SERVICE, llm.THINKING, llm.MAX_ANSWER_TOKENS, llm.REPEAT = self.saved
        llm.SESSION_ID = None
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
        return extraction.ask_model(items, lambda item, piece: f'{stand_ins.TRIPLES_PROMPT} #{item["id"]}#', calls, workers,
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

    # ---------------------------------------------------------------- the repeat

    def test_repeat_in_the_cache_key_from_2_on(self):
        """Repeat 1 (the default, or given) is the key answers were saved under before the setting existed; each later
        repeat has a key of its own, so the same prompt is asked again, once per repeat."""
        self.calls(model="claude-opus-5.5")
        self.assertEqual(llm.cache_identity(), "litellm:claude-opus-5.5")
        before = cache_module.key("p", "piece")
        self.calls(model="claude-opus-5.5", repeat=1)
        self.assertEqual(cache_module.key("p", "piece"), before)                        # repeat 1: answers stay valid
        self.calls(model="claude-opus-5.5", repeat=2)
        self.assertEqual(llm.cache_identity(), "litellm:claude-opus-5.5|repeat:2")
        two = cache_module.key("p", "piece")
        self.assertNotEqual(two, before)
        self.calls(model="claude-opus-5.5", repeat=3)
        self.assertNotIn(cache_module.key("p", "piece"), (before, two))                # each repeat its own answers
        self.calls(model="gemini-2.5-pro", repeat=2)
        self.assertEqual(llm.cache_identity(), "litellm:gemini-2.5-pro|thinking:low|repeat:2")
        self.assertEqual(llm.describe()["repeat"], 2)                                   # in the run's record

    def test_repeat_must_be_a_whole_number_from_1(self):
        from common.stop import Stop
        for bad in (0, -1, 1.5, "2", True, None):
            with self.subTest(repeat=bad), self.assertRaisesRegex(Stop, "whole number from 1 on"):
                self.calls(repeat=bad)
        self.calls(repeat=5)                                                            # near-miss: any whole number
        self.assertEqual(llm.REPEAT, 5)

    def test_repeat_in_the_report_only_from_2_on(self):
        self.calls(repeat=1)
        self.assertNotIn("Repeat ", "\n".join(report.model_calls([("x", 1, 0)], 0, llm.model_label())))
        self.calls(repeat=2)
        self.assertIn("Repeat 2 (setting `repeat`)", "\n".join(report.model_calls([("x", 1, 0)], 0, llm.model_label())))

    def test_unknown_thinking_level(self):
        from common.stop import Stop
        with self.assertRaisesRegex(Stop, "low, medium, high, model_default"):
            self.calls(thinking="none")

    def test_unusable_settings_stop(self):
        """A setting paid_calls can't use stops the step (Stop: `stopped`), never fails it: an unknown service, an
        empty model, an unknown thinking level."""
        from common.stop import Stop
        for settings, words in (({"service": "nowhere"}, "service must be one of asksage, litellm, but is 'nowhere'"),
                                ({"model": " "}, "model must be a text .not empty., but is ' '"),
                                ({"thinking": "max"}, "thinking must be one of low, medium, high, model_default, but is 'max'")):
            with self.subTest(settings=settings), self.assertRaisesRegex(Stop, words):
                self.calls(**settings)

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

    # ---------------------------------------------------------------- the cut-off advice: from the token counts

    def cut_off_advice(self, reasoning, **settings):
        """The advice for record r01's answer, cut off with KG_STAND_IN_REASONING = reasoning."""
        os.environ["KG_STAND_IN_CUT_OFF"] = "#r01#"
        os.environ["KG_STAND_IN_REASONING"] = reasoning
        self.ask(self.calls(**settings), ["r00", "r01"])
        (cut,) = self.entries()
        return cut["what_to_do"]

    def test_cut_off_advice_thinking(self):
        """Thinking took most of the tokens though capped at low: the advice says so, not that the answer is long."""
        text = self.cut_off_advice("12000")
        self.assertIn("Thinking used most of the tokens: the model spent 12,000 of the 16,000 tokens thinking, "
                      "leaving 4,000 for the answer", text)
        self.assertIn("already at its lowest cap (low): raise MAX_ANSWER_TOKENS", text)
        self.assertIn("`--thinking model_default`", text)
        self.assertNotIn("answer itself is long", text)

    def test_cut_off_advice_thinking_lower(self):
        text = self.cut_off_advice("12000", thinking="high")
        self.assertIn("set the step's thinking setting lower (it is high; `--thinking medium` or `--thinking low`)",
                      text)

    def test_cut_off_advice_answer(self):
        """Little thinking, and the answer used the rest: the answer itself is long."""
        text = self.cut_off_advice("900", thinking="high")
        self.assertIn("The answer itself is long: the model spent 900 of the 16,000 tokens thinking and 15,100 on "
                      "the answer; raise MAX_ANSWER_TOKENS in common/common_helpers/llm.py (now 16,000)", text)
        self.assertIn("max_chars", text)
        self.assertNotIn("--thinking", text)

    def test_cut_off_advice_unreported(self):
        """No thinking count from the service: the advice says it can't tell, and gives both fixes."""
        text = self.cut_off_advice("unreported", thinking="medium")
        self.assertIn("Thinking tokens not reported; can't tell which used the 16,000 tokens, the model's thinking "
                      "or the answer itself (the answer got 16,000 tokens in all)", text)
        self.assertIn("if the model thinks, set the step's thinking setting lower (it is medium; `--thinking low`)",
                      text)
        self.assertIn("if not, raise MAX_ANSWER_TOKENS", text)

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

    def test_wrong_shape_per_text_piece(self):
        """Extraction (040, 050, 060): an answer without its "triples" list is asked once more, then fails; the
        failed-call record names the step, the record and text piece, and what was wrong; nothing is saved. A
        wrong-shaped answer saved before is asked again (the run's warnings name the cache file); a right one is reused."""
        items = [{"id": i, "pieces": ["text"]} for i in ("r00", "r01")]
        prompts = {"r00": f"{llm.TEST_PROMPT} #r00#", "r01": f"{stand_ins.TRIPLES_PROMPT} #r01#"}    # r00: {"ok": true}
        ask = lambda calls: extraction.ask_model(items, lambda item, piece: prompts[item["id"]], calls, 1, "draft",
                                                 "050 will draft", "drafting")
        first = ask(self.calls())
        self.assertEqual((sorted(first.of), list(first.failed)), (["r01"], ["r00"]))
        self.assertIn('"triples" should be a JSON list, but is missing', first.failed["r00"])
        [entry] = self.entries()
        self.assertEqual((entry["step"], entry["stage"], entry["record"], entry["text_piece"], entry["error_type"],
                          entry["asks"]), ("050_annotate", "draft", "r00", 1, "BadReply", 2))
        self.assertIn("isn't a JSON object of the shape asked for", entry["error"])
        cache = cache_module.Cache(self.tmp / "050_annotate" / "cache", "draft")
        self.assertEqual(list(cache.answers.values()), [{"triples": []}])                  # r00's not saved
        prompts["r00"] = prompts["r00"].replace(llm.TEST_PROMPT, stand_ins.TRIPLES_PROMPT)  # stand-in now answers right
        cache.put(cache_module.key(prompts["r00"]), {"ok": True})                          # as an older version saved it
        stand_ins.PAYLOADS.clear()
        second = ask(self.calls())
        self.assertEqual((sorted(second.of), second.calls, second.reused), (["r00", "r01"], 1, 1))
        self.assertEqual(len(stand_ins.PAYLOADS), 2)                                       # the test call and r00's
        self.assertEqual(len(llm.RUN_WARNINGS), 1)
        self.assertIn(f"{step.repo_path(cache.path)} were JSON of the wrong shape", llm.RUN_WARNINGS[0])

    def test_failed_call_record(self):
        calls = self.calls()
        os.environ["KG_STAND_IN_CUT_OFF"] = "#r01#"
        os.environ["KG_STAND_IN_FAIL"] = "#r02#"
        os.environ["KG_STAND_IN_REASONING"] = "300"
        self.ask(calls, ["r00", "r01", "r02"])
        cut, failed = self.entries()
        self.assertEqual((cut["outcome"], cut["record"], cut["text_piece"], cut["stage"]), ("cut_off", "r01", 1, "draft"))
        self.assertEqual(cut["finish_reason"], "length")
        self.assertEqual((cut["reasoning_tokens"], cut["answer_tokens"]), (300, 16000))
        self.assertTrue(cut["answer"].startswith('{"tri'))                              # the partial answer, whole
        self.assertEqual(cut["call_settings"], {"temperature": 0, "max_answer_tokens": 16000, "thinking": "low",
                                                "thinking_sent": "low", "effort": None,
                                                "read_timeout_s": llm.READ_TIMEOUT})
        self.assertEqual(len(cut["prompt_sha256"]), 64)
        self.assertIn("The answer itself is long", cut["what_to_do"])
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


    # ---------------------------------------------------------------- the session id

    def step_calls(self, folder: str, run_id: str):
        """The Calls a step's own paid_calls makes, in a run of that step."""
        audit.end_run()
        audit.begin_run(run_id, {})
        moves = step.load_moves(folder)
        empty = type("Empty", (), {"notes": []})()
        args = (empty, empty) if folder == "060_extract" else (empty,)
        return moves.paid_calls(*args, {**SETTINGS, "model": "claude-opus-5.5"}, self.tmp / folder)

    def test_session_header_for_060_only(self):
        sent = {}
        for folder in ("040_induce_schema", "050_annotate", "060_extract", "070_evaluate"):
            run_id = f"{folder}_2026-10-31_1200"
            self.step_calls(folder, run_id)
            stand_ins.PAYLOADS.clear()
            stand_ins.HEADERS.clear()
            llm.call_llm(llm.TEST_PROMPT + " #x#", cache_until="#x#")
            sent[folder] = (stand_ins.HEADERS[0].get(llm.SESSION_HEADER), stand_ins.PAYLOADS[0], llm.cache_identity())
            self.assertEqual(llm.describe().get("session_id"), run_id if folder == "060_extract" else None, folder)
        self.assertEqual(sent["060_extract"][0], "060_extract_2026-10-31_1200")      # the run's id
        for folder in ("040_induce_schema", "050_annotate", "070_evaluate"):
            self.assertIsNone(sent[folder][0], folder)
            # the same words, settings and cache key with or without the header
            self.assertEqual(sent[folder][1], sent["060_extract"][1], folder)
            self.assertEqual(sent[folder][2], sent["060_extract"][2], folder)

    def test_session_header_through_ask_sage_never(self):
        self.step_calls("060_extract", "060_extract_2026-10-31_1200")
        llm.SERVICE = "asksage"
        self.assertNotIn("session_id", llm.describe())
        self.assertNotIn("Session:", "\n".join(report.model_calls([("extracting", 0, 0)], 0, "m")))

    def test_session_in_the_report_of_060(self):
        self.step_calls("060_extract", "060_extract_2026-10-31_1200")
        text = "\n".join(report.model_calls([("extracting", 1, 0)], 1, llm.model_label()))
        self.assertIn("`x-litellm-session-id` `060_extract_2026-10-31_1200` (this run's id)", text)
        self.step_calls("050_annotate", "050_annotate_2026-10-31_1200")
        self.assertNotIn("Session:", "\n".join(report.model_calls([("drafting", 1, 0)], 1, llm.model_label())))

    # ---------------------------------------------------------------- LiteLLM's answer cache

    def sent_by_step(self, folder: str, switch: str) -> tuple:
        """(the request body, the cache key, the run record) of one call of a step's run, with the bypass switch."""
        with mock.patch.dict(os.environ, {llm.ANSWER_CACHE_SWITCH: switch}):
            self.step_calls(folder, f"{folder}_2026-10-31_1200")
            stand_ins.PAYLOADS.clear()
            llm.call_llm(llm.TEST_PROMPT + " #x#", cache_until="#x#")
            return stand_ins.PAYLOADS[0], llm.cache_identity(), llm.describe(), llm._last.reply["settings_sent"]

    def test_answer_cache_bypass_on_every_step(self):
        """With LITELLM_BYPASS_ANSWER_CACHE=1, every LiteLLM call of 040, 050, 060 and 070 carries the cache control;
        the words sent, the other settings and the cache key are the same as without it."""
        for folder in ("040_induce_schema", "050_annotate", "060_extract", "070_evaluate"):
            with self.subTest(folder=folder):
                on, key_on, made_on, settings_on = self.sent_by_step(folder, "1")
                off, key_off, made_off, settings_off = self.sent_by_step(folder, "")
                self.assertEqual(on["cache"], {"no-cache": True, "no-store": True})
                self.assertNotIn("cache", off)
                self.assertEqual({k: v for k, v in on.items() if k != "cache"}, off)     # messages and settings
                self.assertEqual(key_on, key_off)                                        # the cache key
                self.assertEqual(made_on["answer_cache"], "bypassed")
                self.assertTrue(made_off["answer_cache"].startswith("not bypassed (LITELLM_BYPASS_ANSWER_CACHE"))
                self.assertEqual(settings_on["cache"], on["cache"])                      # what was sent, recorded
                self.assertNotIn("cache", settings_off)

    def test_answer_cache_switch_values(self):
        """1, true and yes switch it on, in any case, spaces around ignored; anything else leaves it off."""
        for value, on in (("1", True), ("true", True), (" YES ", True), ("True", True), ("", False), ("0", False),
                          ("no", False), ("false", False), ("on", False), ("11", False), ("yes please", False)):
            with self.subTest(value=value), mock.patch.dict(os.environ, {llm.ANSWER_CACHE_SWITCH: value}):
                self.assertEqual(llm.answer_cache_bypassed(), on)
                self.assertEqual(llm.answer_cache_control(), llm.ANSWER_CACHE_CONTROL if on else {})
        with mock.patch.dict(os.environ, {llm.ANSWER_CACHE_SWITCH: "1"}):
            llm.answer_cache_control()["cache"]["no-cache"] = False              # a copy: the constant stays
            self.assertEqual(llm.ANSWER_CACHE_CONTROL, {"cache": {"no-cache": True, "no-store": True}})

    def test_answer_cache_never_through_ask_sage(self):
        sent = []

        class Reply:
            status_code, text = 200, ""

            def raise_for_status(self):
                pass

            def json(self):
                return {"status": 200, "message": "OK"}
        with mock.patch.dict(os.environ, {llm.ANSWER_CACHE_SWITCH: "1"}), \
                mock.patch.object(llm.requests, "post", lambda url, json=None, **k: sent.append(json) or Reply()), \
                mock.patch.object(llm, "_asksage_token", lambda: "token"):
            llm.SERVICE = "asksage"
            llm.call_llm("hi", model="google-claude-sonnet-5", service="asksage")
            self.assertNotIn("cache", sent[0])
            self.assertNotIn("answer_cache", llm.describe())
            self.assertNotIn("answer cache", "\n".join(report.model_calls([("x", 1, 0)], 1, "m")))

    def test_answer_cache_in_the_report(self):
        for switch, words in (("1", "LiteLLM answer cache: bypassed (every request asked LiteLLM for a fresh answer"),
                              ("", "LiteLLM answer cache: not bypassed (LITELLM_BYPASS_ANSWER_CACHE isn't set")):
            with mock.patch.dict(os.environ, {llm.ANSWER_CACHE_SWITCH: switch}):
                self.step_calls("060_extract", "060_extract_2026-10-31_1200")
                self.assertIn(words, "\n".join(report.model_calls([("extracting", 1, 0)], 1, llm.model_label())))


class CtrlC(unittest.TestCase):
    """Ctrl+C ends a step `interrupted` (exit code 130), never `stopped` (2): during the model calls, at the question
    before paying, and anywhere else (docs/running_on_nasa_laptop.md, section 4, *How a step ends*). Declining the
    question, or a closed input, still ends it `stopped`."""

    def test_during_the_calls(self):
        def handle(n, key, result, error):
            raise KeyboardInterrupt
        with self.assertRaises(llm.Interrupted) as caught:
            llm.run_parallel(lambda: "answer", {"a": (), "b": ()}, 1, handle, "Answers received are kept.")
        self.assertIsInstance(caught.exception, KeyboardInterrupt)
        self.assertNotIsInstance(caught.exception, SystemExit)
        self.assertIn("Answers received are kept.", str(caught.exception))

    def test_at_the_question(self):
        import builtins
        for typed, raised, words in ((KeyboardInterrupt, llm.Interrupted, "Cancelled with Ctrl+C. Nothing was spent."),
                                     (EOFError, SystemExit, "Cancelled. Nothing was spent."),
                                     ("n", SystemExit, "Cancelled. Nothing was spent.")):
            effect = typed if isinstance(typed, type) else None
            with self.subTest(typed=typed), mock.patch.object(builtins, "input", side_effect=effect,
                                                              return_value=None if effect else typed):
                with self.assertRaises(raised) as caught:
                    llm.confirm("Go?")
                said = caught.exception.code if isinstance(caught.exception, SystemExit) else str(caught.exception)
                self.assertEqual(said.strip(), words)
        with mock.patch.object(builtins, "input", return_value="n"), self.assertRaises(SystemExit) as caught:
            llm.confirm("Go?", spent="Only the test call was paid for.")
        self.assertEqual(caught.exception.code, "Cancelled. Only the test call was paid for.")

    def test_run_step_status(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            for raised, code, status in ((llm.Interrupted("Cancelled with Ctrl+C. Nothing was spent."), 130, "interrupted"),
                                         (KeyboardInterrupt(), 130, "interrupted"),
                                         (SystemExit("Cancelled. Nothing was spent."), 2, "stopped")):
                def main(inputs, settings, output, raised=raised):
                    raise raised
                with self.subTest(raised=repr(raised)), \
                        mock.patch.object(step, "RESULTS_DIR", tmp / "results"), \
                        mock.patch.object(step, "REPORTS_DIR", tmp / "reports"), \
                        mock.patch.object(step, "LOGS_DIR", tmp / "logs"):
                    with self.assertRaises(SystemExit) as caught:
                        step.run_step("999_stand_in", {}, {}, main, argv=[])
                    self.assertEqual(caught.exception.code, code)
                    reports = sorted((tmp / "reports").glob("999_stand_in_*.md"))
                    self.assertIn(status, reports[-1].read_text(encoding="utf-8"))
                    for r in reports:
                        r.unlink()
        finally:
            logging.shutdown()
            shutil.rmtree(tmp, ignore_errors=True)


class ReplyKinds(Guards):
    """One rule says what a reply is (llm.classify_reply), from the finish reason AND the content, for both services:
    complete, cut off, refused, empty, malformed. Every variant below, near-misses included; the kinds then drive the
    cache (a cut-off kept, a refusal never stored), the re-ask (never for a cut-off or a refusal) and the reason a
    record is left out for (dropped.kind)."""

    OBJECT = '{"triples": [{"subject": "MODIS", "predicate": "ABOARD", "object": "Aqua"}]}'
    UNFINISHED = '{"triples": [{"subject": "MODIS", "predicate": "ABOARD", "obj'
    REFUSALS = ("I'm sorry, but I can't help with that.", "I cannot extract facts from this text.",
                "Sorry, I am unable to assist with this request.", "As an AI, I can't do that.",
                "Unfortunately, I am not able to process this record.", "I apologize, but I won't do that.",
                "I\u2019m unable to help.", "```\nI'm sorry, I can't help with that.\n```")

    def kinds(self, cases, service=None):
        for text, reason, native, expected in cases:
            with self.subTest(text=str(text)[:40], reason=reason, native=native):
                self.assertEqual(llm.classify_reply(text, reason, native, service)[0], expected)

    def test_complete(self):
        o = self.OBJECT
        self.kinds([(o, "stop", None, "complete"), (o, None, None, "complete"),
                    (o, "end_turn", None, "complete"), (o, "eos", None, "complete"),
                    (o, "STOP", None, "complete"), (o, "tool_calls", None, "complete"),   # unknown reason: the content decides
                    (f"```json\n{o}\n```", "stop", None, "complete"),                      # fenced
                    (f"```JSON\n{o}\n```", "stop", None, "complete"),                      # the tag in capitals
                    (f"```\n{o}\n```", "stop", None, "complete"),                          # no tag
                    (f"Here is the JSON you asked for:\n{o}\nI hope this helps.", "stop", None, "complete"),
                    (f"I can't say more than this: {o}", "stop", None, "complete"),        # refusal words before an object: not a refusal
                    ('{"triples": []}', "stop", None, "complete"),                         # no facts (a refusal sent this way can't be told apart)
                    ('{"notes": "line\n```\nmore"}'.replace("\n", "\\n"), "stop", None, "complete"),   # a fence inside a value
                    ])
        data, state = llm.find_json(f"```json\n{o}\n```")
        self.assertEqual((state, data["triples"][0]["object"]), ("object", "Aqua"))
        data, state = llm.find_json('{"a": "x\n```\ny"}'.replace("\n", "\\n"))             # the value's fence is kept
        self.assertEqual(data["a"], "x\n```\ny")

    def test_cut_off(self):
        u = self.UNFINISHED
        self.kinds([(u, "length", None, "cut_off"), (self.OBJECT, "length", None, "cut_off"),   # the service says so
                    (u, "stop", "MAX_TOKENS", "cut_off"), (u, None, "max_output_tokens", "cut_off"),
                    (u, None, None, "cut_off"),                 # no finish reason at all (Ask Sage): the content says so
                    (u, "tool_calls", None, "cut_off"),         # an unknown reason doesn't say the model stopped itself
                    ('```json\n' + u, None, None, "cut_off"),   # cut inside a fence
                    ("Here it is: " + u, None, None, "cut_off"),
                    ('{"triples": [{"subject": "a string left open', None, None, "cut_off"),
                    ])
        self.kinds([(u, None, None, "cut_off")], service="asksage")
        self.assertIn("Ask Sage takes no answer limit", llm.classify_reply(u, None, None, "asksage")[1])

    def test_refused(self):
        self.kinds([(t, "stop", None, "refused") for t in self.REFUSALS]
                   + [(t, None, None, "refused") for t in self.REFUSALS]           # Ask Sage: no finish reason
                   + [("", "content_filter", None, "refused"), ("", "stop", "SAFETY", "refused"),
                      (self.OBJECT, "content_filter", None, "refused"),            # a filter's reason wins over content
                      ("x", "stop", "recitation", "refused"), ("", "refusal", None, "refused")])

    def test_empty(self):
        self.kinds([("", "stop", None, "empty"), ("   \n", None, None, "empty"), (None, "stop", None, "empty")])

    def test_malformed(self):
        u = self.UNFINISHED
        self.kinds([(u, "stop", None, "malformed"),                     # the model stopped itself mid-object: ask again
                    (u, "end_turn", None, "malformed"),
                    ('{"a": 1} {"b": 2}', "stop", None, "malformed"),  # two objects: which one was meant can't be told
                    ('{"a": 1}\n{"b": 2}', None, None, "malformed"),
                    ('{"a": 1,}', "stop", None, "malformed"),          # closed, but not valid JSON
                    ("Here are the facts: MODIS is aboard Aqua.", "stop", None, "malformed"),   # prose, no refusal
                    ("I can help with that! The facts are below.", "stop", None, "malformed"),  # "I can", not "I can't"
                    ("The record is sorry about the data gaps.", "stop", None, "malformed"),    # "sorry" not at the start
                    ("[1, 2]", "stop", None, "complete"),               # a JSON value that isn't an object: call_llm_json refuses it
                    ])

    def test_find_json_states(self):
        for text, state in ((self.OBJECT, "object"), (self.UNFINISHED, "unterminated"), ("no braces", "none"),
                            ('{"a": 1} {"b": 2}', "several"), ('{"a": 1,}', "invalid"),
                            ('{"a": "}"}', "object"), ('{"a": "{"', "unterminated"), ('{"a": "\\"}', "unterminated")):
            self.assertEqual(llm.find_json(text)[1], state, text)

    # ---------------------------------------------------------------- through LiteLLM

    def test_litellm_prose_refusal_not_reasked_not_stored(self):
        """A refusal in prose with finish_reason "stop" (HTTP 200) is a refusal: one call (never asked once more), the
        record left out as refused (not malformed), nothing stored, the failed-call record naming it."""
        calls = self.calls()
        os.environ["KG_STAND_IN_REFUSE"] = "#r01#"
        replies = self.ask(calls, ["r00", "r01"])
        self.assertEqual((sorted(replies.of), list(replies.failed), replies.kinds), (["r00"], ["r01"], {"r01": "refused"}))
        self.assertEqual(len([p for p in stand_ins.PAYLOADS if "#r01#" in str(p)]), 1)   # not asked again
        self.assertIn("the model refused to answer", replies.failed["r01"])
        self.assertEqual(llm.REASKS["not_json"], 0)
        cache = cache_module.Cache(self.tmp / "050_annotate" / "cache", "draft")
        self.assertEqual(len(cache.answers), 1)                                           # r00's answer only
        (entry,) = self.entries()
        self.assertEqual((entry["outcome"], entry["error_type"], entry["finish_reason"]), ("failed", "Refused", "stop"))
        self.assertIn("Asking again gets the same answer", entry["what_to_do"])
        again = self.ask(self.calls(), ["r00", "r01"])                                    # a rerun asks it again (not a cut-off)
        self.assertEqual(again.kinds, {"r01": "refused"})

    def test_litellm_unknown_finish_reason_with_complete_answer(self):
        def post(url, headers=None, json=None, timeout=None, **_):
            reply = stand_ins.stand_in_post(url, headers=headers, json=json, timeout=timeout)
            reply._body["choices"][0]["finish_reason"] = "end_turn"
            return reply
        with mock.patch.object(llm, "_post", post):
            replies = self.ask(self.calls(), ["r00"])
        self.assertEqual(list(replies.of), ["r00"])

    def test_litellm_unfinished_object_with_stop_is_malformed(self):
        """The model stopped itself inside an object (finish_reason "stop"): asked once more, then malformed."""
        def post(url, headers=None, json=None, timeout=None, **_):
            reply = stand_ins.stand_in_post(url, headers=headers, json=json, timeout=timeout)
            reply._body["choices"][0]["message"]["content"] = self.UNFINISHED
            return reply
        with mock.patch.object(llm, "_post", post):
            replies = self.ask(self.calls(), ["r00"])
        self.assertEqual(replies.kinds, {"r00": "malformed"})
        self.assertEqual(len(stand_ins.PAYLOADS), 3)                                      # test call, the call, asked once more

    # ---------------------------------------------------------------- through Ask Sage

    def asksage(self, answers: dict):
        """requests.post standing in for Ask Sage: the answer is answers[word] for the word in the prompt."""
        sent = []

        class Reply:
            status_code, text, headers = 200, "", {}

            def __init__(self, message):
                self.message = message

            def raise_for_status(self):
                pass

            def json(self):
                return {"status": 200, "message": self.message}

        def post(url, json=None, **k):
            sent.append(json)
            if url.endswith("/query"):
                word = next(w for w in answers if w in json["message"])
                return Reply(answers[word])
            return Reply(llm.TEST_PROMPT and '{"ok": true}')
        return sent, post

    def test_asksage_cut_off_recognized_and_not_paid_twice(self):
        """Through Ask Sage (no finish reason, no answer limit) an answer stopping inside an unfinished JSON object
        is a cut-off: not asked once more, kept in the cache as cut off, and a rerun reports it without a call."""
        llm.SERVICE = "asksage"
        sent, post = self.asksage({"#r00#": self.OBJECT, "#r01#": self.UNFINISHED, "ok": '{"ok": true}'})
        with mock.patch.object(llm.requests, "post", post), mock.patch.object(llm, "_asksage_token", lambda: "t"):
            calls = self.calls(service="asksage", model="google-claude-sonnet-5")
            replies = self.ask(calls, ["r00", "r01"])
            self.assertEqual((sorted(replies.of), replies.kinds), (["r00"], {"r01": "cut_off"}))
            self.assertEqual(len([p for p in sent if "#r01#" in p["message"]]), 1)       # not asked once more
            self.assertIn("Ask Sage takes no answer limit", replies.failed["r01"])
            note = extraction.failed_note(replies, "the drafted batch")
            self.assertIn("lower the step's max_chars", note)                             # the advice for Ask Sage
            self.assertNotIn("MAX_ANSWER_TOKENS in", note)                                # no limit to raise there
            sent.clear()
            again = self.ask(self.calls(service="asksage", model="google-claude-sonnet-5"), ["r00", "r01"])
            self.assertEqual(sent, [])                                                    # nothing paid
            self.assertIn("not asked again", again.failed["r01"])
            self.assertEqual(again.kinds, {"r01": "cut_off"})
        (entry,) = [e for e in self.entries() if e["outcome"] == "cut_off"]
        self.assertEqual((entry["error_type"], entry["finish_reason"], entry["record"]), ("CutOff", None, "r01"))
        self.assertTrue(entry["answer"].startswith('{"triples"'))

    def test_asksage_prose_refusal(self):
        llm.SERVICE = "asksage"
        sent, post = self.asksage({"#r00#": self.OBJECT, "#r01#": self.REFUSALS[0], "ok": '{"ok": true}'})
        with mock.patch.object(llm.requests, "post", post), mock.patch.object(llm, "_asksage_token", lambda: "t"):
            replies = self.ask(self.calls(service="asksage", model="google-claude-sonnet-5"), ["r00", "r01"])
        self.assertEqual(replies.kinds, {"r01": "refused"})
        self.assertEqual(len([p for p in sent if "#r01#" in p["message"]]), 1)
        cache = cache_module.Cache(self.tmp / "050_annotate" / "cache", "draft")
        self.assertEqual(len(cache.answers), 1)                                           # never stored

    def test_asksage_malformed_asked_once_more(self):
        llm.SERVICE = "asksage"
        sent, post = self.asksage({"#r00#": "Here are the facts: MODIS is aboard Aqua.", "ok": '{"ok": true}'})
        with mock.patch.object(llm.requests, "post", post), mock.patch.object(llm, "_asksage_token", lambda: "t"):
            replies = self.ask(self.calls(service="asksage", model="google-claude-sonnet-5"), ["r00"])
        self.assertEqual(replies.kinds, {"r00": "malformed"})
        self.assertEqual(len([p for p in sent if "#r00#" in p["message"]]), 2)           # asked once more

    def test_cut_off_marker_valid_per_service_limit(self):
        """The cut-off marker records the answer limit the service was sent: through LiteLLM MAX_ANSWER_TOKENS (an
        old marker, written as 16000 by a run before, still counts), through Ask Sage none."""
        cache = cache_module.Cache(self.tmp / "cache", "draft")
        cache.put_cut_off("k", llm.CutOff("cut"))
        self.assertEqual(cache.answers["k"][cache_module.CUT_OFF]["max_answer_tokens"], 16000)
        self.assertTrue(cache.cut_off("k"))
        llm.MAX_ANSWER_TOKENS = 32000
        self.assertIsNone(cache.cut_off("k"))                                             # a higher limit: asked again
        llm.SERVICE = "asksage"
        cache.put_cut_off("a", llm.CutOff("cut"))
        self.assertIsNone(cache.answers["a"][cache_module.CUT_OFF]["max_answer_tokens"])
        self.assertTrue(cache.cut_off("a"))
        self.assertIsNone(cache.cut_off("k"))                                             # LiteLLM's marker isn't Ask Sage's


class Budget(unittest.TestCase):
    """A used-up budget or quota (llm.budget_exhausted: LiteLLM's budget answers, the providers' quota and credit
    answers) is never retried: the first such answer stops the whole run, no worker sends another call, the answers
    already received stay in the cache, and one message names the service, the numbers it reported, and what to do.
    An ordinary rate limit still retries. Near-misses included."""

    NASA = "Budget has been exceeded! User=iiordane in Team=trial-moderate Current cost: 25.0, Max budget: 25.0"

    calls, entries, ask = Guards.calls, Guards.entries, Guards.ask      # Guards' set-up, without its tests

    def setUp(self):
        Guards.setUp(self)
        llm.BUDGET_GONE["error"] = None

    def tearDown(self):
        llm.BUDGET_GONE["error"] = None
        Guards.tearDown(self)

    def budget(self, status=429, message=NASA, kind="budget_exceeded"):
        return stand_ins.StandInReply(status, {"error": {"message": message, "type": kind, "code": str(status)}})

    def test_which_answers_are_a_used_up_budget(self):
        for status, text, gone in (
                (429, self.NASA, True),
                (429, "Budget has been exceeded! TeamMember=iiordane Current cost: 27.04, Max budget: 25.0", True),
                (400, "ExceededBudget: User=u1 over budget. Spend=3.7e-05, Budget=0.0", True),
                (400, "LiteLLM Virtual Key: k, exceeded budget for model=gpt-6.1-sol", True),
                (401, "Authentication Error, ExceededTokenBudget: Current spend for token: 7.2e-05", True),
                (429, '{"error": {"type": "budget_exceeded", "message": "over"}}', True),
                (429, "You exceeded your current quota, please check your plan and billing details. insufficient_quota",
                 True),
                (400, "Your credit balance is too low to access the Anthropic API.", True),
                # near-misses: not a used-up budget
                (429, "Rate limit reached for requests per minute; try again in 20s", False),
                (429, "Rate limit: the token budget per minute is exceeded, try again shortly", False),
                (400, "max_tokens must be greater than thinking.budget_tokens", False),
                (400, "thinking: you exceeded budget_tokens", False),
                (200, self.NASA, False),                                   # an answer, whatever its words
                (500, "internal error while computing the budget", False)):
            with self.subTest(text=text):
                self.assertEqual(llm.budget_exhausted(status, text), gone)

    def test_not_retried_and_nothing_sent_after(self):
        self.calls()
        posts = []

        def post(url, headers=None, json=None, timeout=None, **_):
            posts.append(1)
            return self.budget()
        with mock.patch.object(llm, "_post", post):
            with self.assertRaises(llm.BudgetExhausted) as caught:
                llm.call_llm("x", model="gemini-2.5-pro", service="litellm")
            self.assertEqual(len(posts), 1)                                           # not asked again
            said = str(caught.exception.code)
            for words in ("LiteLLM answered that the budget for this account is used up", "HTTP 429", "iiordane",
                          "trial-moderate", "a cost of 25.0 against a budget of 25.0",
                          "ask the LiteLLM administrators to raise or reset the budget", "nothing to retry",
                          "kept in the cache"):
                self.assertIn(words, said)
            self.assertNotIn('{"error"', said)                                       # LiteLLM's words, not its JSON
            with self.assertRaises(llm.BudgetExhausted):                             # any later call: never sent
                llm.call_llm("y", model="gemini-2.5-pro", service="litellm")
            from helpers import check_effort
            with self.assertRaises(llm.BudgetExhausted):                             # nor a check helper's request
                check_effort.ask("gemini-2.5-pro", "q", {})
        self.assertEqual(len(posts), 1)

    def test_a_400_budget_answer_stops_too(self):
        posts = []

        def post(url, headers=None, json=None, timeout=None, **_):
            posts.append(1)
            return self.budget(400, "ExceededBudget: User=u1 over budget. Spend=3.7e-05, Budget=0.0")
        with mock.patch.object(llm, "_post", post), self.assertRaises(llm.BudgetExhausted) as caught:
            llm.call_llm("x", model="gemini-2.5-pro", service="litellm")
        self.assertEqual(len(posts), 1)
        self.assertIn("a cost of 3.7e-05 against a budget of 0.0", str(caught.exception.code))

    def test_rate_limits_still_retry(self):
        for message in ("stand-in: too many requests", "Rate limit: the token budget per minute is exceeded"):
            posts = []

            def post(url, headers=None, json=None, timeout=None, message=message, **_):
                posts.append(1)
                if len(posts) < 3:
                    return stand_ins.StandInReply(429, {"error": {"message": message, "code": 429}})
                return stand_ins.stand_in_post(url, headers=headers, json=json, timeout=timeout)
            with self.subTest(message=message), mock.patch.object(llm, "_post", post):
                llm.call_llm(llm.TEST_PROMPT, model="gemini-2.5-pro", service="litellm")
                self.assertEqual(len(posts), 3)
        self.assertIsNone(llm.BUDGET_GONE["error"])

    def test_a_run_stops_at_once_and_keeps_its_answers(self):
        calls = self.calls()
        sent = []

        def post(url, headers=None, json=None, timeout=None, **_):
            prompt = json["messages"][0]["content"]
            sent.append(prompt)
            if "#r03#" in prompt:
                return self.budget()
            return stand_ins.stand_in_post(url, headers=headers, json=json, timeout=timeout)

        ids = [f"r{i:02}" for i in range(10)]
        with mock.patch.object(llm, "_post", post), self.assertRaises(llm.BudgetExhausted) as caught:
            self.ask(calls, ids)
        self.assertIn("ask the LiteLLM administrators", str(caught.exception.code))
        records = [p for p in sent if "#r" in p]
        self.assertEqual(len(records), 4)                                            # r00 to r03; none after
        self.assertTrue(all(any(f"#{i}#" in p for i in ids[:4]) for p in records))
        kept = json.loads((self.tmp / "050_annotate" / "cache" / "draft.json").read_text(encoding="utf-8"))
        self.assertEqual(len(kept), 3)                                               # r00 to r02, paid once
        entries = self.entries()
        refused = [e for e in entries if e["outcome"] == "failed"]
        self.assertEqual([e["record"] for e in refused], ["r03"])
        self.assertEqual(refused[0]["error_type"], "BudgetExhausted")
        self.assertIn("raise or reset the budget", refused[0]["what_to_do"])
        not_sent = sorted(e["record"] for e in entries if e["outcome"] == "not_sent")
        self.assertEqual(not_sent, ids[4:])
        self.assertTrue(all("budget is used up" in e["why"] for e in entries if e["outcome"] == "not_sent"))

        # a rerun in the same process sends nothing at all: not even the test call
        sent.clear()
        with mock.patch.object(llm, "_post", post), self.assertRaises(llm.BudgetExhausted):
            self.ask(self.calls(), ids)
        self.assertEqual(sent, [])

    def test_with_several_workers_no_call_after_the_answer(self):
        import threading
        calls = self.calls()
        lock, order, gone = threading.Lock(), [], threading.Event()

        def post(url, headers=None, json=None, timeout=None, **_):
            prompt = json["messages"][0]["content"]
            with lock:
                order.append(("after" if gone.is_set() else "before", prompt))
            if "#r05#" in prompt:
                gone.set()
                return self.budget()
            return stand_ins.stand_in_post(url, headers=headers, json=json, timeout=timeout)

        with mock.patch.object(llm, "_post", post), self.assertRaises(llm.BudgetExhausted):
            self.ask(calls, [f"r{i:02}" for i in range(30)], workers=4)
        after = [p for when, p in order if when == "after"]
        self.assertLessEqual(len(after), 3)            # at most the other workers' calls already on their way
        self.assertLess(len(order), 30)
        answered = [p for _, p in order if "#r05#" not in p and "#r" in p]
        kept = json.loads((self.tmp / "050_annotate" / "cache" / "draft.json").read_text(encoding="utf-8"))
        self.assertEqual(len(kept), len(answered))     # every answer paid for is kept

    def test_a_step_ends_stopped_with_the_message(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            def main(inputs, settings, output):
                raise llm.BudgetExhausted(llm.budget_message("litellm", 429, self.NASA), 429)
            with mock.patch.object(step, "RESULTS_DIR", tmp / "results"), \
                    mock.patch.object(step, "REPORTS_DIR", tmp / "reports"), \
                    mock.patch.object(step, "LOGS_DIR", tmp / "logs"):
                with self.assertRaises(SystemExit) as caught:
                    step.run_step("999_stand_in", {}, {}, main, argv=[])
                self.assertEqual(caught.exception.code, 2)
                text = sorted((tmp / "reports").glob("999_stand_in_*.md"))[-1].read_text(encoding="utf-8")
                self.assertIn("stopped", text)
                self.assertIn("raise or reset the budget", text)
        finally:
            logging.shutdown()
            shutil.rmtree(tmp, ignore_errors=True)

    def test_ask_sage(self):
        """Ask Sage documents no form for a used-up allowance; the same words stop the run, as an HTTP error or as
        its error object in an HTTP 200 answer. Its plain rate limit still retries."""
        class Answer:
            def __init__(self, status, body):
                self.status_code, self._body, self.headers = status, body, {}
                self.text = json.dumps(body)

            def json(self):
                return self._body

            def raise_for_status(self):
                pass

        for answer, stops in ((Answer(429, {"message": self.NASA}), True),
                              (Answer(200, {"status": 200, "message": "Sorry.",
                                            "error": {"code": "insufficient_quota", "http_status": 429}}), True),
                              (Answer(200, {"status": 402, "message": "Your credit balance is too low"}), True),
                              (Answer(429, {"message": "Too many requests"}), False),
                              (Answer(200, {"status": 200, "message": "Sorry.",
                                            "error": {"code": "model_not_permitted", "http_status": 400}}), False)):
            llm.BUDGET_GONE["error"] = None
            posts = []

            def post(*a, answer=answer, **k):
                posts.append(1)
                return answer
            with self.subTest(body=answer._body), mock.patch.object(llm.requests, "post", post), \
                    mock.patch.object(llm, "_asksage_token", lambda: "t"):
                if stops:
                    with self.assertRaises(llm.BudgetExhausted) as caught:
                        llm.call_llm("x", model="m", service="asksage")
                    self.assertEqual(len(posts), 1)
                    self.assertIn("Ask Sage answered that the budget", str(caught.exception.code))
                    self.assertIn("ask the Ask Sage administrators", str(caught.exception.code))
                else:
                    with self.assertRaises(Exception) as caught:
                        llm.call_llm("x", model="m", service="asksage")
                    self.assertNotIsInstance(caught.exception, llm.BudgetExhausted)
                    self.assertIsNone(llm.BUDGET_GONE["error"])
                    if answer.status_code == 429:
                        self.assertEqual(len(posts), 4)                          # retried



class FreeCommands(unittest.TestCase):
    """A command whose docs say it is free is free by code: it calls llm.forbid_model_calls first, after which
    call_llm and litellm_post stop the run before any request leaves (found on 2026-11-02: `py
    helpers/second_opinion.py --apply true`, documented as free, drafted 60 calls again after the ground truth changed).
    And a run that pays shows the count to pay in the question itself, before Enter; one that pays nothing never asks."""

    calls, ask = Guards.calls, Guards.ask

    def setUp(self):
        Guards.setUp(self)

    def tearDown(self):
        llm.allow_model_calls()
        Guards.tearDown(self)

    def test_nothing_leaves_once_forbidden(self):
        posts, asked = [], []
        llm.forbid_model_calls("the command under test is free: a test")
        with mock.patch.object(llm, "_post", lambda *a, **k: posts.append(1)), \
                mock.patch.object(llm, "_ask_asksage", lambda *a, **k: asked.append(1)):
            for service in ("litellm", "asksage"):
                with self.subTest(service=service), self.assertRaises(llm.ModelCallForbidden) as caught:
                    llm.call_llm("x", model="gemini-2.5-pro", service=service)
                said = str(caught.exception.code)
                for words in ("the command under test is free: a test", "nothing was sent and nothing was paid",
                              "a mistake in the code"):
                    self.assertIn(words, said)
            with self.assertRaises(llm.ModelCallForbidden):
                llm.litellm_post("http://x.invalid/chat/completions", {}, {}, 5)   # the helpers' direct requests too
            self.assertFalse(issubclass(llm.ModelCallForbidden, Exception))         # no `except Exception` swallows it
        self.assertEqual((posts, asked), ([], []))
        # near miss: allowed again (the tests' reset), the same call is sent
        llm.allow_model_calls()
        self.calls()
        self.assertEqual(llm.call_llm(llm.TEST_PROMPT, model="gemini-2.5-pro", service="litellm").strip()[:1], "{")

    def test_every_free_command_forbids_first(self):
        """Each command documented as free calls llm.forbid_model_calls before anything else it does (the listing of
        py helpers/models.py: before listing; py helpers/second_opinion.py: first thing when --apply true)."""
        import ast
        for rel, where in (("helpers/compare_runs.py", "main"), ("helpers/partial_pairs.py", "main"),
                           ("helpers/review_page.py", "main"), ("helpers/models.py", "if not args.wanted"),
                           ("helpers/second_opinion.py", "if settings['apply']")):
            with self.subTest(command=rel):
                tree = ast.parse((support.ROOT / rel).read_text(encoding="utf-8"))
                main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")
                body = main.body
                if where != "main":
                    body = next(n for n in ast.walk(main) if isinstance(n, ast.If)
                                and ast.unparse(n.test) == where.removeprefix("if ")).body
                calls = [ast.unparse(s.value.func) for s in body if isinstance(s, ast.Expr) and isinstance(s.value, ast.Call)]
                first = [ast.unparse(s) for s in body[:2]]
                self.assertIn("llm.forbid_model_calls", calls, rel)
                self.assertTrue(any("llm.forbid_model_calls" in s for s in first), (rel, first))

    def test_steps_that_cost_nothing_never_import_the_model_client(self):
        """Steps 010, 020 and 030 say they make no model calls: none of their code imports common/common_helpers/llm.py
        (nor anything that sends requests to a model), so none can."""
        import ast
        for step_dir in ("010_harvest", "020_clean", "030_split"):
            for path in sorted((support.ROOT / step_dir).rglob("*.py")):
                with self.subTest(file=path.relative_to(support.ROOT).as_posix()):
                    tree = ast.parse(path.read_text(encoding="utf-8"))
                    names = {a.name for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom)) for a in n.names}
                    modules = {n.module or "" for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
                    self.assertNotIn("llm", names)
                    self.assertFalse(any(m.endswith("llm") or m.endswith("cache") for m in modules | names), names)

    def test_the_count_to_pay_is_in_the_question(self):
        questions = []
        with mock.patch.object(llm, "confirm", lambda q, *a, **k: questions.append(q)):
            calls = self.calls(confirm_paid_calls=True)
            self.ask(calls, ["a", "b"])
            self.assertEqual(len(questions), 1)
            self.assertIn("2 model call(s) to pay for, and 1 test call first", questions[0])
            # near misses: every answer in the cache: no question at all; one new piece: the question says 1
            calls = self.calls(confirm_paid_calls=True)
            self.ask(calls, ["a", "b"])
            self.assertEqual(len(questions), 1)
            calls = self.calls(confirm_paid_calls=True)
            self.ask(calls, ["a", "b", "c"])
            self.assertIn("1 model call(s) to pay for, and 1 test call first", questions[1])

if __name__ == "__main__":
    unittest.main()
