# Partial pairs of several runs, reviewed through Git

Step 070's [partial pairs](../070_evaluate/metrics/pairs.md) need my [verdict](../docs/terminology.md#7-evaluating-extraction-step-070) (`annotations/partial_pair_reviews.csv`), and the [annotation tool](../docs/terminology.md#4-ground-truth-and-samples)'s *Partial pairs* view shows only the latest 070 [run](../docs/terminology.md#8-the-pipeline)'s. Repeats of one recipe each pair differently, a run's outputs stay on the computer that ran it (the NASA laptop), and I review on another computer, through Git. So this helper collects the partial pairs of several runs into a file in Git, and moves the verdicts I fill there into `annotations/partial_pair_reviews.csv`. Free: no [model calls](../docs/terminology.md#8-the-pipeline).

```
py helpers/partial_pairs.py                                       list the 070 runs whose pairs can be collected
py helpers/partial_pairs.py --runs <070 run id> <070 run id> ...  collect their partial pairs with no verdict
py helpers/partial_pairs.py --apply true                          move the filled verdicts into partial_pair_reviews.csv
py helpers/partial_pairs.py --delete_stale true --runs <070 run id> ...
                                                                  delete the verdicts that match no partial pair of those runs
```

It writes only `annotations/partial_pairs_to_review.csv`, and, with `--apply true` or `--delete_stale true`, `annotations/partial_pair_reviews.csv`.

## Collecting

**Which pairs.** Every partial pair of a [tuning record](../docs/terminology.md#7-evaluating-extraction-step-070), in any of the runs given, with no verdict now in `annotations/partial_pair_reviews.csv`: none filed, or two different ones filed (a conflict, which counts as none: `common/common_helpers/latest.py`). Each pair is listed once, under the key step 070 files a verdict by: the record and both triples' [subject instance](../docs/terminology.md#2-triples), predicate and [object instance](../docs/terminology.md#2-triples), [evened out](../docs/terminology.md#2-triples) (`common/common_helpers/partial_reviews.py`, `pair_key`). Two runs that write one pair differently (case, spacing) give one row, written as the earliest run wrote it. The [held-out part](../docs/terminology.md#7-evaluating-extraction-step-070)'s pairs are never collected: reviewing them would mean looking at held-out results.

**Where each run's pairs come from.** Its `compared_triples.csv` (`070_evaluate/070_evaluate.md`, *Outputs*). The file in `outputs/intermediate_results/070_evaluate/` is the latest run's; an earlier run's is kept in `previous_runs/<run id>/` only when a later run changed it (`common/common_helpers/step.py`, `PREVIOUS_RUNS`). So the helper reads the sha256 the run's manifest records for the file, and takes the file, live or kept, with that sha256: always the run's own. A run whose file isn't found stops the command, naming it and listing the runs that can be collected.

**The file to review**, `annotations/partial_pairs_to_review.csv`, one row per pair, sorted by record title:

| Column | What it holds |
|---|---|
| `record_id`, `record_title` | The record (its title from 020's `records.jsonl`) |
| `predicate` | The [ground truth triple](../docs/terminology.md#4-ground-truth-and-samples)'s predicate ([ground truth schema](../docs/terminology.md#3-schemas)) |
| `ground_truth_triple`, `extracted_triple` | Both classed triples as `per_record.md` shows them, `subject (subject class) PREDICATE object (object class)`; the extracted triple as translated into the ground truth schema |
| `runs` | The 070 runs that had the pair, separated by `; ` |
| `verdict` | Empty; I write `same fact` or `not the same fact`, the two values `annotations/partial_pair_reviews.csv` takes (case and spacing aside) |
| `ground_truth_subject` … `translated_object` | The cells the verdict is filed under, copied as they are into `annotations/partial_pair_reviews.csv` |
| `pair_fingerprint` | A short sha256 of `record_id` and those six cells, so an edit of them is caught |

Collecting again replaces the file. It stops while the file holds a filled verdict not yet moved, so none is lost: run `--apply true` first.

## Moving the verdicts

`py helpers/partial_pairs.py --apply true` adds each filled verdict to `annotations/partial_pair_reviews.csv`, written as one of the two values, and takes its row out of the file to review; rows with an empty `verdict` stay. It checks every filled row first, and if any fails, moves nothing and names every line:

- the verdict is neither `same fact` nor `not the same fact` (case and spacing aside);
- a cell the verdict is filed under was changed since collecting (its `pair_fingerprint` no longer fits): such a verdict might name no partial pair. The shown columns (`record_title`, `predicate`, `ground_truth_triple`, `extracted_triple`, `runs`) may change freely;
- two rows for one pair with different verdicts, in the file to review, or between it and `annotations/partial_pair_reviews.csv` (a verdict filed meanwhile in the annotation tool): a conflict, by the one rule for several rows about one thing (`common/common_helpers/latest.py`). The same verdict twice is no conflict, and is filed once.

Then run step 070 again.

## Deleting the verdicts that no longer apply

Step 070 warns when verdicts *no longer match a partial pair* (`070_evaluate/070_evaluate.md`, *Checks and warnings*). `py helpers/partial_pairs.py --delete_stale true --runs <070 run id> ...` deletes those rows of `annotations/partial_pair_reviews.csv`: each verdict on a tuning record that some run given evaluated, whose two triples can pair at the partial level in none of them. The test is 070's own (`pairing.verdict_keys`), applied to each run's ground truth triples and translated extracted triples as its `compared_triples.csv` lists them. A verdict on a record none of the runs evaluated is kept. Give every run whose pairs still count: a verdict on a pair of repeat 1 may match nothing in repeat 2, and with repeat 2 alone it would be deleted. It prints each row it deletes; Git keeps the earlier file.

## Known limits

- **A rename or merge in the annotation tool** changes the predicates' spellings in `annotations/partial_pair_reviews.csv`, not in the file to review: move the filled verdicts before one, and collect again after it.
- **The test for deleting** is today's code applied to each run's kept triples: if the code that evens out or pairs changed since a run, a verdict is judged as step 070 would judge it now on that run's triples.
