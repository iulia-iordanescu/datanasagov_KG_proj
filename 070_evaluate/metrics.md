# Evaluation metrics

The one place each of evaluation's numbers is explained: what it is, its formula with an example, how to read it, what it assumes, and where it comes from. Other files point here instead of repeating it. Each metric's worked example is under *Examples*, and where it comes from under *Sources*, at the end. Terms: [docs/terminology.md](../docs/terminology.md).

Contents:

- [What the metrics count: pairs](#what-the-metrics-count-pairs)
- [The metrics](#the-metrics): [Precision](#precision), [Recall](#recall), [F1](#f1), [Entity-class accuracy](#entity-class-accuracy), [Recall upper bound](#recall-upper-bound)
- [Why "approximately": reasons every metric shares](#why-approximately-reasons-every-metric-shares)
- [Examples](#examples), [Sources](#sources)

Formulas use the usual set symbols: \|…\| is the number of members, ∪ is union (in either), ∩ is intersection (in both). Between statements, ∨ is the inclusive or (one, the other, or both) and ∧ is and (both). Every count is over all the evaluated records of one part (tuning or held-out) together, not one record at a time, and never includes the DESCRIBES rows (they're compared on their own: see the describes metrics in [`070_evaluate.md`](070_evaluate.md), until they get a section here).

## What the metrics count: pairs

### <ins>Definition</ins>

A **pair** is one extracted triple and one ground truth triple of the same record that evaluation takes to state the same fact, once the extracted triple's predicate, subject class and object class are translated into the ground truth vocabulary (through the translation table, [`annotations/component_class_mapping.csv`](../annotations/component_class_mapping.csv)). Each triple has at most one partner. Evaluation finds the largest possible set of exact pairs, then, among the triples left, the largest possible set of partial pairs. There are two **pair levels**, exact and partial, and when two triples count as stating the same fact depends on the level: they form an **exact pair** or a **partial pair**.

| Pair level | Two triples count as stating the same fact when… |
|---|---|
| exact | (same predicate) ∧ (same subject instance) ∧ (same object instance), once evened out (glossary): ignoring case, spacing, quote marks, dashes, punctuation at either end, and a leading "a", "an", or "the" |
| partial | (same predicate) ∧ ((the two subject instances are equal) ∨ (one subject instance appears inside the other as whole words, either way round)) ∧ ((the two object instances are equal) ∨ (one object instance appears inside the other as whole words, either way round)). Only triples left without an exact partner can form one. |

Strict is an extra condition on a pair at either level: a **strict pair** is an exact or partial pair with (the same subject classes) ∧ (the same object classes).

So every pair is exactly one of these four:

| | strict ((same subject classes) ∧ (same object classes)) | not strict |
|---|---|---|
| exact pair | exact pairs ∩ strict pairs | exact pairs, not strict |
| partial pair | partial pairs ∩ strict pairs | partial pairs, not strict |

All pairs = exact pairs ∪ partial pairs (no pair is both). Strict pairs are some of each.

A triple left without a partner is **extracted only** (an extracted triple) or **ground truth only** (a ground truth triple).

### <ins>Assumes and can't see</ins>

- Containment can be fooled: "MODIS" is inside "MODIS Terra", a different instrument. On tuning records you review partial pairs in the annotation tool (*Partial pairs*); two triples marked "not the same fact" are never paired. Held-out records' partial pairs are never reviewed (that would mean looking at them).
- Two component classes of the current schema that translate to one component class of the ground truth vocabulary can't be told apart.

Worked example: [Pairs: example](#pairs-example). Sources: [Pairs: sources](#pairs-sources).

## The metrics

### Precision

#### <ins>Definition</ins>

The proportion of the extracted triples that are correct. What "correct" means depends on the version.

#### <ins>Formula</ins>

Four versions.

| Version | An extracted triple counts as correct when it… | Formula |
|---|---|---|
| exact precision | forms an exact pair | \|exact pairs\| ÷ \|extracted triples\| |
| partial precision | forms an exact or a partial pair | \|exact pairs ∪ partial pairs\| ÷ \|extracted triples\| |
| strict exact precision | (forms an exact pair) ∧ (the pair is strict) | \|exact pairs ∩ strict pairs\| ÷ \|extracted triples\| |
| strict partial precision | (forms an exact or a partial pair) ∧ (the pair is strict) | \|(exact pairs ∪ partial pairs) ∩ strict pairs\| ÷ \|extracted triples\| |

Each version is a number from 0 to 1; with no extracted triples across the records, it is undefined.

#### <ins>Interpretations</ins>

Let *p* be the value of one version of precision. Then, *p* is the proportion of extracted triples that are correct, where "correct" is defined by the version (table above). So in a knowledge graph built from the whole catalog's extracted triples, approximately 1 − *p* of its edges would not be correct.

- Partial precision minus exact precision: the proportion of the extracted triples that form a partial pair but not an exact pair. In such a pair, the two triples have the same predicate, but (their subject instances are worded differently, one inside the other as whole words) ∨ (their object instances are worded differently, one inside the other as whole words) (e.g. "MODIS" vs "Moderate Resolution Imaging Spectroradiometer (MODIS)").
- Precision minus strict precision, at the same pair level: the proportion of the extracted triples that form a pair at that level but not a strict one. In such a pair, (the two triples' subject classes differ) ∨ (the two triples' object classes differ).
- In every version, an extracted triple is not correct when (the text doesn't state the fact) ∨ (it repeats a fact already extracted) ∨ (it's true but missing from the ground truth). The first two are mistakes of extraction; the third, a mistake in the ground truth. A triple has at most one partner, so of two extracted triples stating one fact, only one can form a pair. It is also not correct when, compared with the ground truth triple stating the same fact (after translation), it differs as below. Such a difference comes from (a mistake of extraction) ∨ (a wrong row of the translation table) ∨ (a mistake in the ground truth triple).

  | Version | An extracted triple is also not correct when… |
  |---|---|
  | exact precision | (its predicate differs) ∨ (its subject instance differs, once evened out) ∨ (its object instance differs, once evened out) |
  | partial precision | (its predicate differs) ∨ (its subject instance neither equals the ground truth triple's subject instance, nor contains it, nor is contained in it, as whole words) ∨ (its object instance neither equals the ground truth triple's object instance, nor contains it, nor is contained in it, as whole words) |
  | strict exact precision | (its predicate differs) ∨ (its subject instance differs, once evened out) ∨ (its object instance differs, once evened out) ∨ (its subject class differs) ∨ (its object class differs) |
  | strict partial precision | (its predicate differs) ∨ (its subject instance neither equals the ground truth triple's subject instance, nor contains it, nor is contained in it, as whole words) ∨ (its object instance neither equals the ground truth triple's object instance, nor contains it, nor is contained in it, as whole words) ∨ (its subject class differs) ∨ (its object class differs) |
- Read with recall: each alone can be fooled (see *F1*, *Interpretations*).

#### <ins>Assumes and can't see</ins>

- That the ground truth lists every fact the records state: an extracted triple that is true but missing from the ground truth counts as not correct, so it lowers *p*.
- Above, *Interpretations* states that approximately 1 − *p* of the knowledge graph's edges would not be correct, where *p* is any one version of precision. It is approximate for two kinds of reason:
  - the [reasons every metric shares](#why-approximately-reasons-every-metric-shares); the report measures one of them, sampling error, with *p*'s margin of error;
  - one of precision's own: if graph building (step 080, not built yet) merges repeated extracted triples into one edge, the proportion of edges that are not correct can differ from 1 − *p*. Merging turns a fact that many records state into one edge, but leaves a fact that one record states as one edge. Example: [Precision: example](#precision-example), *Triples vs distinct facts*.

Worked example: [Precision: example](#precision-example). Sources: [Precision: sources](#precision-sources).

### Recall

#### <ins>Definition</ins>

The proportion of the ground truth triples that extraction found. What "found" means depends on the version.

#### <ins>Formula</ins>

Four versions.

| Version | A ground truth triple counts as found when it… | Formula |
|---|---|---|
| exact recall | forms an exact pair | \|exact pairs\| ÷ \|ground truth triples\| |
| partial recall | forms an exact or a partial pair | \|exact pairs ∪ partial pairs\| ÷ \|ground truth triples\| |
| strict exact recall | (forms an exact pair) ∧ (the pair is strict) | \|exact pairs ∩ strict pairs\| ÷ \|ground truth triples\| |
| strict partial recall | (forms an exact or a partial pair) ∧ (the pair is strict) | \|(exact pairs ∪ partial pairs) ∩ strict pairs\| ÷ \|ground truth triples\| |

Each version is a number from 0 to 1; with no ground truth triples across the records, it is undefined.

#### <ins>Interpretations</ins>

Let *r* be the value of one version of recall. Then, *r* is the proportion of ground truth triples that are found, where "found" is defined by the version (table above). So a knowledge graph built from the whole catalog's extracted triples would hold approximately *r* of the facts the records state, each fact counted once per record that states it.

- Partial recall minus exact recall: the proportion of the ground truth triples that form a partial pair but not an exact pair. In such a pair, the two triples have the same predicate, but (their subject instances are worded differently, one inside the other as whole words) ∨ (their object instances are worded differently, one inside the other as whole words) (e.g. "MODIS" vs "Moderate Resolution Imaging Spectroradiometer (MODIS)").
- Recall minus strict recall, at the same pair level: the proportion of the ground truth triples that form a pair at that level but not a strict one. In such a pair, (the two triples' subject classes differ) ∨ (the two triples' object classes differ).
- In every version, a ground truth triple is not found when (the text doesn't state the fact) ∨ (it repeats a fact the ground truth already lists) ∨ (no extracted triple states the fact). The first two are mistakes in the ground truth; the third, a mistake of extraction. A triple has at most one partner, so of two ground truth triples stating one fact, only one can form a pair. The third includes the facts whose predicate the current schema has no counterpart for (see *Recall upper bound*). It is also not found when, compared with the extracted triple stating the same fact (after translation), they differ as below. Such a difference comes from (a mistake of extraction) ∨ (a wrong row of the translation table) ∨ (a mistake in the ground truth triple).

  | Version | A ground truth triple is also not found when… |
  |---|---|
  | exact recall | (the extracted triple's predicate differs from its predicate) ∨ (the extracted triple's subject instance differs from its subject instance, once evened out) ∨ (the extracted triple's object instance differs from its object instance, once evened out) |
  | partial recall | (the extracted triple's predicate differs from its predicate) ∨ (the extracted triple's subject instance neither equals its subject instance, nor contains it, nor is contained in it, as whole words) ∨ (the extracted triple's object instance neither equals its object instance, nor contains it, nor is contained in it, as whole words) |
  | strict exact recall | (the extracted triple's predicate differs from its predicate) ∨ (the extracted triple's subject instance differs from its subject instance, once evened out) ∨ (the extracted triple's object instance differs from its object instance, once evened out) ∨ (the extracted triple's subject class differs from its subject class) ∨ (the extracted triple's object class differs from its object class) |
  | strict partial recall | (the extracted triple's predicate differs from its predicate) ∨ (the extracted triple's subject instance neither equals its subject instance, nor contains it, nor is contained in it, as whole words) ∨ (the extracted triple's object instance neither equals its object instance, nor contains it, nor is contained in it, as whole words) ∨ (the extracted triple's subject class differs from its subject class) ∨ (the extracted triple's object class differs from its object class) |
- Read with precision: each alone can be fooled (see *F1*, *Interpretations*).

#### <ins>Assumes and can't see</ins>

- That the ground truth lists every fact the records state: a fact missing from it isn't counted at all, neither found nor missed.
- Above, *Interpretations* states that a knowledge graph built from the whole catalog's extracted triples would hold approximately *r* of the facts the records state, each fact counted once per record that states it, where *r* is any one version of recall. It is approximate for the [reasons every metric shares](#why-approximately-reasons-every-metric-shares); the report measures one of them, sampling error, with *r*'s margin of error. Unlike precision's reading, it doesn't depend on graph building: merging repeated extracted triples into one edge changes how many edges there are, not which facts the knowledge graph holds.
- *r* counts a fact once per record that states it. The proportion of distinct facts the knowledge graph holds, each counted once, is a different number, and can differ from *r*. Example: [Recall: example](#recall-example), *Triples vs distinct facts*.

Worked example: [Recall: example](#recall-example). Sources: [Recall: sources](#recall-sources).

### F1

#### <ins>Definition</ins>

Precision and recall combined into one number, high only when both are.

#### <ins>Formula</ins>

Four versions, each from the precision and recall of the same version.

| Version | Formula |
|---|---|
| exact F1 | 2 × exact precision × exact recall ÷ (exact precision + exact recall) |
| partial F1 | 2 × partial precision × partial recall ÷ (partial precision + partial recall) |
| strict exact F1 | 2 × strict exact precision × strict exact recall ÷ (strict exact precision + strict exact recall) |
| strict partial F1 | 2 × strict partial precision × strict partial recall ÷ (strict partial precision + strict partial recall) |

The code computes the same number as 2 × \|pairs counted\| ÷ (\|extracted triples\| + \|ground truth triples\|), which also settles the edge cases: F1 is 0 when no pair is counted (even with no extracted triples, where precision is undefined).

Each version is a number from 0 to 1; with neither extracted triples nor ground truth triples across the records, it is undefined.

#### <ins>Interpretations</ins>

Let *f* be the value of one version of F1. Then, *f* is the harmonic mean of that version's precision and recall: a kind of average, pulled toward the lower of the two (example: [F1: example](#f1-example)).

- Why one number: precision and recall can each be fooled alone. An extractor that states just one triple it is sure of gets high precision and almost no recall; one that states everything it can think of gets high recall and low precision. *f* is high only when both are.
- The usual headline number for comparing runs or models, and for comparing with published results.

#### <ins>Assumes and can't see</ins>

- It weighs precision and recall equally. If one matters more (for a graph, a wrong statement is often worse than a missing one), read precision and recall themselves.
- It doesn't show which of the two is low.
- Read for the whole catalog, *f* is approximate for the the [reasons every metric shares](#why-approximately-reasons-every-metric-shares); the report measures one of them, sampling error, with *f*'s margin of error.

Worked example: [F1: example](#f1-example). Sources: [F1: sources](#f1-sources).

### Entity-class accuracy

#### <ins>Definition</ins>

Among the pairs counted, the proportion that are strict. Which pairs are counted depends on the version.

#### <ins>Formula</ins>

Two versions.

| Version | Pairs counted | Formula |
|---|---|---|
| exact entity-class accuracy | exact pairs | \|exact pairs ∩ strict pairs\| ÷ \|exact pairs\| |
| partial entity-class accuracy | exact pairs ∪ partial pairs | \|(exact pairs ∪ partial pairs) ∩ strict pairs\| ÷ \|exact pairs ∪ partial pairs\| |

Each version is a number from 0 to 1; with no pairs counted across the records, it is undefined.

#### <ins>Interpretations</ins>

Let *a* be the value of one version of entity-class accuracy. Then, *a* is the proportion of the pairs counted that are strict, where the pairs counted are defined by the version (table above). So of the knowledge graph's correct edges, approximately *a* would also have both nodes' entity classes right.

- Read with precision and recall: they say whether facts are found; this says whether the things in them are classed right.

#### <ins>Assumes and can't see</ins>

- Only paired triples are judged: the subject class and object class of a triple without a partner aren't counted anywhere.
- Two component classes of the current schema that translate to one component class of the ground truth vocabulary look the same, so mixing them up isn't seen.
- Above, *Interpretations* states that approximately *a* of the knowledge graph's correct edges would also have both nodes' entity classes right, where *a* is any one version of entity-class accuracy. It is approximate for two kinds of reason:
  - the [reasons every metric shares](#why-approximately-reasons-every-metric-shares); the report measures one of them, sampling error, with *a*'s margin of error;
  - one of its own: if graph building (step 080, not built yet) merges repeated extracted triples into one edge, the proportion of correct edges whose entity classes are right can differ from *a*, for the reason given under *Precision*, *Assumes and can't see*.

Worked example: [Entity-class accuracy: example](#entity-class-accuracy-example). Sources: [Entity-class accuracy: sources](#entity-class-accuracy-sources).

### Recall upper bound

#### <ins>Definition</ins>

The proportion of the ground truth triples that the current schema can express at all: the most recall any extraction with this schema and translation table could get. A ground truth triple is **within reach** when its predicate is one that some checked row of the translation table translates to. It is **within strict reach** when (it is within reach) ∧ (its subject class is one that some checked row translates to) ∧ (its object class is one that some checked row translates to). Which ground truth triples count depends on the version.

#### <ins>Formula</ins>

Two versions.

| Version | A ground truth triple counts when it is… | Formula |
|---|---|---|
| recall upper bound | within reach | \|ground truth triples within reach\| ÷ \|ground truth triples\| |
| strict recall upper bound | within strict reach | \|ground truth triples within strict reach\| ÷ \|ground truth triples\| |

Each version is a number from 0 to 1; with no ground truth triples across the records, it is undefined.

#### <ins>Interpretations</ins>

Let *u* be the value of one version of the recall upper bound. Then, *u* is the proportion of ground truth triples within reach (for the strict version, within strict reach). So no extraction with this schema and translation table can get a recall (for the strict version, a strict recall) above *u*: the other 1 − *u* of the ground truth triples use a component class the current schema has no counterpart for.

- Read with recall: the gap between the two is what extraction missed although the schema could express it.
- A low upper bound points at the schema (schema induction, or the schema additions) or at the translation table (a row that says `(none)`, or a missing row).
- The strict version is the limit for strict recall: a triple can be within reach but not within strict reach when (the schema has no counterpart for its subject class) ∨ (it has none for its object class).

#### <ins>Assumes and can't see</ins>

- Within reach means only that the schema has the component classes: not that the model could find the fact in the text.
- It depends on the translation table: a row wrongly saying `(none)` lowers it.
- Read for the whole catalog, *u* is approximate for the the [reasons every metric shares](#why-approximately-reasons-every-metric-shares); the report measures one of them, sampling error, with *u*'s margin of error.

Worked example: [Recall upper bound: example](#recall-upper-bound-example). Sources: [Recall upper bound: sources](#recall-upper-bound-sources).

## Why "approximately": reasons every metric shares

Every metric is computed on the evaluated records only (the fair sample of finished, extracted records). Reading it for the whole catalog assumes two things:

- the evaluated records are a random sample of the catalog (only the fair sample is evaluated);
- the pipeline wasn't adjusted to these records (true of the held-out part until it is looked at).

Even then, every metric is approximate for the whole catalog, for the five reasons below. Each has the same parts: what it means, and how the report checks or limits it. A metric with reasons of its own lists them in its own section, under *Assumes and can't see*. Sources for all five: [Why "approximately": sources](#why-approximately-sources).

### Sampling error

**What it means.** Another sample of the same size would give a somewhat different value.

**How the report checks or limits it: the margin of error.** A range around each metric's value that says how much the value could change with another sample of the same size. Every metric gets one, except the describes baseline and the describes per-entity-class average. Example: [Sampling error: example](#sampling-error-example).

- **How it is computed**, by the bootstrap, with fixed numbers in `070_evaluate/070_evaluate_helpers/stats.py`:
  1. Redraw the evaluated records: within each stratum, draw at random, with repeats, as many records as the stratum has. Whole records are drawn, never single triples.
  2. Compute the metric on the redrawn records, adding up their counts as on the real ones. A redraw where the metric is undefined (e.g. no extracted triples) is skipped.
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
  | The evaluated records are a random sample of the catalog | The redraws stand in for other samples of the catalog. | Only the fair sample is evaluated (by design). |
  | Whole records vary, independently of each other | A record's triples come from one text and one model call, so they succeed or fail together; redrawing single triples would make the range too narrow. | Records are redrawn whole (by design). |
  | Enough records | With very few, the range is itself unreliable, usually too narrow. | No range below 20 evaluated records (a rule of thumb; no source found gives a number). |
  | Every stratum adds spread | A stratum with only 1 evaluated record puts that record in every redraw, so the range comes out too narrow. | Lists the strata with only 1 evaluated record. |
  | The range isn't at 0% or 100% | There, a percentile range is too narrow. | Lists the metrics whose range reaches 0% or 100%. |
  | No one record dominates | A record with most of the triples sways every redraw it's in. | Gives the largest record's proportion of the extracted triples and of the ground truth triples, for reading (no established threshold). |
  | A small proportion of the catalog is evaluated | Redrawing with repeats treats the catalog as endless; for a large proportion, the range comes out somewhat too wide. | Gives the proportion of the catalog evaluated; holds below 5%. |
- **What it can't see.** Only sampling error: the other four reasons can move the whole catalog's value outside the range.

### The sample's mix of maintainers

**What it means.** The pool was drawn stratified by maintainer, and only its first finished records are evaluated. If their mix of maintainers differs from the catalog's, the value leans toward the over-represented maintainers.

**How the report checks or limits it.**
- The pool matches the catalog's mix of maintainers: it was drawn with proportional allocation (`annotations/ground_truth_candidates.json`).
- The report's strata table compares, per stratum, the proportion of the evaluated records with the proportion of the pool.
- From 20 evaluated records on, it warns when the two differ by more than 10 percentage points (`SHARE_GAP`). The 10 points is a rule of thumb, with no source found.

### Small-sample bias of a ratio

**What it means.** Each metric is a ratio of two counts that both vary from sample to sample. Such a ratio is slightly biased in small samples: averaged over many samples, it isn't exactly the whole catalog's value.

**How the report checks or limits it.** It doesn't check it. The bias shrinks as the sample grows, faster than the sampling error does, so it is small next to the margin of error.

### Tuning on the evaluated records

**What it means.** Changes made after looking at the tuning part's numbers (to the schema, the schema additions, or the prompts) fit those records, so the tuning part's numbers come out higher than the whole catalog's would.

**How the report checks or limits it.** The held-out part: its numbers are shown only with the setting `evaluate_held_out`, meant for the end, and each look is logged in `annotations/held_out_looks.csv`.

### An imperfect ground truth

**What it means.** "Correct" means having a partner in the ground truth. A fact missing from it, or a mistake in it, shifts the value the same way in every sample.

**How the report checks or limits it.** It doesn't: nothing in the numbers shows it. Only care in annotating limits it (see `050_annotate/050_annotate.md`).

## Examples

### Pairs: example

One record. Its ground truth triples:

| | Subject instance (subject class) | Predicate | Object instance (object class) |
|---|---|---|---|
| G1 | MODIS (Instrument) | ABOARD | Aqua (Spacecraft) |
| G2 | AIRS (Instrument) | ABOARD | Aqua (Spacecraft) |
| G3 | MODIS Snow Cover (Dataset) | ACQUIRED_BY | MODIS (Instrument) |
| G4 | MODIS Snow Cover (Dataset) | HAS_TIME_SPAN | 2002–2023 (TimeSpan) |
| G5 | CERES (Instrument) | ABOARD | Aqua (Spacecraft) |

Its extracted triples, after translation, and what each becomes:

| | Subject instance (subject class) | Predicate | Object instance (object class) | Outcome |
|---|---|---|---|---|
| E1 | the MODIS (Instrument) | ABOARD | Aqua (Spacecraft) | exact pair with G1 ("the" is ignored); strict |
| E2 | AIRS (Dataset) | ABOARD | Aqua (Spacecraft) | exact pair with G2; not strict (subject class Dataset, not Instrument) |
| E3 | MODIS Snow Cover 5-Min L2 Swath (Dataset) | ACQUIRED_BY | Moderate Resolution Imaging Spectroradiometer (MODIS) (Instrument) | partial pair with G3 ("MODIS Snow Cover" is inside the subject instance, "MODIS" inside the object instance); strict |
| E4 | MODIS Snow Cover (Dataset) | HAS_TIME_SPAN | the period 2002–2023 (Dataset) | partial pair with G4 ("2002–2023" is inside the object instance); not strict (object class Dataset, not TimeSpan) |
| E5 | MODIS (Instrument) | ABOARD | Terra (Spacecraft) | extracted only: no ground truth triple has the object Terra |
| E6 | Moderate Resolution Imaging Spectroradiometer (MODIS) (Instrument) | ABOARD | Aqua (Spacecraft) | extracted only: it would form a partial pair with G1, but G1 already has an exact partner, E1, and a triple has at most one |

And G5 (CERES ABOARD Aqua) has no partner: ground truth only, a missed fact.

In all: 6 extracted triples, 5 ground truth triples; 2 exact pairs (E1–G1 strict, E2–G2 not); 2 partial pairs (E3–G3 strict, E4–G4 not); so 2 strict pairs, one at each pair level; 2 extracted only (E5, E6); 1 ground truth only (G5).

### Precision: example

*Micro-averaging.* Record A: 4 extracted triples, 3 of them correct. Record B: 1 extracted triple, correct. Precision = (3 + 1) ÷ (4 + 1) = 80%. Averaging the records' own precisions (75% and 100%) would give 87.5% instead, letting record B's single extracted triple weigh as much as record A's four. This holds for every version: only what "correct" means changes, that is, which pairs count (by pair level: exact, or exact or partial; by strictness: any, or strict only; see the table under *Formula*).

*Triples vs distinct facts.* 3 records each give the extracted triple "MODIS" ABOARD "Aqua", which is correct, and 1 record gives "AIRS" ABOARD "Terra", which is not. Precision = 3 ÷ 4 = 75%, so 1 − *p* = 25%. If each extracted triple becomes one edge, 1 of the 4 edges is not correct: 25%, as 1 − *p* says. If the 3 repeats are merged into one edge, 1 of the 2 edges is not correct: 50%.

### Recall: example

*Micro-averaging.* Record A: the ground truth has 5 triples, 3 of them found. Record B: it has 2, 1 found. Recall = (3 + 1) ÷ (5 + 2) = 57%. Averaging the records' own recalls (60% and 50%) would give 55% instead, letting record B's 2 ground truth triples weigh as much as record A's 5. This holds for every version: only what "found" means changes, that is, which pairs count (by pair level: exact, or exact or partial; by strictness: any, or strict only; see the table under *Formula*).

*Triples vs distinct facts.* 3 records each state "MODIS" ABOARD "Aqua", and extraction finds it in all 3; 1 record states "AIRS" ABOARD "Terra", and extraction misses it. Recall = 3 ÷ 4 = 75%. Counting each fact once per record that states it, the knowledge graph holds 3 of 4: 75%, as *r* says, whether or not graph building merges the 3 repeats into one edge. Counting distinct facts, it holds 1 of 2: 50%, also whether or not the repeats are merged.

### F1: example

With the records of the examples above: 4 pairs, 5 extracted triples, 7 ground truth triples. Precision 80%, recall 57%, F1 = 2 × 0.80 × 0.57 ÷ (0.80 + 0.57) = 67%.

*Pulled toward the lower.* Precision 100% and recall 10% give F1 = 2 × 1.00 × 0.10 ÷ (1.00 + 0.10) = 18%, not the 55% of the plain average.

### Entity-class accuracy: example

4 pairs, 3 of them strict: entity-class accuracy = 3 ÷ 4 = 75%.

### Recall upper bound: example

The record of the *Pairs* example has 5 ground truth triples, with the predicates ABOARD (G1, G2, G5), ACQUIRED_BY (G3) and HAS_TIME_SPAN (G4). Say the current schema has counterparts for ABOARD and ACQUIRED_BY but not HAS_TIME_SPAN, and none for the entity class Dataset.

- Within reach: G1, G2, G3, G5 (G4's predicate has no counterpart). Recall upper bound = 4 ÷ 5 = 80%.
- Within strict reach: G1, G2, G5 (G3's subject class, Dataset, has no counterpart either). Strict recall upper bound = 3 ÷ 5 = 60%.

### Sampling error: example

40 evaluated records, in two strata of 30 and 10, with exact precision 70%. Each redraw takes 30 records at random, with repeats, from the first stratum's 30, and 10 from the second's 10, and computes exact precision on them. Of the 1,000 values, the middle 95% run from 61% to 78%. The report says: "for the whole catalog, exact precision is likely between 61% and 78%".

## Sources

### Pairs: sources

- *Exact* and *partial*: the WebNLG 2020 challenge's evaluation of text-to-triples extraction (Castro Ferreira et al., 2020, [paper](https://aclanthology.org/2020.webnlg-1.7.pdf)). Ours is stricter on partial: whole words, not any overlap.
- Credit: here a partial pair counts as fully right. The SemEval-2013 scoring convention ([nervaluate](https://github.com/MantisAI/nervaluate)) gives a partial match half credit: partial precision = (exact + 0.5 × partial) ÷ extracted. Full credit fits our meaning of a partial pair, the same fact named differently (on tuning records, confirmed by your review), but our partial numbers are higher than that convention's and not directly comparable with published partial scores.
- *Strict*, meaning right relation and right entity types: the "Strict" setting of end-to-end relation extraction (Bekoulis et al., 2018, as described by Taillé et al., 2020, [paper](https://aclanthology.org/2020.emnlp-main.301/)). WebNLG's "strict" means something else (the element's role must match), so it isn't the source here.
- At most one partner per triple, largest set of pairs: a maximum matching (Kuhn's algorithm, `070_evaluate/070_evaluate_helpers/pairing.py`).

### Precision: sources

The standard definition of precision, summed over all items before dividing (*micro-averaging*), as opposed to averaging per record (*macro-averaging*): Manning, Raghavan & Schütze, *Introduction to Information Retrieval* (2008), sections 8.3 and 13.6 ([book](https://nlp.stanford.edu/IR-book/)). Micro-averaging fits precision's interpretation: every extracted triple weighs the same, as every edge would in the knowledge graph. Macro-averaging answers another question (for a typical record, what proportion of its extracted triples is correct). The WebNLG+ 2020 challenge reports its text-to-triples scores macro-averaged (Castro Ferreira et al., 2020, Table 10, [paper](https://aclanthology.org/2020.webnlg-1.7.pdf)), so our numbers aren't directly comparable with its published ones.

### Recall: sources

The standard definition of recall, micro-averaged like precision: Manning, Raghavan & Schütze (2008), sections 8.3 and 13.6. As for precision, the WebNLG+ 2020 challenge reports recall macro-averaged (Castro Ferreira et al., 2020, Table 10), so our numbers aren't directly comparable with its published ones.

### F1: sources

The F-measure of van Rijsbergen, *Information Retrieval* (1979), with precision and recall weighted equally; Manning, Raghavan & Schütze (2008), section 8.3. The standard headline metric in relation extraction.

### Entity-class accuracy: sources

No single standard name. It separates the two settings end-to-end relation extraction reports side by side, "Strict" (with entity types) and "Boundaries" (without), described by Taillé et al. (2020): here, strict pairs ÷ all pairs.

### Recall upper bound: sources

An upper bound on recall, set by an earlier stage of a pipeline (here, the schema), is standard: Pink, Nothman & Curran (2014), "Analysing recall loss in named entity slot filling", EMNLP ([paper](https://aclanthology.org/D14-1089.pdf)): "the recall of a system's coarse candidate generation process sets a hard upper bound on performance". As there, the bound uses the same matching rule as the metric it bounds: a pair needs only the predicate, so the recall upper bound counts only the predicate; a strict pair also needs the entity classes, so the strict recall upper bound counts them too. The name "recall upper bound" is the established one; no paper found uses a schema-specific term.

### Why "approximately": sources

- Sampling error, the margin of error:
  - The bootstrap, and its percentile range: Efron & Tibshirani, *An Introduction to the Bootstrap* (1993).
  - Drawing whole records rather than single triples, since a record's triples succeed or fail together, is the cluster (or block) bootstrap; drawing within each stratum is the stratified bootstrap: Davison & Hinkley, *Bootstrap Methods and their Application* (1997).
  - The threshold of 20 records: a rule of thumb, with no source found.
  - Below 5% of the catalog evaluated, drawing with repeats from a finite catalog is negligible: Cochran, *Sampling Techniques* (1977), chapter 2.
  - A stratum with only 1 evaluated record gives no estimate of its spread: the single-unit stratum of survey sampling (Cochran, 1977).
  - A percentile range is too narrow near 0% or 100%: Efron & Tibshirani (1993).
- The sample's mix of maintainers: stratified sampling with proportional allocation, Cochran (1977), chapter 5. The 10-point warning: a rule of thumb, with no source found.
- Small-sample bias of a ratio: the ratio estimator, biased by an amount that shrinks faster than its sampling error as the sample grows, Cochran (1977), chapter 6.
- Tuning on the evaluated records: a test set used to choose between versions no longer gives an unbiased estimate; a part kept unseen until the end does. Hastie, Tibshirani & Friedman, *The Elements of Statistical Learning* (2nd ed., 2009), section 7.2.
- An imperfect ground truth: a reference set missing true triples makes evaluation "overly pessimistic" for methods that extract them, Zhang & Soh, *Extract, Define, Canonicalize* (2024), [paper](https://arxiv.org/abs/2404.03868).
