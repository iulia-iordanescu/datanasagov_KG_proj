#!/usr/bin/env python3
"""
ground_truth_sampler.py -- picks the 1000 records we'll build ground truth
from. Run it once:

    py ground_truth_sampler.py inputs.json

What it does: reads inputs.json, groups records by maintainer (maintainers
too small to get 2 places are combined into one group), gives each group a
number of places proportional to its size totalling 1000, draws that many
records at random from each group, shuffles them, and writes their ids to
ground_truth_pool.csv.

It only picks ids. No model, no network. If either output file already
exists it refuses to run, since changing the pool halfway through
annotating would mix two different samples.

How the 1000 are picked
-----------------------
1. Who can be picked. Every record inputs_io.py reads from inputs.json. The
   loader skips records with empty text and drops exact duplicates (same
   id, same text); build_inputs.py has already removed both, so in
   practice every record is eligible and results describe the whole
   catalog.

2. Records are grouped by maintainer (the "group" field, which
   build_inputs.py fills with the maintainer), and each group is sampled
   separately. This is stratified sampling. It works best when records
   inside a group resemble each other [1], and description style depends
   heavily on who wrote it. Sampling proportionally by group is at least
   as precise as picking 1000 records at random from the whole catalog,
   apart from rare exceptions involving very small groups [1, sec. 5.6].

3. Each group gets places in proportion to its size: a maintainer holding
   10% of the records gets 10% of the places. The textbook rule gives extra
   places to groups whose results vary more [2; 1, sec. 5.5]. We ASSUME
   extraction quality varies about as much for one maintainer as another;
   under that assumption the rule becomes plain proportional.

   A consequence: every record in the catalog has nearly the same chance of
   being picked, differing only by the rounding in step 5. So a plain
   average over the pool describes the whole catalog, and no weighting is
   needed [3].

4. Small maintainers are combined. Measuring how far a result could be off
   (its margin of error) needs at least 2 records from each group, because
   it compares records within a group, and one record has nothing to be
   compared with [1; 4]. A maintainer whose share is under 2 places is
   therefore combined with all others like it into one group, "(small
   maintainers)", which gets its own proportional share. Combining small
   groups this way is the standard fix, called collapsing strata [4]. The
   script warns if even the combined group earns fewer than 2 places.

5. Rounding. Shares are rarely whole numbers. Each group first gets the
   whole part of its share; the places left over go one each to the groups
   whose dropped fractions were largest. This is the largest-remainder
   (Hamilton) method [5]. It is used because it always meets three
   requirements at once: whole numbers, a total of exactly 1000, and every
   group within one place of its exact share. Simple rounding can miss the
   total, and dropping fractions always falls short.

6. Within each group, records are picked at random, each equally likely.

7. The 1000 rows are shuffled. A random subset of an equal-chance sample is
   itself an equal-chance sample [1], so the first k rows are a fair sample
   of the catalog for any k: annotate from the top and stop anywhere.

8. --seed (default 1000, an arbitrary fixed value) fixes every random step,
   so the same inputs and seed rebuild the identical pool. This is ordinary
   reproducibility practice and has no effect on the statistics.

References
----------
[1] Cochran, W. G. (1977). Sampling Techniques, 3rd ed. Wiley. Ch. 5,
    stratified random sampling.
[2] Neyman, J. (1934). On the two different aspects of the representative
    method. Journal of the Royal Statistical Society, 97(4), 558-625.
[3] Kish, L. (1965). Survey Sampling. Wiley. Proportionate stratified
    samples give every element an equal chance (self-weighting).
[4] Lohr, S. L. (2019). Sampling: Design and Analysis, 2nd ed. CRC Press.
    Variance estimation needs two or more units per stratum; collapsed
    strata.
[5] Balinski, M. L. & Young, H. P. (2001). Fair Representation, 2nd ed.
    Brookings Institution Press. The Hamilton (largest-remainder) method.

Output
------
In ground_truth_sample_outputs/ (change with --out-dir), never
overwritten. --size changes the 1000.

    ground_truth_pool.csv    id, maintainer, group, group_size,
                             drawn_from_group
    ground_truth_pool.json   how the draw was made: seed, totals, places
                             and size of each group, and the list of
                             maintainers combined into the small group

"group" is the maintainer, or "(small maintainers)" for a combined one.

Needs inputs_io.py in the same folder.
"""

from __future__ import annotations

import argparse
import collections
import csv
import json
import random
import sys
from datetime import date
from pathlib import Path

try:
    # The loader every step shares, so these ids are the ids the extractor
    # and the scorer will use.
    from inputs_io import load_inputs
except ImportError:                                     # pragma: no cover
    raise SystemExit("This script needs inputs_io.py in the same folder.")

DEFAULT_OUT_DIR = Path("ground_truth_sample_outputs")
POOL_CSV = "ground_truth_pool.csv"
POOL_JSON = "ground_truth_pool.json"
POOL_COLUMNS = ["id", "maintainer", "group", "group_size", "drawn_from_group"]

#: A group needs at least this many places for its variability to be
#: estimable; maintainers whose share falls below it are collapsed.
MIN_PLACES = 2
SMALL = "(small maintainers)"


def form_groups(sizes: dict[str, int], total: int) -> dict[str, str]:
    """Map each maintainer to its sampling group.

    A maintainer whose proportional share of `total` places is under
    MIN_PLACES joins the SMALL group; every other maintainer is its own
    group.
    """
    n = sum(sizes.values())
    return {m: (m if total * s / n >= MIN_PLACES else SMALL)
            for m, s in sizes.items()}


def allocate(group_sizes: dict[str, int], total: int) -> dict[str, int]:
    """Proportional places per group, by the largest-remainder method.

    Each group gets the whole part of its exact share; the places left over
    go one each to the groups with the largest fractional parts. The result
    sums to `total` exactly and every group is within one place of its
    exact share. Ties are broken by group name so the result never depends
    on input order.
    """
    n = sum(group_sizes.values())
    exact = {g: total * s / n for g, s in group_sizes.items()}
    places = {g: int(e) for g, e in exact.items()}
    leftover = total - sum(places.values())
    by_remainder = sorted(exact, key=lambda g: (-(exact[g] - places[g]), g))
    for g in by_remainder[:leftover]:
        places[g] += 1
    return places


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Pick the fixed pool of records ground truth will be "
                    "built from. Runs once.")
    ap.add_argument("inputs", nargs="+",
                    help="inputs.json (file(s) or globs)")
    ap.add_argument("-n", "--size", type=int, default=1000,
                    help="how many records to pick (default: 1000)")
    ap.add_argument("--seed", type=int, default=1000,
                    help="random seed; same inputs and seed give the same "
                         "pool (default: 1000)")
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR,
                    help=f"where to write (default: {DEFAULT_OUT_DIR})")
    args = ap.parse_args()

    csv_path = args.out_dir / POOL_CSV
    json_path = args.out_dir / POOL_JSON
    for path in (csv_path, json_path):
        if path.exists():
            sys.exit(f"{path} already exists. The pool is picked once and "
                     f"then kept, so nothing was written. To start over, "
                     f"move that file aside deliberately.")

    records = load_inputs(args.inputs)
    if not records:
        sys.exit(f"No texts found in {args.inputs}.")
    if not 1 <= args.size < len(records):
        sys.exit(f"--size must be at least 1 and below the {len(records):,} "
                 f"records available.")

    maint_size = collections.Counter(m for _, _, m in records)
    group_of = form_groups(maint_size, args.size)
    members: dict[str, list] = collections.defaultdict(list)
    for rec in records:
        members[group_of[rec[2]]].append(rec)
    group_size = {g: len(v) for g, v in members.items()}
    places = allocate(group_size, args.size)
    if SMALL in places and places[SMALL] < MIN_PLACES:
        print(f"  WARNING: the combined small-maintainer group earns only "
              f"{places[SMALL]} place(s), under the {MIN_PLACES} needed to "
              f"measure its margin of error", file=sys.stderr)

    rng = random.Random(args.seed)
    picked = []
    for g in sorted(places):              # fixed order: reproducible draw
        picked.extend(rng.sample(sorted(members[g]), places[g]))
    rng.shuffle(picked)

    rows = [{"id": i, "maintainer": m, "group": group_of[m],
             "group_size": group_size[group_of[m]],
             "drawn_from_group": places[group_of[m]]}
            for i, _, m in picked]

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=POOL_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    collapsed = sorted(m for m, g in group_of.items() if g == SMALL)
    json_path.write_text(json.dumps({
        "tool": "ground_truth_sampler.py",
        "picked_on": date.today().isoformat(),
        "inputs": args.inputs, "seed": args.seed,
        "records_in_population": len(records), "picked": len(rows),
        "design": "stratified by maintainer, proportional allocation, "
                  f"maintainers with a share under {MIN_PLACES} places "
                  "collapsed into one group, largest-remainder rounding, "
                  "rows shuffled",
        "groups": len(places),
        "places_per_group": dict(sorted(places.items(),
                                        key=lambda kv: -kv[1])),
        "group_sizes": dict(sorted(group_size.items(),
                                   key=lambda kv: -kv[1])),
        "maintainers_collapsed": len(collapsed),
        "collapsed_maintainers": collapsed,
    }, indent=1, ensure_ascii=False), encoding="utf-8")

    print(f"\nPicked {len(rows):,} of {len(records):,} records, seed "
          f"{args.seed}", file=sys.stderr)
    print(f"  {len(places):,} groups: {len(places) - (SMALL in places):,} "
          f"maintainers on their own, plus {len(collapsed):,} small "
          f"maintainers combined", file=sys.stderr)
    for g, k in sorted(places.items(), key=lambda kv: -kv[1])[:6]:
        print(f"  {g}: {k} of {group_size[g]:,}", file=sys.stderr)
    print(f"  pool  {csv_path}", file=sys.stderr)
    print(f"  how   {json_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
