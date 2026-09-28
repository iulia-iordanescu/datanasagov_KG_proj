# 030_split

## Purpose

Sets the two samples of records that later steps work on, and keeps them apart:

- **The ground truth candidates pool**: 1,000 records that are candidates for annotation. A person annotates them in pool order, and the annotated records become the ground truth that 070 scores the extraction against. Only a subset of the pool is ever annotated, since verifying 1,000 records by hand is more than the time available. The pool was shuffled when it was drawn, so the first *k* records are a fair sample of the catalog for any *k*, and annotation can stop anywhere.
- **The induction sample**: the records 040 learns the schema from.

No record is ever in both. 070 measures how well extraction works on text the schema was *not* learned from; scoring on records the schema was learned from would flatter it.

**The pool is not drawn here.** It was drawn once, on 2026-09-21, by the earlier `ground_truth_sampler.py`, and annotation has started on it, so it must never change. It is kept in `annotations/ground_truth_candidates.csv`, in Git; 030 reads it. The induction sample is drawn here.

## Inputs

| Input | Default | Contents |
|---|---|---|
| `records` | `020_clean/records.jsonl` | 020's cleaned records. |
| `candidates` | `./annotations/ground_truth_candidates.csv` (in Git) | The ground truth candidates pool, one row per record in pool order: `id`, `maintainer`, and how it was drawn (`group`, `group_size`, `drawn_from_group`). `ground_truth_candidates.json` beside it describes the draw (seed 1000, 36,323 records, stratified by maintainer); 030 doesn't read it. |

## Outputs

In `outputs/intermediate_results/030_split/`:

| File | Contents |
|---|---|
| `splits.json` | The two samples, and how they were drawn. **Written once** (see How to run). |
| `_manifest.json` | Run id, settings, input files and their hashes, output hash, headline numbers. Written when a run finishes. |

`splits.json`, shortened:

```json
{"ground_truth_candidates": {
   "records": [{"id": "3122be4c…", "position": 0, "maintainer": "Paul Gill",
                "_origin": ["annotations/ground_truth_candidates.csv#3122be4c…",
                            "020_clean/records.jsonl#3122be4c…"]}, …],
   "dropped": [{"id": "d57e1e22…", "position": 946,
                "reason": "not in 020's records: no longer in the catalog"}]},
 "induction_sample": {
   "records": [{"id": "84b86e22…", "maintainer": "Earthdata Forum",
                "_origin": ["020_clean/records.jsonl#84b86e22…"]}, …],
   "maintainers": [{"maintainer": "Earthdata Forum", "records": 10649,
                    "eligible": 10356, "sampled": 15}, …]},
 "drawn": {"run_id": "030_split_2026-09-28_1620",
           "settings": {"induction_maintainers": 10, "texts_per_maintainer": 15, "induction_seed": 7},
           "inputs": {"records": "020_clean/records.jsonl",
                      "candidates": "annotations/ground_truth_candidates.csv"}}}
```

| Field | Meaning |
|---|---|
| `ground_truth_candidates.records` | The pool's records that are still in the catalog, in pool order. `position` is the record's place in the pool file, counting from 0, kept even when an earlier record was dropped. `maintainer` is 020's (joined) maintainer. |
| `ground_truth_candidates.dropped` | Pool records no longer in 020's records, with their position and why. |
| `induction_sample.records` | The induction sample, grouped by maintainer, largest maintainer first. |
| `induction_sample.maintainers` | Per maintainer: its records in the catalog, how many were eligible, how many were sampled. |
| `drawn` | The run that wrote the file, its settings and its inputs. |

Each run also leaves `outputs/reports/<run id>.md` and `outputs/logs/<run id>.log`.

## Settings

| Setting | Default | Meaning | When to change it |
|---|---|---|---|
| `induction_maintainers` | 10 | The induction sample comes from this many of the largest maintainers (by their records in the catalog). | To learn the schema from more or fewer of the catalog's maintainers. |
| `texts_per_maintainer` | 15 | Records sampled from each of them. | To give the schema more or less text per maintainer. |
| `induction_seed` | 7 | Fixes the random draw: the same records and settings always give the same sample. | Only to draw a different sample on purpose. |

The settings only take effect when `splits.json` is written, i.e. when it doesn't exist yet.

## How to run

From the repo root, with the environment active:

```
py 030_split.py                          reads 020's records and the pool in annotations/
py 030_split.py --texts_per_maintainer 20
py 030_split.py --help                   list inputs and settings
```

It took 2 s on 2026-09-28.

**Written once.** The pool is annotated in order, and the induction sample decides what the schema is learned from, so `splits.json` must not change under work in progress. If it already exists, 030 keeps it as it is. The run still draws, and compares: if its draw differs from the kept file, because the records, the pool file or the settings changed since, it warns. To draw again on purpose, delete `outputs/intermediate_results/030_split/splits.json` and rerun, knowing that work relying on the old one (a schema learned from the old induction sample) is then out of date.

## How it works

1. **Load the records** that 020 wrote, by id (`common/records_io.py`, shared by every step that reads them).
2. **Read the ground truth candidates pool** from `annotations/`, in its order. An id listed twice, or a file without `id` and `maintainer` columns, stops the step. A pool record that is no longer in 020's records (it left the catalog) is dropped and listed; the others keep their positions, so annotation continues where it was. A pool record whose maintainer in the file differs from 020's current maintainer is listed; 020's is used.
3. **Draw the induction sample.** The maintainers are ranked by how many records they hold in the catalog (ties by name), and the `induction_maintainers` largest are taken. From each, `texts_per_maintainer` records are drawn at random, from the *eligible* ones: never a record of the pool (kept or dropped), and never a record with no title or notes, which gives the schema nothing to learn from. The draw uses `induction_seed` over the eligible ids in sorted order, so the same records and settings always give the same sample, whatever the order of the records file. A maintainer with fewer eligible records gives all of them.
4. **Check the samples are disjoint.** A record in both stops the step.
5. **Write `splits.json`** (under a temporary name, renamed when complete), or keep the existing one, and report.

The code is in `030_split/moves.py`.

### Why "undefined" is one of the induction maintainers

989 records have no maintainer; 020 files them under `undefined`, a value the catalog itself also uses. By size it is the 5th largest group, so it is one of the 10 induction maintainers, and 15 of its records are sampled. It was kept on purpose, although its records don't come from one author:

- Sampling each maintainer separately is meant to show the schema step the vocabulary of as much of the catalog as possible, so that the largest maintainers don't drown the others. That purpose doesn't need each group to share one writing style. (That property matters for the ground truth candidates pool, which estimates catalog-wide scores, not for the induction sample.)
- Replacing `undefined` with the next largest maintainer, Christopher Rumsey (178 records), would cover 0.5% of the catalog instead of 2.7%: the 10 maintainers would hold 89.4% of the catalog's records instead of 91.6%.

## Checks and warnings

| Message | Meaning | What to do |
|---|---|---|
| *N ground truth candidates are no longer in the catalog and were dropped* | Pool records that left the catalog since the pool was drawn. Listed in the report. 1 on 2026-09-28 (position 946). | Nothing: the others keep their positions. If a dropped record was already annotated, its ground truth no longer has a text to score against. |
| *N ground truth candidates have a different maintainer in 020's records than in the pool file* | A maintainer's spelling is joined differently now, or the record's maintainer changed. Listed in the report. 0 on 2026-09-28. | Usually nothing; 020's maintainer is used. |
| *N induction maintainers have fewer than … eligible records* | A maintainer had fewer eligible records than `texts_per_maintainer`, so it gave all it had. | Nothing, unless you want the sample to be exactly `induction_maintainers × texts_per_maintainer`. |
| *splits.json already exists and was kept, but this run's draw differs from it* | The records, the pool file or the settings changed since `splits.json` was written. | Usually nothing: the kept file is what work in progress relies on. To take the change, delete `splits.json` and rerun. |
| *… lists these ids more than once* (the step stops) | The pool file repeats an id. | Fix `annotations/ground_truth_candidates.csv`. |
| *… needs the columns id and maintainer* (the step stops) | The pool file isn't in the expected form. | Check the file. |
| *missing input files: candidates …* (the step stops) | The pool file isn't there. 030 never draws a pool. | Put the pool in `annotations/ground_truth_candidates.csv`, or pass `--candidates`. |
| *… must be at least 1* (the step stops) | `induction_maintainers` or `texts_per_maintainer` is 0 or less. | Fix the setting. |
| *N records are in both samples* (the step stops) | Should never happen: the induction sample excludes the pool by construction. | A code change broke `induction_sample`; fix it. |

## Human work

None in this step. The pool it reads is human work: never edit or reorder `annotations/ground_truth_candidates.csv` while annotation is in progress.

## Known limits

- **The pool describes the catalog of 2026-09-21** (36,323 records), not today's. Records added since can't be in it, and records removed since are dropped. Its maintainers match 020's joined names exactly on 2026-09-28.
- **Only the largest maintainers feed the induction sample**: the 10 largest hold 91.6% of the catalog's records (2026-09-28). A class or predicate used only by the other maintainers can't be learned.
- **Equal allocation.** Every induction maintainer gives the same number of records, however large it is, so the schema sees small maintainers as much as large ones. A class used by only one maintainer has at most `texts_per_maintainer` records to recur in.
- **This induction sample is new.** The earlier `best_induce_schema.py` drew its own sample (seed 7, from `inputs.json`) and didn't exclude the pool; no schema learned from that sample is kept in this repo, so nothing needs it.
