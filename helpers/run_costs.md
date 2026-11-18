# Cost and time of the runs

What did each [run](../docs/terminology.md#8-the-pipeline) of step 060 cost, and how long did it take? `py helpers/run_costs.py` puts every kept run of step 060 in one table:

```
py helpers/run_costs.py                       the table, from what the runs' records and reports keep
py helpers/run_costs.py --fetch_times true    the same, and each older batch job's times read from its maker
```

Free: no model calls. It writes `outputs/reports/run_costs_<date>_<time>.md` (the table) and `outputs/reports/run_costs_<date>_<time>.csv` (the same rows, the processing times and wall times also in seconds), and prints where they are.

## What it reads

The kept run records of step 060: `outputs/intermediate_results/060_extract/previous_runs/<run id>/extracted_triples_details.json` for every earlier run, and `outputs/intermediate_results/060_extract/extracted_triples_details.json` for the latest. Beside each record it reads the run's `_manifest.json` (its start and end, its schema input) and `schema_used.json` (whether the schema was the ground truth schema). A run that stopped before it finished keeps no record, so it has no row; its report still gives its tokens.

## The table

One row per run, oldest first:

| Column | What it holds |
|---|---|
| Run id, Model, Service, Thinking, Repeat | From the record's `made`: the model, the service that reached it, the setting `thinking` and the setting `repeat`. |
| Schema | `ground truth` when the run extracted with the ground truth schema (`schema_used.json`, `made`, `ground_truth_schema`, or the schema input's path), `induced` when with the schema step 040 induced, else the schema file's path. |
| Records | The records chosen, and how many of them were extracted. |
| Input tokens, Cache read, Cache write, Output tokens, Thinking tokens | The service's token counts for the run: sent and not read from the cache, read from the cache, written to the cache (both lifetimes), received (thinking included), and of those received, the thinking. |
| Cost $ | In US dollars, as the run's record computed it: from the token counts and each maker's list prices (`PRICES` in `common/common_helpers/llm.py`), each batch request at the batch price and each single request at the standard price. Not the maker's invoice. |
| Job processing time | Each batch job's end minus its creation, as its maker reported them (`–` for a run without batch jobs). |
| Run wall time | From the run's start to when its record was written. |
| Notes | Where a number came from when the record doesn't keep it, and why a value is `unknown` or `not recorded`. |

## Runs recorded before their cost was kept

A run's record keeps its tokens by price, its cost, its wall time and its jobs' times under `made` (`spent`, and each job in `batch_jobs`). An older record keeps none of these, so for such a run:

- **Tokens** come from the run's report (`outputs/reports/<run id>.md`, *Model calls*, its tokens table). Without a report they are `not recorded`.
- **Cost** is computed from those totals only when every token was billed at one price. That holds for a run of single requests, and for a batch run whose report shows no test call and no reply asked again and whose jobs asked no cut answer again. It also needs a model with one price at every prompt length, or a run whose input tokens, all prompts together, are no more than the length above which the higher price applies. Anthropic's cache writes are then priced at the lifetime the code sends: 5 minutes in a single request, 1 hour in a batch request. Otherwise the cost is `not recorded`, and the notes say why.
- **Job processing time** is `not recorded`, unless `--fetch_times true` reads the job's times from its maker by the job's id: Anthropic's `GET /v1/messages/batches/{id}`, OpenAI's `GET /v1/batches/{id}`, Google's `batches.get`. These requests read a job's state and times, never a model's answers; they need the maker's key in `.env`. A job whose times can't be read stays `not recorded`, and the notes say why.
- **Run wall time** is the manifest's start to its end.

A cost is `unknown` when it can't be computed from a price: a run through LiteLLM or Ask Sage (each bills its own account, and the prices kept are those of the makers' own APIs), a model `PRICES` doesn't list, a date no listed price covers, or tokens of a kind with no listed price. The notes say which.

## What it can't see

- **The maker's invoice.** The cost is the token counts times the list prices read on 2026-11-18. A credit, a tax, a discount of the account or a later change of price doesn't show in it.
- **Runs without a record.** A run that stopped before it finished leaves no record, so its tokens are not in the table. A batch job such a run sent is counted by the run that collected it.
