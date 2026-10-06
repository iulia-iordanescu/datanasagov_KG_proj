# Evaluation metrics

The one place each of evaluation's numbers is explained: what it is, its formula with an example, how to read it, what it assumes, and where it comes from. Other files point here instead of repeating it. Each metric's worked example is under *Examples*, and where it comes from under *Sources*, at the end. Terms: [docs/terminology.md](../docs/terminology.md).

Formulas use the usual set symbols: \|…\| is the number of members, ∪ is union (in either), ∩ is intersection (in both). Every count is over all the evaluated records of one part (tuning or held-out) together, not one record at a time, and never includes the DESCRIBES rows (they're compared on their own, see *What each record describes*).

## Pairs

### <ins>Definition</ins>

A **pair** is one extracted triple and one ground truth triple of the same record that evaluation takes to state the same fact, once the extracted triple's predicate, subject class and object class are translated into the ground truth vocabulary (through the translation table, [`annotations/component_class_mapping.csv`](../annotations/component_class_mapping.csv)). Each triple has at most one partner. Evaluation finds the largest possible set of exact pairs, then, among the triples left, the largest possible set of partial pairs. There are two **pair levels**, exact and partial, and when two triples count as stating the same fact depends on the level: they form an **exact pair** or a **partial pair**.

| Pair level | Two triples count as stating the same fact when… |
|---|---|
| exact | they have the same predicate, the same subject instance and the same object instance, once evened out (glossary): ignoring case, spacing, quote marks, dashes, punctuation at either end and a leading "a", "an" or "the" |
| partial | they have the same predicate; the two subject instances are equal or one appears inside the other as whole words (either way round); and the same holds for the two object instances. Only triples left without an exact partner can form one. |

Strict is an extra condition on a pair at either level: a **strict pair** is an exact or partial pair whose subject classes and object classes are also the same.

So every pair is exactly one of these four:

| | strict (subject classes and object classes the same) | not strict |
|---|---|---|
| exact pair | exact pairs ∩ strict pairs | exact pairs, not strict |
| partial pair | partial pairs ∩ strict pairs | partial pairs, not strict |

All pairs = exact pairs ∪ partial pairs (no pair is both), and strict pairs are some of each.

A triple left without a partner is **extracted only** (an extracted triple) or **ground truth only** (a ground truth triple: a missed fact).

### <ins>Assumes and can't see</ins>

- Containment can be fooled: "MODIS" is inside "MODIS Terra", a different instrument. On tuning records you review partial pairs in the annotation tool (*Partial pairs*); two triples marked "not the same fact" are never paired. Held-out records' partial pairs are never reviewed (that would mean looking at them).
- Two component classes of the current schema that translate to one component class of the ground truth vocabulary can't be told apart.

Worked example: [Pairs: example](#pairs-example). Sources: [Pairs: sources](#pairs-sources).

## From the evaluated records to the whole catalog

Every metric is computed on the evaluated records only (the fair sample of finished, extracted records). Read for the whole catalog, it is approximate, for these reasons, each with what checks or limits it.

| Reason | What it means | What checks or limits it |
|---|---|---|
| sampling error | A different sample of the same size would give a somewhat different number. | The margin of error says how much (see *Margin of error*). Given only from 20 evaluated records on. |
| the sample's mix of maintainers | The pool was drawn stratified by maintainer, and only its first finished records are evaluated: if their mix of maintainers differs from the catalog's, the number leans toward the over-represented ones. | The pool matches the catalog's mix of maintainers (drawn with proportional allocation: `annotations/ground_truth_candidates.json`). The report compares, per sampling group, the share of the evaluated records with the share of the pool, and, from 20 evaluated records on, warns when they differ by more than 10 percentage points (`SHARE_GAP`). |
| small-sample bias of a ratio | Each metric is a ratio of two counts that both vary from sample to sample; such a ratio is slightly biased in small samples. | It shrinks as the sample grows; it is small next to the sampling error. |
| an imperfect ground truth | "Correct" means having a partner in the ground truth: a fact missing from it, or a mistake in it, shifts the number the same way in every sample. | Nothing in the numbers; only care in annotating (see `050_annotate/050_annotate.md`). |
| triples vs edges | If step 080 merges identical triples from different records into one edge, a share of edges can differ from a share of extracted triples. | Unknown until step 080 is built. |

## Precision

### <ins>Definition</ins>

The share of the extracted triples that are correct. What "correct" means depends on the version.

### <ins>Formula</ins>

Four versions.

| Version | An extracted triple counts as correct when it… | Formula |
|---|---|---|
| exact precision | forms an exact pair | \|exact pairs\| ÷ \|extracted triples\| |
| partial precision | forms an exact or a partial pair | \|exact pairs ∪ partial pairs\| ÷ \|extracted triples\| |
| strict exact precision | forms an exact pair, with the right subject class and object class | \|exact pairs ∩ strict pairs\| ÷ \|extracted triples\| |
| strict partial precision | forms an exact or a partial pair, with the right subject class and object class | \|(exact pairs ∪ partial pairs) ∩ strict pairs\| ÷ \|extracted triples\| |

### <ins>Interpretations</ins>

Below, *p* is the value of one version of precision, and "correct" is that version's (table above). *p* is a number from 0 to 1 (shown as 0% to 100%; with no extracted triples it is undefined, shown as "–").

- *p* of the extracted triples are correct. So in a knowledge graph built from the whole catalog's extracted triples, approximately 1 − *p* of those edges would not be correct.
- Partial precision minus exact precision: the share of the extracted triples that are correct only once wording differences are forgiven (e.g. "MODIS" vs "Moderate Resolution Imaging Spectroradiometer (MODIS)").
- Precision minus strict precision, at the same pair level: the share of the extracted triples that state the right fact but with a wrong subject class or object class.
- In every version, an extracted triple is not correct when: the text doesn't state the fact; it repeats, in other words, a fact already extracted (only one of the two can form a pair); or it's true but missing from the ground truth. It is also not correct when, compared with the ground truth triple stating the same fact:

  | Version | An extracted triple is also not correct when… |
  |---|---|
  | exact precision | its predicate differs; or its subject instance or object instance differs, once evened out |
  | partial precision | its predicate differs; or its subject instance or object instance neither equals the ground truth's nor contains it (or is contained in it) as whole words |
  | strict exact precision | as for exact precision; or its subject class or object class differs |
  | strict partial precision | as for partial precision; or its subject class or object class differs |

### <ins>Assumes and can't see</ins>

- That the ground truth lists every fact the records state: a true triple missing from it counts against precision.
- Why "approximately" for the whole catalog: see [*From the evaluated records to the whole catalog*](#from-the-evaluated-records-to-the-whole-catalog).
- How sure the number is: see *Margin of error*.

Worked example: [Precision: example](#precision-example). Sources: [Precision: sources](#precision-sources).

## Recall

### <ins>Definition</ins>

The share of the ground truth triples that extraction found. What "found" means depends on the version.

### <ins>Formula</ins>

Four versions.

| Version | A ground truth triple counts as found when it… | Formula |
|---|---|---|
| exact recall | forms an exact pair | \|exact pairs\| ÷ \|ground truth triples\| |
| partial recall | forms an exact or a partial pair | \|exact pairs ∪ partial pairs\| ÷ \|ground truth triples\| |
| strict exact recall | forms an exact pair, and extraction gave the right subject class and object class | \|exact pairs ∩ strict pairs\| ÷ \|ground truth triples\| |
| strict partial recall | forms an exact or a partial pair, and extraction gave the right subject class and object class | \|(exact pairs ∪ partial pairs) ∩ strict pairs\| ÷ \|ground truth triples\| |

### <ins>Interpretations</ins>

- As a chance: recall 57% means a fact the ground truth lists has a 57% chance of being found.
- For the graph: with recall 57%, it would lack 3 of every 7 facts the records state.
- Read with precision: each alone can be fooled. An extractor that states just one triple it is sure of has perfect precision and almost no recall; one that states everything it can think of has perfect recall and poor precision.
- Low recall means many ground truth triples without a partner: facts extraction missed, facts whose predicate the current schema doesn't have (see *Recall upper bound*), or a wrong row in the translation table ([`annotations/component_class_mapping.csv`](../annotations/component_class_mapping.csv)).

### <ins>Assumes and can't see</ins>

- That the ground truth lists every fact the records state: a fact missing from it isn't counted at all, neither found nor missed.
- How sure the number is: see *Margin of error*.

Worked example: [Recall: example](#recall-example). Sources: [Recall: sources](#recall-sources).

## F1

### <ins>Definition</ins>

Precision and recall combined into one number, high only when both are.

### <ins>Formula</ins>

Four versions, each from the precision and recall of the same version.

| Version | Formula |
|---|---|
| exact F1 | 2 × exact precision × exact recall ÷ (exact precision + exact recall) |
| partial F1 | 2 × partial precision × partial recall ÷ (partial precision + partial recall) |
| strict exact F1 | 2 × strict exact precision × strict exact recall ÷ (strict exact precision + strict exact recall) |
| strict partial F1 | 2 × strict partial precision × strict partial recall ÷ (strict partial precision + strict partial recall) |

The code computes the same number as 2 × \|pairs counted\| ÷ (\|extracted triples\| + \|ground truth triples\|), which also settles the edge cases: F1 is 0 when no pair is counted (even with no extracted triples, where precision is undefined), and undefined ("–") only when there are neither extracted triples nor ground truth triples.

### <ins>Interpretations</ins>

- Not a chance: it's a kind of average of precision and recall (the *harmonic mean*), pulled toward the lower of the two. Precision 100% with recall 10% gives F1 18%, not 55%.
- The usual headline number for comparing runs or models, and for comparing with published results.

### <ins>Assumes and can't see</ins>

- It weighs precision and recall equally. If one matters more (for a graph, a wrong statement is often worse than a missing one), read precision and recall themselves.
- It doesn't show which of the two is low.

Worked example: [F1: example](#f1-example). Sources: [F1: sources](#f1-sources).

## Entity-class accuracy

### <ins>Definition</ins>

Among the pairs counted, the share that are strict. Which pairs are counted depends on the version.

### <ins>Formula</ins>

Two versions.

| Version | Pairs counted | Formula |
|---|---|---|
| exact entity-class accuracy | exact pairs | \|exact pairs ∩ strict pairs\| ÷ \|exact pairs\| |
| partial entity-class accuracy | exact pairs ∪ partial pairs | \|(exact pairs ∪ partial pairs) ∩ strict pairs\| ÷ \|exact pairs ∪ partial pairs\| |

### <ins>Interpretations</ins>

- As a chance: entity-class accuracy 75% means that when extraction gets a fact right, its subject class and object class are both right with a 75% chance.
- For the graph: the share of right statements whose two nodes also get the right node labels.
- Read with precision and recall: they say whether facts are found; this says whether the things in them are classed right.

### <ins>Assumes and can't see</ins>

- Only paired triples are judged: the subject class and object class of a triple without a partner aren't counted anywhere.
- Two component classes of the current schema that translate to one component class of the ground truth vocabulary look the same, so mixing them up isn't seen.
- How sure the number is: see *Margin of error*.

Worked example: [Entity-class accuracy: example](#entity-class-accuracy-example). Sources: [Entity-class accuracy: sources](#entity-class-accuracy-sources).

## Recall upper bound

### <ins>Definition</ins>

The share of the ground truth triples that the current schema can express at all: the most recall any extraction with this schema and translation table could get. A ground truth triple is **within reach** when its predicate is one that some checked row of the translation table translates to, and **within strict reach** when its subject class and object class are too. Which ground truth triples count depends on the version.

### <ins>Formula</ins>

Two versions.

| Version | A ground truth triple counts when it is… | Formula |
|---|---|---|
| recall upper bound | within reach | \|ground truth triples within reach\| ÷ \|ground truth triples\| |
| strict recall upper bound | within strict reach | \|ground truth triples within strict reach\| ÷ \|ground truth triples\| |

### <ins>Interpretations</ins>

- As a limit: recall upper bound 80% means no extraction with this schema can find more than 80% of the facts; the other 20% use a predicate it has no counterpart for.
- Read with recall: the gap between the two is what extraction missed although the schema could express it (see *Recall within reach*).
- A low upper bound points at the schema (schema induction, or the schema additions) or at the translation table (a row that says `(none)`, or a missing row).
- The strict version is the limit for strict recall: a triple can be within reach but not within strict reach when the schema has no counterpart for its subject class or object class.

### <ins>Assumes and can't see</ins>

- Within reach means only that the schema has the component classes: not that the model could find the fact in the text.
- It depends on the translation table: a row wrongly saying `(none)` lowers it.
- How sure the number is: see *Margin of error*.

Worked example: [Recall upper bound: example](#recall-upper-bound-example). Sources: [Recall upper bound: sources](#recall-upper-bound-sources).

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

Record A: 4 extracted triples, 3 of them in pairs. Record B: 1 extracted triple, in a pair. Precision = (3 + 1) ÷ (4 + 1) = 80%. Averaging the records' own precisions (75% and 100%) would give 87.5% instead, letting record B's single triple weigh as much as record A's four.

### Recall: example

Record A: the ground truth has 5 triples, 3 of them found. Record B: it has 2, 1 found. Recall = (3 + 1) ÷ (5 + 2) = 57%.

### F1: example

With the records of the examples above: 4 pairs, 5 extracted triples, 7 ground truth triples. Precision 80%, recall 57%, F1 = 2 × 0.80 × 0.57 ÷ (0.80 + 0.57) = 67%.

### Entity-class accuracy: example

4 pairs, 3 of them strict: entity-class accuracy = 3 ÷ 4 = 75%.

### Recall upper bound: example

The record of the *Pairs* example has 5 ground truth triples, with the predicates ABOARD (G1, G2, G5), ACQUIRED_BY (G3) and HAS_TIME_SPAN (G4). Say the current schema has counterparts for ABOARD and ACQUIRED_BY but not HAS_TIME_SPAN, and none for the entity class Dataset.

- Within reach: G1, G2, G3, G5 (G4's predicate has no counterpart). Recall upper bound = 4 ÷ 5 = 80%.
- Within strict reach: G1, G2, G5 (G3's subject class, Dataset, has no counterpart either). Strict recall upper bound = 3 ÷ 5 = 60%.

## Sources

### Pairs: sources

- *Exact* and *partial*: the WebNLG 2020 challenge's evaluation of text-to-triples extraction (Castro Ferreira et al., 2020, [paper](https://aclanthology.org/2020.webnlg-1.7.pdf)). Ours is stricter on partial: whole words, not any overlap.
- Credit: here a partial pair counts as fully right. The SemEval-2013 scoring convention ([nervaluate](https://github.com/MantisAI/nervaluate)) gives a partial match half credit: partial precision = (exact + 0.5 × partial) ÷ extracted. Full credit fits our meaning of a partial pair, the same fact named differently (on tuning records, confirmed by your review), but our partial numbers are higher than that convention's and not directly comparable with published partial scores.
- *Strict*, meaning right relation and right entity types: the "Strict" setting of end-to-end relation extraction (Bekoulis et al., 2018, as described by Taillé et al., 2020, [paper](https://aclanthology.org/2020.emnlp-main.301/)). WebNLG's "strict" means something else (the element's role must match), so it isn't the source here.
- At most one partner per triple, largest set of pairs: a maximum matching (Kuhn's algorithm, `070_evaluate/070_evaluate_helpers/pairing.py`).

### Precision: sources

The standard definition of precision, summed over all items before dividing (*micro-averaging*), as opposed to averaging per record (*macro-averaging*): Manning, Raghavan & Schütze, *Introduction to Information Retrieval* (2008), sections 8.3 and 13.6 ([book](https://nlp.stanford.edu/IR-book/)). Micro-averaging over triples is the usual choice in relation extraction.

### Recall: sources

The standard definition of recall, micro-averaged like precision: Manning, Raghavan & Schütze (2008), sections 8.3 and 13.6.

### F1: sources

The F-measure of van Rijsbergen, *Information Retrieval* (1979), with precision and recall weighted equally; Manning, Raghavan & Schütze (2008), section 8.3. The standard headline metric in relation extraction.

### Entity-class accuracy: sources

No single standard name. It separates the two settings end-to-end relation extraction reports side by side, "Strict" (with entity types) and "Boundaries" (without), described by Taillé et al. (2020): here, strict pairs ÷ all pairs.

### Recall upper bound: sources

An upper bound on recall, set by an earlier stage of a pipeline (here, the schema), is standard: Pink, Nothman & Curran (2014), "Analysing recall loss in named entity slot filling", EMNLP ([paper](https://aclanthology.org/D14-1089.pdf)): "the recall of a system's coarse candidate generation process sets a hard upper bound on performance". As there, the bound uses the same matching rule as the metric it bounds: a pair needs only the predicate, so the recall upper bound counts only the predicate; a strict pair also needs the entity classes, so the strict recall upper bound counts them too. The name "recall upper bound" is the established one; no paper found uses a schema-specific term.
