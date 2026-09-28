"""
maintainers.py -- joins the spellings of one maintainer.

The same maintainer is written several ways in this catalog: "Kristan
Morgan" and "KRISTAN MORGAN", "ANDREY SAVTCHENKO" and "ANDREY SAVTCHENKO,
PH. D", "Parnchai Sawaengphokhai" and "Sawaengphokhai Parnchai". Two
spellings are one maintainer when they have the same words once these are
ignored:

    case, punctuation, spacing and word order
    the degree Ph.D, however it is written (PhD, Ph.D., PH. D, Ph D)
    the honorifics Dr, Mr, Ms, Mrs and Prof, as whole words

Every other word counts, so names differing by a middle name or an initial
("Lola Olsen", "Lola M. Olsen"; "Mama Pucci", "Mama D. Pucci") stay apart,
and so do names differing by Jr. or Sr., which can tell a father from a son.
Merging those would need a rule someone would have to choose, and joining two
people is worse than keeping one person's spellings apart.

Joined spellings are written in "John Doe" form.

This matters beyond looks: 030 will stratify its samples by maintainer, so a
maintainer split across two spellings would count as two groups, and 080
would make two nodes for one person.

Adapted from to_be_reshaped/build_inputs.py (group_key, group_display,
join_groups). That version dropped the single words "ph" and "d" wherever
they appeared, to remove "Ph. D", so a middle initial D was ignored too
("John D. Smith" matched "John Smith"), and it ignored Jr. and Sr. The
degree is now removed as one unit, and selftest() checks both cases.
"""
from __future__ import annotations

import collections
import re

#: Used when a record's maintainer is missing or blank. "undefined" is also a
#: literal maintainer value in this catalog, so blanks join that group rather
#: than forming a second one that means the same thing.
UNKNOWN = "undefined"

#: The degree Ph.D, however it is punctuated or spaced, as one unit. The "ph"
#: must start a word, so "Joseph D." or "Ralph D." are not read as a degree.
DEGREE = re.compile(r"\bph\.?\s*d\b\.?", re.IGNORECASE)

#: Honorifics ignored when comparing names, as whole words only.
HONORIFICS = {"dr", "mr", "ms", "mrs", "prof"}


def as_harvested(value) -> str:
    """The maintainer as the catalog gives it, with runs of spaces (and any
    other whitespace) inside it collapsed to one space and none at either
    end, so "Parnchai  Sawaengphokhai" is not a spelling of its own. Blanks
    become UNKNOWN."""
    return " ".join(str(value or "").split()) or UNKNOWN


def _name_words(name: str) -> list[str]:
    """The words of a name, as written, without the degree and honorifics."""
    words = re.split(r"[\s,]+", DEGREE.sub(" ", name).strip())
    return [w for w in words
            if w and re.sub(r"[^a-z0-9]", "", w.lower()) not in HONORIFICS]


def name_key(name: str) -> str:
    """What two spellings of one maintainer have in common: the words,
    lowercased and without punctuation, the degree and honorifics, SORTED so
    that a swapped first and last name still matches."""
    words = [re.sub(r"[^a-z0-9]", "", w.lower()) for w in _name_words(name)]
    return " ".join(sorted(w for w in words if w))


def display_name(spellings: collections.Counter) -> str:
    """The name for a set of joined spellings, in "John Doe" form: degree
    and honorifics dropped, and a name written in capitals title-cased. A
    spelling that is already mixed case is preferred and left alone, so
    acronyms such as NASA survive. Which spelling that is comes down to
    record counts, so for a name whose word order varies the name follows
    the majority."""
    ranked = spellings.most_common()
    name = next((n for n, _ in ranked if not n.isupper()), ranked[0][0])
    name = " ".join(_name_words(name)).strip(" ,.")
    return name.title() if name.isupper() else name


def join(names: list[str]) -> tuple[dict, list]:
    """For a list of harvested names (one per record), returns
    ({harvested name: joined name}, joins). joins has one entry per
    maintainer written more than one way, most records first:
    {"name", "spellings", "records"}. A maintainer written only one way
    keeps its spelling untouched."""
    spellings: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for name in names:
        spellings[name_key(name)][name] += 1

    mapping, joins = {}, []
    for counts in spellings.values():
        if len(counts) == 1:
            only = next(iter(counts))
            mapping[only] = only
            continue
        joined = display_name(counts)
        for spelling in counts:
            mapping[spelling] = joined
        joins.append({"name": joined, "spellings": sorted(counts),
                      "records": sum(counts.values())})
    joins.sort(key=lambda j: -j["records"])
    return mapping, joins


# --------------------------------------------------------------------------
# self-test
# --------------------------------------------------------------------------

#: (spelling, spelling, should they be one maintainer?). Every entry is a
#: rule the joining must keep; add to it rather than trusting a change by eye.
SELFTESTS = [
    ("KRISTAN MORGAN", "Kristan Morgan", True),                  # case
    ("Parnchai Sawaengphokhai", "Sawaengphokhai Parnchai", True),  # word order
    ("ANDREY SAVTCHENKO", "ANDREY SAVTCHENKO, PH. D", True),      # degree, spaced
    ("Jane Doe", "Jane Doe, PhD", True),                          # degree, one word
    ("Jane Doe", "Jane Doe Ph.D.", True),                         # degree, dotted
    ("Jane Doe", "Dr. Jane Doe", True),                           # honorific
    ("Jane Doe", "Prof Jane Doe", True),                          # honorific
    ("Mama Pucci", "Mama D. Pucci", False),                       # initial D is a name
    ("Lola Olsen", "Lola M. Olsen", False),                       # any initial is a name
    ("John Smith", "John Smith Jr.", False),                      # Jr. tells people apart
    ("John Smith", "John Smith Sr", False),                       # Sr. tells people apart
    ("Joseph Doe", "Joseph D. Doe", False),                       # "ph" inside a word
    ("Ralph D. Lorenz", "Ralph Lorenz", False),                   # "ph" then an initial
    ("Dr. Jane Doe", "Dr. John Doe", False),                      # honorific isn't the name
]

#: (spellings, the joined name expected).
DISPLAY_TESTS = [
    (["ANDREY SAVTCHENKO", "ANDREY SAVTCHENKO, PH. D"], "Andrey Savtchenko"),
    (["DR. PAUL STACKHOUSE", "Dr. Paul Stackhouse", "Paul Stackhouse"], "Paul Stackhouse"),
    (["JOHN D. SMITH", "John D. Smith"], "John D. Smith"),
]


def selftest() -> None:
    """Check every rule above; raise AssertionError listing failures."""
    failures = []
    for a, b, same in SELFTESTS:
        if (name_key(a) == name_key(b)) != same:
            failures.append(f"{a!r} and {b!r} should {'' if same else 'not '}be one maintainer "
                            f"(keys {name_key(a)!r}, {name_key(b)!r})")
    for spellings, expected in DISPLAY_TESTS:
        mapping, _ = join(spellings)
        got = {mapping[s] for s in spellings}
        if got != {expected}:
            failures.append(f"{spellings} should be joined as {expected!r}, got {sorted(got)}")
    if failures:
        raise AssertionError(f"{len(failures)} failure(s):\n  " + "\n  ".join(failures))


if __name__ == "__main__":
    selftest()
    print(f"PASS: {len(SELFTESTS) + len(DISPLAY_TESTS)} checks green.")
