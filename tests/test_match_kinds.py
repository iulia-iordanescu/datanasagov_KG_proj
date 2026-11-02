"""The translation table's match column (docs/terminology.md, *match*): its values and their problems
(common/common_helpers/component_class_mapping.py), step 070's warnings about rows (component_classes.py), the counts
by match kind, the recall upper bound split, the pin misfits (pairing.py), the suggestions for broader and overlap rows,
and the report's lines, with the near-misses. No metric changes."""
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from support import use_step

use_step("070_evaluate")
import component_classes                         # noqa: E402
import moves                                     # noqa: E402
import pairing                                   # noqa: E402
import readings                                  # noqa: E402
import stats                                     # noqa: E402
from common import component_class_mapping as m  # noqa: E402
from common import llm                           # noqa: E402
from common.files import append_csv, write_csv   # noqa: E402
from common.stop import Stop                     # noqa: E402
from test_evaluate_pairing import record         # noqa: E402

GTS = ("ENTITY CLASSES\n--------------\n"
       "Dataset           a set of observations\n"
       "Mission           a named spaceflight effort\n"
       "Spacecraft        a vehicle in space\n"
       "Time              a calendar time\n"
       "Region            an area of the Earth\n\n"
       "PREDICATES\n----------\n"
       "FROM_MISSION      comes from this mission\n"
       "                  only: any -> Mission\n"
       "HAS_TIME_SPAN     covers this time\n"
       "                  only: any -> Time\n"
       "HAS_SPATIAL_COVERAGE  covers this area\n"
       "                  only: any -> Region\n"
       "ALSO_KNOWN_AS     is also called\n")
GTT_DEF = {"Dataset": "a set of observations", "Mission": "a named spaceflight effort", "Spacecraft": "a vehicle in space",
           "Time": "a calendar time", "Region": "an area of the Earth", "FROM_MISSION": "comes from this mission",
           "HAS_TIME_SPAN": "covers this time", "HAS_SPATIAL_COVERAGE": "covers this area",
           "ALSO_KNOWN_AS": "is also called"}


def row(kind, crt, gtt, match="", checked="yes", swap="no", if_subject="", if_object="", line=0):
    return {"kind": kind, "component_class_from_past_or_crt_schema": crt, "component_class_in_gtt": gtt,
            "swap_subject_and_object": swap, "match": match, "checked": checked,
            "definition_from_past_or_crt_schema": "d", "definition_in_gtt": GTT_DEF.get(gtt, ""),
            "if_subject_class": if_subject, "if_object_class": if_object, "_line": line}


# The current schema's rows: Dataset and Mission the same; Craft narrower than Spacecraft; Period broader than Time;
# Place (none). COVERS broader than HAS_TIME_SPAN, with no conditional row; SOURCED_FROM (none), and if its object is a
# Mission, FROM_MISSION; FROM_MISSION checked before the match column (no match value); NAMED swapped onto the
# symmetric ALSO_KNOWN_AS.
ROWS = [row("entity class", "Dataset", "Dataset", "same", "same component class"),
        row("entity class", "Mission", "Mission", "same", "same component class"),
        row("entity class", "Craft", "Spacecraft", "narrower"),
        row("entity class", "Period", "Time", "broader"),
        row("entity class", "Place", "(none)"),
        row("predicate", "COVERS", "HAS_TIME_SPAN", "broader"),
        row("predicate", "SOURCED_FROM", "(none)"),
        row("predicate", "SOURCED_FROM", "FROM_MISSION", "same", if_object="Mission"),
        row("predicate", "FROM_MISSION", "FROM_MISSION", "", "same component class"),
        row("predicate", "NAMED", "ALSO_KNOWN_AS", "narrower", swap="yes")]
SCHEMA_USED = {"entity_classes": [{"component_class": c, "definition": "d"}
                                  for c in ("Dataset", "Mission", "Craft", "Period", "Place")],
               "predicates": [{"component_class": p, "definition": "d"}
                              for p in ("COVERS", "SOURCED_FROM", "FROM_MISSION", "NAMED")]}


def triple(s, sc, p, o, oc):
    return {"subject": s, "subject_class": sc, "predicate": p, "object": o, "object_class": oc}


def with_lines(rows):
    return [dict(r, _line=i + 2) for i, r in enumerate(rows)]


class Values(unittest.TestCase):

    def test_value_problems(self):
        rows = with_lines([row("entity class", "Craft", "Spacecraft", "close"),          # not a match value
                           row("entity class", "Place", "(none)", "same"),               # a match on (none)
                           row("entity class", "Spot", "(none)", ""),                    # near miss: (none), empty
                           row("entity class", "Probe", "Spacecraft", "overlap")])       # near miss: fine
        self.assertEqual(m.value_problems(rows), ["line 2 (Craft): match 'close'", "line 3 (Place): match 'same'"])

    def test_read_normalises_and_old_table_reads_empty(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            write_csv(tmp / "m.csv", m.COLUMNS, [row("entity class", "Craft", "Spacecraft", " Broader ")])
            self.assertEqual(m.read_mapping(tmp / "m.csv")[0]["match"], "broader")
            old = [c for c in m.COLUMNS if c != "match"]
            write_csv(tmp / "m.csv", old, [row("entity class", "Craft", "Spacecraft", "narrower")])
            rows = m.read_mapping(tmp / "m.csv")
            self.assertEqual(rows[0]["match"], "")
            self.assertEqual([r["component_class_from_past_or_crt_schema"] for r in m.missing_match(rows)], ["Craft"])
            # a row a step appends to such a file lands under the file's own columns (match left out)
            append_csv(tmp / "m.csv", m.COLUMNS, [row("predicate", "COVERS", "HAS_TIME_SPAN", "broader", "no")])
            added = m.read_mapping(tmp / "m.csv")[1]
            self.assertEqual((added["component_class_in_gtt"], added["checked"], added["match"]), ("HAS_TIME_SPAN", "no", ""))
        finally:
            shutil.rmtree(tmp)

    def test_missing_match(self):
        self.assertTrue(m.is_missing_match(row("entity class", "Craft", "Spacecraft", "")))
        self.assertTrue(m.is_missing_match(row("entity class", "Craft", "Spacecraft", "", "same component class")))
        self.assertFalse(m.is_missing_match(row("entity class", "Craft", "Spacecraft", "", "no")))     # not checked
        self.assertFalse(m.is_missing_match(row("entity class", "Place", "(none)", "")))              # (none)
        self.assertFalse(m.is_missing_match(row("entity class", "Craft", "Spacecraft", "narrower")))
        gtt = m.gtt_definitions({"entity_classes": {"Spacecraft": "a vehicle in space"}, "predicates": {}})
        self.assertIn(m.NO_MATCH, m.row_states(row("entity class", "Craft", "Spacecraft", ""), None, gtt))

    def test_inexact_alone_and_symmetric_swaps(self):
        rows = with_lines(ROWS + [row("predicate", "USES", "HAS_TIME_SPAN", "overlap"),
                                  row("predicate", "TAKES", "HAS_TIME_SPAN", "broader"),             # near miss:
                                  row("predicate", "TAKES", "FROM_MISSION", "same", if_object="Mission"),   # conditioned
                                  row("predicate", "NAMES", "ALSO_KNOWN_AS", "same")])               # near miss: no swap
        self.assertEqual([r["component_class_from_past_or_crt_schema"] for r in m.inexact_alone(rows)], ["COVERS", "USES"])
        self.assertEqual([r["component_class_from_past_or_crt_schema"] for r in m.symmetric_swaps(rows)], ["NAMED"])

    def test_suggested_widened(self):
        gtt = m.gtt_definitions({"entity_classes": {"Time": "a calendar time"}, "predicates": {}})
        for match, suggested in (("broader", True), ("overlap", True), ("narrower", False), ("same", False)):
            with self.subTest(match=match):
                states = m.row_states(row("entity class", "Period", "Time", match), None, gtt, suggested="Region")
                self.assertEqual(m.SUGGESTED in states, suggested)


class Stage(unittest.TestCase):
    """translate_component_classes on ROWS: its warnings, the matches it keeps, and the counts they give."""

    REPLY = {"suggestions": [
        {"kind": "predicate", "schema": "COVERS", "ground_truth": "HAS_SPATIAL_COVERAGE"},     # kept, beside its target
        {"kind": "predicate", "schema": "COVERS", "ground_truth": "FROM_MISSION"},             # not offered: dropped
        {"kind": "entity class", "schema": "Dataset", "ground_truth": "Region"},               # not asked: dropped
        {"kind": "entity class", "schema": "Place", "ground_truth": "Region"}]}                # a (none) row: kept

    def run_stage(self, rows=ROWS, schema_used=SCHEMA_USED, suggest=True):
        tmp = Path(tempfile.mkdtemp())
        prompts = []
        try:
            write_csv(tmp / "map.csv", m.COLUMNS, rows)
            (tmp / "gts.txt").write_text(GTS, encoding="utf-8")
            paid = SimpleNamespace(made=0, start=lambda plan: None, test_calls=0)
            paid.made_call = lambda: setattr(paid, "made", paid.made + 1)
            paid.outcome = lambda where, prompt, error=None, watched=True: None
            calls = SimpleNamespace(paid=paid, cache_dir=tmp / "cache")

            def answer(prompt, read_timeout=180, check=None):
                prompts.append(prompt)
                return self.REPLY
            with mock.patch.object(llm, "call_llm_json", answer):
                t = component_classes.translate_component_classes(
                    {"component_class_mapping": str(tmp / "map.csv"), "ground_truth_schema": str(tmp / "gts.txt")},
                    type("E", (), {"schema_used": schema_used})(), calls, suggest=suggest)
            return t, prompts, tmp / "map.csv"
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_warnings(self):
        t, _, _ = self.run_stage()
        notes = " | ".join(t.notes)
        self.assertEqual(len(t.notes), 3, t.notes)
        self.assertIn("1 checked row(s)", t.notes[0])
        self.assertIn("FROM_MISSION (current schema) --> FROM_MISSION (ground truth schema)", t.notes[0])
        self.assertIn("COVERS (current schema) --> HAS_TIME_SPAN (ground truth schema) (broader)", t.notes[1])
        self.assertNotIn("SOURCED_FROM", t.notes[1])                       # (none), and conditioned
        self.assertNotIn("Period", notes)                                  # an entity class's row is never warned about
        self.assertIn("NAMED (current schema) --> ALSO_KNOWN_AS", t.notes[2])
        # none of it stops, and a table with nothing to warn about has no note (near miss)
        quiet = [r for r in ROWS if r["component_class_from_past_or_crt_schema"] not in ("COVERS", "NAMED")]
        quiet = [dict(r, match="same") if r["component_class_from_past_or_crt_schema"] == "FROM_MISSION" else r
                 for r in quiet]
        used = dict(SCHEMA_USED, predicates=[p for p in SCHEMA_USED["predicates"]
                                             if p["component_class"] not in ("COVERS", "NAMED")])
        self.assertEqual(self.run_stage(quiet, used)[0].notes, [])

    def test_suggestions_for_broader_rows(self):
        t, prompts, _ = self.run_stage()
        self.assertEqual(len(prompts), 1)
        inexact = json.loads(prompts[0].split("\nINEXACT\n", 1)[1])
        self.assertEqual({(x["kind"], x["component_class"], x["translated_to"]) for x in inexact},
                         {("entity class", "Period", "Time"), ("predicate", "COVERS", "HAS_TIME_SPAN")})
        self.assertNotIn("Craft", prompts[0].split("\nINEXACT\n", 1)[1])      # narrower: not asked
        self.assertEqual(t.suggested, [
            {"kind": "predicate", "component_class_from_past_or_crt_schema": "COVERS",
             "component_class_in_gtt": "HAS_SPATIAL_COVERAGE", "beside": "HAS_TIME_SPAN"},
            {"kind": "entity class", "component_class_from_past_or_crt_schema": "Place", "component_class_in_gtt": "Region"}])

    def test_suggest_false_asks_nothing_and_translates_the_same(self):
        """--suggest false (2026-11-02, re-scoring with no model budget): no suggestion call, the status says so, and
        every translation 070 scores with is the same as with suggestions asked (suggestions never change a row)."""
        asked, _, _ = self.run_stage()
        t, prompts, _ = self.run_stage(suggest=False)
        self.assertEqual(prompts, [])
        self.assertEqual((t.suggested, t.suggest_calls, t.suggestions), ([], 0, "not asked (--suggest false)"))
        self.assertEqual(asked.suggestions, "asked")                        # near miss: asked by default
        for f in ("entity", "predicate", "reachable", "conditional", "reach_conditional", "match", "match_conditional",
                  "reach_kind", "reach_conditional_kind", "pinned", "rows_used", "to_none", "untranslated",
                  "merged", "reversed_used", "conditional_rows_used"):
            self.assertEqual(getattr(t, f), getattr(asked, f), f)
        tmp_dir = lambda notes: [re.sub(r"tmp\w+", "tmp", n) for n in notes]          # noqa: E731  (each run's own folder)
        self.assertEqual(tmp_dir(t.notes), tmp_dir(asked.notes))
        ex = [triple("D", "Dataset", "COVERS", "2001", "Period"), triple("D", "Dataset", "SOURCED_FROM", "R", "Mission")]
        gt = [triple("D", "Dataset", "HAS_TIME_SPAN", "2001", "Time")]
        self.assertEqual(pairing.compare_record(record(gt, ex), t)["compared"],
                         pairing.compare_record(record(gt, ex), asked)["compared"])

    def test_suggest_false_stops_on_a_missing_row_before_paying(self):
        """A component class of the current schema with no row, and none of its name in the ground truth schema: with
        --suggest false 070 stops before any call, names it and both ways on, and leaves the table as it was. Near
        miss: one whose name the ground truth schema has still gets its row, free (no model)."""
        used = dict(SCHEMA_USED, entity_classes=SCHEMA_USED["entity_classes"] + [{"component_class": "Gizmo",
                                                                                 "definition": "d"}])
        tmp = Path(tempfile.mkdtemp())
        try:
            write_csv(tmp / "map.csv", m.COLUMNS, ROWS)
            (tmp / "gts.txt").write_text(GTS, encoding="utf-8")
            before = (tmp / "map.csv").read_bytes()
            inputs = {"component_class_mapping": str(tmp / "map.csv"), "ground_truth_schema": str(tmp / "gts.txt")}
            sent = []
            with mock.patch.object(llm, "call_llm_json", lambda *a, **k: sent.append(1)), self.assertRaises(Stop) as caught:
                component_classes.translate_component_classes(inputs, type("E", (), {"schema_used": used})(), None,
                                                              suggest=False)
            said = str(caught.exception)
            for words in ("1 component class(es) of the current schema have no row", "entity class Gizmo (current schema)",
                          "With --suggest false 070 calls no model", "Nothing was paid and the table wasn't changed",
                          "run `py 070_evaluate/run.py` (the model proposes those rows: up to 1 paid call(s)",
                          "then run `py 070_evaluate/run.py --suggest false` again"):
                self.assertIn(words, said)
            self.assertEqual((sent, (tmp / "map.csv").read_bytes()), ([], before))
            near = dict(SCHEMA_USED, entity_classes=SCHEMA_USED["entity_classes"] + [{"component_class": "Spacecraft",
                                                                                     "definition": "d"}])
            with self.assertRaises(Stop) as caught:
                component_classes.translate_component_classes(inputs, type("E", (), {"schema_used": near})(), None,
                                                              suggest=False)
            self.assertIn("Added 1 row(s)", str(caught.exception))
            self.assertEqual(m.read_mapping(tmp / "map.csv")[-1]["component_class_from_past_or_crt_schema"], "Spacecraft")
        finally:
            shutil.rmtree(tmp)

    def test_automatic_rows_get_same(self):
        used = dict(SCHEMA_USED, entity_classes=SCHEMA_USED["entity_classes"] + [{"component_class": "Spacecraft",
                                                                                 "definition": "d"}])
        tmp = Path(tempfile.mkdtemp())
        try:
            write_csv(tmp / "map.csv", m.COLUMNS, ROWS)
            (tmp / "gts.txt").write_text(GTS, encoding="utf-8")
            with self.assertRaises(Stop):
                component_classes.translate_component_classes(
                    {"component_class_mapping": str(tmp / "map.csv"), "ground_truth_schema": str(tmp / "gts.txt")},
                    type("E", (), {"schema_used": used})(), None)
            added = m.read_mapping(tmp / "map.csv")[-1]
            self.assertEqual((added["component_class_from_past_or_crt_schema"], added["checked"], added["match"]),
                             ("Spacecraft", "same component class", "same"))
        finally:
            shutil.rmtree(tmp)

    def compared(self):
        t, _, _ = self.run_stage()
        gt = [triple("D", "Dataset", "FROM_MISSION", "Rosetta", "Mission"),       # through the same conditional row
              triple("D", "Dataset", "FROM_MISSION", "Giotto", "Spacecraft"),     # only through the row with no match
              triple("D", "Dataset", "HAS_TIME_SPAN", "2001", "Time"),            # only through COVERS (broader)
              triple("D", "Dataset", "HAS_SPATIAL_COVERAGE", "Arctic", "Region")]  # out of reach
        ex = [triple("D", "Dataset", "COVERS", "2001", "Period"),                 # broader; pairs; fits the pin
              triple("D", "Dataset", "COVERS", "Arctic", "Place"),                # broader; extracted only; pin misfit
              triple("D", "Dataset", "SOURCED_FROM", "Rosetta", "Mission"),       # same (conditional); pairs
              triple("D", "Dataset", "SOURCED_FROM", "X", "Dataset"),             # untranslatable
              triple("D", "Dataset", "FROM_MISSION", "Y", "Craft")]               # no match value; pin misfit
        return t, pairing.compare_record(record(gt, ex), t)

    def test_counts_by_match_kind(self):
        t, rec = self.compared()
        c = rec["compared"]["counts"]
        self.assertEqual({k: c[f"occurrences_match_{k.replace(' ', '_')}"] for k in pairing.MATCH_KINDS},
                         {"same": 1, "narrower": 0, "broader": 2, "overlap": 0, "no match value": 1})
        self.assertEqual(c["untranslatable"], 1)
        self.assertEqual({k: c[f"extracted_only_match_{k.replace(' ', '_')}"] for k in pairing.MATCH_KINDS},
                         {"same": 0, "narrower": 0, "broader": 1, "overlap": 0, "no match value": 1})
        self.assertEqual(({k: c[f"entity_classes_match_{k.replace(' ', '_')}"] for k in pairing.MATCH_KINDS},
                          c["entity_classes_to_none"]),
                         ({"same": 7, "narrower": 1, "broader": 1, "overlap": 0, "no match value": 0}, 1))
        # the recall upper bound split: one of each bucket, one out of reach; the headline counts all three
        self.assertEqual([pairing.reach_bucket(g, t) for g in rec["gt"]],
                         ["same or narrower", "no match value", "only broader or overlap", None])
        self.assertEqual((c["within_reach"], c["within_reach_same_or_narrower"], c["within_reach_no_match_value"],
                          c["within_reach_only_broader_or_overlap"]), (3, 1, 1, 1))
        self.assertEqual((c["pin_checked"], c["pin_misfits"]), (4, 2))
        # the numbers: what the part sums, and no metric moved by it
        n = stats.numbers([rec])
        self.assertEqual(n["by_match"]["within_reach"],
                         {"same or narrower": 1, "no match value": 1, "only broader or overlap": 1})
        self.assertEqual(n["by_match"]["recall_upper_bound"]["only broader or overlap"], 0.25)
        self.assertEqual(n["recall_upper_bound"], 0.75)
        self.assertEqual(pairing.translation_disagreements([rec]), [
            {"predicate": "COVERS", "translated_predicate": "HAS_TIME_SPAN", "subject_class": "Dataset",
             "translated_subject_class": "Dataset", "object_class": "Place",
             "translated_object_class": "Place" + pairing.NO_TRANSLATION, "count": 1},
            {"predicate": "FROM_MISSION", "translated_predicate": "FROM_MISSION", "subject_class": "Dataset",
             "translated_subject_class": "Dataset", "object_class": "Craft", "translated_object_class": "Spacecraft",
             "count": 1}])
        # the report's lines
        lines = "\n".join(moves._match_lines(n))
        self.assertIn("same: 1; narrower: 0; broader: 2; overlap: 0; no match value: 1", lines)
        self.assertIn("broader: 1 of 2", lines)
        self.assertIn("only broader or overlap: 1 (25% of the 4)", lines)
        self.assertIn("**Pin misfits:** 2 of the 4", lines)
        table = "\n".join(moves._disagreement_lines(pairing.translation_disagreements([rec])))
        self.assertIn("| COVERS | HAS_TIME_SPAN | Dataset | Dataset | Place | (none) | 1 |", table)
        self.assertIn("None.", "\n".join(moves._disagreement_lines([])))

    def test_identity_is_same(self):
        t = component_classes.Translation(gtt={"entity class": {"Dataset": "x"}, "predicate": {"HAS_TIME_SPAN": "y"}})
        component_classes.identity(t)
        g = triple("D", "Dataset", "HAS_TIME_SPAN", "2001", "Dataset")
        self.assertEqual(pairing.reach_bucket(g, t), "same or narrower")
        self.assertEqual(pairing.match_of(g, t), "same")


class Pins(unittest.TestCase):

    PINNED = {"frommission": [("any", "mission")], "builtby": [("spacecraft", "any"), ("any", "person")]}   # keyed

    def fits(self, sc, p, oc):
        return pairing.pin_fits(triple("A", sc, p, "B", oc), self.PINNED)

    def test_pin_fits(self):
        self.assertTrue(self.fits("Dataset", "FROM_MISSION", "Mission"))
        self.assertFalse(self.fits("Dataset", "FROM_MISSION", "Spacecraft"))                     # near miss
        self.assertIsNone(self.fits("Dataset", "HAS_TIME_SPAN", "Spacecraft"))                   # not pinned
        self.assertTrue(self.fits("Spacecraft", "BUILT_BY", "Organization"))                     # the first pair
        self.assertTrue(self.fits("Mission", "BUILT_BY", "Person"))                              # the second
        self.assertFalse(self.fits("Mission", "BUILT_BY", "Organization"))                       # neither
        marked = "Mission" + pairing.NO_TRANSLATION
        self.assertFalse(self.fits("Dataset", "FROM_MISSION", marked))                           # (none): no named one
        self.assertTrue(self.fits("Spacecraft", "BUILT_BY", marked))                              # "any" fits it
        self.assertIsNone(self.fits("Dataset", "FROM_MISSION" + pairing.NO_TRANSLATION, "Mission"))   # untranslatable

    def test_read_from_the_schema(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            (tmp / "gts.txt").write_text(GTS, encoding="utf-8")
            self.assertEqual(component_classes.gtt_pins(tmp / "gts.txt"),
                             {"frommission": [("any", "mission")], "hastimespan": [("any", "time")],
                              "hasspatialcoverage": [("any", "region")]})          # component_class_key, "any" kept
        finally:
            shutil.rmtree(tmp)


class Readings(unittest.TestCase):

    def test_merged_predicates_listed(self):
        t, rec = Stage().compared()
        t.merged = {"entity class": {}, "predicate": {"HAS_PURPOSE": ["HAS_OBJECTIVE", "USED_TO_STUDY"]}}
        rec.update(position=1, title="")
        n = stats.with_margins([rec])
        evaluated = SimpleNamespace(extraction_made={}, schema_used={})
        text = "\n".join(readings.readings("tuning", n, [rec], evaluated, t, None, {}))
        self.assertIn("Can't see mix-ups between predicates of the current schema that translate to the same ground "
                      "truth predicate (such a mix-up still pairs): HAS_OBJECTIVE, USED_TO_STUDY (current schema) --> "
                      "HAS_PURPOSE (ground truth schema).", text)
        self.assertIn("1 of the occurrences left extracted only went through a predicate's row marked broader", text)
        self.assertIn("Split by the best match among the rows that reach them", text)
        t.merged = {"entity class": {}, "predicate": {}}                                      # near miss: none
        self.assertNotIn("between predicates", "\n".join(readings.readings("tuning", n, [rec], evaluated, t, None, {})))


if __name__ == "__main__":
    unittest.main()
