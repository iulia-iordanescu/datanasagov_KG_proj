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


def files(folder: Path, schema: str = SCHEMA, mapping: str = MAPPING) -> dict:
    (folder / "ground_truth_schema.txt").write_text(schema, encoding="utf-8")
    (folder / "component_class_mapping.csv").write_text(mapping, encoding="utf-8")
    return {"schema_path": folder / "ground_truth_schema.txt", "mapping_path": folder / "component_class_mapping.csv"}


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
                         [R.fingerprint(self.tmp / "ground_truth_schema.txt"), R.fingerprint(self.tmp / "component_class_mapping.csv")])
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

    def write(self, folder: Path, name: str, rows: list) -> Path:
        path = folder / name
        with open(path, "w", encoding="utf-8-sig", newline="") as fh:
            w = csv.DictWriter(fh, R.COMMENT_COLUMNS, lineterminator="\r\n")
            w.writeheader()
            w.writerows(rows)
        return path

    def row(self, kind, entry, shown, comment, at="2026-10-24T10:00:00-04:00", who="Jane Smith"):
        return {"reviewer": who, "page_version": "review_2026-10-24_abc1234", "git_commit": "abc1234", "kind": kind,
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
ADDRESS = "iulia.m.iordanescu+kgreview@gmail.com"


def page_comments(now: dict) -> dict:
    """Comments as the page keeps them (its localStorage): a general one of two lines, a long one, one on an entry
    that changed since, one on a row of the translation table."""
    at = lambda m: f"2026-10-24T10:{m:02d}:00-04:00"                              # noqa: E731
    one = lambda kind, entry, text, m, shown: {"kind": kind, "entry": entry, "text": text, "at": at(m),  # noqa: E731
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
                  "comments = {}; for (let i = 0; i < 40; i++) comments['entity class|E' + i] = {kind: 'entity class', "
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
        return {f"{c['kind']}|{c['entry']}": (c["text"].strip(), c["shown"], c["at"], c["version"], c["commit"])
                for c in self.comments.values()}

    def got(self, read: dict) -> dict:
        return {f"{c['kind']}|{c['entry']}": (c["comment"], c["entry_text_shown"], c["timestamp"], c["page_version"],
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


if __name__ == "__main__":
    unittest.main()
