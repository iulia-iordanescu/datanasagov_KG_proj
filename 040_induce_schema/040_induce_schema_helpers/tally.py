"""
tally.py -- after stage 8: the run's statistics, for the report, the manifest's headline and
induction_evidence.json (key "statistics"). Code only, no model.

  - triple instances per text: over every text, and per stratum (common/common_helpers/report.py, per_text_stats:
    the number of texts, minimum, maximum, mean, median, standard deviation, total, texts with none);
  - the texts that gave no triple instance (none listed, or none verified), each with its record id and stratum;
  - what each code check of stages 2 to 8 removed: triple instances (CHECKS), and the model's other answers it
    ignored (labels, merges, predicate splits, definitions; other_checks), with the texts a check removed wholly (every
    triple instance the text still had when the check ran);
  - the model calls that failed or were cut off, by stage (counted around each stage: moves.py, watch).

A check removes a text wholly when the text had at least one triple instance just before the check and none after
it: so a text whose model call failed (left out before any check) is in none of them, and is counted with the
failed calls instead.
"""
from __future__ import annotations

from common.report import per_text_stats

#: The code checks that remove triple instances, in the order they run: (stage, check, what it removes).
NOT_A_TRIPLE = "not a triple instance"
STATED_TWICE = "stated twice"
UNVERIFIED = "unverified"
NO_PATTERN = "a component instance without a final label"
NOT_IN_SCHEMA = "pattern not in the schema"
CHECKS = (
    (2, NOT_A_TRIPLE, "items of the reply with a slot empty, or not text or a number (dropped)"),
    (2, STATED_TWICE, "copies of a triple instance two text pieces of one text both state (one copy kept)"),
    (2, UNVERIFIED, "triple instances with no source text, or a source text not in the text (left out)"),
    (6, NO_PATTERN, "triple instances whose subject, predicate or object instance has no label: they count toward "
                    "no pattern (their labeled slots still count)"),
    (8, NOT_IN_SCHEMA, "triple instances whose pattern is deferred (not in the schema): the schema keeps no "
                       "evidence from them"),
)


def per_text(triples) -> dict:
    """{"listed": [count per text], "verified": [count per text]}, in the order of the texts: listed is every
    well-formed item once (verified + unverified)."""
    return {"listed": [len(t["triple_instances"]) + len(t["unverified"]) for t in triples.texts],
            "verified": [len(t["triple_instances"]) for t in triples.texts]}


def per_stratum(triples, strata: list) -> dict:
    """{stratum: [verified triple instances per text]}, in the order of strata (each stratum, even one with no
    text read)."""
    out = {s: [] for s in strata}
    for t in triples.texts:
        out.setdefault(t.get("stratum", ""), []).append(len(t["triple_instances"]))
    return out


def no_triple_instances(triples) -> dict:
    """{"listed": [...], "verified": [...]}: the texts whose replies listed no triple instance, and those with none
    verified (the first among them), each {"id", "stratum"}."""
    row = lambda t: {"id": t["id"], "stratum": t.get("stratum", "")}          # noqa: E731
    return {"listed": [row(t) for t in triples.texts if not t["triple_instances"] and not t["unverified"]],
            "verified": [row(t) for t in triples.texts if not t["triple_instances"]]}


def removed_by_checks(triples, counts, schema) -> list:
    """[{"stage", "check", "what", "removed", "texts_wholly": [{"id", "stratum"}]}], one per CHECKS entry: how
    many triple instances each removed, and the texts it removed wholly."""
    in_schema = {tuple(p["pattern"]) for p in schema.patterns}
    rows = {name: {"stage": stage, "check": name, "what": what, "removed": 0, "texts_wholly": []}
            for stage, name, what in CHECKS}
    for t in triples.texts:
        verified, unverified = len(t["triple_instances"]), len(t["unverified"])
        malformed, copies = t.get("malformed", 0), t.get("duplicates", 0)
        patterns = counts.pattern_of.get(t["id"], [])
        with_pattern = [p for p in patterns if p is not None]
        kept_in_schema = [p for p in with_pattern if p in in_schema]
        # (check, before it, after it): the triple instances the text had just before each check and just after
        steps = ((NOT_A_TRIPLE, malformed + copies + unverified + verified, copies + unverified + verified),
                 (STATED_TWICE, copies + unverified + verified, unverified + verified),
                 (UNVERIFIED, unverified + verified, verified),
                 (NO_PATTERN, verified, len(with_pattern)),
                 (NOT_IN_SCHEMA, len(with_pattern), len(kept_in_schema)))
        for name, before, after in steps:
            rows[name]["removed"] += before - after
            if before and not after:
                rows[name]["texts_wholly"].append({"id": t["id"], "stratum": t.get("stratum", "")})
    return list(rows.values())


def other_checks(labels, splits, definitions, schema, deferred_reasons: dict) -> list:
    """[{"stage", "check", "removed", "unit"}]: the model's other answers code ignored or left without effect."""
    refused_labels = sum(len(v) for v in labels.refused.values())
    unlabeled = sum(len(v) for v in labels.unlabeled.values()) - refused_labels
    rows = [(3, "no usable label after a second try (left unlabeled)", unlabeled, "component instances"),
            (3, "refused by the service, even asked alone (left unlabeled)", refused_labels, "component instances")]
    for code, words in (("into_not_a_label", "a merge into something that isn't a label"),
                        ("not_sent", "a label that wasn't sent"), ("merged_twice", "a label merged twice"),
                        ("cycle", "a merge that would close a cycle")):
        rows.append((4, words, sum(len(v.get(code, [])) for v in labels.merge_issues.values()), "merges"))
    for why in sorted({r["why"].split(":")[0] for r in splits.rejected}):
        rows.append((5, f"predicate split rejected: {why}", sum(r["why"].split(":")[0] == why for r in splits.rejected),
                     "predicate splits"))
    rows.append((5, "predicate split dropped by max_new_predicates", len(splits.dropped), "predicate splits"))
    rows.append((5, "refused by the service, even asked alone (not split)", len(splits.refused), "predicates"))
    rows.append((5, "predicate split undone by merging again (every part of its predicate ended in one predicate)",
                 len(splits.undone), "predicate splits"))
    for code, words in (("into_not_a_label", "a merge into something that isn't a label"),
                        ("not_sent", "a label that wasn't sent"), ("merged_twice", "a label merged twice"),
                        ("cycle", "a merge that would close a cycle"),
                        ("both_seen", "a merge of two predicates both there at stage 4")):
        rows.append((5, f"merging again: {words}", len(splits.merge_issues.get(code, [])), "merges"))
    rows.append((7, "a definition of a schema entry that wasn't sent (ignored)", len(definitions.unknown),
                 "definitions"))
    rows.append((7, "refused by the service, even asked alone (no definition)", len(definitions.refused),
                 "schema entries"))
    for code, words in deferred_reasons.items():
        rows.append((8, f"deferred: {words}", sum(d["reason_code"] == code for d in schema.deferred),
                     "schema entries"))
    return [{"stage": s, "check": c, "removed": n, "unit": u} for s, c, n, u in rows]


def stats(counts: list) -> dict:
    """per_text_stats, with the mean and standard deviation rounded to 2 decimals for the files."""
    s = per_text_stats(counts)
    return {k: (round(v, 2) if k in ("mean", "sd") and v is not None else v) for k, v in s.items()}
