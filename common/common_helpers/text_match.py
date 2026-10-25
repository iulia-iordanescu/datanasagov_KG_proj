"""
common/common_helpers/text_match.py -- how a component instance or a source text is looked
for in a text.

Every check that asks whether a component instance or a source text is "in" a
record's text, or whether two component instances are "the same", evens out
both sides first, and nothing else:

    same     upper/lower case; runs of spaces, tabs, and line breaks; Unicode
             variants of one character (NFKC, e.g. a non-breaking space or a
             full-width letter); the dashes and hyphens of every width; and
             quote marks, which are ignored altogether (they carry no
             content), so "Aqua satellite" is found in '"Aqua" satellite'
             and "Earth's" still matches "Earth’s". On the component
             instance or source text being looked for, also punctuation at
             either end and a leading "the", "a" or "an". So "the Aqua
             satellite." is found in "…aboard Aqua Satellite…". And when a
             passage is looked up in a text (Text.contains), punctuation
             inside either one counts as a space, so "MODIS aboard Aqua" is
             found in "The MODIS, aboard Aqua". Two component instances being
             compared (norm_text) keep their inner punctuation. A number
             written against its unit gets a space, so "500m" is "500 m"
             and "3.95micron" is "3.95 micron": only for a unit in UNITS,
             and only when the number and the unit are each whole
             ("MOD021KM" and "500 meters" are left as they are).
    not same anything else: "MODIS" is not "Moderate Resolution Imaging
             Spectroradiometer", "on Aqua" is not "aboard Aqua", and digits
             are kept, so "Level-2" is not "Level 3".

What is looked up in a text is found only as whole words and whole numbers
(Text.contains): a match may not cut a word or a number in two. So "Aqua" is
not found in "Aquarius", "5 minutes" not in "25 minutes", "500 m" not in
"500 meter". Two exceptions: a plural ending ("s", "es") may follow, so
"Aqua satellite" is found in "Aqua satellites"; and a letter next to a digit
counts as a break between words, so "67P" is found in "Comet67P", where the
text lost a space. Text that lost a space between two words ("thecomet") still
hides a word; a component instance there gets a flag a person looks at.

    from common.text_match import Text, norm_text
    text = Text(record_text)            # evened out once per record
    text.contains("the Aqua satellite") # True / False
    norm_text("  The MODIS  ")          # "modis": the key two component instances share if they are the same

Shared by every step that checks triple instances against texts (040, 050,
060), by 070's matching and by common/common_helpers/triples_io.py, so "the same" means
one thing everywhere.

Adapted from norm_text in archive/to_be_reshaped/triple_io.py and _flat/_in in
archive/to_be_reshaped/validate_triples.py, which evened out four quotes and two
dashes (this evens out every common quote and dash) and evened out a whole
record's text again for every check (this does it once per record). Quote
marks are now ignored rather than evened out: the old code couldn't find
"Aqua satellite" in '"Aqua" satellite'.
"""
from __future__ import annotations

import functools
import re
import unicodedata

#: Every common Unicode quote, prime, and dash, as its plain ASCII form.
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

#: Units that, written right after a number ("500m", "4.63km", "3.95micron"), get a space before them, so they match
#: the same number and unit written with one ("500 m"). One space is the evened-out form because it is how the SI
#: Brochure writes a value, and how 080 is to write every exported value. Written as they are once evened out:
#: casefolded ("K" is "k", "MHz" is "mhz") and NFKC ("µm" with the micro sign is "μm"). Because case is evened out
#: first, "500k" (a thousand) and "500M" (a million) also get a space; harmless, as both sides of a comparison get the
#: same. Kept short on purpose: units only. No day, days, week, month or year: "8 Day" and "8day" differ little, and
#: a day word after a number is often part of a name ("8-Day", "Day 1"), where a space put in risks making two
#: different things look the same.
UNITS = ("m", "km", "cm", "mm", "nm", "μm", "um", "micron", "microns", "s", "sec", "min", "h", "hr", "ms",
         "hz", "khz", "mhz", "ghz", "k", "°c", "degc", "hpa", "pa", "db", "m/s", "km/h")

# A whole number (not the end of a name like "MOD021KM", nor the tail of "4.63"), then, with no space, a whole unit:
# no letter or digit after it, so "500meters" and "5mins" are left as they are. Longest unit first: "m/s" before "m".
_NUMBER_UNIT = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)(%s)(?!\w)"
                          % "|".join(map(re.escape, sorted(UNITS, key=len, reverse=True))))


def even(s) -> str:
    """Case, spacing, Unicode variants, and dashes evened out; quote marks
    removed; a number written against its unit (UNITS) given a space."""
    s = unicodedata.normalize("NFKC", str(s or "")).translate(QUOTES_AND_DASHES)
    s = s.replace('"', "").replace("'", "")
    return _NUMBER_UNIT.sub(r"\1 \2", re.sub(r"\s+", " ", s.casefold()))


def norm_text(s) -> str:
    """A component instance or source text as it is looked for: evened
    out, then edge punctuation and a leading article removed. Two component
    instances are the same when their norm_text is equal."""
    s = even(s).strip(EDGE)
    return _LEADING.sub("", s) if _LEADING else s


#: Endings that may follow a word looked up in a text, so "Aqua satellite" is found in "Aqua satellites". English
#: only; () turns it off.
PLURAL_ENDINGS = ("es", "s")

_PLURAL = "(?:%s)?" % "|".join(map(re.escape, PLURAL_ENDINGS)) if PLURAL_ENDINGS else ""
_NOT_AFTER = {"letter": r"(?<![^\W\d_])", "digit": r"(?<!\d)"}       # a match may not start inside a word / number
_NOT_BEFORE = {"letter": _PLURAL + r"(?![^\W\d_])", "digit": r"(?!\d)"}  # nor end inside one


def _kind(c: str) -> str:
    return "digit" if c.isdigit() else "letter" if c.isalpha() else ""


@functools.lru_cache(maxsize=4096)
def _whole(n: str) -> re.Pattern:
    """n as a pattern that matches only whole words and whole numbers: a letter at either end of n may not touch
    another letter in the text, a digit another digit."""
    return re.compile(_NOT_AFTER.get(_kind(n[0]), "") + re.escape(n) + _NOT_BEFORE.get(_kind(n[-1]), ""))


#: Inside a passage being looked up, and in the text it's looked up in, these count as a space: a model copying a
#: passage often drops or adds a comma ("MODIS aboard Aqua" for "MODIS, aboard Aqua"). A space, not nothing, so
#: "2.5" (as "2 5") is still not found as "25".
INNER = ".,;:!?()[]{}"
_INNER = str.maketrans(dict.fromkeys(INNER, " "))


def _lookup_form(s: str) -> str:
    return re.sub(r" +", " ", s.translate(_INNER)).strip()


class Text:
    """One record's text, evened out once, to look things up in."""

    def __init__(self, text: str):
        self.flat = _lookup_form(even(text))

    def contains(self, needle) -> bool:
        """Whether needle is in the text as whole words and whole numbers, punctuation inside either counting as a
        space (INNER). A needle that is blank once evened out is never found.

        >>> Text("Salinity from Aquarius and the Aqua satellites.").contains("aqua satellite")
        True
        >>> Text("Salinity from Aquarius.").contains("Aqua"), Text("in 25 minutes").contains("5 minutes")
        (False, False)
        >>> Text("near Comet67P").contains("67P"), Text("starting at noon").contains("START")
        (True, False)
        """
        n = _lookup_form(norm_text(needle))
        return bool(n) and n in self.flat and bool(_whole(n).search(self.flat))
