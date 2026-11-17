"""Evaluation's report (070_evaluate_helpers/stats.py and moves.py): precision and recall per predicate and per
entity class, and per record, on a case worked out by hand; the part's numbers pooled, not averaged over records;
what 060 removed, per reason; the reading of each row."""
import re
import unittest

from support import ROOT, use_step

use_step("070_evaluate")
import moves                                     # noqa: E402
import pairing                                   # noqa: E402
import readings                                  # noqa: E402
import stats                                     # noqa: E402
from test_evaluate_pairing import counts_record, record, translation, triple   # noqa: E402

# Worked out by hand. The translation table: every component class below translates to itself; USES_GADGET and
# Gadget (current schema) have rows that say (none).
CLASSES = ["Instrument", "Spacecraft", "Dataset", "MissionName"]
PREDICATES = ["ABOARD", "ACQUIRED_BY_INSTRUMENT", "ALSO_KNOWN_AS"]
GT = [triple("MODIS", "Instrument", "ABOARD", "Aqua", "Spacecraft"),                                   # g0
      triple("AIRS", "Instrument", "ABOARD", "Aqua", "Spacecraft"),                                    # g1
      triple("MODIS Snow Cover", "Dataset", "ACQUIRED_BY_INSTRUMENT", "MODIS", "Instrument")]          # g2
EXTRACTED = [triple("MODIS", "Instrument", "ABOARD", "Aqua", "Spacecraft"),          # e0: exact pair with g0
             triple("AIRS", "Dataset", "ABOARD", "Aqua", "Spacecraft"),              # e1: exact pair with g1, subject class wrong
             triple("MODIS", "Instrument", "ABOARD", "Terra", "Spacecraft"),         # e2: extracted only
             triple("Snow Cover", "Dataset", "ACQUIRED_BY_INSTRUMENT", "MODIS", "Instrument"),   # e3: partial pair with g2
             triple("MODIS Snow Cover", "Dataset", "USES_GADGET", "G1", "Gadget")]   # e4: untranslatable (its predicate's row says (none))
NONE = pairing.NO_TRANSLATION


def compared(gt=GT, extracted=EXTRACTED, rid="r1"):
    return pairing.compare_record(record(gt, extracted, rid=rid), translation(CLASSES, PREDICATES))


def rows(tables, table):
    """{component class: (occurrences, ground truth triples, counted against, exact pairs, partial-level pairs,
    exact precision, exact recall, partial precision, partial recall)}, in the table's order."""
    return {r["component_class"]: (r["occurrences"], r["ground_truth_triples"], r["counted_against"],
                                   r["exact"]["pairs"], r["partial"]["pairs"],
                                   r["exact"]["precision"]["value"], r["exact"]["recall"]["value"],
                                   r["partial"]["precision"]["value"], r["partial"]["recall"]["value"])
            for r in tables[table]}


def strict_rows(tables, table):
    """{component class: (within reach, ground truth triples within strict reach, strict recall upper bound, then at
    each level: strict pairs, F1, strict precision, strict recall, strict F1, strict recall within reach)}."""
    return {r["component_class"]: (r["within_reach"], r["within_strict_reach"], r["strict_recall_upper_bound"]["value"])
            + tuple(x for level in pairing.LEVELS for x in (
                r[level]["strict_pairs"], r[level]["f1"]["value"], r[level]["strict_precision"]["value"],
                r[level]["strict_recall"]["value"], r[level]["strict_f1"]["value"],
                r[level]["strict_recall_within_reach"]["value"]))
            for r in tables[table]}


class MarginCheckLines(unittest.TestCase):
    """The report's table of the margin of error's assumptions: the design effects, for reading, and the proportion
    of the catalog evaluated, which doesn't hold above 5%."""

    def checks(self, deff, share=0.001):
        return {"deff_range": deff, "catalog_proportion": share,
                "largest_record": {"extracted triples": {"record": "r1", "proportion": 0.1},
                                   "ground truth triples": {"record": "r1", "proportion": 0.1}}}

    def test_row(self):
        text = "\n".join(moves._margin_check_lines(self.checks({"low": 1.0, "high": 2.5})))
        self.assertIn("the design effect across the numbers: 1.00 to 2.50; below 10 records each range says it may "
                      "still be too narrow", text)
        self.assertNotIn("doesn't hold", text)
        text = "\n".join(moves._margin_check_lines(self.checks(None, share=0.2)))
        self.assertIn("none (every number at 0% or 100%, or one record)", text)
        self.assertEqual(text.count("doesn't hold"), 1)


class HeldOutLook(unittest.TestCase):
    """A look is logged only when a held-out record was evaluated: with none, nothing was seen, so no line is added
    and the count doesn't grow."""

    def test_no_held_out_record_no_look(self):
        import tempfile
        from types import SimpleNamespace
        from unittest import mock
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp:
            looks = Path(tmp) / "held_out_looks.csv"
            evaluated = SimpleNamespace(records=[{"id": "t1", "part": "tuning", "gt": [], "gt_describes": None}],
                                        schema_used={"made": {}})
            with mock.patch.object(moves, "LOOKS", looks):
                self.assertIsNone(moves._log_look(evaluated, SimpleNamespace(entity={}, predicate={}), "s.json"))
            self.assertFalse(looks.exists())

    def test_a_look_keeps_its_held_out_counts_apart(self):
        """A run that looked keeps its held-out records' counts in held_out_evaluations/<run id>.json, with the
        look's line of the log and its number, and its tuning records' counts in evaluations/ as every run does:
        neither file holds a record of the other part."""
        import json
        import tempfile
        from types import SimpleNamespace
        from unittest import mock
        from pathlib import Path
        from common.files import read_csv
        tr = translation(CLASSES, PREDICATES)
        records = []
        for n, (rid, part) in enumerate((("t1", "tuning"), ("h1", "held-out"), ("h2", "held-out"))):
            records.append(pairing.compare_record({**record(GT, EXTRACTED[:n + 1], rid=rid, part=part), "position": n}, tr))
        evaluated = SimpleNamespace(records=records, schema_used={"made": {"run_id": "060_extract_2026-01-01_0000"}},
                                    extraction_made={}, pending=[])
        with tempfile.TemporaryDirectory() as tmp:
            out, log = Path(tmp) / "out", Path(tmp) / "held_out_looks.csv"
            with mock.patch.object(moves, "LOOKS", log):
                first = moves._log_look(evaluated, tr, "s.json")
                second = moves._log_look(evaluated, tr, "s.json")
            self.assertEqual((first["count"], second["count"]), (1, 2))
            self.assertEqual(read_csv(log), [first["row"], second["row"]])            # what is kept is the logged line
            tuning = moves._keep_evaluation(evaluated, tr, out, records[:1], {})
            held = moves._keep_evaluation(evaluated, tr, out, records[1:], {}, look=second)
            self.assertEqual((tuning.parent.name, held.parent.name), ("evaluations", "held_out_evaluations"))
            kept_tuning, kept_held = (json.loads(p.read_text(encoding="utf-8")) for p in (tuning, held))
            self.assertEqual([r["id"] for r in kept_tuning["records"]], ["t1"])
            self.assertNotIn("look", kept_tuning)
            self.assertNotIn("part", kept_tuning)
            self.assertEqual([r["id"] for r in kept_held["records"]], ["h1", "h2"])
            self.assertEqual(kept_held["part"], "held-out")
            self.assertEqual(kept_held["look"], {**second["row"], "number": 2})
            self.assertEqual(kept_held["look"]["held_out_records"], "2")
            self.assertEqual(kept_held["look"]["extraction_run_id"], "060_extract_2026-01-01_0000")
            self.assertEqual(kept_held["recipe"], kept_tuning["recipe"])              # one recipe, written the one way
            for kept, source in ((kept_tuning, records[:1]), (kept_held, records[1:])):
                self.assertEqual([r["counts"] for r in kept["records"]],
                                 [dict(r["compared"]["counts"]) for r in source])
                # and what 070's split by drafting model reads, so py helpers/held_out_results.py can give it
                self.assertEqual([r["groups"] for r in kept["records"]],
                                 [{n: {k: dict(c) for k, c in g.items()} for n, g in r["compared"]["groups"].items()}
                                  for r in source])
                self.assertEqual([r["drafted_by_spellings"] for r in kept["records"]],
                                 [r["compared"]["drafted_by_spellings"] for r in source])
            self.assertEqual(sorted(p.name for p in out.iterdir()), ["evaluations", "held_out_evaluations"])


class HeldOutResults(unittest.TestCase):
    """py helpers/held_out_results.py: the held-out looks kept by 070, grouped by recipe (repeats together), each
    group pooled over its repeats as py helpers/compare_runs.py pools, with and without records left out on request;
    how many looks the log holds for each extraction, and whether the fingerprints agree across the looks. It reads
    kept results only."""

    @classmethod
    def setUpClass(cls):
        import importlib.util
        spec = importlib.util.spec_from_file_location("held_out_results", ROOT / "helpers" / "held_out_results.py")
        cls.h = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.h)

    #: (pairs, of) per record and repeat, pool positions 2, 5, 8, 11: record h08 is the one left out on request
    SIZES = [4, 10, 5, 8]
    PAIRS = {"model-a": [[4, 5, 1, 8], [2, 5, 1, 8], [3, 8, 0, 4]], "model-b": [[1, 2, 5, 3], [1, 4, 5, 3]]}

    def look(self, model, repeat, pairs, **more):
        """A kept look as 070 writes it: the extraction's recipe, the look's line, each record's counts."""
        records = []
        for i, (m, n) in enumerate(zip(pairs, self.SIZES)):
            counts = {"extracted": n, "untranslatable": 0, "gt": n, "within_reach": n, "within_strict_reach": n}
            for level in ("exact", "partial"):
                counts.update({f"{level}_pairs": m, f"{level}_strict_pairs": m, f"{level}_subject_class_pairs": m,
                               f"{level}_object_class_pairs": m, f"{level}_pairs_within_reach": m,
                               f"{level}_strict_pairs_within_strict_reach": m, f"{level}_pending_pairs": 0})
            records.append({"id": f"h{3 * i + 2:02d}", "position": 3 * i + 2, "stratum": "s", "twin": "",
                            "ground_truth_sha256": "g", "pending_sha256": "p", "translation": {}, "counts": counts,
                            "describes": {"truth": "D", "said": "D", "right": True}})
        run_id, ex = f"070_evaluate_2026-11-20_10{repeat:02d}-{model[-1]}", f"060_extract_2026-11-19_09{repeat:02d}-{model[-1]}"
        row = {"date": "2026-11-20", "run_id": run_id, "schema": "the_schema.json", "held_out_records": str(len(records)),
               "extraction_run_id": ex, "translation_sha256": more.get("translation", "t" * 64),
               "held_out_ground_truth_sha256": more.get("ground_truth", "g" * 64)}
        recipe = {"extraction (060)": {"run_id": ex, "git_commit": "abc", "schema": "the_schema.json",
                                       "settings": {"service": "anthropic", "model": model, "repeat": repeat},
                                       "model_calls": {"model": model, "repeat": repeat}},
                  "evaluation (070)": {"git_commit": more.get("commit", "def"), "translation": "the translation table",
                                       "translation_sha256": row["translation_sha256"], "evaluation_version": 3}}
        return {"run_id": run_id, "part": "held-out", "look": {**row, "number": more.get("number", repeat)},
                "recipe": recipe, "records": records}

    def looks(self):
        return [self.look(model, k + 1, pairs) for model, repeats in self.PAIRS.items() for k, pairs in enumerate(repeats)]

    def test_groups_are_repeats_of_one_recipe(self):
        runs = self.looks()
        groups = self.h.groups_of(runs)
        self.assertEqual([[self.h.extraction_of(r)["model"] for r in g] for g in groups],
                         [["model-a"] * 3, ["model-b"] * 2])
        self.assertEqual([[self.h.extraction_of(r)["repeat"] for r in g] for g in groups], [[1, 2, 3], [1, 2]])
        # parts that change neither the question nor the scoring (code versions, workers, batch, served_as, 070's
        # own model) don't split a recipe: such a run pools with model-a's repeats
        alike = self.look("model-a", 4, self.PAIRS["model-a"][0], commit="other")
        ex = alike["recipe"]["extraction (060)"]
        ex["git_commit"] = "abc (plus uncommitted changes)"
        ex["settings"].update(workers=8, batch=True, confirm_paid_calls=False)
        ex["model_calls"]["served_as"] = []
        alike["recipe"]["evaluation (070)"].update(service="google", model="gemini")
        self.assertEqual([len(g) for g in self.h.groups_of(runs + [alike])], [4, 2])
        # near-miss: the same model with another thinking setting isn't a repeat of that recipe, so it isn't pooled
        other = self.look("model-a", 4, self.PAIRS["model-a"][0])
        other["recipe"]["extraction (060)"]["settings"]["thinking"] = "low"
        self.assertEqual([len(g) for g in self.h.groups_of(runs + [other])], [3, 2, 1])
        self.assertIn("**More than one group extracts with model-a:**", self.h.report(runs + [other], []))

    def test_pooled_over_the_repeats_with_and_without(self):
        """Worked out by hand: model-a's exact recall pooled over 3 repeats is all its pairs over 3 x all its ground
        truth triples, (4+5+1+8 + 2+5+1+8 + 3+8+0+4) / (3 x 27) = 49/81; without h08 (5 ground truth triples; 1, 1, 0
        pairs) it is 47/66."""
        runs = self.looks()
        leave, unknown = self.h.leave_out_ids("#8", runs)
        self.assertEqual((leave, unknown), (["h08"], []))
        s = self.h.summary(self.h.groups_of(runs)[0], leave)
        self.assertEqual((s["ids"], s["without_ids"], s["left_out_here"]),
                         (["h02", "h05", "h08", "h11"], ["h02", "h05", "h11"], ["h08"]))
        pooled = {r["label"]: r for r in s["pooled"]}
        without = {r["label"]: r for r in s["pooled_without"]}
        self.assertAlmostEqual(pooled["exact: recall"]["value"], 49 / 81)
        self.assertAlmostEqual(without["exact: recall"]["value"], 47 / 66)
        self.assertLess(pooled["exact: recall"]["low"], 49 / 81)
        self.assertGreater(pooled["exact: recall"]["high"], 49 / 81)
        # each repeat's own value, on the same records
        each = {r["label"]: r for r in s["spread"]}["exact: recall"]
        self.assertEqual([round(v * 27) for v in each["values"]], [18, 16, 15])
        # the second group, by its own counts: (1+2+5+3 + 1+4+5+3) / (2 x 27); without h08, 14/44
        s = self.h.summary(self.h.groups_of(runs)[1], leave)
        self.assertAlmostEqual({r["label"]: r for r in s["pooled"]}["exact: recall"]["value"], 24 / 54)
        self.assertAlmostEqual({r["label"]: r for r in s["pooled_without"]}["exact: recall"]["value"], 14 / 44)
        text = self.h.report(runs, [r["look"] for r in runs], leave)
        self.assertIn("## Group 1: anthropic model-a, 3 repeat(s)", text)
        self.assertIn("## Group 2: anthropic model-b, 2 repeat(s)", text)
        self.assertIn("| Number | Pooled over the 3 repeat(s), all 4 records | 95% range | Bootstrap 95% range | "
                      "Without the 1 left out (3 records) | 95% range | Bootstrap 95% range |", text)
        rng = r"[0-9.]+% to [0-9.]+%"
        self.assertRegex(text, rf"\| exact: recall \| 60\.5% \| {rng} \| {rng} \| 71\.2% \| {rng} \| {rng} \|")
        self.assertRegex(text, rf"\| exact: recall \| 44\.4% \| {rng} \| {rng} \| 31\.8% \| {rng} \| {rng} \|")
        self.assertRegex(text, rf"\| exact: strict_recall \| 60\.5% \| {rng} \| – \|")      # bootstrap: headline only
        self.assertIn("1 record(s), named with `--leave_out`: #8 (`h08`)", text)
        # nothing left out: one column, and no section on records left out
        text = self.h.report(runs, [r["look"] for r in runs])
        self.assertIn("| Number | Pooled over the 3 repeat(s), all 4 records | 95% range | Bootstrap 95% range |\n", text)
        self.assertNotIn("left out on request", text)

    def test_leave_out_names_records_by_position_or_id(self):
        runs = self.looks()
        self.assertEqual(self.h.leave_out_ids("5, #11 ,h02,5", runs), (["h05", "h11", "h02"], []))
        self.assertEqual(self.h.leave_out_ids("", runs), ([], []))
        # near-misses: a position no held-out record of these runs has (a tuning record's), and an unknown id
        self.assertEqual(self.h.leave_out_ids("3,#8,nope", runs), (["h08"], ["3", "nope"]))

    def test_a_record_not_in_every_repeat_is_left_out_and_said(self):
        runs = self.looks()[:3]
        runs[1]["records"] = [r for r in runs[1]["records"] if r["id"] != "h05"]      # e.g. its model call failed
        runs[2]["records"][0]["ground_truth_sha256"] = "changed"                      # h02's ground truth changed
        s = self.h.summary(runs, [])
        self.assertEqual(s["ids"], [])                                                # h02 out, so nothing before it
        self.assertEqual(s["left"]["not evaluated in every run"], ["h05"])
        self.assertEqual(s["left"]["ground truth changed between the runs"], ["h02"])
        text = self.h.report(runs, [])
        self.assertIn("No record is left to pool, so this group has no numbers.", text)
        self.assertIn("Left out, ground truth changed between the runs: 1 (#2 (`h02`))", text)

    def test_the_looks_and_their_fingerprints(self):
        runs = self.looks()
        log = [r["look"] for r in runs]
        text = self.h.report(runs, [{k: v for k, v in row.items() if k != "number"} for row in log])
        self.assertIn("5 run(s) of step 070, each a look at the held-out part, in 2 group(s)", text)
        self.assertIn("- **Fingerprint of the translation** (`translation_sha256`): the same in all 5 looks.", text)
        self.assertIn("- **Fingerprint of the held-out records' ground truth** (`held_out_ground_truth_sha256`): the "
                      "same in all 5 looks.", text)
        self.assertIn("- **Looks per extraction:** every extraction summarized here has one look in the log.", text)
        self.assertIn("holds 5 look(s) in all; all are summarized here.", text)
        self.assertTrue(all(len(e["looks"]) == 1 and e["in_log"] == 1 for e in self.h.looks_of(runs, log)))
        # an extraction looked at twice, the ground truth changed in between; a look of the log not summarized; a
        # kept look whose line is gone from the log; and a translation fingerprint that differs between the looks
        earlier = {**runs[0]["look"], "run_id": "070_evaluate_2026-11-18_0800", "held_out_ground_truth_sha256": "x" * 64}
        stranger = {**runs[0]["look"], "run_id": "070_evaluate_2026-11-17_0700", "extraction_run_id": "060_other"}
        runs[4]["look"]["translation_sha256"] = "u" * 64
        log = [stranger, earlier] + [r["look"] for r in runs[:4]]
        entries = self.h.looks_of(runs, log)
        self.assertEqual([len(e["looks"]) for e in entries], [2, 1, 1, 1, 0])
        self.assertEqual(entries[0]["same"], {"translation_sha256": True, "held_out_ground_truth_sha256": False})
        self.assertEqual([e["in_log"] for e in entries], [1, 1, 1, 1, 0])
        self.assertEqual(self.h.same_everywhere(runs), {"translation_sha256": False, "held_out_ground_truth_sha256": True})
        text = self.h.report(runs, log)
        self.assertIn("(`translation_sha256`): NOT the same in all 5 looks", text)
        self.assertIn(f"- **Looked at more than once:** 060's run `{entries[0]['extraction']['run_id']}` has 2 looks "
                      f"in the log (070's runs `070_evaluate_2026-11-18_0800`, `{runs[0]['run_id']}`); between them, "
                      f"the held-out records' ground truth changed, so a change was made after a look.", text)
        self.assertIn(f"- **Looks not in the log as kept:** `{runs[4]['run_id']}` has 0 line(s)", text)
        self.assertIn("holds 6 look(s) in all; 2 of them are not summarized here", text)
        self.assertNotIn("every extraction summarized here has one look", text)

    def test_two_looks_at_one_extraction_are_refused(self):
        runs = self.looks()
        self.assertIsNone(self.h.check(runs))
        self.assertIn("given more than once", self.h.check(runs + runs[:1]))
        again = self.look("model-a", 1, self.PAIRS["model-a"][0])
        again["run_id"] = "070_evaluate_2026-11-21_1200"                               # a second look, the same 060 run
        self.assertIn("looks at the same extraction, whose repeat would count twice", self.h.check(runs + [again]))

    def test_reads_kept_results_only(self):
        """The command lists and summarizes from the files kept: no line is added to the log, nothing is written
        beside the report, and no model call can leave (llm.forbid_model_calls, which the listing sets too)."""
        import io
        import json
        import os
        import tempfile
        from contextlib import redirect_stdout
        from pathlib import Path
        from unittest import mock
        from common import llm
        self.addCleanup(llm.allow_model_calls)                                       # the other tests of this file
        with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(os.environ):
            tmp = Path(tmp)
            kept, log, reports = tmp / "held_out_evaluations", tmp / "held_out_looks.csv", tmp / "reports"
            kept.mkdir()
            runs = self.looks()
            for run in runs:
                (kept / f"{run['run_id']}.json").write_text(json.dumps(run), encoding="utf-8")
            columns = moves.LOOKS_COLUMNS
            log.write_text("\n".join([",".join(columns)] + [",".join(r["look"][c] for c in columns) for r in runs])
                           + "\n", encoding="utf-8")
            before = log.read_bytes()
            with mock.patch.object(self.h, "KEPT", kept), mock.patch.object(self.h, "LOOKS", log), \
                    mock.patch.object(self.h, "REPORTS_DIR", reports):
                said = io.StringIO()
                with redirect_stdout(said):
                    self.assertEqual(self.h.main([]), 0)
                self.assertEqual(said.getvalue().count("070_evaluate_2026-11-20"), 5)
                said = io.StringIO()
                with redirect_stdout(said):
                    self.assertEqual(self.h.main(["--leave_out", "8"] + [str(kept / f"{r['run_id']}.json") for r in runs]), 0)
                self.assertIn("Summarized 5 held-out look(s) in 2 group(s), with and without 1 record(s)", said.getvalue())
                with self.assertRaises(SystemExit) as stop:                          # a mismatch with what was asked: said, nothing written
                    self.h.main(["--leave_out", "999"] + [str(kept / f"{r['run_id']}.json") for r in runs])
                self.assertIn("--leave_out names 1 record(s) that are not held-out records of these runs (999)", str(stop.exception))
                with self.assertRaises(SystemExit) as stop:
                    self.h.load("070_evaluate_2026-01-01_0000", kept)
                self.assertIn("No held-out look is kept for 070_evaluate_2026-01-01_0000", str(stop.exception))
            self.assertEqual(log.read_bytes(), before)
            self.assertEqual(len(list(reports.glob("held_out_results_*.md"))), 1)
            self.assertEqual(sorted(p.name for p in tmp.iterdir()), ["held_out_evaluations", "held_out_looks.csv", "reports"])
            self.assertIn("py helpers/held_out_results.py is free", llm.FORBIDDEN["why"])

    #: By drafting model, worked out by hand: two repeats of one recipe, two held-out records. h02 has 6
    #: occurrences and 4 ground truth triples (3 drafted by claude-opus-5-5, spelled "claude-opus-5.5"; 1 with no
    #: drafting model); h05 has 3 occurrences and 2 (1 claude-opus-5-5, 1 gemini-4-argon). Each group's counts per
    #: repeat: (exact pairs, exact strict pairs, partial pairs, partial strict pairs).
    DRAFTED = {"h02": {"gt": {"claude-opus-5-5": 3, "": 1}, "extracted": 6,
                       "pairs": [{"claude-opus-5-5": (2, 2, 3, 2), "": (0, 0, 1, 1)},
                                 {"claude-opus-5-5": (1, 1, 2, 2), "": (0, 0, 0, 0)}]},
               "h05": {"gt": {"claude-opus-5-5": 1, "gemini-4-argon": 1}, "extracted": 3,
                       "pairs": [{"claude-opus-5-5": (1, 1, 1, 1), "gemini-4-argon": (0, 0, 1, 0)},
                                 {"claude-opus-5-5": (1, 1, 1, 1), "gemini-4-argon": (1, 1, 1, 1)}]}}

    def drafted_looks(self, with_groups=True):
        """Two kept looks (repeats 1 and 2 of claude-opus-5-5) of the records of DRAFTED, as 070 keeps them."""
        runs = []
        for k in (0, 1):
            run = self.look("claude-opus-5-5", k + 1, [0, 0, 0, 0])
            run["records"] = run["records"][:2]
            for r in run["records"]:
                d = self.DRAFTED[r["id"]]
                groups = {g: {"gt": d["gt"][g], "exact_pairs": e, "exact_strict_pairs": es, "partial_pairs": p,
                              "partial_strict_pairs": ps} for g, (e, es, p, ps) in d["pairs"][k].items()}
                counts = {"extracted": d["extracted"], "untranslatable": 0, "gt": sum(d["gt"].values()),
                          **{f"{level}_pairs": sum(g[f"{level}_pairs"] for g in groups.values())
                             for level in ("exact", "partial")},
                          **{f"{level}_strict_pairs": sum(g[f"{level}_strict_pairs"] for g in groups.values())
                             for level in ("exact", "partial")}}
                r["counts"] = counts
                if with_groups:
                    r["groups"] = {"drafted_by": groups}
                    r["drafted_by_spellings"] = {g: ["claude-opus-5.5"] if g == "claude-opus-5-5" else [g] if g else [""]
                                                 for g in groups}
            runs.append(run)
        return runs

    def test_by_drafting_model_pooled_over_the_repeats(self):
        """Each record's parts are averaged over the 2 repeats, then summed over the records. claude-opus-5-5:
        exact recall (1.5 + 1) / (3 + 1) = 5/8; partial recall (2.5 + 1) / 4 = 7/8; exact share of pairs (1.5 + 1)
        / (2.5 + 1) = 5/7; entity-class accuracy (2 + 1) / 3.5 = 6/7; attributed precision, partial: each record's
        denominator is its counted occurrences less the other groups' pairs, h02 (6 − 4 + 3, 6 − 2 + 2) = 5.5 on
        average and h05 (3 − 2 + 1, 3 − 2 + 1) = 2, so (2.5 + 1) / (5.5 + 2) = 7/15; F1 2 × 3.5 / (7.5 + 4) = 14/23.
        gemini-4-argon: exact recall 0.5 / 1, partial recall 1 / 1, entity-class accuracy 0.5 / 1. Without h05:
        claude-opus-5-5's exact recall 1.5 / 3 = 1/2, and gemini-4-argon, which drafted no triple of h02, has no
        row."""
        runs = self.drafted_looks()
        s = self.h.summary(runs, ["h05"])
        by, without = s["drafted_by"]["groups"], s["drafted_by_without"]["groups"]
        self.assertEqual(list(by), ["claude-opus-5-5", "gemini-4-argon", ""])          # most triples first, none last
        claude = {path: r["value"] for path, r in by["claude-opus-5-5"]["numbers"].items()}
        self.assertEqual((by["claude-opus-5-5"]["gt_triples"], by["claude-opus-5-5"]["records"]), (4, 2))
        for path, value in {("exact", "recall"): 5 / 8, ("partial", "recall"): 7 / 8, ("exact_share",): 5 / 7,
                            ("partial", "entity_class_accuracy"): 6 / 7, ("partial", "precision"): 7 / 15,
                            ("partial", "f1"): 14 / 23}.items():
            self.assertAlmostEqual(claude[path], value, msg=path)
        gemini = {path: r["value"] for path, r in by["gemini-4-argon"]["numbers"].items()}
        self.assertAlmostEqual(gemini[("exact", "recall")], 0.5)
        self.assertAlmostEqual(gemini[("partial", "recall")], 1.0)
        self.assertAlmostEqual(gemini[("partial", "entity_class_accuracy")], 0.5)
        self.assertEqual(list(without), ["claude-opus-5-5", ""])
        self.assertAlmostEqual(without["claude-opus-5-5"]["numbers"][("exact", "recall")]["value"], 0.5)
        # one repeat alone gives 070's own by_group numbers: the same grouping code, not a second one
        one = self.h.by_drafting_model(runs[:1], ["h02", "h05"])["groups"]
        own = stats.by_group(self.h.compare_runs.as_records(runs[0], ["h02", "h05"]), "drafted_by")
        for g in own:
            self.assertAlmostEqual(one[g]["numbers"][("partial", "precision")]["value"], own[g]["partial"]["precision"]["value"])
            self.assertAlmostEqual(one[g]["numbers"][("partial", "precision")]["low"], own[g]["partial"]["precision"]["low"])
            self.assertAlmostEqual(one[g]["numbers"][("exact_share",)]["value"], own[g]["exact_share"]["value"])
        text = self.h.report(runs, [r["look"] for r in runs], ["h05"])
        self.assertIn("### By who drafted the ground truth, pooled over the 2 repeat(s)", text)
        self.assertIn("| Ground truth triples | Count | Records | Recall (exact) | Recall (partial) | Exact share of pairs | "
                      "Entity-class accuracy (partial) | Precision, attributed (partial) | F1, attributed (partial) |", text)
        self.assertRegex(text, r"\| drafted by `claude-opus-5\.5` \(the extraction model's name\) \| 4 \| 2 \| 62\.5% "
                               r"\([0-9.]+% to [0-9.]+%\) \| 87\.5% ")
        self.assertIn("| no drafting model recorded (`drafted_by` empty) | 1 | 1 |", text)
        self.assertIn("Without the 1 record(s) left out on request (1 records):", text)
        self.assertRegex(text, r"\| drafted by `claude-opus-5\.5` \(the extraction model's name\) \| 3 \| 1 \| 50\.0% ")

    def test_by_drafting_model_near_misses(self):
        # a look kept before the split was kept: said, no numbers
        runs = self.drafted_looks()
        runs[1] = self.drafted_looks(with_groups=False)[1]
        by = self.h.by_drafting_model(runs, ["h02", "h05"])
        self.assertIsNone(by["groups"])
        self.assertIn("kept without the counts by drafting model", by["why"])
        self.assertIn("No numbers by drafting model: a look of this group was kept without", self.h.report(runs, []))
        # a drafted_by cell changed between the looks (the ground truth fingerprint doesn't cover it)
        runs = self.drafted_looks()
        g = runs[1]["records"][1]["groups"]["drafted_by"]
        g["claude-opus-5-5"]["gt"], g["gemini-4-argon"]["gt"] = 2, 0
        self.assertIn("fall into the drafting models differently in two runs",
                      self.h.by_drafting_model(runs, ["h02", "h05"])["why"])
        self.assertEqual(self.h.by_drafting_model(runs, [])["why"], "no record is pooled")

    def test_limits_are_the_guides(self):
        guide = (ROOT / "helpers" / "held_out_results.md").read_text(encoding="utf-8")
        plain = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", guide)
        for line in self.h.LIMITS:
            self.assertIn(line, plain)


class PerComponentClass(unittest.TestCase):
    def setUp(self):
        self.tables = stats.per_component_class([compared()])

    def test_per_predicate(self):
        got = rows(self.tables, "predicate")
        self.assertEqual(got, {
            "ACQUIRED_BY_INSTRUMENT": (1, 1, 2, 0, 1, 0.0, 0.0, 1.0, 1.0),
            "ABOARD": (3, 2, 1, 2, 2, 2 / 3, 1.0, 2 / 3, 1.0),
            f"USES_GADGET{NONE}": (1, 0, 0, 0, 0, None, None, None, None)})   # e4 untranslatable: out of precision
        self.assertEqual(list(got), ["ACQUIRED_BY_INSTRUMENT", "ABOARD", f"USES_GADGET{NONE}"])  # most counted against first

    def test_per_subject_class(self):
        # e1's wrong subject class: against Dataset's precision (extraction named it) and Instrument's recall (the
        # ground truth has it), though e1 and g1 are a pair
        got = rows(self.tables, "subject class")
        self.assertEqual(got, {
            "Dataset": (3, 1, 3, 0, 1, 0.0, 0.0, 1 / 2, 1.0),             # e4 is untranslatable: 2 counted
            "Instrument": (2, 2, 2, 1, 1, 0.5, 0.5, 0.5, 0.5)})
        self.assertEqual(list(got), ["Dataset", "Instrument"])

    def test_per_object_class(self):
        got = rows(self.tables, "object class")
        self.assertEqual(got, {
            "Instrument": (1, 1, 2, 0, 1, 0.0, 0.0, 1.0, 1.0),
            "Spacecraft": (3, 2, 1, 2, 2, 2 / 3, 1.0, 2 / 3, 1.0),
            f"Gadget{NONE}": (1, 0, 0, 0, 0, None, None, None, None)})
        self.assertEqual(list(got), ["Instrument", "Spacecraft", f"Gadget{NONE}"])

    def test_strict_f1_and_reach(self):
        """Every component class here is within reach and every ground truth triple within strict reach. Strict:
        e1 pairs with g1 but its subject class is wrong, so it is strict for no row; e0 (exact) and e3 (partial)
        are strict."""
        self.assertEqual(strict_rows(self.tables, "predicate"), {
            "ACQUIRED_BY_INSTRUMENT": (True, 1, 1.0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 1, 1.0, 1.0, 1.0, 1.0, 1.0),
            "ABOARD": (True, 2, 1.0, 1, 0.8, 1 / 3, 0.5, 0.4, 0.5, 1, 0.8, 1 / 3, 0.5, 0.4, 0.5),
            f"USES_GADGET{NONE}": (None, 0, None, 0, None, None, None, None, None, 0, None, None, None, None, None)})
        self.assertEqual(strict_rows(self.tables, "subject class"), {
            "Dataset": (True, 1, 1.0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 1, 2 / 3, 1 / 2, 1.0, 2 / 3, 1.0),
            "Instrument": (True, 2, 1.0, 1, 0.5, 0.5, 0.5, 0.5, 0.5, 1, 0.5, 0.5, 0.5, 0.5, 0.5)})
        self.assertEqual(strict_rows(self.tables, "object class"), {
            "Instrument": (True, 1, 1.0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 1, 1.0, 1.0, 1.0, 1.0, 1.0),
            f"Gadget{NONE}": (None, 0, None, 0, None, None, None, None, None, 0, None, None, None, None, None),
            "Spacecraft": (True, 2, 1.0, 1, 0.8, 1 / 3, 0.5, 0.4, 0.5, 1, 0.8, 1 / 3, 0.5, 0.4, 0.5)})

    def test_out_of_reach(self):
        """Checked rows translate only to ABOARD, Instrument, and Spacecraft; extraction says only e0. Then
        ACQUIRED_BY_INSTRUMENT and Dataset (subject class) are out of reach, so g2 is within strict reach for no
        row; Instrument as object class is within reach, but its one ground truth triple (g2) isn't within strict
        reach, since its subject class (Dataset) is out of reach."""
        t = translation(CLASSES, PREDICATES, reachable_entity=["Instrument", "Spacecraft"], reachable_predicates=["ABOARD"])
        tables = stats.per_component_class([pairing.compare_record(record(GT, EXTRACTED[:1]), t)])
        reach = {table: {r["component_class"]: (r["within_reach"], r["within_strict_reach"], r["ground_truth_triples"],
                                                 r["strict_recall_upper_bound"]["value"],
                                                 r["exact"]["strict_recall_within_reach"]["value"])
                         for r in tables[table]} for table in tables}
        self.assertEqual(reach, {
            "predicate": {"ACQUIRED_BY_INSTRUMENT": (False, 0, 1, 0.0, None), "ABOARD": (True, 2, 2, 1.0, 0.5)},
            "subject class": {"Dataset": (False, 0, 1, 0.0, None), "Instrument": (True, 2, 2, 1.0, 0.5)},
            "object class": {"Instrument": (True, 0, 1, 0.0, None), "Spacecraft": (True, 2, 2, 1.0, 0.5)}})
        text = "\n".join(moves._per_component_class_lines({"records": 1}, tables))
        self.assertIn("| ACQUIRED_BY_INSTRUMENT | out of reach; 0 of 1 ground truth triple within strict reach | 0% | 0 "
                      "| 0 | 0 | 1 | 1 | 0 | no value (0 to divide by) | 0% | 0% | no value (0 to divide by) | 0% | 0% | no value (0 to divide by: no ground truth triple within strict reach) "
                      "| 0 |", text)
        self.assertIn("| Instrument | within reach; 0 of 1 ground truth triple within strict reach | 0% |", text)

    def test_counts_agree_with_the_totals(self):
        """Each table's occurrences, ground truth triples, and predicate pairs add up to the part's counts."""
        c = compared()["compared"]["counts"]
        for table in ("predicate", "subject class", "object class"):
            self.assertEqual(sum(r["occurrences"] for r in self.tables[table]), c["extracted"])
            self.assertEqual(sum(r["ground_truth_triples"] for r in self.tables[table]), c["gt"])
        for level in pairing.LEVELS:
            self.assertEqual(sum(r[level]["pairs"] for r in self.tables["predicate"]), c[f"{level}_pairs"])
            for table in ("predicate", "subject class", "object class"):       # a strict pair counts for every row it names
                self.assertEqual(sum(r[level]["strict_pairs"] for r in self.tables[table]), c[f"{level}_strict_pairs"])
            self.assertEqual(sum(r[level]["pairs"] for r in self.tables["subject class"]), c[f"{level}_subject_class_pairs"])
            self.assertEqual(sum(r[level]["pairs"] for r in self.tables["object class"]), c[f"{level}_object_class_pairs"])

    def test_swapped_pair_counts_the_way_round_it_was_paired(self):
        """An ALSO_KNOWN_AS occurrence paired with subject and object swapped counts for the entity classes it was
        paired with: Spacecraft as subject class, MissionName as object class."""
        gt = [triple("Aqua", "Spacecraft", "ALSO_KNOWN_AS", "EOS PM-1", "MissionName")]
        ex = [triple("EOS PM-1", "MissionName", "ALSO_KNOWN_AS", "Aqua", "Spacecraft")]
        tables = stats.per_component_class([compared(gt, ex)])
        self.assertEqual(rows(tables, "subject class"), {"Spacecraft": (1, 1, 0, 1, 1, 1.0, 1.0, 1.0, 1.0)})
        self.assertEqual(rows(tables, "object class"), {"MissionName": (1, 1, 0, 1, 1, 1.0, 1.0, 1.0, 1.0)})

    def test_margins(self):
        """Every row gets its range from 2 records on, by the part's formula; one record: none; fewer than
        FEW_RECORDS records with something to divide by: marked few_records."""
        one = stats.per_component_class([compared(rid="r0")])
        self.assertIsNone(one["predicate"][0]["exact"]["precision"]["low"])
        few = stats.per_component_class([compared(rid=f"r{i}") for i in range(3)])
        row = next(r for r in few["predicate"] if r["component_class"] == "ABOARD")["exact"]["precision"]
        self.assertEqual((row["few_records"], row["low"] is not None), (True, True))
        other = [triple("MODIS", "Instrument", "ABOARD", "Aqua", "Spacecraft")]
        recs = [compared(rid=f"r{i}") if i % 2 else compared(other, other, rid=f"r{i}") for i in range(20)]
        aboard = next(r for r in stats.per_component_class(recs)["predicate"] if r["component_class"] == "ABOARD")
        p = aboard["exact"]["precision"]
        self.assertAlmostEqual(p["value"], (10 * 2 + 10) / (10 * 3 + 10))
        self.assertLess(p["low"], p["value"])
        self.assertGreater(p["high"], p["value"])
        self.assertFalse(p["few_records"])
        f = aboard["exact"]["strict_f1"]                          # the strict versions get ranges by the same formula
        self.assertAlmostEqual(f["value"], 2 * (10 + 10) / (10 * 5 + 10 * 2))
        self.assertLess(f["low"], f["value"])
        # every record has all its ground truth triples within strict reach: 100%, each record one trial (our choice)
        u = aboard["strict_recall_upper_bound"]
        self.assertEqual((u["value"], u["high"], u["deff"]), (1.0, 1.0, None))
        self.assertLess(u["low"], 1.0)

    def test_report_tables(self):
        n = {"records": 1}
        text = "\n".join(moves._per_component_class_lines(n, self.tables))
        self.assertIn("**One record only, so no number has a margin of error", text)
        self.assertIn("| Predicate (ground truth schema) | Reach | Strict recall upper bound | Occurrences | Untranslatable | Occurrences with "
                      "multiplicity > 1 | Ground truth "
                      "triples | Counted against it (exact) | Exact pairs that count for it | Precision (exact) | Recall "
                      "(exact) | F1 (exact) | Precision (strict exact) | Recall (strict exact) | F1 (strict exact) | "
                      "Recall within reach (strict exact) | Pairs that count for it (partial level) | Precision (partial) "
                      "| Recall (partial) | F1 (partial) | Precision (strict partial) | Recall (strict partial) | F1 "
                      "(strict partial) | Recall within reach (strict partial) |", text)
        self.assertIn("| ABOARD | within reach; 2 of 2 ground truth triples within strict reach | 100% | 3 | 0 | 0 | 2 | 1 | 2 | "
                      "67% | 100% | 80% | 33% | 50% | 40% | 50% | 2 | 67% | 100% | 80% | 33% | 50% | 40% | 50% |", text)
        # e4 is untranslatable: out of Dataset's precision (2 counted, not 3) and of its count against it
        self.assertIn("| Dataset | within reach; 1 of 1 ground truth triple within strict reach | 100% | 3 | 1 | 0 | 1 | 3 | 0 | "
                      "0% | 0% | 0% | 0% | 0% | 0% | 0% | 1 | 50% | 100% | 67% | 50% | 100% | 67% | 100% |", text)
        none, all_out = "no value (0 to divide by)", moves.ALL_UNTRANSLATABLE
        self.assertIn(f"| Gadget{NONE} | none: translates to (none), so not in the ground truth schema | {none} | 1 | 1 | 0 | 0 | 0 | 0 | "
                      f"{all_out} | {none} | {none} | {all_out} | {none} | {none} | {moves.NONE_WITHIN_STRICT_REACH} | 0 | "
                      f"{all_out} | {none} | {none} | {all_out} | {none} | {none} | {moves.NONE_WITHIN_STRICT_REACH} |", text)
        n["records"] = 5
        self.assertIn("From 5 records only (fewer than 10)", "\n".join(moves._per_component_class_lines(n, self.tables)))
        n["records"] = 30
        text = "\n".join(moves._per_component_class_lines(n, self.tables))
        self.assertIn("about 1 in 20 of their margins of error misses the true value by chance (each is a 95% range)", text)
        self.assertNotIn("records only", text)


class PerRecord(unittest.TestCase):
    """Each record's own numbers, on the case above: 5 occurrences, 3 ground truth triples; exact pairs e0-g0 and
    e1-g1, partial pair e3-g2; strict: e0 (exact) and e3 (partial), since e1's subject class is wrong; all 3 ground
    truth triples within reach and within strict reach."""
    def setUp(self):
        self.r = dict(compared(), position=3, part="tuning", stratum="g",
                      title="MODIS and AIRS aboard Aqua: a title longer than fifty characters")

    def test_numbers(self):
        (row,) = stats.per_record([self.r])
        self.assertEqual((row["id"], row["position"], row["occurrences"], row["ground_truth_triples"],
                          row["counted_against"], row["recall_upper_bound"], row["strict_recall_upper_bound"]),
                         ("r1", 3, 5, 3, 3, 1.0, 1.0))           # 5 - 1 untranslatable + 3 - 2 x 2 exact pairs
        self.assertEqual(row["untranslatable"], 1)                                # e4
        self.assertEqual(row["exact"], {"pairs": 2, "strict_pairs": 1, "precision": 2 / 4, "recall": 2 / 3,
                                        "f1": 4 / 7, "strict_precision": 1 / 4, "strict_recall": 1 / 3,
                                        "strict_f1": 2 / 7, "recall_within_reach": 2 / 3,
                                        "strict_recall_within_reach": 1 / 3})
        self.assertEqual(row["partial"], {"pairs": 3, "strict_pairs": 2, "precision": 3 / 4, "recall": 1.0,
                                          "f1": 6 / 7, "strict_precision": 2 / 4, "strict_recall": 2 / 3,
                                          "strict_f1": 4 / 7, "recall_within_reach": 1.0,
                                          "strict_recall_within_reach": 2 / 3})

    def test_worst_first_then_pool_position(self):
        perfect = [triple("MODIS", "Instrument", "ABOARD", "Aqua", "Spacecraft")]
        recs = [dict(compared(perfect, perfect, rid="good"), position=0, title=""),
                dict(compared(rid="late"), position=9, title=""), dict(compared(rid="early"), position=5, title="")]
        self.assertEqual([(x["id"], x["counted_against"]) for x in stats.per_record(recs)],
                         [("early", 3), ("late", 3), ("good", 0)])

    def test_no_value(self):
        """A record with no occurrences: no precision; with no ground truth triples: no recall, no upper bound."""
        (row,) = stats.per_record([dict(compared(GT, [], rid="none said"), position=0, title="")])
        self.assertEqual((row["exact"]["precision"], row["exact"]["recall"], row["exact"]["f1"]), (None, 0.0, 0.0))
        (row,) = stats.per_record([dict(compared([], EXTRACTED[:1], rid="no truth"), position=0, title="")])
        self.assertEqual((row["exact"]["precision"], row["exact"]["recall"], row["recall_upper_bound"],
                          row["exact"]["recall_within_reach"]), (0.0, None, None, None))
        text = "\n".join(moves._per_record_lines([row]))
        self.assertIn("| 0 | `no truth` |  | 1 | 0 | 0 | 0 | 1 | no value (0 to divide by) | no value (0 to divide by) | 0 | 0 | 0% | no value (0 to divide by) | 0% |", text)

    def test_report_table(self):
        text = "\n".join(moves._per_record_lines(stats.per_record([self.r])))
        self.assertIn("are never an average of these (why: `070_evaluate/metrics.md`, *Pooled, not averaged*)", text)
        self.assertIn("No margin of error: each row is one record, and a range needs at least 2 "
                      "(`070_evaluate/metrics/approximately.md`). *no value (0 to divide by)*: e.g. precision of a record "
                      "with no occurrences", text)
        self.assertIn("| Pool position | Record id (first 8 characters) | Title (first 50 characters) | Occurrences | "
                      "Untranslatable | Occurrences with multiplicity > 1 | Ground truth triples | Counted against it (exact) | Recall upper bound | Strict recall upper "
                      "bound | Pairs (exact) | Strict pairs (exact) | Precision (exact) | Recall (exact) | F1 (exact) | "
                      "Precision (strict exact) | Recall (strict exact) | F1 (strict exact) | Recall within reach "
                      "(exact) | Recall within reach (strict exact) | Pairs (partial) | Strict pairs (partial) | "
                      "Precision (partial) | Recall (partial) | F1 (partial) | Precision (strict partial) | Recall "
                      "(strict partial) | F1 (strict partial) | Recall within reach (partial) | Recall within reach "
                      "(strict partial) |", text)
        self.assertIn("| 3 | `r1` | MODIS and AIRS aboard Aqua: a title longer than fi\u2026 | 5 | 1 | 0 | 3 | 3 | 100% | 100% | "
                      "2 | 1 | 50% | 67% | 57% | 25% | 33% | 29% | 67% | 33% | "
                      "3 | 2 | 75% | 100% | 86% | 50% | 67% | 57% | 100% | 67% |", text)
        many = stats.per_record([dict(compared(rid=f"r{i}"), position=i, title="") for i in range(moves.SHOW + 2)])
        self.assertIn("| \u2026 2 more, in `metrics.json` and `per_record.md` |", "\n".join(moves._per_record_lines(many)))
        self.assertEqual(moves._per_record_lines([])[-2], "| none |" + " |" * 29)

    def test_block_in_per_record_md(self):
        text = moves._per_record([self.r], 0)
        block = ("Occurrences 5 (with multiplicity > 1: 0; untranslatable: 1) \u00b7 ground truth triples 3 \u00b7 counted against it (exact) 3 \u00b7 recall "
                 "upper bound 100% \u00b7 strict recall upper bound 100%\n\n"
                 "| | exact | partial | strict exact | strict partial |\n|---|---:|---:|---:|---:|\n"
                 "| Pairs | 2 | 3 | 1 | 2 |\n| Precision | 50% | 75% | 25% | 50% |\n| Recall | 67% | 100% | 33% | 67% |\n"
                 "| F1 | 57% | 86% | 29% | 57% |\n| Recall within reach | 67% | 100% | 33% | 67% |\n")
        self.assertIn(block, text)
        self.assertLess(text.index(block), text.index("**Pairs**"))           # above the record's pairs


class Multiplicity(unittest.TestCase):
    """Two extracted triples that translate to the same translated extracted triple: "MODIS" and "the MODIS"
    (Instrument) ABOARD "Aqua" (Spacecraft) read the same once evened out, so that element of the record's multiset
    of translated extracted triples has multiplicity 2. Only one of its occurrences pairs with the ground truth
    triple; the other is extracted only."""
    def setUp(self):
        ex = [EXTRACTED[0], triple("the MODIS", "Instrument", "ABOARD", "Aqua", "Spacecraft"), EXTRACTED[2]]
        self.r = dict(compared(GT[:1], ex), position=0, title="T")

    def test_counted(self):
        c = self.r["compared"]
        self.assertEqual(c["multiplicity"], [2, 2, 1])  # pyright: ignore[reportIndexIssue]  (compared() returns a dict)
        self.assertEqual(c["counts"]["occurrences_multiplicity_above_1"], 2)  # pyright: ignore[reportIndexIssue]  (as above)
        (row,) = stats.per_record([self.r])
        self.assertEqual((row["occurrences"], row["occurrences_multiplicity_above_1"]), (3, 2))
        tables = stats.per_component_class([self.r])
        self.assertEqual({r["component_class"]: (r["occurrences"], r["occurrences_multiplicity_above_1"])
                          for r in tables["object class"]}, {"Spacecraft": (3, 2)})

    def test_marked_in_per_record_md(self):
        text = moves._per_record([self.r], 0)
        mark = (" \u2014 \u00d72: 2 extracted triples translate to this (as extracted, current schema): MODIS "
                "(Instrument) ABOARD Aqua (Spacecraft); the MODIS (Instrument) ABOARD Aqua (Spacecraft)")
        self.assertIn("- \u2713 exact: MODIS (Instrument) ABOARD Aqua (Spacecraft)" + mark + "\n", text)
        self.assertIn("- \u2717 the MODIS (Instrument) ABOARD Aqua (Spacecraft)" + mark + "\n", text)
        self.assertIn("- \u2717 MODIS (Instrument) ABOARD Terra (Spacecraft)\n", text)     # multiplicity 1: no mark
        self.assertIn("Occurrences 3 (with multiplicity > 1: 2; untranslatable: 0)", text)


class RowReadings(unittest.TestCase):
    """One line per row below each table (070_evaluate.md, *Reading each row*), on the case above, and on rows built
    to meet each rule and cause of that section, with the near misses of the threshold for too few."""
    END = " (rules: `070_evaluate/070_evaluate.md`, *Reading each row*)"
    SCHEMA = "the current schema (by default step 040's induced schema plus the schema additions)"
    TABLE = "the translation table (`annotations/component_class_mapping.csv`)"
    UNPAIRED = ("step 060's extraction stated a fact the ground truth doesn't have (wrong, or right but not annotated), "
                "stated one the ground truth has with {} or in words too different to pair even at the partial level, "
                "restated a fact already in a pair, or repeated an occurrence (multiplicity > 1); or a row of the "
                "translation table translates its predicate or an entity class to the wrong component class of the "
                "ground truth schema, or with the wrong swap_subject_and_object; among others, the counts don't tell "
                "which (each occurrence, with its pair if any: `per_record.md`; every cause: "
                "`070_evaluate/metrics/precision.md`, *When an occurrence counts as not correct*).")
    #: What the counts never rule out for a ground truth triple with no pair (causes (e) and (h)).
    NOT_RULED_OUT = ("step 060 removed the extracted triple for a check, a row of the translation table translates its "
                     "predicate to the wrong one or with the wrong swap_subject_and_object, a near-repeat in the "
                     "ground truth, a \"not the same fact\" verdict, or its occurrence taken by a wrong pair; the "
                     "counts don't tell which (every cause: `070_evaluate/metrics/recall.md`, *When a ground truth "
                     "triple counts as not found*)")

    def setUp(self):
        self.r = dict(compared(), position=3, title="T")
        self.tables = stats.per_component_class([self.r])

    def reading(self, table, name):
        row = next(x for x in self.tables[table] if x["component_class"] == name)
        return readings.component_class_reading(row, table)

    @staticmethod
    def row(O, G, k, Pe, Pp, Sp, reach=True, many=0, name="ABOARD"):
        """A row of a table per predicate or per entity class, from its counts."""
        return {"component_class": name, "occurrences": O, "ground_truth_triples": G, "within_strict_reach": k,
                "within_reach": reach, "occurrences_multiplicity_above_1": many,
                "exact": {"pairs": Pe}, "partial": {"pairs": Pp, "strict_pairs": Sp}}

    @staticmethod
    def rec(O, G, W, Ws, Pe, Se, many=0):
        """A row of the table per record, from its counts (a made-up record, not a real one)."""
        return {"id": "hypothetical", "position": 9, "occurrences": O, "ground_truth_triples": G, "within_reach": W,
                "within_strict_reach": Ws, "counted_against": O + G - 2 * Pe, "occurrences_multiplicity_above_1": many,
                "exact": {"pairs": Pe, "strict_pairs": Se, "recall": Pe / G if G else None,
                          "precision": Pe / O if O else None}}

    def test_component_class_rows(self):
        self.assertEqual(self.reading("predicate", "ABOARD"),
                         "ABOARD (predicate, ground truth schema): 3 occurrences and 2 ground truth triples (2 within "
                         "strict reach); 2 pairs that count for it at the partial level (2 exact, 0 partial), 1 of them "
                         "strict. In 1 pair, the two triples differ in subject class or object class: every one of this "
                         "row's ground truth triples is within strict reach, so either step 060's extraction gave a "
                         "wrong subject class or object class, or a row of the translation table translates one to the "
                         "wrong one. 1 occurrence has no pair that counts for it (each against its precision): "
                         + self.UNPAIRED.format("another predicate") + self.END)
        # e1 (AIRS, Dataset) pairs with g1 (AIRS, Instrument), but not for Instrument as subject class
        self.assertEqual(self.reading("subject class", "Instrument"),
                         "Instrument (subject class, ground truth schema): 2 occurrences and 2 ground truth triples (2 "
                         "within strict reach); 1 pair that counts for it at the partial level (1 exact, 0 partial), 1 "
                         "of them strict. 1 ground truth triple has no pair that counts for it (each against its "
                         "recall): within strict reach; among the causes, step 060's extraction left the fact out, "
                         "gave it another predicate or another subject class, or wrote a subject instance or object "
                         "instance too differently to pair even at the partial level (`070_evaluate/metrics/pairs.md`, "
                         "Definition), or " + self.NOT_RULED_OUT + ". 1 occurrence has no pair that counts for it (each against its precision): "
                         + self.UNPAIRED.format("another predicate or another subject class") + self.END)
        # 1 occurrence + 1 ground truth triple in a strict partial pair: nothing counts against it at the partial
        # level, so not too few; the pair is partial, not exact (cause (g))
        self.assertEqual(self.reading("predicate", "ACQUIRED_BY_INSTRUMENT"),
                         "ACQUIRED_BY_INSTRUMENT (predicate, ground truth schema): 1 occurrence and 1 ground truth "
                         "triple (1 within strict reach); 1 pair that counts for it at the partial level (0 exact, 1 "
                         "partial), 1 of them strict. 1 of these pairs is partial, not exact: in each, the subject "
                         "instance or object instance of one triple is inside the other's as whole words, not the same "
                         "(`070_evaluate/metrics/pairs.md`, Definition), so at the exact level its two triples count "
                         "against this row (column *Counted against it (exact)*): step 060's extraction wrote the "
                         "instance more or less fully than the ground truth, or the pair is a wrong one "
                         "(`070_evaluate/metrics/pairs.md`, *When a pair isn't the same fact*)." + self.END)
        self.assertEqual(self.reading("object class", f"Gadget{NONE}"),
                         f"Gadget{NONE}: its row of {self.TABLE} says (none), so its 1 occurrence can't be in a pair "
                         f"(1 of them untranslatable, left out of its precision: precision has no value): either {self.SCHEMA} has an object class the ground truth schema lacks, or "
                         f"that row should name one of the ground truth schema's." + self.END)
        self.assertEqual(readings.component_class_reading(self.row(1, 2, 2, 1, 1, 1), "predicate"),
                         "ABOARD (predicate, ground truth schema): 1 occurrence and 2 ground truth triples (2 within "
                         "strict reach); 1 pair that counts for it at the partial level (1 exact, 0 partial), 1 of them "
                         "strict. 1 ground truth triple has no pair that counts for it (each against its recall): "
                         "within strict reach; among the causes, step 060's extraction left the fact out, gave it "
                         "another predicate, or wrote a subject instance or object instance too differently to pair "
                         "even at the partial level (`070_evaluate/metrics/pairs.md`, Definition), or "
                         + self.NOT_RULED_OUT + "." + self.END)
        self.assertEqual(readings.component_class_reading(self.row(2, 2, 2, 2, 2, 2), "predicate"),
                         "ABOARD (predicate, ground truth schema): 2 occurrences and 2 ground truth triples (2 within "
                         "strict reach); 2 pairs that count for it at the partial level (2 exact, 0 partial), 2 of them "
                         "strict. Nothing counts against it at the partial level: every occurrence and ground truth "
                         "triple is in a strict pair that counts for it." + self.END)

    def test_not_all_within_strict_reach(self):
        """With a ground truth triple out of strict reach, causes (d) and (e) name no one step."""
        line = readings.component_class_reading(self.row(2, 3, 1, 2, 2, 1), "object class")
        self.assertIn(": 2 occurrences and 3 ground truth triples (1 within strict reach); 2 pairs that count for it "
                      "at the partial level (2 exact, 0 partial), 1 of them strict. 2 of its ground truth triples are "
                      "out of strict reach (no checked row translates to their predicate, subject class, or object "
                      f"class), so they can't be in a strict pair: either {self.SCHEMA} has no predicate or entity "
                      f"class with that meaning, or {self.TABLE} has no checked row translating one of the current "
                      "schema's to it. In 1 pair, the two triples differ in subject class: the ground truth triple is "
                      "out of strict reach (above), step 060's extraction gave a wrong subject class, or a row of the "
                      "translation table translates one to the wrong one; the counts don't tell which. 1 ground truth "
                      "triple has no pair that counts for it (each against its recall): either some are out of strict "
                      "reach (above), or, among the other causes, step 060's extraction left the fact out, gave it "
                      "another predicate or another object class, or wrote", line)
        self.assertIn(self.NOT_RULED_OUT, line)

    def test_too_few(self):
        """At most TOO_FEW triples with something against it: no cause. One more triple, or nothing against it: read."""
        self.assertEqual(readings.TOO_FEW, 2)
        self.assertEqual(readings.component_class_reading(self.row(1, 1, 1, 0, 0, 0), "predicate"),
                         "ABOARD (predicate, ground truth schema): 1 occurrence and 1 ground truth triple (1 within "
                         "strict reach); 0 pairs that count for it at the partial level (0 exact, 0 partial), 0 of them "
                         "strict: only 2 triples (1 occurrence + 1 ground truth triple), and 070 names a cause only for "
                         "more than 2 (a rule of thumb, with no source): too few to say which step caused the 2 of them "
                         "with no pair that counts for it at the partial level." + self.END)
        self.assertIn("too few to say which step caused its 1 pair that isn't strict.",
                      readings.component_class_reading(self.row(1, 1, 1, 1, 1, 0), "predicate"))
        self.assertIn("too few", readings.component_class_reading(self.row(0, 1, 1, 0, 0, 0), "predicate"))
        self.assertNotIn("too few", readings.component_class_reading(self.row(2, 1, 1, 0, 0, 0), "predicate"))
        self.assertNotIn("too few", readings.component_class_reading(self.row(1, 1, 1, 1, 1, 1), "predicate"))
        self.assertIn("too few to say which step caused the 2 of them with no exact pair.",
                      readings.record_reading(self.rec(1, 1, 1, 1, 0, 0)))
        self.assertNotIn("too few", readings.record_reading(self.rec(2, 1, 1, 1, 0, 0)))
        self.assertEqual(readings.record_reading(self.rec(0, 0, 0, 0, 0, 0)),
                         "Record hypothet (pool position 9): no occurrences and no ground truth triples: nothing to "
                         "compare." + self.END)

    def test_out_of_reach(self):
        t = translation(CLASSES, PREDICATES, reachable_entity=["Instrument", "Spacecraft"], reachable_predicates=["ABOARD"])
        tables = stats.per_component_class([pairing.compare_record(record(GT, EXTRACTED[:1]), t)])
        row = next(x for x in tables["predicate"] if x["component_class"] == "ACQUIRED_BY_INSTRUMENT")
        self.assertEqual(readings.component_class_reading(row, "predicate"),
                         f"ACQUIRED_BY_INSTRUMENT (predicate, ground truth schema): out of reach: no checked row of "
                         f"{self.TABLE} translates a predicate of the current schema to it, so none of its 1 ground "
                         f"truth triple can be in a pair (recall 0%): either {self.SCHEMA} has no predicate with that "
                         f"meaning, or {self.TABLE} has no checked row translating one of the current schema's to it."
                         + self.END)

    def test_record_rows(self):
        (row,) = stats.per_record([self.r])
        self.assertEqual(readings.record_reading(row),
                         "Record r1 (pool position 3): 5 occurrences and 3 ground truth triples (3 within reach, 3 "
                         "within strict reach); 2 exact pairs, 1 of them strict; exact recall 67%, exact precision 50% "
                         "(1 untranslatable extracted triple, left out of its precision: section *Schema fit* of the report). "
                         "In 1 exact pair, the two triples differ in subject class or object class: every ground truth "
                         "triple of the record is within strict reach, so either step 060's extraction gave a wrong "
                         "entity class, or a row of the translation table translates one to the wrong one. 2 of its "
                         "occurrences have no exact pair, but only 1 of its ground truth triples within reach lacks one, "
                         "so at least 1 of its occurrences state no fact among those ground truth triples: step 060's "
                         "extraction stated facts the ground truth doesn't have (wrong, or right but not annotated), "
                         "stated with a predicate within reach a fact the ground truth has with one out of reach, "
                         "restated a fact already in an exact pair, or repeated an occurrence (multiplicity > 1), among "
                         "others; the counts don't tell which (every cause: `070_evaluate/metrics/precision.md`, *When "
                         "an occurrence counts as not correct*)." + self.END)
        self.assertEqual(readings.record_reading(self.rec(10, 40, 40, 40, 6, 6)),           # the guide's example
                         "Record hypothet (pool position 9): 10 occurrences and 40 ground truth triples (40 within "
                         "reach, 40 within strict reach); 6 exact pairs, 6 of them strict; exact recall 15%, exact "
                         "precision 60%. 34 of its ground truth triples within reach have no exact pair, but only 4 of "
                         "its occurrences lack one, so at least 30 of the record's facts within reach have no "
                         "occurrence left that could pair with them: among the causes, step 060's extraction left them "
                         "out, or " + self.NOT_RULED_OUT + "." + self.END)
        self.assertEqual(readings.record_reading(self.rec(3, 4, 3, 2, 1, 0)),
                         "Record hypothet (pool position 9): 3 occurrences and 4 ground truth triples (3 within reach, "
                         "2 within strict reach); 1 exact pair, 0 of them strict; exact recall 25%, exact precision 33%. "
                         f"1 of its ground truth triples is out of reach (no checked row translates a predicate of the "
                         f"current schema to theirs), so it can't be in any pair: either {self.SCHEMA} has no "
                         f"predicate with that meaning, or {self.TABLE} has no checked row translating one of the "
                         f"current schema's to it. In 1 exact pair, the two triples differ in subject class or object "
                         f"class: the ground truth triple is out of strict reach, step 060's extraction gave a wrong "
                         f"entity class, or a row of the translation table translates one to the wrong one; the counts "
                         f"don't tell which. 2 of its ground truth triples within reach and 2 of its occurrences have no "
                         f"exact pair: the counts don't tell whether step 060's extraction left facts out, stated them "
                         f"with another predicate or in other words (column *Pairs (partial)*: how many pair at the "
                         f"partial level), or stated facts the ground truth doesn't have." + self.END)
        self.assertIn("exact precision no value (0 to divide by)", readings.record_reading(self.rec(0, 3, 3, 3, 0, 0)))
        self.assertIn("Nothing counts against it at the exact level: every occurrence and ground truth triple is in a "
                      "strict exact pair.", readings.record_reading(self.rec(3, 3, 3, 3, 3, 3)))

    def test_multiplicity_mentioned(self):
        ex = [EXTRACTED[0], triple("the MODIS", "Instrument", "ABOARD", "Aqua", "Spacecraft"), EXTRACTED[2]]
        (row,) = stats.per_record([dict(compared(GT[:1], ex), position=0, title="")])
        self.assertTrue(readings.record_reading(row).endswith(
            " 2 of its occurrences have multiplicity > 1: two or more extracted triples of their record translate to "
            "the same translated extracted triple, and at most one of those copies can pair with a given ground truth "
            "triple (`070_evaluate/metrics/pairs.md`, Example, *A multiset of translated extracted triples*)." + self.END))

    def test_below_each_table(self):
        intro = ("Reading each row: one line per row above, in the same order. Each line gives the counts it rests on "
                 "and, for each thing that counts against the row, the step that can cause it (step 040's schema, the "
                 "translation table, step 060's extraction, or the ground truth), among those the counts leave "
                 "possible (the counts never rule out every other: each full list is in "
                 "`070_evaluate/metrics/recall.md` and `precision.md`). Every cause a line can name, the rule (numbers and conditions) that names it, "
                 "and the threshold for too few: `070_evaluate/070_evaluate.md`, *Reading each row*.")
        text = "\n".join(moves._per_component_class_lines({"records": 1}, self.tables))
        self.assertEqual(text.count(intro), 3)
        self.assertIn("\n1. ACQUIRED_BY_INSTRUMENT (predicate, ground truth schema): 1 occurrence", text)
        self.assertIn("\n2. ABOARD (predicate, ground truth schema): 3 occurrences", text)
        lines = [x for x in text.split("\n") if re.match(r"\d+\. ", x)]
        self.assertTrue(lines and all(x.endswith(self.END) for x in lines))
        text = "\n".join(moves._per_record_lines(stats.per_record([self.r])))
        self.assertEqual(text.count(intro), 1)
        self.assertIn("\n1. Record r1 (pool position 3): 5 occurrences", text)
        self.assertIn("Reading: Record r1 (pool position 3): 5 occurrences", moves._per_record([self.r], 0))

    def test_guide_states_the_rules(self):
        """The guide's section gives the threshold the code uses, and the causes (a) to (h)."""
        guide = (ROOT / "070_evaluate" / "070_evaluate.md").read_text(encoding="utf-8")
        section = guide[guide.index("### Reading each row"):guide.index("### Twins")]
        self.assertIn(f"*Too few*: O + G is at most {readings.TOO_FEW}", section)
        self.assertIn("a rule of thumb, with no source", section)
        for cause in "abcdefgh":
            self.assertIn(f"| ({cause}) |", section)


class PooledNotAveraged(unittest.TestCase):
    """070_evaluate/metrics.md, *Pooled, not averaged*: record A has 2 ground truth triples and extraction found 2,
    record B has 48 and extraction found 12."""
    def test_part_pools_and_differs_from_the_mean_of_the_records(self):
        recs = [counts_record(2, 2, 2, 2, id="A", position=0), counts_record(12, 48, 12, 12, id="B", position=1)]
        pooled = stats.numbers(recs)["exact"]["recall"]
        own = [x["exact"]["recall"] for x in stats.per_record(recs)]
        self.assertAlmostEqual(pooled, 14 / 50)
        self.assertEqual(sorted(own), [0.25, 1.0])
        self.assertAlmostEqual(sum(own) / len(own), 0.625)
        self.assertNotAlmostEqual(pooled, sum(own) / len(own))


class RemovedBy060(unittest.TestCase):
    """What 060's checks removed from the evaluated records, per reason as 060 wrote it."""
    RECORDS = [{"removed": {"source_text": 2, "duplicate": 1}},
               {"removed": {"source_text": 1, "component_class_not_in_schema source_text": 1}},
               {"removed": {}}]

    def test_per_reason(self):
        self.assertEqual(stats.removed_by_reason(self.RECORDS), [
            {"reason": "source_text", "removed": 3, "records": 2},
            {"reason": "component_class_not_in_schema source_text", "removed": 1, "records": 1},
            {"reason": "duplicate", "removed": 1, "records": 1}])

    def test_report_table(self):
        text = "\n".join(moves._removed_lines(3, stats.removed_by_reason(self.RECORDS)))
        self.assertIn("| `source_text` | its source text is missing, or isn't in the record's text | 3 | 2 |", text)
        self.assertIn("| `component_class_not_in_schema source_text` | an entity class or predicate the current schema "
                      "doesn't have and its source text is missing, or isn't in the record's text | 1 | 1 |", text)
        self.assertIn("| all | | 5 | |", text)
        self.assertIn("| Reason (as 060 wrote it) | What it means | Items removed | Records with any item removed for it |",
                      text)
        self.assertIn("| `nonsense` | a reason 070 doesn't know: not one of those in `docs/terminology.md`, *extracted triple* "
                      "| 1 | 1 |", "\n".join(moves._removed_lines(1, [{"reason": "nonsense", "removed": 1, "records": 1}])))
        self.assertIn("None: 060 removed nothing from these records.", "\n".join(moves._removed_lines(1, [])))


if __name__ == "__main__":
    unittest.main()
