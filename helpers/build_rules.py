"""
build_rules · Builds the model's copy of the rules from the annotation guidelines.

The rules have one home, annotations/guidelines.md. This writes the model's copy,
common/common_prompts/extraction_rules.txt, from it and from annotations/rules_model_differences.txt, the list of
every way in which the model's copy differs, each with its reason. Run it after every change to either file; a test
(tests/test_model_rules.py) fails while the model's copy differs from what this writes.
Free: no model calls. Writes only the file named above.

    py helpers/build_rules.py

Reads:   annotations/guidelines.md, annotations/rules_model_differences.txt, annotations/ground_truth_schema.txt
Writes:  common/common_prompts/extraction_rules.txt
Details: common/common_helpers/model_rules.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))                                                  # the repository folder, for common/

from common import console                                                     # noqa: E402
from common.model_rules import MODEL_COPY, write_model_copy                     # noqa: E402
from common.step import repo_path                                              # noqa: E402


def main() -> int:
    console.setup()
    try:
        changed = write_model_copy()
    except ValueError as e:
        print(f"Nothing was written: {e}")
        return 1
    print(f"{repo_path(MODEL_COPY)}: {'written' if changed else 'already up to date'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
