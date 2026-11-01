"""
common/common_helpers/latest.py -- which of several rows about one thing counts: the one rule, and it reports.

Several files a person writes may hold more than one row for one key: a verdict filed twice for one partial pair
(annotations/partial_pair_reviews.csv, by a hand edit), a reviewer's comments on one entry across emails
(helpers/review_page.py --read). "The last one wins" silently hid a conflict, and a comment emptied to withdraw it
kept the older one. latest_by_key is the rule every reader uses:

    chosen, problems = latest_by_key(rows, key, value, when=None, where=None)

    key(row)      what the row is about (the pair, the (reviewer, entry))
    value(row)    the row's verdict or comment, "" for a withdrawal
    when(row)     the row's timestamp (ISO 8601, any offset; "" or none: unknown), or None when rows carry none
    where(row)    how to name the row in a problem ("line 7", "file.eml")

With timestamps, the latest row wins, a withdrawal (empty value) like any other, so the key then has no row.
Without them, or when the latest rows share a timestamp, the rows must agree: the same value counts once; different
values are a conflict, reported in problems, and the key gets no row (nothing is chosen in the dark). A timestamp that
can't be read is a problem too, and its row is skipped. chosen: {key: row}, in the order the keys first appear.
"""
from __future__ import annotations

import datetime as dt


def parse_when(text) -> dt.datetime | None:
    """A timestamp as a comparable moment (ISO 8601, "Z" or an offset allowed, a space in place of T allowed; one
    with no offset is read as UTC), or None when it can't be read."""
    s = str(text or "").strip()
    if not s:
        return None
    try:
        moment = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None
    return moment if moment.tzinfo else moment.replace(tzinfo=dt.timezone.utc)


def latest_by_key(rows, key, value, when=None, where=None) -> tuple:
    """(chosen, problems): see the module."""
    where = where or (lambda r: f"row {rows.index(r) + 1}")
    groups, problems = {}, []
    for r in rows:
        k = key(r)
        if when is not None:
            moment = parse_when(when(r))
            if moment is None:
                problems.append(f"{where(r)}: its timestamp {str(when(r) or '')!r} can't be read (expected ISO 8601, "
                                f"e.g. 2026-10-24T10:00:00-04:00), so the row is skipped")
                continue
        else:
            moment = None
        groups.setdefault(k, []).append((moment, r))
    chosen = {}
    for k, group in groups.items():
        if when is not None:
            top = max(m for m, _ in group)
            group = [(m, r) for m, r in group if m == top]
        values = {" ".join(str(value(r) or "").split()).lower() for _, r in group}
        if len(values) > 1:
            problems.append("conflict: " + " and ".join(f"{where(r)} ({value(r)!r})" for _, r in group)
                            + (" are about the same thing with the same timestamp" if when is not None else
                               " are about the same thing") + ", and differ, so neither counts: keep one, delete the other")
            continue
        if not values.pop():
            continue                                     # withdrawn: the latest says nothing
        chosen[k] = group[-1][1]
    return chosen, problems
