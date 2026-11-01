# Schema fit

Part of [Evaluation metrics](../metrics.md), which explains the notation and lists every metric.

## <ins>Definition</ins>

The proportion of the occurrences whose [predicate](../../docs/terminology.md#3-schemas) the [ground truth schema](../../docs/terminology.md#3-schemas) can say, through the checked [translation table](../../docs/terminology.md#7-evaluating-extraction-step-070).

An occurrence is an **untranslatable occurrence** when its predicate translates to `(none)` through the row that applies to it: its [conditional row](../../docs/terminology.md#7-evaluating-extraction-step-070) with the most conditions that hold for its subject's and object's entity classes, as extracted, else its unconditional row (code: `070_evaluate/070_evaluate_helpers/pairing.py`, `is_untranslatable`). A predicate with no row at all translates to `(none)` too. The other occurrences are the **translatable occurrences**. Nothing else makes an occurrence untranslatable:

- an [entity class](../../docs/terminology.md#3-schemas) whose row says `(none)` doesn't: such an occurrence can still form a [pair](pairs.md), and only can't be [strict](pairs.md) ([Precision](precision.md), row 16 of *When an occurrence counts as not correct*);
- a conditional row that leaves some cases at `(none)` makes exactly those cases untranslatable. *Suppose:* SOURCED_FROM (current schema) has its unconditional row to `(none)` and a conditional row, if its object is of entity class Mission, to FROM_MISSION (ground truth schema). *Then:* "D" (Dataset) SOURCED_FROM "Rosetta" (Mission) is translatable, and "D" (Dataset) SOURCED_FROM "X" (Dataset) is untranslatable.

Why the predicate alone: it is the one component class a pair must match ([Pairs](pairs.md), *Definition*), and [within reach](recall_upper_bound.md) is defined by the predicate for the same reason. An untranslatable occurrence can pair with nothing: its translated predicate is marked as the current schema's, so it equals no predicate of the ground truth schema, of a [ground truth triple](../../docs/terminology.md#4-ground-truth-and-samples) or of a fact that waits on an expert.

## <ins>Formula</ins>

One version (it counts no pairs, so it has no [pair level](pairs.md)).

| Version | Formula |
|---|---|
| schema fit | (\|occurrences\| − \|U\|) ÷ \|occurrences\| |

U is the set of the untranslatable occurrences. It is a number from 0 to 1; with no occurrences across the [records](../../docs/terminology.md#1-records-and-their-text), it is undefined.

U is left out of [precision](precision.md)'s denominator and of [F1](f1.md)'s ([Precision](precision.md), *Untranslatable occurrences*). [Recall](recall.md), the [recall upper bound](recall_upper_bound.md), [recall within reach](recall_within_reach.md), [entity-class accuracy](entity_class_accuracy.md) and [describes accuracy](describes.md) don't count occurrences, so they don't change.

## <ins>Interpretations</ins>

Let *s* be the value of schema fit. It reads two ways: what was computed, on the evaluated records, and what it means for the [knowledge graph](../../docs/terminology.md#8-the-pipeline), for the whole catalog.

**What was computed** (the evaluated records)

1. *s* is the proportion of the evaluated records' occurrences whose predicate the ground truth schema can say; 1 − *s* is the proportion that the ground truth can neither confirm nor deny.
2. Precision is computed over the proportion *s* of the occurrences only (less those matching a fact that waits on an expert), so read the two together: a high precision with a low *s* judges a small part of what extraction said.
3. It is the mirror of the [recall upper bound](recall_upper_bound.md) on the extraction side: the recall upper bound says what the ground truth states that the current schema can reach; schema fit says what the current schema states that the ground truth schema can judge.

**What it means for the knowledge graph** (the whole catalog, approximately)

Say the knowledge graph is built from the whole catalog's [extracted triples](../../docs/terminology.md#6-extracting-with-a-schema-step-060), one [edge](../../docs/terminology.md#8-the-pipeline) per extracted triple. Then:

1. Approximately 1 − *s* of its edges would have a predicate that no ground truth triple could ever confirm or deny: they may be right or wrong.

## <ins>Assumes and can't see</ins>

- That every `(none)` row of the translation table is right: a wrong one lowers *s*, and hides from precision an occurrence that should have been judged ([Precision](precision.md), *Untranslatable occurrences*).
- It is not a mistake of the model by itself, nor of a schema by itself: it is a gap between two schemas. In Text2KGBench (below), the model is given the ontology [the schema it is judged by], so a triple outside it is the model's; here the model extracts with the [current schema](../../docs/terminology.md#6-extracting-with-a-schema-step-060) and never sees the ground truth schema.
- Read for the whole catalog, *s* is approximate for the [reasons every metric shares](approximately.md); the [report](../../docs/terminology.md#8-the-pipeline) measures one of them, sampling error, with *s*'s [margin of error](approximately.md#sampling-error).

Worked example: [Schema fit: example](#example). Sources: [Schema fit: sources](#sources).

## Example

*Suppose:* two records are evaluated. Record A has 4 occurrences, 1 of them with the predicate OPERATED_BY (current schema), whose row says `(none)`; record B has 2 occurrences, both translatable. *Then:* \|occurrences\| = 6, \|U\| = 1, and schema fit = (6 − 1) ÷ 6 = 83%. With 3 [exact pairs](pairs.md) and no fact waiting on an expert, exact precision = 3 ÷ (6 − 1) = 60%, not 3 ÷ 6 = 50%: the OPERATED_BY occurrence is judged neither right nor wrong.

## Sources

- Text2KGBench (Mihindukulasooriya, Tiwari, Enguix & Lata, "Text2KGBench: A Benchmark for Ontology-Driven Knowledge Graph Generation from Text", ISWC 2023, [paper](https://arxiv.org/abs/2308.02357), section 4) reports, beside precision, **ontology conformance**: "ontology conforming LLM output triples divided by total LLM output triples", where "a triple is considered to be conforming to the ontology if the relation is one of the canonical relations listed in the ontology". It doesn't say whether a triple that doesn't conform stays in precision's denominator. What I take from it: a conformance proportion reported as a number of its own; schema fit is that number, with the difference above (here the model never sees the ground truth schema).
- EDC (Zhang & Soh, "Extract, Define, Canonicalize: An LLM-based Framework for Knowledge Graph Construction", 2024, [paper](https://arxiv.org/abs/2404.03868), section 3.1, *Target Alignment*): "If a transformation is deemed unreasonable, indicating no semantic equivalent in the target schema", then "the component, and its related triplets are excluded", and precision, recall and F1 are computed over what remains (section 4.1.1). The paper doesn't report how many were excluded. What I take from it: leaving triples with no counterpart in the target schema out of precision is the field's practice; schema fit adds the share left out, which EDC doesn't report.
- Decided on 2026-11-01, before any look at the held-out part (`annotations/held_out_looks.csv` held only its header): from evaluation version 3 (`pairing.py`, `EVALUATION_VERSION`), untranslatable occurrences leave precision, F1 and partial F1, since a fact the ground truth schema can't express is not an extraction mistake.
