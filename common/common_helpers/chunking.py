"""
common/common_helpers/chunking.py -- the text a model reads for one record, in pieces
short enough for one call each.

    from common.chunking import pieces
    for piece in pieces(record, max_chars=8000):
        ...                                   # one model call per piece

A record's text is its chosen fields (title and notes, then any extra ones 020
kept), joined in that order, each preceded by its field name:

    title: MODIS/Aqua Surface Reflectance

    notes: The MODIS instrument aboard Aqua …

Almost every record fits in one piece. A longer one is split at paragraph
breaks, else at sentence ends, else at the last space before the limit. The
title is repeated at the top of every piece, so each piece says what it is
about, and each piece of the other fields is marked "part i of n":

    title: MODIS/Aqua Surface Reflectance

    notes (part 2 of 3): …

Nothing is cut off: every character of the fields is in some piece. Shared by
every step that sends records to a model (040, 050 and 060), so a
long record is read the same way everywhere.

Adapted from chunk_text in to_be_reshaped/inputs_io.py, which re-parsed the
field names out of one string and cut the text into pieces without saying which
part a piece was.
"""
from __future__ import annotations

import re

from common.records_io import TEXT_FIELDS

#: Characters per model call. Few records are longer (45 of 36,375 on
#: 2026-09-27).
MAX_CHARS = 8000

#: The field repeated at the top of every piece.
CONTEXT_FIELD = "title"


def text_fields(record: dict) -> list:
    """The record's text fields, in the order 020 wrote them: the ones its
    _cleaning lists (title, notes, then extra ones), else title and notes."""
    return list(record.get("_cleaning") or TEXT_FIELDS)


def full_text(record: dict) -> str:
    """The record's whole text: each non-empty field, preceded by its field name."""
    return "\n\n".join(f"{name}: {record[name].strip()}" for name in text_fields(record)
                       if (record.get(name) or "").strip())


def _split_paragraph(par: str, budget: int) -> list:
    """One paragraph longer than budget, split at sentence ends where
    possible, else at the last space before the limit, else hard."""
    out, cur = [], ""
    for sentence in re.split(r"(?<=[.!?])\s+", par):
        while len(sentence) > budget:
            cut = sentence.rfind(" ", 0, budget)
            cut = cut if cut > budget // 2 else budget
            if cur:
                out.append(cur)
                cur = ""
            out.append(sentence[:cut])
            sentence = sentence[cut:].lstrip()
        if cur and len(cur) + 1 + len(sentence) > budget:
            out.append(cur)
            cur = sentence
        else:
            cur = f"{cur} {sentence}" if cur else sentence
    if cur:
        out.append(cur)
    return out


def _parts(value: str, budget: int) -> list:
    """A field's text in parts of at most budget characters, split at
    paragraph breaks first."""
    paragraphs = []
    for par in value.split("\n\n"):
        paragraphs += [par] if len(par) <= budget else _split_paragraph(par, budget)
    parts, cur = [], ""
    for par in paragraphs:
        if cur and len(cur) + 2 + len(par) > budget:
            parts.append(cur)
            cur = par
        else:
            cur = f"{cur}\n\n{par}" if cur else par
    if cur:
        parts.append(cur)
    return parts


def pieces(record: dict, max_chars: int = MAX_CHARS) -> list:
    """The record's text as a list of pieces of at most max_chars (the whole
    text, as one piece, when it fits)."""
    whole = full_text(record)
    if len(whole) <= max_chars:
        return [whole] if whole else []

    title = (record.get(CONTEXT_FIELD) or "").strip()
    header = f"{CONTEXT_FIELD}: {title}" if title and len(title) < max_chars // 4 else ""
    fields = [n for n in text_fields(record)
              if (record.get(n) or "").strip() and not (header and n == CONTEXT_FIELD)]
    out = []
    for name in fields:
        value = record[name].strip()
        # Room for the header, this field's name with "(part i of n)", and
        # the blank lines between them.
        budget = max_chars - len(header) - len(name) - 40
        parts = _parts(value, budget)
        for i, part in enumerate(parts, 1):
            prefix = name if len(parts) == 1 else f"{name} (part {i} of {len(parts)})"
            out.append("\n\n".join(x for x in (header, f"{prefix}: {part}") if x))
    return out
