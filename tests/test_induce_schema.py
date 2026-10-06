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


if __name__ == "__main__":
    unittest.main()
