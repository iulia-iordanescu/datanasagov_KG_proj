# Evaluation metrics

The one place each of evaluation's numbers is explained: what it is, its formula with an example, how to read it, what it assumes, and where it comes from. Other files point here instead of repeating it. Each metric's worked example is under *Examples*, and where it comes from under *Sources*, at the end. Terms: [docs/terminology.md](../docs/terminology.md).

Formulas use the usual set symbols: \|…\| is the number of members, ∪ is union (in either), ∩ is intersection (in both). Every count is over all the evaluated records together, and never includes the DESCRIBES rows (they're compared on their own, see *What each record describes*).

## Pairs

### <ins>Definition</ins>

A **pair** is one extracted triple and one ground truth triple of the same record that evaluation takes to state the same fact, once the extracted triple's predicate, subject class and object class are translated into the ground truth vocabulary (through `annotations/component_class_mapping.csv`). Each triple has at most one partner, and evaluation finds the largest possible set of pairs. There are two kinds, **exact pairs** and **partial pairs**, and when two triples count as stating the same fact depends on the kind.

| Kind | Two triples count as stating the same fact when… |
|---|---|
| exact pair | they have the same predicate, the same subject instance and the same object instance, ignoring case, spacing, quote marks, dashes, punctuation at either end and a leading "a", "an" or "the" |
| partial pair | they have the same predicate; the two subject instances are equal or one appears inside the other as whole words (either way round); and the same holds for the two object instances. Only triples left without an exact partner can form one. |

Strict is an extra condition on a pair of either kind: a **strict pair** is an exact or partial pair whose subject classes and object classes are also the same.

So every pair is exactly one of these four:

| | strict (classes the same) | not strict |
|---|---|---|
| exact pair | exact pairs ∩ strict pairs | exact pairs, not strict |
| partial pair | partial pairs ∩ strict pairs | partial pairs, not strict |

All pairs = exact pairs ∪ partial pairs (no pair is both), and strict pairs are some of each.

A triple left without a partner is **extracted only** (an extracted triple) or **ground truth only** (a ground truth triple: a missed fact).

### <ins>Assumes and can't see</ins>

- Containment can be fooled: "MODIS" is inside "MODIS Terra", a different instrument. On tuning records you review partial pairs in the annotation tool (*Partial pairs*); two triples marked "not the same fact" are never paired. Held-out records' partial pairs are never reviewed (that would mean looking at them).
- Two component classes of the current schema that translate to one component class of the ground truth vocabulary can't be told apart.

Worked example: [Pairs: example](#pairs-example). Sources: [Pairs: sources](#pairs-sources).

## Precision

### <ins>Definition</ins>

The share of extraction's triples that are correct. What "correct" means depends on the version.

### <ins>Formula</ins>

Four versions.

| Version | An extracted triple counts as correct when it… | Formula |
|---|---|---|
| exact precision | forms an exact pair | \|exact pairs\| ÷ \|extracted triples\| |
| partial precision | forms an exact or a partial pair | \|exact pairs ∪ partial pairs\| ÷ \|extracted triples\| |
| strict exact precision | forms an exact pair, with the right subject class and object class | \|exact pairs ∩ strict pairs\| ÷ \|extracted triples\| |
| strict partial precision | forms an exact or a partial pair, with the right subject class and object class | \|(exact pairs ∪ partial pairs) ∩ strict pairs\| ÷ \|extracted triples\| |

### <ins>How to read it</ins>

- As a chance: precision 80% means a triple extraction keeps has an 80% chance of forming a pair.
- For the graph: with precision 80%, 1 statement in 5 would have no counterpart in the ground truth.
- Low precision means many triples without a partner: a wrong subject, predicate or object, a fact the text doesn't state, the same fact again in other words, or a true fact the ground truth lacks.

### <ins>Assumes and can't see</ins>

- That the ground truth lists every fact the records state: a true triple missing from it counts against precision.
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

### <ins>How to read it</ins>

- As a chance: recall 57% means a fact the ground truth lists has a 57% chance of being found.
- For the graph: with recall 57%, it would lack 3 of every 7 facts the records state.
- Low recall means many ground truth triples without a partner: facts extraction missed, facts whose predicate the current schema doesn't have (see *Recall upper bound*), or a wrong row in the translation table.

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

### <ins>How to read it</ins>

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

### <ins>How to read it</ins>

- As a chance: entity-class accuracy 75% means that when extraction gets a fact right, its subject class and object class are both right with a 75% chance.
- For the graph: the share of right statements whose two nodes also get the right node labels.
- Read with precision and recall: they say whether facts are found; this says whether the things in them are classed right.

### <ins>Assumes and can't see</ins>

- Only paired triples are judged: the classes of a triple without a partner aren't counted anywhere.
- Two component classes of the current schema that translate to one component class of the ground truth vocabulary look the same, so mixing them up isn't seen.
- How sure the number is: see *Margin of error*.

Worked example: [Entity-class accuracy: example](#entity-class-accuracy-example). Sources: [Entity-class accuracy: sources](#entity-class-accuracy-sources).

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

In all: 6 extracted triples, 5 ground truth triples; 2 exact pairs (E1–G1 strict, E2–G2 not); 2 partial pairs (E3–G3 strict, E4–G4 not); so 2 strict pairs, one of each kind; 2 extracted only (E5, E6); 1 ground truth only (G5).

### Precision: example

Record A: 4 extracted triples, 3 of them in pairs. Record B: 1 extracted triple, in a pair. Precision = (3 + 1) ÷ (4 + 1) = 80%. Averaging the records' own precisions (75% and 100%) would give 87.5% instead, letting record B's single triple weigh as much as record A's four.

### Recall: example

Record A: the ground truth has 5 triples, 3 of them found. Record B: it has 2, 1 found. Recall = (3 + 1) ÷ (5 + 2) = 57%.

### F1: example

With the records of the examples above: 4 pairs, 5 extracted triples, 7 ground truth triples. Precision 80%, recall 57%, F1 = 2 × 0.80 × 0.57 ÷ (0.80 + 0.57) = 67%.

### Entity-class accuracy: example

4 pairs, 3 of them strict: entity-class accuracy = 3 ÷ 4 = 75%.

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
