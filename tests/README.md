# Tests

Checks that the pipeline does what its docs say, so a change that breaks something is caught before it is committed, not in the next sweep.

```
py tests/run_all.py            every test (about 40 s)
py tests/run_all.py pairing    only the test files whose name contains "pairing"
```

It prints one line per test file, then the failures in full. Exit code 0 means every test passed.

Nothing here calls the model or data.nasa.gov, and nothing is written into the repository: the tests work in temporary folders, and `run_all.py` fails if `git status` differs after the run.

## What each file checks

| File | Checks |
|---|---|
| `test_harvest.py` | Harvest, against a stand-in for data.nasa.gov's API: paging, a rerun keeping the batch files on disk, an interrupted run resuming, a busy page retried, a page that isn't JSON, a changed page size or `max_records`, the catalog growing or running dry, the warnings. |
| `test_clean.py` | Cleaning: no word, number or URL lost (the self-tests, the doctests, 3,000 random broken HTML snippets), maintainer spellings joined or kept apart, the step's moves on two small batch files (records with no id or a repeated id dropped, titles made one line). |
| `test_split.py` | Splitting: the tuning and held-out rule, candidates no longer in the catalog, the induction candidates never in the pool, their order fixed by the seed alone, splits.json written once. |
| `test_schema_io.py` | Reading both shapes of a schema, the additions file, the source rule for additions, and the annotation tool's edits to the hand-built schema (byte-order mark and line endings kept; a refused or faulty edit leaves the file as it was). Also: the real hand-built schema reads cleanly. |
| `test_common.py` | Reading the ground truth (lines, problems), the ground truth vocabulary, the fair sample, every check of a triple instance, building rows from the model's replies, text pieces, the translation table, partial pair reviews. Also: the real ground truth and pool read without problems. |
| `test_induce_schema.py` | Schema induction's code stages: matching labels, merging synonyms (chains, cycles, invalid merges), counting support, building the schema from the evidence. |
| `test_evaluate_pairing.py` | Evaluation: every example in `070_evaluate/metrics.md`, the largest pairing, exact before partial, reversed rows, `(none)` rows, partial pair reviews, component class mismatches, every formula and its edge cases, margins of error, the held-out part kept aside. |
| `test_annotator.py` | The annotation tool, through its HTTP API: opening and saving a batch, adding to the hand-built schema, the translation table, the schema additions, partial pair reviews. |
| `test_pipeline.py` | The whole pipeline, step 010 to step 070, each step run as a person runs it, with the stand-in model: outputs, the model's deliberate mistakes caught, a rerun paying nothing twice, evaluation waiting for the translation table, and evaluation's numbers on a case worked out by hand. |
| `test_docs.py` | Each step guide's Inputs, Settings and Prompts tables match its `run.py` and prompts folder; every file path named in the docs and code exists; the glossary defines each term once; "class" never stands alone. |

`stand_ins.py` holds the two stand-ins (data.nasa.gov's API and the model); `stand_in_run.py` runs one step with them; `support.py` is what the test files share.

## When a test fails

Read its message first: it names what differs from what the docs say. Then either the code is wrong (fix it), or the docs and the test describe something that was changed on purpose (change all three together).

## Adding a test

Every bug fixed gets a test that fails without the fix. Add it to the file of the step it belongs to, in the same style; a new file `test_<something>.py` is picked up by `run_all.py` on its own.
