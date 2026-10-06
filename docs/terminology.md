# Terminology

The words this project uses, and exactly what each one means. It is expected to change as the project progresses, and is necessary for the best possible understanding of this documentation. Check back often for edits :)

**Contents**

1. [Records and their text](#1-records-and-their-text)
2. [Triples](#2-triples)
3. [Schemas](#3-schemas)
4. [Ground truth and samples](#4-ground-truth-and-samples)
5. [Learning the schema (step 040)](#5-learning-the-schema-step-040)
6. [Extracting with a schema (step 060)](#6-extracting-with-a-schema-step-060)
7. [Evaluating extraction (step 070)](#7-evaluating-extraction-step-070)
8. [The pipeline](#8-the-pipeline)

---

## 1. Records and their text

| Term | Meaning |
|---|---|
| **record** | The metadata of one catalog entry. The catalog we work with is typically data.nasa.gov. |
| **metadata field** | A record's key, e.g. `title`, `notes`, `maintainer`. Also called: *field*, *metadata field name*, *field name*. |
| **populated content of a metadata field** | The value associated with a record's key. |
| **maintainer** | A record's `maintainer` field, with its spellings joined by step 020: "KRISTAN MORGAN" and "Kristan Morgan" are one maintainer. `undefined` when the record has none. |
| **text** (of a record) | What a model is given to read for one record: the record's chosen fields, joined in order, each preceded by its field name so the model can tell which part came from which field (example below). The chosen fields are `title` and `notes`; step 020's setting `extra_text_fields` can add more. |
| **text piece** | Part of a long text, short enough for one model call. Almost every text is a single piece. |
| **source text** | The passage of a text that states a triple instance, copied word for word from the text. |

A record's text:

```
title: MODIS/Aqua Surface Reflectance

notes: The MODIS instrument aboard Aqua …
```

---

## 2. Triples

| Term | Meaning |
|---|---|
| **fact** | Something a record's text states, e.g. that MODIS is aboard Aqua. A triple instance writes one fact down; different triple instances can write the same fact (e.g. "MODIS" and "Moderate Resolution Imaging Spectroradiometer" as subject). |
| **triple instance** | One fact, written in three pieces: a subject, a predicate and an object, e.g. "MODIS" – "is aboard" – "Aqua". Also called: *triple*. |
| **component** | One of the three pieces of a triple: **subject**, **predicate** or **object**. |
| **slot** | Where a component sits in a triple. |
| **component instance** | A value filling a slot. "Rosetta" might fill a subject or object slot; "is mounted on" might fill a predicate slot. |
| **subject instance** | The component instance in the subject slot: the text's words for one particular thing, e.g. "MODIS". Its component class, the **subject class**, is an entity class (`Instrument`). |
| **object instance** | The component instance in the object slot, e.g. "Aqua". Its component class, the **object class**, is an entity class (`Spacecraft`). |
| **predicate instance** | The component instance in the predicate slot: the text's words for a relation, e.g. "is mounted on". Its component class is a predicate (`ABOARD`, section 3). Steps 050–070 write the predicate itself in this slot, not the words: the words name no particular thing, and the graph needs only the kind of relation (an edge's type). The words stay in the triple's source text. Only step 040, which learns the schema, collects the words before naming their predicate. |
| **verified triple instance** | One whose source text is really in its record's text, checked in code. An **unverified** one (no source text, or a source text that isn't in the text) can't be trusted: step 040 leaves it out of what it counts; step 050 keeps it, marked as an error, for the person to fix; step 060 removes it (reason `source_text`). |
| **DESCRIBES row** | The one triple instance every record gets that no text states, written by code: `<record id>` (`CatalogEntry`) DESCRIBES `<the record's title>` (`<entity class>`). It keeps the catalog entry apart from the thing the entry is about. The model's only part in it is naming that entity class; `X` means none was named yet. |
| **error** / **flag** | What a check of a triple instance can raise. An **error** is something code can prove wrong (e.g. its source text isn't in the text); a **flag** is often a sign of a mistake, often fine (e.g. a reworded subject or object instance, or a component class the schema doesn't have). Listed in `050_annotate/050_annotate.md`. |

---

## 3. Schemas

| Term | Meaning |
|---|---|
| **schema** | An object that describes the entity classes, the predicates, and the allowed relationships between predicates and entity classes. These allowed relationships are the **patterns**. |
| **schema entry** | An entity class, a predicate, or a pattern. |
| **entity class** | A collective term for subject classes and object classes. In a schema, the role of an entity class is either a subject or an object, strictly a subject, or strictly an object. E.g. `Instrument`, `Spacecraft`. |
| **predicate** | A word with two senses, told apart by context: **(1)** the component in the middle slot of a triple; **(2)** a schema entry: a kind of relation, e.g. `ABOARD`, the component class of predicate instances. |
| **kind** | Of a component class: whether it is an entity class or a predicate (e.g. the translation table's `kind` column). |
| **component class** | The class of a component in a particular schema. For a subject or an object, one of the schema's entity classes; for a predicate, one of the schema's predicates (examples below). |
| **pattern** | One allowed combination of an entity class, a predicate and an entity class, read from subject to object, e.g. `Instrument ABOARD Spacecraft`. |
| **schema additions** | Entity classes, predicates and patterns a person adds by hand to the schema step 060 extracts with, in `annotations/schema_additions.txt`, each with where the idea came from (`source:`). They have no support. |
| **hand-built schema** | The schema a person wrote while annotating the first records: `annotations/schema_derived_from_manual_annotation.txt`. It grows as annotation goes: each component class coined in the ground truth is added to it with a one-line definition (the annotation tool's buttons do it). Step 050 shows it to the model as the component classes to reuse; step 040 compares the schema it learns with it. |
| **domain** (of a predicate) | The entity classes its subject may belong to. |
| **range** (of a predicate) | The entity classes its object may belong to. |

**Component class, by example.** `Instrument` is the component class of the subject instances "MODIS" and "AIRS"; `ABOARD` is the component class of the predicate instances "is aboard" and "is mounted on".

**Patterns, domain and range.** A predicate's patterns together give its domain (the subject classes that appear in them) and its range (the object classes). `HAS_TIME_SPAN`, with the patterns `Dataset HAS_TIME_SPAN TimeSpan` and `MissionPhase HAS_TIME_SPAN TimeSpan`, has the domain {Dataset, MissionPhase} and the range {TimeSpan}. Patterns say more than domain and range together: they say which subject class goes with which object class. Patterns found by step 040 record where a predicate was seen in the texts, which is not necessarily everywhere it is allowed.

**In a graph database.** These terms belong to no particular kind of graph. In a labeled property graph (LPG) such as Neo4j:

| This project | In an LPG (e.g. Neo4j) |
|---|---|
| entity class | node label, e.g. `(:Instrument)` |
| predicate (schema entry) | relationship type, e.g. `[:ABOARD]` |
| pattern | `(:Instrument)-[:ABOARD]->(:Spacecraft)`, as Neo4j's own schema view shows |
| domain, range | the node labels allowed at the start and at the end of a relationship type (a convention; Neo4j doesn't enforce it) |

The words *domain* and *range* were standardized in RDF Schema, another kind of graph, and are used the same way for any graph.

---

## 4. Ground truth and samples

| Term | Meaning |
|---|---|
| **ground truth** | Triple instances a person has checked and corrected for a record. Kept in `annotations/ground_truth/`, one file per batch of records corrected together (`batch_000.csv` holds those annotated before the pipeline; `batch_001.csv` is corrected from step 050's draft batch 1, and so on); the ground truth is all the files together. |
| **ground truth triple** | A triple instance of the ground truth: a row of a ground truth file other than its record's DESCRIBES row (and other than the empty row of a record that states no facts). What step 070 pairs with the extracted triples. A **row** is any line of such a file. |
| **ground truth candidates pool** (the **pool** for short) | 1,000 records drawn once (2026-09-21) as candidates for ground truth, in a shuffled order. A person annotates them in that order, and only a subset ever gets annotated, since 1,000 is more than there is time to check. Each record's place in that order is its **pool position** (0, 1, 2, …). |
| **sampling group** | One of the groups the pool was drawn by: a large maintainer on its own, or "(small maintainers)" for the 404 maintainers too small to earn two of the 1,000 places. Each group got places in proportion to its size; `annotations/ground_truth_candidates.csv` names each record's group. Margins of error and per-group numbers in step 070 follow these groups. |
| **draft batch** | The triple instances a model drafted, in one run of step 050, for a few records (10 by default), waiting for a person to correct them: `drafted_triples_batch<N>.csv` in 050's output folder. Corrected with the annotation tool (`py helpers/annotate.py`), it becomes the ground truth file `batch_<NNN>.csv` with the same number. |
| **annotation tool** | `py helpers/annotate.py`: a page in your browser, on your computer only, to read and correct triple instances, check the translation table, review partial pairs and edit the schema additions (see `annotations/README.md`). Not a step. |
| **fair sample** | Records taken from the start of the ground truth candidates pool, in its order, with none skipped. Since the pool is shuffled, those are a fair sample of the whole catalog, so results measured on them hold for the catalog. Step 050 says when the ground truth stops being one (e.g. after drafting hand-picked records). Step 070 evaluates only the fair sample of finished, extracted records: the longest run of the pool's first records that a person has finished and 060 extracted. |
| **induction candidates** | Every record that isn't in the ground truth candidates pool and has text, each maintainer's in a fixed random order. Step 040 learns the schema from the first few of the largest maintainers. |

---

## 5. Learning the schema (step 040)

| Term | Meaning |
|---|---|
| **label** | The general word a model gives a component instance in step 040. For a subject or object instance, the kind of thing it is ("MODIS" → `Instrument`), which becomes an entity class. For a predicate instance, the relation it expresses ("is aboard" → `ABOARD`), which becomes a predicate. Not the same as a *node label* in a graph database (section 3), though an entity class does become one. |
| **support** | How many different texts a schema entry was found in. A text stating it twice counts once. |
| **deferred** | A schema entry that was found but isn't in the schema, with the reason: support below `min_support`, judged too vague, or a pattern through a schema entry that isn't in the schema. |
| **model call** (also **paid call**) | One request to the AI model, paid for. Every answer is kept in a cache, so a rerun pays only for what isn't there yet. Before a run's first one, the step stops and asks (setting `confirm_paid_calls`). |

---

## 6. Extracting with a schema (step 060)

| Term | Meaning |
|---|---|
| **current schema** | The schema step 060 extracted with in its last run: its schema input (040's by default, or any given with `--schema`) plus the schema additions, merged, written to `schema_used.json`. Step 070 reads it (and 080 will), so they use exactly what 060 used. A **past schema** is one an earlier run of 060 used. |
| **extracted triple** | A triple instance step 060 kept after checking it: one in `extracted_triples.csv`, the graph's facts and what 070 evaluates. The ones its checks **removed** go to `extracted_triples_removed.csv` with the reason: `source_text` (its source text is missing or isn't in the record's text), `component_class_not_in_schema`, `duplicate` or `malformed`. Removed is not deleted: the file keeps them for a person to look at. |
| **component class outside the schema** | An entity class or predicate the model used though the schema doesn't have it (e.g. `Satellite` when the schema says `Spacecraft`). Such a triple instance is removed; the report lists these component classes, most used first, as candidates for the schema additions. A component class that differs only in case, spaces or punctuation (`Space craft`) is not outside the schema: it's accepted and written in the schema's spelling. |

---

## 7. Evaluating extraction (step 070)

Step 070 compares the triple instances (triples, for short) step 060 extracted with the ground truth, which works as the answer key. An example: a record's ground truth has 5 triples; 060 extracts 4, of which 3 form **pairs** with ground truth triples and 1 is extracted only (the text never says it); 2 ground truth triples are left without a partner (missed).

Each metric below is also read out in sentences, with each run's own counts, in the report; how: `070_evaluate/070_evaluate.md`, section *Reading the metrics*.

| Term | Meaning |
|---|---|
| **pair** | An extracted triple and a ground truth triple of the same record that step 070 links as stating the same fact, after the extracted triple's component classes are translated into the ground truth vocabulary. Their predicates must be the same; their subjects and objects agree at one of two **pair levels**: **exact pair**, the same once evened out (case, spacing, quote marks, dashes, punctuation at either end and a leading "the/a/an" ignored); **partial pair**, one contained in the other as whole words, either way round ("MODIS" in "Moderate Resolution Imaging Spectroradiometer (MODIS)"). A pair is **strict** when the subject classes and the object classes agree too. |
| **pairing** | How step 070 forms the pairs, record by record. Every triple, in either list, ends with zero or one partner, always from the other list; the two lists can have any lengths. Exact pairs are formed first, then partial ones among the triples left, each round forming as many pairs as possible (in maths, a *maximum matching*). An extracted triple left without a partner is **extracted only** (it counts against precision); a ground truth triple left without one is **ground truth only**, i.e. missed (against recall). |
| **translation table** | The table [`annotations/component_class_mapping.csv`](../annotations/component_class_mapping.csv), checked by a person: which component class of the ground truth vocabulary each component class of the current schema means, or `(none)`. What one row says is a **translation**. Its columns abbreviate (crt: **current**, gtt: **ground truth triples**): `component_class_from_past_or_crt_schema` is a component class of the current schema or a past schema (one table serves every schema); `component_class_in_gtt` is the component class in the ground truth triples (the ground truth vocabulary); `definition_from_past_or_crt_schema` keeps that schema's definition of the component class from when the row was written or last checked, so a row whose component class the current schema defines differently is stale (a **row state**) and must be checked again. `swap_subject_and_object` when it says the same relation the other way round ("A CARRIES B" is "B ABOARD A"). |
| **row state** | A note the annotation tool shows (⚑) on a row of the translation table, and that step 070's report warns about: **stale** (checked when the current schema defined its component class differently; it counts as unchecked), **now exists** (says `(none)`, though the ground truth vocabulary now has a component class spelled the same), **suggested** (says `(none)`, and the model suggests a component class the ground truth vocabulary gained since), **shared** (another component class of the current schema translates to the same one, so evaluation can't tell them apart) or **repeated** (the component class has more than one row). Not a **flag**, which is raised by a check of a triple instance. |
| **ground truth vocabulary** | The entity classes and predicates of the ground truth: every one in the hand-built schema, plus every distinct one the ground truth triples use that the hand-built schema lacks (a **coined** component class, compared ignoring case and punctuation). A coined component class has no definition until it is added to the hand-built schema (the annotation tool's buttons do it); once every coined component class is added, the ground truth vocabulary is exactly the hand-built schema's entity classes and predicates. Step 050 shows it to the model as the component classes to reuse, the annotation tool suggests it, and step 070 translates the component classes of the current schema into it before comparing. |
| **precision** | When 060 says something, how often it is right: the pairs, divided by all the triples 060 extracted. In the example, 3 ÷ 4 = 75%. Low precision means many extracted triples have no pair: the subject, the predicate or the object is wrong, or the text never states the fact at all. In the knowledge graph that graph building (step 080) makes from the extracted triples, each one would be a statement that shouldn't be there, and it can bring in nodes that shouldn't exist (e.g. an invented subject). |
| **recall** | Of everything true in the text, how much 060 caught: the pairs, divided by all the ground truth triples. In the example, 3 ÷ 5 = 60%. Low recall means extraction misses many facts: the knowledge graph made from its triples would lack them. |
| **F1** | Precision and recall in one number: 2 × precision × recall ÷ (precision + recall). In the example, 2 × 3 ÷ (4 + 5) = 67%. High only when both are; the usual headline number for comparing runs or models, and with published results. **Strict F1** counts only strict pairs. |
| **entity-class accuracy** | Of the pairs, how many are strict: subject class and object class right too. |
| **within reach** | A ground truth triple whose predicate is something the current schema translates to: all a pair needs, since a pair doesn't need the entity classes to agree. **Within strict reach**: its two entity classes are too, all a strict pair needs. |
| **recall upper bound** | The ground truth triples within reach, divided by all of them: the best recall any extractor could get with that schema. The **strict recall upper bound**, with strict reach, is the best strict recall. **Recall within reach** is the pairs whose ground truth triple is within reach, divided by the ground truth triples within reach (strict: strict pairs ÷ triples within strict reach). A low upper bound points at the schema, a low recall within reach at the extraction. |
| **margin of error** | How shaky a number is: "precision 65%, likely between 45% and 88%". With few records a number could easily have come out quite different, so its margin is wide; with many, narrow. Without it, a real improvement can't be told from luck. |
| **bootstrap** | How 070 computes a margin of error: it recomputes the number about 1,000 times, each time from records drawn at random from the evaluated ones, with repeats allowed, and takes the middle 95% of the results. It draws **whole records**, since the triples of one record succeed or fail together, and draws **within the pool's sampling groups**, the way the pool was drawn. It is only valid when the evaluated records are a random sample (the first records of the pool) and there are enough of them; step 070 checks both. A margin covers only which records happened to be picked: not mistakes in the ground truth, and not the model answering differently on another run. |
| **tuning part** | The ground truth records whose metrics may be looked at while improving the pipeline (a prompt, the schema, a setting): pool positions 0–5, and from position 6 on, two of every three records. Step 030 marks each ground truth candidate's part in `splits.json`. |
| **held-out part** | The ground truth records kept aside: from pool position 6 on, every third record (8, 11, 14, …). Their metrics are not looked at while improving the pipeline, only at the end; that is the number reported as how well the pipeline works. Otherwise the pipeline gets tuned to the records it is evaluated on, and its metrics flatter it. |

The two are reported together because each alone can be fooled: an extractor that states just one triple it is sure of has perfect precision and almost no recall; one that states everything it can think of has perfect recall and poor precision. They are counted over all the evaluated records of a part (tuning or held-out) together, not one record at a time.

---

## 8. The pipeline

| Term | Meaning |
|---|---|
| **step** | One of the 8 numbered parts of the pipeline, `010_harvest` to `080_build_graph`. Each step reads what earlier steps wrote and writes its own output. |
| **stage** | One part of a step's work, in order; e.g. step 040 has 7 stages. Never called a step. |
| **move** | One line of a step's `main()` in its control panel, e.g. `records = clean.clean_text(records)`: a stage, or a step's bookkeeping (`paid_calls`, `results`). The **main moves** are those lines; each is timed in the report. |
| **model** (**LLM**) | The AI model the steps ask, a large language model reached through NASA's Ask Sage service (the default is `MODEL` in `common/common_helpers/llm.py`; each step that asks it has a `model` setting, and `py helpers/models.py` lists the models Ask Sage shows your account). In code comments, `LLM:` marks a move that asks it and `code:` one that doesn't. |
| **control panel** | A step's short script, `run.py` in the step's folder, e.g. `040_induce_schema/run.py`: its inputs, its settings and its main moves, one line each. The rest of the folder is the code behind it. You run it from the repository folder: `py 040_induce_schema/run.py`. |
| **parameter** | Any value that decides how code behaves, e.g. how many texts to learn from, or how many component instances go in one model call. |
| **setting** | A parameter of a step that its control panel shows for a person to change, e.g. `texts_per_maintainer`, given on the command line as `--texts_per_maintainer 30`. A parameter nobody tunes (e.g. 80 component instances per labeling call) isn't a setting: it's fixed in the step's code, as a named constant (`LABEL_BATCH`). |
| **run** | One execution of one step. Its **run id** (e.g. `040_induce_schema_2026-09-28_1811`) names its report and its log. |
| **report** | The page a run writes for people (`outputs/reports/<run id>.md`): what it read and wrote, its numbers, its warnings. |
| **log** | The line-by-line record of a run (`outputs/logs/<run id>.log`). |
| **manifest** | The file a step's output folder gets when a run finishes (`_manifest.json`): which files went in and came out, each with its hash. |
| **origin** | Where one output item came from, written inside the output file (`_origin`): the input item(s) it was made from, e.g. `010_harvest/batch_00000.json#<record id>`. `helpers/audit.py` follows origins back to the API request. |
