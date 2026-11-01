# A second opinion on the ground truth

Many [ground truth triples](../docs/terminology.md#4-ground-truth-and-samples) were first drafted by a [model](../docs/terminology.md#8-the-pipeline) (step 050) and corrected by me; the rest I wrote. The facts the drafting model missed are the facts I had to add alone, and a person correcting a model's draft tends to keep what is there ([`070_evaluate/metrics/recall.md`](../070_evaluate/metrics/recall.md), *Assumes and can't see*). The standard remedy is a second annotator from another source, whose annotation shows what the first one missed: Tan et al., "Revisiting DocRED – Addressing the False Negative Problem in Relation Extraction", EMNLP 2022 ([paper](https://aclanthology.org/2022.emnlp-main.580/)), re-annotated a benchmark and found its labels incomplete. Here the second annotator is another model, which gives a **second opinion**: it drafts every [finished record](../docs/terminology.md#4-ground-truth-and-samples) again, and each ground truth triple is matched against that fresh draft.

```
py helpers/second_opinion.py                       draft every finished record again (asks before paying), match, report
py helpers/second_opinion.py --apply true          the same, and record what was found in annotations/second_opinion.csv
py helpers/second_opinion.py --ids <id>,<id>       only these finished records
py helpers/second_opinion.py --model <name>        another model (the default: gemini-4-argon)
```

The ground truth is never changed: the second opinion writes no [drafted batch](../docs/terminology.md#4-ground-truth-and-samples), and nothing in `annotations/` unless `--apply true`, which writes only `annotations/second_opinion.csv` (below). Decided on 2026-11-01; the entry in [`docs/improvements.md`](../docs/improvements.md), section *050_annotate*, says why.

## How it drafts

Exactly the way step 050 drafts, so the second opinion is a draft 050 could have made: 050's prompt (`050_annotate/050_annotate_prompts/draft.txt`, with the shared rules and reply format of `common/common_prompts/`), the [ground truth schema](../docs/terminology.md#3-schemas) as 050 shows it (the file, plus the [component classes](../docs/terminology.md#3-schemas) coined and the [patterns](../docs/terminology.md#3-schemas) used in the finished [tuning records](../docs/terminology.md#7-evaluating-extraction-step-070): `common/common_helpers/ground_truth.py`, `ground_truth_schema_view`), 050's parsing and checks (`common/common_helpers/extraction.py`, `build_rows`), and 050's settings `max_chars`, `workers` and `thinking` (medium). The code is 050's own, called from `helpers/second_opinion.py` (`050_annotate/050_annotate_helpers/records.py`, `read_inputs` and `items_for`; `draft.py`, `ask_model`; `moves.py`, `build_rows`), so the two can't drift apart. One thing differs: 050 skips a record already in the ground truth; the second opinion drafts only records that are finished there (`common/common_helpers/ground_truth.py`, the selection `EVALUABLE`: every part of the [pool](../docs/terminology.md#4-ground-truth-and-samples), held-out records included, and records outside the pool), in pool order, or those of them named by `--ids`.

It runs in the frame every [step](../docs/terminology.md#8-the-pipeline) runs in (`common/common_helpers/step.py`, `run_step`): a [run id](../docs/terminology.md#8-the-pipeline) (`second_opinion_<date>_<time>`), a [log](../docs/terminology.md#8-the-pipeline), a [report](../docs/terminology.md#8-the-pipeline) and a [manifest](../docs/terminology.md#8-the-pipeline) in `outputs/intermediate_results/second_opinion/`, which record the model, every [setting](../docs/terminology.md#8-the-pipeline), the exact model the service said answered, the settings each call was sent with, and the prompts by [fingerprint](../docs/terminology.md#8-the-pipeline). It asks before its first [paid call](../docs/terminology.md#8-the-pipeline), showing every note first: which records it drafts (by part), what was skipped and why (an id not in the catalog, a record not finished, one with no text), whether some ground truth triples were drafted by the very model asked (column `drafted_by`), and the ground truth's problems. Every answer is cached in its own `cache/`, so a rerun, `--apply true` among them, pays nothing.

**The model.** `gemini-4-argon` by default (Google's flagship, released 2026-09-30; usable through NASA's LiteLLM on 2026-11-01; `gemini-3.1-pro-preview` is usable too): another maker than 060's model (`claude-opus-5-5`), and a later model than 050's (`gemini-2.5-pro`), so a fact both of those miss still has a chance. Through LiteLLM it is sent no temperature (Google: "Remove `temperature`, `top_p`, and `top_k` from your requests. If provided, they are ignored", [Gemini 4 guide](https://ai.google.dev/gemini-api/docs/latest-model)) and its thinking level as `reasoning_effort` (LiteLLM maps it to Gemini's `thinking_level`, [LiteLLM's Gemini page](https://docs.litellm.ai/docs/providers/gemini)); the answer limit is the pipeline's 32,000 tokens (`common/common_helpers/llm.py`, `MAX_ANSWER_TOKENS`; Google advises at least 32,768 for this model, so a cut-off answer is possible on a very long record, and the report says so). With `LITELLM_BYPASS_ANSWER_CACHE=1` in `.env`, LiteLLM's own answer cache is bypassed as in every step.

## How it matches

For each drafted record, its ground truth triples (the [describes triple](../docs/terminology.md#2-triples) left out: code writes it on both sides) are paired with the fresh draft's [classed triples](../docs/terminology.md#2-triples) by step 070's own pairing (`070_evaluate/070_evaluate_helpers/pairing.py`, `pair_triples`): the largest set of [exact pairs](../docs/terminology.md#7-evaluating-extraction-step-070), then of [partial pairs](../docs/terminology.md#7-evaluating-extraction-step-070), each triple with at most one partner, ties broken by the triples' contents ([`070_evaluate/metrics/pairs.md`](../070_evaluate/metrics/pairs.md)). No [translation table](../docs/terminology.md#7-evaluating-extraction-step-070): both sides use the ground truth schema. No [partial pair review](../docs/terminology.md#7-evaluating-extraction-step-070) applies: those verdicts are about 060's extracted triples. A ground truth triple is **found by the second opinion** when it has a partner (exact or partial), **not found** otherwise; a draft triple with no partner is a fact the ground truth lacks, or one its rules leave out on purpose, or a wrong one.

A ground truth triple not found was stated by one annotator only. It is not thereby wrong: the fresh draft can miss a fact, or state it in words the pairing can't match (*When a pair isn't the same fact*, in `pairs.md`), or leave out what the [annotation guidelines](../docs/terminology.md#4-ground-truth-and-samples) ask for (a qualifier taken out of an instance, rule 19). What it does tell: step 070's recall on the triples found is recall on facts two annotators agree on; recall on the triples not found is recall on facts only I (or the drafting model and I) stated.

## What it writes

In `outputs/intermediate_results/second_opinion/`:

| File | Contents |
|---|---|
| `second_opinion_triples.csv` | The fresh draft, in a drafted batch's columns (`050_annotate/050_annotate.md`, *Outputs*), `drafted_by` naming the second opinion's model. Every drafted record's, held-out ones included: read the held-out records' rows only through the counts below. |
| `second_opinion_matches.csv` | One row per ground truth triple of each drafted record: `record_id`, `position`, `part`, `status` (`found (exact)`, `found (partial)`, `not found`), `entity_classes_agree` (`yes`/`no` for a pair: whether it is a [strict pair](../docs/terminology.md#7-evaluating-extraction-step-070)), the ground truth triple (`ground_truth_*`, with its `drafted_by`), and its partner (`draft_*`, with the draft's [source text](../docs/terminology.md#1-records-and-their-text)); then, for TUNING records only, one row per draft triple with no partner (`status` `draft only`): the facts to review. |
| `second_opinion_details.json` | The run's record: run id, model, service, the settings as sent, the settings given; each record's pool position, part, status (`drafted` or `failed`, with the error), ground truth triples, found exact, found partial, not found, draft only, and the items 050's checks removed; the records skipped while choosing; the records left out because a model call failed; what `--apply true` wrote. |
| `cache/`, `_manifest.json` | As for every step. |

The report (`outputs/reports/second_opinion_<date>_<time>.md`), section *Results*: a table per record (ground truth triples; found exact, found partial, not found; draft only); *Found by the second opinion*, the counts by part of the pool and by the ground truth triples' `drafted_by` (a row a model drafted and I corrected, or a row I wrote); *The second opinion's facts the ground truth lacks (tuning records)*, every draft-only triple of the tuning records with its source text, grouped by record, for review; *Provenance recorded*, what `--apply true` wrote, or how to write it.

**Held-out records.** They are drafted too, so that step 070 can group their triples, and their found / not found counts are in the table and the counts. Their draft-only triples are counted and nowhere listed, not in the report nor in `second_opinion_matches.csv`: reviewing them would let the [held-out part](../docs/terminology.md#7-evaluating-extraction-step-070) shape the ground truth and the annotation guidelines (`annotations/guidelines.md`, *Before you start*). Read `second_opinion_triples.csv` with the same care.

## The provenance: `annotations/second_opinion.csv`

With `--apply true`, one row per ground truth triple of every record drafted this run, keyed by the record's id and the classed triple as the ground truth writes it (compared as step 070's exact pairs compare: `common/common_helpers/triples_io.py`, `classed_key`):

| Column | Meaning |
|---|---|
| `id`, `subject`, `subject_class`, `predicate`, `object`, `object_class` | The ground truth triple: the key. Not a second home of the fact: the ground truth file stays the one place it is stated, and a row whose triple is no longer there (reworded, deleted, its record unfinished again) is stale. |
| `checked_by` | The models whose second opinion was matched against this record, comma-separated. |
| `found_by` | Of those, the models whose draft paired with this triple (exact or partial pair). |
| `found_exact_by` | Of those, the models whose draft paired with it exactly. |

Applying with a model rewrites that model's verdicts on the records drafted now (it is removed from the three columns where it no longer belongs, then added where it does), keeps every other model's, drops a row of those records whose triple is no longer in the ground truth (so a reworded triple needs the second opinion applied again, which the cache makes free), and leaves the rows of records not drafted now as they are. Rows are ordered by pool position. The file is read by `common/common_helpers/second_opinion.py`; `drafted_by`, in the ground truth files, stays what it is: who first drafted the row. The file starts with its header only, and nothing but `--apply true` writes it. Commit it after applying.

A ground truth triple's **group** by the second opinion: *found* (`found_by` names a model), *not found* (`checked_by` names one, `found_by` none), *not checked* (no row: the record wasn't drafted, or the triple was reworded since).

## What step 070 does with it

Step 070 reads the file and gives, for each part, under *Metrics*, the subsection *By the second opinion*: for each group, its ground truth triples, [recall](../docs/terminology.md#7-evaluating-extraction-step-070) at both pair levels, and at the partial level its pairs, [precision](../docs/terminology.md#7-evaluating-extraction-step-070) and [F1](../docs/terminology.md#7-evaluating-extraction-step-070), with the formula (`070_evaluate/070_evaluate.md`, *By the second opinion*). It warns when a row names a classed triple that is no longer a ground truth triple of an evaluated record. The same numbers are in `metrics.json` (`parts.<part>.numbers.second_opinion`). A ground truth not yet checked by any second opinion gives no subsection.

## What it can't see

- **A fact both annotators missed** is still invisible: the second opinion lowers the number of such facts, it doesn't count them.
- **The same mistakes.** Two models of one maker, or two trained on similar data, miss similar facts; the default model is from another maker than 060's, but from the same maker as 050's. The report notes every ground truth triple whose `drafted_by` is the very model asked.
- **Words the pairing can't match**: a fact stated in different words on the two sides counts as not found (`pairs.md`, *Assumes and can't see*).
- **The schema view includes the record's own coined component classes**: the model sees, as 050 does, the component classes and patterns the finished tuning records use, these records among them; not their triples.
- **No model answers the same twice**: the setting `repeat` (2, 3, ...) asks again into answers of its own, as in every step.
