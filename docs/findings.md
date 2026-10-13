# Findings

What has been measured about the pipeline, newest first. Each entry says what was measured, on which runs and data, the numbers, and what they mean and don't mean. How each step works is in its guide; this file holds results. Terms: [docs/terminology.md](terminology.md).

The runs' own files (reports, logs, outputs) stay on the laptop that ran them, in `outputs/`, which Git doesn't carry; each entry names them.

**How this file is kept.** *Current picture* (below) is rewritten whenever results change: what is known now, with links to the entries it rests on. The dated entries are never rewritten: a later measurement that corrects or replaces one is a new entry, and the old one gets a line saying "Superseded by the entry of <date>". So the file also records what was known when.

## Current picture

- **The baseline schema** is 040's run of 2026-10-12 (60 entity classes, 104 predicates, 1,233 patterns), used unchanged by 060's and 070's experiments. [2026-10-12](#2026-10-12--step-040--the-baseline-schema)
- **040's schema is not reproducible run to run** (about a third of the entity classes and half the predicates were named differently in two runs); experiments that change 040 need repeated runs of one recipe first. [2026-10-12](#the-schema-varies-from-run-to-run)
- **Entity classes and predicates saturate within 150 texts; patterns don't,** so patterns are the part to make stricter (`min_support`) before 060 runs on the whole catalog. [2026-10-12](#saturation)
- **Data tables** in about 2% of descriptions are described, not extracted cell by cell (rule 8). [2026-10-12](#data-tables-in-descriptions)

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

In both runs, the service behind LiteLLM withheld some answers of stage 3's predicate labeling (`finish_reason` `content_filter`). The batches were asked again in halves (`common/common_helpers/cache.py`, `ask_split`) down to batches of 2, and in the end nothing was refused: smaller batches went through. What sets the filter off, and whose filter it is, isn't known.
