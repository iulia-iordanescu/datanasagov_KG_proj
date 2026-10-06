"""
tests/run_all.py -- runs every test of the pipeline.

    py tests/run_all.py             every test file
    py tests/run_all.py pairing     only the test files whose name contains "pairing"

Each tests/test_*.py file runs in its own Python process: the steps' helper
folders hold files with the same name (moves.py, records.py), so two steps'
helpers can't be imported into one process. Nothing here calls a model or
data.nasa.gov, and nothing is written into the repository: the end-to-end
test works in a temporary copy. Instructions: tests/README.md.
"""
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
TIME_LIMIT = 300            # seconds per test file; the slowest takes about 20


def repository_state() -> str:
    """What Git sees in the repository, outputs/ included: the tests must leave it as it was."""
    return subprocess.run(["git", "status", "--porcelain", "--ignored", "--untracked-files=all", "--", ".",
                           ":(exclude)tests/__pycache__", ":(exclude)*/__pycache__/*"],
                          cwd=HERE.parent, capture_output=True, text=True, check=True).stdout


def main(argv: list) -> int:
    files = sorted(HERE.glob("test_*.py"))
    if argv:
        files = [f for f in files if any(a in f.stem for a in argv)]
    if not files:
        print("no test file matches")
        return 1
    before = repository_state()
    failed = []
    for f in files:
        clock = time.monotonic()
        try:
            run = subprocess.run([sys.executable, "-m", "unittest", "-q", f.stem], cwd=HERE, timeout=TIME_LIMIT,
                                 capture_output=True, text=True, encoding="utf-8", errors="replace")
            ok, said = run.returncode == 0, run.stdout + run.stderr
        except subprocess.TimeoutExpired:
            ok, said = False, f"still running after {TIME_LIMIT} s: something loops forever or waits for input\n"
        took = time.monotonic() - clock
        print(f"{'ok  ' if ok else 'FAIL'}  {f.name:<34} {took:6.1f} s")
        if not ok:
            failed.append(f.name)
            print(said)
    print(f"\n{len(files) - len(failed)} of {len(files)} test files passed"
          + (f"; failed: {', '.join(failed)}" if failed else ""))
    if repository_state() != before:
        print("FAIL  the tests changed files in the repository (git status differs from before the run)")
        return 1
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
