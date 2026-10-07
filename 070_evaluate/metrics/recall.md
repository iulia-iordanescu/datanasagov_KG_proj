# Recall

Part of [Evaluation metrics](../metrics.md), which explains the notation and lists every metric.

## <ins>Definition</ins>

The proportion of the [ground truth triples](../../docs/terminology.md#4-ground-truth-and-samples) that extraction found. What "found" means depends on the version.

## <ins>Formula</ins>

Four versions.

| Version | A ground truth triple counts as found when it… | Formula |
|---|---|---|
| exact recall | forms an exact [pair](pairs.md) | \|exact pairs\| ÷ \|ground truth triples\| |
| partial recall | forms an exact or a partial pair | \|exact pairs ∪ partial pairs\| ÷ \|ground truth triples\| |
| strict exact recall | (forms an exact pair) ∧ (the pair is strict) | \|exact pairs ∩ strict pairs\| ÷ \|ground truth triples\| |
| strict partial recall | (forms an exact or a partial pair) ∧ (the pair is strict) | \|(exact pairs ∪ partial pairs) ∩ strict pairs\| ÷ \|ground truth triples\| |

Each version is a number from 0 to 1; with no ground truth triples across the [records](../../docs/terminology.md#1-records-and-their-text), it is undefined.

## <ins>Interpretations</ins>

Let *r* be the value of one version of recall. It reads two ways: what was computed, on the evaluated records, and what it means for the [knowledge graph](../../docs/terminology.md#8-the-pipeline), for the whole catalog. Each item of the second is the counterpart of the item with the same number in the first.

**What was computed** (the evaluated records)

1. *r* is the proportion of the evaluated records' ground truth triples that are found, where "found" is defined by the version (table above).
2. Partial recall minus exact recall is the proportion of the ground truth triples that form a partial pair but not an exact pair. In such a pair, the two [triples](../../docs/terminology.md#2-triples) have the same [predicate](../../docs/terminology.md#3-schemas), but (their [subject instances](../../docs/terminology.md#2-triples) are worded differently, one inside the other as whole words) ∨ (their [object instances](../../docs/terminology.md#2-triples) are worded differently, one inside the other as whole words) (e.g. "MODIS" vs "Moderate Resolution Imaging Spectroradiometer (MODIS)").
3. Recall minus strict recall, at the same pair level, is the proportion of the ground truth triples that form a pair at that level but not a strict one. In such a pair, (the two triples' [subject classes](../../docs/terminology.md#2-triples) differ) ∨ (the two triples' [object classes](../../docs/terminology.md#2-triples) differ).

**What it means for the knowledge graph** (the whole catalog, approximately)

Say the knowledge graph is built from the whole catalog's [extracted triples](../../docs/terminology.md#6-extracting-with-a-schema-step-060). Of the facts the catalog's records state, each counted once per record that states it:

1. approximately *r* would be in the graph;
2. approximately (partial recall minus exact recall) would be in it only with (the subject's [node](../../docs/terminology.md#8-the-pipeline) named differently from the [ground truth](../../docs/terminology.md#4-ground-truth-and-samples)) ∨ (the object's node named differently from the ground truth);
3. approximately (recall minus strict recall) would be in it, at that pair level, only with (the subject's node of the wrong [entity class](../../docs/terminology.md#3-schemas)) ∨ (the object's node of the wrong entity class).

## <ins>Assumes and can't see</ins>

- That the ground truth lists every fact the records state: a fact missing from it isn't counted at all, neither found nor missed.
- Not found means not in a pair the version counts, which isn't the same as missed by extraction. Examples: [Recall: example](#example), *A repeated fact*, *A wrong component class*, and *A wrong row of the translation table*.
- *What it means for the knowledge graph* is approximate for the [reasons every metric shares](approximately.md); the report measures one of them, sampling error, with *r*'s [margin of error](approximately.md#sampling-error). Unlike precision's, it doesn't depend on graph building: merging repeated extracted triples into one edge changes how many edges there are, not which facts the graph holds.
- *r* counts a fact once per record that states it. The proportion of distinct facts the knowledge graph holds, each counted once, is a different number, and can differ from *r*. Example: [Recall: example](#example), *Triples vs distinct facts*.
- Alone, *r* can be fooled: read it with [precision](precision.md) (see [F1](f1.md), *Interpretations*).

Worked example: [Recall: example](#example). Sources: [Recall: sources](#sources).

## Example

*Micro-averaging.* [Record](../../docs/terminology.md#1-records-and-their-text) A: the [ground truth](../../docs/terminology.md#4-ground-truth-and-samples) has 5 [triples](../../docs/terminology.md#2-triples), 3 of them found. Record B: it has 2, 1 found. Recall = (3 + 1) ÷ (5 + 2) = 57%. Averaging the records' own recalls (60% and 50%) would give 55% instead, letting record B's 2 [ground truth triples](../../docs/terminology.md#4-ground-truth-and-samples) weigh as much as record A's 5. This holds for every version: only what "found" means changes, that is, which [pairs](pairs.md) count (by pair level: exact, or exact or partial; by strictness: any, or strict only; see the table under *Formula*).

*Triples vs distinct facts.* 3 records each state "MODIS" ABOARD "Aqua", and extraction finds it in all 3; 1 record states "AIRS" ABOARD "Terra", and extraction misses it. Recall = 3 ÷ 4 = 75%. Counting each [fact](../../docs/terminology.md#2-triples) once per record that states it, the [knowledge graph](../../docs/terminology.md#8-the-pipeline) holds 3 of 4: 75%, as *r* says, whether or not graph building merges the 3 repeats into one [edge](../../docs/terminology.md#8-the-pipeline). Counting distinct facts, it holds 1 of 2: 50%, also whether or not the repeats are merged.

*A repeated fact.* The ground truth of one record lists the same fact twice: "MODIS ABOARD Aqua" and "the MODIS instrument ABOARD Aqua". Extraction gives it once. The [extracted triple](../../docs/terminology.md#6-extracting-with-a-schema-step-060) pairs with one of them; the other has no partner left, so it counts as not found, though extraction found the fact.

*A wrong component class.* The ground truth has "MODIS (Instrument) ABOARD Aqua (Spacecraft)". Extraction gives "MODIS (Dataset) ABOARD Aqua (Spacecraft)": the same fact, with the wrong [subject class](../../docs/terminology.md#2-triples). For strict exact recall the ground truth triple counts as not found, since the subject classes differ; the mistake is extraction's.

*A wrong row of the translation table.* The ground truth has "MODIS ABOARD Aqua". Extraction gives "MODIS MOUNTED_ON Aqua", which is right, but the table's row says MOUNTED_ON → ACQUIRED_BY. After translation the extracted triple reads "MODIS ACQUIRED_BY Aqua": the predicates differ, so the ground truth triple counts as not found, though extraction found it.

## Sources

The standard definition of recall, micro-averaged like [precision](precision.md): Manning, Raghavan & Schütze (2008), sections 8.3 and 13.6. As for precision, the WebNLG+ 2020 challenge reports recall macro-averaged (Castro Ferreira et al., 2020, Table 10), so our numbers aren't directly comparable with its published ones.
