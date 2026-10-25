# 050_annotate

Terms ([triple instance](../docs/terminology.md#2-triples), [entity class](../docs/terminology.md#3-schemas), [ground truth](../docs/terminology.md#4-ground-truth-and-samples), [drafted batch](../docs/terminology.md#4-ground-truth-and-samples), [fair sample](../docs/terminology.md#4-ground-truth-and-samples), …) are as defined in [docs/terminology.md](../docs/terminology.md), especially section *Ground truth and samples*.

## Purpose

Drafts [classed triples](../docs/terminology.md#2-triples), the [drafted triples](../docs/terminology.md#4-ground-truth-and-samples), for you to correct into [ground truth](../docs/terminology.md#4-ground-truth-and-samples). A [model](../docs/terminology.md#8-the-pipeline) reads the next [records](../docs/terminology.md#1-records-and-their-text) of the [ground truth candidates pool](../docs/terminology.md#4-ground-truth-and-samples) and lists **every [fact](../docs/terminology.md#2-triples) each record states**, as classed triples. It uses the [ground truth schema](../docs/terminology.md#3-schemas)'s [component classes](../docs/terminology.md#3-schemas), and any you [coined](../docs/terminology.md#3-schemas) while annotating, where they fit, and coins new ones where they don't: leaving a fact out is worse than a new [entity class](../docs/terminology.md#3-schemas) or [predicate](../docs/terminology.md#3-schemas). Code adds each record's [describes triple](../docs/terminology.md#2-triples), removes [the same classed triple twice](../docs/terminology.md#4-ground-truth-and-samples) and replies that aren't classed triples, and checks every drafted triple against the record's [text](../docs/terminology.md#1-records-and-their-text) and the ground truth [schema](../docs/terminology.md#3-schemas).

Each [run](../docs/terminology.md#8-the-pipeline) writes one numbered **[drafted batch](../docs/terminology.md#4-ground-truth-and-samples)**. You correct it with the [annotation tool](../docs/terminology.md#4-ground-truth-and-samples) (`py helpers/annotate.py`), which saves it into `annotations/ground_truth/` as the ground truth file with the same number. No [step](../docs/terminology.md#8-the-pipeline) ever writes there.

Each run also checks your ground truth files for [errors](../docs/terminology.md#2-triples) (see *Your ground truth* in the [report](../docs/terminology.md#8-the-pipeline)).

## To do

What to do, and when, is in [`docs/upkeep.md`](../docs/upkeep.md), one page for every step; `py run_pipeline.py --status` (or the [annotation tool](../docs/terminology.md#4-ground-truth-and-samples)'s home page) lists what is waiting now. For this step, in short:

- Choose the model before the real runs ([*Before the first run*](../docs/upkeep.md#before-the-first-run)).
- Correct each [drafted batch](../docs/terminology.md#4-ground-truth-and-samples) in the annotation tool, in pool order (within each part), adding what its [drafted triples](../docs/terminology.md#4-ground-truth-and-samples) missed ([*After step 050 drafts a batch*](../docs/upkeep.md#after-step-050-drafts-a-batch)). `py run_pipeline.py` drafts the next drafted batch only once none is waiting (a drafted batch not opened yet, or a [ground truth](../docs/terminology.md#4-ground-truth-and-samples) file with a record not finished), while `py 050_annotate/run.py` alone drafts the next records anyway.
- Add each [entity class](../docs/terminology.md#3-schemas) or predicate you coin to the [ground truth schema](../docs/terminology.md#3-schemas), and fix every ✖ ([*While annotating*](../docs/upkeep.md#while-annotating)).
## Inputs

| Input | Default | Contents |
|---|---|---|
| `records` | `020_clean/records.jsonl` | 020's cleaned [records](../docs/terminology.md#1-records-and-their-text): the [texts](../docs/terminology.md#1-records-and-their-text). |
| `splits` | `030_split/splits.json` | 030's [ground truth](../docs/terminology.md#4-ground-truth-and-samples) candidates: the [pool](../docs/terminology.md#4-ground-truth-and-samples)'s 999 records still in the catalog, in the pool's order. |
| `ground_truth_schema` | `./annotations/ground_truth_schema.txt` (in Git) | The [ground truth schema](../docs/terminology.md#3-schemas). Shown to the [model](../docs/terminology.md#8-the-pipeline) as the [component classes](../docs/terminology.md#3-schemas) to reuse, together with the component classes [coined](../docs/terminology.md#3-schemas) in the ground truth, and the patterns the ground truth uses that its file doesn't list; every [drafted triple](../docs/terminology.md#4-ground-truth-and-samples) is checked against the ground truth schema alone, so a coined component class is flagged in the [drafted batch](../docs/terminology.md#4-ground-truth-and-samples), and is an error in the [annotation tool](../docs/terminology.md#4-ground-truth-and-samples) and a stop in step 070 once a [finished record](../docs/terminology.md#4-ground-truth-and-samples) uses it, until you add it there. |
| `ground_truth` | `./annotations/ground_truth/batch_*.csv` (in Git) | Your ground truth: records in it are never drafted again, every [run](../docs/terminology.md#8-the-pipeline) checks it, and the component classes you coined in it are shown to the model for reuse. Before the first drafted batch is corrected there are no files yet: the [step](../docs/terminology.md#8-the-pipeline) then starts from the top of the pool. |

Drafted batches already in 050's output folder are read too: their records are waiting to be corrected, so they're not drafted again.

## Outputs

In `outputs/intermediate_results/050_annotate/`:

**On a rerun:** a new [drafted batch](../docs/terminology.md#4-ground-truth-and-samples) is added; a drafted batch already there is never overwritten. `cache/` keeps every answer, so a run stopped partway pays again only for what it didn't get.

| File | Contents |
|---|---|
| `drafted_triples_batch<N>.csv` | The drafted batch: one row per [classed triple](../docs/terminology.md#2-triples), grouped by [record](../docs/terminology.md#1-records-and-their-text), each record's [describes triple](../docs/terminology.md#2-triples) first. |
| `drafted_triples_batch<N>_details.json` | How the batch was made: the [run](../docs/terminology.md#8-the-pipeline) id, [model](../docs/terminology.md#8-the-pipeline), and [settings](../docs/terminology.md#8-the-pipeline); each record's [pool](../docs/terminology.md#4-ground-truth-and-samples) position, number of [text pieces](../docs/terminology.md#1-records-and-their-text), status (`drafted` or `failed`, with the error), [drafted triples](../docs/terminology.md#4-ground-truth-and-samples), and every item removed (with why); the records passed over while choosing; whether it's still a [fair sample](../docs/terminology.md#4-ground-truth-and-samples). |
| `cache/` | Every model answer, so a rerun pays only for what isn't there yet (see *How to run*). Not listed in the [manifest](../docs/terminology.md#8-the-pipeline). |
| `_manifest.json` | [Run id](../docs/terminology.md#8-the-pipeline), settings, input files and their hashes, output files and their hashes, headline numbers, and the [harvest](../docs/terminology.md#1-records-and-their-text) date. Written when a run finishes. |

N is one more than the highest batch number used so far, by a drafted batch or a [ground truth](../docs/terminology.md#4-ground-truth-and-samples) file (`batch_000.csv` is 0, so the first drafted batch is 1).

The drafted batch's columns are the ground truth's, plus two:

| Column | Meaning |
|---|---|
| `id` | The record. |
| `subject`, `subject_class`, `predicate`, `object`, `object_class` | The classed triple, as the model wrote it. |
| `drafted_by` | The model that drafted the row (the setting `model`). The [annotation tool](../docs/terminology.md#4-ground-truth-and-samples) keeps it in the ground truth, and leaves it empty on a row you add; step 060 reads it to warn when it would extract with the same model, or one from the same maker. |
| `source_text` | The passage of the record's [text](../docs/terminology.md#1-records-and-their-text) that states it, as the model copied it. `(record structure)` on the describes triple. |
| `all_facts_extracted` | Always `0` in a drafted batch: you set it to 1 (the tool's "All [facts](../docs/terminology.md#2-triples) extracted" box) once a record is finished. |
| `flags` | Every check the row failed (see *Checks on each row*). Not kept in the ground truth: the tool recomputes the checks as you edit. |
| `origin` | Where the row came from: `020_clean/records.jsonl#<record id>` (see `helpers/audit.md`). |

Each run also leaves `outputs/reports/<run id>.md` (the [report](../docs/terminology.md#8-the-pipeline): what it read and wrote, its numbers, its warnings) and `outputs/logs/<run id>.log` (everything it did, line by line); how to read them: `helpers/audit.md`. A run in which a [model call](../docs/terminology.md#8-the-pipeline) failed also leaves `outputs/logs/<run id>_failed_calls.jsonl`, the failed-call record: each failed call, why, and what to change (`docs/running_on_nasa_laptop.md`, section 5).

## Settings

| Setting | Default | What it does | When to change it |
|---|---|---|---|
| `records_per_batch` | 10 | How many [records](../docs/terminology.md#1-records-and-their-text) to draft this [run](../docs/terminology.md#8-the-pipeline). | To draft more or fewer in one sitting. |
| `start_position` | 0 | The [pool](../docs/terminology.md#4-ground-truth-and-samples) position to start from. Records already in the [ground truth](../docs/terminology.md#4-ground-truth-and-samples) or waiting in a [drafted batch](../docs/terminology.md#4-ground-truth-and-samples) are always skipped, so 0 means "the first ones not done yet". | To jump ahead in the pool (the [report](../docs/terminology.md#8-the-pipeline) then says the ground truth is no longer a [fair sample](../docs/terminology.md#4-ground-truth-and-samples)). |
| `part` | tuning | Which part of the pool to draft from: `tuning`, `held-out`, or `both` (the pool's order, restricted to that part; `start_position` and the skipping below work as before). The default is tuning, because the pipeline is improved on [tuning records](../docs/terminology.md#7-evaluating-extraction-step-070): [held-out records](../docs/terminology.md#7-evaluating-extraction-step-070) are drafted only when you choose, e.g. when the [tuning part](../docs/terminology.md#7-evaluating-extraction-step-070) is done and you want the held-out numbers. Each part's first records in pool order are a fair sample of the part, so drafting one part leaves the other fair. Ignored when `ids` is set. | To draft held-out records (`held-out`), or both parts in pool order (`both`, the earlier behaviour). |
| `ids` | empty | Exactly these records instead (how to write them: `docs/running_on_nasa_laptop.md`, *Settings several steps share*). They are drafted in the order listed, at most `records_per_batch` of them. | To draft records you choose. |
| `max_chars` | 8000 | A [text](../docs/terminology.md#1-records-and-their-text) longer than this is split into [text pieces](../docs/terminology.md#1-records-and-their-text), one [model call](../docs/terminology.md#8-the-pipeline) each (`common/common_helpers/chunking.py`). | Rarely. |
| `workers` | 4 | Model calls made at the same time. | Lower it if the service refuses calls for coming too fast. |
| `service` | litellm | The service that reaches the model (its values, and what each needs: `docs/running_on_nasa_laptop.md`, *Settings several steps share*). | See *Choosing a model* in `docs/running_on_nasa_laptop.md`. |
| `model` | gemini-2.5-pro | The AI [model](../docs/terminology.md#8-the-pipeline) to ask: by default from another maker than 060's (claude-opus-5.5), so the facts one model misses aren't missing from both the ground truth and the extraction. How to name one, and what changing it costs: `docs/running_on_nasa_laptop.md`, *Settings several steps share*. | See *Choosing a model* in `docs/running_on_nasa_laptop.md`. |
| `thinking` | low | How much a model that thinks before it answers may think (its values, and which models it is sent to: `docs/running_on_nasa_laptop.md`, *Settings several steps share*). | When the report's warning says an answer was cut off with most of its tokens spent thinking. See *The thinking cap* in `docs/running_on_nasa_laptop.md`, section 5. |
| `confirm_paid_calls` | true | Stop and ask before the first model call. | `false` for runs with nobody at the keyboard, e.g. the whole pipeline. |

## How to run

From the repository folder, with the environment active (`docs/virtual_environment_setup.md`), on a computer that can reach the model's service and has its key in `.env` (`docs/running_on_nasa_laptop.md`):

```
py 050_annotate/run.py --help                            every input and setting, with its default
py 050_annotate/run.py                                   the next 10 records of the pool
py 050_annotate/run.py --records_per_batch 3             the next 3
py 050_annotate/run.py --start_position 200              10 records from pool position 200 on
py 050_annotate/run.py --ids 3122be4c-…,cfd6ec3f-…       exactly these
py 050_annotate/run.py --ids my_ids.txt                  the ids in this file
py 050_annotate/run.py --confirm_paid_calls false        don't ask (unattended runs)
```

**Paying.** Before its first [model call](../docs/terminology.md#8-the-pipeline), 050 logs its plan (how many [records](../docs/terminology.md#1-records-and-their-text), which batch number, how many calls, the [model](../docs/terminology.md#8-the-pipeline)) and waits: Enter starts (the answers that go ahead, and the ones that stop it having spent nothing: `docs/running_on_nasa_laptop.md`, section 5). If the [run](../docs/terminology.md#8-the-pipeline) can't do exactly what you asked, it says so first, above the question (*Step 050 found N warnings:*, then each one, numbered; they're listed under *Checks and warnings*). Its first call is the [test call](../docs/terminology.md#8-the-pipeline), which checks that the model name and key work. A run whose answers are all in the cache never asks and never pays. Model calls: one per record, plus one per extra [text](../docs/terminology.md#1-records-and-their-text) piece, plus the test call.

**The cache.** Every model answer is kept in `cache/`, under a [fingerprint](../docs/terminology.md#8-the-pipeline) of everything that decided it (every part, and what isn't one: `docs/running_on_nasa_laptop.md`, section 5, *What a saved answer depends on*). A rerun reuses every answer whose fingerprint is unchanged: a failed call isn't kept, so a rerun asks only the calls that failed (but an answer cut off at the length limit is kept as cut off, and not asked again with the same settings: *A cut-off isn't paid for twice* in `docs/running_on_nasa_laptop.md`, section 5). Only an answer of the shape the step reads is kept (a `"triples"` list): one of another shape is asked once more, saying what was wrong, then counts as a failed call; one kept by an earlier version of the code is asked again, and the report's warnings name the cache file (`shape_error` in `common/common_helpers/extraction.py`, `Cache.get` in `common/common_helpers/cache.py`). Editing a prompt asks again exactly the calls that use it (a file of `common/common_prompts/`: 040's, 050's, and 060's); deleting `cache/` (or all of `outputs/`) means paying for every call again.

**Then correct the [drafted batch](../docs/terminology.md#4-ground-truth-and-samples)**, with the [annotation tool](../docs/terminology.md#4-ground-truth-and-samples):

```
py helpers/annotate.py
```

Pick the drafted batch at the top of the page. The full steps are in [annotations/README.md](../annotations/README.md).

## How it works

Four [stages](../docs/terminology.md#8-the-pipeline), in `050_annotate/run.py`'s `main()`; stage 2 asks the [model](../docs/terminology.md#8-the-pipeline), the others are code:

1. **Pick the [records](../docs/terminology.md#1-records-and-their-text)** (`records.py`, `pick_records`). By default, the [pool](../docs/terminology.md#4-ground-truth-and-samples)'s records of the part(s) named by `part` (tuning unless you change it) in pool order, from `start_position` on, skipping those already in the [ground truth](../docs/terminology.md#4-ground-truth-and-samples), those waiting in a [drafted batch](../docs/terminology.md#4-ground-truth-and-samples), and those with no [text](../docs/terminology.md#1-records-and-their-text), until there are `records_per_batch`. With `ids`, those records, skipping the same ones. Anything that makes the drafted batch differ from what you asked becomes a note shown before paying; so does a note naming the [pool positions](../docs/terminology.md#4-ground-truth-and-samples) this run drafts and the part. It also works out, for each part, whether the ground truth, the drafted batches waiting to be corrected, and this batch together are still exactly the first records of that part in pool order: a [fair sample](../docs/terminology.md#4-ground-truth-and-samples) of the part.
2. **Ask the model** (`draft.py`, `ask_model`). One call per [text piece](../docs/terminology.md#1-records-and-their-text), with the prompt `050_annotate/050_annotate_prompts/draft.txt`: *completeness first* (every [fact](../docs/terminology.md#2-triples), whether or not the [schema](../docs/terminology.md#3-schemas) can express it), then *naming* (the schema's [component classes](../docs/terminology.md#3-schemas) when one fits; otherwise a new one in the same style: [entity classes](../docs/terminology.md#3-schemas) in CamelCase, [predicates](../docs/terminology.md#3-schemas) in UPPER_SNAKE_CASE). Its rules and reply format are in `common/common_prompts/` and shared with [step](../docs/terminology.md#8-the-pipeline) 060, so the [drafted triples](../docs/terminology.md#4-ground-truth-and-samples) and what 060 extracts are asked for the same way. Every answer goes into `cache/` the moment it arrives. A record with any failed call is left out of the batch, never half drafted.
3. **Build the rows** (`build_rows`, with `common/common_helpers/extraction.py`, shared with 060). The [describes triple](../docs/terminology.md#2-triples) first, with the [describes class](../docs/terminology.md#2-triples) the model named (`X` if none). Then each [classed triple](../docs/terminology.md#2-triples): an item that can't be one is removed as *malformed* (every way: `malformed` under *extracted triple* in the terminology); [the same classed triple twice](../docs/terminology.md#4-ground-truth-and-samples) (e.g. from two text pieces of one text) keeps one copy, the first that passes the checks below (the first copy when none does), and the others are removed as *duplicate*. Every row is checked (below), copies included. Nothing is removed for failing a check: that's for you to decide.
4. **Check your ground truth** (`check_ground_truth`, with `common/common_helpers/ground_truth.py`). Every row of every ground truth file, for errors (below).

**Then the results** (`results`): the drafted batch and its details file are written, never over an existing one; the [report](../docs/terminology.md#8-the-pipeline). Its subsection *What this run worked on* (section *Results*) ends with a table, *Classed triples per text*: for each text (one record's text), how many drafted triples the model listed, its describes triple not counted, given as the number of texts, min, max, mean, median, total, and texts with none. It has one row, since 050 removes none for a check (you decide, in the [annotation tool](../docs/terminology.md#4-ground-truth-and-samples)). A classed triple two text pieces of a text both state counts once; items that weren't [triple instances](../docs/terminology.md#2-triples), and texts whose [model call](../docs/terminology.md#8-the-pipeline) failed, aren't counted. The headline, and `_manifest.json`, also give the total and its mean per text (`drafted triples`).

The code: `050_annotate/` holds `run.py` (the [control panel](../docs/terminology.md#8-the-pipeline): inputs, [settings](../docs/terminology.md#8-the-pipeline), and the [moves](../docs/terminology.md#8-the-pipeline), in order); `050_annotate/050_annotate_helpers/` holds `moves.py` (the moves, and writing the results), `records.py`, and `draft.py`; `050_annotate/050_annotate_prompts/` holds the prompts (see *Prompts*). Shared with other steps: `common/common_helpers/extraction.py` and `common/common_prompts/` (asking the model and building rows, with 060), `common/common_helpers/validate.py` (the checks), `common/common_helpers/ground_truth.py`, `common/common_helpers/cache.py`, `common/common_helpers/llm.py`.

### Checks on each row

Run against the [record](../docs/terminology.md#1-records-and-their-text)'s **whole** [text](../docs/terminology.md#1-records-and-their-text), including [drafted triples](../docs/terminology.md#4-ground-truth-and-samples) from one [text piece](../docs/terminology.md#1-records-and-their-text). Step 050 writes them in the [drafted batch](../docs/terminology.md#4-ground-truth-and-samples)'s `flags` column. The [annotation tool](../docs/terminology.md#4-ground-truth-and-samples) runs the same checks as you edit and shows each in plain words, as ✖ (an error: fix it) or ⚑ (a flag: worth a look), with two differences: the four `…_not_in_schema` checks are ✖ there (step 070 stops on a [finished record](../docs/terminology.md#4-ground-truth-and-samples) that uses a [component class](../docs/terminology.md#3-schemas) the [ground truth schema](../docs/terminology.md#3-schemas) lacks, so add it, or fix the typo), and `conflicting_classes` is shown at the top of the page, among the [ground truth](../docs/terminology.md#4-ground-truth-and-samples)'s problems (*… state the same subject instance, predicate, and object instance, with different entity classes*), not on the row. The rows marked *tool* are the tool's own. Stage 4, 050's check of your ground truth (in the report), runs the errors of the table except `empty`: the two marked *stage 4* are its own.

| Check | Type | Meaning |
|---|---|---|
| `no_source_text` | [error](../docs/terminology.md#2-triples) | The row has no [source text](../docs/terminology.md#1-records-and-their-text). |
| `source_not_in_text` | error | Its source text isn't in the record's text: it may be invented. |
| `describes_undecided` | error | The [describes triple](../docs/terminology.md#2-triples) has no [entity class](../docs/terminology.md#3-schemas) (`X`): choose one. |
| `describes_subject_not_id` | error | The describes triple's [subject](../docs/terminology.md#2-triples) instance isn't the record's id. |
| `id_not_in_records` | error (*stage 4*) | The row's id isn't a record of the catalog (a typo, or a record since removed). |
| `incomplete` | error (*stage 4*) | [Subject instance](../docs/terminology.md#2-triples), predicate, or [object instance](../docs/terminology.md#2-triples) is empty, but not all three. A row with all three empty is a record annotated as stating no facts: fine. |
| `empty` | error (*tool*) | Subject instance, predicate, or object instance is empty, on a row of the page. How it relates to `incomplete`: the same check on the page, where a row with all three empty is one not filled in yet (never saved: a save leaves blank rows out, and writes one only for a record with no other row), so it is `empty` too; in a ground truth file, that row means "states no facts", so `incomplete` leaves it out. A row is never both. |
| `subject_not_in_text`, `object_not_in_text` | [flag](../docs/terminology.md#2-triples) | Not found in the text. Found means: its words, [evened out](../docs/terminology.md#2-triples), are in the text as whole words in that order (punctuation inside counting as a space), or, for an instance that is wholly a quantity, the same quantity however written. So not found has these causes, all of them: reworded ("the instrument" for "MODIS"); an acronym expanded or shortened; words in another order or form (a plural, another spelling); a piece of a word ("Aqua" inside "Aquarius") or of a number ("5 minutes" inside "25 minutes"); words joined from separate places (rule 12 of the [annotation guidelines](../docs/terminology.md#4-ground-truth-and-samples) copies a list's shared words onto each item, and rule 13 gives one thing one wording within a record, so such an instance is rightly flagged); or words that aren't in the record at all. Fine if on purpose. |
| `subject_not_in_source`, `object_not_in_source` | flag | Not in the row's own source text. Not raised for a subject instance that is the record's title. |
| `subject_equals_object` | flag | Subject instance and [object](../docs/terminology.md#2-triples) instance are the same. |
| `dataset_subject_not_title` | flag | The [subject class](../docs/terminology.md#2-triples) is Dataset, but the subject instance isn't the record's title (compared evened out: case and spacing don't matter). It may be this record's own dataset worded differently (rule 13 of the annotation guidelines, one thing one wording): then use the title. Or it is another dataset, such as an input ("radiance data", "pixels"): keep it, nothing to do. Not raised on the describes triple. One shared check on every row: the ground truth in the tool, the drafted triples of 050, and the [extracted triples](../docs/terminology.md#6-extracting-with-a-schema-step-060) of 060, so a model's wording is judged as yours is. |
| `subject_class_not_in_schema`, `object_class_not_in_schema`, `describes_class_not_in_schema` | flag | A coined entity class: a new one, or a typo. |
| `predicate_not_in_schema` | flag | A coined [predicate](../docs/terminology.md#3-schemas): a new one, or a typo. |
| `pattern_not_in_schema` | flag | The predicate is in the [schema](../docs/terminology.md#3-schemas), but the ground truth schema has no pattern with this subject class, predicate, and [object class](../docs/terminology.md#2-triples). |
| `pattern_not_pinned` | flag | The predicate is a [pinned predicate](../docs/terminology.md#3-schemas) of the ground truth schema, and its "only:" line doesn't list this subject class and object class. |
| `conflicting_classes` | flag | The same subject instance, predicate, and object instance appear in another row with a different subject class or object class; both rows are flagged. |
| `not_connected` | flag (*tool*) | No chain of ground truth triples links this one to the catalog entry (the describes triple and the title) (`annotations/guidelines.md`, *Finishing a record*). |

How the checks relate: a row gets those of the first case that applies, in this order. Stage 4 (the ground truth's files): an id not in the catalog gets `id_not_in_records` alone; a row with all three empty gets none (a record stating no facts); a row with some empty, `incomplete` alone; the describes triple, its `describes_…` checks; any other row, every other check that applies. The tool: the describes triple, its `describes_…` checks; a row with any of the three empty, `empty` alone; any other row, every other check that applies. Among those, `no_source_text` and `source_not_in_text` exclude each other (the second needs a source text), and so do the `…_not_in_source` flags, which never come with `no_source_text`; any other two can come together.

"In the text" means found once evened out. Entity classes and predicates are compared with the schema's by [loose match](../docs/terminology.md#3-schemas), so `has version` is `HAS_VERSION`.

## Prompts

| Prompt file | Sent in | Asks the model to |
|---|---|---|
| `050_annotate/050_annotate_prompts/draft.txt` | [stage](../docs/terminology.md#8-the-pipeline) 2, one call per [text piece](../docs/terminology.md#1-records-and-their-text) | list **every** [fact](../docs/terminology.md#2-triples) the [record](../docs/terminology.md#1-records-and-their-text) states (completeness first), using the [ground truth schema](../docs/terminology.md#3-schemas)'s [entity classes](../docs/terminology.md#3-schemas) and [predicates](../docs/terminology.md#3-schemas) where one fits and coining a new one otherwise; the prompt shows the ground truth schema: the ground truth schema as written, then, under *ALSO USED IN THE GROUND TRUTH (no definition yet)*, any [component classes](../docs/terminology.md#3-schemas) [coined](../docs/terminology.md#3-schemas) in the [ground truth](../docs/terminology.md#4-ground-truth-and-samples) (with nothing coined, the prompt is unchanged), then, under *MORE PATTERNS THE GROUND TRUTH USES (subject class -> object class)*, any patterns the ground truth uses that the ground truth schema's file doesn't list (with none, nothing is added) |
| `common/common_prompts/extraction_rules.txt` | inside `draft.txt` (`$rules`) | follow the rules shared with 040 and 060, the model's copy of the [annotation guidelines](../docs/terminology.md#4-ground-truth-and-samples): what counts as a fact and how to write a [classed triple](../docs/terminology.md#2-triples). The rules themselves: `annotations/guidelines.md` (the model's copy: this file; a test keeps the two in step) |
| `common/common_prompts/extraction_reply.txt` | inside `draft.txt` (`$reply`) | reply in the JSON form shared with 040 and 060, each classed triple with its entity classes |

Each prompt is a plain text file: open it to read exactly what the [model](../docs/terminology.md#8-the-pipeline) is told. `$name` marks where the code fills something in. The prompts speak plainly to the model ("facts", "entity classes", "predicates"), explaining any term they use. Editing a prompt is allowed: the next [run](../docs/terminology.md#8-the-pipeline) asks again every call that uses it, and pays for them. The two `common/common_prompts/` files are shared with 060: editing them changes both [steps](../docs/terminology.md#8-the-pipeline). Their examples are invented (`060_extract/060_extract.md`, *Prompts*, says why).

## Checks and warnings

Messages several steps share are in [`docs/running_on_nasa_laptop.md`, section 7, *Shared warnings and stops*](../docs/running_on_nasa_laptop.md#shared-warnings-and-stops); below are this step's own.

**Shown before paying**, above the confirmation question (and also in the [report](../docs/terminology.md#8-the-pipeline)'s warnings):

| Message | Meaning | What to do |
|---|---|---|
| *You asked for N records (records_per_batch), but only M are left in the pool from position P on.* | The rest of the [pool](../docs/terminology.md#4-ground-truth-and-samples) is already in the [ground truth](../docs/terminology.md#4-ground-truth-and-samples) or waiting in a [drafted batch](../docs/terminology.md#4-ground-truth-and-samples). | Nothing, or a lower `start_position`. |
| *N record(s) you listed is not in the catalog / without text / already in the ground truth / waiting in a drafted batch to be corrected (batch K), so skipped* | With `ids`: those [records](../docs/terminology.md#1-records-and-their-text) can't or needn't be drafted. Each is counted under the first reason that applies, in the message's order (code: `usable` in `records.py`, which also skips pool records the same way). | Check for typos; a record waiting in a drafted batch is drafted again only if you delete that drafted batch (both its files) before correcting it. |
| *You listed N records that can be drafted, but records_per_batch is M* | Only the first M are drafted now. | Raise `records_per_batch`, or run again for the rest. |
| *start_position (N) is ignored, because the setting ids names the records* | The two [settings](../docs/terminology.md#8-the-pipeline) can't both apply. | Nothing to do if you meant the ids; to draft from a [pool position](../docs/terminology.md#4-ground-truth-and-samples) instead, leave `ids` empty. |
| *With this drafted batch, the ground truth is no longer the first records of the tuning (or held-out) part of the pool* | Hand-picked records or a jump ahead leave records of that part behind. | Nothing, if on purpose. But 070 evaluates only the [fair sample](../docs/terminology.md#4-ground-truth-and-samples) of each part (the part's first records in pool order, with none of the part skipped), so records of that part after the gap are not evaluated until the records before them are finished too. The other part is not affected. |

**In the report**, under *Warnings*:

| Message | Meaning | What to do |
|---|---|---|
| *N record(s) failed: a model call for one of their text pieces failed, so each is left out of the batch whole* | A [model call](../docs/terminology.md#8-the-pipeline) for a [text piece](../docs/terminology.md#1-records-and-their-text) of those records failed (after the model client's own retries), so each is left out whole, never half drafted. The report gives each record's id and why. | Run the step again: only the failed pieces are asked again, and every answer already paid for is reused. The next run drafts them first. An answer cut off at the length limit isn't asked again with the same settings: first change the setting the warning names (`docs/running_on_nasa_laptop.md`, section 7). Each failed call is described in `outputs/logs/<run id>_failed_calls.jsonl`. |
| *No record was drafted, so no drafted batch was written.* | Every record chosen had a model call fail, for any reason a call can fail: an error from the service (after the retries: `docs/running_on_nasa_laptop.md`, section 7, *trying again in N s*), a cut-off, no answer within `READ_TIMEOUT`, no usable answer, or an answer that twice wasn't JSON of the shape asked for. The warning before it says why for each record. | Fix the cause it names (e.g. the connection, or `--thinking low` for cut-offs); run again. |
| *N component class(es) used in the ground truth aren't in the ground truth schema, so the model saw them without a definition* | [Entity classes](../docs/terminology.md#3-schemas) or predicates you [coined](../docs/terminology.md#3-schemas) while annotating (or typos). The model was shown them to reuse, but with no definition to go on. | Add each one you mean to keep, with a one-line definition, to the [ground truth schema](../docs/terminology.md#3-schemas) (the [annotation tool](../docs/terminology.md#4-ground-truth-and-samples)'s buttons do it); fix any typo in the ground truth. |
| *N ground truth triple(s) or [describes triple](../docs/terminology.md#2-triples)(s) have an error to fix* | [Errors](../docs/terminology.md#2-triples) of stage 4 (*Checks on each row*), listed under *Your ground truth* with file and line. | Fix them with the tool or any editor. |
| *N of M rows of the drafted batch have no origin, so they can't be traced to the input they came from* | Should never happen: a code change dropped the field that records where each item came from. | Fix the code before using the output. |

**The step stops** with:

| Message | Meaning | What to do |
|---|---|---|
| *Nothing to draft: none of the records chosen can be drafted …* | No record could be chosen; the reasons follow. | Change the settings: the reasons are listed. |
| *missing input files, so the step can't run:*, then one line per missing file, e.g. *records: … (run `py 020_clean/run.py` first, or give another file with --records)*, or *ground_truth_schema: … (give the file with --ground_truth_schema)* | An input file isn't there: usually an earlier step hasn't run. | Run the steps in order, or pass the file with `--<input>`. |
| *… must be at least N* | A setting is out of range: `records_per_batch` or `workers` under 1, `start_position` under 0, or `max_chars` under 1,000. | Fix the setting. |

## Audit trail

- **Prompts.** The [report](../docs/terminology.md#8-the-pipeline)'s *Prompts* section lists every prompt the [run](../docs/terminology.md#8-the-pipeline) filled in, each with a [fingerprint](../docs/terminology.md#8-the-pipeline) (sha256) of its exact text, so the prompt behind any answer is known even if the prompt file was edited later (`_manifest.json` keeps the full fingerprints).
- **[Log](../docs/terminology.md#8-the-pipeline).** `outputs/logs/<run id>.log` records the command line, the [settings](../docs/terminology.md#8-the-pipeline), the git commit, every [model call](../docs/terminology.md#8-the-pipeline)'s retries, each [move](../docs/terminology.md#8-the-pipeline)'s duration, each output file's hash and, on failure, the full traceback.
- **[Origin](../docs/terminology.md#8-the-pipeline).** Each row of a [drafted batch](../docs/terminology.md#4-ground-truth-and-samples) has an `origin` column naming its [record](../docs/terminology.md#1-records-and-their-text) in 020's `records.jsonl`. The [ground truth](../docs/terminology.md#4-ground-truth-and-samples) files carry none: they are made by a person, so a trace stops there.
- **Trace.** `py helpers/audit.py <record id>` follows a record back through every [step](../docs/terminology.md#8-the-pipeline)'s output to the 010 [batch file](../docs/terminology.md#1-records-and-their-text) and the API request that first returned it (`helpers/audit.md`). It searches only the files a step's last run wrote, so for 050 the newest drafted batch; a record in an older one is found through 030's `splits.json`.

## Known limits

- **Tested with a stand-in model before its first real run.** As of 2026-09-29, 050 had been tested only with a [stand-in model](../docs/terminology.md#8-the-pipeline), because the model's services can't be reached from the laptop it was built on. Numbers in this guide come from the catalog, the code, or the stand-in, not from a real [run](../docs/terminology.md#8-the-pipeline). Since 2026-10-12, the model's service is reached from the NASA laptop, where step 040 made, with the real model, the schema that 060 and 070 start from ([`findings.md`](../docs/findings.md#2026-10-12--step-040--the-baseline-schema)); 050 first ran with the real model there on 2026-10-21 (`gemini-2.5-pro` through LiteLLM; [`findings.md`](../docs/findings.md#2026-10-21--step-050--why-a-drafted-answer-was-cut-off)).
- **The [schema](../docs/terminology.md#3-schemas) in the prompt is the [ground truth schema](../docs/terminology.md#3-schemas)**, whatever the [current schema](../docs/terminology.md#6-extracting-with-a-schema-step-060) is: the [ground truth](../docs/terminology.md#4-ground-truth-and-samples) should record every [fact](../docs/terminology.md#2-triples) in stable [component classes](../docs/terminology.md#3-schemas), not only what one schema can express.
- **A [record](../docs/terminology.md#1-records-and-their-text) deleted from its ground truth file is not drafted again**: it's still in its [drafted batch](../docs/terminology.md#4-ground-truth-and-samples), which is how 050 knows it was seen. To redraft it, list it with `ids` after removing it from that drafted batch file.
- **The model varies.** Rerunning with an empty cache can draft different [drafted triples](../docs/terminology.md#4-ground-truth-and-samples); the cache makes a rerun reproducible.
