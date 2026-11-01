"""The second opinion (helpers/second_opinion.py): which finished records it drafts again (every part; held-out ones
too, their draft's facts the ground truth lacks never listed), each ground truth triple found (exact, partial) or not
by 070's pairing without translation, with the near misses; several runs combined (each ground truth triple found in k
of the runs, exactly in j; the draft-only facts the union over the runs, with the runs that proposed each; a failed
run counted on the others); what --apply true writes into annotations/second_opinion.csv (two models merged, the same
model again replaced, a reworded triple dropped, other records kept, the reader's near misses); the whole helper run
with the stand-in model in a temporary copy, its answers differing by repeat: 1 run, then 3 runs paying only for
repeats 2 and 3 and asking once, then the same 3 runs paying nothing; and the settings sent to gemini-4-argon. Step
070's side: tests/test_evaluate_second_opinion.py."""
import importlib.util
import json
import os
import re
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
from common.second_opinion import (COLUMNS, FOUND, NOT_CHECKED, NOT_FOUND, TRIPLE, groups_of, key_of,  # noqa: E402
                                   read_table, runs_of, stale_rows, write_table)
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

    def combined(self, runs: list, ids=("t0", "h1", "t2")):
        """runs: one {id: draft triples} per run (a record missing from a run: its call failed in that run)."""
        chosen = self.chosen(ids)
        made = [self.helper.Run(r, None, self.drafts(rows), self.helper.match(chosen, self.drafts(rows)))
                for r, rows in enumerate(runs, 1)]
        return self.helper.combine(chosen, made, len(runs))


class Matching(Fixture):

    def test_exact_partial_and_not_found(self):
        draft = {"t0": [triple("the MODIS", "Instrument", "ABOARD", "Aqua", "Spacecraft"),                 # exact
                        triple("MODIS Snow Cover 5-Min L2 Swath", "Dataset", "ACQUIRED_BY_INSTRUMENT",
                               "Moderate Resolution Imaging Spectroradiometer (MODIS)", "Instrument"),   # partial
                        triple("CERES", "Instrument", "ABOARD", "Aqua", "Spacecraft")],                    # another object: not found
                 "h1": GT_H1, "t2": GT_T2}
        m = self.matched(draft)
        self.assertEqual([level for _, level, _ in m.per_record["t0"]["gt"]], ["exact", "partial", None])
        self.assertEqual([t["object"] for t in m.per_record["t0"]["draft_only"]], ["Aqua"])
        c = self.combined([draft])
        statuses = [(r["status"], r.get("found_in_runs", r.get("proposed_in_runs")), r.get("found_exact_in_runs"))
                    for r in c.rows if r["record_id"] == "t0"]
        self.assertEqual(statuses, [(FOUND, 1, 1), (FOUND, 1, 0), (NOT_FOUND, 0, 0), (self.helper.DRAFT_ONLY, 1, None)])
        found = next(r for r in c.rows if r["status"] == FOUND)
        self.assertEqual((found["draft_subject"], found["ground_truth_drafted_by"], found["entity_classes_agree_in_runs"],
                          found["draft_run"], found["runs"]), ("the MODIS", "gemini-2.5-pro", 1, 1, 1))
        self.assertTrue(all(r["origin"] for r in c.rows))

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
        c = self.combined([draft], ids=("t0",))
        self.assertEqual([(g["found"], g["agree"]) for g in c.per_record["t0"]["gt"]], [(0, 0), (1, 0), (0, 0)])

    def test_describes_triples_never_matched(self):
        m = self.matched({"t2": [describes("t2")] + GT_T2}, ids=("t2",))
        self.assertEqual(len(m.per_record["t2"]["gt"]), 1)             # the ground truth's describes triple isn't a triple to find
        self.assertEqual(m.per_record["t2"]["draft_only"], [])         # nor the draft's

    def test_held_out_facts_counted_not_listed(self):
        draft = {"h1": GT_H1 + [triple("AIRS", "Instrument", "ABOARD", "Terra", "Spacecraft")],
                 "t2": GT_T2 + [triple("OMI", "Instrument", "ABOARD", "Terra", "Spacecraft")]}
        c = self.combined([draft, draft], ids=("h1", "t2"))
        self.assertEqual(len(c.per_record["h1"]["draft_only"]), 1)     # counted
        listed = [r for r in c.rows if r["status"] == self.helper.DRAFT_ONLY]
        self.assertEqual([(r["record_id"], r["proposed_in_runs"]) for r in listed], [("t2", 2)])   # the tuning record's only
        self.assertEqual([r["status"] for r in c.rows if r["record_id"] == "h1"], [FOUND])

    def test_order_free_and_one_partner_each(self):
        draft = {"t0": [triple("MODIS", "Instrument", "ABOARD", "Aqua", "Spacecraft")] * 2}   # stated twice: one pair
        m = self.matched(draft, ids=("t0",))
        self.assertEqual([level for _, level, _ in m.per_record["t0"]["gt"]], ["exact", None, None])
        self.assertEqual(len(m.per_record["t0"]["draft_only"]), 1)
        a = self.combined([{"t0": GT_T0}], ids=("t0",)).rows
        b = self.combined([{"t0": list(reversed(GT_T0))}], ids=("t0",)).rows
        self.assertEqual([(r["ground_truth_subject"], r["status"]) for r in a], [(r["ground_truth_subject"], r["status"]) for r in b])

    def test_failed_record_not_matched(self):
        m = self.matched({"t2": GT_T2}, ids=("t0", "t2"))
        self.assertEqual(m.not_drafted, ["t0"])
        self.assertEqual(list(m.per_record), ["t2"])
        self.assertEqual(list(self.combined([{"t2": GT_T2}], ids=("t0", "t2")).per_record), ["t2"])


class Combining(Fixture):
    """Several runs combined: each ground truth triple found in k of the runs, exactly in j; the draft-only facts the
    union over the runs, each with the runs that proposed it; a record a run failed for counted on the others."""

    def test_three_runs(self):
        partial = triple("MODIS Snow Cover 5-Min L2", "Dataset", "ACQUIRED_BY_INSTRUMENT", "MODIS", "Instrument")
        other = triple("CERES", "Instrument", "ABOARD", "Aqua", "Spacecraft")                    # not the ground truth's
        moon = triple("MODIS", "Instrument", "ABOARD", "Moon", "Spacecraft")
        runs = [{"t0": [GT_T0[0], partial, other]},                                          # run 1
                {"t0": [GT_T0[0], GT_T0[1], moon, moon]},                                   # run 2: the Moon stated twice
                {"t0": [triple("the MODIS", "instrument", "aboard", "Aqua", "spacecraft"),     # run 3: evened out, exact
                        triple("CERES", "instrument", "ABOARD", "Aqua", "Spacecraft")]}]      # the same draft-only fact as run 1's
        c = self.combined(runs, ids=("t0",))
        gt = c.per_record["t0"]["gt"]
        self.assertEqual([(g["found"], g["exact"]) for g in gt], [(3, 3), (2, 1), (0, 0)])
        self.assertEqual(gt[1]["partner"][0], 2)                        # the partner from the first run that paired it exactly
        self.assertIsNone(gt[2]["partner"])
        union = {u["triple"]["object"]: u["runs"] for u in c.per_record["t0"]["draft_only"]}
        self.assertEqual(union, {"Aqua": [1, 3], "Moon": [2]})          # once per run, however often a run states it
        self.assertEqual(c.per_record["t0"]["runs"], [1, 2, 3])
        rows = [r for r in c.rows if r["status"] == self.helper.DRAFT_ONLY]
        self.assertEqual(sorted((r["draft_object"], r["proposed_in_runs"], r["draft_run"]) for r in rows),
                         [("Aqua", 2, 1), ("Moon", 1, 2)])

    def test_a_failed_run_counts_on_the_others(self):
        c = self.combined([{"t0": GT_T0}, {}, {"t0": GT_T0[:1]}], ids=("t0",))
        e = c.per_record["t0"]
        self.assertEqual((e["runs"], e["failed"]), ([1, 3], [2]))
        self.assertEqual([g["found"] for g in e["gt"]], [2, 1, 1])
        self.assertTrue(all(r["runs"] == 2 for r in c.rows))
        self.assertEqual(self.combined([{}, {}], ids=("t0",)).per_record, {})                 # every run failed: nothing


class Apply(Fixture):

    def setUp(self):
        self.path = self.tmp / f"second_opinion_{self._testMethodName}.csv"

    def apply(self, runs, model, ids=("t0", "h1", "t2")):
        llm.MODEL = model
        c = self.combined(runs, ids)
        return self.helper.apply(self.chosen(ids), c, {"apply": True}, self.path), read_table(self.path)

    def by(self, table, rid, t):
        return {m: (c["runs"], c["found_in_runs"], c["found_exact_in_runs"]) for m, c in table[key_of(rid, t)]["by"].items()}

    def test_nothing_without_the_setting(self):
        self.assertIsNone(self.helper.apply(self.chosen(), self.combined([{"t2": GT_T2}], ("t2",)), {"apply": False}, self.path))
        self.assertFalse(self.path.exists())

    def test_two_models_merge_and_the_same_model_replaces(self):
        runs_a = [{"t0": GT_T0[:1], "h1": GT_H1, "t2": []}, {"t0": GT_T0[:2], "h1": [], "t2": []},
                  {"t0": [], "h1": [], "t2": []}]
        applied, table = self.apply(runs_a, "model-a")
        self.assertEqual((applied["rows"], applied["triples"], applied["rebuilt"], applied["dropped"]), (5, 5, 5, 0))
        self.assertEqual(self.by(table, "t0", GT_T0[0]), {"model-a": (3, 2, 2)})
        self.assertEqual(self.by(table, "t0", GT_T0[1]), {"model-a": (3, 1, 1)})
        self.assertEqual(self.by(table, "h1", GT_H1[0]), {"model-a": (3, 1, 1)})
        self.assertEqual(groups_of("t0", GT_T0, table), [FOUND, FOUND, NOT_FOUND])          # found in at least one run
        self.assertEqual(groups_of("t2", GT_T2, table), [NOT_FOUND])
        self.assertEqual(runs_of("t0", GT_T0, table), [{"model-a": (2, 3)}, {"model-a": (1, 3)}, {"model-a": (0, 3)}])
        self.assertEqual(runs_of("t9", GT_T0[:1], table), [{}])
        # a second model, one run, on t0 only: t0's triples gain it, the others keep model-a's alone
        partial = triple("MODIS Snow Cover 5-Min L2", "Dataset", "ACQUIRED_BY_INSTRUMENT", "MODIS", "Instrument")
        applied, table = self.apply([{"t0": [partial]}], "model-b", ids=("t0",))
        self.assertEqual((applied["rows"], applied["triples"]), (8, 5))
        self.assertEqual(self.by(table, "t0", GT_T0[1]), {"model-a": (3, 1, 1), "model-b": (1, 1, 0)})   # a partial pair isn't exact
        self.assertEqual(self.by(table, "t0", GT_T0[2]), {"model-a": (3, 0, 0), "model-b": (1, 0, 0)})
        self.assertEqual(self.by(table, "t2", GT_T2[0]), {"model-a": (3, 0, 0)})                          # kept as it was
        # model-a again, 2 runs finding nothing of t0: its earlier counts on t0 are replaced, not kept beside
        _, table = self.apply([{"t0": []}, {"t0": []}], "model-a", ids=("t0",))
        self.assertEqual(self.by(table, "t0", GT_T0[0]), {"model-b": (1, 0, 0), "model-a": (2, 0, 0)})
        self.assertEqual(groups_of("t0", GT_T0, table), [NOT_FOUND, FOUND, NOT_FOUND])      # model-b's partial pair
        self.assertEqual(len(table), 5)
        text = self.path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(text[0], ",".join(COLUMNS))
        self.assertTrue(text[1].startswith("t0,"))                                         # pool order
        self.assertEqual(len(text), 1 + 8)                                                 # one row per triple and model

    def test_reworded_triple_dropped(self):
        self.apply([{"t0": GT_T0}], "model-a", ids=("t0",))
        stale = {**GT_T0[2], "object": "Terra satellite"}                                   # a reworded ground truth triple
        table = read_table(self.path)
        table[key_of("t0", stale)] = {**table.pop(key_of("t0", GT_T0[2])), "object": "Terra satellite"}
        write_table(self.path, list(table.values()))
        self.assertEqual(len(stale_rows(read_table(self.path), self.gt.select("evaluable").rows)), 1)
        applied, table = self.apply([{"t0": GT_T0}], "model-a", ids=("t0",))
        self.assertEqual((applied["dropped"], len(table)), (1, 3))
        self.assertNotIn(key_of("t0", stale), table)

    def test_reader_near_misses(self):
        self.assertEqual(read_table(self.tmp / "absent.csv"), {})
        (self.tmp / "bad.csv").write_text("id,subject\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            read_table(self.tmp / "bad.csv")
        (self.tmp / "old.csv").write_text("id,subject,subject_class,predicate,object,object_class,checked_by,found_by,"
                                          "found_exact_by\n", encoding="utf-8")
        with self.assertRaises(ValueError) as e:                                            # the file's header before runs
            read_table(self.tmp / "old.csv")
        self.assertIn("model", str(e.exception))
        row = {"id": "t0", **{c: GT_T0[0][c] for c in TRIPLE}}

        def rows(*models):
            write_csv(self.path, COLUMNS, [{**row, "model": m, "runs": n, "found_in_runs": k, "found_exact_in_runs": j}
                                           for m, n, k, j in models])
        rows(("m1", "3", " 0 ", "0"), ("m2", 1, 1, 0))
        entry = read_table(self.path)[key_of("t0", GT_T0[0])]
        self.assertEqual(list(entry["by"]), ["m1", "m2"])
        self.assertEqual(groups_of("t0", GT_T0, read_table(self.path)), [FOUND, NOT_CHECKED, NOT_CHECKED])
        rows(("m1", 3, 0, 0))
        self.assertEqual(groups_of("t0", GT_T0, read_table(self.path)), [NOT_FOUND, NOT_CHECKED, NOT_CHECKED])
        for bad in [("m1", 0, 0, 0), ("m1", 3, 4, 0), ("m1", 3, 1, 2), ("m1", 3, -1, 0), ("m1", "three", 0, 0),
                    ("m1", 3, "", 0), ("", 3, 1, 1)]:
            rows(bad)
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                read_table(self.path)
        rows(("m1", 3, 1, 1), ("m1", 2, 0, 0))                                             # one model twice for one triple
        with self.assertRaises(ValueError) as e:
            read_table(self.path)
        self.assertIn("two rows", str(e.exception))


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
        self.assertTrue(any("drafts 3 finished record(s) again (1 held-out, 2 tuning)" in n and "in 3 run(s)" in n
                            for n in chosen.notes))
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

    def test_answer_cache_noted_for_several_runs(self):
        """Several runs through LiteLLM without its answer cache bypassed may be copies of one run: noted before paying;
        not for one run, nor through Ask Sage, nor with the cache bypassed."""
        def noted(**more):
            return any(llm.ANSWER_CACHE_SWITCH in n for n in self.helper.pick_records(self.inputs(), self.settings(**more), self.tmp).notes)
        saved = os.environ.pop(llm.ANSWER_CACHE_SWITCH, None)
        load = llm.load_dotenv
        llm.load_dotenv = lambda *a, **k: None
        try:
            self.assertTrue(noted(service="litellm", runs=3))
            self.assertFalse(noted(service="litellm", runs=1))
            self.assertFalse(noted(service="asksage", runs=3))
            os.environ[llm.ANSWER_CACHE_SWITCH] = "1"
            self.assertFalse(noted(service="litellm", runs=3))
        finally:
            llm.load_dotenv = load
            os.environ.pop(llm.ANSWER_CACHE_SWITCH, None)
            if saved is not None:
                os.environ[llm.ANSWER_CACHE_SWITCH] = saved

    def test_runs_out_of_bounds_stop(self):
        for runs in (0, 21, "3", True):
            with self.subTest(runs=runs), self.assertRaises(Stop):
                self.helper.pick_records(self.inputs(), self.settings(runs=runs), self.tmp)

    def test_nothing_to_draft_stops(self):
        with self.assertRaises(Stop):
            self.helper.pick_records(self.inputs(), self.settings(ids="u3"), self.tmp)


class WholeRun(unittest.TestCase):
    """The helper run as a person runs it, with the stand-in model (its answers differing by repeat:
    tests/stand_ins.py, KG_STAND_IN_VARY), in a temporary copy: 1 run; then 3 runs, paying for repeats 2 and 3 only
    and asking once for both; then the same 3 runs with --apply true, paying nothing and writing only
    annotations/second_opinion.csv."""

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
                gt_row("rec-1", triple("MODIS", "Instrument", "ABOARD", "Terra", "Spacecraft", "MODIS aboard Aqua")),  # only repeat 3 states it
                gt_row("rec-2", describes("rec-2", "AIRS Aqua Dataset 2")),
                gt_row("rec-2", triple("AIRS", "Instrument", "ABOARD", "Aqua", "Spacecraft", "AIRS aboard Aqua")),
                gt_row("rec-3", describes("rec-3", "OMI Aura Dataset 3")),
                gt_row("rec-3", triple("OMI", "Instrument", "ABOARD", "Aura", "Spacecraft", "OMI aboard Aura"), finished="0")]
        write_csv(cls.repo / "annotations" / "ground_truth" / "batch_001.csv", FILE_COLUMNS, rows)
        cls.folder = results / "second_opinion"

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.repo)

    def run_helper(self, *args, expect=0):
        env = {k: v for k, v in os.environ.items() if k != llm.ANSWER_CACHE_SWITCH}
        r = subprocess.run([sys.executable, str(HERE / "stand_in_run.py"), str(self.repo), "helpers/second_opinion.py",
                            "--confirm_paid_calls", "false", *args],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL,
                           env={**env, "KG_STAND_IN_VARY": "1"})
        out = r.stdout + r.stderr
        self.assertEqual(r.returncode, expect, out[-3000:])
        self.assertNotIn("Traceback", out, out[-3000:])
        return out, int(re.search(r"stand-in model answered (\d+) prompt", out).group(1))

    def matches(self) -> dict:
        rows = read_csv(self.folder / "second_opinion_matches.csv")
        return {(r["record_id"], r["status"], r["ground_truth_object"] or r["draft_object"],
                 r["draft_object_class"] if r["status"] == "draft only" else ""): r for r in rows}

    def report(self) -> str:
        reports = (self.repo / "outputs" / "reports").glob("second_opinion_*.md")
        return max(reports, key=lambda p: p.stat().st_mtime_ns).read_text(encoding="utf-8")       # this run's

    def test_one_run_then_three_then_apply(self):
        # 1 run
        out, prompts = self.run_helper("--runs", "1")
        self.assertEqual(prompts, 3)                                   # the test call, then one call per finished record
        draft = read_csv(self.folder / "second_opinion_triples.csv")
        self.assertEqual({(r["id"], r["run"]) for r in draft}, {("rec-1", "1"), ("rec-2", "1")})
        self.assertTrue(all(r["drafted_by"] == "gemini-4-argon" for r in draft))
        m = self.matches()
        self.assertEqual(m[("rec-1", "found", "Aqua", "")]["found_in_runs"], "1")
        self.assertEqual(m[("rec-1", "not found", "Terra", "")]["found_in_runs"], "0")
        self.assertEqual(sum(1 for k in m if k[1] == "draft only"), 2)           # rec-1's Moon and Satellite rows
        self.assertFalse(any(k[0] == "rec-2" and k[1] == "draft only" for k in m))   # held-out: never listed
        details = json.loads((self.folder / "second_opinion_details.json").read_text(encoding="utf-8"))
        self.assertEqual((details["made"]["model"], details["runs"], details["made"]["repeats"]), ("gemini-4-argon", 1, [1]))
        self.assertIsNone(details["applied"])
        self.assertEqual({r["id"]: r["runs_drafted"] for r in details["records"]}, {"rec-1": [1], "rec-2": [1]})
        self.assertEqual((self.repo / "annotations" / "second_opinion.csv").read_text(encoding="utf-8").count("\n"), 1)  # header only
        self.assertNotIn(llm.ANSWER_CACHE_SWITCH + "=1 isn't set", out)            # one run: nothing to copy
        manifest = json.loads((self.folder / "_manifest.json").read_text(encoding="utf-8"))
        self.assertTrue(any(p["file"].endswith("draft.txt") for p in manifest["prompts"]))     # 050's prompt, by fingerprint
        report = self.report()
        self.assertIn("### The second opinion's facts the ground truth lacks (tuning records)", report)
        self.assertIn("held-out records are counted here and nowhere else", report)
        self.assertIn("aboard the Moon", report)
        self.assertNotIn("AIRS (Instrument) ABOARD Terra", report)
        self.assertIn("py helpers/second_opinion.py --apply", report)

        # 3 runs (the default): repeat 1 is in the cache, so it pays for repeats 2 and 3 only, asking once for both
        out, prompts = self.run_helper()
        self.assertEqual(prompts, 1 + 4)
        self.assertIn("3 run(s) × 2 text piece(s) = 6 model call(s), 2 of them already in the cache, so 4 to pay for "
                      "(run 1: 0, run 2: 2, run 3: 2)", out)
        self.assertEqual(out.count("test call: ok"), 1)
        self.assertIn(llm.ANSWER_CACHE_SWITCH + "=1 isn't set", out)               # noted before paying
        draft = read_csv(self.folder / "second_opinion_triples.csv")
        self.assertEqual(sorted({r["run"] for r in draft}), ["1", "2", "3"])
        m = self.matches()
        aqua = m[("rec-1", "found", "Aqua", "")]
        self.assertEqual((aqua["runs"], aqua["found_in_runs"], aqua["found_exact_in_runs"], aqua["draft_run"]),
                         ("3", "2", "2", "1"))                         # repeat 2 leaves it out
        terra = m[("rec-1", "found", "Terra", "")]
        self.assertEqual((terra["found_in_runs"], terra["draft_run"]), ("1", "3"))      # only repeat 3 states it
        self.assertEqual(m[("rec-2", "found", "Aqua", "")]["found_in_runs"], "2")
        self.assertEqual(m[("rec-1", "draft only", "Moon", "Spacecraft")]["proposed_in_runs"], "3")
        self.assertEqual(m[("rec-1", "draft only", "Aqua", "Satellite")]["proposed_in_runs"], "2")
        self.assertEqual(sum(1 for k in m if k[1] == "draft only"), 2)           # the union: each fact once
        report = self.report()
        self.assertIn("| Found in | 0 of 3 | 1 of 3 | 2 of 3 | 3 of 3 |", report)
        self.assertIn("| Ground truth triples | 0 | 1 | 2 | 0 |", report)
        self.assertIn("in 3 of 3 run(s)", report)
        self.assertIn("draft classed triples, run 3 of 3", report)

        # the same 3 runs again, applied: nothing paid; the only file of annotations/ it writes is second_opinion.csv
        before = {p.name: p.read_bytes() for p in (self.repo / "annotations").rglob("*") if p.is_file()}
        out, prompts = self.run_helper("--apply", "true")
        after = {p.name: p.read_bytes() for p in (self.repo / "annotations").rglob("*") if p.is_file()}
        self.assertEqual(prompts, 0)
        self.assertEqual(sorted(n for n in after if after[n] != before.get(n)), ["second_opinion.csv"])
        self.assertEqual(set(before), set(after))
        table = read_table(self.repo / "annotations" / "second_opinion.csv")
        self.assertEqual(len(table), 3)

        def by(rid, o):
            c = table[key_of(rid, triple(rid.replace("rec-1", "MODIS").replace("rec-2", "AIRS"), "Instrument", "ABOARD", o,
                                         "Spacecraft"))]["by"]["gemini-4-argon"]
            return c["runs"], c["found_in_runs"], c["found_exact_in_runs"]
        self.assertEqual((by("rec-1", "Aqua"), by("rec-1", "Terra"), by("rec-2", "Aqua")), ((3, 2, 2), (3, 1, 1), (3, 2, 2)))
        self.assertEqual(list((self.repo / "outputs").rglob("drafted_triples_batch*")), [])   # never a drafted batch


class ModelSettings(unittest.TestCase):

    def test_gemini_4_argon(self):
        """Its maker says temperature is ignored, so none is sent; its thinking level goes as reasoning_effort."""
        self.assertFalse(llm.temperature_sent("gemini-4-argon", "litellm"))
        self.assertTrue(llm.takes_thinking_cap("gemini-4-argon", "litellm"))
        self.assertEqual(llm.maker("gemini-4-argon"), "Google")
        self.assertIsNone(llm.effort_note("gemini-4-argon"))
        helper = load_helper()
        self.assertEqual((helper.SETTINGS["model"], helper.SETTINGS["runs"]), ("gemini-4-argon", 3))
        self.assertNotIn("repeat", helper.SETTINGS)                    # the runs are the repeats


if __name__ == "__main__":
    unittest.main()
