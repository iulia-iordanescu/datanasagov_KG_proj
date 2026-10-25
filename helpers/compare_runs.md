# Comparing runs

Is one [recipe](../docs/terminology.md#8-the-pipeline) better than another? To find out whether a change helped, evaluate both recipes (step 070) on the same finished tuning records, then compare them:

```
py helpers/compare_runs.py                                      the evaluations kept so far, with each one's run id
py helpers/compare_runs.py <run id A> <run id B> [<run id C> ...]   compare them; A is the baseline
```

Free: no model calls. It writes a report, `outputs/reports/compare_runs_<date>_<time>.md`, and prints where it is.

## Making two recipes to compare

*Suppose* you want to know whether extracting with another model helps. *Then:*

1. Extract and evaluate with the first model: `py 060_extract/run.py --service litellm --model claude-opus-5.5`, then `py 070_evaluate/run.py`. Note 070's run id (top of its report, or the newest file in `outputs/intermediate_results/070_evaluate/evaluations/`).
2. The same with the other model: `py 060_extract/run.py --service litellm --model gemini-3.1-pro-preview` (not `gemini-2.5-pro`, the model step 050 drafts with: step 060 warns about it, since it inflates recall), then `py 070_evaluate/run.py`.
3. Compare: `py helpers/compare_runs.py <first run id> <second run id>`.

Change one thing at a time, so a difference has one cause.

## What the report says

- **The runs**, A, B, C, …, with 070's run id. A is the baseline; each other run is compared with it.
- **What differs between the runs:** every part of each run's recipe that isn't the same in every run. From 060's run: its code version, settings (service and model among them), prompts by fingerprint, and the schema files it read, by fingerprint. From 070's run: its code version, settings (service and model among them), and the translation (the translations it used), by fingerprint. A difference in the numbers comes from one of these, or from the partial-pair verdicts (`annotations/partial_pair_reviews.csv`), which the recipe doesn't hold yet: review no partial pairs between the runs you compare.
- **The records compared:** the tuning records evaluated in every run, with the same ground truth in every run. A record whose ground truth changed between the runs (you corrected it in between) is left out and named, since a difference there could come from your correction rather than the recipe. Held-out records are never compared.
- **One table per run compared with the baseline:** for each number (precision, recall, F1, and the others 070 gives a margin of error), the baseline's value, the other run's, the difference in points, the 95% range of the difference, and a verdict, one of six: *<run> higher* or *<run> lower* (the whole range is above, or below, 0), *can't tell apart* (the range holds 0), *the same* (no difference, and a range of 0 or none), *no range (too few records)*, or *not comparable (a number is missing)* (one run has no value for it).

## How the range is computed

By a paired bootstrap, the standard way to compare two systems on one test set: the same records are drawn at random, with repeats, as many as were compared, the same draw for both runs; the difference is recomputed; this is done 1,000 times, and the middle 95% of the differences is the range. Drawing the same records for both runs is what makes it *paired*: a hard record is hard for both, so the range of the difference is much narrower than the two runs' own margins of error, and a real difference shows sooner. A range all above 0 means higher by more than chance; all below 0, lower; one that includes 0, the two can't be told apart on these records. Below 20 records, no range is given (as for 070's own margins). The numbers are computed by 070's own code (`070_evaluate/070_evaluate_helpers/stats.py`), so they are exactly 070's.

## Where the evaluations come from

Each run of step 070 keeps its tuning records' counts and its recipe in `outputs/intermediate_results/070_evaluate/evaluations/<run id>.json`, one file per run, never overwritten (`070_evaluate/070_evaluate.md`, *Outputs*). They are in `outputs/`, so they stay on the laptop that ran 070 and are lost if `outputs/` is deleted; copy the folder to compare runs made on two laptops.

## What it can't see

- **Many comparisons:** about 1 in 20 ranges misses by chance, so among many rows, one *higher* or *lower* alone is not a finding; a change that shows on several related numbers is.
- **Only these records:** the range covers which records happened to be evaluated, not mistakes in the ground truth, nor a model answering differently on another run of the same recipe (temperature 0 makes that rare, not impossible).
- **Tuning records only:** compare and choose on the tuning part; evaluate the recipe you report once on the held-out part, at the end (`py 070_evaluate/run.py --evaluate_held_out true`).
