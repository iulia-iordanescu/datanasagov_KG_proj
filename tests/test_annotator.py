"""The annotation tool (helpers/annotator/server.py), through its HTTP API,
in a temporary copy of the repository: opening and saving a batch, adding
to the ground truth schema, the translation table, the schema additions, and
partial pair reviews. Nothing in the real annotations/ is touched."""
import csv
import json
import shutil
import sys
import threading
import unittest
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request
from unittest import mock

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
#: Where each stand-in record came from in the harvest (its _origin): r1's batch file is saved in HARVEST, r2's isn't.
ORIGINS = {"r1": ["010_harvest/batch_00000.json#r1"], "r2": ["010_harvest/batch_01000.json#r2"]}
HARVEST = TMP / "harvest_stand_in"                  # a stand-in for step 010's folder, so 010 itself looks not run
RAW_R1 = {"id": "r1", "name": "airs-aqua", "title": "Title r1", "notes": "AIRS aboard Aqua; Aqua orbits Earth.",
          "extras": [{"key": "harvest_source", "value": "ünïcode"}]}
POOL = ["r0", "r1", "r2", "r3"] +[f"p{i}" for i in range(4, 9)] + ["r8"]      # r8: position 9, tuning


def setUpModule():
    (TMP / "annotations" / "ground_truth_schema.txt").write_text(HAND, encoding="utf-8")
    for step in ("020_clean", "030_split", "050_annotate", "060_extract", "070_evaluate"):
        (RESULTS / step).mkdir(parents=True)
    with open(RESULTS / "020_clean" / "records.jsonl", "w", encoding="utf-8") as fh:
        for rid, notes in RECORDS.items():
            fh.write(json.dumps({"id": rid, "title": f"Title {rid}", "notes": notes, "maintainer": "m",
                                 **({"_origin": ORIGINS[rid]} if rid in ORIGINS else {})}) + "\n")
    HARVEST.mkdir()
    (HARVEST / "batch_00000.json").write_text(json.dumps({"request": "GET …", "records": [RAW_R1]}), encoding="utf-8")
    (HARVEST / "_manifest.json").write_text(json.dumps({"harvest_date": "2026-10-01"}), encoding="utf-8")
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


def checks_table_codes() -> set:
    """The codes in the first column of 050's table *Checks on each row* (050_annotate/050_annotate.md)."""
    import re
    text = (Path(__file__).resolve().parents[1] / "050_annotate" / "050_annotate.md").read_text(encoding="utf-8")
    section = text.split("### Checks on each row", 1)[1].split("\n## ", 1)[0]
    rows = [line for line in section.splitlines() if line.startswith("| `")]
    assert rows, "050_annotate.md: no table under *Checks on each row*"
    return {code for line in rows for code in re.findall(r"`([a-z_]+)`", line.split("|")[1])}


class A_Paths(unittest.TestCase):

    def test_never_the_real_repository(self):
        for path in (server.ANNOTATIONS_DIR, server.RESULTS_DIR, server.GROUND_TRUTH_SCHEMA, server.MAPPING_PATH,
                     server.ADDITIONS, server.REVIEWS_PATH, server.GROUND_TRUTH_DIR):
            self.assertTrue(path.resolve().is_relative_to(TMP.resolve()), path)

    def test_every_check_has_a_message(self):
        """Every check the tool shows has a message: all of them but stage 4's own and those on rows together."""
        from common import validate
        self.assertEqual(set(validate.ALL_CHECKS) - set(validate.GROUND_TRUTH_ERRORS) - set(validate.ROWS_FLAGS),
                         set(server.MESSAGES))
        self.assertEqual(len(validate.ALL_CHECKS), len(set(validate.ALL_CHECKS)))     # each code once

    def test_050_checks_table_lists_every_check(self):
        """050's guide, *Checks on each row*, the home of the checks' meanings: its Check column names exactly the
        check codes (common/common_helpers/validate.py, ALL_CHECKS)."""
        from common import validate
        self.assertEqual(checks_table_codes(), set(validate.ALL_CHECKS))
        self.assertLessEqual(set(ground_truth.ROW_ERRORS), set(validate.ALL_CHECKS))

    def test_dataset_subject_message(self):
        row = {"id": "r1", "subject": "radiance data", "subject_class": "Dataset", "predicate": "USES",
               "object": "pixels", "object_class": "Dataset", "source_text": "radiance data"}
        message = server._message("dataset_subject_not_title", row, [], "MODIS Snow")
        self.assertIn("(MODIS Snow)", message)
        self.assertIn("another dataset", message)

    def test_fonts(self):
        """The page's typefaces come from the tool itself (no network needed), and only its own .woff2 files."""
        r = urllib.request.urlopen(url("/fonts/LibreFranklin.woff2"))
        self.assertEqual(r.headers["Content-Type"], "font/woff2")
        self.assertGreater(len(r.read()), 10000)
        for bad in ("/fonts/OFL-LibreFranklin.txt", "/fonts/..%2Fserver.py", "/fonts/nope.woff2"):
            with self.subTest(bad=bad), self.assertRaises(urllib.error.HTTPError):
                urllib.request.urlopen(url(bad))

    def test_page_and_help(self):
        page = urllib.request.urlopen(url("/")).read().decode("utf-8")
        self.assertIn("<html", page.lower())
        for view in server.HELP_SECTIONS:
            self.assertTrue(get(f"/api/help?view={view}")["markdown"].startswith("#"), view)
        self.assertIn("error", get("/api/help?view=nope"))
        for view in ("mapping", "partial", "additions", "vocab"):                  # what the view is for, at its top
            intro = get(f"/api/help?view={view}")["intro"]
            self.assertTrue(intro and not intro.startswith("#"), view)              # the section's first paragraph
        batch = get("/api/help?view=batch")["markdown"]                            # with the tool's two lists
        self.assertIn("### What the tool can do", batch)
        self.assertIn("### What the tool can't do", batch)
        self.assertIn('id="intro"', page)
        st = get("/api/status")                                                    # the home page's What to do next
        self.assertEqual([s["step"] for s in st["steps"]][:2], ["010_harvest", "020_clean"])
        self.assertTrue(all(i["doc"].startswith("docs/upkeep.md#") for i in st["items"]))
        self.assertIn("drawNextUp()", page)
        self.assertIn("refreshDefinitions()", page)                            # a component class field's definition
        self.assertIn('showHelp("/api/guidelines")', page)                      # the rules, one click away while annotating
        terms = get("/api/terms")                                                  # a term's definition, on hover
        self.assertIn("ground truth schema", terms)
        self.assertNotIn("](", terms["ground truth schema"])                   # plain text: no Markdown links
        self.assertIn("pool position", terms)                                      # named in bold inside a definition
        self.assertEqual(get("/api/doc?path=annotations/guidelines.md")["file"], "annotations/guidelines.md")
        for outside in (".env", "../outside.md", "common/common_helpers/llm.py"):    # only .md files of the repository
            self.assertIn("error", get(f"/api/doc?path={outside}"), outside)
        g = get("/api/guidelines")
        self.assertEqual(g["file"], "annotations/guidelines.md")
        self.assertTrue(g["markdown"].startswith("# Annotation guidelines"))


class B_Batch(unittest.TestCase):

    def test_1_open_copies_the_draft(self):
        b = get("/api/batch?n=0")
        self.assertEqual([r["id"] for r in b["records"]], ["r0", "r1", "r2", "r3"])
        self.assertEqual(len(gt_rows()), 6)
        self.assertEqual({r["drafted_by"] for r in gt_rows()}, {"test-model"})   # the copy keeps who drafted each row
        # the page's list of component classes: every one offered has a definition entry, and coined ones are named
        self.assertEqual(sorted(b["definitions"]["entity_classes"]), b["entity_classes"])
        self.assertEqual(sorted(b["definitions"]["predicates"]), b["predicates"])
        self.assertEqual(set(b["coined"]), {"entity_classes", "predicates"})
        # the definition under each component class field: every component class the batch uses has an entry
        # (the describes triple's subject class and predicate are written by code: no field, no definition)
        for rec in b["records"]:
            for r in rec["rows"]:
                for key, kind in (("subject_class", "entity_classes"), ("predicate", "predicates"),
                                  ("object_class", "entity_classes")):
                    if r[key] and r[key] != "X" and (key == "object_class" or r["predicate"] != "DESCRIBES"):
                        self.assertIn(r[key], b["definitions"][kind], (rec["id"], key))
        # the pattern buttons' list: every pattern a ground truth triple uses
        used = {(r["subject_class"], r["predicate"], r["object_class"]) for rec in b["records"]
                for r in rec["rows"] if r["predicate"] not in ("", "DESCRIBES") and r["object_class"]}
        self.assertTrue(used)
        self.assertLessEqual(used, {tuple(p) for p in b["patterns"]})
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
        recs[0]["rows"][0]["subject"] = "typo"                                 # the describes triple: put back to the id
        recs[0]["rows"].append({"subject": "", "predicate": "", "object": ""})  # a row not filled in
        recs[1]["finished"] = True
        recs[1]["rows"][0]["object_class"] = "Dataset"
        recs[2]["finished"] = True
        recs[2]["rows"] = []                                                   # states no facts
        recs[3]["rows"][0]["predicate"] = ""                                   # incomplete
        saved = post("/api/save", {"n": 0, "records": recs})
        problems = saved["problems"]
        self.assertTrue(all(len(p) == 3 for p in saved["patterns"]))          # the pattern buttons' list, as saved
        self.assertEqual((saved["definitions"], saved["coined"]), (b["definitions"], b["coined"]))  # the definitions
                                                                    # under the fields, refreshed after each save
        self.assertEqual([len(p) for p in problems], [3, 2, 0, 1])               # one list per row sent
        # MODIS aboard Aqua: no chain links it to the catalog entry (r0, Title r0)
        self.assertEqual([[p["code"] for p in row] for row in problems[0]], [[], ["not_connected"], ["empty"]])
        self.assertEqual([p["code"] for p in problems[3][0]], ["empty", "not_connected"])   # r3 has no describes triple
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
        # saving again with nothing new leaves the file untouched
        path = TMP / "annotations" / "ground_truth" / "batch_000.csv"
        stamp = path.stat().st_mtime_ns
        post("/api/save", {"n": 0, "records": get("/api/batch?n=0")["records"]})
        self.assertEqual(path.stat().st_mtime_ns, stamp)
        listed = get("/api/batches")["batches"]
        self.assertEqual(listed, [{"n": 0, "draft": "drafted_triples_batch0.csv", "ground_truth": "batch_000.csv",
                                   "records": 4, "finished": 3}])

    def test_3_missing_batch(self):
        self.assertIn("error", get("/api/batch?n=7"))

    def test_not_connected(self):
        """A record whose ground truth triples form two pieces: the piece not linked to the catalog entry is
        flagged, row by row, naming its component instances; the piece linked to it (as evened out: "the Aqua
        satellite" is "Aqua satellite") isn't. The view and a save agree."""
        def row(s, p, o):
            return {**{c: "" for c in ground_truth.FILE_COLUMNS}, "id": "r1", "subject": s, "predicate": p, "object": o}
        rows = [{**row("r1", "DESCRIBES", "Title r1"), "subject_class": "CatalogEntry"},
                row("Title r1", "FROM", "the Aqua satellite"),
                row("AIRS", "ABOARD", "Aqua satellite"),
                row("Aqua", "ORBITS", "Earth"),                                # another piece
                row("Earth", "HAS", "Moon"),
                row("", "", ""),                                               # not filled in: skipped
                row("Sun", "", "")]                                            # no object: skipped
        expected = [[], [], [], ["not_connected"], ["not_connected"], [], []]
        view = server.record_view(server.Data(), "r1", rows, False)
        self.assertEqual([[p["code"] for p in r["problems"] if p["code"] == "not_connected"] for r in view["rows"]],
                         expected)
        self.assertIn('Not connected: "Aqua", "Earth", "Moon".', view["rows"][3]["problems"][-1]["message"])
        self.assertEqual([[p["code"] for p in found] for found in server.connection_problems("r1", rows)], expected)
        self.assertEqual(server.connection_problems("r1", rows[:1]), [[]])     # only the describes triple

    def test_record_links(self):
        """Suppose the stand-in record r1's batch file from the harvest of 2026-10-01 is on this computer, and r2's
        and r0's aren't (r2 names a batch file that isn't there; r0 names none). Then About this record gets, for r1,
        a link to its saved copy, with the harvest's date, and for r2 and r0 none (the page says "not on this
        computer"); every record gets the address of its web page in the live catalog, built from its id (nothing is
        fetched)."""
        with mock.patch.object(server, "HARVEST", HARVEST):
            data = server.Data()
            views = {rid: server.record_view(data, rid, [], False) for rid in ("r0", "r1", "r2")}
        self.assertEqual(views["r1"]["saved_copy"], {"url": "/api/raw_record?id=r1", "harvest_date": "2026-10-01"})
        self.assertIsNone(views["r2"]["saved_copy"])
        self.assertIsNone(views["r0"]["saved_copy"])
        self.assertEqual(views["r1"]["catalog_page_url"], "https://data.nasa.gov/dataset/r1")

    def test_raw_record(self):
        """Suppose r1's batch file from the harvest is on this computer, holding r1's entry as the catalog sent it.
        Then /api/raw_record?id=r1 answers with that entry exactly, as indented JSON. An id that isn't a record's
        (an unknown one, a path, an empty one) or a record whose batch file isn't here (r2, r0) gets an error, and
        no file is read."""
        with mock.patch.object(server, "HARVEST", HARVEST):
            answer = urllib.request.urlopen(url("/api/raw_record?id=r1"))
            body = answer.read().decode("utf-8")
            self.assertEqual(answer.headers["Content-Type"], "application/json; charset=utf-8")
            self.assertEqual(json.loads(body), RAW_R1)
            self.assertIn('\n  "name": "airs-aqua"', body)                      # indented, not on one line
            self.assertIn("ünïcode", body)
            for bad in ("nope", "../../annotations/ground_truth_schema.txt", "batch_00000.json", "", "r2", "r0"):
                with self.subTest(id=bad), self.assertRaises(urllib.error.HTTPError) as caught:
                    urllib.request.urlopen(url("/api/raw_record?id=" + urllib.parse.quote(bad, safe="")))
                caught.exception.close()
                self.assertEqual(caught.exception.code, 404)

    def test_not_in_source_but_elsewhere(self):
        """Suppose r1's text is "AIRS aboard Aqua; Aqua orbits Earth." and a ground truth triple's source text is
        "Aqua orbits Earth". Then a subject instance "AIRS" (elsewhere in the text) gets the "not in the source
        text" flag with the note, naming the subject instance, that it may be on purpose; "MODIS" (in neither) gets
        the flag without it. The same for the object instance: with source text "AIRS aboard", an object instance
        "Aqua" gets the note naming the object instance."""
        def problem(slot, subject, obj, source):
            row = {**{c: "" for c in ground_truth.FILE_COLUMNS}, "id": "r1", "subject": subject,
                   "subject_class": "Instrument", "predicate": "ABOARD", "object": obj,
                   "object_class": "Spacecraft", "source_text": source}
            found = {p["code"]: p["message"] for p in server.check_row(server.Data(), row, "Title r1")}
            return found[f"{slot}_not_in_source"], f"{slot}_not_in_text" in found
        note = (" However, the {} instance does appear elsewhere in the record's text, so it may be written this way "
                "on purpose, to follow a rule: e.g. rule 13 of \"Writing a classed triple\" (one wording for a thing "
                "within a record) or rule 2 of \"What counts as a fact\" (the title states facts too); if so, "
                "nothing to do.")
        message, not_in_text = problem("subject", "AIRS", "Aqua", "Aqua orbits Earth")
        self.assertFalse(not_in_text)
        self.assertEqual(message, server.MESSAGES["subject_not_in_source"] + note.format("subject"))
        message, not_in_text = problem("subject", "MODIS", "Aqua", "Aqua orbits Earth")
        self.assertTrue(not_in_text)
        self.assertEqual(message, server.MESSAGES["subject_not_in_source"])
        message, not_in_text = problem("object", "AIRS", "Aqua", "AIRS aboard")
        self.assertFalse(not_in_text)
        self.assertEqual(message, server.MESSAGES["object_not_in_source"] + note.format("object"))


class C_HandSchema(unittest.TestCase):

    def test_adds(self):
        hand = TMP / "annotations" / "ground_truth_schema.txt"
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
        self.assertEqual(gaps, {"file": gaps["file"], "component_classes": []})
        s = schema_io.read_ground_truth_schema(hand)
        self.assertEqual(s["sources"]["entity_classes"], {"Planet": "ground truth tuning #1"})
        # patterns are never added: the ground truth schema's include every one the ground truth uses, and a
        # pattern used for the first time is flagged, for a look (a wrong entity class or direction)
        self.assertIn("error", post("/api/hand/add", {"entry_type": "pattern", "predicate": "ORBITS",
                                                      "subject_class": "Spacecraft", "object_class": "Planet"}))
        self.assertNotIn(("Spacecraft", "ORBITS", "Planet"), s["patterns"])
        orbits = next(v for v in get("/api/vocab")["vocabulary"]["predicate"] if v["component_class"] == "ORBITS")
        self.assertEqual(orbits["patterns"], [["Spacecraft", "Planet"]])

        def schema_flags():
            b = get("/api/batch?n=0")
            return [p["code"] for rec in b["records"] for row in rec["rows"] for p in row["problems"]
                    if p["code"].endswith("_in_schema")]
        self.assertEqual(schema_flags(), ["pattern_not_in_schema"])           # its first use
        other = TMP / "annotations" / "ground_truth" / "batch_009.csv"
        row = next(r for r in gt_rows() if r["predicate"] == "ORBITS")
        with open(other, "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, ground_truth.FILE_COLUMNS)
            w.writeheader()
            w.writerow({**{c: row.get(c, "") for c in ground_truth.FILE_COLUMNS}, "id": "r-other"})
        try:
            self.assertEqual(schema_flags(), [])                              # used again elsewhere: no flag
        finally:
            other.unlink()

    def test_held_out_frozen(self):
        """The ground truth schema is frozen for held-out records (annotations/guidelines.md, Before you start): a
        component class a held-out record coins gets its own message and no button, and can't be added; nothing can be
        added while a held-out record is shown."""
        hand = TMP / "annotations" / "ground_truth_schema.txt"
        path = TMP / "annotations" / "ground_truth" / "batch_000.csv"
        saved, before = path.read_bytes(), hand.read_bytes()
        rows = gt_rows()
        rows[-1].update(subject="CERES", subject_class="Instrument", predicate="ABOARD", object="Terra",
                        object_class="Moonlet", source_text="CERES aboard Terra")      # r3: held-out
        rows[1]["object_class"] = "Comet"                                     # r0: tuning
        try:
            with open(path, "w", encoding="utf-8", newline="") as fh:
                w = csv.DictWriter(fh, ground_truth.FILE_COLUMNS)
                w.writeheader()
                w.writerows(rows)
            problem = next(p for rec in get("/api/batch?n=0")["records"] for row in rec["rows"] for p in row["problems"]
                           if p["code"] == "object_class_not_in_schema" and row["object_class"] == "Moonlet")
            self.assertIn("held-out record (pool position 3)", problem["message"])
            self.assertIn("annotations/left_out.md", problem["message"])
            self.assertIsNone(problem["add"])
            refused = post("/api/hand/add", {"entry_type": "entity class", "component_class": "Moonlet", "definition": "small"})
            self.assertIn("used by 1 held-out record(s): pool position 3 (r3)", refused["error"])
            shown = post("/api/hand/add", {"entry_type": "entity class", "component_class": "Comet", "definition": "a comet",
                                           "record": "r3"})
            self.assertIn("the record shown, r3 (pool position 3), is a held-out record", shown["error"])
            self.assertEqual(hand.read_bytes(), before)
            # a tuning record's coined component class keeps its button
            tuning = next(p for rec in get("/api/batch?n=0")["records"] for row in rec["rows"] for p in row["problems"]
                          if p["code"] == "object_class_not_in_schema" and row["object_class"] == "Comet")
            self.assertEqual(tuning["add"], {"entry_type": "entity class", "component_class": "Comet"})
        finally:
            path.write_bytes(saved)
            hand.write_bytes(before)


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
        """The ground truth schema defines Spacecraft as "a vehicle in space"; the row stored another definition."""
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
        self.assertIn("repeated rows", post("/api/mapping/delete", {"line": 2, "kind": "entity class",
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

    def test_missing_target_and_coined(self):
        """The dropdown offers only the ground truth schema file's component classes, as step 070 reads it: never a
        coined one (Comet: used in the ground truth, not in the file), and saving one is refused with what to do. A
        row whose target is missing is marked (never stale_gtt), and saving it unchanged keeps it. A row of a past
        schema only is never stale."""
        batch = TMP / "annotations" / "ground_truth" / "batch_000.csv"
        saved = batch.read_bytes()
        self.addCleanup(batch.write_bytes, saved)
        rows = gt_rows()
        rows[-1]["object_class"] = "Comet"
        with open(batch, "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, ground_truth.FILE_COLUMNS)
            w.writeheader()
            w.writerows(rows)
        cols = component_class_mapping.COLUMNS
        with open(self.path, "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(cols)
            w.writerows([["entity class", "Satellite", "Rocket", "no", "yes", "an orbiting craft", "a stored meaning"],
                         ["entity class", "OldThing", "Spacecraft", "no", "yes", "gone now", "a vehicle in space"]])
        v = get("/api/mapping")
        self.assertNotIn("Comet", [x["component_class"] for x in v["gtt"]["entity class"]])
        self.assertIn("Spacecraft", [x["component_class"] for x in v["gtt"]["entity class"]])
        self.assertEqual([(r["missing_target"], r["stale"], r["stale_gtt"]) for r in v["rows"]],
                         [(True, False, False), (False, False, False)])
        same = [{"kind": "entity class", "component_class_from_past_or_crt_schema": "Satellite",
                 "component_class_in_gtt": "Rocket", "checked": "yes", "keep_definition": True}]
        self.assertEqual(post("/api/mapping/save", {"rows": same}), {"saved": True})
        self.assertEqual(self.read()[0]["component_class_in_gtt"], "Rocket")
        before = self.path.read_bytes()
        coined = [dict(same[0], component_class_in_gtt="Comet")]
        said = post("/api/mapping/save", {"rows": coined})["error"]
        self.assertIn("only coined", said)
        self.assertIn("add it to the ground truth schema first", said)
        other = [dict(same[0], component_class_in_gtt="Moon")]
        self.assertIn("Pick one from the list", post("/api/mapping/save", {"rows": other})["error"])
        self.assertEqual(self.path.read_bytes(), before)

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
    """The Ground truth schema view: definitions, renaming, merging, every file at once or none."""

    GT_ROWS = [["r0", "r0", "CatalogEntry", "DESCRIBES", "Title r0", "Satelite", "(record structure)", "1", "m"],
               ["r0", "MODIS", "Instrument", "ABOARD", "Aqua", "Satelite", "MODIS aboard Aqua", "1", "m"],
               ["r1", "AIRS", "Instrument", "aboard", "Aqua", "Spacecraft", "AIRS aboard Aqua", "1", "m"],
               ["r1", "Aqua", "satelite", "ORBITS", "Earth", "Planet", "Aqua orbits Earth", "1", "m"]]
    HAND = HAND + "ORBITS            goes around\n                  Spacecraft -> Planet\n" \
        .replace("Spacecraft -> Planet", "Satelite -> Planet")

    def setUp(self):
        self.files = [TMP / "annotations" / "ground_truth" / "batch_000.csv", server.GROUND_TRUTH_SCHEMA,
                      server.MAPPING_PATH, server.REVIEWS_PATH]
        self.saved = {p: p.read_bytes() if p.exists() else None for p in self.files}
        with open(self.files[0], "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(ground_truth.FILE_COLUMNS)
            w.writerows(self.GT_ROWS)
        server.GROUND_TRUTH_SCHEMA.write_text(self.HAND.replace("Dataset           a collection of data",
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
        # the overview at the top of the page shows each predicate's patterns (an entity class has none)
        orbits = next(e for e in v["predicate"] if e["component_class"] == "ORBITS")
        self.assertEqual((orbits["patterns"], sat["patterns"]), ([["Satelite", "Planet"]], []))

    def test_held_out_shown_refused(self):
        before = self.snapshot()
        for path in ("/api/vocab/plan", "/api/vocab/apply"):
            r = post(path, {"kind": "entity class", "old": "Satelite", "new": "Satellite", "record": "r3"})
            self.assertIn("renaming or merging Satelite is refused", r["error"])
        r = post("/api/vocab/define", {"kind": "entity class", "component_class": "Satelite", "definition": "new", "record": "r3"})
        self.assertIn("changing the definition of Satelite is refused", r["error"])
        self.assertEqual(self.snapshot(), before)
        self.assertNotIn("error", post("/api/vocab/plan", {"kind": "entity class", "old": "Satelite", "new": "Satellite",
                                                           "record": "r0"}))

    def test_plan_writes_nothing(self):
        before = self.snapshot()
        plan = post("/api/vocab/plan", {"kind": "entity class", "old": "Satelite", "new": "Spacecraft"})
        self.assertTrue(plan["merge"])
        self.assertEqual([c["file"] for c in plan["changes"]],
                         ["annotations/ground_truth/batch_000.csv", f"annotations/{server.GROUND_TRUTH_SCHEMA.name}",
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
        hand = schema_io.read_ground_truth_schema(server.GROUND_TRUTH_SCHEMA)
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
        self.assertIn("CIRCLES", schema_io.read_ground_truth_schema(server.GROUND_TRUTH_SCHEMA)["predicates"])
        reviews = partial_reviews.read_reviews(server.REVIEWS_PATH)
        self.assertEqual(list(reviews.values()), ["same fact"])
        self.assertEqual(list(reviews)[0][2], partial_reviews.norm_text("CIRCLES"))

    def test_merge_predicate_moves_patterns(self):
        post("/api/vocab/apply", {"kind": "predicate", "old": "ORBITS", "new": "ABOARD"})
        hand = schema_io.read_ground_truth_schema(server.GROUND_TRUTH_SCHEMA)
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
        hand = schema_io.read_ground_truth_schema(server.GROUND_TRUTH_SCHEMA)
        self.assertEqual(hand["predicates"]["ABOARD"], "is anywhere on")
        self.assertEqual(hand["patterns"].count(("Instrument", "ABOARD", "Spacecraft")), 1)
        self.assertIn("add it first", post("/api/vocab/define", {"kind": "entity class", "component_class": "Planet",
                                                                 "definition": "a world"})["error"])
        self.assertIn("definition", post("/api/vocab/define", {"kind": "entity class", "component_class": "Dataset",
                                                               "definition": "  "})["error"])


class Z_ReviewerComments(unittest.TestCase):
    """The Reviewer comments view's data, and the comments under each entry: annotations/reviews/ read as
    py helpers/review_page.py --read reads it (common/common_helpers/review_comments.py), read-only."""

    def test_view(self):
        from common import review_comments as RC
        folder = TMP / "annotations" / "reviews"
        shutil.rmtree(folder, ignore_errors=True)
        v = get("/api/reviewer_comments")
        self.assertEqual((v["comments"], v["files"], v["folder"]), ([], [], "annotations/reviews/"))
        folder.mkdir()
        try:
            now = RC.entry_texts(TMP / "annotations" / "ground_truth_schema.txt",
                                 TMP / "annotations" / "component_class_mapping.csv")
            row = {"reviewer": "Jane Smith", "page_version": "review_2026-10-24_abc1234", "git_commit": "abc1234",
                   "timestamp": "2026-10-24T10:00:00-04:00"}
            with open(folder / "comments_Jane_Smith_2026-10-24.csv", "w", encoding="utf-8-sig", newline="") as fh:
                w = csv.DictWriter(fh, RC.COMMENT_COLUMNS)
                w.writeheader()
                w.writerow({**row, "kind": "entity class", "entry": "Instrument", "comment": "Fine.",
                            "entry_text_shown": now[("entity class", "Instrument")]})
                w.writerow({**row, "kind": "entity class", "entry": "Spacecraft", "comment": "Too vague.",
                            "entry_text_shown": "Spacecraft: old words"})
                w.writerow({**row, "kind": "predicate", "entry": "HAS_WIDGET", "comment": "Drop it.",
                            "entry_text_shown": "HAS_WIDGET: has a widget"})
            (folder / "spam.eml").write_bytes(b"From: someone@notnasa.gov\r\nSubject: hi\r\n\r\nREVIEW COMMENTS (format 1)\r\n")
            before = sorted(p.name for p in folder.iterdir())
            v = get("/api/reviewer_comments")
            states = {c["entry"]: (c["state"], c["sender"]) for c in v["comments"]}
            self.assertEqual(states, {"Instrument": ("unchanged", v["not_verified"]),
                                      "Spacecraft": ("changed", v["not_verified"]),
                                      "HAS_WIDGET": ("gone", v["not_verified"])})
            self.assertEqual(v["files"], ["comments_Jane_Smith_2026-10-24.csv", "spam.eml"])
            self.assertIn("spam.eml: sent from someone@notnasa.gov", v["problems"][0])
            self.assertEqual(sorted(p.name for p in folder.iterdir()), before)             # read-only
        finally:
            shutil.rmtree(folder)

    def test_expert_questions(self):
        """The questions for experts, with what each answer may change, for the record's "Questions for experts"
        line and the Reviewer comments view; a file not in its format is a problem, not a failure."""
        path = TMP / "annotations" / "questions_for_experts.md"
        self.assertEqual(get("/api/expert_questions")["questions"], [])               # no file: none
        rid = "aaaaaaaa-0000-0000-0000-000000000001"
        path.write_text("# Questions\n\n## Q1: Closed list?\n\n- status: open\n- priority: high\n"
                        "- question kind: general\n- topic: layouts\n\n### The question\n\nIs it closed?\n\n"
                        "### My current reading\n\nUndecided.\n\n"
                        f"### Affects\n\n- record at pool position 0: {rid}\n"
                        f"- classed triple of the record at pool position 0: \"A\" (Dataset) HAS_X \"b\" (Thing)\n",
                        encoding="utf-8")
        try:
            q, = get("/api/expert_questions")["questions"]
            self.assertEqual((q["id"], q["priority"], q["question_kind"]), ("Q1", "high", "general"))
            self.assertEqual([r["id"] for r in q["affects"]["records"]], [rid])
            self.assertEqual(q["affects"]["triples"][0]["object"], "b")
            path.write_text("# Questions\n\n## Q1 no colon\n", encoding="utf-8")
            v = get("/api/expert_questions")
            self.assertEqual(v["questions"], [])
            self.assertIn("isn't a question's heading", v["problem"])
        finally:
            path.unlink()
        page = urllib.request.urlopen(url("/")).read().decode("utf-8")
        for needed in ("/api/expert_questions", "expertQuestionsOn(rec.id)", 'kind === "question" ? questionHead(entry)'):
            self.assertIn(needed, page)

    def test_page(self):
        page = urllib.request.urlopen(url("/")).read().decode("utf-8")
        for needed in ('id="reviewcomments"', "reviewerNotes(kind, v.component_class)",
                       'reviewerNotes("translation row", rowReviewEntry(r))', "/api/reviewer_comments"):
            self.assertIn(needed, page)
        self.assertIn("reviews", server.HELP_SECTIONS)
        self.assertTrue(get("/api/help?view=reviews")["intro"])


class Y_LeftOut(unittest.TestCase):
    """What the ground truth leaves out on purpose (annotations/left_out.md), read by ONE reader
    (common/common_helpers/left_out.py) for the record's folded section and the Left out view; read-only."""

    GOOD = "\n".join([
        '# Left out on purpose', '', 'Introduction, not read.', '',
        '## "Title A" (pool position 0, id r0)', '',
        '2 items, 1 that may matter. A note.', '',
        '- **Left out:** "great" (notes)',
        '  - **Rule:** What counts as a fact, rule 5: "Leave out words such as great."',
        '  - Written without it.',
        '- **Left out:** "1149" (title)',
        '  - **Rule:** What counts as a fact, rule 1: "never write down what a code stands for"',
        '  - **May matter because:** it may identify the dataset.',
        '  - **Question:** Q6 (b), and Q24.', '',
        '## "Title B" (pool position 1, id r1)', '',
        '1 item, none that may matter.', '',
        '- **Left out:** "x"',
        '  - **Rule:** none to quote. I decided so.', ''])

    def read(self, text):
        from common.left_out import read_left_out
        path = TMP / "left_out_test.md"
        path.write_text(text, encoding="utf-8")
        try:
            return read_left_out(path)
        finally:
            path.unlink()

    def test_reader(self):
        from common.left_out import NO_RULE, rule_ref
        a, b = self.read(self.GOOD)
        self.assertEqual((a["title"], a["position"], a["id"], len(a["items"])), ("Title A", 0, "r0", 2))
        first, second = a["items"]
        self.assertEqual((first["words"], first["notes"], first["may_matter"]),
                         ('"great" (notes)', ["Written without it."], ""))
        self.assertEqual((rule_ref(first), rule_ref(b["items"][0])), ("What counts as a fact, rule 5", NO_RULE))
        self.assertEqual((second["may_matter"], second["questions"]), ("it may identify the dataset.", ["Q6", "Q24"]))

    def test_malformed_names_the_line(self):
        """(a change to the good file, a fragment of the line the message must name, what it must say)"""
        cases = [(('- **Left out:** "1149"', '- Left out: "1149"'), 'Left out: "1149"', "must start with"),
                 (("(pool position 1, id r1)", "(position 1)"), "(position 1)", "a heading must be"),
                 (("2 items, 1 that", "3 items, 1 that"), '## "Title A"', "says 3 item(s) but lists 2"),
                 (("1 that may matter", "2 that may matter"), '## "Title A"', "says 2 that may matter but 1"),
                 (("  - **Rule:** What counts as a fact, rule 1", "  - Rule: x"), '"1149" (title)', "needs a"),
                 (("  - Written without it.", "  - **Rule:** twice"), "**Rule:** twice", "two"),
                 (("  - Written", "   - Written"), "   - Written", "indented line must start"),
                 (("id r1)", "id r0)"), "id r0)\n\n1 item", "two sections"),
                 (("2 items, 1 that may matter. A note.", "A note."), "## \"Title A\"", "how many items")]
        for (old, new), fragment, what in cases:
            text = self.GOOD.replace(old, new)
            self.assertNotEqual(text, self.GOOD, old)
            n = text[:text.index(fragment)].count("\n") + 1
            with self.assertRaises(ValueError) as caught:
                self.read(text)
            self.assertIn(f"line {n}:", str(caught.exception), old)
            self.assertIn(what, str(caught.exception), old)

    def test_the_real_file_is_in_its_format(self):
        from common.left_out import LEFT_OUT_PATH, read_left_out
        real = Path(__file__).resolve().parents[1] / "annotations" / LEFT_OUT_PATH.name
        self.assertTrue(read_left_out(real))

    def test_view(self):
        path = TMP / "annotations" / "left_out.md"
        try:
            path.write_text(self.GOOD, encoding="utf-8")
            v = get("/api/left_out")
            self.assertEqual(v["problem"], "")
            self.assertEqual([len(s["items"]) for s in v["sections"]], [2, 1])
            self.assertEqual(v["rules"], ["What counts as a fact, rule 1", "What counts as a fact, rule 5", v["no_rule"]])
            self.assertEqual(v["sections"][0]["items"][1]["questions"], ["Q6", "Q24"])
            before = path.read_bytes()
            path.write_text(self.GOOD.replace("2 items", "3 items"), encoding="utf-8")
            v = get("/api/left_out")
            self.assertEqual(v["sections"], [])
            self.assertIn("left_out.md, line 5", v["problem"])
            path.write_bytes(before)
        finally:
            if path.exists():
                path.unlink()
        self.assertTrue(get("/api/left_out")["problem"])                                 # no file: said, not a failure

    def test_page(self):
        """The folded section after the triples, titled with the item count and absent at 0; the view and its filters."""
        page = urllib.request.urlopen(url("/")).read().decode("utf-8")
        for needed in ('id="leftout"', "leftOutSection(rec)", "`Left out on purpose (${sec.items.length})`",
                       "if (!sec || !sec.items.length) return null;", "Only items that may matter", "Every rule",
                       "Search what is left out", 'itemsOneAtATime("leftout"', "/api/left_out"):
            self.assertIn(needed, page)
        self.assertLess(page.index("leftOutSection(rec));"), page.index('$("record").replaceChildren(head,'))
        self.assertIn("leftout", server.HELP_SECTIONS)
        self.assertTrue(get("/api/help?view=leftout")["intro"])


if __name__ == "__main__":
    unittest.main()
