# Entity-class accuracy

Part of [Evaluation metrics](../metrics.md), which explains the notation and lists every metric.

## <ins>Definition</ins>

Among the [pairs](pairs.md) counted, the proportion that are [strict](pairs.md): the proportion whose [subject classes](../../docs/terminology.md#2-triples) and [object classes](../../docs/terminology.md#2-triples) are also the same. Which pairs are counted depends on the version.

## <ins>Formula</ins>

Two versions.

| Version | Pairs counted | Formula |
|---|---|---|
| exact entity-class accuracy | [exact pairs](pairs.md) | \|exact pairs ∩ [strict pairs](pairs.md)\| ÷ \|exact pairs\| |
| partial entity-class accuracy | exact pairs ∪ [partial pairs](pairs.md) | \|(exact pairs ∪ partial pairs) ∩ strict pairs\| ÷ \|exact pairs ∪ partial pairs\| |

Each version is a number from 0 to 1; with no pairs counted across the [records](../../docs/terminology.md#1-records-and-their-text), it is undefined.

**How it ties to precision and recall.** At the same [pair level](pairs.md), [precision](precision.md) and strict precision divide by the same number of occurrences, and [recall](recall.md) and strict recall by the same number of [ground truth triples](../../docs/terminology.md#4-ground-truth-and-samples). So, whenever entity-class accuracy is defined:

- strict exact precision = exact precision × exact entity-class accuracy;
- strict exact recall = exact recall × exact entity-class accuracy;
- strict partial precision = partial precision × partial entity-class accuracy;
- strict partial recall = partial recall × partial entity-class accuracy.

These are exact, not approximate: for example, \|exact pairs ∩ strict pairs\| ÷ \|occurrences\| = (\|exact pairs\| ÷ \|occurrences\|) × (\|exact pairs ∩ strict pairs\| ÷ \|exact pairs\|).

## <ins>Interpretations</ins>

Let *a* be the value of one version of entity-class accuracy. It reads two ways: what was computed, on the evaluated records, and what it means for the [knowledge graph](../../docs/terminology.md#8-the-pipeline), for the whole catalog. Each item of the second is the counterpart of the item with the same number in the first.

**What was computed** (the evaluated records)

1. *a* is the proportion of the pairs counted that are strict, where the pairs counted are defined by the version (table above): of the [facts](../../docs/terminology.md#2-triples) extraction stated correctly, the proportion it also gave both [entity classes](../../docs/terminology.md#3-schemas) right.
2. *a* is the factor by which requiring the entity classes too lowers precision and recall, at the same pair level (*How it ties to precision and recall*, above). So 1 − *a* is the proportion of the correct occurrences that stop counting as correct, and equally the proportion of the found ground truth triples that stop counting as found, when the entity classes must also be the same.

**What it means for the knowledge graph** (the whole catalog, approximately)

Say the knowledge graph is built from the whole catalog's [extracted triples](../../docs/terminology.md#6-extracting-with-a-schema-step-060), one [edge](../../docs/terminology.md#8-the-pipeline) per extracted triple, each [node](../../docs/terminology.md#8-the-pipeline) with the entity class its extracted triple gives it. Then:

1. Of its correct edges (correct as the version defines it), approximately *a* would also have both nodes of the right entity class.
2. Of the facts the catalog's records state that the graph would hold, approximately *a* would be held with both nodes of the right entity class.

## <ins>Assumes and can't see</ins>

- Only pairs are judged. The subject class and object class of an occurrence or a ground truth triple without a partner aren't counted anywhere: an extracted triple that is wrong, or a repeat of a fact already paired, can have wrong entity classes without lowering *a*. Example: [Entity-class accuracy: example](#example), *A wrong entity class on a repeat*.
- When several sets of pairs at a pair level are equally large, evaluation takes one with the most strict pairs ([Pairs](pairs.md), *Definition*). Since those sets have the same number of pairs, that choice also gives the highest *a* any of them gives: when it is unclear which occurrence a ground truth triple pairs with, *a* gives extraction the benefit of the doubt.
- Two [component classes](../../docs/terminology.md#3-schemas) of the [current schema](../../docs/terminology.md#6-extracting-with-a-schema-step-060) that translate to one component class of the [ground truth vocabulary](../../docs/terminology.md#7-evaluating-extraction-step-070) look the same, so mixing them up isn't seen. The [report](../../docs/terminology.md#8-the-pipeline) lists such component classes (section *The translation table*).
- A wrong row of the [translation table](../../docs/terminology.md#7-evaluating-extraction-step-070) for an entity class lowers *a* even when extraction gave the right entity class. The report's *Component class mismatches* lists, for every pair whose entity classes differ, which entity class of the current schema met which entity class of the ground truth vocabulary, and how often (subject classes and object classes counted together): a frequent one is a row to check.
- *What it means for the knowledge graph* is approximate for two kinds of reason:
  - the [reasons every metric shares](approximately.md); the report measures one of them, sampling error, with *a*'s [margin of error](approximately.md#sampling-error);
  - two of its own, both about graph building ([step](../../docs/terminology.md#8-the-pipeline) 080, not built yet):
    - if it merges repeated extracted triples into one edge, the proportion of correct edges whose entity classes are right can differ from *a*, for the reason given under [Precision](precision.md), *Assumes and can't see*;
    - if it merges the nodes of one thing named in several extracted triples, and those extracted triples give it different entity classes, the merged node gets one entity class, chosen by a rule not decided yet, so it can be right in edges where *a* counted it wrong, or the reverse.

Worked example: [Entity-class accuracy: example](#example). Sources: [Entity-class accuracy: sources](#sources).

## Example

In each example, a [component class](../../docs/terminology.md#3-schemas) whose translation the example doesn't give is in both the [current schema](../../docs/terminology.md#6-extracting-with-a-schema-step-060) and the [ground truth vocabulary](../../docs/terminology.md#7-evaluating-extraction-step-070), and translates to itself.

*Both versions, and how they tie to precision and recall.* *Suppose:* a [record](../../docs/terminology.md#1-records-and-their-text)'s [text](../../docs/terminology.md#1-records-and-their-text) says that Aqua carries MODIS, AIRS, AMSR-E, and the Clouds and the Earth's Radiant Energy System (CERES). Its [ground truth](../../docs/terminology.md#4-ground-truth-and-samples) has 4 [ground truth triples](../../docs/terminology.md#4-ground-truth-and-samples):

| | Subject instance (subject class) | Predicate | Object instance (object class) |
|---|---|---|---|
| G1 | MODIS (Instrument) | ABOARD | Aqua (Spacecraft) |
| G2 | AIRS (Instrument) | ABOARD | Aqua (Spacecraft) |
| G3 | AMSR-E (Instrument) | ABOARD | Aqua (Spacecraft) |
| G4 | Clouds and the Earth's Radiant Energy System (CERES) (Instrument) | ABOARD | Aqua (Spacecraft) |

Extraction gives 5 [extracted triples](../../docs/terminology.md#6-extracting-with-a-schema-step-060), so the record has 5 occurrences:

| | Subject instance (subject class) | Predicate | Object instance (object class) | What evaluation does with it |
|---|---|---|---|---|
| E1 | MODIS (Instrument) | ABOARD | Aqua (Spacecraft) | an [exact pair](pairs.md) with G1, strict |
| E2 | AIRS (Instrument) | ABOARD | Aqua (Spacecraft) | an exact pair with G2, strict |
| E3 | AMSR-E (Dataset) | ABOARD | Aqua (Spacecraft) | an exact pair with G3, not strict: the [subject classes](../../docs/terminology.md#2-triples) differ |
| E4 | CERES (Instrument) | ABOARD | Aqua (Spacecraft) | a [partial pair](pairs.md) with G4 ("CERES" is inside G4's [subject instance](../../docs/terminology.md#2-triples), as a whole word), strict |
| E5 | MODIS (Instrument) | ABOARD | Terra (Spacecraft) | extracted only: the text doesn't say MODIS is aboard Terra |

*Then:*

- Exact entity-class accuracy = 2 strict exact pairs ÷ 3 exact pairs = 67%.
- Partial entity-class accuracy = 3 [strict pairs](pairs.md) ÷ 4 pairs (3 exact, 1 partial) = 75%.
- Exact precision = 3 ÷ 5 = 60%, and strict exact precision = 2 ÷ 5 = 40% = 60% × 67%.
- Exact recall = 3 ÷ 4 = 75%, and strict exact recall = 2 ÷ 4 = 50% = 75% × 67%.
- Partial precision = 4 ÷ 5 = 80%, and strict partial precision = 3 ÷ 5 = 60% = 80% × 75%.

*A wrong entity class on a repeat.* *Suppose:* a record's text says MODIS is aboard Aqua. Its ground truth has one ground truth triple, G1: "MODIS" (Instrument) ABOARD "Aqua" (Spacecraft). Extraction gives E1, "MODIS" (Instrument) ABOARD "Aqua" (Spacecraft), and E2, "the MODIS instrument" (Dataset) ABOARD "Aqua" (Spacecraft). *Then:* E1 and G1 form an exact pair, which is strict; E2 is eligible with G1 at the partial pair level, but G1 already has its partner, so E2 is extracted only. Exact entity-class accuracy = 1 ÷ 1 = 100%: E2's wrong subject class isn't counted, though precision counts E2 as not correct (1 ÷ 2 = 50%).

## Sources

No single standard name. End-to-end relation extraction reports two ways of scoring side by side (Taillé et al., 2020, "Let's Stop Incorrect Comparisons in End-to-end Relation Extraction!", EMNLP, [paper](https://aclanthology.org/2020.emnlp-main.301.pdf)): "Strict", which also requires both arguments' entity types to be right, and "Boundaries", which doesn't. Here, strict [pairs](pairs.md) are what "Strict" counts and all pairs are what "Boundaries" counts, so entity-class accuracy is the "Strict" score divided by the "Boundaries" score, at the same [pair level](pairs.md) (for precision and for recall alike, by *How it ties to precision and recall*, above).
