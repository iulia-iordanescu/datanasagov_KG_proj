"""
audit · Trace an item back to its source

Finds an item (a catalog record, a cleaned record, later a triple) in the
pipeline's outputs and follows its origin upstream, step by step, to the API
request that first returned it. Each hop names the run that made it and that
run's report and log.

    py audit.py <key>                        e.g. a CKAN record id
    py audit.py <key> --step 010_harvest     look in one step only
    py audit.py --step 010_harvest --file batch_01000.json --position 17

Details: instructions/000_audit.md
"""
import argparse
import sys

from common.trace import find, trace


def main() -> int:
    ap = argparse.ArgumentParser(prog="py audit.py", description=__doc__.split("\n\n")[1])
    ap.add_argument("key", nargs="?", help="the item's key, e.g. a CKAN record id")
    ap.add_argument("--step", help="look only in this step, e.g. 010_harvest")
    ap.add_argument("--file", help="output file name inside the step's folder")
    ap.add_argument("--position", type=int, help="position in that file, counting from 0")
    args = ap.parse_args()
    if args.key is None and args.file is None:
        ap.error("give a key, or --file (with --step and --position)")

    hits = find(key=args.key, step=args.step, file=args.file, position=args.position)
    if not hits:
        print("Not found in any step's output.")
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
