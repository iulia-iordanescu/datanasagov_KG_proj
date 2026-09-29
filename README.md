# data.nasa.gov Knowledge Graph

Fall 2026 Pathways internship project: building a knowledge graph (KG) for [data.nasa.gov](https://data.nasa.gov).

## What's in this repository

Every file and folder, what it is, and where it's explained. Each fact is written in one place; other places link to it.

**What you run**

| File or folder | What it is | Explained in |
|---|---|---|
| `010_harvest.py` … `060_extract.py` | The pipeline steps, run in order, one short script each: its inputs, its settings, and its main moves | the step's guide, `instructions/<step>.md` (same sections, in the same order, for every step) |
| `010_harvest/` … `060_extract/` | The code behind each step's script; for the steps that call the AI model (040, 050, 060), also the prompts it sends, as text files in `prompts/` | the step's guide, section *How it works* |
| `annotate.py`, `annotator/` | The annotation tool: a page in your browser for reading and correcting draft batches of ground truth | [`annotations/README.md`](annotations/README.md) |
| `audit.py` | Traces a record back to the download that first brought it in: `py audit.py <record id>` | [`instructions/000_audit.md`](instructions/000_audit.md) |
| `common/` | Code shared by several steps (reading records and schemas, the model client, the checks, the reports, …) | the opening comment of each file, for people reading the code |

**What you read or edit**

| File or folder | What it is | Explained in |
|---|---|---|
| `README.md` | This page: what's where, and why the pipeline is built the way it is | — |
| `instructions/` | One guide per step (`010_harvest.md` … `060_extract.md`), plus `000_audit.md`: reading a run's report and log, and tracing records | — |
| `docs/terminology.md` | What every word used here means | — |
| `docs/virtual_environment_setup.md` | Setting up a computer to run the pipeline: Python 3.14, its own environment (`.myvenv`), the packages, your Ask Sage key in `.env`, and VS Code | — |
| `docs/running_on_nasa_laptop.md` | The checklist for running the pipeline on the NASA laptop, the one that can reach the AI model: getting the code, the order of the steps, what costs money, what to do when something goes wrong | — |
| `annotations/` | Work made by a person, kept in Git: the ground truth (`ground_truth/`), the ground truth candidates pool (`ground_truth_candidates.csv`, `.json`), the hand-built schema, the schema additions, and the notes and old drafts they started from (`archive/`) | [`annotations/README.md`](annotations/README.md), which lists every file there |
| `TODO.md` | Your to-do list | — |
| `requirements.txt` | The Python packages the pipeline needs, installed with `pip install -r requirements.txt` | [`docs/virtual_environment_setup.md`](docs/virtual_environment_setup.md) |

**What runs make (only on your computer, never in Git)**

| File or folder | What it is | Explained in |
|---|---|---|
| `outputs/intermediate_results/<step>/` | What each step wrote: its output files, `_manifest.json` (which files went in and came out, with their hashes), and, for steps that call the model, `cache/` (every paid answer; don't delete it) | the step's guide, section *Outputs* |
| `outputs/reports/<run id>.md` | One page per run of a step: what it read and wrote, its numbers, its warnings | [`instructions/000_audit.md`](instructions/000_audit.md) |
| `outputs/logs/<run id>.log` | Everything a run did, line by line, and why it failed if it did | [`instructions/000_audit.md`](instructions/000_audit.md) |
| `.env` | Your Ask Sage email and key | [`docs/virtual_environment_setup.md`](docs/virtual_environment_setup.md), part 6 |
| `.myvenv/` | The project's Python environment | [`docs/virtual_environment_setup.md`](docs/virtual_environment_setup.md) |

**Background and settings, rarely needed**

| File or folder | What it is |
|---|---|
| `to_be_reshaped/` | The scripts from before the pipeline, kept as reference while their work moves into the steps. Never run. |
| `docs/pipeline_redesign_plan.md` | An earlier write-up of the pipeline's design, kept as background. |
| `docs/v0_schema.txt` | An early version of the schema. Nothing reads it. |
| `docs/pipeline_implementation_prompt.md` | (only on your laptop, not in Git) The hand-off note Claude builds from. |
| `.gitattributes`, `.gitignore` | Git settings: plain line endings on every computer, and the files Git leaves out (`outputs/`, `.env`, `.myvenv/`, …). |

## Pipeline overview

Phase 1 (done) was built by the scripts `nasa_harvest.py` and `nasa_census.py`. Phase 2 is a pipeline of 8 numbered steps, run in order, each from its own short script in the repository folder (`py 010_harvest.py`, …). Each step reads what earlier steps wrote in `outputs/intermediate_results/` (or files kept in `annotations/`), writes its own output there, and leaves a report and a log. Details of each step are in its guide, `instructions/<step>.md`.

| Step | What it does | Reads | Writes | Status |
|---|---|---|---|---|
| `010_harvest` | Downloads every catalog record from data.nasa.gov's API | the API | `batch_*.json`, one per page | built |
| `020_clean` | Turns HTML in the text into plain text; joins maintainer spellings | 010 | `records.jsonl` | built |
| `030_split` | Keeps the ground truth candidates pool in its order; orders every other record with text, per maintainer, for 040 | 020, `annotations/ground_truth_candidates.csv` | `splits.json` | built |
| `040_induce_schema` | Learns the schema from a sample of texts (model calls) | 020, 030, the hand-built schema | `the_schema.json`, `induction_evidence.json` | built; not yet run with the real model |
| `050_annotate` | Drafts ground truth for a person to correct (model calls) | 020, 030, the hand-built schema, `annotations/ground_truth/` | `drafted_triples_batch<N>.csv`, `…_details.json` | built; not yet run with the real model |
| `060_extract` | Extracts the triple instances the schema can express (model calls); by default from the finished ground truth records | 020, 040, `annotations/schema_additions.txt`, `annotations/ground_truth/` | `extracted_triples.csv`, `extracted_triples_removed.csv`, `schema_used.json`, `extraction_details.json` | built; not yet run with the real model |
| `070_evaluate` | Scores extraction against the ground truth | `annotations/ground_truth/`, 060 | | not built |
| `080_build_graph` | Builds the graph | 020, 060 | | not built |

Two helpers aren't steps: `py annotate.py`, the annotation tool, a page in your browser for reading and correcting draft batches; and `py audit.py <record id>`, which traces a record back to the download that first brought it in. Code shared by the steps is in `common/`; files made by a person are in `annotations/`.

## Records and fields

Throughout this project, a "record" is the metadata of one catalog entry in <[data.nasa.gov](https://data.nasa.gov)>. In JSON terms, each record is one object with 31 possible top-level key-value pairs, of which 24 are populated at least once across the catalog (title, description, maintainer, tags, and so on; the other 7 are empty on every record). Being metadata, the records describe the catalog entries; any actual scientific data or content lives in separate NASA data archives that each record links to, and is never downloaded here. Most catalog entries of data.nasa.gov are datasets.
The keys of these top-level key-value pairs are what we call metadata fields or just fields. Fields come from the raw JSON in which data.nasa.gov's public API returns each record. The API returns every record with the same metadata form provided by CKAN, a standard open-source catalog software, which data.nasa.gov runs on. The data.nasa.gov website renders each record as a readable page (headline, description text, tag buttons), but the harvest in this project comes from the API, which is why we know each the exact name (top-level key) and its exact associated populated content (associated value of the top-level key) of each field for a record, rather than guessing either from webpage text.

An example of a real record can be seen by opening the following link in a browser (ticking off the pretty-print box at the top is advised):<https://data.nasa.gov/api/3/action/package_search?rows=1>. You can see field names that exist in every record, like `id`, `title`, `notes`, `maintainer`, `organization`, `tags`, `resources`, `extras`, etc., as well as the populated contents of each field, which are particular to this record. Several fields hold nested objects and arrays that have fields of their own: `organization` is an object with ~7 inner keys, `tags` is an array where each of its entries has ~4 inner keys, `resources` is an array where each of its entries has ~15 inner keys, and `extras` is a (currently unexplored!) array of extra key-value pairs. Our census counted at the top level, then reached one level deeper only where the design needed it (`tags[].name`, `resources[].format`, `organization.title`). The inner-key counts are approximate because we never censused the nested layers, only the three aforementioned inner keys the design actually reads.

**A note on timing:** the catalog itself is not static! A handful of records is added every week, so any harvest is a snapshot of a specific date. The phase 1 graph was built from a harvest taken 2026-08-30 (36,289 records); a re-harvest on 2026-09-02 returned 36,323. We take care to note the date on which a harvest was taken whenever counts are involved in this README.

## Project phases

There are two phases to the building of this knowledge graph. Phase 1 turned the structured fields, such as `maintainer`, of every record into a fact; phase 2, still in progress, extracts additional facts from the fields involving free-text descriptions such as `title` (title of catalog entry) and `notes` (explanation of catalog entry). Phase 1 is mostly complete, and its schema is summarized in the table below:

| Node label | Count | From | Properties | Relationship to Dataset |
|---|---:|---|---|---|
| Dataset | 36,289 | one per record | id, name, title, created, modified, license | |
| Maintainer | 434 | `maintainer` field | name | `(Dataset)-[:MAINTAINED_BY]->(Maintainer)` |
| Keyword | 8,277 | `tags`, cleaned | name | `(Dataset)-[:TAGGED_WITH]->(Keyword)` |
| Format | 63 | `resources[].format` | name | `(Dataset)-[:AVAILABLE_AS]->(Format)` |


## Phase 1: how the census decided the design

A data census (nasa_census.py) is what decided this design. This script counted, for every field, how often it is filled and how many distinct values it holds. Those counts decided whether and what each field becomes in the knowledge graph:

- If many records share a field's values and those values are worth traversing through, the values become nodes. If a field fails that test but its values still answer some question by filtering or identifying (license, title, dates), the values become properties.
- If a field's values answer no question anyone would ask the graph (`creator_user_id`, `isopen`), the field is ignored.
- Values that mean "empty" become nothing, whatever their field.

These decisions work because of convergence, meaning many different records mentioning the same value. When a value converges, such as 6,214 records sharing the maintainer "Planetary Data System", storing it as one node attaches all 6,214 relationships to it, and standing on that node answers "everything connected to this value" in one hop. A value only one record mentions would yield a node with a single relationship, connecting nothing to nothing, so non-converging values stay properties.

This node-versus-property criterion is standard in property-graph design. The criterion also involves judgment, not just counting: `license_title` has only 4 distinct values shared across thousands of records, but nobody would traverse from license to license, only filter by it, so per the first bullet it stays a property.

Each field's numbers then forced a decision:

- `organization` has 1 distinct value across all records ("NASA"), which connects everything to everything and therefore means nothing, so it is ignored.
- `maintainer` has 435 distinct values that are heavily shared, so it became the `Maintainer` label and the `MAINTAINED_BY` relationship type. Its value "undefined" (989 records) means empty and produces no relationship.
- `tags` has 8,279 distinct values with 132k total uses, so it became the `Keyword` label and `TAGGED_WITH`. Its junk values "__" (7,673 uses) and "nasa" (1,086 uses) produce no nodes.
- `resources[].format` has 63 distinct, heavily shared values, so it became the `Format` label and `AVAILABLE_AS`. Resources exist on only 54.9% of records, so a dataset with no formats is normal, not an error.
- `license_title` has only 4 distinct values. You would filter on it, never traverse through it, so it stays a property on `Dataset`.
- `id`, `name`, `title`, and the timestamps are unique per record, so they stay properties on `Dataset`.
- `notes` is 100% filled with a median of 529 characters of prose, which code cannot parse, so it is reserved for phase 2.
- The remaining administrative fields (`creator_user_id`, `isopen`, `state`, `owner_org`, `private`, `type`, `tracking_summary`, and similar) are populated but answer no question anyone would ask the graph, so they are ignored.
- `extras` is not ignored but deferred: it holds a grab-bag of additional key-value pairs (a look at one record showed entries like publisher and time coverage), and we might explore it further down the line.
- 7 fields (`author`, `author_email`, `groups`, `relationships_as_subject`, `relationships_as_object`, `url`, `version`) exist on every record but are populated on none, so there is nothing to decide about them.

Only three nested fields got a deeper look: `tags[].name`, `resources[].format`, and `organization.title`. Digging into a nested field only pays off if it might contain values shared across records, since only shared values can become nodes, and these three are the only nested fields where that is possible. The other nested fields hold view counts (unique numbers per record) or are empty on every record, and `extras` was consciously deferred, as noted above. Within each of the three, we read the one inner key that names the thing (`name`, `format`, `title`) and skipped the keys that administer it (ids, states, sizes, timestamps).

Phase 1 collected the facts that can be read directly from the structured fields as triples: once again, no interpretation is needed so code just copies each field value directly. Phase 2 extracts triples from the natural-language prose in each record's `notes` and `title` fields, which requires actually reading the text, so a large language model processes this text and code checks its output.

## Phase 2: extracting facts from text (work in progress)

> Phase 2 is not part of the polished deliverable yet.

Phase 2 mines the free-text `notes` and `title` fields of each record, which is where the interesting facts hide: which instrument took the data, aboard which spacecraft, observing what, measuring what.

Where phase 1 merely copied field values into triples, phase 2 has to extract facts from prose, so the work splits into three questions: what vocabulary (schema) should the triples use, how do we get the triples out, and how do we know whether they are right.

### Cleaning (step 020)

The `notes` and `title` fields are cleaned before anything reads them. In the harvest of 2026-09-27, 1,277 of 36,375 descriptions and 6 titles carried HTML markup baked into the text (escaped tags, sometimes escaped twice), which would otherwise produce triples about paragraph tags rather than about datasets. The cleaner verifies its own work: every word, number and URL fragment in the source must survive into the cleaned value, and a value that would lose content falls back to a cruder method or to the source text itself. In that harvest, 2 descriptions needed a fallback and none lost content. Titles are also made one line: 3,356 had line breaks or runs of spaces inside, which the website hides but a file keeps. The cleaned records are written to `records.jsonl` (step 020), one per line, each field under its own key.

The same step also joins maintainer spellings, e.g. "Kristan Morgan" and "KRISTAN MORGAN" are one person; left apart they count as two communities everywhere downstream. Names matching once case, punctuation, word order and titles (Dr., Ph.D.) are ignored are treated as one, which took the 434 spellings in the harvest of 2026-09-27 down to 422 maintainers. Names differing by a middle initial are left apart, since merging those needs a rule nobody has chosen.

Details: [`instructions/020_clean.md`](instructions/020_clean.md).

### Two samples that never overlap (step 030)

Two parts of the work need records to read: learning the schema, and the ground truth that judges extraction. They must never share a record. If the schema were learned from the same records it is later judged on, it would have seen the exam questions before the exam, and its scores would look better than it is. So step 030 keeps them apart:

- the **ground truth candidates pool**: 1,000 records drawn once, on 2026-09-21, in a shuffled order (below); 999 are still in the catalog;
- the **induction candidates**: every other record with text (35,376 on 2026-09-28), each maintainer's in a fixed random order.

Both orders are fixed, so taking more records later keeps the ones already taken, and any first *k* is a fair sample.

Details: [`instructions/030_split.md`](instructions/030_split.md).

### Schema induction (step 040)

The schema is derived from the catalog rather than written in advance. The data-driven method to induce the schema follows AutoSchemaKG ([arXiv:2505.23628](https://arxiv.org/abs/2505.23628)): take a sample of records (the first 15 induction candidates of each of the 10 largest maintainers, who together hold 91.6% of the catalog's records), extract facts with no schema imposed, give every extracted name a general label, merge the labels that mean one thing, and count how many distinct records produced each candidate. The model also says what kind of thing each record describes (a dataset, a web tool, a document), so the schema always has entity classes for that. Every candidate is kept with its evidence; a cutoff, to be chosen from step 070's scores, decides which enter the schema (today: all of them). Support is counted in distinct records and distinct maintainers, so a pattern backed by one maintainer's house style is visible as such rather than passing as a catalog-wide regularity. What code can check, it checks rather than trusting the model: each extracted fact's source text must really be in its record's text, or the fact isn't counted, and the counts, the patterns' entity classes and each entity class's examples are computed by code.

Details: [`instructions/040_induce_schema.md`](instructions/040_induce_schema.md).

### Ground truth: an annotated pool (step 050 and the annotation tool)

None of the above says whether extraction is correct, and no query built on the graph is worth more than the extraction under it. Assessing quality needs ground truth: triple instances a person has checked, record by record. The ground truth candidates pool is where they come from. They are candidates: only a subset will ever be annotated and used as ground truth, since verifying 1,000 records by hand is more than the time available.

The pool is a stratified random sample: records are grouped by maintainer, each group gets places in proportion to its size, maintainers too small to earn two places are combined into one group, and the rows are shuffled so that the first k of them are a fair sample for any k. That last property is what makes partial annotation usable: annotation will stop long before 1,000, and wherever it stops, what has been annotated is still a fair sample rather than one biased by alphabetical or by-maintainer ordering. Records are therefore annotated in the pool's order; step 050 says when the ground truth stops being the first records of the pool.

Annotating is slow, and the rules had to be worked out on the records themselves. Each record gets one structural row, the DESCRIBES row, keeping the catalog entry separate from the thing it describes. The entity classes and predicates decided this way are kept in the hand-built schema (`annotations/schema_derived_from_manual_annotation.txt`), which grows as annotation proceeds; it is small and elementary, and it is expected to keep growing.

Writing every triple by hand is the bottleneck, so step 050 drafts the triple instances of the next few records (10 per batch by default), asking the model for every fact the text states, in the hand-built schema's names where they fit. A person then corrects each draft batch in the annotation tool (`py annotate.py`), a page in the browser that shows each record's text with its triple instances and saves every change into `annotations/ground_truth/`. The draft is not ground truth: a human keeps, edits, deletes or adds, driven by the record's text. Two biases remain, since the ground truth starts as a model's draft: accepting a wrong row is easy, and a fact the model missed is unlikely to be added. So any score against this ground truth is reported as such: drafted by a model and corrected by a person, not written from scratch.

Details: [`instructions/050_annotate.md`](instructions/050_annotate.md).

### Extraction (step 060)

Step 060 extracts, from each record's text, only the facts the schema can express, in only the schema's names. The schema is 040's induced one by default, plus any entity classes and predicates added by hand (`annotations/schema_additions.txt`, e.g. on a mentor's advice, each noting where the idea came from); any other schema can be given instead. Code checks every triple instance: one whose source text isn't in the record's text (it may be invented), or that uses a name the schema doesn't have, is removed with the reason; the rest are kept. The names outside the schema the model keeps reaching for are listed, as candidates for the schema. Until the schema is final, 060 extracts only from the finished ground truth records, which is all step 070 can score; afterwards, from every record.

Details: [`instructions/060_extract.md`](instructions/060_extract.md).

### Evaluation (step 070, not built yet)

With enough annotated records, extraction can be scored: recall is how many of the hand-written facts the extractor found, and precision is how many of its answers were right. The point of the exercise is not a single number but a fixed measuring stick: the same annotated records can be run against a different prompt, a different model, or extraction with and without the induced schema, and the difference between those runs is what says whether any of them is worth its cost.

Planned so far, to be settled when 070 is built: the induced schema's names are translated to the ground truth's names through a mapping a person checks; the *schema ceiling* (how much of the ground truth the schema can express at all) is reported apart from precision and recall; the DESCRIBES row is scored on its own, since code writes most of it; the ground truth is split into a tuning part, on which settings such as 040's cutoff may be chosen, and a held-out part scored once, so the reported scores don't flatter choices made by looking at them; and scores per maintainer group use the pool's own sampling groups.

### Building the graph (step 080, not built yet)

Step 080 will build the graph from the structured fields (maintainers, keywords, formats, as in phase 1) and the triple instances 060 kept, as plain files of nodes and edges. Which graph database to load them into (a labeled property graph such as Neo4j is the plan) is decided separately.
