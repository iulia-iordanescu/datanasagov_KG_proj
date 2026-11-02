# A second judge of my decisions

Two kinds of my decisions in `annotations/` judge what a [model](../docs/terminology.md#8-the-pipeline) wrote: the [second opinion](../docs/terminology.md#4-ground-truth-and-samples)'s facts the [ground truth](../docs/terminology.md#4-ground-truth-and-samples) lacks, drafted by `gemini-4-argon` (the column `decision` of `annotations/second_opinion_candidates.csv`: `helpers/second_opinion.md`, *The draft's facts to review*), and the [verdicts](../docs/terminology.md#7-evaluating-extraction-step-070) on [partial pairs](../docs/terminology.md#7-evaluating-extraction-step-070), whose extracted triples come from `claude-opus-5-5` (`annotations/partial_pairs_to_review.csv`: `helpers/partial_pairs.md`). They are one rater's decisions, and they may lean the way of the models whose output they judge; a model asked to judge tends to favor output like its own (self-preference). The [second judge](../docs/terminology.md#4-ground-truth-and-samples) is a second, independent rater: a model from another maker than both, which sees everything a decision was made from but never the decision. How far it reaches the same decisions is the inter-annotator agreement the field reports for an annotation (Artstein & Poesio, "Inter-Coder Agreement for Computational Linguistics", Computational Linguistics 34(4), 2008, [paper](https://aclanthology.org/J08-4004/)).

```
py helpers/second_judge.py                              judge both tasks (asks once before paying), report
py helpers/second_judge.py --tasks facts                one task only: facts or partial_pairs
py helpers/second_judge.py --ground_truth_at <commit>   the facts task shows the ground truth as it was at that Git commit
py helpers/second_judge.py --model <name>               another judge (the default: gpt-6-astra)
```

It runs in the frame every [step](../docs/terminology.md#8-the-pipeline) runs in (`common/common_helpers/step.py`, `run_step`): a [run id](../docs/terminology.md#8-the-pipeline) (`second_judge_<date>_<time>`), a [log](../docs/terminology.md#8-the-pipeline), a [report](../docs/terminology.md#8-the-pipeline) and a [manifest](../docs/terminology.md#8-the-pipeline), which record the model, every [setting](../docs/terminology.md#8-the-pipeline), the settings each call was sent with and the two prompts by [fingerprint](../docs/terminology.md#8-the-pipeline). It asks before its first [paid call](../docs/terminology.md#8-the-pipeline), and keeps every answer in `outputs/intermediate_results/second_judge/cache/` (`facts.json`, `partial_pairs.json`), so a rerun pays nothing while the prompts are unchanged (it then doesn't ask before paying; if it asks, its question gives the count to pay: `docs/running_on_nasa_laptop.md`, *When a rerun is free*); the setting `repeat` (2, 3, ...) asks again, with answers of their own (`docs/running_on_nasa_laptop.md`, *Repeats: how much the numbers vary on their own*). Decided on 2026-11-02 (`docs/improvements.md`, section *050_annotate*).

## The two tasks

Each is judged, written and reported on its own. One model call per row, the prompt's shared part first (instructions, then the guidelines and the schema, the same for every row), so a service that caches the start of a prompt can reuse it.

**Facts** (`helpers/helpers_prompts/second_judge_facts.txt`). For each row of `annotations/second_opinion_candidates.csv` with a `decision` (a [classed triple](../docs/terminology.md#2-triples) the second opinion proposed for a [tuning record](../docs/terminology.md#7-evaluating-extraction-step-070), which no [ground truth triple](../docs/terminology.md#4-ground-truth-and-samples) paired with), the judge gets: the [annotation guidelines](../docs/terminology.md#4-ground-truth-and-samples) (`annotations/guidelines.md`, the whole file, as I read it), the [ground truth schema](../docs/terminology.md#3-schemas) as step 050 shows it, the record's title and [text](../docs/terminology.md#1-records-and-their-text) (all its [text fields](../docs/terminology.md#1-records-and-their-text), as the [annotation tool](../docs/terminology.md#4-ground-truth-and-samples) shows them), the record's ground truth triples with their [source texts](../docs/terminology.md#1-records-and-their-text) (never who drafted them), and the candidate with its source text. It answers one of the three kinds of decision, `added`, `left out` or `already in the ground truth in other words`, with the rule of the guidelines it relies on most (its section's heading and its number) and a reason of one or two sentences, as JSON. A rule the guidelines don't have is listed in the report. One classed triple of a record is judged once, whichever model proposed it (a decision is about the fact).

**Partial pairs** (`helpers/helpers_prompts/second_judge_pairs.txt`). For each row of `annotations/partial_pairs_to_review.csv` with a verdict (in its column `verdict`, or, once moved, in `annotations/partial_pair_reviews.csv`), the judge gets the record's title and text, the ground truth triple and the extracted triple as the row writes them, and what "the same fact" means, quoted from [`070_evaluate/metrics/pairs.md`](../070_evaluate/metrics/pairs.md) (*When a pair isn't the same fact*, and the examples *The largest set of pairs* and *Whole words inside, not any overlap*; a test keeps each quote in that file). It answers `same fact` or `not the same fact`, with a reason.

**Blind.** No prompt holds my label: each is built from the record and the row's triples only, so it is the same whatever the decision or verdict (a test builds it under every label and finds one prompt). The judge sees neither the model that proposed a candidate, nor how many repeats did, nor who drafted a ground truth triple.

**Only rows with my label.** A row without a decision or verdict is not judged, and the notes before paying name it: a judge's label read before deciding would shape the decision, and the agreement would no longer measure two independent raters. Decide it, then run this again (it pays only for the new rows).

**The ground truth as it was.** Applying a decision can change the ground truth: a candidate decided `added` becomes a ground truth triple, and the judge would then find it there and answer *already in the ground truth in other words*. So `--ground_truth_at <commit>` shows the judge each record's ground truth triples as they were at that Git commit, read from Git into `outputs/intermediate_results/second_judge/ground_truth_at_<commit>/` (the files in `annotations/` aren't touched). For the 150 decisions of 2026-11-01 that is `13a71b1` (*Second opinion applied*), the commit before `67081ea` applied them (four ground truth triples added and one changed). Without the setting, the run notes the ground truth triples drafted by the candidates' model, which are most likely such additions; with it, it notes whether the guidelines or the ground truth schema changed since that commit, since the judge reads today's.

## The judge

`gpt-6-astra` by default: OpenAI's flagship (released 2026-09-03). The fallback, if NASA's LiteLLM doesn't offer it, is `gpt-6.1-sol` (`--model gpt-6.1-sol`). Try it first, with one tiny paid call: `py helpers/models.py --try gpt-6-astra`.

The judge must come from another maker than the extraction model (`claude-opus-5-5`, Anthropic) and than every model whose drafts the candidates come from (`gemini-4-argon`, Google): a judge from one of those makers stops the run before it pays, and so does a model whose maker its name doesn't tell (`common/common_helpers/llm.py`, `MAKERS`). After the run, a warning names any model LiteLLM says answered that isn't the judge's maker's.

What it is sent, through LiteLLM, each verified in OpenAI's own docs on 2026-11-02 (`common/common_helpers/llm.py`, the rules for OpenAI's GPT-6 models):

- **No temperature:** "When reasoning effort is not `none`, remove `temperature`, `top_p`, and `top_logprobs`", and "GPT-6 Astra and GPT-6.1 Sol do not support the `none` reasoning effort" ([OpenAI, latest model guide](https://developers.openai.com/api/docs/guides/latest-model)).
- **`reasoning_effort`, the setting `thinking`** (`medium` by default): Chat Completions take `reasoning_effort` (same guide); GPT-6 Astra supports "`low`, `medium`, `high`, `xhigh`, and `max`" ([OpenAI, GPT-6 Astra](https://developers.openai.com/api/docs/models/gpt-6-astra)), and LiteLLM passes it on ([LiteLLM, GPT-6 Astra](https://docs.litellm.ai/blog/gpt_6_astra)). `--thinking model_default` sends none.
- **`max_completion_tokens`, not `max_tokens`:** 32,000 tokens, as for every model. OpenAI's reference calls `max_tokens` "deprecated in favor of `max_completion_tokens`" ([Chat Completions reference](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create)), and LiteLLM's note says a LiteLLM version before its fix sends `max_tokens` on unchanged, which OpenAI rejects; GPT-6 Astra's answers may be up to 128,000 tokens.

## Agreement

For each task, over the rows judged, with my label and the judge's:

- **Raw agreement** *p*o = the rows both label the same ÷ the rows judged. The share of my decisions an independent reader reaches.
- **Agreement expected by chance** *p*e = Σ over the labels *k* of (my share of rows labelled *k*) × (the judge's share of rows labelled *k*): how often two raters would agree if each labelled at random with its own shares of the labels (Cohen's kappa uses each rater's own shares: Artstein & Poesio, section 2.4).
- **Cohen's kappa** κ = (*p*o − *p*e) ÷ (1 − *p*e): the share of the agreement possible beyond chance that was reached. 1: full agreement; 0: no more than chance; below 0: less than chance. Undefined when *p*e = 1 (both raters gave every row one same label). Artstein & Poesio (section 5.3) doubt "that a single cutoff point is appropriate for all purposes", and "feel that if a threshold needs to be set, 0.8 is a good value".
- **Per label:** my count, the judge's, the rows both gave it, and the specific agreement 2 × both ÷ (ours + the judge's) (Cicchetti & Feinstein, "High agreement but low kappa: II. Resolving the paradoxes", Journal of Clinical Epidemiology 43(6), 1990), with the confusion matrix (rows: my label; columns: the judge's).
- **The disagreements,** each with the record, the candidate or the pair, both labels, the judge's rule and its reason: the list to read.

**Why raw agreement beside kappa.** When one label is far more common than the others, *p*e is high, and κ is low even when the raters agree on almost every row: "chance-corrected agreement may be low even though *A*o is high" (Artstein & Poesio, section 3.2, the prevalence effect). *Suppose:* of 100 rows, both label 90 *common*, and each labels *rare* 5 rows the other labels *common*. *Then:* *p*o = 0.90, *p*e = 0.95 × 0.95 + 0.05 × 0.05 = 0.905, and κ = (0.90 − 0.905) ÷ 0.095 ≈ −0.05. In their words, the test of reliability then is "the ability to agree on the rare categories", which the per-label rows show. **When one rater used a single label** (all my verdicts are `same fact`, say), *p*e = *p*o and κ = 0 whatever the other did: the report says so, and the raw agreement and the disagreements are what counts.

For the facts task the report also says, of the rows both call `left out`, in how many the judge names my rule.

## What it writes

- `annotations/second_judge.csv`, in Git: one row per judged row and model, with the columns `task` (`facts` or `partial pairs`), `id`, `title`, `candidate_triple` and `source_text` (facts), `ground_truth_triple` and `extracted_triple` (partial pairs), `model`, `label`, `rule` (facts: "<section>, rule <n>") and `reason`. My labels stay in their own files. A rerun replaces the rows of the tasks it judged for its model and keeps every other row.
- `outputs/intermediate_results/second_judge/second_judge_details.json`: the run's settings and what was sent, and every judged row with my label and the judge's.

## What it can't see

- **One judge, one answer each:** a model doesn't answer the same way twice. Repeats (`--repeat 2`, `--repeat 3`) show how much its labels vary on their own.
- **Agreement is not correctness:** two raters can agree on a wrong label, and a disagreement says only that one of the two is wrong. The disagreements are for me to read again against the record and the rules.
- **Its own leanings:** the judge comes from a third maker, which keeps it independent of the two models whose output is judged, not free of leanings of its own.
- **Only the rows with my label:** a row decided after this run isn't in its agreement until the next run.
