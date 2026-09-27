"""
inputs_io.py -- the one place inputs.json is read.

Every step after build_inputs.py reads the same collection of texts:

    best_induce_schema.py          samples texts from it to induce the schema
    ground_truth_sampler.py        draws texts from it to be annotated by hand
    draft_ground_truth_triples.py  drafts triples for those texts
    extract_triples_for_kg.py      extracts schema triples from its texts
    validate_triples.py            checks triples against their texts

They must read it identically. Loading makes real decisions - which file
shapes are accepted, what happens to a record with no text, what happens
when two records share an id - and if two scripts decided differently, one
could hand you a text that another skips or renames. The mismatch would
only surface much later, as a scoring error with no obvious cause.

This module holds that single decision, so there is one implementation to
fix rather than several that can drift apart. load_inputs was lifted
unchanged out of best_induce_schema.py, which now imports it from here.

    from inputs_io import load_inputs
    texts = load_inputs(["inputs.json"])      # [(id, text, group), ...]

Accepted file shapes, one or many paths, globs allowed:

    [{"id": ..., "text": ..., "group": ...}, ...]   what build_inputs writes
    {"<id>": "<text>", ...}                         group becomes "(none)"

It is also the one place a record's TEXT is taken apart, for the same
reason: build_inputs.py writes each text as labelled sections, and every
script must find those sections, the title and the chunks of a long record
in exactly the same way.

    clean_labels     labels as given on a command line, made uniform
    report_path      where build_inputs.py's report for an inputs file is
    all_sections     every label in an inputs file, as build_inputs.py
                     recorded writing it
    split_sections   the text as (label, section) pairs
    sections         the text as {label: body}
    chosen_text      only some sections, labelled, e.g. the ones sent to a
                     model
    title_of         the context section (the title), whitespace collapsed
    chunk_text       a long text cut into pieces a model call can take

SECTIONS
--------
build_inputs.py writes a record's text as labelled paragraphs:

    title: MODIS Land Cover

    notes: Yearly maps.

    Made from Terra data.

A paragraph starting "<label>:" for a known label starts that section; any
other paragraph belongs to the section above it, which is how notes with
blank lines stay whole. So a function taking sections must be given EVERY
label the text has, not only the ones wanted: a label it does not know
reads as more of the section above.

That full list is not typed by hand. build_inputs.py records the labels it
wrote ("text_order") in its report beside the inputs file, and
all_sections reads it from there, so the drafter, the extractor and the
validator split texts by exactly the labels that are in them. A label list
given on the command line must then match it, or they stop.

A text with no labelled paragraph at all, such as one from the
{"<id>": "<text>"} file shape, has no sections: sections, chosen_text and
title_of return nothing for it, and split_sections returns it whole with
label None.

Known weakness: a paragraph INSIDE notes that happens to start with another
section's label (e.g. "author:") is mistaken for that section. Fixing that
means storing each section under its own key in inputs.json.

Standard library only.
"""

from __future__ import annotations

import glob
import json
import re
from collections import Counter
from pathlib import Path

#: Group recorded for a text whose record has no group, or whose file shape
#: carries none. A literal string rather than None so it groups and prints
#: like any other group name.
NO_GROUP = "(none)"

#: Section labels build_inputs.py writes into each record's text, by default.
SECTIONS = ("title", "notes")

#: The section naming what a record is about: the DESCRIBES object, and the
#: part repeated at the top of every chunk of a long record.
CONTEXT_SECTION = "title"

#: Characters per model call. A record longer than this is split into
#: chunks; almost none are.
MAX_CHARS = 8000


def _files(paths) -> list[str]:
    """Every file the paths name, globs expanded, in the order read. A
    build_inputs.py report caught by a glob such as *.json is left out, so
    it is never read as texts."""
    files = [fp for pattern in paths for fp in sorted(glob.glob(pattern))]
    reports = {report_path(fp) for fp in files}
    return [fp for fp in files if Path(fp) not in reports]


def load_inputs(paths):
    """Read every path (globs allowed) into a list of (id, text, group).

    Texts that are empty or blank are dropped. Repeated ids are resolved as
    described below.
    """
    inputs = []
    for fp in _files(paths):
        # utf-8-sig: a file saved by PowerShell may start with an
        # invisible byte-order mark, which plain utf-8 cannot parse.
        data = json.loads(Path(fp).read_text(encoding="utf-8-sig"))
        if isinstance(data, dict):
            inputs.extend((k, str(v), NO_GROUP) for k, v in data.items())
        else:
            for r in data:
                inputs.append((str(r.get("id")), str(r.get("text") or ""),
                               str(r.get("group") or NO_GROUP).strip()
                               or NO_GROUP))
    inputs = [(i, t, g) for i, t, g in inputs if t.strip()]

    # Support is a count of DISTINCT ids, so two records sharing an id count
    # as one text everywhere downstream - silently halving the evidence a
    # class earned. Identical text under a repeated id is a true duplicate
    # and is dropped; different text under a repeated id is two real texts
    # with a collided key, so the key is made unique and the run goes on.
    seen, deduped, exact, collided = {}, [], 0, Counter()
    for _id, text, group in inputs:
        if _id not in seen:
            seen[_id] = text
            deduped.append((_id, text, group))
            continue
        if seen[_id] == text:
            exact += 1
            continue
        # Counter lookup, not a scan of everything kept so far: a catalog
        # with many collisions would otherwise make loading quadratic.
        collided[_id] += 1
        new_id = f"{_id}#{collided[_id] + 1}"
        while new_id in seen:                     # an id that literally
            collided[_id] += 1                    # contains "#n" already
            new_id = f"{_id}#{collided[_id] + 1}"
        seen[new_id] = text
        deduped.append((new_id, text, group))
    if exact:
        print(f"  {exact} exact duplicate records dropped (same id, same text)")
    if collided:
        print(f"  WARNING: {len(collided)} ids reused for DIFFERENT text "
              f"(e.g. {list(collided)[:3]}); made unique with a #n suffix. Fix "
              f"the upstream export - ids should be unique.")
    return deduped


# ------------------------------ record text --------------------------------

def clean_labels(labels) -> list[str]:
    """Section labels without their colon or spaces, blanks dropped:
    "title:" and "title" are the same label."""
    return [n.strip().rstrip(":").strip() for n in labels or []
            if n.strip().rstrip(":").strip()]


def report_path(inputs_file) -> Path:
    """Where build_inputs.py writes its report for an inputs file, and so
    where every later script looks for it: inputs.json -> inputs_report.json
    in the same folder."""
    p = Path(inputs_file)
    return p.with_name(p.stem + "_report.json")


def all_sections(given, paths, given_as: str = "--all-sections"
                 ) -> tuple[list[str], str | None]:
    """Every section label in these inputs files (globs allowed), taken from
    the report build_inputs.py wrote beside each one.

    given     labels named by the user (or a saved run), or None/empty
    given_as  what to call them in a message

    Returns (labels, warning). warning is None unless some file has no
    report to check against: then `given` is used, or SECTIONS if none,
    plus every label a report did record.

    Raises ValueError when `given` differs from what the reports recorded:
    a label left out would read as part of the section above it, and an
    extra one would cut a section wherever a paragraph starts with it."""
    given = clean_labels(given)
    recorded, unreported = [], []
    files = _files(paths)
    for fp in files:
        rp = report_path(fp)
        labels = (json.loads(rp.read_text("utf-8-sig")).get("text_order")
                  if rp.exists() else None)
        if labels:
            recorded += clean_labels(labels)
        else:
            unreported.append(fp)
    recorded = list(dict.fromkeys(recorded))

    if not unreported:
        if given and set(given) != set(recorded):
            raise ValueError(
                f"{given_as} is {' '.join(given)}, but build_inputs.py wrote "
                f"these inputs with the sections {' '.join(recorded)} (see "
                f"{', '.join(str(report_path(f)) for f in files)}).")
        return recorded, None

    missing = [n for n in recorded if n not in given]
    if given and missing:
        raise ValueError(
            f"{given_as} leaves out {' '.join(missing)}, which build_inputs.py "
            f"wrote into some of these inputs.")
    labels = list(dict.fromkeys((given or list(SECTIONS)) + recorded))
    return labels, (
        f"no build_inputs.py report beside {', '.join(unreported[:3])}, so "
        f"its section labels cannot be checked; assuming {' '.join(labels)}")


def split_sections(text: str, labels) -> list[tuple[str | None, str]]:
    """The text as (label, section) pairs, in order, each section still
    starting with its "<label>:". Text before the first label is one pair
    with label None."""
    heads = tuple(f"{n}:" for n in labels)
    out: list[list] = []
    for par in text.split("\n\n"):
        label = next((n for n, h in zip(labels, heads) if par.startswith(h)),
                     None)
        if label is not None or not out:
            out.append([label, par])
        else:
            out[-1][1] += "\n\n" + par
    return [(label, body) for label, body in out]


def sections(text: str, labels) -> dict[str, str]:
    """The text as {label: body}, the "<label>:" removed. Text before the
    first label belongs to no section and is left out."""
    return {label: body[len(label) + 1:].strip()
            for label, body in split_sections(text, labels) if label}


def chosen_text(text: str, chosen, labels) -> str:
    """Only the chosen sections, each still labelled, in the order chosen.
    labels must name every section the text has (see SECTIONS above)."""
    parts = sections(text, labels)
    return "\n\n".join(f"{n}: {parts[n]}" for n in chosen if parts.get(n))


def title_of(text: str, labels, context: str | None = CONTEXT_SECTION) -> str:
    """The context section's body with runs of whitespace collapsed, as a
    CSV cell holds it; "" if the text has none."""
    if not context:
        return ""
    return re.sub(r"\s+", " ", sections(text, labels).get(context, "")).strip()


def _split_long(par: str, budget: int) -> list[str]:
    """Split one paragraph longer than budget: at sentence ends where
    possible, else at the last space before the limit."""
    out, cur = [], ""
    for sent in re.split(r"(?<=[.!?])\s+", par):
        while len(sent) > budget:
            cut = sent.rfind(" ", 0, budget)
            cut = cut if cut > budget // 2 else budget
            if cur:
                out.append(cur)
                cur = ""
            out.append(sent[:cut])
            sent = sent[cut:].lstrip()
        if cur and len(cur) + 1 + len(sent) > budget:
            out.append(cur)
            cur = sent
        else:
            cur = f"{cur} {sent}" if cur else sent
    if cur:
        out.append(cur)
    return out


def chunk_text(text: str, max_chars: int = MAX_CHARS, labels=SECTIONS,
               context: str | None = CONTEXT_SECTION) -> list[str]:
    """Split text into pieces of at most max_chars, at paragraph breaks,
    else at sentence ends.

    If the text has a context section (the title, by default) under a
    quarter of max_chars, it is repeated at the top of every chunk, wherever
    it sits in the text, so each chunk knows what it describes. Facts in it
    then come back once per chunk; the caller deals with the repeats."""
    if len(text) <= max_chars:
        return [text]
    parts = split_sections(text, labels)
    header = ""
    if context:
        found = [body for label, body in parts if label == context]
        if found and len(found[0]) < max_chars // 4:
            header = found[0] + "\n\n"
            parts = [(label, body) for label, body in parts if label != context]
    body = "\n\n".join(b for _, b in parts)
    budget = max_chars - len(header)

    pieces = []
    for par in body.split("\n\n"):
        pieces.extend([par] if len(par) <= budget else _split_long(par, budget))
    chunks, cur = [], ""
    for p in pieces:
        if cur and len(cur) + 2 + len(p) > budget:
            chunks.append(cur)
            cur = p
        else:
            cur = f"{cur}\n\n{p}" if cur else p
    if cur:
        chunks.append(cur)
    return [header + c for c in chunks]
