"""
draft.py -- stage 2: the model drafts each chosen record's triple instances.

One call per text piece (a long record is split, as in 040: common/common_helpers/chunking.py).
The prompt (prompts/draft.txt) puts COMPLETENESS FIRST: every fact the
record states, whether or not the hand-built schema can express it; then
NAMING: the schema's entity classes and predicates when one fits, a new
name otherwise. Its rules and reply format are shared with 060
(common/common_prompts/), so the ground truth and what 060 extracts are asked for
the same way.

The calls themselves are made by common/common_helpers/extraction.ask_model (shared with
060): every answer is kept in cache/draft.json (common/common_helpers/cache.py) the moment
it arrives, so a rerun, e.g. after a failed call or Ctrl+C, pays only for
what it doesn't have. A record whose call fails, for any piece, is left out
of the batch, never half drafted; the next run drafts it again.
"""
from __future__ import annotations

from pathlib import Path

from common import extraction
from common.prompt_files import fill, load

PROMPTS_DIR = Path(__file__).resolve().parents[1] / "050_annotate_prompts"   # 050_annotate/050_annotate_prompts/
PROMPT = load(PROMPTS_DIR / "draft.txt")


def prompt_for(chosen, item: dict, piece: str) -> str:
    return fill(PROMPT, schema=chosen.schema_text, rules=extraction.rules_for(chosen.records[item["id"]]),
                reply=extraction.REPLY.template.strip(), text=extraction.wrap(piece))


def ask_model(chosen, calls, settings: dict) -> extraction.Replies:
    return extraction.ask_model(chosen.items, lambda item, piece: prompt_for(chosen, item, piece), calls,
                                settings["workers"], "draft",
                                f"050 will draft {len(chosen.items)} record(s) into batch {chosen.batch}",
                                "drafting")
