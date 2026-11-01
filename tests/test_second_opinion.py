"""The second opinion (helpers/second_opinion.py): which finished records it drafts again (every part; held-out ones
too, their draft's facts the ground truth lacks never listed), each ground truth triple found (exact, partial) or not
by 070's pairing without translation, with the near misses; what --apply true writes into annotations/second_opinion.csv
(two models merged, the same model again replaced, a reworded triple dropped, other records kept); step 070's recall
and partial F1 by group (found, not found, not checked) and its report; the whole helper run with the stand-in model
in a temporary copy, paying nothing the second time; and the settings sent to gemini-4-argon. Step 070's side:
tests/test_evaluate_second_opinion.py."""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from support import ROOT, temp_repo

from common import llm                                                        # noqa: E402
from common.files import read_csv, write_csv                                  # noqa: E402
from common.ground_truth import FILE_COLUMNS, read_ground_truth              # noqa: E402
from common.second_opinion import (COLUMNS, FOUND, NOT_CHECKED, NOT_FOUND, groups_of, key_of, read_table,  # noqa: E402
                                   stale_rows, write_table)
from common.stop import Stop                                                  # noqa: E402

HERE = Path(__file__).resolve().parent


def load_helper():
    """helpers/second_opinion.py as a module (it loads 050's moves and 070's pairing itself)."""
    if "second_opinion_helper" in sys.modules:
        return sys.modules["second_opinion_helper"]
    spec = importlib.util.spec_from_file_location("second_opinion_helper", ROOT / "helpers" / "second_opinion.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def triple(s, sc, p, o, oc, source="x"):
    return {"subject": s, "subject_class": sc, "predicate": p, "object": o, "object_class": oc, "source_text": source}


def gt_row(rid, t, finished="1", drafted_by=""):
    return {"id": rid, **{k: t.get(k, "") for k in FILE_COLUMNS if k not in ("id", "all_facts_extracted", "drafted_by")},
            "all_facts_extracted": finished, "drafted_by": drafted_by}


def describes(rid, title="T"):
    return {"id": rid, "subject": rid, "subject_class": "CatalogEntry", "predicate": "DESCRIBES", "object": title,
            "object_class": "Dataset", "source_text": "(record structure)"}


POOL = [{"id": "t0", "position": 0, "part": "tuning"}, {"id": "h1", "position": 1, "part": "held-out"},
        {"id": "t2", "position": 2, "part": "tuning"}, {"id": "u3", "position": 3, "part": "tuning"}]
GT_T0 = [triple("MODIS", "Instrument", "ABOARD", "Aqua", "Spacecraft"),
         triple("MODIS Snow Cover", "Dataset", "ACQUIRED_BY_INSTRUMENT", "MODIS", "Instrument"),
         triple("CERES", "Instrument", "ABOARD", "Terra", "Spacecraft")]
GT_H1 = [triple("AIRS", "Instrument", "ABOARD", "Aqua", "Spacecraft")]
GT_T2 = [triple("OMI", "Instrument", "ABOARD", "Aura", "Spacecraft")]


class Fixture(unittest.TestCase):
    """A ground truth of three finished records (t0 and t2 tuning, h1 held-out) and one unfinished (u3), in a
    temporary folder, read as the helper reads it."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="kg_so_"))
        folder = cls.tmp / "ground_truth"
        folder.mkdir()
        rows = [gt_row("t0", describes("t0"))] + [gt_row("t0", t, drafted_by="gemini-2.5-pro") for t in GT_T0[:2]] \
            + [gt_row("t0", GT_T0[2])] + [gt_row("h1", t) for t in GT_H1] + [gt_row("t2", t) for t in GT_T2] \
            + [gt_row("u3", triple("MLS", "Instrument", "ABOARD", "Aura", "Spacecraft"), finished="0")]
        write_csv(folder / "batch_001.csv", FILE_COLUMNS, rows)
        cls.helper = load_helper()
        cls.gt = read_ground_truth(folder, POOL)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp)

    def chosen(self, ids=("t0", "h1", "t2")):
        c = self.helper.records_stage.Chosen()
        c.ground_truth = self.gt
        c.positions = {r["id"]: r["position"] for r in POOL}
        c.parts = {r["id"]: r["part"] for r in POOL}
        c.items = [{"id": i, "position": c.positions[i], "title": f"Title {i}", "pieces": ["p"]} for i in ids]
        return c

    def drafts(self, rows: dict):
        d = self.helper.annotate.Drafts()
        d.rows = {rid: [{**describes(rid), "errors": [], "flags": []}]
                  + [{**t, "id": rid, "errors": [], "flags": []} for t in ts] for rid, ts in rows.items()}
        return d

    def matched(self, rows: dict, ids=("t0", "h1", "t2")):
        return self.helper.match(self.chosen(ids), self.drafts(rows))


class Matching(Fixture):

    def test_exact_partial_and_not_found(self):
        draft = {"t0": [triple("the MODIS", "Instrument", "ABOARD", "Aqua", "Spacecraft"),                 # exact
                        triple("MODIS Snow Cover 5-Min L2 Swath", "Dataset", "ACQUIRED_BY_INSTRUMENT",
                               "Moderate Resolution Imaging Spectroradiometer (MODIS)", "Instrument"),   # partial
                        triple("CERES", "Instrument", "ABOARD", "Aqua", "Spacecraft")],                    # another object: not found
                 "h1": GT_H1, "t2": GT_T2}
        m = self.matched(draft)
        levels = [level for _, level, _ in m.per_record["t0"]["gt"]]
        self.assertEqual(levels, ["exact", "partial", None])
        self.assertEqual([t["object"] for t in m.per_record["t0"]["draft_only"]], ["Aqua"])
        statuses = [(r["record_id"], r["status"]) for r in m.rows]
        self.assertEqual(statuses.count(("t0", self.helper.FOUND_EXACT)), 1)
        self.assertEqual(statuses.count(("t0", self.helper.FOUND_PARTIAL)), 1)
        self.assertEqual(statuses.count(("t0", self.helper.NOT_FOUND_STATUS)), 1)
        self.assertEqual(statuses.count(("t0", self.helper.DRAFT_ONLY)), 1)
        found = next(r for r in m.rows if r["status"] == self.helper.FOUND_EXACT)
        self.assertEqual((found["draft_subject"], found["ground_truth_drafted_by"], found["entity_classes_agree"]),
                         ("the MODIS", "gemini-2.5-pro", "yes"))
        self.assertTrue(all(r["origin"] for r in m.rows))

    def test_near_misses(self):
        """The same subject and object with another predicate, or another entity class only, and a subject that
        overlaps without whole words."""
        draft = {"t0": [triple("MODIS", "Instrument", "ACQUIRED_BY_INSTRUMENT", "Aqua", "Spacecraft"),   # predicate differs
                        triple("MODIS Snow Cover", "Dataset", "ACQUIRED_BY_INSTRUMENT", "MODIS", "Sensor"),   # entity class differs: found, not strict
                        triple("CERESFM5", "Instrument", "ABOARD", "Terra", "Spacecraft")]               # not whole words
                 }
        m = self.matched(draft, ids=("t0",))
        gt = m.per_record["t0"]["gt"]
        self.assertEqual([level for _, level, _ in gt], [None, "exact", None])
        self.assertEqual([agree for _, _, agree in gt], [None, False, None])
        self.assertEqual(len(m.per_record["t0"]["draft_only"]), 2)

    def test_describes_triples_never_matched(self):
        m = self.matched({"t2": [describes("t2")] + GT_T2}, ids=("t2",))
        self.assertEqual(len(m.per_record["t2"]["gt"]), 1)             # the ground truth's describes triple isn't a triple to find
        self.assertEqual(m.per_record["t2"]["draft_only"], [])         # nor the draft's

    def test_held_out_facts_counted_not_listed(self):
        draft = {"h1": GT_H1 + [triple("AIRS", "Instrument", "ABOARD", "Terra", "Spacecraft")],
                 "t2": GT_T2 + [triple("OMI", "Instrument", "ABOARD", "Terra", "Spacecraft")]}
        m = self.matched(draft, ids=("h1", "t2"))
        self.assertEqual(len(m.per_record["h1"]["draft_only"]), 1)     # counted
        listed = [r for r in m.rows if r["status"] == self.helper.DRAFT_ONLY]
        self.assertEqual([r["record_id"] for r in listed], ["t2"])      # the tuning record's only
        self.assertEqual([r["status"] for r in m.rows if r["record_id"] == "h1"], [self.helper.FOUND_EXACT])

    def test_order_free_and_one_partner_each(self):
        draft = {"t0": [triple("MODIS", "Instrument", "ABOARD", "Aqua", "Spacecraft")] * 2}   # stated twice: one pair
        m = self.matched(draft, ids=("t0",))
        self.assertEqual([level for _, level, _ in m.per_record["t0"]["gt"]], ["exact", None, None])
        self.assertEqual(len(m.per_record["t0"]["draft_only"]), 1)
        a = self.matched({"t0": GT_T0}, ids=("t0",)).rows
        b = self.matched({"t0": list(reversed(GT_T0))}, ids=("t0",)).rows
        self.assertEqual([(r["ground_truth_subject"], r["status"]) for r in a], [(r["ground_truth_subject"], r["status"]) for r in b])

    def test_failed_record_not_matched(self):
        m = self.matched({"t2": GT_T2}, ids=("t0", "t2"))
        self.assertEqual(m.not_drafted, ["t0"])
        self.assertEqual(list(m.per_record), ["t2"])


class Apply(Fixture):

    def setUp(self):
        self.path = self.tmp / f"second_opinion_{self._testMethodName}.csv"

    def apply(self, rows, model, ids=("t0", "h1", "t2")):
        llm.MODEL = model
        m = self.matched(rows, ids)
        return self.helper.apply(self.chosen(ids), m, {"apply": True}, self.path), read_table(self.path)

    def test_nothing_without_the_setting(self):
        self.assertIsNone(self.helper.apply(self.chosen(), self.matched({"t2": GT_T2}, ("t2",)), {"apply": False}, self.path))
        self.assertFalse(self.path.exists())

    def test_two_models_merge_and_the_same_model_replaces(self):
        draft_a = {"t0": GT_T0[:1], "h1": GT_H1, "t2": []}
        applied, table = self.apply(draft_a, "model-a")
        self.assertEqual((applied["rows"], applied["rebuilt"], applied["dropped"]), (5, 5, 0))
        row = table[key_of("t0", GT_T0[0])]
        self.assertEqual((row["checked_by"], row["found_by"], row["found_exact_by"]), (["model-a"], ["model-a"], ["model-a"]))
        self.assertEqual(groups_of("t0", GT_T0, table), [FOUND, NOT_FOUND, NOT_FOUND])
        self.assertEqual(groups_of("t2", GT_T2, table), [NOT_FOUND])
        # a second model, on t0 only: t0's rows gain it, the others keep model-a's verdict
        partial = triple("MODIS Snow Cover 5-Min L2", "Dataset", "ACQUIRED_BY_INSTRUMENT", "MODIS", "Instrument")
        _, table = self.apply({"t0": [partial]}, "model-b", ids=("t0",))
        self.assertEqual(table[key_of("t0", GT_T0[1])]["found_by"], ["model-b"])
        self.assertEqual(table[key_of("t0", GT_T0[1])]["found_exact_by"], [])            # a partial pair isn't exact
        self.assertEqual(table[key_of("t0", GT_T0[0])]["checked_by"], ["model-a", "model-b"])
        self.assertEqual(table[key_of("t0", GT_T0[0])]["found_by"], ["model-a"])
        self.assertEqual(table[key_of("t2", GT_T2[0])]["checked_by"], ["model-a"])          # kept as it was
        # model-a again, now finding nothing of t0: its earlier verdicts on t0 are replaced, not kept beside
        _, table = self.apply({"t0": []}, "model-a", ids=("t0",))
        self.assertEqual(table[key_of("t0", GT_T0[0])]["found_by"], [])
        self.assertEqual(table[key_of("t0", GT_T0[0])]["checked_by"], ["model-b", "model-a"])
        self.assertEqual(len(table), 5)
        text = self.path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(text[0], ",".join(COLUMNS))
        self.assertTrue(text[1].startswith("t0,"))                                         # pool order

    def test_reworded_triple_dropped(self):
        self.apply({"t0": GT_T0}, "model-a", ids=("t0",))
        stale = {**GT_T0[2], "object": "Terra satellite"}                                   # a reworded ground truth triple
        table = read_table(self.path)
        table[key_of("t0", stale)] = {**table.pop(key_of("t0", GT_T0[2])), "object": "Terra satellite"}
        write_table(self.path, list(table.values()))
        self.assertEqual(len(stale_rows(read_table(self.path), self.gt.select("evaluable").rows)), 1)
        applied, table = self.apply({"t0": GT_T0}, "model-a", ids=("t0",))
        self.assertEqual((applied["dropped"], len(table)), (1, 3))
        self.assertNotIn(key_of("t0", stale), table)

    def test_reader_near_misses(self):
        self.assertEqual(read_table(self.tmp / "absent.csv"), {})
        (self.tmp / "bad.csv").write_text("id,subject\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            read_table(self.tmp / "bad.csv")
        write_table(self.path, [{"id": "t0", **GT_T0[0], "checked_by": "m1 ,m1, m2", "found_by": "", "found_exact_by": ""}])
        row = read_table(self.path)[key_of("t0", GT_T0[0])]
        self.assertEqual(row["checked_by"], ["m1", "m2"])
        self.assertEqual(groups_of("t0", GT_T0, read_table(self.path)), [NOT_FOUND, NOT_CHECKED, NOT_CHECKED])


class Picking(Fixture):

    def inputs(self):
        records = self.tmp / "records.jsonl"
        records.write_text("\n".join(json.dumps({"id": i, "title": f"Title {i}", "notes": "MODIS aboard Aqua.", "maintainer": "M"})
                                     for i in ("t0", "h1", "t2", "u3", "x9")) + "\n", encoding="utf-8")
        splits = self.tmp / "splits.json"
        splits.write_text(json.dumps({"ground_truth_candidates": {"records": POOL}}), encoding="utf-8")
        return {"records": records, "splits": splits, "ground_truth_schema": ROOT / "annotations" / "ground_truth_schema.txt",
                "ground_truth": self.tmp / "ground_truth" / "batch_*.csv"}

    def settings(self, **more):
        return {**self.helper.SETTINGS, **more}

    def test_every_finished_record_in_pool_order_both_parts(self):
        chosen = self.helper.pick_records(self.inputs(), self.settings(), self.tmp)
        self.assertEqual([i["id"] for i in chosen.items], ["t0", "h1", "t2"])
        self.assertTrue(any("1 record(s) of the ground truth aren't finished" in n for n in chosen.notes))
        self.assertTrue(any("drafts 3 finished record(s) again (1 held-out, 2 tuning)" in n for n in chosen.notes))
        self.assertEqual(chosen.skipped, {})

    def test_ids_with_an_unfinished_and_an_unknown_one(self):
        chosen = self.helper.pick_records(self.inputs(), self.settings(ids="t2, u3, x9, nope"), self.tmp)
        self.assertEqual([i["id"] for i in chosen.items], ["t2"])
        notes = " ".join(chosen.notes)
        self.assertIn("u3", notes)
        self.assertIn("not finished in the ground truth", notes)
        self.assertIn("x9", notes)                                        # in the catalog, not in the ground truth
        self.assertIn("nope", notes)
        self.assertIn("not in the catalog", notes)

    def test_same_model_as_drafted_by_is_noted(self):
        chosen = self.helper.pick_records(self.inputs(), self.settings(model="gemini-2.5-pro"), self.tmp)
        self.assertTrue(any("2 ground truth triple(s) of these records were drafted by gemini-2.5-pro itself" in n
                            for n in chosen.notes))
        chosen = self.helper.pick_records(self.inputs(), self.settings(), self.tmp)
        self.assertFalse(any("itself" in n for n in chosen.notes))

    def test_nothing_to_draft_stops(self):
        with self.assertRaises(Stop):
            self.helper.pick_records(self.inputs(), self.settings(ids="u3"), self.tmp)


class WholeRun(unittest.TestCase):
    """The helper run as a person runs it, with the stand-in model, in a temporary copy: its outputs, the second run
    paying nothing, --apply true writing only annotations/second_opinion.csv."""

    @classmethod
    def setUpClass(cls):
        cls.repo = temp_repo()
        results = cls.repo / "outputs" / "intermediate_results"
        (results / "020_clean").mkdir(parents=True)
        (results / "030_split").mkdir(parents=True)
        pool = [{"id": "rec-1", "position": 0, "part": "tuning"}, {"id": "rec-2", "position": 1, "part": "held-out"},
                {"id": "rec-3", "position": 2, "part": "tuning"}]
        (results / "030_split" / "splits.json").write_text(json.dumps({"ground_truth_candidates": {"records": pool}}), encoding="utf-8")
        records = [{"id": "rec-1", "title": "MODIS Aqua Dataset 1", "notes": "MODIS aboard Aqua measured record 1.", "maintainer": "M"},
                   {"id": "rec-2", "title": "AIRS Aqua Dataset 2", "notes": "AIRS aboard Aqua measured record 2.", "maintainer": "M"},
                   {"id": "rec-3", "title": "OMI Aura Dataset 3", "notes": "OMI aboard Aura measured record 3.", "maintainer": "M"}]
        (results / "020_clean" / "records.jsonl").write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")
        # a ground truth schema with the entity classes the stand-in model uses
        (cls.repo / "annotations" / "ground_truth_schema.txt").write_text(
            "ENTITY CLASSES\n--------------\n\nDataset           a set of observations\nInstrument        a device\n"
            "Spacecraft        a craft\n\nPREDICATES\n----------\n\nABOARD               is carried on\n"
            "                     Instrument -> Spacecraft\n", encoding="utf-8")
        rows = [gt_row("rec-1", describes("rec-1", "MODIS Aqua Dataset 1")),
                gt_row("rec-1", triple("MODIS", "Instrument", "ABOARD", "Aqua", "Spacecraft", "MODIS aboard Aqua"), drafted_by="gemini-2.5-pro"),
                gt_row("rec-1", triple("MODIS", "Instrument", "ABOARD", "Terra", "Spacecraft", "MODIS aboard Aqua")),  # not in the text: not found
                gt_row("rec-2", describes("rec-2", "AIRS Aqua Dataset 2")),
                gt_row("rec-2", triple("AIRS", "Instrument", "ABOARD", "Aqua", "Spacecraft", "AIRS aboard Aqua")),
                gt_row("rec-3", describes("rec-3", "OMI Aura Dataset 3")),
                gt_row("rec-3", triple("OMI", "Instrument", "ABOARD", "Aura", "Spacecraft", "OMI aboard Aura"), finished="0")]
        write_csv(cls.repo / "annotations" / "ground_truth" / "batch_001.csv", FILE_COLUMNS, rows)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.repo)

    def run_helper(self, *args, expect=0):
        r = subprocess.run([sys.executable, str(HERE / "stand_in_run.py"), str(self.repo), "helpers/second_opinion.py",
                            "--confirm_paid_calls", "false", *args],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL,
                           env={**os.environ})
        out = r.stdout + r.stderr
        self.assertEqual(r.returncode, expect, out[-3000:])
        self.assertNotIn("Traceback", out, out[-3000:])
        return out, int(__import__("re").search(r"stand-in model answered (\d+) prompt", out).group(1))

    def test_run_rerun_and_apply(self):
        out, prompts = self.run_helper()
        self.assertEqual(prompts, 3)                                   # the test call, then one call per finished record
        folder = self.repo / "outputs" / "intermediate_results" / "second_opinion"
        draft = read_csv(folder / "second_opinion_triples.csv")
        self.assertEqual({r["id"] for r in draft}, {"rec-1", "rec-2"})
        self.assertTrue(all(r["drafted_by"] == "gemini-4-argon" for r in draft))
        matches = read_csv(folder / "second_opinion_matches.csv")
        by = {(r["record_id"], r["status"]): r for r in matches}
        self.assertIn(("rec-1", "found (exact)"), by)
        self.assertIn(("rec-1", "not found"), by)
        self.assertEqual(by[("rec-1", "not found")]["ground_truth_object"], "Terra")
        self.assertEqual(sum(1 for r in matches if r["status"] == "draft only"), 2)     # rec-1's Moon and Satellite rows
        self.assertFalse(any(r["record_id"] == "rec-2" and r["status"] == "draft only" for r in matches))   # held-out: never listed
        details = json.loads((folder / "second_opinion_details.json").read_text(encoding="utf-8"))
        self.assertEqual(details["made"]["model"], "gemini-4-argon")
        self.assertIsNone(details["applied"])
        self.assertEqual({r["id"]: r["status"] for r in details["records"]}, {"rec-1": "drafted", "rec-2": "drafted"})
        self.assertEqual(sorted((self.repo / "annotations").glob("second_opinion.csv"))[0].read_text(encoding="utf-8").count("\n"), 1)  # header only
        manifest = json.loads((folder / "_manifest.json").read_text(encoding="utf-8"))
        self.assertTrue(any(p["file"].endswith("draft.txt") for p in manifest["prompts"]))     # 050's prompt, by fingerprint
        report = sorted((self.repo / "outputs" / "reports").glob("second_opinion_*.md"))[-1].read_text(encoding="utf-8")
        self.assertIn("### The second opinion's facts the ground truth lacks (tuning records)", report)
        self.assertIn("held-out records are counted here and nowhere else", report)
        self.assertIn("aboard the Moon", report)
        self.assertNotIn("AIRS (Instrument) ABOARD Terra", report)
        self.assertIn("py helpers/second_opinion.py --apply true", report)
        # the second run pays nothing, and applies: the only file of annotations/ it writes is second_opinion.csv
        before = {p.name: p.read_bytes() for p in (self.repo / "annotations").rglob("*") if p.is_file()}
        out, prompts = self.run_helper("--apply", "true")
        after = {p.name: p.read_bytes() for p in (self.repo / "annotations").rglob("*") if p.is_file()}
        self.assertEqual(sorted(n for n in after if after[n] != before.get(n)), ["second_opinion.csv"])
        self.assertEqual(set(before), set(after))
        self.assertEqual(prompts, 0)
        table = read_table(self.repo / "annotations" / "second_opinion.csv")
        self.assertEqual(len(table), 3)
        row = table[key_of("rec-1", triple("MODIS", "Instrument", "ABOARD", "Terra", "Spacecraft"))]
        self.assertEqual((row["checked_by"], row["found_by"]), (["gemini-4-argon"], []))
        row = table[key_of("rec-2", triple("AIRS", "Instrument", "ABOARD", "Aqua", "Spacecraft"))]
        self.assertEqual(row["found_exact_by"], ["gemini-4-argon"])
        self.assertEqual(list((self.repo / "outputs").rglob("drafted_triples_batch*")), [])   # never a drafted batch


class ModelSettings(unittest.TestCase):

    def test_gemini_4_argon(self):
        """Its maker says temperature is ignored, so none is sent; its thinking level goes as reasoning_effort."""
        self.assertFalse(llm.temperature_sent("gemini-4-argon", "litellm"))
        self.assertTrue(llm.takes_thinking_cap("gemini-4-argon", "litellm"))
        self.assertEqual(llm.maker("gemini-4-argon"), "Google")
        self.assertIsNone(llm.effort_note("gemini-4-argon"))
        helper = load_helper()
        self.assertEqual(helper.SETTINGS["model"], "gemini-4-argon")


if __name__ == "__main__":
    unittest.main()
