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
"""
from __future__ import annotations

from pathlib import Path
from string import Template


def load(path) -> Template:
    return Template(Path(path).read_text(encoding="utf-8"))


def fill(template: Template, **values) -> str:
    """The prompt with every $name filled in. A $name with no value, or a
    stray "$", stops with an error instead of reaching the model half-filled."""
    return template.substitute(**values)
