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

_used: dict = {}                     # {file, as the report names it: sha256 of its text}


class Prompt(Template):
    """A prompt's text, remembering the file it came from."""
    def __init__(self, text: str, path: Path):
        super().__init__(text)
        self.path = Path(path)


def load(path) -> Prompt:
    return Prompt(Path(path).read_text(encoding="utf-8"), path)


def fill(template: Template, **values) -> str:
    """The prompt with every $name filled in. A $name with no value, or a
    stray "$", stops with an error instead of reaching the model half-filled.
    The prompt's file and fingerprint are recorded for the run's report."""
    _record(template)
    return template.substitute(**values)


def text(template: Template) -> str:
    """A prompt's text as it is, for pasting into another prompt (e.g. the
    reply format); recorded for the run's report like a filled prompt."""
    _record(template)
    return template.template


def _record(template: Template) -> None:
    if isinstance(template, Prompt):
        from common.audit import ref_path
        _used[ref_path(template.path)] = hashlib.sha256(template.template.encode("utf-8")).hexdigest()


def prompts_used() -> list:
    """[{"file", "sha256"}] of every prompt filled in since reset_prompts()."""
    return [{"file": f, "sha256": h} for f, h in sorted(_used.items())]


def reset_prompts() -> None:
    _used.clear()
