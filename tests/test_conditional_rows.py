"""Conditional rows of the translation table (docs/terminology.md, *conditional row*): the table's helpers
(common/common_helpers/component_class_mapping.py), step 070's translation stage (component_classes.py), and
pairing's translation and reach (pairing.py), with the near-misses."""
import shutil
import tempfile
import unittest
from pathlib import Path

from support import use_step

use_step("070_evaluate")
import component_classes                         # noqa: E402
import pairing                                   # noqa: E402
from common import component_class_mapping as m  # noqa: E402
from common.files import write_csv               # noqa: E402
from common.stop import Stop                     # noqa: E402

GTS = ("ENTITY CLASSES\n--------------\n"
       "Dataset           a set of observations\n"
       "Mission           a named spaceflight effort\n"
       "Spacecraft        a vehicle in space\n\n"
       "PREDICATES\n----------\n"
       "FROM_MISSION      comes from this mission\n"
       "FROM_SPACECRAFT   comes from this spacecraft\n")
ENTITY_DEF = {"Dataset": "a set of observations", "Mission": "a named spaceflight effort", "Spacecraft": "a vehicle in space"}
GTT_PRED_DEF = {"FROM_MISSION": "comes from this mission", "FROM_SPACECRAFT": "comes from this spacecraft", "(none)": ""}


def row(kind, crt, gtt, checked="yes", swap="no", if_subject="", if_object="", line=0):
    gtt_def = ENTITY_DEF.get(gtt, "") if kind == "entity class" else GTT_PRED_DEF.get(gtt, "")
    return {"kind": kind, "component_class_from_past_or_crt_schema": crt, "component_class_in_gtt": gtt,
            "swap_subject_and_object": swap, "checked": checked, "definition_from_past_or_crt_schema": "d",
            "definition_in_gtt": gtt_def, "if_subject_class": if_subject, "if_object_class": if_object, "_line": line}


ENTITY_ROWS = [row("entity class", c, c, "same component class") for c in ("Dataset", "Mission", "Spacecraft")]
SOURCED = [row("predicate", "SOURCED_FROM", "(none)"),
           row("predicate", "SOURCED_FROM", "FROM_MISSION", if_object="Mission"),
           row("predicate", "SOURCED_FROM", "FROM_SPACECRAFT", if_object="Spacecraft")]


def triple(s, sc, p, o, oc):
    return {"subject": s, "subject_class": sc, "predicate": p, "object": o, "object_class": oc}


class Helpers(unittest.TestCase):

    def test_rule_for_most_conditions_wins(self):
        rows = SOURCED + [row("predicate", "SOURCED_FROM", "FROM_MISSION", if_subject="Dataset", if_object="Spacecraft")]
        pick = lambda s, o: m.rule_for(rows, s, o)["component_class_in_gtt"]   # noqa: E731
        self.assertEqual(pick("Dataset", "Mission"), "FROM_MISSION")
        self.assertEqual(pick("Dataset", "spacecraft"), "FROM_MISSION")          # both conditions beat one; case aside
        self.assertEqual(pick("Instrument", "Spacecraft"), "FROM_SPACECRAFT")
        self.assertEqual(pick("Dataset", "Instrument"), "(none)")                # near-miss: falls back to unconditional
        self.assertIsNone(m.rule_for(SOURCED[1:], "Dataset", "Instrument"))

    def test_repeats_count_the_condition(self):
        rows = [dict(r, _line=i + 2) for i, r in enumerate(SOURCED)]
        self.assertEqual(m.repeats(rows), [])
        rows.append(dict(SOURCED[1], _line=9))
        self.assertEqual(m.repeats(rows), [{"kind": "predicate", "component_class": "SOURCED_FROM", "lines": [3, 9]}])

    def test_conflict_only_for_one_condition_each(self):
        a = row("predicate", "USES", "FROM_MISSION", if_subject="Dataset", line=2)
        b = row("predicate", "USES", "FROM_SPACECRAFT", if_object="Spacecraft", line=3)
        self.assertEqual(m.conflicts([a, b]), [{"component_class": "USES", "lines": [2, 3]}])
        settle = row("predicate", "USES", "FROM_SPACECRAFT", if_subject="Dataset", if_object="Spacecraft", line=4)
        self.assertEqual(m.conflicts([a, b, settle]), [])                         # a row with both conditions settles it
        self.assertEqual(m.conflicts([a, dict(b, component_class_in_gtt="FROM_MISSION")]), [])   # same translation
        self.assertEqual(m.conflicts([a, dict(b, if_object_class="", if_subject_class="Mission")]), [])  # can't both hold

    def test_entity_class_row_takes_no_condition(self):
        bad = m.value_problems([row("entity class", "Craft", "Spacecraft", if_subject="Dataset", line=5)])
        self.assertEqual(bad, ["line 5 (Craft): if_subject_class 'Dataset'"])

    def test_condition_text(self):
        self.assertEqual(m.condition_text(SOURCED[1]), "if its object of entity class Mission")
        self.assertEqual(m.condition_text(SOURCED[0]), "")


class Stage(unittest.TestCase):
    """translate_component_classes reads conditional rows, checks them like any row, and stops on a conflict."""

    def run_stage(self, rows, predicates=("SOURCED_FROM",)):
        tmp = Path(tempfile.mkdtemp())
        try:
            write_csv(tmp / "map.csv", m.COLUMNS, rows)
            (tmp / "gts.txt").write_text(GTS, encoding="utf-8")
            evaluated = type("E", (), {"schema_used": {
                "entity_classes": [{"component_class": c, "definition": "d"} for c in ("Dataset", "Mission", "Spacecraft")],
                "predicates": [{"component_class": p, "definition": "d"} for p in predicates]}})()
            t = component_classes.translate_component_classes(
                {"component_class_mapping": str(tmp / "map.csv"), "ground_truth_schema": str(tmp / "gts.txt")}, evaluated, None)
            return t
        finally:
            shutil.rmtree(tmp)

    def test_translates_and_reaches(self):
        t = self.run_stage(ENTITY_ROWS + SOURCED)
        self.assertEqual(t.conditional_rows_used, 2)
        ex = pairing.translate(triple("D", "Dataset", "SOURCED_FROM", "Rosetta", "Mission"), t)
        self.assertEqual(ex["predicate"], "FROM_MISSION")
        ex = pairing.translate(triple("D", "Dataset", "SOURCED_FROM", "ROSETTA-ORBITER", "Spacecraft"), t)
        self.assertEqual(ex["predicate"], "FROM_SPACECRAFT")
        ex = pairing.translate(triple("D", "Dataset", "SOURCED_FROM", "X", "Dataset"), t)     # near-miss
        self.assertTrue(ex["predicate"].endswith(pairing.NO_TRANSLATION))
        # reach: through a conditional row, the ground truth triple's entity class in that slot must be the condition's
        self.assertTrue(pairing._within_reach(triple("D", "Dataset", "FROM_MISSION", "Rosetta", "Mission"), t))
        self.assertFalse(pairing._within_reach(triple("D", "Dataset", "FROM_MISSION", "Rosetta", "Spacecraft"), t))
        self.assertEqual(t.untranslated["predicate"], [])

    def test_unchecked_conditional_row_stops(self):
        rows = ENTITY_ROWS + SOURCED[:1] + [dict(SOURCED[1], checked="no")]
        with self.assertRaises(Stop) as stop:
            self.run_stage(rows)
        self.assertIn("SOURCED_FROM (current schema) if its object of entity class Mission --> FROM_MISSION", str(stop.exception))
        self.assertIn("still need checking", str(stop.exception))

    def test_condition_outside_the_schema_stops(self):
        with self.assertRaises(Stop) as stop:
            self.run_stage(ENTITY_ROWS + SOURCED[:1] + [dict(SOURCED[1], if_object_class="Rocket")])
        self.assertIn("name an entity class that the current schema doesn't have", str(stop.exception))

    def test_conflict_stops(self):
        rows = ENTITY_ROWS + SOURCED[:1] + [row("predicate", "SOURCED_FROM", "FROM_MISSION", if_subject="Dataset"),
                                            row("predicate", "SOURCED_FROM", "FROM_SPACECRAFT", if_object="Spacecraft")]
        with self.assertRaises(Stop) as stop:
            self.run_stage(rows)
        self.assertIn("would both apply to the same extracted triple", str(stop.exception))

    def test_swap_moves_the_condition(self):
        rows = ENTITY_ROWS + [row("predicate", "HOSTS", "(none)"),
                              row("predicate", "HOSTS", "FROM_MISSION", swap="yes", if_subject="Mission"),
                              row("predicate", "FROM_SPACECRAFT", "FROM_SPACECRAFT", "same component class")]
        t = self.run_stage(rows, predicates=("HOSTS", "FROM_SPACECRAFT"))   # nothing left untranslated: no model call
        ex = pairing.translate(triple("Rosetta", "Mission", "HOSTS", "D", "Dataset"), t)
        self.assertEqual((ex["subject"], ex["predicate"], ex["object"]), ("D", "FROM_MISSION", "Rosetta"))
        self.assertTrue(pairing._within_reach(triple("D", "Dataset", "FROM_MISSION", "Rosetta", "Mission"), t))
        self.assertFalse(pairing._within_reach(triple("Rosetta", "Mission", "FROM_MISSION", "D", "Dataset"), t))


class IdentityAndNowExists(unittest.TestCase):
    """The comparison run: 060 extracted with the ground truth schema itself, so 070 translates every component class
    to itself without reading the table (which needn't even exist); a schema that differs in one definition, or one
    merged with an addition, is not it (and stops, if 060 marked it as the ground truth schema). And a (none) row
    whose own component class the ground truth schema has since gained (now exists) stops 070, unless it was kept
    (none) on purpose, against that entry's definition."""

    GT_USED = {"entity_classes": [{"component_class": c, "definition": d} for c, d in ENTITY_DEF.items()],
               "predicates": [{"component_class": p, "definition": d} for p, d in GTT_PRED_DEF.items() if p != "(none)"],
               "made": {"ground_truth_schema": True}}

    def run_stage(self, schema_used, rows=None):
        tmp = Path(tempfile.mkdtemp())
        try:
            if rows is not None:
                write_csv(tmp / "map.csv", m.COLUMNS, rows)
            (tmp / "gts.txt").write_text(GTS, encoding="utf-8")
            evaluated = type("E", (), {"schema_used": schema_used})()
            return component_classes.translate_component_classes(
                {"component_class_mapping": str(tmp / "map.csv"), "ground_truth_schema": str(tmp / "gts.txt"),
                 "schema_used": str(tmp / "schema_used.json")}, evaluated, None)
        finally:
            shutil.rmtree(tmp)

    def test_identity_without_a_table(self):
        for flagged in (True, False):                        # recognized by content too (an older 060 run)
            with self.subTest(flagged=flagged):
                used = {**self.GT_USED, "made": {"ground_truth_schema": flagged}}
                t = self.run_stage(used)                     # no table file at all: it isn't read
                self.assertEqual(t.how, component_classes.IDENTITY)
                ex = pairing.translate(triple("D", "Dataset", "FROM_MISSION", "Rosetta", "Mission"), t)
                self.assertEqual((ex["subject_class"], ex["predicate"], ex["object_class"]),
                                 ("Dataset", "FROM_MISSION", "Mission"))
                self.assertEqual((t.calls, t.suggest_calls, t.rows_used), (0, 0, 5))
                self.assertTrue(pairing._within_reach(triple("D", "Dataset", "FROM_SPACECRAFT", "A", "Spacecraft"), t))
        # spacing aside, a definition is the same
        used = {**self.GT_USED, "entity_classes": [dict(e, definition=e["definition"].replace(" ", "  "))
                                                   for e in self.GT_USED["entity_classes"]]}
        self.assertEqual(self.run_stage(used).how, component_classes.IDENTITY)

    def test_near_misses_stop_when_marked(self):
        redefined = {**self.GT_USED, "predicates": [{"component_class": "FROM_MISSION", "definition": "was sent by"},
                                                    {"component_class": "FROM_SPACECRAFT",
                                                     "definition": "comes from this spacecraft"}]}
        dropped = {**self.GT_USED, "entity_classes": self.GT_USED["entity_classes"][:2]}
        added = {**self.GT_USED, "entity_classes": self.GT_USED["entity_classes"]
                 + [{"component_class": "Probe", "definition": "x", "from": "additions"}]}
        for used, says in ((redefined, "FROM_MISSION (predicate, defined differently in the ground truth schema now)"),
                           (dropped, "Spacecraft (entity class, only in the ground truth schema)"),
                           (added, "1 came from the schema additions: Probe")):
            with self.subTest(says=says):
                with self.assertRaises(Stop) as stop:
                    self.run_stage(used, rows=[])
                self.assertIn("extracted with the ground truth schema, but", str(stop.exception))
                self.assertIn(says, str(stop.exception))
                self.assertIn("--schema annotations/ground_truth_schema.txt", str(stop.exception))
        # not marked by 060: another schema, translated through the table (here: rows added, and a stop to check)
        with self.assertRaises(Stop) as stop:
            self.run_stage({**redefined, "made": {}}, rows=[])
        self.assertIn("Added", str(stop.exception))

    def test_now_exists_stops_unless_kept_on_purpose(self):
        used = {"entity_classes": [{"component_class": c, "definition": "d"} for c in ENTITY_DEF],
                "predicates": [{"component_class": "FROM_MISSION", "definition": "d"}], "made": {}}
        coined = dict(row("predicate", "FROM_MISSION", "(none)"), _line=5)      # checked before FROM_MISSION existed
        with self.assertRaises(Stop) as stop:
            self.run_stage(used, ENTITY_ROWS + [coined])
        self.assertIn("line 5: FROM_MISSION (current schema) --> (none), but FROM_MISSION (ground truth schema) now "
                      "exists", str(stop.exception))
        self.assertIn("tick Checked again", str(stop.exception))
        # kept (none) on purpose: checked against FROM_MISSION's definition, so it translates to nothing, no stop
        kept = dict(coined, definition_in_gtt=GTT_PRED_DEF["FROM_MISSION"])
        t = self.run_stage(used, ENTITY_ROWS + [kept])
        self.assertEqual(list(t.predicate.values()), [(None, False)])
        # the entry redefined since: stale (the ground truth schema's definition), so checked again
        with self.assertRaises(Stop) as stop:
            self.run_stage(used, ENTITY_ROWS + [dict(coined, definition_in_gtt="came from a mission")])
        self.assertIn("were checked when the ground truth schema", str(stop.exception))
        # not checked at all: asked first as an unchecked row
        with self.assertRaises(Stop) as stop:
            self.run_stage(used, ENTITY_ROWS + [dict(coined, checked="no")])
        self.assertIn("still need checking", str(stop.exception))


if __name__ == "__main__":
    unittest.main()
