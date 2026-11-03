# Why "approximately": reasons every metric shares

Part of [Evaluation metrics](../metrics.md), which explains the notation and lists every metric.

Every metric is computed on the evaluated [records](../../docs/terminology.md#1-records-and-their-text) only (the [fair sample](../../docs/terminology.md#4-ground-truth-and-samples) of finished, extracted records). Reading it for the whole catalog assumes two things:

- the evaluated records are a random sample of the catalog (only the fair sample is evaluated: for each part, the first records of the part in pool order, with none of the part skipped; the pool's order restricted to one part is still random, so each part is a random sample on its own);
- the pipeline wasn't adjusted to these records (true of the [held-out part](../../docs/terminology.md#7-evaluating-extraction-step-070) until it is looked at).

Even then, every metric is approximate for the whole catalog, for the five reasons below. Each has the same parts: its meaning, and how the [report](../../docs/terminology.md#8-the-pipeline) checks or limits it. A metric with reasons of its own lists them in its own section, under *Assumes and can't see*. Sources for all five: [Why "approximately": sources](#sources).

## Sampling error

**Meaning.** Another sample of the same size would give a somewhat different value.

**How the [report](../../docs/terminology.md#8-the-pipeline) checks or limits it: the margin of error.** A range around each metric's value that says how much the value could change with another sample of the same size. Every metric gets one, except the [describes baseline](describes.md) and the [describes per-entity-class average](describes.md). Example: [Sampling error: example](#example).

- **How it is computed**, by the clustered Wilson interval (`clustered_wilson` in `070_evaluate/070_evaluate_helpers/stats.py`), with no redraws and no seed. Every metric is a ratio A ÷ B of sums over the evaluated [records](../../docs/terminology.md#1-records-and-their-text) (precision: pairs ÷ counted occurrences; recall: pairs ÷ [ground truth triples](../../docs/terminology.md#4-ground-truth-and-samples); F1: 2 × pairs ÷ (counted occurrences + ground truth triples); and so on: `RATIO_PARTS` in `stats.py`, the one home of every formula, from which the value is computed too). Record *r* gives *a*<sub>r</sub> and *b*<sub>r</sub>, with *a*<sub>r</sub> ≤ *b*<sub>r</sub>; A = Σ *a*<sub>r</sub>, B = Σ *b*<sub>r</sub>, and *n* is the number of records with *b*<sub>r</sub> > 0. That is a proportion estimated from a cluster sample, the records being the clusters:
  1. B = 0: no value. Otherwise *p̂* = A ÷ B.
  2. *n* = 1: the value, no range.
  3. The variance of *p̂* over the records (the linearized variance of a ratio, with the small-sample factor *n* ÷ (*n* − 1)): *v̂* = *n* ÷ (*n* − 1) × Σ (*a*<sub>r</sub> − *p̂* × *b*<sub>r</sub>)² ÷ B².
  4. The **design effect**, how many times that variance is the one B independent [triples](../../docs/terminology.md#2-triples) would give: deff = *v̂* ÷ (*p̂*(1 − *p̂*) ÷ B), at least 1 (a value below 1 would claim more information than B independent triples). The **effective sample size** is *n*<sub>eff</sub> = B ÷ deff, kept between *n* and B. When *p̂* is 0% or 100%, *v̂* is 0 and the design effect undefined: then every record counts as one trial, *n*<sub>eff</sub> = *n* (our choice, the conservative side: 3 records of 100 correct occurrences each give a lower bound near 44%, not 99%).
  5. The degrees-of-freedom adjustment: *n*′ = *n*<sub>eff</sub> × (*z* ÷ *t*<sub>0.975, *n* − 1</sub>)², *z* = 1.96 (`Z`) and *t* the Student t quantile (`t_quantile`, in plain Python).
  6. The Wilson score interval with *n*′: centre = (*p̂* + *z*² ÷ (2*n*′)) ÷ (1 + *z*² ÷ *n*′); half-width = *z* × √(*p̂*(1 − *p̂*) ÷ *n*′ + *z*² ÷ (4*n*′²)) ÷ (1 + *z*² ÷ *n*′); the range is centre ± half-width, kept within 0% and 100%.

  The same formula gives the range of the part, of each [stratum](../../docs/terminology.md#4-ground-truth-and-samples), and of each row per predicate and per [entity class](../../docs/terminology.md#3-schemas), from 2 records on. Below 10 records (`FEW_RECORDS`, our choice) each range comes with a caveat: the design effect is itself estimated from those few records, so the range may still be too narrow; read it as a rough width, not a bound (a row of a table: marked *(few records)*).

  **Repeats** (several runs of one recipe, `py helpers/compare_runs.py`, *Pooled over the repeats*): the record stays the cluster, never record × repeat; its parts are its means over the K runs, ā<sub>r</sub> and b̄<sub>r</sub>, and the range is the one above on those. The value is then the same as pooling all the counts, and the range narrows only as much as the model's own variation the repeats average away. Step 070 itself evaluates one run.

  **Measured coverage.** On synthetic records (each with 1 + Poisson(6) occurrences, and a success rate of its own drawn from Beta(2.8, 1.2): mean 70%, intracluster correlation 0.2), 3,000 samples of each size, seeded, the 95% range held the true 70% in these proportions of the samples: 5 records: 97.3%; 10: 95.3%; 20: 94.3%; 28: 95.1%; 40: 94.9% (code: `tests/test_evaluate_intervals.py`, which prints them). Measured with these settings only: records whose triples move together more strongly, or whose sizes vary more, may cover less.
- **How to read it.** Let *m* be the value of one metric, and *L* to *H* its range. The report says "for the whole catalog, *m* is likely between *L* and *H* (a 95% interval over these *N* records' B triples, worth *n*′ independent ones once the records' clustering is counted)".
  - A narrow range: another sample of the same size would give nearly the same value. A wide one: it could give quite a different value.
  - More evaluated records give a narrower range; so do records whose triples move together less (a smaller design effect).
  - Two values whose ranges overlap a lot may differ only by chance.
- **Assumptions.** No distribution for the metric (e.g. not a normal one), but the following. The report checks each, in its section *The margin of error's assumptions, checked*, and warns when one doesn't hold.

  | Assumption | Why it matters | How the report checks it |
  |---|---|---|
  | The evaluated records are a random sample of the catalog | The range speaks of other samples of the catalog. | Only the [fair sample](../../docs/terminology.md#4-ground-truth-and-samples) is evaluated, for each part separately (by design): a part's order is the shuffled pool's order restricted to it, so its first records are random. |
  | Whole records vary, independently of each other | A record's [extracted triples](../../docs/terminology.md#6-extracting-with-a-schema-step-060) come from one [text](../../docs/terminology.md#1-records-and-their-text) and one [model call](../../docs/terminology.md#8-the-pipeline), so they succeed or fail together; a variance taken triple by triple would make the range too narrow. | Each record is one cluster (by design). The records are taken from all strata together, as they were sampled: the evaluated records of a part are its first records of the [pool](../../docs/terminology.md#4-ground-truth-and-samples), so how many come from each stratum is itself random. |
  | The records' clustering is estimated from the records themselves | With few records, the design effect is uncertain, so the range may be too narrow. | The caveat below 10 records, and the measured coverage above; the report gives the lowest and highest design effect across the metrics, for reading. |
  | A ratio treated as a proportion | The Wilson interval is for a proportion; F1 and the accuracies are ratios of record sums, each record's numerator at most its denominator. | By design (reasonable practice: the linearized variance holds for any ratio of sums). |
  | No one record dominates | A record with most of the [classed triples](../../docs/terminology.md#2-triples) sways the variance. | Gives the largest record's proportion of the occurrences and of the ground truth triples, for reading (no established threshold). |
  | A small proportion of the catalog is evaluated | The formula treats the catalog as endless; for a large proportion, the range comes out somewhat too wide. | Gives the proportion of the catalog evaluated; holds below 5%. |
- **Limits.** Only sampling error: the other four reasons can move the whole catalog's value outside the range.

## The sample's mix of strata

**Meaning.** The [pool](../../docs/terminology.md#4-ground-truth-and-samples) was drawn stratified by [maintainer](../../docs/terminology.md#1-records-and-their-text), and only the first [finished records](../../docs/terminology.md#4-ground-truth-and-samples) of each part are evaluated. If their mix of strata differs from the catalog's, the value leans toward the over-represented maintainers.

**How the [report](../../docs/terminology.md#8-the-pipeline) checks or limits it.**
- The pool matches the catalog's mix of strata: it was drawn with proportional allocation (`annotations/ground_truth_candidates.json`).
- The report's [strata](../../docs/terminology.md#4-ground-truth-and-samples) table compares, per stratum, the proportion of the evaluated [records](../../docs/terminology.md#1-records-and-their-text) with the proportion of the pool.
- From 10 evaluated records on, it warns when the two differ by more than 10 percentage points (`SHARE_GAP`). The 10 points is a rule of thumb, with no source found.
- The [margin of error](#sampling-error) already includes this chance: it takes the records from all strata together, so the mix of strata varies in it as it does from sample to sample.

## Small-sample bias of a ratio

**Meaning.** Each metric is a ratio of two counts that both vary from sample to sample. Such a ratio is slightly biased in small samples: averaged over many samples, it isn't exactly the whole catalog's value.

**How the [report](../../docs/terminology.md#8-the-pipeline) checks or limits it.** It doesn't check it. The bias shrinks as the sample grows, faster than the sampling error does, so it is small next to the [margin of error](#sampling-error).

## Tuning on the evaluated records

**Meaning.** Changes made after looking at the [tuning part](../../docs/terminology.md#7-evaluating-extraction-step-070)'s numbers (whatever was changed: the [schema](../../docs/terminology.md#3-schemas), the [schema additions](../../docs/terminology.md#3-schemas), the prompts, the [translation table](../../docs/terminology.md#7-evaluating-extraction-step-070)'s rows, fixes to the [ground truth](../../docs/terminology.md#4-ground-truth-and-samples) of tuning [records](../../docs/terminology.md#1-records-and-their-text), the partial-pair verdicts, a setting, or the choice of model) fit those records, so the tuning part's numbers come out higher than the whole catalog's would.

**How the [report](../../docs/terminology.md#8-the-pipeline) checks or limits it.** The [held-out part](../../docs/terminology.md#7-evaluating-extraction-step-070): its numbers are shown only with the [setting](../../docs/terminology.md#8-the-pipeline) `evaluate_held_out`, meant for the end, and each look is logged in `annotations/held_out_looks.csv`.

## An imperfect ground truth

**Meaning.** "Correct" means having a partner in the [ground truth](../../docs/terminology.md#4-ground-truth-and-samples). A [fact](../../docs/terminology.md#2-triples) missing from it, or a mistake in it, shifts the value the same way in every sample.

**How the [report](../../docs/terminology.md#8-the-pipeline) checks or limits it.** It doesn't: nothing in the numbers shows it. Only care in annotating limits it (see `050_annotate/050_annotate.md`).

## Example

*Suppose:* 20 evaluated [records](../../docs/terminology.md#1-records-and-their-text), each with 10 occurrences, 7 of them correct: exact [precision](precision.md) 70%. *Then:* every record is at 70%, so the variance over the records is 0, the design effect is floored to 1, *n*<sub>eff</sub> = 200, *n*′ = 200 × (1.96 ÷ 2.093)² = 175.4, and the Wilson range is 63% to 76%. *Suppose instead:* the same totals, but 10 records with 10 of 10 correct and 10 with 4 of 10. *Then:* the design effect is 4.5, *n*′ = 38.9, and the range is 54% to 82%: the records' [triples](../../docs/terminology.md#2-triples) move together, so the 200 occurrences are worth about 39 independent ones. The [report](../../docs/terminology.md#8-the-pipeline) says, for the first: "for the whole catalog, exact precision is likely between 63% and 76%".

## Sources

- Sampling error, the [margin of error](#sampling-error):
  - The Wilson score interval: Wilson, "Probable Inference, the Law of Succession, and Statistical Inference", *Journal of the American Statistical Association* 22 (1927). Recommended for small samples: Brown, Cai & DasGupta, "Interval Estimation for a Binomial Proportion", *Statistical Science* 16(2), 2001, [paper](https://doi.org/10.1214/ss/1009213286), whose abstract recommends "the Wilson interval or the equal-tailed Jeffreys prior interval for small n" (checked on 2026-11-01 through the abstract as a search index shows it, and a paper quoting it, [PMC2706447](https://pmc.ncbi.nlm.nih.gov/articles/PMC2706447/): "the Wilson or the Jeffreys interval for small sample sizes (n≤40)"; the publisher's page could not be fetched).
  - With records as clusters, the effective sample size and the degrees-of-freedom adjustment: Korn & Graubard, "Confidence Intervals for Proportions with Small Expected Number of Positive Counts Estimated from Survey Data", *Survey Methodology* 24 (1998); Dean & Pagano, "Evaluating confidence interval methods for binomial proportions in clustered surveys", *Journal of Survey Statistics and Methodology* (2015), who "adjusted the effective sample size by multiplying it by (z/t_d)²"; Franco, Little, Louis & Slud, "Comparative Study of Confidence Intervals for Proportions in Complex Sample Surveys", *Journal of Survey Statistics and Methodology* 7(3), 2019, [paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC6690503/): "We recommend intervals of the Wilson or Bayes uniform prior form", computed with the effective sample size "without rounding"; and "all intervals undercover when there is clustering". The linearized variance of a ratio of sums: Cochran, *Sampling Techniques* (1977), chapter 6 (not verified in the book).
  - Why not the bootstrap 070 used until 2026-11-01 (a percentile range of 1,000 redraws of whole records, from 20 records on): "the common bootstrap percentile interval badly under-covers in small samples" (Hesterberg, "What Teachers Should Know About the Bootstrap: Resampling in the Undergraduate Statistics Curriculum", *The American Statistician*, 2015, [arXiv:1411.5279](https://arxiv.org/abs/1411.5279)); for evaluations of language models on small sets, intervals of the normal approximation and the bootstrap "perform very poorly, usually dramatically underestimating uncertainty", and "We would, therefore, recommend using WS [Wilson score] or Bayesian intervals in practice" (Bowyer, Aitchison & Ivanova, "Position: Don't Use the CLT in LLM Evals With Fewer Than a Few Hundred Datapoints", ICML 2025, [arXiv:2503.01747](https://arxiv.org/abs/2503.01747)). That the questions' clustering, not their number, sets the variance, and that repeats are averaged per question rather than pooled ("computing a pooled standard error across all KN answers will be inconsistent"): Miller, "Adding Error Bars to Evals: A Statistical Approach to Language Model Evaluations", 2024, [arXiv:2411.00640](https://arxiv.org/abs/2411.00640). The fallback if the measured coverage fell short: Bowyer et al.'s hierarchical Beta-Binomial interval.
  - The caveat below 10 records: our choice; the nearest published line, reported in the few-clusters literature, is that cluster-robust procedures "perform poorly with fewer than eleven clusters" (MacKinnon & Webb, a working paper, found by search and not read in full).
  - The paired comparison of two runs (`py helpers/compare_runs.py`) keeps a bootstrap, since a difference of two ratios is not a proportion: its expanded percentile range is Hesterberg's (2015, sections 1.1 and 5.3), with 10,000 redraws (section 3.6: "We suggest r = 10000 for routine use").
  - Below 5% of the catalog evaluated, an endless catalog is a negligible simplification: Cochran, *Sampling Techniques* (1977), chapter 2 (not verified in the book; a secondary source gives the same rule, checked on 2026-10-31).
- The sample's mix of strata: stratified sampling with proportional allocation, which "gives a self-weighting sample", so the overall numbers need no weighting: Cochran (1977), section 5.3, p. 91 (checked in the book on 2026-10-31). The 10-point warning: a rule of thumb, with no source found; the nearest convention, for comparing two groups, is a standardized difference of 0.1, which "some researchers have proposed" as meaningful imbalance (Austin, "Balance diagnostics for comparing the distribution of baseline covariates between treatment groups in propensity-score matched samples", *Statistics in Medicine*, 2009, [paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC3472075/)); ours is in raw percentage points.
- Small-sample bias of a ratio: the ratio estimator, biased by an amount that shrinks faster than its sampling error as the sample grows, Cochran (1977), chapter 6 (not verified in the book).
- Tuning on the evaluated records: a test set used to choose between versions no longer gives an unbiased estimate; a part kept unseen until the end does. Hastie, Tibshirani & Friedman, *The Elements of Statistical Learning* (2nd ed., 2009), section 7.2.
- An imperfect [ground truth](../../docs/terminology.md#4-ground-truth-and-samples): a reference set missing true facts makes evaluation "overly pessimistic" for methods that extract them, Zhang & Soh, *Extract, Define, Canonicalize* (2024), [paper](https://arxiv.org/abs/2404.03868).
