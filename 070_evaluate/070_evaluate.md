# 070_evaluate

Terms ([precision](../docs/terminology.md#7-evaluating-extraction-step-070), [recall](../docs/terminology.md#7-evaluating-extraction-step-070), [pair](../docs/terminology.md#7-evaluating-extraction-step-070), pairing, [margin of error](../docs/terminology.md#7-evaluating-extraction-step-070), [bootstrap](../docs/terminology.md#7-evaluating-extraction-step-070), [tuning part](../docs/terminology.md#7-evaluating-extraction-step-070), [held-out part](../docs/terminology.md#7-evaluating-extraction-step-070), …) are as defined in [docs/terminology.md](../docs/terminology.md), especially section *Evaluating extraction (step 070)*.

## Purpose

Evaluates what [step](../docs/terminology.md#8-the-pipeline) 060 extracted against the [ground truth](../docs/terminology.md#4-ground-truth-and-samples), the answer key:

- **[precision](../docs/terminology.md#7-evaluating-extraction-step-070)**: when 060 says something, how often it is right;
- **[recall](../docs/terminology.md#7-evaluating-extraction-step-070)**: of the ground truth triples, how many 060 found;

each with its **[margin of error](../docs/terminology.md#7-evaluating-extraction-step-070)**, so a real improvement can be told from luck. Around them:

- **[entity-class accuracy](../docs/terminology.md#7-evaluating-extraction-step-070)**: of the [extracted triples](../docs/terminology.md#6-extracting-with-a-schema-step-060) 060 got right, how often it also named the right [entity classes](../docs/terminology.md#3-schemas);
- **[F1](../docs/terminology.md#7-evaluating-extraction-step-070)**: precision and recall in one number, the usual headline for comparing [runs](../docs/terminology.md#8-the-pipeline) or [models](../docs/terminology.md#8-the-pipeline);
- **[recall upper bound](../docs/terminology.md#7-evaluating-extraction-step-070)**: how much of the ground truth the [schema](../docs/terminology.md#3-schemas) can express at all (the most recall can be), and **recall [within reach](../docs/terminology.md#7-evaluating-extraction-step-070)**: how well 060 did on what it could do; each also in a strict version, with the entity classes. A low upper bound means the schema needs work; a high upper bound with low recall within reach means the extraction does;
- **what each [record](../docs/terminology.md#1-records-and-their-text) describes**: how often 060 named the right entity class for the [DESCRIBES row](../docs/terminology.md#2-triples), next to what always guessing the most common kind would get.

Before comparing, the [component classes](../docs/terminology.md#3-schemas) of the [current schema](../docs/terminology.md#6-extracting-with-a-schema-step-060) (the one 060 used) are translated into the [ground truth vocabulary](../docs/terminology.md#7-evaluating-extraction-step-070), through a table you check. Only the **[fair sample](../docs/terminology.md#4-ground-truth-and-samples)** of the ground truth is evaluated, and by default only its **[tuning part](../docs/terminology.md#7-evaluating-extraction-step-070)**: the [held-out part](../docs/terminology.md#7-evaluating-extraction-step-070) is kept for the end.

The ground truth was drafted by a model (050) and corrected by a person, not written from scratch; so recall is likely overstated (see [`metrics/recall.md`](metrics/recall.md), *Assumes and can't see*). The [report](../docs/terminology.md#8-the-pipeline) says so, under *Where these numbers come from*.

## To do

### Every step

- **Run it** after the [steps](../docs/terminology.md#8-the-pipeline) before it, and again whenever their outputs change (see *How to run*).
- **Before a step pays for [model calls](../docs/terminology.md#8-the-pipeline),** read what it prints: anything it can't do exactly as asked is listed above the question. Then press Enter to go ahead, or anything else to stop, having spent nothing. (Steps that call no [model](../docs/terminology.md#8-the-pipeline) don't ask.)
- **Read the [report](../docs/terminology.md#8-the-pipeline)'s Warnings:** the report is `outputs/reports/<step>_<date>_<time>.md` (the step prints its path when it ends). Each warning is explained, with what to do, in *Checks and warnings* below.
- **Commit every changed file in the `annotations/` folder to Git,** so your work is safe.

### This step

- **Check the [translation table](../docs/terminology.md#7-evaluating-extraction-step-070) ([`annotations/component_class_mapping.csv`](../annotations/component_class_mapping.csv)) whenever this [step](../docs/terminology.md#8-the-pipeline) adds rows:** `py helpers/annotate.py`, *Translation table*, shows each row with both definitions and an example [extracted triple](../docs/terminology.md#6-extracting-with-a-schema-step-060). A wrong translation silently turns right extracted triples into wrong ones, or the reverse. Then **rerun** this step.
- **Act on the [row states](../docs/terminology.md#7-evaluating-extraction-step-070)** there and in the [report](../docs/terminology.md#8-the-pipeline) (`outputs/reports/070_evaluate_<date>_<time>.md`): rows that are [stale](../docs/terminology.md#7-evaluating-extraction-step-070) (the [component class](../docs/terminology.md#3-schemas)'s definition changed), [now exists](../docs/terminology.md#7-evaluating-extraction-step-070) or [suggested](../docs/terminology.md#7-evaluating-extraction-step-070) (the [ground truth vocabulary](../docs/terminology.md#7-evaluating-extraction-step-070) gained a counterpart), or [repeated](../docs/terminology.md#7-evaluating-extraction-step-070).
- **Review the partial [pairs](../docs/terminology.md#7-evaluating-extraction-step-070)** of the [tuning part](../docs/terminology.md#7-evaluating-extraction-step-070): `py helpers/annotate.py`, *Partial pairs* (your [verdicts](../docs/terminology.md#7-evaluating-extraction-step-070) go to `annotations/partial_pair_reviews.csv`). Mark each `same fact` or `not the same fact`, with the [record](../docs/terminology.md#1-records-and-their-text)'s [text](../docs/terminology.md#1-records-and-their-text) at hand.
- **Read the report's *Component class mismatches*:** it's how a wrong row of the translation table shows up, even one you checked. Also read *The translation table*: component classes that share a translation are ones the metrics can't tell apart; if that distinction matters to you, make it in the [ground truth](../docs/terminology.md#4-ground-truth-and-samples).
- **Read `outputs/intermediate_results/070_evaluate/per_record.md`**, especially the [partial pairs](metrics/pairs.md) and the extracted triples "extracted, but not in the ground truth": some may be real facts you missed while annotating. Add those only to **tuning** records (fixing the ground truth from extraction's answers favours extraction).
- **[Margins of error](../docs/terminology.md#7-evaluating-extraction-step-070) need at least 20 finished tuning records;** until then, read `outputs/intermediate_results/070_evaluate/per_record.md` rather than the numbers.
- **Look at the [held-out part](../docs/terminology.md#7-evaluating-extraction-step-070) only at the end** (`--evaluate_held_out true`), and commit `annotations/held_out_looks.csv` after each look.
- **Add [schema additions](../docs/terminology.md#3-schemas) (`annotations/schema_additions.txt`) only from the tuning part**, or from outside knowledge: adding [entity classes](../docs/terminology.md#3-schemas) or [predicates](../docs/terminology.md#3-schemas) because of what held-out records need is tuning on them.
- **Raise With Mentors: checking a sample of the occurrences left extracted only,** to see how far precision and recall are understated ([`metrics/pairs.md`](metrics/pairs.md), *The same fact in different words*). It's an involved process: such an occurrence can be the same fact in different words as a [ground truth triple](../docs/terminology.md#4-ground-truth-and-samples) left ground truth only, a repeat of a fact already paired, a fact the ground truth lacks, the result of a wrong translation, or actually wrong, and each means something different.

## Inputs

| Input | Default | Contents |
|---|---|---|
| `records` | `020_clean/records.jsonl` | Titles, for the per-record list. |
| `splits` | `030_split/splits.json` | The [pool](../docs/terminology.md#4-ground-truth-and-samples)'s order, and each [record](../docs/terminology.md#1-records-and-their-text)'s part (tuning or held-out). |
| `extracted_triples` | `060_extract/extracted_triples.csv` | The [extracted triples](../docs/terminology.md#6-extracting-with-a-schema-step-060). |
| `extracted_triples_details` | `060_extract/extracted_triples_details.json` | Which records 060 extracted (a record whose call failed is left out, not counted as zero). |
| `schema_used` | `060_extract/schema_used.json` | The [schema](../docs/terminology.md#3-schemas) 060 used: the [component classes](../docs/terminology.md#3-schemas) to translate. |
| `candidates` | `./annotations/ground_truth_candidates.csv` (in Git) | Each pool record's [stratum](../docs/terminology.md#4-ground-truth-and-samples). |
| `hand_schema` | `./annotations/schema_derived_from_manual_annotation.txt` (in Git) | The [hand-built schema](../docs/terminology.md#3-schemas): with the component classes [coined](../docs/terminology.md#7-evaluating-extraction-step-070) in the [ground truth](../docs/terminology.md#4-ground-truth-and-samples), the [ground truth vocabulary](../docs/terminology.md#7-evaluating-extraction-step-070), built by `common/common_helpers/ground_truth.vocabulary` as in 050 and the [annotation tool](../docs/terminology.md#4-ground-truth-and-samples). |
| `ground_truth` | `./annotations/ground_truth/batch_*.csv` (in Git) | The answer key. Only records you've finished (*All facts extracted*) are evaluated. |
| `component_class_mapping` | `./annotations/component_class_mapping.csv` (in Git) | The [translation table](../docs/terminology.md#7-evaluating-extraction-step-070) (below). |
| `partial_reviews` | `./annotations/partial_pair_reviews.csv` (in Git) | Your [verdicts](../docs/terminology.md#7-evaluating-extraction-step-070) on partial [pairs](../docs/terminology.md#7-evaluating-extraction-step-070) (`same fact` / `not the same fact`), made in `py helpers/annotate.py`, *Partial pairs*. An extracted triple and a [ground truth triple](../docs/terminology.md#4-ground-truth-and-samples) you marked `not the same fact` are never paired. Starts with its header only. |

## Outputs

In `outputs/intermediate_results/070_evaluate/`:

**On a rerun:** the three files are replaced; `cache/` keeps every answer; the lines 070 added to `annotations/` stay.

| File | Contents |
|---|---|
| `per_record.md` | For reading. Each evaluated [record](../docs/terminology.md#1-records-and-their-text) of the parts shown (the [tuning part](../docs/terminology.md#7-evaluating-extraction-step-070); the [held-out part](../docs/terminology.md#7-evaluating-extraction-step-070) too with `--evaluate_held_out true`, so its [classed triples](../docs/terminology.md#2-triples) stay unseen until then): what it describes (✓/✗), its **[pairs](../docs/terminology.md#7-evaluating-extraction-step-070)** (✓ exact or ≈ partial, with the [ground truth triple](../docs/terminology.md#4-ground-truth-and-samples) when they differ), **extracted but not in the [ground truth](../docs/terminology.md#4-ground-truth-and-samples)** (they count against [precision](../docs/terminology.md#7-evaluating-extraction-step-070)) and **in the ground truth but not extracted** (against [recall](../docs/terminology.md#7-evaluating-extraction-step-070); marked *out of reach* when the [schema](../docs/terminology.md#3-schemas) can't express them). [Extracted triples](../docs/terminology.md#6-extracting-with-a-schema-step-060) are shown translated into the [ground truth vocabulary](../docs/terminology.md#7-evaluating-extraction-step-070). Opens well in VS Code or on GitHub. |
| `compared_triples.csv` | For sorting and filtering, e.g. in Excel. One row per pair, and one per occurrence or ground truth triple left without a partner, of the parts shown: record, [pool](../docs/terminology.md#4-ground-truth-and-samples) position, part, [stratum](../docs/terminology.md#4-ground-truth-and-samples), `status` (`exact pair`, `partial pair`, `extracted only`: no partner, counts against precision; `ground truth only`: no partner, counts against recall), `entity_classes_right`, `within_reach`, `within_strict_reach`, then the classed triple as extracted, as translated, and as in the ground truth, and where each came from (`origin`). |
| `metrics.json` | For comparing [runs](../docs/terminology.md#8-the-pipeline). Every number (each with `value`, `low`, `high`: the margin), per part and per stratum; which records were evaluated and which left out, and why; the [component class](../docs/terminology.md#3-schemas) mismatches (`component_class_mismatches`, see *Then the results*); the [model](../docs/terminology.md#8-the-pipeline)'s suggestions for `(none)` rows (`translation_suggestions`, which the [annotation tool](../docs/terminology.md#4-ground-truth-and-samples) shows); the tuning part's [partial pairs](metrics/pairs.md) not yet reviewed and ruled out by your review (`partial_pairs_tuning`); the [settings](../docs/terminology.md#8-the-pipeline). |
| `cache/` | Every model answer, so a rerun pays only for what isn't there yet (see *How to run*). Not listed in the [manifest](../docs/terminology.md#8-the-pipeline). |
| `_manifest.json` | [Run id](../docs/terminology.md#8-the-pipeline), settings, input files and their hashes, output files and their hashes, headline numbers and the [harvest](../docs/terminology.md#1-records-and-their-text) date. Written when a run finishes. |

Each run also leaves `outputs/reports/<run id>.md` (the [report](../docs/terminology.md#8-the-pipeline): what it read and wrote, its numbers, its warnings) and `outputs/logs/<run id>.log` (everything it did, line by line); how to read them: `helpers/audit.md`. The report shows the numbers, the group table and every warning: read it first.

**Two files in `annotations/` that 070 adds to**, the only exceptions to "no [step](../docs/terminology.md#8-the-pipeline) writes into `annotations/`". 070 only ever **adds** lines at their end; a line already there is never changed or deleted:

| File | What 070 adds |
|---|---|
| `annotations/component_class_mapping.csv` | Rows for component classes of the [current schema](../docs/terminology.md#6-extracting-with-a-schema-step-060) that have none yet (see *How it works*, [stage](../docs/terminology.md#8-the-pipeline) 2). |
| `annotations/held_out_looks.csv` | One line per run with `--evaluate_held_out true`: date, run id, current schema, held-out records evaluated. Commit it: it's how the looks are counted, across laptops and after `outputs/` is deleted. |

## Settings

| Setting | Default | What it does | When to change it |
|---|---|---|---|
| `evaluate_held_out` | false | Also show the [held-out part](../docs/terminology.md#7-evaluating-extraction-step-070)'s numbers, and log the look in `annotations/held_out_looks.csv`. | Only at the end, for the numbers you report. Each look is a chance to tune on the held-out part without meaning to. |
| `model` | google-claude-sonnet-5 | The AI [model](../docs/terminology.md#8-the-pipeline) to ask. `py helpers/models.py` lists the models Ask Sage shows your account; a listed one may still refuse you, which the [run](../docs/terminology.md#8-the-pipeline)'s first call (the one-line test) finds out for the price of that call. Every cached answer is tied to its model: another model asks everything again, and switching back reuses the earlier answers. | See *Choosing a model* in `docs/running_on_nasa_laptop.md`. |
| `confirm_paid_calls` | true | Stop and ask before evaluating when there are warnings (*Checks and warnings*), and before the first [model call](../docs/terminology.md#8-the-pipeline) (070 calls the model only about the [translation table](../docs/terminology.md#7-evaluating-extraction-step-070): to propose rows for [component classes](../docs/terminology.md#3-schemas) without one, and to suggest counterparts for `(none)` rows). | `false` for runs with nobody at the keyboard, e.g. the whole pipeline. |

The numbers that are fixed on purpose (in `070_evaluate/070_evaluate_helpers/stats.py`): `MIN_RECORDS = 20` (fewer evaluated [records](../docs/terminology.md#1-records-and-their-text): no margin), `REDRAWS = 1000`, `SEED = 70` (a rerun gives the same margins), `SHARE_GAP = 0.10` (see *Checks and warnings*). In `pairing.py`: `MISMATCH_WARN = 2` (a component class mismatch seen this often becomes a warning; see *Checks and warnings*).

## How to run

From the repository folder, with the environment active (`docs/virtual_environment_setup.md`), and, when [component classes](../docs/terminology.md#3-schemas) need translating, on a computer that can reach Ask Sage with your key in `.env` (`docs/running_on_nasa_laptop.md`):

```
py 070_evaluate/run.py --help                    every input and setting, with its default
py 070_evaluate/run.py                           the tuning part
py 070_evaluate/run.py --evaluate_held_out true     also the held-out part (for the end; each look is logged)
py 070_evaluate/run.py --confirm_paid_calls false    don't ask (unattended runs)
```

Needs 060's output. The first [run](../docs/terminology.md#8-the-pipeline) with a new [schema](../docs/terminology.md#3-schemas) stops after adding rows to `annotations/component_class_mapping.csv`: check them, then run again.

**Paying.** Before its first [model call](../docs/terminology.md#8-the-pipeline), 070 logs its plan (how many component classes to translate, the [model](../docs/terminology.md#8-the-pipeline)) and waits: Enter starts, anything else stops the run having spent nothing. Any warnings were already shown, and asked about, before evaluating (stage 1), so this question doesn't repeat them. Its first call is a one-line test that the model name and key work. A run whose answers are all in the cache never asks and never pays. Model calls: at most two, both about the [translation table](../docs/terminology.md#7-evaluating-extraction-step-070): one when the [current schema](../docs/terminology.md#6-extracting-with-a-schema-step-060) has component classes without a row in `annotations/component_class_mapping.csv`, and one when there are both `(none)` rows of the current schema and component classes of the [ground truth vocabulary](../docs/terminology.md#7-evaluating-extraction-step-070) nothing translates to (asked once per such pair of lists). None otherwise: the evaluation is code.

**The cache.** Every model answer is kept in `cache/`, under a [fingerprint](../docs/terminology.md#8-the-pipeline) of everything that decided it: the model, the prompt's exact text, and what was sent. A rerun reuses every answer whose fingerprint is unchanged: a failed call isn't kept, so a rerun asks only the calls that failed; editing a prompt asks again exactly the calls that use it; deleting `cache/` (or all of `outputs/`) means paying for every call again.

## How it works

Four [stages](../docs/terminology.md#8-the-pipeline), in `070_evaluate/run.py`'s `main()`; stage 2 may ask the [model](../docs/terminology.md#8-the-pipeline) (for [component classes](../docs/terminology.md#3-schemas) without a row, and for suggestions on `(none)` rows), the others are code:

1. **Pick the [records](../docs/terminology.md#1-records-and-their-text)** (`records.py`, `pick_records`). A record is evaluated if you've finished it in the [ground truth](../docs/terminology.md#4-ground-truth-and-samples) and 060's last [run](../docs/terminology.md#8-the-pipeline) extracted it. Of those, only the **[fair sample](../docs/terminology.md#4-ground-truth-and-samples)**: the longest run of the [pool](../docs/terminology.md#4-ground-truth-and-samples)'s first records that are all evaluated. A record after a gap (an unfinished or unextracted pool record before it) or outside the pool is left out and named, so every evaluated record belongs to a fair sample. Every warning found here (*Checks and warnings*: ground truth problems, records left out, …) is shown before anything is evaluated, and the run asks whether to go ahead (unless `confirm_paid_calls` is false); [the same classed triple twice](../docs/terminology.md#4-ground-truth-and-samples) in a record stops the run.
2. **Translate component classes** (`component_classes.py`, `translate_component_classes`), through `annotations/component_class_mapping.csv`:

   ```
   kind,component_class_from_past_or_crt_schema,component_class_in_gtt,swap_subject_and_object,checked,definition_from_past_or_crt_schema
   entity class,Satellite,Spacecraft,no,yes,A craft that orbits a body.
   predicate,CARRIES,ABOARD,yes,yes,Has on board.         "A CARRIES B" is "B ABOARD A"
   entity class,Gadget,(none),no,yes,A small device.      nothing in the ground truth means this
   entity class,Dataset,Dataset,no,same component class,A set of data.
   ```

   For each component class of the [current schema](../docs/terminology.md#6-extracting-with-a-schema-step-060) without a row: one equal to a component class of the [ground truth vocabulary](../docs/terminology.md#7-evaluating-extraction-step-070) (by [loose match](../docs/terminology.md#3-schemas)) gets a row at once, `checked` = `same component class` (you can still change it in the [annotation tool](../docs/terminology.md#4-ground-truth-and-samples), if the two definitions mean different things; it then needs checking like any other row); the model proposes the others (one [paid call](../docs/terminology.md#8-the-pipeline), after the usual confirmation), `checked` = `no`. The [step](../docs/terminology.md#8-the-pipeline) then stops. You check each `no` row: fix `component_class_in_gtt` (a component class of the ground truth vocabulary, or `(none)`) and `swap_subject_and_object` where wrong, then set `checked` to `yes`. Evaluation runs only once every row it needs is checked. Each row also keeps the current schema's definition of its component class from when it was written or last checked (`definition_from_past_or_crt_schema`). A **[stale](../docs/terminology.md#7-evaluating-extraction-step-070)** row stops the step until you check it again; checking it again stores the new definition. So the one table can serve every schema: a component class keeps its row while its meaning stays the same. The model's proposals are only a first draft: in testing, a stand-in's deliberate mistake (`Phase` → `(none)` instead of `MissionPhase`) is exactly what the check is for.
3. **Compare, record by record** (`pairing.py`, `compare`). Each [extracted triple](../docs/terminology.md#6-extracting-with-a-schema-step-060) is translated into a [translated extracted triple](../docs/terminology.md#7-evaluating-extraction-step-070). Then the occurrences in the record's multiset of translated extracted triples and its ground truth triples are paired, [exact pairs](metrics/pairs.md) first, then [partial pairs](metrics/pairs.md), as [`metrics/pairs.md`](metrics/pairs.md) defines them. Every partial pair is listed in `per_record.md`, and you review the [tuning part](../docs/terminology.md#7-evaluating-extraction-step-070)'s partial pairs in `py helpers/annotate.py`, *Partial pairs*: an occurrence and a [ground truth triple](../docs/terminology.md#4-ground-truth-and-samples) you mark `not the same fact` are never paired.

   Which ground truth triples are [within reach](../docs/terminology.md#7-evaluating-extraction-step-070) or [within strict reach](../docs/terminology.md#7-evaluating-extraction-step-070): [`metrics/recall_upper_bound.md`](metrics/recall_upper_bound.md). The [DESCRIBES rows](../docs/terminology.md#2-triples) are compared only on their [entity class](../docs/terminology.md#3-schemas), apart from the other [classed triples](../docs/terminology.md#2-triples), since code writes the rest of them.
4. **Compute the metrics** (`stats.py`, `compute_metrics`). Precision, recall, F1, [entity-class accuracy](../docs/terminology.md#7-evaluating-extraction-step-070), and the [recall upper bound](../docs/terminology.md#7-evaluating-extraction-step-070), each in its versions: [`metrics.md`](metrics.md#the-metrics). The others, until `metrics.md` has them:

   | Number | Is |
   |---|---|
   | recall within reach | pairs whose ground truth triple is within reach ÷ ground truth triples within reach |
   | strict recall within reach | [strict pairs](metrics/pairs.md) ÷ ground truth triples within strict reach |
   | describes: accuracy | records whose [describes class](../docs/terminology.md#2-triples) is right ÷ records whose ground truth names one |
   | describes: baseline | the share of the most common entity class: what always guessing it would get |
   | describes: per-entity-class average | each entity class's accuracy, averaged, so rare entity classes count as much as common ones |

   Each is given at both [pair levels](metrics/pairs.md) (**exact**, and **partial**, which counts exact and partial pairs), with its **[margin of error](../docs/terminology.md#7-evaluating-extraction-step-070)** by the **[bootstrap](../docs/terminology.md#7-evaluating-extraction-step-070)** (below), for the tuning part, for the [held-out part](../docs/terminology.md#7-evaluating-extraction-step-070) when asked, and per [stratum](../docs/terminology.md#4-ground-truth-and-samples). The [report](../docs/terminology.md#8-the-pipeline) adds a table of what 060 said each record describes versus what it is.

**Then the results** (`results`): `metrics.json`, `per_record.md` and `compared_triples.csv` are written, replacing the last run's; with `--evaluate_held_out true`, a line is added to `annotations/held_out_looks.csv`; the report. The report also lists **component class mismatches** (`pairing.py`, `component_class_mismatches`), possible translation errors, found in the shown parts' classed triples: a wrong or missing row of the [translation table](../docs/terminology.md#7-evaluating-extraction-step-070) leaves a trace where extraction found the fact but a component class differs. A paired extracted triple whose entity class differs from the ground truth's suggests the row of the current schema's entity class is wrong (its row may say `(none)`, or the wrong entity class); an unpaired extracted triple and an unpaired ground truth triple with the same subject and object (or the two swapped) but different predicates suggest the predicate's row is wrong (or its `swap_subject_and_object`). Each mismatch is counted, e.g. *Gadget (current schema) --> (none), met Device (ground truth vocabulary) 9 times*; a single one may just be extraction choosing the wrong component class, a frequent one is a row to check.

The code: `070_evaluate/` holds `run.py` (the [control panel](../docs/terminology.md#8-the-pipeline): inputs, [settings](../docs/terminology.md#8-the-pipeline) and the [moves](../docs/terminology.md#8-the-pipeline), in order); `070_evaluate/070_evaluate_helpers/` holds `moves.py` (the moves, and writing the results), `records.py`, `component_classes.py`, `pairing.py`, `stats.py` and `readings.py` (the metrics read as sentences); `070_evaluate/070_evaluate_prompts/` holds the prompts (see *Prompts*). Shared with other steps: `common/common_helpers/ground_truth.py` (reading the ground truth; the fair sample), `common/common_helpers/text_match.py`, `common/common_helpers/triples_io.py`, `common/common_helpers/files.py` (adding lines without changing any), `common/common_helpers/cache.py`, `common/common_helpers/llm.py`.

### Reading the metrics

A percentage alone is hard to use, so for each part the [report](../docs/terminology.md#8-the-pipeline) also writes every metric out as sentences, filled in with that [run](../docs/terminology.md#8-the-pipeline)'s own counts (section *Reading the metrics* of the report; code: `readings.py`). It starts with **where these numbers come from**: extraction's run and [model](../docs/terminology.md#8-the-pipeline), its [schema](../docs/terminology.md#3-schemas) and how many additions it had (naming any learned from tuning [records](../docs/terminology.md#1-records-and-their-text), which come from the very records being evaluated), the [translation table](../docs/terminology.md#7-evaluating-extraction-step-070), the [ground truth](../docs/terminology.md#4-ground-truth-and-samples) records ([pool](../docs/terminology.md#4-ground-truth-and-samples) positions), the partial [pairs](../docs/terminology.md#7-evaluating-extraction-step-070) reviewed or not, for the [held-out part](../docs/terminology.md#7-evaluating-extraction-step-070) how many times it has been looked at, and where each run's full recipe is (its report's Run, [Settings](../docs/terminology.md#8-the-pipeline), Prompts and Inputs sections).

Then, per metric, the readings that hold for it, such as:

- the counts behind it, e.g. "of the 8 [extracted triples](../docs/terminology.md#6-extracting-with-a-schema-step-060) of these records, 4 (50%) form [exact pairs](metrics/pairs.md)";
- read as a chance, e.g. "an extracted triple has a 50% chance of forming an exact pair";
- what it means for a [knowledge graph](../docs/terminology.md#8-the-pipeline) built from the extracted triples, e.g. "4 of the 8 statements would have no exact counterpart in the ground truth";
- how sure it is: "for the whole catalog, likely between 52% and 70%" (the [margin of error](../docs/terminology.md#7-evaluating-extraction-step-070)), or, with fewer than 20 records, that it has none;
- what it assumes, e.g. that the ground truth lists every [fact](../docs/terminology.md#2-triples) the records state;
- where needed, what it can't see, e.g. [entity-class accuracy](../docs/terminology.md#7-evaluating-extraction-step-070) can't see mix-ups between [component classes](../docs/terminology.md#3-schemas) of the [current schema](../docs/terminology.md#6-extracting-with-a-schema-step-060) that translate to the same component class of the [ground truth vocabulary](../docs/terminology.md#7-evaluating-extraction-step-070).

A metric gets only the readings that apply to it: the [recall upper bound](../docs/terminology.md#7-evaluating-extraction-step-070), for instance, has no "chance" reading, and *what each record describes* is read against what always guessing the most common kind would get.

### The margin of error, and the checks it needs

How it is computed, what it assumes, and how the [report](../docs/terminology.md#8-the-pipeline) checks each assumption: [`070_evaluate/metrics/approximately.md`, *Sampling error*](metrics/approximately.md#sampling-error).

**Per [stratum](../docs/terminology.md#4-ground-truth-and-samples)**, every stratum of the [pool](../docs/terminology.md#4-ground-truth-and-samples) is listed with its number of evaluated [records](../docs/terminology.md#1-records-and-their-text), its share of them and its share of the pool; its numbers appear once it has 20 records. Overall numbers need no weighting, because each stratum had places in proportion to its size. Two more checks:

- the report warns when the evaluated records' mix of strata drifts from the pool's: [`metrics/approximately.md`, *The sample's mix of maintainers*](metrics/approximately.md#the-samples-mix-of-maintainers);
- with many strata, about 1 in 20 margins misses the true value by chance, so one stratum that looks unusually good or bad is not, alone, a finding. The report says so beside the table.

## Prompts

| Prompt file | Sent in | Asks the model to |
|---|---|---|
| `070_evaluate/070_evaluate_prompts/map_component_classes.txt` | [stage](../docs/terminology.md#8-the-pipeline) 2, one call, only for [component classes](../docs/terminology.md#3-schemas) of the [current schema](../docs/terminology.md#6-extracting-with-a-schema-step-060) without a row | for each of those component classes, give the component class of the [ground truth vocabulary](../docs/terminology.md#7-evaluating-extraction-step-070) that means the same thing (or none), and say whether a [predicate](../docs/terminology.md#3-schemas) states the relation in the opposite direction; the ground truth vocabulary's component classes and definitions are shown in the prompt |
| `070_evaluate/070_evaluate_prompts/suggest_component_classes.txt` | stage 2, one call, only when there are both rows of the current schema that say `(none)` and component classes of the ground truth vocabulary nothing translates to; the answer is cached by those two lists, so the same lists are never paid for twice | for each `(none)` component class, whether a component class of the ground truth vocabulary nothing translates to means the same thing (suggest only if confident) |

Each prompt is a plain text file: open it to read exactly what the [model](../docs/terminology.md#8-the-pipeline) is told. `$name` marks where the code fills something in. The prompts use this project's terms (component class, [entity class](../docs/terminology.md#3-schemas), predicate, ground truth vocabulary, current schema), each explained in the prompt. Editing a prompt is allowed: the next [run](../docs/terminology.md#8-the-pipeline) asks again every call that uses it, and pays for them. Its answers are only proposals: you check every row before evaluation uses it.

## Checks and warnings

**Shown before paying**, above the confirmation question (and also in the [report](../docs/terminology.md#8-the-pipeline)'s warnings):

| Message | Meaning | What to do |
|---|---|---|
| *N finished ground truth record(s) weren't extracted by 060's last run* | They can't be evaluated. | Run `py 060_extract/run.py`. |
| *N record(s) are left out because they aren't in the fair sample* | A [pool](../docs/terminology.md#4-ground-truth-and-samples) [record](../docs/terminology.md#1-records-and-their-text) before them isn't finished or extracted, or they're outside the pool. | Finish (or extract) the records before them. |
| *N evaluated record(s) have no stratum* | Not in the pool file. | Normally impossible for pool records. |
| *Ground truth, record … is in batch_… and batch_…: annotated twice* | A record is annotated twice. It's left out of the [ground truth](../docs/terminology.md#4-ground-truth-and-samples) until fixed. | Keep it in one file. |
| *Ground truth, record … (batch_…): all_facts_extracted is 0 on some rows, 1 on others* | Mixed, so the record doesn't count as finished. | Set it the same on every row (the tool's box does). |
| *Ground truth, record … (batch_…): lines … and … are the same classed triple.*, then each line | [The same classed triple twice](../docs/terminology.md#4-ground-truth-and-samples) in one record (a hand edit). Only one copy can be paired, so evaluation would count the other as missed. Also stops evaluation: *Step 070 can't evaluate: N classed triples appear twice in a record of the ground truth, and only one copy could be paired.*, then each one, numbered. | Delete one of the two rows. |
| *Ground truth, record … (batch_…): lines … and … state the same subject instance, predicate, and object instance, with different entity classes.*, then each line | Likely one fact given two [entity classes](../docs/terminology.md#3-schemas) by mistake. | If they state one fact, delete the line with the wrong entity classes. |
| *Ground truth, batch_… lacks the column(s) …; not read* | A ground truth file without one of the columns (see `annotations/README.md`). | Add the column. |

**In the report**, under *Warnings*:

| Message | Meaning | What to do |
|---|---|---|
| *only N record(s) evaluated, fewer than 20* | No [margin of error](../docs/terminology.md#7-evaluating-extraction-step-070); don't draw conclusions yet. | Annotate more; until then, read `per_record.md` rather than the numbers. |
| *some stratum's share … differs from its share of the pool* | The evaluated records' mix of [maintainers](../docs/terminology.md#1-records-and-their-text) differs from the pool's (and so from the catalog's), by chance: the [fair sample](../docs/terminology.md#4-ground-truth-and-samples) is a random sample. | Look at the group table, and read the numbers with that in mind; the difference shrinks as more records are evaluated. |
| *an assumption of the margin of error doesn't hold* | Some ranges are less trustworthy: which assumption, and why, is in the report's section *The margin of error's assumptions, checked* ([`metrics/approximately.md`, *Sampling error*](metrics/approximately.md#sampling-error)). | Usually: annotate more records. A [stratum](../docs/terminology.md#4-ground-truth-and-samples) with only 1 evaluated record, or a range at 0% or 100%, becomes rarer as records are added. |
| *The model suggests N row(s) of component_class_mapping.csv that say (none) may now have a counterpart in the ground truth vocabulary* | The [ground truth vocabulary](../docs/terminology.md#7-evaluating-extraction-step-070) gained [component classes](../docs/terminology.md#3-schemas) since those rows were checked, and the [model](../docs/terminology.md#8-the-pipeline) thinks a different one means the same as the row's component class of the [current schema](../docs/terminology.md#6-extracting-with-a-schema-step-060) (e.g. *Gadget (current schema) --> Device (ground truth vocabulary)*). Rows are never changed by it. | Check the row in `py helpers/annotate.py`, *Translation table* (it shows the suggestion): pick the suggested component class if right, keep `(none)` otherwise. |
| *N partial pair(s) of the tuning part aren't reviewed yet* | The partial level counts [pairs](../docs/terminology.md#7-evaluating-extraction-step-070) nobody has confirmed; some may not be the same [fact](../docs/terminology.md#2-triples) (e.g. `MODIS` vs `MODIS Terra`). | Review them in `py helpers/annotate.py`, *Partial pairs*; rerun 070. |
| *N row(s) of component_class_mapping.csv translate to (none) though the ground truth vocabulary now has the same component class* | A row checked as `(none)` before that component class joined the ground truth vocabulary (you [coined](../docs/terminology.md#7-evaluating-extraction-step-070) it, or added it to the [hand-built schema](../docs/terminology.md#3-schemas)): probably out of date. Not a stop, since `(none)` may still be right if the ground truth's component class means something else. | Check the row in `py helpers/annotate.py`, *Translation table* (it's flagged there); change it to the ground truth vocabulary's component class, or keep `(none)`. |
| *N component class mismatch(es) seen 2 or more times where extraction found the triple but a component class differed* | A row of `component_class_mapping.csv` may translate a component class of the current schema to the wrong one of the ground truth vocabulary, to `(none)` when one fits, or with the wrong `swap_subject_and_object`. | Look at *Component class mismatches* in the report; fix the rows that are wrong (`py helpers/annotate.py`, *Translation table*). |
| *The held-out part was looked at: N time(s) so far* | After `--evaluate_held_out true`: each look is logged and counted. | Commit `annotations/held_out_looks.csv`. |
| *N of M compared triples have no origin, so they can't be traced to the input they came from* | Should never happen: a code change dropped the field that records where each item came from. | Fix the code before using the output. |

**The [step](../docs/terminology.md#8-the-pipeline) stops** with:

| Message | Meaning | What to do |
|---|---|---|
| *Added N row(s) to component_class_mapping.csv …* | New component classes of the current schema. If the model proposed a component class that isn't in the ground truth vocabulary, the row says `(none)` and the message ends by listing them (*The model proposed N component class(es) that aren't in the ground truth vocabulary, written as (none): …*). | Check the rows with `checked` = `no` (easiest in `py helpers/annotate.py`, *Translation table*), then run again. |
| *N checked row(s) of component_class_mapping.csv were checked when the current schema defined the component class differently* | A later [schema](../docs/terminology.md#3-schemas) uses the component class, but defines it differently from when the row was checked: the translation may no longer be right. | Check those rows again in `py helpers/annotate.py`, *Translation table* (it shows both definitions), then run again. |
| *N row(s) of component_class_mapping.csv still need checking* | Rows added by an earlier [run](../docs/terminology.md#8-the-pipeline) aren't checked yet. | Check them in `py helpers/annotate.py`, *Translation table* (or in the CSV: fix `component_class_in_gtt` and `swap_subject_and_object` where wrong, then set `checked` to `yes`), then run again. |
| *N checked row(s) … translate to a component class that isn't in the ground truth vocabulary* | A typo in `component_class_in_gtt`, or one since renamed; each is listed as *component class (current schema) --> component class (not in the ground truth vocabulary)*. | Choose a component class of the ground truth vocabulary, or `(none)`. |
| *component_class_mapping.csv has N component class(es) with more than one row: … (lines …)* | Two rows for one component class (usually from a hand edit), so which translation counts is unclear. | Keep one row per component class: `py helpers/annotate.py`, *Translation table*, shows a *Delete this row* button on each [repeated](../docs/terminology.md#7-evaluating-extraction-step-070) row. |
| *component_class_mapping.csv lacks the column(s) …* | The file's header was changed. | Restore the header: `kind,component_class_from_past_or_crt_schema,component_class_in_gtt,swap_subject_and_object,checked,definition_from_past_or_crt_schema`. |
| *kind must be 'entity class' or 'predicate'* | A typo in `kind`. | Fix it. |
| *Nothing to evaluate yet* | No finished ground truth record that 060 extracted is in the fair sample. | Finish records in `py helpers/annotate.py`, then run 060. |
| *splits.json has no tuning / held-out part* | An old `splits.json`. | Delete 030's `splits.json`, run `py 030_split/run.py`. |
| *missing input files … run 060_extract first* | 060 hasn't run. | Run it. |
| *model must name a model* | The `model` [setting](../docs/terminology.md#8-the-pipeline) is empty. | Give a model's name (`py helpers/models.py` lists them). |
| *Test call to … failed* | Ask Sage refuses you that model, the key is wrong, or Ask Sage can't be reached. Nothing else was called. | If Ask Sage says the model isn't allowed, choose another (`--model`; `py helpers/models.py` lists them). Otherwise check `.env` and the network. |
| *Cancelled. Nothing was spent.* | You declined at the confirmation. | — |
| *Set ASKSAGE_EMAIL and ASKSAGE_API_KEY (e.g. in .env).* | The Ask Sage credentials aren't set, so no model can be called. | Put them in `.env` (see `docs/running_on_nasa_laptop.md`). |

## Audit trail

- **Prompts.** The [report](../docs/terminology.md#8-the-pipeline)'s *Prompts* section lists every prompt the [run](../docs/terminology.md#8-the-pipeline) filled in, each with a [fingerprint](../docs/terminology.md#8-the-pipeline) (sha256) of its exact text, so the prompt behind any answer is known even if the prompt file was edited later (`_manifest.json` keeps the full fingerprints).
- **[Log](../docs/terminology.md#8-the-pipeline).** `outputs/logs/<run id>.log` records the command line, the [settings](../docs/terminology.md#8-the-pipeline), the git commit, the [model call](../docs/terminology.md#8-the-pipeline)'s retries (if any), each [move](../docs/terminology.md#8-the-pipeline)'s duration, each output file's hash and, on failure, the full traceback.
- **[Origin](../docs/terminology.md#8-the-pipeline).** Each row of `compared_triples.csv` has an `origin` column naming the 060 row it compares (`060_extract/extracted_triples.csv#<position>`) and the [ground truth](../docs/terminology.md#4-ground-truth-and-samples) row (`annotations/ground_truth/batch_000.csv#<position>`); the ground truth is made by a person, so a trace stops there.
- **Trace.** `py helpers/audit.py <record id>` follows a [record](../docs/terminology.md#1-records-and-their-text) back through every [step](../docs/terminology.md#8-the-pipeline)'s output to the 010 [batch file](../docs/terminology.md#1-records-and-their-text) and the API request that first returned it (`helpers/audit.md`).
- **[Held-out looks](../docs/terminology.md#7-evaluating-extraction-step-070).** `annotations/held_out_looks.csv` keeps one line per look at the [held-out part](../docs/terminology.md#7-evaluating-extraction-step-070), in Git.

## Known limits

- **Not yet run with the real [model](../docs/terminology.md#8-the-pipeline).** As of 2026-09-29, 070 has been tested only with a hand-made 060 output whose right answers were worked out in advance (all 16 numbers came out as expected), and with synthetic [records](../docs/terminology.md#1-records-and-their-text) for the margins; 060 itself hasn't run with the real model yet, because Ask Sage can't be reached from the laptop it was built on. The numbers in this guide come from those tests, not from a real [run](../docs/terminology.md#8-the-pipeline).
- **One translation per [component class](../docs/terminology.md#3-schemas).** A component class of the [current schema](../docs/terminology.md#6-extracting-with-a-schema-step-060) translates to at most one component class of the [ground truth vocabulary](../docs/terminology.md#7-evaluating-extraction-step-070); if it covers two (e.g. `Instrument` (current schema) for both `Instrument` and `Sensor` (ground truth vocabulary)), pick the closer one.
- **Partial pairing can be fooled**, and doesn't catch the same [fact](../docs/terminology.md#2-triples) in different words ("the satellite" for "Aqua"), which understates precision and recall: see `metrics/[pairs](../docs/terminology.md#7-evaluating-extraction-step-070).md`, *Assumes and can't see*. You review the [tuning part](../docs/terminology.md#7-evaluating-extraction-step-070)'s [partial pairs](metrics/pairs.md); the [held-out part](../docs/terminology.md#7-evaluating-extraction-step-070)'s aren't reviewed until the pipeline is frozen for the final evaluation (looking at them earlier would mean looking at it). Before you review them there (at the final evaluation), the held-out part's partial level may count pairs that aren't the same fact. Its exact level can't be fooled this way, so read the held-out part's exact numbers as its main ones.
- **The [ground truth](../docs/terminology.md#4-ground-truth-and-samples) started as a model's draft**: [recall](../docs/terminology.md#7-evaluating-extraction-step-070) is likely overstated (see [`metrics/recall.md`](metrics/recall.md), *Assumes and can't see*).
- **The threshold of 20 records** for a margin is a rule of thumb.
