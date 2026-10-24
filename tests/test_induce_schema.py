"""Schema induction (040_induce_schema), the stages code decides: matching
the model's labels, merging synonyms (chains, cycles, invalid merges),
counting support, and building the schema from the evidence."""
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
from common import llm                            # noqa: E402


def texts(*items):
    """Triples with texts [(id, maintainer, title, describes_class, [(s, p, o), ...])]."""
    return SimpleNamespace(texts=[{"id": i, "maintainer": m, "title": t, "describes_class": d,
                                   "triple_instances": [{"subject": s, "predicate": p, "object": o} for s, p, o in tis]}
                                  for i, m, t, d, tis in items])


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


class Labeling(unittest.TestCase):

    def test_match(self):
        labels, missing = label._match(["MODIS", "Aqua  craft", "Terra", "Aura"],
                                       {"MODIS": "Instrument", "aqua craft": "Spacecraft", "Terra": " ", "Aura": 3,
                                        "extra": "Ignored"})
        self.assertEqual(labels, {"MODIS": "Instrument", "Aqua  craft": "Spacecraft"})
        self.assertEqual(missing, ["Terra", "Aura"])
        self.assertEqual(label._match(["a"], "not a dict"), ({}, ["a"]))

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
    return SimpleNamespace(of={"entity": entity, "predicate": predicate},
                           merged_into={"entity": merged or {}, "predicate": {}})


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
        self.c = count.count_support(self.triples, labels_for(entity, predicate, merged={"Sensor": "Instrument"}))

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
        folds = {f["into"]: f["folded"] for f in self.c.spelling_folds}
        self.assertEqual(folds["Instrument"], ["Instrument", "instrument"])
        self.assertEqual(folds["Spacecraft"], ["Space craft", "Spacecraft"])        # the most frequent spelling

    def test_unlabeled_costs_only_its_own(self):
        self.assertEqual(self.c.unlabeled_slots, {"object": 1})              # Mystery
        self.assertEqual(len(self.c.patterns), 1)

    def test_titles_count(self):
        ds = self.entry("entity_classes", "Dataset")
        self.assertEqual((ds["support"], ds["examples"]), (2, ["MODIS L2", "AIRS L1"]))
        self.assertEqual((self.c.texts_with_triple_instances, self.c.texts_with_describes_class), (2, 2))

    def test_predicate_examples_are_facts(self):
        """A predicate's examples are the triple instances that most often state it: they show its subject and
        object, which its definition must say."""
        self.assertEqual(self.entry("predicates", "ABOARD")["examples"][0], "MODIS -- is aboard -- Aqua")
        self.assertIn("AIRS -- flies on -- Aqua", self.entry("predicates", "ABOARD")["examples"])


class Checking(unittest.TestCase):

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
        self.assertIn("label ORIGINATES_FROM -> merged into From (stage 4) -> spelling fold to FROM (stage 5) = "
                      "FROM: DEFERRED (too vague: says nothing about what kind of origin); support 2, 2 maintainer(s)",
                      out)
        self.assertIn("label FROM = FROM: DEFERRED", out)    # an entity class merge of the same word isn't used
        self.assertIn("UNVERIFIED (source_text)", out)
        self.assertNotIn("MODIS", out)
        self.assertIn("     2  FROM: DEFERRED", out)
        self.assertIn("     1  (unverified): left out", out)

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
