#!/usr/bin/env python3
"""
sample_messy_notes.py

Find the notes that actually contain HTML and show the raw text next to
the rendered text, so the decoding can be checked by eye.

This is a test tool, not a sampling tool. Where
sample_some_notes_for_ground_truth.py draws a random sample, this one
deliberately hunts for the worst cases: the notes with the most markup,
the most entities, and the most links.

Usage
-----
    python sample_messy_notes.py data
    python sample_messy_notes.py data -n 20
    python sample_messy_notes.py data --out messy_check.txt

Reads the same batch files. Writes a side-by-side comparison file and
prints a summary of how much markup exists catalog-wide.
"""

from __future__ import annotations

import argparse
import collections
import importlib.util
import json
import re
import sys
from pathlib import Path

ENTITY = re.compile(r"&([a-zA-Z][a-zA-Z0-9]*|#\d+|#[xX][0-9a-fA-F]+);")
TAG = re.compile(r"</?[a-zA-Z][^>]*>")
URL = re.compile(r"https?://[^\s\"'<>\]]+")

# The renderer under test lives in the sampler; import it rather than
# copying it, so this checks the real code and not a stale duplicate.
SAMPLER = "sample_some_notes_for_ground_truth.py"


def load_renderer(folder: Path):
    """Import readable() from the sampler sitting next to this script."""
    path = Path(__file__).with_name(SAMPLER)
    if not path.exists():
        raise SystemExit(f"Cannot find {SAMPLER} next to this script.")
    spec = importlib.util.spec_from_file_location("sampler", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def messiness(notes: str) -> int:
    """Score a note by how much markup it carries.

    Tags are weighted above entities because they are what the renderer
    has to interpret; a note full of escaped quotes is not a hard case.
    """
    return 3 * len(TAG.findall(notes)) + len(ENTITY.findall(notes))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Find the most marked-up notes and show raw vs rendered."
    )
    parser.add_argument("input", type=Path, nargs="?", default=Path("data"),
                        help="folder holding the batch files (default: data)")
    parser.add_argument("-n", "--count", type=int, default=15,
                        help="how many notes to show (default: 15)")
    parser.add_argument("--out", type=Path, default=Path("messy_check.txt"),
                        help="output file (default: messy_check.txt)")
    parser.add_argument("--pattern", default="batch_*.json")
    args = parser.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

    sampler = load_renderer(args.input)
    files = sorted(args.input.glob(args.pattern))
    if not files:
        raise SystemExit(f"No files matching {args.pattern!r} in {args.input}")

    worst: list[tuple[int, dict]] = []
    total = 0
    with_tags = 0
    with_entities = 0
    tag_counts = collections.Counter()
    url_total = 0

    for path in files:
        for record in json.loads(path.read_text(encoding="utf-8")):
            notes = record.get("notes") or ""
            total += 1
            has_tag = bool(TAG.search(notes))
            has_ent = bool(ENTITY.search(notes))
            if has_tag:
                with_tags += 1
            if has_ent:
                with_entities += 1
            if not (has_tag or has_ent):
                continue

            decoded = sampler.unescape_fully(notes)
            for name in re.findall(r"</?([a-zA-Z][a-zA-Z0-9]*)", decoded):
                tag_counts[name.lower()] += 1
            url_total += len(set(URL.findall(decoded)))

            worst.append((messiness(decoded), {
                "maintainer": record.get("maintainer") or "undefined",
                "id": record.get("id") or "",
                "name": record.get("name") or "",
                "notes": notes,
            }))

    worst.sort(key=lambda pair: -pair[0])
    picked = [row for _, row in worst[:args.count]]

    # ---- summary -------------------------------------------------
    print(f"Scanned {len(files)} files, {total:,} records.\n")
    print(f"  notes with HTML tags     : {with_tags:,} "
          f"({with_tags / total:.1%})")
    print(f"  notes with escaped chars : {with_entities:,} "
          f"({with_entities / total:.1%})")
    print(f"  notes with either        : {len(worst):,} "
          f"({len(worst) / total:.1%})")
    print(f"  URLs inside markup       : {url_total:,}\n")
    print("Tags present, most common first:")
    for name, count in tag_counts.most_common(15):
        print(f"  {count:>6}  <{name}>")

    # ---- URL preservation check ----------------------------------
    lost = 0
    checked = 0
    for row in picked:
        before = set(URL.findall(sampler.unescape_fully(row["notes"])))
        after = set(URL.findall(sampler.readable(row["notes"])))
        checked += len(before)
        lost += len(before - after)
    print(f"\nURL check on the {len(picked)} shown: "
          f"{checked} found, {lost} lost.")

    # ---- side-by-side file ---------------------------------------
    bar = "=" * 78
    out = [bar, "RAW vs RENDERED -- the most marked-up notes in the catalog",
           f"showing {len(picked)} of {len(worst):,} notes containing markup",
           bar, ""]

    for i, row in enumerate(picked, start=1):
        out += [bar, f"[{i}] {row['maintainer']}  |  {row['name'][:60]}",
                f"     {row['id']}", bar, "",
                "--- RAW (as stored, and as the CSV keeps it) " + "-" * 32, "",
                row["notes"].strip(), "",
                "--- RENDERED (as the .txt file shows it) " + "-" * 36, "",
                sampler.readable(row["notes"]).strip(), "", ""]

    args.out.write_text("\n".join(out), encoding="utf-8")
    print(f"\nWrote {args.out} -- open it and compare the two halves.")


if __name__ == "__main__":
    main()
