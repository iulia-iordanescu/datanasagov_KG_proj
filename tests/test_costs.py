"""What a run cost and how long it took (common/common_helpers/llm_costs.py, llm.PRICES) and the table of every run
of step 060 (helpers/run_costs.py):

    price lookup        a model's price by any spelling of its name, only through its maker's own API
    cost arithmetic     batch rows at the batch price, single rows at the standard price, cache reads and writes
                        (Anthropic's 5-minute and 1-hour writes apart), the long-prompt tier, the price periods
    unknown price       a model not listed, a service other than a maker's own API, a date no period covers, tokens
                        of a kind with no listed price: the cost is unknown, saying why, never estimated
    token counts        an OpenAI cache write counted once, as a write, not also as input; each reply under its kind
    maker times         each maker's job times as ISO times, and the processing time between them
    the helper's table  fake run records, new and old: what each row computes, and "not recorded" for the rest
"""
import datetime as dt
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import support                                    # noqa: F401  (the repository on the import path)
from common import audit, llm

sys.path.insert(0, str(support.ROOT / "helpers"))
import run_costs                                  # noqa: E402

DAY = "2026-11-18"


def row(kind="batch", tier="base", day=DAY, **counts):
    return {"kind": kind, "tier": tier, "day": day, **dict.fromkeys(llm.COUNTS, 0), **counts}


class Prices(unittest.TestCase):

    def test_lookup_by_any_spelling_through_the_makers_api(self):
        for name in ("claude-opus-5-5", "claude-opus-5.5", "Claude-Opus-5-5"):
            self.assertEqual(llm.price_entry(name, "anthropic")["periods"][0]["standard"]["input"], 4)
        self.assertIsNone(llm.price_entry("claude-opus-5-5", "litellm"))         # near miss: another service
        self.assertIsNone(llm.price_entry("claude-opus-5", "anthropic"))         # near miss: another version
        self.assertIsNone(llm.price_entry("gpt-6.1-sol", "anthropic"))           # near miss: another maker's API
        self.assertEqual(llm.price_entry("gpt-5.6-sol", "openai")["periods"][0]["batch"]["input"], 2.00)
        self.assertEqual(llm.price_entry("gemini-3.8-flash", "google")["periods"][0]["batch"]["output"], 1.875)

    def test_every_price_is_whole(self):
        """Every entry: its service a maker's own API; every period has a standard and a batch price, and a long one
        where long_above is set; a batch price never above the standard one."""
        for name, entry in llm.PRICES.items():
            self.assertIn(entry["service"], llm.DIRECT_SERVICES, name)
            self.assertEqual(llm.maker(name), llm.DIRECT_SERVICES[entry["service"]]["maker"], name)
            for period in entry["periods"]:
                names = ("standard", "batch") + (("standard_long", "batch_long") if entry["long_above"] else ())
                for kind in names:
                    self.assertEqual(tuple(period[kind]), llm.PRICE_FIELDS, (name, kind))
                for f in llm.PRICE_FIELDS:
                    s, b = period["standard"][f], period["batch"][f]
                    self.assertEqual(s is None, b is None, (name, f))
                    if s is not None:
                        self.assertLessEqual(b, s, (name, f))

    def test_batch_and_single_cache_read_and_write(self):
        """Claude Opus 5.5: batch $2 input, $0.10 read, $2.50 5-minute write, $4 1-hour write, $10 output; standard
        $4, $0.20, $5, $8, $20 (per million tokens)."""
        rows = [row("batch", input_tokens=1_000_000, cache_read_tokens=2_000_000, cache_write_1h_tokens=500_000,
                    output_tokens=100_000, reasoning_tokens=60_000),
                row("single", input_tokens=10_000, cache_write_tokens=50_000, output_tokens=1_000)]
        cost = llm.run_cost(rows, "claude-opus-5-5", "anthropic")
        batch = 1 * 2 + 2 * 0.10 + 0.5 * 4 + 0.1 * 10                  # thinking is part of the output, not added
        single = 0.01 * 4 + 0.05 * 5 + 0.001 * 20
        self.assertIsNone(cost["unknown"])
        self.assertAlmostEqual(cost["usd"], batch + single, places=9)
        self.assertAlmostEqual(cost["parts"][0]["usd"], batch, places=9)
        self.assertEqual(cost["parts"][1]["price"]["cache_write"], 5)
        self.assertEqual(cost["prices_from"], llm.PRICE_PAGES["anthropic"])

    def test_long_prompts_and_periods(self):
        long_ = row("single", "long", input_tokens=1_000_000)
        self.assertAlmostEqual(llm.run_cost([long_], "claude-haiku-5-5", "anthropic")["usd"], 0.50)
        self.assertAlmostEqual(llm.run_cost([row("single", input_tokens=1_000_000)], "claude-haiku-5-5",
                                            "anthropic")["usd"], 0.10)
        # Gemini 4 Argon: batch input $1.00 through 2026-11-30, $2.00 from 2026-12-01
        for day, usd in (("2026-11-30", 1.00), ("2026-12-01", 2.00)):
            self.assertAlmostEqual(llm.run_cost([row(day=day, input_tokens=1_000_000)], "gemini-4-argon",
                                                "google")["usd"], usd)
        # the tier, from the prompt's length, the cached part included
        llm_model = (llm.MODEL, llm.SERVICE)
        from common.llm_costs import tier_of
        self.assertEqual(tier_of(100_000, "claude-haiku-5-5", "anthropic"), "base")
        self.assertEqual(tier_of(100_001, "claude-haiku-5-5", "anthropic"), "long")
        self.assertEqual(tier_of(10_000_000, "claude-opus-5-5", "anthropic"), "base")      # one price at any length
        self.assertEqual((llm.MODEL, llm.SERVICE), llm_model)

    def test_unknown_never_estimated(self):
        r = [row(input_tokens=1000)]
        cost = llm.run_cost(r, "gpt-6-astra", "openai")
        self.assertIsNone(cost["usd"])
        self.assertIn("lists no price for the model gpt-6-astra", cost["unknown"])
        cost = llm.run_cost(r, "claude-opus-5-5", "litellm")
        self.assertIsNone(cost["usd"])
        self.assertIn("LiteLLM", cost["unknown"])
        cost = llm.run_cost([row(day="2026-12-01", input_tokens=1000)], "gpt-5.6-sol", "openai")
        self.assertIsNone(cost["usd"])                                  # its promotional price ends on 2026-11-30
        self.assertIn("2026-12-01", cost["unknown"])
        cost = llm.run_cost([row(cache_write_tokens=10)], "gemini-4-argon", "google")
        self.assertIsNone(cost["usd"])                                  # Google lists no cache write price
        self.assertIn("cache write", cost["unknown"])
        self.assertEqual(llm.run_cost([row(cache_write_tokens=0)], "gemini-4-argon", "google")["usd"], 0)
        self.assertEqual(llm.run_cost([], "gemini-4-argon", "google")["usd"], 0)
        self.assertEqual(llm.money(None), "unknown")
        self.assertEqual(llm.money(0.004), "$0.0040")
        self.assertEqual(llm.money(12.345), "$12.35")


class TokenCounts(unittest.TestCase):

    def setUp(self):
        self.saved = (llm.MODEL, llm.SERVICE, dict(llm.REQUESTS))
        llm.TOKENS_BY_PRICE.clear()
        for k in llm.REQUESTS:
            llm.REQUESTS[k] = 0

    def tearDown(self):
        llm.MODEL, llm.SERVICE = self.saved[:2]
        llm.REQUESTS.update(self.saved[2])
        llm.TOKENS_BY_PRICE.clear()
        llm._last.reply = {}

    def test_openai_cache_write_counted_once(self):
        llm.MODEL, llm.SERVICE = "gpt-5.6-sol", "openai"
        llm._last.reply = {}
        with mock.patch("common.llm_costs._today", lambda: DAY):
            llm._count_tokens({"prompt_tokens": 100, "completion_tokens": 7,
                               "prompt_tokens_details": {"cached_tokens": 30, "cache_write_tokens": 50}})
        self.assertEqual((llm.REQUESTS["input_tokens"], llm.REQUESTS["cache_read_tokens"],
                          llm.REQUESTS["cache_write_tokens"]), (20, 30, 50))
        (r,) = llm.by_price_rows()
        self.assertEqual((r["kind"], r["input_tokens"], r["cache_read_tokens"], r["cache_write_tokens"]),
                         ("single", 20, 30, 50))
        self.assertAlmostEqual(llm.run_cost([r])["usd"], (20 * 4 + 30 * 0.40 + 50 * 5 + 7 * 20) / 1e6, places=12)

    def test_kind_tier_and_day_of_each_reply(self):
        llm.MODEL, llm.SERVICE = "claude-haiku-5-5", "anthropic"
        llm._last.reply = {"batch_job": "msgbatch_1", "batch_created": "2026-11-17T23:59:00-05:00"}
        llm._count_tokens({"prompt_tokens": 120_000, "completion_tokens": 5})
        llm._last.reply = {}
        with mock.patch("common.llm_costs._today", lambda: DAY):
            llm._count_tokens({"prompt_tokens": 100_000, "completion_tokens": 5})
        self.assertEqual([(r["kind"], r["tier"], r["day"]) for r in llm.by_price_rows()],
                         [("batch", "long", "2026-11-17"), ("single", "base", DAY)])


class MakerTimes(unittest.TestCase):

    def test_times_and_processing(self):
        a = llm.maker_times("anthropic", {"created_at": "2026-11-18T15:00:00Z", "ended_at": "2026-11-18T15:06:00.5Z",
                                          "expires_at": "2026-11-19T15:00:00Z"})
        self.assertEqual(a, {"created_at": "2026-11-18T15:00:00+00:00", "ended_at": "2026-11-18T15:06:00.500000+00:00"})
        self.assertEqual(llm.job_processing("anthropic", a), {"seconds": 360.5, "from": "created_at", "to": "ended_at"})
        o = llm.maker_times("openai", {"created_at": 1_795_014_000, "in_progress_at": 1_795_014_060,
                                       "completed_at": None, "expired_at": 1_795_100_400})
        self.assertEqual(set(o), {"created_at", "in_progress_at", "expired_at"})
        self.assertEqual(llm.job_processing("openai", o)["to"], "expired_at")
        g = llm.maker_times("google", type("Job", (), {"create_time": dt.datetime(2026, 11, 18, 15),
                                                       "update_time": dt.datetime(2026, 11, 18, 16)})())
        self.assertEqual(g["create_time"], "2026-11-18T15:00:00+00:00")
        self.assertEqual(llm.job_processing("google", g)["seconds"], 3600.0)
        self.assertIsNone(llm.job_processing("anthropic", {"created_at": a["created_at"]}))   # not ended: none
        self.assertIsNone(llm.job_processing("openai", None))


class Table(unittest.TestCase):
    """helpers/run_costs.py on fake kept runs: a new record (tokens by price, cost, times kept), an old batch record
    whose tokens all came from one job (cost from the report's totals), an old batch record with single requests
    beside it (cost not recorded), an old single-request record of a model whose price depends on the prompt's
    length (computed when the run's whole input is below that length), and a run through LiteLLM (cost unknown)."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.results, self.reports = self.tmp / "results", self.tmp / "reports"
        self.reports.mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def keep(self, run_id, made, records=2, schema="annotations/ground_truth_schema.txt", report=None,
             minutes=10, current=False):
        folder = (self.results / "060_extract") if current else (self.results / "060_extract" / "previous_runs" / run_id)
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "extracted_triples_details.json").write_text(json.dumps({
            "made": {"run_id": run_id, **made},
            "records": [{"id": f"r{i}", "status": "extracted"} for i in range(records)]}), encoding="utf-8")
        (folder / "_manifest.json").write_text(json.dumps({
            "run_id": run_id, "started": "2026-11-18T10:00:00-05:00",
            "finished": f"2026-11-18T10:{minutes:02d}:00-05:00",
            "inputs": [{"name": "schema", "path": schema}]}), encoding="utf-8")
        if report:
            (self.reports / f"{run_id}.md").write_text(report, encoding="utf-8")

    @staticmethod
    def report(tokens, test_calls=0, asked_again=0):
        i, r, w, o, t = tokens
        return (f"- **replies asked again:** {asked_again}\n\n"
                f"| the one-line test (first paid call of a run) | {test_calls} | – |\n\n"
                f"| sent, not from the cache | {i:,} |\n| sent, read from the cache (billed at a fraction) | {r:,} |\n"
                f"| sent, written to the cache (billed a little above normal) | {w:,} |\n| received | {o:,} |\n"
                f"| received as thinking (reasoning tokens, where the service reports them) | {t:,} |\n")

    def test_new_and_old_records(self):
        new_rows = [row("batch", answers=2, input_tokens=1_000_000, output_tokens=100_000, reasoning_tokens=50_000),
                    row("single", answers=1, input_tokens=10_000)]
        cost = llm.run_cost(new_rows, "claude-opus-5-5", "anthropic")
        self.keep("060_extract_2026-11-18_1000", {
            "service": "anthropic", "model": "claude-opus-5-5", "thinking": "high", "repeat": 2, "batch": True,
            "batch_jobs": [{"service": "anthropic", "id": "msgbatch_A", "maker_times": {
                "created_at": "2026-11-18T15:00:00+00:00", "ended_at": "2026-11-18T15:12:30+00:00"}}],
            "spent": {"tokens": {"input_tokens": 1_010_000, "cache_read_tokens": 0, "cache_write_tokens": 0,
                                 "output_tokens": 100_000, "reasoning_tokens": 50_000},
                      "tokens_by_price": new_rows, "cost": cost,
                      "wall_time": {"started": "x", "until": "y", "seconds": 800.0}}}, schema="x/040_induce_schema/s")
        # old, batch, no single request: every token at the batch price (Sonnet 5.5: $1 input, $0.05 read, $2 1-hour
        # write, $5 output)
        self.keep("060_extract_2026-11-18_1100", {
            "service": "anthropic", "model": "claude-sonnet-5-5", "thinking": "high", "repeat": 1, "batch": True,
            "batch_jobs": [{"service": "anthropic", "id": "msgbatch_B", "how": "resumed"}]},
            report=self.report((18_099, 1_268_904, 32_536, 158_032, 82_474)))
        # old, batch, with a test call: batch and single tokens not kept apart
        self.keep("060_extract_2026-11-18_1200", {
            "service": "google", "model": "gemini-3.8-flash", "thinking": "high", "repeat": 1, "batch": True,
            "batch_jobs": [{"service": "google", "id": "batches/C"}]},
            report=self.report((1000, 0, 0, 100, 50), test_calls=1))
        # old, single requests, a model priced by prompt length, whose whole input is below that length
        self.keep("060_extract_2026-11-18_1300", {
            "service": "anthropic", "model": "claude-haiku-5-5", "thinking": "lowest", "repeat": 1, "batch": False},
            report=self.report((678, 0, 65_070, 1_554, 0)))
        # old, through LiteLLM, the current run (the output folder itself)
        self.keep("060_extract_2026-11-18_1400", {
            "service": "litellm", "model": "claude-opus-5-5", "thinking": "low", "repeat": 1, "batch": False},
            report=self.report((10, 0, 0, 5, 0)), current=True)
        # a record with no report: nothing about its tokens
        self.keep("060_extract_2026-11-18_1500", {"service": "openai", "model": "gpt-6-luna", "batch": False})

        fetched = []

        def fetch(service, job_id):
            fetched.append(job_id)
            return {"ended": True, "times": {"created_at": "2026-11-18T15:00:00+00:00",
                                             "ended_at": "2026-11-18T15:06:00+00:00"}}
        rows = {r["run_id"][-4:]: r for r in run_costs.collect(self.results, self.reports, fetch)}
        self.assertEqual(list(rows), ["1000", "1100", "1200", "1300", "1400", "1500"])
        new = rows["1000"]
        self.assertEqual((new["schema"], new["repeat"], new["records"]), ("induced", 2, "2 (2 extracted)"))
        self.assertAlmostEqual(new["cost_usd"], 1 * 2 + 0.1 * 10 + 0.01 * 4)
        self.assertEqual((new["input_tokens"], new["reasoning_tokens"]), (1_010_000, 50_000))
        self.assertEqual(new["job_processing"], "msgbatch_A: 12 min 30 s")
        self.assertEqual(new["wall_time"], "13 min 20 s")                          # the record's, not the manifest's
        old = rows["1100"]
        self.assertEqual(old["schema"], "ground truth")
        self.assertAlmostEqual(old["cost_usd"], (18_099 * 1 + 1_268_904 * 0.05 + 32_536 * 2 + 158_032 * 5) / 1e6,
                               places=12)
        self.assertEqual(old["job_processing"], "msgbatch_B: 6 min 0 s")             # read from the maker (fetch)
        self.assertEqual(old["wall_time"], "10 min 0 s")                             # the manifest's start and end
        self.assertIn("tokens from the run's report", old["notes"])
        self.assertEqual(rows["1200"]["cost_usd"], run_costs.NOT_RECORDED)
        self.assertIn("weren't kept apart", rows["1200"]["notes"])
        self.assertAlmostEqual(rows["1300"]["cost_usd"], (678 * 0.10 + 65_070 * 0.125 + 1_554 * 0.50) / 1e6)
        self.assertEqual(rows["1300"]["job_processing"], "–")
        self.assertEqual(rows["1400"]["cost_usd"], "unknown")
        self.assertIn("LiteLLM", rows["1400"]["notes"])
        self.assertEqual((rows["1500"]["input_tokens"], rows["1500"]["cost_usd"]),
                         (run_costs.NOT_RECORDED, run_costs.NOT_RECORDED))
        self.assertEqual(fetched, ["msgbatch_B", "batches/C"])                        # only jobs without their times
        # without fetching: the old job's time not recorded
        rows = {r["run_id"][-4:]: r for r in run_costs.collect(self.results, self.reports)}
        self.assertEqual(rows["1100"]["job_processing"], f"msgbatch_B: {run_costs.NOT_RECORDED}")
        # the files: one Markdown table and one CSV, a line per run
        md, csv_path = run_costs.write(list(rows.values()), self.reports)
        text = md.read_text(encoding="utf-8")
        self.assertIn("| 060_extract_2026-11-18_1100 | claude-sonnet-5-5 | anthropic | high | ground truth |", text)
        self.assertIn("not the maker's invoice", text)
        self.assertEqual(len(csv_path.read_text(encoding="utf-8").strip().splitlines()), 1 + 6)

    def test_old_long_prompt_model_above_its_length(self):
        """Near miss of the run above: the same model, its whole input above 100,000 tokens: not recorded."""
        self.keep("060_extract_2026-11-18_1300", {
            "service": "anthropic", "model": "claude-haiku-5-5", "thinking": "high", "repeat": 1, "batch": False},
            report=self.report((50_000, 60_000, 0, 1, 0)))
        (r,) = run_costs.collect(self.results, self.reports)
        self.assertEqual(r["cost_usd"], run_costs.NOT_RECORDED)
        self.assertIn("110,000 input tokens", r["notes"])


class RunWallTime(unittest.TestCase):

    def test_wall_time_from_the_runs_start(self):
        self.assertIsNone(llm.wall_time())                     # outside a run
        audit.begin_run("060_extract_2026-11-18_1000", {}, "2026-11-18T10:00:00-05:00", llm.time.monotonic() - 42)
        try:
            wall = llm.wall_time()
        finally:
            audit.end_run()
        self.assertEqual(wall["started"], "2026-11-18T10:00:00-05:00")
        self.assertGreaterEqual(wall["seconds"], 42)
        self.assertIsNone(audit.run_started())


if __name__ == "__main__":
    unittest.main()
