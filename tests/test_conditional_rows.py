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


if __name__ == "__main__":
    unittest.main()
