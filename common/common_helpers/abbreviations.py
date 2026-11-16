"""
common/common_helpers/abbreviations.py -- rule 20's abbreviation test, implemented once, and the short forms a
record's text sets off in parentheses or commas.

Rule 20 of "Writing a classed triple" (annotations/guidelines.md): a short form "is an abbreviation only when each of
its letters is a letter of those words, in the same order, and its first letter starts the first of them (the test of
Schwartz and Hearst, 2003)". The test is the algorithm of A. S. Schwartz and M. A. Hearst, "A simple algorithm for
identifying abbreviation definitions in biomedical text", Pacific Symposium on Biocomputing 8:451-462 (2003),
Figure 2 (findBestLongForm), ported here: the short form's characters are matched from its last to its first against
the words before it, from right to left, case ignored; a character that is neither a letter nor a digit ("&", "-") is
skipped; the first character must start a word (the character before it, if any, is neither a letter nor a digit, so
"1" of "Sentinel-1" starts a word); letters skipped inside words are allowed ("x" of DSWx is the "x" of "Extent").
The words looked at are at most min(|A| + 5, 2|A|) words before the short form (|A|: its characters), as Schwartz and
Hearst limit the long form.

    passes(short, words)       whether short is an abbreviation of the words just before it
    long_form(short, words)    the shortest long form the test finds (from the start of a word), or None
    is_short_form(token, commas=False)
                               whether a token can be a short form: Schwartz and Hearst's candidate (2 to 10
                               characters, a letter among them, a letter or digit first), one word; set off by commas
                               (commas=True), also shaped like an acronym (two capitals, or a capital and a digit), so
                               the items of a plain list ("Terra, Aqua, and Aura") and describing words ("small,
                               polar, orbit") are never taken for one
    short_forms(text)          every short form a text sets off: "(T)" right after words, and ", T," right after words
                               (commas=True), each with the words before it and whether it passes

Used by common/common_helpers/validate.py, check_abbreviations, which FLAGS a model's reply that disagrees with the
test (040, 050, 060); nothing is ever changed by it.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

#: Where the words before a short form stop: a sentence's end, a clause mark, a bracket or a line break.
_CLAUSE_END = re.compile(r"[.;:!?()\[\]{}\n]\s|[;:()\[\]{}\n]")
_PARENS = re.compile(r"\(([^()\s]{2,10})\)")
_COMMAS = re.compile(r",\s*([^,\s]{2,10})\s*,")


def _window(short: str, words: str) -> str:
    """The last min(|A| + 5, 2|A|) words of words (Schwartz and Hearst's limit on a long form's length)."""
    n = len(short)
    parts = words.split()
    return " ".join(parts[-min(n + 5, 2 * n):]) if parts else ""


def long_form(short: str, words: str) -> str | None:
    """The shortest long form of short at the end of words, by Schwartz and Hearst's findBestLongForm, or None."""
    s, text = short.strip(), _window(short.strip(), words)
    if not any(c.isalnum() for c in s) or not s[:1].isalnum():
        return None
    si, li = len(s) - 1, len(text) - 1
    while si >= 0:
        c = s[si].lower()
        if not c.isalnum():
            si -= 1
            continue
        while li >= 0 and (text[li].lower() != c or (si == 0 and li > 0 and text[li - 1].isalnum())):
            li -= 1
        if li < 0:
            return None
        li -= 1
        si -= 1
    start = text.rfind(" ", 0, li + 1) + 1
    return text[start:]


def passes(short: str, words: str) -> bool:
    """Whether short is an abbreviation of the words just before it (rule 20's test)."""
    return long_form(short, words) is not None


def is_short_form(token: str, commas: bool = False) -> bool:
    """Whether a token can be a short form (see the top of this file)."""
    t = token.strip()
    if not (2 <= len(t) <= 10) or any(c.isspace() for c in t) or not t[0].isalnum() \
            or not any(c.isalpha() for c in t):
        return False
    if commas:
        capitals = sum(c.isupper() for c in t)
        return capitals >= 2 or (capitals >= 1 and any(c.isdigit() for c in t))
    return True


@dataclass(frozen=True)
class ShortForm:
    short: str          # as the text writes it
    words: str          # the words before it, back to the clause's start (or the previous comma, for commas)
    passes: bool        # rule 20's test
    commas: bool        # set off by commas, not parentheses


def _before(text: str, end: int, commas: bool) -> str:
    """The words before position end, back to the start of the clause (and of the list item, for commas)."""
    head = text[:end]
    starts = [m.end() for m in _CLAUSE_END.finditer(head)]
    if commas:
        starts.append(head.rfind(",") + 1)
    return head[max(starts, default=0):].strip()


def short_forms(text: str) -> list:
    """Every short form text sets off right after words, in the order written (see the top of this file)."""
    found = []
    for m in _PARENS.finditer(text):
        t = m.group(1)
        words = _before(text, m.start(), False)
        if is_short_form(t) and words:
            found.append((m.start(), ShortForm(t, words, passes(t, words), False)))
    for m in re.finditer(r"(?=" + _COMMAS.pattern + ")", text):      # overlapping: "A, HG, B, HGI, C"
        t = m.group(1)
        words = _before(text, m.start(), True)
        if is_short_form(t, commas=True) and words:
            found.append((m.start(), ShortForm(t, words, passes(t, words), True)))
    return [f for _, f in sorted(found, key=lambda x: x[0])]
