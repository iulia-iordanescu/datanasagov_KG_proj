# What extracting from the whole catalog would take

Preliminary, computed on 2026-11-13, still to be reviewed by a person.

## What is missing

The six reported runs called the model on the NASA laptop, and their reports (section *Model calls*) hold the token counts as the service counted them and the duration of each run. Those reports and logs are not on this computer. The 28 reports of step 060 in `outputs/reports/` here, dated 2026-11-05 and 2026-11-06, are all of runs answered from the answer cache: each shows 0 requests sent, 0 tokens, and a duration of about 5 seconds. The cache itself (`outputs/intermediate_results/060_extract/cache/extract.json`) keeps each answer's content and no token count or time. `docs/improvements.md` (*Cost per run*, *Prompt size and cost*, *Measure the step times on the NASA laptop*) records the same gap.

The following are therefore not available here, and this page does not invent them:

- the tokens per request as the service counted them: sent, read from the prompt cache, written to it, received, and received as thinking;
- the time per record, and with it the time for the whole catalog;
- what NASA's LiteLLM charges per token, and what the six runs cost.

What can be measured here is the size in characters of every request and of the content of every answer. The rest of this page gives those measurements and a rough estimate built on them. Every token count and dollar figure below is an estimate from characters and list prices, not a measurement.

## What was measured

Catalog size: `outputs/intermediate_results/020_clean/records.jsonl` has 36,406 records. Split as step 060 splits them (`max_chars` 8000), they give 36,466 requests, since 45 records have more than one text piece.

Each request was built again with the code and prompts of the commit whose prompt fingerprints the six runs record, with nothing sent (script `helpers/analysis/prompt_sizes.py`).

| Measured, in characters | Induced schema | Ground truth schema |
|---|---:|---:|
| Start of the prompt that is the same in every request (instructions, schema, rules, examples) | 112,456 | 75,550 |
| Of which the schema | 58,123 | 21,217 |
| Whole prompt per record, 20 evaluated records: mean (lowest to highest) | 113,885 (112,899 to 118,512) | 76,979 (75,993 to 81,606) |
| Rows of `extracted_triples.csv` per record, mean of 3 repeats: mean (lowest to highest) | 19.8 (2.7 to 60.3) | 20.7 (6.3 to 49.0) |
| Those rows written as JSON, per record, mean of 3 repeats: mean (lowest to highest) | 5,551 (730 to 17,552) | 5,944 (1,984 to 14,623) |

The record's own text is a small part of each prompt. The 20 evaluated records have 1,258 characters of text on average (272 to 5,885), and the catalog's records have 971 on average (median 603.5, longest 13,280). With the induced schema, 98.7% of an average prompt is the identical start.

## A rough estimate per record

Assumptions, each a source of error:

1. One token is about 4 characters. This is the rough rule of `060_extract/060_extract.md` (*The schema in the prompt*), "not counted exactly".
2. The answer is as long as its kept rows written as JSON. The answer as the model wrote it is not kept. Thinking tokens, which are billed as received tokens, are not known and are left out, so the received tokens are understated.
3. Prices are Anthropic's list prices for Claude Opus 5.5 per million tokens: $4.00 sent, $20.00 received, $0.20 read from the prompt cache, and $5.00 written to it (1.25 times the sent price). They are Anthropic's published prices (https://platform.claude.com/docs/en/about-claude/pricing, checked on 2026-11-17), not stored in the repository. The read and write ratios agree with those in `060_extract/060_extract.md` (*Prompt caching, for cost*). What NASA's LiteLLM charges may differ.

| Estimate per record, 20 evaluated records | Induced schema | Ground truth schema |
|---|---:|---:|
| Tokens sent: mean (lowest to highest) | 28,471 (28,225 to 29,628) | 19,245 (18,998 to 20,402) |
| Tokens received, visible answer only: mean (lowest to highest) | 1,388 (182 to 4,388) | 1,486 (496 to 3,656) |
| Cost with no prompt caching: mean (lowest to highest) | $0.142 ($0.117 to $0.206) | $0.107 ($0.086 to $0.155) |
| Cost with the identical start read from the prompt cache: mean (lowest to highest) | $0.035 ($0.010 to $0.099) | $0.035 ($0.014 to $0.083) |
| Time | not available | not available |

## Extrapolation to the 36,406 records

Further assumptions: the prompt, the schema and the model stay as in the six runs; each of the 36,466 requests is sent once, with no retry and no failed call; and a catalog record gets as long an answer on average as one of the 20 evaluated records. The last assumption likely overstates the answers, since the 20 records are longer on average than the catalog's (1,258 against 971 characters of text). Scaling the answers by that ratio gives the lower figure in the row of received tokens. The costs use the higher figure.

| Estimate for the whole catalog | Induced schema | Ground truth schema |
|---|---:|---:|
| Tokens sent in the identical start | 1,025 million | 689 million |
| Tokens sent after it (the records) | 10.4 million | 10.4 million |
| Tokens received, visible answer only | 39 to 51 million | 42 to 54 million |
| Cost with no prompt caching | about $5,153 | about $3,879 |
| Cost if half of the requests read the start from the cache and half write it | about $3,718 | about $2,914 |
| Cost if every request after the first reads the start from the cache | about $1,257 | about $1,262 |
| Time | not available | not available |

Prompt caching decides most of the cost. With the induced schema and no caching, the identical start is about $4,101 of the $5,153, and read from the cache on every request it is about $205. Step 060 marks that start for caching (`060_extract/060_extract.md`, *Prompt caching, for cost*). How often a request reads the cache through NASA's LiteLLM in a long run is not known. In the test of 2026-10-12, 4 of 8 identical requests read it, which fits several copies of the model behind the service, each writing its own cache once. The row with half reads and half writes takes that test's proportion, and the same section expects that in a long run nearly all requests would read. Batch requests, at half price where the service offers them, are not included, and whether NASA's LiteLLM offers them is not known (same section).

The estimate covers step 060 only, and the two schemas' estimates differ only through the length of the schema in the prompt and the length of the answers.

## To replace the estimate with measurements

On the NASA laptop, the reports of the paid 060 runs behind the six reported runs give the tokens sent, read from the cache, written to it and received, and the duration (`docs/improvements.md`, *Cost per run*, smallest version, part 1). Those numbers, divided by the 20 records and multiplied by 36,406, replace assumptions 1 and 2. The run on a random 1% of the catalog that the same entry plans would replace the assumption about the length of the answers, and would give the rates of failed and cut-off answers.

## Where the numbers come from

Scripts `helpers/analysis/prompt_sizes.py` (characters of each prompt and of the catalog's texts) and `helpers/analysis/scalability.py` (answers' characters from the six runs' `extracted_triples.csv`, which include each record's describes triple; tokens and dollars). Their results are `prompt_sizes.json` and `scalability.json` in `outputs/analysis/`, a working folder that is not in Git.
