# Evaluation metrics

The one place each of evaluation's numbers is explained: what it is, its formula with an example, how to read it, what it assumes, and where it comes from. Other files point here instead of repeating it. Each has a file of its own (listed below), ending with a worked example and its sources. Terms: [docs/terminology.md](../docs/terminology.md).

Formulas use the usual set symbols: \|…\| is the number of members, ∪ is union (in either), ∩ is intersection (in both). Between statements, ∨ is the inclusive or (one, the other, or both) and ∧ is and (both). Square brackets around words, as in [a record's [extracted triples](../docs/terminology.md#6-extracting-with-a-schema-step-060) and [ground truth](../docs/terminology.md#4-ground-truth-and-samples) triples], mark them as one **unit**: a group spelled out in full and named as one thing. Every count is over all the evaluated [records](../docs/terminology.md#1-records-and-their-text) of one part (tuning or held-out) together, not one record at a time (*Pooled, not averaged*, below), and never includes the [describes triples](../docs/terminology.md#2-triples) (they're compared on their own: see [Describes accuracy](metrics/describes.md)).

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

For precision, recall, F1 and entity-class accuracy, the versions differ only in which [pairs](metrics/pairs.md) count: exact counts the [exact pairs](metrics/pairs.md); partial counts the exact pairs and the [partial pairs](metrics/pairs.md); strict keeps, of those, only the [strict pairs](metrics/pairs.md) (the same [subject classes](../docs/terminology.md#2-triples) and the same [object classes](../docs/terminology.md#2-triples), by [loose match](../docs/terminology.md#3-schemas)). Recall [within reach](metrics/recall_upper_bound.md) counts the same pairs as recall, and its strict versions divide only by the [ground truth triples](../docs/terminology.md#4-ground-truth-and-samples) [within strict reach](metrics/recall_upper_bound.md), not all those within reach. The recall upper bound counts no pairs: its strict version counts the ground truth triples within strict reach instead of those within reach. Precision, recall, and F1, and their strict versions, are also given per predicate, per subject class, and per object class, at both [pair levels](metrics/pairs.md), with each one's reach, strict recall upper bound, and strict recall within reach: what counts for each is in [070's guide, *Per predicate and per entity class*](070_evaluate.md#per-predicate-and-per-entity-class).

## Pooled, not averaged

Each number of a part pools every evaluated record's counts: precision is the sum of the records' pairs ÷ the sum of their occurrences, recall the sum of their pairs ÷ the sum of their ground truth triples, and so on for every metric, also per stratum, per predicate, and per [entity class](../docs/terminology.md#3-schemas). It is never the average of each record's own number. (The one average is the [describes per-entity-class average](metrics/describes.md), which averages over [describes classes](../docs/terminology.md#2-triples) on purpose.) *Suppose* record A has 2 ground truth triples and extraction found 2 (recall 100%), record B has 48 and extraction found 12 (25%). *Then*, pooled: 14 ÷ 50 = 28%. The average of the two, 62.5%, would let the small record weigh as much as the large one. Pooled, each [ground truth triple](../docs/terminology.md#4-ground-truth-and-samples) and each occurrence counts once, whichever record it is in.

Each record's own numbers, by the same formulas over its counts alone, are in the report's table *Per record* and at the top of each record in `per_record.md` ([070's guide, *Per record*](070_evaluate.md#per-record)). They are for finding the weak records, have no [margin of error](metrics/approximately.md), and are never averaged into a part's numbers.

## Which part of the pipeline each number speaks for

The numbers can tell some parts of the pipeline apart, so a weak result can be traced to the part that caused it.

- **Ground truth only because of the schema, or because of extraction.** A [ground truth triple](../docs/terminology.md#4-ground-truth-and-samples) can be ground truth only because it is out of reach (the [current schema](../docs/terminology.md#6-extracting-with-a-schema-step-060) has no predicate for it, or no checked row of the [translation table](../docs/terminology.md#7-evaluating-extraction-step-070) translates one of the current schema's predicates to it, so 060 couldn't express it), or because extraction didn't find it although it could, among other causes (every cause: [`metrics/recall.md`](metrics/recall.md), *When a ground truth triple counts as not found*). The [recall upper bound](metrics/recall_upper_bound.md) is the proportion of them the schema can express, the most recall can be with it; [recall within reach](metrics/recall_within_reach.md) is the proportion of those that extraction found. *Suppose* the recall upper bound is 70% and recall within reach 90%. *Then* most ground truth only triples come from being out of reach (the schema or the translation table), not from extraction.
- **Finding a fact or classifying it.** A [pair](metrics/pairs.md) counts a fact found when its [subject instance](../docs/terminology.md#2-triples), predicate, and [object instance](../docs/terminology.md#2-triples) match, whatever [entity classes](../docs/terminology.md#3-schemas) they were given; a [strict pair](metrics/pairs.md) also needs the entity classes right. [Entity-class accuracy](metrics/entity_class_accuracy.md) is the proportion of the pairs whose entity classes are right, and its subject and object versions say which slot goes wrong. So "finds the facts but misclassifies them" and "doesn't find them" are different numbers.
- **The [describes class](../docs/terminology.md#2-triples)** has its own accuracy ([describes accuracy](metrics/describes.md)), apart from every other fact.

What the numbers can't tell apart:

- **The translation table's mistakes.** A wrong translation looks like an extraction mistake. The report's *Component class mismatches* points to rows that are likely wrong, but no number counts them apart.
- **How good 050's [drafted triples](../docs/terminology.md#4-ground-truth-and-samples) were.** Comparing each [drafted batch](../docs/terminology.md#4-ground-truth-and-samples)'s drafted triples with the [ground truth](../docs/terminology.md#4-ground-truth-and-samples) corrected from them would measure it; that isn't built.
- **How good the ground truth is.** That needs a second person annotating the same records and their agreement measured; not built either. The ground truth started as drafted triples, so recall is likely overstated ([recall](metrics/recall.md), *Assumes and can't see*).
- **Steps 010 to 030** aren't evaluated here; their own checks and the tests (`tests/README.md`) cover them.

To isolate any one part, change only that part and compare the two evaluations on the same records (`helpers/compare_runs.md`).
