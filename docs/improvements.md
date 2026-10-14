# Improvements list

The changes to make to the pipeline itself: what to change, why, and where the idea came from. Not to be confused with a step guide's *To do*, which says what a person running that step must do. An item that is done is deleted here, and the commit that does it says so. Measured results that an item rests on are in [`findings.md`](findings.md).

## The whole pipeline

- **Repeat runs, to measure run-to-run noise.** A setting that skips the saved answers, so that a step can be run again with exactly the same settings. One run isn't a baseline: two runs of step 040 with the same settings kept the names of 41 of 63 entity classes and 67 of 126 predicates. From: [`findings.md`](findings.md), 2026-10-12.
- **Cost per run.** Each report already gives the tokens sent and received (section *Model calls*); a price per token would turn them into dollars. From: the literature review of 2026-10-07.
- **A batch API at NASA's LiteLLM**, if it has one: many calls sent together, at a discount. Ask NASA's LiteLLM administrators. From: 2026-10-13.
- **Saved answers that are JSON of the wrong shape.** An answer that is JSON is saved whatever its shape (`common/common_helpers/cache.py`, `ask_cached`), so a rerun reuses a useless one instead of asking again. Check the shape before saving. From: 2026-10-12.
- **Keep the saved answers safe:** every model answer behind a reported number is in the steps' `cache/` folders under `outputs/`, which Git doesn't carry, so they exist only on the computer that ran the step. Archive them with each run that numbers are reported from. From: the methods review of 2026-10-11, item 7.
- **`tests/run_all.py` on the NASA laptop:** its first run there reported that the tests changed files, and the next run passed. Find why. From: 2026-10-12.
- **README, *How to reproduce*:** setup and running are in [`running_on_nasa_laptop.md`](running_on_nasa_laptop.md); building the graph waits for step 080. From: `TODO.md`.
- **Other catalogs:** some things fit only data.nasa.gov. The catalog's address is fixed in the code (`010_harvest/010_harvest_helpers/ckan_client.py`); "undefined" is treated as a maintainer (`020_clean/020_clean_helpers/maintainers.py`); splitting into strata needs a maintainer field that other catalogs may not fill; step 040's prompts say "a catalog of NASA datasets". From: the methods review of 2026-10-11, item 11.
- **Competency questions:** 10 to 20 questions the knowledge graph should answer, to judge it by. From: the literature review of 2026-10-07.

## 020_clean

- **DCAT 3.0** (the W3C's vocabulary for data catalogs): enforce it. What that would change isn't worked out yet. From: `TODO.md`.

## 040_induce_schema

- **The sample of texts:** 10 maintainers × 15 texts is the documented baseline, not a design shown to be best. Taking only the 10 largest maintainers, it can never sample the records of the others (about 8% of the catalog, on the 2026-09-27 harvest; the methods review of 2026-10-11, item 3). Compare designs with `helpers/compare_runs.py`, guided by the saturation curve in 040's report. From: [`findings.md`](findings.md), 2026-10-12.
- **`min_support`** above 1 (it is 1, which keeps everything found): try other values once runs can be compared. From: 040's guide, *Settings*.
- **Near-duplicate texts inflate support.** If a maintainer's 15 texts are nearly the same text, every schema entry found in them counts 15 times. Measure how alike each maintainer's texts are; then drop the near-duplicates (taking others from the same maintainer), or count that maintainer once. It matters once `min_support` is above 1. 040's report lists twins between the texts it learned from and the pool, not near-duplicates among its own texts. From: `TODO.md`.
- **Nothing filters junk from stage 2:** e.g. "dataset" as a bare subject instance, or "VNP43D66 is the BSA" read as an "is a" statement, both gaining real support. A list of generic subject instances to drop would cost nothing. From: `TODO.md`.
- **Alternatives to stage 4 (merging synonymous labels):** grouping by similarity, passing the chosen labels forward from batch to batch, or another approach entirely. From: `TODO.md`.
- **Which fields to learn from:** 040 uses `title` and `notes` and any field 020's `extra_text_fields` adds; which other fields help is untested. From: `TODO.md`.
- **Ideas to compare the schema with:** the Purview glossary, Neo4j's capabilities, the five science domains of NASA's Science Mission Directorate (SMD) site, and the filters data.nasa.gov's search offers. From: `TODO.md`.

## 050_annotate

- **A near-duplicate check when coining:** before the annotation tool adds a coined entity class or predicate, show the closest ones already in the ground truth schema, by spelling (`Satelite`, `Satellite`) and by words shared with their names and definitions, with a button to use one instead. A model would also catch synonyms that share no words (`Probe`, `Spacecraft`), at a paid call each. For now, coined ones are reviewed together at the end of a batch. From: 2026-10-14.
- **Less work per annotated record:** measure the time per record on batch 0 first; then decide what to automate (e.g. a second model checking each draft and pointing at doubtful component classes, so a person looks only there). From: 2026-10-06 (queued), 2026-10-14.
- **Gemini 2.5 Pro and error 500:** in a test with an answer limit of 20 tokens it answered error 500 ("no choices"), probably its thinking using up the limit. Watch whether real drafting calls get it: each costs retries. From: [`findings.md`](findings.md), 2026-10-12.

## 060_extract

- **Patterns in or out of the prompt:** patterns are 58% of the schema text (about 14,500 tokens in all). Compare runs with and without them. From: [`findings.md`](findings.md), 2026-10-12.
- **Experiment: the source text first in the model's answer.** The reply asks for subject, predicate, object and their entity classes, then the source text last, so the model states a fact and finds its passage afterwards. Asking for the passage first, then the fact, may give facts that keep closer to the text. A model that thinks before answering (claude-opus-5.5 does) may gain less. From: Negro, Futia, Kůs and Montagna, *Knowledge Graphs and LLMs in Action* (Manning, 2026), section 14.7.1.
- **An entity class or predicate that does badly:** try another name for it first (a generic name gave unstable results there; a specific one fixed it). From: Negro, Futia, Kůs and Montagna, *Knowledge Graphs and LLMs in Action* (Manning, 2026), section 5.3.3.
- **Prompt size and cost:** measure both on the first run. From: 2026-10-12.
- **The content filter:** in step 040 the service refused phrases from GeneLab (space biology) records. Watch whether 060's failed records cluster there. From: [`findings.md`](findings.md), 2026-10-12.
- **A fixed schema for the full run,** chosen and kept in Git, so that the full run doesn't depend on whatever `outputs/` holds. From: 2026-10-12.

## 070_evaluate

- **Raise With Mentors: checking a sample of the occurrences left extracted only,** to see how far precision and recall are understated ([`metrics/pairs.md`](../070_evaluate/metrics/pairs.md), *The same fact in different words*). It's an involved process: such an occurrence can be the same fact in different words as a ground truth triple left ground truth only, a repeat of a fact already paired, a fact the ground truth lacks, the result of a wrong translation, or actually wrong, and each means something different. From: 070's guide, *To do*.
- **About 10 records annotated from scratch,** with no draft: measures how far the drafts steer annotation (recall may be overstated by a model-drafted ground truth: [`metrics/recall.md`](../070_evaluate/metrics/recall.md)). From: the literature review of 2026-10-07.
- **A second annotator** for a sample of records, to measure agreement between people (Hripcsak & Rothschild 2005). From: the literature review of 2026-10-07.
- **A second person checking a sample of the translation table,** frozen before the held-out part is looked at. From: the literature review of 2026-10-07.
- **How many extracted triples 060 removed, per reason,** in 070's report. From: the literature review of 2026-10-07.
- **Precision and recall per predicate and per entity class,** to see which ones extraction gets wrong (070 gives them per part and per stratum only). From: Negro, Futia, Kůs and Montagna, *Knowledge Graphs and LLMs in Action* (Manning, 2026), section 5.3.3.
- **Other quality metrics,** e.g. coverage. 070 already reports partial pairs, entity-class accuracy, and the recall upper bound. From: `TODO.md`.
- **The model's run-to-run variation** isn't among the reasons the numbers are approximate ([`metrics/approximately.md`](../070_evaluate/metrics/approximately.md)), and margins of error leave it out. Add it once repeat runs measure it (see *The whole pipeline*). From: the methods review of 2026-10-11, item 6.
- **Comparing runs whose schemas differ:** several component classes of a schema may translate to one of the ground truth schema, so a finer schema is forgiven some wrong entity classes ([`metrics/pairs.md`](../070_evaluate/metrics/pairs.md), row 5 of *When a pair isn't the same fact*). `helpers/compare_runs.py` should say so when the runs' schemas differ. From: the methods review of 2026-10-11, item 10.
- **The 10-point threshold** of 070's warning that a stratum's share of the evaluated records differs from its share of the pool: no source for 10. From: the literature review of 2026-10-07.
- **Citations not yet checked:** Cochran (1977) for the 5% rule and the ratio bias, cited from memory in the metric docs. From: the literature review of 2026-10-07.
- **Report wording:** "share" where "proportion" is meant (070's guide, `070_evaluate_helpers/readings.py`), and "extracted triple(s)" where an occurrence is meant (070's report). From: 2026-10-08.

## 080_build_graph

- **Three layers:** the records; each extracted triple as extracted (never merged), with its record and source text; and the knowledge graph built from those. The knowledge graph can then be rebuilt without asking a model again, and every edge can show the passage it came from. From: Negro, Futia, Kůs and Montagna, *Knowledge Graphs and LLMs in Action* (Manning, 2026), section 6.1.
- **Linking instances to reference lists,** so that one thing named several ways ("Aqua", "EOS PM-1") becomes one node. First processing levels, a short fixed list (L0, L1A, L1B, L2, L3, L4: every spelling, such as "Level 3" or "L-3", mapped to one); then NASA's missions ([A to Z of NASA missions](https://www.nasa.gov/a-to-z-of-nasa-missions/)), where an instance with no match is flagged for a person to check, not dropped, since the catalog also names missions of other agencies; GCMD keywords as another list. How: the instance keeps the record's words and gets an edge to its entry, saying how the match was made; candidates come from the list, never from a model (exact match after evening out, "Long Name (ACRONYM)" split into both forms, then near spellings as candidates only); a model chooses only among two or more candidates, and may answer "none of these"; a small hand-checked set of instance → entry (or none) measures it. Aliases ("EOS PM-1" for Aqua) must be written for our lists. From: `TODO.md`; 2026-10-13; Negro, Futia, Kůs and Montagna, *Knowledge Graphs and LLMs in Action* (Manning, 2026), chapters 7 and 8 (which choose without a "none" answer and don't measure linking).
- **Which predicates give properties instead of edges,** by the rule of README, *Phase 1*: a processing level, for example, has few values, which people filter by but don't go from node to node through. From: `TODO.md`; 2026-10-13.
- **Splitting a number with a unit** ("250 m") into a value and a unit, as graphs store quantities (Wikidata, QUDT, schema.org's QuantitativeValue). From: 2026-10-11.
- **Splitting a qualifier from what it qualifies** ("daily snow cover" into snow cover, daily), which annotation and extraction keep together (annotation guidelines, rule 9 of *Writing a classed triple*). From: 2026-10-13.
- **An extracted triple many records state:** one edge per extracted triple, or one edge listing the records it came from. Either way, keep which records each edge came from. From: 2026-10-06.
- **Merging instances that name the same thing** beyond the lists: similar spelling plus shared neighbors (two spacecraft names spelled alike that carry the same instrument), grouped into connected components, the longest name kept; generic words ("Data", "Product", "Level") never count as similar. From: Negro, Futia, Kůs and Montagna, *Knowledge Graphs and LLMs in Action* (Manning, 2026), section 6.1.4.
- **Checks of the graph:** how well nodes were merged (precision and recall of merging), duplicate nodes, and a person checking a sample of edges. From: the literature review of 2026-10-07.
- **Phase 1's maintainers:** README's table says 434 Maintainer nodes, but 020 joins maintainer spellings down to 422. Rebuild phase 1's part with 020's cleaning. From: `TODO.md`.
- **More facts from the structured fields** (phase 1): other metadata fields may give more facts, some of them properties. From: `TODO.md`.
