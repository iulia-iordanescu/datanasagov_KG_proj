# Tests

Checks that the pipeline does what its docs say, so a change that breaks something is caught before it is committed, not in the next sweep.

```
py tests/run_all.py            every test (about 40 s)
py tests/run_all.py pairing    only the test files whose name contains "pairing"
```

It prints one line per test file, then the failures in full. Exit code 0 means every test passed.

Nothing here calls the [model](../docs/terminology.md#8-the-pipeline) or data.nasa.gov, and nothing is written into the repository: the tests work in temporary folders, and `run_all.py` fails if `git status` differs after the [run](../docs/terminology.md#8-the-pipeline).

## What each file checks

| File | Checks |
|---|---|
| `test_harvest.py` | [Harvest](../docs/terminology.md#1-records-and-their-text), against a stand-in for data.nasa.gov's API: paging, a rerun keeping the [batch files](../docs/terminology.md#1-records-and-their-text) on disk, an interrupted [run](../docs/terminology.md#8-the-pipeline) resuming, a busy page retried, a page that isn't JSON, a changed page size or `max_records`, the catalog growing or running dry, the warnings. |
| `test_clean.py` | Cleaning: no word, number or URL lost (the self-tests, the doctests, 3,000 random broken HTML snippets), [maintainer](../docs/terminology.md#1-records-and-their-text) spellings joined or kept apart, the [step](../docs/terminology.md#8-the-pipeline)'s [moves](../docs/terminology.md#8-the-pipeline) on two small batch files ([records](../docs/terminology.md#1-records-and-their-text) with no id or a repeated id dropped, titles made one line). |
| `test_split.py` | Splitting: the tuning and held-out rule, candidates no longer in the catalog, the [induction candidates](../docs/terminology.md#4-ground-truth-and-samples) never in the [pool](../docs/terminology.md#4-ground-truth-and-samples), their order fixed by the seed alone, splits.json written once. |
| `test_schema_io.py` | Reading both shapes of a [schema](../docs/terminology.md#3-schemas), the additions file, the source rule for additions, and the [annotation tool](../docs/terminology.md#4-ground-truth-and-samples)'s edits to the [hand-built schema](../docs/terminology.md#3-schemas) (byte-order mark and line endings kept; a refused or faulty edit leaves the file as it was). Also: the real hand-built schema reads cleanly. |
| `test_common.py` | Reading the [ground truth](../docs/terminology.md#4-ground-truth-and-samples) (lines, problems), the [ground truth vocabulary](../docs/terminology.md#7-evaluating-extraction-step-070), the [fair sample](../docs/terminology.md#4-ground-truth-and-samples), every check of a [classed triple](../docs/terminology.md#2-triples), building rows from the [model](../docs/terminology.md#8-the-pipeline)'s replies, [text pieces](../docs/terminology.md#1-records-and-their-text), the [translation table](../docs/terminology.md#7-evaluating-extraction-step-070), [partial pair reviews](../docs/terminology.md#7-evaluating-extraction-step-070). Also: the real ground truth and pool read without problems. |
| `test_induce_schema.py` | Schema induction's code [stages](../docs/terminology.md#8-the-pipeline): matching [labels](../docs/terminology.md#5-learning-the-schema-step-040), merging synonyms (chains, cycles, invalid merges), counting [support](../docs/terminology.md#5-learning-the-schema-step-040), building the schema from the [evidence](../docs/terminology.md#5-learning-the-schema-step-040). |
| `test_evaluate_pairing.py` | Evaluation: every example in `070_evaluate/metrics/`, the largest pairing, exact before partial, reversed rows, `(none)` rows, partial pair reviews, [component class](../docs/terminology.md#3-schemas) mismatches, every formula and its edge cases, [margins of error](../docs/terminology.md#7-evaluating-extraction-step-070), the [held-out part](../docs/terminology.md#7-evaluating-extraction-step-070) kept aside. |
| `test_annotator.py` | The annotation tool, through its HTTP API: opening and saving a batch, adding to the hand-built schema, the translation table, the [schema additions](../docs/terminology.md#3-schemas), partial pair reviews. |
| `test_pipeline.py` | The whole pipeline, step 010 to step 070, each step run as a person runs it, with the [stand-in model](../docs/terminology.md#8-the-pipeline): outputs, the model's deliberate mistakes caught, a rerun paying nothing twice, evaluation waiting for the translation table, and evaluation's numbers on a case worked out by hand. |
| `test_docs.py` | Each step guide's Inputs, [Settings](../docs/terminology.md#8-the-pipeline) and Prompts tables match its `run.py` and prompts folder; every file path named in the docs and code exists; docs/terminology.md defines each term once; "class" never stands alone. |

`stand_ins.py` holds the two stand-ins (data.nasa.gov's API and the model); `stand_in_run.py` runs one step with them; `support.py` is what the test files share.

## When a test fails

Read its message first: it names what differs from what the docs say. Then either the code is wrong (fix it), or the docs and the test describe something that was changed on purpose (change all three together).

## Adding a test

Every bug fixed gets a test that fails without the fix. Add it to the file of the [step](../docs/terminology.md#8-the-pipeline) it belongs to, in the same style; a new file `test_<something>.py` is picked up by `run_all.py` on its own.
