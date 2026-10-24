# Evaluation metrics

The one place each of evaluation's numbers is explained: what it is, its formula with an example, how to read it, what it assumes, and where it comes from. Other files point here instead of repeating it. Each has a file of its own (listed below), ending with a worked example and its sources. Terms: [docs/terminology.md](../docs/terminology.md).

Formulas use the usual set symbols: \|…\| is the number of members, ∪ is union (in either), ∩ is intersection (in both). Between statements, ∨ is the inclusive or (one, the other, or both) and ∧ is and (both). Square brackets around words, as in [a record's [extracted triples](../docs/terminology.md#6-extracting-with-a-schema-step-060) and [ground truth](../docs/terminology.md#4-ground-truth-and-samples) triples], mark them as one **unit**: a group spelled out in full and named as one thing. Every count is over all the evaluated [records](../docs/terminology.md#1-records-and-their-text) of one part (tuning or held-out) together, not one record at a time, and never includes the [describes triples](../docs/terminology.md#2-triples) (they're compared on their own: see [Describes accuracy](metrics/describes.md)).

## The metrics

Read them in this order: what they count first, then each metric, then why each is approximate for the whole catalog.

| File | What it explains |
|---|---|
| [What the metrics count: pairs](metrics/pairs.md) | when an occurrence and a [ground truth triple](../docs/terminology.md#4-ground-truth-and-samples) count as stating the same fact: exact, partial, and [strict pairs](metrics/pairs.md) |
| [Precision](metrics/precision.md) | the proportion of the occurrences that are correct |
| [Recall](metrics/recall.md) | the proportion of the ground truth triples that extraction found |
| [F1](metrics/f1.md) | precision and recall combined into one number |
| [Entity-class accuracy](metrics/entity_class_accuracy.md) | among the pairs, the proportion whose [entity classes](../docs/terminology.md#3-schemas) are also right; and, by slot, the proportion whose [subject classes](../docs/terminology.md#2-triples) are right, and whose [object classes](../docs/terminology.md#2-triples) are right |
| [Recall upper bound](metrics/recall_upper_bound.md) | the most recall the [current schema](../docs/terminology.md#6-extracting-with-a-schema-step-060) allows |
| [Recall within reach](metrics/recall_within_reach.md) | recall over only the ground truth triples [within reach](metrics/recall_upper_bound.md) (whose [predicate](../docs/terminology.md#3-schemas) some checked row of the [translation table](../docs/terminology.md#7-evaluating-extraction-step-070) translates to): recall ÷ recall upper bound |
| [Describes accuracy](metrics/describes.md) | how often extraction names the right [describes class](../docs/terminology.md#2-triples), next to always naming the most common one |
| [Why "approximately"](metrics/approximately.md) | the reasons every metric shares, including the [margin of error](../docs/terminology.md#7-evaluating-extraction-step-070) |

## Versions of each metric

| Metric | Versions |
|---|---|
| [Precision](metrics/precision.md) | exact, partial, strict exact, strict partial |
| [Recall](metrics/recall.md) | exact, partial, strict exact, strict partial |
| [F1](metrics/f1.md) | exact, partial, strict exact, strict partial |
| [Recall within reach](metrics/recall_within_reach.md) | exact, partial, strict exact, strict partial |
| [Entity-class accuracy](metrics/entity_class_accuracy.md) | exact, partial (each also by slot: [subject-class accuracy](metrics/entity_class_accuracy.md) and [object-class accuracy](metrics/entity_class_accuracy.md)) |
| [Recall upper bound](metrics/recall_upper_bound.md) | recall upper bound, [strict recall upper bound](metrics/recall_upper_bound.md) |
| [Describes accuracy](metrics/describes.md) | one version (shown with the [describes baseline](metrics/describes.md) and the [describes per-entity-class average](metrics/describes.md)) |

For precision, recall, F1 and entity-class accuracy, the versions differ only in which [pairs](metrics/pairs.md) count: exact counts the [exact pairs](metrics/pairs.md); partial counts the exact pairs and the [partial pairs](metrics/pairs.md); strict keeps, of those, only the [strict pairs](metrics/pairs.md) (the same [subject classes](../docs/terminology.md#2-triples) and the same [object classes](../docs/terminology.md#2-triples), by [loose match](../docs/terminology.md#3-schemas)). Recall [within reach](metrics/recall_upper_bound.md) counts the same pairs as recall, and its strict versions divide only by the [ground truth triples](../docs/terminology.md#4-ground-truth-and-samples) [within strict reach](metrics/recall_upper_bound.md), not all those within reach. The recall upper bound counts no pairs: its strict version counts the ground truth triples within strict reach instead of those within reach. Precision and recall are also given per predicate, per subject class, and per object class, at both [pair levels](metrics/pairs.md): what counts for each is in [070's guide, *Per predicate and per entity class*](070_evaluate.md#per-predicate-and-per-entity-class).

## Which part of the pipeline each number speaks for

The numbers can tell some parts of the pipeline apart, so a weak result can be traced to the part that caused it.

- **Ground truth only because of the schema, or because of extraction.** A [ground truth triple](../docs/terminology.md#4-ground-truth-and-samples) can be ground truth only because the [current schema](../docs/terminology.md#6-extracting-with-a-schema-step-060) has no predicate for it (060 couldn't express it), or because extraction didn't find it although it could. The [recall upper bound](metrics/recall_upper_bound.md) is the proportion of them the schema can express, the most recall can be with it; [recall within reach](metrics/recall_within_reach.md) is the proportion of those that extraction found. *Suppose* the recall upper bound is 70% and recall within reach 90%. *Then* most ground truth only triples come from the schema, not from extraction.
- **Finding a fact or classifying it.** A [pair](metrics/pairs.md) counts a fact found when its [subject instance](../docs/terminology.md#2-triples), predicate, and [object instance](../docs/terminology.md#2-triples) match, whatever [entity classes](../docs/terminology.md#3-schemas) they were given; a [strict pair](metrics/pairs.md) also needs the entity classes right. [Entity-class accuracy](metrics/entity_class_accuracy.md) is the proportion of the pairs whose entity classes are right, and its subject and object versions say which slot goes wrong. So "finds the facts but misclassifies them" and "doesn't find them" are different numbers.
- **The [describes class](../docs/terminology.md#2-triples)** has its own accuracy ([describes accuracy](metrics/describes.md)), apart from every other fact.

What the numbers can't tell apart:

- **The [translation table](../docs/terminology.md#7-evaluating-extraction-step-070)'s mistakes.** A wrong translation looks like an extraction mistake. The report's *Component class mismatches* points to rows that are likely wrong, but no number counts them apart.
- **How good 050's [drafted triples](../docs/terminology.md#4-ground-truth-and-samples) were.** Comparing each [drafted batch](../docs/terminology.md#4-ground-truth-and-samples)'s drafted triples with the [ground truth](../docs/terminology.md#4-ground-truth-and-samples) corrected from them would measure it; that isn't built.
- **How good the ground truth is.** That needs a second person annotating the same records and their agreement measured; not built either. The ground truth started as drafted triples, so recall is likely overstated ([recall](metrics/recall.md), *Assumes and can't see*).
- **Steps 010 to 030** aren't evaluated here; their own checks and the tests (`tests/README.md`) cover them.

To isolate any one part, change only that part and compare the two evaluations on the same records (`helpers/compare_runs.md`).
