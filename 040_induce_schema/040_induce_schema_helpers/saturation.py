"""
saturation.py -- after stage 5: would more texts have added schema entries? Code only, no model.

THE CURVE. For k = 25, 50, ... texts, the number of schema entries (entity classes, predicates, patterns) that
would have reached min_support had 040 read only k of its texts, averaged over every order the texts could
have been read in. An entry found in n of the N texts reaches min_support = s among k texts drawn from them
with the hypergeometric probability

    P(X >= s),  X ~ Hypergeometric(N texts, n of them with the entry, k drawn)
              = sum over x from s to min(n, k) of  C(n, x) * C(N - n, k - x) / C(N, k)

and the expected number of entries is the sum of that probability over all entries. This is the exact average
over all orders: no random draw, no seed. What the last CHECKPOINT texts added (the expected number at N minus
that at N - CHECKPOINT) shows whether the sample has stopped finding entries: near 0, more texts of the same
kind would barely change the schema.

It is the sample-based species accumulation curve of ecology (Gotelli & Colwell 2011, "Estimating species
richness", in Magurran & McGill (eds), Biological Diversity, ch. 4): a text is a sample, an entry a species,
counted by incidence; here an entry counts only once it reaches min_support texts. As there, it speaks only for
what the sample was drawn from (here: 040's maintainers, 15 texts each by default), and it is descriptive: it
gives no verdict. It uses the labels 040 assigned with every text in view, so it is slightly optimistic: a
smaller sample might have labeled a few component instances differently.

THE BREADTH TABLE. For each entry that reached min_support, how many maintainers' texts it was found in: 1, 2,
or 3 or more. Entries found in one maintainer only are that maintainer's own vocabulary; many of them suggest
the maintainers 040 doesn't read have their own too.

Entries count here by support alone; the check stage may still leave out one the model judged too vague.
"""
from __future__ import annotations

from math import comb

#: Texts between two rows of the curve.
CHECKPOINT = 25
#: The three kinds of schema entry, as the report names them, and their list in count.Counts.
KINDS = (("entity classes", "entity_classes"), ("predicates", "predicates"), ("patterns", "patterns"))


def reaches(n_texts: int, found_in: int, drawn: int, min_support: int) -> float:
    """The probability that an entry found in found_in of n_texts texts is in at least min_support of drawn texts
    picked from them at random (the hypergeometric upper tail).

    >>> reaches(4, 2, 2, 2)                    # both of its 2 texts among 2 drawn from 4: 1 way in 6
    0.16666666666666666
    >>> reaches(150, 150, 2, 2), reaches(150, 1, 150, 2)
    (1.0, 0.0)
    """
    total = comb(n_texts, drawn)
    return sum(comb(found_in, x) * comb(n_texts - found_in, drawn - x)
               for x in range(min_support, min(found_in, drawn) + 1)) / total


def curve(counts, n_texts: int, min_support: int) -> dict:
    """{"texts": [25, 50, ..., n_texts], kind: [expected entries at each], "added_by_last": {kind: number}}."""
    points = list(range(CHECKPOINT, n_texts, CHECKPOINT)) + [n_texts] if n_texts else []
    out = {"texts": points}
    for name, attr in KINDS:
        supports = [e["support"] for e in getattr(counts, attr)]
        out[name] = [sum(reaches(n_texts, n, k, min_support) for n in supports) for k in points]
    last = max(n_texts - CHECKPOINT, 0)
    out["added_by_last"] = {name: (out[name][-1] - sum(reaches(n_texts, e["support"], last, min_support)
                                                        for e in getattr(counts, attr)))
                            if points else 0.0 for name, attr in KINDS}
    return out


def breadth(counts, min_support: int) -> dict:
    """{kind: {"1": entries, "2": entries, "3 or more": entries}}: entries that reached min_support, by how many
    maintainers' texts they were found in."""
    out = {}
    for name, attr in KINDS:
        row = {"1": 0, "2": 0, "3 or more": 0}
        for e in getattr(counts, attr):
            if e["support"] >= min_support:
                m = len(e["maintainers"])
                row["1" if m == 1 else "2" if m == 2 else "3 or more"] += 1
        out[name] = row
    return out


def report_lines(sat: dict, wide: dict, n_texts: int, min_support: int) -> list:
    """The report's subsection *Saturation*."""
    lines = ["### Saturation", "",
             f"Would more texts have added schema entries? For k texts, the number of schema entries that would have "
             f"reached min_support ({min_support} texts) had 040 read only k of its {n_texts}, averaged over every "
             f"order the texts could have been read in (an exact formula, no random draw; "
             f"040_induce_schema/040_induce_schema.md, *Saturation*). The last column is what the last {CHECKPOINT} "
             f"texts added: near 0, more texts of the same kind would barely change the schema.", ""]
    if not sat["texts"]:
        return lines + ["No text was read.", ""]
    lines += ["| Schema entries | " + " | ".join(f"{k} texts" for k in sat["texts"])
              + f" | Added by the last {CHECKPOINT} texts |",
              "|---|" + "---:|" * (len(sat["texts"]) + 1)]
    for name, _ in KINDS:
        lines.append(f"| {name} | " + " | ".join(f"{v:.1f}" for v in sat[name])
                     + f" | {sat['added_by_last'][name]:.1f} |")
    first = KINDS[0][0]
    lines += ["", f"*How to read a row, e.g. {first}:* had 040 read only {sat['texts'][0]} of its texts, about "
                  f"{sat[first][0]:.1f} {first} would have reached min_support, on average over every reading order; "
                  f"with all {n_texts}, {sat[first][-1]:.1f}. The last {CHECKPOINT} texts added "
                  f"{sat['added_by_last'][first]:.1f}. It speaks only for the maintainers 040 read, and is slightly "
                  f"optimistic (the labels were chosen with every text in view).", "",
              "Schema entries that reached min_support, by how many maintainers' texts they were found in (an entry "
              "found in one maintainer's texts only is that maintainer's own vocabulary; many such suggest the "
              "maintainers 040 doesn't read have their own too):", "",
              "| Schema entries | 1 maintainer | 2 maintainers | 3 or more |", "|---|---:|---:|---:|"]
    lines += [f"| {name} | {wide[name]['1']} | {wide[name]['2']} | {wide[name]['3 or more']} |" for name, _ in KINDS]
    return lines + [""]
