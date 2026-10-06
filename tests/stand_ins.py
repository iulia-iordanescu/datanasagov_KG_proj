"""
tests/stand_ins.py -- stand-ins for the two things the tests never call:
data.nasa.gov's CKAN API (StandInCatalog) and the model (stand_in_model).

StandInCatalog serves package_search on 127.0.0.1 from made-up records,
with the faults a real harvest meets: a record with no id, a repeated id,
HTML-escaped notes, maintainer spellings to join, and, when asked, a busy
page (503 once), a failing page (404), or a page that isn't JSON.

stand_in_model(prompt) answers every prompt of steps 040 to 070, from the
prompt's own text, deterministically, with deliberate faults the steps must
catch (see each branch). A test sets common.llm.call_llm = stand_in_model.
"""
import hashlib
import json
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

# ------------------------------------------------------------------ catalog

MAINTAINERS = ["Kristan Morgan", "KRISTAN MORGAN", "Morgan, Kristan", "Dr. Jane Roe", "Jane  Roe",
               "Earthdata Forum", "Ames Team", "", None]
#: Instruments and spacecraft the made-up notes mention, so the stand-in model
#: finds real passages.
INSTRUMENTS = ["MODIS", "AIRS", "CERES", "OMI", "MLS"]
SPACECRAFT = ["Aqua", "Terra", "Aura"]


def record(i: int) -> dict:
    """The made-up catalog's record number i."""
    inst, craft = INSTRUMENTS[i % len(INSTRUMENTS)], SPACECRAFT[i % len(SPACECRAFT)]
    notes = (f"&lt;p&gt;{inst} aboard &lt;b&gt;{craft}&lt;/b&gt; measured record {i}.&lt;/p&gt;"
             f"&lt;a href=\"https://example.org/{i}\"&gt;https://example.org/{i}&lt;/a&gt;") if i % 3 == 0 \
        else f"{inst} aboard {craft} measured record {i}. Data from {inst} are in HDF." if i % 7 else ""
    r = {"id": f"rec-{i:04d}", "name": f"dataset-{i}",
         "title": f"{inst} {craft} Dataset {i} &amp; more" if i % 4 == 0 else f"{inst} {craft} Dataset {i}",
         "notes": notes,
         "maintainer": MAINTAINERS[i % len(MAINTAINERS)],
         "organization": {"title": "NASA"} if i % 2 else None,
         "tags": [{"name": "earth science"}, {"name": f"tag{i % 3}"}],
         "resources": [{"format": "HDF"}, {"format": "csv" if i % 2 else "CSV"}],
         "license_title": "Public Domain", "url": f"https://example.org/{i}",
         "metadata_created": f"2020-01-01T00:00:{i % 60:02d}", "metadata_modified": "2024-01-01T00:00:00"}
    if i == 5:
        del r["id"]                       # a record with no id
    if i == 8:
        r["id"] = "rec-0003"              # a repeated id
    return r


class StandInCatalog:
    """with StandInCatalog(count=40) as cat: ... cat.url is package_search's URL.
    cat.count, cat.fail_starts, cat.busy_once, cat.not_json_starts can be
    changed between requests; cat.requests lists every start asked for."""

    def __init__(self, count: int):
        self.count, self.fail_starts, self.busy_once, self.not_json_starts = count, set(), set(), set()
        self.requests, self._busy_done = [], set()
        cat = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                q = parse_qs(urlparse(self.path).query)
                rows, start = int(q["rows"][0]), int(q["start"][0])
                cat.requests.append(start)
                if start in cat.busy_once and start not in cat._busy_done:
                    cat._busy_done.add(start)
                    return self._send(503, b"busy", "text/plain")
                if start in cat.fail_starts:
                    return self._send(404, b"not found", "text/plain")
                if start in cat.not_json_starts:
                    return self._send(200, b"<html>maintenance</html>", "text/html")
                body = {"success": True, "result": {"count": cat.count, "results":
                        [record(i) for i in range(start, min(start + rows, cat.count))]}}
                self._send(200, json.dumps(body).encode(), "application/json")

            def _send(self, status, data, kind):
                self.send_response(status)
                self.send_header("Content-Type", kind)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}/api/3/action/package_search"

    def __enter__(self):
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        return self

    def __exit__(self, *exc):
        self.server.shutdown()
        self.server.server_close()


# -------------------------------------------------------------------- model

CALLS = []          # every prompt the stand-in model answered


def _h(s: str) -> int:
    return int(hashlib.sha256(s.encode("utf-8")).hexdigest(), 16)


def _between(prompt: str, begin: str, end: str) -> str:
    return prompt[prompt.rindex(begin) + len(begin):prompt.rindex(end)]


def _json_after(prompt: str, header: str):
    return json.loads(prompt[prompt.rindex(header) + len(header):].strip())


def _schema_classes(prompt: str) -> tuple:
    """The entity classes and predicates a step 050/060 prompt lists."""
    head = prompt.split("----- BEGIN RECORD -----")[0]
    entity = re.findall(r"^(\w+) {2,}", head.split("PREDICATES")[0].split("ENTITY CLASSES")[-1], re.M)
    predicates = re.findall(r"^([A-Z][A-Z_]+) {2,}", head.split("PREDICATES")[-1], re.M)
    return entity, predicates


def _record_reply(prompt: str) -> dict:
    """Steps 050 and 060: the facts of the record, as the record's own words.
    Faults: a repeat, a source text that isn't in the text, a component class
    outside the schema, a malformed item; some records name no entity class
    for the DESCRIBES row."""
    text = _between(prompt, "----- BEGIN RECORD -----", "----- END RECORD -----").strip()
    entity, predicates = _schema_classes(prompt)
    instrument = "Instrument" if "Instrument" in entity else entity[0]
    spacecraft = "Spacecraft" if "Spacecraft" in entity else entity[-1]
    aboard = "ABOARD" if "ABOARD" in predicates else predicates[0]
    triples = []
    for m in re.finditer(r"\b(%s) aboard (%s)\b" % ("|".join(INSTRUMENTS), "|".join(SPACECRAFT)), text):
        triples.append({"subject": m.group(1), "subject_class": instrument, "predicate": aboard,
                        "object": m.group(2), "object_class": spacecraft, "source_text": m.group(0)})
    if triples:
        first = triples[0]
        triples += [dict(first),                                                          # a repeat
                    {**first, "object": "Moon", "source_text": "aboard the Moon"},        # not in the text
                    {**first, "object_class": "Satellite"},                               # outside the schema
                    {"subject": ["MODIS"], "predicate": aboard, "object": "Aqua"}]        # malformed
    h = _h(text)
    return {"describes_class": "" if h % 4 == 0 else "Dataset", "triples": triples}


def _induce_texts(prompt: str) -> dict:
    """Step 040's extraction: pairs of capitalized words of the text, with the
    passage between them. Faults: an invented passage, a missing one, a
    malformed item."""
    text = _between(prompt, "----- BEGIN TEXT -----", "----- END TEXT -----")
    words = re.findall(r"\b[A-Z][A-Za-z0-9-]{2,}\b", text)[:6]
    verbs = ["is aboard", "is mounted on", "measures", "is part of"]
    triples = []
    for a, b in zip(words, words[1:]):
        i = text.find(a)
        j = text.find(b, i + len(a))
        source = text[i:j + len(b)] if 0 <= i < j else f"{a} and {b} together"
        if _h(a + b) % 7 == 0:
            source = f"{a} is said to relate to {b}"            # not in the text
        triples.append({"subject": a, "predicate": verbs[_h(a + b) % len(verbs)], "object": b, "source_text": source})
    triples.append({"subject": "", "predicate": "x", "object": "y"})   # malformed
    return {"describes_class": "Dataset", "triples": triples}


ENTITY_LABELS = ["Instrument", "Sensor", "Spacecraft", "Satellite", "Organization", "Mission"]
PREDICATE_LABELS = ["ABOARD", "MOUNTED_ON", "MEASURES", "PART_OF"]


def _labels(prompt: str) -> dict:
    """Step 040's labeling: reuse a label of the running vocabulary or coin one."""
    entities = "\nSUBJECTS AND OBJECTS (each with one usage" in prompt
    header = ("SUBJECTS AND OBJECTS" if entities else "PREDICATES") + \
        " (each with one usage example, \"subject -- predicate -- object\"):"
    items = _json_after(prompt, header)
    coin = ENTITY_LABELS if entities else PREDICATE_LABELS
    return {"labels": {item: coin[_h(item) % len(coin)] for item in items}}


def _merges(prompt: str) -> dict:
    """Step 040's merging: two pairs of synonyms, and one invalid merge."""
    labels = [x["label"] for x in _json_after(prompt, "LABELS:")]
    pairs = [("Sensor", "Instrument"), ("Satellite", "Spacecraft"), ("MOUNTED_ON", "ABOARD")]
    merges = [{"into": b, "labels": [a, b]} for a, b in pairs if a in labels and b in labels]
    merges.append({"into": "Gadget", "labels": ["Gadget", "Widget"]})       # not labels: ignored
    return {"merges": merges}


def _definitions(prompt: str) -> dict:
    """Step 040's definitions: one each, Mission too vague, plus one not sent."""
    header = "ENTITY CLASSES:" if "\nENTITY CLASSES:" in prompt else "PREDICATES:"
    entries = _json_after(prompt, header)
    d, vague = {}, {}
    for e in entries:
        name = e["component_class"]
        if name == "Mission":
            vague[name] = "stand-in: too vague"
        else:
            d[name] = f"A {name} (stand-in definition)."
    d["Bogus"] = "not sent"
    return {"definitions": d, "too_vague": vague}


#: Step 070's translations: the current schema's component class -> the ground truth vocabulary's.
TRANSLATIONS = {"Satellite": "Spacecraft", "Sensor": "Instrument", "MOUNTED_ON": "ABOARD"}


def _mapping(prompt: str) -> dict:
    schema = json.loads(prompt[prompt.rindex("\nSCHEMA\n") + len("\nSCHEMA\n"):].strip())
    if "has since gained" in prompt:
        return {"suggestions": []}
    return {"mapping": [{"kind": i["kind"], "schema": i["component_class"],
                         "ground_truth": TRANSLATIONS.get(i["component_class"], i["component_class"]
                                                          if i["component_class"] != "Gadget" else None),
                         "reversed": False} for i in schema]}


def stand_in_model(prompt, attempts=4, read_timeout=180):
    CALLS.append(prompt)
    if "----- BEGIN RECORD -----" in prompt:
        return json.dumps(_record_reply(prompt))
    if "----- BEGIN TEXT -----" in prompt:
        return json.dumps(_induce_texts(prompt))
    if "(each with one usage example" in prompt:
        return json.dumps(_labels(prompt))
    if '"merges"' in prompt:
        return json.dumps(_merges(prompt))
    if "\nSCHEMA\n" in prompt:
        return json.dumps(_mapping(prompt))
    if "\nENTITY CLASSES:" in prompt or "\nPREDICATES:" in prompt:
        return json.dumps(_definitions(prompt))
    if '{"ok": true}' in prompt:
        return '{"ok": true}'
    raise AssertionError("stand-in model: a prompt it doesn't know:\n" + prompt[:500])
