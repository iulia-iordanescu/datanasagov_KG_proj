"""Records left out because a model call failed (common/common_helpers/dropped.py): why each failed, counted by reason
and by maintainer, and the report section every step (040, 050, 060, 070) shows, with the near-misses."""
import unittest
from types import SimpleNamespace

import support  # noqa: F401  (puts the repository on the import path)
from common import dropped, llm
from common.stop import Stop


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
        self.assertEqual(dropped.kind(llm.Refused("the model refused to answer: prose")), "refused")   # llm.classify_reply
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
        self.assertEqual(dropped.kind_from_text("piece 1: the model refused to answer: the model declined to answer, "
                                                "in prose (finish_reason 'stop', 38 characters)"), "refused")
        self.assertEqual(dropped.kind_from_text("piece 1: the service refused this request (HTTP 400)"), "other")
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
        schema = tmp / "ground_truth_schema.txt"     # without its held-out-only entries: the pool here is made up
        schema.write_text(support.without_held_out_only_text(
            (ROOT / "annotations" / "ground_truth_schema.txt").read_text(encoding="utf-8-sig")), encoding="utf-8")
        inputs = {"ground_truth": tmp / "ground_truth" / "batch_*.csv",
                  "ground_truth_schema": schema,
                  "splits": tmp / "splits.json", "candidates": tmp / "candidates.csv",
                  "extracted_triples_details": tmp / "details.json",
                  "extracted_triples": tmp / "extracted.csv",
                  "extracted_triples_removed": tmp / "removed.csv",
                  "schema_used": tmp / "schema_used.json", "records": tmp / "records.jsonl",
                  "partial_reviews": tmp / "reviews.csv"}
        dropped.reset()
        self.addCleanup(dropped.reset)
        ev = module.pick_records(inputs, {"confirm_paid_calls": False})
        # each finished record not evaluated is one entry of the record of discarded items, with why
        not_evaluated = {e["record_id"]: e["reason"] for e in dropped.DISCARDS if e["item_type"] == "record"}
        self.assertEqual(set(not_evaluated), {"r1", "r2", "r3"})
        self.assertIn("060's model calls failed", not_evaluated["r1"])
        self.assertIn("not extracted by 060's last run", not_evaluated["r3"])
        # near miss: a record left out without its entry stops the run at the accounting check of stage 1
        from unittest import mock
        dropped.reset()
        with mock.patch.object(dropped, "discard", lambda *a, **k: None), self.assertRaises(Stop) as caught:
            module.pick_records(inputs, {"confirm_paid_calls": False})
        self.assertIn("Accounting check failed in stage 1 (pick_records): 4 records in the ground truth went in, 1 "
                      "were kept", str(caught.exception))
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


class Discards(unittest.TestCase):
    """The one record of discarded items every pipeline step keeps (dropped.discard, fold, replace, account, write,
    discards_section): one entry per item, and an accounting check that stops a run when an item vanishes without
    a record."""

    def setUp(self):
        dropped.reset()
        self.addCleanup(dropped.reset)

    def test_entries(self):
        a = dropped.discard("stage 1 (x)", "record", "no id", {"title": "T"}, record_id="r1",
                            setting={"max_records": 5}, where="010_harvest/batch_00000.json#3")
        self.assertEqual(a, {"stage": "stage 1 (x)", "action": "discarded", "item_type": "record", "reason": "no id",
                             "setting": {"max_records": 5}, "record_id": "r1", "item": {"title": "T"},
                             "where": "010_harvest/batch_00000.json#3"})
        b = dropped.fold("stage 1 (x)", "record", "repeat", {"id": "r1"}, {"where": "f#0"})
        self.assertEqual((b["action"], b["kept_as"]), ("folded", {"where": "f#0"}))
        self.assertNotIn("setting", b)                                    # only when a setting decided it
        c = dropped.replace("stage 2 (y)", "maintainer", "joined", {"maintainer": "A"}, {"maintainer": "B"})
        self.assertEqual(c["action"], "replaced")
        self.assertEqual(len(dropped.DISCARDS), 3)
        for bad in (("", "record", "why"), ("s", "", "why"), ("s", "record", "")):
            with self.assertRaises(ValueError):                           # every entry says stage, type and why
                dropped.discard(*bad, {})

    def test_account_passes_when_every_item_is_recorded(self):
        since = dropped.mark()
        dropped.discard("s", "record", "a", {})
        dropped.fold("s", "record", "b", {}, {})
        dropped.replace("s", "record", "c", {}, {})                       # replaced: still kept, not counted
        dropped.account("s", "records", 5, 3, since=since)

    def test_near_miss_an_item_vanishes(self):
        """An item removed without a record: the run stops, naming the stage and the counts."""
        since = dropped.mark()
        dropped.discard("s", "record", "a", {})
        with self.assertRaises(Stop) as caught:
            dropped.account("stage 3 (z)", "records read", 5, 3, since=since)
        self.assertIn("Accounting check failed in stage 3 (z): 5 records read went in, 3 were kept and 0 were "
                      "recorded as discarded, so 2 went missing without a record", str(caught.exception))
        self.assertIn("fault in the step's code", str(caught.exception))
        with self.assertRaises(Stop):                                     # another stage's entries don't count
            dropped.account("s", "records", 5, 3, since=since)
        with self.assertRaises(Stop) as caught:                           # recorded twice, or kept and recorded
            dropped.account("s", "records", 3, 3, since=since)
        self.assertIn("recorded as discarded more than once", str(caught.exception))

    def test_account_counts_only_since_the_mark_and_the_type(self):
        dropped.discard("s", "record", "before the mark", {})
        since = dropped.mark()
        dropped.discard("s", "text", "a", {})
        dropped.discard("s", "triple instance", "b", {"kind": "entity class"})
        dropped.account("s", "texts", 2, 1, since=since, item_type="text")
        dropped.account("s", "items", 2, 1, since=since, only=lambda e: e["item"].get("kind") == "entity class")
        with self.assertRaises(Stop):
            dropped.account("s", "texts", 3, 1, since=since, item_type="text")

    def test_write_and_section(self):
        import json
        import shutil
        import tempfile
        from pathlib import Path
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp)
        (tmp / dropped.DISCARDS_FILE).write_text("an earlier run's\n", encoding="utf-8")
        path = dropped.write(tmp)                                         # nothing discarded: an empty file
        self.assertEqual(Path(path).read_text(encoding="utf-8"), "")
        self.assertIn("None: no stage of this run discarded", "\n".join(dropped.discards_section("x/discarded.jsonl")))
        dropped.discard("stage 1 (a)", "record", "no id", {"title": "T|U"})
        dropped.discard("stage 1 (a)", "record", "no id", {"title": "V"})
        dropped.fold("stage 1 (a)", "record", "repeat", {"id": "r"}, {"where": "f#1"})
        path = dropped.write(tmp)
        lines = [json.loads(x) for x in Path(path).read_text(encoding="utf-8").splitlines()]
        self.assertEqual([e["item"] for e in lines], [{"title": "T|U"}, {"title": "V"}, {"id": "r"}])
        text = "\n".join(dropped.discards_section("x/discarded.jsonl"))
        self.assertIn("### Items discarded", text)
        self.assertIn("3 item(s) were discarded", text)
        self.assertIn("`x/discarded.jsonl`", text)
        self.assertIn("| stage 1 (a) | record | discarded | no id | 2 |", text)
        self.assertIn("| stage 1 (a) | record | folded | repeat | 1 |", text)

    def test_run_step_writes_the_file_and_the_section(self):
        """Every pipeline step's run writes the file (listed among its outputs) and the report's section; a step's
        accounting check that fails stops the run, with no file and no manifest."""
        import json
        import logging
        import shutil
        import tempfile
        from pathlib import Path
        from unittest import mock
        from common import step
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        self.addCleanup(logging.shutdown)

        def main(inputs, settings, output):
            since = dropped.mark()
            dropped.discard("stage 1 (main)", "record", "no text", {"id": "b"}, record_id="b")
            dropped.account("stage 1 (main)", "records", 2, 1, since=since)
            return step.Results(headline={}, details="### What this run worked on")

        def leaky(inputs, settings, output):
            since = dropped.mark()                                     # a record removed without a record of it
            dropped.account("stage 1 (main)", "records", 2, 1, since=since)
            return step.Results(headline={})
        patches = [mock.patch.object(step, "RESULTS_DIR", tmp / "results"),
                   mock.patch.object(step, "REPORTS_DIR", tmp / "reports"),
                   mock.patch.object(step, "LOGS_DIR", tmp / "logs"),
                   mock.patch.object(step, "PIPELINE_STEPS", step.PIPELINE_STEPS + ["999_stand_in"])]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        step.run_step("999_stand_in", {}, {}, main, argv=[])
        out = tmp / "results" / "999_stand_in"
        entries = [json.loads(x) for x in (out / dropped.DISCARDS_FILE).read_text(encoding="utf-8").splitlines()]
        self.assertEqual([(e["stage"], e["record_id"], e["reason"]) for e in entries],
                         [("stage 1 (main)", "b", "no text")])
        manifest = json.loads((out / "_manifest.json").read_text(encoding="utf-8"))
        self.assertIn(dropped.DISCARDS_FILE, [r["file"] for r in manifest["outputs"]])
        first = manifest["run_id"]
        report = max((tmp / "reports").glob("999_stand_in_*.md")).read_text(encoding="utf-8")
        self.assertIn("### What this run worked on\n\n### Items discarded", report)
        self.assertIn("| stage 1 (main) | record | discarded | no text | 1 |", report)
        with self.assertRaises(SystemExit) as caught:
            step.run_step("999_stand_in", {}, {}, leaky, argv=[])
        self.assertEqual(caught.exception.code, 2)                         # stopped
        report = max((tmp / "reports").glob("999_stand_in_*.md"), key=lambda p: p.stat().st_mtime_ns)
        self.assertIn("Accounting check failed in stage 1 (main)", report.read_text(encoding="utf-8"))
        # the stopped run wrote no file: the first run's file and manifest stand
        self.assertEqual(json.loads((out / "_manifest.json").read_text(encoding="utf-8"))["run_id"], first)
        self.assertEqual(len((out / dropped.DISCARDS_FILE).read_text(encoding="utf-8").splitlines()), 1)

    def test_only_pipeline_steps_write_it(self):
        """A helper that runs in run_step's frame (py helpers/second_opinion.py) writes no such file."""
        import logging
        import shutil
        import tempfile
        from pathlib import Path
        from unittest import mock
        from common import step
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        self.addCleanup(logging.shutdown)
        with mock.patch.object(step, "RESULTS_DIR", tmp / "results"), mock.patch.object(step, "REPORTS_DIR", tmp / "r"), \
                mock.patch.object(step, "LOGS_DIR", tmp / "logs"):
            step.run_step("999_stand_in", {}, {}, lambda i, s, o: step.Results(headline={}), argv=[])
        self.assertFalse((tmp / "results" / "999_stand_in" / dropped.DISCARDS_FILE).exists())

    def test_every_step_records(self):
        """Every pipeline step's helpers record what they discard through dropped.py (and so through run_step)."""
        from support import ROOT
        from common.step import PIPELINE_STEPS
        for name in PIPELINE_STEPS:
            text = "".join(p.read_text(encoding="utf-8") for p in (ROOT / name / f"{name}_helpers").glob("*.py"))
            self.assertRegex(text, r"dropped\.(discard|fold)\(", name)
            self.assertIn("dropped.account(", text + (ROOT / "common" / "common_helpers" / "extraction.py")
                          .read_text(encoding="utf-8"), name)


class ExtractionRows(unittest.TestCase):
    """050 and 060 record each item build_rows (and 060's checks) removed from a record's replies, the duplicate folded
    into the copy kept, and the describes class that lost (extraction.record_removed); and each record left out
    after a failed model call (extraction.record_left_out). Near misses: an item left unrecorded stops the run."""

    def setUp(self):
        dropped.reset()
        self.addCleanup(dropped.reset)

    def build(self):
        from common import extraction
        from common.validate import SchemaEntries
        text = "MODIS is aboard Aqua. Terra carries ASTER."
        t1 = {"subject": "MODIS", "subject_class": "Instrument", "predicate": "IS_ABOARD", "object": "Aqua",
              "object_class": "Spacecraft", "source_text": "MODIS is aboard Aqua."}
        t2 = {"subject": "Terra", "subject_class": "Spacecraft", "predicate": "CARRIES", "object": "ASTER",
              "object_class": "Instrument", "source_text": "Terra carries ASTER."}
        replies = [{"describes_class": "Dataset", "triples": [t1, {"subject": ""}, t2]},
                   {"describes_class": "Dataset", "triples": [dict(t1)]},
                   {"describes_class": "Collection", "triples": []}]
        entries = SchemaEntries({"entity_classes": {"Instrument": "", "Spacecraft": "", "Dataset": ""},
                                 "predicates": {"IS_ABOARD": "", "CARRIES": ""}, "patterns": []})
        rows, removed = extraction.build_rows("r1", "T", text, replies, entries)
        return extraction, replies, rows, removed

    def test_recorded(self):
        extraction, replies, rows, removed = self.build()
        extraction.record_removed("stage 3 (build_rows)", "r1", replies, rows, removed)
        by = {e["reason"].split(":")[0]: e for e in dropped.DISCARDS}
        self.assertEqual(set(by), {"malformed", "duplicate", "named by a text piece, but more text pieces named "
                                                             "another one (or as many, and it was named first)"})
        self.assertEqual(by["duplicate"]["action"], "folded")
        self.assertEqual(by["duplicate"]["kept_as"]["subject"], "MODIS")
        self.assertEqual(by["malformed"]["record_id"], "r1")
        replaced = [e for e in dropped.DISCARDS if e["action"] == "replaced"]
        self.assertEqual([e["item"] for e in replaced], [{"describes_class": "Collection"}])

    def test_near_miss_an_unrecorded_removal(self):
        extraction, replies, rows, removed = self.build()
        with self.assertRaises(Stop):
            extraction.record_removed("stage 3 (build_rows)", "r1", replies, rows, removed[:-1])   # one forgotten
        dropped.reset()
        with self.assertRaises(Stop):                                     # a row kept that the replies don't hold
            extraction.record_removed("stage 3 (build_rows)", "r1", replies, rows + [rows[-1]], removed)

    def test_left_out(self):
        from common import extraction
        r = replies({"b": "piece 1: refused"}, kinds={"b": "refused"})
        r.of = {"a": [{}]}
        extraction.record_left_out("stage 2 (ask_model)", r, [{"id": "a"}, {"id": "b", "maintainer": "M"}])
        self.assertEqual([(e["record_id"], e["item_type"]) for e in dropped.DISCARDS], [("b", "record")])
        self.assertIn(dropped.KINDS["refused"], dropped.DISCARDS[0]["reason"])
        dropped.reset()
        r.failed = {}                                                     # near miss: b neither answered nor failed
        with self.assertRaises(Stop):
            extraction.record_left_out("stage 2 (ask_model)", r, [{"id": "a"}, {"id": "b"}])


class ReadIdsFolds(unittest.TestCase):
    def test_repeated_id(self):
        from common.records_io import read_ids
        dropped.reset()
        self.addCleanup(dropped.reset)
        self.assertEqual(read_ids("a, b, a"), ["a", "b"])
        self.assertEqual(dropped.DISCARDS, [])                            # no stage given: nothing recorded
        self.assertEqual(read_ids("a, b, a", "stage 1 (pick_records)"), ["a", "b"])
        self.assertEqual([(e["action"], e["record_id"]) for e in dropped.DISCARDS], [("folded", "a")])


if __name__ == "__main__":
    unittest.main()
