# Why "approximately": reasons every metric shares

Part of [Evaluation metrics](../metrics.md), which explains the notation and lists every metric.

Every metric is computed on the evaluated [records](../../docs/terminology.md#1-records-and-their-text) only (the [fair sample](../../docs/terminology.md#4-ground-truth-and-samples) of finished, extracted records). Reading it for the whole catalog assumes two things:

- the evaluated records are a random sample of the catalog (only the fair sample is evaluated);
- the pipeline wasn't adjusted to these records (true of the [held-out part](../../docs/terminology.md#7-evaluating-extraction-step-070) until it is looked at).

Even then, every metric is approximate for the whole catalog, for the five reasons below. Each has the same parts: what it means, and how the [report](../../docs/terminology.md#8-the-pipeline) checks or limits it. A metric with reasons of its own lists them in its own section, under *Assumes and can't see*. Sources for all five: [Why "approximately": sources](#sources).

## Sampling error

**What it means.** Another sample of the same size would give a somewhat different value.

**How the [report](../../docs/terminology.md#8-the-pipeline) checks or limits it: the margin of error.** A range around each metric's value that says how much the value could change with another sample of the same size. Every metric gets one, except the describes baseline and the describes per-entity-class average. Example: [Sampling error: example](#example).

- **How it is computed**, by the bootstrap, with fixed numbers in `070_evaluate/070_evaluate_helpers/stats.py`:
  1. Redraw the evaluated [records](../../docs/terminology.md#1-records-and-their-text): within each [stratum](../../docs/terminology.md#4-ground-truth-and-samples), draw at random, with repeats, as many records as the stratum has. Whole records are drawn, never single [classed triples](../../docs/terminology.md#2-triples).
  2. Compute the metric on the redrawn records, adding up their counts as on the real ones. A redraw where the metric is undefined (e.g. no [extracted triples](../../docs/terminology.md#6-extracting-with-a-schema-step-060)) is skipped.
  3. Repeat 1,000 times (`REDRAWS`), from a fixed seed (`SEED = 70`), so a rerun gives the same range.
  4. The range is the middle 95% of the 1,000 values: from the 2.5th to the 97.5th percentile.

  With fewer than 20 evaluated records (`MIN_RECORDS`), no range is given.
- **How to read it.** Let *m* be the value of one metric, and *L* to *H* its range. The report says "for the whole catalog, *m* is likely between *L* and *H*".
  - A narrow range: another sample of the same size would give nearly the same value. A wide one: it could give quite a different value.
  - More evaluated records give a narrower range.
  - Two values whose ranges overlap a lot may differ only by chance.
- **What it assumes.** No distribution for the metric (e.g. not a normal one), but the following. The report checks each, in its section *The margin of error's assumptions, checked*, and warns when one doesn't hold.

  | Assumption | Why it matters | How the report checks it |
  |---|---|---|
  | The evaluated records are a random sample of the catalog | The redraws stand in for other samples of the catalog. | Only the [fair sample](../../docs/terminology.md#4-ground-truth-and-samples) is evaluated (by design). |
  | Whole records vary, independently of each other | A record's extracted triples come from one [text](../../docs/terminology.md#1-records-and-their-text) and one [model call](../../docs/terminology.md#8-the-pipeline), so they succeed or fail together; redrawing single classed triples would make the range too narrow. | Records are redrawn whole (by design). |
  | Enough records | With very few, the range is itself unreliable, usually too narrow. | No range below 20 evaluated records (a rule of thumb; no source found gives a number). |
  | Every stratum adds spread | A stratum with only 1 evaluated record puts that record in every redraw, so the range comes out too narrow. | Lists the strata with only 1 evaluated record. |
  | The range isn't at 0% or 100% | There, a percentile range is too narrow. | Lists the metrics whose range reaches 0% or 100%. |
  | No one record dominates | A record with most of the classed triples sways every redraw it's in. | Gives the largest record's proportion of the extracted triples and of the [ground truth triples](../../docs/terminology.md#4-ground-truth-and-samples), for reading (no established threshold). |
  | A small proportion of the catalog is evaluated | Redrawing with repeats treats the catalog as endless; for a large proportion, the range comes out somewhat too wide. | Gives the proportion of the catalog evaluated; holds below 5%. |
- **What it can't see.** Only sampling error: the other four reasons can move the whole catalog's value outside the range.

## The sample's mix of maintainers

**What it means.** The [pool](../../docs/terminology.md#4-ground-truth-and-samples) was drawn stratified by [maintainer](../../docs/terminology.md#1-records-and-their-text), and only its first [finished records](../../docs/terminology.md#4-ground-truth-and-samples) are evaluated. If their mix of maintainers differs from the catalog's, the value leans toward the over-represented maintainers.

**How the [report](../../docs/terminology.md#8-the-pipeline) checks or limits it.**
- The pool matches the catalog's mix of maintainers: it was drawn with proportional allocation (`annotations/ground_truth_candidates.json`).
- The report's [strata](../../docs/terminology.md#4-ground-truth-and-samples) table compares, per stratum, the proportion of the evaluated [records](../../docs/terminology.md#1-records-and-their-text) with the proportion of the pool.
- From 20 evaluated records on, it warns when the two differ by more than 10 percentage points (`SHARE_GAP`). The 10 points is a rule of thumb, with no source found.

## Small-sample bias of a ratio

**What it means.** Each metric is a ratio of two counts that both vary from sample to sample. Such a ratio is slightly biased in small samples: averaged over many samples, it isn't exactly the whole catalog's value.

**How the [report](../../docs/terminology.md#8-the-pipeline) checks or limits it.** It doesn't check it. The bias shrinks as the sample grows, faster than the sampling error does, so it is small next to the [margin of error](#sampling-error).

## Tuning on the evaluated records

**What it means.** Changes made after looking at the [tuning part](../../docs/terminology.md#7-evaluating-extraction-step-070)'s numbers (to the [schema](../../docs/terminology.md#3-schemas), the [schema additions](../../docs/terminology.md#3-schemas), or the prompts) fit those [records](../../docs/terminology.md#1-records-and-their-text), so the tuning part's numbers come out higher than the whole catalog's would.

**How the [report](../../docs/terminology.md#8-the-pipeline) checks or limits it.** The [held-out part](../../docs/terminology.md#7-evaluating-extraction-step-070): its numbers are shown only with the [setting](../../docs/terminology.md#8-the-pipeline) `evaluate_held_out`, meant for the end, and each look is logged in `annotations/held_out_looks.csv`.

## An imperfect ground truth

**What it means.** "Correct" means having a partner in the [ground truth](../../docs/terminology.md#4-ground-truth-and-samples). A [fact](../../docs/terminology.md#2-triples) missing from it, or a mistake in it, shifts the value the same way in every sample.

**How the [report](../../docs/terminology.md#8-the-pipeline) checks or limits it.** It doesn't: nothing in the numbers shows it. Only care in annotating limits it (see `050_annotate/050_annotate.md`).

## Example

40 evaluated [records](../../docs/terminology.md#1-records-and-their-text), in two [strata](../../docs/terminology.md#4-ground-truth-and-samples) of 30 and 10, with exact [precision](precision.md) 70%. Each redraw takes 30 records at random, with repeats, from the first stratum's 30, and 10 from the second's 10, and computes exact precision on them. Of the 1,000 values, the middle 95% run from 61% to 78%. The [report](../../docs/terminology.md#8-the-pipeline) says: "for the whole catalog, exact precision is likely between 61% and 78%".

## Sources

- Sampling error, the [margin of error](#sampling-error):
  - The [bootstrap](#sampling-error), and its percentile range: Efron & Tibshirani, *An Introduction to the Bootstrap* (1993).
  - Drawing whole [records](../../docs/terminology.md#1-records-and-their-text) rather than single [classed triples](../../docs/terminology.md#2-triples), since a record's [extracted triples](../../docs/terminology.md#6-extracting-with-a-schema-step-060) succeed or fail together, is the cluster (or block) bootstrap; drawing within each [stratum](../../docs/terminology.md#4-ground-truth-and-samples) is the stratified bootstrap: Davison & Hinkley, *Bootstrap Methods and their Application* (1997).
  - The threshold of 20 records: a rule of thumb, with no source found.
  - Below 5% of the catalog evaluated, drawing with repeats from a finite catalog is negligible: Cochran, *Sampling Techniques* (1977), chapter 2.
  - A stratum with only 1 evaluated record gives no estimate of its spread: the single-unit stratum of survey sampling (Cochran, 1977).
  - A percentile range is too narrow near 0% or 100%: Efron & Tibshirani (1993).
- The sample's mix of [maintainers](../../docs/terminology.md#1-records-and-their-text): stratified sampling with proportional allocation, Cochran (1977), chapter 5. The 10-point warning: a rule of thumb, with no source found.
- Small-sample bias of a ratio: the ratio estimator, biased by an amount that shrinks faster than its sampling error as the sample grows, Cochran (1977), chapter 6.
- Tuning on the evaluated records: a test set used to choose between versions no longer gives an unbiased estimate; a part kept unseen until the end does. Hastie, Tibshirani & Friedman, *The Elements of Statistical Learning* (2nd ed., 2009), section 7.2.
- An imperfect [ground truth](../../docs/terminology.md#4-ground-truth-and-samples): a reference set missing true facts makes evaluation "overly pessimistic" for methods that extract them, Zhang & Soh, *Extract, Define, Canonicalize* (2024), [paper](https://arxiv.org/abs/2404.03868).
