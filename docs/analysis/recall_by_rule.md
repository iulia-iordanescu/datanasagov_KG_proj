# Recall by guideline rule

Preliminary, computed on 2026-11-13 by scripts that Claude Fable 5.2 wrote and Claude Opus 5.5 ran, still to be reviewed by a person.

## What this is

Each ground truth row has a column `rules`, which lists the numbers of the rules of `annotations/guidelines.md` that the triple uses. This page gives, for each rule number, the recall of the ground truth triples that list it, over the six runs of `rescore_2026-11-13.md` (three repeats with the induced schema, three with the ground truth schema), on the ground truth of 2026-11-13.

Formula, for a rule *r* and one run: recall of *r* = the ground truth triples that list *r* and are in a pair ÷ the ground truth triples that list *r*, with both counts summed over the 20 evaluated records. At the partial level a pair is an exact pair or a partial pair, and at the exact level an exact pair only, as `070_evaluate/metrics/pairs.md` and `070_evaluate/metrics/recall.md` define them. The pairs are those that step 070 made in each run (`compared_triples.csv`, column `status`), and nothing was paired again. A column gives the mean of that proportion over its runs. The row *all* is recall as step 070 reports it, for reference.

## How to read it

- The groups overlap. A ground truth triple lists several rules and is counted in the row of each, so the rows do not add up to 432 and their recalls are not independent.
- Rules 2, 11, 13, 14 and 17 apply to every ground truth triple and are not recorded in the column, so they have no row. No ground truth triple of the evaluated records lists rule 3.
- A rule's row holds the triples that use the rule, which is not the same as the triples the rule causes extraction to miss. The triples of a row also differ in their records and in their other rules, so a row with low recall is a place to look and not a finding about the rule.
- A row with fewer than 10 ground truth triples is marked *too small*: rules 4, 5, 6, 7, 8, 10, and the one triple that records no rule. Its recall changes by many points with one triple and should not be read.
- The column *Within reach* counts the row's ground truth triples that the induced schema can express through the translation table (`070_evaluate/metrics/recall_upper_bound.md`). With the ground truth schema every triple is within reach. A row with few triples within reach is limited by the schema before extraction starts: rule 9 has 47 triples, of which 24 are within reach.
- The values in the column `rules` were written by a model and are still to be reviewed by a person (`docs/improvements.md`, *The rules each ground truth triple uses, recorded per triple*).
- The extractions were made with the rules of 2026-11-05, before the rules changed on 2026-11-12 and 2026-11-13.

## The table

| Rule | Title (the rule's bold first words in the guidelines) | Ground truth triples | Within reach, induced schema | Partial recall, induced schema (mean of 3 repeats) | Partial recall, ground truth schema (mean of 3 repeats) | Partial recall, mean of the six runs | Exact recall, mean of the six runs |
|---|---|---:|---:|---:|---:|---:|---:|
| 1 | Only what the record states. | 98 | 87 | 59.2% | 79.3% | 69.2% | 64.6% |
| 4 | Not "is a" facts. | 8 (too small) | 4 | 8.3% | 100.0% | 54.2% | 54.2% |
| 5 | Not opinions. | 3 (too small) | 2 | 0.0% | 33.3% | 16.7% | 16.7% |
| 6 | Not negated facts. | 1 (too small) | 1 | 0.0% | 100.0% | 50.0% | 50.0% |
| 7 | Not facts the record doesn't assert as true: | 8 (too small) | 3 | 25.0% | 100.0% | 62.5% | 52.1% |
| 8 | Not the values inside a data table; only what the table is about. | 3 (too small) | 3 | 44.4% | 77.8% | 61.1% | 55.6% |
| 9 | Not a fact without a specific thing. | 47 | 24 | 31.9% | 84.4% | 58.2% | 50.4% |
| 10 | Not words that are true only as of when the record was written. | 5 (too small) | 3 | 20.0% | 66.7% | 43.3% | 43.3% |
| 12 | The subject instance is what the sentence is about | 188 | 144 | 28.4% | 63.1% | 45.7% | 39.2% |
| 15 | One fact per ground truth triple. | 99 | 66 | 32.0% | 80.8% | 56.4% | 50.0% |
| 16 | Each fact once, | 69 | 56 | 77.3% | 91.3% | 84.3% | 74.4% |
| 18 | A number with a unit: the object instance is the number and its unit, as written; what the number measures goes in the predicate. | 38 | 29 | 31.6% | 85.1% | 58.3% | 54.4% |
| 19 | A qualifier that is a temporal resolution, an area the data cover, a processing level, a spatial resolution, a country, a time of day, or a target body is a ground truth triple of its own, and is taken out of the instance. | 94 | 79 | 53.5% | 70.9% | 62.2% | 54.8% |
| 20 | A name with its own abbreviation, another name or code of its own, or a short note in parentheses is one instance, as written. | 133 | 106 | 48.1% | 78.2% | 63.2% | 55.5% |
| 21 | General facts: include them; about another dataset, only when the record links it to the record's dataset by "part of" or "made from". | 176 | 139 | 32.0% | 63.4% | 47.7% | 40.2% |
| 22 | A list: one ground truth triple per item. | 138 | 100 | 37.7% | 72.5% | 55.1% | 49.5% |
| 23 | One thing, one wording, within a record. | 176 | 137 | 54.0% | 80.9% | 67.4% | 59.2% |
| 24 | A processing step: output = method(input). | 55 | 43 | 46.1% | 79.4% | 62.7% | 55.5% |
| none listed | (no rule recorded) | 1 (too small) | 1 | 100.0% | 100.0% | 100.0% | 100.0% |
| all | (all ground truth triples, for reference) | 432 | 325 | 44.8% | 77.2% | 61.0% | 54.6% |

The same rows, with exact recall per schema, are in `recall_by_rule.csv` beside this file.

## Precision by rule is not defined

Precision divides the pairs by the counted occurrences (`070_evaluate/metrics/precision.md`). An occurrence that is left extracted only has no ground truth triple, and only ground truth triples have a `rules` value, so such an occurrence belongs to no rule. A precision per rule would need the occurrences of that rule as its denominator, and that set does not exist. Step 070's attributed precision (`070_evaluate/070_evaluate.md`, *By the second opinion*) could be computed per rule. It counts every unpaired occurrence against every group alike, and its groups there do not overlap, while the rules' groups do. It is left out.

## Where the numbers come from

Scripts `helpers/analysis/analyses.py` (function `by_rule`) and `helpers/analysis/tables.py`. They read the six runs' `compared_triples.csv`, copied after each run into `outputs/analysis/runs/` (the same files are kept in `outputs/intermediate_results/070_evaluate/previous_runs/`), and `annotations/ground_truth/batch_*.csv`. Every one of the 432 ground truth triples of each run was matched to its row in the ground truth files by record id and classed triple.
