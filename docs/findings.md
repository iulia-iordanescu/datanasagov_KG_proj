# Findings

What has been measured about the pipeline, newest first. Each entry says what was measured, on which runs and data, the numbers, and what they mean and don't mean. How each step works is in its guide; this file holds results. Terms: [docs/terminology.md](terminology.md).

The runs' own files (reports, logs, outputs) stay on the laptop that ran them, in `outputs/`, which Git doesn't carry; each entry names them.

**How this file is kept.** Two parts for two readers. *Current picture* (below) is for reading: what is known now, in plain words, a few lines, rewritten whenever results change, each line linking to the evidence. The dated entries after it are the evidence: what was run, the numbers, and what each result does and doesn't show; they are what later decisions rest on. Entries are never rewritten: a later measurement that corrects or replaces one is a new entry, and the old one gets a line saying "Superseded by the entry of <date>". So the file also records what was known when.

## Current picture

- **The schema we start from** is the one step 040 made on 2026-10-12: 60 kinds of things, 104 relations, 1,233 allowed combinations. Every experiment on extraction (060) and evaluation (070) uses this same file. [Evidence](#2026-10-12--step-040--the-baseline-schema)
- **Step 040 gives a differently worded schema each time it runs**, even with almost nothing changed: in two runs, about a third of the kinds of things and half the relations had other names (e.g. FileFormat in one, DataFormat in the other). So a change to 040 itself can only be judged after running the same setup several times, to see how much it varies on its own. [Evidence](#the-schema-varies-from-run-to-run)
- **150 texts are enough to find the kinds of things and the relations** (the last texts read added almost none), but not the combinations, which keep growing. The combinations are the part to trim before extraction runs on the whole catalog. [Evidence](#saturation)
- **Tables of numbers inside descriptions** (about 2% of records) are described, not copied cell by cell (rule 8 of the annotation guidelines). [Evidence](#data-tables-in-descriptions)
- **Prompt caching** (paying a fraction for the part of a request that is the same every time) **works through NASA's LiteLLM for Claude**, the way 060 sends it. Extraction (060) uses it; nothing else repeats enough to be worth it. For Gemini it's unclear. [Evidence](#2026-10-12--litellm--prompt-caching-works-after-a-first-write-per-copy-of-the-model), [more](#2026-10-12--litellm--caching-inside-the-user-message-and-gemini)
- **The safety filter of the model's service** sometimes stops answers about space-biology phrases (e.g. "was more virulent than"). Step 040 works around it; extraction (060) on space-biology records may lose some facts, to be watched in its report. [Evidence](#2026-10-12--step-040--what-the-content-filter-stopped-on)

## 2026-10-12 · LiteLLM · Caching inside the user message, and Gemini

**The test.** On the NASA laptop, the same 2,523-token block as in the entry below, this time marked for caching as the first part of the user message (not a separate system message), sent 4 times to `claude-opus-5.5` and 4 times to `gemini-2.5-pro`, each with an answer limit of 20 tokens.

**Claude.** All 4 requests wrote the cache (2,524 tokens), none read it. With the block as a separate system message (the entry below), 4 of 8 read it. Four writes in a row could still be four different copies of the model, so this doesn't prove the user-message form never reads; but only the system-message form has been seen to read, so 060 keeps that form. 040's extraction gets no caching: its saving would be small (about 150 requests with a 1,000–2,000-token identical start), and its requests stay as the baseline run sent them.

**Gemini.** The first request answered and reported its whole prompt (1,930 tokens) as read from a cache, though Gemini had not been sent it before; why isn't known. The next three failed: HTTP 500 from LiteLLM, "provider returned a response with no 'choices'". A likely but unverified cause is the 20-token answer limit: Gemini 2.5 Pro thinks before answering and its thinking counts against the limit, so it may have used all 20 before writing anything. 050's requests allow 16,000 tokens (`MAX_ANSWER_TOKENS`). If 050 meets the same error, it would cost calls: an HTTP 500 is asked again (`RETRY_STATUSES` in `common/common_helpers/llm.py`); each report now counts every request, which would show it. 050 asks for no caching.

## 2026-10-12 · LiteLLM · Prompt caching works, after a first write per copy of the model

**The test.** On the NASA laptop, identical requests to `claude-opus-5.5` through NASA's LiteLLM, each starting with the same 2,523-token block marked for Anthropic's prompt caching. First two requests: both wrote the cache, neither read it. Then six more, in this order: read, read, wrote, wrote, read, read (2,523 tokens each time).

**What it means.** The caching instruction reaches the model's service, and cached reads happen. That the first requests wrote and later ones read, with writes reappearing between reads, fits several copies of the model behind the service, each with its own cache that is written once and then read; this is inferred, not confirmed by the service. Since writing costs 1.25 times normal input and reading 0.05 times (for Opus 5.5, per Anthropic's documentation), caching pays once about 1 request in 5 reads: here 4 of 8 did, and in a long run nearly all would. 060 asks for caching since (`060_extract/060_extract.md`, *The schema in the prompt*), and each report counts the tokens read from and written to the cache, which will show the real share.

## 2026-10-12 · Step 040 · What the content filter stopped on

**The evidence.** In run `040_induce_schema_2026-10-12_1629`, its log (`outputs/logs/040_induce_schema_2026-10-12_1629.log`, DEBUG lines starting "answer stopped by the service") holds what the model wrote before each of the two stops, both in stage 3's predicate labeling. The last words before the first (a batch of 80, 699 characters): `"was grown in LSMMG using": "USES", "was grown`. Before the second (a batch of 40, 163 characters): `"was more virulent than": "COMPARED_TO", "was observed in": …`. LSMMG is low-shear modeled microgravity, a way of growing microbes; both phrases come from GeneLab's space-biology records (how bacteria behave in spaceflight). No tokens were spent thinking.

**A hypothesis, not verified.** A safety filter for biological content: recent Anthropic models run with classifiers that block content on making pathogens more dangerous, and a list of bare phrases such as "was more virulent than" and "was grown in … using", without their records, can look like that. Smaller batches, where such phrases are fewer, went through. Whose filter it is (the model maker's, or one added by the service LiteLLM forwards to) isn't known, nor whether every such stop is labeled `content_filter`.

**What it means.** For 040, nothing more: asking again in halves got every batch answered. For 060, which extracts from whole records (in 040, every text's extraction went through), failed records clustering in GeneLab's would point to the same filter; 060's report lists every failed record.

## 2026-10-12 · Step 040 · The baseline schema

**The run.** `040_induce_schema_2026-10-12_1714`, on the NASA laptop: the harvest of 2026-10-01; `claude-opus-5.5` through LiteLLM; 15 texts from each of the 10 largest maintainers (150 texts); `min_support` 1; the extraction rules with rule 8 (values inside a data table aren't facts). It found 2,767 verified triple instances in 150 texts, and made a schema of 60 entity classes, 104 predicates and 1,233 patterns. This is the baseline schema: 060's and 070's experiments use this file unchanged. Its report: `outputs/reports/040_induce_schema_2026-10-12_1714.md`.

### The schema varies from run to run

The run before it, `040_induce_schema_2026-10-12_1629`, had the same setup except rule 8 (its schema and evidence are kept in `outputs/intermediate_results/040_induce_schema/previous_runs/040_induce_schema_2026-10-12_1629/`). Rule 8 changes what about 3 of the 150 texts give, yet:

| | Before rule 8 | After | Same name in both |
|---|---:|---:|---:|
| Entity classes | 63 | 60 | 41 |
| Predicates | 126 | 104 | 67 |

Most of the difference is one idea under another name: `FileFormat` → `DataFormat`, `Resolution` → `SpatialResolution`, `Substance` → `Chemical`, `Publication` and `ResearchPaper` → `Paper`, `RELEASED_ON` → `RELEASE_DATE`, `UPDATED_ON` → `LAST_UPDATED`.

*What it means.* 040's schema is not reproducible from run to run: the model names things differently, and the first names chosen shape later ones (stage 3's running vocabulary). So an experiment that changes 040 itself (its sample, `min_support`, its prompts) needs the same recipe run several times, to see how much the schema moves by chance alone, before a difference can be called an effect.

*What it doesn't mean.* The two runs differ by rule 8 and by chance, so this comparison can't separate the two; only a repeat of one recipe can (it needs a setting that asks the model again instead of reusing the cache, not built yet). Comparing by name also overstates the difference, since a renamed idea counts as a loss and a gain; a fair comparison would match synonyms first (not designed yet). It doesn't affect experiments on 060 or 070, which use the baseline schema unchanged.

### Saturation

From the run's report (*Saturation*): the expected number of schema entries after k of the 150 texts, averaged over every reading order.

| Texts read | 25 | 50 | 75 | 100 | 125 | 150 | Added by the last 25 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Entity classes | 54 | 58 | 60 | 60 | 60 | 60 | 0.01 |
| Predicates | 71 | 86 | 94 | 99 | 102 | 105 | 2.8 |
| Patterns | 297 | 537 | 746 | 934 | 1,106 | 1,264 | 158 |

Entity classes are saturated: more texts from these 10 maintainers would find no new kinds of things. Predicates nearly are. Patterns are not, and with `min_support` 1 likely never will be: every combination of entity classes and a predicate seen once counts. This speaks only for the 10 maintainers read.

### Breadth

| Schema entries found in texts of | 1 maintainer | 2 | 3 or more |
|---|---:|---:|---:|
| Entity classes | 2 | 9 | 49 |
| Predicates | 24 | 14 | 67 |
| Patterns | 1,067 | 145 | 52 |

Entity classes and most predicates are shared across maintainers, a hint that the 412 maintainers not read use them too. Most patterns come from one maintainer: local combinations, which fits their curve. Both point to patterns as the part of the schema to make stricter, e.g. by `min_support` (an experiment to make before 060's run on the whole catalog, whose every prompt includes the schema).

### Data tables in descriptions

In the run before (`_1629`), one record's answer (`2346cc06-9a33-471e-b30d-ac41fa072be6`, "Chandra Point Sources in 18 Distant Galaxy Clusters", 4,230 characters) was cut off at the 16,000-token limit after 26,399 characters: not a loop, but 164 distinct facts, one per cell of an 18-row table (redshift, position, exposure time of each cluster), with no tokens spent thinking. About 2% of the catalog's records (766, by a rough pattern for table-like lines) have such tables. Rule 8 (`annotations/guidelines.md`, *What counts as a fact*) now keeps what a table is about and leaves out its cells; under it the same record gave 29 facts and fit.

### The service's content filter

In both runs, the service behind LiteLLM withheld some answers of stage 3's predicate labeling (`finish_reason` `content_filter`). The batches were asked again in halves (`common/common_helpers/cache.py`, `ask_split`) down to batches of 2, and in the end nothing was refused: smaller batches went through. What sets the filter off, and whose filter it is, isn't known. Superseded in part by the entry of 2026-10-12, *Step 040 · What the content filter stopped on*.
