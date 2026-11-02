"""py helpers/partial_pairs.py: the partial pairs of several 070 runs collected for review (the union, once per
verdict key, only those with no verdict, tuning records only), each run's compared_triples.csv found by its
manifest's sha256 (live or in previous_runs/), the verdicts moved into partial_pair_reviews.csv (validated: the two
verdicts, the cells unchanged, no conflict), and the verdicts that match no partial pair of the runs deleted."""
import csv
import hashlib
import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from support import ROOT, use_step

use_step("070_evaluate")
from common.partial_reviews import COLUMNS as REVIEW_COLUMNS, NOT_SAME, SAME, read_reviews, review_problems  # noqa: E402

spec = importlib.util.spec_from_file_location("partial_pairs", ROOT / "helpers" / "partial_pairs.py")
pp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pp)

COMPARED_COLUMNS = (["record_id", "part", "status"] + [f"translated_{k}" for k in pp.CLASSED]
                    + [f"ground_truth_{k}" for k in pp.CLASSED])


def triple(s, p, o, sc="Platform", oc="Instrument"):
    return {"subject": s, "subject_class": sc, "predicate": p, "object": o, "object_class": oc}


def row(rid, status, gt=None, ex=None, part="tuning"):
    out = {"record_id": rid, "part": part, "status": status}
    out.update({f"ground_truth_{k}": v for k, v in (gt or {}).items()})
    out.update({f"translated_{k}": v for k, v in (ex or {}).items()})
    return out


GT1 = triple("Aqua", "HAS_INSTRUMENT", "MODIS instrument")
GT2 = triple("Aqua", "HAS_PROCESSING_LEVEL", "Level 2", oc="ProcessingLevel")
GT5 = triple("Terra", "HAS_INSTRUMENT", "ASTER")
EX1 = triple("Aqua", "HAS_INSTRUMENT", "MODIS")
EX1_OTHER_SPELLING = triple("aqua", "has_instrument", "  MODIS ")      # the same key, evened out
EX2 = triple("Aqua", "HAS_PROCESSING_LEVEL", "2", oc="ProcessingLevel")
EX5 = triple("Terra", "HAS_INSTRUMENT", "ASTER instrument")
EXACT = triple("Aqua", "HAS_ORBIT", "polar", oc="Orbit")

RUN_A = [row("r1", "partial pair", GT1, EX1), row("r1", "partial pair", GT2, EX2)]
RUN_C = [row("r1", "partial pair", GT1, EX1_OTHER_SPELLING), row("r1", "ground truth only", GT2),
         row("r1", "exact pair", EXACT, EXACT), row("r1", "extracted only", ex=triple("Aqua", "HAS_ORBIT", "sun")),
         row("r2", "partial pair", GT5, EX5),
         row("h1", "partial pair", triple("X", "HAS_INSTRUMENT", "Y"), triple("X", "HAS_INSTRUMENT", "Y Z"),
             part="held-out")]


def review(rid, gt, ex, verdict):
    return {"record_id": rid, **{f"ground_truth_{s}": gt[s] for s in ("subject", "predicate", "object")},
            **{f"translated_{s}": ex[s] for s in ("subject", "predicate", "object")}, "verdict": verdict}


def write(path, columns, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, columns, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


class PartialPairs(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        out = self.out = self.tmp / "070_evaluate"
        # Run A's file was changed by run B: kept in previous_runs/A/. Run B's file was left unchanged by run C, so
        # only the live copy holds it (previous_runs/B/ keeps B's manifest and the other files C changed).
        write(out / "previous_runs" / "070_evaluate_2026-11-01_1644" / "compared_triples.csv", COMPARED_COLUMNS, RUN_A)
        write(out / "compared_triples.csv", COMPARED_COLUMNS, RUN_C)
        for run_id, folder, path in (("070_evaluate_2026-11-01_1644", out / "previous_runs" / "070_evaluate_2026-11-01_1644",
                                      out / "previous_runs" / "070_evaluate_2026-11-01_1644" / "compared_triples.csv"),
                                     ("070_evaluate_2026-11-01_1701", out / "previous_runs" / "070_evaluate_2026-11-01_1701",
                                      out / "compared_triples.csv"),
                                     ("070_evaluate_2026-11-01_1706", out, out / "compared_triples.csv")):
            folder.mkdir(parents=True, exist_ok=True)
            (folder / "_manifest.json").write_text(json.dumps(
                {"run_id": run_id, "outputs": [{"file": "compared_triples.csv", "sha256": sha(path)}]}), encoding="utf-8")
        self.runs = ["070_evaluate_2026-11-01_1644", "070_evaluate_2026-11-01_1701", "070_evaluate_2026-11-01_1706"]
        self.reviews = self.tmp / "partial_pair_reviews.csv"
        self.to_review = self.tmp / "partial_pairs_to_review.csv"
        self.records = self.tmp / "records.jsonl"
        self.records.write_text("\n".join(json.dumps(r) for r in (
            {"id": "r1", "title": "Aqua MODIS Level 2"}, {"id": "r2", "title": "Terra ASTER"})) + "\n", encoding="utf-8")
        write(self.reviews, REVIEW_COLUMNS, [
            review("r1", GT2, EX2, SAME),                                   # P3: reviewed, so not collected
            review("r1", GT1, triple("Aqua", "HAS_INSTRUMENT", "Terra"), NOT_SAME),   # pairs in no run: stale
            review("r9", GT1, EX1, SAME),                                   # a record no run evaluated: kept
        ])

    def collect(self, runs=None):
        return pp.write_to_review(runs or self.runs, self.out, self.to_review, self.reviews, self.records)

    def fill(self, verdicts: dict, edit=None):
        rows = read(self.to_review)
        for r in rows:
            r["verdict"] = verdicts.get(r["record_id"], "")
            if edit and r["record_id"] in edit:
                r.update(edit[r["record_id"]])
        write(self.to_review, pp.TO_REVIEW_COLUMNS, rows)

    # ---- collecting ----

    def test_finds_each_runs_own_file(self):
        """A file a later run left unchanged is found by its sha256 (run B's is the live one), never by its folder."""
        self.assertEqual(pp.kept_runs(self.out), self.runs)
        rows = pp.compared_rows(self.runs, self.out)
        self.assertEqual(rows[self.runs[0]], read(self.out / "previous_runs" / self.runs[0] / "compared_triples.csv"))
        self.assertEqual(rows[self.runs[1]], rows[self.runs[2]])

    def test_union_deduplicated_and_unreviewed_only(self):
        rows = self.collect()
        by_record = {r["record_id"]: r for r in rows}
        self.assertEqual(sorted(by_record), ["r1", "r2"])               # held-out h1 and reviewed P3 left out
        self.assertEqual(len(rows), 2)                                  # P1 once, though spelled two ways
        p1 = by_record["r1"]
        self.assertEqual(p1["runs"], "; ".join(self.runs))
        self.assertEqual(p1["record_title"], "Aqua MODIS Level 2")
        self.assertEqual(p1["predicate"], "HAS_INSTRUMENT")
        self.assertEqual(p1["ground_truth_triple"], "Aqua (Platform) HAS_INSTRUMENT MODIS instrument (Instrument)")
        self.assertEqual(p1["extracted_triple"], "Aqua (Platform) HAS_INSTRUMENT MODIS (Instrument)")  # the first run's spelling
        self.assertEqual(by_record["r2"]["runs"], "070_evaluate_2026-11-01_1701; 070_evaluate_2026-11-01_1706")
        self.assertEqual([r["verdict"] for r in rows], ["", ""])
        self.assertEqual(list(read(self.to_review)[0]), pp.TO_REVIEW_COLUMNS)

    def test_one_run_only(self):
        """Near miss: run A alone has P1 and P3, and P3 is reviewed."""
        rows = self.collect([self.runs[0]])
        self.assertEqual([(r["record_id"], r["runs"]) for r in rows], [("r1", self.runs[0])])

    def test_a_conflicting_verdict_is_no_verdict(self):
        """Two different verdicts on P1 (a hand edit): neither counts, so P1 is collected."""
        with open(self.reviews, "a", encoding="utf-8", newline="") as f:
            csv.DictWriter(f, REVIEW_COLUMNS, lineterminator="\n").writerows(
                [review("r1", GT1, EX1, SAME), review("r1", GT1, EX1, NOT_SAME)])
        self.assertIn("r1", {r["record_id"] for r in self.collect()})

    def test_unknown_or_repeated_run_stops(self):
        with self.assertRaises(pp.Problem) as e:
            self.collect(["070_evaluate_2026-11-01_1645"])
        self.assertIn("070_evaluate_2026-11-01_1645", str(e.exception))
        self.assertIn(self.runs[0], str(e.exception))                   # the runs kept are named
        with self.assertRaises(pp.Problem):
            self.collect([self.runs[0], self.runs[0]])

    def test_changed_file_is_not_the_runs(self):
        """Near miss: a compared_triples.csv whose sha256 isn't the manifest's isn't read as the run's."""
        path = self.out / "previous_runs" / self.runs[0] / "compared_triples.csv"
        path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        with self.assertRaises(pp.Problem):
            self.collect([self.runs[0]])

    def test_collecting_again_keeps_filled_verdicts(self):
        self.collect()
        self.fill({"r1": SAME})
        before = self.to_review.read_bytes()
        with self.assertRaises(pp.Problem) as e:
            self.collect()
        self.assertIn("--apply true", str(e.exception))
        self.assertEqual(self.to_review.read_bytes(), before)

    # ---- applying ----

    def test_round_trip(self):
        self.collect()
        self.fill({"r1": "  Same  FACT ", "r2": ""})
        added, already = pp.apply(self.to_review, self.reviews)
        self.assertEqual((len(added), already), (1, []))
        reviews = read_reviews(self.reviews)
        self.assertEqual(reviews[pp.row_key(review("r1", GT1, EX1, ""))], SAME)
        self.assertEqual(review_problems(self.reviews), [])
        self.assertEqual(read(self.reviews)[-1]["verdict"], SAME)           # written as one of the two, evened out
        self.assertEqual([r["record_id"] for r in read(self.to_review)], ["r2"])   # moved out; the empty one stays
        self.assertEqual([r["record_id"] for r in self.collect()], ["r2"])         # no longer without a verdict

    def test_wrong_verdict_moves_nothing(self):
        self.collect()
        self.fill({"r1": "same", "r2": SAME})
        before = (self.reviews.read_bytes(), self.to_review.read_bytes())
        with self.assertRaises(pp.Problem) as e:
            pp.apply(self.to_review, self.reviews)
        self.assertIn("line 2", str(e.exception))
        self.assertEqual((self.reviews.read_bytes(), self.to_review.read_bytes()), before)

    def test_edited_cells_move_nothing(self):
        self.collect()
        self.fill({"r1": SAME}, edit={"r1": {"translated_object": "MODIS Terra"}})
        with self.assertRaises(pp.Problem) as e:
            pp.apply(self.to_review, self.reviews)
        self.assertIn("changed since it was collected", str(e.exception))
        self.fill({"r1": SAME}, edit={"r1": {"translated_object": "MODIS", "record_title": "a title edited",
                                                "ground_truth_triple": "edited"}})
        self.assertEqual(len(pp.apply(self.to_review, self.reviews)[0]), 1)   # near miss: the shown cells may change

    def test_duplicate_rows(self):
        self.collect()
        rows = read(self.to_review)
        p1 = next(r for r in rows if r["record_id"] == "r1")
        write(self.to_review, pp.TO_REVIEW_COLUMNS, rows + [dict(p1)])
        self.fill({"r1": SAME})                                             # the same verdict twice: one row added
        self.assertEqual(len(pp.apply(self.to_review, self.reviews)[0]), 1)
        self.assertEqual(sum(r["record_id"] == "r1" and r["translated_object"] == "MODIS" for r in read(self.reviews)), 1)

    def test_conflicts_move_nothing(self):
        self.collect()
        rows = read(self.to_review)
        p1 = next(r for r in rows if r["record_id"] == "r1")
        write(self.to_review, pp.TO_REVIEW_COLUMNS, rows + [{**p1, "verdict": NOT_SAME}])
        rows = read(self.to_review)
        rows[0]["verdict"] = SAME if rows[0]["record_id"] == "r1" else ""
        write(self.to_review, pp.TO_REVIEW_COLUMNS, rows)
        with self.assertRaises(pp.Problem) as e:
            pp.apply(self.to_review, self.reviews)
        self.assertIn("conflict", str(e.exception))

    def test_against_a_verdict_already_there(self):
        self.collect()
        self.fill({"r1": SAME})
        with open(self.reviews, "a", encoding="utf-8", newline="") as f:     # filed meanwhile in the annotation tool
            csv.DictWriter(f, REVIEW_COLUMNS, lineterminator="\n").writerow(review("r1", GT1, EX1, NOT_SAME))
        with self.assertRaises(pp.Problem) as e:
            pp.apply(self.to_review, self.reviews)
        self.assertIn("conflict", str(e.exception))
        self.fill({"r1": NOT_SAME})                                          # the same verdict: not added twice
        added, already = pp.apply(self.to_review, self.reviews)
        self.assertEqual((added, len(already)), ([], 1))
        self.assertEqual(len(read(self.reviews)), 4)

    # ---- stale verdicts ----

    def test_stale_over_all_runs(self):
        gone = pp.delete_stale(self.runs, self.out, self.reviews)
        self.assertEqual([(r["record_id"], r["translated_object"]) for r in gone], [("r1", "Terra")])
        self.assertEqual(sorted((r["record_id"], r["ground_truth_object"]) for r in read(self.reviews)),
                         [("r1", "Level 2"), ("r9", "MODIS instrument")])   # r9: evaluated in no run, kept

    def test_stale_in_the_latest_run_only(self):
        """Near miss: P3's verdict applies in run A only, so given run C alone it is stale too."""
        gone = pp.delete_stale([self.runs[2]], self.out, self.reviews)
        self.assertEqual(sorted(r["translated_object"] for r in gone), ["2", "Terra"])

    def test_stale_matches_step_070(self):
        """The keys a verdict applies under are 070's own (pairing.verdict_keys): exact pairs count, a swapped
        reading doesn't for a predicate that isn't symmetric, and two unrelated objects don't."""
        keys = pp.pairing.verdict_keys("r1", [GT1, EXACT], [EX1, EXACT, triple("Aqua", "HAS_INSTRUMENT", "Terra")])
        self.assertEqual(len(keys), 2)
        self.assertIn(pp.row_key(review("r1", EXACT, EXACT, "")), keys)


if __name__ == "__main__":
    unittest.main()
