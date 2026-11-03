# Reproducing a report's numbers

The NASA TM of 2026-11-03 quotes the numbers of six [runs](../docs/terminology.md#8-the-pipeline): three [repeats](../docs/terminology.md#8-the-pipeline) of extraction (step 060) with the [induced schema](../docs/terminology.md#3-schemas) and three with the [ground truth schema](../docs/terminology.md#3-schemas), each evaluated by step 070. This helper makes those six runs again from the extractions already saved, and says for each number whether it is still the one the report quotes. Free by code: no [model call](../docs/terminology.md#8-the-pipeline).

```
py helpers/reproduce_results.py                       the numbers of docs/reported_numbers.json
py helpers/reproduce_results.py --expected <file>     another report's numbers, in the same form
```

It takes about two minutes on the NASA laptop: on 2026-11-02 each 060 run from the cache took about 2 s and each 070 run about 4 s, and each of the 15 commands below also starts Python anew.

## What it runs

Each command exactly as you would type it, each in its own process, one after the other:

1. For each repeat *n* of the induced schema (1, 2, 3): `py 060_extract/run.py --repeat n`, then `py 070_evaluate/run.py --suggest false`.
2. The same with `--schema annotations/ground_truth_schema.txt` added to each 060 command.
3. `py 060_extract/run.py --repeat 1` once more, so the outputs are left as a normal run leaves them.
4. `py helpers/compare_runs.py` on the three induced-schema runs, and `py helpers/compare_runs.py --across_schemas true --baseline … --changed …` on all six ([`compare_runs.md`](compare_runs.md)).

The first command that doesn't finish stops it, since the commands after it need what that one would have written; its own messages say why, and what to do.

## Why it is free

Every answer 060 needs is in 060's answer cache (`outputs/intermediate_results/060_extract/cache/`) from the runs the report used, and 070 runs with `--suggest false`, which calls no model (`070_evaluate/070_evaluate.md`, *Settings*). The helper first calls `llm.forbid_model_calls`, and that reaches the processes of the steps too (through the environment variable `KG_NO_MODEL_CALLS`, `common/common_helpers/llm.py`). So if a step would need a model call, because an answer is missing from the cache (another computer, or a cache deleted), it stops before its question and before any call, with this message: *060_extract would pay for N model call(s) the cache can't answer (…), but this command calls no model (…), so the run stopped before any request left: nothing was sent and nothing was paid. The answers this needs aren't in 060's cache on this computer …* Run the helper on the computer whose `outputs/` folder holds the report's runs, or copy that folder here first. To make new runs instead, which pays, run the steps themselves.

## The numbers it compares

`docs/reported_numbers.json`, in Git, holds the report's numbers: the report's name, the date of the numbers, the commit of `annotations/` they were made with, the repeats per recipe, the report's six 070 run ids, and each number, written as the report quotes it (a percentage with one decimal, *D* in points, *p* with four significant digits). Each number names one of three kinds:

- `pooled`: a number of `py helpers/compare_runs.py` (for example `partial: f1`, `recall upper bound`, `schema fit`), pooled over the induced schema's repeats, with its 95% range when the entry gives `low` and `high` (the clustered Wilson interval, [`compare_runs.md`](compare_runs.md), *Pooled over the repeats*);
- `repeat`: the same number for one repeat (`"repeat": 2`);
- `decision`: the decision rule across schemas, `partial F1 with the ground truth schema`, `D` or `p` ([`compare_runs.md`](compare_runs.md), *Did a change help?*).

When a later report quotes other numbers, write its own file in this form and give it with `--expected`, or update this one with the report.

## Its report

`outputs/reports/reproduce_results_<date>_<time>.md`, with a log of the same name in `outputs/logs/`: how many numbers are the same; the six new runs (060's and 070's run ids) beside the report's; and each number, the report's value beside its value now, *same* or **differs**. A number differs when something the runs read changed since the report: [the ground truth](../docs/terminology.md#4-ground-truth-and-samples), the [translation table](../docs/terminology.md#7-evaluating-extraction-step-070), the partial-pair [verdicts](../docs/terminology.md#7-evaluating-extraction-step-070), the code, or 060's cache. `git log` since the commit the file names shows what changed in Git.

## Known limits

- **Only on a computer with the report's cache.** The cache is in `outputs/`, which isn't in Git; without it the helper stops before paying, as above.
- **The whole of each report.** It compares the numbers the file names, not every number of the six runs' reports; those reports are in `outputs/reports/`, made by this run.
