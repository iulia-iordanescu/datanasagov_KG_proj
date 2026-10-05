"""
readings.py -- each metric read as plain sentences, with the run's own
numbers in them, for the report (see the guide's section *Reading the
metrics*).

A metric is a ratio; these bullets say what it counts, in this run's terms:
what the triples are and where they came from (once per part, in "Where
these numbers come from"), then, per metric, the counts behind it, how to
read it as a chance and for the knowledge graph where that holds, how sure
it is (the margin of error, or why there is none), and what it assumes. A
metric gets only the readings that hold for it.
"""
from __future__ import annotations

import collections

import stats


def pct(x) -> str:
    """A share as a whole percentage: "50%", or "–" for none."""
    return "–" if x is None else f"{100 * x:.0f}%"


def _of(k: int, n: int) -> str:
    """k, with its share of n: "4 (50%)" (the sentence names n)."""
    return f"{k} ({pct(k / n) if n else '–'})"


def _sure(n: dict, metric: dict, what: str) -> str:
    """How sure a metric is: its margin of error, or why there is none."""
    if metric is None or metric.get("value") is None:
        return f"- Not computed: nothing to count it over."
    if metric.get("low") is None:
        return (f"- Computed over {n['records']} record(s): too few for a margin of error (it needs "
                f"{stats.MIN_RECORDS}), so {what} could easily be quite different over the whole catalog.")
    return (f"- For the whole catalog, {what} is likely between {pct(metric['low'])} and {pct(metric['high'])} "
            f"(the margin of error: the middle 95% of {stats.RESHUFFLES:,} redraws of these {n['records']} records).")


def where_from(part: str, recs: list, evaluated, names, looks) -> list:
    """Once per part: what these numbers were computed from."""
    made = evaluated.extraction_made
    schema = evaluated.schema_used.get("made", {})
    additions = [e for kind in ("entity_classes", "predicates") for e in evaluated.schema_used.get(kind, [])
                 if e.get("from") == "additions"]
    from_tuning = [e for e in additions if "ground truth tuning" in (e.get("source") or "").lower()]
    positions = sorted(r["position"] for r in recs if r.get("position") is not None)
    review = {k: sum(r["compared"]["partial_review"][k] for r in recs) for k in ("unreviewed", "rejected")}
    out = ["#### Where these numbers come from", "",
           f"- **Extracted triples:** the triples extraction kept in run `{made.get('run_id', 'unknown: not in the details file of extraction')}` "
           f"(model `{made.get('model', 'unknown')}`), in `060_extract/extracted_triples.csv`.",
           f"- **Extraction's schema (the current schema):** `{schema.get('schema', 'unknown')}`, plus "
           f"`{schema.get('additions', 'annotations/schema_additions.txt')}` ({len(additions)} addition(s)).",
           ("- **Schema additions learned from tuning records:** "
            + "; ".join(f"{e['name']} ({e.get('source')})" for e in from_tuning) + ". They come from the very records "
            "being evaluated, so they help here more surely than on records the pipeline hasn't seen."
            if from_tuning else "- **Schema additions learned from tuning records:** none."),
           "- **Names:** extraction's names translated into the ground truth vocabulary through "
           "`annotations/name_mapping.csv`.",
           f"- **Ground truth:** `annotations/ground_truth/`, the {len(recs)} finished {part} record(s) of the fair "
           f"part (pool positions {', '.join(f'#{p}' for p in positions) or '–'}).",
           ("- **Partial pairs:** " + (f"{review['unreviewed']} not reviewed yet; {review['rejected']} ruled out by "
                                        f"your review (counted as extracted only and ground truth only)."
                                        if part == "tuning" else
                                        "never reviewed for the held-out part (that would mean looking at it).")),
           ]
    if part == "held-out":
        out.append(f"- **Held-out looks:** the held-out numbers have been shown {looks} time(s), this run "
                   f"included (`annotations/held_out_looks.csv`). A change made after seeing them lets these "
                   f"records influence the pipeline, so they no longer measure records it was never adjusted to.")
    out += ["- **The full recipe** of each run (code version, settings, prompts with their fingerprints, inputs "
            "and the runs that made them): that run's report in `outputs/reports/`, sections Run, Settings, "
            "Prompts and Inputs.", ""]
    return out


def readings(part: str, n: dict, recs: list, evaluated, names, looks, confusion: dict) -> list:
    E, G = n["extracted"], n["gt_triples"]
    ex, pa = n["exact"], n["partial"]
    out = [f"### Reading the metrics: {part} part", ""] + where_from(part, recs, evaluated, names, looks)

    # precision
    out += [f"#### Precision: {pct(ex['precision']['value'])} (exact pairs), {pct(pa['precision']['value'])} "
            f"(exact and partial pairs)", "",
            f"- Of the {E} triples extraction kept for these records, {_of(ex['pairs'], E)} form exact pairs with "
            f"ground truth triples; counting partial pairs too, {_of(pa['pairs'], E)}.",
            f"- Read as a chance: a triple extraction keeps for such a record has a {pct(ex['precision']['value'])} "
            f"chance of forming an exact pair ({pct(pa['precision']['value'])} counting partial pairs).",
            f"- In a knowledge graph built from these triples, {E - ex['pairs']} of the {E} statements "
            f"({pct((E - ex['pairs']) / E) if E else '–'}) would have no "
            f"exact counterpart in the ground truth: a wrong subject, predicate or object, or a fact the text "
            f"doesn't state ({E - pa['pairs']} counting partial pairs as right).",
            _sure(n, ex["precision"], "exact precision"),
            "- Assumes the ground truth lists every fact these records state: a true triple missing from it "
            "counts against precision.", ""]

    # recall
    out += [f"#### Recall: {pct(ex['recall']['value'])} (exact pairs), {pct(pa['recall']['value'])} "
            f"(exact and partial pairs)", "",
            f"- Of the {G} ground truth triples, {_of(ex['pairs'], G)} have an exact pair; counting partial pairs "
            f"too, {_of(pa['pairs'], G)}.",
            f"- Read as a chance: a ground truth triple has a {pct(ex['recall']['value'])} chance of being found "
            f"as an exact pair ({pct(pa['recall']['value'])} counting partial pairs).",
            f"- A knowledge graph built from extraction's triples would lack {G - ex['pairs']} of the {G} "
            f"facts ({pct((G - ex['pairs']) / G) if G else '–'}) these records state, per the ground truth ({G - pa['pairs']} counting partial pairs as found).",
            _sure(n, ex["recall"], "exact recall"),
            "- Assumes the ground truth lists every fact these records state: a fact missing from it is not "
            "counted at all.", ""]

    # strict
    out += [f"#### Strict precision and strict recall: {pct(ex['strict_precision']['value'])} and "
            f"{pct(ex['strict_recall']['value'])} (exact pairs)", "",
            f"- The same, counting only strict pairs: pairs whose two entity classes also agree, after translation. "
            f"{ex['strict_pairs']} of the {ex['pairs']} exact pairs are strict ({pa['strict_pairs']} of the "
            f"{pa['pairs']} counting partial pairs).",
            f"- Strict precision: {ex['strict_pairs']} of the {E} extracted triples "
            f"({pct(ex['strict_precision']['value'])}); strict recall: {ex['strict_pairs']} of the {G} ground "
            f"truth triples ({pct(ex['strict_recall']['value'])}).",
            "- For a knowledge graph: a strict pair is a statement whose two nodes would also get the right "
            "entity classes (node labels).",
            _sure(n, ex["strict_precision"], "exact strict precision"), ""]

    # entity-class accuracy
    shared = [f"{', '.join(v)} (current schema) --> {k} (ground truth vocabulary)"
              for kind in ("entity class",) for k, v in names.merged.get(kind, {}).items()]
    out += [f"#### Entity-class accuracy: {pct(ex['entity_class_accuracy']['value'])} (exact pairs), "
            f"{pct(pa['entity_class_accuracy']['value'])} (exact and partial pairs)", "",
            f"- Of the {ex['pairs']} exact pairs, {_of(ex['strict_pairs'], ex['pairs'])} also have both entity "
            f"classes right; of the {pa['pairs']} pairs counting partial ones, {_of(pa['strict_pairs'], pa['pairs'])}.",
            f"- Read as a chance: when extraction gets a triple right, its two entity classes are both right with "
            f"a {pct(ex['entity_class_accuracy']['value'])} chance.",
            _sure(n, ex["entity_class_accuracy"], "exact entity-class accuracy")]
    if shared:
        out.append("- Can't see mix-ups between current-schema names that translate to the same ground truth name: "
                   + "; ".join(shared) + ".")
    out.append("")

    # schema ceiling and recall within reach
    W = n["within_reach"]
    out += [f"#### Schema ceiling: {pct(n['schema_ceiling']['value'])}", "",
            f"- Of the {G} ground truth triples, {_of(W, G)} are within reach: their predicate and both entity "
            f"classes have a counterpart in the current schema, through the translation table.",
            f"- It's the best recall any extraction could get with this schema and translation table: "
            f"{G - W} ground truth triple(s) say something the schema has no names for.",
            _sure(n, n["schema_ceiling"], "the schema ceiling"), ""]
    out += [f"#### Recall within reach: {pct(ex['recall_within_reach']['value'])} (exact pairs), "
            f"{pct(pa['recall_within_reach']['value'])} (exact and partial pairs)", "",
            f"- Of the {W} ground truth triples within reach, {_of(ex['pairs_within_reach'], W)} have an exact "
            f"pair; counting partial pairs too, {_of(pa['pairs_within_reach'], W)}.",
            "- Read with the schema ceiling: a low ceiling points at the schema; a low recall within reach points "
            "at extraction (its model, prompt or checks), since those triples could have been found.",
            _sure(n, ex["recall_within_reach"], "exact recall within reach"), ""]

    # describes
    d = n["describes"]
    truths = collections.Counter()
    for (t, _), k in confusion.items():
        truths[t] += k
    common = truths.most_common(1)[0][0] if truths else None
    right = round((d["accuracy"]["value"] or 0) * d["records"]) if d["accuracy"]["value"] is not None else 0
    out += [f"#### What each record describes: {pct(d['accuracy']['value'])}", "",
            f"- Of the {d['records']} record(s) whose ground truth names what the record describes (the DESCRIBES "
            f"row's entity class), extraction named the same entity class for {_of(right, d['records'])}.",
            (f"- Always guessing the most common kind, `{common}` (ground truth vocabulary), would get "
             f"{pct(d['majority_baseline'])}: the accuracy means something only when it's clearly above that."
             if common else "- No baseline: no record names what it describes."),
            f"- Averaged per kind ({len(truths)} kind(s)): {pct(d['per_kind_average'])}, so a rare kind counts as "
            f"much as a common one.",
            _sure(n, d["accuracy"], "this accuracy"), ""]
    return out
