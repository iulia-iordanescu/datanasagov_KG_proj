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
| **batch file** | One page of a harvest as step 010 saved it (`outputs/intermediate_results/010_harvest/batch_<start>.json`): up to 1,000 records, exactly as the API returned them. Not to be confused with a drafted batch, or with a file of the ground truth (`annotations/ground_truth/batch_<NNN>.csv`). |
| **request block** | The top of a batch file: the API request that returned its records, when, and with what status. Every record's origin starts there. |
| **record** | The metadata of one catalog entry. The catalog we work with is typically data.nasa.gov. |
| **metadata field** | A record's key, e.g. `title`, `notes`, `maintainer`. Also called: *field*, *metadata field name*, *field name*. |
| **text field** | A metadata field whose value goes into a record's text: `title`, `notes`, and any named in step 020's setting `extra_text_fields`. |
| **populated content of a metadata field** | The value associated with a record's key. |
| **maintainer** | A record's `maintainer` field, with its spellings joined by step 020: "KRISTAN MORGAN" and "Kristan Morgan" are one maintainer. `undefined` when the record has none. |
| **text** (of a record) | What a model is given to read for one record: the record's text fields, joined in order, each preceded by its field name so the model can tell which part came from which field (example below). |
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
| **predicate instance** | The component instance in the predicate slot: words for a relation, e.g. "is mounted on" (in step 040, a short verb phrase in the model's words). Its component class is a predicate (`ABOARD`, section 3). Steps 050–070 write the predicate itself in this slot, not the words: the words name no particular thing, and the graph needs only the type of relation (an edge's type). The words stay in the classed triple's source text. Only step 040, which learns the schema, collects predicate instances before naming their predicate. |
| **verified triple instance** | One whose source text is really in its record's text, checked in code; a classed triple is **verified** the same way. An **unverified** one (no source text, or a source text that isn't in the text) can't be trusted: step 040 leaves it out of what it counts; step 050 keeps it, marked as an error, for the person to fix; step 060 removes it (reason `source_text`). |
| **describes triple** | The one classed triple every record gets that no text states, written by code: `<record id>` (`CatalogEntry`) DESCRIBES `<the record's title>` (`<entity class>`). It keeps the catalog entry apart from the thing the entry is about. The model's only part in it is naming that entity class, the **describes class** (`describes_class` in its reply), e.g. `Dataset`; `X` means none was named yet. |
| **error** / **flag** | What a check of a triple instance or a classed triple can raise. An **error** is something code can prove wrong (e.g. its source text isn't in the text); a **flag** is often a sign of a mistake, often fine (e.g. a reworded subject or object instance, or a component class the schema doesn't have). Listed in `050_annotate/050_annotate.md`. The annotation tool shows a component class the ground truth schema doesn't have as an error, not a flag, since it could be a typo. |
| **evened out** | How two subject instances, object instances, or source texts are compared: case, spacing, quote marks, dashes, punctuation at either end, and a leading "a", "an", or "the" are ignored, so "The MODIS" = "modis" (`common/common_helpers/text_match.py`). When a source text or a component instance is looked for in a record's text, punctuation inside either one also counts as a space, so "MODIS aboard Aqua" is found in "The MODIS, aboard Aqua"; two component instances being compared keep their inner punctuation. What is looked for in a text is found only as whole words and whole numbers: a match may not cut a word or a number in two, so "Aqua" is not found in "Aquarius", nor "5 minutes" in "25 minutes". Two exceptions: a plural ending ("s" or "es") may follow, so "Aqua satellite" is found in "Aqua satellites"; and a letter next to a digit counts as a break between words, so "67P" is found in "Comet67P". Where the record's text lost the space between two words ("thecomet"), a word inside them is not found: a subject instance or object instance there gets a flag, and a source text that starts or ends there is not found. |

---

## 3. Schemas

| Term | Meaning |
|---|---|
| **schema** | A description of the entity classes, the predicates, and the patterns: which entity classes each predicate has been seen between. |
| **schema entry** | An entity class, a predicate, or a pattern. |
| **entity class** | A type of thing a subject instance or object instance can be, e.g. `Instrument`, `Spacecraft`: a schema entry. The entity class of a classed triple's subject instance is its subject class; of its object instance, its object class. Through its patterns, an entity class can be a subject class, an object class, or both. |
| **predicate** | A word with two senses, told apart by context: **(1)** the component in the middle slot of a triple instance or a classed triple; **(2)** a schema entry: a type of relation, e.g. `ABOARD`, the component class of predicate instances. |
| **kind** | Of a component class: whether it is an entity class or a predicate (e.g. the translation table's `kind` column). |
| **component class** | What a component instance is classed as in a particular schema. For a subject instance or an object instance, one of the schema's entity classes; for a predicate instance, one of the schema's predicates (examples below). |
| **loose match** | How two component classes are compared: only letters and digits count, so `Space_craft` = `spacecraft` (`common/common_helpers/triples_io.component_class_key`). Step 040's **spelling fold** makes two labels that are a loose match one label. |
| **merge** | Making two labels or component classes that mean the same thing into one: in step 040 (stage 4), two labels the model judges the same (`Sensor` = `Instrument`); in the annotation tool, two component classes of the ground truth schema, by a person (**Rename or merge…**). Not a **spelling fold**, which code makes for labels that are a loose match. |
| **pattern** | The component classes of the three slots of a classed triple, as a schema lists them: a subject class, a predicate, and an object class, read from subject to object, e.g. `Instrument ABOARD Spacecraft`. The subject class and the object class may be the same entity class (`PersonName ALSO_KNOWN_AS PersonName`), though that is unusual. A schema's patterns record where its predicates have been seen, not everywhere a predicate may be used. |
| **pinned predicate** | A predicate of the ground truth schema that may join only the entity classes listed on its "only:" line ("any": any entity class), e.g. `ACQUIRED_BY_INSTRUMENT`, with `only: Dataset -> Instrument`. The checks flag a ground truth triple with any other pattern (`pattern_not_pinned`). Any other predicate may join whatever entity classes its meaning fits. |
| **schema additions** | A (typically) mini schema that a person discovers and manually writes to `annotations/schema_additions.txt` with the intention of including it with a second and (typically) larger, more complete schema passed together as a schema step 060 uses for extraction, hoping that step 060 performs better than it would with just the larger schema alone. This larger schema is usually the induced schema, since that is the default schema file step 060 takes. Each entry of this mini schema requires a source describing how it was discovered--- e.g. a subject-matter expert like a mentor; annotating tuning records; outside research, etc. |
| **ground truth schema** | The schema of the ground truth, which a person writes while annotating: `annotations/ground_truth_schema.txt`, its entity classes and predicates, each with a one-line definition, and its patterns: those its file lists, and every one the ground truth uses (code reads them from the ground truth files, so none is ever added by hand). Every entity class and predicate a ground truth triple uses must be in it. One used that it doesn't have yet (compared by loose match) is **coined**: a new one, or a typo. The annotation tool marks a coined one ✖, with a button that adds it with a definition, and step 070 stops while a finished record uses one; a pattern used for the first time is only flagged ⚑, for a look (a wrong entity class or direction). Step 050 shows it to the model as the component classes to reuse, step 040 compares the schema it learns with it, and step 070 translates the component classes of the current schema into it before comparing. |
| **domain** (of a predicate) | The entity classes its subject may belong to. |
| **range** (of a predicate) | The entity classes its object may belong to. |

**Component class, by example.** `Instrument` is the component class of the subject instances "MODIS" and "AIRS"; `ABOARD` is the component class of the predicate instances "is aboard" and "is mounted on".

**Patterns, domain, and range.** A predicate's patterns together give its domain (the subject classes that appear in them) and its range (the object classes). `HAS_TIME_SPAN`, with the patterns `Dataset HAS_TIME_SPAN TimeSpan` and `MissionPhase HAS_TIME_SPAN TimeSpan`, has the domain {Dataset, MissionPhase} and the range {TimeSpan}. Patterns say more than domain and range together: they say which subject class goes with which object class. Patterns record where a predicate was seen: in step 040's texts for the induced schema, and in the ground truth for the ground truth schema; not necessarily everywhere it is allowed.

**In a graph database.** These terms belong to no particular type of graph. In a labeled property graph (LPG) such as Neo4j:

| This project | In an LPG (e.g. Neo4j) |
|---|---|
| entity class | node label, e.g. `(:Instrument)` |
| predicate (schema entry) | relationship type, e.g. `[:ABOARD]` |
| pattern | `(:Instrument)-[:ABOARD]->(:Spacecraft)`, as Neo4j's own schema view shows |
| domain, range | the node labels allowed at the start and at the end of a relationship type (a convention; Neo4j doesn't enforce it) |

The words *domain* and *range* were standardized in RDF Schema, another type of graph, and are used the same way for any graph.

---

## 4. Ground truth and samples

| Term | Meaning |
|---|---|
| **ground truth** | The classed triples of the records chosen for annotation, as a person corrects them. Only a finished record's have been checked; a record not finished yet may still hold drafted triples as the model wrote them. Kept in `annotations/ground_truth/`, one file per batch of records (`batch_000.csv` holds 6 records annotated by hand before step 050 was built: their ground truth triples were written entirely by a person, not drafted and corrected, except those of pool positions 2, 3, and 4, which a model drafted and a person corrected (the model is named in their `drafted_by` column); `batch_001.csv` and every later file are corrected from step 050's drafted batch of the same number); the ground truth is all the files together. |
| **ground truth triple** | A classed triple of the ground truth, other than its record's describes triple. A record that states no facts has none (its ground truth file keeps only its id, to show it was annotated). What step 070 pairs with the occurrences of the extracted triples. A record's ground truth triples form its **set of ground truth triples**. Two of them with the same subject instance and object instance (evened out) and the same predicate must differ in subject class, object class, or both (by loose match): otherwise they are **the same classed triple twice**, and step 070 refuses to run until one is deleted; when they do differ, step 070 warns before evaluating. It has been checked by a person only once its record is finished. |
| **finished record** | A record of the ground truth whose *All facts extracted* box a person has ticked in the annotation tool, saying every fact its text states is among its ground truth triples (its ground truth file then has `1` in its `all_facts_extracted` column). By default, step 060 extracts only finished records, and step 070 evaluates only them. |
| **ground truth candidates pool** (the **pool** for short) | 1,000 records drawn once (2026-09-21) as candidates for ground truth, in a shuffled order. A person annotates them in that order, and only a subset ever gets annotated, since 1,000 is more than there is time to check. Each record's place in that order is its **pool position** (0, 1, 2, …). |
| **stratum** (plural **strata**) | One of the groups the pool was drawn by (stratified sampling): a large maintainer on its own, or "(small maintainers)" for the 404 maintainers too small to earn two of the 1,000 places. Each stratum got places in proportion to its size; `annotations/ground_truth_candidates.csv` names each record's stratum. Step 070's per-stratum numbers follow the strata. |
| **drafted batch** | The records step 050 drafts in one run (10 by default), numbered N. To **draft**: step 050's model writes the facts a record's text states as classed triples, for a person to correct; these classed triples are the **drafted triples**. A drafted batch is first the file `drafted_triples_batch<N>.csv` in 050's output folder; when it is opened in the annotation tool, it is copied into the ground truth file `batch_<NNN>.csv` of the same number, where a person corrects it. Not a **batch file** (step 010's harvest pages). |
| **drafted triple** | A classed triple step 050's model drafted (see **drafted batch**). When its drafted batch is opened in the annotation tool, it is copied into the ground truth file, and becomes a ground truth triple of a record not finished yet. |
| **annotation guidelines** | The rules for writing ground truth triples: [`annotations/guidelines.md`](../annotations/guidelines.md). The model follows the same rules when it drafts (050) and extracts (060): `common/common_prompts/extraction_rules.txt` (a test keeps the two in step). |
| **annotation tool** | `py helpers/annotate.py`: a page in your browser, on your computer only, to read and correct classed triples, check the translation table, review partial pairs, edit the schema additions, and add component classes to the ground truth schema (see `annotations/README.md`). Not a step. |
| **fair sample** | Records taken from the start of the ground truth candidates pool, in its order, with none skipped. Since the pool is shuffled, those are a fair sample of the whole catalog, so results measured on them hold for the catalog. Step 050 says when the ground truth stops being one (e.g. after drafting hand-picked records). Step 070 evaluates only the fair sample of finished, extracted records: the longest run of the pool's first records that a person has finished and 060 extracted. |
| **induction candidates** | Every record that isn't in the ground truth candidates pool and has text, each maintainer's in a fixed random order. Step 040 learns the schema from the first few of the largest maintainers. |

---

## 5. Learning the schema (step 040)

| Term | Meaning |
|---|---|
| **induced schema** | The schema step 040 learns from the texts of the induction candidates, written to `outputs/intermediate_results/040_induce_schema/the_schema.json`. By default, the current schema is the induced schema plus the schema additions. |
| **label** | The general word a model gives a component instance in step 040. For a subject or object instance, the type of thing it is ("MODIS" → `Instrument`), which becomes an entity class. For a predicate instance, the relation it expresses ("is aboard" → `ABOARD`), which becomes a predicate. Not the same as a *node label* in a graph database (section 3), though an entity class does become one. |
| **running vocabulary** | In step 040's labeling, the labels chosen so far. Each batch of component instances is shown it, so the model reuses a label when one fits instead of making up a near-duplicate. |
| **support** | How many different texts a schema entry was found in. A text stating it twice counts once. |
| **evidence** (of a schema entry) | What step 040 keeps to show why a schema entry is in the schema: its support, the maintainers and texts it was found in, and, for an entity class, examples (in `the_schema.json`). `induction_evidence.json` keeps everything the run saw and decided, from each text's triple instances to every label and merge. |
| **deferred** | A schema entry that was found but isn't in the schema, with the reason: support below `min_support`, judged too vague, or a pattern through a schema entry that isn't in the schema. |

---

## 6. Extracting with a schema (step 060)

| Term | Meaning |
|---|---|
| **current schema** | The schema step 060 extracts with. By default, the induced schema plus the schema additions. A person may give step 060 another **schema file** instead of the induced schema (`--schema <file>`), and another **additions file** instead of `annotations/schema_additions.txt` (`--additions <file>`), e.g. an empty one to leave the schema additions out. The schema step 060's last run used is written to `schema_used.json`, which step 070 reads (and 080 will), so both use exactly what 060 used. A **past schema** is one an earlier run of 060 used. |
| **extracted triple** | A classed triple step 060 kept after checking it: one in `extracted_triples.csv`, the graph's facts and what 070 evaluates. The ones its checks **removed** go to `extracted_triples_removed.csv` with the reason: `source_text` (its source text is missing or isn't in the record's text), `component_class_not_in_schema`, `duplicate`, or `malformed`. Removed is not deleted: the file keeps them for a person to look at. A record's extracted triples form its **set of extracted triples**. Two of them may share subject instance, object instance (evened out), and predicate only if they differ in subject class or object class (by loose match); otherwise they are the same classed triple twice, and step 060 removes one as `duplicate`. |
| **component class outside the schema** | An entity class or predicate the model used though the schema doesn't have it (e.g. `Satellite` when the schema says `Spacecraft`). Such a classed triple is removed; the report lists these component classes, most used first, as candidates for the schema additions. A component class that is a loose match for one of the schema's (`Space craft`) is not outside the schema: it's accepted and written in the schema's spelling. |

---

## 7. Evaluating extraction (step 070)

Step 070 compares the extracted triples with the ground truth, which works as the answer key. Every metric, with its formula, how to read it, and an example, is in [`070_evaluate/metrics.md`](../070_evaluate/metrics.md).

Each metric below is also read out in sentences, with each run's own counts, in the report; how: `070_evaluate/070_evaluate.md`, section *Reading the metrics*.

| Term | Meaning |
|---|---|
| **pair** | See [`070_evaluate/metrics/pairs.md`](../070_evaluate/metrics/pairs.md). It defines the **exact pair**, the **partial pair**, the **strict pair**, the **pair level** (exact or partial), **eligible** (meeting a pair level's requirements), and the **set of pairs** (one choice of pairs in a record). It explains why a record's translated extracted triples form a **multiset**, and what an element's **multiplicity** is. It also names what pairing leaves without a partner: an occurrence without one is **extracted only**, and a ground truth triple without one is **ground truth only**. |
| **partial pair review** | A person's ruling on a partial pair of a tuning record, **same fact** or **not the same fact**, made in the annotation tool (*Partial pairs*) and kept in `annotations/partial_pair_reviews.csv`. An occurrence and a ground truth triple marked "not the same fact" are never paired. The ruling itself is the **verdict**. |
| **translation table** | The table [`annotations/component_class_mapping.csv`](../annotations/component_class_mapping.csv), checked by a person: which component class of the ground truth schema each component class of the current schema means, or `(none)`. What one row says is a **translation**. Its columns abbreviate (crt: **current**, gtt: **ground truth triples**): `component_class_from_past_or_crt_schema` is a component class of the current schema or a past schema (one table serves every schema); `component_class_in_gtt` is a component class of the ground truth schema, the one the ground truth triples use; `definition_from_past_or_crt_schema` keeps that schema's definition of the component class from when the row was written or last checked, so a changed definition shows (the row is then stale: see **row state**). `checked` says whether a person has checked the row (`yes`, or `same component class` for a row accepted automatically because the two are spelled the same); `definition_in_gtt` keeps the ground truth schema's definition of `component_class_in_gtt` from that check. `swap_subject_and_object` is `yes` when the row's predicate says the same relation the other way round ("A CARRIES B" is "B ABOARD A"). |
| **component class mismatch** | Where extraction stated a ground truth triple's fact but, after translation, a component class differs: a pair whose subject class or object class differs, or an extracted only occurrence and a ground truth only triple with the same subject instance and object instance but different predicates. Step 070 counts them per row of the translation table; a frequent one points at a wrong row. |
| **translated extracted triple** | An extracted triple whose predicate, subject class, and object class are translated into the ground truth schema, through the translation table ([`annotations/component_class_mapping.csv`](../annotations/component_class_mapping.csv)); when the predicate's row says `swap_subject_and_object` is `yes`, its subject instance and object instance swap places too. What evaluation compares with the ground truth triples, one occurrence at a time. Two extracted triples can translate to the same translated extracted triple, so a record's translated extracted triples form a multiset, not a set (see the **pair** entry). |
| **occurrence in a record's multiset of translated extracted triples** | A translated extracted triple of a record, counted once for each extracted triple that translates to it, so a record has exactly one occurrence per extracted triple. Pairs are made between an occurrence and a ground truth triple, and precision counts occurrences. Also called: **occurrence**. What a multiset, an occurrence, and a multiplicity are in general: [`070_evaluate/metrics/pairs.md`](../070_evaluate/metrics/pairs.md), Example, *A multiset of translated extracted triples*. |
| **row state** | A note the annotation tool shows (⚑) on a row of the translation table, and that step 070's report warns about: **stale** (checked, but since then the current schema's definition of its component class changed, or the ground truth schema's definition of the one it translates to changed, or was missing when the row was checked; it counts as unchecked), **now exists** (says `(none)`, though the ground truth schema now has a component class spelled the same: it was added to the ground truth schema since), **suggested** (says `(none)`, and the model suggests a component class the ground truth schema gained since), **shared** (another component class of the current schema translates to the same one, so evaluation can't tell them apart) or **repeated** (the component class has more than one row). Not a **flag**, which is raised by a check of a triple instance or a classed triple. |
| **precision** | See [`070_evaluate/metrics/precision.md`](../070_evaluate/metrics/precision.md). |
| **recall** | See [`070_evaluate/metrics/recall.md`](../070_evaluate/metrics/recall.md). |
| **F1** | See [`070_evaluate/metrics/f1.md`](../070_evaluate/metrics/f1.md). |
| **entity-class accuracy** | See [`070_evaluate/metrics/entity_class_accuracy.md`](../070_evaluate/metrics/entity_class_accuracy.md): entity-class accuracy, and, by slot, **subject-class accuracy** and **object-class accuracy**. |
| **within reach** | See [`070_evaluate/metrics/recall_upper_bound.md`](../070_evaluate/metrics/recall_upper_bound.md): within reach and **within strict reach**. |
| **recall upper bound** | See [`070_evaluate/metrics/recall_upper_bound.md`](../070_evaluate/metrics/recall_upper_bound.md): the recall upper bound and the **strict recall upper bound**. |
| **recall within reach** | See [`070_evaluate/metrics/recall_within_reach.md`](../070_evaluate/metrics/recall_within_reach.md). |
| **describes accuracy** | See [`070_evaluate/metrics/describes.md`](../070_evaluate/metrics/describes.md): the describes accuracy, the **describes baseline**, and the **describes per-entity-class average**. |
| **margin of error** | See [`070_evaluate/metrics/approximately.md`, *Sampling error*](../070_evaluate/metrics/approximately.md#sampling-error). |
| **bootstrap** | How the margin of error is computed: see [`070_evaluate/metrics/approximately.md`, *Sampling error*](../070_evaluate/metrics/approximately.md#sampling-error). |
| **tuning part** | The ground truth records whose metrics may be looked at while improving the pipeline (a prompt, the schema, a setting): pool positions 0–5, and from position 6 on, two of every three records. Step 030 marks the part of each record of the pool in `splits.json`. A record of it is a **tuning record**. |
| **held-out part** | The ground truth records kept aside: from pool position 6 on, every third record (8, 11, 14, …). Their metrics are not looked at while improving the pipeline, only at the end; that is the number reported as how well the pipeline works. Otherwise the pipeline gets tuned to the records it is evaluated on, and its metrics flatter it. A record of it is a **held-out record**. |
| **held-out look** | One run of step 070 with `--evaluate_held_out true`: one time the held-out records' numbers were shown. Each is logged in `annotations/held_out_looks.csv`. A change made after a look lets the held-out records influence the pipeline. |
| **twin** | An evaluated record with the same title, the same `notes` field, or both, evened out, as a record the induced schema was learned from: the schema has then seen some or most of the twin's text. Its **twin kind** says what it shares with one such record: *whole text* (`title` and `notes`), *notes only*, or *title only*. A record with two kinds (with two different records) gets the one that shares more text: whole text, then notes only, then title only. Step 070 names the twins and gives each part's numbers both with and without them. Which records the schema was learned from, and why these kinds: [`070_evaluate/070_evaluate.md`, *Twins*](../070_evaluate/070_evaluate.md#twins). |


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
| **model** (**LLM**) | The AI model the steps ask, a large language model reached through a service, NASA's Ask Sage or NASA's LiteLLM (the defaults are `MODEL` and `SERVICE` in `common/common_helpers/llm.py`; each step that asks it has a `model` and a `service` setting, and `py helpers/models.py --service <service>` lists the models the service shows your account). In code comments, `LLM:` marks a move that asks it and `code:` one that doesn't. |
| **stand-in model** | A fake model used to test a step without the real one: code that returns made-up answers in the right format, without calling the model's service (LiteLLM or Ask Sage) or paying. A step tested only with a stand-in hasn't been run on real model answers yet. |
| **stand-in catalog** | A fake data.nasa.gov used to test harvest without the real one: code that answers like data.nasa.gov's API, with made-up records, on your own computer. Only the tests use it (`tests/stand_ins.py`). |
| **model call** (also **paid call**) | One request to the AI model, paid for. Every answer is kept in a cache, so a rerun pays only for what isn't there yet. Before a run's first one, the step stops and asks (setting `confirm_paid_calls`). |
| **test call** | The one-line paid call a step makes before its others, to check that the key, the service, and the model work. |
| **control panel** | A step's short script, `run.py` in the step's folder, e.g. `040_induce_schema/run.py`: its inputs, its settings, and its main moves, one line each. The rest of the folder is the code behind it. You run it from the repository folder: `py 040_induce_schema/run.py`. |
| **setting** | A value that decides how a step behaves and that its control panel shows for a person to change, e.g. `texts_per_maintainer`, given on the command line as `--texts_per_maintainer 30`. A value nobody tunes (e.g. 80 component instances per labeling call) isn't a setting: it's fixed in the step's code, as a named constant (`LABEL_BATCH`). |
| **run** | One execution of one step. Its **run id** (e.g. `040_induce_schema_2026-09-28_1811`) names its report and its log. |
| **report** | The page a run writes for people (`outputs/reports/<run id>.md`): what it read and wrote, its numbers, its warnings. |
| **log** | The line-by-line record of a run (`outputs/logs/<run id>.log`). |
| **upkeep** | Everything a person does to keep the project going (annotating, checking the translation table, reviewing partial pairs, committing, …), grouped by when it comes up: [`upkeep.md`](upkeep.md). `py run_pipeline.py --status` and the annotation tool's home page list what is waiting now, each item with its section there. Not a list of changes to the pipeline: those are in the improvements list. |
| **To do section** | The section *To do* of a step's guide (`<step>/<step>.md`): what a person does for that step, in short, with links to the upkeep's sections. |
| **improvements list** | The changes to make to the pipeline itself, each with why and where the idea came from: [`improvements.md`](improvements.md). |
| **manifest** | The file a step's output folder gets when a run finishes (`_manifest.json`): which files went in and came out, each with its hash. |
| **row** | One line of a CSV file the project keeps: in a ground truth file, a ground truth triple or a describes triple; in the translation table, one translation. |
| **fingerprint** | A short code computed from exact content: a file, a prompt, a set of settings. The same content always gives the same fingerprint, and any change gives a different one. Used to tell whether an input or a cached model answer still matches (technically a SHA-256 hash). |
| **recipe** | Everything that decides a run's output: its code version (Git commit), its settings (model and service among them), its prompts and input files by fingerprint, and, for step 070, the translation table used. `py helpers/compare_runs.py` compares two recipes on the same records. |
| **origin** | Where one output item came from, written inside the output file (`_origin`): the input item(s) it was made from, e.g. `010_harvest/batch_00000.json#<record id>`. `helpers/audit.py` follows origins back to the API request. |
