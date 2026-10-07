# 070_evaluate

Terms (precision, recall, pair, pairing, margin of error, bootstrap, tuning part, held-out part, …) are as defined in [docs/terminology.md](../docs/terminology.md), especially section *Evaluating extraction (step 070)*.

## Purpose

Evaluates what step 060 extracted against the ground truth, the answer key:

- **precision**: when 060 says something, how often it is right;
- **recall**: of the triples in the ground truth, how many 060 found;

each with its **margin of error**, so a real improvement can be told from luck. Around them:

- **entity-class accuracy**: of the triples 060 got right, how often it also named the right entity classes;
- **F1**: precision and recall in one number, the usual headline for comparing runs or models;
- **recall upper bound**: how much of the ground truth the schema can express at all (the most recall can be), and **recall within reach**: how well 060 did on what it could do; each also in a strict version, with the entity classes. A low upper bound means the schema needs work; a high upper bound with low recall within reach means the extraction does;
- **what each record describes**: how often 060 named the right entity class for the DESCRIBES row, next to what always guessing the most common kind would get.

Before comparing, the component classes of the current schema (the one 060 used) are translated into the ground truth vocabulary, through a table you check. Only the **fair sample** of the ground truth is evaluated, and by default only its **tuning part**: the held-out part is kept for the end.

The ground truth was drafted by a model (050) and corrected by a person, not written from scratch; a triple both missed is counted nowhere, so recall may come out higher than it is. The report says so.

## To do

### Every step

- **Run it** after the steps before it, and again whenever their outputs change (see *How to run*).
- **Before a step pays for model calls,** read what it prints: anything it can't do exactly as asked is listed above the question. Then press Enter to go ahead, or anything else to stop, having spent nothing. (Steps that call no model don't ask.)
- **Read the report's Warnings:** the report is `outputs/reports/<step>_<date>_<time>.md` (the step prints its path when it ends). Each warning is explained, with what to do, in *Checks and warnings* below.
- **Commit every changed file in the `annotations/` folder to Git,** so your work is safe.

### This step

- **Check the translation table ([`annotations/component_class_mapping.csv`](../annotations/component_class_mapping.csv)) whenever this step adds rows:** `py helpers/annotate.py`, *Translation table*, shows each row with both definitions and an example triple. A wrong translation silently turns right triples into wrong ones, or the reverse. Then **rerun** this step.
- **Act on the row states** (glossary: *row state*) there and in the report (`outputs/reports/070_evaluate_<date>_<time>.md`): rows that are stale (the component class's definition changed), now exists or suggested (the ground truth vocabulary gained a counterpart), or repeated.
- **Review the partial pairs** of the tuning part: `py helpers/annotate.py`, *Partial pairs* (your verdicts go to `annotations/partial_pair_reviews.csv`). Mark each `same fact` or `not the same fact`, with the record's text at hand.
- **Read the report's *Component class mismatches*:** it's how a wrong row of the translation table shows up, even one you checked. Also read *The translation table*: component classes that share a translation are ones the metrics can't tell apart; if that distinction matters to you, make it in the ground truth.
- **Read `outputs/intermediate_results/070_evaluate/per_record.md`**, especially the partial pairs and the triples "extracted, but not in the ground truth": some may be real triples you missed while annotating. Add those only to **tuning** records (fixing the ground truth from extraction's answers favours extraction).
- **Margins of error need at least 20 finished tuning records;** until then, read `outputs/intermediate_results/070_evaluate/per_record.md` rather than the numbers.
- **Look at the held-out part only at the end** (`--evaluate_held_out true`), and commit `annotations/held_out_looks.csv` after each look.
- **Add schema additions (`annotations/schema_additions.txt`) only from the tuning part**, or from outside knowledge: adding entity classes or predicates because of what held-out records need is tuning on them.

## Inputs

| Input | Default | Contents |
|---|---|---|
| `records` | `020_clean/records.jsonl` | Titles, for the per-record list. |
| `splits` | `030_split/splits.json` | The pool's order, and each record's part (tuning or held-out). |
| `extracted_triples` | `060_extract/extracted_triples.csv` | The extracted triples. |
| `extracted_triples_details` | `060_extract/extracted_triples_details.json` | Which records 060 extracted (a record whose call failed is left out, not counted as zero). |
| `schema_used` | `060_extract/schema_used.json` | The schema 060 used: the component classes to translate. |
| `candidates` | `./annotations/ground_truth_candidates.csv` (in Git) | Each pool record's sampling group. |
| `hand_schema` | `./annotations/schema_derived_from_manual_annotation.txt` (in Git) | The hand-built schema: with the component classes coined in the ground truth, the ground truth vocabulary, built by `common/common_helpers/ground_truth.vocabulary` as in 050 and the annotation tool. |
| `ground_truth` | `./annotations/ground_truth/batch_*.csv` (in Git) | The answer key. Only records you've finished (*All facts extracted*) are evaluated. |
| `component_class_mapping` | `./annotations/component_class_mapping.csv` (in Git) | The translation table (below). |
| `partial_reviews` | `./annotations/partial_pair_reviews.csv` (in Git) | Your verdicts on partial pairs (`same fact` / `not the same fact`), made in `py helpers/annotate.py`, *Partial pairs*. Two triples you marked `not the same fact` are never paired. Starts with its header only. |

## Outputs

In `outputs/intermediate_results/070_evaluate/`:

**On a rerun:** the three files are replaced; `cache/` keeps every answer; the lines 070 added to `annotations/` stay.

| File | Contents |
|---|---|
| `per_record.md` | For reading. Each evaluated record of the parts shown (the tuning part; the held-out part too with `--evaluate_held_out true`, so its triples stay unseen until then): what it describes (✓/✗), its **pairs** (✓ exact or ≈ partial, with the ground truth's triple when they differ), **extracted but not in the ground truth** (they count against precision) and **in the ground truth but not extracted** (against recall; marked *out of reach* when the schema can't express them). Extracted triples are shown translated into the ground truth vocabulary. Opens well in VS Code or on GitHub. |
| `compared_triples.csv` | For sorting and filtering, e.g. in Excel. One row per pair, and one per triple left without a partner, of the parts shown: record, pool position, part, group, `status` (`exact pair`, `partial pair`, `extracted only`: no partner, counts against precision; `ground truth only`: no partner, counts against recall), `entity_classes_right`, `within_reach`, `within_strict_reach`, then the triple as extracted, as translated, and as in the ground truth, and where each came from (`origin`). |
| `metrics.json` | For comparing runs. Every number (each with `value`, `low`, `high`: the margin), per part and per sampling group; which records were evaluated and which left out, and why; the component class mismatches (`component_class_mismatches`, see *Then the results*); the model's suggestions for `(none)` rows (`translation_suggestions`, which the annotation tool shows); the tuning part's partial pairs not yet reviewed and ruled out by your review (`partial_pairs_tuning`); the settings. |
| `cache/` | Every model answer, so a rerun pays only for what isn't there yet (see *How to run*). Not listed in the manifest. |
| `_manifest.json` | Run id, settings, input files and their hashes, output files and their hashes, headline numbers and the harvest date. Written when a run finishes. |

Each run also leaves `outputs/reports/<run id>.md` (the report: what it read and wrote, its numbers, its warnings) and `outputs/logs/<run id>.log` (everything it did, line by line); how to read them: `helpers/audit.md`. The report shows the numbers, the group table and every warning: read it first.

**Two files in `annotations/` that 070 adds to**, the only exceptions to "no step writes into `annotations/`". 070 only ever **adds** lines at their end; a line already there is never changed or deleted:

| File | What 070 adds |
|---|---|
| `annotations/component_class_mapping.csv` | Rows for component classes of the current schema that have none yet (see *How it works*, stage 2). |
| `annotations/held_out_looks.csv` | One line per run with `--evaluate_held_out true`: date, run id, current schema, held-out records evaluated. Commit it: it's how the looks are counted, across laptops and after `outputs/` is deleted. |

## Settings

| Setting | Default | What it does | When to change it |
|---|---|---|---|
| `evaluate_held_out` | false | Also show the held-out part's numbers, and log the look in `annotations/held_out_looks.csv`. | Only at the end, for the numbers you report. Each look is a chance to tune on the held-out part without meaning to. |
| `model` | google-claude-sonnet-5 | The AI model to ask. `py helpers/models.py` lists the models Ask Sage shows your account; a listed one may still refuse you, which the run's first call (the one-line test) finds out for the price of that call. Every cached answer is tied to its model: another model asks everything again, and switching back reuses the earlier answers. | See *Choosing a model* in `docs/running_on_nasa_laptop.md`. |
| `confirm_paid_calls` | true | Stop and ask before the first model call (070 calls the model only about the translation table: to propose rows for component classes without one, and to suggest counterparts for `(none)` rows). | `false` for runs with nobody at the keyboard, e.g. the whole pipeline. |

The numbers that are fixed on purpose (in `070_evaluate/070_evaluate_helpers/stats.py`): `MIN_RECORDS = 20` (fewer evaluated records: no margin), `REDRAWS = 1000`, `SEED = 70` (a rerun gives the same margins), `SHARE_GAP = 0.10` (see *Checks and warnings*). In `pairing.py`: `MISMATCH_WARN = 2` (a component class mismatch seen this often becomes a warning; see *Checks and warnings*).

## How to run

From the repository folder, with the environment active (`docs/virtual_environment_setup.md`), and, when component classes need translating, on a computer that can reach Ask Sage with your key in `.env` (`docs/running_on_nasa_laptop.md`):

```
py 070_evaluate/run.py --help                    every input and setting, with its default
py 070_evaluate/run.py                           the tuning part
py 070_evaluate/run.py --evaluate_held_out true     also the held-out part (for the end; each look is logged)
py 070_evaluate/run.py --confirm_paid_calls false    don't ask (unattended runs)
```

Needs 060's output. The first run with a new schema stops after adding rows to `annotations/component_class_mapping.csv`: check them, then run again.

**Paying.** Before its first model call, 070 logs its plan (how many component classes to translate, the model) and waits: Enter starts, anything else stops the run having spent nothing. If the run can't do exactly what you asked, it says so first, above the question (*Before you pay: this run can't do exactly what you asked*, then the reasons, listed under *Checks and warnings*). Its first call is a one-line test that the model name and key work. A run whose answers are all in the cache never asks and never pays. Model calls: at most two, both about the translation table: one when the current schema has component classes without a row in `annotations/component_class_mapping.csv`, and one when there are both `(none)` rows of the current schema and component classes of the ground truth vocabulary nothing translates to (asked once per such pair of lists). None otherwise: the evaluation is code.

**The cache.** Every model answer is kept in `cache/`, under a fingerprint of everything that decided it: the model, the prompt's exact text, and what was sent. A rerun reuses every answer whose fingerprint is unchanged: a failed call isn't kept, so a rerun asks only the calls that failed; editing a prompt asks again exactly the calls that use it; deleting `cache/` (or all of `outputs/`) means paying for every call again.

## How it works

Four stages, in `070_evaluate/run.py`'s `main()`; stage 2 may ask the model (for component classes without a row, and for suggestions on `(none)` rows), the others are code:

1. **Pick the records** (`records.py`, `pick_records`). A record is evaluated if you've finished it in the ground truth and 060's last run extracted it. Of those, only the **fair sample**: the longest run of the pool's first records that are all evaluated. A record after a gap (an unfinished or unextracted pool record before it) or outside the pool is left out and named, so every evaluated record belongs to a fair sample.
2. **Translate component classes** (`component_classes.py`, `translate_component_classes`), through `annotations/component_class_mapping.csv`:

   ```
   kind,component_class_from_past_or_crt_schema,component_class_in_gtt,swap_subject_and_object,checked,definition_from_past_or_crt_schema
   entity class,Satellite,Spacecraft,no,yes,A craft that orbits a body.
   predicate,CARRIES,ABOARD,yes,yes,Has on board.         "A CARRIES B" is "B ABOARD A"
   entity class,Gadget,(none),no,yes,A small device.      nothing in the ground truth means this
   entity class,Dataset,Dataset,no,same component class,A set of data.
   ```

   For each component class of the current schema without a row: one equal to a component class of the ground truth vocabulary (ignoring case and punctuation) gets a row at once, `checked` = `same component class`; the model proposes the others (one paid call, after the usual confirmation), `checked` = `no`. The step then stops. You check each `no` row: fix `component_class_in_gtt` (a component class of the ground truth vocabulary, or `(none)`) and `swap_subject_and_object` where wrong, then set `checked` to `yes`. Evaluation runs only once every row it needs is checked. Each row also keeps the current schema's definition of its component class from when it was written or last checked (`definition_from_past_or_crt_schema`): if a later schema defines that component class differently, the row is **stale** (it may no longer be right) and the step stops until you check it again; checking it again stores the new definition. So the one table can serve every schema: a component class keeps its row while its meaning stays the same. The model's proposals are only a first draft: in testing, a stand-in's deliberate mistake (`Phase` → `(none)` instead of `MissionPhase`) is exactly what the check is for.
3. **Compare, record by record** (`pairing.py`, `compare`). Each extracted triple is translated into the ground truth vocabulary; a reversed predicate also swaps subject and object. Then the ground truth's triples and the extracted triples are **paired**: every triple, in either list, ends with **zero or one partner**, always from the other list (so a triple stated twice earns one pair, not two; the two lists can have any lengths). Two rounds, each finding the largest possible set of pairs (in maths, a *maximum matching*: a pair may be swapped to free a partner for a triple that would otherwise have none; taking each triple's first possible partner in list order could lose a real pair, and make the metrics depend on the order triples were written in):
   - **exact**: subject and object the same once evened out (case, spacing, quote marks, dashes, edge punctuation and a leading "the/a/an" ignored, as everywhere in the pipeline), predicate the same;
   - **partial**, among the triples still unpaired: the same, except that a subject or object may be contained in the other as whole words: "MODIS" in "Moderate Resolution Imaging Spectroradiometer (MODIS)". This can be fooled ("MODIS" in "MODIS Terra"), which is why every partial pair is listed in `per_record.md`, and why you review the tuning part's partial pairs in `py helpers/annotate.py`, *Partial pairs*: two triples you mark `not the same fact` are never paired.

   A pair is **strict** when the subject classes and the object classes also agree. A ground truth triple is **within reach** when its predicate is one some checked row translates to: that's all a pair needs, since a pair doesn't need the entity classes to agree. It's **within strict reach** when both its entity classes are too: all a strict pair needs. The DESCRIBES rows are compared only on their entity class, apart from the triples, since code writes the rest of them.
4. **Compute the metrics** (`stats.py`, `compute_metrics`). Every number is summed over the records before dividing (a triple is an answer, whichever record it's in):

   | Number | Is |
   |---|---|
   | precision | pairs ÷ extracted triples |
   | recall | pairs ÷ ground truth triples |
   | F1 | 2 × precision × recall ÷ (precision + recall), the same as 2 × pairs ÷ (extracted triples + ground truth triples): high only when both are |
   | strict precision, strict recall, strict F1 | the same, counting only strict pairs |
   | entity-class accuracy | strict pairs ÷ pairs |
   | recall upper bound | ground truth triples within reach ÷ all ground truth triples: the most recall can be |
   | strict recall upper bound | ground truth triples within strict reach ÷ all ground truth triples: the most strict recall can be |
   | recall within reach | pairs whose ground truth triple is within reach ÷ ground truth triples within reach |
   | strict recall within reach | strict pairs ÷ ground truth triples within strict reach |
   | describes: accuracy | records whose describes class is right ÷ records whose ground truth names one |
   | describes: baseline | the share of the most common entity class: what always guessing it would get |
   | describes: per-entity-class average | each entity class's accuracy, averaged, so rare entity classes count as much as common ones |

   Each is given at both pair levels (**exact**, and **partial**, which counts exact and partial pairs), with its **margin of error** by the **bootstrap** (below), for the tuning part, for the held-out part when asked, and per sampling group. The report adds a table of what 060 said each record describes versus what it is.

**Then the results** (`results`): `metrics.json`, `per_record.md` and `compared_triples.csv` are written, replacing the last run's; with `--evaluate_held_out true`, a line is added to `annotations/held_out_looks.csv`; the report. The report also lists **component class mismatches** (`pairing.py`, `component_class_mismatches`), possible translation errors, found in the shown parts' triples: a wrong or missing row of the translation table leaves a trace where extraction found the triple but a component class differs. A paired triple whose entity class differs from the ground truth's suggests the row of the current schema's entity class is wrong (its row may say `(none)`, or the wrong entity class); an unpaired extracted triple and an unpaired ground truth triple with the same subject and object (or the two swapped) but different predicates suggest the predicate's row is wrong (or its `swap_subject_and_object`). Each mismatch is counted, e.g. *Gadget (current schema) --> (none), met Device (ground truth vocabulary) 9 times*; a single one may just be extraction choosing the wrong component class, a frequent one is a row to check.

The code: `070_evaluate/` holds `run.py` (the control panel: inputs, settings and the moves, in order); `070_evaluate/070_evaluate_helpers/` holds `moves.py` (the moves, and writing the results), `records.py`, `component_classes.py`, `pairing.py`, `stats.py` and `readings.py` (the metrics read as sentences); `070_evaluate/070_evaluate_prompts/` holds the prompts (see *Prompts*). Shared with other steps: `common/common_helpers/ground_truth.py` (reading the ground truth; the fair sample), `common/common_helpers/text_match.py`, `common/common_helpers/triples_io.py`, `common/common_helpers/files.py` (adding lines without changing any), `common/common_helpers/cache.py`, `common/common_helpers/llm.py`.

### Reading the metrics

A percentage alone is hard to use, so for each part the report also writes every metric out as sentences, filled in with that run's own counts (section *Reading the metrics* of the report; code: `readings.py`). It starts with **where these numbers come from**: extraction's run and model, its schema and how many additions it had (naming any learned from tuning records, which come from the very records being evaluated), the translation table, the ground truth records (pool positions), the partial pairs reviewed or not, for the held-out part how many times it has been looked at, and where each run's full recipe is (its report's Run, Settings, Prompts and Inputs sections).

Then, per metric, the readings that hold for it, such as:

- the counts behind it, e.g. "of the 8 extracted triples of these records, 4 (50%) form exact pairs";
- read as a chance, e.g. "an extracted triple has a 50% chance of forming an exact pair";
- what it means for a knowledge graph built from the extracted triples, e.g. "4 of the 8 statements would have no exact counterpart in the ground truth";
- how sure it is: "for the whole catalog, likely between 52% and 70%" (the margin of error), or, with fewer than 20 records, that it has none;
- what it assumes, e.g. that the ground truth lists every fact the records state;
- where needed, what it can't see, e.g. entity-class accuracy can't see mix-ups between component classes of the current schema that translate to the same component class of the ground truth vocabulary.

A metric gets only the readings that apply to it: the recall upper bound, for instance, has no "chance" reading, and *what each record describes* is read against what always guessing the most common kind would get.

### The margin of error, and the checks it needs

How it is computed, what it assumes, and how the report checks each assumption: [`070_evaluate/metrics.md`](metrics.md#sampling-error).

**Per sampling group**, every group of the pool is listed with its number of evaluated records, its share of them and its share of the pool; its numbers appear once it has 20 records. Overall numbers need no weighting, because each group had places in proportion to its size. Two more checks:

- if a group's share of the evaluated records differs from its share of the pool by more than 10 points (with enough records), the report warns: the evaluated records don't mirror the pool;
- with many groups, about 1 in 20 margins misses the true value by chance, so one group that looks unusually good or bad is not, alone, a finding. The report says so beside the table.

## Prompts

| Prompt file | Sent in | Asks the model to |
|---|---|---|
| `070_evaluate/070_evaluate_prompts/map_component_classes.txt` | stage 2, one call, only for component classes of the current schema without a row | for each of those component classes, give the component class of the ground truth vocabulary that means the same thing (or none), and say whether a predicate states the relation in the opposite direction; the ground truth vocabulary's component classes and definitions are shown in the prompt |
| `070_evaluate/070_evaluate_prompts/suggest_component_classes.txt` | stage 2, one call, only when there are both rows of the current schema that say `(none)` and component classes of the ground truth vocabulary nothing translates to; the answer is cached by those two lists, so the same lists are never paid for twice | for each `(none)` component class, whether a component class of the ground truth vocabulary nothing translates to means the same thing (suggest only if confident) |

Each prompt is a plain text file: open it to read exactly what the model is told. `$name` marks where the code fills something in. The prompts use this project's terms (component class, entity class, predicate, ground truth vocabulary, current schema), each explained in the prompt. Editing a prompt is allowed: the next run asks again every call that uses it, and pays for them. Its answers are only proposals: you check every row before evaluation uses it.

## Checks and warnings

**Shown before paying**, above the confirmation question (and also in the report's warnings):

| Message | Meaning | What to do |
|---|---|---|
| *N finished ground truth record(s) weren't extracted by 060's last run* | They can't be evaluated. | Run `py 060_extract/run.py`. |
| *N record(s) are left out because they aren't in the fair sample* | A pool record before them isn't finished or extracted, or they're outside the pool. | Finish (or extract) the records before them. |
| *N evaluated record(s) have no sampling group* | Not in the pool file. | Normally impossible for pool records. |
| *Ground truth: record … is in batch_… and batch_…: annotated twice* | A record is annotated twice. It's left out of the ground truth until fixed. | Keep it in one file. |
| *Ground truth: record … all_facts_extracted is 0 on some rows, 1 on others* | Mixed, so the record doesn't count as finished. | Set it the same on every row (the tool's box does). |
| *Ground truth: record … in batch_…: lines … and … are the same triple (…)* | The same subject, predicate and object twice in one record (a hand edit). Only one copy can be paired, so evaluation would count the other as missed. | Delete one of the two rows. |
| *Ground truth: batch_… lacks the column(s) …; not read* | A ground truth file without one of the columns (see `annotations/README.md`). | Add the column. |

**In the report**, under *Warnings*:

| Message | Meaning | What to do |
|---|---|---|
| *only N record(s) evaluated, fewer than 20* | No margin of error; don't draw conclusions yet. | Annotate more; until then, read `per_record.md` rather than the numbers. |
| *some sampling group's share … differs from its share of the pool* | The evaluated records' mix of maintainers differs from the pool's (and so from the catalog's), by chance: the fair sample is a random sample. | Look at the group table, and read the numbers with that in mind; the difference shrinks as more records are evaluated. |
| *an assumption of the margin of error doesn't hold* | Some ranges are less trustworthy: which assumption, and why, is in the report's section *The margin of error's assumptions, checked* ([`metrics.md`](metrics.md#sampling-error)). | Usually: annotate more records. A sampling group with only 1 evaluated record, or a range at 0% or 100%, becomes rarer as records are added. |
| *The model suggests N row(s) of component_class_mapping.csv that say (none) may now have a counterpart in the ground truth vocabulary* | The ground truth vocabulary gained component classes since those rows were checked, and the model thinks a different one means the same as the row's component class of the current schema (e.g. *Gadget (current schema) --> Device (ground truth vocabulary)*). Rows are never changed by it. | Check the row in `py helpers/annotate.py`, *Translation table* (it shows the suggestion): pick the suggested component class if right, keep `(none)` otherwise. |
| *N partial pair(s) of the tuning part aren't reviewed yet* | The partial level counts pairs nobody has confirmed; some may not be the same fact (e.g. `MODIS` vs `MODIS Terra`). | Review them in `py helpers/annotate.py`, *Partial pairs*; rerun 070. |
| *N row(s) of component_class_mapping.csv translate to (none) though the ground truth vocabulary now has the same component class* | A row checked as `(none)` before that component class joined the ground truth vocabulary (you coined it, or added it to the hand-built schema): probably out of date. Not a stop, since `(none)` may still be right if the ground truth's component class means something else. | Check the row in `py helpers/annotate.py`, *Translation table* (it's flagged there); change it to the ground truth vocabulary's component class, or keep `(none)`. |
| *N component class mismatch(es) seen 2 or more times where extraction found the triple but a component class differed* | A row of `component_class_mapping.csv` may translate a component class of the current schema to the wrong one of the ground truth vocabulary, to `(none)` when one fits, or with the wrong `swap_subject_and_object`. | Look at *Component class mismatches* in the report; fix the rows that are wrong (`py helpers/annotate.py`, *Translation table*). |
| *The held-out part was looked at: N time(s) so far* | After `--evaluate_held_out true`: each look is logged and counted. | Commit `annotations/held_out_looks.csv`. |
| *N of M compared triples have no origin, so they can't be traced to the input they came from* | Should never happen: a code change dropped the field that records where each item came from. | Fix the code before using the output. |

**The step stops** with:

| Message | Meaning | What to do |
|---|---|---|
| *Added N row(s) to component_class_mapping.csv …* | New component classes of the current schema. If the model proposed a component class that isn't in the ground truth vocabulary, the row says `(none)` and the message ends by listing them (*The model proposed N component class(es) that aren't in the ground truth vocabulary, written as (none): …*). | Check the rows with `checked` = `no` (easiest in `py helpers/annotate.py`, *Translation table*), then run again. |
| *N checked row(s) of component_class_mapping.csv were checked when the current schema defined the component class differently* | A later schema uses the component class, but defines it differently from when the row was checked: the translation may no longer be right. | Check those rows again in `py helpers/annotate.py`, *Translation table* (it shows both definitions), then run again. |
| *N row(s) of component_class_mapping.csv still need checking* | Rows added by an earlier run aren't checked yet. | Check them in `py helpers/annotate.py`, *Translation table* (or in the CSV: fix `component_class_in_gtt` and `swap_subject_and_object` where wrong, then set `checked` to `yes`), then run again. |
| *N checked row(s) … translate to a component class that isn't in the ground truth vocabulary* | A typo in `component_class_in_gtt`, or one since renamed; each is listed as *component class (current schema) --> component class (not in the ground truth vocabulary)*. | Choose a component class of the ground truth vocabulary, or `(none)`. |
| *component_class_mapping.csv has N component class(es) with more than one row: … (lines …)* | Two rows for one component class (usually from a hand edit), so which translation counts is unclear. | Keep one row per component class: `py helpers/annotate.py`, *Translation table*, shows a *Delete this row* button on each repeated row. |
| *component_class_mapping.csv lacks the column(s) …* | The file's header was changed. | Restore the header: `kind,component_class_from_past_or_crt_schema,component_class_in_gtt,swap_subject_and_object,checked,definition_from_past_or_crt_schema`. |
| *kind must be 'entity class' or 'predicate'* | A typo in `kind`. | Fix it. |
| *Nothing to evaluate yet* | No finished ground truth record that 060 extracted is in the fair sample. | Finish records in `py helpers/annotate.py`, then run 060. |
| *splits.json has no tuning / held-out part* | An old `splits.json`. | Delete 030's `splits.json`, run `py 030_split/run.py`. |
| *missing input files … run 060_extract first* | 060 hasn't run. | Run it. |
| *model must name a model* | The `model` setting is empty. | Give a model's name (`py helpers/models.py` lists them). |
| *Test call to … failed* | Ask Sage refuses you that model, the key is wrong, or Ask Sage can't be reached. Nothing else was called. | If Ask Sage says the model isn't allowed, choose another (`--model`; `py helpers/models.py` lists them). Otherwise check `.env` and the network. |
| *Cancelled. Nothing was spent.* | You declined at the confirmation. | — |
| *Set ASKSAGE_EMAIL and ASKSAGE_API_KEY (e.g. in .env).* | The Ask Sage credentials aren't set, so no model can be called. | Put them in `.env` (see `docs/running_on_nasa_laptop.md`). |

## Audit trail

- **Prompts.** The report's *Prompts* section lists every prompt the run filled in, each with a fingerprint (sha256) of its exact text, so the prompt behind any answer is known even if the prompt file was edited later (`_manifest.json` keeps the full fingerprints).
- **Log.** `outputs/logs/<run id>.log` records the command line, the settings, the git commit, the model call's retries (if any), each move's duration, each output file's hash and, on failure, the full traceback.
- **Origin.** Each row of `compared_triples.csv` has an `origin` column naming the 060 row it compares (`060_extract/extracted_triples.csv#<position>`) and the ground truth row (`annotations/ground_truth/batch_000.csv#<position>`); the ground truth is made by a person, so a trace stops there.
- **Trace.** `py helpers/audit.py <record id>` follows a record back through every step's output to the 010 batch file and the API request that first returned it (`helpers/audit.md`).
- **Held-out looks.** `annotations/held_out_looks.csv` keeps one line per look at the held-out part, in Git.

## Known limits

- **Not yet run with the real model.** As of 2026-09-29, 070 has been tested only with a hand-made 060 output whose right answers were worked out in advance (all 16 numbers came out as expected), and with synthetic records for the margins; 060 itself hasn't run with the real model yet, because Ask Sage can't be reached from the laptop it was built on. The numbers in this guide come from those tests, not from a real run.
- **One translation per component class.** A component class of the current schema translates to at most one component class of the ground truth vocabulary; if it covers two (e.g. `Instrument` (current schema) for both `Instrument` and `Sensor` (ground truth vocabulary)), pick the closer one.
- **Partial pairing can be fooled**, and doesn't catch synonyms ("the satellite" for "Aqua"). You review the tuning part's partial pairs; the held-out part's are never reviewed (that would mean looking at it), so its partial level may count pairs that aren't the same fact.
- **The ground truth started as a model's draft**: recall may be overstated (see Purpose).
- **The threshold of 20 records** for a margin is a rule of thumb.
