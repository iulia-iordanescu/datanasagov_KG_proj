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

    def write_pool(self, rows, header="id,maintainer,group,group_size,drawn_from_group"):
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
        self.write_pool([("r03", "A")], header="record,who,group,group_size,drawn_from_group")
        with self.assertRaisesRegex(ValueError, "needs the columns"):
            self.split()

    def test_disjoint(self):
        pool, induction = self.split()
        induction.records.append({"id": "r03"})
        with self.assertRaisesRegex(ValueError, "never overlap"):
            moves.check_disjoint(pool, induction)

    def test_write_once(self):
        out = self.tmp / "out"
        out.mkdir()
        pool, induction = self.split()
        moves.results(pool, induction, self.inputs, SETTINGS, out)
        written = (out / moves.OUTPUT_NAME).read_text(encoding="utf-8")
        data = json.loads(written)
        self.assertEqual([r["part"] for r in data[moves.CANDIDATES]["records"]], ["tuning"] * 3)
        again = moves.results(pool, induction, self.inputs, SETTINGS, out)
        self.assertFalse(any("differs" in w for w in again.warnings))
        records = moves.load_records(self.inputs)
        pool2 = moves.ground_truth_candidates(self.inputs, records)
        changed = moves.results(pool2, moves.induction_candidates(records, pool2, {"induction_seed": 8}),
                                self.inputs, SETTINGS, out)
        self.assertTrue(any("differs" in w for w in changed.warnings))
        self.assertEqual((out / moves.OUTPUT_NAME).read_text(encoding="utf-8"), written)   # kept as it was


if __name__ == "__main__":
    unittest.main()
