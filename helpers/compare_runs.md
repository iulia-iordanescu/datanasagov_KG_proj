# Comparing runs

Is one [recipe](../docs/terminology.md#8-the-pipeline) better than another? To find out whether a change helped, evaluate both recipes (step 070) on the same finished tuning records, then compare them:

```
py helpers/compare_runs.py                                      the evaluations kept so far, with each one's run id
py helpers/compare_runs.py <run id A> <run id B> [<run id C> ...]   compare them; A is the baseline
py helpers/compare_runs.py --across_schemas true <run id A> <run id B> ...   the same, for runs translated differently
py helpers/compare_runs.py --baseline <run id> ... --changed <run id> ...   did the change help? (the decision rule)
py helpers/compare_runs.py --across_schemas true --baseline <run id> ... --changed <run id> ...
                                                                 the decision rule for two groups translated differently
```

Free: no model calls. It writes a report, `outputs/reports/compare_runs_<date>_<time>.md` (`compare_runs_decision_<date>_<time>.md` for the decision rule), and prints where it is.

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

Evaluate each repeat before the next, since 070 reads 060's latest output, and keep 070's own `repeat` at 1, so the three evaluations use the same translation proposals. The report's *Spread across the runs* then gives each number's width across the repeats, the model's own variation on these records. Whether a later change helped is decided by the rule fixed before the runs, on these repeats and the change's (*Did a change help?*, below), not by that width. A vote across repeats (keeping a triple most repeats extracted) isn't built yet (`docs/improvements.md`).

## Did a change help?

Decided on 2026-10-31 and 2026-11-01, before any run it is applied to (`docs/improvements.md`, *The decision rule for "did a change help"*). Run the baseline's repeats and the changed recipe's repeats on the same finished tuning records (each as in *Repeats of one recipe*, above), then:

```
py helpers/compare_runs.py --baseline <070 run id of each baseline repeat> --changed <070 run id of each repeat of the change>
```

*Suppose* the baseline's 3 repeats have the 070 run ids `2026-11-01_1010`, `2026-11-01_1105` and `2026-11-01_1150`, and the change's 3 repeats `2026-11-02_0930`, `2026-11-02_1015` and `2026-11-02_1100`. *Then:* `py helpers/compare_runs.py --baseline 2026-11-01_1010 2026-11-01_1105 2026-11-01_1150 --changed 2026-11-02_0930 2026-11-02_1015 2026-11-02_1100`. It prints the verdict and where the report is.

**The rule** (the report prints the same, from `RULE` in `helpers/compare_runs.py`):

- **The deciding number:** partial F1, chosen before the runs; every other number is shown, not tested.
- **Formula:** for each record *i* and each recipe, the record's counts are averaged over that recipe's runs: *P*(*i*) = 2 × its exact and partial pairs; *Q*(*i*) = its occurrences, less the untranslatable ones and those matching a fact that waits on an expert, + its ground truth triples. A recipe's partial F1 = Σ *P*(*i*) ÷ Σ *Q*(*i*) over the *n* records, and *D* = the changed recipe's partial F1 − the baseline's.
- **The test:** an exact paired permutation (sign-flip) test over records. Each of the 2^*n* ways of swapping the two recipes' (*P*(*i*), *Q*(*i*)) on some of the records gives a *D*\*; *p* = (the number of them with |*D*\*| ≥ |*D*|) ÷ 2^*n*, two-sided. Above 20 records, 100,000 random swaps from a fixed seed instead, and *p* = (that number + 1) ÷ 100,001.
- **The verdict:** *helped* when *D* > 0 and *p* ≤ 0.05; *worse* when *D* < 0 and *p* ≤ 0.05; *can't tell apart* otherwise.
- **The smallest p:** swapping every record gives −*D*, so *p* is never below 2 ÷ 2^*n* = 1 ÷ 2^(*n* − 1); with 5 records or fewer that is above 0.05, so the verdict can only be *can't tell apart*.

**How to read *p*.** If the change made no difference on any record, each record's two results (the baseline's and the change's) would be equally likely either way round, so each of the 2^*n* swaps would be as likely as the one observed. *p* is then the share of them that give a difference at least as large as *D*, in either direction: a small *p* means a difference this large rarely comes from which recipe's label each record's results happened to carry. The model's own variation is inside each record's counts, and the record is what is swapped, so the test needs no assumption about how the numbers are distributed and is exact for any number of records (a property of permutation tests; Dror et al., below, advise a randomization test for a small test set). It says whether the two recipes differ on these records, not by how much on the whole catalog.

**The smallest p, by the number of records.** Swapping every record turns *D* into −*D*, so at least 2 of the 2^*n* swaps always reach |*D*|, and *p* ≥ 1 ÷ 2^(*n* − 1), the case where every record moved the same way and none could be swapped to give a larger difference:

| Records *n* | 1 | 2 | 3 | 4 | 5 | 6 | 10 | 12 | 20 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Smallest *p* | 1 | 0.5 | 0.25 | 0.125 | 0.0625 | 0.03125 | 0.00195 | 0.00049 | 0.0000019 |

So with 5 records or fewer the verdict is always *can't tell apart*, and the report says so. A record with the same counts in both recipes can't move *D*: with *m* records that differ, the smallest reachable *p* is 1 ÷ 2^(*m* − 1), and the report gives it when *m* < *n*. A record with nothing to divide by in either recipe (no occurrence counted and no ground truth triple) is left out of the test and named.

*Suppose* 6 records, and the change raised every record's partial F1, with the same counted occurrences and ground truth triples in both recipes. *Then* only the observed assignment and the one swapping all 6 reach |*D*|: *p* = 2 ÷ 64 = 0.03125, and the verdict is *helped*. *Suppose* the same on 5 records. *Then* *p* = 2 ÷ 32 = 0.0625: *can't tell apart*, though every record went up.

**Repeats of different numbers.** Each record's counts are averaged over its recipe's runs, so a baseline of 5 repeats and a change of 3 compare their means (in the code, each record's sums times the other recipe's number of runs: whole numbers, compared exactly, `paired_parts`). Up to 20 records every swap is counted (2^20 = 1,048,576, a few seconds); above, 100,000 random swaps from the seed `SEED`, and *p* = (the swaps reaching |*D*| + 1) ÷ 100,001, so a sampled *p* is never 0 (Phipson & Smyth, below); the report says which.

**What it checks first, and stops on.** Every run of both recipes must have been evaluated under the same version of what 070 counts (as above), translated the same way (unless `--across_schemas true`, below), and on the same tuning records: a record not evaluated in every run stops it, naming the records, since the rule needs one fair sample in every run. A record whose ground truth, facts waiting on an expert or translation changed between the runs is left out, and the compared set ends before it, as in every comparison (*The records compared*, below). A run given twice, or in both recipes, is refused. A recipe whose runs differ in more than the repeat is said in the report, under *The runs*.

**Across schemas** (added on 2026-11-02). With `--across_schemas true`, the two recipes may be translated differently, each recipe's own runs one way: the induced schema's repeats through the translation table against the ground truth schema's repeats by identity (*Runs translated differently are refused, unless asked for*, below). A recipe whose own runs are translated two ways still stops it. The rule and the test are the same; no record is left out for a different translation of its classed triples' shapes, since that difference is what is compared. The report is titled *Did the change help? A comparison across schemas*, and says at the top that the verdict measures the schema and its translation together, not extraction alone: *helped* means the changed recipe's schema and translation scored higher on these records. The ground truth schema was shaped while annotating these very tuning records, so its recipe is a reference, not a competitor. Without the flag, groups translated differently stop it, as before.

**The report:** the rule; the answer (the verdict, both recipes' partial F1, *D*, *p* and how it was computed, the number of records and the smallest *p* for them); how many records went up, down or stayed the same; each record's partial F1 in both recipes; every other number 070 gives a margin of error, pooled the same way, shown but not tested; the runs; what differs between them (and what the recipe doesn't record, as above); the records compared; and what it can't see:

- **Only these records:** *p* says whether the two recipes differ on these records by more than the model's own variation across each recipe's runs and the records' differences explain; it is not a range for the whole catalog, and it doesn't see mistakes in the ground truth.
- **One change, one number, named before the runs:** the rule's 1-in-20 chance of a wrong *helped* or *worse* holds only then; deciding after looking at several numbers, or trying several changes and keeping the best, raises it.
- **Tuning records only:** compare and choose on the tuning part; evaluate the recipe you report once on the held-out part, at the end (`py 070_evaluate/run.py --evaluate_held_out true`).

**Why only one number.** With about 30 numbers per comparison, some differ by chance (*What it can't see*, below, *Many comparisons*), so the decision rests on one number named before the runs, partial F1 ([F1](../070_evaluate/metrics/f1.md)), and the others are shown only (my choice, decided on 2026-10-31).

**Sources.** Dror, Baumer, Shlomov & Reichart, "The Hitchhiker's Guide to Testing Statistical Significance in Natural Language Processing", ACL 2018, pp. 1383–1392 ([paper](https://aclanthology.org/P18-1128/)): for a statistic whose distribution is unknown (F1) on a small test set, "Use bootstrap or randomization test"; "The (two-sided) p-value of the test is calculated as the proportion of these permutations where the absolute difference was greater than or equal to the absolute value of the difference". Miller, "Adding Error Bars to Evals: A Statistical Approach to Language Model Evaluations", 2024 ([arXiv:2411.00640](https://arxiv.org/abs/2411.00640)), sections 2.2, 3.1 and 4.2: the record is the unit (the cluster), repeats are averaged within it, and two versions are compared paired, on the same records ("We therefore recommend using the paired version of the standard error estimate wherever practicable"). Phipson & Smyth, "Permutation P-values Should Never Be Zero: Calculating Exact P-values When Permutations Are Randomly Drawn", *Statistical Applications in Genetics and Molecular Biology* 9(1), 2010 ([doi:10.2202/1544-6115.1585](https://doi.org/10.2202/1544-6115.1585)), for the + 1 of a sampled *p*.

## What the report says

- **The runs**, A, B, C, …, with 070's run id. A is the baseline; each other run is compared with it.
- **Runs evaluated under different versions of what 070 counts are refused.** When the runs' `evaluation (070) / evaluation_version` (`070_evaluate/070_evaluate_helpers/pairing.py`, `EVALUATION_VERSION`) differ, the comparison stops, saying so and to re-run `py 070_evaluate/run.py` on the same 060 output. Why a stop and not a line under *What differs*: the numbers here are recomputed from each run's kept counts by today's formulas, and a count a later version subtracts is missing from an older run's counts (read as 0): version 3 leaves the untranslatable occurrences out of precision, a count version 2 never kept, so a version-2 run would be recomputed under the old formula while labelled with the new one.
- **Runs translated differently are refused, unless asked for.** A run of 060 with the ground truth schema is evaluated by identity, every component class translated to itself (`070_evaluate/070_evaluate.md`, *Comparing with the ground truth schema*); the others through the translation table. Each run's recipe says which (`evaluation (070) / translation`: "identity (060 used the ground truth schema)" or "the translation table (annotations/component_class_mapping.csv)"; a run before 2026-11-01 records nothing and used the table), and the table *The runs* shows it. A comparison mixing the two stops, saying so, since a difference between them comes from the schema and its translation together, not from extraction alone. With `--across_schemas true` it goes ahead as a comparison across schemas: the report is titled *Comparing evaluations across schemas* (with the decision rule, *Did the change help? A comparison across schemas*), says so at the top, and doesn't leave records out for a different translation of their classed triples' shapes (that difference is what is compared). Runs whose induced schemas differ, both through the table, are not yet flagged (`docs/improvements.md`, *Comparing runs whose schemas differ*).
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
