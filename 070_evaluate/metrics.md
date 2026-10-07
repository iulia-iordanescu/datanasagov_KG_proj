# Evaluation metrics

The one place each of evaluation's numbers is explained: what it is, its formula with an example, how to read it, what it assumes, and where it comes from. Other files point here instead of repeating it. Each has a file of its own (listed below), ending with a worked example and its sources. Terms: [docs/terminology.md](../docs/terminology.md).

Formulas use the usual set symbols: \|…\| is the number of members, ∪ is union (in either), ∩ is intersection (in both). Between statements, ∨ is the inclusive or (one, the other, or both) and ∧ is and (both). Every count is over all the evaluated [records](../docs/terminology.md#1-records-and-their-text) of one part (tuning or held-out) together, not one record at a time, and never includes the [DESCRIBES rows](../docs/terminology.md#2-triples) (they're compared on their own: see the describes metrics in [`070_evaluate.md`](070_evaluate.md), until they get a section here).

## The metrics

Read them in this order: what they count first, then each metric, then why each is approximate for the whole catalog.

| File | What it explains |
|---|---|
| [What the metrics count: pairs](metrics/pairs.md) | when an [extracted triple](../docs/terminology.md#6-extracting-with-a-schema-step-060) and a [ground truth triple](../docs/terminology.md#4-ground-truth-and-samples) count as stating the same fact: exact, partial, and strict pairs |
| [Precision](metrics/precision.md) | the proportion of the extracted triples that are correct |
| [Recall](metrics/recall.md) | the proportion of the ground truth triples that extraction found |
| [F1](metrics/f1.md) | precision and recall combined into one number |
| [Entity-class accuracy](metrics/entity_class_accuracy.md) | among the pairs, the proportion whose [entity classes](../docs/terminology.md#3-schemas) are also right |
| [Recall upper bound](metrics/recall_upper_bound.md) | the most recall the [current schema](../docs/terminology.md#6-extracting-with-a-schema-step-060) allows |
| [Why "approximately"](metrics/approximately.md) | the reasons every metric shares, including the [margin of error](../docs/terminology.md#7-evaluating-extraction-step-070) |
