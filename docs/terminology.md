# Terminology

The words this project uses, and exactly what each one means. It is expected to change as the project progresses, and is necessary for the best possible understanding of this documentation. Check back often for edits :)

**Contents**

1. [Records and their text](#1-records-and-their-text)
2. [Triples](#2-triples)
3. [Schemas](#3-schemas)
4. [Ground truth and samples](#4-ground-truth-and-samples)
5. [Learning the schema (step 040)](#5-learning-the-schema-step-040)
6. [The pipeline](#6-the-pipeline)

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
| **component** | One of the three named pieces of a triple: **subject**, **predicate** or **object**. |
| **slot** | Where a component sits in a triple. |
| **component instance** | A value filling a slot. "Rosetta" might fill a subject or object slot; "is mounted on" might fill a predicate slot. |
| **triple instance** | A triple with all three slots filled: one fact stated as subject, predicate and object, e.g. "MODIS" – "is aboard" – "Aqua". |
| **verified triple instance** | One whose source text is really in its record's text, checked in code. An **unverified** one (no source text, or a source text that isn't in the text) can't be trusted: step 040 leaves it out of what it counts; step 050 keeps it, marked as an error, for the person to fix. |
| **DESCRIBES row** | The one triple instance every record gets that no text states, written by code: `<record id>` (`CatalogEntry`) DESCRIBES `<the record's title>` (`<entity class>`). It keeps the catalog entry apart from the thing the entry is about. The model's only part in it is naming that entity class; `X` means none was named yet. |
| **error** / **flag** | What a check of a triple instance can raise. An **error** is something code can prove wrong (e.g. its source text isn't in the text); a **flag** is often a sign of a mistake, often fine (e.g. a reworded name, or a name the schema doesn't have). Listed in `instructions/050_annotate.md`. |

---

## 3. Schemas

| Term | Meaning |
|---|---|
| **schema** | An object that describes the entity classes, the predicates, and the allowed relationships between predicates and entity classes. These allowed relationships are the **patterns**. |
| **schema entry** | An entity class, a predicate, or a pattern. |
| **entity class** | A collective name for subject classes and object classes. In a schema, the role of an entity class is either a subject or an object, strictly a subject, or strictly an object. E.g. `Instrument`, `Spacecraft`. |
| **predicate** | A word with two senses, told apart by context (details below): **(1)** the component in the middle slot of a triple; **(2)** a schema entry: a kind of relation, e.g. `ABOARD`. |
| **component class** | The class of a component in a particular schema. For a subject or an object, one of the schema's entity classes; for a predicate, one of the schema's predicates (examples below). |
| **pattern** | One allowed combination of an entity class, a predicate and an entity class, read from subject to object, e.g. `Instrument ABOARD Spacecraft`. |
| **hand-built schema** | The schema a person wrote while annotating the first records: `annotations/schema_derived_from_manual_annotation.txt`. Step 050 shows it to the model as the names to reuse; step 040 compares the schema it learns with it. |
| **domain** (of a predicate) | The entity classes its subject may belong to. |
| **range** (of a predicate) | The entity classes its object may belong to. |

**Predicate, in its two senses.** In the triple instance "MODIS" – "is mounted on" – "Aqua", the predicate component instance is the text's own words, "is mounted on". In a schema, the predicate `ABOARD` is a kind of relation: the class of every predicate component instance that expresses it ("is aboard", "is mounted on", "flies on"). A schema's predicates are to predicate component instances what its entity classes are to subject and object component instances.

**Component class, by example.** `Instrument` is the component class of the subject component instances "MODIS" and "AIRS"; `ABOARD` is the component class of the predicate component instances "is aboard" and "is mounted on".

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
| **ground truth candidates pool** | 1,000 records drawn once (2026-09-21) as candidates for ground truth, in a shuffled order. A person annotates them in that order, and only a subset ever gets annotated, since 1,000 is more than there is time to check. |
| **draft batch** | The triple instances a model drafted, in one run of step 050, for a few records (10 by default), waiting for a person to correct them: `drafted_triples_batch<N>.csv` in 050's output folder. Corrected with the annotation tool (`py annotate.py`), it becomes the ground truth file `batch_<NNN>.csv` with the same number. |
| **annotation tool** | `py annotate.py`: a page in your browser, on your computer only, to read and correct triple instances (see `annotations/ground_truth/README.md`). Not a step. |
| **fair sample** | Records taken from the start of the ground truth candidates pool, in its order, with none skipped. Since the pool is shuffled, those are a fair sample of the whole catalog, so results measured on them hold for the catalog. Step 050 says when the ground truth stops being one (e.g. after drafting hand-picked records). |
| **induction candidates** | Every record that isn't in the ground truth candidates pool and has text, each maintainer's in a fixed random order. Step 040 learns the schema from the first few of the largest maintainers. |

---

## 5. Learning the schema (step 040)

| Term | Meaning |
|---|---|
| **label** | The general name a model gives a component instance in step 040. For one in a subject or object slot, the kind of thing it is ("MODIS" → `Instrument`), which becomes an entity class. For one in a predicate slot, the relation it expresses ("is aboard" → `ABOARD`), which becomes a predicate. Not the same as a *node label* in a graph database (section 3), though an entity class does become one. |
| **support** | How many different texts a schema entry was found in. A text stating it twice counts once. |
| **deferred** | A schema entry that was found but isn't in the schema, with the reason: support below `min_support`, judged too vague, or a pattern through a schema entry that isn't in the schema. |
| **model call** | One request to the AI model, paid for. Every answer is kept in a cache, so a rerun pays only for what changed. |

---

## 6. The pipeline

| Term | Meaning |
|---|---|
| **step** | One of the 8 numbered parts of the pipeline, `010_harvest` to `080_build_graph`. Each step reads what earlier steps wrote and writes its own output. |
| **stage** | One part of a step's work, in order; e.g. step 040 has 7 stages. Never called a step. |
| **control panel** | A step's short script, e.g. `040_induce_schema.py`: its settings and its main moves, one line each. The code behind it is in the step's folder. |
| **parameter** | Any value that decides how code behaves, e.g. how many texts to learn from, or how many component instances go in one model call. |
| **setting** | A parameter of a step that its control panel shows for a person to change, e.g. `texts_per_maintainer`, given on the command line as `--texts_per_maintainer 30`. A parameter nobody tunes (e.g. 80 component instances per labeling call) isn't a setting: it's fixed in the step's code, as a named constant (`LABEL_BATCH`). |
| **run** | One execution of one step. Its **run id** (e.g. `040_induce_schema_2026-09-28_1811`) names its report and its log. |
| **report** | The page a run writes for people (`outputs/reports/<run id>.md`): what it read and wrote, its numbers, its warnings. |
| **log** | The line-by-line record of a run (`outputs/logs/<run id>.log`). |
| **manifest** | The file a step's output folder gets when a run finishes (`_manifest.json`): which files went in and came out, each with its hash. |
| **origin** | Where one output item came from, written inside the output file (`_origin`): the input item(s) it was made from, e.g. `010_harvest/batch_00000.json#<record id>`. `audit.py` follows origins back to the API request. |
