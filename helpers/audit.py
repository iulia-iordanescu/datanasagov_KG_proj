"""
audit · Trace an item back to its source

Finds an item (a catalog record, a cleaned record, a schema entry) in the
pipeline's outputs and follows its origin upstream, step by step, to the API
request that first returned it. Each hop names the run that made it and that
run's report and log.

    py helpers/audit.py <key>                        e.g. a CKAN record id
    py helpers/audit.py <key> --step 010_harvest     look in one step only
    py helpers/audit.py --step 010_harvest --file batch_01000.json --position 17
    py helpers/audit.py --induction "aboard|on board"  what step 040 did with the triple
                                                     instances that match: label, merge,
                                                     in the schema or deferred

Details: helpers/audit.md
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # the repository folder, for common/

from common.induction_trace import trace_induction
from common.trace import find, trace


def main() -> int:
    ap = argparse.ArgumentParser(prog="py helpers/audit.py", description=__doc__.split("\n\n")[1])
    ap.add_argument("key", nargs="?", help="the item's key, e.g. a CKAN record id")
    ap.add_argument("--step", help="look only in this step, e.g. 010_harvest")
    ap.add_argument("--file", help="output file name inside the step's folder")
    ap.add_argument("--position", type=int, help="position in that file, counting from 0")
    ap.add_argument("--induction", metavar="REGEX",
                    help="trace step 040's triple instances whose predicate instance, source text, predicate "
                         "label or final predicate matches this regular expression (case ignored)")
    ap.add_argument("--limit", type=int, default=30, help="with --induction: the most triple instances "
                                                          "(and summary rows) shown; default 30")
    ap.add_argument("--folder", help="with --induction: the folder holding the_schema.json and "
                                     "induction_evidence.json; default step 040's output folder")
    args = ap.parse_args()
    if args.induction is not None:
        try:
            re.compile(args.induction)
        except re.error as e:
            ap.error(f"--induction {args.induction!r} isn't a valid regular expression ({e}); "
                     f'separate alternatives with |, e.g. "aboard|on board"')
        try:
            trace_induction(args.induction, limit=max(args.limit, 1), folder=args.folder)
        except (FileNotFoundError, ValueError) as e:
            print(e)
            return 1
        return 0
    if args.key is None and args.file is None:
        ap.error("give a key, --file (with --step and --position), or --induction")

    hits = find(key=args.key, step=args.step, file=args.file, position=args.position)
    if not hits:
        print("Not found in any step's output (outputs/intermediate_results/), so there is nothing to trace. Check "
              "the key (e.g. a record id); if you gave --step, try without it.")
        return 1
    if len(hits) > 1:
        print(f"{len(hits)} items match; showing each.\n")
    for step, path, position, item in hits[:20]:
        trace(step, path, position, item)
        print()
    if len(hits) > 20:
        print(f"... {len(hits) - 20} more not shown")
    return 0


if __name__ == "__main__":
    sys.exit(main())
