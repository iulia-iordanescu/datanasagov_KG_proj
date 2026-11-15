"""Schema induction (040_induce_schema), the stages code decides: drawing
the texts by stratum (twins skipped), matching the model's labels (sent with
their source text), merging synonyms (chains, cycles, invalid merges),
checking and capping the splits, counting support, building the schema from
the evidence, and the run's statistics."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from support import use_step

use_step("040_induce_schema")
import check                                      # noqa: E402
import count                                      # noqa: E402
import label                                      # noqa: E402
import merge                                      # noqa: E402
import saturation                                 # noqa: E402
import split                                      # noqa: E402
import tally                                      # noqa: E402
import texts as texts_stage                       # noqa: E402
from common import llm                            # noqa: E402


def texts(*items):
    """Triples with texts [(id, maintainer, title, describes_class, [(s, p, o), ...])]."""
    return SimpleNamespace(texts=[{"id": i, "maintainer": m, "title": t, "describes_class": d,
                                   "triple_instances": [{"subject": s, "predicate": p, "object": o,
                                                         "source_text": f"{s} {p} {o}"} for s, p, o in tis],
                                   "unverified": []}
                                  for i, m, t, d, tis in items])


class Drawing(unittest.TestCase):
    """Stage 1: texts_per_stratum texts from each stratum, in rounds; whole-text and notes-only twins of a text
    already drawn skipped, title-only twins kept."""

    RECORDS = {"a": {"title": "Snow", "notes": "Daily snow."}, "b": {"title": "Ice", "notes": "daily  SNOW."},
               "c": {"title": "Snow", "notes": "Weekly snow."}, "d": {"title": "Fire", "notes": "Burned area."},
               "e": {"title": "snow", "notes": "Daily snow."}, "f": {"title": "Rain", "notes": "Daily rain."},
               "g": {"title": "Wind", "notes": ""}, "h": {"title": "Wind", "notes": ""}}

    def test_twins_skipped_title_only_kept(self):
        taken, skipped, title_only = texts_stage.draw({"S1": ["a", "c", "f"], "S2": ["b", "e", "d"]}, ["S1", "S2"],
                                                      self.RECORDS, 3)
        self.assertEqual(taken, {"S1": ["a", "c", "f"], "S2": ["d"]})
        # b: the same notes evened out (notes only); e: the same title and notes evened out (whole text)
        self.assertEqual([(k["id"], k["twin_kind"], k["twin_of"]) for k in skipped],
                         [("b", "notes only", "a"), ("e", "whole text", "a")])
        self.assertEqual(title_only, {"S1": 1, "S2": 0})                 # c: the same title, other notes: kept

    def test_empty_notes_are_never_the_same(self):
        """Near miss: two texts with the same title and no notes share no notes, so they are title-only twins, kept."""
        taken, skipped, title_only = texts_stage.draw({"S": ["g", "h"]}, ["S"], self.RECORDS, 2)
        self.assertEqual((taken["S"], skipped, title_only["S"]), (["g", "h"], [], 1))

    def test_taking_more_keeps_what_was_taken(self):
        orders = {"S1": ["a", "c", "f"], "S2": ["b", "e", "d", "g"], "S3": ["h"]}
        for per in range(1, 4):
            fewer, _, _ = texts_stage.draw(orders, ["S1", "S2", "S3"], self.RECORDS, per)
            more, _, _ = texts_stage.draw(orders, ["S1", "S2", "S3"], self.RECORDS, per + 1)
            for s in orders:
                self.assertEqual(more[s][:len(fewer[s])], fewer[s], (per, s))

    def test_doctest(self):
        import doctest
        self.assertEqual(doctest.testmod(texts_stage).failed, 0)

    def test_small_stratum_order_is_030s_construction(self):
        """The stratum "(small maintainers)" is ordered as 030 orders a maintainer's candidates: the same seed, the
        stratum's name in place of the maintainer's; its first k are a random sample for every k."""
        import random
        ids = [f"r{i}" for i in range(30)]
        order = texts_stage._small_order(list(reversed(ids)), 7)            # the input order doesn't matter
        self.assertEqual(order, random.Random("7/(small maintainers)").sample(sorted(ids), 30))
        self.assertNotEqual(order, texts_stage._small_order(ids, 8))

    def test_read_strata(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp)
        good = {"strata": 3, "places_per_stratum": {"A": 5, "B": 2, "(small maintainers)": 3},
                "stratum_sizes": {"A": 50, "B": 20, "(small maintainers)": 30}, "collapsed_maintainers": ["x", "y"]}
        path = tmp / "design.json"
        path.write_text(json.dumps(good), encoding="utf-8")
        strata, of = texts_stage.read_strata(path)
        self.assertEqual(strata, ["A", "(small maintainers)", "B"])        # largest first
        self.assertEqual(of, {"A": "A", "B": "B", "x": "(small maintainers)", "y": "(small maintainers)"})
        for broken in ({**good, "strata": 4}, {k: v for k, v in good.items() if k != "collapsed_maintainers"},
                       {**good, "places_per_stratum": {"A": 5, "B": 2, "small": 3}}):
            path.write_text(json.dumps(broken), encoding="utf-8")
            with self.subTest(broken=broken), self.assertRaisesRegex(ValueError, "describe the pool's strata"):
                texts_stage.read_strata(path)

    def test_old_settings_refused(self):
        """The earlier design's settings stop the run with what replaced them, not argparse's bare message."""
        import contextlib
        import io
        from common.step import _parse_command_line
        for argv in (["--texts_per_maintainer", "4"], ["--induction-maintainers=3"]):
            err = io.StringIO()
            with self.subTest(argv=argv), contextlib.redirect_stderr(err), self.assertRaises(SystemExit) as e:
                _parse_command_line("040_induce_schema", {}, {"texts_per_stratum": 8}, argv,
                                    retired=texts_stage.RETIRED)
            self.assertEqual(e.exception.code, 2)
            self.assertIn("earlier sample design", err.getvalue())
            self.assertIn("--texts_per_stratum", err.getvalue())
        # near miss: a setting that merely starts the same way is argparse's to judge, not refused as retired
        _, chosen, _ = _parse_command_line("040_induce_schema", {}, {"texts_per_stratum": 8},
                                           ["--texts_per_stratum", "3"], retired=texts_stage.RETIRED)
        self.assertEqual(chosen["texts_per_stratum"], 3)


class Scripted:
    """A model that gives each prompt kind a fixed reply, and counts calls."""

    def __init__(self, replies):
        self.replies, self.prompts = replies, []

    def __enter__(self):
        self.saved = llm.call_llm, llm.call_llm_json
        llm.call_llm = lambda prompt, **kw: '{"ok": true}'

        def answer(prompt, **kw):
            self.prompts.append(prompt)
            for marker, reply in self.replies.items():
                if marker in prompt:
                    return reply
            raise AssertionError("no scripted reply")
        llm.call_llm_json = answer
        self.tmp = Path(tempfile.mkdtemp())
        return llm.Calls(paid=llm.PaidCalls(confirm=False), cache_dir=self.tmp)

    def __exit__(self, *exc):
        llm.call_llm, llm.call_llm_json = self.saved
        shutil.rmtree(self.tmp)


class Extracting(unittest.TestCase):

    def test_duplicate_keeps_the_copy_that_passed(self):
        """Stage 2: a triple instance stated by two pieces counts once, and the copy kept is the first that passed
        its checks: a first copy with a wrong source text doesn't make the fact unverified."""
        import extract
        from common import extraction
        good = {"subject": "MODIS", "predicate": "is aboard", "object": "Aqua", "source_text": "MODIS aboard Aqua"}
        bad = dict(good, source_text="MODIS rides Aqua")
        item = {"id": "r", "maintainer": "m", "title": "T", "text": "title: T\n\nnotes: MODIS aboard Aqua.",
                "record": {}, "pieces": ["p1", "p2"]}
        for first, second, verified, unverified in [(bad, good, 1, 0), (good, bad, 1, 0), (good, good, 1, 0),
                                                    (bad, bad, 0, 1)]:
            with self.subTest(first=first["source_text"], second=second["source_text"]):
                replies = extraction.Replies(of={"r": [{"triples": [first]}, {"triples": [second]}]})
                saved = extraction.ask_model
                extraction.ask_model = lambda *a, **k: replies
                try:
                    out = extract.extract_triple_instances(SimpleNamespace(items=[item]), None, {"workers": 1})
                finally:
                    extraction.ask_model = saved
                t = out.texts[0]
                self.assertEqual((len(t["triple_instances"]), len(t["unverified"])), (verified, unverified))
                self.assertEqual(sum(out.errors.values()), unverified)


    def test_flags_counted_for_verified_only(self):
        """Stage 2: the report's "Verified, with flags worth a look" counts the flags of verified triple instances
        only; an unverified one's flags (here subject_not_in_text) aren't counted."""
        import extract
        from common import extraction
        verified = {"subject": "the instrument", "predicate": "is aboard", "object": "Aqua",
                    "source_text": "MODIS aboard Aqua"}                 # subject_not_in_text, subject_not_in_source
        unverified = {"subject": "Terra", "predicate": "carries", "object": "Aqua",
                      "source_text": "Terra carries Aqua"}             # source_not_in_text; subject_not_in_text
        item = {"id": "r", "maintainer": "m", "title": "T", "text": "title: T\n\nnotes: MODIS aboard Aqua.",
                "record": {}, "pieces": ["p1"]}
        replies = extraction.Replies(of={"r": [{"triples": [verified, unverified]}]})
        saved = extraction.ask_model
        extraction.ask_model = lambda *a, **k: replies
        try:
            out = extract.extract_triple_instances(SimpleNamespace(items=[item]), None, {"workers": 1})
        finally:
            extraction.ask_model = saved
        self.assertEqual(out.errors, {"source_not_in_text": 1})
        self.assertEqual(out.flags, {"subject_not_in_text": 1, "subject_not_in_source": 1})

class Labeling(unittest.TestCase):

    def test_match(self):
        labels, missing = label._match(["MODIS", "Aqua  craft", "Terra", "Aura"],
                                       {"MODIS": "Instrument", "aqua craft": "Spacecraft", "Terra": " ", "Aura": 3,
                                        "extra": "Ignored"})
        self.assertEqual(labels, {"MODIS": "Instrument", "Aqua  craft": "Spacecraft"})
        self.assertEqual(missing, ["Terra", "Aura"])
        self.assertEqual(label._match(["a"], "not a dict"), ({}, ["a"]))

    def test_source_text_sent(self):
        """Each component instance is sent with its shortest triple instance and that triple instance's source text."""
        triples = texts(("t1", "m", "T1", "", [("Dawn", "carries", "GRaND"), ("Dawn", "is a spacecraft of", "NASA")]))
        triples.texts[0]["triple_instances"][0]["source_text"] = "the GRaND instrument aboard the Dawn spacecraft"
        found = label.component_instances(triples)
        self.assertEqual(found["entity"]["Dawn"][1], {"example": "Dawn -- carries -- GRaND",
                                                      "source_text": "the GRaND instrument aboard the Dawn spacecraft"})
        model = Scripted({"\nINSTANCES (": {"labels": {"Dawn": "Spacecraft", "GRaND": "Instrument",
                                                               "NASA": "Organization"}},
                          "PREDICATE INSTANCES (": {"labels": {"carries": "CARRIES", "is a spacecraft of": "OF"}}})
        with model as calls:
            label.label_component_instances(triples, calls)
        sent = model.prompts[0]
        items = json.loads(sent[sent.rindex("and its source text):") + len("and its source text):"):])
        self.assertEqual(items["Dawn"]["source_text"], "the GRaND instrument aboard the Dawn spacecraft")

    def test_left_out_asked_again(self):
        triples = texts(("t1", "m", "T1", "", [("MODIS", "is aboard", "Aqua"), ("AIRS", "is aboard", "Aqua")]))
        first = {"MODIS": "Instrument", "Aqua": "Spacecraft"}               # AIRS left out
        replies = iter([{"labels": first}, {"labels": {"AIRS": "Instrument"}}, {"labels": {"is aboard": "ABOARD"}}])
        with Scripted({}) as calls:
            llm.call_llm_json = lambda prompt, **kw: next(replies)
            result = label.label_component_instances(triples, calls)
        self.assertEqual(result.of["entity"], {"MODIS": "Instrument", "Aqua": "Spacecraft", "AIRS": "Instrument"})
        self.assertEqual(result.vocabulary["entity"], ["Spacecraft", "Instrument"])     # in the batch's order (AIRS, Aqua, MODIS)
        self.assertEqual(result.unlabeled, {"entity": [], "predicate": []})
        self.assertEqual(result.calls, 3)


class Merging(unittest.TestCase):

    def merge(self, entity_merges, vocabulary=("Detector", "Instrument", "Sensor", "Spacecraft", "Craft")):
        labels = label.Labels(of={"entity": {}, "predicate": {}},
                              vocabulary={"entity": list(vocabulary), "predicate": ["ABOARD"]})
        with Scripted({"LABELS": {"merges": entity_merges}}) as calls:
            return merge.merge_labels(labels, texts(), calls)

    def test_chain_followed(self):
        m = self.merge([{"into": "Detector", "labels": ["Sensor"]}, {"into": "Instrument", "labels": ["Detector"]}])
        self.assertEqual(m.merged_into["entity"]["Sensor"], "Instrument")
        self.assertEqual(m.merged_into["entity"]["Detector"], "Instrument")
        self.assertEqual({(x["label"], x["into"]) for x in m.merges}, {("Sensor", "Instrument"), ("Detector", "Instrument")})

    def test_cycle_refused(self):
        m = self.merge([{"into": "Instrument", "labels": ["Sensor"]}, {"into": "Sensor", "labels": ["Instrument"]}])
        self.assertEqual(m.merged_into["entity"]["Sensor"], "Instrument")
        self.assertEqual(m.merged_into["entity"]["Instrument"], "Instrument")
        self.assertEqual(m.merge_issues["entity"]["cycle"], ["Instrument"])

    def test_long_cycle_refused(self):
        m = self.merge([{"into": "Detector", "labels": ["Sensor"]}, {"into": "Instrument", "labels": ["Detector"]},
                        {"into": "Sensor", "labels": ["Instrument"]}])
        finals = set(m.merged_into["entity"][x] for x in ("Sensor", "Detector", "Instrument"))
        self.assertEqual(finals, {"Instrument"})
        self.assertEqual(m.merge_issues["entity"]["cycle"], ["Instrument"])

    def test_invalid_items(self):
        m = self.merge([{"into": "Gadget", "labels": ["Sensor"]},                    # into not a label
                        {"into": "Instrument", "labels": ["Sensor", "Widget", "Instrument"]},
                        {"into": "Spacecraft", "labels": ["Sensor"]},                # merged twice: the first stands
                        "not a dict", {"into": "Craft", "labels": "Spacecraft"}])
        issues = m.merge_issues["entity"]
        self.assertEqual((issues["into_not_a_label"], issues["not_sent"], issues["merged_twice"]), (["Gadget"], ["Widget"], ["Sensor"]))
        self.assertEqual(m.merged_into["entity"]["Sensor"], "Instrument")
        self.assertEqual(m.merged_into["entity"]["Spacecraft"], "Spacecraft")

    def test_titles_count_like_stage_5(self):
        """A label used only for titles (WebTool here) reaches the model with its texts and its titles as examples."""
        triples = texts(("t1", "m1", "Giovanni", "WebTool", [("MODIS", "is aboard", "Aqua")]),
                        ("t2", "m1", "Worldview", "WebTool", []))
        labels = label.Labels(of={"entity": {"MODIS": "Instrument", "Aqua": "Spacecraft", "Giovanni": "WebTool",
                                             "Worldview": "WebTool"}, "predicate": {"is aboard": "ABOARD"}},
                              vocabulary={"entity": ["Instrument", "Spacecraft", "WebTool"], "predicate": ["ABOARD"]})
        model = Scripted({"merges": {"merges": []}})
        with model as calls:
            merge.merge_labels(labels, triples, calls)
        prompt = next(p for p in model.prompts if "WebTool" in p)
        listing = json.loads(prompt[prompt.rindex("LABELS:") + len("LABELS:"):])
        web = next(e for e in listing if e["label"] == "WebTool")
        self.assertEqual((web["texts"], sorted(web["examples"])), (2, ["Giovanni", "Worldview"]))

    def test_one_label_no_call(self):
        labels = label.Labels(of={"entity": {}, "predicate": {}}, vocabulary={"entity": ["A"], "predicate": ["P"]})
        with Scripted({}) as calls:
            m = merge.merge_labels(labels, texts(), calls)
        self.assertEqual((m.merge_calls, m.merged_into["entity"]), (0, {"A": "A"}))

    def test_too_many(self):
        labels = label.Labels(of={"entity": {}, "predicate": {}},
                              vocabulary={"entity": [f"L{i}" for i in range(merge.MAX_LABELS_ONE_CALL + 1)], "predicate": []})
        with Scripted({}) as calls, self.assertRaisesRegex(ValueError, "more than one call takes"):
            merge.merge_labels(labels, texts(), calls)


def labels_for(entity, predicate, merged=None):
    """Labels as stage 4 leaves them: merged, then folded by spelling (merge.fold_spellings)."""
    labels = label.Labels(of={"entity": entity, "predicate": predicate},
                          merged_into={"entity": merged or {}, "predicate": {}})
    merge.fold_spellings(labels)
    return labels


NO_SPLITS = split.Splits()


class Counting(unittest.TestCase):

    def setUp(self):
        self.triples = texts(
            ("t1", "m1", "MODIS L2", "Dataset", [("MODIS", "is aboard", "Aqua"), ("MODIS", "is aboard", "Aqua"),
                                                 ("AIRS", "flies on", "Aqua"), ("OMI", "is aboard", "Aura")]),
            ("t2", "m2", "AIRS L1", "Dataset", [("AIRS", "is aboard", "Terra"), ("CERES", "is aboard", "Mystery")]),
            ("t3", "m2", "Plain", "", []))
        entity = {"MODIS": "Instrument", "AIRS": "instrument", "CERES": "Sensor", "Aqua": "Spacecraft", "Aura": "Spacecraft", "OMI": "Instrument",
                  "Terra": "Space craft", "MODIS L2": "Dataset", "AIRS L1": "Dataset"}
        predicate = {"is aboard": "ABOARD", "flies on": "ABOARD"}
        self.labels = labels_for(entity, predicate, merged={"Sensor": "Instrument"})
        self.c = count.count_support(self.triples, self.labels, NO_SPLITS)

    def entry(self, kind, name):
        return next(e for e in getattr(self.c, kind) if e.get("component_class", e.get("pattern")) == name)

    def test_support_is_texts(self):
        inst = self.entry("entity_classes", "Instrument")
        self.assertEqual((inst["support"], inst["texts"], inst["maintainers"]), (2, ["t1", "t2"], ["m1", "m2"]))
        self.assertEqual(self.entry("predicates", "ABOARD")["support"], 2)
        self.assertEqual(self.entry("patterns", ["Instrument", "ABOARD", "Spacecraft"])["support"], 2)

    def test_spellings_folded(self):
        names = {e["component_class"] for e in self.c.entity_classes}
        self.assertEqual(names, {"Instrument", "Spacecraft", "Dataset"})
        folds = {f["into"]: f["folded"] for f in self.labels.spelling_folds}           # stage 4 folds them
        self.assertEqual(folds["Instrument"], ["Instrument", "instrument"])
        self.assertEqual(folds["Spacecraft"], ["Space craft", "Spacecraft"])        # the most frequent spelling

    def test_unlabeled_costs_only_its_own(self):
        self.assertEqual(self.c.unlabeled_slots, {"object": 1})              # Mystery
        self.assertEqual(len(self.c.patterns), 1)

    def test_titles_count(self):
        ds = self.entry("entity_classes", "Dataset")
        self.assertEqual((ds["support"], ds["examples"]), (2, ["MODIS L2", "AIRS L1"]))
        self.assertEqual((self.c.texts_with_triple_instances, self.c.texts_with_describes_class), (2, 2))

    def test_split_reassigns_by_object_class(self):
        """Stage 5's kept split gives a triple instance the new predicate only when its object has an entity class the
        split took; others keep the predicate; an unlabeled object never moves."""
        splits = split.Splits(into={"ABOARD": {"Spacecraft": "ABOARD_SPACECRAFT"}})
        c = count.count_support(self.triples, self.labels, splits)
        patterns = {tuple(p["pattern"]): p["support"] for p in c.patterns}
        self.assertEqual(patterns, {("Instrument", "ABOARD_SPACECRAFT", "Spacecraft"): 2})
        predicates = {p["component_class"]: p["support"] for p in c.predicates}
        self.assertEqual(predicates, {"ABOARD_SPACECRAFT": 2, "ABOARD": 1})          # t2: CERES -- Mystery
        self.assertEqual(c.pattern_of["t2"], [("Instrument", "ABOARD_SPACECRAFT", "Spacecraft"), None])

    def test_predicate_examples_are_facts(self):
        """A predicate's examples are the triple instances that most often state it: they show its subject and
        object, which its definition must say."""
        self.assertEqual(self.entry("predicates", "ABOARD")["examples"][0], "MODIS -- is aboard -- Aqua")
        self.assertIn("AIRS -- flies on -- Aqua", self.entry("predicates", "ABOARD")["examples"])


class Splitting(unittest.TestCase):
    """Stage 5's code checks, each with a near miss that passes, and the cap."""

    def setUp(self):
        # SOURCED_FROM reaches Mission (2 texts), Spacecraft (1) and Instrument (1); ABOARD only Spacecraft
        self.triples = texts(("t1", "m1", "T1", "", [("data", "came from", "Apollo 11"), ("MODIS", "is aboard", "Aqua")]),
                             ("t2", "m1", "T2", "", [("images", "came from", "Cassini"), ("x", "came from", "Apollo 12")]),
                             ("t3", "m2", "T3", "", [("y", "came from", "MODIS")]))
        self.labels = labels_for({"data": "Data", "images": "Data", "x": "Data", "y": "Data", "MODIS": "Instrument",
                                  "Aqua": "Spacecraft", "Apollo 11": "Mission", "Apollo 12": "Mission",
                                  "Cassini": "Spacecraft"},
                                 {"came from": "SOURCED_FROM", "is aboard": "ABOARD"})
        self.found = split.object_classes(self.triples, self.labels)
        self.predicates = set(self.labels.final["predicate"].values())

    def check(self, *items):
        passed, rejected = split.check([{"splits": list(items)}], self.found, self.predicates)
        return passed, [r["why"].split(":")[0] for r in rejected]

    def test_found_and_sent(self):
        self.assertEqual({p: set(ocs) for p, ocs in self.found.items()},
                         {"SOURCED_FROM": {"Mission", "Spacecraft", "Instrument"}, "ABOARD": {"Spacecraft"}})

    def test_each_check_and_its_near_miss(self):
        ok = {"predicate": "SOURCED_FROM", "into": "FROM_MISSION", "object_classes": ["Mission"]}
        cases = [
            ("not an object", ["SOURCED_FROM"], split.NOT_AN_OBJECT),
            ("predicate not sent (ABOARD has one object entity class)", {**ok, "predicate": "ABOARD"}, split.NOT_SENT),
            ("no name", {**ok, "into": "  "}, split.NO_NAME),
            ("an existing name, spelled otherwise", {**ok, "into": "aboard"}, split.NAME_TAKEN),
            ("its own name", {**ok, "into": "Sourced From"}, split.NAME_TAKEN),
            ("no object entity class", {**ok, "object_classes": []}, split.NO_CLASSES),
            ("not the predicate's", {**ok, "object_classes": ["Organization"]}, split.NOT_AN_OBJECT_CLASS),
            ("every object entity class", {**ok, "object_classes": ["Mission", "Spacecraft", "Instrument"]},
             split.EVERY_CLASS),
        ]
        for what, item, why in cases:
            with self.subTest(what):
                self.assertEqual(self.check(item)[1], [why])
        # near misses that pass: the predicate and the entity class in another spelling, read as the ones sent
        passed, rejected = self.check({"predicate": "sourced_from", "into": "FROM_MISSION", "object_classes": ["mission"]})
        self.assertEqual((passed, rejected), ([{"predicate": "SOURCED_FROM", "into": "FROM_MISSION",
                                               "object_classes": ["Mission"]}], []))

    def test_first_split_stands(self):
        passed, rejected = self.check(
            {"predicate": "SOURCED_FROM", "into": "FROM_MISSION", "object_classes": ["Mission"]},
            {"predicate": "SOURCED_FROM", "into": "FROM_CRAFT", "object_classes": ["Spacecraft", "Mission"]},  # Mission taken
            {"predicate": "SOURCED_FROM", "into": "from_mission", "object_classes": ["Instrument"]},           # name taken
            {"predicate": "SOURCED_FROM", "into": "FROM_SPACECRAFT", "object_classes": ["Spacecraft"]})
        self.assertEqual([p["into"] for p in passed], ["FROM_MISSION", "FROM_SPACECRAFT"])
        self.assertEqual(rejected, [split.CLASS_TWICE, split.NAME_TWICE])

    def test_added_counts_a_predicate_split_away(self):
        ocs = {"SOURCED_FROM": {"Mission", "Spacecraft", "Instrument"}}
        one = {"predicate": "SOURCED_FROM", "object_classes": ["Mission"]}
        rest = {"predicate": "SOURCED_FROM", "object_classes": ["Spacecraft", "Instrument"]}
        self.assertEqual(split.added_by([one], ocs), 1)
        self.assertEqual(split.added_by([one, rest], ocs), 1)       # every object entity class taken: SOURCED_FROM is gone

    def test_cap_keeps_most_supported_first(self):
        passed = [{"predicate": "SOURCED_FROM", "into": "FROM_SPACECRAFT", "object_classes": ["Spacecraft"], "texts": 1},
                  {"predicate": "SOURCED_FROM", "into": "FROM_MISSION", "object_classes": ["Mission"], "texts": 2}]
        kept, dropped = split.capped(passed, self.found, 1)
        self.assertEqual(([s["into"] for s in kept], [s["into"] for s in dropped]), (["FROM_MISSION"], ["FROM_SPACECRAFT"]))
        kept, dropped = split.capped(passed, self.found, 2)                         # near miss: room for both
        self.assertEqual((len(kept), dropped), (2, []))
        # splits that take every object entity class add one predicate less, so a cap of 1 keeps both halves of a full split
        full = passed[1:] + [{"predicate": "SOURCED_FROM", "into": "FROM_OTHER", "object_classes": ["Spacecraft",
                                                                                                   "Instrument"], "texts": 2}]
        kept, dropped = split.capped(full, self.found, 1)
        self.assertEqual((len(kept), dropped), (2, []))

    def test_stage_end_to_end(self):
        """The model's reply, checked and capped; max_new_predicates 0 asks nothing."""
        reply = {"splits": [{"predicate": "SOURCED_FROM", "into": "FROM_MISSION", "object_classes": ["Mission"]},
                            {"predicate": "SOURCED_FROM", "into": "FROM_SPACECRAFT", "object_classes": ["Spacecraft"]},
                            {"predicate": "SOURCED_FROM", "into": "FROM_GADGET", "object_classes": ["Gadget"]}]}
        model = Scripted({"splits": reply})
        with model as calls:
            s = split.split_predicates(self.triples, self.labels, {"max_new_predicates": 1}, calls)
        self.assertEqual([e["predicate"] for e in s.sent], ["SOURCED_FROM"])
        self.assertEqual(s.into, {"SOURCED_FROM": {"Mission": "FROM_MISSION"}})
        self.assertEqual(([d["into"] for d in s.dropped], [r["into"] for r in s.rejected], s.added, s.calls),
                         (["FROM_SPACECRAFT"], ["FROM_GADGET"], 1, 1))
        self.assertEqual(s.kept[0]["texts"], 2)
        with Scripted({}) as calls:
            none = split.split_predicates(self.triples, self.labels, {"max_new_predicates": 0}, calls)
        self.assertEqual((none.calls, none.into, none.sent), (0, {}, []))


class Tallying(unittest.TestCase):
    """The statistics: what each check removed, and the texts it removed wholly."""

    def test_removed_by_checks(self):
        t = lambda i, verified, unverified, malformed=0, duplicates=0: {                     # noqa: E731
            "id": i, "stratum": "S", "malformed": malformed, "duplicates": duplicates,
            "triple_instances": [{"n": n} for n in range(verified)], "unverified": [{}] * unverified}
        triples = SimpleNamespace(texts=[t("all malformed", 0, 0, malformed=2), t("all unverified", 0, 3),
                                         t("copies", 1, 0, duplicates=2), t("none listed", 0, 0),
                                         t("no pattern", 1, 0), t("deferred", 2, 1), t("kept", 1, 0)])
        counts = SimpleNamespace(pattern_of={"copies": [("A", "P", "B")], "no pattern": [None],
                                             "deferred": [("A", "Q", "B"), None], "kept": [("A", "P", "B")]})
        schema = SimpleNamespace(patterns=[{"pattern": ["A", "P", "B"]}])
        rows = {r["check"]: (r["removed"], [x["id"] for x in r["texts_wholly"]])
                for r in tally.removed_by_checks(triples, counts, schema)}
        self.assertEqual(rows, {tally.NOT_A_TRIPLE: (2, ["all malformed"]), tally.STATED_TWICE: (2, []),
                                tally.UNVERIFIED: (4, ["all unverified"]), tally.NO_PATTERN: (2, ["no pattern"]),
                                tally.NOT_IN_SCHEMA: (1, ["deferred"])})
        empty = tally.no_triple_instances(triples)
        self.assertEqual([x["id"] for x in empty["listed"]], ["all malformed", "none listed"])
        self.assertEqual(len(empty["verified"]), 3)

    def test_per_stratum_keeps_empty_strata(self):
        triples = SimpleNamespace(texts=[{"stratum": "A", "triple_instances": [1, 2]}, {"stratum": "A", "triple_instances": []}])
        self.assertEqual(tally.per_stratum(triples, ["A", "B"]), {"A": [2, 0], "B": []})
        self.assertEqual(tally.stats([2, 0])["sd"], round(2 ** 0.5, 2))


class Checking(unittest.TestCase):

    def test_ground_truth_problems_reach_the_warnings(self):
        """The ground truth's own problems (here a file missing columns), read when comparing with the ground truth
        schema, are kept for the report's warnings, and left out of the comparison written to the evidence file."""
        from common.step import load_moves
        from support import ROOT
        moves = load_moves("040_induce_schema")
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp)
        (tmp / "batch_000.csv").write_text("id,subject\nr1,MODIS\n", encoding="utf-8")
        (tmp / "splits.json").write_text('{"ground_truth_candidates": {"records": []}}', encoding="utf-8")
        schema = check.Schema()
        comparison = moves.compare_with_ground_truth_schema(
            {"ground_truth_schema": ROOT / "annotations" / "ground_truth_schema.txt",
             "ground_truth": tmp / "batch_*.csv", "splits": tmp / "splits.json"}, schema)
        self.assertEqual(len(comparison["ground_truth_problems"]), 1)
        self.assertIn("lacks the column(s)", comparison["ground_truth_problems"][0])

    def test_check_schema(self):
        e = lambda name, support, maint=("m1", "m2"): {"component_class": name, "support": support,   # noqa: E731
                                                        "texts": [f"t{i}" for i in range(support)],
                                                        "maintainers": list(maint), "examples": ["x"]}
        counts = SimpleNamespace(
            entity_classes=[e("Instrument", 3), e("Spacecraft", 2, ("m1",)), e("Mission", 2), e("Rare", 1)],
            predicates=[e("ABOARD", 3), e("PART_OF", 2)],
            patterns=[{"pattern": ["Instrument", "ABOARD", "Spacecraft"], "support": 2, "maintainers": ["m1"], "texts": ["t0", "t1"]},
                      {"pattern": ["Instrument", "ABOARD", "Mission"], "support": 2, "maintainers": ["m1"], "texts": ["t0", "t1"]},
                      {"pattern": ["Rare", "PART_OF", "Spacecraft"], "support": 1, "maintainers": ["m1"], "texts": ["t0"]}])
        definitions = SimpleNamespace(of={"entity_classes": {"Instrument": "A device.", "Spacecraft": "A craft."},
                                          "predicates": {"ABOARD": "Is carried on."}},
                                      too_vague={"entity_classes": {"Mission": "too broad"}})
        s = check.check_schema(counts, definitions, {"min_support": 2})
        self.assertEqual([x["component_class"] for x in s.entity_classes], ["Instrument", "Spacecraft"])
        self.assertEqual([x["component_class"] for x in s.predicates], ["ABOARD", "PART_OF"])
        self.assertEqual(s.predicates[1]["definition"], check.MISSING_DEFINITION)
        self.assertEqual(s.missing_definitions, [{"kind": "predicate", "component_class": "PART_OF"}])
        self.assertEqual(s.single_maintainer, [{"kind": "entity class", "component_class": "Spacecraft"}])
        self.assertEqual([x["pattern"] for x in s.patterns], [["Instrument", "ABOARD", "Spacecraft"]])
        deferred = {d["schema_entry"]: d["reason"] for d in s.deferred}
        self.assertEqual(deferred, {"Mission": "too vague: too broad", "Rare": "support 1 < min_support 2",
                                    "Instrument ABOARD Mission": "Mission is not in the schema",
                                    "Rare PART_OF Spacecraft": "support 1 < min_support 2"})
        self.assertEqual({d["entry_type"] for d in s.deferred}, {"entity class", "pattern"})
        self.assertTrue(all(x["_origin"] for x in s.entity_classes + s.predicates + s.patterns))
        json.dumps(s.__dict__)                                                # the schema is writable as JSON


class Saturation(unittest.TestCase):
    """The curve is the exact average over every reading order; the breadth table counts maintainers."""

    @staticmethod
    def counts(found_in: dict, maintainers: dict | None = None):
        rows = [{"support": len(ts), "texts": sorted(ts), "maintainers": sorted((maintainers or {}).get(k, {"m"}))}
                for k, ts in found_in.items()]
        return count.Counts(entity_classes=rows, predicates=[], patterns=[])

    def test_exact_average_over_every_order(self):
        import itertools
        found_in = {"Instrument": {"T1", "T2", "T3"}, "Spacecraft": {"T2", "T4"}, "Mission": {"T3"}}
        texts, s = ["T1", "T2", "T3", "T4"], 2
        for k in range(1, 5):                           # brute force: every order, the schema after k texts
            sizes = [sum(len(ts & set(order[:k])) >= s for ts in found_in.values())
                     for order in itertools.permutations(texts)]
            exact = sum(saturation.reaches(4, len(ts), k, s) for ts in found_in.values())
            self.assertAlmostEqual(exact, sum(sizes) / len(sizes), msg=k)

    def test_curve_and_last_texts(self):
        c = self.counts({f"E{i}": {f"T{j}" for j in range(60)} for i in range(5)})   # 5 entries in every text
        sat = saturation.curve(c, 60, 2)
        self.assertEqual(sat["texts"], [25, 50, 60])
        self.assertEqual([round(v, 6) for v in sat["entity classes"]], [5, 5, 5])
        self.assertAlmostEqual(sat["added_by_last"]["entity classes"], 0)        # flat: the last 25 add nothing
        rare = self.counts({"Rare": {"T1", "T2"}})                               # found in 2 of 60: still rising
        self.assertGreater(saturation.curve(rare, 60, 2)["added_by_last"]["entity classes"], 0.5)
        self.assertEqual(saturation.curve(self.counts({}), 0, 2)["texts"], [])

    def test_breadth(self):
        c = self.counts({"A": {"T1", "T2"}, "B": {"T1", "T2", "T3"}, "C": {"T1"}},
                        {"A": {"PDS"}, "B": {"PDS", "NSIDC", "HEASARC"}, "C": {"PDS"}})
        self.assertEqual(saturation.breadth(c, 2)["entity classes"], {"1": 1, "2": 0, "3 or more": 1})  # C below 2
        lines = saturation.report_lines(saturation.curve(c, 3, 2), saturation.breadth(c, 2), 3, 2)
        self.assertIn("### Saturation", lines)


class TracingInduction(unittest.TestCase):
    """helpers/audit.py --induction (common/common_helpers/induction_trace.py), on files laid out as
    moves.results writes them: a label merged and then spelling-folded, a deferred predicate, an unlabeled
    predicate instance, an unverified triple instance, the --limit cap, a missing file."""

    def setUp(self):
        self.folder = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.folder)
        ti = lambda s, p, o, src: {"subject": s, "predicate": p, "object": o, "source_text": src}
        evidence = {
            "made": {"run_id": "040_induce_schema_2026-10-20_1000"},
            "texts": [
                {"id": "R1", "maintainer": "PDS", "title": "T1", "describes_class": "Dataset",
                 "triple_instances": [ti("samples", "came from", "Apollo 11", "samples from the Apollo 11 mission"),
                                      ti("MODIS", "is aboard", "Aqua", "MODIS aboard Aqua")],
                 "unverified": [{**ti("data", "taken from", "Viking", "not in the text"), "errors": ["source_text"]}]},
                {"id": "R2", "maintainer": "NSIDC", "title": "T2", "describes_class": "Dataset",
                 "triple_instances": [ti("images", "originate from", "Cassini", "images from the Cassini spacecraft"),
                                      ti("grid", "is gridded on", "EASE", "gridded on EASE")]}],
            "labels": {"entity": {}, "predicate": {"came from": "FROM", "is aboard": "ABOARD",
                                                   "originate from": "ORIGINATES_FROM"}},
            "unlabeled": {"entity": [], "predicate": ["is gridded on"]},
            "refused": {"labels": {"entity": [], "predicate": []}, "definitions": []},
            "merges": [{"kind": "predicate", "label": "ORIGINATES_FROM", "into": "From", "component_instances": 1,
                        "texts": 1},
                       {"kind": "entity class", "label": "FROM", "into": "Nonsense", "component_instances": 1,
                        "texts": 1}],
            "spelling_folds": [{"kind": "predicate", "into": "FROM", "folded": ["FROM", "From"]}],
            "counts": {"predicates": [{"component_class": "FROM", "support": 2, "maintainers": ["NSIDC", "PDS"]},
                                      {"component_class": "ABOARD", "support": 1, "maintainers": ["PDS"]}]}}
        schema = {"entity_classes": [], "patterns": [],
                  "predicates": [{"component_class": "ABOARD", "support": 1, "maintainers": ["PDS"]}],
                  "deferred": [{"entry_type": "predicate", "schema_entry": "FROM", "support": 2,
                                "reason": "too vague: says nothing about what kind of origin"}]}
        for name, data in (("induction_evidence.json", evidence), ("the_schema.json", schema)):
            (self.folder / name).write_text(json.dumps(data), encoding="utf-8")

    def trace(self, regex, limit=30):
        from common.induction_trace import trace_induction
        lines = []
        n = trace_induction(regex, limit=limit, folder=self.folder, out=lines.append)
        return n, "\n".join(lines)

    def test_chain_and_status(self):
        n, out = self.trace("from|mission")
        self.assertEqual(n, 3)                              # 2 verified, 1 unverified; "is aboard" doesn't match
        self.assertIn("label ORIGINATES_FROM -> merged into From (stage 4) -> spelling fold to FROM (stage 4) = "
                      "FROM: DEFERRED (too vague: says nothing about what kind of origin); support 2, 2 maintainer(s)",
                      out)
        self.assertIn("label FROM = FROM: DEFERRED", out)    # an entity class merge of the same word isn't used
        self.assertIn("UNVERIFIED (source_text)", out)
        self.assertNotIn("MODIS", out)
        self.assertIn("     2  FROM: DEFERRED", out)
        self.assertIn("     1  (unverified): left out", out)

    def test_split_shown(self):
        """A predicate split by its object's entity class (stage 5) shows the split in the chain; a triple instance
        whose object has another entity class (near miss) doesn't."""
        path = self.folder / "induction_evidence.json"
        evidence = json.loads(path.read_text(encoding="utf-8"))
        evidence["labels"]["entity"] = {"Apollo 11": "Mission", "Cassini": "Craft"}
        evidence["spelling_folds"].append({"kind": "entity class", "into": "MISSION", "folded": ["MISSION", "Mission"]})
        evidence["splits"] = {"into": {"FROM": {"MISSION": "FROM_MISSION"}}}
        path.write_text(json.dumps(evidence), encoding="utf-8")
        _, out = self.trace("Apollo|Cassini")
        self.assertIn("label FROM -> split to FROM_MISSION by its object's entity class, MISSION (stage 5) = "
                      "FROM_MISSION", out)                       # Mission folded to MISSION before the split is read
        cassini = out.split("Cassini", 1)[1].split("\n")[2]
        self.assertNotIn("split", cassini)

    def test_matches_the_label_and_unlabeled(self):
        n, out = self.trace("^ABOARD$")                      # the label, not the words
        self.assertEqual(n, 1)
        self.assertIn("label ABOARD = ABOARD: IN THE SCHEMA; support 1, 1 maintainer(s)", out)
        n, out = self.trace("gridded")
        self.assertIn("no label: the model left it unlabeled, even asked twice: counts toward no predicate", out)

    def test_limit_and_nothing(self):
        n, out = self.trace(".", limit=1)
        self.assertEqual(n, 5)
        self.assertIn("... 4 more triple instance(s) not shown (--limit 5 shows all)", out)
        self.assertIn("more predicate(s) not shown", out)
        self.assertEqual(self.trace("zzz")[0], 0)

    def test_missing_file_names_the_step(self):
        (self.folder / "the_schema.json").unlink()
        with self.assertRaises(FileNotFoundError) as e:
            self.trace(".")
        self.assertIn("py 040_induce_schema/run.py", str(e.exception))


if __name__ == "__main__":
    unittest.main()
