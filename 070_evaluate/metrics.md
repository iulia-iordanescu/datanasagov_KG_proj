# Evaluation metrics

The one place each of evaluation's numbers is explained: what it is, its formula with an example, how to read it, what it assumes, and where it comes from. Other files point here instead of repeating it. Each metric's worked example is under *Examples*, and where it comes from under *Sources*, at the end. Terms: [docs/terminology.md](../docs/terminology.md).

Contents:

- [What the metrics count: pairs](#what-the-metrics-count-pairs)
- [The metrics](#the-metrics): [Precision](#precision), [Recall](#recall), [F1](#f1), [Entity-class accuracy](#entity-class-accuracy), [Recall upper bound](#recall-upper-bound)
- [Why "approximately": reasons every metric shares](#why-approximately-reasons-every-metric-shares)
- [Examples](#examples), [Sources](#sources)

Formulas use the usual set symbols: \|…\| is the number of members, ∪ is union (in either), ∩ is intersection (in both). Between statements, ∨ is the inclusive or (one, the other, or both) and ∧ is and (both). Every count is over all the evaluated [records](../docs/terminology.md#1-records-and-their-text) of one part (tuning or held-out) together, not one record at a time, and never includes the [DESCRIBES rows](../docs/terminology.md#2-triples) (they're compared on their own: see the describes metrics in [`070_evaluate.md`](070_evaluate.md), until they get a section here).

## What the metrics count: pairs

### <ins>Definition</ins>

A **pair** is one [extracted triple](../docs/terminology.md#6-extracting-with-a-schema-step-060) and one [ground truth triple](../docs/terminology.md#4-ground-truth-and-samples) of the same [record](../docs/terminology.md#1-records-and-their-text) that evaluation takes to state the same [fact](../docs/terminology.md#2-triples), once the extracted triple's [predicate](../docs/terminology.md#3-schemas), [subject class](../docs/terminology.md#2-triples) and [object class](../docs/terminology.md#2-triples) are translated into the [ground truth vocabulary](../docs/terminology.md#7-evaluating-extraction-step-070) (through the [translation table](../docs/terminology.md#7-evaluating-extraction-step-070), [`annotations/component_class_mapping.csv`](../annotations/component_class_mapping.csv)). Each [triple](../docs/terminology.md#2-triples) has at most one partner. Evaluation finds the largest possible set of exact pairs, then, among the triples left, the largest possible set of partial pairs. There are two **pair levels**, exact and partial, and when two triples count as stating the same fact depends on the level: they form an **exact pair** or a **partial pair**.

Two triples count as stating the same fact when, at the…

- **exact pair level**, all three hold:
  - the same predicate;
  - the same [subject instance](../docs/terminology.md#2-triples), once [evened out](../docs/terminology.md#2-triples);
  - the same [object instance](../docs/terminology.md#2-triples), once evened out.
- **partial pair level** (only for triples left without an exact partner), all three hold:
  - the same predicate;
  - (the two subject instances are equal) ∨ (one appears inside the other as whole words, either way round);
  - (the two object instances are equal) ∨ (one appears inside the other as whole words, either way round).

Strict is an extra condition on a pair at either level: a **strict pair** is an exact or partial pair with (the same subject classes) ∧ (the same object classes).

So every pair is exactly one of these four:

| | strict ((same subject classes) ∧ (same object classes)) | not strict |
|---|---|---|
| exact pair | exact pairs ∩ strict pairs | exact pairs, not strict |
| partial pair | partial pairs ∩ strict pairs | partial pairs, not strict |

All pairs = exact pairs ∪ partial pairs (no pair is both). Strict pairs are some of each.

A triple left without a partner is **extracted only** (an extracted triple) or **[ground truth](../docs/terminology.md#4-ground-truth-and-samples) only** (a ground truth triple).

### <ins>Assumes and can't see</ins>

- Containment can be fooled: "MODIS" is inside "MODIS Terra", a different instrument. On tuning records you review partial pairs in the [annotation tool](../docs/terminology.md#4-ground-truth-and-samples) (*Partial pairs*); two triples marked "not the same fact" are never paired. Held-out records' partial pairs are never reviewed (that would mean looking at them).
- Two [component classes](../docs/terminology.md#3-schemas) of the [current schema](../docs/terminology.md#6-extracting-with-a-schema-step-060) that translate to one component class of the ground truth vocabulary can't be told apart.

Worked example: [Pairs: example](#pairs-example). Sources: [Pairs: sources](#pairs-sources).

## The metrics

### Precision

#### <ins>Definition</ins>

The proportion of the [extracted triples](../docs/terminology.md#6-extracting-with-a-schema-step-060) that are correct. What "correct" means depends on the version.

#### <ins>Formula</ins>

Four versions.

| Version | An extracted triple counts as correct when it… | Formula |
|---|---|---|
| exact precision | forms an exact [pair](#what-the-metrics-count-pairs) | \|exact pairs\| ÷ \|extracted triples\| |
| partial precision | forms an exact or a partial pair | \|exact pairs ∪ partial pairs\| ÷ \|extracted triples\| |
| strict exact precision | (forms an exact pair) ∧ (the pair is strict) | \|exact pairs ∩ strict pairs\| ÷ \|extracted triples\| |
| strict partial precision | (forms an exact or a partial pair) ∧ (the pair is strict) | \|(exact pairs ∪ partial pairs) ∩ strict pairs\| ÷ \|extracted triples\| |

Each version is a number from 0 to 1; with no extracted triples across the [records](../docs/terminology.md#1-records-and-their-text), it is undefined.

In every version, an extracted triple is not correct when one or more of these hold:

- the [text](../docs/terminology.md#1-records-and-their-text) doesn't state the [fact](../docs/terminology.md#2-triples) (a mistake of extraction);
- it repeats a fact already extracted (a mistake of extraction): another extracted triple of the same record could pair with the same [ground truth triple](../docs/terminology.md#4-ground-truth-and-samples) at this pair level (see [*What the metrics count: pairs*](#what-the-metrics-count-pairs)). A triple has at most one partner, so only one of the two forms a pair. Example: [Precision: example](#precision-example), *A repeated fact*;
- it's true but missing from the [ground truth](../docs/terminology.md#4-ground-truth-and-samples) (a mistake in the ground truth);
- it states the same fact as a ground truth triple, but differs from it, after translation, as the table below says. That comes from (a mistake of extraction) ∨ (a wrong row of the [translation table](../docs/terminology.md#7-evaluating-extraction-step-070), which can turn a correct triple into a wrong one) ∨ (a mistake in the ground truth triple). Examples: [Precision: example](#precision-example), *A wrong component class* and *A wrong row of the translation table*.

| Version | An extracted triple is also not correct when… |
|---|---|
| exact precision | (its predicate differs) ∨ (its [subject instance](../docs/terminology.md#2-triples) differs, once [evened out](../docs/terminology.md#2-triples)) ∨ (its [object instance](../docs/terminology.md#2-triples) differs, once evened out) |
| partial precision | (its predicate differs) ∨ (its subject instance neither equals the ground truth triple's subject instance, nor contains it, nor is contained in it, as whole words) ∨ (its object instance neither equals the ground truth triple's object instance, nor contains it, nor is contained in it, as whole words) |
| strict exact precision | (its predicate differs) ∨ (its subject instance differs, once evened out) ∨ (its object instance differs, once evened out) ∨ (its [subject class](../docs/terminology.md#2-triples) differs) ∨ (its [object class](../docs/terminology.md#2-triples) differs) |
| strict partial precision | (its predicate differs) ∨ (its subject instance neither equals the ground truth triple's subject instance, nor contains it, nor is contained in it, as whole words) ∨ (its object instance neither equals the ground truth triple's object instance, nor contains it, nor is contained in it, as whole words) ∨ (its subject class differs) ∨ (its object class differs) |

#### <ins>Interpretations</ins>

Let *p* be the value of one version of precision. It reads two ways: what was computed, on the evaluated records, and what it means for the [knowledge graph](../docs/terminology.md#8-the-pipeline), for the whole catalog. Each item of the second is the counterpart of the item with the same number in the first.

**What was computed** (the evaluated records)

1. *p* is the proportion of the evaluated records' extracted triples that are correct, where "correct" is defined by the version (table above).
2. Partial precision minus exact precision is the proportion of the extracted triples that form a partial pair but not an exact pair. In such a pair, the two [triples](../docs/terminology.md#2-triples) have the same [predicate](../docs/terminology.md#3-schemas), but (their subject instances are worded differently, one inside the other as whole words) ∨ (their object instances are worded differently, one inside the other as whole words) (e.g. "MODIS" vs "Moderate Resolution Imaging Spectroradiometer (MODIS)").
3. Precision minus strict precision, at the same pair level, is the proportion of the extracted triples that form a pair at that level but not a strict one. In such a pair, (the two triples' subject classes differ) ∨ (the two triples' object classes differ).

**What it means for the knowledge graph** (the whole catalog, approximately)

Say the knowledge graph is built from the whole catalog's extracted triples, one [edge](../docs/terminology.md#8-the-pipeline) per extracted triple. Then:

1. Approximately 1 − *p* of its edges would not be correct.
2. Approximately (partial precision minus exact precision) of its edges would state a fact the ground truth also states, by partial pairing, but with (the subject's [node](../docs/terminology.md#8-the-pipeline) named differently from the ground truth) ∨ (the object's node named differently from the ground truth), e.g. a node "Moderate Resolution Imaging Spectroradiometer (MODIS)" where the ground truth says "MODIS".
3. Approximately (precision minus strict precision) of its edges would state a fact the ground truth also states, at that pair level, but with (the subject's node of the wrong [entity class](../docs/terminology.md#3-schemas)) ∨ (the object's node of the wrong entity class).

#### <ins>Assumes and can't see</ins>

- That the ground truth lists every fact the records state: an extracted triple that is true but missing from the ground truth counts as not correct, so it lowers *p*.
- *What it means for the knowledge graph* is approximate for two kinds of reason:
  - the [reasons every metric shares](#why-approximately-reasons-every-metric-shares); the [report](../docs/terminology.md#8-the-pipeline) measures one of them, sampling error, with *p*'s [margin of error](#sampling-error);
  - one of precision's own: if graph building ([step](../docs/terminology.md#8-the-pipeline) 080, not built yet) merges repeated extracted triples into one edge, the proportions of edges above can differ from what was computed. Merging turns a fact that many records state into one edge, but leaves a fact that one record states as one edge. Example: [Precision: example](#precision-example), *Triples vs distinct facts*.
- Alone, *p* can be fooled: read it with [recall](#recall) (see *F1*, *Interpretations*).

Worked example: [Precision: example](#precision-example). Sources: [Precision: sources](#precision-sources).

### Recall

#### <ins>Definition</ins>

The proportion of the [ground truth triples](../docs/terminology.md#4-ground-truth-and-samples) that extraction found. What "found" means depends on the version.

#### <ins>Formula</ins>

Four versions.

| Version | A ground truth triple counts as found when it… | Formula |
|---|---|---|
| exact recall | forms an exact [pair](#what-the-metrics-count-pairs) | \|exact pairs\| ÷ \|ground truth triples\| |
| partial recall | forms an exact or a partial pair | \|exact pairs ∪ partial pairs\| ÷ \|ground truth triples\| |
| strict exact recall | (forms an exact pair) ∧ (the pair is strict) | \|exact pairs ∩ strict pairs\| ÷ \|ground truth triples\| |
| strict partial recall | (forms an exact or a partial pair) ∧ (the pair is strict) | \|(exact pairs ∪ partial pairs) ∩ strict pairs\| ÷ \|ground truth triples\| |

Each version is a number from 0 to 1; with no ground truth triples across the [records](../docs/terminology.md#1-records-and-their-text), it is undefined.

In every version, a ground truth triple is not found when one or more of these hold:

- the [text](../docs/terminology.md#1-records-and-their-text) doesn't state the fact (a mistake in the [ground truth](../docs/terminology.md#4-ground-truth-and-samples));
- it repeats a fact the ground truth already lists (a mistake in the ground truth): another ground truth triple of the same record could pair with the same [extracted triple](../docs/terminology.md#6-extracting-with-a-schema-step-060) at this pair level (see [*What the metrics count: pairs*](#what-the-metrics-count-pairs)). A triple has at most one partner, so only one of the two forms a pair. Example: [Recall: example](#recall-example), *A repeated fact*;
- no extracted triple states the fact (a mistake of extraction, or a limit of the [current schema](../docs/terminology.md#6-extracting-with-a-schema-step-060): see [Recall upper bound](#recall-upper-bound));
- an extracted triple states the same fact, but differs from it, after translation, as the table below says. That comes from (a mistake of extraction) ∨ (a wrong row of the [translation table](../docs/terminology.md#7-evaluating-extraction-step-070), which can turn a correct extracted triple into a wrong one) ∨ (a mistake in the ground truth triple). Examples: [Recall: example](#recall-example), *A wrong component class* and *A wrong row of the translation table*.

| Version | A ground truth triple is also not found when… |
|---|---|
| exact recall | (the extracted triple's predicate differs from its predicate) ∨ (the extracted triple's [subject instance](../docs/terminology.md#2-triples) differs from its subject instance, once [evened out](../docs/terminology.md#2-triples)) ∨ (the extracted triple's [object instance](../docs/terminology.md#2-triples) differs from its object instance, once evened out) |
| partial recall | (the extracted triple's predicate differs from its predicate) ∨ (the extracted triple's subject instance neither equals its subject instance, nor contains it, nor is contained in it, as whole words) ∨ (the extracted triple's object instance neither equals its object instance, nor contains it, nor is contained in it, as whole words) |
| strict exact recall | (the extracted triple's predicate differs from its predicate) ∨ (the extracted triple's subject instance differs from its subject instance, once evened out) ∨ (the extracted triple's object instance differs from its object instance, once evened out) ∨ (the extracted triple's [subject class](../docs/terminology.md#2-triples) differs from its subject class) ∨ (the extracted triple's [object class](../docs/terminology.md#2-triples) differs from its object class) |
| strict partial recall | (the extracted triple's predicate differs from its predicate) ∨ (the extracted triple's subject instance neither equals its subject instance, nor contains it, nor is contained in it, as whole words) ∨ (the extracted triple's object instance neither equals its object instance, nor contains it, nor is contained in it, as whole words) ∨ (the extracted triple's subject class differs from its subject class) ∨ (the extracted triple's object class differs from its object class) |

#### <ins>Interpretations</ins>

Let *r* be the value of one version of recall. It reads two ways: what was computed, on the evaluated records, and what it means for the [knowledge graph](../docs/terminology.md#8-the-pipeline), for the whole catalog. Each item of the second is the counterpart of the item with the same number in the first.

**What was computed** (the evaluated records)

1. *r* is the proportion of the evaluated records' ground truth triples that are found, where "found" is defined by the version (table above).
2. Partial recall minus exact recall is the proportion of the ground truth triples that form a partial pair but not an exact pair. In such a pair, the two [triples](../docs/terminology.md#2-triples) have the same [predicate](../docs/terminology.md#3-schemas), but (their subject instances are worded differently, one inside the other as whole words) ∨ (their object instances are worded differently, one inside the other as whole words) (e.g. "MODIS" vs "Moderate Resolution Imaging Spectroradiometer (MODIS)").
3. Recall minus strict recall, at the same pair level, is the proportion of the ground truth triples that form a pair at that level but not a strict one. In such a pair, (the two triples' subject classes differ) ∨ (the two triples' object classes differ).

**What it means for the knowledge graph** (the whole catalog, approximately)

Say the knowledge graph is built from the whole catalog's extracted triples. Of the facts the catalog's records state, each counted once per record that states it:

1. approximately *r* would be in the graph;
2. approximately (partial recall minus exact recall) would be in it only with (the subject's [node](../docs/terminology.md#8-the-pipeline) named differently from the ground truth) ∨ (the object's node named differently from the ground truth);
3. approximately (recall minus strict recall) would be in it, at that pair level, only with (the subject's node of the wrong [entity class](../docs/terminology.md#3-schemas)) ∨ (the object's node of the wrong entity class).

#### <ins>Assumes and can't see</ins>

- That the ground truth lists every fact the records state: a fact missing from it isn't counted at all, neither found nor missed.
- *What it means for the knowledge graph* is approximate for the [reasons every metric shares](#why-approximately-reasons-every-metric-shares); the report measures one of them, sampling error, with *r*'s [margin of error](#sampling-error). Unlike precision's, it doesn't depend on graph building: merging repeated extracted triples into one edge changes how many edges there are, not which facts the graph holds.
- *r* counts a fact once per record that states it. The proportion of distinct facts the knowledge graph holds, each counted once, is a different number, and can differ from *r*. Example: [Recall: example](#recall-example), *Triples vs distinct facts*.
- Alone, *r* can be fooled: read it with [precision](#precision) (see *F1*, *Interpretations*).

Worked example: [Recall: example](#recall-example). Sources: [Recall: sources](#recall-sources).

### F1

#### <ins>Definition</ins>

[Precision](#precision) and [recall](#recall) combined into one number, high only when both are.

#### <ins>Formula</ins>

Four versions, each from the precision and recall of the same version.

| Version | Formula |
|---|---|
| exact F1 | 2 × exact precision × exact recall ÷ (exact precision + exact recall) |
| partial F1 | 2 × partial precision × partial recall ÷ (partial precision + partial recall) |
| strict exact F1 | 2 × strict exact precision × strict exact recall ÷ (strict exact precision + strict exact recall) |
| strict partial F1 | 2 × strict partial precision × strict partial recall ÷ (strict partial precision + strict partial recall) |

The code computes the same number as 2 × \|[pairs](#what-the-metrics-count-pairs) counted\| ÷ (\|[extracted triples](../docs/terminology.md#6-extracting-with-a-schema-step-060)\| + \|[ground truth triples](../docs/terminology.md#4-ground-truth-and-samples)\|), which also settles the edge cases: F1 is 0 when no pair is counted (even with no extracted triples, where precision is undefined).

Each version is a number from 0 to 1; with neither extracted triples nor ground truth triples across the [records](../docs/terminology.md#1-records-and-their-text), it is undefined.

#### <ins>Interpretations</ins>

Let *f* be the value of one version of F1. Then, *f* is the harmonic mean of that version's precision and recall: a kind of average, pulled toward the lower of the two (example: [F1: example](#f1-example)).

- Why one number: precision and recall can each be fooled alone. An extractor that states just one [triple](../docs/terminology.md#2-triples) it is sure of gets high precision and almost no recall; one that states everything it can think of gets high recall and low precision. *f* is high only when both are.
- The usual headline number for comparing [runs](../docs/terminology.md#8-the-pipeline) or [models](../docs/terminology.md#8-the-pipeline), and for comparing with published results.

#### <ins>Assumes and can't see</ins>

- It weighs precision and recall equally. If one matters more (for a graph, a wrong statement is often worse than a missing one), read precision and recall themselves.
- It doesn't show which of the two is low.
- Read for the whole catalog, *f* is approximate for the the [reasons every metric shares](#why-approximately-reasons-every-metric-shares); the [report](../docs/terminology.md#8-the-pipeline) measures one of them, sampling error, with *f*'s [margin of error](#sampling-error).

Worked example: [F1: example](#f1-example). Sources: [F1: sources](#f1-sources).

### Entity-class accuracy

#### <ins>Definition</ins>

Among the [pairs](#what-the-metrics-count-pairs) counted, the proportion that are strict. Which pairs are counted depends on the version.

#### <ins>Formula</ins>

Two versions.

| Version | Pairs counted | Formula |
|---|---|---|
| exact entity-class accuracy | exact pairs | \|exact pairs ∩ strict pairs\| ÷ \|exact pairs\| |
| partial entity-class accuracy | exact pairs ∪ partial pairs | \|(exact pairs ∪ partial pairs) ∩ strict pairs\| ÷ \|exact pairs ∪ partial pairs\| |

Each version is a number from 0 to 1; with no pairs counted across the [records](../docs/terminology.md#1-records-and-their-text), it is undefined.

#### <ins>Interpretations</ins>

Let *a* be the value of one version of entity-class accuracy. Then, *a* is the proportion of the pairs counted that are strict, where the pairs counted are defined by the version (table above). So of the [knowledge graph](../docs/terminology.md#8-the-pipeline)'s correct [edges](../docs/terminology.md#8-the-pipeline), approximately *a* would also have both [nodes](../docs/terminology.md#8-the-pipeline)' [entity classes](../docs/terminology.md#3-schemas) right.

- Read with [precision](#precision) and [recall](#recall): they say whether [facts](../docs/terminology.md#2-triples) are found; this says whether the things in them are classed right.

#### <ins>Assumes and can't see</ins>

- Only paired [triples](../docs/terminology.md#2-triples) are judged: the [subject class](../docs/terminology.md#2-triples) and [object class](../docs/terminology.md#2-triples) of a triple without a partner aren't counted anywhere.
- Two [component classes](../docs/terminology.md#3-schemas) of the [current schema](../docs/terminology.md#6-extracting-with-a-schema-step-060) that translate to one component class of the [ground truth vocabulary](../docs/terminology.md#7-evaluating-extraction-step-070) look the same, so mixing them up isn't seen.
- Above, *Interpretations* states that approximately *a* of the knowledge graph's correct edges would also have both nodes' entity classes right, where *a* is any one version of entity-class accuracy. It is approximate for two kinds of reason:
  - the [reasons every metric shares](#why-approximately-reasons-every-metric-shares); the [report](../docs/terminology.md#8-the-pipeline) measures one of them, sampling error, with *a*'s [margin of error](#sampling-error);
  - one of its own: if graph building ([step](../docs/terminology.md#8-the-pipeline) 080, not built yet) merges repeated [extracted triples](../docs/terminology.md#6-extracting-with-a-schema-step-060) into one edge, the proportion of correct edges whose entity classes are right can differ from *a*, for the reason given under *Precision*, *Assumes and can't see*.

Worked example: [Entity-class accuracy: example](#entity-class-accuracy-example). Sources: [Entity-class accuracy: sources](#entity-class-accuracy-sources).

### Recall upper bound

#### <ins>Definition</ins>

The proportion of the [ground truth triples](../docs/terminology.md#4-ground-truth-and-samples) that the [current schema](../docs/terminology.md#6-extracting-with-a-schema-step-060) can express at all: the most recall any extraction with this [schema](../docs/terminology.md#3-schemas) and [translation table](../docs/terminology.md#7-evaluating-extraction-step-070) could get. A ground truth triple is **within reach** when its [predicate](../docs/terminology.md#3-schemas) is one that some checked row of the translation table translates to. It is **within strict reach** when (it is within reach) ∧ (its [subject class](../docs/terminology.md#2-triples) is one that some checked row translates to) ∧ (its [object class](../docs/terminology.md#2-triples) is one that some checked row translates to). Which ground truth triples count depends on the version.

#### <ins>Formula</ins>

Two versions.

| Version | A ground truth triple counts when it is… | Formula |
|---|---|---|
| recall upper bound | within reach | \|ground truth triples within reach\| ÷ \|ground truth triples\| |
| strict recall upper bound | within strict reach | \|ground truth triples within strict reach\| ÷ \|ground truth triples\| |

Each version is a number from 0 to 1; with no ground truth triples across the [records](../docs/terminology.md#1-records-and-their-text), it is undefined.

#### <ins>Interpretations</ins>

Let *u* be the value of one version of the recall upper bound. Then, *u* is the proportion of ground truth triples within reach (for the strict version, within strict reach). So no extraction with this schema and translation table can get a recall (for the strict version, a strict recall) above *u*: the other 1 − *u* of the ground truth triples use a [component class](../docs/terminology.md#3-schemas) the current schema has no counterpart for.

- Read with recall: the gap between the two is what extraction missed although the schema could express it.
- A low upper bound points at the schema (schema induction, or the [schema additions](../docs/terminology.md#3-schemas)) or at the translation table (a row that says `(none)`, or a missing row).
- The strict version is the limit for strict recall: a [triple](../docs/terminology.md#2-triples) can be within reach but not within strict reach when (the schema has no counterpart for its subject class) ∨ (it has none for its object class).

#### <ins>Assumes and can't see</ins>

- Within reach means only that the schema has the component classes: not that the [model](../docs/terminology.md#8-the-pipeline) could find the [fact](../docs/terminology.md#2-triples) in the [text](../docs/terminology.md#1-records-and-their-text).
- It depends on the translation table: a row wrongly saying `(none)` lowers it.
- Read for the whole catalog, *u* is approximate for the the [reasons every metric shares](#why-approximately-reasons-every-metric-shares); the [report](../docs/terminology.md#8-the-pipeline) measures one of them, sampling error, with *u*'s [margin of error](#sampling-error).

Worked example: [Recall upper bound: example](#recall-upper-bound-example). Sources: [Recall upper bound: sources](#recall-upper-bound-sources).

## Why "approximately": reasons every metric shares

Every metric is computed on the evaluated [records](../docs/terminology.md#1-records-and-their-text) only (the [fair sample](../docs/terminology.md#4-ground-truth-and-samples) of finished, extracted records). Reading it for the whole catalog assumes two things:

- the evaluated records are a random sample of the catalog (only the fair sample is evaluated);
- the pipeline wasn't adjusted to these records (true of the [held-out part](../docs/terminology.md#7-evaluating-extraction-step-070) until it is looked at).

Even then, every metric is approximate for the whole catalog, for the five reasons below. Each has the same parts: what it means, and how the [report](../docs/terminology.md#8-the-pipeline) checks or limits it. A metric with reasons of its own lists them in its own section, under *Assumes and can't see*. Sources for all five: [Why "approximately": sources](#why-approximately-sources).

### Sampling error

**What it means.** Another sample of the same size would give a somewhat different value.

**How the [report](../docs/terminology.md#8-the-pipeline) checks or limits it: the margin of error.** A range around each metric's value that says how much the value could change with another sample of the same size. Every metric gets one, except the describes baseline and the describes per-entity-class average. Example: [Sampling error: example](#sampling-error-example).

- **How it is computed**, by the bootstrap, with fixed numbers in `070_evaluate/070_evaluate_helpers/stats.py`:
  1. Redraw the evaluated [records](../docs/terminology.md#1-records-and-their-text): within each [stratum](../docs/terminology.md#4-ground-truth-and-samples), draw at random, with repeats, as many records as the stratum has. Whole records are drawn, never single [triples](../docs/terminology.md#2-triples).
  2. Compute the metric on the redrawn records, adding up their counts as on the real ones. A redraw where the metric is undefined (e.g. no [extracted triples](../docs/terminology.md#6-extracting-with-a-schema-step-060)) is skipped.
  3. Repeat 1,000 times (`REDRAWS`), from a fixed seed (`SEED = 70`), so a rerun gives the same range.
  4. The range is the middle 95% of the 1,000 values: from the 2.5th to the 97.5th percentile.

  With fewer than 20 evaluated records (`MIN_RECORDS`), no range is given.
- **How to read it.** Let *m* be the value of one metric, and *L* to *H* its range. The report says "for the whole catalog, *m* is likely between *L* and *H*".
  - A narrow range: another sample of the same size would give nearly the same value. A wide one: it could give quite a different value.
  - More evaluated records give a narrower range.
  - Two values whose ranges overlap a lot may differ only by chance.
- **What it assumes.** No distribution for the metric (e.g. not a normal one), but the following. The report checks each, in its section *The margin of error's assumptions, checked*, and warns when one doesn't hold.

  | Assumption | Why it matters | How the report checks it |
  |---|---|---|
  | The evaluated records are a random sample of the catalog | The redraws stand in for other samples of the catalog. | Only the [fair sample](../docs/terminology.md#4-ground-truth-and-samples) is evaluated (by design). |
  | Whole records vary, independently of each other | A record's triples come from one [text](../docs/terminology.md#1-records-and-their-text) and one [model call](../docs/terminology.md#8-the-pipeline), so they succeed or fail together; redrawing single triples would make the range too narrow. | Records are redrawn whole (by design). |
  | Enough records | With very few, the range is itself unreliable, usually too narrow. | No range below 20 evaluated records (a rule of thumb; no source found gives a number). |
  | Every stratum adds spread | A stratum with only 1 evaluated record puts that record in every redraw, so the range comes out too narrow. | Lists the strata with only 1 evaluated record. |
  | The range isn't at 0% or 100% | There, a percentile range is too narrow. | Lists the metrics whose range reaches 0% or 100%. |
  | No one record dominates | A record with most of the triples sways every redraw it's in. | Gives the largest record's proportion of the extracted triples and of the [ground truth triples](../docs/terminology.md#4-ground-truth-and-samples), for reading (no established threshold). |
  | A small proportion of the catalog is evaluated | Redrawing with repeats treats the catalog as endless; for a large proportion, the range comes out somewhat too wide. | Gives the proportion of the catalog evaluated; holds below 5%. |
- **What it can't see.** Only sampling error: the other four reasons can move the whole catalog's value outside the range.

### The sample's mix of maintainers

**What it means.** The [pool](../docs/terminology.md#4-ground-truth-and-samples) was drawn stratified by [maintainer](../docs/terminology.md#1-records-and-their-text), and only its first [finished records](../docs/terminology.md#4-ground-truth-and-samples) are evaluated. If their mix of maintainers differs from the catalog's, the value leans toward the over-represented maintainers.

**How the [report](../docs/terminology.md#8-the-pipeline) checks or limits it.**
- The pool matches the catalog's mix of maintainers: it was drawn with proportional allocation (`annotations/ground_truth_candidates.json`).
- The report's [strata](../docs/terminology.md#4-ground-truth-and-samples) table compares, per stratum, the proportion of the evaluated [records](../docs/terminology.md#1-records-and-their-text) with the proportion of the pool.
- From 20 evaluated records on, it warns when the two differ by more than 10 percentage points (`SHARE_GAP`). The 10 points is a rule of thumb, with no source found.

### Small-sample bias of a ratio

**What it means.** Each metric is a ratio of two counts that both vary from sample to sample. Such a ratio is slightly biased in small samples: averaged over many samples, it isn't exactly the whole catalog's value.

**How the [report](../docs/terminology.md#8-the-pipeline) checks or limits it.** It doesn't check it. The bias shrinks as the sample grows, faster than the sampling error does, so it is small next to the [margin of error](#sampling-error).

### Tuning on the evaluated records

**What it means.** Changes made after looking at the [tuning part](../docs/terminology.md#7-evaluating-extraction-step-070)'s numbers (to the [schema](../docs/terminology.md#3-schemas), the [schema additions](../docs/terminology.md#3-schemas), or the prompts) fit those [records](../docs/terminology.md#1-records-and-their-text), so the tuning part's numbers come out higher than the whole catalog's would.

**How the [report](../docs/terminology.md#8-the-pipeline) checks or limits it.** The [held-out part](../docs/terminology.md#7-evaluating-extraction-step-070): its numbers are shown only with the [setting](../docs/terminology.md#8-the-pipeline) `evaluate_held_out`, meant for the end, and each look is logged in `annotations/held_out_looks.csv`.

### An imperfect ground truth

**What it means.** "Correct" means having a partner in the [ground truth](../docs/terminology.md#4-ground-truth-and-samples). A [fact](../docs/terminology.md#2-triples) missing from it, or a mistake in it, shifts the value the same way in every sample.

**How the [report](../docs/terminology.md#8-the-pipeline) checks or limits it.** It doesn't: nothing in the numbers shows it. Only care in annotating limits it (see `050_annotate/050_annotate.md`).

## Examples

### Pairs: example

One [record](../docs/terminology.md#1-records-and-their-text). Its [ground truth triples](../docs/terminology.md#4-ground-truth-and-samples):

| | Subject instance (subject class) | Predicate | Object instance (object class) |
|---|---|---|---|
| G1 | MODIS (Instrument) | ABOARD | Aqua (Spacecraft) |
| G2 | AIRS (Instrument) | ABOARD | Aqua (Spacecraft) |
| G3 | MODIS Snow Cover (Dataset) | ACQUIRED_BY | MODIS (Instrument) |
| G4 | MODIS Snow Cover (Dataset) | HAS_TIME_SPAN | 2002–2023 (TimeSpan) |
| G5 | CERES (Instrument) | ABOARD | Aqua (Spacecraft) |

Its [extracted triples](../docs/terminology.md#6-extracting-with-a-schema-step-060), after translation, and what each becomes:

| | Subject instance (subject class) | Predicate | Object instance (object class) | Outcome |
|---|---|---|---|---|
| E1 | the MODIS (Instrument) | ABOARD | Aqua (Spacecraft) | exact [pair](#what-the-metrics-count-pairs) with G1 ("the" is ignored); strict |
| E2 | AIRS (Dataset) | ABOARD | Aqua (Spacecraft) | exact pair with G2; not strict ([subject class](../docs/terminology.md#2-triples) Dataset, not Instrument) |
| E3 | MODIS Snow Cover 5-Min L2 Swath (Dataset) | ACQUIRED_BY | Moderate Resolution Imaging Spectroradiometer (MODIS) (Instrument) | partial pair with G3 ("MODIS Snow Cover" is inside the [subject instance](../docs/terminology.md#2-triples), "MODIS" inside the [object instance](../docs/terminology.md#2-triples)); strict |
| E4 | MODIS Snow Cover (Dataset) | HAS_TIME_SPAN | the period 2002–2023 (Dataset) | partial pair with G4 ("2002–2023" is inside the object instance); not strict ([object class](../docs/terminology.md#2-triples) Dataset, not TimeSpan) |
| E5 | MODIS (Instrument) | ABOARD | Terra (Spacecraft) | extracted only: no ground truth triple has the [object](../docs/terminology.md#2-triples) Terra |
| E6 | Moderate Resolution Imaging Spectroradiometer (MODIS) (Instrument) | ABOARD | Aqua (Spacecraft) | extracted only: it would form a partial pair with G1, but G1 already has an exact partner, E1, and a [triple](../docs/terminology.md#2-triples) has at most one |

And G5 (CERES ABOARD Aqua) has no partner: [ground truth](../docs/terminology.md#4-ground-truth-and-samples) only, a missed [fact](../docs/terminology.md#2-triples).

In all: 6 extracted triples, 5 ground truth triples; 2 exact pairs (E1–G1 strict, E2–G2 not); 2 partial pairs (E3–G3 strict, E4–G4 not); so 2 strict pairs, one at each pair level; 2 extracted only (E5, E6); 1 ground truth only (G5).

### Precision: example

*Micro-averaging.* [Record](../docs/terminology.md#1-records-and-their-text) A: 4 [extracted triples](../docs/terminology.md#6-extracting-with-a-schema-step-060), 3 of them correct. Record B: 1 extracted triple, correct. Precision = (3 + 1) ÷ (4 + 1) = 80%. Averaging the records' own precisions (75% and 100%) would give 87.5% instead, letting record B's single extracted triple weigh as much as record A's four. This holds for every version: only what "correct" means changes, that is, which [pairs](#what-the-metrics-count-pairs) count (by pair level: exact, or exact or partial; by strictness: any, or strict only; see the table under *Formula*).

*Triples vs distinct facts.* 3 records each give the extracted triple "MODIS" ABOARD "Aqua", which is correct, and 1 record gives "AIRS" ABOARD "Terra", which is not. Precision = 3 ÷ 4 = 75%, so 1 − *p* = 25%. If each extracted triple becomes one [edge](../docs/terminology.md#8-the-pipeline), 1 of the 4 edges is not correct: 25%, as 1 − *p* says. If the 3 repeats are merged into one edge, 1 of the 2 edges is not correct: 50%.

*A repeated fact.* The [ground truth](../docs/terminology.md#4-ground-truth-and-samples) has "MODIS ABOARD Aqua" once. Extraction gives it twice: "MODIS ABOARD Aqua" and "the MODIS instrument ABOARD Aqua". The [ground truth triple](../docs/terminology.md#4-ground-truth-and-samples) pairs with one of them; the other has no partner left, so it counts as not correct, though what it says is true.

*A wrong component class.* The text says MODIS is aboard Aqua. The ground truth has "MODIS (Instrument) ABOARD Aqua (Spacecraft)". Extraction gives "MODIS (Dataset) ABOARD Aqua (Spacecraft)": the same fact, with the wrong [subject class](../docs/terminology.md#2-triples). The [translation table](../docs/terminology.md#7-evaluating-extraction-step-070) and the ground truth are both right: the mistake is extraction's. For strict exact precision it counts as not correct, since the subject classes differ.

*A wrong row of the translation table.* Extraction gives "MODIS MOUNTED_ON Aqua", which is right: MOUNTED_ON is the [current schema](../docs/terminology.md#6-extracting-with-a-schema-step-060)'s word for ABOARD. But the table's row says MOUNTED_ON → ACQUIRED_BY. After translation the triple reads "MODIS ACQUIRED_BY Aqua", while the ground truth says "MODIS ABOARD Aqua": the predicates differ, so it counts as not correct, though extraction did nothing wrong.

### Recall: example

*Micro-averaging.* [Record](../docs/terminology.md#1-records-and-their-text) A: the [ground truth](../docs/terminology.md#4-ground-truth-and-samples) has 5 [triples](../docs/terminology.md#2-triples), 3 of them found. Record B: it has 2, 1 found. Recall = (3 + 1) ÷ (5 + 2) = 57%. Averaging the records' own recalls (60% and 50%) would give 55% instead, letting record B's 2 [ground truth triples](../docs/terminology.md#4-ground-truth-and-samples) weigh as much as record A's 5. This holds for every version: only what "found" means changes, that is, which [pairs](#what-the-metrics-count-pairs) count (by pair level: exact, or exact or partial; by strictness: any, or strict only; see the table under *Formula*).

*Triples vs distinct facts.* 3 records each state "MODIS" ABOARD "Aqua", and extraction finds it in all 3; 1 record states "AIRS" ABOARD "Terra", and extraction misses it. Recall = 3 ÷ 4 = 75%. Counting each [fact](../docs/terminology.md#2-triples) once per record that states it, the [knowledge graph](../docs/terminology.md#8-the-pipeline) holds 3 of 4: 75%, as *r* says, whether or not graph building merges the 3 repeats into one [edge](../docs/terminology.md#8-the-pipeline). Counting distinct facts, it holds 1 of 2: 50%, also whether or not the repeats are merged.

*A repeated fact.* The ground truth of one record lists the same fact twice: "MODIS ABOARD Aqua" and "the MODIS instrument ABOARD Aqua". Extraction gives it once. The [extracted triple](../docs/terminology.md#6-extracting-with-a-schema-step-060) pairs with one of them; the other has no partner left, so it counts as not found, though extraction found the fact.

*A wrong component class.* The ground truth has "MODIS (Instrument) ABOARD Aqua (Spacecraft)". Extraction gives "MODIS (Dataset) ABOARD Aqua (Spacecraft)": the same fact, with the wrong [subject class](../docs/terminology.md#2-triples). For strict exact recall the ground truth triple counts as not found, since the subject classes differ; the mistake is extraction's.

*A wrong row of the translation table.* The ground truth has "MODIS ABOARD Aqua". Extraction gives "MODIS MOUNTED_ON Aqua", which is right, but the table's row says MOUNTED_ON → ACQUIRED_BY. After translation the extracted triple reads "MODIS ACQUIRED_BY Aqua": the predicates differ, so the ground truth triple counts as not found, though extraction found it.

### F1: example

With the [records](../docs/terminology.md#1-records-and-their-text) of the examples above: 4 [pairs](#what-the-metrics-count-pairs), 5 [extracted triples](../docs/terminology.md#6-extracting-with-a-schema-step-060), 7 [ground truth triples](../docs/terminology.md#4-ground-truth-and-samples). [Precision](#precision) 80%, [recall](#recall) 57%, F1 = 2 × 0.80 × 0.57 ÷ (0.80 + 0.57) = 67%.

*Pulled toward the lower.* Precision 100% and recall 10% give F1 = 2 × 1.00 × 0.10 ÷ (1.00 + 0.10) = 18%, not the 55% of the plain average.

### Entity-class accuracy: example

4 [pairs](#what-the-metrics-count-pairs), 3 of them strict: entity-class accuracy = 3 ÷ 4 = 75%.

### Recall upper bound: example

The [record](../docs/terminology.md#1-records-and-their-text) of the *Pairs* example has 5 [ground truth triples](../docs/terminology.md#4-ground-truth-and-samples), with the [predicates](../docs/terminology.md#3-schemas) ABOARD (G1, G2, G5), ACQUIRED_BY (G3) and HAS_TIME_SPAN (G4). Say the [current schema](../docs/terminology.md#6-extracting-with-a-schema-step-060) has counterparts for ABOARD and ACQUIRED_BY but not HAS_TIME_SPAN, and none for the [entity class](../docs/terminology.md#3-schemas) Dataset.

- Within reach: G1, G2, G3, G5 (G4's predicate has no counterpart). Recall upper bound = 4 ÷ 5 = 80%.
- Within strict reach: G1, G2, G5 (G3's [subject class](../docs/terminology.md#2-triples), Dataset, has no counterpart either). Strict recall upper bound = 3 ÷ 5 = 60%.

### Sampling error: example

40 evaluated [records](../docs/terminology.md#1-records-and-their-text), in two [strata](../docs/terminology.md#4-ground-truth-and-samples) of 30 and 10, with exact [precision](#precision) 70%. Each redraw takes 30 records at random, with repeats, from the first stratum's 30, and 10 from the second's 10, and computes exact precision on them. Of the 1,000 values, the middle 95% run from 61% to 78%. The [report](../docs/terminology.md#8-the-pipeline) says: "for the whole catalog, exact precision is likely between 61% and 78%".

## Sources

### Pairs: sources

- *Exact* and *partial*: the WebNLG 2020 challenge's evaluation of text-to-triples extraction (Castro Ferreira et al., 2020, [paper](https://aclanthology.org/2020.webnlg-1.7.pdf)). Ours is stricter on partial: whole words, not any overlap.
- Credit: here a partial [pair](#what-the-metrics-count-pairs) counts as fully right. The SemEval-2013 scoring convention ([nervaluate](https://github.com/MantisAI/nervaluate)) gives a partial match half credit: partial [precision](#precision) = (exact + 0.5 × partial) ÷ extracted. Full credit fits our meaning of a partial pair, the same [fact](../docs/terminology.md#2-triples) named differently (on tuning [records](../docs/terminology.md#1-records-and-their-text), confirmed by your review), but our partial numbers are higher than that convention's and not directly comparable with published partial scores.
- *Strict*, meaning right relation and right entity types: the "Strict" [setting](../docs/terminology.md#8-the-pipeline) of end-to-end relation extraction (Bekoulis et al., 2018, as described by Taillé et al., 2020, [paper](https://aclanthology.org/2020.emnlp-main.301/)). WebNLG's "strict" means something else (the element's role must match), so it isn't the source here.
- At most one partner per [triple](../docs/terminology.md#2-triples), largest set of pairs: a maximum matching (Kuhn's algorithm, `070_evaluate/070_evaluate_helpers/pairing.py`).

### Precision: sources

The standard definition of precision, summed over all items before dividing (*micro-averaging*), as opposed to averaging per [record](../docs/terminology.md#1-records-and-their-text) (*macro-averaging*): Manning, Raghavan & Schütze, *Introduction to Information Retrieval* (2008), sections 8.3 and 13.6 ([book](https://nlp.stanford.edu/IR-book/)). Micro-averaging fits precision's interpretation: every [extracted triple](../docs/terminology.md#6-extracting-with-a-schema-step-060) weighs the same, as every [edge](../docs/terminology.md#8-the-pipeline) would in the [knowledge graph](../docs/terminology.md#8-the-pipeline). Macro-averaging answers another question (for a typical record, what proportion of its extracted triples is correct). The WebNLG+ 2020 challenge reports its text-to-triples scores macro-averaged (Castro Ferreira et al., 2020, Table 10, [paper](https://aclanthology.org/2020.webnlg-1.7.pdf)), so our numbers aren't directly comparable with its published ones.

### Recall: sources

The standard definition of recall, micro-averaged like [precision](#precision): Manning, Raghavan & Schütze (2008), sections 8.3 and 13.6. As for precision, the WebNLG+ 2020 challenge reports recall macro-averaged (Castro Ferreira et al., 2020, Table 10), so our numbers aren't directly comparable with its published ones.

### F1: sources

The F-measure of van Rijsbergen, *Information Retrieval* (1979), with [precision](#precision) and [recall](#recall) weighted equally; Manning, Raghavan & Schütze (2008), section 8.3. The standard headline metric in relation extraction.

### Entity-class accuracy: sources

No single standard name. It separates the two [settings](../docs/terminology.md#8-the-pipeline) end-to-end relation extraction reports side by side, "Strict" (with entity types) and "Boundaries" (without), described by Taillé et al. (2020): here, strict [pairs](#what-the-metrics-count-pairs) ÷ all pairs.

### Recall upper bound: sources

An upper bound on recall, set by an earlier stage of a pipeline (here, the [schema](../docs/terminology.md#3-schemas)), is standard: Pink, Nothman & Curran (2014), "Analysing recall loss in named entity slot filling", EMNLP ([paper](https://aclanthology.org/D14-1089.pdf)): "the recall of a system's coarse candidate generation process sets a hard upper bound on performance". As there, the bound uses the same matching rule as the metric it bounds: a [pair](#what-the-metrics-count-pairs) needs only the [predicate](../docs/terminology.md#3-schemas), so the recall upper bound counts only the predicate; a strict pair also needs the [entity classes](../docs/terminology.md#3-schemas), so the strict recall upper bound counts them too. The name "recall upper bound" is the established one; no paper found uses a schema-specific term.

### Why "approximately": sources

- Sampling error, the [margin of error](#sampling-error):
  - The [bootstrap](#sampling-error), and its percentile range: Efron & Tibshirani, *An Introduction to the Bootstrap* (1993).
  - Drawing whole [records](../docs/terminology.md#1-records-and-their-text) rather than single [triples](../docs/terminology.md#2-triples), since a record's triples succeed or fail together, is the cluster (or block) bootstrap; drawing within each [stratum](../docs/terminology.md#4-ground-truth-and-samples) is the stratified bootstrap: Davison & Hinkley, *Bootstrap Methods and their Application* (1997).
  - The threshold of 20 records: a rule of thumb, with no source found.
  - Below 5% of the catalog evaluated, drawing with repeats from a finite catalog is negligible: Cochran, *Sampling Techniques* (1977), chapter 2.
  - A stratum with only 1 evaluated record gives no estimate of its spread: the single-unit stratum of survey sampling (Cochran, 1977).
  - A percentile range is too narrow near 0% or 100%: Efron & Tibshirani (1993).
- The sample's mix of [maintainers](../docs/terminology.md#1-records-and-their-text): stratified sampling with proportional allocation, Cochran (1977), chapter 5. The 10-point warning: a rule of thumb, with no source found.
- Small-sample bias of a ratio: the ratio estimator, biased by an amount that shrinks faster than its sampling error as the sample grows, Cochran (1977), chapter 6.
- Tuning on the evaluated records: a test set used to choose between versions no longer gives an unbiased estimate; a part kept unseen until the end does. Hastie, Tibshirani & Friedman, *The Elements of Statistical Learning* (2nd ed., 2009), section 7.2.
- An imperfect [ground truth](../docs/terminology.md#4-ground-truth-and-samples): a reference set missing true triples makes evaluation "overly pessimistic" for methods that extract them, Zhang & Soh, *Extract, Define, Canonicalize* (2024), [paper](https://arxiv.org/abs/2404.03868).
