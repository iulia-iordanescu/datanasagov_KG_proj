"""
tests/stand_in_run.py -- runs one step of a temporary copy of the
repository with the stand-ins (tests/stand_ins.py) instead of the model and
data.nasa.gov. Used by test_pipeline.py:

    py tests/stand_in_run.py <repository copy> <step folder> [the step's options]

The environment variable KG_TEST_CATALOG gives the stand-in catalog's URL
(step 010). Prints how many prompts the stand-in model answered.
"""
import importlib.util
import os
import sys
from pathlib import Path

repo, step, argv = Path(sys.argv[1]).resolve(), sys.argv[2], sys.argv[3:]
sys.path[:0] = [str(repo), str(Path(__file__).resolve().parent)]

import stand_ins                                  # noqa: E402
from common import llm                            # noqa: E402

assert Path(llm.__file__).resolve().is_relative_to(repo), "the copy's code must be the one running"
llm.call_llm = stand_ins.stand_in_model

spec = importlib.util.spec_from_file_location("panel", repo / step / "run.py")
panel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(panel)
if "ckan_client" in sys.modules:
    sys.modules["ckan_client"].URL = os.environ["KG_TEST_CATALOG"]

from common.step import run_step                  # noqa: E402

try:
    run_step(step, panel.INPUTS, panel.SETTINGS, panel.main, argv=argv,
             may_be_empty=getattr(panel, "MAY_BE_EMPTY", ()))
finally:
    print(f"[stand-in model answered {len(stand_ins.CALLS)} prompt(s)]")
