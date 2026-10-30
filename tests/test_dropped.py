"""Records left out because a model call failed (common/common_helpers/dropped.py): why each failed, counted by reason
and by maintainer, and the report section every step (040, 050, 060, 070) shows, with the near-misses."""
import unittest
from types import SimpleNamespace

import support  # noqa: F401  (puts the repository on the import path)
from common import dropped, llm


def replies(failed, cut_off=(), kinds=None):
    r = SimpleNamespace(failed=dict(failed), cut_off={i: {} for i in cut_off})
    if kinds is not None:
        r.kinds = kinds
    return r


def error(cls, message="x", finish_reason=None):
    e = cls(message)
    e.finish_reason = finish_reason
    return e


class Kind(unittest.TestCase):
    def test_each_kind(self):
        self.assertEqual(dropped.kind(error(llm.ApiError, finish_reason="content_filter")), "refused")
        self.assertEqual(dropped.kind(error(llm.CutOff, finish_reason="length")), "cut_off")
        self.assertEqual(dropped.kind(llm.WrongShape("no triples list")), "malformed")
        self.assertEqual(dropped.kind(llm.ApiError("HTTP 403")), "service_error")
        self.assertEqual(dropped.kind(RuntimeError("HTTP 503 after 4 attempts")), "service_error")
        self.assertEqual(dropped.kind(KeyError("bug")), "other")

    def test_near_misses(self):
        # a cut-off answer that a filter stopped is a refusal: asking again with a higher limit won't help
        self.assertEqual(dropped.kind(error(llm.CutOff, finish_reason="content_filter")), "refused")
        # the model maker's own reason counts too, in any case
        e = llm.ApiError("x")
        e.native_finish_reason = "SAFETY"
        self.assertEqual(dropped.kind(e), "refused")
        # an ordinary finish_reason is not a refusal
        self.assertEqual(dropped.kind(error(llm.ApiError, finish_reason="stop")), "service_error")

    def test_from_text(self):
        self.assertEqual(dropped.kind_from_text("piece 1: the model gave no usable answer (finish_reason "
                                                "'content_filter', 0 characters)"), "refused")
        self.assertEqual(dropped.kind_from_text("piece 2: prompt safety check failed"), "other")   # the word alone
        self.assertEqual(dropped.kind_from_text(""), "other")


class LeftOut(unittest.TestCase):
    ITEMS = [{"id": "a", "maintainer": "GeneLab Outreach"}, {"id": "b", "maintainer": None}, {"id": "c"},
             {"id": "d", "maintainer": "Thomas Morgan"}]

    def test_uses_the_kinds_ask_model_kept(self):
        got = dropped.left_out(replies({"a": "w1", "b": "w2"}, kinds={"a": "refused", "b": "malformed"}), self.ITEMS)
        self.assertEqual([(e["id"], e["maintainer"], e["reason"], e["why"]) for e in got],
                         [("a", "GeneLab Outreach", "refused", "w1"), ("b", dropped.UNDEFINED, "malformed", "w2")])

    def test_without_kinds(self):
        got = dropped.left_out(replies({"c": "piece 1: x", "d": "(finish_reason 'content_filter', 0)"},
                                       cut_off=["c"]), self.ITEMS)
        self.assertEqual([(e["id"], e["reason"]) for e in got], [("c", "cut_off"), ("d", "refused")])
        self.assertEqual(got[0]["maintainer"], dropped.UNDEFINED)        # no maintainer key at all

    def test_none_failed(self):
        self.assertEqual(dropped.left_out(replies({}), self.ITEMS), [])

    def test_details_counts(self):
        entries = dropped.left_out(replies({"a": "w", "d": "w"}, kinds={"a": "refused", "d": "refused"}), self.ITEMS)
        d = dropped.details(entries)
        self.assertEqual(d["by_reason"], {"refused": 2})
        self.assertEqual(d["by_maintainer"], {"GeneLab Outreach": 1, "Thomas Morgan": 1})
        self.assertEqual([e["id"] for e in d["records"]], ["a", "d"])


class Section(unittest.TestCase):
    ITEMS = [{"id": "a", "maintainer": "GeneLab Outreach"}, {"id": "b", "maintainer": "GeneLab Outreach"},
             {"id": "c", "maintainer": "Thomas | Morgan"}]

    def test_none(self):
        lines = dropped.section([], self.ITEMS, "the output", "d.json")
        self.assertEqual(lines[0], "### Records left out")
        self.assertIn("None: every record chosen (3) was answered", "\n".join(lines))

    def test_some(self):
        entries = [{"id": "a", "maintainer": "GeneLab Outreach", "reason": "refused", "why": "w"},
                   {"id": "c", "maintainer": "Thomas | Morgan", "reason": "cut_off", "why": "w"}]
        text = "\n".join(dropped.section(entries, self.ITEMS, "the output", "d.json"))
        self.assertIn("2 of the 3 record(s) chosen were left out of the output", text)
        self.assertIn("`d.json` (key `left_out`)", text)
        self.assertIn(f"| {dropped.KINDS['refused']} | 1 |", text)
        self.assertIn(f"| {dropped.KINDS['cut_off']} | 1 |", text)
        self.assertNotIn(dropped.KINDS["malformed"], text)                 # only reasons that occurred
        self.assertIn("| GeneLab Outreach | 1 | 2 |", text)               # left out, of those chosen
        self.assertIn(r"| Thomas \| Morgan | 1 | 1 |", text)               # a "|" is escaped: it can't break the table

    def test_no_details_file(self):
        entries = [{"id": "a", "maintainer": "x", "reason": "other", "why": "w"}]
        self.assertIn("in this report's warnings", "\n".join(dropped.section(entries, self.ITEMS, "the batch", None)))

    def test_same_wording_everywhere(self):
        # every step calls this one function; the wording differs only by `where` and the file named
        entries = [{"id": "a", "maintainer": "GeneLab Outreach", "reason": "refused", "why": "w"}]
        one = dropped.section(entries, self.ITEMS, "X", "f")
        two = dropped.section(entries, self.ITEMS, "Y", "g")
        self.assertEqual([l for l in one if "X" not in l and "`f`" not in l],
                         [l for l in two if "Y" not in l and "`g`" not in l])


class EveryStepUsesIt(unittest.TestCase):
    """The steps that call a model per record report their left-out records through dropped.py, not their own code."""
    def test_steps(self):
        from support import ROOT
        for path in ("040_induce_schema/040_induce_schema_helpers/moves.py", "050_annotate/050_annotate_helpers/moves.py",
                     "060_extract/060_extract_helpers/moves.py", "070_evaluate/070_evaluate_helpers/moves.py"):
            text = (ROOT / path).read_text(encoding="utf-8")
            self.assertIn("dropped.section(", text, path)
        for path in ("040_induce_schema/040_induce_schema_helpers/moves.py", "050_annotate/050_annotate_helpers/moves.py",
                     "060_extract/060_extract_helpers/moves.py"):
            self.assertIn('"left_out": dropped.details(', (ROOT / path).read_text(encoding="utf-8"), path)


class Step070(unittest.TestCase):
    """070 says which finished records extraction failed for, and why, apart from those 060 didn't choose."""

    def test_failed_and_not_chosen(self):
        import importlib.util
        import json
        import shutil
        import sys
        import tempfile
        from pathlib import Path
        from support import ROOT
        from common import ground_truth, partial_reviews
        from common.files import write_csv
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp)
        parts = ["tuning", "tuning", "tuning", "tuning"]
        ids = [f"r{i}" for i in range(len(parts))]
        pool = [{"id": i, "position": n, "part": p} for n, (i, p) in enumerate(zip(ids, parts))]
        (tmp / "splits.json").write_text(json.dumps({"ground_truth_candidates": {"records": pool}}), encoding="utf-8")
        (tmp / "records.jsonl").write_text("\n".join(json.dumps({"id": i, "title": f"t {i}", "notes": f"n {i}",
                                                                 "maintainer": "GeneLab Outreach" if i == "r1" else "M"})
                                                     for i in ids), encoding="utf-8")
        (tmp / "ground_truth").mkdir()
        write_csv(tmp / "ground_truth" / "batch_000.csv", ground_truth.COLUMNS,
                  [dict(zip(ground_truth.COLUMNS, [i, "", "", "", "", "", "", "1"])) for i in ids])
        # 060: r0 extracted; r1 refused (named in left_out); r2 failed in an older 060 (status only); r3 not chosen
        (tmp / "details.json").write_text(json.dumps({"made": {}, "records": [
            {"id": "r0", "status": "extracted"}, {"id": "r1", "status": "failed", "error": "piece 1: x"},
            {"id": "r2", "status": "failed", "error": "piece 1: no usable answer (finish_reason 'content_filter', 0)"}],
            "left_out": {"records": [{"id": "r1", "maintainer": "GeneLab Outreach", "reason": "refused", "why": "w"}]}}),
            encoding="utf-8")
        write_csv(tmp / "extracted.csv", ["id"], [])
        write_csv(tmp / "removed.csv", ["id", "reason"], [])
        write_csv(tmp / "candidates.csv", ["id", "stratum"], [{"id": i, "stratum": "s"} for i in ids])
        (tmp / "schema_used.json").write_text(json.dumps({"learned_from": {"known": True, "ids": []}}), encoding="utf-8")
        (tmp / "reviews.csv").write_text(",".join(partial_reviews.COLUMNS) + "\n", encoding="utf-8")
        spec = importlib.util.spec_from_file_location("records_070_dropped",
                                                      ROOT / "070_evaluate" / "070_evaluate_helpers" / "records.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules["records_070_dropped"] = module
        spec.loader.exec_module(module)
        ev = module.pick_records({"ground_truth": tmp / "ground_truth" / "batch_*.csv",
                                  "ground_truth_schema": ROOT / "annotations" / "ground_truth_schema.txt",
                                  "splits": tmp / "splits.json", "candidates": tmp / "candidates.csv",
                                  "extracted_triples_details": tmp / "details.json",
                                  "extracted_triples": tmp / "extracted.csv",
                                  "extracted_triples_removed": tmp / "removed.csv",
                                  "schema_used": tmp / "schema_used.json", "records": tmp / "records.jsonl",
                                  "partial_reviews": tmp / "reviews.csv"}, {"confirm_paid_calls": False})
        self.assertEqual([(e["id"], e["reason"], e["maintainer"]) for e in ev.extraction_failed],
                         [("r1", "refused", "GeneLab Outreach"), ("r2", "refused", "M")])
        self.assertEqual(ev.left_out["finished, but not extracted by 060's last run"], ["r3"])
        self.assertEqual(ev.left_out["finished, but 060's model calls failed for them in its last run"], ["r1", "r2"])
        note = next(n for n in ev.notes if "060's model calls failed" in n)
        self.assertIn("r1 (refused; maintainer GeneLab Outreach)", note)
        self.assertEqual(len(ev.finished), 4)
        text = "\n".join(dropped.section(ev.extraction_failed, ev.finished, "this evaluation", "f.json"))
        self.assertIn("2 of the 4 record(s) chosen were left out of this evaluation", text)
        self.assertIn("| GeneLab Outreach | 1 | 1 |", text)


class ReAsks(unittest.TestCase):
    """Replies asked once more because they weren't usable (llm.call_llm_json), counted per run (llm.REASKS)."""

    def test_lines(self):
        none = dropped.reasks_lines({"not_json": 0, "wrong_shape": 0, "fixed": 0, "still_failed": 0})
        self.assertEqual(none[0], "### Replies asked again")
        self.assertIn("None: every reply", "\n".join(none))
        text = "\n".join(dropped.reasks_lines({"not_json": 2, "wrong_shape": 1, "fixed": 2, "still_failed": 1}))
        self.assertIn("3 repl(ies) came back unusable the first time", text)
        self.assertIn("2 not a JSON object, 1 a JSON object of the wrong shape", text)
        self.assertIn("Asking again fixed 2; 1 were still unusable", text)

    def test_headline(self):
        self.assertEqual(dropped.reasks_headline({"not_json": 1, "wrong_shape": 0, "fixed": 1, "still_failed": 0}),
                         {"replies asked again": 1, "replies fixed by asking again": 1, "replies still unusable": 0})
        self.assertEqual(dropped.reasks_headline({})["replies asked again"], 0)       # a run that asked nothing

    def test_counted_by_call_llm_json(self):
        replies = iter(["not json at all", '{"triples": []}',          # 1: not JSON, fixed
                        '{"x": 1}', '{"x": 2}',                          # 2: wrong shape twice: still unusable
                        '{"triples": []}'])                              # 3: fine the first time
        real = llm.call_llm
        llm.call_llm = lambda prompt, **kw: next(replies)
        self.addCleanup(setattr, llm, "call_llm", real)
        for k in llm.REASKS:
            llm.REASKS[k] = 0
        check = lambda d: None if "triples" in d else "no triples list"
        llm.call_llm_json("p", check=check)
        with self.assertRaises(llm.BadReply):
            llm.call_llm_json("p", check=check)
        llm.call_llm_json("p", check=check)
        self.assertEqual(llm.REASKS, {"not_json": 1, "wrong_shape": 1, "fixed": 1, "still_failed": 1})


if __name__ == "__main__":
    unittest.main()
