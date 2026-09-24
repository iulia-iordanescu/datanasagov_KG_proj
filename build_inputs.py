#!/usr/bin/env python3
"""
build_inputs.py -- turn the harvested CKAN batches into the
collection_of_inputs (inputs.json) that the rest of the pipeline reads.

WHO READS ITS OUTPUT
--------------------
    best_induce_schema.py    samples texts from it to induce the schema
    extract_triples_for_kg.py  extracts triples following a schema from every text 
    ground_truth_sampler.py  draws texts from it to be annotated by hand

All three load it with inputs_io.load_inputs(), so they see the same ids. Changing the output shape ("id", "group", "text") or the section
format ("name: value" blocks separated by blank lines) affects all of
them: if you add a field with --fields, pass the same name to
extract_triples_for_kg.py --sections.

    py build_inputs.py data                      -> inputs.json
    py build_inputs.py data --fields notes title author
    py build_inputs.py data --text-order notes title
    py build_inputs.py data --out lite.json --max-records 200

WHAT IT DOES
------------
Walks every batch_*.json in the given directory and emits one object per
record:

    {"id":    <the CKAN id>,
     "group": <the maintainer>,
     "text":  "title: <cleaned title>\\n\\nnotes: <cleaned notes>"}

The chosen fields are CLEANED first, by note_cleaning.py, which strips the
HTML markup that a portion of this catalog carries and verifies that no
word, number or URL was lost in doing so. Sending raw markup to the
extractor would produce triples about <p> tags rather than about datasets.

Each field is written under its own label so the extraction model can tell
a title from a description.

TWO SEPARATE ORDERS. --fields says WHICH fields to clean; --text-order says
in what order they appear in the text. They are separate because the two
answers need not agree, and because the first entry of --fields can carry
other meaning elsewhere in the pipeline. Defaults: clean `notes title`,
write `title notes` - the title reads as context for the description that
follows. A cleaned field not named in --text-order is appended after the
named ones, so adding a field can never silently drop it from the text.

MAINTAINER SPELLINGS ARE JOINED
-------------------------------
The same maintainer is written several ways in this catalog: "Kristan
Morgan" and "KRISTAN MORGAN", "ANDREY SAVTCHENKO" and "ANDREY SAVTCHENKO,
PH. D", "Parnchai Sawaengphokhai" and "Sawaengphokhai Parnchai". Names that
match once case, punctuation, word order, and titles (Dr., Ph.D) are
ignored are treated as one maintainer, written in "John Doe" form. Names
differing by a middle name or initial, such as "Lola Olsen" and "Lola M.
Olsen", stay apart; merging those needs a rule you would have to choose.

This is not cosmetic. The group field is what ground_truth_sampler.py
stratifies on, so a maintainer split across two spellings counts as two
strata: it takes two of the pool's guaranteed places instead of one, and
each of its records claims to represent only half as many catalog records
as it really does. Joining before the pool is drawn avoids both.

Every join is listed in the report and printed. --keep-group-spellings
turns the joining off and leaves the labels exactly as harvested.

RECORDS WITHOUT AN ID ARE DROPPED
---------------------------------
A record with a missing or blank id is skipped, counted, and its source
file and position listed in the report. It is not given a made-up id.
Decision and reasons:
  * The id is how every later step tells texts apart: the extractor saves
    triples under it, and scoring matches predicted triples to ground-truth
    triples by it.
  * An id made up from the record's position (e.g. "batch_03000.json#12")
    points at a different record after a re-harvest shifts the files, so
    ground truth written under it would be scored against the wrong text,
    silently.
  * An id made up from the record's content (its CKAN "name", or a hash of
    its text) is stable, but more machinery than is justified while no
    record is known to lack an id. Revisit if the report shows drops.

WHAT IT RECORDS
---------------
Alongside the output it writes build_inputs_report.json: how many records
were read, skipped and written; how each field was cleaned, counted by
method (parsed / conservative / source); and the ids of every field that
needed a fallback method, so an odd triple downstream can be traced back to
a value that was hard to clean. Nothing is decided silently.

REQUIRES note_cleaning.py beside this file (or on the Python path).
Standard library otherwise.
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path

try:
    from note_cleaning import DEFAULT_FIELDS, clean_record
except ImportError:                                     # pragma: no cover
    raise SystemExit(
        "This script needs note_cleaning.py, which should sit in the same\n"
        "folder. Copy it there, or add its folder to PYTHONPATH.")

#: Record key holding the community label. induce_schema samples by it;
#: extract_triples only carries it through to its output. For this
#: catalog that is the maintainer; change it here if you regroup by
#: organization, tag or anything else.
GROUP_FIELD = "maintainer"

#: Record key holding the stable identifier.
ID_FIELD = "id"

#: Order the cleaned fields appear in the emitted text, which is a separate
#: question from WHICH fields are cleaned (--fields). Title first reads as
#: context for the description that follows. Override with --text-order; a
#: cleaned field not named there is appended afterwards, in --fields order,
#: so adding a field can never silently drop it from the text.
DEFAULT_TEXT_ORDER = ("title", "notes")

#: Used when GROUP_FIELD is missing or blank. "undefined" is also a literal
#: maintainer value in this catalog, so blanks join that bucket rather than
#: forming a second one that means the same thing.
UNKNOWN_GROUP = "undefined"


#: Words dropped from a maintainer name before comparing two of them.
NAME_TITLES = {"dr", "mr", "ms", "mrs", "phd", "ph", "d", "jr", "sr", "prof"}


def group_key(name: str) -> str:
    """What two spellings of one maintainer have in common: the words,
    lowercased, stripped of punctuation and titles, and SORTED so that a
    swapped first and last name still matches."""
    words = [w for w in re.findall(r"[a-z0-9]+", name.lower())
             if w not in NAME_TITLES]
    return " ".join(sorted(words))


def group_display(spellings: collections.Counter) -> str:
    """The label for a set of joined spellings, in "John Doe" form: titles
    dropped, and a name written in capitals title-cased. A spelling that is
    already mixed case is preferred and left alone, so acronyms such as
    NASA survive. Which spelling that is comes down to record counts, so
    for a name whose word order varies the label follows the majority."""
    ranked = spellings.most_common()
    name = next((n for n, _ in ranked if not n.isupper()), ranked[0][0])
    words = [w for w in re.split(r"[\s,]+", name.strip())
             if re.sub(r"[^a-z0-9]", "", w.lower()) not in NAME_TITLES and w]
    name = " ".join(words).strip(" ,.")
    return name.title() if name.isupper() else name


def join_groups(records: list[dict]) -> list[dict]:
    """Replace each record's group with one label per maintainer.

    Returns the joins made, one entry per maintainer whose name was written
    more than one way, for the report. Records are edited in place.
    """
    spellings: dict[str, collections.Counter] = collections.defaultdict(
        collections.Counter)
    for r in records:
        spellings[group_key(r["group"])][r["group"]] += 1

    label, joins = {}, []
    for key, counts in spellings.items():
        if len(counts) == 1:
            label[key] = next(iter(counts))          # untouched
            continue
        label[key] = group_display(counts)
        joins.append({"name": label[key],
                      "spellings": sorted(counts),
                      "records": sum(counts.values())})
    for r in records:
        r["group"] = label[group_key(r["group"])]
    joins.sort(key=lambda j: -j["records"])
    return joins


def iter_records(folder: Path, pattern: str):
    """Yield (source_file, index, record) for every record in every batch."""
    files = sorted(folder.glob(pattern))
    if not files:
        raise SystemExit(f"No files matching {pattern!r} in {folder}")
    print(f"Reading {len(files)} file(s): {files[0].name} ... {files[-1].name}",
          file=sys.stderr)
    for path in files:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as err:
            print(f"  WARNING: {path.name} unreadable ({err}); skipped",
                  file=sys.stderr)
            continue
        if isinstance(payload, dict):      # {"result": {"results": [...]}} etc
            for key in ("results", "result", "records", "data"):
                if key in payload:
                    payload = payload[key]
                    break
            if isinstance(payload, dict):
                payload = payload.get("results", payload.get("result", []))
        if not isinstance(payload, list):
            print(f"  WARNING: {path.name} is not a list of records; skipped",
                  file=sys.stderr)
            continue
        for i, record in enumerate(payload):
            if isinstance(record, dict):
                yield path.name, i, record


def resolve_text_order(fields: list[str], text_order: list[str]) -> list[str]:
    """Decide the order sections appear in, given both flags.

    --fields says WHICH fields are cleaned; --text-order says in what order
    they are written out. The two are separate because the first field of
    --fields can carry other meaning, and because the order that reads best
    is not always the order you want to name the fields in.

    Fields named in --text-order come first, in that order. Any cleaned
    field not named there follows, in --fields order, so adding a field to
    --fields can never silently drop it from the text. A name in
    --text-order that is not being cleaned is reported and ignored.
    """
    named = [f for f in text_order if f in fields]
    unnamed = [f for f in fields if f not in named]
    for f in text_order:
        if f not in fields:
            print(f"  WARNING: --text-order names {f!r}, which is not in "
                  f"--fields ({', '.join(fields)}); ignored", file=sys.stderr)
    if unnamed:
        print(f"  NOTE: {', '.join(unnamed)} not named in --text-order; "
              f"appended after the named fields", file=sys.stderr)
    return named + unnamed


def build_text(cleaned, order: list[str]) -> str:
    """Join the cleaned fields into one labelled block.

    Each field gets its own "name: value" section, in the resolved order, so
    the extraction model can tell a title from a description instead of
    meeting an undifferentiated wall of text. Fields that are empty after
    cleaning are omitted rather than left as an empty heading.
    """
    sections = []
    for name in order:
        value = cleaned.text(name).strip()
        if value:
            sections.append(f"{name}: {value}")
    return "\n\n".join(sections)


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Build inputs.json (read by best_induce_schema.py "
                    "and extract_triples_for_kg.py) from harvested CKAN batches.")
    ap.add_argument("input", type=Path,
                    help="folder holding the batch files")
    ap.add_argument("--pattern", default="batch_*.json",
                    help="glob for batch files (default: batch_*.json)")
    ap.add_argument("--fields", nargs="+", metavar="FIELD",
                    default=list(DEFAULT_FIELDS),
                    help="record fields to clean and include, in the order "
                         "they should appear in the text "
                         "(default: notes title)")
    ap.add_argument("--text-order", nargs="+", metavar="FIELD",
                    default=list(DEFAULT_TEXT_ORDER),
                    help="order the cleaned fields appear in the emitted "
                         "text (default: title notes). Separate from "
                         "--fields, which says which fields to clean; any "
                         "cleaned field not named here is appended after")
    ap.add_argument("--out", type=Path, default=Path("inputs.json"),
                    help="output path (default: inputs.json)")
    ap.add_argument("--report", type=Path,
                    default=Path("build_inputs_report.json"),
                    help="where the cleaning audit is written "
                         "(default: build_inputs_report.json)")
    ap.add_argument("--keep-group-spellings", action="store_true",
                    help=f"do not join {GROUP_FIELD} spellings that differ "
                         f"only in case, punctuation, word order or titles")
    ap.add_argument("--max-records", type=int, default=0,
                    help="stop after this many written records "
                         "(0 = no limit); useful for a quick trial run")
    args = ap.parse_args()

    if args.max_records < 0:
        sys.exit(f"--max-records must be >= 0 (got {args.max_records}).")

    text_order = resolve_text_order(args.fields, args.text_order)
    print(f"  cleaning {', '.join(args.fields)}; writing sections as "
          f"{', '.join(text_order)}", file=sys.stderr)

    out: list[dict] = []
    tiers: dict[str, collections.Counter] = {f: collections.Counter()
                                             for f in args.fields}
    needs_review: list[dict] = []
    missing_field = collections.Counter()
    seen_ids: set[str] = set()
    read = skipped_empty = duplicate_ids = 0
    dropped_no_id: list[str] = []

    for source, index, record in iter_records(args.input, args.pattern):
        read += 1

        # No id -> dropped, before any cleaning, so it counts nowhere else.
        # Why drop instead of inventing one: see RECORDS WITHOUT AN ID in the
        # module docstring.
        record_id = str(record.get(ID_FIELD) or "").strip()
        if not record_id:
            dropped_no_id.append(f"{source}#{index}")
            continue

        cleaned = clean_record(record, fields=args.fields)
        for name in cleaned.missing:
            missing_field[name] += 1
        for name, note in cleaned.fields.items():
            tiers[name][note.tier] += 1
            if note.needs_review:
                needs_review.append({"id": record.get(ID_FIELD), "field": name,
                                     "method": note.tier, "source": source})

        text = build_text(cleaned, text_order)
        if not text:
            # Nothing to extract from. Counted, not silently discarded.
            skipped_empty += 1
            continue

        if record_id in seen_ids:
            # induce_schema counts DISTINCT ids, so a repeat would silently
            # merge two records' evidence; extract_triples would likewise
            # merge their triples, and scoring matches texts by id. It de-duplicates too, but the
            # problem belongs here, where the id is assigned.
            duplicate_ids += 1
            record_id = f"{record_id}#{duplicate_ids}"
        seen_ids.add(record_id)

        group = str(record.get(GROUP_FIELD) or "").strip() or UNKNOWN_GROUP
        out.append({"id": record_id, "group": group, "text": text})

        if args.max_records and len(out) >= args.max_records:
            print(f"  stopping at --max-records {args.max_records}",
                  file=sys.stderr)
            break

    if not out:
        sys.exit("No records had text in any of the chosen fields "
                 f"({', '.join(args.fields)}). Check --fields against your "
                 "data.")

    joins = [] if args.keep_group_spellings else join_groups(out)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=1, ensure_ascii=False),
                        encoding="utf-8")

    groups = collections.Counter(r["group"] for r in out)
    report = {
        "input": str(args.input), "pattern": args.pattern,
        "fields": args.fields, "text_order": text_order,
        "output": str(args.out),
        "records_read": read, "records_written": len(out),
        "skipped_no_text": skipped_empty,
        "dropped_no_id": len(dropped_no_id),
        "dropped_no_id_at": dropped_no_id,
        "duplicate_ids": duplicate_ids,
        "fields_missing_from_record": dict(missing_field),
        "groups": len(groups),
        "group_spellings_joined": len(joins),
        "group_joins": joins,
        "largest_groups": groups.most_common(10),
        "cleaning_methods": {f: dict(c) for f, c in tiers.items()},
        "needed_fallback": needs_review,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=1, ensure_ascii=False),
                           encoding="utf-8")

    print(f"\nRead {read:,} records; wrote {len(out):,} to {args.out}",
          file=sys.stderr)
    if skipped_empty:
        print(f"  {skipped_empty:,} skipped: no text in "
              f"{', '.join(args.fields)}", file=sys.stderr)
    for name, counts in tiers.items():
        detail = ", ".join(f"{k} {v:,}" for k, v in sorted(counts.items()))
        print(f"  {name}: cleaned by {detail}", file=sys.stderr)
    if needs_review:
        print(f"  {len(needs_review):,} field value(s) needed a fallback "
              f"cleaning method; ids in {args.report}", file=sys.stderr)
    for name, count in missing_field.items():
        print(f"  WARNING: {count:,} record(s) had no {name!r} field at all",
              file=sys.stderr)
    if dropped_no_id:
        print(f"  WARNING: {len(dropped_no_id):,} record(s) had no "
              f"{ID_FIELD!r} and were dropped; positions in {args.report}",
              file=sys.stderr)
    if duplicate_ids:
        print(f"  WARNING: {duplicate_ids:,} duplicate id(s) made unique with "
              f"a #n suffix; fix the upstream export", file=sys.stderr)
    if joins:
        print(f"  {len(joins):,} maintainer(s) had their spellings joined "
              f"(details in {args.report}):", file=sys.stderr)
        for j in joins[:5]:
            print(f"    {j['name']}: {' || '.join(j['spellings'])}",
                  file=sys.stderr)
        if len(joins) > 5:
            print(f"    ... and {len(joins) - 5:,} more", file=sys.stderr)
    elif args.keep_group_spellings:
        print(f"  {GROUP_FIELD!r} spellings left as harvested "
              f"(--keep-group-spellings)", file=sys.stderr)
    print(f"  {len(groups):,} group(s) from {GROUP_FIELD!r}; largest: "
          f"{[g for g, _ in groups.most_common(3)]}", file=sys.stderr)
    if len(groups) == 1:
        print("  WARNING: every record is in one group, so induce_schema's "
              "stratified sampling will draw --sample-per-group texts in "
              f"TOTAL. Check that {GROUP_FIELD!r} is the right key.",
              file=sys.stderr)
    print(f"  audit written to {args.report}", file=sys.stderr)


if __name__ == "__main__":
    main()
