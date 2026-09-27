#!/usr/bin/env python3
"""
extract_triples_for_kg.py -- asks a model for the facts in each record that a
given schema can express, and writes them as triples, each checked in code.

The extractor shares how it runs with the drafter
(draft_ground_truth_triples.py): the options marked * below, choosing
records, the prompt's rules, the confirmation stop, the calls, long records,
the DESCRIBES row and the four output files are all in extraction_run.py,
described there once. This docstring covers only what is the extractor's own.

USAGE
-----
    py extract_triples_for_kg.py inputs.json --schema the_schema.json
    py extract_triples_for_kg.py inputs.json --schema s.txt --limit 5
    py extract_triples_for_kg.py inputs.json --schema s.txt --ids-from gt.csv
    py extract_triples_for_kg.py inputs.json --schema s.txt --exclude-ids-from ev.json

where s.txt stands for schema_derived_from_manual_annotation.txt, gt.csv for
ground_truth_triples.csv and ev.json for induction_evidence.json.

OPTIONS  (* = shared with the drafter; see extraction_run.py)
-------
    inputs *            inputs.json (required)
    --schema FILE       the schema (required): the_schema.json from
                        best_induce_schema.py, or a text file like
                        schema_derived_from_manual_annotation.txt (both
                        formats: validate_triples.read_schema)
    --ids-from FILE *   extract only these ids. One already in the output is
                        skipped, since that is how a run resumes
    --exclude-ids-from FILE [FILE ...] *
                        never extract these ids
    --limit N *         extract at most N records this run (default: all that
                        are left)
    --out-dir DIR *     where the four output files go, created if missing
                        (default: extraction_outputs)
    --sections, --all-sections, --context-section *
                        which sections the model sees, every section label
                        in inputs.json, and the section naming what a record
                        is about (defaults: title notes / the labels
                        build_inputs.py recorded writing / title)
    --max-chars N *     split a record longer than this into chunks
                        (default: 8000)
    --workers N *       model calls made at the same time (default: 4)
    --model NAME *      override MODEL in llm_client.py
    --yes *             skip the confirmation stop
    --strict-patterns   count a triple outside the class pairs the schema
                        lists for its predicate as an error, not a flag

  !! DOMAIN AND RANGE ARE NOT ENFORCED YET. The schema's class pairs are not
  !! yet the full list of what each predicate allows, so a triple outside
  !! them is only flagged (pattern_not_in_schema). See DOMAIN AND RANGE in
  !! validate_triples.py for what the schema needs before turning on
  !! --strict-patterns.

CHOOSING RECORDS
----------------
--ids-from extracts only the ids in a file, such as the ground truth ids for
scoring. --exclude-ids-from skips the ids in a file, such as the texts the
schema was induced from.

ERRORS AND FLAGS
----------------
Every triple is checked in code (validate_triples.py lists every check),
and each check that fires adds its name to one of two columns:

    errors   provably wrong, e.g. a class that is not in the schema. Here a
             name outside the schema really is a mistake, since the prompt
             allows only the schema's names
    flags    worth a look, often fine, e.g. a subject the text words
             differently

No check removes a triple; filter on the errors column to leave those out.
triple_io.load_triples, which the evaluator will use, reads every row,
errors included, so filter before scoring if that is intended.

WHAT IT WRITES  (in --out-dir)
--------------
One folder holds one run. Its four files are described in full under THE
FILES A RUN WRITES in extraction_run.py:

    extracted_triples.csv            one row per triple
    extracted_triples_removed.csv    duplicates and malformed items
    extracted_triples_run.json       how the run was made
    extracted_triples_replies.jsonl  every reply, per record

The CSV's columns: id, subject, subject_class, predicate, object,
object_class, source_text, errors, flags.

RESUMING
--------
Run the same command again and records already in extracted_triples.csv are
skipped, while records whose call failed, or that were in flight when a run
was stopped, are tried again. A record appears whole or not at all.

So for scoring: a record missing from extracted_triples.csv was not
extracted (not run yet, or its call failed) and should be left out, not
scored as zero. A record with only its DESCRIBES row was extracted and
states no fact the schema can express.

A resumed run must use the same settings: the "settings" saved in
extracted_triples_run.json (the schema, the model, the prompt, --sections,
--all-sections, --context-section, --max-chars and --strict-patterns). If
any differ, or that file is missing, the run stops; use a new --out-dir. If
extracted_triples.csv is gone but any of the other three files is still
there, the run also stops, so an old log is never mixed into a new one.

WHAT THIS FILE NEEDS, in the same folder
----------------------------------------
    extraction_run.py     everything shared with the drafter
    llm_client.py         the Ask Sage client
    inputs_io.py          reads inputs.json and splits its texts
    triple_io.py          the triple format; reads id files
    validate_triples.py   reads the schema; every check
    .env                  ASKSAGE_EMAIL and ASKSAGE_API_KEY
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import llm_client as llm
import extraction_run as run
from triple_io import COLUMNS
from validate_triples import STRICT_PATTERNS, read_schema

#: Where the output files go, and the base of their names. The drafter's
#: are named the same way, from drafted_triples_batch<N>.
DEFAULT_DIR = Path("extraction_outputs")
BASE = "extracted_triples"

OUT_COLUMNS = COLUMNS + ["errors", "flags"]

PROMPT = """Extract the facts this record states that the schema below can
express, as subject / predicate / object triples.

{schema}

RULES
- Use ONLY the classes and predicates above, spelled exactly as written,
  describes_class included. Leave out any fact they cannot express; do not
  invent names.
{rules}

{reply}
"""


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Extract the triples a schema allows from each record; "
                    "see the docstring for every option.")
    # The options shared with the drafter (*) come from extraction_run.py.
    run.add_options(ap, out_dir=DEFAULT_DIR, limit=None, workers=4)
    ap.add_argument("--schema", type=Path, required=True,
                    help="the schema file (required)")
    ap.add_argument("--strict-patterns", action="store_true",
                    default=STRICT_PATTERNS,
                    help="make pattern_not_in_schema an error, not a flag")
    args = ap.parse_args()

    # ---- settings, checked before anything is read
    run.apply_options(args)
    if not args.schema.exists():
        sys.exit(f"Schema not found: {args.schema}")
    schema = read_schema(args.schema)
    if not schema.classes or not schema.preds:
        sys.exit(f"No classes or no predicates found in {args.schema}.")
    # Only the first rule is the extractor's own; the other rules and the
    # reply format are the drafter's too (extraction_run.py).
    prompt = PROMPT.format(schema=schema.text,
                           rules=run.extraction_rules(args.sections),
                           reply=run.REPLY_FORMAT)

    # ---- the output files: one folder never mixes two runs
    paths = run.output_paths(args.out_dir, BASE)
    record = run.run_record(
        "extract_triples_for_kg.py", args, schema_path=args.schema,
        prompt=prompt, classes=schema.classes.values(),
        preds=schema.preds.values(), strict_patterns=args.strict_patterns)
    done, earlier = set(), None
    if paths["csv"].exists():
        if not paths["run"].exists():
            sys.exit(f"{paths['csv']} has no {paths['run'].name} beside it, "
                     f"so its settings cannot be checked. Use a new "
                     f"--out-dir.")
        earlier = json.loads(paths["run"].read_text("utf-8-sig"))
        if earlier.get("settings") != record["settings"]:
            sys.exit(f"{paths['csv']} was made with different settings "
                     f"(see {paths['run']}). Use a new --out-dir.")
        # utf-8-sig: a file opened and saved in Excel gains an invisible
        # byte-order mark, which would otherwise hide the "id" header.
        with paths["csv"].open(newline="", encoding="utf-8-sig") as fh:
            done = {r["id"] for r in csv.DictReader(fh) if r.get("id")}
    else:
        leftover = [str(p) for k, p in paths.items()
                    if k != "csv" and p.exists()]
        if leftover:
            sys.exit(f"{', '.join(leftover)} left from an earlier run whose "
                     f"{paths['csv']} is gone. Move them aside first.")

    # ---- choose the records. Those already in the output are always
    # skipped: that is how a run resumes.
    texts = run.load_texts(args)
    ids = run.choose_ids(list(texts), set(texts), args, done=done,
                         redo_done=False)
    todo = run.prepare([(i, texts[i]) for i in ids], args)
    if not todo:
        print(f"Nothing to extract: {len(done):,} record(s) already done "
              f"in {paths['csv']}.", file=sys.stderr)
        return

    # ---- report, then wait: everything above is free, everything below paid
    calls = run.print_plan(
        "Extracting", todo, [f"{len(done):,} record(s) already done in "
                             f"{paths['csv']}, skipped"],
        args.schema, schema.classes.values(), schema.preds.values(), args)
    llm.start_paid_calls(calls, skip_confirm=args.yes)

    # ---- the calls. The run record is written once; a resumed run adds its
    # own time and selection under "resumed", leaving the first run's.
    if earlier is not None:
        earlier.setdefault("resumed", []).append(
            {"created": record["created"], "selection": record["selection"]})
        record = earlier
    run.write_run_record(paths["run"], record)
    counts = run.run_records(
        todo, prompt=prompt, schema=schema,
        strict_patterns=args.strict_patterns, workers=args.workers,
        paths=paths, columns=OUT_COLUMNS)
    run.print_summary(counts, paths)


if __name__ == "__main__":
    main()
