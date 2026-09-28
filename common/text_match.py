"""
common/text_match.py -- how a component instance or a source text is looked
for in a text.

Every check that asks whether a component instance or a source text is "in" a
record's text, or whether two component instances are "the same", evens out
both sides first, and nothing else:

    same     upper/lower case; runs of spaces, tabs and line breaks; Unicode
             variants of one character (NFKC, e.g. a non-breaking space or a
             full-width letter); the dashes and hyphens of every width; and
             quote marks, which are ignored altogether (they carry no
             content), so "Aqua satellite" is found in '"Aqua" satellite'
             and "Earth's" still matches "Earth’s". On the component
             instance or source text being looked for, also punctuation at
             either end and a leading "the", "a" or "an". So "the Aqua
             satellite." is found in "…aboard Aqua Satellite…".
    not same anything else: "MODIS" is not "Moderate Resolution Imaging
             Spectroradiometer", "on Aqua" is not "aboard Aqua", and digits
             are kept, so "Level-2" is not "Level 3".

    from common.text_match import Text, norm_text
    text = Text(record_text)            # evened out once per record
    text.contains("the Aqua satellite") # True / False
    norm_text("  The MODIS  ")          # "modis": the key two component instances share if they are the same

Shared by every step that checks triple instances against texts (040, 050,
060) and by common/triples_io.py, so "the same" means one thing everywhere.

Adapted from norm_text in to_be_reshaped/triple_io.py and _flat/_in in
to_be_reshaped/validate_triples.py, which evened out four quotes and two
dashes (this evens out every common quote and dash) and evened out a whole
record's text again for every check (this does it once per record). Quote
marks are now ignored rather than evened out: the old code couldn't find
"Aqua satellite" in '"Aqua" satellite'.
"""
from __future__ import annotations

import re
import unicodedata

#: Every common Unicode quote, prime and dash, as its plain ASCII form.
QUOTES_AND_DASHES = str.maketrans({
    **dict.fromkeys("‘’‚‛′ʼ`´", "'"),
    **dict.fromkeys("“”„‟″«»", '"'),
    **dict.fromkeys("‐‑‒–—―−﹘﹣－", "-"),
})

#: Stripped from either end of a component instance or source text being looked for.
EDGE = " \t\n.,;:!?\"'()[]{}"

#: Words dropped from the START of a component instance or source text before
#: comparing, so "the MODIS instrument" and "MODIS instrument" match. English only; () turns it off.
LEADING_WORDS = ("the", "a", "an")

_LEADING = re.compile(r"^(?:%s)\s+" % "|".join(map(re.escape, LEADING_WORDS))) if LEADING_WORDS else None


def even(s) -> str:
    """Case, spacing, Unicode variants and dashes evened out; quote marks
    removed."""
    s = unicodedata.normalize("NFKC", str(s or "")).translate(QUOTES_AND_DASHES)
    s = s.replace('"', "").replace("'", "")
    return re.sub(r"\s+", " ", s.casefold())


def norm_text(s) -> str:
    """A component instance or source text as it is looked for: evened
    out, then edge punctuation and a leading article removed. Two component
    instances are the same when their norm_text is equal."""
    s = even(s).strip(EDGE)
    return _LEADING.sub("", s) if _LEADING else s


class Text:
    """One record's text, evened out once, to look things up in."""

    def __init__(self, text: str):
        self.flat = even(text)

    def contains(self, needle) -> bool:
        """Whether needle is in the text. A needle that is blank once evened
        out is never found."""
        n = norm_text(needle)
        return bool(n) and n in self.flat
