"""
common/ -- code shared by the pipeline steps and the helpers.

    common/common_helpers/   the shared scripts (files.py, llm.py, step.py, ...)
    common/common_prompts/   the prompts shared by steps 050 and 060

The scripts live in common_helpers/, but are imported as if they sat
directly in common/: `from common.files import write_csv`. The line below
tells Python to look for common's modules in common_helpers/ too, so the
folder can stay tidy without every import in the project growing longer.
"""
from pathlib import Path

__path__.append(str(Path(__file__).resolve().parent / "common_helpers"))
