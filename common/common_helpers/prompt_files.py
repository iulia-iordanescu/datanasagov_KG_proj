"""
common/common_helpers/prompt_files.py -- reads the prompts steps send to a model.

Each prompt is a plain text file, readable and editable like a document:

    <step>/<step>_prompts/<name>.txt       a prompt used by one step
    common/common_prompts/<name>.txt       a prompt shared by several steps

A prompt marks the places the code fills in with $name (Python's
string.Template), e.g. $text for a record's text. A "$" meant literally is
written "$$". JSON braces in a prompt need no escaping.

    from common.prompt_files import load, fill
    template = load(PROMPTS_DIR / "extract.txt")      # PROMPTS_DIR: the step's <step>_prompts/ folder
    prompt = fill(template, text=piece)

A step that caches model answers folds the prompt's text (load(...).template)
into the cache key, so editing a prompt re-runs exactly what depended on it.

Every prompt filled in during a run is recorded (prompts_used): its file and
a fingerprint (sha256) of its exact text, so the run's report and manifest
say precisely which prompt texts its model answers came from, whether paid
for in this run or taken from the cache, and even if a prompt was edited
without being committed to Git.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from string import Template

from common.files import read_text

_used: dict = {}                     # {file, as the report names it: sha256 of its text}


class Prompt(Template):
    """A prompt's text, remembering the file it came from."""
    def __init__(self, text: str, path: Path):
        super().__init__(text)
        self.path = Path(path)


def load(path) -> Prompt:
    return Prompt(read_text(path), path)       # a byte-order mark (Notepad) never reaches the model


def again_note(problems: list) -> str:
    """What a second ask about some items adds under the filled prompt: what was wrong with the first reply about
    each, one line each ("- <item>: <what was wrong>"), after the instruction to answer for each again; "" when
    problems is empty. problems: [(item, what was wrong)]. So a second ask never sends the first prompt again word for
    word, which the answer cache (common/common_helpers/cache.py) would answer with the first reply, and the model
    learns what to correct, as common/common_helpers/llm_calls.py's call_llm_json says what was wrong with a reply of
    the wrong shape. Shared by 040's labeling (stage 3) and defining (stage 7)."""
    if not problems:
        return ""
    return ("\n\nYour last reply had a problem with each item listed here. Answer for each again, following the "
            "instructions above:\n" + "\n".join(f"- {item}: {why}" for item, why in problems))


def fill(template: Template, **values) -> str:
    """The prompt with every $name filled in. A $name with no value, or a
    stray "$", stops with an error instead of reaching the model half-filled.
    A prompt with $words gets the definitions of the terms it uses (words_for),
    unless the caller gives them. The prompt's file and fingerprint are
    recorded for the run's report."""
    _record(template)
    if "$words" in template.template and "words" not in values:
        values["words"] = words_for(template.template)
    return template.substitute(**values)


#: The definitions of the terms the prompts use (common/common_prompts/words.txt), one entry per term: those also in
#: the extraction rules' words section are worded as there (tests/test_parallel.py checks it).
WORDS = Path(__file__).resolve().parents[1] / "common_prompts" / "words.txt"


def _entries() -> list:
    """[(terms, entry text)] of words.txt, in its order: an entry is a line starting "- " and the lines indented under
    it; its terms are the names before its first ". " ("Instance, subject instance, object instance")."""
    out, head = [], []
    lines = read_text(WORDS).split("\n")
    for line in lines:
        if line.startswith("- "):
            out.append([line])
        elif line.startswith("  ") and out:
            out[-1].append(line)
        elif not out:
            head.append(line)
    return [([t.strip().lower() for t in e[0][2:].split(". ", 1)[0].split(",")], "\n".join(e)) for e in out]


def _uses(text: str, term: str) -> bool:
    """Whether text uses term, in any case, singular or plural ("entity", "entities"; "kind", "kinds")."""
    import re
    plural = term[:-1] + "ies" if term.endswith("y") else term + "s"
    return re.search(r"(?<![\w-])(?:%s|%s)(?![\w-])" % (re.escape(term), re.escape(plural)), text, re.I) is not None


def words_for(text: str) -> str:
    """The WORDS section for a prompt: the heading and introduction of words.txt, then every entry whose term the
    prompt uses, and every entry a chosen entry's own definition uses, in the file's order. So every term a prompt
    uses is defined in it, in the same words in every prompt."""
    entries = _entries()
    chosen, seen = set(), text.replace("$words", "")
    while True:
        more = {i for i, (terms, _) in enumerate(entries) if i not in chosen and any(_uses(seen, t) for t in terms)}
        if not more:
            break
        chosen |= more
        seen = "\n".join(entries[i][1] for i in chosen)
    head = read_text(WORDS).split("\n- ", 1)[0].rstrip()
    _used[_ref(WORDS)] = hashlib.sha256(read_text(WORDS).encode("utf-8")).hexdigest()
    return "\n".join([head, ""] + [entries[i][1] for i in sorted(chosen)])


def text(template: Template) -> str:
    """A prompt's text as it is, for pasting into another prompt (e.g. the
    reply format); recorded for the run's report like a filled prompt."""
    _record(template)
    return template.template


def _ref(path) -> str:
    from common.audit import ref_path
    return ref_path(path)


def _record(template: Template) -> None:
    if isinstance(template, Prompt):
        _used[_ref(template.path)] = hashlib.sha256(template.template.encode("utf-8")).hexdigest()


def prompts_used() -> list:
    """[{"file", "sha256"}] of every prompt filled in since reset_prompts()."""
    return [{"file": f, "sha256": h} for f, h in sorted(_used.items())]


def reset_prompts() -> None:
    _used.clear()
