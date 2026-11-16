"""
write_docs · Writes the four pages of docs/analysis/ from the numbers the other scripts of helpers/analysis/ computed.

Produces: docs/analysis/rescore_2026-11-13.md, recall_by_rule.md, scalability.md and by_record_kind.md, each replaced
through tests/doc_guard.py (delete, then create), so the doc guard's ledger records them.

    py helpers/analysis/write_docs.py        after rescore_runs.py, prompt_sizes.py, analyses.py, tables.py, scalability.py

No model call: it reads outputs/analysis/results.json, tables.json, scalability.json and runs.json only. The prose of
the pages is in this file; the numbers and tables are filled in from those files.
"""
import re
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "outputs" / "analysis"                                         # the working folder (not in Git)
sys.path.insert(0, str(ROOT / "tests"))
from doc_guard import create as _create, edit_block                          # noqa: E402
sys.path.insert(0, str(ROOT))
from common.files import read_json, read_text                                 # noqa: E402


def create(rel, text):
    """The page as one recorded edit of its last version (a page already in Git can't be created again), or created."""
    path = ROOT / rel
    if not path.exists():
        _create(rel, text)
    elif read_text(path) != text:
        edit_block(rel, read_text(path), text)

r = read_json(HERE / "results.json")
t = read_json(HERE / "tables.json")
s = read_json(HERE / "scalability.json")
made = read_json(HERE / "runs.json")
ids = [made[n] for n in ("1816", "1816-2", "1816-3", "1817", "1817-2", "1817-3")]
ids_text = (", ".join(f"`{i}`" for i in ids[:3]) + " (induced schema) and " + ", ".join(f"`{i}`" for i in ids[3:])
            + " (ground truth schema)")
SCRATCH = "helpers/analysis"
LABEL = "Preliminary, computed on 2026-11-13 by scripts that Claude Fable 5.2 wrote and Claude Opus 5.5 ran, still to be reviewed by a person."
p1 = lambda v: f"{100 * v:.1f}"
old, new = r["old"], r["new"]

# ------------------------------------------------------------------ 1. re-score
ROWS = [("partial: f1", "Partial F1", "2 × (exact pairs + partial pairs) ÷ (counted occurrences + ground truth triples)"),
        ("partial: precision", "Partial precision", "(exact pairs + partial pairs) ÷ counted occurrences"),
        ("partial: recall", "Partial recall", "(exact pairs + partial pairs) ÷ ground truth triples"),
        ("exact: f1", "Exact F1", "2 × exact pairs ÷ (counted occurrences + ground truth triples)"),
        ("recall upper bound", "Recall upper bound", "ground truth triples within reach ÷ ground truth triples"),
        ("partial: recall_within_reach", "Partial recall within reach", "(exact pairs + partial pairs) ÷ ground truth triples within reach"),
        ("exact: recall_within_reach", "Exact recall within reach", "exact pairs ÷ ground truth triples within reach"),
        ("schema fit", "Schema fit", "(occurrences − untranslatable extracted triples) ÷ occurrences")]


def cell(n, k):
    v, lo, hi = n["pooled"][k]
    reps = n["repeats"][k]
    return f"{p1(v)}% ({p1(lo)} to {p1(hi)}) | {p1(min(reps))} to {p1(max(reps))}"


def refcell(n, k):
    reps = n["repeats_reference"][k]
    return f"{p1(n['pooled_reference'][k][0])}% | {p1(min(reps))} to {p1(max(reps))}"


def triple(x):
    return f"\"{x[0]}\" {x[1]} \"{x[2]}\""


table = "\n".join(f"| {label} | {formula} | {cell(old, k)} | {cell(new, k)} | {100 * (new['pooled'][k][0] - old['pooled'][k][0]):+.1f} |"
                  for k, label, formula in ROWS)
reftable = "\n".join(f"| {label} | {refcell(old, k)} | {refcell(new, k)} |" for k, label, _ in ROWS[:4])
reps = "\n".join(f"| Partial F1, repeat {i + 1} | {p1(old['repeats']['partial: f1'][i])}% | {p1(new['repeats']['partial: f1'][i])}% |" for i in range(3))
titles = {e_id: e["title"] for e_id, e in r["by_kind"]["records"].items()}
names = {"1816": "induced schema, repeat 1", "1816-2": "induced schema, repeat 2", "1816-3": "induced schema, repeat 3",
         "1817": "ground truth schema, repeat 1", "1817-2": "ground truth schema, repeat 2", "1817-3": "ground truth schema, repeat 3"}
unj = "\n".join(f"| {i} | {titles[u['record_id']]} | {triple(u['ground_truth'])} | {triple(u['translated'])} | {'; '.join(names[x] for x in u['runs'])} |"
                for i, u in enumerate(r["unjudged"], 1))
w = r["what_if"]
ui = sum(sum(v.values()) for k, v in r["unjudged_per_run"].items() if k.startswith("1816"))
ur = sum(sum(v.values()) for k, v in r["unjudged_per_run"].items() if k.startswith("1817"))
a, b = w["induced, as scored"], w["induced, unjudged pairs taken off"]
c, d = w["ground truth schema, as scored"], w["ground truth schema, unjudged pairs taken off"]
rescore = f"""# The six reported runs scored again against the ground truth of 2026-11-13

{LABEL}

## What was done

The NASA TM reports six runs: three repeats of extraction (step 060) with the induced schema and three with the ground truth schema, each evaluated by step 070. `docs/reported_numbers.json` names them and pins their numbers to the annotations of commit `5b958ce`. The ground truth changed on 2026-11-12 and 2026-11-13, and this page scores the same six extractions against the ground truth as it was in the working folder after the last of those changes (read on 2026-11-13 at 14:55 local time). No model was called. `docs/reported_numbers.json` is unchanged.

The six extractions are the files that step 060 kept in `outputs/intermediate_results/060_extract/previous_runs/060_extract_2026-11-05_1816`, `_1816-2`, `_1816-3` (induced schema) and `_1817`, `_1817-2`, `_1817-3` (ground truth schema). Each file has the sha256 that its run's manifest records. `py helpers/analysis/rescore_runs.py` checks those hashes and has step 070 score each one with this command, with the environment variable `KG_NO_MODEL_CALLS` set, which stops any model call in code:

```
py 070_evaluate/run.py --suggest false --confirm_paid_calls false --extracted_triples <folder>/extracted_triples.csv --extracted_triples_details <folder>/extracted_triples_details.json --schema_used <folder>/schema_used.json
```

The command names three of step 070's four inputs from step 060. The fourth, `extracted_triples_removed.csv`, was read from step 060's live folder. That file has the sha256 that each of the six runs' manifests records for it (checked on 2026-11-16), so every number of this page comes from the six runs' own files. Since 2026-11-16 the script names each run of step 060 to step 070 (`--extraction_run`), which reads all four of its files, each found by the sha256 that the run's manifest records.

`py helpers/reproduce_results.py` could not be used, because it runs step 060 again from its answer cache, and the extraction rules in the prompt changed on 2026-11-12, so the cached answers no longer match the prompt. The translation table is that of the working folder, unchanged since commit `5b958ce`, and the verdicts on partial pairs are those of the working folder, with the six added on 2026-11-12 (*Partial pairs*, below). The new 070 runs are {ids_text}. The numbers below come from their files in `outputs/intermediate_results/070_evaluate/evaluations/`, computed with the functions of `helpers/compare_runs.py` (`pooled`, `spread`, `sign_flip`) by the script `{SCRATCH}/analyses.py`. The same script applied to the six reported runs returns every number of `docs/reported_numbers.json`. To make the four pages of this folder again, run the scripts of `helpers/analysis/` in this order, none of which calls a model: `rescore_runs.py`, `prompt_sizes.py`, `analyses.py`, `tables.py`, `scalability.py`, `write_docs.py`.

## What changed in the ground truth

The changes are those recorded in `docs/improvements.md`, section *050_annotate*, in the entries dated 2026-11-12 and 2026-11-13. All of them were made by a model (Claude Fable 5.2, and Claude Opus 5.5 for the last stage) and are still to be reviewed by a person. The 20 finished records had 416 ground truth triples at commit `5b958ce` and have 432 now. The count moved in seven stages, of which the fifth and the seventh changed triples without changing the count.

1. A fact counts wherever its words are, even inside a name (416 to 431). Rule 2 gained the part *A fact inside a name*, and 15 ground truth triples were added, for example "radiance data" HAS_MEASUREMENTS_OF "radiance". None was changed or deleted.
2. Fixes from two audits of the ground truth against the guidelines (431 to 428). One triple was deleted because its name does not say how two things are related, six instances took the title's capitals under rule 23, and the column `rules` was corrected.
3. An entity class may come from a public reference (428 to 431). Rule 1 now allows an official NASA list and then Wikidata as the source of a name's entity class, and three triples were added for names that had been left out as unexplained.
4. Rules made clear after the two audits (431 to 430). Nine points were decided, among them lists joined by "/" or "+" (rule 22), a processing step on the record's dataset's own values (rule 24), an amount per member (rule 9, one triple deleted), and source texts cut to the shortest passage (rule 17).
5. Third round of rule fixes (430, no triple added or deleted). Ten points were decided after two more audits, among them which fact a word inside a name states (rule 2), source texts under rule 17, and a processing step whose input is the record's dataset's own values (rule 24). Ground truth triples were reworded, and the values of the column `rules` changed.
6. Fourth round of rule fixes (430 to 432). Fifteen points were decided after a third pair of audits. Six ground truth triples were added and four were deleted. For example, "SDSS Quasar Catalog" HAS_TARGET "Quasar" is a ground truth triple again.
7. Fifth round of rule fixes (432, one triple added and one deleted). Nine points were decided after a fourth pair of audits. "COMET ESCORT 3" HAS_TARGET "67P/Churyumov-Gerasimenko 1 (1969 R1)" was added, as the other mission phases of the record have their target, and "2XMMi-DR3" FROM_PLATFORM "XMM-Newton" was deleted because the record states it only by combining two passages. Source texts of qualifier facts were cut to the qualifier's words, and the values of the column `rules` were made uniform.

Each ground truth row also has a column `rules` since 2026-11-11, which lists the rules of `annotations/guidelines.md` that the triple uses. Step 070 does not read it.

## The numbers, before and after

The table gives each number that `docs/reported_numbers.json` holds for the induced schema. Each value pools the three repeats over the 20 evaluated records of the tuning part, with its 95% range by the clustered Wilson interval in parentheses, as `helpers/compare_runs.md` (*Pooled over the repeats*) defines it. The column after it gives the lowest and the highest of the three repeats. Counted occurrences are the occurrences less the untranslatable extracted triples and less those paired with a fact that waits on an expert (`070_evaluate/metrics/precision.md`).

| Number | Formula | Reported (annotations of `5b958ce`), pooled | Reported, repeats | Now (2026-11-13), pooled | Now, repeats | Change in points |
|---|---|---|---|---|---|---:|
{table}

| Number | Reported | Now |
|---|---:|---:|
{reps}
| Partial F1 with the ground truth schema (decision rule) | {p1(old['decision']['f1_reference'])}% | {p1(new['decision']['f1_reference'])}% |
| *D* = partial F1 with the ground truth schema − partial F1 with the induced schema, in points | {p1(old['decision']['D'])} | {p1(new['decision']['D'])} |
| *p* of the paired sign-flip test over the 20 records | {old['decision']['p']:.4g} | {new['decision']['p']:.4g} |
| Ground truth triples of the 20 evaluated records | {old['gt_triples'][0]} | {new['gt_triples'][0]} |

The three runs with the ground truth schema, pooled over their repeats, with the lowest and highest repeat:

| Number | Reported, pooled | Reported, repeats | Now, pooled | Now, repeats |
|---|---|---|---|---|
{reftable}

Reading: with the induced schema, partial F1 moves from {p1(old['pooled']['partial: f1'][0])}% to {p1(new['pooled']['partial: f1'][0])}%, a change much smaller than the width of its 95% range ({p1(new['pooled']['partial: f1'][1])} to {p1(new['pooled']['partial: f1'][2])}). Precision is almost unchanged and recall falls by {100 * (old['pooled']['partial: recall'][0] - new['pooled']['partial: recall'][0]):.1f} points. The recall upper bound rises from {p1(old['pooled']['recall upper bound'][0])}% to {p1(new['pooled']['recall upper bound'][0])}%, so recall within reach falls more than recall does. Schema fit does not depend on the ground truth and is unchanged. The difference *D* between the two schemas keeps its sign and its *p*.

These extractions were made with the rules of 2026-11-05. The numbers therefore describe earlier extractions against a newer ground truth, and they are not the numbers that a new extraction with the rules of 2026-11-13 would give.

## Partial pairs

A partial pair counts at the partial level unless a person marks it "not the same fact" (`070_evaluate/070_evaluate.md`, *Checks and warnings*). Against the ground truth of 2026-11-12 the six runs held six different partial pairs with no verdict. I judged them on 2026-11-12 in `annotations/partial_pair_reviews.csv`: "2XMMi-DR3" HAS_NUMBER_OF "353,191 detections" against "353,191" is not the same fact, as for every count written without what it counts, and the other five are the same fact. The numbers above are scored with these verdicts, and {'no' if not r['unjudged'] else len(r['unjudged'])} partial pair of the six runs is left without a verdict.

Step 070 also warned in each run that between 47 and 62 earlier verdicts match no partial pair of that run any more, and that 19 rows of `annotations/second_opinion.csv` name a triple that is no longer a ground truth triple of its record. Neither warning changes a number above.
"""
create("docs/analysis/rescore_2026-11-13.md", rescore)

# ------------------------------------------------------------------ 2. recall by rule
g = r["by_rule"]["groups"]
small = [k for k in g if g[k]["1816"]["n"] < 10 and k.isdigit()]
by_rule = f"""# Recall by guideline rule

{LABEL}

## What this is

Each ground truth row has a column `rules`, which lists the numbers of the rules of `annotations/guidelines.md` that the triple uses. This page gives, for each rule number, the recall of the ground truth triples that list it, over the six runs of `rescore_2026-11-13.md` (three repeats with the induced schema, three with the ground truth schema), on the ground truth of 2026-11-13.

Formula, for a rule *r* and one run: recall of *r* = the ground truth triples that list *r* and are in a pair ÷ the ground truth triples that list *r*, with both counts summed over the 20 evaluated records. At the partial level a pair is an exact pair or a partial pair, and at the exact level an exact pair only, as `070_evaluate/metrics/pairs.md` and `070_evaluate/metrics/recall.md` define them. The pairs are those that step 070 made in each run (`compared_triples.csv`, column `status`), and nothing was paired again. A column gives the mean of that proportion over its runs. The row *all* is recall as step 070 reports it, for reference.

## How to read it

- The groups overlap. A ground truth triple lists several rules and is counted in the row of each, so the rows do not add up to {new['gt_triples'][0]} and their recalls are not independent.
- Rules 2, 11, 13, 14 and 17 apply to every ground truth triple and are not recorded in the column, so they have no row. No ground truth triple of the evaluated records lists rule 3.
- A rule's row holds the triples that use the rule, which is not the same as the triples the rule causes extraction to miss. The triples of a row also differ in their records and in their other rules, so a row with low recall is a place to look and not a finding about the rule.
- A row with fewer than 10 ground truth triples is marked *too small*: rules {', '.join(sorted(small, key=int))}, and the one triple that records no rule. Its recall changes by many points with one triple and should not be read.
- The column *Within reach* counts the row's ground truth triples that the induced schema can express through the translation table (`070_evaluate/metrics/recall_upper_bound.md`). With the ground truth schema every triple is within reach. A row with few triples within reach is limited by the schema before extraction starts: rule 9 has {g["9"]["1816"]["n"]} triples, of which {g["9"]["1816"]["within_reach"]} are within reach.
- The values in the column `rules` were written by a model and are still to be reviewed by a person (`docs/improvements.md`, *The rules each ground truth triple uses, recorded per triple*).
- The extractions were made with the rules of 2026-11-05, before the rules changed on 2026-11-12 and 2026-11-13.

## The table

| Rule | Title (the rule's bold first words in the guidelines) | Ground truth triples | Within reach, induced schema | Partial recall, induced schema (mean of 3 repeats) | Partial recall, ground truth schema (mean of 3 repeats) | Partial recall, mean of the six runs | Exact recall, mean of the six runs |
|---|---|---:|---:|---:|---:|---:|---:|
{t['by_rule_md']}

The same rows, with exact recall per schema, are in `recall_by_rule.csv` beside this file.

## Precision by rule is not defined

Precision divides the pairs by the counted occurrences (`070_evaluate/metrics/precision.md`). An occurrence that is left extracted only has no ground truth triple, and only ground truth triples have a `rules` value, so such an occurrence belongs to no rule. A precision per rule would need the occurrences of that rule as its denominator, and that set does not exist. Step 070's attributed precision (`070_evaluate/070_evaluate.md`, *By the second opinion*) could be computed per rule. It counts every unpaired occurrence against every group alike, and its groups there do not overlap, while the rules' groups do. It is left out.

## Where the numbers come from

Scripts `{SCRATCH}/analyses.py` (function `by_rule`) and `{SCRATCH}/tables.py`. They read the six runs' `compared_triples.csv`, copied after each run into `outputs/analysis/runs/` (the same files are kept in `outputs/intermediate_results/070_evaluate/previous_runs/`), and `annotations/ground_truth/batch_*.csv`. Every one of the {new['gt_triples'][0]} ground truth triples of each run was matched to its row in the ground truth files by record id and classed triple.
"""
create("docs/analysis/recall_by_rule.md", by_rule)

# ------------------------------------------------------------------ 3. scalability
cat, smp, ind, ref = s["catalog"], s["sample"], s["induced schema"], s["ground truth schema"]
ci, cr = ind["catalog_est"], ref["catalog_est"]


def usd(v):
    return f"${v:,.0f}"


def n0(v):
    return f"{v:,.0f}"


def rng(d, mean, lo, hi, f=n0):
    return f"{f(d[mean])} ({f(d[lo])} to {f(d[hi])})"


def usd3(d):
    return f"${d['mean']:.3f} (${d['min']:.3f} to ${d['max']:.3f})"


scal = f"""# What extracting from the whole catalog would take

{LABEL}

## What is missing

The six reported runs called the model on the NASA laptop, and their reports (section *Model calls*) hold the token counts as the service counted them and the duration of each run. Those reports and logs are not on this computer. The 28 reports of step 060 in `outputs/reports/` here, dated 2026-11-05 and 2026-11-06, are all of runs answered from the answer cache: each shows 0 requests sent, 0 tokens, and a duration of about 5 seconds. The cache itself (`outputs/intermediate_results/060_extract/cache/extract.json`) keeps each answer's content and no token count or time. `docs/improvements.md` (*Cost per run*, *Prompt size and cost*, *Measure the step times on the NASA laptop*) records the same gap.

The following are therefore not available here, and this page does not invent them:

- the tokens per request as the service counted them: sent, read from the prompt cache, written to it, received, and received as thinking;
- the time per record, and with it the time for the whole catalog;
- what NASA's LiteLLM charges per token, and what the six runs cost.

What can be measured here is the size in characters of every request and of the content of every answer. The rest of this page gives those measurements and a rough estimate built on them. Every token count and dollar figure below is an estimate from characters and list prices, not a measurement.

## What was measured

Catalog size: `outputs/intermediate_results/020_clean/records.jsonl` has {cat['records']:,} records. Split as step 060 splits them (`max_chars` 8000), they give {cat['requests']:,} requests, since {cat['records_with_more_than_one_piece']} records have more than one text piece.

Each request was built again with the code and prompts of the commit whose prompt fingerprints the six runs record, with nothing sent (script `{SCRATCH}/prompt_sizes.py`).

| Measured, in characters | Induced schema | Ground truth schema |
|---|---:|---:|
| Start of the prompt that is the same in every request (instructions, schema, rules, examples) | {ind['identical_start_chars']:,} | {ref['identical_start_chars']:,} |
| Of which the schema | {ind['schema_text_chars']:,} | {ref['schema_text_chars']:,} |
| Whole prompt per record, 20 evaluated records: mean (lowest to highest) | {rng(ind['sample_prompt_chars'], 'mean', 'min', 'max')} | {rng(ref['sample_prompt_chars'], 'mean', 'min', 'max')} |
| Rows of `extracted_triples.csv` per record, mean of 3 repeats: mean (lowest to highest) | {ind['sample_triples']['mean']:.1f} ({ind['sample_triples']['min']:.1f} to {ind['sample_triples']['max']:.1f}) | {ref['sample_triples']['mean']:.1f} ({ref['sample_triples']['min']:.1f} to {ref['sample_triples']['max']:.1f}) |
| Those rows written as JSON, per record, mean of 3 repeats: mean (lowest to highest) | {rng(ind['sample_answer_chars'], 'mean', 'min', 'max')} | {rng(ref['sample_answer_chars'], 'mean', 'min', 'max')} |

The record's own text is a small part of each prompt. The 20 evaluated records have {n0(smp['piece_chars_mean_per_record'])} characters of text on average ({smp['piece_chars_min']:,} to {smp['piece_chars_max']:,}), and the catalog's records have {n0(cat['piece_chars_mean_per_record'])} on average (median {cat['piece_chars_median_per_record']:,.1f}, longest {cat['piece_chars_max_per_record']:,}). With the induced schema, {100 * ind['identical_start_chars'] / ind['sample_prompt_chars']['mean']:.1f}% of an average prompt is the identical start.

## A rough estimate per record

Assumptions, each a source of error:

1. One token is about 4 characters. This is the rough rule of `060_extract/060_extract.md` (*The schema in the prompt*), "not counted exactly".
2. The answer is as long as its kept rows written as JSON. The answer as the model wrote it is not kept. Thinking tokens, which are billed as received tokens, are not known and are left out, so the received tokens are understated.
3. Prices are Anthropic's list prices for Claude Opus 5.5 per million tokens: $4.00 sent, $20.00 received, $0.20 read from the prompt cache, and $5.00 written to it (1.25 times the sent price). They come from the reference table of Claude Code's `claude-api` skill, cached on 2026-11-03, and not from the repository. The read and write ratios agree with those in `060_extract/060_extract.md` (*Prompt caching, for cost*). What NASA's LiteLLM charges may differ.

| Estimate per record, 20 evaluated records | Induced schema | Ground truth schema |
|---|---:|---:|
| Tokens sent: mean (lowest to highest) | {rng(ind['sample_tokens_est'], 'input_mean', 'input_min', 'input_max')} | {rng(ref['sample_tokens_est'], 'input_mean', 'input_min', 'input_max')} |
| Tokens received, visible answer only: mean (lowest to highest) | {rng(ind['sample_tokens_est'], 'output_visible_mean', 'output_visible_min', 'output_visible_max')} | {rng(ref['sample_tokens_est'], 'output_visible_mean', 'output_visible_min', 'output_visible_max')} |
| Cost with no prompt caching: mean (lowest to highest) | {usd3(ind['sample_cost_est_per_record']['no_cache'])} | {usd3(ref['sample_cost_est_per_record']['no_cache'])} |
| Cost with the identical start read from the prompt cache: mean (lowest to highest) | {usd3(ind['sample_cost_est_per_record']['start_read_from_cache'])} | {usd3(ref['sample_cost_est_per_record']['start_read_from_cache'])} |
| Time | not available | not available |

## Extrapolation to the {cat['records']:,} records

Further assumptions: the prompt, the schema and the model stay as in the six runs; each of the {cat['requests']:,} requests is sent once, with no retry and no failed call; and a catalog record gets as long an answer on average as one of the 20 evaluated records. The last assumption likely overstates the answers, since the 20 records are longer on average than the catalog's ({n0(smp['piece_chars_mean_per_record'])} against {n0(cat['piece_chars_mean_per_record'])} characters of text). Scaling the answers by that ratio gives the lower figure in the row of received tokens. The costs use the higher figure.

| Estimate for the whole catalog | Induced schema | Ground truth schema |
|---|---:|---:|
| Tokens sent in the identical start | {n0(ci['input_tokens_start'] / 1e6)} million | {n0(cr['input_tokens_start'] / 1e6)} million |
| Tokens sent after it (the records) | {ci['input_tokens_rest'] / 1e6:.1f} million | {cr['input_tokens_rest'] / 1e6:.1f} million |
| Tokens received, visible answer only | {ci['output_visible_tokens_scaled_by_text_length'] / 1e6:.0f} to {ci['output_visible_tokens'] / 1e6:.0f} million | {cr['output_visible_tokens_scaled_by_text_length'] / 1e6:.0f} to {cr['output_visible_tokens'] / 1e6:.0f} million |
| Cost with no prompt caching | about {usd(ci['cost_no_cache'])} | about {usd(cr['cost_no_cache'])} |
| Cost if half of the requests read the start from the cache and half write it | about {usd(ci['cost_half_reads_half_writes'])} | about {usd(cr['cost_half_reads_half_writes'])} |
| Cost if every request after the first reads the start from the cache | about {usd(ci['cost_all_reads_but_one_write'])} | about {usd(cr['cost_all_reads_but_one_write'])} |
| Time | not available | not available |

Prompt caching decides most of the cost. With the induced schema and no caching, the identical start is about {usd(ci['cost_input_start_no_cache'])} of the {usd(ci['cost_no_cache'])}, and read from the cache on every request it is about {usd(ci['cost_input_start_all_read'])}. Step 060 marks that start for caching (`060_extract/060_extract.md`, *Prompt caching, for cost*). How often a request reads the cache through NASA's LiteLLM in a long run is not known. In the test of 2026-10-12, 4 of 8 identical requests read it, which fits several copies of the model behind the service, each writing its own cache once. The row with half reads and half writes takes that test's proportion, and the same section expects that in a long run nearly all requests would read. Batch requests, at half price where the service offers them, are not included, and whether NASA's LiteLLM offers them is not known (same section).

The estimate covers step 060 only, and the two schemas' estimates differ only through the length of the schema in the prompt and the length of the answers.

## To replace the estimate with measurements

On the NASA laptop, the reports of the paid 060 runs behind the six reported runs give the tokens sent, read from the cache, written to it and received, and the duration (`docs/improvements.md`, *Cost per run*, smallest version, part 1). Those numbers, divided by the 20 records and multiplied by {cat['records']:,}, replace assumptions 1 and 2. The run on a random 1% of the catalog that the same entry plans would replace the assumption about the length of the answers, and would give the rates of failed and cut-off answers.

## Where the numbers come from

Scripts `{SCRATCH}/prompt_sizes.py` (characters of each prompt and of the catalog's texts) and `{SCRATCH}/scalability.py` (answers' characters from the six runs' `extracted_triples.csv`, which include each record's describes triple; tokens and dollars). Their results are `prompt_sizes.json` and `scalability.json` in `outputs/analysis/`, a working folder that is not in Git.
"""
create("docs/analysis/scalability.md", scal)

# ------------------------------------------------------------------ 4. by kind of record
LONG = int(re.search(r"\| more than [^|]* \| 10 \| (\d+) \|", t["length_md"]).group(1))
kind = f"""# Scores by kind of record

{LABEL}

## What this is

The 20 evaluated records of the tuning part, grouped in two ways that need no judgment, with partial F1 per group on the ground truth of 2026-11-13. The runs are the six of `rescore_2026-11-13.md`.

Formula: partial F1 of a group = 2 × (exact pairs + partial pairs) ÷ (counted occurrences + ground truth triples), with each count summed over the group's records in one run (`070_evaluate/metrics/f1.md`). Counted occurrences are the occurrences less the untranslatable extracted triples and less those paired with a fact that waits on an expert. Each cell gives the mean of the three repeats, with the lowest and highest repeat in parentheses. Step 070 pools counts and never averages records' own numbers (`070_evaluate/metrics.md`, *Pooled, not averaged*). The column *Mean of the records' own partial F1* is the unweighted average over the group's records, given only to show how far a long record moves the pooled number.

**The groups are tiny.** They hold between 1 and 10 records, so every number here describes these 20 records and supports no claim about a kind of record in the catalog. The range in parentheses is the spread over three repeats on the same records, not a margin of error over records. No test was made between groups.

## By stratum

The stratum is the record's group of maintainers in `annotations/ground_truth_candidates.csv`, which step 030 used to draw the pool. It is the only field in the repository that sorts the evaluated records by where they come from: `organization` is "NASA" for all 20. Which data system a maintainer stands for is not recorded in the repository, so the strata are not relabelled here. Step 070 warns that the stratum *Planetary Data System* has none of the evaluated records while it is 17% of the pool.

| Stratum | Records | Ground truth triples | Partial F1, induced schema | Mean of the records' own partial F1, induced schema | Partial F1, ground truth schema |
|---|---:|---:|---:|---:|---:|
{t['strata_md']}

## By length of the record's text

The length is the number of characters of the record's text as step 060 sends it (script `prompt_sizes.py`). The split is at the median of the 20 records, {t['median_chars']:g} characters.

| Length of the text | Records | Ground truth triples | Partial F1, induced schema | Mean of the records' own partial F1, induced schema | Partial F1, ground truth schema |
|---|---:|---:|---:|---:|---:|
{t['length_md']}

In these 20 records, the 10 longer texts hold {LONG} of the {new['gt_triples'][0]} ground truth triples and have the lower pooled partial F1 with both schemas. Length and stratum are mixed, since the longest texts belong to few strata, so the two tables do not show two separate effects.

## Each record

Partial F1 with the induced schema is the mean of the record's own value over the three repeats (`metrics.json`, `per_record`).

| Pool position | Title | Stratum | Characters of text | Ground truth triples | Partial F1, induced schema |
|---:|---|---|---:|---:|---:|
{t['per_record_md']}

## Where the numbers come from

Scripts `{SCRATCH}/analyses.py` (function `by_kind`) and `{SCRATCH}/tables.py`. They read each run's counts per record from `outputs/intermediate_results/070_evaluate/evaluations/` (one file per run: {', '.join(ids)}), and each record's own partial F1 from the six `metrics.json` copied into `outputs/analysis/runs/`.
"""
create("docs/analysis/by_record_kind.md", kind)
assert not r["unjudged"], "partial pairs without a verdict: list them in the page before writing it"
print("wrote the four pages of docs/analysis/")
