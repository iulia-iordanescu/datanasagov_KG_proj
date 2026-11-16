"""
rescore_runs · Scores the six extractions the report quotes against the ground truth as it is now, with no model call.

Produces: six new runs of step 070 (three repeats with the induced schema, three with the ground truth schema), a copy
of each run's metrics.json, compared_triples.csv, per_record.md and _manifest.json in outputs/analysis/runs/<name>/,
and outputs/analysis/runs.json ({name: 070 run id}), which the other scripts of helpers/analysis/ read.

    py helpers/analysis/rescore_runs.py

It does not run step 060: it gives step 070 the run of 060 to score (--extraction_run), and step 070 reads the
four files of that run as it wrote them (so it still works after the extraction prompt changed, when
py helpers/reproduce_results.py cannot answer from 060's cache): each found by the sha256 its run's manifest records,
in the run's folder in outputs/intermediate_results/060_extract/previous_runs/, in another kept run's folder, or
live (common.step.gather_run), and gathered beside that run's manifest in
outputs/intermediate_results/070_evaluate/extractions/<060 run id>/ when they aren't all in its own folder. Every run's four files are looked for before any run of 070, so when no copy of a
file is left, nothing is scored and the message names the file: step 070 is never given another run's version of
it. Free by code: llm.forbid_model_calls first, which reaches the processes of step 070 too, and 070 runs with
--suggest false. Writes nothing in annotations/ (070 adds rows to the translation table only for a component class
without one, which stops the run).
"""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))                                                  # the repository folder, for common/
from common import llm                                                         # noqa: E402
from common.files import read_json, write_json                                 # noqa: E402
from common.step import outputs_of_run, run_manifests                          # noqa: E402
from common.stop import Stop                                                   # noqa: E402

WORK = ROOT / "outputs" / "analysis"
EXTRACTION = ROOT / "outputs" / "intermediate_results" / "060_extract"
EVALUATE = ROOT / "outputs" / "intermediate_results" / "070_evaluate"
#: name: 060's run whose extraction is scored (the runs behind docs/reported_numbers.json), and its recipe.
RUNS = {"1816": ("060_extract_2026-11-05_1816", "induced schema"), "1816-2": ("060_extract_2026-11-05_1816-2", "induced schema"),
        "1816-3": ("060_extract_2026-11-05_1816-3", "induced schema"), "1817": ("060_extract_2026-11-05_1817", "ground truth schema"),
        "1817-2": ("060_extract_2026-11-05_1817-2", "ground truth schema"),
        "1817-3": ("060_extract_2026-11-05_1817-3", "ground truth schema")}
#: The file names of step 070's four inputs from step 060 (070_evaluate/run.py, INPUTS; a test keeps them equal):
#: all four are the scored run's own, so no number (the report's table *Removed by 060* among them) comes from the live
#: folder's later run.
FILES = ("extracted_triples.csv", "extracted_triples_removed.csv", "extracted_triples_details.json", "schema_used.json")
KEPT = ("metrics.json", "compared_triples.csv", "per_record.md", "_manifest.json")
AGAIN = ("or take the run out of RUNS in helpers/analysis/rescore_runs.py, then run "
         "`py helpers/analysis/rescore_runs.py` again.")


def check_kept(extraction: str, output: Path = EXTRACTION, found: dict | None = None) -> dict:
    """{file name: the file} for the four files of 060's run `extraction`, each as that run wrote it
    (common.step.outputs_of_run, which step 070 uses too). SystemExit with its message, naming every file that can't
    be given, when the run isn't kept or a file of it has no copy left."""
    try:
        return outputs_of_run(output, extraction, FILES, found, again=AGAIN)
    except Stop as e:
        sys.exit(f"{e} Nothing was scored.")


def main() -> int:
    llm.forbid_model_calls("py helpers/analysis/rescore_runs.py is free: it scores saved extractions, and 070 runs with "
                           "--suggest false")
    made = {}
    found = run_manifests(EXTRACTION)
    for extraction, _ in RUNS.values():                                        # all, before any run of 070
        check_kept(extraction, EXTRACTION, found)
    for name, (extraction, _) in RUNS.items():
        args = ["--suggest", "false", "--confirm_paid_calls", "false", "--extraction_run", extraction]
        code = subprocess.run([sys.executable, str(ROOT / "070_evaluate" / "run.py"), *args], cwd=ROOT).returncode
        if code:
            sys.exit(f"step 070 didn't finish on {extraction} (exit code {code}): its messages above say why.")
        made[name] = read_json(EVALUATE / "_manifest.json")["run_id"]
        (WORK / "runs" / name).mkdir(parents=True, exist_ok=True)
        for f in KEPT:
            shutil.copyfile(EVALUATE / f, WORK / "runs" / name / f)
    write_json(WORK / "runs.json", made)
    print("070 runs:", " ".join(made.values()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
