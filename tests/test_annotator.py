"""The annotation tool (helpers/annotator/server.py), through its HTTP API,
in a temporary copy of the repository: opening and saving a batch, adding
to the hand-built schema, the translation table, the schema additions, and
partial pair reviews. Nothing in the real annotations/ is touched."""
import csv
import json
import shutil
import sys
import threading
import unittest
import urllib.error
import urllib.request

from support import temp_repo

TMP = temp_repo(annotations=True)
sys.path[:0] = [str(TMP), str(TMP / "helpers")]
from annotator import server                      # noqa: E402
from common import component_class_mapping, ground_truth, partial_reviews, schema_io   # noqa: E402

HAND = """ENTITY CLASSES
--------------
Instrument        a device that takes measurements
Spacecraft        a vehicle in space
Dataset           a collection of data

PREDICATES
----------
ABOARD            is carried on
                  Instrument -> Spacecraft
"""

RESULTS = TMP / "outputs" / "intermediate_results"
RECORDS = {"r0": "MODIS aboard Aqua.", "r1": "AIRS aboard Aqua; Aqua orbits Earth.", "r2": "No facts here.",
           "r3": "CERES aboard Terra."}
POOL = ["r0", "r1", "r2", "r3"] + [f"p{i}" for i in range(4, 9)] + ["r8"]      # r8: position 9, tuning


def setUpModule():
    (TMP / "annotations" / "schema_derived_from_manual_annotation.txt").write_text(HAND, encoding="utf-8")
    for step in ("020_clean", "030_split", "050_annotate", "060_extract", "070_evaluate"):
        (RESULTS / step).mkdir(parents=True)
    with open(RESULTS / "020_clean" / "records.jsonl", "w", encoding="utf-8") as fh:
        for rid, notes in RECORDS.items():
            fh.write(json.dumps({"id": rid, "title": f"Title {rid}", "notes": notes, "maintainer": "m"}) + "\n")
    pool = [{"id": rid, "position": i, "part": "held-out" if i == 8 else "tuning"} for i, rid in enumerate(POOL)]
    pool[3]["part"] = "held-out"                                                   # r3: held-out, for the tests
    (RESULTS / "030_split" / "splits.json").write_text(json.dumps({"ground_truth_candidates": {"records": pool}}))
    rows = [["r0", "r0", "CatalogEntry", "DESCRIBES", "Title r0", "Dataset", "(record structure)"],
            ["r0", "MODIS", "Instrument", "ABOARD", "Aqua", "Spacecraft", "MODIS aboard Aqua"],
            ["r1", "r1", "CatalogEntry", "DESCRIBES", "Title r1", "X", "(record structure)"],
            ["r1", "Aqua", "Spacecraft", "ORBITS", "Earth", "Planet", "Aqua orbits Earth"],
            ["r2", "r2", "CatalogEntry", "DESCRIBES", "Title r2", "Dataset", "(record structure)"],
            ["r3", "CERES", "Instrument", "ABOARD", "Terra", "Spacecraft", "CERES aboard Terra"]]
    with open(RESULTS / "050_annotate" / "drafted_triples_batch0.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(ground_truth.COLUMNS[:-1] + [ground_truth.DRAFTED_BY, "flags", "origin"])
        w.writerows(r + ["test-model", "", ""] for r in rows)                  # drafted_by: as 050 writes it
    global SERVER
    SERVER = server.serve(0)
    threading.Thread(target=SERVER.serve_forever, daemon=True).start()


def tearDownModule():
    SERVER.shutdown()
    SERVER.server_close()
    shutil.rmtree(TMP)


def url(path):
    return f"http://127.0.0.1:{SERVER.server_address[1]}{path}"


def get(path):
    try:
        return json.load(urllib.request.urlopen(url(path)))
    except urllib.error.HTTPError as e:
        with e:
            return {"error": json.load(e)["error"]}


def post(path, body):
    req = urllib.request.Request(url(path), json.dumps(body).encode(), {"Content-Type": "application/json"})
    try:
        return json.load(urllib.request.urlopen(req))
    except urllib.error.HTTPError as e:
        with e:
            return {"error": json.load(e)["error"]}


def gt_rows():
    with open(TMP / "annotations" / "ground_truth" / "batch_000.csv", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


class A_Paths(unittest.TestCase):

    def test_never_the_real_repository(self):
        for path in (server.ANNOTATIONS_DIR, server.RESULTS_DIR, server.HAND_SCHEMA, server.MAPPING_PATH,
                     server.ADDITIONS, server.REVIEWS_PATH, server.GROUND_TRUTH_DIR):
            self.assertTrue(path.resolve().is_relative_to(TMP.resolve()), path)

    def test_every_check_has_a_message(self):
        from common import validate
        codes = set(validate.ERRORS) | set(validate.FLAGS) | {
            "subject_class_not_in_schema", "object_class_not_in_schema", "predicate_not_in_schema",
            "pattern_not_in_schema", "describes_undecided", "describes_class_not_in_schema",
            "describes_subject_not_id", "empty"}
        self.assertEqual(codes, set(server.MESSAGES))

    def test_page_and_help(self):
        page = urllib.request.urlopen(url("/")).read().decode("utf-8")
        self.assertIn("<html", page.lower())
        for view in server.HELP_SECTIONS:
            self.assertTrue(get(f"/api/help?view={view}")["markdown"].startswith("#"), view)
        self.assertIn("error", get("/api/help?view=nope"))


class B_Batch(unittest.TestCase):

    def test_1_open_copies_the_draft(self):
        b = get("/api/batch?n=0")
        self.assertEqual([r["id"] for r in b["records"]], ["r0", "r1", "r2", "r3"])
        self.assertEqual(len(gt_rows()), 6)
        self.assertEqual({r["drafted_by"] for r in gt_rows()}, {"test-model"})   # the copy keeps who drafted each row
        r1 = b["records"][1]
        codes = [p["code"] for row in r1["rows"] for p in row["problems"]]
        self.assertIn("describes_undecided", codes)
        offers = [p["add"] for row in r1["rows"] for p in row["problems"] if p["add"]]
        self.assertIn({"entry_type": "predicate", "component_class": "ORBITS"}, offers)
        self.assertIn({"entry_type": "entity class", "component_class": "Planet"}, offers)
        self.assertFalse(any(o["entry_type"] == "pattern" for o in offers))   # Planet isn't in the schema yet

    def test_2_save(self):
        b = get("/api/batch?n=0")
        recs = b["records"]
        recs[0]["finished"] = True
        recs[0]["rows"][0]["subject"] = "typo"                                 # the DESCRIBES row: put back to the id
        recs[0]["rows"].append({"subject": "", "predicate": "", "object": ""})  # a row not filled in
        recs[1]["finished"] = True
        recs[1]["rows"][0]["object_class"] = "Dataset"
        recs[2]["finished"] = True
        recs[2]["rows"] = []                                                   # states no facts
        recs[3]["rows"][0]["predicate"] = ""                                   # incomplete
        problems = post("/api/save", {"n": 0, "records": recs})["problems"]
        self.assertEqual([len(p) for p in problems], [3, 2, 0, 1])               # one list per row sent
        self.assertEqual([[p["code"] for p in row] for row in problems[0]], [[], [], ["empty"]])
        self.assertEqual([p["code"] for p in problems[3][0]], ["empty"])
        rows = gt_rows()
        self.assertEqual([r["id"] for r in rows], ["r0", "r0", "r1", "r1", "r2", "r3"])
        self.assertEqual(rows[0]["subject"], "r0")
        self.assertEqual(rows[4], {**{c: "" for c in ground_truth.FILE_COLUMNS}, "id": "r2", "all_facts_extracted": "1"})
        self.assertEqual([r["drafted_by"] for r in rows], ["test-model"] * 4 + ["", "test-model"])  # kept; empty on r2's
                                                                                                # row the tool wrote
        self.assertEqual([r["all_facts_extracted"] for r in rows], ["1", "1", "1", "1", "1", "0"])
        gt = ground_truth.read_ground_truth(TMP / "annotations" / "ground_truth")
        self.assertEqual(gt.problems, [])
        self.assertTrue(gt.records["r2"]["finished"])
        listed = get("/api/batches")["batches"]
        self.assertEqual(listed, [{"n": 0, "draft": "drafted_triples_batch0.csv", "ground_truth": "batch_000.csv",
                                   "records": 4, "finished": 3}])

    def test_3_missing_batch(self):
        self.assertIn("error", get("/api/batch?n=7"))


class C_HandSchema(unittest.TestCase):

    def test_adds(self):
        hand = TMP / "annotations" / "schema_derived_from_manual_annotation.txt"
        gaps = get("/api/gaps")
        self.assertEqual({(g["entry_type"], g["component_class"], g["uses"]) for g in gaps["component_classes"]},
                         {("entity class", "Planet", 1), ("predicate", "ORBITS", 1)})
        before = hand.read_bytes()
        self.assertIn("error", post("/api/hand/add", {"entry_type": "entity class", "component_class": "spacecraft",
                                                      "definition": "again"}))
        self.assertIn("error", post("/api/hand/add", {"entry_type": "entity class", "component_class": "Planet",
                                                      "definition": " "}))
        self.assertIn("error", post("/api/hand/add", {"entry_type": "nonsense"}))
        self.assertEqual(hand.read_bytes(), before)
        added = post("/api/hand/add", {"entry_type": "entity class", "component_class": "Planet", "definition": "a planet"})
        self.assertIn("source: ground truth tuning #1", added["added"])
        post("/api/hand/add", {"entry_type": "predicate", "component_class": "ORBITS", "definition": "goes around"})
        gaps = get("/api/gaps")
        self.assertEqual(gaps["component_classes"], [])
        self.assertEqual([(p["subject_class"], p["predicate"], p["object_class"]) for p in gaps["patterns"]],
                         [("Spacecraft", "ORBITS", "Planet")])
        post("/api/hand/add", gaps["patterns"][0])
        self.assertEqual(get("/api/gaps"), {"file": gaps["file"], "component_classes": [], "patterns": []})
        s = schema_io.read_hand_schema(hand)
        self.assertEqual(s["sources"]["entity_classes"], {"Planet": "ground truth tuning #1"})
        self.assertIn(("Spacecraft", "ORBITS", "Planet"), s["patterns"])
        b = get("/api/batch?n=0")
        flags = [p["code"] for rec in b["records"] for row in rec["rows"] for p in row["problems"] if p["type"] == "flag"
                 and p["code"].endswith("_in_schema")]
        self.assertEqual(flags, [])

    def test_held_out_source_named(self):
        rows = gt_rows()
        rows[-1]["object_class"] = "Moonlet"                                  # r3: held-out
        with open(TMP / "annotations" / "ground_truth" / "batch_000.csv", "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, ground_truth.FILE_COLUMNS)
            w.writeheader()
            w.writerows(rows)
        added = post("/api/hand/add", {"entry_type": "entity class", "component_class": "Moonlet", "definition": "small"})
        self.assertIn("source: ground truth held-out #3", added["added"])


class D_Mapping(unittest.TestCase):

    def setUp(self):
        self.path = TMP / "annotations" / "component_class_mapping.csv"
        cols = component_class_mapping.COLUMNS
        rows = [["entity class", "Satellite", "Spacecraft", "", "yes", "an old definition"],
                ["predicate", "MOUNTED_ON", "", "", "", ""],
                ["entity class", "Craft", "(none)", "", "", ""],
                ["entity class", "craft", "Spacecraft", "", "", ""]]
        with open(self.path, "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(cols)
            w.writerows(rows)
        (RESULTS / "060_extract" / "schema_used.json").write_text(json.dumps(
            {"entity_classes": [{"component_class": "Satellite", "definition": "an orbiting craft"},
                                {"component_class": "Craft", "definition": "a craft"}],
             "predicates": [{"component_class": "MOUNTED_ON", "definition": "sits on"}]}))

    def read(self):
        return component_class_mapping.read_mapping(self.path)

    def test_view(self):
        v = get("/api/mapping")
        self.assertTrue(v["found"])
        self.assertEqual([r["stale"] for r in v["rows"]], [True, False, False, False])
        self.assertEqual([r["repeated"] for r in v["rows"]], [False, False, True, True])
        self.assertEqual(v["rows"][0]["crt_definition"], "an orbiting craft")

    def test_save(self):
        sent = [{"kind": "entity class", "component_class_from_past_or_crt_schema": "Satellite",
                 "component_class_in_gtt": "Spacecraft", "checked": "yes", "keep_definition": True},
                {"kind": "predicate", "component_class_from_past_or_crt_schema": "MOUNTED_ON",
                 "component_class_in_gtt": "aboard", "checked": "yes", "swap_subject_and_object": "yes"}]
        self.assertEqual(post("/api/mapping/save", {"rows": sent}), {"saved": True})
        rows = self.read()
        self.assertEqual(rows[0]["definition_from_past_or_crt_schema"], "an old definition")   # still stale
        self.assertEqual((rows[1]["component_class_in_gtt"], rows[1]["swap_subject_and_object"],
                          rows[1]["definition_from_past_or_crt_schema"]), ("ABOARD", "yes", "sits on"))
        self.assertEqual(len(rows), 4)                                         # rows after the sent ones kept
        sent[0].pop("keep_definition")
        post("/api/mapping/save", {"rows": sent})
        self.assertEqual(self.read()[0]["definition_from_past_or_crt_schema"], "an orbiting craft")

    def test_stale_gtt(self):
        """The hand-built schema defines Spacecraft as "a vehicle in space"; the row stored another definition."""
        cols = component_class_mapping.COLUMNS
        with open(self.path, "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(cols)
            w.writerow(["entity class", "Satellite", "Spacecraft", "no", "yes", "an orbiting craft", "an old meaning"])
            w.writerow(["entity class", "Craft", "Spacecraft", "no", "yes", "a craft", "a vehicle in space"])
        v = get("/api/mapping")
        self.assertEqual([(r["stale"], r["stale_gtt"]) for r in v["rows"]], [(False, True), (False, False)])
        sent = [{"kind": "entity class", "component_class_from_past_or_crt_schema": n, "component_class_in_gtt": "Spacecraft",
                 "checked": "yes", "keep_definition": True} for n in ("Satellite", "Craft")]
        post("/api/mapping/save", {"rows": sent})
        self.assertEqual(self.read()[0]["definition_in_gtt"], "an old meaning")              # not ticked: still stale
        sent[0].pop("keep_definition")
        post("/api/mapping/save", {"rows": sent})
        self.assertEqual(self.read()[0]["definition_in_gtt"], "a vehicle in space")          # ticked: stores it
        self.assertFalse(get("/api/mapping")["rows"][0]["stale_gtt"])

    def test_refusals(self):
        before = self.path.read_bytes()
        bad_name = [{"kind": "entity class", "component_class_from_past_or_crt_schema": "Satellite",
                     "component_class_in_gtt": "Rocket", "checked": "yes"}]
        self.assertIn("isn't an entity class", post("/api/mapping/save", {"rows": bad_name})["error"])
        moved = [{"kind": "predicate", "component_class_from_past_or_crt_schema": "Satellite"}]
        self.assertIn("reload", post("/api/mapping/save", {"rows": moved})["error"])
        self.assertIn("extra rows", post("/api/mapping/delete", {"line": 2, "kind": "entity class",
                                                                 "component_class": "Satellite"})["error"])
        self.assertIn("reload", post("/api/mapping/delete", {"line": 4, "kind": "entity class",
                                                             "component_class": "Satellite"})["error"])
        self.assertEqual(self.path.read_bytes(), before)

    def test_automatic_row_can_be_changed(self):
        # a row accepted automatically (same spelling) keeps that status unchanged; changed by hand, it needs checking
        cols = component_class_mapping.COLUMNS
        with open(self.path, "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(cols)
            w.writerows([["entity class", "Spacecraft", "Spacecraft", "", "same component class", ""],
                         ["entity class", "Instrument", "Instrument", "", "same component class", ""]])
        sent = [{"kind": "entity class", "component_class_from_past_or_crt_schema": "Spacecraft",
                 "component_class_in_gtt": "Spacecraft", "checked": "same component class"},
                {"kind": "entity class", "component_class_from_past_or_crt_schema": "Instrument",
                 "component_class_in_gtt": "Spacecraft", "checked": "same component class"}]   # an old page's status
        self.assertEqual(post("/api/mapping/save", {"rows": sent}), {"saved": True})
        self.assertEqual([(r["component_class_in_gtt"], r["checked"]) for r in self.read()],
                         [("Spacecraft", "same component class"), ("Spacecraft", "no")])

    def test_delete_repeat(self):
        self.assertEqual(post("/api/mapping/delete", {"line": 5, "kind": "entity class", "component_class": "craft"}),
                         {"deleted": True})
        self.assertEqual([r["component_class_from_past_or_crt_schema"] for r in self.read()],
                         ["Satellite", "MOUNTED_ON", "Craft"])


class E_Additions(unittest.TestCase):

    path = TMP / "annotations" / "schema_additions.txt"

    def setUp(self):
        self.path.write_text("# my comments\n# kept\n\nENTITY CLASSES\n--------------\n", encoding="utf-8")

    def test_save_and_view(self):
        entries = [{"entry_type": "entity class", "component_class": "Probe", "definition": "a  small craft",
                    "source": "mentor"},
                   {"entry_type": "predicate", "component_class": "CARRIES", "definition": "carries",
                    "source": "ground truth tuning #0", "patterns": [["Spacecraft", "Instrument"]]},
                   {"entry_type": "pattern", "subject_class": "Probe", "predicate": "ABOARD", "object_class": "Spacecraft",
                    "source": "ground truth tuning #1"}]
        self.assertEqual(post("/api/additions/save", {"entries": entries}), {"saved": True})
        text = self.path.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("# my comments\n# kept\n"))
        view = get("/api/additions")
        self.assertEqual(view["unread"], [])
        self.assertEqual(view["entries"], [
            {**entries[0], "definition": "a small craft", "patterns": []}, entries[1], entries[2]])

    def test_refusals(self):
        before = self.path.read_bytes()
        cases = {"held-out": {"entry_type": "entity class", "component_class": "Probe", "definition": "d",
                              "source": "ground truth tuning #3"},
                 "needs a source": {"entry_type": "entity class", "component_class": "Probe", "definition": "d"},
                 "one word": {"entry_type": "entity class", "component_class": "Two words", "definition": "d", "source": "x"},
                 "needs a one-line definition": {"entry_type": "predicate", "component_class": "P", "source": "x"},
                 "one word each": {"entry_type": "pattern", "subject_class": "A B", "predicate": "P", "object_class": "C",
                                   "source": "x"}}
        for why, entry in cases.items():
            with self.subTest(why=why):
                self.assertIn(why, post("/api/additions/save", {"entries": [entry]})["error"])
                self.assertIn(why, post("/api/additions/check", entry)["problem"])
        twice = [{"entry_type": "pattern", "subject_class": "A", "predicate": "P", "object_class": "B", "source": "x"},
                 {"entry_type": "pattern", "subject_class": "a", "predicate": "p", "object_class": "b", "source": "y"}]
        self.assertIn("twice", post("/api/additions/save", {"entries": twice})["error"])
        self.assertEqual(self.path.read_bytes(), before)

    def test_unread_line_blocks_saving(self):
        self.path.write_text("ENTITY CLASSES\n--------------\nTwo words here\n", encoding="utf-8")
        self.assertIn("can't read", post("/api/additions/save", {"entries": []})["error"])


class F_Partial(unittest.TestCase):

    def test_reviews(self):
        compared = RESULTS / "070_evaluate" / "compared_triples.csv"
        cols = ["record_id", "status"] + [f"{w}_{s}" for w in ("ground_truth", "translated")
                                          for s in ("subject", "predicate", "object")]
        with open(compared, "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, cols)
            w.writeheader()
            for rid in ("r0", "r3"):
                w.writerow({"record_id": rid, "status": "partial pair", "ground_truth_subject": "MODIS",
                            "ground_truth_predicate": "ABOARD", "ground_truth_object": "Aqua",
                            "translated_subject": "MODIS Terra", "translated_predicate": "ABOARD",
                            "translated_object": "Aqua"})
        items = get("/api/partial")["items"]
        self.assertEqual([i["record_id"] for i in items], ["r0"])           # held-out r3: not shown
        item = {k: v for k, v in items[0].items() if k in partial_reviews.COLUMNS}
        self.assertEqual(post("/api/partial/review", {**item, "verdict": "not the same fact"}), {"saved": True})
        self.assertEqual(post("/api/partial/review", {**item, "verdict": "same fact"}), {"saved": True})
        self.assertEqual(list(partial_reviews.read_reviews(server.REVIEWS_PATH).values()), ["same fact"])
        post("/api/partial/review", {**item, "verdict": ""})
        self.assertEqual(partial_reviews.read_reviews(server.REVIEWS_PATH), {})
        self.assertIn("held-out", post("/api/partial/review", {**item, "record_id": "r3", "verdict": "same fact"})["error"])
        self.assertIn("verdict", post("/api/partial/review", {**item, "verdict": "maybe"})["error"])


class G_Vocabulary(unittest.TestCase):
    """The Ground truth vocabulary view: definitions, renaming, merging, every file at once or none."""

    GT_ROWS = [["r0", "r0", "CatalogEntry", "DESCRIBES", "Title r0", "Satelite", "(record structure)", "1", "m"],
               ["r0", "MODIS", "Instrument", "ABOARD", "Aqua", "Satelite", "MODIS aboard Aqua", "1", "m"],
               ["r1", "AIRS", "Instrument", "aboard", "Aqua", "Spacecraft", "AIRS aboard Aqua", "1", "m"],
               ["r1", "Aqua", "satelite", "ORBITS", "Earth", "Planet", "Aqua orbits Earth", "1", "m"]]
    HAND = HAND + "ORBITS            goes around\n                  Spacecraft -> Planet\n" \
        .replace("Spacecraft -> Planet", "Satelite -> Planet")

    def setUp(self):
        self.files = [TMP / "annotations" / "ground_truth" / "batch_000.csv", server.HAND_SCHEMA,
                      server.MAPPING_PATH, server.REVIEWS_PATH]
        self.saved = {p: p.read_bytes() if p.exists() else None for p in self.files}
        with open(self.files[0], "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(ground_truth.FILE_COLUMNS)
            w.writerows(self.GT_ROWS)
        server.HAND_SCHEMA.write_text(self.HAND.replace("Dataset           a collection of data",
                                                        "Dataset           a collection of data\n"
                                                        "Satelite          a craft in orbit"), encoding="utf-8")
        cols = component_class_mapping.COLUMNS
        with open(server.MAPPING_PATH, "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(cols)
            w.writerow(["entity class", "Satellite", "Satelite", "no", "yes", "an orbiting craft", "a craft in orbit"])
            w.writerow(["predicate", "MOUNTED_ON", "ABOARD", "no", "yes", "sits on", "is carried on"])
        with open(server.REVIEWS_PATH, "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(partial_reviews.COLUMNS)
            w.writerow(["r1", "AIRS", "ORBITS", "Aqua", "the AIRS", "ORBITS", "Aqua", "same fact"])

    def tearDown(self):
        for p, content in self.saved.items():
            if content is None:
                p.unlink(missing_ok=True)
            else:
                p.write_bytes(content)

    def snapshot(self):
        return {p: p.read_bytes() for p in self.files if p.exists()}

    def test_view(self):
        v = get("/api/vocab")["vocabulary"]
        sat = next(e for e in v["entity class"] if e["component_class"] == "Satelite")
        self.assertEqual((sat["definition"], sat["in_hand"], sat["uses"], sat["files"], sat["translated_from"]),
                         ("a craft in orbit", True, 3, ["batch_000.csv"], ["Satellite"]))
        planet = next(e for e in v["entity class"] if e["component_class"] == "Planet")
        self.assertFalse(planet["in_hand"])                                   # coined, no definition

    def test_plan_writes_nothing(self):
        before = self.snapshot()
        plan = post("/api/vocab/plan", {"kind": "entity class", "old": "Satelite", "new": "Spacecraft"})
        self.assertTrue(plan["merge"])
        self.assertEqual([c["file"] for c in plan["changes"]],
                         ["annotations/ground_truth/batch_000.csv", f"annotations/{server.HAND_SCHEMA.name}",
                          f"annotations/{server.MAPPING_PATH.name}"])
        self.assertIn("3 cell(s)", plan["changes"][0]["what"])
        self.assertTrue(any("stale" in n for n in plan["notes"]))             # Spacecraft's definition differs
        self.assertEqual(self.snapshot(), before)

    def test_merge_entity_class(self):
        done = post("/api/vocab/apply", {"kind": "entity class", "old": "satelite", "new": "spacecraft"})
        self.assertEqual((done["old"], done["new"], done["merge"]), ("Satelite", "Spacecraft", True))
        rows = gt_rows()
        self.assertEqual([r["object_class"] for r in rows][:2], ["Spacecraft", "Spacecraft"])   # DESCRIBES too
        self.assertEqual(rows[3]["subject_class"], "Spacecraft")                                 # any spelling
        self.assertEqual([r["subject"] for r in rows], ["r0", "MODIS", "AIRS", "Aqua"])          # nothing else
        self.assertEqual([r["drafted_by"] for r in rows], ["m"] * 4)
        hand = schema_io.read_hand_schema(server.HAND_SCHEMA)
        self.assertNotIn("Satelite", hand["entity_classes"])
        self.assertEqual(hand["entity_classes"]["Spacecraft"], "a vehicle in space")
        self.assertIn(("Spacecraft", "ORBITS", "Planet"), hand["patterns"])
        table = component_class_mapping.read_mapping(server.MAPPING_PATH)
        self.assertEqual(table[0]["component_class_in_gtt"], "Spacecraft")
        self.assertEqual(table[0]["definition_in_gtt"], "a craft in orbit")    # kept: so the row is stale
        self.assertTrue(get("/api/mapping")["rows"][0]["stale_gtt"])
        self.assertEqual(table[1]["component_class_in_gtt"], "ABOARD")          # other rows untouched

    def test_rename_predicate_keeps_reviews(self):
        done = post("/api/vocab/apply", {"kind": "predicate", "old": "ORBITS", "new": "CIRCLES"})
        self.assertFalse(done["merge"])
        self.assertEqual(gt_rows()[3]["predicate"], "CIRCLES")
        self.assertIn("CIRCLES", schema_io.read_hand_schema(server.HAND_SCHEMA)["predicates"])
        reviews = partial_reviews.read_reviews(server.REVIEWS_PATH)
        self.assertEqual(list(reviews.values()), ["same fact"])
        self.assertEqual(list(reviews)[0][2], partial_reviews.norm_text("CIRCLES"))

    def test_merge_predicate_moves_patterns(self):
        post("/api/vocab/apply", {"kind": "predicate", "old": "ORBITS", "new": "ABOARD"})
        hand = schema_io.read_hand_schema(server.HAND_SCHEMA)
        self.assertNotIn("ORBITS", hand["predicates"])
        self.assertEqual(sorted(p for p in hand["patterns"] if p[1] == "ABOARD"),
                         [("Instrument", "ABOARD", "Spacecraft"), ("Satelite", "ABOARD", "Planet")])
        self.assertEqual([r["predicate"] for r in gt_rows()], ["DESCRIBES", "ABOARD", "aboard", "ABOARD"])

    def test_conflicting_reviews_refused(self):
        with open(server.REVIEWS_PATH, "a", encoding="utf-8", newline="") as fh:
            csv.writer(fh).writerow(["r1", "AIRS", "ABOARD", "Aqua", "the AIRS", "ABOARD", "Aqua", "not the same fact"])
        before = self.snapshot()
        self.assertIn("different verdicts",
                      post("/api/vocab/apply", {"kind": "predicate", "old": "ORBITS", "new": "ABOARD"})["error"])
        self.assertEqual(self.snapshot(), before)

    def test_refusals(self):
        before = self.snapshot()
        for body, words in [({"kind": "entity class", "old": "Rocket", "new": "Craft"}, "isn't an entity class"),
                            ({"kind": "entity class", "old": "Satelite", "new": "Space ship"}, "one word"),
                            ({"kind": "entity class", "old": "Satelite", "new": "Satelite"}, "the same"),
                            ({"kind": "entity class", "old": "Satelite", "new": "CatalogEntry"}, "written by code"),
                            ({"kind": "thing", "old": "Satelite", "new": "Craft"}, "kind")]:
            with self.subTest(body=body):
                self.assertIn(words, post("/api/vocab/plan", body)["error"])
                self.assertIn(words, post("/api/vocab/apply", body)["error"])
        self.assertEqual(self.snapshot(), before)

    def test_all_files_or_none(self):
        before = self.snapshot()
        real = server.os.replace
        calls = []

        def fail_second(src, dst):
            calls.append(dst)
            if len(calls) == 2:
                raise OSError("disk full")
            return real(src, dst)

        server.os.replace = fail_second
        try:
            self.assertIn("disk full", post("/api/vocab/apply", {"kind": "entity class", "old": "Satelite",
                                                                 "new": "Spacecraft"})["error"])
        finally:
            server.os.replace = real
            for p in self.files:
                p.with_name(p.name + ".part").unlink(missing_ok=True)
        self.assertEqual(self.snapshot(), before)

    def test_define(self):
        done = post("/api/vocab/define", {"kind": "predicate", "component_class": "aboard", "definition": "is  anywhere on"})
        self.assertEqual(done, {"saved": True, "stale": ["MOUNTED_ON"]})
        hand = schema_io.read_hand_schema(server.HAND_SCHEMA)
        self.assertEqual(hand["predicates"]["ABOARD"], "is anywhere on")
        self.assertEqual(hand["patterns"].count(("Instrument", "ABOARD", "Spacecraft")), 1)
        self.assertIn("add it first", post("/api/vocab/define", {"kind": "entity class", "component_class": "Planet",
                                                                 "definition": "a world"})["error"])
        self.assertIn("definition", post("/api/vocab/define", {"kind": "entity class", "component_class": "Dataset",
                                                               "definition": "  "})["error"])


if __name__ == "__main__":
    unittest.main()
