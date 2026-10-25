#!/usr/bin/env python3
"""
validate_triples.py -- checks triples in code, against the schema and against
the text of the record they came from.

The drafter and the extractor run these checks on every record as they go
(through extraction_run.build_rows). Run this file by itself ("standalone")
to check a file you already have, such as a drafted batch, an extractor
output or the hand-corrected ground truth:

    py validate_triples.py extraction_outputs/extracted_triples.csv inputs.json
    py validate_triples.py ground_truth_sample_outputs/drafted_triples_batch1.csv inputs.json
    py validate_triples.py ground_truth_triples.csv inputs.json --schema s.txt

(s.txt stands for schema_derived_from_manual_annotation.txt.)

It writes <name>_checked.csv beside the file (<name> is the file's name
without .csv, and the file is replaced each run): every row, grouped by
record, with its "errors" and "flags" columns filled in afresh. It prints
how often each check fired. It removes nothing, not even duplicates.

Standalone options:

    triples             the CSV to check
    inputs              inputs.json. Several files work, as does a name with
                        a * in it, which stands for any characters
    --schema FILE       the schema. Default: the one named in <name>_run.json,
                        which the drafter and the extractor write beside
                        their output
    --sections LABEL [LABEL ...]
                        the sections the triples were taken from; checks use
                        only their text. Default: those in <name>_run.json,
                        else title notes
    --all-sections LABEL [LABEL ...]
                        every section label in inputs.json. Default: those
                        in <name>_run.json, else those build_inputs.py
                        recorded writing, else title notes. Stops if it
                        differs from what build_inputs.py recorded. See
                        SECTIONS in inputs_io.py
    --strict-patterns   make pattern_not_in_schema an error, not a flag.
                        Also on when <name>_run.json says the run used it

  !! DOMAIN AND RANGE ARE NOT ENFORCED YET. The schema is still too young
  !! for its class pairs to be the full list of what each predicate allows,
  !! so a triple outside them is only flagged. Turn on --strict-patterns
  !! once the schema's pairs are complete. See DOMAIN AND RANGE below.

ERRORS AND FLAGS
----------------
Errors are what code can prove wrong: a name is in the schema or it is not,
a passage is in the record or it is not. Flags are what code cannot decide:
often a sign of a mistake, often fine (a reworded title, a name the text
spells two ways). Neither removes a triple: both are columns, and you filter
on them. The one exception is duplicate, which the drafter and the extractor
move to their _removed.csv; standalone, this file only marks it.

The extractor writes errors and flags in two columns; the drafter puts both
in its one flags column, since nothing in a draft is final (its docstring
says why).

HOW TEXT IS COMPARED
--------------------
Every check below that asks whether a name or passage is "in" some text, or
whether two names are "the same", first evens out both sides:

    same     upper/lower case, runs of spaces and line breaks, curly vs
             straight quotes, long vs short dashes. On the name or passage
             being looked for, also punctuation at either end and a leading
             "the", "a" or "an". So "the Aqua satellite." is found in
             "...aboard Aqua Satellite..."
    not same anything else: "MODIS" is not "Moderate Resolution Imaging
             Spectroradiometer", and "on Aqua" is not "aboard Aqua"

Class and predicate names are looked up more loosely: only their letters and
digits count, case ignored, so "physical quantity" finds PhysicalQuantity
and "has target" finds HAS_TARGET. A name found this way is rewritten in the
schema's own spelling.

ERRORS
------
    subject_class_not_in_schema
                             the subject's class is not a schema class
    object_class_not_in_schema
                             the object's class is not a schema class
    predicate_not_in_schema  the predicate is not a schema predicate
    pattern_not_in_schema    only with --strict-patterns: see FLAGS
    no_source_text           source_text is blank
    source_not_in_text       source_text is not a passage of the record's text
    duplicate                an earlier row of the same record has the same
                             subject, predicate, object, subject_class and
                             object_class. The first row is not marked
    describes_undecided      the DESCRIBES row's class is X or blank: none was
                             named
    describes_class_not_in_schema
                             the DESCRIBES row's class is not a schema class
                             (kept as given)
    describes_no_title       the DESCRIBES row's object, the title, is blank
    id_not_in_inputs         the row's id names no record in inputs.json, so
                             there is no text to check it against, and no
                             other check is made on it. e.g. a hand-typed
                             "abc-123" for "abc-132"
    describes_subject_not_id the DESCRIBES row's subject is not the id in its
                             own id column. e.g. a hand-typed subject
                             "abc-123" in the row for "abc-132"

The last two come only from hand edits, so they only fire standalone: the
drafter and the extractor take every id from inputs.json and write the
DESCRIBES row in code. They check different cells: the first, the id column
against inputs.json; the second, the subject cell against the id column.

FLAGS
-----
    subject_not_in_text      the subject is not in the record's text
    object_not_in_text       the object is not in the record's text
    subject_not_in_source    the subject is not in its own source_text, the
                             passage quoted as proof. e.g. subject "MODIS",
                             source_text "aboard Aqua". Not raised when the
                             subject is the same as the record's title (the
                             DESCRIBES row's object), since a fact about the
                             title rarely names it: "This dataset contains
                             ..." is about the title
    object_not_in_source     the object is not in its own source_text
    pattern_not_in_schema    (subject_class, predicate, object_class) is not a
                             pair the schema lists for this predicate. Raised
                             only when the predicate lists pairs at all, and
                             only when both classes and the predicate are in
                             the schema. An error instead, for every
                             predicate, with --strict-patterns
    subject_equals_object    the subject and object are the same name.
                             Classes are ignored. e.g. "MODIS" ALSO_KNOWN_AS
                             "modis"
    conflicting_classes      another row of the same record has the same
                             subject, predicate and object but different
                             classes. Every such row is kept and flagged.
                             NOTE: scoring does not see it. triple_io's
                             triple_key ignores classes, so the evaluator
                             counts these rows as one triple

ROWS CHECKED DIFFERENTLY
------------------------
    the DESCRIBES row   (subject_class CatalogEntry, predicate DESCRIBES,
                        both looked up loosely like schema names) gets only
                        the describes_* checks. It is written in
                        code, not quoted from the text, so no text check
                        applies to it
    a no-facts row      a row with an id but a blank subject, predicate and
                        object, which the ground truth uses to say "this
                        record was annotated and states no facts". Passed
                        through with no checks

DOMAIN AND RANGE  (missing: waiting on the schema)
----------------
A predicate's domain is the classes its subject may have; its range, the
classes its object may have. The schema states them as class pairs under
each predicate ("Dataset -> TimeSpan; MissionPhase -> TimeSpan"). Today
those pairs record where a predicate has been SEEN, not everywhere it is
ALLOWED, so enforcing them would mark correct triples as errors.

    off (default)       pattern_not_in_schema is a flag, and only for a
                        predicate that lists pairs at all
    --strict-patterns   pattern_not_in_schema is an error: every triple's
                        (subject_class, predicate, object_class) must be a
                        listed pair, so every triple using a predicate
                        that lists none is an error

Before switching it on, the schema needs, for every predicate, the full list
of pairs it allows. The extractor's prompt already shows the model the pairs,
so no prompt change is needed.

WHAT THIS FILE PROVIDES TO THE OTHER SCRIPTS
--------------------------------------------
    read_schema       either schema format, as a Schema
    check_record      every check on one record's rows
    ENTRY_CLASS, ENTRY_PREDICATE, ENTRY_SOURCE, UNDECIDED
                      what the DESCRIBES row is made of
    STRICT_PATTERNS   the default for --strict-patterns
"""

from __future__ import annotations

import argparse
import collections
import csv
import json
import re
import sys
import unicodedata
from pathlib import Path

from inputs_io import (SECTIONS, all_sections, chosen_text, clean_labels,
                       load_inputs)
from triple_io import COLUMNS, _QUOTES, label_key, norm_text, triple_key

#: The DESCRIBES row every record gets, written in code by the drafter and
#: the extractor (extraction_run.describes_row): <id> (CatalogEntry)
#: DESCRIBES <title> (<class>). Its source_text is ENTRY_SOURCE, and
#: UNDECIDED marks a class not yet chosen.
ENTRY_CLASS, ENTRY_PREDICATE, UNDECIDED = "CatalogEntry", "DESCRIBES", "X"
ENTRY_SOURCE = "(record structure)"

#: Enforce domain and range? False until the schema's class pairs are the
#: full list of what each predicate allows (see DOMAIN AND RANGE above).
#: --strict-patterns sets it for one run.
STRICT_PATTERNS = False


# ------------------------------ schema --------------------------------------

def _warn_unknown_pairs(classes, preds, pairs, path) -> None:
    """A class pair naming a class or predicate the schema does not define
    (usually a typo) can never match any triple, so it is reported."""
    bad = [p for p in pairs
           if p[0] not in classes or p[1] not in preds or p[2] not in classes]
    if bad:
        print(f"  WARNING: {len(bad)} class pair(s) in {path} name a class or "
              f"predicate the schema does not define, so they can never "
              f"match (e.g. {' '.join(bad[0])})", file=sys.stderr)


class Schema:
    """Class and predicate names, looked up loosely: label_key keeps only
    letters and digits, case ignored, so "physical quantity" finds
    PhysicalQuantity.
    pairs holds the (subject_class, predicate, object_class) the schema
    lists, in the schema's own spelling."""

    def __init__(self, classes, preds, pairs, text):
        self.classes = {label_key(n): n for n in classes}
        self.preds = {label_key(n): n for n in preds}
        self.pairs = set(pairs)
        self.paired_preds = {p for _, p, _ in self.pairs}
        self.text = text                   # the schema as the prompt shows it

    def cls(self, name):
        return self.classes.get(label_key(name))

    def pred(self, name):
        return self.preds.get(label_key(name))


def read_schema(path: Path) -> Schema:
    """Read either schema format.

    the_schema.json from best_induce_schema.py: names from entity_classes
    and predicates, class pairs from patterns.

    A text file like schema_derived_from_manual_annotation.txt: a CLASSES
    and a PREDICATES section, each a heading line, a line of dashes, then
    one entry per line: the name at the left margin, then two or more
    spaces and its description (or nothing). Class pairs sit on indented
    lines beneath their predicate as "A -> B; C -> D". A line holding a
    single word at the margin therefore counts as a name. Any other line,
    such as a sentence of prose, is ignored."""
    if path.suffix.lower() == ".json":
        s = json.loads(path.read_text(encoding="utf-8-sig"))
        def named(key):
            return {e["name"]: e.get("definition", "") for e in s.get(key, [])
                    if isinstance(e, dict) and e.get("name")}
        classes, preds = named("entity_classes"), named("predicates")
        pairs = [tuple(p["pattern"]) for p in s.get("patterns", [])
                 if isinstance(p, dict) and len(p.get("pattern") or []) == 3]
        by_pred = collections.defaultdict(list)
        for a, p, b in pairs:
            by_pred[p].append(f"{a} -> {b}")
        text = "CLASSES\n" + "\n".join(f"{n}  {d}" for n, d in classes.items())
        text += "\n\nPREDICATES (subject -> object)\n" + "\n".join(
            f"{n}  {d}" + (f"\n    {'; '.join(by_pred[n])}" if n in by_pred else "")
            for n, d in preds.items())
        _warn_unknown_pairs(classes, preds, pairs, path)
        return Schema(classes, preds, pairs, text)

    text = path.read_text(encoding="utf-8-sig")

    def block(heading):
        m = re.search(rf"^{heading}\r?\n-+\r?\n(.*?)(?=\r?\n[A-Z ]+\r?\n-+|\Z)",
                      text, re.S | re.M)
        return m.group(1) if m else ""

    name_re = re.compile(r"^([A-Za-z][A-Za-z0-9_]*)(?:\s{2,}|\s*$)", re.M)
    classes = name_re.findall(block("CLASSES"))
    preds, pairs, cur = [], [], None
    for line in block("PREDICATES").splitlines():
        m = name_re.match(line)
        if m:
            cur = m.group(1)
            preds.append(cur)
        elif cur and "->" in line:
            for pair in line.split(";"):
                a, _, b = pair.partition("->")
                if a.strip() and b.strip():
                    pairs.append((a.strip(), cur, b.strip()))
    _warn_unknown_pairs(classes, preds, pairs, path)
    return Schema(classes, preds, pairs, text.strip())


# ------------------------------ text matching ------------------------------

def _flat(s) -> str:
    """The text being searched, evened out as norm_text evens out the name
    being looked for, minus norm_text's trimming of edges and articles."""
    s = unicodedata.normalize("NFKC", str(s or "")).translate(_QUOTES)
    return re.sub(r"\s+", " ", s.casefold())


def _in(needle, flat_text) -> bool:
    """Is needle in flat_text (already passed through _flat)? A needle that
    is blank once evened out is never found."""
    n = norm_text(needle)
    return bool(n) and n in flat_text


# ------------------------------ the checks ----------------------------------

def is_describes(row: dict) -> bool:
    """The structural row: subject_class CatalogEntry, predicate DESCRIBES,
    matched loosely like any schema name, so a hand-typed "catalogentry"
    still counts."""
    return (label_key(row.get("subject_class")) == label_key(ENTRY_CLASS)
            and label_key(row.get("predicate")) == label_key(ENTRY_PREDICATE))


def check_row(row: dict, flat_text: str, schema: Schema, doc_id: str,
              strict_patterns: bool = STRICT_PATTERNS, title: str = ""):
    """(errors, flags) for one row, except duplicate and conflicting_classes,
    which need the whole record (check_record adds them). Class and
    predicate names found in the schema are rewritten in place to the
    schema's spelling. title is the record's DESCRIBES object, the one
    subject exempt from subject_not_in_source."""
    errors, flags = [], []

    if is_describes(row):
        row["subject_class"], row["predicate"] = ENTRY_CLASS, ENTRY_PREDICATE
        if row["subject"] != doc_id:
            errors.append("describes_subject_not_id")
        if label_key(row["object_class"]) in ("", label_key(UNDECIDED)):
            row["object_class"] = UNDECIDED
            errors.append("describes_undecided")
        elif schema.cls(row["object_class"]):
            row["object_class"] = schema.cls(row["object_class"])
        else:
            errors.append("describes_class_not_in_schema")
        if not row["object"]:
            errors.append("describes_no_title")
        return errors, flags

    for k in ("subject_class", "object_class"):
        name = schema.cls(row[k])
        if name:
            row[k] = name
        else:
            errors.append(f"{k}_not_in_schema")
    name = schema.pred(row["predicate"])
    if name:
        row["predicate"] = name
    else:
        errors.append("predicate_not_in_schema")

    if not row["source_text"].strip():
        errors.append("no_source_text")
    elif not _in(row["source_text"], flat_text):
        errors.append("source_not_in_text")

    for k in ("subject", "object"):
        if not _in(row[k], flat_text):
            flags.append(f"{k}_not_in_text")
    if row["source_text"].strip():
        source = _flat(row["source_text"])
        # A fact about the title is usually stated without naming it ("This
        # dataset contains..."), so a title subject is exempt.
        if (not _in(row["subject"], source)
                and norm_text(row["subject"]) != norm_text(title)):
            flags.append("subject_not_in_source")
        if not _in(row["object"], source):
            flags.append("object_not_in_source")
    # Domain and range, asked only once all three names are in the schema.
    # One check, one name; --strict-patterns only moves it from flag to error.
    names_ok = not any(e.endswith("_not_in_schema") for e in errors)
    pattern = (row["subject_class"], row["predicate"], row["object_class"])
    if names_ok and pattern not in schema.pairs:
        if strict_patterns:
            errors.append("pattern_not_in_schema")
        elif row["predicate"] in schema.paired_preds:
            flags.append("pattern_not_in_schema")
    if norm_text(row["subject"]) == norm_text(row["object"]):
        flags.append("subject_equals_object")
    return errors, flags


def check_record(doc_id: str, rows: list[dict], text: str | None,
                 schema: Schema, strict_patterns: bool = STRICT_PATTERNS):
    """Check every row of one record. Returns [(row, errors, flags)], rows in
    the order given, each row a cleaned copy. text is the record's chosen
    text; None means the id is not in the inputs."""
    # first[key] for each subject/predicate/object: the flags list of the
    # first row that had it, and every class pair seen with it so far.
    flat, first, out = _flat(text or ""), {}, []
    title = next((str(r.get("object") or "") for r in rows if is_describes(r)), "")
    for row in rows:
        row = {**row, **{k: str(row.get(k) or "").strip() for k in COLUMNS}}
        if text is None:
            out.append((row, ["id_not_in_inputs"], []))
            continue
        if not (row["subject"] or row["predicate"] or row["object"]):
            out.append((row, [], []))     # "annotated, no facts" marker row
            continue
        errors, flags = check_row(row, flat, schema, doc_id,
                                  strict_patterns, title)
        key = triple_key(row)
        classes = (label_key(row["subject_class"]), label_key(row["object_class"]))
        if key not in first:
            first[key] = (flags, {classes})
        elif classes in first[key][1]:
            errors.append("duplicate")
        else:
            # Same fact, other classes: a disagreement to look at, not a
            # repeat to drop. This row and the first are both flagged.
            flags.append("conflicting_classes")
            if "conflicting_classes" not in first[key][0]:
                first[key][0].append("conflicting_classes")
            first[key][1].add(classes)
        out.append((row, errors, flags))
    return out


# ------------------------------ command line --------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description="Check a triples CSV in code.")
    ap.add_argument("triples", type=Path)
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("--schema", type=Path)
    ap.add_argument("--sections", nargs="+")
    ap.add_argument("--all-sections", nargs="+")
    ap.add_argument("--strict-patterns", action="store_true",
                    default=STRICT_PATTERNS)
    args = ap.parse_args()
    if not args.triples.exists():
        sys.exit(f"Not found: {args.triples}")

    # <name>_run.json, written beside the file by the drafter or extractor.
    run_path = args.triples.with_name(args.triples.stem + "_run.json")
    run = (json.loads(run_path.read_text("utf-8-sig")).get("settings", {})
           if run_path.exists() else {})
    schema_path = args.schema or (Path(run["schema"]) if "schema" in run else None)
    if not schema_path:
        sys.exit(f"No --schema given, and no schema in {run_path} to take "
                 f"it from.")
    chosen = clean_labels(args.sections) or run.get("sections") or list(SECTIONS)
    # The labels build_inputs.py recorded writing are checked against
    # --all-sections, else against the run's; a mismatch with the run's
    # means inputs.json was rebuilt differently since.
    given_as = ("--all-sections" if args.all_sections
                else f"all_sections in {run_path.name}")
    try:
        all_labels, warning = all_sections(
            args.all_sections or run.get("all_sections"), args.inputs,
            given_as)
    except ValueError as exc:
        sys.exit(f"{exc} " + ("Leave --all-sections out to use those."
                              if args.all_sections else
                              "These may not be the inputs the triples were "
                              "made from."))
    if warning:
        print(f"  WARNING: {warning}", file=sys.stderr)
    strict = args.strict_patterns or run.get("strict_patterns", False)
    if not schema_path.exists():
        sys.exit(f"Schema not found: {schema_path}")
    schema = read_schema(schema_path)
    labels = list(dict.fromkeys(all_labels + chosen))

    with args.triples.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        if not reader.fieldnames or "id" not in reader.fieldnames:
            sys.exit(f"{args.triples} has no header row with an id column.")
        # errors and flags are recomputed, so any old ones are dropped.
        header = [c for c in reader.fieldnames if c not in ("errors", "flags")]
        rows = list(reader)
    by_id = collections.defaultdict(list)
    for r in rows:
        by_id[(r.get("id") or "").strip()].append(r)
    texts = {i: chosen_text(t, chosen, labels)
             for i, t, _ in load_inputs(args.inputs) if i in by_id}

    out_path = args.triples.with_name(args.triples.stem + "_checked.csv")
    counts, bad = collections.Counter(), 0
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, header + ["errors", "flags"],
                           extrasaction="ignore")
        w.writeheader()
        for doc_id, recs in by_id.items():
            for row, errors, flags in check_record(doc_id, recs, texts.get(doc_id),
                                                   schema, strict):
                counts.update(errors + flags)
                bad += bool(errors)
                w.writerow({**row, "errors": " ".join(errors),
                            "flags": " ".join(flags)})

    print(f"{len(rows):,} row(s) in {len(by_id):,} record(s); {bad:,} with an "
          f"error.  schema {schema_path}, text from {', '.join(chosen)}, "
          f"patterns {'enforced' if strict else 'flagged only'}",
          file=sys.stderr)
    for name, n in counts.most_common():
        print(f"  {n:6,}  {name}", file=sys.stderr)
    print(f"-> {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
