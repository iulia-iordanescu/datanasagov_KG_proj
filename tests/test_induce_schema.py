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
                                        "extra": "Ignored"}, "entity")
        self.assertEqual(labels, {"MODIS": "Instrument", "Aqua  craft": "Spacecraft"})
        self.assertEqual(missing, ["Terra", "Aura"])
        self.assertEqual(label._match(["a"], "not a dict", "entity"), ({}, ["a"]))

    def test_label_must_be_one_word(self):
        """A label must be one word of the format its prompt asks for (label.well_formed): a phrase, an arrow or a
        hyphen is not taken, and recorded; near misses that are taken: another case (stage 4 folds it), digits, an
        underscore in a predicate label, spaces at the ends."""
        for kind, good, bad in (
                ("entity", ["Instrument", "instrument", "Level2Product", " PhysicalQuantity "],
                 ["Space craft", "Data -> Mission", "Level-2", "Physical_Quantity", "2Level", "", 7, None]),
                ("predicate", ["ABOARD", "MEASURED_BY", "aboard", "LEVEL2_OF", " MEASURED_BY "],
                 ["MEASURED BY", "MEASURED__BY", "_ABOARD", "ABOARD_", "MEASURED-BY", "A -> B", "", ["ABOARD"]])):
            for value in good:
                with self.subTest(kind=kind, value=value):
                    self.assertTrue(label.well_formed(kind, value))
            for value in bad:
                with self.subTest(kind=kind, value=value):
                    self.assertFalse(label.well_formed(kind, value))
        from common import dropped
        dropped.reset()
        self.addCleanup(dropped.reset)
        triples = texts(("t1", "m", "T1", "", [("MODIS", "is aboard", "Aqua")]))
        replies = iter([{"labels": {"MODIS": "Instrument", "Aqua": "Space craft"}},       # a phrase: asked again
                        {"labels": {"Aqua": "Spacecraft"}},
                        {"labels": {"is aboard": "IS ABOARD"}}, {"labels": {"is aboard": "ABOARD"}}])
        prompts = []
        with Scripted({}) as calls:
            llm.call_llm_json = lambda prompt, **kw: prompts.append(prompt) or next(replies)
            result = label.label_component_instances(triples, calls)
        self.assertTrue(prompts[1].endswith("- \"Aqua\": its label, \"Space craft\", isn't one CamelCase word (letters "
                                            "and digits only), the format asked for"), prompts[1][-200:])
        self.assertNotIn("Your last reply", prompts[0])
        self.assertEqual((result.of["entity"]["Aqua"], result.of["predicate"]), ("Spacecraft", {"is aboard": "ABOARD"}))
        # the second ask of a batch of one isn't the first prompt again, which the cache would answer: 4 calls made
        self.assertEqual(result.calls, 4)
        reasons = [e["reason"] for e in dropped.DISCARDS if e["stage"] == label.STAGE]
        self.assertEqual(sum("isn't one CamelCase word" in r for r in reasons), 1, reasons)
        self.assertEqual(sum("isn't one UPPER_SNAKE_CASE word" in r for r in reasons), 1, reasons)

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
                        "not a dict", {"into": "Craft", "labels": "Spacecraft"},
                        {"into": ["Instrument"], "labels": ["Detector"]},           # into isn't text: no label
                        {"into": {"x": 1}, "labels": ["Detector"]},
                        {"into": "Instrument", "labels": [{"x": 1}, ["Detector"], 7, "Detector"]}])  # labels not text
        issues = m.merge_issues["entity"]
        self.assertEqual((issues["into_not_a_label"], issues["not_sent"], issues["merged_twice"]),
                         (["Gadget", ["Instrument"], {"x": 1}], ["Widget", {"x": 1}, ["Detector"], 7], ["Sensor"]))
        self.assertEqual(m.merged_into["entity"]["Sensor"], "Instrument")
        self.assertEqual(m.merged_into["entity"]["Spacecraft"], "Spacecraft")
        self.assertEqual(m.merged_into["entity"]["Detector"], "Instrument")      # near miss: the text label is merged

    def scripted_failures(self, *outcomes):
        """merge.merge_labels over entity labels only, each call's outcome in turn: an exception to raise, or a
        reply; (labels, the prompts sent, the discards)."""
        from common import dropped
        dropped.reset()
        self.addCleanup(dropped.reset)
        triples = texts(("t1", "m1", "T1", "", [("MODIS", "is aboard", "Aqua"), ("CERES", "is aboard", "Terra")]))
        labels = label.Labels(of={"entity": {"MODIS": "Instrument", "CERES": "Sensor", "Aqua": "Spacecraft",
                                             "Terra": "Spacecraft"}, "predicate": {"is aboard": "ABOARD"}},
                              vocabulary={"entity": ["Instrument", "Sensor", "Spacecraft"], "predicate": ["ABOARD"]})
        prompts, left = [], list(outcomes)

        def answer(prompt, **kw):
            prompts.append(prompt)
            got = left.pop(0)
            if isinstance(got, Exception):
                raise got
            return got
        with Scripted({}) as calls:
            llm.call_llm_json = answer
            m = merge.merge_labels(labels, triples, calls)
        return m, prompts, list(dropped.DISCARDS)

    def test_refused_asked_again_without_examples(self):
        """A merge call refused (or cut off, or twice of the wrong shape) is asked once more with the examples left
        out; its answer is used, and the fallback is kept for the report."""
        for failure in (llm.Refused("content filter"), llm.CutOff("cut off"), llm.BadReply("not JSON twice")):
            with self.subTest(failure=type(failure).__name__):
                m, prompts, _ = self.scripted_failures(failure, {"merges": [{"into": "Instrument",
                                                                             "labels": ["Sensor"]}]})
                first = json.loads(prompts[0][prompts[0].rindex("LABELS:") + len("LABELS:"):])
                again = json.loads(prompts[1][prompts[1].rindex("LABELS:") + len("LABELS:"):])
                self.assertTrue(all("examples" in e for e in first))
                self.assertEqual(again, [{"label": e["label"], "texts": e["texts"]} for e in first])
                self.assertEqual(m.merged_into["entity"]["Sensor"], "Instrument")
                self.assertEqual(m.merge_fallback["entity"], {"kind": "entity class", "labels": 3,
                                                              "first": str(failure), "without_examples": "answered"})
                self.assertIsNone(m.merge_fallback.get("predicate"))         # one label: no call

    def test_refused_twice_merges_nothing(self):
        """Refused again without examples: no label of the call is merged, the call is recorded, the step goes on;
        near miss: a failure that isn't a refusal, a cut-off or a bad reply still stops the step."""
        m, prompts, discards = self.scripted_failures(llm.Refused("filter"), llm.Refused("filter again"))
        self.assertEqual(len(prompts), 2)
        self.assertEqual(m.merged_into["entity"], {"Instrument": "Instrument", "Sensor": "Sensor",
                                                   "Spacecraft": "Spacecraft"})
        self.assertEqual(m.merge_fallback["entity"]["without_examples"], "filter again")
        call = [e for e in discards if e["item_type"] == "merge call"]
        self.assertEqual(len(call), 1)
        self.assertEqual(call[0]["item"], {"kind": "entity class", "labels": ["Instrument", "Sensor", "Spacecraft"]})
        self.assertIn("filter; asked again: filter again", call[0]["reason"])
        with self.assertRaises(llm.ApiError):
            self.scripted_failures(llm.ApiError("HTTP 401: key not valid"))

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

    def test_predicate_listing_shows_entity_classes(self):
        """Stage 4 shows each predicate label with up to EXAMPLES triple instances, each instance with its entity class
        as stage 4's own entity class merge left it (Sensor merged into Instrument first); an unlabeled instance is
        written without one; chosen by count.representative (a new text and maintainer first, then a new text, ties
        alphabetically)."""
        triples = texts(("t1", "m1", "T1", "", [("CERES", "is aboard", "Terra"), ("MODIS", "is aboard", "Aqua"),
                                                ("MODIS", "is aboard", "Aqua")]),
                        ("t2", "m1", "T2", "", [("OMI", "flies on", "Mystery"), ("AIRS", "is aboard", "Aqua")]))
        labels = label.Labels(of={"entity": {"CERES": "Sensor", "MODIS": "Instrument", "Terra": "Spacecraft",
                                             "Aqua": "Spacecraft", "OMI": "Instrument", "AIRS": "Instrument"},
                                  "predicate": {"is aboard": "ABOARD", "flies on": "FLIES_ON"}},
                              vocabulary={"entity": ["Sensor", "Instrument", "Spacecraft"],
                                          "predicate": ["ABOARD", "FLIES_ON"]})
        model = Scripted({"Below are the labels given to subject": {"merges": [{"into": "Instrument",
                                                                                "labels": ["Sensor"]}]},
                          "Below are the labels given to predicate": {"merges": []}})
        with model as calls:
            merge.merge_labels(labels, triples, calls)
        prompt = next(p for p in model.prompts if "FLIES_ON" in p)
        listing = {e["label"]: e for e in json.loads(prompt[prompt.rindex("LABELS:") + len("LABELS:"):])}
        self.assertEqual(listing["ABOARD"], {"label": "ABOARD", "texts": 2, "examples": [
            "AIRS (Instrument) -- is aboard -- Aqua (Spacecraft)", "CERES (Instrument) -- is aboard -- Terra (Spacecraft)",
            "MODIS (Instrument) -- is aboard -- Aqua (Spacecraft)"]})
        self.assertEqual(listing["FLIES_ON"]["examples"], ["OMI (Instrument) -- flies on -- Mystery"])
        entity_prompt = next(p for p in model.prompts if "Sensor" in p)
        self.assertIn('"CERES"', entity_prompt)                            # entity labels: their instances, as before

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
    """Labels as stage 4 leaves them: folded by spelling (merge.fold_spellings), then merged (merge.final_labels)."""
    labels = label.Labels(of={"entity": entity, "predicate": predicate},
                          merged_into={"entity": merged or {}, "predicate": {}})
    merge.fold_spellings(labels)
    merge.final_labels(labels)
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
        self.assertEqual((ds["support"], ds["examples"]), (2, ["AIRS L1", "MODIS L2"]))         # ties alphabetically
        self.assertEqual((self.c.texts_with_triple_instances, self.c.texts_with_describes_class), (2, 2))

    def test_split_reassigns_by_its_grouping(self):
        """Stage 5's kept split gives a triple instance the new predicate only when its pattern is in a group the split
        took; others keep the predicate; a triple instance with an unlabeled object never moves (CERES -- Mystery)."""
        splits = split.Splits(into={"ABOARD": {"by": "object", "to": {"Spacecraft": "ABOARD_SPACECRAFT"}}})
        c = count.count_support(self.triples, self.labels, splits)
        patterns = {tuple(p["pattern"]): p["support"] for p in c.patterns}
        self.assertEqual(patterns, {("Instrument", "ABOARD_SPACECRAFT", "Spacecraft"): 2})
        predicates = {p["component_class"]: p["support"] for p in c.predicates}
        self.assertEqual(predicates, {"ABOARD_SPACECRAFT": 2, "ABOARD": 1})          # t2: CERES -- Mystery
        self.assertEqual(c.pattern_of["t2"], [("Instrument", "ABOARD_SPACECRAFT", "Spacecraft"), None])

    def test_pins_counted_for_predicates_found(self):
        """Counting keeps stage 5's pin of each predicate it counts, and no pin of a predicate it doesn't."""
        splits = split.Splits(into={"ABOARD": {"by": "object", "to": {"Spacecraft": "ABOARD_SPACECRAFT"}}},
                              pinned={"ABOARD_SPACECRAFT": [("any", "Spacecraft")], "GONE": [("any", "X")]})
        c = count.count_support(self.triples, self.labels, splits)
        self.assertEqual(c.pinned, {"ABOARD_SPACECRAFT": [("any", "Spacecraft")]})

    def test_predicate_examples_are_facts(self):
        """A predicate's examples are triple instances that state it (count.representative): they show its subject and
        object, which its definition must say; its pattern found in the most texts gives the first, then each other
        group (here CERES's, whose object has no label) one, before the first gives a second."""
        self.assertEqual(self.entry("predicates", "ABOARD")["examples"],
                         ["AIRS -- flies on -- Aqua", "CERES -- is aboard -- Mystery", "AIRS -- is aboard -- Terra",
                          "MODIS -- is aboard -- Aqua", "OMI -- is aboard -- Aura"])


class Representative(unittest.TestCase):
    """count.representative: the examples of a schema entry, one per group (pattern) found in the most texts first,
    each from a new text and, where possible, a new maintainer; deterministic."""

    def test_near_duplicates_give_one_example(self):
        """Five near-duplicate texts of one maintainer repeat one wording in pattern A; pattern B has one text of
        another maintainer; pattern A has another wording in a text of a third maintainer. Then A gives its most
        supported wording, B its one, and A's second pick is the third maintainer's, not a near-duplicate."""
        dup = [("A", "granule -- from -- MODIS", f"d{i}", "m1") for i in range(5)]
        dup += [("A", "granule v2 -- from -- MODIS", f"d{i}", "m1") for i in range(5)]
        cands = dup + [("B", "map -- from -- Landsat", "x", "m2"), ("A", "scene -- from -- ASTER", "y", "m3")]
        self.assertEqual(count.representative(cands, 3), ["granule -- from -- MODIS", "map -- from -- Landsat",
                                                         "scene -- from -- ASTER"])
        self.assertEqual(count.representative(list(reversed(cands)), 3), count.representative(cands, 3))  # order-free
        # near miss: with room for more, the near-duplicate's other wording comes last (no new text is left)
        self.assertEqual(count.representative(cands, 5)[3:], ["granule v2 -- from -- MODIS"])

    def test_most_supported_groups_first_and_edges(self):
        cands = [("small", "s", "t1", "m1"), ("big", "b1", "t2", "m2"), ("big", "b2", "t3", "m2"),
                 ("mid", "m", "t4", "m3"), ("mid", "m", "t5", "m3")]
        self.assertEqual(count.representative(cands, 3), ["b1", "m", "s"])           # big (2 texts), mid (2), small
        self.assertEqual(count.representative(cands, 1), ["b1"])
        self.assertEqual(count.representative([], 5), [])
        self.assertEqual(count.representative(cands, 0), [])
        # within a group, a new maintainer first: g2's second pick is b2 (m4), not b1 (m1, already shown)
        cands = [("g1", "s", "t1", "m1"), ("g2", "b1", "t2", "m1"), ("g2", "b2", "t3", "m4"), ("g2", "b0", "t9", "m1")]
        self.assertEqual(count.representative(cands, 3), ["b0", "s", "b2"])


class SplitLookup(unittest.TestCase):
    """Splits.predicate: each grouping's group, a triple instance with a side unlabeled never moving (whatever the
    grouping), and merging again applied after the split."""

    def test_each_grouping(self):
        s = split.Splits(into={"P": {"by": "subject", "to": {"A": "P_A"}},
                               "Q": {"by": "object", "to": {"B": "Q_B"}},
                               "R": {"by": "pattern", "to": {"A -> B": "R_AB"}}},
                         final={"P_A": "P_A", "Q_B": "OTHER"})
        cases = [("P", "A", "C", "P_A"), ("P", "C", "A", "P"),             # subject: A as object doesn't count
                 ("Q", "C", "B", "OTHER"), ("Q", "B", "C", "Q"),           # object, then merged again into OTHER
                 ("R", "A", "B", "R_AB"), ("R", "B", "A", "R"), ("R", "A", "C", "R"),   # the pattern, not one side
                 ("P", None, "C", "P"), ("Q", "C", None, "Q"),             # an unlabeled side never moves
                 ("P", "A", None, "P"),                                    # ... even on the side not grouped by
                 (None, "A", "B", None), ("S", "A", "B", "S")]             # no label; a predicate not split
        for p, sc, oc, expected in cases:
            with self.subTest(p=p, sc=sc, oc=oc):
                self.assertEqual(s.predicate(p, sc, oc), expected)

    def test_pin_of_each_grouping(self):
        self.assertEqual([split.pin_of("subject", "A"), split.pin_of("object", "B"), split.pin_of("pattern", "A -> B")],
                         [("A", "any"), ("any", "B"), ("A", "B")])


class SplitFixture:
    """The triple instances and labels stage 5's tests share.

    SOURCED_FROM: one subject entity class (Data) and three object ones: Mission (t1, t2), Spacecraft (t2),
    Instrument (t3). MEASURES: two subject entity classes and two object ones, whose patterns cut across both:
    Instrument -> Variable (t1, t2), Instrument -> Image (t3), Spacecraft -> Variable (t3, t4), Spacecraft -> Image
    (t4). ABOARD: one pattern (not sent)."""

    def setUp(self):
        self.triples = texts(
            ("t1", "m1", "T1", "", [("data", "came from", "Apollo 11"), ("MODIS", "is aboard", "Aqua"),
                                    ("MODIS", "measures", "temperature")]),
            ("t2", "m1", "T2", "", [("images", "came from", "Cassini"), ("x", "came from", "Apollo 12"),
                                    ("AIRS", "measures", "humidity")]),
            ("t3", "m2", "T3", "", [("y", "came from", "MODIS"), ("AIRS", "measures", "scene"),
                                    ("Aqua", "measures", "temperature")]),
            ("t4", "m2", "T4", "", [("Terra", "measures", "humidity"), ("Terra", "measures", "mosaic")]))
        self.labels = labels_for({"data": "Data", "images": "Data", "x": "Data", "y": "Data", "MODIS": "Instrument",
                                  "AIRS": "Instrument", "Aqua": "Spacecraft", "Terra": "Spacecraft",
                                  "Apollo 11": "Mission", "Apollo 12": "Mission", "Cassini": "Spacecraft",
                                  "temperature": "Variable", "humidity": "Variable", "scene": "Image",
                                  "mosaic": "Image"},
                                 {"came from": "SOURCED_FROM", "is aboard": "ABOARD", "measures": "MEASURES"})
        self.found = split.patterns_of(self.triples, self.labels)
        self.predicates = set(self.labels.final["predicate"].values())

    def check(self, *items, min_texts=1):
        passed, rejected = split.check([{"splits": list(items)}], self.found, self.predicates, min_texts)
        return passed, [r["why"].split(":")[0] for r in rejected]

    def run_stage(self, splits, merges=(), cap=10, min_texts=1):
        """The stage with these replies: (Splits, the prompts sent)."""
        model = Scripted({'"splits": [': {"splits": list(splits)}, '"merges": [': {"merges": list(merges)}})
        with model as calls:
            s = split.split_predicates(self.triples, self.labels, {"max_new_predicates": cap,
                                                                   "min_split_texts": min_texts}, calls)
        return s, model.prompts



class Splitting(SplitFixture, unittest.TestCase):
    """Stage 5's code checks, each with a near miss that passes, and the cap."""

    def test_found_and_sent(self):
        self.assertEqual({p: set(pats) for p, pats in self.found.items()},
                         {"SOURCED_FROM": {("Data", "Mission"), ("Data", "Spacecraft"), ("Data", "Instrument")},
                          "ABOARD": {("Instrument", "Spacecraft")},
                          "MEASURES": {("Instrument", "Variable"), ("Instrument", "Image"), ("Spacecraft", "Variable"),
                                       ("Spacecraft", "Image")}})
        self.assertEqual({p for p, pats in self.found.items() if split.several(pats)}, {"SOURCED_FROM", "MEASURES"})
        groups = {g: sorted(e["texts"]) for g, e in split.groups(self.found["MEASURES"], "subject").items()}
        self.assertEqual(groups, {"Instrument": ["t1", "t2", "t3"], "Spacecraft": ["t3", "t4"]})

    def test_one_side_varies_is_sent(self):
        """A predicate with one subject entity class but several object ones is sent (near miss: one of each isn't),
        and so is one with several subject entity classes and one object entity class."""
        self.assertTrue(split.several({("Data", "Mission"): {}, ("Data", "Spacecraft"): {}}))
        self.assertTrue(split.several({("Data", "Mission"): {}, ("Image", "Mission"): {}}))
        self.assertFalse(split.several({("Data", "Mission"): {}}))
        self.assertFalse(split.several({}))                                 # no pattern at all

    def test_each_check_and_its_near_miss(self):
        ok = {"predicate": "SOURCED_FROM", "by": "object", "into": "FROM_MISSION", "takes": ["Mission"]}
        measures = {"predicate": "MEASURES", "by": "pattern", "into": "MEASURED", "takes": ["Instrument -> Variable"]}
        cases = [
            ("not an object", ["SOURCED_FROM"], split.NOT_AN_OBJECT),
            ("predicate not sent (ABOARD has one pattern)", {**ok, "predicate": "ABOARD"}, split.NOT_SENT),
            ("no name", {**ok, "into": "  "}, split.NO_NAME),
            ("an existing name, spelled otherwise", {**ok, "into": "aboard"}, split.NAME_TAKEN),
            ("its own name", {**ok, "into": "Sourced_From"}, split.NAME_TAKEN),
            ("a phrase", {**ok, "into": "Sourced From"}, split.NOT_ONE_WORD),
            ("an arrow", {**ok, "into": "Data -> Mission"}, split.NOT_ONE_WORD),
            ("a hyphen", {**ok, "into": "FROM-MISSION"}, split.NOT_ONE_WORD),
            ("not text", {**ok, "into": ["FROM_MISSION"]}, split.NO_NAME),
            ("no grouping", {**ok, "by": "verb"}, split.NO_GROUPING),
            ("grouping left out", {k: v for k, v in ok.items() if k != "by"}, split.NO_GROUPING),
            ("no group", {**ok, "takes": []}, split.NO_GROUPS),
            ("takes not a list", {**ok, "takes": "Mission"}, split.NO_GROUPS),
            ("only blank groups", {**ok, "takes": ["  ", ""]}, split.NO_GROUPS),
            ("a blank group beside a real one", {**ok, "takes": ["Mission", " "]}, split.NOT_ITS_GROUP),
            ("a group that isn't text", {**ok, "takes": ["Mission", 7]}, split.NOT_ITS_GROUP),
            ("not the predicate's", {**ok, "takes": ["Organization"]}, split.NOT_ITS_GROUP),
            ("the predicate's on the other side only", {**ok, "by": "subject", "takes": ["Mission"]},
             split.NOT_ITS_GROUP),
            ("a pattern it doesn't have", {**measures, "takes": ["Variable -> Instrument"]}, split.NOT_ITS_GROUP),
            ("a pattern not written as one", {**measures, "takes": ["Instrument Variable"]}, split.NOT_ITS_GROUP),
            ("an entity class where a pattern is asked", {**measures, "takes": ["Instrument"]}, split.NOT_ITS_GROUP),
            ("every object entity class", {**ok, "takes": ["Mission", "Spacecraft", "Instrument"]}, split.EVERY_GROUP),
            ("its one subject entity class is every group", {**ok, "by": "subject", "takes": ["Data"]},
             split.EVERY_GROUP),
            ("every pattern", {**measures, "takes": ["Instrument -> Variable", "Instrument -> Image",
                                                     "Spacecraft -> Variable", "Spacecraft -> Image"]},
             split.EVERY_GROUP),
        ]
        for what, item, why in cases:
            with self.subTest(what):
                self.assertEqual(self.check(item)[1], [why])
        _, why = split.check([{"splits": [{**ok, "by": "subject", "takes": ["Mission"]}]}], self.found, self.predicates)
        self.assertIn("Mission (among its object entity classes only)", why[0]["why"])
        # near misses that pass: the predicate and each group in another spelling, read as the ones sent
        passed, rejected = self.check({"predicate": "sourced_from", "by": "Object", "into": "FROM_MISSION",
                                       "takes": ["mission"]})
        self.assertEqual((passed, rejected), ([{"predicate": "SOURCED_FROM", "by": "object", "into": "FROM_MISSION",
                                               "takes": ["Mission"], "only": [["any", "Mission"]], "texts": 2,
                                               "triple_instances": 2}], []))
        passed, _ = self.check({**measures, "takes": ["instrument->variable", "Spacecraft -> Image"]})
        self.assertEqual((passed[0]["takes"], passed[0]["only"], passed[0]["texts"]),
                         (["Instrument -> Variable", "Spacecraft -> Image"],
                          [["Instrument", "Variable"], ["Spacecraft", "Image"]], 3))
        passed, _ = self.check({**measures, "by": "subject", "takes": ["Spacecraft"]})
        self.assertEqual((passed[0]["only"], passed[0]["texts"], passed[0]["triple_instances"]),
                         ([["Spacecraft", "any"]], 2, 3))

    def test_min_split_texts(self):
        """A new predicate needs supporting texts (texts with a triple instance it would take) at least min_split_texts;
        a group found in one text fails, two groups of one text each (two texts) pass, and the setting is recorded."""
        from common import dropped
        dropped.reset()
        self.addCleanup(dropped.reset)
        one_text = {"predicate": "SOURCED_FROM", "by": "object", "into": "FROM_CRAFT", "takes": ["Spacecraft"]}
        self.assertEqual(self.check(one_text, min_texts=2)[1], [split.TOO_FEW_TEXTS])
        self.assertEqual(self.check(one_text, min_texts=1)[1], [])                       # near miss: the setting
        two_texts = {**one_text, "takes": ["Spacecraft", "Instrument"]}                  # t2 and t3
        self.assertEqual(self.check(two_texts, min_texts=2)[1], [])
        same_text = {"predicate": "MEASURES", "by": "pattern", "into": "M", "takes": ["Spacecraft -> Image"]}
        self.assertEqual(self.check(same_text, min_texts=2)[1], [split.TOO_FEW_TEXTS])    # t4 only
        self.assertEqual(self.check({**same_text, "takes": ["Spacecraft -> Variable"]}, min_texts=2)[1], [])
        self.assertEqual(self.check(two_texts, min_texts=3)[1], [split.TOO_FEW_TEXTS])
        settings = [e["setting"] for e in dropped.DISCARDS if "min_split_texts" in e["reason"]]
        self.assertIn({"min_split_texts": 2}, settings)
        # a split rejected for too few texts leaves its group free for a later split, and fixes no grouping
        passed, rejected = self.check(one_text, {**one_text, "by": "subject", "into": "X", "takes": ["Data"]},
                                      {**two_texts, "into": "FROM_PLATFORM"}, min_texts=2)
        self.assertEqual(([p["into"] for p in passed], rejected),
                         (["FROM_PLATFORM"], [split.TOO_FEW_TEXTS, split.EVERY_GROUP]))

    def test_one_grouping_per_predicate(self):
        """The first split of a predicate that passes fixes its grouping; another grouping of the same predicate is
        rejected; another predicate keeps its own choice; splits by one grouping may together take every group."""
        passed, rejected = self.check(
            {"predicate": "MEASURES", "by": "subject", "into": "BY_INSTRUMENT", "takes": ["Instrument"]},
            {"predicate": "MEASURES", "by": "object", "into": "OF_IMAGE", "takes": ["Image"]},          # other grouping
            {"predicate": "MEASURES", "by": "pattern", "into": "OF_X", "takes": ["Spacecraft -> Image"]},   # and again
            {"predicate": "SOURCED_FROM", "by": "object", "into": "FROM_MISSION", "takes": ["Mission"]},
            {"predicate": "MEASURES", "by": "subject", "into": "BY_SPACECRAFT", "takes": ["Spacecraft"]})
        self.assertEqual([p["into"] for p in passed], ["BY_INSTRUMENT", "FROM_MISSION", "BY_SPACECRAFT"])
        self.assertEqual(rejected, [split.OTHER_GROUPING, split.OTHER_GROUPING])
        self.assertEqual(split.added_by(passed, self.found), 2)        # MEASURES split away whole: 2 - 1, plus 1

    def test_first_split_stands(self):
        passed, rejected = self.check(
            {"predicate": "SOURCED_FROM", "by": "object", "into": "FROM_MISSION", "takes": ["Mission"]},
            {"predicate": "SOURCED_FROM", "by": "object", "into": "FROM_CRAFT", "takes": ["Spacecraft", "Mission"]},
            {"predicate": "SOURCED_FROM", "by": "object", "into": "from_mission", "takes": ["Instrument"]},
            {"predicate": "SOURCED_FROM", "by": "object", "into": "FROM_SPACECRAFT", "takes": ["Spacecraft"]},
            {"predicate": "MEASURES", "by": "pattern", "into": "M1", "takes": ["Instrument -> Image"]},
            {"predicate": "MEASURES", "by": "pattern", "into": "M2", "takes": ["instrument -> image"]})
        self.assertEqual([p["into"] for p in passed], ["FROM_MISSION", "FROM_SPACECRAFT", "M1"])
        self.assertEqual(rejected, [split.GROUP_TWICE, split.NAME_TWICE, split.GROUP_TWICE])

    def test_group_named_twice_counted_once(self):
        passed, _ = self.check({"predicate": "SOURCED_FROM", "by": "object", "into": "FROM_MISSION",
                                "takes": ["Mission", "mission"]})
        self.assertEqual(passed[0]["takes"], ["Mission"])

    def test_added_counts_a_predicate_split_away(self):
        one = {"predicate": "SOURCED_FROM", "by": "object", "takes": ["Mission"]}
        rest = {"predicate": "SOURCED_FROM", "by": "object", "takes": ["Spacecraft", "Instrument"]}
        self.assertEqual(split.added_by([one], self.found), 1)
        self.assertEqual(split.added_by([one, rest], self.found), 1)       # every group taken: SOURCED_FROM is gone
        pattern = [{"predicate": "MEASURES", "by": "pattern", "takes": ["Instrument -> Variable", "Spacecraft -> Image"]},
                   {"predicate": "MEASURES", "by": "pattern", "takes": ["Instrument -> Image"]}]
        self.assertEqual(split.added_by(pattern, self.found), 2)          # Spacecraft -> Variable stays: none gone

    def test_cap_keeps_most_supported_first(self):
        passed = [{"predicate": "SOURCED_FROM", "by": "object", "into": "FROM_SPACECRAFT", "takes": ["Spacecraft"],
                   "texts": 1},
                  {"predicate": "SOURCED_FROM", "by": "object", "into": "FROM_MISSION", "takes": ["Mission"], "texts": 2}]
        kept, dropped = split.capped(passed, self.found, 1)
        self.assertEqual(([s["into"] for s in kept], [s["into"] for s in dropped]), (["FROM_MISSION"], ["FROM_SPACECRAFT"]))
        kept, dropped = split.capped(passed, self.found, 2)                         # near miss: room for both
        self.assertEqual((len(kept), dropped), (2, []))
        # splits that take every group add one predicate less, so a cap of 1 keeps both halves of a full split
        full = passed[1:] + [{"predicate": "SOURCED_FROM", "by": "object", "into": "FROM_OTHER",
                              "takes": ["Spacecraft", "Instrument"], "texts": 2}]
        kept, dropped = split.capped(full, self.found, 1)
        self.assertEqual((len(kept), dropped), (2, []))

    def test_stage_end_to_end(self):
        """The model's reply, checked and capped; max_new_predicates 0 asks nothing."""
        s, prompts = self.run_stage([
            {"predicate": "SOURCED_FROM", "by": "object", "into": "FROM_MISSION", "takes": ["Mission"]},
            {"predicate": "SOURCED_FROM", "by": "object", "into": "FROM_SPACECRAFT", "takes": ["Spacecraft"]},
            {"predicate": "SOURCED_FROM", "by": "object", "into": "FROM_GADGET", "takes": ["Gadget"]}], cap=1)
        self.assertEqual([e["predicate"] for e in s.sent], ["MEASURES", "SOURCED_FROM"])
        self.assertEqual(s.into, {"SOURCED_FROM": {"by": "object", "to": {"Mission": "FROM_MISSION"}}})
        self.assertEqual(([d["into"] for d in s.dropped], [r["into"] for r in s.rejected], s.added, s.calls),
                         (["FROM_SPACECRAFT"], ["FROM_GADGET"], 1, 1))
        self.assertEqual((s.kept[0]["texts"], s.pinned, s.net_added, s.merge_calls), (2, {"FROM_MISSION": [
            ("any", "Mission")]}, 1, 1))
        self.assertEqual(len(prompts), 2)                                   # splitting, then merging again
        with Scripted({}) as calls:
            none = split.split_predicates(self.triples, self.labels, {"max_new_predicates": 0, "min_split_texts": 2},
                                          calls)
        self.assertEqual((none.calls, none.merge_calls, none.into, none.sent, none.pinned, none.net_added),
                         (0, 0, {}, [], {}, 0))

    def test_sent_shows_every_grouping(self):
        """Each predicate sent shows its patterns (with texts and examples) and the texts of each subject entity class
        and object entity class, so a split by any grouping can be read off."""
        _, prompts = self.run_stage([])
        sent = json.loads(prompts[0][prompts[0].rindex("object instances):") + len("object instances):"):])
        m = next(e for e in sent if e["predicate"] == "MEASURES")
        self.assertEqual((m["texts"], m["subject_classes"], m["object_classes"]),
                         (4, {"Instrument": 3, "Spacecraft": 2}, {"Variable": 4, "Image": 2}))
        self.assertEqual([(p["subject"], p["object"], p["texts"]) for p in m["patterns"]],
                         [("Instrument", "Variable", 2), ("Spacecraft", "Variable", 2), ("Instrument", "Image", 1),
                          ("Spacecraft", "Image", 1)])
        self.assertEqual(m["patterns"][0]["examples"], ["AIRS -- measures -- humidity",
                                                        "MODIS -- measures -- temperature"])   # ties alphabetically
        self.assertEqual(len(prompts), 1)                                   # nothing split: no merging again

    def test_unlabeled_subject_is_not_moved_or_shown(self):
        """A triple instance whose subject has no label has no pattern: it is in no group, counts toward no split's
        support, and stays with its predicate (near miss: the same triple instance with a labeled subject moves)."""
        self.triples.texts[3]["triple_instances"].append({"subject": "nobody", "predicate": "came from",
                                                          "object": "Apollo 13", "source_text": "x"})
        self.labels.final["entity"]["Apollo 13"] = "Mission"
        s, _ = self.run_stage([{"predicate": "SOURCED_FROM", "by": "object", "into": "FROM_MISSION",
                                "takes": ["Mission"]}])
        self.assertEqual(s.kept[0]["texts"], 2)                            # t4's triple instance has no pattern
        c = count.count_support(self.triples, self.labels, s)
        self.assertEqual(c.pattern_of["t4"][-1], None)
        self.assertEqual({p["component_class"]: p["support"] for p in c.predicates}["SOURCED_FROM"], 3)   # t2, t3, t4
        self.labels.final["entity"]["nobody"] = "Data"                      # near miss
        s, _ = self.run_stage([{"predicate": "SOURCED_FROM", "by": "object", "into": "FROM_MISSION",
                                "takes": ["Mission"]}])
        self.assertEqual(s.kept[0]["texts"], 3)


class MergingAgain(SplitFixture, unittest.TestCase):
    """Stage 5's merging again, after the cap: stage 4's predicate merge prompt and code over every predicate after
    splitting; merges of two predicates both there at stage 4 set aside; splits undone when every part of their
    predicate ends in one predicate; pins after a merge (the union when every member is pinned, none otherwise)."""

    def setUp(self):
        super().setUp()
        from common import dropped
        self.dropped = dropped
        dropped.reset()
        self.addCleanup(dropped.reset)

    def records(self, stage, item_type=None):
        return [e for e in self.dropped.DISCARDS if e["stage"] == stage
                and (item_type is None or e["item_type"] == item_type)]

    MISSION = {"predicate": "SOURCED_FROM", "by": "object", "into": "FROM_MISSION", "takes": ["Mission"]}
    CRAFT = {"predicate": "SOURCED_FROM", "by": "object", "into": "FROM_CRAFT", "takes": ["Spacecraft", "Instrument"]}
    BY_INSTRUMENT = {"predicate": "MEASURES", "by": "subject", "into": "BY_INSTRUMENT", "takes": ["Instrument"]}

    def test_prompt_is_stage_4s_over_every_predicate_after_splitting(self):
        _, prompts = self.run_stage([self.MISSION, self.CRAFT])
        listing = json.loads(prompts[1][prompts[1].rindex("LABELS:") + len("LABELS:"):])
        self.assertEqual([e["label"] for e in listing], ["ABOARD", "FROM_CRAFT", "FROM_MISSION", "MEASURES"])
        self.assertEqual(next(e for e in listing if e["label"] == "FROM_MISSION"),
                         {"label": "FROM_MISSION", "texts": 2, "examples": [
                             "data (Data) -- came from -- Apollo 11 (Mission)",
                             "x (Data) -- came from -- Apollo 12 (Mission)"]})

    def test_parts_of_one_split_show_their_own_triple_instances(self):
        """The new predicates of one split share their predicate instance ("came from"), so each is shown with the
        triple instances it took, whose entity classes differ (near miss: the words alone are the same)."""
        _, prompts = self.run_stage([self.MISSION, self.CRAFT])
        listing = {e["label"]: e["examples"] for e in json.loads(
            prompts[1][prompts[1].rindex("LABELS:") + len("LABELS:"):])}
        self.assertEqual(listing["FROM_CRAFT"], ["y (Data) -- came from -- MODIS (Instrument)",
                                                 "images (Data) -- came from -- Cassini (Spacecraft)"])
        self.assertTrue(all("(Mission)" in x for x in listing["FROM_MISSION"]))
        self.assertFalse(any("(Mission)" in x for x in listing["FROM_CRAFT"]))
        words = lambda xs: {x.split(" -- ")[1] for x in xs}                # noqa: E731
        self.assertEqual(words(listing["FROM_CRAFT"]), words(listing["FROM_MISSION"]))
        self.assertIn("the same predicate instance alone is no reason to merge them", prompts[1])
        self.assertIn(merge.PROMPTS["predicate"].template.split("$labels")[0].split("$words")[1].strip()[:200],
                      prompts[1])

    def test_split_merged_back_together_is_undone(self):
        """Both new predicates of a full split merged into one: a renaming, so the split is undone and SOURCED_FROM
        is whole again, with no pin; every step is recorded."""
        s, _ = self.run_stage([self.MISSION, self.CRAFT], [{"into": "FROM_MISSION", "labels": ["FROM_CRAFT"]}])
        self.assertEqual((s.into, s.kept, s.pinned), ({}, [], {}))
        self.assertEqual([(u["into"], u["ends_in"], u["goes_to"]) for u in s.undone],
                         [("FROM_CRAFT", "FROM_MISSION", "SOURCED_FROM"), ("FROM_MISSION", "FROM_MISSION",
                                                                           "SOURCED_FROM")])
        self.assertEqual((s.predicate("SOURCED_FROM", "Data", "Mission"), s.net_added, s.added), ("SOURCED_FROM", 0, 1))
        undone = [e["item"]["into"] for e in self.records(split.STAGE, "predicate split")]
        self.assertEqual(sorted(undone), ["FROM_CRAFT", "FROM_MISSION"])
        folds = sorted((e["item"]["label"], e["kept_as"]["label"]) for e in self.records(split.MERGE_AGAIN_STAGE))
        self.assertEqual(folds, [("FROM_CRAFT", "SOURCED_FROM"), ("FROM_MISSION", "SOURCED_FROM")])

    def test_split_merged_back_into_its_predicate_is_undone(self):
        s, _ = self.run_stage([self.MISSION], [{"into": "SOURCED_FROM", "labels": ["FROM_MISSION"]}])
        self.assertEqual(([u["goes_to"] for u in s.undone], s.into, s.final.get("SOURCED_FROM")),
                         (["SOURCED_FROM"], {}, "SOURCED_FROM"))
        # near miss: only one of two new predicates merged back, so the split stands (with one part fewer)
        s, _ = self.run_stage([self.MISSION, {**self.CRAFT, "takes": ["Spacecraft"]}],
                              [{"into": "SOURCED_FROM", "labels": ["FROM_MISSION"]}])
        self.assertEqual((s.undone, s.predicate("SOURCED_FROM", "Data", "Mission"),
                          s.predicate("SOURCED_FROM", "Data", "Spacecraft")), ([], "SOURCED_FROM", "FROM_CRAFT"))
        self.assertEqual(s.pinned, {"FROM_CRAFT": [("any", "Spacecraft")]})       # FROM_MISSION joined unpinned

    def test_new_predicate_merged_into_another_predicate(self):
        """A new predicate merged into a different, existing predicate takes that predicate's lack of a pin; the
        split stands (its predicate kept other triple instances), and the dropped pin is recorded."""
        s, _ = self.run_stage([self.MISSION], [{"into": "ABOARD", "labels": ["FROM_MISSION"]}])
        self.assertEqual((s.undone, s.predicate("SOURCED_FROM", "Data", "Mission"), s.pinned), ([], "ABOARD", {}))
        pins = [(e["action"], e["item"]) for e in self.records(split.MERGE_AGAIN_STAGE, "pinned predicate")]
        self.assertEqual(pins, [("discarded", {"predicate": "FROM_MISSION", "only": ["any", "Mission"]})])
        self.assertEqual(s.net_added, 0)                                    # one added, one merged away

    def test_both_old_set_aside(self):
        """A merge of two predicates both there at stage 4 is set aside and recorded (stage 4 judged them); a merge of
        an old predicate into a new one is kept (near miss)."""
        s, _ = self.run_stage([self.MISSION], [{"into": "ABOARD", "labels": ["MEASURES"]},
                                               {"into": "FROM_MISSION", "labels": ["ABOARD"]}])
        self.assertEqual(s.merge_issues["both_seen"], ["MEASURES"])
        self.assertEqual((s.final["MEASURES"], s.final["ABOARD"]), ("MEASURES", "FROM_MISSION"))
        self.assertEqual(s.pinned, {})                                      # ABOARD has no pin
        set_aside = [e["item"] for e in self.records(split.MERGE_AGAIN_STAGE, "merge")]
        self.assertEqual(set_aside, [{"kind": "predicate", "merge": {"label": "MEASURES", "into": "ABOARD"}}])

    def test_chain_and_pinned_union(self):
        """A chain of merges among new predicates of two splits is followed to its end; the predicate they become is
        pinned to the union of their pins, since each is pinned; neither split is undone (each predicate kept a part)."""
        s, _ = self.run_stage([self.MISSION, {**self.CRAFT, "takes": ["Spacecraft"]}, self.BY_INSTRUMENT],
                              [{"into": "FROM_CRAFT", "labels": ["FROM_MISSION"]},
                               {"into": "BY_INSTRUMENT", "labels": ["FROM_CRAFT"]}])
        self.assertEqual((s.final["FROM_MISSION"], s.final["FROM_CRAFT"], s.undone), ("BY_INSTRUMENT", "BY_INSTRUMENT", []))
        self.assertEqual(s.pinned, {"BY_INSTRUMENT": [("Instrument", "any"), ("any", "Spacecraft"), ("any", "Mission")]})
        unions = [e["item"]["predicate"] for e in self.records(split.MERGE_AGAIN_STAGE, "pinned predicate")]
        self.assertEqual(sorted(set(unions)), ["FROM_CRAFT", "FROM_MISSION"])
        self.assertEqual(s.net_added, 1)                                    # three added, two merged away

    def test_undone_into_another_splits_new_predicate(self):
        """Every part of SOURCED_FROM merged into a new predicate of MEASURES: the split is undone and SOURCED_FROM,
        whole again, is merged into it; SOURCED_FROM has no pin, so the predicate it joins loses its pin."""
        s, _ = self.run_stage([self.MISSION, self.CRAFT, self.BY_INSTRUMENT],
                              [{"into": "BY_INSTRUMENT", "labels": ["FROM_MISSION", "FROM_CRAFT"]}])
        self.assertEqual([(u["into"], u["goes_to"]) for u in s.undone],
                         [("FROM_CRAFT", "BY_INSTRUMENT"), ("FROM_MISSION", "BY_INSTRUMENT")])
        self.assertEqual((s.predicate("SOURCED_FROM", "Data", "Mission"), list(s.into), s.pinned),
                         ("BY_INSTRUMENT", ["MEASURES"], {}))
        restored = [e for e in self.records(split.MERGE_AGAIN_STAGE, "label") if e["item"]["label"] == "SOURCED_FROM"]
        self.assertEqual([e["kept_as"] for e in restored], [{"label": "BY_INSTRUMENT"}])

    def test_undoing_cascades(self):
        """SOURCED_FROM's parts end in MEASURES' new predicate; MEASURES' parts then end in one predicate too (its
        own new one), so both are undone, and SOURCED_FROM ends in MEASURES."""
        s, _ = self.run_stage([self.MISSION, self.CRAFT, self.BY_INSTRUMENT],
                              [{"into": "BY_INSTRUMENT", "labels": ["FROM_MISSION", "FROM_CRAFT", "MEASURES"]}])
        self.assertEqual({u["predicate"] for u in s.undone}, {"SOURCED_FROM", "MEASURES"})
        self.assertEqual((s.into, s.predicate("SOURCED_FROM", "Data", "Mission"),
                          s.predicate("MEASURES", "Instrument", "Image"), s.pinned), ({}, "MEASURES", "MEASURES", {}))
        self.assertEqual(s.net_added, -1)                                   # SOURCED_FROM merged into MEASURES

    def test_cap_before_merging_again(self):
        """The cap is applied first: a split it dropped stays dropped even when merging again undoes the split it
        kept."""
        s, _ = self.run_stage([self.MISSION, {**self.CRAFT, "takes": ["Spacecraft"]}],
                              [{"into": "SOURCED_FROM", "labels": ["FROM_MISSION"]}], cap=1)
        self.assertEqual(([d["into"] for d in s.dropped], [u["into"] for u in s.undone], s.into, s.added),
                         (["FROM_CRAFT"], ["FROM_MISSION"], {}, 1))

    def test_accounting_near_miss(self):
        from unittest import mock
        from common.stop import Stop
        with mock.patch.object(self.dropped, "fold", lambda *a, **k: None), self.assertRaises(Stop) as caught:
            self.run_stage([self.MISSION], [{"into": "SOURCED_FROM", "labels": ["FROM_MISSION"]}])
        self.assertIn("Accounting check failed in stage 5 (merge_predicates_again)", str(caught.exception))


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

    def test_split_by_grouping_and_merged_again(self):
        """Since 2026-11-15: a split names its grouping ("by"); a pattern split needs both entity classes (Cassini's
        subject has no label: no split shown, a near miss), and merging again shows after the split."""
        path = self.folder / "induction_evidence.json"
        evidence = json.loads(path.read_text(encoding="utf-8"))
        evidence["labels"]["entity"] = {"Apollo 11": "Mission", "samples": "Sample", "Cassini": "Mission"}
        evidence["splits"] = {"into": {"FROM": {"by": "pattern", "to": {"Sample -> Mission": "SAMPLE_FROM"}}},
                              "final": {"SAMPLE_FROM": "COLLECTED_DURING", "FROM": "FROM"}}
        path.write_text(json.dumps(evidence), encoding="utf-8")
        _, out = self.trace("Apollo|Cassini")
        self.assertIn("-> split to SAMPLE_FROM by its pattern, Sample -> Mission (stage 5) -> merged again into "
                      "COLLECTED_DURING (stage 5) = COLLECTED_DURING", out)
        cassini = out.split("Cassini", 1)[1].split("\n")[2]
        self.assertNotIn("split", cassini)
        evidence["splits"]["into"]["FROM"] = {"by": "subject", "to": {"Sample": "SAMPLE_FROM"}}
        path.write_text(json.dumps(evidence), encoding="utf-8")
        _, out = self.trace("Apollo")
        self.assertIn("split to SAMPLE_FROM by its subject's entity class, Sample (stage 5)", out)

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


class Discards(unittest.TestCase):
    """Every stage of 040 records each item it doesn't keep in the record of discarded items
    (common/common_helpers/dropped.py), and its accounting checks stop the run when an item vanishes without a record
    of it (the near misses: the recording switched off)."""

    def setUp(self):
        from common import dropped
        from common.stop import Stop
        from unittest import mock
        self.dropped, self.Stop, self.mock = dropped, Stop, mock
        dropped.reset()
        self.addCleanup(dropped.reset)

    def off(self, name="discard"):
        """The recording of one action switched off: an item removed without an entry."""
        return self.mock.patch.object(self.dropped, name, lambda *a, **k: None)

    def of(self, stage, action=None):
        return [e for e in self.dropped.DISCARDS if e["stage"] == stage and (action is None or e["action"] == action)]

    def test_stage_1_twins_and_not_reached(self):
        orders = {"S1": ["a", "c", "f"], "S2": ["b", "e", "d", "g"]}
        taken, skipped, _ = texts_stage.draw(orders, ["S1", "S2"], Drawing.RECORDS, 1)
        texts_stage._record_not_taken(orders, ["S1", "S2"], taken, skipped, Drawing.RECORDS, 1)
        folded = {e["record_id"]: e["kept_as"]["id"] for e in self.of(texts_stage.STAGE, "folded")}
        self.assertEqual(folded, {"b": "a", "e": "a"})                       # twins, into the text they twin
        not_reached = sorted(e["record_id"] for e in self.of(texts_stage.STAGE, "discarded"))
        self.assertEqual(not_reached, ["c", "f", "g"])                       # d was taken from S2
        self.assertEqual({e["setting"]["texts_per_stratum"] for e in self.of(texts_stage.STAGE, "discarded")}, {1})
        self.dropped.account(texts_stage.STAGE, "induction candidates", 7, 2)

    def test_stage_2_items_not_kept(self):
        import extract
        from common import extraction
        good = {"subject": "MODIS", "predicate": "is aboard", "object": "Aqua", "source_text": "MODIS aboard Aqua"}
        invented = {"subject": "Terra", "predicate": "carries", "object": "Aqua", "source_text": "Terra carries Aqua"}
        item = {"id": "r", "maintainer": "m", "title": "T", "text": "title: T\n\nnotes: MODIS aboard Aqua.",
                "record": {}, "pieces": ["p1", "p2"]}
        replies = extraction.Replies(of={"r": [{"triples": [good, {"subject": ""}, invented], "describes_class": "A"},
                                               {"triples": [dict(good)], "describes_class": "B"}]})
        saved = extraction.ask_model
        extraction.ask_model = lambda *a, **k: replies
        self.addCleanup(setattr, extraction, "ask_model", saved)
        extract.extract_triple_instances(SimpleNamespace(items=[item]), None, {"workers": 1})
        reasons = sorted(e["reason"].split(":")[0] for e in self.of(extract.STAGE) if e["action"] != "replaced")
        self.assertEqual(reasons, ["not a triple instance", "the same fact stated twice in one text (triple_key)",
                                   "unverified"])
        self.assertEqual([e["item"] for e in self.of(extract.STAGE, "replaced")], [{"describes_class": "B"}])
        with self.off(), self.assertRaises(self.Stop) as caught:
            extract.extract_triple_instances(SimpleNamespace(items=[item]), None, {"workers": 1})
        self.assertIn("Accounting check failed in stage 2 (extract_triple_instances): 4 items in the replies about "
                      "text r went in, 1 were kept", str(caught.exception))

    def test_stage_4_merges_and_folds(self):
        m = Merging().merge([{"into": "Gadget", "labels": ["Sensor"]},
                             {"into": "Instrument", "labels": ["Sensor", "Widget", "Instrument"]},
                             {"into": "Spacecraft", "labels": ["Sensor"]}, "not a dict",
                             {"into": "Craft", "labels": "Spacecraft"}])
        set_aside = [e["reason"].split(": ", 1)[1] for e in self.of(merge.STAGE, "discarded")]
        self.assertEqual(sorted(set_aside), sorted(merge.ISSUE_WHY[k] for k in (
            "into_not_a_label", "not_sent", "into_itself", "merged_twice", "not_an_object", "labels_not_a_list")))
        self.assertEqual([(e["item"]["label"], e["kept_as"]["label"]) for e in self.of(merge.STAGE, "folded")],
                         [(x["label"], x["into"]) for x in m.merges])

    def test_stage_4_near_miss(self):
        labels = label.Labels(of={"entity": {"a": "Sensor", "b": "Instrument"}, "predicate": {}},
                              vocabulary={"entity": ["Instrument", "Sensor"], "predicate": []})
        with Scripted({"LABELS": {"merges": [{"into": "Instrument", "labels": ["Sensor"]}]}}) as calls, \
                self.off("fold"), self.assertRaises(self.Stop) as caught:
            merge.merge_labels(labels, texts(), calls)
        self.assertIn("Accounting check failed in stage 4 (merge_labels): 2 entity class labels went in, 1 were "
                      "kept", str(caught.exception))

    def test_stage_5_rejected_dropped_undone_and_off(self):
        s = Splitting()
        s.setUp()
        settings = {"max_new_predicates": 1, "min_split_texts": 2}
        gadget = {"predicate": "SOURCED_FROM", "by": "object", "into": "FROM_GADGET", "takes": ["Gadget"]}
        craft = {"predicate": "SOURCED_FROM", "by": "object", "into": "FROM_CRAFT", "takes": ["Spacecraft"]}
        reply = {"splits": [{"predicate": "SOURCED_FROM", "by": "object", "into": "FROM_MISSION", "takes": ["Mission"]},
                            {"predicate": "MEASURES", "by": "subject", "into": "BY_SPACECRAFT", "takes": ["Spacecraft"]},
                            craft, gadget, "not an object"]}
        replies = {'"splits": [': reply, '"merges": [': {"merges": []}}
        with Scripted(replies) as calls:
            split.split_predicates(s.triples, s.labels, settings, calls)
        got = sorted((e["item"].get("into") or str(e["item"].get("raw")), e["reason"].split(":")[0],
                      str(e.get("setting"))) for e in self.of(split.STAGE))
        self.assertEqual(got, sorted([
            ("FROM_MISSION", "passed the checks, but keeping it would add more predicates than max_new_predicates "
                              "allows (the splits with the most texts are kept first)", str({"max_new_predicates": 1})),
            ("not an object", "proposed by the model, rejected by code", "None"),
            (str(craft), "proposed by the model, rejected by code", str({"min_split_texts": 2})),
            (str(gadget), "proposed by the model, rejected by code", "None")]))
        with Scripted(replies) as calls, self.off(), self.assertRaises(self.Stop):
            split.split_predicates(s.triples, s.labels, settings, calls)
        self.dropped.reset()                                               # undone by merging again: recorded too
        undo = {'"splits": [': reply, '"merges": [': {"merges": [{"into": "MEASURES", "labels": ["BY_SPACECRAFT"]}]}}
        with Scripted(undo) as calls:
            split.split_predicates(s.triples, s.labels, settings, calls)
        self.assertIn(("BY_SPACECRAFT", "undone by merging again"),
                      [(e["item"].get("into"), e["reason"].split(":")[0]) for e in self.of(split.STAGE)])
        self.dropped.reset()
        with Scripted({}) as calls:                                        # splitting off: the predicates not sent
            split.split_predicates(s.triples, s.labels, {**settings, "max_new_predicates": 0}, calls)
        self.assertEqual([(e["item"]["predicate"], e["setting"]) for e in self.of(split.STAGE)],
                         [("MEASURES", {"max_new_predicates": 0}), ("SOURCED_FROM", {"max_new_predicates": 0})])

    def test_stage_6_no_pattern(self):
        c = Counting()
        c.setUp()                                                          # CERES -- is aboard -- Mystery: no label
        no_pattern = [e["item"]["object"] for e in self.of(count.STAGE)]
        self.assertEqual(no_pattern, ["Mystery"])
        with self.off(), self.assertRaises(self.Stop) as caught:
            count.count_support(c.triples, c.labels, NO_SPLITS)
        self.assertIn("Accounting check failed in stage 6 (count_support): 6 verified triple instances went in, 5 "
                      "were kept", str(caught.exception))

    def test_stage_8_deferred(self):
        e = lambda name, support: {"component_class": name, "support": support, "texts": ["t0"] * support,  # noqa: E731
                                   "maintainers": ["m1"], "examples": ["x"]}
        counts = SimpleNamespace(entity_classes=[e("Instrument", 2), e("Rare", 1)], predicates=[e("ABOARD", 2)],
                                 patterns=[{"pattern": ["Rare", "ABOARD", "Instrument"], "support": 2,
                                            "maintainers": ["m1"], "texts": ["t0"]}])
        definitions = SimpleNamespace(of={}, too_vague={})
        check.check_schema(counts, definitions, {"min_support": 2})
        self.assertEqual(sorted(x["item"]["schema_entry"] for x in self.of(check.STAGE)),
                         ["Rare", "Rare ABOARD Instrument"])
        self.assertEqual({x["setting"]["min_support"] for x in self.of(check.STAGE)}, {2})
        with self.off(), self.assertRaises(self.Stop):
            check.check_schema(counts, definitions, {"min_support": 2})


class FoldBeforeMerging(unittest.TestCase):
    """Stage 4 folds spellings before its merge call (the most frequent spelling wins, ties alphabetically), so the
    model sees one spelling of each label; each fold is recorded. Stage 3's running vocabulary holds one spelling."""

    def setUp(self):
        from common import dropped
        dropped.reset()
        self.addCleanup(dropped.reset)
        self.dropped = dropped

    def test_merge_call_sees_one_spelling(self):
        labels = label.Labels(of={"entity": {"a": "Space craft", "b": "Spacecraft", "c": "Spacecraft", "d": "Sensor",
                                             "e": "Instrument"}, "predicate": {"p": "ABOARD"}},
                              vocabulary={"entity": ["Space craft", "Spacecraft", "Sensor", "Instrument"],
                                          "predicate": ["ABOARD"]})
        model = Scripted({"LABELS": {"merges": [{"into": "Instrument", "labels": ["Sensor"]}]}})
        with model as calls:
            m = merge.merge_labels(labels, texts(), calls)
        sent = json.loads(model.prompts[0][model.prompts[0].rindex("LABELS:") + len("LABELS:"):])
        self.assertEqual([e["label"] for e in sent], ["Instrument", "Sensor", "Spacecraft"])   # no "Space craft"
        self.assertEqual(m.final["entity"], {"a": "Spacecraft", "b": "Spacecraft", "c": "Spacecraft",
                                             "d": "Instrument", "e": "Instrument"})
        self.assertEqual(m.spelling_folds, [{"kind": "entity class", "into": "Spacecraft",
                                             "folded": ["Space craft", "Spacecraft"]}])
        folds = [(e["item"]["label"], e["kept_as"]["label"]) for e in self.dropped.DISCARDS if e["action"] == "folded"]
        self.assertEqual(sorted(folds), [("Sensor", "Instrument"), ("Space craft", "Spacecraft")])

    def test_tie_alphabetical_and_digits_kept(self):
        labels = label.Labels(of={"entity": {"a": "Level2", "b": "level 2", "c": "Level3"}, "predicate": {}},
                              vocabulary={"entity": ["Level2", "level 2", "Level3"], "predicate": []})
        with Scripted({"LABELS": {"merges": []}}) as calls:
            m = merge.merge_labels(labels, texts(), calls)
        self.assertEqual(m.final["entity"], {"a": "Level2", "b": "Level2", "c": "Level3"})      # "L" sorts before "l"

    def test_running_vocabulary_one_spelling(self):
        self.assertEqual(label.one_spelling(["Spacecraft"], ["Space craft", "Instrument", "instrument", "SPACECRAFT"]),
                         ["Instrument"])
        self.assertEqual(label.one_spelling([], ["Level2", "Level3"]), ["Level2", "Level3"])    # digits apart
        triples = texts(("t1", "m", "T1", "", [("MODIS", "is aboard", "Aqua"), ("AIRS", "is aboard", "Terra")]))
        replies = iter([{"labels": {"MODIS": "Instrument", "Aqua": "Spacecraft", "AIRS": "instrument",
                                    "Terra": "SpaceCraft"}}, {"labels": {"is aboard": "ABOARD"}}])
        with Scripted({}) as calls:
            llm.call_llm_json = lambda prompt, **kw: next(replies)
            result = label.label_component_instances(triples, calls)
        self.assertEqual(sorted(result.vocabulary["entity"]), ["Spacecraft", "instrument"])   # first met in the batch
        self.assertEqual(result.of["entity"]["AIRS"], "instrument")          # kept as the model gave it: stage 4 folds


class SplittingShowsEveryName(unittest.TestCase):
    """Stage 5's prompt shows every predicate found, whose names code refuses for a new predicate, not only the
    predicates sent."""

    def test_names_shown(self):
        s = Splitting()
        s.setUp()
        model = Scripted({"splits": {"splits": []}})
        with model as calls:
            split.split_predicates(s.triples, s.labels, {"max_new_predicates": 1, "min_split_texts": 2}, calls)
        prompt = model.prompts[0]
        found = json.loads(prompt.split("must differ from all of these):\n", 1)[1].split("\n\nPREDICATES (", 1)[0])
        self.assertEqual(found, ["ABOARD", "MEASURES", "SOURCED_FROM"])       # ABOARD isn't sent (one pattern)
        sent = json.loads(prompt[prompt.rindex("object instances):") + len("object instances):"):])
        self.assertEqual([e["predicate"] for e in sent], ["MEASURES", "SOURCED_FROM"])


class DescribesClassByMajority(unittest.TestCase):
    """Stage 2 takes the describes class the most text pieces named (extraction.describes_class, as 050 and 060)."""

    def test_majority(self):
        import extract
        from common import dropped, extraction
        dropped.reset()
        self.addCleanup(dropped.reset)
        item = {"id": "r", "maintainer": "m", "title": "T", "text": "title: T", "record": {}, "pieces": ["1", "2", "3"]}
        for named, chosen in ((["WebTool", "Dataset", "dataset"], "Dataset"), (["A", "B", ""], "A"),
                              (["", "", "C"], "C")):
            with self.subTest(named=named):
                replies = extraction.Replies(of={"r": [{"triples": [], "describes_class": n} for n in named]})
                saved = extraction.ask_model
                extraction.ask_model = lambda *a, **k: replies
                try:
                    out = extract.extract_triple_instances(SimpleNamespace(items=[item]), None, {"workers": 1})
                finally:
                    extraction.ask_model = saved
                self.assertEqual(out.texts[0]["describes_class"], chosen)
        replaced = [(e["item"]["describes_class"], e["reason"]) for e in dropped.DISCARDS
                    if e["item_type"] == "describes class"]
        self.assertIn(("WebTool", "named by a text piece, but more text pieces of the same text named another one "
                                  "(or as many, and it was named first)"), replaced)
        self.assertIn(("dataset", "named by a text piece, but another spelling of the one chosen, which is kept in "
                                  "its first spelling"), replaced)


class Defining(unittest.TestCase):
    """Stage 7: a predicate is sent with its patterns; both prompts list the entity classes being defined; an entry
    left out, or a definition naming a word shaped like an entity class that isn't one, is asked once more."""

    def counts(self):
        e = lambda name, support, ex=("x",): {"component_class": name, "support": support,  # noqa: E731
                                              "texts": ["t"] * support, "maintainers": ["m"], "examples": list(ex)}
        return SimpleNamespace(
            entity_classes=[e("Instrument", 3), e("Spacecraft", 2), e("Rare", 1), e("Thing", 2)],
            predicates=[e("ABOARD", 2, ("MODIS -- is aboard -- Aqua",)), e("HAS", 2)],
            patterns=[{"pattern": ["Instrument", "ABOARD", "Spacecraft"], "support": 2},
                      {"pattern": ["Rare", "ABOARD", "Spacecraft"], "support": 1},        # Rare: below min_support
                      {"pattern": ["Thing", "ABOARD", "Spacecraft"], "support": 2}])      # Thing: too vague

    def test_words_shaped_like_entity_classes(self):
        import define
        known = ["Instrument", "Spacecraft", "PhysicalQuantity", "MapProjection"]
        cases = [("a device on a Spacecraft", []),                                   # one part: never checked
                 ("holds measurements of this PhysicalQuantity", []),
                 ("holds several PhysicalQuantities", []),                           # plural "ies" for a "y"
                 ("holds several PhysicalQuantityies", ["PhysicalQuantityies"]),     # near miss: no such plural
                 ("is drawn in these MapProjections", []),                           # plural "s"
                 ("was made by MODIS aboard SeaWiFS, as GeoTIFF or NetCDF", []),     # proper nouns: no lowercase part
                 ("was taken at McMurdo", ["McMurdo"]),                              # a CamelCase proper noun: listed
                 ("covers this SpatialExtent and this SpatialExtent", ["SpatialExtent"]),   # once
                 ("is a Physicalquantity or physicalQuantity", []),                  # not CamelCase
                 ("uses the Level-2 MapProjection-like grid", []),                   # inside a hyphenated word
                 ("measures a Physical Quantity", [])]
        for text, expected in cases:
            with self.subTest(text=text):
                self.assertEqual(define.not_entity_classes(text, known), expected)

    def test_patterns_sent_and_asked_again(self):
        import define
        from common import dropped
        dropped.reset()
        self.addCleanup(dropped.reset)
        replies = {
            "ENTITY CLASSES TO DEFINE": [
                {"definitions": {"Instrument": "a device carried by a Spacecraft", "Spacecraft": "a craft"},
                 "too_vague": {"Thing": "anything"}}],
            "PREDICATES:": [
                {"definitions": {"ABOARD": "is carried on this SpaceVehicle"}},                 # HAS left out
                {"definitions": {"ABOARD": "is carried on this Spacecraft", "HAS": "has this PhysicalQuantity"}}],
        }
        prompts = []

        def answer(prompt, **kw):
            prompts.append(prompt)
            key = next(k for k in replies if k in prompt)
            return replies[key].pop(0)
        with Scripted({}) as calls:
            llm.call_llm_json = answer
            d = define.write_definitions(self.counts(), {"min_support": 2}, calls)
        first = prompts[1]
        listing = json.loads(first.split("ENTITY CLASSES OF THE SCHEMA:\n", 1)[1].split("\n\nPREDICATES:", 1)[0])
        self.assertEqual(listing, ["Instrument", "Spacecraft"])            # Rare below min_support, Thing too vague
        sent = json.loads(first[first.rindex("PREDICATES:") + len("PREDICATES:"):])
        self.assertEqual(sent[0]["patterns"], [{"subject": "Instrument", "object": "Spacecraft", "texts": 2}])
        entries, note = prompts[2][prompts[2].rindex("PREDICATES:") + len("PREDICATES:"):].split("\n\nYour last", 1)
        again = json.loads(entries)
        self.assertEqual([e["component_class"] for e in again], ["HAS", "ABOARD"])   # missing, then wrong word
        self.assertEqual(note.split("\n")[1:], [   # what was wrong with each, as call_llm_json's re-ask says it
            '- HAS: it was neither defined nor listed under "too_vague"',
            "- ABOARD: its definition named SpaceVehicle, which is not listed under ENTITY CLASSES OF THE SCHEMA"])
        self.assertNotIn("Your last reply", prompts[1])                    # near miss: the first ask has no note
        self.assertEqual(d.of["predicates"], {"ABOARD": "is carried on this Spacecraft",
                                              "HAS": "has this PhysicalQuantity"})
        self.assertEqual(d.not_entity_classes, [])                         # HAS was missing, not checked twice
        self.assertEqual(len(prompts), 3)
        replaced = [e for e in dropped.DISCARDS if e["action"] == "replaced"]
        self.assertEqual([(e["item"]["definition"], e["kept_as"]["definition"]) for e in replaced],
                         [("is carried on this SpaceVehicle", "is carried on this Spacecraft")])

    def test_still_wrong_is_kept_and_listed(self):
        import define
        from common import dropped
        dropped.reset()
        self.addCleanup(dropped.reset)
        replies = iter([{"definitions": {"Instrument": "a device", "Spacecraft": "a craft"},
                         "too_vague": {"Thing": "anything"}},
                        {"definitions": {"ABOARD": "is carried on this SpaceVehicle"}, "too_vague": {"HAS": "vague"}},
                        {"too_vague": {"ABOARD": "vague after all"}}])        # second ask: no definition
        with Scripted({}) as calls:
            llm.call_llm_json = lambda prompt, **kw: next(replies)
            d = define.write_definitions(self.counts(), {"min_support": 2}, calls)
        self.assertEqual(d.of["predicates"], {"ABOARD": "is carried on this SpaceVehicle"})    # the first kept
        self.assertEqual(d.too_vague["predicates"], {"HAS": "vague"})
        self.assertEqual(d.not_entity_classes, [{"kind": "predicate", "component_class": "ABOARD",
                                                 "definition": "is carried on this SpaceVehicle",
                                                 "words": ["SpaceVehicle"]}])
        reasons = [e["reason"] for e in dropped.DISCARDS]
        self.assertTrue(any("the second reply gave no definition, so the first is kept, which still names "
                            "SpaceVehicle" in r for r in reasons), reasons)
        self.assertTrue(any(r.startswith("in the model's reply (too_vague, asked once more), but not taken")
                            for r in reasons), reasons)


class DefiningPinnedPredicates(unittest.TestCase):
    """Stage 7: a predicate stage 5 pinned is sent with "must_name" (its pin's entity classes being defined) and its
    definition must name each, checked as the ground truth schema's pins are (schema_io.unnamed_pinned); one that
    doesn't is asked once more, and one that still doesn't is kept, recorded and listed."""

    def counts(self):
        e = lambda name, support: {"component_class": name, "support": support, "texts": ["t"] * support,  # noqa: E731
                                   "maintainers": ["m"], "examples": ["x"]}
        return SimpleNamespace(
            entity_classes=[e("Data", 2), e("Mission", 2), e("Spacecraft", 2), e("Rare", 1)],
            predicates=[e("FROM_MISSION", 2), e("FROM_CRAFT", 2), e("ABOUT_RARE", 2), e("HAS", 2)],
            patterns=[{"pattern": ["Data", "FROM_MISSION", "Mission"], "support": 2}],
            pinned={"FROM_MISSION": [("any", "Mission")], "FROM_CRAFT": [("Data", "Spacecraft")],
                    "ABOUT_RARE": [("any", "Rare")]})                       # Rare: below min_support

    def run_define(self, second):
        import define
        from common import dropped
        dropped.reset()
        self.addCleanup(dropped.reset)
        replies = iter([{"definitions": {"Data": "values", "Mission": "a mission", "Spacecraft": "a craft"}},
                        {"definitions": {"FROM_MISSION": "came from this mission",          # lowercase: not named
                                         "FROM_CRAFT": "was carried on one of the Spacecrafts of this Data",   # plural
                                         "ABOUT_RARE": "is about something rare", "HAS": "has"}},
                        second])
        prompts = []

        def answer(prompt, **kw):
            prompts.append(prompt)
            return next(replies)
        with Scripted({}) as calls:
            llm.call_llm_json = answer
            d = define.write_definitions(self.counts(), {"min_support": 2}, calls)
        return d, prompts, dropped.DISCARDS

    def test_must_name_sent_and_asked_again(self):
        d, prompts, discards = self.run_define({"definitions": {"FROM_MISSION": "was produced during this Mission"}})
        sent = json.loads(prompts[1][prompts[1].rindex("PREDICATES:") + len("PREDICATES:"):])
        must = {e["component_class"]: e.get("must_name") for e in sent}
        self.assertEqual(must, {"FROM_MISSION": ["Mission"], "FROM_CRAFT": ["Data", "Spacecraft"], "ABOUT_RARE": None,
                                "HAS": None})                              # Rare isn't being defined; HAS isn't pinned
        entries, note = prompts[2][prompts[2].rindex("PREDICATES:") + len("PREDICATES:"):].split("\n\nYour last", 1)
        self.assertEqual([e["component_class"] for e in json.loads(entries)], ["FROM_MISSION"])
        self.assertEqual(note.split("\n")[1:], ["- FROM_MISSION: its definition didn't name Mission, which its "
                                                '"must_name" lists'])
        self.assertEqual(d.of["predicates"]["FROM_MISSION"], "was produced during this Mission")
        self.assertEqual(d.pins_not_named, [])
        self.assertIn("doesn't name Mission, which its pin allows", d.asked_again[0]["why"])
        replaced = [e for e in discards if e["action"] == "replaced"]
        self.assertEqual([(e["item"]["pinned_not_named"], e["kept_as"]["pinned_not_named"]) for e in replaced],
                         [(["Mission"], [])])
        self.assertNotIn("must_name", prompts[0])                          # entity classes are never pinned

    def test_still_not_named_is_kept_and_listed(self):
        d, _, discards = self.run_define({"definitions": {"FROM_MISSION": "came from this Missionary"}})
        self.assertEqual(d.of["predicates"]["FROM_MISSION"], "came from this Missionary")
        self.assertEqual(d.pins_not_named, [{"kind": "predicate", "component_class": "FROM_MISSION",
                                             "definition": "came from this Missionary", "entity_classes": ["Mission"]}])
        reasons = [e["reason"] for e in discards if e["action"] == "replaced"]
        self.assertTrue(any("it still doesn't name Mission (listed in the report)" in r for r in reasons), reasons)


class SharedPinCheck(unittest.TestCase):
    """The one check that a definition names its pin's entity classes (schema_io.unnamed_pinned), with near misses."""

    def test_near_misses(self):
        from common.schema_io import unnamed_pinned
        cases = [("came from this Mission", [("any", "Mission")], []),
                 ("came from one of these Missions", [("any", "Mission")], []),        # plural "s"
                 ("holds these PhysicalQuantities", [("any", "PhysicalQuantity")], []),  # plural "ies" for a "y"
                 ("holds these PhysicalQuantitys", [("any", "PhysicalQuantity")], []),   # a wrong plural names it too
                 ("covers these Days", [("any", "Day")], []),
                 ("covers these Daies", [("any", "Day")], ["Day"]),                    # near miss: "y" after a vowel
                 ("came from these Processes", [("any", "Process")], []),              # plural "es"
                 ("came from this mission", [("any", "Mission")], ["Mission"]),        # spelling must be exact
                 ("came from this Missionary", [("any", "Mission")], ["Mission"]),     # a whole word only
                 ("came from this Sub-Mission", [("any", "Mission")], ["Mission"]),    # inside a hyphenated word
                 ("a Data value from a Spacecraft", [("Data", "Spacecraft")], []),
                 ("a value from a Spacecraft", [("Data", "Spacecraft"), ("any", "Spacecraft")], ["Data"]),
                 ("anything", [("any", "any")], []), ("", [("any", "Mission")], ["Mission"])]
        for definition, pins, expected in cases:
            with self.subTest(definition=definition):
                self.assertEqual(unnamed_pinned(definition, pins), expected)


class PinsInTheSchema(unittest.TestCase):
    """Stage 8 writes the pin of each predicate in the schema, and none of a deferred predicate; a pair of a pin naming
    an entity class not in the schema is left out, and a pinned predicate left with none is deferred."""

    def test_pin_through_an_entity_class_not_in_the_schema(self):
        from common import dropped
        dropped.reset()
        self.addCleanup(dropped.reset)
        e = lambda name, support: {"component_class": name, "support": support, "texts": ["t0"] * support,  # noqa: E731
                                   "maintainers": ["m1"], "examples": ["x"]}
        counts = SimpleNamespace(entity_classes=[e("Data", 2), e("Mission", 2), e("Rare", 1)],
                                 predicates=[e("FROM_RARE", 2), e("FROM_EITHER", 2), e("FROM_ANY", 2)], patterns=[],
                                 pinned={"FROM_RARE": [("any", "Rare")],
                                         "FROM_EITHER": [("any", "Rare"), ("any", "Mission")],
                                         "FROM_ANY": [("Data", "any")]})
        schema = check.check_schema(counts, SimpleNamespace(of={}, too_vague={}), {"min_support": 2})
        self.assertEqual(schema.pinned, {"FROM_EITHER": [["any", "Mission"]], "FROM_ANY": [["Data", "any"]]})
        self.assertEqual([(d["schema_entry"], d["reason_code"]) for d in schema.deferred if d["entry_type"] == "predicate"],
                         [("FROM_RARE", check.NOT_IN_SCHEMA)])
        left_out = [e["item"] for e in dropped.DISCARDS if e["item_type"] == "pinned predicate"]
        self.assertEqual(left_out, [{"predicate": "FROM_RARE", "only": ["any", "Rare"]},
                                    {"predicate": "FROM_EITHER", "only": ["any", "Rare"]}])

    def test_pins_written_for_predicates_in_the_schema(self):
        e = lambda name, support: {"component_class": name, "support": support, "texts": ["t0"] * support,  # noqa: E731
                                   "maintainers": ["m1"], "examples": ["x"]}
        counts = SimpleNamespace(entity_classes=[e("Data", 2), e("Mission", 2)],
                                 predicates=[e("FROM_MISSION", 2), e("RARE_SPLIT", 1), e("VAGUE_SPLIT", 2)],
                                 patterns=[], pinned={"FROM_MISSION": [("any", "Mission")],
                                                      "RARE_SPLIT": [("Data", "any")],
                                                      "VAGUE_SPLIT": [("any", "Data")]})
        definitions = SimpleNamespace(of={}, too_vague={"predicates": {"VAGUE_SPLIT": "vague"}})
        schema = check.check_schema(counts, definitions, {"min_support": 2})
        self.assertEqual(schema.pinned, {"FROM_MISSION": [["any", "Mission"]]})
        no_pins = check.check_schema(SimpleNamespace(**{k: v for k, v in vars(counts).items() if k != "pinned"}),
                                     definitions, {"min_support": 2})
        self.assertEqual(no_pins.pinned, {})                               # counts with no pins (an older shape)


if __name__ == "__main__":
    unittest.main()
