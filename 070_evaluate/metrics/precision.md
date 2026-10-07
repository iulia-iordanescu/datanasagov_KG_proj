# Precision

Part of [Evaluation metrics](../metrics.md), which explains the notation and lists every metric.

## <ins>Definition</ins>

The proportion of the [extracted triples](../../docs/terminology.md#6-extracting-with-a-schema-step-060) that are correct. What "correct" means depends on the version.

## <ins>Formula</ins>

Four versions.

| Version | An extracted triple counts as correct when it… | Formula |
|---|---|---|
| exact precision | forms an exact [pair](pairs.md) | \|exact pairs\| ÷ \|extracted triples\| |
| partial precision | forms an exact or a partial pair | \|exact pairs ∪ partial pairs\| ÷ \|extracted triples\| |
| strict exact precision | (forms an exact pair) ∧ (the pair is strict) | \|exact pairs ∩ strict pairs\| ÷ \|extracted triples\| |
| strict partial precision | (forms an exact or a partial pair) ∧ (the pair is strict) | \|(exact pairs ∪ partial pairs) ∩ strict pairs\| ÷ \|extracted triples\| |

Each version is a number from 0 to 1; with no extracted triples across the [records](../../docs/terminology.md#1-records-and-their-text), it is undefined.

## <ins>Interpretations</ins>

Let *p* be the value of one version of precision. It reads two ways: what was computed, on the evaluated records, and what it means for the [knowledge graph](../../docs/terminology.md#8-the-pipeline), for the whole catalog. Each item of the second is the counterpart of the item with the same number in the first.

**What was computed** (the evaluated records)

1. *p* is the proportion of the evaluated records' extracted triples that are correct, where "correct" is defined by the version (table above).
2. Partial precision minus exact precision is the proportion of the extracted triples that form a partial pair but not an exact pair. In such a pair, the two [triples](../../docs/terminology.md#2-triples) have the same [predicate](../../docs/terminology.md#3-schemas), but (their [subject instances](../../docs/terminology.md#2-triples) are worded differently, one inside the other as whole words) ∨ (their [object instances](../../docs/terminology.md#2-triples) are worded differently, one inside the other as whole words) (e.g. "MODIS" vs "Moderate Resolution Imaging Spectroradiometer (MODIS)").
3. Precision minus strict precision, at the same pair level, is the proportion of the extracted triples that form a pair at that level but not a strict one. In such a pair, (the two triples' [subject classes](../../docs/terminology.md#2-triples) differ) ∨ (the two triples' [object classes](../../docs/terminology.md#2-triples) differ).

**What it means for the knowledge graph** (the whole catalog, approximately)

Say the knowledge graph is built from the whole catalog's extracted triples, one [edge](../../docs/terminology.md#8-the-pipeline) per extracted triple. Then:

1. Approximately *p* of its edges would be correct.
2. Approximately (partial precision minus exact precision) of its edges would state a fact the [ground truth](../../docs/terminology.md#4-ground-truth-and-samples) also states, by partial pairing, but with (the subject's [node](../../docs/terminology.md#8-the-pipeline) named differently from the ground truth) ∨ (the object's node named differently from the ground truth), e.g. a node "Moderate Resolution Imaging Spectroradiometer (MODIS)" where the ground truth says "MODIS".
3. Approximately (precision minus strict precision) of its edges would state a fact the ground truth also states, at that pair level, but with (the subject's node of the wrong [entity class](../../docs/terminology.md#3-schemas)) ∨ (the object's node of the wrong entity class).

## <ins>Assumes and can't see</ins>

- That the ground truth lists every fact the records state: an extracted triple that is true but missing from the ground truth counts as not correct, so it lowers *p*.
- Not correct means not in a pair the version counts, which isn't the same as false. Examples: [Precision: example](#example), *A repeated fact*, *A wrong component class*, and *A wrong row of the translation table*.
- *What it means for the knowledge graph* is approximate for two kinds of reason:
  - the [reasons every metric shares](approximately.md); the [report](../../docs/terminology.md#8-the-pipeline) measures one of them, sampling error, with *p*'s [margin of error](approximately.md#sampling-error);
  - one of precision's own: if graph building ([step](../../docs/terminology.md#8-the-pipeline) 080, not built yet) merges repeated extracted triples into one edge, the proportions of edges above can differ from what was computed. Merging turns a fact that many records state into one edge, but leaves a fact that one record states as one edge. Example: [Precision: example](#example), *Triples vs distinct facts*.
- Alone, *p* can be fooled: read it with [recall](recall.md) (see [F1](f1.md), *Interpretations*).

Worked example: [Precision: example](#example). Sources: [Precision: sources](#sources).

## Example

*Micro-averaging.* [Record](../../docs/terminology.md#1-records-and-their-text) A: 4 [extracted triples](../../docs/terminology.md#6-extracting-with-a-schema-step-060), 3 of them correct. Record B: 1 extracted triple, correct. Precision = (3 + 1) ÷ (4 + 1) = 80%. Averaging the records' own precisions (75% and 100%) would give 87.5% instead, letting record B's single extracted triple weigh as much as record A's four. This holds for every version: only what "correct" means changes, that is, which [pairs](pairs.md) count (by pair level: exact, or exact or partial; by strictness: any, or strict only; see the table under *Formula*).

*Triples vs distinct facts.* 3 records each give the extracted triple "MODIS" ABOARD "Aqua", which is correct, and 1 record gives "AIRS" ABOARD "Terra", which is not. Precision = 3 ÷ 4 = 75%. If each extracted triple becomes one [edge](../../docs/terminology.md#8-the-pipeline), 3 of the 4 edges are correct: 75%, as *p* says. If the 3 repeats are merged into one edge, 1 of the 2 edges is correct: 50%.

*A repeated fact.* The [ground truth](../../docs/terminology.md#4-ground-truth-and-samples) has "MODIS ABOARD Aqua" once. Extraction gives it twice: "MODIS ABOARD Aqua" and "the MODIS instrument ABOARD Aqua". The [ground truth triple](../../docs/terminology.md#4-ground-truth-and-samples) pairs with one of them; the other has no partner left, so it counts as not correct, though what it says is true.

*A wrong component class.* The text says MODIS is aboard Aqua. The ground truth has "MODIS (Instrument) ABOARD Aqua (Spacecraft)". Extraction gives "MODIS (Dataset) ABOARD Aqua (Spacecraft)": the same fact, with the wrong [subject class](../../docs/terminology.md#2-triples). The [translation table](../../docs/terminology.md#7-evaluating-extraction-step-070) and the ground truth are both right: the mistake is extraction's. For strict exact precision it counts as not correct, since the subject classes differ.

*A wrong row of the translation table.* Extraction gives "MODIS MOUNTED_ON Aqua", which is right: MOUNTED_ON is the [current schema](../../docs/terminology.md#6-extracting-with-a-schema-step-060)'s word for ABOARD. But the table's row says MOUNTED_ON → ACQUIRED_BY. After translation the triple reads "MODIS ACQUIRED_BY Aqua", while the ground truth says "MODIS ABOARD Aqua": the predicates differ, so it counts as not correct, though extraction did nothing wrong.

## Sources

The standard definition of precision, summed over all items before dividing (*micro-averaging*), as opposed to averaging per [record](../../docs/terminology.md#1-records-and-their-text) (*macro-averaging*): Manning, Raghavan & Schütze, *Introduction to Information Retrieval* (2008), sections 8.3 and 13.6 ([book](https://nlp.stanford.edu/IR-book/)). Micro-averaging fits precision's interpretation: every [extracted triple](../../docs/terminology.md#6-extracting-with-a-schema-step-060) weighs the same, as every [edge](../../docs/terminology.md#8-the-pipeline) would in the [knowledge graph](../../docs/terminology.md#8-the-pipeline). Macro-averaging answers another question (for a typical record, what proportion of its extracted triples is correct). The WebNLG+ 2020 challenge reports its text-to-triples scores macro-averaged (Castro Ferreira et al., 2020, Table 10, [paper](https://aclanthology.org/2020.webnlg-1.7.pdf)), so our numbers aren't directly comparable with its published ones.
