# Comparing runs

Is one [recipe](../docs/terminology.md#8-the-pipeline) better than another? To find out whether a change helped, evaluate both recipes (step 070) on the same finished tuning records, then compare them:

```
py helpers/compare_runs.py                                      the evaluations kept so far, with each one's run id
py helpers/compare_runs.py <run id A> <run id B> [<run id C> ...]   compare them; A is the baseline
py helpers/compare_runs.py --across_schemas true <run id A> <run id B> ...   the same, for runs translated differently
```

Free: no model calls. It writes a report, `outputs/reports/compare_runs_<date>_<time>.md`, and prints where it is.

## Making two recipes to compare

*Suppose* you want to know whether extracting with another model helps. *Then:*

1. Extract and evaluate with the first model: `py 060_extract/run.py --service litellm --model claude-opus-5-5`, then `py 070_evaluate/run.py`. Note 070's run id (top of its report, or the newest file in `outputs/intermediate_results/070_evaluate/evaluations/`).
2. The same with the other model: `py 060_extract/run.py --service litellm --model gemini-3.1-pro-preview` (not `gemini-2.5-pro`, the model step 050 drafts with: step 060 warns about it, since it inflates recall), then `py 070_evaluate/run.py`.
3. Compare: `py helpers/compare_runs.py <first run id> <second run id>`.

Change one thing at a time, so a difference has one cause.

## Repeats of one recipe

One run of a recipe isn't a baseline: the model can answer differently on another run, and a rerun reuses the saved answers, so it can't show how much. Every step that calls the model has the setting `repeat`: `1` (the default) reuses the saved answers, and `2`, `3`, ... ask again, each repeat into cached answers of its own (`common/common_helpers/llm.py`, `REPEAT`). So, for the noise floor of extraction:

1. `py 060_extract/run.py --repeat 1`, then `py 070_evaluate/run.py`; note 070's run id.
2. `py 060_extract/run.py --repeat 2`, then `py 070_evaluate/run.py`; note its run id.
3. `py 060_extract/run.py --repeat 3`, then `py 070_evaluate/run.py`; note its run id.
4. `py helpers/compare_runs.py <id 1> <id 2> <id 3>`.

Evaluate each repeat before the next, since 070 reads 060's latest output, and keep 070's own `repeat` at 1, so the three evaluations use the same translation proposals. The report's *Spread across the runs* then gives each number's width across the repeats: a later change is a real improvement only where it moves a number by more than that width, and its comparison with one repeat should be read against it. A vote across repeats (keeping a triple most repeats extracted) isn't built yet (`docs/improvements.md`).

## What the report says

- **The runs**, A, B, C, …, with 070's run id. A is the baseline; each other run is compared with it.
- **Runs evaluated under different versions of what 070 counts are refused.** When the runs' `evaluation (070) / evaluation_version` (`070_evaluate/070_evaluate_helpers/pairing.py`, `EVALUATION_VERSION`) differ, the comparison stops, saying so and to re-run `py 070_evaluate/run.py` on the same 060 output. Why a stop and not a line under *What differs*: the numbers here are recomputed from each run's kept counts by today's formulas, and a count a later version subtracts is missing from an older run's counts (read as 0): version 3 leaves the untranslatable occurrences out of precision, a count version 2 never kept, so a version-2 run would be recomputed under the old formula while labelled with the new one.
- **Runs translated differently are refused, unless asked for.** A run of 060 with the ground truth schema is evaluated by identity, every component class translated to itself (`070_evaluate/070_evaluate.md`, *Comparing with the ground truth schema*); the others through the translation table. Each run's recipe says which (`evaluation (070) / translation`: "identity (060 used the ground truth schema)" or "the translation table (annotations/component_class_mapping.csv)"; a run before 2026-11-01 records nothing and used the table), and the table *The runs* shows it. A comparison mixing the two stops, saying so, since a difference between them comes from the schema and its translation together, not from extraction alone. With `--across_schemas true` it goes ahead as a comparison across schemas: the report is titled *Comparing evaluations across schemas*, says so at the top, and doesn't leave records out for a different translation of their classed triples' shapes (that difference is what is compared). Runs whose induced schemas differ, both through the table, are not yet flagged (`docs/improvements.md`, *Comparing runs whose schemas differ*).
- **What differs between the runs:** every part of each run's recipe that isn't the same in every run. From 060's run: its code version, settings (service and model among them), how its model calls were sent (the exact model that answered, the answer limit, temperature, thinking and effort), prompts by fingerprint, and the schema files it read, by fingerprint. From 070's run: its code version, its matching version (what counts as the same subject instance or object instance; `(not recorded)` for a run before 2026-10-24, which compared quantities as words), the service and model it asked, the translation (the translations it used), by fingerprint, the facts that wait on an expert (`facts_waiting_on_an_expert`: that occurrences matching them were left out of precision, how many there were, and their rows of `annotations/pending_triples.csv` by fingerprint; `(not recorded)` for a run before 2026-10-31, which counted those occurrences against precision), and the untranslatable occurrences (`untranslatable_occurrences`: that they were left out of precision, and the predicate rows to `(none)` by fingerprint; `(not recorded)` before evaluation version 3). A difference in the numbers comes from one of these, or from what the recipe doesn't record, all of it (the report lists the same, from `UNRECORDED` in `helpers/compare_runs.py`):
  - **The records' text:** 020's `records.jsonl` (the text the model read) isn't in the recipe; a new harvest between the runs changes it unseen.
  - **Code not committed:** the code version is the Git commit; a change not committed when a run was made is invisible.
  - **070's model call settings:** of 070's settings, only the service and the model are recorded (not its thinking cap); its translation is recorded by fingerprint, so a different translation shows anyway.
  - **The partial-pair verdicts** (`annotations/partial_pair_reviews.csv`): review no partial pairs between the runs you compare.
  - **The model's own variation:** the same recipe can answer differently on another run (no setting makes a model answer the same every time), and a cached answer is reused, so two runs of one recipe usually agree; repeats of one recipe (060's setting `repeat`: 2, 3, ...) are asked again, so their *Spread across the runs* measures it.
- **The records compared:** the tuning records evaluated in every run, with the same ground truth, the same facts waiting on an expert (`annotations/pending_triples.csv`) and the same translation of their classed triples' shapes (`annotations/component_class_mapping.csv`, for the shapes the record has in every run) in every run. A record differing in any of these (you corrected it in between) is left out and named, since a difference there could come from your correction rather than the recipe; each run of 070 keeps these three per record (`evaluations/<run id>.json`; a run before 2026-11-01 kept the ground truth only, and the report then says what it couldn't check). The records kept must still be the first records of the pool (a fair sample), so the compared set ends before the first record left out, in pool order, and the records after it are left out too, named *after a record left out, so no longer the first records of the pool*. The same run given twice is refused (a run compared with itself shows nothing). Held-out records are never compared.
- **Spread across the runs:** for each number, every run's value, the lowest, the highest, the mean, and the width (highest − lowest). When the runs are repeats of one recipe (only 060's `repeat` differs, besides 060's run id), the report says so: the width is then the model's own variation on these records, the noise floor (*Repeats of one recipe*, below).
- **One table per run compared with the baseline:** for each number (precision, recall, F1, and the others 070 gives a margin of error), the baseline's value, the other run's, the difference in points, the 95% range of the difference, and a verdict, one of six, the first that applies in this order: *not comparable (a number is missing)* (one run has no value for it); *the same* (no difference, and a range of 0 or none); *no range (one record)*; *<run> higher* or *<run> lower* (the whole range is above, or below, 0); *can't tell apart* (the range holds 0).

## How the range is computed

By a paired bootstrap, the standard way to compare two systems on one test set (Koehn, "Statistical Significance Tests for Machine Translation Evaluation", EMNLP 2004, [paper](https://aclanthology.org/W04-3250/)): the same records are drawn at random, with repeats, as many as were compared, the same draw for both runs; the difference is recomputed; this is done 10,000 times (`REDRAWS`, from a fixed seed, `SEED`; Hesterberg 2015, section 3.6: "We suggest r = 10000 for routine use"), and the range is the expanded percentile range of the differences (Hesterberg, "What Teachers Should Know About the Bootstrap: Resampling in the Undergraduate Statistics Curriculum", *The American Statistician*, 2015, [arXiv:1411.5279](https://arxiv.org/abs/1411.5279), sections 1.1 and 5.3): with *n* records, the values at positions α′/2·(*k* − 1), rounded down, and (1 − α′/2)·(*k* − 1), rounded up, of the *k* sorted differences, where α′/2 = Φ(−√(*n* ÷ (*n* − 1)) × *t*<sub>0.975, *n* − 1</sub>), below the plain 0.025, to make up for the bootstrap's narrowness in small samples (`interval` and `expanded_alpha` in `helpers/compare_runs.py`); a redraw where a number is undefined in either run is skipped, and the row then says from how many redraws its range comes. Drawing the same records for both runs is what makes it *paired*: a hard record is hard for both, so the range of the difference is much narrower than the two runs' own margins of error, and a real difference shows sooner. A range all above 0 means higher by more than chance; all below 0, lower; one that includes 0, the two can't be told apart on these records. From 2 records on there is a range; below 10 the report says each range is a rough width; with one record, none (verdict *no range (one record)*). The numbers are computed by 070's own code (`070_evaluate/070_evaluate_helpers/stats.py`), so they are exactly 070's.

This is a second method in a second place, on purpose: 070's own margins of error are clustered Wilson intervals ([`070_evaluate/metrics/approximately.md`](../070_evaluate/metrics/approximately.md#sampling-error), *Sampling error*), which are for a proportion, and a difference of two proportions is not one.

**Pooled over the repeats.** When the runs are repeats of one recipe, the report also gives each number over all the repeats, with its range by 070's clustered Wilson interval: each record's counts are averaged over the runs and the record stays the cluster (Miller, "Adding Error Bars to Evals: A Statistical Approach to Language Model Evaluations", 2024, [arXiv:2411.00640](https://arxiv.org/abs/2411.00640), sections 2.2 and 3.1), so the repeats narrow the range only as much as the model's own variation they average away. Beside it, the variance between records (of each record's own proportion) and the mean variance within a record across the repeats: when the first is much larger, more records would narrow the range more than more repeats would (reasonable practice; no source gives a threshold).

## Where the evaluations come from

Each run of step 070 keeps its tuning records' counts and its recipe in `outputs/intermediate_results/070_evaluate/evaluations/<run id>.json`, one file per run, never overwritten (`070_evaluate/070_evaluate.md`, *Outputs*). They are in `outputs/`, so they stay on the laptop that ran 070 and are lost if `outputs/` is deleted; copy the folder to compare runs made on two laptops.

## What it can't see

The report ends with the same list (`LIMITS` in `helpers/compare_runs.py`):

- **Many comparisons:** about 1 in 20 ranges misses by chance, so among many rows, one *higher* or *lower* alone is not a finding; a change that shows on several related numbers is.
- **Only these records:** the range covers which records happened to be evaluated, not mistakes in the ground truth, nor a model answering differently on another run of the same recipe.
- **Tuning records only:** compare and choose on the tuning part; evaluate the recipe you report once on the held-out part, at the end (`py 070_evaluate/run.py --evaluate_held_out true`).
