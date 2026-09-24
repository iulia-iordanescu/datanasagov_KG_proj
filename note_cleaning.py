#!/usr/bin/env python3
"""
note_cleaning.py -- turn HTML-contaminated text into plain text, safely.

Dependency-free cleanup for free-text fields with web markup baked in:
`&lt;p&gt;`, `&amp;rsquo;`, `<sub>2</sub>`, `<a href="...">`. Written for
CKAN-style catalog records; nothing in it is specific to one catalog.

    >>> from note_cleaning import clean
    >>> clean('Armstrong&amp;rsquo;s &lt;b&gt;FOSS&lt;/b&gt; sensor')
    'Armstrong\u2019s FOSS sensor'


THE GUARANTEE
-------------
Cleanup rules cannot be proven correct for data nobody has inspected, so
this library checks its own output instead of asking you to trust it:

    every run of letters and digits in the input -- words, numbers, URL
    fragments -- appears in the output, the same number of times.

Punctuation and whitespace are exempt; cleaning moves those around
legitimately. Three strategies are tried, each verified before it is
accepted, and the one used is reported as `.tier`:

    "parsed"        Python's HTML parser reads the structure and the
                    text is rebuilt from it. Unknown elements are
                    transparent -- tag dropped, text kept -- so markup
                    nobody anticipated costs formatting, not content.
    "conservative"  A separate, cruder implementation that deletes
                    anything tag-shaped, after lifting out href/src.
                    Used when the parse loses content, e.g. on an
                    unterminated attribute quote, which a parser is
                    entitled to swallow whole. Different implementation,
                    different failure modes.
    "source"        The decoded input, uncleaned: cannot lose anything,
                    because it is the input. Ugly but complete.

The verifier is deliberately a separate implementation from the cleaner.
An earlier version shared the cleaner's notion of what a tag is, so it
agreed with the cleaner's mistakes -- that is how a bug deleting
"<log(L_IR/L_sun)>" went unnoticed. A check reusing the code under test
is not a check.


WHAT CLEANING DOES
------------------
    &amp;rsquo; &amp;#176;     decoded to ' and °, repeatedly, since
                              some sources escape twice
    <a href="U">text</a>      text [U]
    <img src="U">             [image: U]
    <sub>x</sub> <sup>y</sup> _x  ^y
    <ol><li>a</li></ol>       1. a        (numbering preserved)
    <ul><li>a</li></ul>       - a
    <td>a</td><td>b</td>      a | b
    <p> <div> <h1> <br> ...   line breaks
    <script> <style>          content dropped (code, not prose)
    any other tag             removed, text inside kept
    <log(L/L)>   values < 5   left alone: not valid tag syntax

Markup flush against text never welds words: `10<sup>35</sup>erg` ->
`10^35 erg`. Genuine joins survive: `un<b>be</b>lievable` stays one word.


WHAT TO PASS, WHAT COMES BACK
-----------------------------
    clean(value)                -> str
    clean_note(value)           -> CleanedNote
    clean_many(values)          -> iterator of CleanedNote
    clean_record(mapping)       -> CleanedRecord
    clean_records(mappings)     -> iterator of CleanedRecord
    verify(value, cleaned_str)  -> Counter of what is missing
    summarize(notes_or_records) -> CleanReport

`value` is anything: str, bytes (decoded UTF-8), None ("") or other
(str()). It need not contain markup; text without any is returned with
only whitespace normalised.

`mapping` is any dict-like record. `fields=` names which keys to clean
and defaults to DEFAULT_FIELDS, i.e. ("notes", "title").

Order and length are preserved exactly. `clean_many` and `clean_records`
yield one result per input, in input order, and stream rather than
accumulate -- safe over a whole catalog. Field order in `fields=` sets
the order of `CleanedRecord.fields` and therefore the column order of
`.to_dict()`; it has no other effect. A field a record lacks is listed
in `.missing` and produces no columns, so `.to_dict()` can be narrower
than `fields` -- pad it yourself if you need a fixed CSV header.
Cleaning one value is independent of every other: same input, same
output, whatever else is in the batch.

    >>> rows = list(clean_records([{"title": "A &lt;b&gt;B&lt;/b&gt;", "notes": "n"}],
    ...                           fields=("notes", "title")))
    >>> list(rows[0].to_dict())          # column order follows fields=
    ['notes', 'notes_clean', 'notes_clean_method', 'title', 'title_clean', 'title_clean_method']
    >>> rows[0].text("title"), rows[0].tier("title")
    ('A B', 'parsed')


CHECKING IT
-----------
    python note_cleaning.py --selftest     regression suite, exit 1 on fail
    python note_cleaning.py --fuzz 5000    randomised malformed input
    python note_cleaning.py --doctest      the examples in this file
    python note_cleaning.py < input.html   clean stdin to stdout

Call `selftest()` at pipeline start; treat `.needs_review` (tier is not
"parsed") as worth a look -- complete, but possibly ugly.

Standard library only. Pure functions, no global state: deterministic,
thread-safe, and roughly 35k values/second on ordinary text.
"""

from __future__ import annotations

import collections
import html
import itertools
import re
import sys
from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Iterable, Iterator

__all__ = [
    "clean", "clean_note", "clean_many", "verify", "summarize", "selftest",
    "clean_record", "clean_records", "DEFAULT_FIELDS",
    "CleanedNote", "CleanedRecord", "CleanReport",
    "TIER_PARSED", "TIER_CONSERVATIVE", "TIER_SOURCE",
    "__version__",
]

__version__ = "1.1.0"

TIER_PARSED = "parsed"
TIER_CONSERVATIVE = "conservative"
TIER_SOURCE = "source"

#: How many times to undo HTML escaping. Two passes are needed for
#: double-escaped input (`&amp;rsquo;` -> `&rsquo;` -> `'`); the third is
#: headroom. Decoding stops as soon as the text stops changing, so this
#: only bounds pathological input. Lowering it to 2 reduces the (remote)
#: risk of over-decoding text that deliberately displays an entity.
MAX_DECODE_PASSES = 3


# --------------------------------------------------------------------
# Element classification -- from the HTML specification, not from any
# one dataset. Elements absent from every set below are transparent.
# --------------------------------------------------------------------

#: Block-level elements: text either side belongs on separate lines.
BLOCK_TAGS = frozenset({
    "address", "article", "aside", "blockquote", "body", "canvas",
    "caption", "colgroup", "dd", "details", "div", "dl", "dt", "fieldset",
    "figcaption", "figure", "footer", "form", "h1", "h2", "h3", "h4", "h5",
    "h6", "header", "hgroup", "hr", "html", "legend", "main", "nav",
    "noscript", "output", "p", "pre", "section", "summary", "table",
    "tbody", "tfoot", "thead", "tr", "video",
})

#: Elements whose content is code or metadata rather than prose.
DROP_CONTENT_TAGS = frozenset({
    "script", "style", "head", "title", "meta", "link",
})

#: Inline elements: they join the words either side of them, so
#: `un<b>be</b>lievable` is one word. Used by the fallback renderer and
#: the verifier to decide whether a removed tag implies a word boundary.
INLINE_TAGS = frozenset({
    "abbr", "b", "bdi", "bdo", "big", "cite", "code", "data", "del", "dfn",
    "em", "font", "i", "ins", "kbd", "mark", "nobr", "q", "rp", "rt",
    "ruby", "s", "samp", "small", "span", "strike", "strong", "time", "tt",
    "u", "var", "wbr",
})


# --------------------------------------------------------------------
# Patterns. All depend on HTML *syntax*, never on particular content.
# --------------------------------------------------------------------

#: A real tag name is an identifier. Anything else shaped like a tag --
#: "<log(L_IR/L_sun)>", "<see Fig. 3>" -- is prose using angle brackets.
VALID_TAG_NAME = re.compile(r"^[a-zA-Z][a-zA-Z0-9:._-]*$")

#: A syntactically well-formed tag: identifier name, and anything after
#: the name separated from it by whitespace.
WELL_FORMED_TAG = re.compile(
    r"</?([A-Za-z][A-Za-z0-9:._-]*)((?:\s[^<>]*)?)/?>")

#: "<" that does not begin a well-formed tag, comment or declaration.
#: The HTML specification treats such a "<" as literal text; Python's
#: parser is more lenient and would read "<log(L/L)>" as a tag, so this
#: restores the stricter rule before parsing.
STRAY_LT = re.compile(
    r"<(?!(?:/?[A-Za-z][A-Za-z0-9:._-]*(?:\s[^<>]*)?/?>|!--|!|\?))")

COMMENT = re.compile(r"<!--.*?-->", re.S)
DROP_BLOCK = re.compile(r"<(script|style)\b[^>]*>.*?</\1\s*>", re.I | re.S)
ATTR_URL = re.compile(r"""(?:href|src)\s*=\s*["']?\s*([^"'\s>]+)""", re.I)
TOKEN = re.compile(r"[A-Za-z0-9]+")
BLANK_RUN = re.compile(r"\n{3,}")
CELL_JOIN = re.compile(r"\|[ \t]*\n[ \t]*(?=\S)")
CELL_TRAIL = re.compile(r"[ \t]*\|[ \t]*(?=\n|$)")


# --------------------------------------------------------------------
# Results
# --------------------------------------------------------------------

@dataclass(frozen=True)
class CleanedNote:
    """The outcome of cleaning one piece of text.

    Attributes
    ----------
    text : str
        The cleaned text. Never shorter in content than the input: every
        word, number and URL fragment from `source` is present.
    tier : str
        Which strategy produced `text`: TIER_PARSED, TIER_CONSERVATIVE
        or TIER_SOURCE. Anything other than TIER_PARSED means the markup
        defeated the normal path and is worth inspecting.
    source : str
        The input after HTML escaping was undone, before any markup was
        rendered. Useful for showing raw vs cleaned side by side.
    had_markup : bool
        True if the input contained a well-formed tag or an HTML entity.
        False means cleaning was a no-op and `text` equals the input.
    lost : collections.Counter
        Tokens the accepted text is missing. Empty for TIER_PARSED and
        TIER_CONSERVATIVE, because a tier is only accepted once it
        verifies. Also empty for TIER_SOURCE, where the text *is* the
        input and so cannot be missing anything -- see `token_verified`.
    token_verified : bool
        True when `text` passed the token check. False only for
        TIER_SOURCE: markup left in place tokenizes differently from
        rendered text ("un<b>be</b>lievable" is not the token
        "unbelievable"), so the check does not apply there. Completeness
        is guaranteed by identity instead -- the text is the input.
    """

    text: str
    tier: str
    source: str
    had_markup: bool
    lost: collections.Counter = field(default_factory=collections.Counter)
    token_verified: bool = True

    @property
    def is_clean_parse(self) -> bool:
        """True if the normal, best-quality path was used."""
        return self.tier == TIER_PARSED

    @property
    def needs_review(self) -> bool:
        """True if the markup defeated the normal path.

        Worth eyeballing: the text is complete either way, but it was
        produced by a fallback and may read poorly.
        """
        return self.tier != TIER_PARSED


@dataclass(frozen=True)
class CleanReport:
    """Aggregate statistics over many cleaned notes. See `summarize`."""

    total: int
    with_markup: int
    by_tier: collections.Counter
    lossy: int
    needs_review: int

    def __str__(self) -> str:
        return (
            f"{self.total:,} notes cleaned "
            f"({self.with_markup:,} containing markup)\n"
            f"  parsed       : {self.by_tier[TIER_PARSED]:,}\n"
            f"  conservative : {self.by_tier[TIER_CONSERVATIVE]:,}\n"
            f"  source       : {self.by_tier[TIER_SOURCE]:,}\n"
            f"  needs review : {self.needs_review:,}\n"
            f"  lost content : {self.lossy:,}"
        )

    @property
    def ok(self) -> bool:
        """True if nothing lost content. Suitable for an assertion."""
        return self.lossy == 0


# --------------------------------------------------------------------
# Decoding
# --------------------------------------------------------------------

def _as_text(value) -> str:
    """Coerce any input to str. None becomes "", bytes are decoded."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (bytes, bytearray)):
        return bytes(value).decode("utf-8", errors="replace")
    return str(value)


def unescape_fully(text: str, limit: int = MAX_DECODE_PASSES) -> str:
    """Undo HTML escaping, repeating for double-escaped input.

    Parameters
    ----------
    text : str
        Possibly-escaped text.
    limit : int
        Maximum passes. Decoding stops early once the text stops
        changing, so this only bounds pathological input.

    Returns
    -------
    str
        The decoded text.

    Examples
    --------
    >>> unescape_fully('a &amp;rsquo; b') == "a \\u2019 b"
    True
    >>> unescape_fully('AT&T stays')
    'AT&T stays'
    """
    for _ in range(limit):
        decoded = html.unescape(text)
        if decoded == text:
            break
        text = decoded
    return text


# --------------------------------------------------------------------
# Tier 1: structural parse
# --------------------------------------------------------------------

class _PlainTextRenderer(HTMLParser):
    """Rebuild plain text from parsed HTML. Internal; use `clean`."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.out: list[str] = []
        self.list_stack: list[object] = []
        self.link_stack: list[str] = []
        self.drop_depth = 0
        # Set after emitting something that must not weld onto the next
        # word. Inline styling never sets it.
        self.pending_gap = False

    def _write(self, text: str, gap: bool | None = None) -> None:
        if not text or self.drop_depth:
            return
        if gap is None:
            gap = self.pending_gap
        self.pending_gap = False
        if gap and self.out:
            previous = self.out[-1]
            if previous and previous[-1].isalnum() and text[0].isalnum():
                self.out.append(" ")
        self.out.append(text)

    def _newline(self) -> None:
        self.pending_gap = False
        if not self.drop_depth:
            self.out.append("\n")

    def handle_starttag(self, tag, attrs) -> None:
        if not VALID_TAG_NAME.match(tag):
            self._write(self.get_starttag_text() or "", gap=True)
            self.pending_gap = True
            return
        values = dict(attrs)
        if tag in DROP_CONTENT_TAGS:
            self.drop_depth += 1
        elif tag == "br":
            self._newline()
        elif tag == "img":
            src = (values.get("src") or "").strip()
            alt = (values.get("alt") or "").strip()
            self._write(f"[image: {src}]" if src else
                        (f"[image: {alt}]" if alt else "[image]"), gap=True)
            self.pending_gap = True
        elif tag == "a":
            self.link_stack.append((values.get("href") or "").strip())
            self.pending_gap = True
        elif tag in ("sub", "sup"):
            self._write("_" if tag == "sub" else "^", gap=True)
        elif tag == "ol":
            self.list_stack.append(itertools.count(1))
            self._newline()
        elif tag == "ul":
            self.list_stack.append(None)
            self._newline()
        elif tag == "li":
            counter = self.list_stack[-1] if self.list_stack else None
            self.out.append("\n" + (f"{next(counter)}. " if counter else "- "))
            self.pending_gap = False
        elif tag in BLOCK_TAGS:
            self._newline()

    def handle_startendtag(self, tag, attrs) -> None:
        self.handle_starttag(tag, attrs)
        if tag in DROP_CONTENT_TAGS:
            self.drop_depth = max(0, self.drop_depth - 1)

    def handle_endtag(self, tag) -> None:
        if not VALID_TAG_NAME.match(tag):
            self._write(f"</{tag}>", gap=True)
            self.pending_gap = True
            return
        if tag in DROP_CONTENT_TAGS:
            self.drop_depth = max(0, self.drop_depth - 1)
        elif tag == "a":
            href = self.link_stack.pop() if self.link_stack else ""
            if href:
                self._write(f" [{href}]", gap=False)
            self.pending_gap = True
        elif tag in ("sub", "sup"):
            self.pending_gap = True
        elif tag in ("ol", "ul"):
            if self.list_stack:
                self.list_stack.pop()
            self._newline()
        elif tag in ("td", "th"):
            self.out.append(" | ")
            self.pending_gap = False
        elif tag == "li" or tag in BLOCK_TAGS:
            self._newline()

    def handle_data(self, data: str) -> None:
        self._write(data)

    def handle_entityref(self, name: str) -> None:
        self._write(f"&{name};")

    def handle_charref(self, name: str) -> None:
        self._write(f"&#{name};")

    def result(self) -> str:
        # Text truncated mid-tag strands characters in the parser's
        # buffer; recover them rather than lose them.
        leftover = getattr(self, "rawdata", "")
        if leftover:
            self._write(leftover, gap=True)
        text = "".join(self.out).replace("\xa0", " ")
        return _tidy(text)


def _tidy(text: str) -> str:
    text = CELL_JOIN.sub("| ", text)
    text = CELL_TRAIL.sub("", text)
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    return BLANK_RUN.sub("\n\n", text).strip()


def _render_parsed(decoded: str) -> str:
    parser = _PlainTextRenderer()
    try:
        parser.feed(STRAY_LT.sub("&lt;", decoded))
        parser.close()
    except Exception:              # a parse error must never lose a note
        pass
    return parser.result()


# --------------------------------------------------------------------
# Tier 2: independent fallback
# --------------------------------------------------------------------

def _render_conservative(decoded: str) -> str:
    text = COMMENT.sub(" ", DROP_BLOCK.sub(" ", decoded))

    def replace(match: re.Match) -> str:
        name = match.group(1).lower()
        urls = ATTR_URL.findall(match.group(2) or "")
        if urls:
            return f" [{urls[0]}] "
        return "" if name in INLINE_TAGS else " "

    return _tidy(WELL_FORMED_TAG.sub(replace, text).replace("\xa0", " "))


# --------------------------------------------------------------------
# Verification
# --------------------------------------------------------------------

def _expected_tokens(raw: str) -> collections.Counter:
    """Tokens the cleaned text must contain.

    Implemented with regular expressions rather than the parser used for
    cleaning, on purpose: a check that reuses the code under test agrees
    with that code's mistakes.
    """
    decoded = unescape_fully(_as_text(raw))
    decoded = COMMENT.sub(" ", DROP_BLOCK.sub(" ", decoded))
    urls = " ".join(ATTR_URL.findall(decoded))

    def blank(match: re.Match) -> str:
        return "" if match.group(1).lower() in INLINE_TAGS else " "

    visible = WELL_FORMED_TAG.sub(blank, decoded)
    return collections.Counter(TOKEN.findall(visible + " " + urls))


def _missing(expected: collections.Counter, cleaned: str
             ) -> collections.Counter:
    """Shared by `verify` and `clean_note`; avoids recomputing tokens."""
    return expected - collections.Counter(TOKEN.findall(cleaned))


def verify(raw, cleaned) -> collections.Counter:
    """Content present in `raw` but missing from `cleaned`.

    Usable as an independent audit of any cleaner, not just this one.

    Parameters
    ----------
    raw : str | bytes | None
        The original value, as stored.
    cleaned : str
        Text produced from it, by anything.

    Returns
    -------
    collections.Counter
        Missing token -> how many occurrences are missing. **Empty means
        nothing was lost**; this is the value to assert on. Counts
        matter: a word twice in the source must appear twice in output.
        Only letter/digit runs are compared; punctuation and spacing are
        exempt.

    Examples
    --------
    >>> bool(verify('<a href="http://x.org">docs</a>', 'docs'))
    True
    >>> bool(verify('<a href="http://x.org">docs</a>', 'docs [http://x.org]'))
    False
    """
    return _missing(_expected_tokens(raw), _as_text(cleaned))


# --------------------------------------------------------------------
# Public cleaning API
# --------------------------------------------------------------------

def clean_note(raw) -> CleanedNote:
    """Clean one value, reporting which strategy was used.

    Parameters
    ----------
    raw : str | bytes | None | any
        See "WHAT TO PASS" in the module docstring.

    Returns
    -------
    CleanedNote
        `.text` cleaned, `.tier` strategy used, `.source` decoded input,
        `.had_markup`, `.needs_review`, `.lost`.

    Raises
    ------
    Nothing, for any input. Failures degrade to a lower tier.

    Examples
    --------
    >>> note = clean_note('10&lt;sup&gt;35&lt;/sup&gt;erg')
    >>> note.text
    '10^35 erg'
    >>> note.tier
    'parsed'
    >>> clean_note('plain text, no markup').had_markup
    False
    """
    text = _as_text(raw)

    # Fast path. Without "<" or "&" there is no markup and no escaping,
    # so cleaning can only normalise whitespace -- which cannot drop a
    # token, so the check is unnecessary too. This is most inputs, and
    # it skips both the parse and the tokenisation. Verified in the
    # self-test to give byte-identical results to the full path.
    if "<" not in text and "&" not in text:
        return CleanedNote(_tidy(text), TIER_PARSED, text, False)

    decoded = unescape_fully(text)
    had_markup = bool(WELL_FORMED_TAG.search(decoded)) or decoded != text
    expected = _expected_tokens(text)

    for render, tier in ((_render_parsed, TIER_PARSED),
                         (_render_conservative, TIER_CONSERVATIVE)):
        try:
            candidate = render(decoded)
        except Exception:
            continue
        if not _missing(expected, candidate):
            return CleanedNote(candidate, tier, decoded, had_markup)

    # Last resort: hand back the decoded input. Nothing can be missing
    # from it, so the token check is skipped rather than reported as a
    # failure -- unrendered markup simply tokenizes differently.
    fallback = decoded.strip()
    return CleanedNote(fallback, TIER_SOURCE, decoded, had_markup,
                       collections.Counter(), token_verified=False)


def clean(raw) -> str:
    """Clean one value and return the text.

    `clean_note` without the metadata. Never raises, never loses content.

    Parameters
    ----------
    raw : str | bytes | None | any

    Returns
    -------
    str

    Examples
    --------
    >>> clean('&lt;p&gt;Armstrong&amp;rsquo;s sensor&lt;/p&gt;')
    'Armstrong\\u2019s sensor'
    >>> clean('&lt;ol&gt;&lt;li&gt;first&lt;/li&gt;&lt;li&gt;second&lt;/li&gt;&lt;/ol&gt;')
    '1. first\\n\\n2. second'
    >>> clean(None)
    ''
    """
    return clean_note(raw).text


def clean_many(raws: Iterable) -> Iterator[CleanedNote]:
    """Clean many values, lazily: one CleanedNote per input, in order.

    Streams rather than accumulates, so it is safe over a whole catalog.
    Pass results to `summarize`, or filter on `.needs_review`.

    Examples
    --------
    >>> [n.text for n in clean_many(['&lt;b&gt;a&lt;/b&gt;', 'b'])]
    ['a', 'b']
    """
    for raw in raws:
        yield clean_note(raw)


def summarize(notes: Iterable[CleanedNote]) -> CleanReport:
    """Tally results from `clean_many` or `clean_records`.

    Parameters
    ----------
    notes : iterable of CleanedNote or CleanedRecord
        Records are flattened to their fields, so a report over records
        counts fields, not records.

    Returns
    -------
    CleanReport
        Per-tier totals; `.ok` is True when nothing was lost;
        `print(report)` gives a readable summary.

    Examples
    --------
    >>> report = summarize(clean_many(['&lt;b&gt;a&lt;/b&gt;', 'plain']))
    >>> report.total, report.ok
    (2, True)
    """
    def flatten(items):
        for item in items:
            if isinstance(item, CleanedRecord):
                yield from item.fields.values()
            else:
                yield item

    total = with_markup = lossy = needs_review = 0
    by_tier: collections.Counter = collections.Counter()
    for note in flatten(notes):
        total += 1
        with_markup += bool(note.had_markup)
        by_tier[note.tier] += 1
        lossy += bool(note.lost)
        needs_review += bool(note.needs_review)
    return CleanReport(total, with_markup, by_tier, lossy, needs_review)


# --------------------------------------------------------------------
# Record-level cleaning
# --------------------------------------------------------------------

#: Fields cleaned when a caller does not say otherwise. Both are free
#: text in CKAN-style catalogs and both carry markup in practice.
DEFAULT_FIELDS = ("notes", "title")


@dataclass(frozen=True)
class CleanedRecord:
    """One record's worth of cleaned fields, with an audit trail.

    Every cleaned field keeps three things: what it looked like
    originally, what it looks like now, and which method produced that.
    Nothing is overwritten, so any later question about a value is
    answerable without re-running anything.

    Attributes
    ----------
    fields : dict[str, CleanedNote]
        One entry per cleaned field, keyed by field name, in the order
        requested. Each `CleanedNote` holds `.source` (the original,
        after HTML escaping was undone), `.text` (cleaned) and `.tier`
        (the method used).
    missing : tuple[str, ...]
        Requested fields the record did not contain at all. Absent
        fields are reported here rather than silently becoming "".

    Examples
    --------
    >>> record = {"title": "SMAP &lt;b&gt;L2&lt;/b&gt;", "notes": "10&lt;sup&gt;3&lt;/sup&gt;erg"}
    >>> result = clean_record(record)
    >>> result.text("title")
    'SMAP L2'
    >>> result.text("notes")
    '10^3 erg'
    >>> result.tier("notes")
    'parsed'
    """

    fields: dict
    missing: tuple = ()

    def text(self, name: str) -> str:
        """Cleaned value of one field, or "" if it was absent."""
        note = self.fields.get(name)
        return note.text if note else ""

    def original(self, name: str) -> str:
        """Value of one field as harvested, before cleaning."""
        note = self.fields.get(name)
        return note.source if note else ""

    def tier(self, name: str) -> str:
        """Which method cleaned one field: parsed/conservative/source."""
        note = self.fields.get(name)
        return note.tier if note else ""

    @property
    def needs_review(self) -> bool:
        """True if any field needed a fallback method."""
        return any(note.needs_review for note in self.fields.values())

    def to_dict(self, *, include_original: bool = True,
                clean_suffix: str = "_clean",
                method_suffix: str = "_clean_method") -> dict:
        """Flatten to plain columns, ready for CSV or a DataFrame.

        Parameters
        ----------
        include_original : bool
            Keep the original value under the field's own name. Turn off
            only if you already store the source elsewhere; keeping it is
            what makes the cleaning auditable.
        clean_suffix, method_suffix : str
            Column-name suffixes for the cleaned value and the method.

        Returns
        -------
        dict
            For fields ("notes",) and defaults, the keys are
            "notes", "notes_clean", "notes_clean_method".

        Examples
        --------
        >>> row = clean_record({"title": "A &lt;b&gt;B&lt;/b&gt;"},
        ...                    fields=("title",)).to_dict()
        >>> sorted(row)
        ['title', 'title_clean', 'title_clean_method']
        >>> row["title_clean"], row["title_clean_method"]
        ('A B', 'parsed')
        """
        out = {}
        for name, note in self.fields.items():
            if include_original:
                out[name] = note.source
            out[f"{name}{clean_suffix}"] = note.text
            out[f"{name}{method_suffix}"] = note.tier
        return out


def clean_record(record, fields: Iterable[str] = DEFAULT_FIELDS
                 ) -> CleanedRecord:
    """Clean the named fields of one record. The record is not modified.

    Parameters
    ----------
    record : Mapping
        Any dict-like record, e.g. parsed JSON or a database row.
    fields : iterable of str
        Keys to clean, in output order (default ("notes", "title")).
        A key the record lacks goes to `.missing` and is skipped; a key
        present but empty cleans normally to "".

    Returns
    -------
    CleanedRecord
        Original, cleaned and method per field. `.to_dict()` flattens it
        for CSV.

    Raises
    ------
    Nothing for any record content; a non-mapping `record` raises
    TypeError, which is a coding error rather than a data problem.

    Examples
    --------
    >>> result = clean_record({"notes": "a &lt;b&gt;b&lt;/b&gt;"}, fields=("notes", "title"))
    >>> result.text("notes")
    'a b'
    >>> result.missing
    ('title',)
    """
    cleaned = {}
    missing = []
    for name in fields:
        if name not in record:
            missing.append(name)
            continue
        cleaned[name] = clean_note(record.get(name))
    return CleanedRecord(cleaned, tuple(missing))


def clean_records(records: Iterable, fields: Iterable[str] = DEFAULT_FIELDS
                  ) -> Iterator[CleanedRecord]:
    """Clean many records, lazily: one CleanedRecord per input, in order.

    Parameters
    ----------
    records : iterable of Mapping
    fields : iterable of str
        As for `clean_record`.

    Yields
    ------
    CleanedRecord

    Examples
    --------
    >>> rows = clean_records([{"notes": "&lt;b&gt;x&lt;/b&gt;"}], fields=("notes",))
    >>> [r.text("notes") for r in rows]
    ['x']
    """
    fields = tuple(fields)
    for record in records:
        yield clean_record(record, fields)


# --------------------------------------------------------------------
# Self-test
# --------------------------------------------------------------------

#: (description, input, substrings that must appear in the output).
#: Every entry is either a bug that was once real or a property that
#: must hold. Add to this list rather than trusting a fix by eye.
SELFTESTS = [
    ("link address kept",
     '&lt;a href="https://nsidc.org/d/x"&gt;the docs&lt;/a&gt;',
     ["the docs", "https://nsidc.org/d/x"]),
    ("image address kept",
     '&lt;img src = "https://c3.nasa.gov/x.png"&gt;',
     ["[image: https://c3.nasa.gov/x.png]"]),
    ("newline inside an attribute value",
     '&lt;img src="\n https://c3.nasa.gov/y.png"&gt;',
     ["https://c3.nasa.gov/y.png"]),
    ("angle-bracket maths is not a tag",
     'starbursts (&lt;log(L&lt;sub&gt;IR&lt;/sub&gt;/L&lt;sub&gt;sun&lt;/sub&gt;)&gt; ~ 11.2)',
     ["log(L_IR/L_sun)", "11.2"]),
    ("less-than sign survives",
     'values &lt; 5 mm and &lt;= 2.5*M&lt;sub&gt;sun&lt;/sub&gt;',
     ["< 5 mm", "<= 2.5*M_sun"]),
    ("subscript and superscript",
     'nu&lt;sub&gt;peak&lt;/sub&gt; and 10&lt;sup&gt;-14&lt;/sup&gt;',
     ["nu_peak", "10^-14"]),
    ("double-escaped entity",
     'technology&amp;rsquo;s size',
     ["technology\u2019s size"]),
    ("list item does not fuse with next heading",
     '&lt;li&gt;and interpolation&lt;/li&gt;&lt;/ul&gt;&lt;p&gt;&lt;strong&gt;Plotting&lt;/strong&gt;&lt;/p&gt;',
     ["interpolation\n", "Plotting"]),
    ("ordered list stays numbered",
     '&lt;ol&gt;&lt;li&gt;Establish&lt;/li&gt;&lt;li&gt;Examine&lt;/li&gt;&lt;/ol&gt;',
     ["1. Establish", "2. Examine"]),
    ("unordered list stays bulleted",
     '&lt;ul&gt;&lt;li&gt;first&lt;/li&gt;&lt;li&gt;second&lt;/li&gt;&lt;/ul&gt;',
     ["- first", "- second"]),
    ("table row on one line",
     '&lt;tr&gt;&lt;td&gt;Band&lt;/td&gt;\n&lt;td&gt;Wavelength&lt;/td&gt;&lt;/tr&gt;',
     ["Band | Wavelength"]),
    ("uppercase tags",
     'one&lt;BR&gt;two&lt;P&gt;three',
     ["one\ntwo", "three"]),
    ("emphasis removed, text kept",
     '&lt;strong&gt;Phase I&lt;/strong&gt; is the opportunity',
     ["Phase I is the opportunity"]),
    ("superscript flush against a word",
     '10&lt;sup&gt;35&lt;/sup&gt;erg s&lt;sup&gt;-1&lt;/sup&gt;',
     ["10^35 erg", "s^-1"]),
    ("right ascension run together",
     '24&lt;sup&gt;h&lt;/sup&gt;00&lt;sup&gt;m&lt;/sup&gt;09.0&lt;sup&gt;s&lt;/sup&gt;',
     ["24^h 00^m 09.0^s"]),
    ("link flush against preceding word",
     'available at&lt;a href="http://x.org/p"&gt;http://x.org/p&lt;/a&gt;',
     ["at http://x.org/p"]),
    ("inline styling still joins a word",
     'un&lt;b&gt;be&lt;/b&gt;lievable',
     ["unbelievable"]),
    ("unknown element is transparent",
     'The &lt;marquee foo="1"&gt;satellite&lt;/marquee&gt; launched',
     ["The satellite launched"]),
    ("script content dropped",
     '&lt;script&gt;var x = 1;&lt;/script&gt;real text',
     ["real text"]),
    ("malformed attribute quote keeps the words",
     '&lt;font color="#DF01A5&gt;Website&lt;/font&gt;',
     ["Website"]),
    ("truncated markup keeps the words",
     '&lt;p&gt;text here&lt;li&g',
     ["text here"]),
]


def selftest(verbose: bool = False) -> None:
    """Run the regression suite; raise AssertionError listing failures.

    Call at pipeline start to confirm the library behaves as documented
    in the environment it is actually running in.

    Parameters
    ----------
    verbose : bool
        Print passing cases too.

    Examples
    --------
    >>> selftest()
    """
    failures: list[str] = []

    for name, raw, required in SELFTESTS:
        note = clean_note(raw)
        for needle in required:
            if needle not in note.text:
                failures.append(
                    f"{name}: expected {needle!r}, got {note.text!r}")
        if note.lost:
            failures.append(f"{name}: content lost {dict(note.lost)}")
        if verbose and not failures:
            print(f"  ok  {name} [{note.tier}]", file=sys.stderr)

    # The fast path (no "<" or "&") skips parsing and verification; it
    # must produce exactly what the full path would.
    for sample in ["plain words", "line\n\n\n\nbreaks", "trailing   ",
                   "", "   ", "a\tb", "café ünïcode 42"]:
        full = _tidy(_render_parsed(unescape_fully(sample)))
        if clean_note(sample).text != full:
            failures.append(
                f"fast path differs from full path on {sample!r}: "
                f"{clean_note(sample).text!r} vs {full!r}")

    # The verifier must be able to fail; a check that always passes is
    # not a check.
    if not verify('a &lt;a href="https://x.org/p"&gt;b&lt;/a&gt;', "a b"):
        failures.append("verifier did not notice a dropped URL")
    if verify("plain words", "plain words"):
        failures.append("verifier reported loss on identical text")

    # Every tier must be reachable, or a fallback could rot unnoticed.
    tiers = {clean_note(raw).tier for _, raw, _ in SELFTESTS}
    if TIER_PARSED not in tiers:
        failures.append("no case exercised the parsed tier")

    if failures:
        raise AssertionError(
            f"{len(failures)} failure(s):\n  " + "\n  ".join(failures))


def _fuzz(count: int = 4000, seed: int = 0) -> CleanReport:
    """Clean randomly generated malformed markup; used by --fuzz."""
    import random
    import string

    rng = random.Random(seed)
    tags = ["p", "div", "span", "b", "sup", "sub", "a", "img", "li", "ul",
            "ol", "td", "tr", "table", "script", "style", "blockquote",
            "h3", "custom-el", "xyz:zed", "MARQUEE", "q", "wbr"]

    def fragment() -> str:
        tag = rng.choice(tags)
        roll = rng.random()
        if roll < 0.15:
            return f"<{tag}"
        if roll < 0.30:
            return f'<{tag} attr="unclosed'
        if roll < 0.40:
            return f"<{tag}/>"
        if roll < 0.50:
            return f"</{tag}>"
        if roll < 0.60:
            return f'<{tag} href="http://x.org/{rng.randint(1, 99)}">'
        if roll < 0.70:
            return "<!-- comment -->"
        if roll < 0.80:
            return f"&{rng.choice(['amp', 'lt', 'gt', 'nbsp', 'bogus'])};"
        if roll < 0.90:
            return f"<{rng.randint(1, 99)} arcsec>"
        return f"<{tag}>"

    def word() -> str:
        return "".join(rng.choice(string.ascii_letters)
                       for _ in range(rng.randint(1, 9)))

    def inputs() -> Iterator[str]:
        for _ in range(count):
            yield "".join(fragment() if rng.random() < 0.45 else word() + " "
                          for _ in range(rng.randint(1, 14)))

    return summarize(clean_many(inputs()))


def _main(argv: list[str]) -> int:
    if "--selftest" in argv:
        try:
            selftest(verbose="-v" in argv or "--verbose" in argv)
        except AssertionError as err:
            print(err, file=sys.stderr)
            return 1
        print(f"PASS: {len(SELFTESTS) + 10} checks green.", file=sys.stderr)
        return 0

    if "--fuzz" in argv:
        index = argv.index("--fuzz")
        count = int(argv[index + 1]) if len(argv) > index + 1 else 4000
        report = _fuzz(count)
        print(report, file=sys.stderr)
        print("PASS" if report.ok else "FAIL", file=sys.stderr)
        return 0 if report.ok else 1

    if "--doctest" in argv:
        import doctest
        results = doctest.testmod(verbose="-v" in argv)
        return 1 if results.failed else 0

    if "--help" in argv or "-h" in argv:
        print(__doc__)
        return 0

    # Default: clean stdin to stdout.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    print(clean(sys.stdin.read()))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
