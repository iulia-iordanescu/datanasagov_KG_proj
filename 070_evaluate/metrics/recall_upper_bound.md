# Recall upper bound

Part of [Evaluation metrics](../metrics.md), which explains the notation and lists every metric.

## <ins>Definition</ins>

The proportion of the [ground truth triples](../../docs/terminology.md#4-ground-truth-and-samples) that the [current schema](../../docs/terminology.md#6-extracting-with-a-schema-step-060) can express at all: the most recall any extraction with this [schema](../../docs/terminology.md#3-schemas) and [translation table](../../docs/terminology.md#7-evaluating-extraction-step-070) could get. A ground truth triple is **within reach** when its [predicate](../../docs/terminology.md#3-schemas) is one that some checked row of the translation table translates to. It is **within strict reach** when (it is within reach) ∧ (its [subject class](../../docs/terminology.md#2-triples) is one that some checked row translates to) ∧ (its [object class](../../docs/terminology.md#2-triples) is one that some checked row translates to). Which ground truth triples count depends on the version.

## <ins>Formula</ins>

Two versions.

| Version | A ground truth triple counts when it is… | Formula |
|---|---|---|
| recall upper bound | within reach | \|ground truth triples within reach\| ÷ \|ground truth triples\| |
| strict recall upper bound | within strict reach | \|ground truth triples within strict reach\| ÷ \|ground truth triples\| |

Each version is a number from 0 to 1; with no ground truth triples across the [records](../../docs/terminology.md#1-records-and-their-text), it is undefined.

## <ins>Interpretations</ins>

Let *u* be the value of one version of the recall upper bound. Then, *u* is the proportion of ground truth triples within reach (for the strict version, within strict reach). So no extraction with this schema and translation table can get a recall (for the strict version, a strict recall) above *u*: the other 1 − *u* of the ground truth triples use a [component class](../../docs/terminology.md#3-schemas) the current schema has no counterpart for.

- Read with recall: the gap between the two is what extraction missed although the schema could express it.
- A low upper bound points at the schema (schema induction, or the [schema additions](../../docs/terminology.md#3-schemas)) or at the translation table (a row that says `(none)`, or a missing row).
- The strict version is the limit for strict recall: a [triple](../../docs/terminology.md#2-triples) can be within reach but not within strict reach when (the schema has no counterpart for its subject class) ∨ (it has none for its object class).

## <ins>Assumes and can't see</ins>

- Within reach means only that the schema has the component classes: not that the [model](../../docs/terminology.md#8-the-pipeline) could find the [fact](../../docs/terminology.md#2-triples) in the [text](../../docs/terminology.md#1-records-and-their-text).
- It depends on the translation table: a row wrongly saying `(none)` lowers it.
- Read for the whole catalog, *u* is approximate for the the [reasons every metric shares](approximately.md); the [report](../../docs/terminology.md#8-the-pipeline) measures one of them, sampling error, with *u*'s [margin of error](approximately.md#sampling-error).

Worked example: [Recall upper bound: example](#example). Sources: [Recall upper bound: sources](#sources).

## Example

The [record](../../docs/terminology.md#1-records-and-their-text) of the *Pairs* example has 5 [ground truth triples](../../docs/terminology.md#4-ground-truth-and-samples), with the [predicates](../../docs/terminology.md#3-schemas) ABOARD (G1, G2, G5), ACQUIRED_BY (G3) and HAS_TIME_SPAN (G4). Say the [current schema](../../docs/terminology.md#6-extracting-with-a-schema-step-060) has counterparts for ABOARD and ACQUIRED_BY but not HAS_TIME_SPAN, and none for the [entity class](../../docs/terminology.md#3-schemas) Dataset.

- Within reach: G1, G2, G3, G5 (G4's predicate has no counterpart). Recall upper bound = 4 ÷ 5 = 80%.
- Within strict reach: G1, G2, G5 (G3's [subject class](../../docs/terminology.md#2-triples), Dataset, has no counterpart either). Strict recall upper bound = 3 ÷ 5 = 60%.

## Sources

An upper bound on recall, set by an earlier stage of a pipeline (here, the [schema](../../docs/terminology.md#3-schemas)), is standard: Pink, Nothman & Curran (2014), "Analysing recall loss in named entity slot filling", EMNLP ([paper](https://aclanthology.org/D14-1089.pdf)): "the recall of a system's coarse candidate generation process sets a hard upper bound on performance". As there, the bound uses the same matching rule as the metric it bounds: a [pair](pairs.md) needs only the [predicate](../../docs/terminology.md#3-schemas), so the recall upper bound counts only the predicate; a [strict pair](pairs.md) also needs the [entity classes](../../docs/terminology.md#3-schemas), so the strict recall upper bound counts them too. The name "recall upper bound" is the established one; no paper found uses a schema-specific term.
