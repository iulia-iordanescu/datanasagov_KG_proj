"""The review page (helpers/review_page.py): the page it writes is one self-contained file that reaches nothing
outside itself, shows every entity class, predicate and row of the translation table, and says which version it
is; the comment files and emails reviewers send back are read into a summary that flags comments on entries that changed or
are gone; the page's emails survive what email clients do to them; reviewers' files stay out of Git; --publish
puts only the page on its branch. Works on temporary copies; nothing in annotations/ or outputs/ is touched."""
import csv
import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
import urllib.parse
from email.message import EmailMessage
from pathlib import Path
from unittest import mock

from support import ROOT

sys.path.insert(0, str(ROOT / "helpers"))
import review_page as R                                                        # noqa: E402
from common import review_comments as RC                                       # noqa: E402

SCHEMA = """ENTITY CLASSES
--------------
Instrument        a device that takes measurements
Spacecraft        a craft that operates in space
                  source: ground truth tuning #2

PREDICATES
----------
Each entry below reads subject -> object.

ABOARD               is carried on
                     Instrument -> Spacecraft
                     only: any -> Spacecraft
"""
MAPPING = """kind,component_class_from_past_or_crt_schema,component_class_in_gtt,swap_subject_and_object,checked,definition_from_past_or_crt_schema,definition_in_gtt
entity class,Satellite,Spacecraft,no,yes,"A craft that orbits a body, e.g. Aqua.",a craft that operates in space
predicate,CARRIES,ABOARD,yes,yes,Has on board.,is carried on
entity class,Gadget,(none),no,no,A small device.,
"""


def files(folder: Path, schema: str = SCHEMA, mapping: str = MAPPING, questions: str = "# Questions\n") -> dict:
    """Stand-ins for the files the page shows; the questions file with no question unless one is given."""
    (folder / "ground_truth_schema.txt").write_text(schema, encoding="utf-8")
    (folder / "component_class_mapping.csv").write_text(mapping, encoding="utf-8")
    (folder / "questions_for_experts.md").write_text(questions, encoding="utf-8")
    return {"schema_path": folder / "ground_truth_schema.txt", "mapping_path": folder / "component_class_mapping.csv",
            "questions_path": folder / "questions_for_experts.md"}


def page_json(page: str) -> dict:
    return json.loads(re.search(r'<script type="application/json" id="data">(.*?)</script>', page, re.S).group(1))


class Page(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        cls.path = R.generate(out_dir=cls.tmp, **files(cls.tmp))
        cls.page = cls.path.read_text(encoding="utf-8")
        cls.data = page_json(cls.page)

    def test_named_by_date_and_commit(self):
        self.assertRegex(self.path.name, r"^review_\d{4}-\d{2}-\d{2}_\w+\.html$")

    def test_reaches_nothing_outside_itself(self):
        """No address the browser would load (the page's own data may quote a web address as text: it is never
        loaded); no script call that sends or fetches; a policy that forbids any request."""
        code = self.page.replace(re.search(r'<script type="application/json" id="data">.*?</script>', self.page, re.S).group(0), "")
        loads = (r"(?i)(src|href)\s*=\s*[\"']?(https?:)?//|(?<![\w.])url\(\s*(?![\"']?data:)|@import|\bfetch\("
                 r"|XMLHttpRequest|sendBeacon|WebSocket|EventSource|[\"(]/fonts/")
        self.assertEqual([m.group(0) for m in re.finditer(loads, code)], [])
        self.assertIn("default-src 'none'", code)
        self.assertIn("data:font/woff2;base64,", code)                        # the typefaces, inside
        self.assertNotRegex(code, r"{{[A-Z_]+}}")                            # every placeholder filled

    def test_the_annotation_tools_look(self):
        """The annotation tool's style sheets, as its page holds them."""
        tool = (ROOT / "helpers" / "annotator" / "page.html").read_text(encoding="utf-8")
        first = re.findall(r"<style>(.*?)</style>", tool, re.S)[1]
        self.assertIn(first.strip()[:2000], self.page)

    def test_every_entry(self):
        s, m = self.data["schema"], self.data["mapping"]["rows"]
        self.assertEqual([e["entry"] for e in s["entity_classes"]], ["Instrument", "Spacecraft"])
        self.assertEqual([e["entry"] for e in s["predicates"]], ["ABOARD"])
        aboard = s["predicates"][0]
        self.assertEqual((aboard["patterns"], aboard["pins"]), ([["Instrument", "Spacecraft"]], [["any", "Spacecraft"]]))
        self.assertEqual(s["entity_classes"][1]["source"], "ground truth tuning #2")
        self.assertEqual(s["notes"], ["Each entry below reads subject -> object."])
        self.assertEqual([r["entry"] for r in m], ["entity class Satellite", "predicate CARRIES", "entity class Gadget"])
        self.assertEqual((m[1]["swap"], m[2]["gtt"], m[2]["checked"]), ("yes", "(none)", "no"))

    def test_version(self):
        v = self.data["version"]
        self.assertEqual([f["sha256"] for f in v["files"]],
                         [R.fingerprint(self.tmp / "ground_truth_schema.txt"), R.fingerprint(self.tmp / "component_class_mapping.csv"),
                          R.fingerprint(self.tmp / "questions_for_experts.md")])
        self.assertEqual(v["id"], self.path.stem)
        self.assertTrue(v["commit"] and v["generated"])
        self.assertIn("A read-only copy: it can't change anything", self.page)

    def test_terms_from_terminology(self):
        """Each term the page shows is docs/terminology.md's entry, word for word (markup aside)."""
        terms = (ROOT / "docs" / "terminology.md").read_text(encoding="utf-8")
        self.assertEqual([t["term"] for t in self.data["glossary"]], R.GLOSSARY)
        for t in self.data["glossary"]:
            words = re.sub(r"<[^>]+>", "", t["meaning_html"]).replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
            plain = re.sub(r"\[([^\[\]]*)\]\([^)]*\)", r"\1", terms).replace("`", "").replace("**", "")
            self.assertIn(words[:120].replace("*", ""), plain.replace("*", ""))

    def test_a_missing_term_stops(self):
        with self.assertRaises(ValueError):
            R.glossary(terms=["no such term"])

    def test_the_real_files(self):
        """The real ground truth schema and translation table make a page with every entry."""
        with tempfile.TemporaryDirectory() as out:
            data = page_json(R.generate(out_dir=Path(out)).read_text(encoding="utf-8"))
        from common.schema_io import read_ground_truth_schema
        from common.component_class_mapping import read_mapping
        schema = read_ground_truth_schema(R.SCHEMA_PATH)
        self.assertEqual([e["entry"] for e in data["schema"]["entity_classes"]], list(schema["entity_classes"]))
        self.assertEqual([e["entry"] for e in data["schema"]["predicates"]], list(schema["predicates"]))
        self.assertEqual(len(data["mapping"]["rows"]), len(read_mapping(R.MAPPING_PATH)))
        self.assertEqual(len({r["entry"] for r in data["mapping"]["rows"]}), len(data["mapping"]["rows"]))   # ids unique


class Comments(unittest.TestCase):
    """A comment file as the page saves it, read back with --read."""

    def test_question_statuses_as_the_guide_lists_them(self):
        """helpers/review_page.md, *The questions file*, the home of a question's statuses: its **status** paragraph
        defines the code's (expert_questions.STATUSES), in their order."""
        from common import expert_questions
        text = (ROOT / "helpers" / "review_page.md").read_text(encoding="utf-8")
        para = text.split("**status**: exactly one of three.", 1)[1].split("**priority**", 1)[0]
        self.assertEqual(tuple(re.findall(r"`([a-z]+)`:", para)), expert_questions.STATUSES)

    def test_states_as_the_guide_lists_them(self):
        """helpers/review_page.md, *What --read reports*, the home of the comment states: its table lists the code's
        states (review_comments.COMMENT_STATES), in their order."""
        text = (ROOT / "helpers" / "review_page.md").read_text(encoding="utf-8")
        section = text.split("### What --read reports", 1)[1].split("\n### ", 1)[0]
        self.assertEqual(tuple(re.findall(r"^\| `([a-z]+)` \|", section, re.M)), RC.COMMENT_STATES)

    def write(self, folder: Path, name: str, rows: list) -> Path:
        path = folder / name
        with open(path, "w", encoding="utf-8-sig", newline="") as fh:
            w = csv.DictWriter(fh, R.COMMENT_COLUMNS, lineterminator="\r\n")
            w.writeheader()
            w.writerows(rows)
        return path

    def row(self, topic, entry, shown, comment, at="2026-10-24T10:00:00-04:00", who="Jane Smith"):
        return {"reviewer": who, "page_version": "review_2026-10-24_abc1234", "git_commit": "abc1234", "topic": topic,
                "entry": entry, "entry_text_shown": shown, "comment": comment, "timestamp": at}

    def test_round_trip_and_flags(self):
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            paths = files(t)
            now = R.entry_texts(**paths)
            reviews = t / "reviews"
            reviews.mkdir()
            self.write(reviews, "a.csv", [
                self.row("general", "(general)", "", "Clear overall, thanks."),
                self.row("entity class", "Instrument", now[("entity class", "Instrument")], 'Also "sensor", maybe.'),
                self.row("entity class", "Spacecraft", "Spacecraft: a vehicle in space", "Too vague."),       # changed since
                self.row("predicate", "HAS_WIDGET", "HAS_WIDGET: has a widget", "Drop it."),                 # gone
                self.row("translation row", "predicate CARRIES", now[("translation row", "predicate CARRIES")], "Right, swapped."),
                self.row("entity class", "Instrument", "", "older words", at="2026-10-23T09:00:00-04:00")])  # older: replaced
            (reviews / "notes.txt").write_text("not a comment file", encoding="utf-8")                      # skipped, and said
            self.write(reviews, "b.csv", [self.row("predicate", "ABOARD", now[("predicate", "ABOARD")], "Fine.", who="Bo Lee")])
            out, text = R.read_and_summarize([reviews], out_dir=t / "out", **paths)
            self.assertTrue(out.exists())
            self.assertIn("6 comment(s) from 2 reviewer(s): Bo Lee, Jane Smith.", text)
            self.assertIn("⚑ 1 comment(s) on an entry that changed since the page they were written on; 1 on an entry "
                          "no longer in the files.", text)
            self.assertIn('Also "sensor", maybe.', text)
            self.assertNotIn("older words", text)
            self.assertIn("notes.txt: no line \"REVIEW COMMENTS (format 1)\"", text)
            spacecraft = text.split("### Spacecraft", 1)[1].split("###", 1)[0]
            self.assertIn("⚑ Changed since that page. Then: Spacecraft: a vehicle in space", spacecraft)
            self.assertIn("Now: Spacecraft: a craft that operates in space | source: ground truth tuning #2", spacecraft)
            self.assertIn("⚑ No longer in the files", text.split("### HAS_WIDGET", 1)[1])
            self.assertNotIn("⚑", text.split("### Instrument", 1)[1].split("###", 1)[0])
            self.assertLess(text.index("## General comments"), text.index("## Entity classes"))

    def test_kind_from_older_pages_is_read_as_topic(self):
        """Copies of the page made before 2026-10-26 called the topic "kind": a comment file with a kind column, and
        an email with [kind] lines, are read with it as the topic, as a file with topic is."""
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            paths = files(t)
            now = R.entry_texts(**paths)
            reviews = t / "reviews"
            reviews.mkdir()
            old_columns = [RC.LEGACY_TOPIC if c == "topic" else c for c in R.COMMENT_COLUMNS]
            with open(reviews / "old.csv", "w", encoding="utf-8-sig", newline="") as fh:
                w = csv.DictWriter(fh, old_columns, lineterminator="\r\n")
                w.writeheader()
                row = self.row("entity class", "Instrument", now[("entity class", "Instrument")], "From an old file.")
                w.writerow({(RC.LEGACY_TOPIC if k == "topic" else k): v for k, v in row.items()})
            (reviews / "old.txt").write_text(
                "REVIEW COMMENTS (format 1): please send this email as it is\n[reviewer] Bo Lee\n"
                "[page_version] review_2026-10-24_abc1234\n[git_commit] abc1234\n[sent] 2026-10-24T14:05:09-04:00\n"
                "[part] 1 of 1\n=== start of part 1 of 1 ===\n\n=== comment ===\n[kind] predicate\n[entry] ABOARD\n"
                "[page_version] review_2026-10-24_abc1234\n[git_commit] abc1234\n[timestamp] 2026-10-24T10:00:00-04:00\n"
                f"[entry_text_shown] {now[('predicate', 'ABOARD')]}\n[comment] From an old email.\n\n"
                "=== end of part 1 of 1 ===\n", encoding="utf-8")
            read = R.read_all([reviews], **paths)
            self.assertEqual(read["problems"], [])
            self.assertEqual(sorted((c["topic"], c["entry"], c["comment"], c["state"]) for c in read["comments"]),
                             [("entity class", "Instrument", "From an old file.", "unchanged"),
                              ("predicate", "ABOARD", "From an old email.", "unchanged")])

    def test_a_file_of_another_shape_is_skipped(self):
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            (t / "x.csv").write_text("name,note\nA,B\n", encoding="utf-8")
            _, text = R.read_and_summarize([t / "x.csv"], out_dir=t / "out", **files(t))
            self.assertIn("x.csv: lacks the column(s) reviewer", text)
            self.assertIn("0 comment(s)", text)


# ------------------------------ emails ----------------------------------------

CHROME = next((p for p in (shutil.which("chrome"), shutil.which("google-chrome"), shutil.which("chromium"),
                           r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                           r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                           r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
               if p and Path(p).exists()), None)
ADDRESS = "+".join(["iulia.m.iordanescu", "kgreview"]) + "@" + "gmail.com"           # never written whole: see the guide


def page_comments(now: dict) -> dict:
    """Comments as the page keeps them (its localStorage): a general one of two lines, a long one, one on an entry
    that changed since, one on a row of the translation table."""
    at = lambda m: f"2026-10-24T10:{m:02d}:00-04:00"                              # noqa: E731
    one = lambda topic, entry, text, m, shown: {"topic": topic, "entry": entry, "text": text, "at": at(m),  # noqa: E731
                                                "version": "review_2026-10-23_abc1234", "commit": "abc1234", "shown": shown}
    return {"general|(general)": one("general", "(general)", "Clear overall.\nSecond line: thanks.", 1, ""),
            "entity class|Instrument": one("entity class", "Instrument", " ".join(f"word{i}" for i in range(300)), 2,
                                           now[("entity class", "Instrument")]),
            "entity class|Spacecraft": one("entity class", "Spacecraft", "Too vague; e.g. a lander-rover pair?", 3,
                                           "Spacecraft: a vehicle in space"),
            "translation row|predicate CARRIES": one("translation row", "predicate CARRIES", "Right, swapped.", 4,
                                                     now[("translation row", "predicate CARRIES")])}


def run_page(page: str, script: str, folder: Path) -> str:
    """The page, opened in headless Chrome with `script` run after its own; what the script left in the body's
    data-out attribute."""
    path = folder / "harness.html"
    path.write_text(page.replace("</body>", f"<script>{script}</script></body>"), encoding="utf-8")
    dom = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-first-run", f"--user-data-dir={folder / 'profile'}",
                          "--dump-dom", path.as_uri()], capture_output=True, text=True, encoding="utf-8",
                         timeout=120).stdout
    return html.unescape(re.search(r'data-out="([^"]*)"', dom).group(1))


def mailto(url: str) -> tuple:
    """(address, subject, body) of a mailto: link."""
    parts = urllib.parse.urlsplit(url)
    q = urllib.parse.parse_qs(parts.query)
    return urllib.parse.unquote(parts.path), q["subject"][0], q["body"][0]


def mangle(body: str, width: int = 60) -> str:
    """What an email client may do to a body: wrap every long line at a space (or after a hyphen), quote it in a
    reply, with a line before and a signature after."""
    lines = []
    for line in body.replace("\r\n", "\n").split("\n"):
        lines += textwrap.wrap(line, width, break_long_words=False, break_on_hyphens=True) or [""]
    return ("On Fri, Oct 24, 2026, Jane Smith <jane@nasa.gov> wrote:\n" + "\n".join("> " + l for l in lines)
            + "\n\n-- \nJane Smith\nGoddard Space Flight Center\n")


@unittest.skipUnless(CHROME, "no Chrome or Edge on this computer to run the page's script")
class Email(unittest.TestCase):
    """The page's Email my comments button: its emails (written by the page's own script, in headless Chrome) read
    back with --read, as sent, wrapped, quoted, merged, in parts, with a part missing."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        cls.paths = files(cls.tmp)
        cls.now = R.entry_texts(**cls.paths)
        cls.page = R.build(R.page_data(**cls.paths))
        cls.comments = page_comments(cls.now)
        script = (f"comments = {json.dumps(cls.comments)}; reviewer = 'Jane Smith';"
                  "const few = {'general|(general)': comments['general|(general)']};"
                  "const all = emailParts('2026-10-24T12:00:00-04:00');"
                  "comments = few; const one = emailParts('2026-10-24T12:30:00-04:00');"
                  "comments = {}; for (let i = 0; i < 40; i++) comments['entity class|E' + i] = {topic: 'entity class', "
                  "entry: 'E' + i, text: 'x '.repeat(400), at: '2026-10-24T10:00:00-04:00', version: 'v', commit: 'c', shown: ''};"
                  "const many = emailParts('2026-10-24T13:00:00-04:00');"
                  "document.body.setAttribute('data-out', JSON.stringify({all, one, many}));")
        cls.out = json.loads(run_page(cls.page, script, cls.tmp))
        cls.bodies = [mailto(p["url"])[2] for p in cls.out["all"]["parts"]]

    def read(self, texts: dict) -> dict:
        folder = Path(tempfile.mkdtemp(dir=self.tmp))
        for name, text in texts.items():
            (folder / name).write_bytes(text.encode("utf-8"))
        return R.read_all([folder], **self.paths)

    def expected(self) -> dict:
        return {f"{c['topic']}|{c['entry']}": (c["text"].strip(), c["shown"], c["at"], c["version"], c["commit"])
                for c in self.comments.values()}

    def got(self, read: dict) -> dict:
        return {f"{c['topic']}|{c['entry']}": (c["comment"], c["entry_text_shown"], c["timestamp"], c["page_version"],
                                              c["git_commit"]) for c in read["comments"]}

    def test_the_address_isnt_in_the_page(self):
        """Put together only when the button is pressed: not in the page's text for address harvesters."""
        for part in ("iordanescu+", "iordanescu@", "@gmail", "kgreview@", "mailto:iulia"):
            self.assertNotIn(part, self.page)

    def test_parts(self):
        parts = self.out["all"]["parts"]
        self.assertGreater(len(parts), 1)
        self.assertLessEqual(len(parts), 5)
        for i, p in enumerate(parts, 1):
            to, subject, body = mailto(p["url"])
            self.assertLessEqual(len(p["url"]), 1900)
            self.assertEqual(to, ADDRESS)
            self.assertEqual(subject, f"Review comments — Jane Smith — {R.page_data(**self.paths)['version']['id']} — "
                                      f"part {i} of {len(parts)}")
            self.assertIn(f"[part] {i} of {len(parts)}", body)
        one = self.out["one"]["parts"]
        self.assertEqual(len(one), 1)
        self.assertNotIn("part", mailto(one[0]["url"])[1])
        self.assertEqual((self.out["many"]["parts"], self.out["many"]["needed"] > 5), ([], True))   # too long: Download

    def test_round_trip(self):
        read = self.read({f"part{i}.txt": b for i, b in enumerate(self.bodies)})
        self.assertEqual(read["problems"], [])
        self.assertEqual(self.got(read), self.expected())
        state = {c["entry"]: c["state"] for c in read["comments"]}
        self.assertEqual(state, {"(general)": "general", "Instrument": "unchanged", "Spacecraft": "changed",
                                 "predicate CARRIES": "unchanged"})
        self.assertTrue(all(c["sender"] == R.NOT_VERIFIED for c in read["comments"]))

    def test_wrapped_quoted_signed_merged_in_any_order(self):
        """Wrapped at 60 characters, quoted in a reply, signed; then all the parts pasted into one file, last first;
        then lines merged two by two (a client that removes "extra" line breaks)."""
        self.assertEqual(self.got(self.read({"a.txt": mangle(self.bodies[0]), **{f"p{i}.txt": mangle(b, 45)
                                             for i, b in enumerate(self.bodies[1:])}})), self.expected())
        self.assertEqual(self.got(self.read({"all.txt": "\n\n".join(reversed(self.bodies))})), self.expected())
        merged = []
        for b in self.bodies:
            lines = b.replace("\r\n", "\n").split("\n")
            merged.append("\n".join(" ".join(lines[i:i + 2]) for i in range(0, len(lines), 2)))
        self.assertEqual(self.got(self.read({f"m{i}.txt": m for i, m in enumerate(merged)})), self.expected())

    def test_a_missing_part(self):
        n = len(self.bodies)
        read = self.read({f"part{i}.txt": b for i, b in enumerate(self.bodies) if i != 1})
        self.assertTrue(any(f"part(s) 2 of {n} missing" in p for p in read["problems"]), read["problems"])
        got = self.got(read)
        self.assertEqual(got["general|(general)"], self.expected()["general|(general)"])   # whole, in part 1
        self.assertNotIn("entity class|Instrument", got)                                  # cut by the gap: left out

    def test_eml(self):
        """An .eml file is read only from an address of nasa.gov or a subdomain; its .csv attachment too; an
        HTML-only body too."""
        def eml(sender, body=None, html_body=None, attach=None) -> str:
            m = EmailMessage()
            if sender:
                m["From"] = sender
            m["To"], m["Subject"] = ADDRESS, "Review comments"
            if body is not None:
                m.set_content(body)
            if html_body is not None:
                (m.add_alternative if body is not None else m.set_content)(html_body, subtype="html")
            if attach:
                m.add_attachment(attach.encode("utf-8"), maintype="text", subtype="csv", filename="comments_Bo_Lee.csv")
            return m.as_string()
        html_body = "<div>" + "<br>".join(html.escape(l) for l in self.bodies[0].split("\r\n")) + "</div>"
        attach = ",".join(R.COMMENT_COLUMNS) + "\r\nBo Lee,v,c,predicate,ABOARD,x,Fine.,2026-10-24T09:00:00-04:00\r\n"
        texts = {f"p{i}.eml": eml("Jane Smith <jane.smith@ndc.nasa.gov>", b) for i, b in enumerate(self.bodies)}
        texts.update({"html.eml": eml("bo@nasa.gov", html_body=html_body, body=None),
                      "csv.eml": eml("Bo Lee <bo@NASA.GOV>", "My file is attached.", attach=attach),
                      "evil.eml": eml("x@nasa.gov.evil.com", self.bodies[0]),
                      "near.eml": eml("x@notnasa.gov", self.bodies[0]),
                      "none.eml": eml(None, self.bodies[0])})
        read = self.read(texts)
        got = {(c["reviewer"], c["entry"]): c["sender"] for c in read["comments"]}
        self.assertEqual(got[("Jane Smith", "Instrument")], "jane.smith@ndc.nasa.gov")
        self.assertEqual(got[("Bo Lee", "ABOARD")], "bo@NASA.GOV")
        self.assertEqual(self.got({"comments": [c for c in read["comments"] if c["reviewer"] == "Jane Smith"]}),
                         self.expected())
        problems = " ".join(read["problems"])
        for name, sender in (("evil.eml", "x@nasa.gov.evil.com"), ("near.eml", "x@notnasa.gov"),
                             ("none.eml", "(no From address)")):
            self.assertIn(f"{name}: sent from {sender}, not from an address of nasa.gov", problems)
        self.assertEqual(len(read["problems"]), 3)
        only = R.read_all([self.tmp / "nowhere"], **self.paths)                      # a folder not there: nothing
        self.assertEqual((only["comments"], only["files"]), ([], []))

    def test_the_summary_marks_unverified(self):
        folder = Path(tempfile.mkdtemp(dir=self.tmp))
        for i, b in enumerate(self.bodies):
            (folder / f"p{i}.txt").write_text(b, encoding="utf-8")
        _, text = R.read_and_summarize([folder], out_dir=folder / "out", **self.paths)
        self.assertIn(f"{len(self.comments)} comment(s) {R.NOT_VERIFIED}", text)
        self.assertIn(f"; {R.NOT_VERIFIED}): Too vague", text)


@unittest.skipUnless(CHROME, "no Chrome or Edge on this computer to run the page's script")
class Display(unittest.TestCase):
    """What the page shows, in headless Chrome: one short version line whose details hold the full version text; the
    current view's tab marked; arrows shown as → while the data, a comment's entry text and its email keep "->"."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        cls.paths = files(cls.tmp)
        cls.page = R.build(R.page_data(**cls.paths))
        script = ("const out = {}; const v = document.getElementById('version');"
                  "out.summary = v.querySelector('summary').textContent; out.full = v.querySelector('details .full').textContent;"
                  "out.open = v.querySelector('details').open;"
                  "state.schema.kind = 'predicate'; show('schema'); out.schema = document.getElementById('view').textContent;"
                  "out.current = [...document.querySelectorAll('nav.tabs .tab[aria-current=page]')].map((t) => t.id);"
                  "state.schema.search = 'Instrument -> Spacecraft'; redraw(); out.found = document.querySelectorAll('.mapbox').length;"
                  "show('home'); out.home = document.getElementById('view').textContent;"
                  "show('terms'); out.terms = document.getElementById('view').textContent;"
                  "setComment(BY_ID['predicate|ABOARD'], 'Fine.'); reviewer = 'Jane Smith';"
                  "out.body = decodeURIComponent(emailParts('2026-10-24T12:00:00-04:00').parts[0].url.split('body=')[1]);"
                  "document.body.setAttribute('data-out', JSON.stringify(out));")
        cls.out = json.loads(run_page(cls.page, script, cls.tmp))

    def test_version_line(self):
        v = R.page_data(**self.paths)["version"]
        y, m, d = map(int, v["date"].split("-"))
        month = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
                 "November", "December"][m - 1]
        self.assertEqual(self.out["summary"], f"Read-only · updated {d} {month} {y}details")
        self.assertFalse(self.out["open"])
        for words in ("A read-only copy: it can't change anything.", f"from Git commit {v['commit']}",
                      f"page version {v['id']}", "Fingerprints (sha256)", v["files"][0]["sha256"], v["files"][1]["sha256"]):
            self.assertIn(words, self.out["full"])

    def test_current_tab(self):
        self.assertEqual(self.out["current"], ["tab-schema"])

    def test_arrows_shown(self):
        for view in ("schema", "home", "terms"):
            self.assertNotIn("->", self.out[view], view)
        self.assertIn("Instrument → Spacecraft", self.out["schema"])
        self.assertIn("only: any → Spacecraft", self.out["schema"])
        self.assertIn("reads subject → object", self.out["schema"])                 # the file's notes
        self.assertIn("only: Dataset → Instrument", self.out["terms"])            # docs/terminology.md's pinned predicate
        self.assertEqual(self.out["found"], 1)                                    # a search typed with "->" still finds it

    def test_data_and_email_keep_the_files_arrows(self):
        self.assertEqual(page_json(self.page)["schema"]["notes"], ["Each entry below reads subject -> object."])
        self.assertIn("[entry_text_shown] ABOARD: is carried on | patterns: Instrument -> Spacecraft | only: any -> Spacecraft",
                      self.out["body"])


def many_rows(n: int, unchecked: int = 0) -> str:
    """A translation table of n entity class rows, the last `unchecked` of them not checked."""
    lines = [MAPPING.splitlines()[0]]
    lines += [f"entity class,Thing{i},Spacecraft,no,{'no' if i >= n - unchecked else 'yes'},A thing.,a craft that operates in space"
              for i in range(n)]
    return "\n".join(lines) + "\n"


class Sample(unittest.TestCase):
    """The Translation table view's rows chosen at random (sample_rows), and what finding none wrong among them
    means (wrong_rows_bound)."""

    def rows(self, n, unchecked=0):
        tmp = Path(tempfile.mkdtemp())
        return R.mapping_entries(files(tmp, mapping=many_rows(n, unchecked))["mapping_path"], tmp / "ground_truth_schema.txt")

    def test_fixed_and_distinct(self):
        rows = self.rows(164)
        sample = R.sample_rows(rows)
        self.assertEqual(len(sample), R.SAMPLE_SIZE)
        self.assertEqual(len(set(sample)), R.SAMPLE_SIZE)
        self.assertEqual(R.sample_rows(rows), sample)                              # the same each time
        self.assertEqual(R.sample_rows(list(reversed(rows))), list(reversed(sample)))   # whatever the rows' order
        self.assertEqual(sample, [r["entry"] for r in rows if r["entry"] in sample])     # in the rows' order
        self.assertNotEqual(R.sample_rows(rows, seed="another seed"), sample)
        self.assertEqual(R.SAMPLE_SIZE, 30)

    def test_stays_while_its_rows_are_there(self):
        rows = self.rows(164)
        sample = R.sample_rows(rows)
        others = [r for r in rows if r["entry"] not in sample]
        self.assertEqual(R.sample_rows([r for r in rows if r is not others[0]]), sample)   # another row taken out
        gone = sample[0]
        after = R.sample_rows([r for r in rows if r["entry"] != gone])               # a sampled row taken out
        self.assertEqual(len(after), R.SAMPLE_SIZE)
        self.assertEqual(len(set(after) - set(sample)), 1)
        self.assertEqual(set(sample) - set(after), {gone})

    def test_only_checked_rows(self):
        rows = self.rows(60, unchecked=20)
        sample = R.sample_rows(rows)
        self.assertEqual(len(sample), R.SAMPLE_SIZE)
        self.assertFalse({r["entry"] for r in rows if r["checked"] == "no"} & set(sample))

    def test_no_sample_when_few(self):
        self.assertIsNone(R.sample_rows(self.rows(30)))                            # every row shown, no button
        self.assertIsNone(R.sample_rows(self.rows(45, unchecked=15)))              # 30 checked: no sample either
        self.assertEqual(len(R.sample_rows(self.rows(31))), 30)

    def test_the_bound(self):
        from math import comb

        def chance(rows, d, sample, wrong):                                      # at most `wrong` wrong in the sample
            return sum(comb(d, i) * comb(rows - d, sample - i) for i in range(wrong + 1)) / comb(rows, sample)
        for rows, sample, wrong in ((164, 30, 0), (164, 30, 1), (164, 30, 2), (50, 30, 0), (164, 30, 30)):
            d = R.wrong_rows_bound(rows, sample, wrong)
            self.assertGreaterEqual(chance(rows, d, sample, wrong), 0.05)
            if d < rows:
                self.assertLess(chance(rows, d + 1, sample, wrong), 0.05)
        self.assertEqual(R.wrong_rows_bound(164, 30), 14)

    def test_the_guide_and_the_code_state_the_bound(self):
        """The numbers helpers/review_page.md and SAMPLE_SIZE's comment state are wrong_rows_bound's."""
        guide = (ROOT / "helpers" / "review_page.md").read_text(encoding="utf-8")
        code = (ROOT / "helpers" / "review_page.py").read_text(encoding="utf-8")
        for text in (guide, code):
            found = re.findall(r"at most (\d+) of the (\d+)(?: rows)? \((\d+\.\d)%\) are wrong", " ".join(text.replace("#:", "").split()))
            self.assertTrue(found)
            for d, rows, pct in found:
                self.assertEqual(int(d), R.wrong_rows_bound(int(rows), R.SAMPLE_SIZE))
                self.assertEqual(pct, f"{100 * int(d) / int(rows):.1f}")
        for k, d in re.findall(r"\| (\d) \| (\d+) \|", guide):              # the guide's table, k found wrong
            self.assertEqual(int(d), R.wrong_rows_bound(164, R.SAMPLE_SIZE, int(k)))


@unittest.skipUnless(CHROME, "no Chrome or Edge on this computer to run the page's script")
class SampleView(unittest.TestCase):
    """In headless Chrome: the Translation table view shows the rows chosen at random first, with the button that
    shows every row; with too few rows, every row and no button; a comment is filed by row in either view."""

    SCRIPT = ("const out = {}; show('mapping'); const boxes = () => document.querySelectorAll('.mapbox').length;"
              "const b = () => document.getElementById('sampleswitch');"
              "out.text = document.getElementById('view').textContent; out.first = boxes(); out.button = b() ? b().textContent : null;"
              "if (b()) { b().click(); out.all = boxes(); out.allText = document.getElementById('view').textContent;"
              "  setComment(BY_ID['translation row|entity class Thing0'], 'Wrong.'); b().click(); out.back = boxes(); }"
              "out.comments = Object.keys(comments).filter((k) => comments[k].text);"
              "document.body.setAttribute('data-out', JSON.stringify(out));")

    def run_with(self, mapping):
        tmp = Path(tempfile.mkdtemp())
        return json.loads(run_page(R.build(R.page_data(**files(tmp, mapping=mapping))), self.SCRIPT, tmp))

    def test_many_rows(self):
        out = self.run_with(many_rows(40))
        self.assertEqual(out["first"], 30)
        self.assertIn("30 rows chosen at random from the 40. If you have time, check these; the button below shows all 40.",
                      out["text"])
        self.assertEqual(out["button"], "Show all 40 rows")
        self.assertEqual(out["all"], 40)
        self.assertIn("Show only the 30 chosen at random", out["allText"])
        self.assertEqual(out["back"], 30)
        self.assertEqual(out["comments"], ["translation row|entity class Thing0"])     # which row, not which view

    def test_unchecked_rows(self):
        out = self.run_with(many_rows(40, unchecked=5))
        self.assertIn("30 rows chosen at random from the 35 checked rows. If you have time, check these; the button "
                      "below shows all 40.", out["text"])

    def test_few_rows(self):
        out = self.run_with(many_rows(30))
        self.assertEqual(out["first"], 30)
        self.assertIsNone(out["button"])
        self.assertNotIn("chosen at random", out["text"])


class Senders(unittest.TestCase):

    def test_allowed_domains(self):
        """nasa.gov or a subdomain of it, case aside; never a domain that merely contains or ends with the words."""
        yes = ["a@nasa.gov", "a@NASA.gov", "a@ndc.nasa.gov", "a@x.y.nasa.gov", "a@nasa.gov."]
        no = ["a@notnasa.gov", "a@nasa.gov.evil.com", "a@nasa.govx", "a@nasa-gov.com", "nasa.gov", "", "a@gov",
              "a@evil.com?nasa.gov", "a@nasagov"]
        self.assertEqual([x for x in yes if not RC.sender_allowed(x)], [])
        self.assertEqual([x for x in no if RC.sender_allowed(x)], [])
        self.assertTrue(RC.sender_allowed("a@example.org", domains=("example.org",)))   # one setting
        self.assertEqual(RC.ALLOWED_SENDER_DOMAINS, ("nasa.gov",))


class Privacy(unittest.TestCase):

    def test_reviewers_files_stay_local(self):
        """Everything in annotations/reviews/ but its README is kept out of Git, and nothing else there ever was."""
        def ignored(path):
            return subprocess.run(["git", "check-ignore", "-q", path], cwd=ROOT).returncode == 0
        for name in ("comments_Jane_Smith_2026-10-24.csv", "email.eml", "pasted.txt", "notes.md"):
            self.assertTrue(ignored(f"annotations/reviews/{name}"), name)
        self.assertFalse(ignored("annotations/reviews/README.md"))
        tracked = subprocess.run(["git", "log", "--all", "--name-only", "--format=", "--", "annotations/reviews"],
                                 cwd=ROOT, capture_output=True, text=True).stdout.split()
        self.assertEqual(set(tracked), {"annotations/reviews/README.md"})


class Publish(unittest.TestCase):
    """--publish, in a temporary Git repository: the branch gh-pages holds the page and .nojekyll, nothing else;
    the checked-out branch and the working folder are untouched."""

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.repo, capture_output=True, text=True, encoding="utf-8", check=True).stdout.strip()

    def test_publish(self):
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            self.repo = t / "repo"
            self.repo.mkdir()
            self.git("init", "-q", "-b", "main")
            self.git("config", "user.email", "test@example.org")
            self.git("config", "user.name", "Test")
            (self.repo / "notes.txt").write_text("mine", encoding="utf-8")
            (self.repo / "reviews.csv").write_text("a reviewer's comment", encoding="utf-8")   # never published
            self.git("add", "notes.txt")
            self.git("commit", "-q", "-m", "first")
            paths = files(t)
            done = R.publish(root=self.repo, push=False, check_clean=False, **paths)
            self.assertTrue(done["changed"])
            self.assertEqual(self.git("ls-tree", "-r", "--name-only", "gh-pages").split(), [".nojekyll", "review/index.html"])
            version = R.page_data(**paths)["version"]
            self.assertEqual(page_json(self.git("show", "gh-pages:review/index.html"))["version"]["content"], version["content"])
            self.assertEqual(done["version"], version["id"])
            self.assertEqual(self.git("rev-parse", "--abbrev-ref", "HEAD"), "main")
            self.assertEqual(self.git("status", "--porcelain"), "?? reviews.csv")
            again = R.publish(root=self.repo, push=False, check_clean=False, **paths)
            self.assertFalse(again["changed"])
            self.assertEqual(self.git("rev-list", "--count", "gh-pages"), "1")
            self.assertEqual(done["url"], "https://iulia-iordanescu.github.io/datanasagov_KG_proj/review/")

    def test_uncommitted_changes_stop(self):
        with tempfile.TemporaryDirectory() as t, \
                mock.patch.object(R, "page_data", return_value={"version": {"edited": True}}):
            with self.assertRaisesRegex(RuntimeError, "changes not yet committed"):
                R.publish(root=Path(t), push=False)

    def test_uncommitted_changes_named_whole(self):
        """Each file is named whole, the first one too (git's status lines start with a space git's output loses)."""
        with tempfile.TemporaryDirectory() as t, \
                mock.patch.object(R, "page_data", return_value={"version": {"edited": False}}), \
                mock.patch.object(R, "_git", return_value="M docs/terminology.md\n M helpers/review_page.py\n?? new file.txt"):
            with self.assertRaises(RuntimeError) as stop:
                R.publish(root=Path(t), push=False)
        self.assertIn("docs/terminology.md, helpers/review_page.py, new file.txt. Commit them", str(stop.exception))


# ------------------------------ questions for experts --------------------------

TUNING, HELD_OUT = "aaaaaaaa-0000-0000-0000-000000000001", "bbbbbbbb-0000-0000-0000-000000000002"
Q_SCHEMA = SCHEMA.replace("PREDICATES", """Dataset           a set of observations
SpatialRepresentation  how data are laid out over the ground

PREDICATES""") + """HAS_SPATIAL_REPRESENTATION  lays out its data as
                            Dataset -> SpatialRepresentation
"""
Q_MAPPING = MAPPING + "entity class,Layout,SpatialRepresentation,no,yes,How data are arranged.,how data are laid out over the ground\n"
GUIDELINES = """# Annotation guidelines

## Writing a classed triple

1. **[Subject instance](x.md) and object instance: the record's own words, as written.** Don't paraphrase them.
"""
QUESTION = """# Questions

Not read: the file's own introduction.

## Q1: Should SpatialRepresentation be a closed list?

- status: open
- priority: high
- question kind: schema entry
- topic: the ground truth schema's SpatialRepresentation

### The question

Is a [record](../docs/terminology.md#1-records-and-their-text)'s layout a closed list? A table:

| What collects the data | Spatial representations |
|---|---|
| a satellite | swath; gridded |

### Example record

- record id: {tuning}
- pool position: 0
- title: Snow V1
- notes: Each file holds 5 minutes of
  swath data.

  A second paragraph.
- source text: 5 minutes of swath data
- classed triple: "Snow V1" (Dataset) HAS_SPATIAL_REPRESENTATION "swath" (SpatialRepresentation)

### Ground truth schema

- entity class SpatialRepresentation: how data are laid out over the ground

### Translation table

- entity class Layout -> SpatialRepresentation: How data are arranged.

### Annotation guidelines

- Writing a classed triple, rule 1: Subject instance and object instance: the record's own words, as written.

### Options

#### Option 1: Keep each record's own words

Each record keeps its words.

#### Option 2: A closed list

One value per layout.

### My current reading

Undecided.

### My notes

The example is the record at pool position 0.

### Consequences

#### Option 1: Keep each record's own words

- The words differ between records.

#### Option 2: A closed list

- A new exception to rule 1.

### Affects

- record at pool position 0: {tuning}
- classed triple of the record at pool position 0: "Snow V1" (Dataset) HAS_SPATIAL_REPRESENTATION "swath" (SpatialRepresentation)
- ground truth schema entry: entity class SpatialRepresentation
- translation table row: entity class Layout
- rule: Writing a classed triple, rule 1
""".replace("{tuning}", TUNING)


def question_world(folder: Path, questions: str = QUESTION) -> dict:
    """The stand-in files a question is checked against: the schema, the translation table, the questions, 020's
    records, 030's splits (one tuning record, one held-out), the ground truth, the guidelines."""
    paths = files(folder, Q_SCHEMA, Q_MAPPING, questions)
    (folder / "records.jsonl").write_text("\n".join(json.dumps(r) for r in [
        {"id": TUNING, "title": "Snow V1", "notes": "Each file holds 5 minutes of swath data.\n\nA second paragraph."},
        {"id": HELD_OUT, "title": "Ice V2", "notes": "Gridded ice."}]) + "\n", encoding="utf-8")
    (folder / "splits.json").write_text(json.dumps({"ground_truth_candidates": {"records": [
        {"id": TUNING, "position": 0, "part": "tuning"}, {"id": HELD_OUT, "position": 1, "part": "held-out"}]}}),
        encoding="utf-8")
    (folder / "gt").mkdir(exist_ok=True)
    (folder / "gt" / "batch_000.csv").write_text(
        "id,subject,subject_class,predicate,object,object_class,source_text,all_facts_extracted\n"
        f"{TUNING},Snow V1,Dataset,HAS_SPATIAL_REPRESENTATION,swath,SpatialRepresentation,5 minutes of swath data,1\n",
        encoding="utf-8")
    (folder / "guidelines.md").write_text(GUIDELINES, encoding="utf-8")
    return {**paths, "records_path": folder / "records.jsonl", "splits_path": folder / "splits.json",
            "ground_truth_dir": folder / "gt", "guidelines_path": folder / "guidelines.md"}


def questions_of(paths: dict) -> list:
    keep = ("questions_path", "records_path", "splits_path", "ground_truth_dir", "schema_path", "guidelines_path",
            "mapping_path")
    return R.questions_data(**{k: paths[k] for k in keep}, terms=R.glossary())


class Questions(unittest.TestCase):
    """annotations/questions_for_experts.md: read in its strict format, every quote checked against its source,
    held-out records refused, Affects complete; on the page, its own view; comments on a question come back like
    any other, marked when the question changed since."""

    def test_read(self):
        with tempfile.TemporaryDirectory() as t:
            q, = questions_of(question_world(Path(t)))
        self.assertEqual((q["id"], q["status"], q["priority"], q["question_kind"]), ("Q1", "open", "high", "schema entry"))
        self.assertEqual(q["records"][0]["notes"], "Each file holds 5 minutes of swath data.\n\nA second paragraph.")
        self.assertEqual(q["question"][1]["table"], [["What collects the data", "Spatial representations"],
                                                     ["a satellite", "swath; gridded"]])
        self.assertIn('<a class="term" data-term="record"', q["question"][0]["p"])
        self.assertEqual([len(v) for v in q["affects"].values()], [1, 1, 1, 1, 1, 0])
        self.assertEqual(q["affects"]["records"][0]["title"], "Snow V1")
        self.assertEqual([o["consequences"] for o in q["options"]], [["The words differ between records."],
                                                                     ["A new exception to rule 1."]])
        self.assertRegex(q["shown"], r"^Q1: Should SpatialRepresentation be a closed list\? \| fingerprint [0-9a-f]{12}$")

    def test_not_in_the_format_is_refused(self):
        """Each breach is refused, naming the file's line and what is expected."""
        cases = {"- status: open\n": ("- status: maybe\n", "line 7 (Q1): its status is \"maybe\""),
                 "- priority: high\n": ("- priority: urgent\n", "its priority is \"urgent\""),
                 "- question kind: schema entry\n": ("", "no \"- question kind: …\" line"),
                 "### Affects\n": ("### Effects\n", "isn't one of a question's parts"),
                 "### My current reading\n\nUndecided.\n": ("", "no \"### My current reading\" part"),
                 "|---|---|\n": ("|---|\n", "a table is a header line"),
                 "One value per layout.\n": ("One value per layout.\n\nConsequences:\n- More work.\n",
                                              "option 2: its consequences go under \"### Consequences\""),
                 "#### Option 2: A closed list\n\n- A new": ("#### Option 2: A list\n\n- A new",
                                                            "the same numbers and titles"),
                 "### Consequences\n": ("### Effects of each\n", "isn't one of a question's parts"),
                 "### Ground truth schema\n": (QUESTION.split("### Example record\n")[1].split("### Ground")[0]
                                              .join(["### Example record\n", "### Ground truth schema\n"]),
                                              "is there twice: a question shows one record"),
                 "Is a [record]": ("At pool position 0, is a [record]", "\"pool position\" is in what the expert reads"),
                 "Undecided.\n": (f"Undecided, as for {TUNING}.\n", f"\"{TUNING}\" is in what the expert reads")}
        for old, (new, words) in cases.items():
            with self.subTest(old=old), tempfile.TemporaryDirectory() as t:
                self.assertIn(old, QUESTION)
                with self.assertRaises(ValueError) as stop:
                    questions_of(question_world(Path(t), QUESTION.replace(old, new, 1)))
                self.assertIn(words, str(stop.exception))
                self.assertIn("questions_for_experts.md, line", str(stop.exception))

    def test_a_held_out_record_is_refused(self):
        with tempfile.TemporaryDirectory() as t:
            text = QUESTION.replace("- record at pool position 0: " + TUNING + "\n",
                                    "- record at pool position 0: " + TUNING + "\n- record at pool position 1: " + HELD_OUT + "\n")
            with self.assertRaises(ValueError) as stop:
                questions_of(question_world(Path(t), text))
        self.assertIn(f"record {HELD_OUT} (pool position 1) is a held-out record", str(stop.exception))

    def test_quotes_and_affects_are_checked(self):
        """A quote that isn't its source's words now, and an Affects that leaves out what an entry it names brings."""
        cases = [("- title: Snow V1", "- title: Snow V2", "the title quoted isn't the record's title"),
                 ("- source text: 5 minutes of swath data", "- source text: 6 minutes", "isn't in record"),
                 ("- entity class SpatialRepresentation: how data are laid out over the ground",
                  "- entity class SpatialRepresentation: how data lie", "is now \"how data are laid out over the ground\""),
                 ("the record's own words, as written.\n\n### Options", "the record's words.\n\n### Options",
                  "aren't the words of rule 1"),
                 ("- translation table row: entity class Layout\n", "",
                  "row entity class Layout (current or past schema) translates to SpatialRepresentation"),
                 ("- classed triple of the record at pool position 0: \"Snow V1\" (Dataset) HAS_SPATIAL_REPRESENTATION "
                  "\"swath\" (SpatialRepresentation)\n", "", "which \"Affects\" doesn't name: add it"),
                 ("## Q1: Should", "## Q1: Should [rows](../docs/terminology.md#8) and", None),
                 ("One value per layout.", 'One value per layout, as the record "Snow V1" has.', None),
                 ("One value per layout.", 'One value per layout, as the record "Snow V2" has.',
                  '"Snow V2" follows the word "record", but isn\'t the title of a record "Affects" names'),
                 ("One value per layout.", 'One value per layout, as the records "Snow V1" and "Ice V2" have.',
                  '"Ice V2" follows the word "record"')]
        for old, new, words in cases:
            with self.subTest(old=old[:40]), tempfile.TemporaryDirectory() as t:
                self.assertIn(old, QUESTION)
                text = QUESTION.replace(old, new, 1)
                if words is None:                                              # a link in a heading: plain words
                    self.assertEqual(len(questions_of(question_world(Path(t), text))), 1)
                    continue
                with self.assertRaises(ValueError) as stop:
                    questions_of(question_world(Path(t), text))
                self.assertIn(words, str(stop.exception))

    def test_a_link_to_a_term_not_shown(self):
        with tempfile.TemporaryDirectory() as t:
            text = QUESTION.replace("Is a [record]", "Is a [stand-in catalog](../docs/terminology.md#8-the-pipeline) [record]")
            with self.assertRaises(ValueError) as stop:
                questions_of(question_world(Path(t), text))
        self.assertIn("isn't a term of the page's Terms view", str(stop.exception))

    def test_the_real_file(self):
        """The real questions file, read and checked against the real sources (when 020 and 030 have run here)."""
        if not (R.RECORDS_PATH.exists() and R.SPLITS_PATH.exists()):
            self.skipTest("020's records.jsonl or 030's splits.json isn't on this computer")
        qs = R.questions_data(terms=R.glossary())
        self.assertTrue(qs)
        self.assertEqual([q["id"] for q in qs], [f"Q{i}" for i in range(1, len(qs) + 1)])
        self.assertTrue(all(len(q["records"]) <= 1 for q in qs))

    def test_the_expert_never_reads_a_pool_position(self):
        """What the expert reads of each question of the real file (its title, its parts for the expert, its
        example's title and notes, the quotes) says no "pool position" and no record id: records are named by title."""
        for q in R.read_questions(R.QUESTIONS_PATH):
            seen = [q["title"]] + [html.unescape(str(q[k])) for k in ("question", "context", "reading", "answer")]
            seen += [str(o["body"]) + o["title"] for o in q["options"]]
            seen += [r["title"] + r["notes"] + str(r["triples"]) for r in q["records"]]
            seen += [x["definition"] for x in q["schema"] + q["rows"]] + [r["words"] for r in q["rules"]]
            for text in seen:
                self.assertNotIn("pool position", text.lower(), q["id"])
                self.assertNotRegex(text, r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}", q["id"])

    def test_comments_on_a_question(self):
        """A comment on a question, read back: unchanged, then changed once the question's words change (its status
        doesn't count); gone when the question is."""
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            paths = files(t, Q_SCHEMA, Q_MAPPING, QUESTION)
            shown = R.entry_texts(**paths)[("question", "Q1")]
            reviews = t / "reviews"
            reviews.mkdir()
            Comments.write(None, reviews, "a.csv", [Comments.row(None, "question", "Q1", shown, "A closed list.")])
            read = lambda: {c["entry"]: c["state"] for c in R.read_all([reviews], **paths)["comments"]}  # noqa: E731
            self.assertEqual(read(), {"Q1": "unchanged"})
            paths["questions_path"].write_text(QUESTION.replace("- status: open", "- status: withdrawn")
                                               .replace("- priority: high", "- priority: low"), encoding="utf-8")
            self.assertEqual(read(), {"Q1": "unchanged"})
            paths["questions_path"].write_text(QUESTION.replace("Undecided.", "A closed list."), encoding="utf-8")
            self.assertEqual(read(), {"Q1": "changed"})
            _, text = R.read_and_summarize([reviews], out_dir=t / "out", **paths)
            self.assertIn("## Questions for experts (annotations/questions_for_experts.md)", text)
            self.assertIn("### Q1: Should SpatialRepresentation be a closed list?", text)
            paths["questions_path"].write_text("# Questions\n", encoding="utf-8")
            self.assertEqual(read(), {"Q1": "gone"})
            paths["questions_path"].write_text("# Questions\n\n## Q1 no colon\n", encoding="utf-8")
            got = R.read_all([reviews], **paths)
            self.assertEqual([c["state"] for c in got["comments"]], ["gone"])
            self.assertIn("The questions can't be read", got["problems"][-1])


@unittest.skipUnless(CHROME, "no Chrome or Edge on this computer to run the page's script")
class QuestionsView(unittest.TestCase):
    """The Questions view, in headless Chrome: its tab; a question whole, its terms linked once each to the Terms
    view; the filters; one at a time; a comment on it sent by email and read back with --read."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        second = QUESTION.split("## Q1: ")[1].replace("Should SpatialRepresentation be a closed list?", "A second one",
                                                      1).replace("- priority: high", "- priority: low")
        third = second.replace("A second one", "An answered one", 1).replace("- status: open", "- status: answered") \
            .replace("### My notes\n", "### The answer\n\nYes.\n\n### My notes\n")
        cls.paths = question_world(cls.tmp, QUESTION + "\n## Q2: " + second + "\n## Q3: " + third)
        cls.page = R.build(R.page_data(**cls.paths))
        script = ("const out = {}; try { show('questions'); const v = () => document.getElementById('view');"
                  "out.text = v().textContent; out.cards = [...v().querySelectorAll('.question .qid')].map((e) => e.textContent);"
                  "out.groups = [...v().querySelectorAll('.groupname')].map((e) => e.textContent);"
                  "const card = v().querySelector('#q-Q1');"
                  "out.terms = [...card.querySelectorAll('a.term')].map((a) => a.dataset.term);"
                  "out.marked = [...card.querySelectorAll('mark')].map((m) => m.textContent);"
                  "out.affects = [...card.querySelectorAll('details.forus h5')].map((h) => h.textContent).join(' | ');"
                  "out.forus = card.querySelector('details.forus summary').textContent; out.forusOpen = card.querySelector('details.forus').open;"
                  "out.last = card.lastElementChild.tagName + '.' + card.lastElementChild.className;"
                  "const top = card.cloneNode(true); top.querySelector('details.forus').remove(); out.top = top.textContent;"
                  "out.tab = document.getElementById('tab-questions').getAttribute('aria-current');"
                  "state.questions.closed = true; redraw(); out.withClosed = [...v().querySelectorAll('.question .qid')].map((e) => e.textContent);"
                  "state.questions.priority = 'low'; redraw(); out.low = [...v().querySelectorAll('.question .qid')].map((e) => e.textContent);"
                  "state.questions.priority = 'all'; oneAtATime = true; redraw(); out.one = [...v().querySelectorAll('.question .qid')].map((e) => e.textContent);"
                  "listStep.go(1); out.next = [...v().querySelectorAll('.question .qid')].map((e) => e.textContent); oneAtATime = false; redraw();"
                  "document.querySelector('#q-Q1 a.term').click(); out.afterClick = view; out.here = document.querySelector('.terms tr.here').id;"
                  "setComment(BY_ID['question|Q1'], 'A closed list, please.'); reviewer = 'Jane Smith';"
                  "out.bodies = emailParts('2026-10-25T12:00:00-04:00').parts.map((p) => decodeURIComponent(p.url.split('body=')[1]));"
                  "out.csv = commentsCsv(); } catch (e) { out.error = String(e) + ' ' + e.stack; }"
                  "document.body.setAttribute('data-out', JSON.stringify(out));")
        cls.out = json.loads(run_page(cls.page, script, cls.tmp))
        assert "error" not in cls.out, cls.out["error"]

    def test_the_view(self):
        self.assertEqual(self.out["tab"], "page")
        self.assertEqual(self.out["cards"], ["Q1", "Q2"])                     # the answered one hidden at first
        self.assertEqual(self.out["groups"], ["High priority (1)", "Low priority (1)"])
        self.assertEqual(self.out["withClosed"], ["Q1", "Q2", "Q3"])
        self.assertEqual(self.out["low"], ["Q2", "Q3"])
        self.assertEqual((self.out["one"], self.out["next"]), (["Q1"], ["Q2"]))
        for words in ("An example", "Each file holds 5 minutes of", "My current reading", "Option 2: A closed list",
                      "The choices I see"):
            self.assertIn(words, self.out["top"])
        for words in ("pool position", TUNING, "A new exception to rule 1", "The example is the record at pool position 0",
                      "What each option would change", "My notes"):
            self.assertNotIn(words, self.out["top"])                         # the expert's part: none of my bookkeeping
            self.assertIn(words, self.out["text"])                           # all of it at the bottom, folded
        self.assertEqual((self.out["forus"], self.out["forusOpen"], self.out["last"]),
                         ("The answer to this question impacts: my bookkeeping, not needed to answer", False,
                          "DETAILS.forus"))
        self.assertIn("1 record, 1 classed triple, 1 row of the translation table", self.out["affects"])

    def test_terms_linked_once(self):
        terms = self.out["terms"]
        self.assertEqual(len(terms), len(set(terms)))
        for t in ("record", "ground truth schema", "ground truth candidates pool", "tuning part", "classed triple"):
            self.assertIn(t, terms)
        self.assertEqual((self.out["afterClick"], self.out["here"]), ("terms", "term-" + terms[0].replace(" ", "-")))
        self.assertIn("5 minutes of swath data", self.out["marked"])

    def test_comment_round_trip(self):
        """Emailed and downloaded, and read back with --read, as the same comment on Q1, unchanged."""
        folder = Path(tempfile.mkdtemp(dir=self.tmp))
        for i, b in enumerate(self.out["bodies"]):
            (folder / f"p{i}.txt").write_text(b, encoding="utf-8")
        (folder / "comments_Jane_Smith.csv").write_text(self.out["csv"], encoding="utf-8")
        for f in (folder / "p0.txt", folder / "comments_Jane_Smith.csv"):
            read = R.read_all([f], **{k: self.paths[k] for k in ("schema_path", "mapping_path", "questions_path")})
            self.assertEqual([(c["topic"], c["entry"], c["comment"], c["state"]) for c in read["comments"]],
                             [("question", "Q1", "A closed list, please.", "unchanged")], f.name)


if __name__ == "__main__":
    unittest.main()
