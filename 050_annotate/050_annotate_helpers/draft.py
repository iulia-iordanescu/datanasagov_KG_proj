"""
draft.py -- stage 2: the model drafts each chosen record's classed triples.

One call per text piece (a long record is split, as in 040: common/common_helpers/chunking.py).
The prompt (050_annotate/050_annotate_prompts/draft.txt) puts COMPLETENESS FIRST: every fact the
record states, whether or not the ground truth schema can express it; then
NAMING: the schema's entity classes and predicates when one fits, a new
one otherwise. Its rules and reply format are shared with 060
(common/common_prompts/), so the ground truth and what 060 extracts are asked for
the same way.

The calls themselves are made by common/common_helpers/extraction.ask_model (shared with
060): every answer is kept in cache/draft.json (common/common_helpers/cache.py) the moment
it arrives, so a rerun, e.g. after a failed call or Ctrl+C, pays only for
what it doesn't have. A record whose call fails, for any piece, is left out
of the drafted batch, never half drafted; the next run drafts it again.
"""
from __future__ import annotations

from pathlib import Path

from common import extraction
from common.prompt_files import load

PROMPTS_DIR = Path(__file__).resolve().parents[1] / "050_annotate_prompts"   # 050_annotate/050_annotate_prompts/
PROMPT = load(PROMPTS_DIR / "draft.txt")


def ask_model(chosen, calls, settings: dict) -> extraction.Replies:
    def prompt_for(item, piece):
        return extraction.prompt(PROMPT, chosen.schema_text, chosen.records[item["id"]], piece,
                                 **extraction.task_parts(extraction.SCOPE_ALL))
    return extraction.ask_model(chosen.items, prompt_for, calls, settings["workers"], "draft",
                                f"050 will draft {len(chosen.items)} record(s) into drafted batch {chosen.batch}",
                                "drafting")
