# 030_split

Terms (ground truth candidates pool, induction candidates, tuning part, held-out part, …) are as defined in [docs/terminology.md](../docs/terminology.md), especially section *Ground truth and samples*.

## Purpose

Sets the two lists of records that later steps work on, and keeps them apart:

- **The ground truth candidates pool**: 1,000 records that are candidates for annotation. A person annotates them in pool order, and the annotated records become the ground truth that 070 evaluates the extraction against. Only a subset of the pool is ever annotated, since verifying 1,000 records by hand is more than the time available. The pool was shuffled when it was drawn, so the first *k* records are a fair sample of the catalog for any *k*, and annotation can stop anywhere.
- **The induction candidates**: for every maintainer, all of its records that the schema may be learned from, in a fixed random order. 040 learns the schema from the first few of each of the largest maintainers.

Each ground truth candidate is also given its **part**, for evaluation in 070: **tuning** (its metrics may be looked at while improving the pipeline) or **held-out** (its metrics are kept aside and looked at only at the end, as the number reported for how well the pipeline works). The rule is fixed here, before any evaluation: pool positions 0–5 are tuning, since the hand-built schema was written while annotating them; from position 6 on, every third record is held-out (8, 11, 14, …) and the rest tuning. Both parts grow as annotation proceeds, and both stay random samples of the catalog. Of the 999 candidates on 2026-09-29: 668 tuning, 331 held-out.

No record is ever in both lists. 070 measures how well extraction works on text the schema was *not* learned from; evaluation on records the schema was learned from would flatter it.

**Both lists are in a fixed random order, and later steps take from the top.** Taking more later keeps what was already taken: if 040 learns from 15 records per maintainer today and 30 tomorrow, the first 15 are the same records, so the model calls already paid for them stay valid. The same holds for adding maintainers.

**The pool is not drawn here.** It was drawn once, on 2026-09-21, by the earlier `ground_truth_sampler.py`, and annotation has started on it, so it must never change. It is kept in `annotations/ground_truth_candidates.csv`, in Git; 030 reads it. The induction candidates are ordered here.

## To do

### Every step

- **Run it** after the steps before it, and again whenever their outputs change (see *How to run*).
- **Before a step pays for model calls,** read what it prints: anything it can't do exactly as asked is listed above the question. Then press Enter to go ahead, or anything else to stop, having spent nothing. (Steps that call no model don't ask.)
- **Read the report's Warnings:** the report is `outputs/reports/<step>_<date>_<time>.md` (the step prints its path when it ends). Each warning is explained, with what to do, in *Checks and warnings* below.
- **Commit every changed file in the `annotations/` folder to Git,** so your work is safe.

### This step

- **Never edit or reorder `annotations/ground_truth_candidates.csv`** (the pool) while annotation is in progress: the order is what makes the ground truth a fair sample.
- `outputs/intermediate_results/030_split/splits.json` is written once and then kept. Delete it and rerun only if you mean to rebuild it (e.g. after a new harvest); the pool's order and parts stay the same.

## Inputs

| Input | Default | Contents |
|---|---|---|
| `records` | `020_clean/records.jsonl` | 020's cleaned records. |
| `candidates` | `./annotations/ground_truth_candidates.csv` (in Git) | The ground truth candidates pool, one row per record in pool order: `id`, `maintainer`, and how it was drawn (`stratum`, `stratum_size`, `drawn_from_stratum`). `ground_truth_candidates.json` beside it describes the draw (seed 1000, 36,323 records, stratified by maintainer); 030 doesn't read it. |

## Outputs

In `outputs/intermediate_results/030_split/`:

**On a rerun:** `splits.json` is written once, then kept as it is: a rerun only compares its own draw with it (see *How to run*).

| File | Contents |
|---|---|
| `splits.json` | The two lists, and how they were made. **Written once** (see How to run). |
| `_manifest.json` | Run id, settings, input files and their hashes, output files and their hashes, headline numbers and the harvest date. Written when a run finishes. |

`splits.json`, shortened:

```json
{"ground_truth_candidates": {
   "records": [{"id": "3122be4c…", "position": 0, "maintainer": "Paul Gill", "part": "tuning",
                "_origin": ["annotations/ground_truth_candidates.csv#3122be4c…",
                            "020_clean/records.jsonl#3122be4c…"]}, …],
   "dropped": [{"id": "d57e1e22…", "position": 946,
                "reason": "not in 020's records: no longer in the catalog"}]},
 "induction_candidates": {
   "maintainers": [{"maintainer": "Earthdata Forum", "rank": 1, "records": 10649, "eligible": 10356}, …],
   "records": [{"id": "…", "maintainer": "Earthdata Forum", "position": 0,
                "_origin": ["020_clean/records.jsonl#…"]}, …]},
 "drawn": {"run_id": "030_split_2026-09-28_1700", "settings": {"induction_seed": 7},
           "inputs": {"records": "020_clean/records.jsonl",
                      "candidates": "annotations/ground_truth_candidates.csv"}}}
```

| Field | Meaning |
|---|---|
| `ground_truth_candidates.records` | The pool's records that are still in the catalog, in pool order. `position` is the record's place in the pool file, counting from 0, kept even when an earlier record was dropped. `maintainer` is 020's (joined) maintainer. `part` is `tuning` or `held-out` (see Purpose); it depends only on `position`, so a dropped record changes no one's part. |
| `ground_truth_candidates.dropped` | Pool records no longer in 020's records, with their position and why. |
| `induction_candidates.maintainers` | Every maintainer, ranked by its records in the catalog (`rank` 1 is the largest; ties by name), with how many of them are induction candidates (`eligible`). |
| `induction_candidates.records` | Every induction candidate, grouped by maintainer in rank order. `position` is the record's place in its maintainer's random order, counting from 0: a step taking *k* records from a maintainer takes positions 0 to *k*−1. |
| `drawn` | The run that wrote the file, its settings and its inputs. |

Each run also leaves `outputs/reports/<run id>.md` (the report: what it read and wrote, its numbers, its warnings) and `outputs/logs/<run id>.log` (everything it did, line by line); how to read them: `helpers/audit.md`.

## Settings

| Setting | Default | What it does | When to change it |
|---|---|---|---|
| `induction_seed` | 7 | Fixes the random order of the induction candidates: the same records and seed always give the same order. | Only to draw a different order on purpose; everything learned from the old order is then out of date. |

The setting only takes effect when `splits.json` is written, i.e. when it doesn't exist yet. How many maintainers and how many records per maintainer the schema is learned from are 040's settings (`induction_maintainers`, `texts_per_maintainer`), not 030's.

## How to run

From the repository folder, with the environment active (`docs/virtual_environment_setup.md`):

```
py 030_split/run.py --help       every input and setting, with its default
py 030_split/run.py              reads 020's records and the pool in annotations/
```

**Paying.** This step makes no model calls: it costs nothing, and keeps no cache.

It took 3–4 s (2026-09-28 and 2026-09-29).

**Written once.** The pool is annotated in order, and the order of the induction candidates decides what the schema is learned from, so `splits.json` must not change under work in progress. If it already exists, 030 keeps it as it is. The run still draws, and compares: if its draw differs from the kept file, because the records, the pool file or the setting changed since, it warns. To draw again on purpose, delete `outputs/intermediate_results/030_split/splits.json` and rerun, knowing that work relying on the old one (a schema learned from the old order) is then out of date.

## How it works

Four stages, in `030_split/run.py`'s `main()`, all code:

1. **Load the records** (`load_records`) that 020 wrote, by id (`common/common_helpers/records_io.py`, shared by every step that reads them).
2. **Read the ground truth candidates pool** (`ground_truth_candidates`) from `annotations/`, in its order. An id listed twice, or a file without `id` and `maintainer` columns, stops the step. A pool record that is no longer in 020's records (it left the catalog) is dropped and listed; the others keep their positions, so annotation continues where it was. A pool record whose maintainer in the file differs from 020's current maintainer is listed; 020's is used. Each record gets its part by the rule in Purpose (`part_of()` in `moves.py`; the rule's numbers are named constants there, not settings, since changing them after metrics have been looked at would defeat the held-out part).
3. **Order the induction candidates** (`induction_candidates`). A record is an induction candidate unless it is in the pool (kept or dropped) or has no title and no notes, which gives the schema nothing to learn from. Maintainers are ranked by how many records they hold in the catalog. Each maintainer's candidates are put in a random order of their own:
   - the generator is seeded by `induction_seed` and the maintainer's name, so one maintainer's order never depends on another's;
   - the ids are sorted before shuffling, so the same records and seed always give the same order, whatever the order of the records file;
   - the shuffle is Python's `random.sample`, which returns its picks in selection order "so that all sub-slices will also be valid random samples" (Python documentation): the first *k* records of a maintainer are a random sample of its candidates, for every *k*.
4. **Check the lists are disjoint** (`check_disjoint`). A record in both stops the step.

**Then the results** (`results`): `splits.json` is written (under a temporary name, renamed when complete), or the existing one kept; the report.

The code: `030_split/` holds `run.py` (the control panel: inputs, settings and the moves, in order); `030_split/030_split_helpers/` holds `moves.py` (the moves, and writing the results). Shared with other steps: `common/common_helpers/records_io.py` (reading records), `common/common_helpers/files.py` (saving files).

On 2026-09-28: 36,375 records; 999 left out as ground truth candidates, 0 for having no text; 35,376 induction candidates across 422 maintainers. On 2026-09-29 `splits.json` was rebuilt once to add each candidate's part: everything already in it came out identical.

### Why "undefined" counts as a maintainer

989 records have no maintainer; 020 files them under `undefined`, a value the catalog itself also uses. It is ranked like any other maintainer (5th largest), so when 040 learns from the 10 largest maintainers, `undefined` is one of them. That was decided on purpose, although its records don't come from one author:

- Learning from each large maintainer separately is meant to show schema induction (040) the vocabulary of as much of the catalog as possible, so that the largest maintainers don't drown the others. That purpose doesn't need each group to share one writing style. (That property matters for the ground truth candidates pool, which estimates catalog-wide metrics, not for schema induction.)
- Replacing `undefined` with the next largest maintainer, Christopher Rumsey (178 records), would cover 0.5% of the catalog instead of 2.7%: the 10 maintainers would hold 89.4% of the catalog's records instead of 91.6%.

## Prompts

None: this step makes no model calls.

## Checks and warnings

**Shown before paying:** none, since this step makes no model calls.

**In the report**, under *Warnings*:

| Message | Meaning | What to do |
|---|---|---|
| *N ground truth candidates are no longer in the catalog and were dropped* | Pool records that left the catalog since the pool was drawn. Listed in the report. 1 on 2026-09-28 (position 946). | Nothing: the others keep their positions. If a dropped record was already annotated, its ground truth no longer has a text to evaluate against. |
| *N ground truth candidates have a different maintainer in 020's records than in the pool file* | A maintainer's spelling is joined differently now, or the record's maintainer changed. Listed in the report. 0 on 2026-09-28. | Usually nothing; 020's maintainer is used. |
| *splits.json already exists and was kept, but this run's draw differs from it* | The records, the pool file or the setting changed since `splits.json` was written. | Usually nothing: the kept file is what work in progress relies on. To take the change, delete `splits.json` and rerun. |
| *N of M ground truth candidates (or induction candidates) have no origin, so they can't be traced to the input they came from* | Should never happen: a code change dropped the field that records where each item came from. | Fix the code before using the output. |

**The step stops** with:

| Message | Meaning | What to do |
|---|---|---|
| *… lists these ids more than once* | The pool file repeats an id. | Fix `annotations/ground_truth_candidates.csv`. |
| *… needs the columns id and maintainer* | The pool file isn't in the expected form. | Check the file. |
| *missing input files: candidates …* | The pool file isn't there. 030 never draws a pool. | Put the pool in `annotations/ground_truth_candidates.csv`, or pass `--candidates`. |
| *N records are both ground truth candidates and induction candidates* | Should never happen: induction candidates exclude the pool by construction. | A code change broke `induction_candidates`; fix it. |

## Audit trail

- **Log.** `outputs/logs/<run id>.log` records the command line, the settings, the git commit, each move's duration, each output file's hash and, on failure, the full traceback.
- **Origin.** Each ground truth candidate's `_origin` names its row in `annotations/ground_truth_candidates.csv` (made by a person, so the trace stops there) and its record in 020's `records.jsonl`; each induction candidate's names its 020 record.
- **Trace.** `py helpers/audit.py <record id>` follows a record back through every step's output to the 010 batch file and the API request that first returned it (`helpers/audit.md`).

## Known limits

- **The pool describes the catalog of 2026-09-21** (36,323 records), not today's. Records added since can't be in it, and records removed since are dropped. Its maintainers match 020's joined names exactly on 2026-09-28.
- **The order is only as fixed as `splits.json`.** Because the order is written once and kept, a re-harvest doesn't change it; records added to the catalog after `splits.json` was written are never induction candidates until it is deliberately redrawn.
- **Replaces an earlier sample.** The earlier `best_induce_schema.py` drew its own induction sample (seed 7, from `inputs.json`) and didn't exclude the pool; no schema learned from that sample is kept in this repo, so nothing needs it.
