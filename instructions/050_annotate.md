# 050_annotate

Terms (triple instance, entity class, ground truth, draft batch, fair sample, …) are as defined in [docs/terminology.md](../docs/terminology.md), especially section *Ground truth and samples*.

## Purpose

Drafts ground truth for you to correct. A model reads the next records of the ground truth candidates pool and lists **every fact each record states**, as triple instances with an entity class for the subject and the object. It uses the hand-built schema's names where they fit and coins new ones where they don't: leaving a fact out is worse than a new name. Code adds each record's DESCRIBES row, removes repeats and replies that aren't triple instances, and checks every row against the record's text and the schema.

Each run writes one numbered **draft batch**. You correct it with the annotation tool (`py annotate.py`), which saves it into `annotations/ground_truth/` as the ground truth file with the same number. No step ever writes there.

Each run also checks your ground truth files for typos (see *Your ground truth* in the report).

## Inputs

| Input | Default | Contents |
|---|---|---|
| `records` | `020_clean/records.jsonl` | 020's cleaned records: the texts. |
| `splits` | `030_split/splits.json` | 030's ground truth candidates: the pool's 999 records still in the catalog, in the pool's order. |
| `hand_schema` | `./annotations/schema_derived_from_manual_annotation.txt` (in Git) | The hand-built schema. Shown to the model as the names to reuse, and the names every row is checked against. |
| `ground_truth` | `./annotations/ground_truth/batch_*.csv` (in Git) | Your ground truth: records in it are never drafted again, and every run checks it. |

Draft batches already in 050's output folder are read too: their records are waiting to be corrected, so they're not drafted again.

## Outputs

In `outputs/intermediate_results/050_annotate/`:

**On a rerun:** a new numbered batch is added; a batch already there is never overwritten.

| File | Contents |
|---|---|
| `drafted_triples_batch<N>.csv` | The draft batch: one row per triple instance, grouped by record, each record's DESCRIBES row first. |
| `drafted_triples_batch<N>_details.json` | How the batch was made: the run id, model and settings; each record's pool position, number of text pieces, status (`drafted` or `failed`, with the error), rows, and every item removed (with why); the records passed over while choosing; whether it's still a fair sample. |
| `cache/` | Every model answer, so a rerun pays only for what isn't there yet (see *How to run*). Not listed in the manifest. |
| `_manifest.json` | Run id, settings, input files and their hashes, output files and their hashes, headline numbers. Written when a run finishes. |

N is one more than the highest batch number used so far, by a draft batch or a ground truth file (`batch_000.csv` is 0, so the first draft batch is 1).

The draft batch's columns are the ground truth's, plus two:

| Column | Meaning |
|---|---|
| `id` | The record. |
| `subject`, `subject_class`, `predicate`, `object`, `object_class` | The triple instance and its entity classes, as the model wrote them. |
| `source_text` | The passage of the record's text that states it, as the model copied it. `(record structure)` on the DESCRIBES row. |
| `all_facts_extracted` | Always `0` in a draft: you set it to 1 (the tool's "All facts extracted" box) once a record is finished. |
| `flags` | Every check the row failed (see *Checks on each row*). Not kept in the ground truth: the tool recomputes the checks as you edit. |
| `origin` | Where the row came from: `020_clean/records.jsonl#<record id>` (see `instructions/000_audit.md`). |

Each run also leaves `outputs/reports/<run id>.md` (the report: what it read and wrote, its numbers, its warnings) and `outputs/logs/<run id>.log` (everything it did, line by line); how to read them: `instructions/000_audit.md`.

## Settings

| Setting | Default | What it does | When to change it |
|---|---|---|---|
| `records_per_batch` | 10 | How many records to draft this run. | To draft more or fewer in one sitting. |
| `start_position` | 0 | The pool position to start from. Records already in the ground truth or waiting in a draft batch are always skipped, so 0 means "the first ones not done yet". | To jump ahead in the pool (the report then says the ground truth is no longer a fair sample). |
| `ids` | empty | Exactly these records instead: ids separated by commas, or the path of a text file with one id per line (a CSV whose first column is the id works too; a header line `id`, blank lines and lines starting with `#` are skipped). They are drafted in the order listed, at most `records_per_batch` of them. | To draft records you choose. |
| `max_chars` | 8000 | A text longer than this is split into text pieces, one model call each (`common/chunking.py`). | Rarely. |
| `workers` | 4 | Model calls made at the same time. | Lower it if Ask Sage refuses calls for coming too fast. |
| `model` | google-claude-sonnet-5 | The AI model to ask. `py models.py` lists the models Ask Sage shows your account; a listed one may still refuse you, which the run's first call (the one-line test) finds out for the price of that call. Every cached answer is tied to its model: another model asks everything again, and switching back reuses the earlier answers. | See *Choosing a model* in `docs/running_on_nasa_laptop.md`. |
| `confirm_paid_calls` | true | Stop and ask before the first model call. | `false` for runs with nobody at the keyboard, e.g. the whole pipeline. |

## How to run

From the repository folder, with the environment active (`docs/virtual_environment_setup.md`), on a computer that can reach Ask Sage and has your key in `.env` (`docs/running_on_nasa_laptop.md`):

```
py 050_annotate.py --help                            every input and setting, with its default
py 050_annotate.py                                   the next 10 records of the pool
py 050_annotate.py --records_per_batch 3             the next 3
py 050_annotate.py --start_position 200              10 records from pool position 200 on
py 050_annotate.py --ids 3122be4c-…,cfd6ec3f-…       exactly these
py 050_annotate.py --ids my_ids.txt                  the ids in this file
py 050_annotate.py --confirm_paid_calls false        don't ask (unattended runs)
```

**Paying.** Before its first model call, 050 logs its plan (how many records, which batch number, how many calls, the model) and waits: Enter starts, anything else stops the run having spent nothing. If the run can't do exactly what you asked, it says so first, above the question (*Before you pay: this run can't do exactly what you asked*, then the reasons, listed under *Checks and warnings*). Its first call is a one-line test that the model name and key work. A run whose answers are all in the cache never asks and never pays. Model calls: one per record, plus one per extra piece of a long text, plus the test call.

**The cache.** Every model answer is kept in `cache/`, under a fingerprint of everything that decided it: the model, the prompt's exact text, and what was sent. A rerun reuses every answer whose fingerprint is unchanged: a failed call isn't kept, so a rerun asks only the calls that failed; editing a prompt asks again exactly the calls that use it; deleting `cache/` (or all of `outputs/`) means paying for every call again.

**Then correct the batch**, with the annotation tool:

```
py annotate.py
```

Pick the batch at the top of the page. The full steps are in [annotations/README.md](../annotations/README.md).

## How it works

Four stages, in `050_annotate.py`'s `main()`; stage 2 asks the model, the others are code:

1. **Pick the records** (`records.py`, `pick_records`). By default, the pool's records in its order, from `start_position` on, skipping those already in the ground truth, those waiting in a draft batch, and those with no text, until there are `records_per_batch`. With `ids`, those records, skipping the same ones. Anything that makes the batch differ from what you asked becomes a note shown before paying. It also works out whether the ground truth, the waiting drafts and this batch together are still exactly the first records of the pool: a fair sample.
2. **Ask the model** (`draft.py`, `ask_model`). One call per text piece, with the prompt `prompts/draft.txt`: *completeness first* (every fact, whether or not the schema can express it), then *naming* (the schema's names when one fits; otherwise a new one in the same style: entity classes in CamelCase, predicates in UPPER_SNAKE_CASE). Its rules and reply format are in `common/prompts/` and shared with step 060, so the ground truth and what 060 extracts are asked for the same way. Every answer goes into `cache/` the moment it arrives. A record with any failed call is left out of the batch, never half drafted.
3. **Build the rows** (`build_rows`, with `common/extraction.py`, shared with 060). The DESCRIBES row first, with the entity class the model named for what the title names (`X` if none). Then each triple instance: an item that can't be one (a missing subject, predicate or object, a list where text belongs, …) is removed as *malformed*; the same subject, predicate, object and entity classes again (e.g. from two pieces of a long text) is removed as a *duplicate*. Every row is checked (below). Nothing is removed for failing a check: that's for you to decide.
4. **Check your ground truth** (`check_ground_truth`, with `common/ground_truth.py`). Every row of every ground truth file, for typos (below).

**Then the results** (`results`): the draft batch and its details file are written, never over an existing one; the report.

The code: `050_annotate/` holds `moves.py` (the moves, and writing the results), `records.py`, `draft.py` and `prompts/`. Shared with other steps: `common/extraction.py` and `common/prompts/` (asking the model and building rows, with 060), `common/validate.py` (the checks), `common/ground_truth.py`, `common/cache.py`, `common/llm.py`.

### Checks on each row

Run against the record's **whole** text, including rows from one piece of a long text. They're written in the `flags` column, and the annotation tool shows them in plain words as you edit.

| Check | Kind | Meaning |
|---|---|---|
| `no_source_text` | error | The row has no source text. |
| `source_not_in_text` | error | Its source text isn't in the record's text: it may be invented. |
| `describes_undecided` | error | The DESCRIBES row has no entity class (`X`): choose one. |
| `describes_subject_not_id` | error | The DESCRIBES row's subject isn't the record's id. |
| `subject_not_in_text`, `object_not_in_text` | flag | Not found in the text: often reworded ("the instrument" for "MODIS"); fine if on purpose. |
| `subject_not_in_source`, `object_not_in_source` | flag | Not in the row's own source text. Not raised for a subject that is the record's title. |
| `subject_equals_object` | flag | Subject and object are the same. |
| `subject_class_not_in_schema`, `object_class_not_in_schema`, `describes_class_not_in_schema` | flag | An entity class the hand-built schema doesn't have: a new one, or a typo. |
| `predicate_not_in_schema` | flag | A predicate the hand-built schema doesn't have. |
| `pattern_not_in_schema` | flag | The predicate is in the schema, but never between these two entity classes. |
| `conflicting_classes` | flag | The same triple instance appears again with other entity classes; both rows are flagged. |

"In the text" ignores case, spacing, quote marks, dash variants, edge punctuation and a leading "the/a/an" (`common/text_match.py`). Names are compared with the schema's loosely: letters and digits only, case ignored, so `has version` is `HAS_VERSION`.

## Prompts

| Prompt file | Sent in | Asks the model to |
|---|---|---|
| `050_annotate/prompts/draft.txt` | stage 2, one call per text piece | list **every** fact the record states (completeness first), naming the entity classes and predicates with the hand-built schema's names where one fits and a new name otherwise; the hand-built schema is shown in the prompt |
| `common/prompts/extraction_rules.txt` | inside `draft.txt` (`$rules`) | follow the rules shared with 060: names as written, the shortest source text copied exactly, one fact per triple, no "is a" triples, the kind of thing the title names |
| `common/prompts/extraction_reply.txt` | inside `draft.txt` (`$reply`) | reply in the JSON form shared with 060 |

Each prompt is a plain text file: open it to read exactly what the model is told. `$name` marks where the code fills something in. The prompts speak plainly to the model ("facts", "names", "classes"), not in this project's terms, which the model doesn't know. Editing a prompt is allowed: the next run asks again every call that uses it, and pays for them. The two `common/prompts/` files are shared with 060: editing them changes both steps.

## Checks and warnings

**Shown before paying**, above the confirmation question (and also in the report's warnings):

| Message | Meaning | What to do |
|---|---|---|
| *You asked for N records (records_per_batch), but only M are left in the pool from position P on.* | The rest of the pool is done or waiting. | Nothing, or a lower `start_position`. |
| *N record(s) you listed is not in the catalog / without text / already in the ground truth / waiting in a draft batch to be corrected (batch K), so skipped* | With `ids`: those records can't or needn't be drafted. | Check for typos; a record waiting in a draft batch is drafted again only if you delete that draft batch (both its files) before correcting it. |
| *You listed N records that can be drafted, but records_per_batch is M* | Only the first M are drafted now. | Raise `records_per_batch`, or run again for the rest. |
| *start_position (N) is ignored, because ids names the records.* | The two settings can't both apply. | Drop one. |
| *With this batch, the ground truth is no longer the first records of the pool* | Hand-picked records or a jump ahead leave pool records behind. | Nothing, if on purpose. But 070 scores only the fair part (the pool's first records, with none skipped), so records after the gap are not scored until the records before them are annotated too. |

**In the report**, under *Warnings*:

| Message | Meaning | What to do |
|---|---|---|
| *N record(s) failed and are not in the batch* | Their model calls failed (after the model client's own retries). | Run the step again: only those are asked again, and every answer already paid for is reused. The next run drafts them first. |
| *No record was drafted, so no batch was written.* | Every call failed. | Check the connection; run again. |
| *Ground truth: record … is in batch_… and batch_…* | A record is annotated twice. | Keep it in one file. |
| *Ground truth: record … all_facts_extracted is 1 on some rows, 0 on others* | Mixed. | Set it the same on every row (the tool's box does). |
| *N row(s) of the ground truth have something to fix* | Typos, listed under *Your ground truth* with file and line: an id that isn't in the catalog, a subject, predicate or object partly empty, no source text or one not in the record's text, a DESCRIBES row without an entity class or whose subject isn't the record's id. | Fix them with the tool or any editor. |

**The step stops** with:

| Message | Meaning | What to do |
|---|---|---|
| *Nothing to draft. …* | No record could be chosen; the reasons follow. | Change the settings: the reasons are listed. |
| *ids names the file …, which doesn't exist* | A typo in the file name. | Fix the file name. |
| *missing input files … (run 020_clean or 030_split first, or pass --records / --splits)* | An input file isn't there: usually an earlier step hasn't run. | Run the steps in order, or pass the file with `--<input>`. |
| *… must be at least N* | A setting is out of range (`max_chars` under 1,000). | Fix the setting. |
| *Test call to … failed* | Ask Sage refuses you that model, the key is wrong, or Ask Sage can't be reached. Nothing else was called. | If Ask Sage says the model isn't allowed, choose another (`--model`; `py models.py` lists them). Otherwise check `.env` and the network. |
| *Cancelled. Nothing was spent.* | You declined at the confirmation. | — |

## Audit trail

- **Log.** `outputs/logs/<run id>.log` records the command line, the settings, the git commit, every model call's retries, each move's duration, each output file's hash and, on failure, the full traceback.
- **Origin.** Each row of a draft batch has an `origin` column naming its record in 020's `records.jsonl`. The ground truth files carry none: they are made by a person, so a trace stops there.
- **Trace.** `py audit.py <record id>` follows a record back through every step's output to the 010 batch file and the API request that first returned it (`instructions/000_audit.md`). It searches only the files a step's last run wrote, so for 050 the newest draft batch; a record in an older one is found through 030's `splits.json`.

## Human work

**Correct every draft batch** with `py annotate.py`: read each record's text first, then fix, delete or add rows until every fact it states is there, tick *All facts extracted*, and commit the file. Two biases to keep in mind, since the ground truth starts as a model's draft:

- accepting a wrong row is easy: reading the text first, then the rows, limits it;
- a fact the model missed is unlikely to be added by hand, and if the extractor (060) misses it too, nothing counts it as missed: recall comes out higher than it should. Adding what's missing matters more than polishing what's there.

Report any score against this ground truth as such: drafted by a model and corrected by a person, not written from scratch.

## Known limits

- **Not yet run with the real model.** As of 2026-09-29, 050 has been tested only with a stand-in for the model, because Ask Sage can't be reached from the laptop it was built on. Numbers in this guide come from the catalog, the code or the stand-in, not from a real run.
- **The schema in the prompt is the hand-built one**, whichever schema 060 ends up using: the ground truth should record every fact in stable names, not only what one schema can express.
- **A record deleted from a corrected batch is not drafted again**: it's still in its draft batch, which is how 050 knows it was seen. To redraft it, list it with `ids` after removing it from that draft batch file.
- **The model varies.** Rerunning with an empty cache can draft different rows; the cache makes a rerun reproducible.
