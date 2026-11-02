"""The second judge (helpers/second_judge.py): agreement and Cohen's kappa on hand-computed cases (Artstein & Poesio
2008's worked example, a prevalence paradox, a rater with one label, both with one same label); the judge's answers
parsed, with their near misses; no decision or verdict in any prompt (a prompt is the same whatever our label); the
partial pairs task's definitions quoted from 070_evaluate/metrics/pairs.md; the settings sent to gpt-6-astra (none
unverified); and the whole helper run with the stand-in model in a temporary copy: only rows with our label judged,
the labels written to annotations/second_judge.csv, the report's agreement and disagreements, the ground truth as it
was at a Git commit, a judge from a forbidden maker refused, and a rerun paying nothing."""
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import unittest
from fractions import Fraction
from pathlib import Path
from unittest import mock

from support import ROOT, temp_repo

import stand_ins                                                              # noqa: E402
from common import llm                                                        # noqa: E402
from common.files import read_csv, write_csv                                  # noqa: E402
from common.ground_truth import FILE_COLUMNS                                  # noqa: E402
from common.second_opinion import CANDIDATE_COLUMNS                           # noqa: E402

HERE = Path(__file__).resolve().parent


def load_helper():
    if "second_judge_helper" in sys.modules:
        return sys.modules["second_judge_helper"]
    spec = importlib.util.spec_from_file_location("second_judge_helper", ROOT / "helpers" / "second_judge.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


J = load_helper()


class Agreement(unittest.TestCase):

    def test_artstein_and_poesio_worked_example(self):
        """Their Table 4 (100 utterances, three labels): A_o = 0.88, A_e^κ = .46 × .52 + .44 × .32 + .1 × .16 = 0.396,
        κ = (0.88 − 0.396) ÷ (1 − 0.396) ≈ 0.8013 (their Table 5)."""
        pairs = ([("stat", "stat")] * 46 + [("stat", "ireq")] * 6 + [("ireq", "ireq")] * 32 + [("chck", "ireq")] * 6
                 + [("chck", "chck")] * 10)
        a = J.agreement(pairs, ("stat", "ireq", "chck"))
        self.assertEqual((a["n"], a["observed"], a["expected"]), (100, Fraction(88, 100), Fraction(396, 1000)))
        self.assertEqual(a["kappa"], Fraction(484, 604))
        self.assertAlmostEqual(float(a["kappa"]), 0.8013, places=4)
        per = {p["label"]: p for p in a["per_label"]}
        self.assertEqual((per["ireq"]["ours"], per["ireq"]["judge"], per["ireq"]["both"]), (32, 44, 32))
        self.assertEqual(per["ireq"]["specific"], Fraction(64, 76))
        self.assertFalse(a["one_label"])

    def test_prevalence_paradox(self):
        """90 of 100 items agree on the common label and none on the rare one: raw agreement 90%, yet p_e = 0.95² +
        0.05² = 0.905 and κ = (0.90 − 0.905) ÷ 0.095 = −1/19: the paradox raw agreement is reported beside κ for."""
        a = J.agreement([("a", "a")] * 90 + [("a", "b")] * 5 + [("b", "a")] * 5, ("a", "b"))
        self.assertEqual((a["observed"], a["expected"], a["kappa"]), (Fraction(9, 10), Fraction(905, 1000), Fraction(-1, 19)))
        per = {p["label"]: p["specific"] for p in a["per_label"]}
        self.assertEqual((per["a"], per["b"]), (Fraction(180, 190), 0))

    def test_one_label_and_none(self):
        """One rater with a single label: p_o = p_e, so κ = 0 (degenerate, flagged); both with one same label: p_e =
        1, κ undefined; full agreement on two labels: κ = 1; no item: nothing."""
        a = J.agreement([("same fact", "same fact")] * 60 + [("same fact", "not the same fact")] * 2, J.LABELS[J.PAIRS])
        self.assertEqual((a["observed"], a["expected"], a["kappa"], a["one_label"]),
                         (Fraction(60, 62), Fraction(60, 62), 0, True))
        a = J.agreement([("same fact", "same fact")] * 5, J.LABELS[J.PAIRS])
        self.assertEqual((a["observed"], a["kappa"], a["one_label"]), (1, None, True))
        self.assertEqual(J.agreement([("a", "a"), ("b", "b")], ("a", "b"))["kappa"], 1)
        self.assertIsNone(J.agreement([], ("a", "b"))["kappa"])

    def test_report_section(self):
        """The section: formula, κ, the degenerate note when one rater used one label, the disagreements."""
        rows = [{"task": J.PAIRS, "id": "r1", "title": "T1", "ours": "same fact", "our_rule": "", "label": l, "rule": "",
                 "reason": "because", "known_rule": True,
                 "cells": {"ground_truth_triple": "G", "extracted_triple": f"E{n}"}}
                for n, l in enumerate(["same fact", "same fact", "not the same fact"])]
        text = "\n".join(J.agreement_lines(J.PAIRS, rows))
        self.assertIn("2 ÷ 3 = **66.7%**", text)
        self.assertIn("κ = (*p*o − *p*e) ÷ (1 − *p*e) = **0.000**", text)
        self.assertIn("**κ is degenerate here:** we used a single label", text)
        self.assertIn("the 1 disagreement(s)", text)
        self.assertIn("ground truth: G; extracted: E2. Ours: same fact; the judge's: not the same fact.", text)


class Answers(unittest.TestCase):

    def test_shapes_and_near_misses(self):
        ok = {"label": "Left out", "section": "Writing a classed triple", "rule": 21, "reason": "r"}
        self.assertIsNone(J.facts_shape(ok))                                      # case aside
        for bad in ({**ok, "label": "leave out"}, {**ok, "rule": "21"}, {**ok, "rule": True}, {**ok, "section": " "},
                    {k: v for k, v in ok.items() if k != "reason"}):
            self.assertIsNotNone(J.facts_shape(bad), bad)
        self.assertIsNone(J.pairs_shape({"label": "Not the same fact", "reason": "r"}))
        for bad in ({"label": "same", "reason": "r"}, {"label": "same fact"}):
            self.assertIsNotNone(J.pairs_shape(bad), bad)
        self.assertEqual(J.label_of_decision("left out (Writing a classed triple, rule 21)"),
                         ("left out", "Writing a classed triple, rule 21"))
        self.assertEqual(J.label_of_decision("already in the ground truth in other words"),
                         ("already in the ground truth in other words", ""))
        rows = J.judged([{"task": J.FACTS}], {0: ok}, {("Writing a classed triple", 21): "w"})
        self.assertEqual((rows[0]["label"], rows[0]["rule"], rows[0]["known_rule"]),
                         ("left out", "Writing a classed triple, rule 21", True))
        self.assertFalse(J.judged([{"task": J.FACTS}], {0: {**ok, "rule": 99}}, {})[0]["known_rule"])


class Blind(unittest.TestCase):
    """No decision and no verdict reaches a prompt: each prompt is built from the record and the item alone."""

    def test_facts_prompt_the_same_whatever_the_decision(self):
        class Chosen:
            records = {"r": {"id": "r", "title": "MODIS Aqua", "notes": "MODIS aboard Aqua."}}
            schema_text = "SCHEMA TEXT"
        row = {"id": "r", "subject": "MODIS", "subject_class": "Instrument", "predicate": "ABOARD", "object": "Moon",
               "object_class": "Spacecraft", "source_text": "MODIS aboard", "model": "gemini-4-argon",
               "proposed_in_repeats": "2", "repeats": "3"}
        gt = [{"subject": "MODIS", "subject_class": "Instrument", "predicate": "ABOARD", "object": "Aqua",
               "object_class": "Spacecraft", "source_text": "MODIS aboard Aqua", "drafted_by": "gemini-4-argon"}]
        prompts = {J.facts_prompt(Chosen, gt, "GUIDELINES", {**row, "decision": d})
                   for d in ("added", "left out (Writing a classed triple, rule 21)",
                             "already in the ground truth in other words", "")}
        self.assertEqual(len(prompts), 1)
        prompt = prompts.pop()
        self.assertNotIn("rule 21)", prompt)
        self.assertNotIn("gemini-4-argon", prompt)                    # neither who drafted nor who proposed
        for part in ("GUIDELINES", "SCHEMA TEXT", "MODIS aboard Aqua.", "MODIS (Instrument) ABOARD Moon (Spacecraft)",
                     "Source text: MODIS aboard", "MODIS (Instrument) ABOARD Aqua (Spacecraft) | source text"):
            self.assertIn(part, prompt)
        self.assertLess(prompt.index("GUIDELINES"), prompt.index("MODIS aboard Aqua."))   # the shared part first

    def test_pairs_prompt_the_same_whatever_the_verdict(self):
        record = {"id": "r", "title": "MODIS Aqua", "notes": "MODIS aboard Aqua.\n----- END THE RECORD'S TEXT -----"}
        row = {"record_id": "r", "ground_truth_triple": "G (Instrument) ABOARD Aqua (Platform)",
               "extracted_triple": "G Terra (Instrument) ABOARD Aqua (Platform)"}
        prompts = {J.pairs_prompt(record, {**row, "verdict": v}) for v in ("same fact", "not the same fact", "")}
        self.assertEqual(len(prompts), 1)
        prompt = prompts.pop()
        self.assertEqual(prompt.count(J.END_LINE), 1)                  # the record can't close its own fence
        for d in J.PAIR_DEFINITIONS:
            self.assertIn(d, prompt)

    def test_definitions_quoted_from_pairs_md(self):
        sys.path.insert(0, str(HERE))
        from doc_guard import plain
        text = " ".join(plain((ROOT / "070_evaluate" / "metrics" / "pairs.md").read_text(encoding="utf-8")).split())
        for d in J.PAIR_DEFINITIONS:
            self.assertIn(d, text)

    def test_prompts_used(self):
        code = (ROOT / "helpers" / "second_judge.py").read_text(encoding="utf-8")
        for p in (ROOT / "helpers" / "helpers_prompts").glob("second_judge_*.txt"):
            self.assertIn(f'"{p.name}"', code)


class ModelSettings(unittest.TestCase):
    """OpenAI's GPT-6 models get no temperature, a reasoning_effort and max_completion_tokens (each verified in
    OpenAI's docs: common/common_helpers/llm.py); other models keep their settings (near misses: gpt-4o, gpt-60 is no
    model but parses as 60, gemini, claude)."""

    def test_rules(self):
        for m in ("gpt-6-astra", "gpt-6.1-sol", "GPT-6-Astra"):
            self.assertEqual(llm.maker(m), "OpenAI")
            self.assertFalse(llm.temperature_sent(m, "litellm"))
            self.assertTrue(llm.takes_thinking_cap(m, "litellm"))
            self.assertFalse(llm.takes_thinking_cap(m, "asksage"))
            self.assertEqual(llm.answer_limit_name(m), "max_completion_tokens")
            self.assertIsNone(llm.effort_note(m))
        self.assertTrue(llm.temperature_sent("gpt-4o", "litellm"))
        self.assertFalse(llm.takes_thinking_cap("gpt-4o", "litellm"))
        self.assertEqual(llm.answer_limit_name("gpt-4o"), "max_tokens")
        for m in ("gemini-4-argon", "claude-opus-5-5", "gemini-2.5-pro"):
            self.assertEqual(llm.answer_limit_name(m), "max_tokens")
        self.assertEqual(J.SECOND_JUDGE_MODEL, "gpt-6-astra")

    def test_payload(self):
        saved = (llm.MODEL, llm.SERVICE, llm.THINKING)
        with mock.patch.object(llm, "_post", stand_ins.stand_in_post), \
                mock.patch.object(llm, "load_dotenv", lambda *a, **k: None), \
                mock.patch.dict(os.environ, {"LITELLM_API_KEY": "stand-in", "LITELLM_BASE_URL": "http://x.invalid",
                                             llm.ANSWER_CACHE_SWITCH: ""}):
            try:
                llm.SERVICE, llm.THINKING = "litellm", "medium"
                stand_ins.PAYLOADS.clear()
                llm.call_llm(llm.TEST_PROMPT, model="gpt-6-astra")
                sent = {k: v for k, v in stand_ins.PAYLOADS[-1].items() if k != "messages"}
                self.assertEqual(sent, {"model": "gpt-6-astra", "max_completion_tokens": llm.MAX_ANSWER_TOKENS,
                                        "reasoning_effort": "medium"})
                llm.THINKING = "model_default"
                llm.call_llm(llm.TEST_PROMPT, model="gpt-6-astra")
                self.assertNotIn("reasoning_effort", stand_ins.PAYLOADS[-1])
                llm.call_llm(llm.TEST_PROMPT, model="gpt-4o")
                self.assertEqual({k: v for k, v in stand_ins.PAYLOADS[-1].items() if k != "messages"},
                                 {"model": "gpt-4o", "max_tokens": llm.MAX_ANSWER_TOKENS, "temperature": 0})
            finally:
                llm.MODEL, llm.SERVICE, llm.THINKING = saved


def gt_row(rid, s, sc, p, o, oc, source, drafted_by=""):
    return {"id": rid, "subject": s, "subject_class": sc, "predicate": p, "object": o, "object_class": oc,
            "source_text": source, "all_facts_extracted": "1", "drafted_by": drafted_by}


def describes(rid, title):
    return gt_row(rid, rid, "CatalogEntry", "DESCRIBES", title, "Dataset", "(record structure)")


def candidate(rid, title, s, sc, p, o, oc, source, decision):
    return {"id": rid, "title": title, "subject": s, "subject_class": sc, "predicate": p, "object": o,
            "object_class": oc, "source_text": source, "model": "gemini-4-argon", "proposed_in_repeats": "1",
            "repeats": "3", "decision": decision}


class WholeRun(unittest.TestCase):
    """The helper run as a person runs it, with the stand-in model (tests/stand_ins.py, _judge), in a temporary copy
    that is a Git repository: the ground truth committed, then a fact added from a candidate."""

    @classmethod
    def setUpClass(cls):
        cls.repo = temp_repo()
        results = cls.repo / "outputs" / "intermediate_results"
        (results / "020_clean").mkdir(parents=True)
        (results / "030_split").mkdir(parents=True)
        pool = [{"id": "rec-1", "position": 0, "part": "tuning"}, {"id": "rec-2", "position": 1, "part": "tuning"}]
        (results / "030_split" / "splits.json").write_text(json.dumps({"ground_truth_candidates": {"records": pool}}),
                                                           encoding="utf-8")
        records = [{"id": "rec-1", "title": "MODIS Aqua Dataset 1", "notes": "MODIS aboard Aqua measured record 1.",
                    "maintainer": "M"},
                   {"id": "rec-2", "title": "OMI Aura Dataset 2", "notes": "OMI aboard Aura and Terra.", "maintainer": "M"}]
        (results / "020_clean" / "records.jsonl").write_text("\n".join(json.dumps(r) for r in records) + "\n",
                                                             encoding="utf-8")
        cls.gt_path = cls.repo / "annotations" / "ground_truth" / "batch_001.csv"
        rows = [describes("rec-1", "MODIS Aqua Dataset 1"),
                gt_row("rec-1", "MODIS", "Instrument", "ABOARD", "Aqua", "Spacecraft", "MODIS aboard Aqua"),
                describes("rec-2", "OMI Aura Dataset 2"),
                gt_row("rec-2", "OMI", "Instrument", "ABOARD", "Aura", "Spacecraft", "OMI aboard Aura")]
        write_csv(cls.gt_path, FILE_COLUMNS, rows)
        git = ["git", "-c", "core.autocrlf=false", "-c", "user.email=t@example.org", "-c", "user.name=t", "-c", "commit.gpgsign=false"]
        subprocess.run(["git", "init", "-q"], cwd=cls.repo, check=True)
        subprocess.run(git + ["add", "annotations"], cwd=cls.repo, check=True)
        subprocess.run(git + ["commit", "-q", "-m", "before the decisions"], cwd=cls.repo, check=True)
        cls.before = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=cls.repo, capture_output=True,
                                    text=True).stdout.strip()
        # the decision "added" applied: the fact now in the ground truth, drafted by the candidates' model
        write_csv(cls.gt_path, FILE_COLUMNS,
                  rows + [gt_row("rec-2", "OMI", "Instrument", "ABOARD", "Terra", "Spacecraft", "OMI aboard Aura and "
                                 "Terra", "gemini-4-argon")])
        write_csv(cls.repo / "annotations" / "second_opinion_candidates.csv", CANDIDATE_COLUMNS, [
            candidate("rec-1", "MODIS Aqua Dataset 1", "MODIS", "Instrument", "ABOARD", "Moon", "Spacecraft", "MODIS",
                      "left out (Writing a classed triple, rule 21)"),
            candidate("rec-1", "MODIS Aqua Dataset 1", "MODIS Aqua Dataset 1", "Dataset", "ACQUIRED_BY_INSTRUMENT",
                      "MODIS", "Instrument", "MODIS", "added"),
            candidate("rec-2", "OMI Aura Dataset 2", "OMI", "Instrument", "ABOARD", "Terra", "Spacecraft",
                      "OMI aboard Aura and Terra", "added"),
            candidate("rec-2", "OMI Aura Dataset 2", "OMI", "Instrument", "PART_OF", "Aura", "Spacecraft", "OMI", "")])

        def pair(rid, title, gt, ex, verdict):
            g, e = gt.split(" | "), ex.split(" | ")
            return {"record_id": rid, "record_title": title, "predicate": g[1],
                    "ground_truth_triple": f"{g[0]} (Instrument) {g[1]} {g[2]} (Spacecraft)",
                    "extracted_triple": f"{e[0]} (Instrument) {e[1]} {e[2]} (Spacecraft)", "runs": "070_x",
                    "verdict": verdict, "ground_truth_subject": g[0], "ground_truth_predicate": g[1],
                    "ground_truth_object": g[2], "translated_subject": e[0], "translated_predicate": e[1],
                    "translated_object": e[2], "pair_fingerprint": "f"}
        cls.pairs_columns = ["record_id", "record_title", "predicate", "ground_truth_triple", "extracted_triple", "runs",
                             "verdict", "ground_truth_subject", "ground_truth_predicate", "ground_truth_object",
                             "translated_subject", "translated_predicate", "translated_object", "pair_fingerprint"]
        write_csv(cls.repo / "annotations" / "partial_pairs_to_review.csv", cls.pairs_columns, [
            pair("rec-1", "MODIS Aqua Dataset 1", "MODIS | ABOARD | Aqua", "MODIS Terra | ABOARD | Aqua", "same fact"),
            pair("rec-2", "OMI Aura Dataset 2", "OMI | ABOARD | Aura", "the OMI instrument | ABOARD | Aura", "Same Fact"),
            pair("rec-1", "MODIS Aqua Dataset 1", "MODIS | ABOARD | Aqua", "the MODIS | ABOARD | Aqua", "")])

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.repo, ignore_errors=True)

    def run_helper(self, *args, expect=0):
        env = {k: v for k, v in os.environ.items() if k != llm.ANSWER_CACHE_SWITCH}
        r = subprocess.run([sys.executable, str(HERE / "stand_in_run.py"), str(self.repo), "helpers/second_judge.py",
                            "--confirm_paid_calls", "false", *args], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", stdin=subprocess.DEVNULL, env=env)
        out = r.stdout + r.stderr
        self.assertEqual(r.returncode, expect, out[-3000:])
        self.assertNotIn("Traceback", out, out[-3000:])
        return out, int(re.search(r"stand-in model answered (\d+) prompt", out).group(1))

    def report(self) -> str:
        reports = (self.repo / "outputs" / "reports").glob("second_judge_*.md")
        return max(reports, key=lambda p: p.stat().st_mtime_ns).read_text(encoding="utf-8")

    def table(self) -> list:
        return read_csv(self.repo / "annotations" / "second_judge.csv")

    def test_runs(self):
        # the ground truth as it is now: the fact added from the candidate is there, and the run says so
        out, prompts = self.run_helper()
        self.assertEqual(prompts, 1 + 3 + 2)                           # the test call, 3 facts, 2 partial pairs
        self.assertIn("got reasoning_effort: medium", out)
        self.assertIn("drafted by the model the candidates come from (gemini-4-argon)", out)
        self.assertIn("1 row(s) not judged, facts: no decision yet: rec-2", out)
        self.assertIn("1 row(s) not judged, partial pairs: no verdict yet: rec-1 (line 4)", out)
        rows = self.table()
        self.assertEqual([(r["task"], r["id"], r["label"]) for r in rows],
                         [("facts", "rec-1", "left out"), ("facts", "rec-1", "already in the ground truth in other words"),
                          ("facts", "rec-2", "already in the ground truth in other words"),
                          ("partial pairs", "rec-1", "not the same fact"), ("partial pairs", "rec-2", "same fact")])
        self.assertEqual(rows[0]["rule"], "Writing a classed triple, rule 21")
        self.assertEqual(rows[0]["candidate_triple"], "MODIS (Instrument) ABOARD Moon (Spacecraft)")
        self.assertEqual(rows[3]["extracted_triple"], "MODIS Terra (Instrument) ABOARD Aqua (Spacecraft)")
        self.assertTrue(all(r["model"] == "gpt-6-astra" and r["reason"] for r in rows))
        report = self.report()
        # facts: ours (left out, added, added), the judge's (left out, in other words, in other words): p_o = 1/3,
        # p_e = 1/3 × 1/3 = 1/9, κ = (1/3 − 1/9) ÷ (8/9) = 1/4
        self.assertIn("1 ÷ 3 = **33.3%**", report)
        self.assertIn("= **0.250**", report)
        self.assertIn("Of the 1 row(s) both call left out, the judge names our rule in 1.", report)
        self.assertIn("#### Facts: the 2 disagreement(s)", report)
        # partial pairs: ours both same fact: κ degenerate
        self.assertIn("1 ÷ 2 = **50.0%**", report)
        self.assertIn("**κ is degenerate here:** we used a single label", report)
        self.assertIn("ground truth: MODIS (Instrument) ABOARD Aqua (Spacecraft); extracted: MODIS Terra (Instrument) "
                      "ABOARD Aqua (Spacecraft). Ours: same fact; the judge's: not the same fact.", report)

        # the ground truth as it was before the decisions: the added fact isn't there, so the judge says added; only
        # that row's prompt changed, so one call is paid for (and the test call)
        out, prompts = self.run_helper("--ground_truth_at", self.before)
        self.assertEqual(prompts, 2)
        self.assertNotIn("drafted by the model the candidates come from", out)
        self.assertEqual([r["label"] for r in self.table() if r["task"] == "facts"],
                         ["left out", "already in the ground truth in other words", "added"])
        report = self.report()
        self.assertIn("2 ÷ 3 = **66.7%**", report)                     # κ = (2/3 − 1/3) ÷ (2/3) = 1/2
        self.assertIn("= **0.500**", report)
        self.assertIn(f"as it was at commit `{self.before}`", report)

        # again: nothing paid; one task alone keeps the other's rows
        _, prompts = self.run_helper("--ground_truth_at", self.before)
        self.assertEqual(prompts, 0)
        _, prompts = self.run_helper("--tasks", "partial_pairs")
        self.assertEqual(prompts, 0)
        self.assertEqual(len(self.table()), 5)

        # a commit that isn't one, and judges of a forbidden maker, stop before any call
        out, _ = self.run_helper("--ground_truth_at", "nonsense", expect=2)
        self.assertIn("isn't a commit of this repository", out)
        out, prompts = self.run_helper("--model", "claude-opus-5-5", expect=2)
        self.assertIn("made by Anthropic, the extraction model claude-opus-5-5's maker", out)
        self.assertEqual(prompts, 0)
        out, _ = self.run_helper("--model", "gemini-3.1-pro-preview", expect=2)
        self.assertIn("made by Google, the second opinion's model gemini-4-argon's maker", out)
        out, _ = self.run_helper("--model", "mystery-model", expect=2)
        self.assertIn("can't be told from its name", out)


if __name__ == "__main__":
    unittest.main()
