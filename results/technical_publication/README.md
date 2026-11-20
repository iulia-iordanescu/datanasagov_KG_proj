# Results of the Technical Publication

This folder holds every number the code produced for the runs behind my Technical Publication, and every record, triple and model call those numbers come from. The runs' own files are in `outputs/`, which Git leaves out, so without this folder the numbers would exist only on the laptop that made them.

The numbers come from the runs of 18 and 19 November 2026: 58 runs of extraction (step 060), each evaluated by step 070 on the 40 finished [tuning records](../../docs/terminology.md#7-evaluating-extraction-step-070), and 27 [held-out looks](../../docs/terminology.md#7-evaluating-extraction-step-070), one for each run of step 060 with the induced schema, on the 40 finished held-out records. Nine models extracted with the ground truth schema and with the induced schema, three repeats each, at the lowest reasoning level each model's maker allows (setting `thinking` `lowest`). Four of them also extracted once with the ground truth schema at a high reasoning level, and their rows have `high` in the column `thinking`.

## How it was made

```
py helpers/export_results.py
```

The script reads the run list `runs.tsv` (in this folder) and the runs' files in `outputs/`, and writes every other file of this folder again. It calls no model and computes no number of its own: each number comes from the functions that `helpers/compare_runs.py`, `helpers/held_out_results.py` and step 070 use for their reports (`helpers/export_results.md`).

The run list `runs.tsv` is a tab-separated file whose lines starting with `#` are comments. A tuning line gives the schema, the thinking setting, the model, the repeat, the run id of step 070's evaluation of its tuning records, and the run id of step 060. A held-out line gives the word `held-out` and the run id of step 070's held-out look. A held-out look finds its model and repeat through the run of step 060 it scored.

## Terms

The terms are those of [`docs/terminology.md`](../../docs/terminology.md), which defines each of them. The ones these files use most are the following.

- A **triple instance** is a fact written as a subject, a predicate and an object, with no entity classes. Schema induction (step 040) finds triple instances.
- A **classed triple** is a fact written as a subject instance with its subject class, a predicate of a schema, and an object instance with its object class. Every classed triple a model gives in its answer for a text is a classed triple in the answer.
- An **extracted triple** is a classed triple that step 060 kept after its checks. The checks remove the others, each for one reason: `source_text` (its source text is missing or isn't in the record's text), `component_class_not_in_schema` (it uses an entity class or predicate the schema doesn't have), both of those together, `duplicate` (the same classed triple twice in the record), `describes_triple` (a describes triple of the model's own), or `malformed` (an item of the answer that isn't a classed triple at all). The full definitions are in `docs/terminology.md`, *extracted triple*.
- A **ground truth triple** is a classed triple of a finished record's ground truth, which a person checked against the record's text. Each record also has one describes triple, which step 070 compares apart and which is not counted among its ground truth triples here.
- A **pair** joins an extracted triple, once translated into the ground truth schema, and a ground truth triple of the same record that step 070 takes to state the same fact. In an **exact pair** the two have the same predicate and the same subject instance and object instance, once evened out. In a **partial pair** they have the same predicate, and each of the two instances is the same or appears, as whole words, inside the other; step 070 applies the verdicts on partial pairs (`annotations/partial_pair_reviews.csv`). A **strict pair** is a pair whose subject classes and object classes match as well. The definitions are in [`070_evaluate/metrics/pairs.md`](../../070_evaluate/metrics/pairs.md).
- A ground truth triple is **within reach** when the translation table has a checked row that translates a predicate of the schema the run extracted with to the ground truth triple's predicate ([`070_evaluate/metrics/recall_upper_bound.md`](../../070_evaluate/metrics/recall_upper_bound.md), which also defines **within strict reach**).
- An **induction text** is one of the 138 records whose text step 040 induced the schema from.
- A **group** is the set of repeats of one schema, thinking setting and model on one part of the pool (tuning or held-out). A group has three runs, or one for the thinking-high runs.

## Conventions

- Proportions (precision, recall, F1 and the others) are written as proportions with four decimals, so 0.7040 is 70.40%. Variances have six decimals.
- An empty cell means there is no value: there is nothing to divide by, the value needs more than one run, or the number has no range.
- The metric names are those of step 070's reports, a pair level followed by the number (`partial: f1`, `exact: recall`), or the number alone (`recall upper bound`, `schema fit`, `describes accuracy`). What each number divides by what, and how to read it, is in [`070_evaluate/metrics.md`](../../070_evaluate/metrics.md).
- A reference `extracted_triples.csv#N` names row N (counted from 0, after the header) of the `extracted_triples.csv` that the run of step 060 wrote. A reference `annotations/ground_truth/batch_NNN.csv#M` names row M (counted from 0, after the header) of a ground truth file in Git.

## The numbers

### `metrics_pooled.csv`

Each row gives one number of one group, pooled over the group's repeats (`helpers/compare_runs.md`, *Pooled over the repeats*).

| Column | Meaning |
|---|---|
| `part` | The part of the pool the group was evaluated on, `tuning` or `held-out`. |
| `schema` | The schema step 060 extracted with, `ground truth` or `induced`. |
| `thinking` | The reasoning setting of step 060, `lowest` or `high`. |
| `model` | The model that extracted. |
| `runs` | The number of runs in the group. |
| `records_pooled` | The number of records pooled, which are the records evaluated in every run of the group with the same ground truth. |
| `records_left_out` | The number of records left out of the pooling because they differ between the runs, which is 0 in every row. |
| `metric` | The name of the number. |
| `value` | The number pooled over the repeats: each record's counts are averaged over the runs, then summed over the records, and the ratio is taken. |
| `low_95` | The lower end of the 95% clustered Wilson range, with the record as the cluster. |
| `high_95` | The upper end of that range. |
| `bootstrap_low_95` | The lower end of the 95% range of a record-level bootstrap with 10,000 redraws, given for precision, recall and F1 at both pair levels only. |
| `bootstrap_high_95` | The upper end of that range. |
| `between_record_variance` | The variance, across the records, of each record's own proportion. |
| `within_record_variance` | The mean, over the records, of the variance of the record's proportion across the runs, which is empty for a group of one run. |

The two numbers `describes majority baseline` and `describes per entity class average` have no range, because they are computed over every record of every repeat taken together.

### `metrics_per_run.csv`

Each row gives one number of one group, with each run's own value and their spread.

| Column | Meaning |
|---|---|
| `part`, `schema`, `thinking`, `model` | The group, as in `metrics_pooled.csv`. |
| `metric` | The name of the number. |
| `run_070_1`, `run_070_2`, `run_070_3` | The run ids of step 070's evaluations of the group's first, second and third run, empty after the first for a group of one run. |
| `value_1`, `value_2`, `value_3` | The number in each of those runs. |
| `mean` | The mean of the number across the runs. |
| `sd` | The sample standard deviation across the runs, empty for one run. |
| `min` | The lowest value across the runs. |
| `max` | The highest value across the runs. |
| `width` | The highest value minus the lowest, empty for one run. |

### `per_record.csv`

Each row gives one record's own numbers in one run, from its own counts, with no range (step 070's numbers per record).

| Column | Meaning |
|---|---|
| `part`, `schema`, `thinking`, `model` | The group the run belongs to. |
| `repeat` | The repeat number of the run within its group. |
| `run_070` | The run id of step 070's evaluation. |
| `run_060` | The run id of step 060's extraction it evaluated. |
| `position` | The record's position in the pool of step 030. |
| `record_id` | The record's id on data.nasa.gov. |
| `title` | The record's title as step 020 wrote it. |
| `extraction_failed` | `yes` when step 060's model call for the record failed, and `no` otherwise. |
| `ground_truth_triples` | The number of the record's ground truth triples. |
| `within_reach` | The number of those ground truth triples that are within reach. |
| `within_strict_reach` | The number of those ground truth triples that are within strict reach. |
| `occurrences` | The number of the record's extracted triples, as step 070 counts them. |
| `untranslatable` | The number of those extracted triples that the translation table sends to no predicate, which are left out of precision. |
| `pending_pairs` | The number of extracted triples paired exactly with a fact that waits on an expert. |
| `exact_pairs` | The number of exact pairs. |
| `exact_strict_pairs` | The number of exact pairs that are strict pairs. |
| `partial_pairs` | The number of pairs at the partial level, which counts exact and partial pairs together. |
| `partial_strict_pairs` | The number of those pairs that are strict pairs. |
| `exact_precision`, `exact_recall`, `exact_f1` | The record's precision, recall and F1 at the exact level. |
| `partial_precision`, `partial_recall`, `partial_f1` | The record's precision, recall and F1 at the partial level. |

### `by_drafting_model.csv`

Each row gives one number of one group for the ground truth triples one model drafted (`helpers/held_out_results.md`), pooled over the repeats.

| Column | Meaning |
|---|---|
| `part`, `schema`, `thinking`, `model`, `runs`, `records_pooled` | The group, as in `metrics_pooled.csv`. |
| `drafted_by` | The model that drafted these ground truth triples (step 050). |
| `spellings` | How the ground truth files spell that model's name. |
| `ground_truth_triples` | The number of ground truth triples that model drafted in the pooled records. |
| `records_with_one` | The number of pooled records with at least one of them. |
| `metric` | The number: `Recall (exact)`, `Recall (partial)`, `Exact share of pairs`, `Entity-class accuracy (partial)`, `Precision, attributed (partial)` or `F1, attributed (partial)`. |
| `value`, `low_95`, `high_95`, `between_record_variance`, `within_record_variance` | The pooled value, its range and its variances, as in `metrics_pooled.csv`. |

### `notable_records.csv`

Each row names a record that stands out across the nine models with the induced schema (thinking `lowest`), on the tuning records or on the held-out records. A model's partial F1 on a record is taken from the record's counts over the model's three repeats.

| Column | Meaning |
|---|---|
| `part` | The part of the pool, `tuning` or `held-out`. |
| `criterion` | The criterion the record meets. |
| `definition` | The definition of that criterion. |
| `rank` | The record's rank under the criterion. |
| `position`, `record_id`, `title` | The record, as in `per_record.csv`. |
| `ground_truth_triples` | The number of the record's ground truth triples. |
| `within_reach` | The number of those that are within reach, the fewest in any run. |
| `not_within_reach` | The number of the record's ground truth triples that are not within reach. |
| `models` | The number of models with a partial F1 on the record. |
| `mean_partial_f1` | The mean, over the models, of each model's partial F1 on the record. |
| `min_partial_f1` | The lowest of those partial F1 values. |
| `max_partial_f1` | The highest of those partial F1 values. |
| `models_at_0` | The number of models whose partial F1 on the record is 0. |

The criteria are the five lowest and the five highest mean partial F1, every record without a ground truth triple, every record on which every model's partial F1 is 0, and the five records with the most ground truth triples not within reach.

## The runs, the models and their calls

### `runs.csv`

Each row describes one run of step 060, from its report and its recipe.

| Column | Meaning |
|---|---|
| `schema`, `thinking`, `model`, `repeat` | The run's schema, reasoning setting, model and repeat number. |
| `run_060` | The run id of step 060. |
| `run_070_tuning` | The run id of step 070's evaluation of the run on the tuning records. |
| `run_070_held_out` | The run id of step 070's held-out look at the run, given for the induced schema only. |
| `model_served` | The model version that the answers record as the one that answered, empty when the answers record none. |
| `thinking_sent` | The value that the setting `thinking` was sent as. |
| `records_extracted` | The number of records step 060 extracted from. An induced-schema run extracted from all 80 finished records, and a ground-truth-schema run from the 40 tuning records. |
| `records_failed` | The number of records left out because a model call for one of their text pieces failed. |
| `classed_triples_in_answer_texts` | The number of texts counted in the report's table *Classed triples per text*. |
| `classed_triples_in_answer_min`, `_max`, `_mean`, `_median`, `_sd` | The lowest, the highest, the mean, the median and the sample standard deviation, over those texts, of the number of classed triples in the model's answer for a text. A classed triple in the answer is counted once here: these are the extracted triples plus those removed for their source text or their component classes, and the duplicates and malformed items are not counted. |
| `classed_triples_in_answer_total` | The total number of those classed triples in the answers, over all the texts. |
| `classed_triples_in_answer_texts_with_none` | The number of texts whose answer had no such classed triple. |
| `extracted_triples_texts`, `_min`, `_max`, `_mean`, `_median`, `_sd`, `_total`, `_texts_with_none` | The same figures for the extracted triples. |
| `removed_total` | The number of classed triples in the answers that step 060's checks removed, for any reason. |
| `removed_component_class_not_in_schema` | The number removed because they use an entity class or predicate the schema doesn't have. |
| `removed_source_text` | The number removed because their source text is missing or isn't in the record's text. |
| `removed_component_class_not_in_schema_and_source_text` | The number removed for both of those reasons at once, each counted once. |
| `removed_duplicate` | The number removed because the same classed triple was already in the record. |
| `removed_describes_triple` | The number removed because they were a describes triple of the model's own, which is 0 in every run. |
| `removed_malformed` | The number of items of the answers removed because they are not classed triples at all. |
| `model_calls_failed` | The number of model calls that failed after the model client's own retries, cut-offs included. |
| `model_calls_cut_off` | The number of model calls whose answer was cut off at the answer limit. |
| `answer_limit_tokens` | The answer limit, in tokens, the calls were sent with. |

### `model_calls.csv`

Each row describes the model calls of one run on one record or text. Step 040 has one row per induction text for its extraction calls, then one row for each other kind of call with the number made. Step 060 has one row per run and record.

| Column | Meaning |
|---|---|
| `step` | The step that made the calls, `040_induce_schema` or `060_extract`. |
| `run` | The run id. |
| `model` | The model called. |
| `thinking` | The reasoning setting of the run. |
| `thinking_sent` | The value that the setting was sent as. |
| `call` | The kind of call: `extract` (one call per text piece), or step 040's `label`, `merge`, `split`, `define` and `test`. |
| `record_id` | The record or induction text, empty for step 040's other kinds of call. |
| `calls` | The number of calls: the text pieces of the record, or the number of calls of that kind. |
| `outcome` | What came of the calls: `extracted` or `failed` for step 060, and `answered` or `failed` for step 040. |
| `error` | Why the calls failed, empty when they did not. |
| `triple_instances` | Step 040 only: the number of triple instances found in the induction text. |
| `malformed_items` | Step 040 only: the number of items of the answer that were not triple instances. |
| `extracted_triples` | Step 060 only: the number of the record's extracted triples. |
| `removed_classed_triples` | Step 060 only: the number of the record's classed triples in the answer that the checks removed. |

The runs record no token count per call, so the token counts are given per run in `model_tokens.csv`.

### `model_tokens.csv`

Each row gives the tokens of one run of step 040 or step 060, as the run's report gives them.

| Column | Meaning |
|---|---|
| `step`, `run`, `model`, `thinking` | The run, as in `model_calls.csv`. |
| `sent_not_from_cache` | The tokens sent that were not read from a cache. |
| `sent_read_from_cache` | The tokens sent that were read from a cache. |
| `sent_written_to_cache` | The tokens sent that were written to a cache. |
| `received` | The tokens received, thinking included. |
| `received_as_thinking` | The tokens received as thinking, where the report gives them. |
| `model_calls_failed` | The number of model calls that failed, cut-offs included. |
| `model_calls_cut_off` | The number of model calls cut off at the answer limit. |

### `models.csv`

Each row gives one model in one role, from the runs' recipes and from the files in `annotations/`.

| Column | Meaning |
|---|---|
| `model` | The model. |
| `role` | What the model did. |
| `where` | The step or helper that called the model. |
| `count` | How much the model did in that role. |
| `count_of` | What `count` counts. |
| `thinking` | The reasoning setting of its calls, where these files record it. |
| `thinking_sent` | The value that the setting was sent as. |
| `temperature` | Whether and how a temperature was sent. |
| `answer_limit_tokens` | The answer limit, in tokens, the calls were sent with. |
| `prompt_files` | The prompt files the model was sent, as paths in this repository. |

### Each model's role

Each model's input can be rebuilt from its prompt files (the column `prompt_files` of `models.csv`), the schema it was shown, and the record's text (`record_texts.jsonl`). How each step fills its prompts is in its guide, section *Prompts*.

- **Schema induction (step 040):** `claude-opus-5-5`, at a high reasoning level, found the triple instances of the 138 induction texts and induced the schema from them, with the prompts of `040_induce_schema/040_induce_schema.md`, *Prompts*. Every induced-schema run of step 060 used this induced schema.
- **Extraction (step 060):** the nine models of `runs.csv` extracted at their maker's lowest reasoning level (`thinking_sent` gives the value sent: `low`, `minimal` or `none`), and four of them also at a high level. Each run was shown either the ground truth schema (`annotations/ground_truth_schema.txt`) or the induced schema, with the prompts of `060_extract/060_extract.md`, *Prompts*.
- **Drafting the ground truth (step 050):** the models named in the ground truth files' column `drafted_by` drafted the ground truth triples, with the prompts of `050_annotate/050_annotate.md`, *Prompts*. A record is finished only once I have checked that every fact of its text is there, so I read and corrected every drafted triple of these records.
- **Second opinion on the ground truth** (`helpers/second_opinion.py`): another model drafted the finished records again with step 050's prompt, three repeats each. The file `annotations/second_opinion.csv` records, for each ground truth triple, in how many repeats it was found.
- **Second judge** (`helpers/second_judge.py`): a model of another maker decided again, without seeing my decision, my decisions on facts the second opinion proposed (`annotations/second_judge.csv`, task `facts`).
- **Translation proposals (step 070):** step 070 made no model call in these evaluations, as each of their reports shows 0 answers received. The translation table it used is `annotations/component_class_mapping.csv`.
- **Partial pair reviews:** Claude Fable 5.2 reviewed every partial pair of the tuning and held-out records under the annotation guidelines, and its verdicts are in `annotations/partial_pair_reviews.csv`.

## Records and triples

### `records.csv`

Each row describes one record the runs used: the 138 induction texts first, then the 80 finished records in pool order.

| Column | Meaning |
|---|---|
| `record_id` | The record's id on data.nasa.gov. |
| `title` | The record's title. |
| `maintainer` | The record's maintainer as data.nasa.gov names it. |
| `stratum` | The stratum of the pool or of the induction sample the record was drawn from. |
| `role` | The record's role: `induction text`, `tuning` or `held-out`. |
| `pool_position` | The record's position in the pool, given for finished records only. |
| `induction_duplicate_kind` | Whether the record's title, its notes, or both are also those of an induction text (`title only`, `notes only`, `whole text`), empty when neither is. |
| `induction_triple_instances` | For an induction text, the number of triple instances step 040 found in it. |
| `ground_truth_triples` | For a finished record, the number of its ground truth triples. |
| `ground_truth_triples_by_drafting_model` | For a finished record, the number of its ground truth triples each model drafted. |
| `within_reach_ground_truth_schema` | The number of its ground truth triples within reach with the ground truth schema, the fewest in any run. |
| `within_reach_induced_schema` | The number of its ground truth triples within reach with the induced schema, the fewest in any run. |
| `not_within_reach_induced_schema` | The number of its ground truth triples not within reach with the induced schema. |
| `partial_f1_<schema>_<thinking>_<model>` | The record's partial F1 in that group, from its counts summed over the group's runs. |
| `partial_pairs_<schema>_<thinking>_<model>` | The record's number of pairs at the partial level in that group, the mean over the group's runs. |

### `record_texts.jsonl`

Each line holds one record of `records.csv`: its `id`, its `role`, and its `title` and `notes` as step 020 wrote them, which are the text the models read. They are public catalog text from data.nasa.gov.

### `induction_triple_instances.csv`

Each row is one triple instance that schema induction found. The column `text_id` is the induction text, `instance` is the triple instance's order in the text's answer (counted from 0), and `subject`, `predicate`, `object` and `source_text` are the triple instance and the words of the text it came from.

### `ground_truth_triples.csv`

Each row is one ground truth triple of the 80 finished records, describes triples left out.

| Column | Meaning |
|---|---|
| `ground_truth_ref` | The triple's reference in the ground truth files. |
| `record_id` | The record. |
| `part` | The record's part of the pool. |
| `position` | The record's position in the pool. |
| `subject`, `subject_class`, `predicate`, `object`, `object_class` | The classed triple. |
| `source_text` | The words of the record's text that state the fact. |
| `drafted_by` | The model that drafted the triple, as the ground truth file writes it, empty when none is recorded. |

### `extracted_triples.csv`

Each row is one extracted triple of one run, as step 070 compared it. The tuning records' rows come from the run's evaluation on the tuning records, and the held-out records' rows from its held-out look.

| Column | Meaning |
|---|---|
| `model`, `schema`, `thinking`, `repeat` | The run's model, schema, reasoning setting and repeat number. |
| `run_060` | The run id of step 060. |
| `run_070` | The run id of step 070's evaluation. |
| `part` | The record's part of the pool. |
| `record_id`, `position` | The record and its position in the pool. |
| `extracted_ref` | The extracted triple's row in the run's `extracted_triples.csv`. |
| `status` | What came of the extracted triple on scoring: `exact pair`, `partial pair`, `extracted only` (it paired with no ground truth triple), or `untranslatable` followed by the reason. |
| `entity_classes_right` | For a pair, `yes` when it is a strict pair and `no` when it is not. |
| `subject_and_object_swapped` | For a pair, `yes` when the extracted triple paired with its subject instance and object instance swapped, which only the predicate ALSO_KNOWN_AS allows. |
| `extracted_subject`, `extracted_subject_class`, `extracted_predicate`, `extracted_object`, `extracted_object_class` | The classed triple as the model extracted it. |
| `source_text` | The words of the record's text the model gave as the fact's source. |
| `flags` | The flags step 060's checks put on the extracted triple. |
| `translated_subject_class`, `translated_predicate`, `translated_object_class` | The extracted triple's translation into the ground truth schema, given only where it differs from the extracted one. |
| `ground_truth_ref` | The ground truth triple it paired with, empty when it paired with none. |

### `extracted_triples_removed.csv`

Each row is one item of a model's answer that step 060's checks removed. The columns `model`, `schema`, `thinking`, `repeat` and `run_060` give the run, and `reason` gives why the item was removed, with two reasons separated by a space when both applied. The columns `record_id`, `subject`, `subject_class`, `predicate`, `object`, `object_class`, `source_text` and `flags` give the item as the answer had it.

### `ground_truth_outcomes.csv`

Each row gives what came of one ground truth triple in one run.

| Column | Meaning |
|---|---|
| `model`, `schema`, `thinking`, `repeat`, `run_060`, `run_070` | The run, as in `extracted_triples.csv`. |
| `part`, `record_id` | The record's part of the pool and the record. |
| `ground_truth_ref` | The ground truth triple. |
| `outcome` | `exact pair`, `partial pair`, or `missed` when no extracted triple paired with it. |
| `entity_classes_right` | For a pair, `yes` when it is a strict pair and `no` when it is not. |
| `within_reach` | `yes` when the ground truth triple was within reach in the run. |
| `within_strict_reach` | `yes` when it was within strict reach in the run. |
| `extracted_ref` | The extracted triple it paired with, empty when it was missed. |

## What is not here

- No file was missing when the folder was written: every run's files were found as the run wrote them, and the script names any it can't find.
- The runs record tokens per run only, so `model_tokens.csv` gives no count per call.
- The settings of the drafting runs of step 050 and of the second opinion's and second judge's runs are in their own reports in `outputs/`, not here; `models.csv` gives what the files in `annotations/` record.
