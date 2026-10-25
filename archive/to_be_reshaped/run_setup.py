"""
run_setup.py -- how the drafter and the extractor set up and record a run, in
one place.

draft_ground_truth_triples.py and extract_triples_for_kg.py both run over
records of inputs.json, and they set up and record a run the same way: the
same command-line options, the same way of choosing records, the same text
sent for each record, the same warnings and printout before anything is
paid for, and the same record of the run afterwards. It lives here so the
two cannot drift apart.

    add_options      the options both scripts take, with the same meaning
    apply_options    check them, and apply --model
    choose_ids       which records may run, from --ids-from,
                     --exclude-ids-from and what was already done
    prepare          each record's text, chunks and title, up to --limit,
                     with every warning about sections and titles
    print_plan       what is about to be paid for, and every class and
                     predicate the model will be handed, printed before the
                     confirmation stop
    output_paths     the four files a run writes, from their base name
    run_record       the run's _run.json: its settings and provenance
    run_records      the calls themselves, writing every record's rows,
                     removed rows and replies the moment it finishes
    print_summary    what the run wrote, printed at the end

OPTIONS BOTH SCRIPTS TAKE
-------------------------
    inputs              inputs.json (required). Several files work, as does a
                        name with a * in it, which stands for any characters
    --sections LABEL [LABEL ...]
                        which sections of each record's text the model sees;
                        every check is made against that same text
                        (default: title notes)
    --all-sections LABEL [LABEL ...]
                        every section label in inputs.json (default: title
                        notes). Only matters if inputs.json has sections you
                        leave out of --sections; see SECTIONS in inputs_io.py
    --context-section LABEL
                        the section naming what a record is about. Its text
                        becomes the DESCRIBES object and is repeated at the
                        top of every chunk of a long record (default: title)
    --ids-from FILE     run only these ids, in the file's order. A triples
                        file (CSV/JSON), induction_evidence.json, or one id
                        per line. An id listed twice counts once
    --exclude-ids-from FILE [FILE ...]
                        never run these ids. Same file kinds. Wins over
                        --ids-from when an id is in both
    --limit N           run at most N records. Counts only records that
                        will actually run: one skipped for having none of
                        --sections does not use up the limit
    --out-dir DIR       where the output files go
    --max-chars N       split a record longer than this into chunks, one call
                        each (default: 8000; see chunk_text in inputs_io.py)
    --workers N         model calls made at the same time
    --model NAME        override MODEL in llm_client.py
    --yes               skip the confirmation stop before the calls; for runs
                        with nobody at the keyboard

The defaults of --limit, --out-dir and --workers differ by script, and each
script's docstring gives them.

WARNINGS BEFORE A RUN
---------------------
Printed before anything is paid for, by both scripts:

    ids in --ids-from that are not in the inputs
    ids in both --ids-from and --exclude-ids-from (if --ids-from is the
        ground truth, it overlaps the texts the schema was induced from)
    a section in --sections that no chosen record has (usually a typo)
    records with no --context-section, whose DESCRIBES row will have no
        title
    --context-section not in --sections, so the model names each
        DESCRIBES class without seeing the title
    records skipped because none of their paragraphs starts with a label in
        --sections
    ids already done that will be run again (the drafter only; see
        choose_ids)

THE FILES A RUN WRITES
----------------------
Both scripts write the same four files, named the same way: a base name,
then a fixed ending.

    <base>.csv              the triples, one row per triple
    <base>_removed.csv      the rows kept out of <base>.csv, each with a
                            reason (duplicate or malformed)
    <base>_run.json         the run's settings and provenance (run_record)
    <base>_replies.jsonl    every reply, per record (ReplyLog)

    drafter    <base> = drafted_triples_batch<N>, one set per batch
    extractor  <base> = extracted_triples, one set per --out-dir

<base>_run.json holds:
    tool, created    which script wrote it, and when (UTC)
    settings         everything that decides what a record's rows would be:
                     the schema file, the model, the exact prompt,
                     --sections, --all-sections, --context-section,
                     --max-chars and --strict-patterns. The extractor
                     compares these on resume; validate_triples.py reads
                     them to check a file the same way it was made
    vocabulary       every class and predicate the prompt carried
    selection        how the records were chosen: the inputs, --ids-from,
                     --exclude-ids-from, --limit (and the drafter's batch
                     and pool). Provenance only

All four are written as each record finishes, never held back until the
end, so a stopped or crashed run keeps everything already paid for: every
finished record's rows, and every reply, even of a record whose rows were
not written yet. A record is "done" once its rows are in <base>.csv.

<base>_replies.jsonl holds one line per record:
    id, status      "ok", or "failed" when a call failed
    error           why it failed (failed records only)
    title, text     the DESCRIBES title, and the exact text the model saw
    replies         every reply, one per chunk, exactly as returned
A record that fails and is retried later gets one line per attempt.
"""

from __future__ import annotations

import argparse
import collections
import json
import sys
import textwrap
import threading
from datetime import datetime, timezone
from pathlib import Path

import csv

import llm_client as llm
from validate_triples import REMOVED_COLUMNS, build_rows
from inputs_io import (CONTEXT_SECTION, MAX_CHARS, SECTIONS, chosen_text,
                       chunk_text, sections, title_of)
from triple_io import read_id_list


def add_options(ap: argparse.ArgumentParser, *, out_dir: Path,
                limit: int | None, workers: int) -> None:
    """Add the options both scripts take (see OPTIONS BOTH SCRIPTS TAKE).
    out_dir, limit and workers are the calling script's defaults."""
    ap.add_argument("inputs", nargs="+",
                    help="inputs.json (several files, or a name with a *)")
    ap.add_argument("--sections", nargs="+", metavar="LABEL",
                    default=list(SECTIONS),
                    help="which sections the model sees (default: title notes)")
    ap.add_argument("--all-sections", nargs="+", metavar="LABEL",
                    default=list(SECTIONS),
                    help="every section label in inputs.json (default: title "
                         "notes)")
    ap.add_argument("--context-section", default=CONTEXT_SECTION,
                    metavar="LABEL",
                    help="the section naming what a record is about "
                         "(default: title)")
    ap.add_argument("--ids-from", type=Path, metavar="FILE",
                    help="run only these ids")
    ap.add_argument("--exclude-ids-from", type=Path, nargs="+", default=[],
                    metavar="FILE", help="never run these ids")
    ap.add_argument("--limit", type=int, default=limit,
                    help=f"run at most N records (default: "
                         f"{limit if limit else 'all'})")
    ap.add_argument("--out-dir", type=Path, default=out_dir,
                    help=f"where the output files go (default: {out_dir})")
    ap.add_argument("--max-chars", type=int, default=MAX_CHARS,
                    help=f"chunk records longer than this (default: "
                         f"{MAX_CHARS})")
    ap.add_argument("--workers", type=int, default=workers,
                    help=f"model calls at the same time (default: {workers})")
    ap.add_argument("--model", help=f"override MODEL (default: {llm.MODEL})")
    ap.add_argument("--yes", action="store_true",
                    help="skip the confirmation stop before the calls")


def apply_options(args: argparse.Namespace) -> None:
    """Check the shared options and apply --model; exit on a bad one.

    Section labels are cleaned ("title:" and "title" are the same label), and
    args.labels is set to every label to split the text by: --all-sections,
    plus any in --sections or --context-section it forgot."""
    for name in ("limit", "max_chars", "workers"):
        value = getattr(args, name)
        if value is not None and value < 1:
            sys.exit(f"--{name.replace('_', '-')} must be 1 or more.")

    def clean(labels):
        return [n.strip().rstrip(":") for n in labels if n.strip().rstrip(":")]

    args.sections = clean(args.sections)
    args.all_sections = clean(args.all_sections)
    args.context_section = args.context_section.strip().rstrip(":")
    if not args.sections:
        sys.exit("--sections needs at least one label.")
    args.labels = list(dict.fromkeys(args.all_sections + args.sections
                                     + [args.context_section]))
    if args.model:
        llm.MODEL = args.model


def choose_ids(order: list[str], available: set[str], args: argparse.Namespace,
               *, done: set[str], redo_done: bool) -> list[str]:
    """The ids to run, in order, with the warnings about them printed.

    order       the ids in the order to run them when --ids-from is not
                given: the pool's order for the drafter, the inputs' order
                for the extractor
    available   every id in the inputs
    done        ids already run (in earlier batches, or in the output file)
    redo_done   True: an id already done is run again, with a note. The
                drafter does this for --ids-from, since each batch is a
                separate set of files. False: it is skipped. The extractor
                always does this, since skipping done ids is how it resumes

    --exclude-ids-from wins over everything. --limit is not applied here
    but in prepare, so that it counts only records that will actually run."""
    banned: set[str] = set()
    for f in args.exclude_ids_from:
        ids = set(read_id_list(f))
        print(f"  excluding {len(ids):,} id(s) listed in {f}", file=sys.stderr)
        banned |= ids

    if args.ids_from:
        listed = list(dict.fromkeys(read_id_list(args.ids_from)))
        overlap = [i for i in listed if i in banned]
        if overlap:
            print(f"  WARNING: {len(overlap):,} id(s) are in both --ids-from "
                  f"and --exclude-ids-from (e.g. {overlap[:3]}); excluded. If "
                  f"--ids-from is the ground truth, it overlaps the texts the "
                  f"schema was induced from", file=sys.stderr)
        missing = [i for i in listed if i not in available]
        if missing:
            print(f"  WARNING: {len(missing):,} id(s) in {args.ids_from} are "
                  f"not in the inputs (e.g. {missing[:3]}); skipped",
                  file=sys.stderr)
        wanted = [i for i in listed if i in available and i not in banned]
    else:
        missing = [i for i in order if i not in available]
        if missing:
            print(f"  WARNING: {len(missing):,} id(s) to run are not in the "
                  f"inputs (e.g. {missing[:3]}); skipped", file=sys.stderr)
        wanted = [i for i in dict.fromkeys(order)
                  if i in available and i not in banned]

    if redo_done:
        repeats = [i for i in wanted if i in done]
        if repeats:
            print(f"  NOTE: {len(repeats):,} of these were already done and "
                  f"will be run again", file=sys.stderr)
    else:
        wanted = [i for i in wanted if i not in done]
    return wanted


def prepare(records: list[tuple[str, str]], args: argparse.Namespace):
    """The records to run, in order, ready to send: [(id, text, chunks,
    title)], at most --limit of them, with every warning about sections and
    titles printed.

    text is only the --sections of the record (chosen_text), which is both
    what the model sees and what every check is made against. title comes
    from the whole record, so the DESCRIBES row has one even when the
    context section is not sent. A record with none of --sections is
    skipped, counted in a warning, and does not use up --limit. The warnings
    cover only the records looked at, not any past the limit."""
    ready, seen, untitled, empty = [], set(), [], []
    for doc_id, full in records:
        if args.limit and len(ready) >= args.limit:
            break
        seen.update(sections(full, args.labels))
        text = chosen_text(full, args.sections, args.labels)
        if not text:
            empty.append(doc_id)
            continue
        title = title_of(full, args.labels, args.context_section)
        if not title:
            untitled.append(doc_id)
        chunks = chunk_text(text, args.max_chars, args.labels,
                            args.context_section)
        ready.append((doc_id, text, chunks, title))

    unseen = [n for n in args.sections if n not in seen]
    if unseen and seen:
        print(f"  WARNING: no chosen record has a section labelled "
              f"{', '.join(repr(n) for n in unseen)}. Check the spelling "
              f"against the fields build_inputs.py wrote", file=sys.stderr)
    if untitled:
        print(f"  WARNING: {len(untitled):,} record(s) have no "
              f"{args.context_section!r} section, so their DESCRIBES row will "
              f"have a blank title (e.g. {untitled[:3]}). Check --sections and "
              f"--all-sections against how build_inputs wrote these records",
              file=sys.stderr)
    if args.context_section not in args.sections:
        print(f"  WARNING: --context-section {args.context_section!r} is not "
              f"in --sections, so the model names each DESCRIBES class "
              f"without seeing the title", file=sys.stderr)
    if empty:
        print(f"  WARNING: {len(empty):,} record(s) skipped: no paragraph of "
              f"their text starts with "
              f"{', '.join(n + ':' for n in args.sections)} "
              f"(e.g. {empty[:3]})", file=sys.stderr)
    return ready


# ------------------------------ before the calls ---------------------------

def print_plan(verb: str, todo, notes: list[str], schema_path, classes,
               preds, args: argparse.Namespace) -> int:
    """Print what is about to be paid for, the same way for both scripts,
    and return the number of calls.

    verb    "Drafting" or "Extracting"
    notes   the calling script's own lines, e.g. how many records are
            already done

    Every class and predicate is printed in full, not truncated: the point
    is to be able to read the list and notice a name that should not be
    there (or one that should) before anything is paid for. Sorted so two
    runs can be compared."""
    calls = sum(len(chunks) for _, _, chunks, _ in todo)
    print(f"{verb} {len(todo):,} record(s) = {calls:,} call(s) to "
          f"{llm.MODEL}, plus 1 test call", file=sys.stderr)
    for note in notes:
        print(f"  {note}", file=sys.stderr)
    print(f"  sections sent: {', '.join(args.sections)}", file=sys.stderr)
    if calls > len(todo):
        print(f"  {calls - len(todo):,} extra call(s): records longer than "
              f"--max-chars {args.max_chars:,} are split into chunks",
              file=sys.stderr)
    print(f"\nschema {schema_path}", file=sys.stderr)
    for label, names in (("classes", classes), ("predicates", preds)):
        head = f"  {len(names)} {label}:".ljust(17)
        body = ", ".join(sorted(names)) if names else "(none)"
        print(textwrap.fill(body, width=78, initial_indent=head,
                            subsequent_indent=" " * 17), file=sys.stderr)
    return calls


# ------------------------------ the record of a run ------------------------

def run_record(tool: str, args: argparse.Namespace, *, schema_path, prompt,
               classes, preds, strict_patterns: bool, **selection) -> dict:
    """The contents of <base>_run.json (see THE FILES A RUN WRITES).

    selection holds anything else about how records were chosen that the
    calling script knows, e.g. the drafter's batch and pool."""
    return {
        "tool": tool,
        "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "settings": {
            "schema": str(schema_path), "model": llm.MODEL, "prompt": prompt,
            "sections": args.sections, "all_sections": args.all_sections,
            "context_section": args.context_section,
            "max_chars": args.max_chars, "strict_patterns": strict_patterns,
        },
        "vocabulary": {"classes": sorted(classes), "predicates": sorted(preds)},
        "selection": {
            "inputs": args.inputs,
            "ids_from": str(args.ids_from) if args.ids_from else None,
            "exclude_ids_from": [str(f) for f in args.exclude_ids_from],
            "limit": args.limit,
            **{k: str(v) if isinstance(v, Path) else v
               for k, v in selection.items()},
        },
    }


def write_run_record(path: Path, record: dict) -> None:
    """Write <base>_run.json."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=1, ensure_ascii=False),
                    encoding="utf-8")


class ReplyLog:
    """<base>_replies.jsonl, appended one line per record as it finishes and
    flushed at once, so a stopped or crashed run keeps every reply already
    paid for. Safe to call from any thread."""

    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = path.open("a", encoding="utf-8")
        self._lock = threading.Lock()

    def write(self, doc_id: str, *, title: str, text: str, replies=None,
              error=None) -> None:
        line = {"id": doc_id, "status": "failed" if error is not None else "ok"}
        if error is not None:
            line["error"] = str(error)
        line.update(title=title, text=text, replies=replies or [])
        with self._lock:
            self._fh.write(json.dumps(line, ensure_ascii=False) + "\n")
            self._fh.flush()

    def close(self) -> None:
        self._fh.close()


# ------------------------------ running the calls --------------------------

def output_paths(out_dir: Path, base: str) -> dict[str, Path]:
    """The four files a run writes (see THE FILES A RUN WRITES)."""
    return {"csv": out_dir / f"{base}.csv",
            "removed": out_dir / f"{base}_removed.csv",
            "run": out_dir / f"{base}_run.json",
            "replies": out_dir / f"{base}_replies.jsonl"}


def run_records(todo, *, prompt: str, schema, strict_patterns: bool,
                workers: int, paths: dict[str, Path], columns: list[str],
                row_fix=None) -> dict:
    """Make the calls for every record in todo (from prepare) and write each
    record's rows, removed rows and replies the moment it finishes.

    For each record, in a worker thread: one call per chunk
    (llm.ask_record); its replies logged to <base>_replies.jsonl at once;
    then validate_triples.build_rows turns them into checked rows. Back in
    this thread its removed rows are appended to <base>_removed.csv, then
    its rows to <base>.csv, flushed straight away. <base>.csv is written
    last because it is what marks a record done: a crash between the two
    redoes the record. A record whose call failed is logged, with its
    error, to <base>_replies.jsonl, and nothing else.

    columns    the columns of <base>.csv
    row_fix    applied to each row just before it is written, e.g. the
               drafter's, which merges errors into flags

    Returns the counts print_summary reports. Ctrl-C cancels every call not
    yet started (llm.run_parallel); records in flight still log their
    replies, but their rows are not written."""
    log = ReplyLog(paths["replies"])
    counts = collections.Counter()
    jobs = {doc_id: (doc_id, text, chunks, title)
            for doc_id, text, chunks, title in todo}

    def work(doc_id, text, chunks, title):
        replies = llm.ask_record(prompt, chunks)
        log.write(doc_id, title=title, text=text, replies=replies)
        return build_rows(doc_id, title, replies, text, schema,
                          strict_patterns)

    new_csv, new_removed = not paths["csv"].exists(), not paths["removed"].exists()
    with paths["csv"].open("a", newline="", encoding="utf-8") as fo, \
         paths["removed"].open("a", newline="", encoding="utf-8") as fr:
        out = csv.DictWriter(fo, columns, extrasaction="ignore")
        rem = csv.DictWriter(fr, REMOVED_COLUMNS)
        if new_csv:
            out.writeheader()
        if new_removed:
            rem.writeheader()

        def handle(n, doc_id, result, error):
            if error is not None:
                _, text, _, title = jobs[doc_id]
                log.write(doc_id, title=title, text=text, error=error)
                counts["failed"] += 1
                print(f"  {n}/{len(jobs)} {doc_id}: FAILED ({error})",
                      file=sys.stderr)
                return
            rows, removed = result
            errors = sum(bool(r["errors"]) for r in rows)
            flags = sum(bool(r["flags"]) for r in rows)
            if row_fix:
                rows = [row_fix(r) for r in rows]
            rem.writerows(removed)
            fr.flush()
            out.writerows(rows)
            fo.flush()
            counts.update(records=1, rows=len(rows), errors=errors,
                          flags=flags, removed=len(removed))
            counts.update(r["reason"] for r in removed)
            print(f"  {n}/{len(jobs)} {doc_id}: {len(rows)} row(s), "
                  f"{errors} with an error, {flags} with a flag; "
                  f"{len(removed)} removed", file=sys.stderr)

        llm.run_parallel(
            work, jobs, workers, handle,
            stop_note=f"Records already finished are written. Records in "
                      f"flight still log their replies in "
                      f"{paths['replies'].name}, but not their rows; they "
                      f"count as not done.")
    log.close()
    return counts


def print_summary(counts, paths: dict[str, Path]) -> None:
    """What a run wrote, printed at the end, the same for both scripts."""
    print(f"\n  {counts['rows']:,} row(s) for {counts['records']:,} "
          f"record(s): {counts['errors']:,} with an error, "
          f"{counts['flags']:,} with a flag -> {paths['csv']}", file=sys.stderr)
    print(f"  {counts['removed']:,} removed ({counts['duplicate']:,} "
          f"duplicate, {counts['malformed']:,} malformed) -> "
          f"{paths['removed']}", file=sys.stderr)
    print(f"  every reply -> {paths['replies']}", file=sys.stderr)
    print(f"  settings    -> {paths['run']}", file=sys.stderr)
    if counts["failed"]:
        print(f"  WARNING: {counts['failed']:,} record(s) failed, logged in "
              f"{paths['replies'].name}; run again to retry them",
              file=sys.stderr)
