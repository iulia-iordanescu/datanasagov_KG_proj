"""
tests/test_parallel.py -- things that should be the same across the pipeline stay the same.

Families of things the steps share (the prompts' guard and reply line, the blocks 050 and 060 share, the settings,
how each stage calls the model, how replies are read) are compared member by member. A difference fails here unless
tests/allowed_differences.txt lists it with its reason, and a listed difference that no longer exists fails too (a
stale line). Also: every setting a run records is the setting its request sent (recorded = sent), and the prompt
fingerprints a run records are those of the prompt files it read.

Built after the test audit of 2026-10-30 (drift found: the two-pass instruction in 060's prompt only, 060 without
the completeness sentence, settings recorded that were never sent).
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import sys
import unittest
from pathlib import Path
from unittest import mock

from support import EXCLUDED_DIRS, ROOT

from common import llm, prompt_files                                          # noqa: E402

ALLOWED = ROOT / "tests" / "allowed_differences.txt"
STEPS = ("040", "050", "060", "070")
COMMON_PROMPTS = ROOT / "common" / "common_prompts"


def allowed(family: str) -> list:
    """[(member, kind, difference, reason, decided)] of one family of tests/allowed_differences.txt."""
    rows = []
    for line in ALLOWED.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            parts = line.split("\t")
            if parts[0] == family:
                rows.append(tuple(parts[1:]))
    return rows


def is_allowed(family: str, member: str, kind: str) -> bool:
    return any(r[0] == member and r[1] == kind for r in allowed(family))


def step_prompts() -> list:
    """Every prompt a step sends: the files in <step>/<step>_prompts/ (common/common_prompts holds blocks they
    include, not prompts of their own)."""
    return sorted(p for p in ROOT.glob("*/*_prompts/*.txt")
                  if not p.relative_to(ROOT).as_posix().startswith(EXCLUDED_DIRS) and p.parent.parent.name[:3] in STEPS)


def member_of(path: Path) -> str:
    return path.parent.parent.name[:3]


def placeholders(text: str) -> list:
    return re.findall(r"\$(\w+)", text.replace("$$", ""))


GUARD = re.compile(r"is (?:DATA|data)\b.*?ignore it", re.S)
JSON_LINE = "Return only JSON, with no prose"


class TheAllowList(unittest.TestCase):
    def test_every_line_is_complete(self):
        families = {"rules", "prompts", "settings", "model-calls", "parsing"}
        for n, line in enumerate(ALLOWED.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip() or line.startswith("#"):
                continue
            with self.subTest(line=n):
                parts = line.split("\t")
                self.assertEqual(len(parts), 6, "a line needs family, member, kind, difference, reason, decided")
                self.assertIn(parts[0], families)
                self.assertTrue(parts[3].strip() and parts[4].strip(), "a difference needs its words and its reason")
                self.assertRegex(parts[5], r"^\d{4}-\d{2}-\d{2}$")


class Prompts(unittest.TestCase):
    """Every prompt guards against instructions inside the data it carries, and asks for JSON in the same words."""

    def test_the_shared_rules_carry_the_guard(self):
        self.assertRegex((COMMON_PROMPTS / "extraction_rules.txt").read_text(encoding="utf-8"), GUARD)

    def test_every_prompt_guards_its_data(self):
        for path in step_prompts():
            with self.subTest(prompt=path.relative_to(ROOT).as_posix()):
                text = path.read_text(encoding="utf-8")
                self.assertTrue(GUARD.search(text) or "rules" in placeholders(text),
                                "this prompt carries data with no sentence saying it is data and to ignore any "
                                "instruction in it: add one (as 040's and 070's prompts have), or include $rules")

    def test_every_prompt_asks_for_json_in_the_same_words(self):
        reply = (COMMON_PROMPTS / "extraction_reply.txt").read_text(encoding="utf-8")
        self.assertIn(JSON_LINE, reply)
        differ = set()
        for path in step_prompts():
            text = path.read_text(encoding="utf-8")
            if JSON_LINE not in text and "reply" not in placeholders(text):
                self.assertRegex(text, r"(?i)return only json", path.name)
                differ.add(member_of(path))
        for member in differ:
            self.assertTrue(is_allowed("prompts", member, "json-line"),
                            f"{member}'s prompts word the JSON line differently: say \"{JSON_LINE}\", or list it "
                            f"in tests/allowed_differences.txt (family prompts, kind json-line) with its reason")
        for member, kind, *_ in allowed("prompts"):
            if kind == "json-line":
                self.assertIn(member, differ, f"stale line: {member}'s prompts now say \"{JSON_LINE}\"")

    def test_shared_phrases_come_from_one_file(self):
        """The completeness sentence, the two passes and the closing line are in common/common_prompts only: a step's
        prompt includes them ($passes, $closing), so no step can say them differently."""
        markers = {"completeness": "extraction_passes.txt", "two passes": "extraction_passes.txt",
                   "now state every fact": "extraction_closing.txt"}
        for marker, home in markers.items():
            self.assertIn(marker, (COMMON_PROMPTS / home).read_text(encoding="utf-8").lower())
        own = set()
        for path in step_prompts():
            text = path.read_text(encoding="utf-8").lower()
            if any(m in text for m in markers):
                own.add(member_of(path))
        for member in own:
            self.assertTrue(is_allowed("prompts", member, "shared-phrases"),
                            f"{member}'s prompt says a shared sentence in its own words: include the shared block "
                            f"instead, or list it in tests/allowed_differences.txt (family prompts, kind shared-phrases)")
        for member, kind, *_ in allowed("prompts"):
            if kind == "shared-phrases":
                self.assertIn(member, own, f"stale line: {member}'s prompt no longer has its own copy")


def sections(text: str) -> list:
    """A template's headers and placeholders, in order: the layout two prompts must share."""
    out = []
    for line in text.splitlines():
        s = line.strip()
        if re.fullmatch(r"[A-Z][A-Z _]{2,}|-{5} .+ -{5}", s):
            out.append(s)
        out += ["$" + p for p in placeholders(line)]
    return out


def task_paragraphs(text: str) -> list:
    """The paragraphs of a template's TASK section (between TASK and $reply), placeholders left out."""
    task = text.split("\nTASK\n", 1)[1].split("$reply", 1)[0]
    return [" ".join(p.split()) for p in re.split(r"\n\s*\n", task) if p.strip() and not p.strip().startswith("$")]


class FiftyAndSixty(unittest.TestCase):
    """050 drafts and 060 extracts with one layout, the same shared blocks and the same words, except where their
    tasks differ (tests/allowed_differences.txt, family prompts, kind task)."""
    T050 = ROOT / "050_annotate" / "050_annotate_prompts" / "draft.txt"
    T060 = ROOT / "060_extract" / "060_extract_prompts" / "extract.txt"

    def test_same_layout(self):
        a, b = (p.read_text(encoding="utf-8") for p in (self.T050, self.T060))
        self.assertEqual(sections(a), sections(b))

    def test_same_gloss(self):
        for path in (self.T050, self.T060):
            self.assertIn("each with an entity class (the kind of thing it is) for the subject and for the object",
                          " ".join(path.read_text(encoding="utf-8").split()), path.name)

    def test_task_paragraphs_differ_only_as_listed(self):
        texts = {"050": task_paragraphs(self.T050.read_text(encoding="utf-8")),
                 "060": task_paragraphs(self.T060.read_text(encoding="utf-8"))}
        for member, other in (("050", "060"), ("060", "050")):
            only = [p for p in texts[member] if p not in texts[other]]
            starts = [re.search(r'"([^"]+)"', r[2]).group(1).rstrip(" …")
                      for r in allowed("prompts") if r[0] == member and r[1] == "task"]
            for paragraph in only:
                with self.subTest(member=member, paragraph=paragraph[:50]):
                    self.assertTrue(any(paragraph.startswith(s) for s in starts),
                                    f"a TASK paragraph only {member}'s prompt has: list it in "
                                    f"tests/allowed_differences.txt (family prompts, member {member}, kind task), "
                                    f"quoting its first words, with its reason")
            for s in starts:
                self.assertTrue(any(p.startswith(s) for p in only), f"stale line: no paragraph only in {member}'s "
                                f"TASK starts \"{s}\"")


def settings_of(step_dir: Path) -> dict:
    """{setting: (value as written, comment)} of a step's run.py SETTINGS."""
    text = (step_dir / "run.py").read_text(encoding="utf-8")
    block = text.split("SETTINGS = {", 1)[1].split("\n}", 1)[0]
    out = {}
    for line in block.splitlines():
        m = re.match(r'\s*"(\w+)":\s*(.+?),\s*(?:#\s*(.*))?$', line)
        if m:
            out[m.group(1)] = (" ".join(m.group(2).split()), " ".join((m.group(3) or "").split()))
    return out


SHARED_SETTINGS = ("max_chars", "workers", "service", "model", "thinking", "confirm_paid_calls")
STEP_DIRS = {"040": "040_induce_schema", "050": "050_annotate", "060": "060_extract", "070": "070_evaluate"}


class Settings(unittest.TestCase):
    """The settings the model-calling steps share have the same default and the same comment as 060's, unless the
    difference is listed (family settings)."""

    def test_same_as_060_or_listed(self):
        reference = settings_of(ROOT / STEP_DIRS["060"])
        differ = set()
        for member in ("040", "050", "070"):
            own = settings_of(ROOT / STEP_DIRS[member])
            for key in SHARED_SETTINGS:
                if own.get(key) != reference[key]:
                    differ.add((member, key))
                    with self.subTest(step=member, setting=key):
                        self.assertTrue(is_allowed("settings", member, key),
                                        f"{STEP_DIRS[member]}/run.py's {key} ({own.get(key)}) differs from 060's "
                                        f"({reference[key]}): make them the same, or list it in "
                                        f"tests/allowed_differences.txt (family settings) with its reason")
        for member, kind, *_ in allowed("settings"):
            self.assertIn((member, kind), differ, f"stale line: {member}'s {kind} is now the same as 060's")

    def test_050_and_060_split_texts_alike(self):
        """060 is evaluated against ground truth drafted by 050 on equal terms: the same text pieces. No exception."""
        self.assertEqual(settings_of(ROOT / STEP_DIRS["050"])["max_chars"][0],
                         settings_of(ROOT / STEP_DIRS["060"])["max_chars"][0])


def call_sites() -> dict:
    """{file: how it calls the model} for every file that calls it: extraction.ask_model (with or without
    cache_until) or ask_cached (with or without ask_split)."""
    found = {}
    for path in sorted(ROOT.glob("*/*_helpers/*.py")) + sorted((ROOT / "common" / "common_helpers").glob("*.py")):
        rel = path.relative_to(ROOT).as_posix()
        if rel.startswith(EXCLUDED_DIRS):
            continue
        text = path.read_text(encoding="utf-8")
        calls = [m for m in re.finditer(r"(?<!def )\b(extraction\.ask_model|ask_cached)\(", text)]
        if not calls:
            continue
        if any(m.group(1) == "extraction.ask_model" for m in calls):
            call = text[calls[0].start():calls[0].start() + 600]
            found[rel] = ("extraction.ask_model with cache_until." if "cache_until=" in call
                          else "extraction.ask_model; no cache_until.")
        else:
            found[rel] = ("ask_cached with ask_split." if re.search(r"\bask_split\(", text)
                          else "ask_cached, no ask_split.")
    return found


class ModelCalls(unittest.TestCase):
    """Every stage that calls the model is in the declared table (family model-calls), saying how it calls: a new
    stage, or a stage that now calls differently, fails until the table says so, with the reason."""

    def test_every_stage_declared(self):
        declared = {r[0]: r[2] for r in allowed("model-calls")}
        self.assertEqual(call_sites(), declared)

    def test_only_the_shared_paths_call_the_service(self):
        """Nothing calls the service but the shared paths (the cache and extraction.ask_model): a stage can't skip the
        cache, the shape check or the paid-call guards."""
        for path in sorted(ROOT.glob("*/*_helpers/*.py")) + sorted((ROOT / "common" / "common_helpers").glob("*.py")):
            rel = path.relative_to(ROOT).as_posix()
            if rel.startswith(EXCLUDED_DIRS) or rel.endswith(("llm.py", "cache.py", "extraction.py")):
                continue
            with self.subTest(file=rel):
                self.assertNotRegex(path.read_text(encoding="utf-8"), r"\bcall_llm(?:_json)?\(")


def step_module(step: str, name: str):
    path = ROOT / step / f"{step}_helpers" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"{step}_{name}", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module                    # dataclasses look their module up there
    spec.loader.exec_module(module)
    return module


class Parsing(unittest.TestCase):
    """040 reads a reply's slots as 050 and 060 do; how it counts duplicates differs only as listed."""

    def test_numbers_read_alike(self):
        from common.triples_io import clean_triple
        extract040 = step_module("040_induce_schema", "extract")
        item = {"subject": "Kestrel", "predicate": "launched in", "object": 2020, "source_text": "launched in 2020"}
        good, bad, _ = extract040._from_reply({"triples": [item]})
        self.assertEqual((len(good), bad), (1, 0))
        self.assertEqual(good[0]["object"], clean_triple({**item, "subject_class": "X", "object_class": "Y",
                                                          "predicate": "P"})["object"])

    def test_duplicates_differ_as_listed(self):
        from common.triples_io import triple_key
        a = {"subject": "MODIS", "predicate": "IS ABOARD", "object": "Aqua"}
        b = {"subject": "modis", "predicate": "IS ABOARD", "object": "aqua"}
        same_for_040 = tuple(a.values()) == tuple(b.values())
        same_for_050_060 = triple_key({**a, "subject_class": "X", "object_class": "Y"}) == \
            triple_key({**b, "subject_class": "X", "object_class": "Y"})
        differs = same_for_040 != same_for_050_060
        self.assertEqual(differs, is_allowed("parsing", "040", "duplicates"),
                         "040's duplicate rule and 050/060's: the difference and tests/allowed_differences.txt "
                         "(family parsing) disagree")


class Reply:
    def __init__(self, body):
        self.status_code, self._body, self.text = 200, body, json.dumps(body)

    def json(self):
        return self._body

    def raise_for_status(self):
        pass


MODELS = ("claude-opus-5.5", "gemini-2.5-pro", "gemini-3-pro", "gpt-5")


class RecordedIsSent(unittest.TestCase):
    """What a run records about a call (describe, call_settings, the failed-call record's settings, the report's
    *Model calls* line) is what the request sent, for each service and model: a setting not sent says "not sent"."""

    def setUp(self):
        self.saved = (llm.MODEL, llm.SERVICE, llm.THINKING)

    def tearDown(self):
        llm.MODEL, llm.SERVICE, llm.THINKING = self.saved
        llm.SERVED.clear()

    def sent(self, service, model):
        payloads = []

        def post(url, headers=None, json=None, timeout=None):
            payloads.append(json)
            if service == "litellm":
                return Reply({"model": model, "choices": [{"message": {"content": '{"ok": true}'},
                                                           "finish_reason": "stop"}]})
            return Reply({"status": 200, "message": '{"ok": true}'})
        with mock.patch.dict("os.environ", {"LITELLM_API_KEY": "sk-test", "LITELLM_BASE_URL": ""}), \
                mock.patch.object(llm.requests, "post", post), mock.patch.object(llm, "load_dotenv", lambda: None), \
                mock.patch.object(llm, "_asksage_token", lambda: "token"):
            llm.call_llm("hi", model=model, service=service)
        return payloads[0]

    def test_recorded_equals_sent(self):
        from common.report import model_calls
        for service in ("litellm", "asksage"):
            for model in MODELS:
                for thinking in ("low", "model_default"):
                    with self.subTest(service=service, model=model, thinking=thinking):
                        llm.MODEL, llm.SERVICE, llm.THINKING = model, service, thinking
                        payload = self.sent(service, model)
                        rec = llm.call_settings(model, service)
                        self.assertEqual(llm.describe(), {**llm.describe(), **rec})
                        if "temperature" in payload:
                            self.assertEqual(rec["temperature"], payload["temperature"])
                        else:
                            self.assertTrue(str(rec["temperature"]).startswith("not sent"))
                        if "max_tokens" in payload:
                            self.assertEqual(rec["max_answer_tokens"], payload["max_tokens"])
                        else:
                            self.assertTrue(str(rec["max_answer_tokens"]).startswith("not sent"))
                        self.assertEqual(rec["thinking_sent"], payload.get("reasoning_effort"))
                        if "reasoning_effort" not in payload:
                            self.assertTrue(str(rec["thinking"]).startswith("not sent"))
                        settings_sent = {k: v for k, v in payload.items() if k not in ("message", "messages")}
                        self.assertEqual(llm._last.reply["settings_sent"], settings_sent)
                        report = "\n".join(model_calls([("x", 1, 0)], 0, llm.model_label()))
                        self.assertIn(f"Temperature: {payload['temperature']}." if "temperature" in payload
                                      else "Temperature: not sent.", report)
                        if "max_tokens" in payload:
                            self.assertIn(f"({payload['max_tokens']:,} tokens)", report)
                        else:
                            self.assertIn("a cut-off can't be detected", report)
                        if "reasoning_effort" in payload:
                            self.assertIn(f"sent as `reasoning_effort` `{payload['reasoning_effort']}`", report)
                        else:
                            self.assertIn("not sent to this model", report)


class Fingerprints(unittest.TestCase):
    """prompt_files records each prompt read (filled or pasted) by the sha256 of its exact text, once, and forgets on
    reset; tests/test_pipeline.py checks each step's manifest against the files, also after a rerun from the cache."""

    def test_recorded_by_text(self):
        prompt_files.reset_prompts()
        path = ROOT / "060_extract" / "060_extract_prompts" / "extract.txt"
        template = prompt_files.load(path)
        prompt_files.text(template)
        prompt_files.text(template)
        reply = prompt_files.load(COMMON_PROMPTS / "extraction_reply.txt")
        prompt_files.fill(reply, fields="x")
        used = {u["file"]: u["sha256"] for u in prompt_files.prompts_used()}
        self.assertEqual(used, {
            "060_extract/060_extract_prompts/extract.txt": hashlib.sha256(path.read_bytes().decode("utf-8")
                                                                          .encode("utf-8")).hexdigest(),
            "common/common_prompts/extraction_reply.txt":
                hashlib.sha256((COMMON_PROMPTS / "extraction_reply.txt").read_text(encoding="utf-8")
                               .encode("utf-8")).hexdigest()})
        prompt_files.reset_prompts()
        self.assertEqual(prompt_files.prompts_used(), [])

    def test_a_plain_template_is_not_recorded(self):
        from string import Template
        prompt_files.reset_prompts()
        prompt_files.fill(Template("$a"), a="1")
        self.assertEqual(prompt_files.prompts_used(), [])


if __name__ == "__main__":
    unittest.main()
