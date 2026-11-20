# Exporting results

The runs' evaluations, reports and output files are in `outputs/`, which Git leaves out, so the numbers behind a publication exist only on the laptop that made them. This helper writes them, with every record, triple and model call they come from, into a folder that is committed:

```
py helpers/export_results.py                                    the runs of results/technical_publication/runs.tsv, into that folder
py helpers/export_results.py --runs <list.tsv> --out <folder>   another run list, into another folder
```

Free: no model calls, by code. It runs no step and changes nothing in `outputs/` or `annotations/`. It prints each file it wrote with its rows and size, and names any file of a run that no longer has a copy. It takes about two minutes.

## What it reads

- **The run list:** a tab-separated file, lines starting with `#` being comments. A tuning line gives the schema, the thinking setting, the model, the repeat, 070's run id of its tuning records, and 060's run id; a held-out line gives `held-out` and 070's run id of a held-out look. A look finds its model and repeat through the run of step 060 it scored, which must be a tuning line's; a line of another shape stops the helper, naming it.
- **The evaluations step 070 kept:** `evaluations/<run id>.json` for the tuning lines (as `py helpers/compare_runs.py` reads them) and `held_out_evaluations/<run id>.json` for the looks (as `py helpers/held_out_results.py` reads them).
- **Each run's own files:** 060's `extracted_triples.csv`, `extracted_triples_removed.csv` and `extracted_triples_details.json`, 070's `compared_triples.csv`, and 040's `induction_evidence.json`, each as that run wrote it: the copy with the sha256 the run's manifest records, live or in `previous_runs/` (`output_of_run` in `common/common_helpers/step.py`). Another run's version is never read in its place; a file with no copy left is named and left out.
- **The runs' reports** (`outputs/reports/<run id>.md`): 060's extraction figures and the token counts of steps 040 and 060.
- **The records' text** (020's `records.jsonl`), the pool (030's `splits.json`), the ground truth (`annotations/ground_truth/`, through `common/common_helpers/ground_truth.py`), and `annotations/second_opinion.csv` and `annotations/second_judge.csv`.

## How the numbers are computed

By the functions the other helpers' reports use, so a number here is the number of their reports:

- **Pooled over the repeats:** `compare_runs.pooled` over the records `compare_runs.common_records` keeps (`helpers/compare_runs.md`, *Pooled over the repeats*): the clustered Wilson range, the bootstrap range of precision, recall and F1, and the variances between and within records.
- **Each run's own values and their spread:** `compare_runs.spread`, with the sample standard deviation across the runs added.
- **The two describes numbers without a range** (the majority baseline and the per entity class average): step 070's `stats.numbers` over every record of every repeat taken together.
- **By drafting model:** `held_out_results.by_drafting_model`, for the tuning groups too.
- **Per record:** step 070's `stats.per_record`, run by run; a record's number over a group's runs comes from its counts summed over them (`compare_runs.group_parts`).
- **The induction-duplicate kind:** `common.ground_truth.twin_kinds`, of each finished record against the induction texts (the same as step 070's per record).

What each file holds, column by column, is in the folder's own `README.md` (`results/technical_publication/README.md` for the Technical Publication).

## What it can't give

- **Token counts per model call:** the runs record tokens per run (each report's *Tokens* table), so the files give them per run.
- **Which service served a run, and what it cost:** left out on purpose, though the reports have both.
- **A run list's files kept elsewhere:** a run whose files are no longer in `outputs/` (deleted, or made on another laptop) is named, not exported; copy its folders into `outputs/` first.
