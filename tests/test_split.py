"""Splitting (030_split): the pool's tuning and held-out parts, the
induction candidates, the two kept apart, and splits.json written once."""
import json
import random
import shutil
import tempfile
import unittest
from pathlib import Path

from support import use_step

use_step("030_split")
import moves                                      # noqa: E402

SETTINGS = {"induction_seed": 7}


def write_records(path, records):
    path.write_text("".join(json.dumps(r) + "\n" for r in records), encoding="utf-8")


class Split(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.records = [{"id": f"r{i:02d}", "title": f"T{i}", "notes": "", "maintainer": ["A", "B", "C"][i % 3]}
                        for i in range(30)]
        self.records[29]["title"] = ""                               # no text: never an induction candidate
        write_records(self.tmp / "records.jsonl", self.records)
        self.pool_rows = [("r03", "A"), ("gone", "A"), ("r05", "Old name"), ("r10", "B")]
        self.write_pool(self.pool_rows)
        self.inputs = {"records": self.tmp / "records.jsonl", "candidates": self.tmp / "pool.csv"}

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def write_manifest(self, partial=False, sha256=None, **extra):
        """020's manifest beside the records, describing records.jsonl as it is now (or with the sha256 given)."""
        import hashlib
        digest = sha256 or hashlib.sha256((self.tmp / "records.jsonl").read_bytes()).hexdigest()
        (self.tmp / "_manifest.json").write_text(json.dumps(
            {"outputs": [{"file": "records.jsonl", "sha256": digest}], "harvest_partial": partial, **extra}),
            encoding="utf-8")

    def write_pool(self, rows, header="id,maintainer,stratum,stratum_size,drawn_from_stratum"):
        lines = [header] + [f"{i},{m},g,1,1" for i, m in rows]
        (self.tmp / "pool.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def split(self):
        records = moves.load_records(self.inputs)
        pool = moves.ground_truth_candidates(self.inputs, records)
        induction = moves.induction_candidates(records, pool, SETTINGS)
        moves.check_disjoint(pool, induction)
        return pool, induction

    def test_part_rule(self):
        held_out = [p for p in range(30) if moves.part_of(p) == "held-out"]
        self.assertEqual(held_out, [8, 11, 14, 17, 20, 23, 26, 29])
        self.assertAlmostEqual(sum(moves.part_of(p) == "held-out" for p in range(1000)) / 1000, 1 / 3, delta=0.01)

    def test_pool(self):
        pool, _ = self.split()
        self.assertEqual([(r["id"], r["position"]) for r in pool.records], [("r03", 0), ("r05", 2), ("r10", 3)])
        self.assertEqual(pool.dropped[0]["id"], "gone")
        self.assertEqual(pool.renamed, [{"id": "r05", "in_pool": "Old name", "now": "C"}])
        self.assertEqual(pool.records[1]["maintainer"], "C")

    def test_induction(self):
        pool, induction = self.split()
        ids = [r["id"] for r in induction.records]
        self.assertFalse(set(ids) & {"r03", "r05", "r10", "gone"})
        self.assertNotIn("r29", ids)
        self.assertEqual((induction.in_pool, induction.without_text), (3, 1))
        self.assertEqual(len(ids), 26)
        self.assertEqual([m["maintainer"] for m in induction.maintainers], ["A", "B", "C"])  # ties: by name
        for m in "ABC":
            positions = [r["position"] for r in induction.records if r["maintainer"] == m]
            self.assertEqual(positions, list(range(len(positions))))

    def test_order_fixed_and_independent(self):
        _, first = self.split()
        random.Random(1).shuffle(self.records)                      # another file order
        self.records.append({"id": "z99", "title": "new", "notes": "", "maintainer": "D"})  # another maintainer
        write_records(self.tmp / "records.jsonl", self.records)
        _, second = self.split()
        of = lambda ind, m: [r["id"] for r in ind.records if r["maintainer"] == m]   # noqa: E731
        for m in "ABC":
            self.assertEqual(of(first, m), of(second, m))
        records = moves.load_records(self.inputs)
        pool = moves.ground_truth_candidates(self.inputs, records)
        reseeded = moves.induction_candidates(records, pool, {"induction_seed": 8})
        self.assertNotEqual(of(first, "A"), of(reseeded, "A"))

    def test_bad_pool_file(self):
        self.write_pool([("r03", "A"), ("r03", "A")])
        with self.assertRaisesRegex(ValueError, "more than once"):
            self.split()
        self.write_pool([("r03", "A")], header="record,who,stratum,stratum_size,drawn_from_stratum")
        with self.assertRaisesRegex(ValueError, "needs the columns"):
            self.split()

    def test_twins_across_parts(self):
        """The report counts the held-out pool records that are twins of a tuning pool record, by twin kind, and the
        finished held-out records that are. Near misses: held-out records that share no title or `notes` with a tuning
        record (p14, finished; p17, unfinished), a held-out twin with no ground truth (p11), and a tuning record's twin
        among the tuning records (p01 of p00: not counted, both are tuning)."""
        texts = {0: ("Snow", "Daily snow."), 1: ("Snow", "Daily snow."), 2: ("Fire", "Burned area."),
                 8: ("Snow", "Daily snow."), 11: ("Fire 2", "Burned area."), 14: ("Ice", "Sea ice."),
                 17: ("Ice cap", "Glaciers.")}
        self.records = [{"id": f"p{i:02d}", "title": t, "notes": n, "maintainer": "A"} for i, (t, n) in texts.items()]
        write_records(self.tmp / "records.jsonl", self.records)
        self.write_pool([(f"p{i:02d}", "A") if i in texts else (f"gone{i}", "A") for i in range(18)])
        records = moves.load_records(self.inputs)
        pool = moves.ground_truth_candidates(self.inputs, records)
        self.assertEqual([r["id"] for r in pool.records if r["part"] == "held-out"], ["p08", "p11", "p14", "p17"])
        gt = self.tmp / "ground_truth"
        gt.mkdir()
        columns = ["id", "subject", "subject_class", "predicate", "object", "object_class", "source_text",
                   "all_facts_extracted"]
        rows = [("p08", "1"), ("p14", "1"), ("p17", "0")]               # p11 a twin but not annotated
        (gt / "batch_001.csv").write_text(",".join(columns) + "\n" + "".join(
            f"{rid},S,Dataset,P,O,Dataset,S P O,{mark}\n" for rid, mark in rows), encoding="utf-8")
        text = "\n".join(moves.twins_across_parts(pool, records, str(gt / "batch_*.csv")))
        self.assertIn("tuning pool record: **2 of 4** (1 whole text, 1 notes only)", text)
        self.assertIn("finished held-out records (as the ground truth stands at this run): **1 of 2** (p08)", text)
        none = "\n".join(moves.twins_across_parts(pool, records, None))             # no ground truth yet
        self.assertIn("**2 of 4**", none)
        self.assertIn("**0 of 0**", none)

    def test_disjoint(self):
        pool, induction = self.split()
        induction.records.append({"id": "r03"})
        with self.assertRaisesRegex(ValueError, "never overlap"):
            moves.check_disjoint(pool, induction)

    def test_write_once(self):
        out = self.tmp / "out"
        out.mkdir()
        self.write_manifest()
        pool, induction = self.split()
        moves.results(pool, induction, moves.load_records(self.inputs), self.inputs, SETTINGS, out)
        written = (out / moves.OUTPUT_NAME).read_text(encoding="utf-8")
        data = json.loads(written)
        self.assertEqual([r["part"] for r in data[moves.CANDIDATES]["records"]], ["tuning"] * 3)
        again = moves.results(pool, induction, moves.load_records(self.inputs), self.inputs, SETTINGS, out)
        self.assertFalse(any("differs" in w for w in again.warnings))
        self.assertIn("### Twins in the pool", again.details)                      # the twin table (common.ground_truth)
        self.assertIn("| **all twins** |", again.details)
        records = moves.load_records(self.inputs)
        pool2 = moves.ground_truth_candidates(self.inputs, records)
        changed = moves.results(pool2, moves.induction_candidates(records, pool2, {"induction_seed": 8}),
                                records, self.inputs, SETTINGS, out)
        self.assertTrue(any("differs" in w for w in changed.warnings))
        self.assertEqual((out / moves.OUTPUT_NAME).read_text(encoding="utf-8"), written)   # kept as it was

    def test_never_from_a_trial_harvest(self):
        """Records whose manifest says they come from a trial harvest: splits.json isn't written, and a kept
        one is left as it is. Records whose origin can't be told aren't written from either: no manifest, one that
        doesn't say, or one describing another version of records.jsonl (replaced since)."""
        out = self.tmp / "out"
        out.mkdir()
        pool, induction = self.split()

        def refused(pattern):
            with self.assertRaisesRegex(moves.Stop, pattern):
                moves.results(pool, induction, moves.load_records(self.inputs), self.inputs, SETTINGS, out)
            self.assertFalse((out / moves.OUTPUT_NAME).exists())
        self.write_manifest(partial=True)
        refused("trial harvest")
        (self.tmp / "_manifest.json").unlink()
        refused("can't tell whether")                                       # no manifest
        self.write_manifest(partial=False, sha256="0" * 64)
        refused("can't tell whether")                                       # another version of the records
        self.write_manifest(partial=None)
        refused("can't tell whether")                                       # it doesn't say
        self.write_manifest(partial=False)
        moves.results(pool, induction, moves.load_records(self.inputs), self.inputs, SETTINGS, out)  # the full harvest
        self.assertTrue((out / moves.OUTPUT_NAME).exists())


class Discards(Split):
    """Stages 2 and 3 record each pool record dropped (no longer in the catalog), each pool maintainer replaced by
    020's, and each record that can't be an induction candidate (in the pool, or no text); the accounting checks stop
    the run when a record vanishes without a record of it. A kept splits.json records this run's draw it didn't
    keep."""

    def setUp(self):
        super().setUp()
        from common import dropped
        self.dropped = dropped
        dropped.reset()
        self.addCleanup(dropped.reset)

    def test_recorded(self):
        pool, induction = self.split()
        by = lambda stage, action="discarded": sorted(e["record_id"] for e in self.dropped.DISCARDS
                                                      if e["stage"] == stage and e["action"] == action)
        self.assertEqual(by(moves.STAGE_2), ["gone"])
        self.assertEqual(by(moves.STAGE_2, "replaced"), ["r05"])
        self.assertEqual(by(moves.STAGE_3), ["r03", "r05", "r10", "r29"])     # 3 in the pool, 1 without text
        why = {e["record_id"]: e["reason"] for e in self.dropped.DISCARDS if e["stage"] == moves.STAGE_3}
        self.assertIn("no text", why["r29"])
        out = self.tmp / "out"
        out.mkdir()
        self.write_manifest()
        records = moves.load_records(self.inputs)
        moves.results(pool, induction, records, self.inputs, SETTINGS, out)
        self.assertEqual(by(moves.STAGE_RESULTS), [])                       # written: nothing set aside
        pool2 = moves.ground_truth_candidates(self.inputs, records)
        moves.results(pool2, moves.induction_candidates(records, pool2, {"induction_seed": 8}), records, self.inputs,
                      SETTINGS, out)
        self.assertTrue(by(moves.STAGE_RESULTS))                            # another draw, not kept: each entry

    def test_near_miss_a_record_left_out_unrecorded(self):
        from unittest import mock
        from common.stop import Stop
        records = moves.load_records(self.inputs)
        with mock.patch.object(self.dropped, "discard", lambda *a, **k: None), self.assertRaises(Stop) as caught:
            moves.ground_truth_candidates(self.inputs, records)
        self.assertIn("Accounting check failed in stage 2 (ground_truth_candidates)", str(caught.exception))
        pool = moves.ground_truth_candidates(self.inputs, records)
        with mock.patch.object(self.dropped, "discard", lambda *a, **k: None), self.assertRaises(Stop) as caught:
            moves.induction_candidates(records, pool, SETTINGS)
        self.assertIn("Accounting check failed in stage 3 (induction_candidates): 30 records from 020 went in, 26 "
                      "were kept", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
