# Held-out results

What did each recipe score on the held-out part? Step 070 shows a run's held-out numbers in that run's report (`--evaluate_held_out true`) and keeps the held-out records' counts. This helper summarizes the held-out looks kept: by recipe, pooled over the repeats, also by who drafted the ground truth, with and without records you choose to leave out.

```
py helpers/held_out_results.py                                      the held-out looks kept so far, with each one's run id
py helpers/held_out_results.py <run id> <run id> ...                summarize them, by recipe, pooled over the repeats
py helpers/held_out_results.py --leave_out 101,119,125 <run id> ... also without these records (pool positions or record ids)
```

Free: no model calls, by code. It runs no step and adds no look. It reads `outputs/intermediate_results/070_evaluate/held_out_evaluations/` and `annotations/held_out_looks.csv`, writes a report, `outputs/reports/held_out_results_<date>_<time>.md`, and prints where it is. Every number in the report was already shown by the run that looked.

## Where the looks come from

A run of step 070 with `--evaluate_held_out true` that evaluates at least one held-out record is a held-out look. It adds one line to `annotations/held_out_looks.csv` and keeps `held_out_evaluations/<run id>.json`: the held-out records' counts (also by who drafted the ground truth, since 2026-11-16), the run's recipe, and that line with its number among the looks (`070_evaluate/070_evaluate.md`, *Outputs*). A run that didn't look keeps no such file. The tuning records' counts stay in `evaluations/`, the only folder `py helpers/compare_runs.py` reads. A look made before 2026-11-16 has a line in the log and no counts kept. The files are in `outputs/`, which isn't in Git, so they stay on the computer that ran 070: keep the folder until the results are reported.

## One look per extraction

*Suppose* three models extracted, 5 repeats each (060's setting `repeat`, 1 to 5), and the ground truth, the guidelines, the ground truth schema and the translation table are frozen. *Then:* each of the 15 runs of step 060 is evaluated once with `py 070_evaluate/run.py --extraction_run <060 run id> --evaluate_held_out true`, which makes 15 looks, and `py helpers/held_out_results.py <the 15 run ids of 070>` gives each model's numbers pooled over its 5 repeats.

Step 070 evaluates one run of step 060 per run: 060's latest by default, or the run named with `--extraction_run <060 run id>`, whose four files (`extracted_triples.csv`, `extracted_triples_removed.csv`, `extracted_triples_details.json`, `schema_used.json`) it finds as that run wrote them. `previous_runs/<060 run id>/` holds only the files the next run changed, so a file missing there is the copy kept in a later run's folder, or the live one: the one with the sha256 that the run's `_manifest.json` records for it (`common/common_helpers/step.py`, `output_of_run` and `gather_run`). Step 070 reads them beside that manifest, copied into its own `extractions/<060 run id>/` when they aren't all in the run's folder. When the run isn't kept, or a file has no copy left, it stops before anything is evaluated, so no look is logged (`070_evaluate/070_evaluate.md`, *Scoring a kept run of 060*). The look's line in `annotations/held_out_looks.csv` names the run scored (`extraction_run_id`).

Two looks at one extraction can't be summarized together, since its repeat would count twice: the command stops and lists them (`same_extraction` in `helpers/compare_runs.py`, the check that also refuses two evaluations of one run of 060 as repeats there). Give one of them; the report says how many looks the log holds for that extraction.

## What the report says

- **The looks.** One row per run: 070's run id, 060's run id, the service and model, the repeat, the date, the look's number in the log, how many lines of the log are looks at the same run of step 060 (*Looks at this extraction*: more than 1 means its held-out numbers were shown more than once), the held-out records evaluated, and the look's two fingerprints (of the translation used, and of the held-out records' ground truth). Under the table: whether each fingerprint is the same in every look summarized; each extraction looked at more than once, with the runs of 070 that looked and whether a fingerprint changed between those looks (a change made after a look lets the held-out records influence the pipeline); each kept look whose line isn't in the log exactly once; and how many looks of the log are not summarized.
- **What differs between the groups.** Runs whose recipes differ only in the repeat and in parts that change neither what the model is asked nor how its answers are scored (run ids, code versions, how the calls were sent and paid for: `helpers/compare_runs.md`, *Spread across the runs*) are one group, the repeats of one recipe. With one recipe per extraction model, each group is one model. The table lists every other part of the recipes that differs between the groups. Two runs of one model whose recipes differ in something else (a prompt, the thinking setting) are two groups, and the report says so: they aren't repeats of one recipe, so they aren't pooled.
- **Each group: the records pooled.** The held-out records evaluated in every run of the group, with the same ground truth, the same facts waiting on an expert and the same translation of their classed triples' shapes, up to the first one left out in pool order (`common_records` in `helpers/compare_runs.py`, the rule comparisons use). Each record left out is listed with why.
- **Each group: pooled over the repeats.** Every number step 070 gives a margin of error, over all the group's repeats: each record's counts are averaged over the runs, and the 95% range is 070's clustered Wilson interval over the records (`070_evaluate/metrics/approximately.md`, *Sampling error*). The pooling is the one of `helpers/compare_runs.md`, *Pooled over the repeats*, after Miller, "Adding Error Bars to Evals: A Statistical Approach to Language Model Evaluations", 2024, [arXiv:2411.00640](https://arxiv.org/abs/2411.00640), sections 2.2 and 3.1. The record stays the cluster, so the repeats narrow the range only as much as the model's own variation they average away. For precision, recall and F1, a second column gives a record-level bootstrap range (`helpers/compare_runs.md`, *Pooled over the repeats*).
- **Each group: by who drafted the ground truth.** The group's ground truth triples split by the model that drafted their rows (column `drafted_by`, every spelling of one model name together), as in 070's subsection *By who drafted the ground truth* (`070_evaluate/070_evaluate.md`, *Shared-model bias*), with 070's own grouping code (`stats.py`, `group_parts`). For each drafting model: recall at both levels, the exact share of pairs and entity-class accuracy, which are numbers of that model's own ground truth triples and pairs, and precision and F1 as 070's attributed values: an extracted triple left without a pair belongs to no drafting model, so it counts against each alike. Each is pooled over the repeats as the numbers above, the record staying the cluster, and given without the records left out on request too. A look kept before 2026-11-16 has no counts by drafting model, and a `drafted_by` cell changed between two looks of the group would mix two splits; in either case the report says so and gives no numbers by drafting model.
- **Each group: each repeat.** Each run's own value on the same records, and the lowest, the highest, the mean and the width across the repeats.

## Leaving records out

`--leave_out` takes pool positions (`101` or `#101`) or record ids, separated by commas. Each group's table then has two more columns: the same numbers without those records. A value that is no held-out record of the runs given stops the command before anything is written, and the message gives the value. A record left out that isn't among a group's pooled records changes nothing there, and the report says so.

Why: a held-out record whose text nearly repeats another record's isn't caught by the check for twins, which compares titles and `notes` for equality. The numbers with and without such records show how much they move the result. The records that remain are no longer the first records of the held-out part of the pool, so their columns are a second reading beside the first, not a fair sample of their own.

## What it can't see

The report ends with the same list (`LIMITS` in `helpers/held_out_results.py`):

- **Only the looks kept on this computer:** a look's counts are in `outputs/`, which isn't in Git; a look made on another computer, or before 2026-11-16, has a line in `annotations/held_out_looks.csv` and no counts here.
- **Only these records:** a range covers which records happened to be evaluated, not mistakes in the ground truth. Pooling over the repeats averages away part of the model's own variation and nothing else.
- **Partial pairs of the held-out part are never reviewed** (that would mean looking at it), so the partial level may count pairs that aren't the same fact.
- **The groups share their records:** two recipes' ranges that overlap don't show the recipes alike, and ranges apart don't prove them different; this helper tests no difference between recipes.
- **Leaving records out is a second reading, not a new sample:** the records left are no longer the first records of the held-out part of the pool, so their numbers are shown beside the full ones, never instead.
