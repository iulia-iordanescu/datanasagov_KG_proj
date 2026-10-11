# 050_annotate

Terms ([triple instance](../docs/terminology.md#2-triples), [entity class](../docs/terminology.md#3-schemas), [ground truth](../docs/terminology.md#4-ground-truth-and-samples), [draft batch](../docs/terminology.md#4-ground-truth-and-samples), [fair sample](../docs/terminology.md#4-ground-truth-and-samples), …) are as defined in [docs/terminology.md](../docs/terminology.md), especially section *Ground truth and samples*.

## Purpose

Drafts [ground truth](../docs/terminology.md#4-ground-truth-and-samples) for you to correct. A [model](../docs/terminology.md#8-the-pipeline) reads the next [records](../docs/terminology.md#1-records-and-their-text) of the [ground truth candidates pool](../docs/terminology.md#4-ground-truth-and-samples) and lists **every [fact](../docs/terminology.md#2-triples) each record states**, as [classed triples](../docs/terminology.md#2-triples). It uses the [component classes](../docs/terminology.md#3-schemas) of the [ground truth vocabulary](../docs/terminology.md#7-evaluating-extraction-step-070) where they fit (the [hand-built schema](../docs/terminology.md#3-schemas)'s, plus any you [coined](../docs/terminology.md#7-evaluating-extraction-step-070) while annotating) and coins new ones where they don't: leaving a fact out is worse than a new [entity class](../docs/terminology.md#3-schemas) or [predicate](../docs/terminology.md#3-schemas). Code adds each record's [DESCRIBES row](../docs/terminology.md#2-triples), removes repeats and replies that aren't classed triples, and checks every row against the record's [text](../docs/terminology.md#1-records-and-their-text) and the [schema](../docs/terminology.md#3-schemas).

Each [run](../docs/terminology.md#8-the-pipeline) writes one numbered **[draft batch](../docs/terminology.md#4-ground-truth-and-samples)**. You correct it with the [annotation tool](../docs/terminology.md#4-ground-truth-and-samples) (`py helpers/annotate.py`), which saves it into `annotations/ground_truth/` as the ground truth file with the same number. No [step](../docs/terminology.md#8-the-pipeline) ever writes there.

Each run also checks your ground truth files for [errors](../docs/terminology.md#2-triples) (see *Your ground truth* in the [report](../docs/terminology.md#8-the-pipeline)).

## To do

### Every step

The same for every [step](../docs/terminology.md#8-the-pipeline): see [*Every step* in step 010's guide](../010_harvest/010_harvest.md#every-step).

### This step

#### Before running

- **Before the real [runs](../docs/terminology.md#8-the-pipeline), choose the [model](../docs/terminology.md#8-the-pipeline):** the strongest one Ask Sage lets you use, and from a different maker than extraction's (`docs/running_on_nasa_laptop.md`, *Choosing a model*).
- **Draft and correct batches in [pool](../docs/terminology.md#4-ground-truth-and-samples) order, without skipping:** a [record](../docs/terminology.md#1-records-and-their-text) after a gap falls out of the [fair sample](../docs/terminology.md#4-ground-truth-and-samples), the only records evaluation evaluates.

#### After running

- **Correct every [draft batch](../docs/terminology.md#4-ground-truth-and-samples)** with `py helpers/annotate.py`: read each record's [text](../docs/terminology.md#1-records-and-their-text) first, then fix, delete or add rows until every [fact](../docs/terminology.md#2-triples) it states is there, and tick *All facts extracted*. The tool saves your corrections to `annotations/ground_truth/batch_<NNN>.csv`; never correct the draft itself (`outputs/intermediate_results/050_annotate/drafted_triples_batch<N>.csv`): it can be deleted and rebuilt. Commit each corrected batch.
- **Add what the draft missed**, above all. Accepting a wrong row is easy (reading the text first, then the rows, limits it); a fact the model missed is unlikely to be added by hand, and if extraction misses it too, nothing counts it as missed: [recall](../docs/terminology.md#7-evaluating-extraction-step-070) comes out higher than it should.
- **Annotate tuning and held-out records the same way.** The tool shows each record's part; it matters only for [component classes](../docs/terminology.md#3-schemas) you'd add to the [schema](../docs/terminology.md#3-schemas) (see extraction's *To do*).
- **When you coin an [entity class](../docs/terminology.md#3-schemas) or [predicate](../docs/terminology.md#3-schemas)**, add it with a one-line definition to the [hand-built schema](../docs/terminology.md#3-schemas) (`annotations/schema_derived_from_manual_annotation.txt`): in the tool, press the button under its [flag](../docs/terminology.md#2-triples). Until then the next drafts reuse it, but the model sees it without a definition, and the tool keeps flagging it (it could be a typo); the tool's page and this [step](../docs/terminology.md#8-the-pipeline)'s [report](../docs/terminology.md#8-the-pipeline) list every such component class.
- **Fix the [errors](../docs/terminology.md#2-triples) and problems** the tool and this step's report point out in the [ground truth](../docs/terminology.md#4-ground-truth-and-samples) (`annotations/ground_truth/`).
- **To rename a component class of the [ground truth vocabulary](../docs/terminology.md#7-evaluating-extraction-step-070), or merge two that mean the same thing**, follow `annotations/README.md`, *Renaming or merging a component class of the ground truth vocabulary*: the tool can't do it, and a file you miss leaves both spellings in the ground truth vocabulary. Everything else the tool can and can't do: `annotations/README.md`, *What the tool can do* and *What the tool can't do*.
- **Report any metric** against this ground truth as such: drafted by a model and corrected by a person, not written from scratch.

## Inputs

| Input | Default | Contents |
|---|---|---|
| `records` | `020_clean/records.jsonl` | 020's cleaned [records](../docs/terminology.md#1-records-and-their-text): the [texts](../docs/terminology.md#1-records-and-their-text). |
| `splits` | `030_split/splits.json` | 030's [ground truth](../docs/terminology.md#4-ground-truth-and-samples) candidates: the [pool](../docs/terminology.md#4-ground-truth-and-samples)'s 999 records still in the catalog, in the pool's order. |
| `hand_schema` | `./annotations/schema_derived_from_manual_annotation.txt` (in Git) | The [hand-built schema](../docs/terminology.md#3-schemas). Shown to the [model](../docs/terminology.md#8-the-pipeline) as the [component classes](../docs/terminology.md#3-schemas) to reuse, together with the component classes [coined](../docs/terminology.md#7-evaluating-extraction-step-070) in the ground truth; every row is checked against the hand-built schema alone, so a coined component class stays flagged until you add it there. |
| `ground_truth` | `./annotations/ground_truth/batch_*.csv` (in Git) | Your ground truth: records in it are never drafted again, every [run](../docs/terminology.md#8-the-pipeline) checks it, and the component classes you coined in it are shown to the model for reuse. Before the first [draft batch](../docs/terminology.md#4-ground-truth-and-samples) is corrected there are no files yet: the [step](../docs/terminology.md#8-the-pipeline) then starts from the top of the pool. |

Draft batches already in 050's output folder are read too: their records are waiting to be corrected, so they're not drafted again.

## Outputs

In `outputs/intermediate_results/050_annotate/`:

**On a rerun:** a new numbered batch is added; a batch already there is never overwritten.

| File | Contents |
|---|---|
| `drafted_triples_batch<N>.csv` | The [draft batch](../docs/terminology.md#4-ground-truth-and-samples): one row per [classed triple](../docs/terminology.md#2-triples), grouped by [record](../docs/terminology.md#1-records-and-their-text), each record's [DESCRIBES row](../docs/terminology.md#2-triples) first. |
| `drafted_triples_batch<N>_details.json` | How the batch was made: the [run](../docs/terminology.md#8-the-pipeline) id, [model](../docs/terminology.md#8-the-pipeline) and [settings](../docs/terminology.md#8-the-pipeline); each record's [pool](../docs/terminology.md#4-ground-truth-and-samples) position, number of [text pieces](../docs/terminology.md#1-records-and-their-text), status (`drafted` or `failed`, with the error), rows, and every item removed (with why); the records passed over while choosing; whether it's still a [fair sample](../docs/terminology.md#4-ground-truth-and-samples). |
| `cache/` | Every model answer, so a rerun pays only for what isn't there yet (see *How to run*). Not listed in the [manifest](../docs/terminology.md#8-the-pipeline). |
| `_manifest.json` | [Run id](../docs/terminology.md#8-the-pipeline), settings, input files and their hashes, output files and their hashes, headline numbers and the [harvest](../docs/terminology.md#1-records-and-their-text) date. Written when a run finishes. |

N is one more than the highest batch number used so far, by a draft batch or a [ground truth](../docs/terminology.md#4-ground-truth-and-samples) file (`batch_000.csv` is 0, so the first draft batch is 1).

The draft batch's columns are the ground truth's, plus two:

| Column | Meaning |
|---|---|
| `id` | The record. |
| `subject`, `subject_class`, `predicate`, `object`, `object_class` | The classed triple, as the model wrote it. |
| `drafted_by` | The model that drafted the row (the setting `model`). The [annotation tool](../docs/terminology.md#4-ground-truth-and-samples) keeps it in the ground truth, and leaves it empty on a row you add; step 060 reads it to warn when it would extract with the same model, or one from the same maker. |
| `source_text` | The passage of the record's [text](../docs/terminology.md#1-records-and-their-text) that states it, as the model copied it. `(record structure)` on the DESCRIBES row. |
| `all_facts_extracted` | Always `0` in a draft: you set it to 1 (the tool's "All [facts](../docs/terminology.md#2-triples) extracted" box) once a record is finished. |
| `flags` | Every check the row failed (see *Checks on each row*). Not kept in the ground truth: the tool recomputes the checks as you edit. |
| `origin` | Where the row came from: `020_clean/records.jsonl#<record id>` (see `helpers/audit.md`). |

Each run also leaves `outputs/reports/<run id>.md` (the [report](../docs/terminology.md#8-the-pipeline): what it read and wrote, its numbers, its warnings) and `outputs/logs/<run id>.log` (everything it did, line by line); how to read them: `helpers/audit.md`.

## Settings

| Setting | Default | What it does | When to change it |
|---|---|---|---|
| `records_per_batch` | 10 | How many [records](../docs/terminology.md#1-records-and-their-text) to draft this [run](../docs/terminology.md#8-the-pipeline). | To draft more or fewer in one sitting. |
| `start_position` | 0 | The [pool](../docs/terminology.md#4-ground-truth-and-samples) position to start from. Records already in the [ground truth](../docs/terminology.md#4-ground-truth-and-samples) or waiting in a [draft batch](../docs/terminology.md#4-ground-truth-and-samples) are always skipped, so 0 means "the first ones not done yet". | To jump ahead in the pool (the [report](../docs/terminology.md#8-the-pipeline) then says the ground truth is no longer a [fair sample](../docs/terminology.md#4-ground-truth-and-samples)). |
| `ids` | empty | Exactly these records instead: ids separated by commas, or the path of a text file with one id per line (a CSV whose first column is the id works too; a header line `id`, blank lines and lines starting with `#` are skipped). They are drafted in the order listed, at most `records_per_batch` of them. | To draft records you choose. |
| `max_chars` | 8000 | A [text](../docs/terminology.md#1-records-and-their-text) longer than this is split into [text pieces](../docs/terminology.md#1-records-and-their-text), one [model call](../docs/terminology.md#8-the-pipeline) each (`common/common_helpers/chunking.py`). | Rarely. |
| `workers` | 4 | Model calls made at the same time. | Lower it if Ask Sage refuses calls for coming too fast. |
| `model` | google-claude-sonnet-5 | The AI [model](../docs/terminology.md#8-the-pipeline) to ask. `py helpers/models.py` lists the models Ask Sage shows your account; a listed one may still refuse you, which the run's first call (the one-line test) finds out for the price of that call. Every cached answer is tied to its model: another model asks everything again, and switching back reuses the earlier answers. | See *Choosing a model* in `docs/running_on_nasa_laptop.md`. |
| `confirm_paid_calls` | true | Stop and ask before the first model call. | `false` for runs with nobody at the keyboard, e.g. the whole pipeline. |

## How to run

From the repository folder, with the environment active (`docs/virtual_environment_setup.md`), on a computer that can reach Ask Sage and has your key in `.env` (`docs/running_on_nasa_laptop.md`):

```
py 050_annotate/run.py --help                            every input and setting, with its default
py 050_annotate/run.py                                   the next 10 records of the pool
py 050_annotate/run.py --records_per_batch 3             the next 3
py 050_annotate/run.py --start_position 200              10 records from pool position 200 on
py 050_annotate/run.py --ids 3122be4c-…,cfd6ec3f-…       exactly these
py 050_annotate/run.py --ids my_ids.txt                  the ids in this file
py 050_annotate/run.py --confirm_paid_calls false        don't ask (unattended runs)
```

**Paying.** Before its first [model call](../docs/terminology.md#8-the-pipeline), 050 logs its plan (how many [records](../docs/terminology.md#1-records-and-their-text), which batch number, how many calls, the [model](../docs/terminology.md#8-the-pipeline)) and waits: Enter starts, anything else stops the [run](../docs/terminology.md#8-the-pipeline) having spent nothing. If the run can't do exactly what you asked, it says so first, above the question (*Step 050 found N warnings:*, then each one, numbered; they're listed under *Checks and warnings*). Its first call is a one-line test that the model name and key work. A run whose answers are all in the cache never asks and never pays. Model calls: one per record, plus one per extra piece of a long [text](../docs/terminology.md#1-records-and-their-text), plus the test call.

**The cache.** Every model answer is kept in `cache/`, under a [fingerprint](../docs/terminology.md#8-the-pipeline) of everything that decided it: the model, the prompt's exact text, and what was sent. A rerun reuses every answer whose fingerprint is unchanged: a failed call isn't kept, so a rerun asks only the calls that failed; editing a prompt asks again exactly the calls that use it; deleting `cache/` (or all of `outputs/`) means paying for every call again.

**Then correct the batch**, with the [annotation tool](../docs/terminology.md#4-ground-truth-and-samples):

```
py helpers/annotate.py
```

Pick the batch at the top of the page. The full steps are in [annotations/README.md](../annotations/README.md).

## How it works

Four [stages](../docs/terminology.md#8-the-pipeline), in `050_annotate/run.py`'s `main()`; stage 2 asks the [model](../docs/terminology.md#8-the-pipeline), the others are code:

1. **Pick the [records](../docs/terminology.md#1-records-and-their-text)** (`records.py`, `pick_records`). By default, the [pool](../docs/terminology.md#4-ground-truth-and-samples)'s records in its order, from `start_position` on, skipping those already in the [ground truth](../docs/terminology.md#4-ground-truth-and-samples), those waiting in a [draft batch](../docs/terminology.md#4-ground-truth-and-samples), and those with no [text](../docs/terminology.md#1-records-and-their-text), until there are `records_per_batch`. With `ids`, those records, skipping the same ones. Anything that makes the batch differ from what you asked becomes a note shown before paying. It also works out whether the ground truth, the waiting drafts and this batch together are still exactly the first records of the pool: a [fair sample](../docs/terminology.md#4-ground-truth-and-samples).
2. **Ask the model** (`draft.py`, `ask_model`). One call per [text piece](../docs/terminology.md#1-records-and-their-text), with the prompt `050_annotate/050_annotate_prompts/draft.txt`: *completeness first* (every [fact](../docs/terminology.md#2-triples), whether or not the [schema](../docs/terminology.md#3-schemas) can express it), then *naming* (the schema's [component classes](../docs/terminology.md#3-schemas) when one fits; otherwise a new one in the same style: [entity classes](../docs/terminology.md#3-schemas) in CamelCase, [predicates](../docs/terminology.md#3-schemas) in UPPER_SNAKE_CASE). Its rules and reply format are in `common/common_prompts/` and shared with [step](../docs/terminology.md#8-the-pipeline) 060, so the ground truth and what 060 extracts are asked for the same way. Every answer goes into `cache/` the moment it arrives. A record with any failed call is left out of the batch, never half drafted.
3. **Build the rows** (`build_rows`, with `common/common_helpers/extraction.py`, shared with 060). The [DESCRIBES row](../docs/terminology.md#2-triples) first, with the entity class the model named for what the title names (`X` if none). Then each [classed triple](../docs/terminology.md#2-triples): an item that can't be one (a missing [subject](../docs/terminology.md#2-triples), predicate or [object](../docs/terminology.md#2-triples), a list where text belongs, …) is removed as *malformed*; the same subject, predicate, object and entity classes again (e.g. from two pieces of a long text) is removed as a *duplicate*. Every row is checked (below). Nothing is removed for failing a check: that's for you to decide.
4. **Check your ground truth** (`check_ground_truth`, with `common/common_helpers/ground_truth.py`). Every row of every ground truth file, for typos (below).

**Then the results** (`results`): the draft batch and its details file are written, never over an existing one; the [report](../docs/terminology.md#8-the-pipeline).

The code: `050_annotate/` holds `run.py` (the [control panel](../docs/terminology.md#8-the-pipeline): inputs, [settings](../docs/terminology.md#8-the-pipeline) and the [moves](../docs/terminology.md#8-the-pipeline), in order); `050_annotate/050_annotate_helpers/` holds `moves.py` (the moves, and writing the results), `records.py` and `draft.py`; `050_annotate/050_annotate_prompts/` holds the prompts (see *Prompts*). Shared with other steps: `common/common_helpers/extraction.py` and `common/common_prompts/` (asking the model and building rows, with 060), `common/common_helpers/validate.py` (the checks), `common/common_helpers/ground_truth.py`, `common/common_helpers/cache.py`, `common/common_helpers/llm.py`.

### Checks on each row

Run against the [record](../docs/terminology.md#1-records-and-their-text)'s **whole** [text](../docs/terminology.md#1-records-and-their-text), including rows from one piece of a long text. They're written in the `flags` column, and the [annotation tool](../docs/terminology.md#4-ground-truth-and-samples) shows them in plain words as you edit.

| Check | Type | Meaning |
|---|---|---|
| `no_source_text` | [error](../docs/terminology.md#2-triples) | The row has no [source text](../docs/terminology.md#1-records-and-their-text). |
| `source_not_in_text` | error | Its source text isn't in the record's text: it may be invented. |
| `describes_undecided` | error | The [DESCRIBES row](../docs/terminology.md#2-triples) has no [entity class](../docs/terminology.md#3-schemas) (`X`): choose one. |
| `describes_subject_not_id` | error | The DESCRIBES row's [subject](../docs/terminology.md#2-triples) isn't the record's id. |
| `subject_not_in_text`, `object_not_in_text` | [flag](../docs/terminology.md#2-triples) | Not found in the text: often reworded ("the instrument" for "MODIS"); fine if on purpose. |
| `subject_not_in_source`, `object_not_in_source` | flag | Not in the row's own source text. Not raised for a subject that is the record's title. |
| `subject_equals_object` | flag | Subject and [object](../docs/terminology.md#2-triples) are the same. |
| `subject_class_not_in_schema`, `object_class_not_in_schema`, `describes_class_not_in_schema` | flag | An entity class the [hand-built schema](../docs/terminology.md#3-schemas) doesn't have: a new one, or a typo. |
| `predicate_not_in_schema` | flag | A [predicate](../docs/terminology.md#3-schemas) the hand-built schema doesn't have. |
| `pattern_not_in_schema` | flag | The predicate is in the [schema](../docs/terminology.md#3-schemas), but never between these two entity classes. |
| `conflicting_classes` | flag | The same subject, predicate, and object appear again with other entity classes; both rows are flagged. |

"In the text" means found once [evened out](../docs/terminology.md#2-triples). Entity classes and predicates are compared with the schema's by [loose match](../docs/terminology.md#3-schemas), so `has version` is `HAS_VERSION`.

## Prompts

| Prompt file | Sent in | Asks the model to |
|---|---|---|
| `050_annotate/050_annotate_prompts/draft.txt` | [stage](../docs/terminology.md#8-the-pipeline) 2, one call per [text piece](../docs/terminology.md#1-records-and-their-text) | list **every** [fact](../docs/terminology.md#2-triples) the [record](../docs/terminology.md#1-records-and-their-text) states (completeness first), using the [hand-built schema](../docs/terminology.md#3-schemas)'s [entity classes](../docs/terminology.md#3-schemas) and [predicates](../docs/terminology.md#3-schemas) where one fits and coining a new one otherwise; the prompt shows the [ground truth vocabulary](../docs/terminology.md#7-evaluating-extraction-step-070): the hand-built schema as written, then, under *ALSO USED IN THE GROUND TRUTH (no definition yet)*, any [component classes](../docs/terminology.md#3-schemas) [coined](../docs/terminology.md#7-evaluating-extraction-step-070) in the [ground truth](../docs/terminology.md#4-ground-truth-and-samples) (with nothing coined, the prompt is unchanged) |
| `common/common_prompts/extraction_rules.txt` | inside `draft.txt` (`$rules`) | follow the rules shared with 060: [subject](../docs/terminology.md#2-triples) and [object](../docs/terminology.md#2-triples) in the record's own words, the shortest [source text](../docs/terminology.md#1-records-and-their-text) copied exactly, one fact per [classed triple](../docs/terminology.md#2-triples), no "is a" classed triples, the kind of thing the title names |
| `common/common_prompts/extraction_reply.txt` | inside `draft.txt` (`$reply`) | reply in the JSON form shared with 060 |

Each prompt is a plain text file: open it to read exactly what the [model](../docs/terminology.md#8-the-pipeline) is told. `$name` marks where the code fills something in. The prompts speak plainly to the model ("facts", "entity classes", "predicates"), explaining any term they use. Editing a prompt is allowed: the next [run](../docs/terminology.md#8-the-pipeline) asks again every call that uses it, and pays for them. The two `common/common_prompts/` files are shared with 060: editing them changes both [steps](../docs/terminology.md#8-the-pipeline).

## Checks and warnings

**Shown before paying**, above the confirmation question (and also in the [report](../docs/terminology.md#8-the-pipeline)'s warnings):

| Message | Meaning | What to do |
|---|---|---|
| *You asked for N records (records_per_batch), but only M are left in the pool from position P on.* | The rest of the [pool](../docs/terminology.md#4-ground-truth-and-samples) is done or waiting. | Nothing, or a lower `start_position`. |
| *N record(s) you listed is not in the catalog / without text / already in the ground truth / waiting in a draft batch to be corrected (batch K), so skipped* | With `ids`: those [records](../docs/terminology.md#1-records-and-their-text) can't or needn't be drafted. | Check for typos; a record waiting in a [draft batch](../docs/terminology.md#4-ground-truth-and-samples) is drafted again only if you delete that draft batch (both its files) before correcting it. |
| *You listed N records that can be drafted, but records_per_batch is M* | Only the first M are drafted now. | Raise `records_per_batch`, or run again for the rest. |
| *start_position (N) is ignored, because ids names the records.* | The two [settings](../docs/terminology.md#8-the-pipeline) can't both apply. | Drop one. |
| *With this batch, the ground truth is no longer the first records of the pool* | Hand-picked records or a jump ahead leave pool records behind. | Nothing, if on purpose. But 070 evaluates only the [fair sample](../docs/terminology.md#4-ground-truth-and-samples) (the pool's first records, with none skipped), so records after the gap are not evaluated until the records before them are annotated too. |
| *Ground truth, record … is in batch_… and batch_…: annotated twice* | A record is annotated twice. It's left out of the [ground truth](../docs/terminology.md#4-ground-truth-and-samples) until fixed. | Keep it in one file. |
| *Ground truth, record … (batch_…): all_facts_extracted is 0 on some rows, 1 on others* | Mixed, so the record doesn't count as finished. | Set it the same on every row (the tool's box does). |
| *Ground truth, record … (batch_…): lines … and … are the same classed triple.*, then each line | [The same classed triple twice](../docs/terminology.md#4-ground-truth-and-samples) in one record (a hand edit). Only one copy can be paired, so evaluation would count the other as missed. Step 070 refuses to run until one is deleted. | Delete one of the two rows. |
| *Ground truth, record … (batch_…): lines … and … state the same subject instance, predicate, and object instance, with different entity classes.*, then each line | Likely one fact given two [entity classes](../docs/terminology.md#3-schemas) by mistake. | If they state one fact, delete the line with the wrong entity classes. |
| *Ground truth, batch_… lacks the column(s) …; not read* | A ground truth file without one of the columns (see `annotations/README.md`). | Add the column. |

**In the report**, under *Warnings*:

| Message | Meaning | What to do |
|---|---|---|
| *N record(s) failed and are not in the batch* | Their [model calls](../docs/terminology.md#8-the-pipeline) failed (after the [model](../docs/terminology.md#8-the-pipeline) client's own retries). | Run the [step](../docs/terminology.md#8-the-pipeline) again: only those are asked again, and every answer already paid for is reused. The next [run](../docs/terminology.md#8-the-pipeline) drafts them first. |
| *No record was drafted, so no batch was written.* | Every call failed. | Check the connection; run again. |
| *N component class(es) used in the ground truth aren't in the hand-built schema, so the model saw them without a definition* | Entity classes or predicates you [coined](../docs/terminology.md#7-evaluating-extraction-step-070) while annotating (or typos). The model was shown them to reuse, but with no definition to go on. | Add each one you mean to keep, with a one-line definition, to the [hand-built schema](../docs/terminology.md#3-schemas) (the [annotation tool](../docs/terminology.md#4-ground-truth-and-samples)'s buttons do it); fix any typo in the ground truth. |
| *N row(s) of the ground truth have something to fix* | [Errors](../docs/terminology.md#2-triples), listed under *Your ground truth* with file and line: an id that isn't in the catalog, a subject, predicate or object partly empty, no [source text](../docs/terminology.md#1-records-and-their-text) or one not in the record's [text](../docs/terminology.md#1-records-and-their-text), a [DESCRIBES row](../docs/terminology.md#2-triples) without an entity class or whose subject isn't the record's id. | Fix them with the tool or any editor. |
| *N of M draft rows have no origin, so they can't be traced to the input they came from* | Should never happen: a code change dropped the field that records where each item came from. | Fix the code before using the output. |

**The step stops** with:

| Message | Meaning | What to do |
|---|---|---|
| *Nothing to draft. …* | No record could be chosen; the reasons follow. | Change the settings: the reasons are listed. |
| *ids names the file …, which doesn't exist* | A typo in the file name. | Fix the file name. |
| *missing input files … (run 020_clean or 030_split first, or pass --records / --splits)* | An input file isn't there: usually an earlier step hasn't run. | Run the steps in order, or pass the file with `--<input>`. |
| *… must be at least N* | A setting is out of range: `records_per_batch` or `workers` under 1, `start_position` under 0, or `max_chars` under 1,000. | Fix the setting. |
| *model must name a model* | The `model` setting is empty. | Give a model's name (`py helpers/models.py` lists them). |
| *Test call to … failed* | Ask Sage refuses you that model, the key is wrong, or Ask Sage can't be reached. Nothing else was called. | If Ask Sage says the model isn't allowed, choose another (`--model`; `py helpers/models.py` lists them). Otherwise check `.env` and the network. |
| *Cancelled. Nothing was spent.* | You declined at the confirmation. | — |
| *Stopped. Calls not yet started were cancelled. Answers already received are kept in the cache; nothing else was written.* | You pressed Ctrl+C while the model calls ran. | Run the step again: the answers already received are reused, not paid for again. |
| *Set ASKSAGE_EMAIL and ASKSAGE_API_KEY (e.g. in .env).* | The Ask Sage credentials aren't set, so no model can be called. | Put them in `.env` (see `docs/running_on_nasa_laptop.md`). |

## Audit trail

- **Prompts.** The [report](../docs/terminology.md#8-the-pipeline)'s *Prompts* section lists every prompt the [run](../docs/terminology.md#8-the-pipeline) filled in, each with a [fingerprint](../docs/terminology.md#8-the-pipeline) (sha256) of its exact text, so the prompt behind any answer is known even if the prompt file was edited later (`_manifest.json` keeps the full fingerprints).
- **[Log](../docs/terminology.md#8-the-pipeline).** `outputs/logs/<run id>.log` records the command line, the [settings](../docs/terminology.md#8-the-pipeline), the git commit, every [model call](../docs/terminology.md#8-the-pipeline)'s retries, each [move](../docs/terminology.md#8-the-pipeline)'s duration, each output file's hash and, on failure, the full traceback.
- **[Origin](../docs/terminology.md#8-the-pipeline).** Each row of a [draft batch](../docs/terminology.md#4-ground-truth-and-samples) has an `origin` column naming its [record](../docs/terminology.md#1-records-and-their-text) in 020's `records.jsonl`. The [ground truth](../docs/terminology.md#4-ground-truth-and-samples) files carry none: they are made by a person, so a trace stops there.
- **Trace.** `py helpers/audit.py <record id>` follows a record back through every [step](../docs/terminology.md#8-the-pipeline)'s output to the 010 [batch file](../docs/terminology.md#1-records-and-their-text) and the API request that first returned it (`helpers/audit.md`). It searches only the files a step's last run wrote, so for 050 the newest draft batch; a record in an older one is found through 030's `splits.json`.

## Known limits

- **Not yet run with the real [model](../docs/terminology.md#8-the-pipeline).** As of 2026-09-29, 050 has been tested only with a stand-in for the model, because Ask Sage can't be reached from the laptop it was built on. Numbers in this guide come from the catalog, the code or the stand-in, not from a real [run](../docs/terminology.md#8-the-pipeline).
- **The [schema](../docs/terminology.md#3-schemas) in the prompt is the hand-built one**, whichever schema 060 ends up using: the [ground truth](../docs/terminology.md#4-ground-truth-and-samples) should record every [fact](../docs/terminology.md#2-triples) in stable [component classes](../docs/terminology.md#3-schemas), not only what one schema can express.
- **A [record](../docs/terminology.md#1-records-and-their-text) deleted from a corrected batch is not drafted again**: it's still in its [draft batch](../docs/terminology.md#4-ground-truth-and-samples), which is how 050 knows it was seen. To redraft it, list it with `ids` after removing it from that draft batch file.
- **The model varies.** Rerunning with an empty cache can draft different rows; the cache makes a rerun reproducible.
