"""
helpers/models.py -- the AI models Ask Sage lists for your account.

    py helpers/models.py

Free: listing is not a model call. Being listed doesn't guarantee access:
Ask Sage may list a model and still refuse it. To use one, give its name to
a step's `model` setting, e.g.

    py 050_annotate/run.py --model <name> --records_per_batch 1

The step's first call is a one-line test: if the model refuses you, the step
stops there, having spent that one tiny call, and says why. Needs the NASA
network and your key in .env (docs/running_on_nasa_laptop.md). Not a
pipeline step: it writes nothing.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # the repository folder, for common/

from common import llm


def main() -> None:
    names = llm.list_models()
    print(f"Ask Sage lists {len(names)} model(s) for your account (listed doesn't mean allowed):")
    for name in names:
        print(f"  {name}{'   <- the default' if name == llm.MODEL else ''}")
    if llm.MODEL not in names:
        print(f"\nThe default, {llm.MODEL} (common/common_helpers/llm.py), isn't in the list.")


if __name__ == "__main__":
    main()
