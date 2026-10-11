# Recall within reach

Part of [Evaluation metrics](../metrics.md), which explains the notation and lists every metric.

## <ins>Definition</ins>

[Recall](recall.md), counted only over the [ground truth triples](../../docs/terminology.md#4-ground-truth-and-samples) [within reach](recall_upper_bound.md): those whose predicate ([ground truth vocabulary](../../docs/terminology.md#7-evaluating-extraction-step-070)) is one that some checked row of the [translation table](../../docs/terminology.md#7-evaluating-extraction-step-070) translates a predicate of the [current schema](../../docs/terminology.md#6-extracting-with-a-schema-step-060) to. Extraction writes only the current schema's predicates, so only these ground truth triples can ever be found. The strict versions count only the ground truth triples [within strict reach](recall_upper_bound.md) (their [subject class](../../docs/terminology.md#2-triples) and [object class](../../docs/terminology.md#2-triples) are also ones that some checked row translates to), and count one as found only in a [strict pair](pairs.md). What "found" means depends on the version.

## <ins>Formula</ins>

Four versions.

| Version | Ground truth triples counted | A ground truth triple counts as found when it… | Formula |
|---|---|---|---|
| exact recall within reach | within reach | forms an [exact pair](pairs.md) | \|exact pairs\| ÷ \|ground truth triples within reach\| |
| partial recall within reach | within reach | forms an exact or a [partial pair](pairs.md) | \|exact pairs ∪ partial pairs\| ÷ \|ground truth triples within reach\| |
| strict exact recall within reach | within strict reach | (forms an exact pair) ∧ (the pair is strict) | \|exact pairs ∩ strict pairs\| ÷ \|ground truth triples within strict reach\| |
| strict partial recall within reach | within strict reach | (forms an exact or a partial pair) ∧ (the pair is strict) | \|(exact pairs ∪ partial pairs) ∩ strict pairs\| ÷ \|ground truth triples within strict reach\| |

Each version is a number from 0 to 1; with no ground truth triples within reach (for the strict versions, within strict reach) across the [records](../../docs/terminology.md#1-records-and-their-text), it is undefined.

Every pair counted in a numerator has its ground truth triple in the denominator: a [pair](pairs.md)'s ground truth triple is always within reach, and a strict pair's always within strict reach ([Recall upper bound](recall_upper_bound.md), *Interpretations*, item 2). So, at the same [pair level](pairs.md), whenever the recall upper bound is above 0:

- recall within reach = recall ÷ [recall upper bound](recall_upper_bound.md);
- strict recall within reach = strict recall ÷ [strict recall upper bound](recall_upper_bound.md).

## <ins>Interpretations</ins>

Let *w* be the value of one version of recall within reach. It reads two ways: what was computed, on the evaluated records, and what it means for the [knowledge graph](../../docs/terminology.md#8-the-pipeline), for the whole catalog. Each item of the second is the counterpart of the item with the same number in the first.

**What was computed** (the evaluated records)

1. *w* is the proportion of the evaluated records' ground truth triples within reach (for the strict versions, within strict reach) that are found, where "found" is defined by the version (table above).
2. Recall splits into two factors: recall = recall upper bound × recall within reach (and strict recall = strict recall upper bound × strict recall within reach). The first is the schema's part (and the translation table's): which ground truth triples could be found at all. The second is extraction's part: how many of those it found.

**What it means for the knowledge graph** (the whole catalog, approximately)

Say the knowledge graph is built from the whole catalog's [extracted triples](../../docs/terminology.md#6-extracting-with-a-schema-step-060). Of the facts the catalog's records state that the current schema can express (each counted once per record that states it):

1. approximately *w* would be in the graph (for the strict versions: with both [nodes](../../docs/terminology.md#8-the-pipeline) of the right [entity class](../../docs/terminology.md#3-schemas));
2. approximately 1 − *w* would be missing from the graph although the current schema can express them: what a better extraction (its model, its prompt, or its checks) could still add with the same schema. A better extraction alone can bring recall at most up to the recall upper bound.

## <ins>Assumes and can't see</ins>

- Everything [recall](recall.md) assumes and can't see, since it is recall over fewer ground truth triples.
- Within reach means only that the schema has the [component classes](../../docs/terminology.md#3-schemas): a ground truth triple within reach can still be hard for the [model](../../docs/terminology.md#8-the-pipeline) to find in the [text](../../docs/terminology.md#1-records-and-their-text). So a low *w* points at extraction (its model, its prompt, or its checks), not at the schema.
- It depends on the translation table: a wrong row changes which ground truth triples are within reach, and which pairs are made, so it can move *w* up or down.
- It counts fewer ground truth triples than recall, so its [margin of error](approximately.md#sampling-error) is wider, the more so the lower the recall upper bound.
- *What it means for the knowledge graph* is approximate for the [reasons every metric shares](approximately.md); the [report](../../docs/terminology.md#8-the-pipeline) measures one of them, sampling error, with *w*'s margin of error.

Worked example: [Recall within reach: example](#example). Sources: [Recall within reach: sources](#sources).

## Example

*Suppose:* the [ground truth vocabulary](../../docs/terminology.md#7-evaluating-extraction-step-070) has the [predicates](../../docs/terminology.md#3-schemas) ABOARD, ACQUIRED_BY, and HAS_TIME_SPAN, and the [entity classes](../../docs/terminology.md#3-schemas) Instrument, Spacecraft, Dataset, and TimeSpan. The checked rows of the [translation table](../../docs/terminology.md#7-evaluating-extraction-step-070) translate [component classes](../../docs/terminology.md#3-schemas) of the [current schema](../../docs/terminology.md#6-extracting-with-a-schema-step-060) to ABOARD, ACQUIRED_BY, Instrument, Spacecraft, and TimeSpan (each to itself), but none translates to HAS_TIME_SPAN or Dataset. A [record](../../docs/terminology.md#1-records-and-their-text)'s [ground truth](../../docs/terminology.md#4-ground-truth-and-samples) has the 5 [ground truth triples](../../docs/terminology.md#4-ground-truth-and-samples) of [Recall upper bound: example](recall_upper_bound.md#example):

| | Subject instance (subject class) | Predicate | Object instance (object class) | Within reach | Within strict reach |
|---|---|---|---|---|---|
| G1 | MODIS (Instrument) | ABOARD | Aqua (Spacecraft) | yes | yes |
| G2 | AIRS (Instrument) | ABOARD | Aqua (Spacecraft) | yes | yes |
| G3 | MODIS Snow Cover (Dataset) | ACQUIRED_BY | MODIS (Instrument) | yes | no |
| G4 | MODIS Snow Cover (Dataset) | HAS_TIME_SPAN | 2002–2023 (TimeSpan) | no | no |
| G5 | CERES (Instrument) | ABOARD | Aqua (Spacecraft) | yes | yes |

Extraction gives 2 [extracted triples](../../docs/terminology.md#6-extracting-with-a-schema-step-060): E1, "MODIS" (Instrument) ABOARD "Aqua" (Spacecraft), and E2, "CERES" (Spacecraft) ABOARD "Aqua" (Spacecraft), with the wrong [subject class](../../docs/terminology.md#2-triples).

*Then:* E1 and G1 form an [exact pair](pairs.md), which is strict; E2 and G5 form an exact pair, which isn't strict.

- Exact recall = 2 ÷ 5 = 40%; [recall upper bound](recall_upper_bound.md) = 4 ÷ 5 = 80%; exact recall within reach = 2 ÷ 4 = 50% = 40% ÷ 80%. Of the 4 ground truth triples the schema can express, extraction found half.
- Strict exact recall = 1 ÷ 5 = 20%; [strict recall upper bound](recall_upper_bound.md) = 3 ÷ 5 = 60%; strict exact recall within reach = 1 ÷ 3 = 33% = 20% ÷ 60%.

## Sources

No standard name was found for this number. It is recall restricted to the items an earlier stage of the pipeline lets through, the stage whose limit the [recall upper bound](recall_upper_bound.md) measures (Pink, Nothman & Curran, 2014, "Analysing recall loss in named entity slot filling", EMNLP, [paper](https://aclanthology.org/D14-1089.pdf)): the recall divided by its upper bound, as *Formula* shows.
