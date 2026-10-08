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
| **harvest** | One download of the whole data.nasa.gov catalog by step 010: a snapshot of one moment. Its **harvest date** is the day the pages were fetched (a range of days if a harvest was resumed). |
| **batch file** | One page of a harvest as step 010 saved it (`outputs/intermediate_results/010_harvest/batch_<start>.json`): up to 1,000 records, exactly as the API returned them. Not to be confused with a draft batch, or with a file of the ground truth (`annotations/ground_truth/batch_<NNN>.csv`). |
| **request block** | The top of a batch file: the API request that returned its records, when, and with what status. Every record's origin starts there. |
| **record** | The metadata of one catalog entry. The catalog we work with is typically data.nasa.gov. |
| **metadata field** | A record's key, e.g. `title`, `notes`, `maintainer`. Also called: *field*, *metadata field name*, *field name*. |
| **populated content of a metadata field** | The value associated with a record's key. |
| **maintainer** | A record's `maintainer` field, with its spellings joined by step 020: "KRISTAN MORGAN" and "Kristan Morgan" are one maintainer. `undefined` when the record has none. |
| **text** (of a record) | What a model is given to read for one record: the record's chosen fields, joined in order, each preceded by its field name so the model can tell which part came from which field (example below). The chosen fields are `title` and `notes`; step 020's setting `extra_text_fields` can add more. |
| **text piece** | Part of a long text, short enough for one model call. Almost every text is a single piece. |
| **source text** | The passage of a text that states the fact of a triple instance or a classed triple, copied word for word from the text. |

A record's text:

```
title: MODIS/Aqua Surface Reflectance

notes: The MODIS instrument aboard Aqua …
```

---

## 2. Triples

| Term | Meaning |
|---|---|
| **fact** | Something a record's text states, e.g. that MODIS is aboard Aqua. A triple instance or a classed triple writes one fact down; different ones can write the same fact (e.g. "MODIS" and "Moderate Resolution Imaging Spectroradiometer" as subject). |
| **triple instance** | One fact, written in three pieces: a subject, a predicate, and an object, e.g. "MODIS" – "is aboard" – "Aqua" (compare **classed triple**). |
| **classed triple** | A fact written as a subject instance with its subject class, a predicate of a schema, and an object instance with its object class, e.g. "MODIS" (`Instrument`) ABOARD "Aqua" (`Spacecraft`). What annotation (step 050) and extraction (step 060) write: every ground truth triple and every extracted triple is a classed triple. |
| **component** | One of the three pieces of a triple instance or a classed triple: **subject**, **predicate**, or **object**. |
| **slot** | Where a component sits in a triple instance or a classed triple. |
| **component instance** | A value filling a slot. "Rosetta" might fill a subject or object slot; "is mounted on" might fill a predicate slot. |
| **subject instance** | The component instance in the subject slot: the text's words for one particular thing, e.g. "MODIS". Its component class, the **subject class**, is an entity class (`Instrument`). |
| **object instance** | The component instance in the object slot, e.g. "Aqua". Its component class, the **object class**, is an entity class (`Spacecraft`). |
| **predicate instance** | The component instance in the predicate slot: words for a relation, e.g. "is mounted on" (in step 040, a short verb phrase in the model's words). Its component class is a predicate (`ABOARD`, section 3). Steps 050–070 write the predicate itself in this slot, not the words: the words name no particular thing, and the graph needs only the kind of relation (an edge's type). The words stay in the classed triple's source text. Only step 040, which learns the schema, collects predicate instances before naming their predicate. |
| **verified triple instance** | One whose source text is really in its record's text, checked in code. An **unverified** one (no source text, or a source text that isn't in the text) can't be trusted: step 040 leaves it out of what it counts; step 050 keeps it, marked as an error, for the person to fix; step 060 removes it (reason `source_text`). |
| **DESCRIBES row** | The one classed triple every record gets that no text states, written by code: `<record id>` (`CatalogEntry`) DESCRIBES `<the record's title>` (`<entity class>`). It keeps the catalog entry apart from the thing the entry is about. The model's only part in it is naming that entity class, the **describes class** (`describes_class` in its reply), e.g. `Dataset`; `X` means none was named yet. |
| **error** / **flag** | What a check of a triple instance or a classed triple can raise. An **error** is something code can prove wrong (e.g. its source text isn't in the text); a **flag** is often a sign of a mistake, often fine (e.g. a reworded subject or object instance, or a component class the schema doesn't have). Listed in `050_annotate/050_annotate.md`. |
| **evened out** | How two subject instances, object instances, or source texts are compared: case, spacing, quote marks, dashes, punctuation at either end, and a leading "a", "an", or "the" are ignored, so "The MODIS" = "modis" (`common/common_helpers/text_match.py`). |

---

## 3. Schemas

| Term | Meaning |
|---|---|
| **schema** | An object that describes the entity classes, the predicates, and the allowed combinations of entity classes and predicates. These allowed combinations are the **patterns**. |
| **schema entry** | An entity class, a predicate, or a pattern. |
| **entity class** | A kind of thing a subject instance or object instance can be, e.g. `Instrument`, `Spacecraft`: a schema entry. The entity class of a classed triple's subject instance is its subject class; of its object instance, its object class. Through its patterns, an entity class can be a subject class, an object class, or both. |
| **predicate** | A word with two senses, told apart by context: **(1)** the component in the middle slot of a triple instance or a classed triple; **(2)** a schema entry: a kind of relation, e.g. `ABOARD`, the component class of predicate instances. |
| **kind** | Of a component class: whether it is an entity class or a predicate (e.g. the translation table's `kind` column). |
| **component class** | What a component instance is classed as in a particular schema. For a subject instance or an object instance, one of the schema's entity classes; for a predicate instance, one of the schema's predicates (examples below). |
| **loose match** | How two component classes are compared: only letters and digits count, so `Space_craft` = `spacecraft` (`common/common_helpers/triples_io.component_class_key`). Step 040's **spelling fold** merges two labels that are a loose match. |
| **pattern** | One allowed combination of an entity class, a predicate, and an entity class, read from subject to object, e.g. `Instrument ABOARD Spacecraft`. |
| **schema additions** | Entity classes, predicates, and patterns a person adds by hand to the schema step 060 extracts with, in `annotations/schema_additions.txt`, each with where the idea came from (`source:`). They have no support. |
| **hand-built schema** | The schema a person wrote while annotating the first records: `annotations/schema_derived_from_manual_annotation.txt`. It grows as annotation goes: each component class coined in the ground truth is added to it with a one-line definition, and each new pattern (the annotation tool's buttons do it). It is part of the ground truth vocabulary, which step 050 shows the model; step 040 compares the schema it learns with it. |
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
| **ground truth** | Classed triples a person has checked and corrected for a record. Kept in `annotations/ground_truth/`, one file per batch of records corrected together (`batch_000.csv` holds those annotated before the pipeline; `batch_001.csv` is corrected from step 050's draft batch 1, and so on); the ground truth is all the files together. |
| **ground truth triple** | A classed triple of the ground truth: a row of a ground truth file other than its record's DESCRIBES row (and other than the empty row of a record that states no facts). What step 070 pairs with the extracted triples. A **row** is any line of such a file. A record's ground truth triples form its **set of ground truth triples**. Two of them with the same subject instance and object instance (evened out) and the same predicate must differ in subject class, object class, or both (by loose match): otherwise they are **the same classed triple twice**, and step 070 refuses to run until one is deleted; when they do differ, step 070 warns before evaluating. |
| **finished record** | A ground truth record whose rows all have `all_facts_extracted` = 1 (*All facts extracted* ticked in the annotation tool). By default, step 060 extracts only finished records, and step 070 evaluates only them. |
| **ground truth candidates pool** (the **pool** for short) | 1,000 records drawn once (2026-09-21) as candidates for ground truth, in a shuffled order. A person annotates them in that order, and only a subset ever gets annotated, since 1,000 is more than there is time to check. Each record's place in that order is its **pool position** (0, 1, 2, …). |
| **stratum** (plural **strata**) | One of the groups the pool was drawn by (stratified sampling): a large maintainer on its own, or "(small maintainers)" for the 404 maintainers too small to earn two of the 1,000 places. Each stratum got places in proportion to its size; `annotations/ground_truth_candidates.csv` names each record's stratum. Margins of error and per-stratum numbers in step 070 follow the strata. |
| **draft batch** | The classed triples a model drafted, in one run of step 050, for a few records (10 by default), waiting for a person to correct them: `drafted_triples_batch<N>.csv` in 050's output folder. Corrected with the annotation tool (`py helpers/annotate.py`), it becomes the ground truth file `batch_<NNN>.csv` with the same number. |
| **annotation tool** | `py helpers/annotate.py`: a page in your browser, on your computer only, to read and correct classed triples, check the translation table, review partial pairs, edit the schema additions, and add component classes and patterns to the hand-built schema (see `annotations/README.md`). Not a step. |
| **fair sample** | Records taken from the start of the ground truth candidates pool, in its order, with none skipped. Since the pool is shuffled, those are a fair sample of the whole catalog, so results measured on them hold for the catalog. Step 050 says when the ground truth stops being one (e.g. after drafting hand-picked records). Step 070 evaluates only the fair sample of finished, extracted records: the longest run of the pool's first records that a person has finished and 060 extracted. |
| **induction candidates** | Every record that isn't in the ground truth candidates pool and has text, each maintainer's in a fixed random order. Step 040 learns the schema from the first few of the largest maintainers. |

---

## 5. Learning the schema (step 040)

| Term | Meaning |
|---|---|
| **induced schema** | The schema step 040 learns from the texts of the induction candidates, written to `outputs/intermediate_results/040_induce_schema/the_schema.json`. Step 060 extracts with it by default, so by default it becomes the current schema. |
| **label** | The general word a model gives a component instance in step 040. For a subject or object instance, the kind of thing it is ("MODIS" → `Instrument`), which becomes an entity class. For a predicate instance, the relation it expresses ("is aboard" → `ABOARD`), which becomes a predicate. Not the same as a *node label* in a graph database (section 3), though an entity class does become one. |
| **running vocabulary** | In step 040's labeling, the labels chosen so far. Each batch of component instances is shown it, so the model reuses a label when one fits instead of coining a near-duplicate. |
| **support** | How many different texts a schema entry was found in. A text stating it twice counts once. |
| **evidence** (of a schema entry) | What step 040 keeps to show why a schema entry is in the schema: its support, the maintainers and texts it was found in, and, for an entity class, examples (in `the_schema.json`). `induction_evidence.json` keeps everything the run saw and decided, from each text's triple instances to every label and merge. |
| **deferred** | A schema entry that was found but isn't in the schema, with the reason: support below `min_support`, judged too vague, or a pattern through a schema entry that isn't in the schema. |

---

## 6. Extracting with a schema (step 060)

| Term | Meaning |
|---|---|
| **current schema** | The schema step 060 extracted with in its last run: its schema input (040's by default, or any given with `--schema`) plus the schema additions, merged, written to `schema_used.json`. Step 070 reads it (and 080 will), so they use exactly what 060 used. A **past schema** is one an earlier run of 060 used. |
| **extracted triple** | A classed triple step 060 kept after checking it: one in `extracted_triples.csv`, the graph's facts and what 070 evaluates. The ones its checks **removed** go to `extracted_triples_removed.csv` with the reason: `source_text` (its source text is missing or isn't in the record's text), `component_class_not_in_schema`, `duplicate`, or `malformed`. Removed is not deleted: the file keeps them for a person to look at. A record's extracted triples form its **set of extracted triples**. Two of them with the same subject instance and object instance (evened out) and the same predicate differ in subject class, object class, or both (by loose match): step 060 removes the same classed triple twice as `duplicate`. |
| **component class outside the schema** | An entity class or predicate the model used though the schema doesn't have it (e.g. `Satellite` when the schema says `Spacecraft`). Such a classed triple is removed; the report lists these component classes, most used first, as possible schema additions. A component class that is a loose match for one of the schema's (`Space craft`) is not outside the schema: it's accepted and written in the schema's spelling. |

---

## 7. Evaluating extraction (step 070)

Step 070 compares the extracted triples with the ground truth, which works as the answer key. Every metric, with its formula, how to read it, and an example, is in [`070_evaluate/metrics.md`](../070_evaluate/metrics.md).

Each metric below is also read out in sentences, with each run's own counts, in the report; how: `070_evaluate/070_evaluate.md`, section *Reading the metrics*.

| Term | Meaning |
|---|---|
| **pair** | See [`070_evaluate/metrics/pairs.md`](../070_evaluate/metrics/pairs.md). It defines the **exact pair**, the **partial pair**, the **strict pair**, the **pair level** (exact or partial), **eligible** (meeting a pair level's requirements), and the **set of pairs** (one choice of which extracted triple pairs with which ground truth triple in a record). It also names the classed triples pairing leaves without a partner: an extracted triple without one is **extracted only**, and a ground truth triple without one is **ground truth only**. |
| **partial pair review** | A person's ruling on a partial pair of a tuning record, **same fact** or **not the same fact**, made in the annotation tool (*Partial pairs*) and kept in `annotations/partial_pair_reviews.csv`. An extracted triple and a ground truth triple marked "not the same fact" are never paired. The ruling itself is the **verdict**. |
| **translation table** | The table [`annotations/component_class_mapping.csv`](../annotations/component_class_mapping.csv), checked by a person: which component class of the ground truth vocabulary each component class of the current schema means, or `(none)`. What one row says is a **translation**. Its columns abbreviate (crt: **current**, gtt: **ground truth triples**): `component_class_from_past_or_crt_schema` is a component class of the current schema or a past schema (one table serves every schema); `component_class_in_gtt` is a component class of the ground truth vocabulary, the one the ground truth triples use; `definition_from_past_or_crt_schema` keeps that schema's definition of the component class from when the row was written or last checked, so a row whose component class the current schema defines differently is stale (a **row state**) and must be checked again. `swap_subject_and_object` is `yes` when the row's predicate says the same relation the other way round ("A CARRIES B" is "B ABOARD A"). |
| **translated extracted triple** | An extracted triple whose predicate, subject class and object class are translated into the ground truth vocabulary, through the translation table ([`annotations/component_class_mapping.csv`](../annotations/component_class_mapping.csv)); when the predicate's row says `swap_subject_and_object` is `yes`, its subject instance and object instance swap places too. What evaluation compares with the ground truth triples. |
| **row state** | A note the annotation tool shows (⚑) on a row of the translation table, and that step 070's report warns about: **stale** (checked when the current schema defined its component class differently; it counts as unchecked), **now exists** (says `(none)`, though the ground truth vocabulary now has a component class spelled the same: it was coined since, or added to the hand-built schema), **suggested** (says `(none)`, and the model suggests a component class the ground truth vocabulary gained since), **shared** (another component class of the current schema translates to the same one, so evaluation can't tell them apart) or **repeated** (the component class has more than one row). Not a **flag**, which is raised by a check of a triple instance or a classed triple. |
| **ground truth vocabulary** | The entity classes and predicates of the ground truth: every one in the hand-built schema, plus every distinct one the ground truth triples use that the hand-built schema lacks (a **coined** component class, compared by loose match). A coined component class has no definition until it is added to the hand-built schema (the annotation tool's buttons do it); once every coined component class is added, the ground truth vocabulary is exactly the hand-built schema's entity classes and predicates. Step 050 shows it to the model as the component classes to reuse, the annotation tool suggests it, and step 070 translates the component classes of the current schema into it before comparing. |
| **precision** | See [`070_evaluate/metrics/precision.md`](../070_evaluate/metrics/precision.md). |
| **recall** | See [`070_evaluate/metrics/recall.md`](../070_evaluate/metrics/recall.md). |
| **F1** | See [`070_evaluate/metrics/f1.md`](../070_evaluate/metrics/f1.md). |
| **entity-class accuracy** | See [`070_evaluate/metrics/entity_class_accuracy.md`](../070_evaluate/metrics/entity_class_accuracy.md). |
| **within reach** | See [`070_evaluate/metrics/recall_upper_bound.md`](../070_evaluate/metrics/recall_upper_bound.md): within reach and **within strict reach**. |
| **recall upper bound** | See [`070_evaluate/metrics/recall_upper_bound.md`](../070_evaluate/metrics/recall_upper_bound.md): the recall upper bound and the **strict recall upper bound**. |
| **recall within reach** | See [`070_evaluate/070_evaluate.md`, *How it works*, stage 4](../070_evaluate/070_evaluate.md#how-it-works), until `metrics.md` has it. |
| **margin of error** | See [`070_evaluate/metrics/approximately.md`, *Sampling error*](../070_evaluate/metrics/approximately.md#sampling-error). |
| **bootstrap** | How the margin of error is computed: see [`070_evaluate/metrics/approximately.md`, *Sampling error*](../070_evaluate/metrics/approximately.md#sampling-error). |
| **tuning part** | The ground truth records whose metrics may be looked at while improving the pipeline (a prompt, the schema, a setting): pool positions 0–5, and from position 6 on, two of every three records. Step 030 marks each ground truth candidate's part in `splits.json`. |
| **held-out part** | The ground truth records kept aside: from pool position 6 on, every third record (8, 11, 14, …). Their metrics are not looked at while improving the pipeline, only at the end; that is the number reported as how well the pipeline works. Otherwise the pipeline gets tuned to the records it is evaluated on, and its metrics flatter it. |
| **held-out look** | One run of step 070 with `--evaluate_held_out true`: one time the held-out records' numbers were shown. Each is logged in `annotations/held_out_looks.csv`. A change made after a look lets the held-out records influence the pipeline. |


---

## 8. The pipeline

| Term | Meaning |
|---|---|
| **step** | One of the 8 numbered parts of the pipeline, `010_harvest` to `080_build_graph`. Each step reads what earlier steps wrote and writes its own output. |
| **knowledge graph** | The graph step 080 will build from the records' metadata fields and the extracted triples: each extracted triple becomes one edge between two nodes. |
| **node** | One thing in the knowledge graph: a record (`Dataset`); a value of a metadata field that many records share (a maintainer, a keyword, or a format: README, *Project phases*, phase 1); or a subject instance or object instance of an extracted triple. A graph database calls its entity class its **node label**. |
| **edge** | A connection from one node to another, with a type: a predicate (`ABOARD`) for an extracted triple, or a phase 1 type such as `MAINTAINED_BY`. A graph database calls it a **relationship**, and its type a **relationship type**. |
| **property** | A value stored on a node rather than as a node of its own, e.g. a record's `title` or `license`: used when few records share the value, or nobody would go from node to node through it (README, *Phase 1*). |
| **stage** | One part of a step's work, in order; e.g. step 040 has 7 stages. Never called a step. |
| **move** | One line of a step's `main()` in its control panel, e.g. `records = clean.clean_text(records)`: a stage, or a step's bookkeeping (`paid_calls`, `results`). The **main moves** are those lines; each is timed in the report. |
| **model** (**LLM**) | The AI model the steps ask, a large language model reached through NASA's Ask Sage service (the default is `MODEL` in `common/common_helpers/llm.py`; each step that asks it has a `model` setting, and `py helpers/models.py` lists the models Ask Sage shows your account). In code comments, `LLM:` marks a move that asks it and `code:` one that doesn't. |
| **stand-in model** | A fake model used to test a step without the real one: code that returns made-up answers in the right format, without calling Ask Sage or paying. A step tested only with a stand-in hasn't been run on real model answers yet. |
| **stand-in catalog** | A fake data.nasa.gov used to test harvest without the real one: code that answers like data.nasa.gov's API, with made-up records, on your own computer. Only the tests use it (`tests/stand_ins.py`). |
| **model call** (also **paid call**) | One request to the AI model, paid for. Every answer is kept in a cache, so a rerun pays only for what isn't there yet. Before a run's first one, the step stops and asks (setting `confirm_paid_calls`). |
| **control panel** | A step's short script, `run.py` in the step's folder, e.g. `040_induce_schema/run.py`: its inputs, its settings, and its main moves, one line each. The rest of the folder is the code behind it. You run it from the repository folder: `py 040_induce_schema/run.py`. |
| **setting** | A value that decides how a step behaves and that its control panel shows for a person to change, e.g. `texts_per_maintainer`, given on the command line as `--texts_per_maintainer 30`. A value nobody tunes (e.g. 80 component instances per labeling call) isn't a setting: it's fixed in the step's code, as a named constant (`LABEL_BATCH`). |
| **run** | One execution of one step. Its **run id** (e.g. `040_induce_schema_2026-09-28_1811`) names its report and its log. |
| **report** | The page a run writes for people (`outputs/reports/<run id>.md`): what it read and wrote, its numbers, its warnings. |
| **log** | The line-by-line record of a run (`outputs/logs/<run id>.log`). |
| **manifest** | The file a step's output folder gets when a run finishes (`_manifest.json`): which files went in and came out, each with its hash. |
| **fingerprint** | A short code computed from exact content: a file, a prompt, a set of settings. The same content always gives the same fingerprint, and any change gives a different one. Used to tell whether an input or a cached model answer still matches (technically a SHA-256 hash). |
| **origin** | Where one output item came from, written inside the output file (`_origin`): the input item(s) it was made from, e.g. `010_harvest/batch_00000.json#<record id>`. `helpers/audit.py` follows origins back to the API request. |
