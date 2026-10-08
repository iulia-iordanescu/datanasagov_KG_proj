# Precision

Part of [Evaluation metrics](../metrics.md), which explains the notation and lists every metric.

## <ins>Definition</ins>

The proportion of the [extracted triples](../../docs/terminology.md#6-extracting-with-a-schema-step-060) that are correct. What "correct" means depends on the version.

## <ins>Formula</ins>

Four versions.

| Version | An extracted triple counts as correct when it… | Formula |
|---|---|---|
| exact precision | forms an [exact pair](pairs.md) | \|exact pairs\| ÷ \|extracted triples\| |
| partial precision | forms an exact or a [partial pair](pairs.md) | \|exact pairs ∪ partial pairs\| ÷ \|extracted triples\| |
| strict exact precision | (forms an exact pair) ∧ (the pair is strict) | \|exact pairs ∩ [strict pairs](pairs.md)\| ÷ \|extracted triples\| |
| strict partial precision | (forms an exact or a partial pair) ∧ (the pair is strict) | \|(exact pairs ∪ partial pairs) ∩ strict pairs\| ÷ \|extracted triples\| |

Each version is a number from 0 to 1; with no extracted triples across the [records](../../docs/terminology.md#1-records-and-their-text), it is undefined.

## <ins>Interpretations</ins>

Let *p* be the value of one version of precision. It reads two ways: what was computed, on the evaluated records, and what it means for the [knowledge graph](../../docs/terminology.md#8-the-pipeline), for the whole catalog. Each item of the second is the counterpart of the item with the same number in the first.

**What was computed** (the evaluated records)

1. *p* is the proportion of the evaluated records' extracted triples that are correct, where "correct" is defined by the version (table above).
2. Partial precision minus exact precision is the proportion of the extracted triples that form a partial pair.
3. Precision minus strict precision, at the same [pair level](pairs.md), is the proportion of the extracted triples that form a pair at that level but not a strict one.

**What it means for the knowledge graph** (the whole catalog, approximately)

Say the knowledge graph is built from the whole catalog's extracted triples, one [edge](../../docs/terminology.md#8-the-pipeline) per extracted triple. Then:

1. Approximately *p* of its edges would be correct.
2. Approximately (partial precision minus exact precision) of its edges would state a fact the [ground truth](../../docs/terminology.md#4-ground-truth-and-samples) also states, by partial pairing, but with (the subject's [node](../../docs/terminology.md#8-the-pipeline) named differently from the ground truth) ∨ (the object's node named differently from the ground truth), e.g. a node "Moderate Resolution Imaging Spectroradiometer (MODIS)" where the ground truth says "MODIS".
3. Approximately (precision minus strict precision) of its edges would state a fact the ground truth also states, at that pair level, but with (the subject's node of the wrong [entity class](../../docs/terminology.md#3-schemas)) ∨ (the object's node of the wrong entity class).

## <ins>Assumes and can't see</ins>

- That the ground truth lists every fact the records state: an extracted triple that is true but missing from the ground truth counts as not correct, so it lowers *p*.
- Not correct means not in a pair the version counts, which isn't the same as false: see *When an extracted triple counts as not correct*, below. The opposite mistake happens too: see [Pairs](pairs.md), *When a pair isn't the same fact*.
- Only the extracted triples step 060 kept: those it removed are counted in neither part of the fraction, and don't reach the knowledge graph either. How many were removed, and why, is in 060's report.
- *What it means for the knowledge graph* is approximate for two kinds of reason:
  - the [reasons every metric shares](approximately.md); the [report](../../docs/terminology.md#8-the-pipeline) measures one of them, sampling error, with *p*'s [margin of error](approximately.md#sampling-error);
  - one of precision's own: if graph building ([step](../../docs/terminology.md#8-the-pipeline) 080, not built yet) merges repeated extracted triples into one edge, the proportions of edges above can differ from what was computed. Merging turns a fact that many records state into one edge, but leaves a fact that one record states as one edge. Example: [Precision: example](#example), *Extracted triples vs distinct facts*.
- Alone, *p* can be fooled: read it with [recall](recall.md) (see [F1](f1.md), *Interpretations*).

## <ins>When an extracted triple counts as not correct</ins>

Under a version, an extracted triple counts as not correct in exactly two situations: (A) it has no partner at all (it is extracted only), or (B) it has a partner, but the version doesn't count that kind of pair. The extracted triples step 060 removed aren't counted at all, so they aren't here.

| # | Cause | Example | Versions it lowers | Whose doing | Is "not correct" the right verdict? | What to do |
|---|---|---|---|---|---|---|
| | **(A) No partner** | | | | | |
| 1 | The text doesn't state it | "MODIS" ABOARD "Terra", where Terra is nowhere in the text | all | extraction | yes | improve extraction (prompt, model, schema) |
| 2 | The text states something else | "Aqua" ABOARD "MODIS" (subject and object swapped) | all | extraction | yes | improve extraction |
| 3 | A repeat of a fact already paired | "the MODIS instrument" ABOARD "Aqua", after "MODIS" ABOARD "Aqua" took the only partner (*A repeated fact*, below) | all | extraction (it said the fact twice) | yes, by design: each fact counts once | nothing |
| 4 | The same fact in different words | "the imaging spectroradiometer" ABOARD "the Aqua satellite" ([Pairs: example](pairs.md#example), *The same fact in different words*) | all | pairing (it can't see synonyms) | no | Raise With Mentors: check a sample of extracted-only triples (`070_evaluate/070_evaluate.md`, *To do*) |
| 5 | A fact the ground truth lacks | the text states it, but the person annotating missed it | all | ground truth | no | add the fact to the ground truth (tuning records only) |
| 6 | Facts split differently | "MODIS and AIRS" ABOARD "Aqua", where the ground truth has two [classed triples](../../docs/terminology.md#2-triples) | all | whichever side broke the rule "one fact per classed triple" | yes if extraction broke it; no if the ground truth did | improve extraction, or split the ground truth's classed triple |
| 7 | A wrong predicate row of the [translation table](../../docs/terminology.md#7-evaluating-extraction-step-070) | MOUNTED_ON → ACQUIRED_BY, where it should be ABOARD (*A wrong row of the translation table*, below) | all | translation table | no | fix the row (the report's *Component class mismatches* shows it) |
| 8 | Its predicate translates to `(none)` | the [current schema](../../docs/terminology.md#6-extracting-with-a-schema-step-060) has LAUNCHED_BY; the [ground truth vocabulary](../../docs/terminology.md#7-evaluating-extraction-step-070) has nothing like it | all | the two vocabularies differ | usually no: the fact may be true | if the fact is true, add it to the ground truth (tuning records only), which coins the predicate; then give the row that counterpart |
| 9 | You marked the partial pair "not the same fact" | "MODIS" vs "MODIS Terra" | partial versions | your review | yes, unless the review was wrong | if it was wrong, take the verdict back ([annotation tool](../../docs/terminology.md#4-ground-truth-and-samples), *Partial pairs*) |
| | **(B) A partner the version doesn't count** | | | | | |
| 10 | A partial pair, under an exact version | "Moderate Resolution Imaging Spectroradiometer (MODIS)" vs "MODIS" | exact versions | none: the version asks for the same [subject instance](../../docs/terminology.md#2-triples) and [object instance](../../docs/terminology.md#2-triples) | yes, by the version's definition | nothing: the partial versions count it |
| 11 | A wrong entity class, from extraction | "MODIS" (Dataset), where the ground truth has (Instrument) (*A wrong component class*, below) | strict versions | extraction | yes | improve extraction |
| 12 | A wrong entity class in the ground truth | the ground truth says (Dataset) by mistake | strict versions | ground truth | no | fix the ground truth |
| 13 | A wrong entity-class row of the translation table | `Satellite` → `Mission`, where it should be `Spacecraft` | strict versions | translation table | no | fix the row |
| 14 | Its entity class translates to `(none)` | the current schema has `Constellation`; the ground truth vocabulary has nothing like it | strict versions | the two vocabularies differ | usually no: the entity class may be right | if the entity class is right, add the fact to the ground truth (tuning records only), which coins the entity class; then give the row that counterpart |
| 15 | The current schema's entity class is broader | the current schema has only `Instrument`; the ground truth uses `Instrument` and `Sensor`; a [ground truth triple](../../docs/terminology.md#4-ground-truth-and-samples) with `Sensor` never agrees | strict versions | the two vocabularies differ: a [component class](../../docs/terminology.md#3-schemas) has one translation | no | none yet: a known limit (`070_evaluate/070_evaluate.md`, *Known limits*) |

Worked example: [Precision: example](#example). Sources: [Precision: sources](#sources).

## Example

*Micro-averaging.* [Record](../../docs/terminology.md#1-records-and-their-text) A: 4 [extracted triples](../../docs/terminology.md#6-extracting-with-a-schema-step-060), 3 of them correct. Record B: 1 extracted triple, correct. Precision = (3 + 1) ÷ (4 + 1) = 80%. Averaging the records' own precisions (75% and 100%) would give 87.5% instead, letting record B's single extracted triple weigh as much as record A's four. This holds for every version: only what "correct" means changes, that is, which [pairs](pairs.md) count (by [pair level](pairs.md): exact, or exact or partial; by strictness: any, or strict only; see the table under *Formula*).

*Extracted triples vs distinct facts.* 3 records each give the extracted triple "MODIS" ABOARD "Aqua", which is correct, and 1 record gives "AIRS" ABOARD "Terra", which is not. Precision = 3 ÷ 4 = 75%. If each extracted triple becomes one [edge](../../docs/terminology.md#8-the-pipeline), 3 of the 4 edges are correct: 75%, as *p* says. If the 3 repeats are merged into one edge, 1 of the 2 edges is correct: 50%.

*A repeated fact.* The [ground truth](../../docs/terminology.md#4-ground-truth-and-samples) has "MODIS ABOARD Aqua" once. Extraction gives it twice: "MODIS ABOARD Aqua" and "the MODIS instrument ABOARD Aqua". The [ground truth triple](../../docs/terminology.md#4-ground-truth-and-samples) pairs with one of them; the other has no partner left, so it counts as not correct, though what it says is true.

*A wrong component class.* The text says MODIS is aboard Aqua. The ground truth has "MODIS (Instrument) ABOARD Aqua (Spacecraft)". Extraction gives "MODIS (Dataset) ABOARD Aqua (Spacecraft)": the same fact, with the wrong [subject class](../../docs/terminology.md#2-triples). The [translation table](../../docs/terminology.md#7-evaluating-extraction-step-070) and the ground truth are both right: the mistake is extraction's. For strict exact precision it counts as not correct, since the subject classes differ.

*A wrong row of the translation table.* Extraction gives "MODIS MOUNTED_ON Aqua", which is right: MOUNTED_ON is the [current schema](../../docs/terminology.md#6-extracting-with-a-schema-step-060)'s word for ABOARD. But the table's row says MOUNTED_ON → ACQUIRED_BY. After translation the extracted triple reads "MODIS ACQUIRED_BY Aqua", while the ground truth says "MODIS ABOARD Aqua": the predicates differ, so it counts as not correct, though extraction did nothing wrong.

## Sources

The standard definition of precision, summed over all items before dividing (*micro-averaging*), as opposed to averaging per [record](../../docs/terminology.md#1-records-and-their-text) (*macro-averaging*): Manning, Raghavan & Schütze, *Introduction to Information Retrieval* (2008), sections 8.3 and 13.6 ([book](https://nlp.stanford.edu/IR-book/)). Micro-averaging fits precision's interpretation: every [extracted triple](../../docs/terminology.md#6-extracting-with-a-schema-step-060) weighs the same, as every [edge](../../docs/terminology.md#8-the-pipeline) would in the [knowledge graph](../../docs/terminology.md#8-the-pipeline). Macro-averaging answers another question (for a typical record, what proportion of its extracted triples is correct). The WebNLG+ 2020 challenge reports its text-to-triples scores macro-averaged (Castro Ferreira et al., 2020, Table 10, [paper](https://aclanthology.org/2020.webnlg-1.7.pdf)), so our numbers aren't directly comparable with its published ones.
