# What the metrics count: pairs

Part of [Evaluation metrics](../metrics.md), which explains the notation and lists every metric.

## <ins>Definition</ins>

A **pair** is one [extracted triple](../../docs/terminology.md#6-extracting-with-a-schema-step-060) and one [ground truth triple](../../docs/terminology.md#4-ground-truth-and-samples) of the same [record](../../docs/terminology.md#1-records-and-their-text) that evaluation takes to state the same [fact](../../docs/terminology.md#2-triples), once the extracted triple's [predicate](../../docs/terminology.md#3-schemas), [subject class](../../docs/terminology.md#2-triples) and [object class](../../docs/terminology.md#2-triples) are translated into the [ground truth vocabulary](../../docs/terminology.md#7-evaluating-extraction-step-070) (through the [translation table](../../docs/terminology.md#7-evaluating-extraction-step-070), [`annotations/component_class_mapping.csv`](../../annotations/component_class_mapping.csv)).

There are two **pair levels**, exact and partial, that define when an extracted triple (after its [component classes](../../docs/terminology.md#3-schemas) are translated) and a ground truth triple of the same record count as stating the same fact.

- They can form an **exact pair** when all three hold:
  - the same predicate;
  - the same [subject instance](../../docs/terminology.md#2-triples), once [evened out](../../docs/terminology.md#2-triples);
  - the same [object instance](../../docs/terminology.md#2-triples), once evened out.
- They can form a **partial pair** when neither has an exact partner and all three hold:
  - the same predicate;
  - (the same subject instance, once evened out) ∨ (one subject instance appears inside the other as whole words, either way round);
  - (the same object instance, once evened out) ∨ (one object instance appears inside the other as whole words, either way round).

Strict is an extra condition on a pair at either level: a **strict pair** is an exact or partial pair with (the same subject classes) ∧ (the same object classes).

So every pair is exactly one of these four:

| | strict ((same subject classes) ∧ (same object classes)) | not strict |
|---|---|---|
| exact pair | exact pairs ∩ strict pairs | exact pairs, not strict |
| partial pair | partial pairs ∩ strict pairs | partial pairs, not strict |

All pairs = exact pairs ∪ partial pairs (no pair is both). Strict pairs are some of each.

Meeting a pair level's requirements makes two such aforementioned [classed triples](../../docs/terminology.md#2-triples) able to pair, not paired: each extracted triple and each ground truth triple of a record has at most one partner, always from the record's other set (its [set of extracted triples](../../docs/terminology.md#6-extracting-with-a-schema-step-060) or its [set of ground truth triples](../../docs/terminology.md#4-ground-truth-and-samples)). A **set of pairs** is one choice, within those rules, of which extracted triple pairs with which ground truth triple in a record; a record often has several possible sets of pairs. Evaluation finds the largest possible set of exact pairs, then, among the classed triples left, the largest possible set of partial pairs: partners are picked so that as many classed triples as possible get one (a *maximum matching*). When several sets of pairs are equally large (have as many pairs), evaluation takes one with the most strict pairs. Examples: [Example](#example), *The largest set of pairs* and *Equally large sets of pairs*.

A classed triple left without a partner is **extracted only** (an extracted triple) or **ground truth only** (a ground truth triple).

Precision and recall are computed from pairs. Each has versions that differ in which pairs they count (by pair level and strictness: see [precision](precision.md) and [recall](recall.md)). An extracted triple in a pair that a version of precision counts is called [*correct*](precision.md); a ground truth triple in a pair that a version of recall counts is called [*found*](recall.md).

## <ins>Assumes and can't see</ins>

- Containment can be fooled: "MODIS" is inside "MODIS Terra", a different instrument. On tuning records you review partial pairs in the [annotation tool](../../docs/terminology.md#4-ground-truth-and-samples) (*Partial pairs*); an extracted triple and a ground truth triple marked "not the same fact" are never paired. Held-out records' partial pairs are never reviewed (that would mean looking at them).
- Two component classes of the [current schema](../../docs/terminology.md#6-extracting-with-a-schema-step-060) that translate to one component class of the ground truth vocabulary can't be told apart.

Worked example: [Pairs: example](#example). Sources: [Pairs: sources](#sources).

## Example

One [record](../../docs/terminology.md#1-records-and-their-text). Its [ground truth triples](../../docs/terminology.md#4-ground-truth-and-samples):

| | Subject instance (subject class) | Predicate | Object instance (object class) |
|---|---|---|---|
| G1 | MODIS (Instrument) | ABOARD | Aqua (Spacecraft) |
| G2 | AIRS (Instrument) | ABOARD | Aqua (Spacecraft) |
| G3 | MODIS Snow Cover (Dataset) | ACQUIRED_BY | MODIS (Instrument) |
| G4 | MODIS Snow Cover (Dataset) | HAS_TIME_SPAN | 2002–2023 (TimeSpan) |
| G5 | CERES (Instrument) | ABOARD | Aqua (Spacecraft) |

Its [extracted triples](../../docs/terminology.md#6-extracting-with-a-schema-step-060), after translation, and what each becomes:

| | Subject instance (subject class) | Predicate | Object instance (object class) | Outcome |
|---|---|---|---|---|
| E1 | the MODIS (Instrument) | ABOARD | Aqua (Spacecraft) | exact pair with G1 ("the" is ignored); strict |
| E2 | AIRS (Dataset) | ABOARD | Aqua (Spacecraft) | exact pair with G2; not strict ([subject class](../../docs/terminology.md#2-triples) Dataset, not Instrument) |
| E3 | MODIS Snow Cover 5-Min L2 Swath (Dataset) | ACQUIRED_BY | Moderate Resolution Imaging Spectroradiometer (MODIS) (Instrument) | partial pair with G3 ("MODIS Snow Cover" is inside the [subject instance](../../docs/terminology.md#2-triples), "MODIS" inside the [object instance](../../docs/terminology.md#2-triples)); strict |
| E4 | MODIS Snow Cover (Dataset) | HAS_TIME_SPAN | the period 2002–2023 (Dataset) | partial pair with G4 ("2002–2023" is inside the object instance); not strict ([object class](../../docs/terminology.md#2-triples) Dataset, not TimeSpan) |
| E5 | MODIS (Instrument) | ABOARD | Terra (Spacecraft) | extracted only: no ground truth triple has the [object](../../docs/terminology.md#2-triples) Terra |
| E6 | Moderate Resolution Imaging Spectroradiometer (MODIS) (Instrument) | ABOARD | Aqua (Spacecraft) | extracted only: it would form a partial pair with G1, but G1 already has an exact partner, E1, and a [classed triple](../../docs/terminology.md#2-triples) has at most one |

And G5 (CERES ABOARD Aqua) has no partner: ground truth only, a missed [fact](../../docs/terminology.md#2-triples).

In all: 6 extracted triples, 5 ground truth triples; 2 exact pairs (E1–G1 strict, E2–G2 not); 2 partial pairs (E3–G3 strict, E4–G4 not); so 2 strict pairs, one at each pair level; 2 extracted only (E5, E6); 1 ground truth only (G5).

*The largest set of pairs.* At the partial level, the [ground truth](../../docs/terminology.md#4-ground-truth-and-samples) has "MODIS instrument suite ABOARD Aqua" and "Terra MODIS ABOARD Aqua"; extraction gives "MODIS ABOARD Aqua" and "MODIS instrument ABOARD Aqua". "MODIS instrument suite ABOARD Aqua" could pair with either extracted triple; "Terra MODIS ABOARD Aqua" only with "MODIS ABOARD Aqua". Taking each classed triple's first possible partner, the first ground truth triple takes "MODIS ABOARD Aqua", and the second is left without one: 1 pair. Evaluation instead pairs "MODIS instrument suite ABOARD Aqua" with "MODIS instrument ABOARD Aqua", and "Terra MODIS ABOARD Aqua" with "MODIS ABOARD Aqua": 2 pairs.

*Equally large sets of pairs.* A record's ground truth has G1, "MODIS" (Instrument) ABOARD "Aqua" (Spacecraft). Extraction gives E1, "MODIS" (Dataset) ABOARD "Aqua" (Spacecraft), then E2, "MODIS" (Instrument) ABOARD "Aqua" (Spacecraft). Each can form an exact pair with G1, which can have only one partner, so the record has two possible sets of pairs: {E1–G1}, leaving E2 extracted only, and {E2–G1}, leaving E1 extracted only. Both have 1 pair: they are equally large. Evaluation takes {E2–G1}, whose pair is strict. Which of E1 and E2 comes first in the file doesn't matter.

## Sources

- *Exact* and *partial*: the WebNLG 2020 challenge's evaluation of text-to-triples extraction (Castro Ferreira et al., 2020, [paper](https://aclanthology.org/2020.webnlg-1.7.pdf)). Two differences. WebNLG scores a triple's subject, predicate, and object each separately, not whole triples, and averages per text, not over all triples, so its numbers aren't directly comparable with ours. And ours is stricter on partial: whole words, not any overlap.
- Credit: here a partial pair counts as fully right. The SemEval-2013 scoring convention ([nervaluate](https://github.com/MantisAI/nervaluate)) gives a partial match half credit: partial [precision](precision.md) = (exact + 0.5 × partial) ÷ extracted. Full credit fits our meaning of a partial pair, the same [fact](../../docs/terminology.md#2-triples) named differently (on tuning [records](../../docs/terminology.md#1-records-and-their-text), confirmed by your review), but our partial numbers are higher than that convention's and not directly comparable with published partial scores. That convention's number is the average of our two levels: (exact ÷ extracted + (exact + partial) ÷ extracted) ÷ 2 = (exact + 0.5 × partial) ÷ extracted; for recall, the same with ground truth triples in place of [extracted triples](../../docs/terminology.md#6-extracting-with-a-schema-step-060).
- *Strict*, meaning right relation and right entity types: the "Strict" [setting](../../docs/terminology.md#8-the-pipeline) of end-to-end relation extraction (Bekoulis et al., 2018, as described by Taillé et al., 2020, [paper](https://aclanthology.org/2020.emnlp-main.301/)). WebNLG's "strict" means something else (the element's role must match), so it isn't the source here.
- At most one partner per [classed triple](../../docs/terminology.md#2-triples), largest set of pairs, and among those the most strict pairs: a minimum-cost maximum matching, each non-strict pair costing 1 and each strict pair 0 (successive shortest augmenting paths, `070_evaluate/070_evaluate_helpers/pairing.py`). Choosing among alignments by weight, not just by size, is how coreference's CEAF does it (Luo, 2005, [paper](https://aclanthology.org/H05-1004/): a maximum-weight bipartite matching, by the Kuhn–Munkres algorithm).
