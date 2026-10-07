"""Evaluation: pairing (070_evaluate_helpers/pairing.py) and the metrics
(stats.py), checked against the examples in 070_evaluate/metrics.md and
against the cases that would catch a wrong pairing."""
import unittest

from support import use_step

use_step("070_evaluate")
import pairing                                   # noqa: E402
import stats                                     # noqa: E402
from component_classes import Translation        # noqa: E402
from common.partial_reviews import NOT_SAME, SAME, pair_key   # noqa: E402
from common.triples_io import component_class_key            # noqa: E402

ENTITY = ["Instrument", "Spacecraft", "Dataset", "TimeSpan", "Mission", "Agency"]
PREDICATES = ["ABOARD", "ACQUIRED_BY", "HAS_TIME_SPAN", "SPONSORED_BY"]


def translation(entity=ENTITY, predicates=PREDICATES, extra_entity=None, extra_predicates=None,
                reachable_entity=None, reachable_predicates=None):
    """Every component class translates to itself, plus the extra rows given."""
    t = Translation()
    t.entity = {component_class_key(c): c for c in entity}
    t.entity.update({component_class_key(k): v for k, v in (extra_entity or {}).items()})
    t.predicate = {component_class_key(p): (p, False) for p in predicates}
    t.predicate.update({component_class_key(k): v for k, v in (extra_predicates or {}).items()})
    t.reachable = {"entity class": {component_class_key(c) for c in (reachable_entity or entity)},
                   "predicate": {component_class_key(p) for p in (reachable_predicates or predicates)}}
    return t


def triple(s, sc, p, o, oc):
    return {"subject": s, "subject_class": sc, "predicate": p, "object": o, "object_class": oc}


def record(gt, extracted, rid="r1", gt_class=None, said_class=None, stratum="g", part="tuning"):
    describes = lambda c: {"object_class": c} if c is not None else None   # noqa: E731
    return {"id": rid, "gt": gt, "extracted": extracted, "stratum": stratum, "part": part,
            "gt_describes": describes(gt_class), "extracted_describes": describes(said_class)}


def counts_record(extracted, gt, pairs, strict, stratum="g", **more):
    """A compared record with only the counts set, for the metric formulas."""
    c = {"extracted": extracted, "gt": gt, "within_reach": more.get("within_reach", gt),
         "within_strict_reach": more.get("within_strict_reach", gt)}
    for level in pairing.LEVELS:
        c[f"{level}_pairs"] = pairs
        c[f"{level}_strict_pairs"] = strict
        c[f"{level}_pairs_within_reach"] = pairs
        c[f"{level}_strict_pairs_within_strict_reach"] = strict
    return {"stratum": stratum, "part": "tuning",
            "compared": {"counts": c, "describes": more.get("describes", {"truth": None, "said": None, "right": False})}}


# metrics.md, "Pairs: example"
G = [triple("MODIS", "Instrument", "ABOARD", "Aqua", "Spacecraft"),
     triple("AIRS", "Instrument", "ABOARD", "Aqua", "Spacecraft"),
     triple("MODIS Snow Cover", "Dataset", "ACQUIRED_BY", "MODIS", "Instrument"),
     triple("MODIS Snow Cover", "Dataset", "HAS_TIME_SPAN", "2002–2023", "TimeSpan"),
     triple("CERES", "Instrument", "ABOARD", "Aqua", "Spacecraft")]
E = [triple("the MODIS", "Instrument", "ABOARD", "Aqua", "Spacecraft"),
     triple("AIRS", "Dataset", "ABOARD", "Aqua", "Spacecraft"),
     triple("MODIS Snow Cover 5-Min L2 Swath", "Dataset", "ACQUIRED_BY",
            "Moderate Resolution Imaging Spectroradiometer (MODIS)", "Instrument"),
     triple("MODIS Snow Cover", "Dataset", "HAS_TIME_SPAN", "the period 2002–2023", "Dataset"),
     triple("MODIS", "Instrument", "ABOARD", "Terra", "Spacecraft"),
     triple("Moderate Resolution Imaging Spectroradiometer (MODIS)", "Instrument", "ABOARD", "Aqua", "Spacecraft")]


class PairsExample(unittest.TestCase):
    """metrics.md's Pairs example, outcome by outcome."""

    def setUp(self):
        self.c = pairing.compare_record(record(G, E), translation())["compared"]

    def test_pairs(self):
        self.assertEqual(sorted(self.c["pairs"]),
                         [(0, 0, "exact"), (1, 1, "exact"), (2, 2, "partial"), (3, 3, "partial")])

    def test_counts(self):
        n = self.c["counts"]
        self.assertEqual((n["extracted"], n["gt"]), (6, 5))
        self.assertEqual((n["exact_pairs"], n["exact_strict_pairs"]), (2, 1))
        self.assertEqual((n["partial_pairs"], n["partial_strict_pairs"]), (4, 2))   # partial counts both passes

    def test_unpaired(self):
        paired_g = {g for g, _, _ in self.c["pairs"]}
        paired_e = {e for _, e, _ in self.c["pairs"]}
        self.assertEqual(set(range(5)) - paired_g, {4})          # G5: ground truth only
        self.assertEqual(set(range(6)) - paired_e, {4, 5})       # E5, E6: extracted only


class Pairing(unittest.TestCase):

    def pairs(self, gt, ex, t=None, reviews=None):
        return pairing.compare_record(record(gt, ex), t or translation(), reviews)["compared"]

    def test_evened_out(self):
        g = [triple("MODIS", "Instrument", "ABOARD", "Aqua-1", "Spacecraft")]
        for s, o in [("modis", "aqua-1"), ("  The MODIS.", "AQUA–1"), ("“MODIS”", "Aqua‑1,"), ("a MODIS", "(Aqua-1)")]:
            with self.subTest(s=s, o=o):
                c = self.pairs(g, [triple(s, "Instrument", "ABOARD", o, "Spacecraft")])
                self.assertEqual(c["pairs"], [(0, 0, "exact")])

    def test_predicate_must_match(self):
        c = self.pairs([triple("MODIS", "Instrument", "ABOARD", "Aqua", "Spacecraft")],
                       [triple("MODIS", "Instrument", "ACQUIRED_BY", "Aqua", "Spacecraft")])
        self.assertEqual(c["pairs"], [])

    def test_predicate_loose_spelling(self):
        t = translation(extra_predicates={"aboard": ("ABOARD", False)})
        c = self.pairs([triple("MODIS", "Instrument", "ABOARD", "Aqua", "Spacecraft")],
                       [triple("MODIS", "Instrument", "Aboard", "Aqua", "Spacecraft")], t)
        self.assertEqual(c["pairs"], [(0, 0, "exact")])

    def test_partial_needs_whole_words(self):
        g = [triple("MODIS", "Instrument", "ABOARD", "Aqua", "Spacecraft")]
        for s, paired in [("MODIS Terra", True), ("Terra-MODIS", True), ("MODISTerra", False), ("MOD", False)]:
            with self.subTest(s=s):
                c = self.pairs(g, [triple(s, "Instrument", "ABOARD", "Aqua", "Spacecraft")])
                self.assertEqual(bool(c["pairs"]), paired)

    def test_partial_either_way_round(self):
        c = self.pairs([triple("Aqua spacecraft MODIS", "Instrument", "ABOARD", "Aqua", "Spacecraft")],
                       [triple("MODIS", "Instrument", "ABOARD", "Aqua", "Spacecraft")])
        self.assertEqual(c["pairs"], [(0, 0, "partial")])

    def test_one_partner_each(self):
        g = [triple("MODIS", "Instrument", "ABOARD", "Aqua", "Spacecraft")]
        c = self.pairs(g, [g[0], dict(g[0])])
        self.assertEqual(len(c["pairs"]), 1)
        self.assertEqual(c["counts"]["extracted"], 2)            # the repeat stays, extracted only

    def test_largest_pairing(self):
        # G0 can pair with E0 or E1; G1 only with E0. Taking G0's first
        # partner (E0) would leave G1 unpaired; the largest pairing pairs both.
        g = [triple("MODIS instrument suite", "Instrument", "ABOARD", "Aqua", "Spacecraft"),
             triple("Terra MODIS", "Instrument", "ABOARD", "Aqua", "Spacecraft")]
        e = [triple("MODIS", "Instrument", "ABOARD", "Aqua", "Spacecraft"),
             triple("MODIS instrument", "Instrument", "ABOARD", "Aqua", "Spacecraft")]
        c = self.pairs(g, e)
        self.assertEqual(sorted(c["pairs"]), [(0, 1, "partial"), (1, 0, "partial")])

    def test_exact_before_partial(self):
        # E0 could pair partially with G0, but G1 is its exact partner.
        g = [triple("MODIS on Aqua", "Instrument", "ABOARD", "Aqua", "Spacecraft"),
             triple("MODIS", "Instrument", "ABOARD", "Aqua", "Spacecraft")]
        c = self.pairs(g, [triple("MODIS", "Instrument", "ABOARD", "Aqua", "Spacecraft")])
        self.assertEqual(c["pairs"], [(1, 0, "exact")])

    def test_reversed_row_swaps(self):
        t = translation(extra_predicates={"FUNDS": ("SPONSORED_BY", True)})
        c = self.pairs([triple("Aqua", "Mission", "SPONSORED_BY", "NASA", "Agency")],
                       [triple("NASA", "Agency", "FUNDS", "Aqua", "Mission")], t)
        self.assertEqual(c["pairs"], [(0, 0, "exact")])
        self.assertEqual(c["counts"]["exact_strict_pairs"], 1)    # entity classes swapped too
        self.assertEqual(c["translated"][0]["crt"],
                         {"subject_class": "Mission", "predicate": "FUNDS", "object_class": "Agency"})

    def test_none_row_never_equal(self):
        t = translation(extra_entity={"Probe": None}, extra_predicates={"CARRIES": (None, False)})
        c = self.pairs([triple("MODIS", "Instrument", "ABOARD", "Aqua", "Spacecraft")],
                       [triple("MODIS", "Instrument", "ABOARD", "Aqua", "Probe"),
                        triple("Aqua", "Spacecraft", "CARRIES", "MODIS", "Instrument")], t)
        self.assertEqual(c["pairs"], [(0, 0, "exact")])
        self.assertEqual(c["counts"]["exact_strict_pairs"], 0)
        self.assertTrue(c["translated"][0]["object_class"].endswith(pairing.NO_TRANSLATION))
        self.assertTrue(c["translated"][1]["predicate"].endswith(pairing.NO_TRANSLATION))

    def test_reviews(self):
        g = [triple("MODIS", "Instrument", "ABOARD", "Aqua", "Spacecraft")]
        e = [triple("MODIS Terra", "Instrument", "ABOARD", "Aqua", "Spacecraft")]
        unreviewed = self.pairs(g, e)
        self.assertEqual(unreviewed["partial_review"], {"rejected": 0, "unreviewed": 1})
        key = pair_key("r1", g[0], unreviewed["translated"][0])
        same = self.pairs(g, e, reviews={key: SAME})
        self.assertEqual((len(same["pairs"]), same["partial_review"]["unreviewed"]), (1, 0))
        rejected = self.pairs(g, e, reviews={key: NOT_SAME})
        self.assertEqual(rejected["pairs"], [])
        self.assertEqual(rejected["partial_review"], {"rejected": 1, "unreviewed": 0})

    def test_review_does_not_block_exact(self):
        g = [triple("MODIS", "Instrument", "ABOARD", "Aqua", "Spacecraft")]
        e = [dict(g[0])]
        key = pair_key("r1", g[0], pairing.translate(e[0], translation()))
        self.assertEqual(self.pairs(g, e, reviews={key: SAME})["pairs"], [(0, 0, "exact")])

    def test_describes(self):
        t = translation(extra_entity={"Probe": None})
        cases = [("Dataset", "Dataset", True), ("Dataset", "dataset", True), ("Dataset", "Instrument", False),
                 ("Dataset", "X", False), ("X", "Dataset", False), ("Dataset", "Probe", False), (None, "Dataset", False)]
        for truth, said, right in cases:
            with self.subTest(truth=truth, said=said):
                d = pairing.compare_record(record([], [], gt_class=truth, said_class=said), t)["compared"]["describes"]
                self.assertEqual(d["right"], right)
                self.assertEqual(d["truth"], truth if truth not in (None, "X") else None)
                self.assertEqual(d["said"] is None, said == "X")


class Reach(unittest.TestCase):
    """metrics.md, "Recall upper bound: example"."""

    def test_example(self):
        t = translation(reachable_entity=["Instrument", "Spacecraft", "TimeSpan"],
                        reachable_predicates=["ABOARD", "ACQUIRED_BY"])
        c = pairing.compare_record(record(G, E), t)["compared"]
        self.assertEqual(c["within_reach"], [True, True, True, False, True])
        self.assertEqual(c["within_strict_reach"], [True, True, False, False, True])
        n = stats.numbers([{"compared": c, "stratum": "g"}])
        self.assertAlmostEqual(n["recall_upper_bound"], 4 / 5)
        self.assertAlmostEqual(n["strict_recall_upper_bound"], 3 / 5)

    def test_strict_reach_needs_the_predicate(self):
        t = translation(reachable_predicates=["ABOARD"])                     # every entity class reachable
        c = pairing.compare_record(record([triple("Aqua", "Spacecraft", "SPONSORED_BY", "NASA", "Agency")], []), t)
        self.assertEqual((c["compared"]["within_reach"], c["compared"]["within_strict_reach"]), ([False], [False]))


class Mismatches(unittest.TestCase):

    def test_entity_class_and_predicate(self):
        t = translation(extra_entity={"Satellite": "Instrument"}, extra_predicates={"CARRIES": ("ACQUIRED_BY", False),
                                                                                   "HOSTS": ("ACQUIRED_BY", False)})
        gt = [triple("MODIS", "Instrument", "ABOARD", "Aqua", "Spacecraft"),
              triple("Aqua", "Spacecraft", "ABOARD", "MODIS", "Instrument"),
              triple("CERES", "Instrument", "ABOARD", "Terra", "Spacecraft")]
        ex = [triple("MODIS", "Instrument", "ABOARD", "Aqua", "Satellite"),     # paired; object class differs
              triple("Aqua", "Spacecraft", "CARRIES", "MODIS", "Instrument"),   # same subject and object, other predicate
              triple("Terra", "Spacecraft", "HOSTS", "CERES", "Instrument")]    # the two swapped
        rec = record(gt, ex)
        pairing.compare_record(rec, t)
        found = pairing.component_class_mismatches([rec])
        self.assertEqual(found, [
            {"kind": "entity class", "crt_component_class": "Satellite", "translated_to": "Instrument",
             "gtt_component_class": "Spacecraft", "swapped": False, "count": 1},
            {"kind": "predicate", "crt_component_class": "CARRIES", "translated_to": "ACQUIRED_BY",
             "gtt_component_class": "ABOARD", "swapped": False, "count": 1},
            {"kind": "predicate", "crt_component_class": "HOSTS", "translated_to": "ACQUIRED_BY",
             "gtt_component_class": "ABOARD", "swapped": True, "count": 1}])

    def test_none_when_all_agree(self):
        rec = record(G, E)
        pairing.compare_record(rec, translation())
        kinds = {m["kind"] for m in pairing.component_class_mismatches([rec])}
        self.assertEqual(kinds, {"entity class"})                # only E2's and E4's entity classes


class Formulas(unittest.TestCase):
    """metrics.md's Precision, Recall, F1, and Entity-class accuracy examples:
    micro-averaged, so the records' counts are added before dividing."""

    def setUp(self):
        self.n = stats.numbers([counts_record(extracted=4, gt=5, pairs=3, strict=2),
                                counts_record(extracted=1, gt=2, pairs=1, strict=1)])

    def test_precision_recall_f1(self):
        for level in pairing.LEVELS:
            m = self.n[level]
            self.assertAlmostEqual(m["precision"], 0.8)                       # (3 + 1) / (4 + 1)
            self.assertAlmostEqual(m["recall"], 4 / 7)                        # (3 + 1) / (5 + 2)
            self.assertAlmostEqual(m["f1"], 2 * 0.8 * (4 / 7) / (0.8 + 4 / 7))
            self.assertEqual(round(100 * m["f1"]), 67)
            self.assertAlmostEqual(m["strict_precision"], 3 / 5)
            self.assertAlmostEqual(m["strict_recall"], 3 / 7)
            self.assertAlmostEqual(m["entity_class_accuracy"], 3 / 4)          # strict pairs / pairs
            self.assertAlmostEqual(m["strict_f1"], 2 * 0.6 * (3 / 7) / (0.6 + 3 / 7))

    def test_not_averaged_per_record(self):
        self.assertNotAlmostEqual(self.n["exact"]["precision"], (3 / 4 + 1 / 1) / 2)

    def test_nothing_to_divide(self):
        n = stats.numbers([counts_record(extracted=0, gt=0, pairs=0, strict=0)])
        for key in ("precision", "recall", "f1", "entity_class_accuracy", "recall_within_reach"):
            self.assertIsNone(n["exact"][key], key)
        self.assertIsNone(n["recall_upper_bound"])
        only_gt = stats.numbers([counts_record(extracted=0, gt=3, pairs=0, strict=0)])["exact"]
        self.assertIsNone(only_gt["precision"])
        self.assertEqual((only_gt["recall"], only_gt["f1"]), (0, 0))

    def test_describes_numbers(self):
        d = lambda truth, right: {"truth": truth, "said": None, "right": right}   # noqa: E731
        recs = [counts_record(1, 1, 1, 1, describes=d("Dataset", True)),
                counts_record(1, 1, 1, 1, describes=d("Dataset", True)),
                counts_record(1, 1, 1, 1, describes=d("Dataset", False)),
                counts_record(1, 1, 1, 1, describes=d("WebTool", False)),
                counts_record(1, 1, 1, 1, describes=d(None, False))]                # no truth: not counted
        n = stats.numbers(recs)["describes"]
        self.assertEqual(n["records"], 4)
        self.assertAlmostEqual(n["accuracy"], 2 / 4)
        self.assertAlmostEqual(n["majority_baseline"], 3 / 4)
        self.assertAlmostEqual(n["per_entity_class_average"], (2 / 3 + 0) / 2)


class Margins(unittest.TestCase):

    def test_too_few_records(self):
        recs = [counts_record(2, 2, 1, 1) for _ in range(stats.MIN_RECORDS - 1)]
        m = stats.with_margins(recs)
        self.assertFalse(m["margins"])
        self.assertEqual(m["exact"]["precision"], {"value": 0.5, "low": None, "high": None})

    def test_margin_contains_spread(self):
        recs = [counts_record(2, 2, i % 3, 0, stratum=f"g{i % 2}") for i in range(40)]
        m = stats.with_margins(recs)
        self.assertTrue(m["margins"])
        p = m["exact"]["precision"]
        self.assertLess(p["low"], p["value"])
        self.assertLess(p["value"], p["high"])
        self.assertEqual(stats.with_margins(recs)["exact"]["precision"], p)    # fixed seed: same margins

    def test_no_spread_no_margin(self):
        m = stats.with_margins([counts_record(2, 2, 2, 2) for _ in range(stats.MIN_RECORDS)])
        self.assertEqual(m["exact"]["precision"], {"value": 1.0, "low": 1.0, "high": 1.0})

    def test_each_stratum_keeps_its_size(self):
        # One record of stratum "a" with precision 0, 39 of stratum "b" with 1:
        # every redraw keeps one "a" record, so precision never falls below 39/40.
        recs = [counts_record(1, 1, 0, 0, stratum="a")] + [counts_record(1, 1, 1, 1, stratum="b") for _ in range(39)]
        p = stats.with_margins(recs)["exact"]["precision"]
        self.assertEqual((p["low"], p["value"], p["high"]), (39 / 40, 39 / 40, 39 / 40))


class MarginChecks(unittest.TestCase):

    def records(self, strata, extracted=2):
        out = []
        for i, g in enumerate(strata):
            r = counts_record(extracted, 2, i % 3, 0, stratum=g)
            r["id"] = f"r{i}"
            out.append(r)
        return out

    def test_all_hold(self):
        recs = self.records(["a", "b"] * 20)
        checks = stats.margin_checks(recs, stats.with_margins(recs), catalog_records=10_000)
        self.assertEqual(checks["single_record_strata"], [])
        self.assertNotIn("exact: precision", checks["at_bound"])
        self.assertAlmostEqual(checks["catalog_proportion"], 40 / 10_000)
        self.assertAlmostEqual(checks["largest_record"]["extracted triples"]["proportion"], 1 / 40)

    def test_failures_found(self):
        recs = self.records(["a"] * 38 + ["b", ""])
        recs[0]["compared"]["counts"]["extracted"] = 41                    # one record with half the extracted triples
        point = stats.with_margins(recs)
        checks = stats.margin_checks(recs, point, catalog_records=200)
        self.assertEqual(checks["single_record_strata"], ["(no stratum)", "b"])
        self.assertIn("exact: strict_precision", checks["at_bound"])        # 0 strict pairs: the range is 0% to 0%
        self.assertEqual(checks["largest_record"]["extracted triples"], {"record": "r0", "proportion": 41 / 119})
        self.assertGreater(checks["catalog_proportion"], stats.FINITE_NEGLIGIBLE)
        import moves
        text = "\n".join(moves._margin_check_lines(checks))
        self.assertEqual(text.count("doesn't hold"), 3)
        self.assertIn("(no stratum), b", text)


class Parts(unittest.TestCase):

    def evaluated(self):
        class Evaluated:
            pass
        e = Evaluated()
        e.records = [dict(counts_record(1, 1, 1, 1), part="tuning"), dict(counts_record(1, 1, 0, 0), part="held-out")]
        e.pool_strata = {"g": 10}
        return e

    def test_held_out_kept_aside(self):
        m = stats.compute_metrics(self.evaluated(), {"evaluate_held_out": False})
        self.assertEqual(set(m), {"tuning", "kept_aside"})
        self.assertEqual(m["kept_aside"], {"held-out": 1})
        self.assertEqual(m["tuning"]["numbers"]["exact"]["precision"]["value"], 1.0)

    def test_held_out_shown(self):
        m = stats.compute_metrics(self.evaluated(), {"evaluate_held_out": True})
        self.assertEqual(m["kept_aside"], {})
        self.assertEqual(m["held-out"]["numbers"]["exact"]["precision"]["value"], 0.0)

    def test_strata_table(self):
        recs = [counts_record(1, 1, 1, 1, stratum="a"), counts_record(1, 1, 1, 1, stratum="a"),
                counts_record(1, 1, 1, 1, stratum="b")]
        rows = {r["stratum"]: r for r in stats.strata_table(recs, {"a": 3, "b": 1, "c": 4})}
        self.assertEqual(set(rows), {"a", "b", "c"})
        self.assertAlmostEqual(rows["a"]["share_evaluated"], 2 / 3)
        self.assertAlmostEqual(rows["a"]["share_pool"], 3 / 8)
        self.assertEqual(rows["c"]["records"], 0)
        self.assertIsNone(rows["a"]["numbers"])                     # fewer than MIN_RECORDS


if __name__ == "__main__":
    unittest.main()
