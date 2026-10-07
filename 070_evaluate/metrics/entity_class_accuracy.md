# Entity-class accuracy

Part of [Evaluation metrics](../metrics.md), which explains the notation and lists every metric.

## <ins>Definition</ins>

Among the [pairs](pairs.md) counted, the proportion that are strict. Which pairs are counted depends on the version.

## <ins>Formula</ins>

Two versions.

| Version | Pairs counted | Formula |
|---|---|---|
| exact entity-class accuracy | exact pairs | \|exact pairs ∩ strict pairs\| ÷ \|exact pairs\| |
| partial entity-class accuracy | exact pairs ∪ partial pairs | \|(exact pairs ∪ partial pairs) ∩ strict pairs\| ÷ \|exact pairs ∪ partial pairs\| |

Each version is a number from 0 to 1; with no pairs counted across the [records](../../docs/terminology.md#1-records-and-their-text), it is undefined.

## <ins>Interpretations</ins>

Let *a* be the value of one version of entity-class accuracy. Then, *a* is the proportion of the pairs counted that are strict, where the pairs counted are defined by the version (table above). So of the [knowledge graph](../../docs/terminology.md#8-the-pipeline)'s correct [edges](../../docs/terminology.md#8-the-pipeline), approximately *a* would also have both [nodes](../../docs/terminology.md#8-the-pipeline)' [entity classes](../../docs/terminology.md#3-schemas) right.

- Read with [precision](precision.md) and [recall](recall.md): they say whether [facts](../../docs/terminology.md#2-triples) are found; this says whether the things in them are classed right.

## <ins>Assumes and can't see</ins>

- Only paired [triples](../../docs/terminology.md#2-triples) are judged: the [subject class](../../docs/terminology.md#2-triples) and [object class](../../docs/terminology.md#2-triples) of a triple without a partner aren't counted anywhere.
- Two [component classes](../../docs/terminology.md#3-schemas) of the [current schema](../../docs/terminology.md#6-extracting-with-a-schema-step-060) that translate to one component class of the [ground truth vocabulary](../../docs/terminology.md#7-evaluating-extraction-step-070) look the same, so mixing them up isn't seen.
- Above, *Interpretations* states that approximately *a* of the knowledge graph's correct edges would also have both nodes' entity classes right, where *a* is any one version of entity-class accuracy. It is approximate for two kinds of reason:
  - the [reasons every metric shares](approximately.md); the [report](../../docs/terminology.md#8-the-pipeline) measures one of them, sampling error, with *a*'s [margin of error](approximately.md#sampling-error);
  - one of its own: if graph building ([step](../../docs/terminology.md#8-the-pipeline) 080, not built yet) merges repeated [extracted triples](../../docs/terminology.md#6-extracting-with-a-schema-step-060) into one edge, the proportion of correct edges whose entity classes are right can differ from *a*, for the reason given under [Precision](precision.md), *Assumes and can't see*.

Worked example: [Entity-class accuracy: example](#example). Sources: [Entity-class accuracy: sources](#sources).

## Example

4 [pairs](pairs.md), 3 of them strict: entity-class accuracy = 3 ÷ 4 = 75%.

## Sources

No single standard name. It separates the two [settings](../../docs/terminology.md#8-the-pipeline) end-to-end relation extraction reports side by side, "Strict" (with entity types) and "Boundaries" (without), described by Taillé et al. (2020): here, strict [pairs](pairs.md) ÷ all pairs.
