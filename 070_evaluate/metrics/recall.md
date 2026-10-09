# Recall

Part of [Evaluation metrics](../metrics.md), which explains the notation and lists every metric.

## <ins>Definition</ins>

The proportion of the [ground truth triples](../../docs/terminology.md#4-ground-truth-and-samples) that extraction found. What "found" means depends on the version.

## <ins>Formula</ins>

Four versions.

| Version | A ground truth triple counts as found when it… | Formula |
|---|---|---|
| exact recall | forms an [exact pair](pairs.md) | \|exact pairs\| ÷ \|ground truth triples\| |
| partial recall | forms an exact or a [partial pair](pairs.md) | \|exact pairs ∪ partial pairs\| ÷ \|ground truth triples\| |
| strict exact recall | (forms an exact pair) ∧ (the pair is strict) | \|exact pairs ∩ [strict pairs](pairs.md)\| ÷ \|ground truth triples\| |
| strict partial recall | (forms an exact or a partial pair) ∧ (the pair is strict) | \|(exact pairs ∪ partial pairs) ∩ strict pairs\| ÷ \|ground truth triples\| |

Each version is a number from 0 to 1; with no ground truth triples across the [records](../../docs/terminology.md#1-records-and-their-text), it is undefined.

## <ins>Interpretations</ins>

Let *r* be the value of one version of recall. It reads two ways: what was computed, on the evaluated records, and what it means for the [knowledge graph](../../docs/terminology.md#8-the-pipeline), for the whole catalog. Each item of the second is the counterpart of the item with the same number in the first.

**What was computed** (the evaluated records)

1. *r* is the proportion of the evaluated records' ground truth triples that are found, where "found" is defined by the version (table above).
2. Partial recall minus exact recall is the proportion of the ground truth triples that form a partial pair.
3. Recall minus strict recall, at the same [pair level](pairs.md), is the proportion of the ground truth triples that form a pair at that level but not a strict one.

**What it means for the knowledge graph** (the whole catalog, approximately)

Say the knowledge graph is built from the whole catalog's [extracted triples](../../docs/terminology.md#6-extracting-with-a-schema-step-060). Of the facts the catalog's records state, each counted once per record that states it:

1. approximately *r* would be in the graph;
2. approximately (partial recall minus exact recall) would be in it only with (the subject's [node](../../docs/terminology.md#8-the-pipeline) named differently from the [ground truth](../../docs/terminology.md#4-ground-truth-and-samples)) ∨ (the object's node named differently from the ground truth);
3. approximately (recall minus strict recall) would be in it, at that pair level, only with (the subject's node of the wrong [entity class](../../docs/terminology.md#3-schemas)) ∨ (the object's node of the wrong entity class).

## <ins>Assumes and can't see</ins>

- That the ground truth lists every fact the records state: a fact missing from it isn't counted at all, neither found nor missed. So recall is likely overstated. The ground truth starts as a model's draft (step 050), and people correcting a model's suggestions tend to keep them, so the draft's gaps tend to stay in the ground truth; and models tend to make the same mistakes, so an extraction model tends to miss what the drafting model missed. Sources: [Recall: sources](#sources).
- Not found means not in a pair the version counts, which isn't the same as missed by extraction: see *When a ground truth triple counts as not found*, below. The opposite mistake happens too: see [Pairs](pairs.md), *When a pair isn't the same fact*.
- *What it means for the knowledge graph* is approximate for the [reasons every metric shares](approximately.md); the report measures one of them, sampling error, with *r*'s [margin of error](approximately.md#sampling-error). Unlike precision's, it doesn't depend on graph building: merging repeated extracted triples into one edge changes how many edges there are, not which facts the graph holds.
- *r* counts a fact once per record that states it. The proportion of distinct facts the knowledge graph holds, each counted once, is a different number, and can differ from *r*. Example: [Recall: example](#example), *Ground truth triples vs distinct facts*.
- Alone, *r* can be fooled: read it with [precision](precision.md) (see [F1](f1.md), *Interpretations*).

## <ins>When a ground truth triple counts as not found</ins>

Under a version, a ground truth triple counts as not found in exactly two situations: (A) it has no partner at all (it is ground truth only), or (B) it has a partner, but the version doesn't count that kind of pair. A fact missing from the ground truth is never counted at all, so it isn't here (see *Assumes and can't see*).

| # | Cause | Example | Versions it lowers | Whose doing | Is "not found" the right verdict? | What to do |
|---|---|---|---|---|---|---|
| | **(A) No partner** | | | | | |
| 1 | Extraction didn't state the fact | the text says MODIS is aboard Aqua; no extracted triple says it | all | extraction | yes | improve extraction (prompt, model, schema) |
| 2 | Extraction stated it, but step 060 removed that extracted triple | its [source text](../../docs/terminology.md#1-records-and-their-text) was copied slightly wrong, so a check removed it | all | 060's checks | no | read `outputs/intermediate_results/060_extract/extracted_triples_removed.csv`; if many removed extracted triples are true, loosen the check |
| 3 | Outside the schema's reach: no [component class](../../docs/terminology.md#3-schemas) of the [current schema](../../docs/terminology.md#6-extracting-with-a-schema-step-060) translates to its [predicate](../../docs/terminology.md#3-schemas) | the ground truth says LAUNCHED_BY; the current schema has nothing like it | all | the current schema | no: extraction couldn't state it | add the predicate to the schema (from tuning records or outside knowledge); the [recall upper bound](recall_upper_bound.md) measures how often this happens |
| 4 | The same fact in different words | ground truth "MODIS" ABOARD "Aqua"; extracted "the imaging spectroradiometer" ABOARD "the Aqua satellite" ([Pairs: example](pairs.md#example), *The same fact in different words*) | all | pairing (it can't see synonyms) | no | Raise With Mentors: check a sample of the occurrences left extracted only (`070_evaluate/070_evaluate.md`, *To do*) |
| 5 | A near-repeat in the ground truth | the ground truth has "MODIS" ABOARD "Aqua" and "the MODIS instrument" ABOARD "Aqua"; extraction states the fact once, so only one of them can pair (*A repeated fact*, below) | all | ground truth | no | delete one of the two from the ground truth |
| 6 | The ground truth triple is wrong | the text doesn't state it | all | ground truth | no: it isn't a fact | fix the ground truth |
| 7 | Facts split differently | the ground truth has "MODIS and AIRS" ABOARD "Aqua", where extraction has two [classed triples](../../docs/terminology.md#2-triples) | all | whichever side broke the rule "one fact per classed triple" | yes if extraction broke it; no if the ground truth did | improve extraction, or split the ground truth's classed triple |
| 8 | A wrong predicate row of the [translation table](../../docs/terminology.md#7-evaluating-extraction-step-070) | MOUNTED_ON → ACQUIRED_BY, or → `(none)`, where it should be ABOARD (*A wrong row of the translation table*, below) | all | translation table | no | fix the row (the report's *Component class mismatches* shows it) |
| 9 | You marked the partial pair "not the same fact" | "MODIS" vs "MODIS Terra" | partial versions | your review | yes, unless the review was wrong | if it was wrong, take the verdict back ([annotation tool](../../docs/terminology.md#4-ground-truth-and-samples), *Partial pairs*) |
| | **(B) A partner the version doesn't count** | | | | | |
| 10 | A partial pair, under an exact version | "MODIS" vs "Moderate Resolution Imaging Spectroradiometer (MODIS)" | exact versions | none: the version asks for the same [subject instance](../../docs/terminology.md#2-triples) and [object instance](../../docs/terminology.md#2-triples) | yes, by the version's definition | nothing: the partial versions count it |
| 11 | A wrong entity class, from extraction | extracted (Dataset), where the ground truth has (Instrument) (*A wrong component class*, below) | strict versions | extraction | yes | improve extraction |
| 12 | A wrong entity class in the ground truth | the ground truth says (Dataset) by mistake | strict versions | ground truth | no | fix the ground truth |
| 13 | A wrong entity-class row of the translation table | `Satellite` → `Mission`, or → `(none)`, where it should be `Spacecraft` | strict versions | translation table | no | fix the row |
| 14 | Outside strict reach: no component class of the current schema translates to its entity class | the ground truth uses `Sensor`; the current schema has only `Instrument`, which translates to `Instrument` | strict versions | the two vocabularies differ | no | add the entity class to the schema, or accept it as a known limit (`070_evaluate/070_evaluate.md`, *Known limits*: one translation per component class) |

Worked example: [Recall: example](#example). Sources: [Recall: sources](#sources).

## Example

*Micro-averaging.* [Record](../../docs/terminology.md#1-records-and-their-text) A: the [ground truth](../../docs/terminology.md#4-ground-truth-and-samples) has 5 [classed triples](../../docs/terminology.md#2-triples), 3 of them found. Record B: it has 2, 1 found. Recall = (3 + 1) ÷ (5 + 2) = 57%. Averaging the records' own recalls (60% and 50%) would give 55% instead, letting record B's 2 [ground truth triples](../../docs/terminology.md#4-ground-truth-and-samples) weigh as much as record A's 5. This holds for every version: only what "found" means changes, that is, which [pairs](pairs.md) count (by [pair level](pairs.md): exact, or exact or partial; by strictness: any, or strict only; see the table under *Formula*).

*Ground truth triples vs distinct facts.* 3 records each state "MODIS" ABOARD "Aqua", and extraction finds it in all 3; 1 record states "AIRS" ABOARD "Terra", and extraction misses it. Recall = 3 ÷ 4 = 75%. Counting each [fact](../../docs/terminology.md#2-triples) once per record that states it, the [knowledge graph](../../docs/terminology.md#8-the-pipeline) holds 3 of 4: 75%, as *r* says, whether or not graph building merges the 3 repeats into one [edge](../../docs/terminology.md#8-the-pipeline). Counting distinct facts, it holds 1 of 2: 50%, also whether or not the repeats are merged.

*A repeated fact.* The ground truth of one record lists the same fact twice: "MODIS ABOARD Aqua" and "the MODIS instrument ABOARD Aqua". Extraction gives it once. Its occurrence pairs with one of them; the other has no partner left, so it counts as not found, though extraction found the fact.

*A wrong component class.* The ground truth has "MODIS (Instrument) ABOARD Aqua (Spacecraft)". Extraction gives "MODIS (Dataset) ABOARD Aqua (Spacecraft)": the same fact, with the wrong [subject class](../../docs/terminology.md#2-triples). For strict exact recall the ground truth triple counts as not found, since the subject classes differ; the mistake is extraction's.

*A wrong row of the translation table.* The ground truth has "MODIS ABOARD Aqua". Extraction gives "MODIS MOUNTED_ON Aqua", which is right, but the table's row says MOUNTED_ON → ACQUIRED_BY. Its [translated extracted triple](../../docs/terminology.md#7-evaluating-extraction-step-070) reads "MODIS ACQUIRED_BY Aqua": the predicates differ, so the ground truth triple counts as not found, though extraction found it.

## Sources

The standard definition of recall, micro-averaged like [precision](precision.md): Manning, Raghavan & Schütze (2008), sections 8.3 and 13.6. The WebNLG+ 2020 challenge reports recall macro-averaged (Castro Ferreira et al., 2020, Table 10), so our numbers aren't directly comparable with its published ones.

Why recall is likely overstated (*Assumes and can't see*):

- People correcting a model's suggestions tend to keep them: Schroeder, Roy & Kabbara, "Just Put a Human in the Loop? Investigating LLM-Assisted Annotation for Subjective Tasks", Findings of ACL 2025 ([paper](https://aclanthology.org/2025.findings-acl.1323/)): annotators "strongly took the LLM suggestions", and evaluating LLMs on those labels made their reported performance "significantly increase". Their tasks were subjective; ours is not, so the size of the effect may differ.
- Models tend to make the same mistakes: Kim, Garg, Peng & Garg, "Correlated Errors in Large Language Models", ICML 2025 ([paper](https://arxiv.org/abs/2506.07962)): across more than 350 models, when two models both err they agree 60% of the time, and larger, more accurate models have highly correlated errors even across providers.
