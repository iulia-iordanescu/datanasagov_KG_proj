# What each record describes

Part of [Evaluation metrics](../metrics.md), which explains the notation and lists every metric.

## <ins>Definition</ins>

Every [record](../../docs/terminology.md#1-records-and-their-text) gets one [DESCRIBES row](../../docs/terminology.md#2-triples), written by code, in which the [model](../../docs/terminology.md#8-the-pipeline)'s only part is the [describes class](../../docs/terminology.md#2-triples): the [entity class](../../docs/terminology.md#3-schemas) of the thing the record is about, e.g. Dataset. So the DESCRIBES rows are left out of every other metric, and compared on their describes class alone. A record counts when its [ground truth](../../docs/terminology.md#4-ground-truth-and-samples) names a describes class (one that isn't `X`). For such a record, extraction is **right** when its describes class, translated through the [translation table](../../docs/terminology.md#7-evaluating-extraction-step-070), is the ground truth's describes class, by [loose match](../../docs/terminology.md#3-schemas). It is not right when extraction named none (`X`), or named one whose row says `(none)`.

## <ins>Formula</ins>

Three numbers, over the records that count.

| Number | Formula |
|---|---|
| describes accuracy | \|records where extraction is right\| ÷ \|records that count\| |
| describes baseline | \|records whose ground truth describes class is the most common one among the records that count\| ÷ \|records that count\| |
| describes per-entity-class average | for each describes class the ground truth names, \|its records where extraction is right\| ÷ \|its records\|; then the average of these proportions, each describes class weighing the same |

Each is a number from 0 to 1; with no records that count, it is undefined. Only describes accuracy gets a [margin of error](approximately.md#sampling-error).

The [report](../../docs/terminology.md#8-the-pipeline) also gives a table of what extraction said against what the ground truth says, one row per combination: the ground truth's describes class, extraction's describes class (translated; `(none named)` for `X`), and the number of records.

## <ins>Interpretations</ins>

Let *d* be the describes accuracy. It reads two ways: what was computed, on the evaluated records, and what it means for the [knowledge graph](../../docs/terminology.md#8-the-pipeline), for the whole catalog. Each item of the second is the counterpart of the item with the same number in the first.

**What was computed** (the evaluated records)

1. *d* is the proportion of the records that count where extraction named the right describes class.
2. The describes baseline is what *d* would be if extraction always named the most common describes class of these records. *d* means something only when it is clearly above the baseline: below it, always naming one describes class would do better.
3. The describes per-entity-class average weighs each describes class the same, however many records it has. Far below *d*, it shows that extraction does well on the common describes classes and badly on the rare ones. Always naming the most common describes class gets 1 ÷ (number of describes classes) on it, so a value well above that shows extraction tells the describes classes apart.

**What it means for the knowledge graph** (the whole catalog, approximately)

Say the knowledge graph is built from the whole catalog's [extracted triples](../../docs/terminology.md#6-extracting-with-a-schema-step-060), with each record's DESCRIBES row as an [edge](../../docs/terminology.md#8-the-pipeline) from the record's [node](../../docs/terminology.md#8-the-pipeline) to the node of the thing it describes. Then:

1. approximately *d* of those nodes would have the right entity class (of the records whose ground truth would name a describes class);
2. a graph that gave every such node the most common describes class would have approximately the describes baseline of them right;
3. the proportion of those nodes with the right entity class, taken for each describes class separately and then averaged, would be approximately the describes per-entity-class average.

## <ins>Assumes and can't see</ins>

- The baseline is computed from the evaluated records' own ground truth, so it knows which describes class is most common among them: a real guesser would have to learn that first. With few records, which describes class is the most common one can itself change from sample to sample. It gets no margin of error.
- The per-entity-class average gives a describes class with 1 record as much weight as one with 50, so with few records it moves a lot from sample to sample: one record can change it by many percentage points. It gets no margin of error either.
- Records whose ground truth describes class is `X` (none named yet) don't count.
- A describes class of the ground truth that no checked row of the translation table translates to can never be right: unlike the other [classed triples](../../docs/terminology.md#2-triples), there is no version counting only the records the schema could get right ([Recall upper bound](recall_upper_bound.md) is about the other ground truth triples).
- Two entity classes of the [current schema](../../docs/terminology.md#6-extracting-with-a-schema-step-060) that translate to one entity class of the [ground truth vocabulary](../../docs/terminology.md#7-evaluating-extraction-step-070) look the same, so mixing them up isn't seen.
- *What it means for the knowledge graph* is approximate for the [reasons every metric shares](approximately.md); the report measures one of them, sampling error, with *d*'s margin of error.

Worked example: [What each record describes: example](#example). Sources: [What each record describes: sources](#sources).

## Example

*Suppose:* Dataset, WebTool, and Catalog are [entity classes](../../docs/terminology.md#3-schemas) in both the [current schema](../../docs/terminology.md#6-extracting-with-a-schema-step-060) and the [ground truth vocabulary](../../docs/terminology.md#7-evaluating-extraction-step-070), and each translates to itself. 10 evaluated [records](../../docs/terminology.md#1-records-and-their-text) count. Their [ground truth](../../docs/terminology.md#4-ground-truth-and-samples) [describes classes](../../docs/terminology.md#2-triples), and what extraction named:

| Ground truth describes class | Records | Extraction named it | Extraction named something else |
|---|---:|---:|---:|
| Dataset | 6 | 6 | 0 |
| WebTool | 3 | 1 | 2 (Dataset) |
| Catalog | 1 | 0 | 1 (Dataset) |

*Then:*

- Describes accuracy = (6 + 1 + 0) ÷ 10 = 70%.
- Describes baseline = 6 ÷ 10 = 60%: naming Dataset every time would get 60%. 70% is above it, but only by one record.
- Describes per-entity-class average = (6 ÷ 6 + 1 ÷ 3 + 0 ÷ 1) ÷ 3 = (100% + 33% + 0%) ÷ 3 = 44%. Naming Dataset every time would get (100% + 0% + 0%) ÷ 3 = 33%. Extraction gets Dataset right, but most of the rarer describes classes wrong.

## Sources

- Describes accuracy is plain classification accuracy: one answer per record, right or not.
- The describes baseline is the usual floor a classifier's accuracy is compared with: giving the most common answer every time (Witten & Frank, *Data Mining*, 2000, section 8.3: ZeroR, which always gives the most common answer, is "useful for determining a baseline performance as a benchmark for other learning schemes").
- The describes per-entity-class average is the balanced accuracy: the average, over the possible answers, of the accuracy on the records whose right answer it is, which drops to chance when plain accuracy is high only because the classifier favors the most common answer (Brodersen, Ong, Stephan & Buhmann, 2010, "The balanced accuracy and its posterior distribution", ICPR, [paper](https://kaybrodersen.github.io/publications/Brodersen_2010b_ICPR.pdf), which defines it for two possible answers; here it averages over every [describes class](../../docs/terminology.md#2-triples) the [ground truth](../../docs/terminology.md#4-ground-truth-and-samples) names). That always naming the most common describes class gets 1 ÷ (number of describes classes) on it follows from the formula: 100% on that describes class, 0% on each other.
