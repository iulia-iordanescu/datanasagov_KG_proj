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

Let *u* be the value of one version of the recall upper bound. It reads two ways: what was computed, on the evaluated records, and what it means for the [knowledge graph](../../docs/terminology.md#8-the-pipeline), for the whole catalog. Each item of the second is the counterpart of the item with the same number in the first.

**What was computed** (the evaluated records)

1. *u* is the proportion of the evaluated records' ground truth triples that are within reach (for the strict version, within strict reach).
2. No extraction with this schema and translation table can get a [recall](recall.md) above the recall upper bound, or a strict recall above the strict recall upper bound, at either [pair level](pairs.md): a [pair](pairs.md) needs the same predicate, and an occurrence has a predicate of the [ground truth vocabulary](../../docs/terminology.md#7-evaluating-extraction-step-070) only when a row translates its predicate to one; a [strict pair](pairs.md) also needs the same subject classes and the same object classes, and an occurrence has [entity classes](../../docs/terminology.md#3-schemas) of the ground truth vocabulary only when rows translate its entity classes to them.
3. Recall upper bound minus strict recall upper bound is the proportion of the ground truth triples that are within reach but not within strict reach: the schema has their predicate, but (no counterpart for their subject class) ∨ (no counterpart for their object class).

**What it means for the knowledge graph** (the whole catalog, approximately)

Say the knowledge graph is built from the whole catalog's [extracted triples](../../docs/terminology.md#6-extracting-with-a-schema-step-060). Of the facts the catalog's records state, each counted once per record that states it:

1. approximately *u* have a predicate that some checked row translates to (for the strict version: a predicate and both entity classes that some checked rows translate to);
2. approximately 1 − (recall upper bound) couldn't be in the graph at all, whatever extraction does, and approximately 1 − (strict recall upper bound) couldn't be in it with both [nodes](../../docs/terminology.md#8-the-pipeline) of the right entity class;
3. approximately (recall upper bound minus strict recall upper bound) could be in it, but not with both nodes of the right entity class.

Read with recall: [recall within reach](recall_within_reach.md) is recall divided by the recall upper bound. A low upper bound points at the schema (schema induction, or the [schema additions](../../docs/terminology.md#3-schemas)) or at the translation table (a row that says `(none)` though a counterpart exists); a low recall within reach points at extraction.

## <ins>Assumes and can't see</ins>

- Within reach means only that the schema has the [component classes](../../docs/terminology.md#3-schemas): not that the [model](../../docs/terminology.md#8-the-pipeline) could find the [fact](../../docs/terminology.md#2-triples) in the [text](../../docs/terminology.md#1-records-and-their-text).
- It depends on the translation table: a row wrongly saying `(none)` lowers it, and a row wrongly translating to a component class of the ground truth vocabulary raises it.
- Each row translates one component class of the current schema to at most one component class of the ground truth vocabulary. So when one component class of the current schema means what two of the ground truth vocabulary mean together (for example, a broad predicate CARRIES of the current schema, covering what both ABOARD and HOSTS of the ground truth vocabulary mean), its row can name only one of them, and the ground truth triples using the other count as out of reach, though the schema could state them.
- The translation table is checked by one person, and a row can be changed after the [tuning part](../../docs/terminology.md#7-evaluating-extraction-step-070)'s numbers have been seen. A row changed because of those numbers fits the tuning part, as any change made while looking at its numbers does ([Why "approximately"](approximately.md), *Tuning on the evaluated records*). Check the rows before looking at the [held-out part](../../docs/terminology.md#7-evaluating-extraction-step-070).
- *What it means for the knowledge graph* is approximate for the [reasons every metric shares](approximately.md); the [report](../../docs/terminology.md#8-the-pipeline) measures one of them, sampling error, with *u*'s [margin of error](approximately.md#sampling-error). Like recall's, it doesn't depend on graph building: merging repeated extracted triples into one edge changes how many edges there are, not which facts the graph could hold.

Worked example: [Recall upper bound: example](#example). Sources: [Recall upper bound: sources](#sources).

## Example

*Suppose:* the [ground truth vocabulary](../../docs/terminology.md#7-evaluating-extraction-step-070) has the [predicates](../../docs/terminology.md#3-schemas) ABOARD, ACQUIRED_BY, and HAS_TIME_SPAN, and the [entity classes](../../docs/terminology.md#3-schemas) Instrument, Spacecraft, Dataset, and TimeSpan. The checked rows of the [translation table](../../docs/terminology.md#7-evaluating-extraction-step-070) translate [component classes](../../docs/terminology.md#3-schemas) of the [current schema](../../docs/terminology.md#6-extracting-with-a-schema-step-060) to ABOARD, ACQUIRED_BY, Instrument, Spacecraft, and TimeSpan, but none translates to HAS_TIME_SPAN or Dataset. A [record](../../docs/terminology.md#1-records-and-their-text)'s [ground truth](../../docs/terminology.md#4-ground-truth-and-samples) has 5 [ground truth triples](../../docs/terminology.md#4-ground-truth-and-samples):

| | Subject instance (subject class) | Predicate | Object instance (object class) | Within reach | Within strict reach |
|---|---|---|---|---|---|
| G1 | MODIS (Instrument) | ABOARD | Aqua (Spacecraft) | yes | yes |
| G2 | AIRS (Instrument) | ABOARD | Aqua (Spacecraft) | yes | yes |
| G3 | MODIS Snow Cover (Dataset) | ACQUIRED_BY | MODIS (Instrument) | yes | no: nothing translates to Dataset |
| G4 | MODIS Snow Cover (Dataset) | HAS_TIME_SPAN | 2002–2023 (TimeSpan) | no: nothing translates to HAS_TIME_SPAN | no |
| G5 | CERES (Instrument) | ABOARD | Aqua (Spacecraft) | yes | yes |

*Then:* recall upper bound = 4 ÷ 5 = 80%; strict recall upper bound = 3 ÷ 5 = 60%. Whatever extraction gives for this record, at most 4 of its ground truth triples can be found, and at most 3 in [strict pairs](pairs.md).

## Sources

An upper bound on recall, set by an earlier stage of a pipeline (here, the [schema](../../docs/terminology.md#3-schemas)), is standard: Pink, Nothman & Curran (2014), "Analysing recall loss in named entity slot filling", EMNLP ([paper](https://aclanthology.org/D14-1089.pdf)): "the recall of a system's coarse candidate generation process sets a hard upper bound on performance". As there, the bound uses the same matching rule as the metric it bounds: a [pair](pairs.md) needs only the [predicate](../../docs/terminology.md#3-schemas), so the recall upper bound counts only the predicate; a [strict pair](pairs.md) also needs the [entity classes](../../docs/terminology.md#3-schemas), so the strict recall upper bound counts them too. The name "recall upper bound" is the established one; no paper found uses a schema-specific term.
