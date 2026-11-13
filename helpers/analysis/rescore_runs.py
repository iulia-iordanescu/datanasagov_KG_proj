"""
rescore_runs · Scores the six extractions the report quotes against the ground truth as it is now, with no model call.

Produces: six new runs of step 070 (three repeats with the induced schema, three with the ground truth schema), a copy
of each run's metrics.json, compared_triples.csv, per_record.md and _manifest.json in outputs/analysis/runs/<name>/,
and outputs/analysis/runs.json ({name: 070 run id}), which the other scripts of helpers/analysis/ read.

    py helpers/analysis/rescore_runs.py

It does not run step 060: it gives step 070 the extraction files that 060 kept in
outputs/intermediate_results/060_extract/previous_runs/ (so it still works after the extraction prompt changed, when
py helpers/reproduce_results.py cannot answer from 060's cache), after checking each file's sha256 against its run's
manifest. Free by code: llm.forbid_model_calls first, which reaches the processes of step 070 too, and 070 runs with
--suggest false. Writes nothing in annotations/ (070 adds rows to the translation table only for a component class
without one, which stops the run).
"""
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))                                                  # the repository folder, for common/
from common import llm                                                         # noqa: E402

WORK = ROOT / "outputs" / "analysis"
EXTRACTIONS = ROOT / "outputs" / "intermediate_results" / "060_extract" / "previous_runs"
EVALUATE = ROOT / "outputs" / "intermediate_results" / "070_evaluate"
#: name: 060's run whose extraction is scored (the runs behind docs/reported_numbers.json), and its recipe.
RUNS = {"1816": ("060_extract_2026-11-05_1816", "induced schema"), "1816-2": ("060_extract_2026-11-05_1816-2", "induced schema"),
        "1816-3": ("060_extract_2026-11-05_1816-3", "induced schema"), "1817": ("060_extract_2026-11-05_1817", "ground truth schema"),
        "1817-2": ("060_extract_2026-11-05_1817-2", "ground truth schema"),
        "1817-3": ("060_extract_2026-11-05_1817-3", "ground truth schema")}
GIVEN = ("extracted_triples.csv", "extracted_triples_details.json", "schema_used.json")
KEPT = ("metrics.json", "compared_triples.csv", "per_record.md", "_manifest.json")


def main() -> int:
    llm.forbid_model_calls("py helpers/analysis/rescore_runs.py is free: it scores saved extractions, and 070 runs with "
                           "--suggest false")
    made = {}
    for name, (extraction, _) in RUNS.items():
        folder = EXTRACTIONS / extraction
        recorded = {o["file"]: o["sha256"] for o in json.loads((folder / "_manifest.json").read_text(encoding="utf-8"))["outputs"]}
        for f in GIVEN:
            if hashlib.sha256((folder / f).read_bytes()).hexdigest() != recorded[f]:
                sys.exit(f"{folder / f} is not the file its run's manifest records: nothing was scored.")
        args = ["--suggest", "false", "--confirm_paid_calls", "false"]
        for option, f in zip(("--extracted_triples", "--extracted_triples_details", "--schema_used"), GIVEN):
            args += [option, str(folder / f)]
        code = subprocess.run([sys.executable, str(ROOT / "070_evaluate" / "run.py"), *args], cwd=ROOT).returncode
        if code:
            sys.exit(f"step 070 didn't finish on {extraction} (exit code {code}): its messages above say why.")
        made[name] = json.loads((EVALUATE / "_manifest.json").read_text(encoding="utf-8"))["run_id"]
        (WORK / "runs" / name).mkdir(parents=True, exist_ok=True)
        for f in KEPT:
            shutil.copyfile(EVALUATE / f, WORK / "runs" / name / f)
    (WORK / "runs.json").write_text(json.dumps(made, indent=1), encoding="utf-8")
    print("070 runs:", " ".join(made.values()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
