#!/usr/bin/env python3
"""
draft_ground_truth_triples.py -- asks a model to draft triples for records a
human will then correct into ground truth.

For each record it asks for EVERY fact the record states, as triples, in the
columns of ground_truth_triples.csv. You correct them by hand; only then are
they ground truth.

The drafter shares how it runs with the extractor (extract_triples_for_kg.py):
the options marked * below, choosing records, the prompt's rules, the
confirmation stop, the calls, the DESCRIBES row and the four output files
are all in extraction_run.py, described there once. This docstring covers
only what is the drafter's own.

USAGE
-----
    py draft_ground_truth_triples.py inputs.json            # next 10 in pool
    py draft_ground_truth_triples.py inputs.json --limit 25
    py draft_ground_truth_triples.py inputs.json --ids-from my_ids.txt

OPTIONS  (* = shared with the extractor; see extraction_run.py)
-------
    inputs *            inputs.json (required)
    --ids-from FILE *   draft these ids instead of the next in the pool. One
                        already drafted is drafted again, with a note
    --exclude-ids-from FILE [FILE ...] *
                        never draft these ids. Give it ground_truth_triples.csv
                        to skip records already annotated by hand
    --limit N *         records to draft (default: 10). Caps --ids-from too
    --pool FILE         the order to draft records in, as written by
                        ground_truth_sampler.py
                        (default: ground_truth_pool.csv in --out-dir)
    --notes FILE        the schema file whose classes and predicates go in
                        the prompt (default:
                        schema_derived_from_manual_annotation.txt in --out-dir).
                        If missing, the drafter runs with no vocabulary
    --out-dir DIR *     where every file is read and written
                        (default: ground_truth_sample_outputs)
    --sections, --all-sections, --context-section *
                        which sections the model sees, every section label
                        in inputs.json, and the section naming what a record
                        is about (defaults: title notes / the labels
                        build_inputs.py recorded writing / title)
    --max-chars N *     split a record longer than this into chunks
                        (default: 8000)
    --workers N *       model calls made at the same time (default: 1)
    --model NAME *      override MODEL in llm_client.py
    --yes *             skip the confirmation stop

WHERE THIS FITS
---------------
    the drafter (this file)   asks for EVERY fact a record states; no schema
                              is imposed, since one would limit the facts it
                              could return. Corrected by hand, its output is
                              the ground truth
    the extractor             asks for ONLY the facts a given schema can
                              express. Its output is what gets scored

A separate script, not yet written, will compare the two with precision and
recall. Two biases push those scores up:

  * A human accepting an incorrect drafted triple is likely. Reading the
    record's text first, then the triples, limits it.
  * Both are models and can miss the same fact. A fact the drafter misses is
    unlikely to be added by hand, so it never enters the ground truth; if the
    extractor misses it too, nothing is deducted. Recall then comes out
    higher than it should, with nothing in the numbers to show it.

Report any score against this ground truth as such: drafted by a model and
corrected by hand, not written from scratch.

THE SCHEMA FILE, AND WHY IT IS IN THE PROMPT
--------------------------------------------
schema_derived_from_manual_annotation.txt comes from
schema_notes_derived_from_manual_annotation.txt, written by hand while
annotating the first records, with DESCRIBES and CatalogEntry taken out: the
DESCRIBES row is written in code, not by the model.

It is in the prompt so drafted triples use the names already decided;
otherwise every batch would arrive in its own vocabulary and nothing could
be compared. The model reuses a class or predicate from the file when one
fits and coins a new one when none does. A new name is allowed but flagged.
A record needing a new class is an important event, since the schema is
still derived from only a few hand-annotated records.

WHAT IT WRITES  (in --out-dir)
--------------
Each run is one batch, numbered from 1. Its four files are described in full
under THE FILES A RUN WRITES in extraction_run.py:

    drafted_triples_batch<N>.csv            the rows to correct
    drafted_triples_batch<N>_removed.csv    duplicates and malformed items
    drafted_triples_batch<N>_run.json       how the batch was made
    drafted_triples_batch<N>_replies.jsonl  every reply, per record

The CSV's columns are those of ground_truth_triples.csv plus flags: id,
subject, subject_class, predicate, object, object_class, source_text,
all_facts_extracted, flags. all_facts_extracted is written as 0, for you to
set by hand. flags names every check the row failed (see FLAGS).

To use a batch: correct drafted_triples_batch<N>.csv, delete its flags
column, and append the rows to ground_truth_triples.csv.

A record counts as drafted once its rows are in a batch CSV, so one whose
call failed, or that was in flight when the batch was stopped, is drafted
again by the next run. To redo a whole batch, delete its four files: its
records return to the pool, and the next run takes the lowest free batch
number. A new batch never writes into an existing file.

Batches written before these files were renamed are named
draft_triples_batch<N> (.csv, .json and _removed.csv). They still count:
their records are not drafted again, and their numbers are not reused.

FLAGS
-----
Every row gets the checks the extractor runs (validate_triples.py lists them
all, with what each means). validate_triples.py sorts them into errors and
flags; the extractor writes those in two columns, since its prompt allows
only the schema's names, so a name outside it is a real mistake. Here every
check goes in the one flags column, because nothing in a draft is final and
the drafter is told to coin names: subject_class_not_in_schema here usually
means "a new class; decide whether it belongs". On the DESCRIBES row,
describes_undecided means the model named no class (it shows X, for you to
fill in).

WHAT THIS FILE NEEDS, in the same folder
----------------------------------------
    extraction_run.py     everything shared with the extractor
    llm_client.py         the Ask Sage client
    inputs_io.py          reads inputs.json and splits its texts
    triple_io.py          the triple format; reads id files
    validate_triples.py   reads the schema; every check
    .env                  ASKSAGE_EMAIL and ASKSAGE_API_KEY
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

import llm_client as llm
import extraction_run as run
from triple_io import COLUMNS
from validate_triples import Schema, read_schema

DEFAULT_DIR = Path("ground_truth_sample_outputs")
POOL_NAME = "ground_truth_pool.csv"
NOTES_NAME = "schema_derived_from_manual_annotation.txt"
#: The base of a batch's file names. The extractor's are named the same
#: way, from extracted_triples.
BASE = "drafted_triples_batch{n}"
#: A batch's CSV of rows, and only that (not its _removed.csv). Batches
#: written before the files were renamed start "draft_", not "drafted_",
#: and still count, so their records are never drafted again by mistake.
BATCH_CSV_RE = re.compile(r"(?:draft|drafted)_triples_batch(\d+)\.csv")
#: Any file of batch <n>, under either name.
BATCH_FILE_GLOB = "draft*_triples_batch{n}[._]*"

#: The columns of ground_truth_triples.csv, plus flags for review.
DRAFT_COLUMNS = COLUMNS + ["all_facts_extracted", "flags"]

PROMPT = """Extract the facts this record states, as subject / predicate /
object triples with a class for the subject and the object.

COMPLETENESS FIRST. Extract every fact the record states, whether or not
the vocabulary below can express it. Leaving a fact out is the worst
outcome; coining a new name is a normal one.

NAMING SECOND. Use a class or predicate from the list when one fits, so
records name the same things the same way. Otherwise coin one in the same
style: classes in CamelCase, predicates in UPPER_SNAKE_CASE. The list is
short and incomplete, so expect to need new names.

{schema}

RULES
{rules}

{reply}
"""


def read_pool(path: Path) -> list[str]:
    """The pool's ids, in the order they were drawn."""
    if not path.exists():
        sys.exit(f"{path} not found. Run ground_truth_sampler.py first, or "
                 f"name the ids with --ids-from.")
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return [r["id"].strip() for r in csv.DictReader(fh)
                if (r.get("id") or "").strip()]


def already_drafted(out_dir: Path) -> tuple[set[str], int]:
    """Ids drafted by earlier runs, and the next free batch number, read
    from the batch files themselves.

    A record is drafted once its rows are in a batch CSV; only those are
    read for ids, not the _removed.csv logs. Every batch CSV counts, not
    just an unbroken run from batch 1, so a gap left by deleting one batch
    does not hide the batches after it. The next batch number skips any
    number that still has any file, so a leftover file is never written
    into."""
    done = set()
    for f in out_dir.glob("draft*_triples_batch*.csv"):
        if not BATCH_CSV_RE.fullmatch(f.name):
            continue
        with f.open(newline="", encoding="utf-8-sig") as fh:
            done |= {r["id"].strip() for r in csv.DictReader(fh)
                     if (r.get("id") or "").strip()}
    batch = 1
    while any(out_dir.glob(BATCH_FILE_GLOB.format(n=batch))):
        batch += 1
    return done, batch


def load_vocabulary(path: Path) -> Schema:
    """The schema file, read by validate_triples.read_schema. A missing
    file is not an error here: the drafter imposes no schema, so it drafts
    with an empty vocabulary instead."""
    if not path.exists():
        print(f"  NOTE: {path} not found; drafting with no vocabulary",
              file=sys.stderr)
        return Schema([], [], [], "(no vocabulary decided yet)")
    return read_schema(path)


def to_draft_row(row: dict) -> dict:
    """A checked row as the drafter writes it: its errors and flags merged
    into the one flags column (see ERRORS AND FLAGS), and
    all_facts_extracted added, as 0, for you to set by hand."""
    errors = row.pop("errors", "")
    row["flags"] = " ".join(filter(None, [errors, row.get("flags", "")]))
    row["all_facts_extracted"] = 0
    return row


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Draft triples for the next pool records, to correct "
                    "by hand into ground truth; see the docstring for every "
                    "option.")
    # The options shared with the extractor (*) come from extraction_run.py.
    run.add_options(ap, out_dir=DEFAULT_DIR, limit=10, workers=1)
    ap.add_argument("--pool", type=Path,
                    help=f"the order to draft records in (default: "
                         f"{POOL_NAME} inside --out-dir)")
    ap.add_argument("--notes", type=Path,
                    help=f"the schema file (default: {NOTES_NAME} inside "
                         f"--out-dir)")
    args = ap.parse_args()
    run.apply_options(args)

    # ---- choose the records
    done, batch = already_drafted(args.out_dir)
    texts = run.load_texts(args)
    if args.ids_from:
        # Records already drafted are drafted again, with a note: each batch
        # is its own set of files, so nothing is overwritten.
        pool, order, redo_done = None, [], True
    else:
        pool = args.pool or (args.out_dir / POOL_NAME)
        order, redo_done = read_pool(pool), False
    ids = run.choose_ids(order, set(texts), args, done=done,
                         redo_done=redo_done, order_name=str(pool))
    if not ids:
        sys.exit("Nothing to draft: every chosen record has been drafted, "
                 "excluded, or is not in the inputs.")
    todo = run.prepare([(i, texts[i]) for i in ids], args)
    if not todo:
        sys.exit("Nothing to draft: none of the chosen records has any of "
                 "--sections.")

    notes_path = args.notes or (args.out_dir / NOTES_NAME)
    schema = load_vocabulary(notes_path)
    classes = sorted(schema.classes.values())
    preds = sorted(schema.preds.values())
    # Only the part above RULES is the drafter's own; the rules and reply
    # format are the extractor's too (extraction_run.py).
    prompt = PROMPT.format(schema=schema.text,
                           rules=run.extraction_rules(args.sections),
                           reply=run.REPLY_FORMAT)

    # ---- report, then wait: everything above is free, everything below paid
    notes = [f"into batch {batch}"]
    if not args.ids_from:
        notes.append(f"{len(ids):,} record(s) in the pool left to draft; "
                     f"taking the next from the top")
    calls = run.print_plan("Drafting", todo, notes, notes_path, classes,
                           preds, args)
    paths = run.output_paths(args.out_dir, BASE.format(n=batch))
    llm.start_paid_calls(calls, skip_confirm=args.yes)

    # ---- the calls
    run.write_run_record(paths["run"], run.run_record(
        "draft_ground_truth_triples.py", args, schema_path=notes_path,
        prompt=prompt, classes=classes, preds=preds, strict_patterns=False,
        batch=batch, pool=pool))
    counts = run.run_records(
        todo, prompt=prompt, schema=schema, strict_patterns=False,
        workers=args.workers, paths=paths, columns=DRAFT_COLUMNS,
        row_fix=to_draft_row)
    run.print_summary(counts, paths)
    print("  These are DRAFTS. Read each record before accepting a row.",
          file=sys.stderr)


if __name__ == "__main__":
    main()
