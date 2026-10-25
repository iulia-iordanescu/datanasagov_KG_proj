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

QUANTITIES. A component instance that is wholly one number and a unit of
QUANTITY_UNITS ("1 kilometer (km)", "4.63 km", "4,630 m", "8 days") is also
the same as any other such instance of the same quantity: same dimension
(length, time, ...), value equal once both are in the dimension's base unit
(to 12 significant digits). So "1 kilometer (km)" is "1km" and "1 km",
"4.63 km" is "4630 m", "8 day" is "8 days"; but "1 km" is not "10 km",
"1 m", "1 km2", "1 square kilometer" or "1 kilometer per second", "500 m" not
"500 nm", "5 minutes" not "5 seconds". A unit's name, plural and symbol are
one unit; a bracketed unit right after it that repeats it ("(km)") is
dropped. Kelvin and degrees Celsius are not converted into each other (a
value may be a temperature or a difference of two). Not a quantity, so
compared as words as before: a number alone ("2002"), a range ("10 to 2.15
hPa"), a percentage, a unit not in the table, a number with no space before
its unit ("8day"; the units of UNITS get one when evened out). instance_key
gives the key two component instances share if they are the same;
quantity_words the words a partial pair compares, with one whole-quantity
word in place of the instance's only number and unit ("1 kilometer (km)
pixel" holds "1 km"). Text.contains finds a component instance that is
wholly a quantity also where the text writes the same quantity otherwise
("1 km" in "a 1 kilometer (km) grid"). Nothing that was the same, contained
or found before stops being so.

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
    norm_text("  The MODIS  ")          # "modis": the instance evened out
    instance_key("1 kilometer (km)")    # "1000 m": the key two component instances share if they are the same

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
#: They are the first list of spellings of each row of QUANTITY_UNITS, in its order (UNITS is built from it, below).

#: Every unit a quantity may be written in, one row per unit: (its symbol, its dimension, how many of the dimension's
#: base unit it is, the spellings that get a space when written against a number (UNITS), its other spellings).
#: Spellings as they are once evened out (casefolded, NFKC). A dimension's base unit is its row with factor 1. Kelvin
#: and degrees Celsius are two dimensions: a value may be a temperature or a difference of two, so neither converts.
QUANTITY_UNITS = (
    ("m", "length", 1, ("m",), ("meter", "meters", "metre", "metres")),
    ("km", "length", 1e3, ("km",), ("kilometer", "kilometers", "kilometre", "kilometres")),
    ("cm", "length", 1e-2, ("cm",), ("centimeter", "centimeters", "centimetre", "centimetres")),
    ("mm", "length", 1e-3, ("mm",), ("millimeter", "millimeters", "millimetre", "millimetres")),
    ("nm", "length", 1e-9, ("nm",), ("nanometer", "nanometers", "nanometre", "nanometres")),
    ("μm", "length", 1e-6, ("μm", "um", "micron", "microns"),
     ("micrometer", "micrometers", "micrometre", "micrometres")),
    ("s", "time", 1, ("s", "sec"), ("second", "seconds", "secs")),
    ("min", "time", 60, ("min",), ("minute", "minutes", "mins")),
    ("h", "time", 3600, ("h", "hr"), ("hour", "hours", "hrs")),
    ("ms", "time", 1e-3, ("ms",), ("millisecond", "milliseconds")),
    ("hz", "frequency", 1, ("hz",), ("hertz",)),
    ("khz", "frequency", 1e3, ("khz",), ("kilohertz",)),
    ("mhz", "frequency", 1e6, ("mhz",), ("megahertz",)),
    ("ghz", "frequency", 1e9, ("ghz",), ("gigahertz",)),
    ("k", "kelvin", 1, ("k",), ("kelvin", "kelvins")),
    ("°c", "degree celsius", 1, ("°c", "degc"), ("degree celsius", "degrees celsius")),
    ("hpa", "pressure", 100, ("hpa",), ("hectopascal", "hectopascals", "mbar", "millibar", "millibars")),
    ("pa", "pressure", 1, ("pa",), ("pascal", "pascals")),
    ("db", "decibel", 1, ("db",), ("decibel", "decibels")),
    ("m/s", "speed", 1, ("m/s",), ("m s-1", "meter per second", "meters per second", "metre per second",
                                   "metres per second")),
    ("km/h", "speed", 1e3 / 3600, ("km/h",), ("km h-1", "kilometer per hour", "kilometers per hour",
                                            "kilometre per hour", "kilometres per hour")),
    ("day", "time", 86400, (), ("day", "days")),
)
UNITS = tuple(sp for row in QUANTITY_UNITS for sp in row[3])

#: Bump when what counts as the same component instance changes, so comparing two runs shows it (070's recipe).
MATCHING_VERSION = 2              # 2: quantities as quantities (QUANTITY_UNITS); 1 (before 2026-10-24): words only

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


# ------------------------------ quantities ---------------------------------

_UNIT_OF = {sp: row for row in QUANTITY_UNITS for sp in row[3] + row[4]}
_UNIT = "|".join(re.escape(sp) for sp in sorted(_UNIT_OF, key=len, reverse=True))
# A number that starts whole (no letter, digit, point or comma before it, nor "square ", "cubic ", "sq "), with
# thousands separators or a decimal part; one space; a whole unit, not followed by more of a unit ("per", "/", "^",
# "squared", "cubed", "-1", or a letter or digit: "km2"); then, optionally, a bracketed spelling of a unit.
_RUN = re.compile(r"(?<![\w.,])(?<!square )(?<!cubic )(?<!sq )(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?) (%s)"
                  r"(?![\w²³/^])(?! ?(?:per|squared|cubed)\b)(?! ?-\d)(?: ?\( ?(%s) ?\)?)?" % (_UNIT, _UNIT))
_NUMBER = re.compile(r"\d+(?:[.,]\d+)*")
_BASE = {row[1]: row[0] for row in QUANTITY_UNITS if row[2] == 1}


def _key(number: str, unit: str) -> str:
    _, dimension, factor, *_ = _UNIT_OF[unit]
    return f"{float(number.replace(',', '')) * factor:.12g} {_BASE[dimension]}"


def _runs(s: str):
    """(start, end, key) of every number and unit in the evened-out s. A bracketed unit right after one is part of it
    when it is the same unit; when it is another, the run is no quantity."""
    for m in _RUN.finditer(s):
        if m.group(3) and _UNIT_OF[m.group(3)][0] != _UNIT_OF[m.group(2)][0]:
            continue
        yield m.start(), m.end(), _key(m.group(1), m.group(2))


def _only_run(n: str):
    """The quantity in n (norm_text) as (start, end, key), when n has exactly one number and it is a quantity (a
    digit inside its unit, as in "m s-1", isn't a second number)."""
    runs = list(_runs(n))
    if len(runs) != 1 or _NUMBER.search(n[:runs[0][0]] + " " + n[runs[0][1]:]):
        return None
    return runs[0]


def quantity(s):
    """The key of s (e.g. "1000 m") when s is wholly one number and a unit (QUANTITY_UNITS), else None."""
    n = norm_text(s)
    run = _only_run(n)
    return run[2] if run and run[0] == 0 and run[1] == len(n) else None


def instance_key(s) -> str:
    """The key two component instances share if they are the same: the quantity's key for one that is wholly a
    quantity, else norm_text."""
    return quantity(s) or norm_text(s)


def quantity_words(s):
    """The words of s (norm_text), its only number and unit made one word, the quantity's key; None when s has not
    exactly one number, or that number has no unit."""
    n = norm_text(s)
    run = _only_run(n)
    if not run:
        return None
    return re.findall(r"\w+", n[:run[0]]) + [run[2]] + re.findall(r"\w+", n[run[1]:])


class Text:
    """One record's text, evened out once, to look things up in."""

    def __init__(self, text: str):
        self.even = even(text)
        self.flat = _lookup_form(self.even)
        self._quantities = None

    def contains(self, needle) -> bool:
        """Whether needle is in the text as whole words and whole numbers, punctuation inside either counting as a
        space (INNER); or, for a needle that is wholly a quantity, whether the text has the same quantity, however
        written (QUANTITIES, above). A needle that is blank once evened out is never found.

        >>> Text("Salinity from Aquarius and the Aqua satellites.").contains("aqua satellite")
        True
        >>> Text("Salinity from Aquarius.").contains("Aqua"), Text("in 25 minutes").contains("5 minutes")
        (False, False)
        >>> Text("near Comet67P").contains("67P"), Text("starting at noon").contains("START")
        (True, False)
        >>> Text("a 1 kilometer (km) grid").contains("1 km"), Text("a 4.63 km swath").contains("4630 m")
        (True, True)
        """
        n = _lookup_form(norm_text(needle))
        if n and n in self.flat and _whole(n).search(self.flat):
            return True
        q = quantity(needle)
        if q is None:
            return False
        if self._quantities is None:
            self._quantities = {k for _, _, k in _runs(self.even)}
        return q in self._quantities
