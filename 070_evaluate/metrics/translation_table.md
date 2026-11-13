# The translation table

Part of [Evaluation metrics](../metrics.md), which explains the notation and lists every metric.

The [translation table](../../docs/terminology.md#7-evaluating-extraction-step-070) (`annotations/component_class_mapping.csv`) turns each [extracted triple](../../docs/terminology.md#6-extracting-with-a-schema-step-060) into a [translated extracted triple](../../docs/terminology.md#7-evaluating-extraction-step-070), which every metric then compares with the [ground truth triples](../../docs/terminology.md#4-ground-truth-and-samples). This page states that translation exactly, as two functions, with the rule that picks a row, the swap of subject and object, what `(none)` does, the properties of the two functions, the four kinds of **match**, and the per-entry coverage measured on the reported runs. What a row is, its columns, and the rule a person follows when writing or checking one are in the terminology (*translation table*); how step 070 adds rows and stops for checking is in [070's guide](../070_evaluate.md), *How it works*, step 2.

The translation goes one way: from the [current schema](../../docs/terminology.md#6-extracting-with-a-schema-step-060), the one step 060 extracted with, to the [ground truth schema](../../docs/terminology.md#3-schemas). The ground truth triples are never translated. They stay as written, and each extracted triple is translated into their schema before it is compared with them. In the reported runs the current schema is the [induced schema](../../docs/terminology.md#5-learning-the-schema-step-040).

## <ins>Notation</ins>

- *E*<sub>c</sub> and *P*<sub>c</sub> are the [entity classes](../../docs/terminology.md#3-schemas) and the [predicates](../../docs/terminology.md#3-schemas) of the current schema.
- *E*<sub>g</sub> and *P*<sub>g</sub> are those of the ground truth schema, without its [held-out-only entries](../../docs/terminology.md#3-schemas), which are never the target of a row (`070_evaluate/070_evaluate_helpers/component_classes.py`, `gtt_schema`).
- ⊥ stands for `(none)`: no counterpart in the ground truth schema.
- Two [component classes](../../docs/terminology.md#3-schemas) are the same when they are the same by [loose match](../../docs/terminology.md#3-schemas) (`common/common_helpers/triples_io.py`, `component_class_key`): case, spacing and punctuation aside, so `PhysicalQuantity` and `physical quantity` are one component class.
- An extracted triple is written (*s*, *c*<sub>s</sub>, *p*, *o*, *c*<sub>o</sub>): its [subject instance](../../docs/terminology.md#2-triples) *s* with its entity class *c*<sub>s</sub>, its predicate *p*, and its [object instance](../../docs/terminology.md#2-triples) *o* with its entity class *c*<sub>o</sub>, all as extracted, so *c*<sub>s</sub>, *c*<sub>o</sub> ∈ *E*<sub>c</sub> and *p* ∈ *P*<sub>c</sub>.

## <ins>The two functions</ins>

The table defines two functions:

- **T**<sub>E</sub> : *E*<sub>c</sub> → *E*<sub>g</sub> ∪ {⊥}, for entity classes: T<sub>E</sub>(*c*) is the target of the row of entity class *c*.
- **T**<sub>P</sub> : *P*<sub>c</sub> × *E*<sub>c</sub> × *E*<sub>c</sub> → (*P*<sub>g</sub> ∪ {⊥}) × {no, yes}, for predicates: T<sub>P</sub>(*p*, *c*<sub>s</sub>, *c*<sub>o</sub>) = (*q*, σ), where *q* is the target of the row of *p* that applies to a subject of entity class *c*<sub>s</sub> and an object of entity class *c*<sub>o</sub> (below), and σ is that row's `swap_subject_and_object`.

T<sub>P</sub> takes the two entity classes as inputs because a predicate can have **conditional rows**, which apply only to some entity classes of its subject or object. T<sub>E</sub> has no such inputs: a condition belongs to a predicate's row only, and step 070 stops on an entity class's row with one (`common/common_helpers/component_class_mapping.py`, `value_problems`).

Both functions are total on the current schema when step 070 scores. One table serves every schema, current and past, so it holds rows for component classes that the current schema lacks. Those rows translate nothing in this run. Step 070 still stops on a problem anywhere in the table that would leave it unclear what a row says: two rows of one component class with the same condition (*repeated*), a conflict (below), or a value outside those its columns take. Before it scores, step 070 makes sure every component class of the current schema has an unconditional row: one spelled like a component class of the ground truth schema gets that one as its target at once (`checked` = `same component class`, `match` = `same`), the model proposes the others, and step 070 then stops until a person has checked them. It also stops on any row of the current schema that is not checked, is stale, has a [missing target](../../docs/terminology.md#7-evaluating-extraction-step-070), or now exists (each a [row state](../../docs/terminology.md#7-evaluating-extraction-step-070)), and on a conditional row whose condition names an entity class not in *E*<sub>c</sub>. So every row that the two functions read is checked, and its meanings are those it was checked against.

## <ins>Which row applies to a predicate</ins>

Let *R*(*p*) be the rows of predicate *p*. Each row *r* has a condition (*a*<sub>r</sub>, *b*<sub>r</sub>), with *a*<sub>r</sub> ∈ *E*<sub>c</sub> ∪ {any} for the subject (column `if_subject_class`) and *b*<sub>r</sub> ∈ *E*<sub>c</sub> ∪ {any} for the object (column `if_object_class`); an empty column is any. The **unconditional row** of *p* is the one with condition (any, any), and every predicate of the current schema has exactly one. The others are **conditional rows**, added by hand.

1. Row *r* **applies** to (*c*<sub>s</sub>, *c*<sub>o</sub>) when (*a*<sub>r</sub> = any ∨ *a*<sub>r</sub> = *c*<sub>s</sub>) ∧ (*b*<sub>r</sub> = any ∨ *b*<sub>r</sub> = *c*<sub>o</sub>). The condition is read on the entity classes as extracted, in the current schema, before any translation or swap.
2. Let *n*(*r*) be the number of conditions of *r*: 0, 1 or 2. Of the rows of *R*(*p*) that apply, the one with the largest *n*(*r*) is used. The unconditional row always applies, so some row is always used, and it is used only when no conditional row applies.
3. Two rows that apply with the same *n*(*r*) cannot have the same condition, since a component class with two rows of the same condition stops step 070 (*repeated*). With *n*(*r*) = 2 they would have the same condition, so a tie can only be between a row with a condition on the subject alone and a row with a condition on the object alone. When these two translate differently (another target or another σ) and *R*(*p*) has no row with both their conditions, they are a **conflict**, and step 070 stops and names both (`conflicts`). A row with both conditions settles them: it applies whenever both of them apply, and it has *n*(*r*) = 2. Two such rows that translate alike give the same result, and the code takes the first in the file.

The code of this rule is `rule_for` (in `common/common_helpers/component_class_mapping.py`) and `predicate_rule` (in `070_evaluate/070_evaluate_helpers/pairing.py`), which apply the same test.

*Suppose:* extraction gives (“MOD11A1” [Dataset], HAS_PROPERTY, “1 km” [SpatialResolution]) in the current schema. HAS_PROPERTY (current schema) has its unconditional row to `(none)` and four conditional rows, each with the subject condition Dataset (current schema); one of them, with the object condition SpatialResolution (current schema), translates to HAS_SPATIAL_RESOLUTION (ground truth schema). *Then:* two rows apply, the unconditional row (*n* = 0) and that conditional row (*n* = 2), so T<sub>P</sub>(HAS_PROPERTY, Dataset, SpatialResolution) = (HAS_SPATIAL_RESOLUTION, no). For (“MOD11A1” [Dataset], HAS_PROPERTY, “land surface temperature” [PhysicalQuantity]) only the unconditional row applies, so T<sub>P</sub> gives (⊥, no).

*Suppose:* ACQUIRED_BY (current schema) has its unconditional row to ACQUIRED_BY_INSTRUMENT (ground truth schema), marked `broader`, and conditional rows with the object conditions Instrument, to ACQUIRED_BY_INSTRUMENT, and Spacecraft, SpaceStation and Aircraft, each to FROM_PLATFORM (ground truth schema), all marked `same`. *Then:* (“MOD11A1” [Dataset], ACQUIRED_BY, “Terra” [Spacecraft]) goes through the conditional row for Spacecraft, so its predicate translates to FROM_PLATFORM, and (“MOD11A1” [Dataset], ACQUIRED_BY, “NASA” [Organization]) goes through the unconditional row, so its predicate translates to ACQUIRED_BY_INSTRUMENT.

## <ins>The translated extracted triple</ins>

Let (*q*, σ) = T<sub>P</sub>(*p*, *c*<sub>s</sub>, *c*<sub>o</sub>). The translated extracted triple τ(*s*, *c*<sub>s</sub>, *p*, *o*, *c*<sub>o</sub>) is

- (*s*, T<sub>E</sub>(*c*<sub>s</sub>), *q*, *o*, T<sub>E</sub>(*c*<sub>o</sub>)) when σ = no, or when *q* = ⊥;
- (*o*, T<sub>E</sub>(*c*<sub>o</sub>), *q*, *s*, T<sub>E</sub>(*c*<sub>s</sub>)) when σ = yes and *q* ≠ ⊥.

The subject instance and the object instance are never translated: only the entity classes and the predicate change. When σ = yes, the subject and the object change places, and each keeps its own entity class, translated (code: `pairing.py`, `translate`).

*Suppose:* extraction gives (“Aqua” [Spacecraft], CARRIES, “MODIS” [Instrument]) in the current schema. The rows say CARRIES → ABOARD with σ = yes (marked `broader`), Spacecraft → Platform (`narrower`) and Instrument → Instrument (`same`); CARRIES has no conditional row. *Then:* T<sub>P</sub>(CARRIES, Spacecraft, Instrument) = (ABOARD, yes), and the translated extracted triple is (“MODIS” [Instrument], ABOARD, “Aqua” [Platform]) in the ground truth schema, since “A carries B” states the fact that “B is aboard A” states.

Each extracted triple gives one translated extracted triple, and two extracted triples can give the same one. A record's translated extracted triples therefore form a multiset, with one **occurrence** per extracted triple ([Pairs](pairs.md), *A multiset of translated extracted triples*).

The swap of a row is not the only swap in evaluation. For a symmetric predicate of the ground truth schema, ALSO_KNOWN_AS, pairing also tries each occurrence with its subject instance and object instance exchanged ([Pairs](pairs.md)). That happens after translation and does not depend on the table, so a row with σ = yes and the target ALSO_KNOWN_AS changes no pair, and step 070 notes such a row without stopping.

## <ins>What `(none)` does</ins>

`(none)` has a different effect for a predicate than for an entity class, because a [pair](pairs.md) needs the same predicate and matching instances but not the same entity classes.

- **The predicate translates to ⊥.** The occurrence keeps its predicate, marked as the current schema's (“ (current schema; translates to (none))” is added to it), so it equals no predicate of the ground truth schema. It is an [untranslatable extracted triple](schema_fit.md): it can pair with no ground truth triple and with no fact that waits on an expert, it is left out of the denominators of [precision](precision.md) and [F1](f1.md), and [schema fit](schema_fit.md) counts it. No swap is made.
- **An entity class translates to ⊥.** The occurrence keeps that entity class, marked the same way, so it equals no entity class of the ground truth schema. The occurrence can still form a pair, since a pair does not need the entity classes. It can never form a [strict pair](pairs.md), and a pair it forms counts as one whose entity class is wrong in that slot for [entity-class accuracy](entity_class_accuracy.md).

*Suppose:* extraction gives (“MOD11A1” [Dataset], HAS_PROPERTY, “land surface temperature” [PhysicalQuantity]), whose predicate translates to ⊥ (above). *Then:* it is an untranslatable extracted triple, whatever the [ground truth](../../docs/terminology.md#4-ground-truth-and-samples) states. *Suppose instead:* the row of Dataset said `(none)`. *Then:* (“MOD11A1” [Dataset], ACQUIRED_BY, “Terra” [Spacecraft]) would still translate to FROM_PLATFORM and could pair with the ground truth triple (“MOD11A1” [Dataset], FROM_PLATFORM, “Terra” [Platform]), but never strictly.

## <ins>Properties</ins>

1. **Each is a function.** Every input has exactly one output: a component class of the current schema has one unconditional row (*repeated* stops step 070 otherwise), and the rule above picks one row of a predicate for every pair of entity classes, a conflict stopping step 070 first.
2. **Neither is one-to-one.** Several inputs can have the same output. *Suppose:* the rows say Spacecraft → Platform, SpaceStation → Platform and Aircraft → Platform, each marked `narrower`. *Then:* T<sub>E</sub> gives Platform for all three, so evaluation cannot tell an extracted Spacecraft from an extracted Aircraft, and a mix-up between them costs nothing. The [report](../../docs/terminology.md#8-the-pipeline) lists such component classes (section *The translation table*), and the [annotation tool](../../docs/terminology.md#4-ground-truth-and-samples) marks their rows *shared*.
3. **Neither need reach every entry of the ground truth schema.** An entry of *E*<sub>g</sub> or *P*<sub>g</sub> that is the output of no input is one that no translated extracted triple can have. Per-entry coverage (below) measures how many entries are reached.
4. **Only this direction is used.** Nothing is translated from the ground truth schema to the current schema, so evaluation never needs an inverse of T<sub>E</sub> or T<sub>P</sub>, which properties 2 and 3 show does not exist.

## <ins>Match</ins>

Each row that does not say `(none)` records its **match**: how the row's component class relates to its target, judged by the person checking the row from the two definitions (step 070 sets `same` on a row it adds as `same component class`). It is empty on a `(none)` row, which has no counterpart.

Let ext(*X*) be the set of things that a component class *X* applies to: for an entity class, its instances; for a predicate, the facts it states, each taken as its subject instance and its object instance. For a conditional row, the row's component class counts only within its condition, so a row's match is judged within its condition: SOURCED_FROM (current schema) if its object is of entity class Mission → FROM_MISSION is `same`, though SOURCED_FROM alone is broader than FROM_MISSION (ground truth schema). For a row with σ = yes, ext of the row's predicate is read with subject and object exchanged. Let *a* be the row's component class and *b* its target. Each example below is a row of the reported runs' table, the row's component class from the induced schema and its target from the ground truth schema:

| match | In sets | Example | SKOS mapping property | Alignment format |
|---|---|---|---|---|
| same | ext(*a*) = ext(*b*) | DERIVED_FROM → COMPUTED_FROM | `skos:exactMatch` (or `skos:closeMatch`: two schemas never chain matches, which is what tells those two apart) | `=` |
| narrower | ext(*a*) ⊊ ext(*b*) | SpaceStation → Platform | `skos:broadMatch` ("has broader match") | `<` |
| broader | ext(*a*) ⊋ ext(*b*) | COVERS → HAS_TIME_SPAN (COVERS also covers an area or a measured variable) | `skos:narrowMatch` | `>` |
| overlap | ext(*a*) ∩ ext(*b*) ≠ ∅, and neither contains the other | Frequency → TemporalResolution | none (`skos:relatedMatch`, an associative link, is the nearest) | none |

The table uses plain words, not the SKOS names, because a SKOS name describes the target ("A `skos:broadMatch` B": B is the broader), which reads backwards.

The match changes no translation and no pair: T<sub>E</sub> and T<sub>P</sub> read only the target and σ. It says how far the translation through a row can be trusted:

- through a `same` or `narrower` row, ext(*a*) ⊆ ext(*b*), so every fact that the row's component class states is one that its target states, and a correct extracted triple translates to a correct one;
- through a `broader` or `overlap` row, a fact in ext(*a*) ∖ ext(*b*) is translated to the target anyway, so an occurrence stating it counts against precision, whereas the same fact through a `(none)` row would be left out of precision.

No metric gives credit for an inexact match: an occurrence counts only when its translated predicate is the ground truth triple's. The match is used in four places, none of which changes a number:

1. the report counts, per part, the occurrences through each kind of row and how many of them are [extracted only](pairs.md) ([070's guide](../070_evaluate.md), *Through which kind of row*);
2. the report splits the [recall upper bound](recall_upper_bound.md) by the best match among the rows that reach each ground truth triple [within reach](recall_upper_bound.md), in this order: `same` or `narrower`, then [no match value](../../docs/terminology.md#7-evaluating-extraction-step-070) yet, then only `broader` or `overlap` (`pairing.py`, `reach_bucket`);
3. step 070 warns about a predicate's unconditional row marked `broader` or `overlap` with no conditional row under it, since all its occurrences outside its target's meaning are translated to that target (`inexact_alone`);
4. the row state *suggested* applies to a row marked `broader` or `overlap` when the model suggests a component class that the ground truth schema has gained for the rest of its meaning.

A checked row with no match value (checked before the column existed, 2026-11-01) is read and used. Step 070 warns, listing it, and counts what goes through it under "no match value", and the annotation tool and the status count it as a row to check (*no match value*, under row state).

## <ins>Translating by identity</ins>

When step 060 extracted with the ground truth schema itself, the current schema is the ground truth schema: the same entity classes and predicates, with the same definitions (spacing aside), none of them from the [schema additions](../../docs/terminology.md#3-schemas) (`component_classes.py`, `identity_problem`). Step 070 then does not read the table. T<sub>E</sub>(*c*) = *c* for every entity class, T<sub>P</sub>(*p*, *c*<sub>s</sub>, *c*<sub>o</sub>) = (*p*, no) for every predicate, and every row counts as `same`. The report then has no section on the translation table ([070's guide](../070_evaluate.md), *Comparing with the ground truth schema*).

## <ins>Within reach</ins>

The [recall upper bound](recall_upper_bound.md) is defined, with its examples, on its own page. In this page's notation, the sets it uses are the following.

- *Reach*<sub>E</sub> = {T<sub>E</sub>(*c*) : *c* ∈ *E*<sub>c</sub>} ∖ {⊥}: the entity classes of the ground truth schema that some entity class of the current schema translates to.
- *Reach*<sub>P</sub> = {*q* ≠ ⊥ : *q* is the target of the unconditional row of some *p* ∈ *P*<sub>c</sub>}.
- A conditional row with target *q* ≠ ⊥ and condition (*a*, *b*) reaches the ground truth triples with predicate *q* whose [subject class](../../docs/terminology.md#2-triples) is T<sub>E</sub>(*a*) (any, if *a* is any) and whose [object class](../../docs/terminology.md#2-triples) is T<sub>E</sub>(*b*) (any, if *b* is any), with the two exchanged when the row has σ = yes. If T<sub>E</sub>(*a*) = ⊥ or T<sub>E</sub>(*b*) = ⊥, the row reaches nothing.

A ground truth triple is within reach when its predicate is in *Reach*<sub>P</sub>, or some conditional row reaches it. It is [within strict reach](recall_upper_bound.md) when, in addition, its subject class and its object class are both in *Reach*<sub>E</sub> (code: `pairing.py`, `_within_reach` and `_within_strict_reach`).

*Suppose:* the only row whose target is FROM_MISSION (ground truth schema) is the conditional row of SOURCED_FROM (current schema) with the object condition Mission, and Mission (current schema) → Mission (ground truth schema). *Then:* a ground truth triple with FROM_MISSION is within reach when its object class is Mission, and is not within reach otherwise.

## <ins>Per-entry coverage</ins>

For a set *S* of predicates of the ground truth schema, and a set *S*′ of its entity classes:

- predicate coverage = |*S* ∩ *Reached*<sub>P</sub>| ÷ |*S*|, where *Reached*<sub>P</sub> is *Reach*<sub>P</sub> together with the target of every conditional row that reaches anything (above);
- entity-class coverage = |*S*′ ∩ *Reach*<sub>E</sub>| ÷ |*S*′|;
- the *same-or-narrower* version of each counts only the entries that at least one `same` or `narrower` row translates to.

Each is a number from 0 to 1, undefined for an empty set. Two choices of *S* and *S*′ are used: the whole ground truth schema (without its held-out-only entries), and the entries that the evaluated ground truth triples use, a predicate as their predicate and an entity class as their subject class or object class.

Predicate coverage is the proportion of the predicates of *S* that some translated extracted triple can have at all, each predicate counted once, however many ground truth triples use it. The entries it does not count are exactly those that the report lists as the "ground truth schema's component classes nothing translates to" (section *The translation table*). The recall upper bound counts ground truth triples instead, so it gives more weight to the predicates that the ground truth uses often. When predicate coverage is much lower than the recall upper bound, the predicates not reached are mostly ones that few ground truth triples use. An entry reached only through a conditional row counts as reached, although only the ground truth triples whose entity classes fit that row's condition are within reach.

Measured on the reported runs (`docs/reported_numbers.json`): the annotations of commit 5b958ce, the induced schema of 060 run `060_extract_2026-11-05_1816-2` (`schema_used.json`), and the 416 ground truth triples of the 20 finished [tuning records](../../docs/terminology.md#7-evaluating-extraction-step-070). The counts come from the translation that step 070 builds (`translate_component_classes`, with no [model call](../../docs/terminology.md#8-the-pipeline)):

| | Reached | Through a `same` or `narrower` row |
|---|---|---|
| predicates of the ground truth schema (85) | 44 (51.8%) | |
| predicates that the ground truth triples use (84) | 43 (51.2%) | 39 (46.4%) |
| entity classes of the ground truth schema (45) | 31 (68.9%) | |
| entity classes that the ground truth triples use (44) | 30 (68.2%) | 19 (43.2%) |

Of the 41 predicates that the ground truth triples use and no row reaches, 32 have one or two ground truth triples each, and the 41 together have 104 of the 416 ground truth triples. The other 3 of the 107 ground truth triples not within reach have a predicate reached only through conditional rows, PRODUCED_USING_ALGORITHM (ground truth schema), with a subject class, Variable, that those rows' condition does not fit. So the induced schema reaches about half of the predicates, counted once each, but 74.3% of the ground truth triples, because the predicates it does not reach are mostly rare ones.

Per-entry coverage is computed by a script from step 070's translation and is not yet in step 070's report (`docs/improvements.md`, *070_evaluate*). It depends on the table in the same ways as the recall upper bound ([Recall upper bound](recall_upper_bound.md), *Assumes and can't see*), and it says only that an entry can be the output of the translation, not that extraction states facts with it.

## Sources

- The four kinds of match follow the mapping properties of the W3C SKOS Reference (section 10, [mapping properties](https://www.w3.org/TR/skos-reference/#mapping)) and the correspondence symbols of the Alignment format ([format](https://moex.gitlabpages.inria.fr/alignapi/format.html)). Recording the kind of match and reporting by it follows TRACE-KG's judgements "Equivalent, Narrower, Broader, or Unrelated": Abolhasani, Ba, He & Pan, "Traceable Context-Enriched Knowledge Graph Generation with Induced Schemas", arXiv:2604.03496v3, section 5.2 ([paper](https://arxiv.org/abs/2604.03496)).
- No credit for an inexact match, as in EDC: Zhang & Soh, "Extract, Define, Canonicalize: An LLM-based Framework for Knowledge Graph Construction", arXiv:2404.03868 ([paper](https://arxiv.org/abs/2404.03868)); and Text2KGBench: Mihindukulasooriya, Tiwari, Enguix & Lata (2023), "Text2KGBench: A Benchmark for Ontology-Driven Knowledge Graph Generation from Text", arXiv:2308.02357 ([paper](https://arxiv.org/abs/2308.02357)).
- Conditional rows: a correspondence restricted to an [entity class](../../docs/terminology.md#3-schemas) of its subject or object is EDOAL's, the Alignment API's "Expressive and Declarative Ontology Alignment Language" (Scharffe, Euzenat & Zimmermann; [language description](https://moex.gitlabpages.inria.fr/alignapi/edoal.html)), whose restrictions `RelationDomainRestriction` and `RelationCoDomainRestriction` limit a correspondence [a row] to one entity class of its subject or of its object. Such correspondences are what complex ontology matching produces: Thiéblin, Haemmerlé, Hernandez & Trojahn, "Survey on complex ontology matching", *Semantic Web* 11(4), 2020 ([paper](https://doi.org/10.3233/SW-190366)).
- Per-entry coverage is adapted from TRACE-KG's measure of schema coverage (Abolhasani, Ba, He & Pan, arXiv:2604.03496v3, as above), which counts the predicates of a reference schema that an [induced schema](../../docs/terminology.md#5-learning-the-schema-step-040) covers. Here an entry counts as covered when a checked row translates some [component class](../../docs/terminology.md#3-schemas) of the [current schema](../../docs/terminology.md#6-extracting-with-a-schema-step-060) to it.
