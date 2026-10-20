# A Knowledge Graph of the data.nasa.gov Catalog: Pipeline Design and Evaluation Plan

Iulia Iordanescu, Pathways intern, Fall 2026

Work in progress: first draft, October 2026. It reports no evaluation results, because the first end-to-end evaluation has not been run.

## Abstract

data.nasa.gov is NASA's public catalog of datasets and related resources. Each catalog entry has structured metadata fields, such as its maintainer and tags, and two text fields, a title and a free-text description. A first phase of this project turned the structured fields into a knowledge graph. The second phase, described here, extracts facts from the text: which instrument collected a dataset, aboard which spacecraft, and what it measures. I built a pipeline of eight steps for this. A large language model induces a schema from a sample of the catalog's text, drafts ground truth for a person to correct, and extracts facts with the induced schema; code checks every fact against the record's text, and an evaluation step compares the extraction with the ground truth. The evaluation reports precision, recall, F1, and a recall upper bound that separates gaps in the schema from extraction errors, each with a bootstrap margin of error, on a tuning part and a held-out part of a stratified random sample of the catalog. So far the harvest, cleaning, splitting, and schema induction have run on the full catalog of 2026-10-01 (36,406 records), and the ground truth holds six annotated records, four of them finished.

## 1. Introduction

The data.nasa.gov catalog describes tens of thousands of datasets, tools, and documents. Its search works on words. A question such as "which datasets were collected by instruments aboard Aqua" needs relations between things, and those relations are written in the prose of each entry's description, not in a structured field.

A knowledge graph holds such relations as typed edges between named things. Building one from the catalog's text raises three questions: what schema the facts should use (which entity classes, such as Instrument, and which predicates, such as ABOARD), how to get the facts out of the text, and how to know whether they are right. My goal for the internship is a pipeline that answers all three in a way another person can rerun and check, with every number traceable to the records and model answers behind it, and every change judged by a measurement. This report records that pipeline as it stands. Its terms follow the project's terminology file, `docs/terminology.md`.

## 2. Background and related work

### 2.1 The catalog and phase 1

data.nasa.gov runs on CKAN, an open-source catalog software, whose public API returns each catalog entry as a JSON object of metadata fields. In this project a record is the metadata of one catalog entry. In the harvest of 2026-10-01, records have 31 possible top-level fields, 24 of them filled on at least one record. The records describe the data; the data themselves live in separate NASA archives and are never downloaded.

Phase 1 turned the structured fields of a harvest taken on 2026-08-30 (36,289 records) into a labeled property graph with Dataset, Maintainer, Keyword, and Format nodes. The `notes` field, filled on every record with a median of 529 characters of prose, was left for phase 2.

### 2.2 Extracting knowledge graphs from text with language models

Recent work uses large language models to extract triples from text, either against a schema given in advance or with a schema the system builds. Text2KGBench [1] evaluates extraction guided by an ontology whose concepts and relations, with their domains and ranges, are listed in the prompt; its authors note that much larger ontologies will need a way to select the part relevant to each text. EDC [2] first extracts triples with no schema, then defines each relation and maps it onto a schema, because large schemas do not fit in a prompt. AutoSchemaKG [3] has a model extract triples and induce a schema from the same text, grouping the extracted instances into semantic categories, at the scale of tens of millions of documents.

My schema induction step follows the data-driven approach of AutoSchemaKG at a much smaller scale. My extraction step follows Text2KGBench in placing the whole schema in the prompt, which the current schema's size allows.

### 2.3 Evaluating extracted triples

The WebNLG+ 2020 shared task [4] had a text-to-RDF track that scored extracted triples against reference triples at several matching levels, including exact and partial matches. End-to-end relation extraction distinguishes a "Strict" criterion, under which a relation counts only if its arguments also have the right entity types, from one that checks only the arguments' boundaries [5]. Wadhwa, Amir, and Wallace [6] evaluated relation extraction by language models with human judgments instead of exact matching, because a model may state a correct fact in words other than the reference annotation's. My evaluation borrows the exact and partial levels and the strict criterion, and adds a review of partial matches by a person.

A reference set drafted by a model and corrected by a person brings its own problems. In controlled experiments, automatic pre-annotation improved annotation speed and quality but also introduced biases that annotators should be warned about [7]. Annotators shown a model's suggestions tend to keep them, which raises the measured performance of models evaluated on those labels [8]. And the errors of different language models are correlated, even across providers [9], so an extraction model may miss the same facts as the drafting model.

### 2.4 Statistics for small evaluation sets

Annotating by hand limits the ground truth to a small sample, so every metric is an estimate. I use the bootstrap with percentile intervals [10], redrawing whole records rather than single triples, since a record's triples come from one model call and succeed or fail together [11]. Two versions of the pipeline are compared on the same records with the paired bootstrap [12]. Part of the sample is held out until the end, since a test set used to choose between versions no longer gives an unbiased estimate [13].

## 3. Data

All later steps work from one harvest of the full catalog, taken on 2026-10-01: 36,406 records, fetched in 37 pages, with no record repeated. The catalog changes quickly. The API reported 36,387 records at 17:00 on 2026-09-27 and 36,178 four hours later, and 14,672 on 2026-10-11, for reasons not known. The project therefore keeps the harvest of 2026-10-01 as a fixed snapshot.

The text a model reads for one record is its title and `notes` field, each preceded by its field name. In that harvest, 1,276 `notes` fields and 6 titles contained HTML markup. After the spellings of one maintainer are joined, the catalog has 422 maintainers. The ten largest hold 91.6% of the records; the fifth largest is the value `undefined`, which the catalog gives to 989 records. About 2% of the records (766, by a rough pattern for table-like lines) contain tables of values in the `notes` field, which the annotation rules treat as data rather than facts (section 5.2).

## 4. Method: the pipeline

The pipeline has eight numbered steps (Table 1). Each is a folder with a short control script that lists its inputs, settings, and stages, and a guide that describes them. Each step reads what earlier steps wrote and leaves a report and a log, and every output item records its origin, so any triple can be traced back to the API request that first returned its record. Steps that call a model cache every answer under a fingerprint of the model, the prompt's exact text, and the input, so a rerun pays only for new calls and reproduces earlier answers exactly. Every prompt is a plain text file in the repository.

Table 1. The pipeline's steps.

| Step | What it does | Calls a model |
|---|---|---|
| 010 harvest | Downloads every record from the catalog's API | no |
| 020 clean | Removes HTML from the text fields and joins maintainer spellings | no |
| 030 split | Keeps the ground truth candidates pool and the induction candidates apart; marks each pool record tuning or held-out | no |
| 040 induce schema | Learns entity classes, predicates, and patterns from a sample of induction candidates | yes |
| 050 annotate | Drafts classed triples for the next pool records, for a person to correct into ground truth | yes |
| 060 extract | Extracts the classed triples the current schema can express | yes |
| 070 evaluate | Compares the extracted triples with the ground truth | only to propose translations |
| 080 build graph | Will build the graph from the metadata fields and the extracted triples | not built |

The model is reached through one of two NASA services, LiteLLM or Ask Sage. The defaults in the code are `claude-opus-5.5` through LiteLLM for steps 040, 060, and 070, and `gemini-2.5-pro` for step 050, so that the drafting model and the extraction model come from different makers. Every call uses temperature 0 and allows answers of up to 16,000 tokens.

### 4.1 Harvest and cleaning (010, 020)

Step 010 requests pages sorted by creation time, so that records added or edited during a harvest do not shift later pages; an earlier harvest in CKAN's default order contained 12 repeated records. Step 020 drops repeated records, converts HTML in the text fields to plain text, and joins maintainer spellings that differ only in case, punctuation, word order, or titles such as "Dr.". The cleaner checks its own output: every word, number, and URL fragment of the source must survive, or the value falls back to a simpler method or stays uncleaned. In the 2026-10-01 harvest, 2 `notes` fields needed the fallback and none lost content.

### 4.2 Splitting (030)

If the records that judge extraction had also shaped the schema, the schema's metrics would flatter it. Step 030 therefore keeps two disjoint lists.

The ground truth candidates pool (the pool) holds 1,000 records drawn once, on 2026-09-21, from the 36,323 records of the catalog then. The draw was stratified by maintainer with proportional allocation (seed 1000), with 19 strata: 18 large maintainers on their own, and one stratum combining the 404 maintainers too small to earn two places. The pool's rows were then shuffled, so the first k records are a fair sample of the catalog for any k, and annotation can stop anywhere without biasing the sample. Of the 1,000, 999 remain in the 2026-10-01 harvest.

The induction candidates are every other record with text, 35,407 records across 422 maintainers, each maintainer's records in a fixed random order. Since both orders are fixed, taking more records later keeps those already taken, and model answers already paid for stay valid.

Step 030 also fixes, before any evaluation, which pool records are tuning and which held out. Pool positions 0 to 5, from which the ground truth schema was written, are tuning. From position 6 on, every third record (8, 11, 14, and so on) is held out and the rest are tuning: 668 tuning and 331 held-out records among the 999.

### 4.3 Schema induction (040)

Step 040 learns the schema from the first 15 induction candidates of each of the 10 largest maintainers, 150 texts in all, in seven stages. The model lists every fact each text states as a triple instance (subject, predicate, object), with no schema given, each with its source text, the shortest passage that states it; it also names the describes class, the entity class of the thing the record's title names, such as Dataset. Code discards any triple instance whose source text is not in the record's text. The model then labels each subject and object instance with an entity class and each predicate instance with a predicate, in batches of 80 that are each shown the labels chosen so far; merges labels that mean the same thing, seeing every label at once; and writes a one-sentence definition of each entity class and predicate, or says it is too vague. Code counts each schema entry's support, the number of distinct texts it was found in, and the maintainers those texts came from, and builds the schema from the counts: an entry enters if its support reaches a minimum (currently 1) and it was not judged too vague. Every entry left out is kept with its reason.

The report also gives a saturation curve: the expected number of schema entries after k of the 150 texts, averaged exactly over every order in which the texts could have been read. It is the sample-based species accumulation curve of ecology [14], with a text as a sample and a schema entry as a species.

### 4.4 Annotation (050)

Step 050 drafts the classed triples of the next pool records, ten per drafted batch by default. A classed triple writes one fact as a subject instance with its entity class, a predicate, and an object instance with its entity class, such as "MODIS" (Instrument) ABOARD "Aqua" (Spacecraft). The drafting prompt asks first for every fact the text states, then for the ground truth schema's entity classes and predicates where they fit, coining new ones where they do not. Code adds each record's describes triple, which links the record's id to its title and keeps the catalog entry apart from the thing it describes, and flags every drafted triple that fails a check against the record's text or the ground truth schema. A person then corrects the batch in a local, browser-based annotation tool, which saves the ground truth files to Git.

### 4.5 Extraction (060)

Step 060 extracts from each record only the facts the current schema can express, in its own entity classes and predicates. By default the current schema is the induced schema plus the schema additions, entries a person writes by hand, each with a line saying where the idea came from; an entry learned from ground truth records must name tuning records only, or it is left out. The extraction prompt shares its rules and reply format with step 050. Code removes, with the reason, any classed triple whose source text is not in the record's text or that uses an entity class or predicate the schema lacks. A classed triple that joins known entity classes and a known predicate in a pattern the schema has not seen is kept and flagged, since a schema's patterns record what was seen, not everything allowed.

The whole schema goes into every request: for the induced schema of 2026-10-12, about 58,000 characters, roughly 14,500 tokens by a four-characters-per-token estimate. Since this part is the same in every request, step 060 marks it for prompt caching. Until the schema is final, step 060 extracts only from finished ground truth records, the only ones step 070 can evaluate.

### 4.6 Graph building (080)

Step 080 is not built. It will write nodes and edges from the phase 1 metadata fields and from the extracted triples, each edge keeping its record and source text. A labeled property graph such as Neo4j is the current plan.

## 5. Ground truth and annotation

### 5.1 The ground truth and its schema

The ground truth is the set of classed triples of the annotated pool records, as a person has corrected them. A record is finished when the person confirms that every fact its text states is among its ground truth triples. Only finished records are evaluated, and only the longest run of them from the start of the pool, so the evaluated records always form a fair sample.

The ground truth uses its own schema, written while annotating (`annotations/ground_truth_schema.txt`): each entity class and predicate with a one-line definition, the patterns the file lists, and every pattern the ground truth uses. Some predicates are pinned to the entity classes they may join; ACQUIRED_BY_INSTRUMENT, for example, may only join a Dataset to an Instrument. The file defines 34 entity classes and 45 predicates and grows as annotation proceeds.

### 5.2 Annotation guidelines

The annotation guidelines (`annotations/guidelines.md`) say what counts as a fact and how to write a classed triple, and the model gets the same rules when it drafts and extracts; a test in the repository checks that each rule of the model's copy has its counterpart in the guidelines. The rules include "Only what the record states", "Every fact the record states", whether or not the schema can express it, "Not negated facts", "Not uncertain facts", and "Not the values inside a data table; only what the table is about". Subject and object instances are "the record's own words, as written". A qualifier that is a time step, an area the data cover, a processing level, a size on the ground, a country, or a time of day becomes a classed triple of its own: "This global dataset provides daily snow cover" gives HAS_MEASUREMENTS_OF "snow cover", HAS_TEMPORAL_RESOLUTION "daily", and HAS_SPATIAL_COVERAGE "global".

### 5.3 Limiting drafting bias

Since the ground truth starts as a model's draft, keeping a wrong drafted triple is easy and adding a fact the model missed is unlikely [7, 8]. The guidelines ask the person to read the record's text before its drafted triples. The drafting model comes from a different maker than the extraction model [9], and step 060 warns before paying when the two are the same model or come from the same maker. Every evaluation report states that the ground truth was drafted by a model and corrected by a person, not written from scratch.

### 5.4 Current state

The ground truth is one file, `annotations/ground_truth/batch_000.csv`, holding pool positions 0 to 5, annotated before step 050 existed. Positions 0 to 3 are finished and hold 43 ground truth triples; positions 4 and 5 are not finished. I annotated all six myself.

## 6. Evaluation design

### 6.1 Translation and pairing

The current schema and the ground truth schema are written independently, so one idea may have different names in each. Step 070 first translates each entity class and predicate of the current schema into the ground truth schema through a translation table. A model proposes rows for those without one, and a person checks every row before it is used. A row can also say that a predicate states the relation the other way round ("A CARRIES B" is "B ABOARD A"). A row must be checked again when either schema's definition of its entity class or predicate changes.

For each record, each translated extracted triple is then paired with at most one ground truth triple, and each ground truth triple with at most one translated extracted triple. An exact pair has the same predicate and the same subject and object instances, once case, spacing, quotes, dashes, edge punctuation, and a leading article are ignored. A partial pair has the same predicate, and its subject instances and its object instances are each equal or one contained in the other as whole words, as "MODIS" is in "Moderate Resolution Imaging Spectroradiometer (MODIS)". Exact pairs are chosen first, as the largest possible matching, and partial pairs only among what is left. A pair is strict when its subject and object entity classes also agree, as in the Strict criterion of [5]. Because partial pairing can join two different things, a person reviews the tuning part's partial pairs, and a pair marked "not the same fact" is never formed again.

### 6.2 Metrics

Counts are summed over all evaluated records of a part before dividing (micro-averaging [15]). Each record's describes triple is compared only on its describes class.

- Precision: the proportion of translated extracted triples that are in a pair.
- Recall: the proportion of ground truth triples that are in a pair.
- F1: the harmonic mean of precision and recall.
- Entity-class accuracy: the proportion of pairs that are strict, overall and by slot.
- Recall upper bound: the proportion of ground truth triples whose predicate some checked row of the translation table translates to, which is the most recall the current schema allows. Recall divided by it, recall within reach, measures extraction on what the schema can express. A low upper bound points at the schema; a high upper bound with low recall within reach points at extraction.
- Describes accuracy: how often extraction names a record's describes class correctly, next to what always naming the most common describes class would score.

Each is reported at the exact and partial levels, with and without the strict requirement, per part and per stratum.

### 6.3 Margin of error

Each metric has a 95% percentile interval from 1,000 bootstrap redraws of whole records with a fixed seed [10, 11]. Records are redrawn from all strata together, since the number of evaluated records per stratum is itself random in a prefix of the shuffled pool. No interval is given below 20 evaluated records, a rule of thumb. The report checks the interval's assumptions, such as whether one record holds most of the triples, and warns when the evaluated records' mix of strata differs from the pool's by more than 10 percentage points.

### 6.4 Tuning, held-out records, and twins

While the pipeline is being improved, step 070 shows only the tuning part's numbers. The held-out part's numbers are shown only on request, at the end, and every such look is logged in `annotations/held_out_looks.csv`, in Git. Changes are compared on tuning records only, one at a time, with the paired bootstrap [12] (`helpers/compare_runs.py`).

Two records can share text: a series of datasets often repeats the same `notes` under different titles. A pool record with the same title, the same `notes`, or both as a record the schema was learned from is a twin, and its numbers may flatter extraction. Counted on 2026-10-12, 21 pool records are twins of the 150 texts step 040 learns from. Step 070 reports each part's precision, recall, and F1 with and without the twins.

## 7. Current status

Table 2. Status of each step as of this draft.

| Step | Status |
|---|---|
| 010 harvest | Full harvest of 2026-10-01 (36,406 records), on the NASA laptop |
| 020 clean | Run on that harvest |
| 030 split | Run on 2026-10-12: 999 pool records, 35,407 induction candidates |
| 040 induce schema | Run with the real model on 2026-10-12 |
| 050 annotate | Tested with a stand-in model only |
| 060 extract | Tested with a stand-in model only |
| 070 evaluate | Tested on a hand-made extraction output whose 16 expected numbers were worked out in advance (all matched), and on synthetic records for the margins |
| 080 build graph | Not built |

The baseline schema comes from step 040's run of 2026-10-12 with `claude-opus-5.5` through LiteLLM on 150 texts. It found 2,767 verified triple instances and has 60 entity classes, 104 predicates, and 1,233 patterns. All extraction and evaluation experiments will use this file unchanged. Four further measurements come from step 040:

- Saturation. The last 25 of the 150 texts added an expected 0.01 entity classes, 2.8 predicates, and 158 patterns. For these ten maintainers, entity classes are saturated and predicates nearly so; patterns are still growing.
- Breadth. 49 of the 60 entity classes were found in the texts of three or more maintainers, while 1,067 of 1,264 counted patterns came from one maintainer only. (These counts precede the removal of vague entries.)
- Run-to-run variation. A run made just before the baseline, differing only by the rule on data tables, gave 63 entity classes and 126 predicates, of which only 41 and 67 were spelled the same in both runs, often one idea under two labels (FileFormat and DataFormat). The induced schema is not reproducible from run to run, so a change to step 040 can only be judged against repeated runs of one setup.
- Service behavior. The service's content filter withheld some labeling answers built from space-biology phrases; asked again in smaller batches, every batch was answered. Prompt caching through LiteLLM worked: 4 of 8 identical test requests read the cache.

A test suite runs in about 40 seconds without calling the model or the catalog and checks that each step does what its guide says.

The first end-to-end evaluation has not been run. It needs steps 050 and 060 to run with the real model, and at least 20 finished records in the tuning part for a margin of error; there are four. No precision, recall, or other evaluation number exists yet.

## 8. Limitations

- The ground truth is drafted by a model, corrected by one person, and small, so recall is likely overstated, and no agreement between annotators has been measured.
- The induced schema varies from run to run, and its minimum support has not been chosen; at 1, every pattern seen once enters it.
- Schema induction reads only the 10 largest maintainers. The other 412, holding 8.4% of the records, are never read, so an entity class or predicate used only there cannot enter the induced schema. The recall upper bound will show whether that matters.
- Partial pairing can join different things that share words ("MODIS" and "MODIS Terra"); review limits this on the tuning part. No pairing catches the same fact in different words ("the satellite" for "Aqua"), which understates precision and recall [6].
- A wrong row of the translation table looks like an extraction error, and two entity classes of the current schema that translate to one of the ground truth schema cannot be told apart.
- The margins of error cover sampling error only, not the model's run-to-run variation, mistakes in the ground truth, or tuning. The thresholds of 20 records and 10 percentage points have no published source.
- Twins are found only by identical titles or `notes` fields; near-identical texts are not measured.

## 9. Next steps

The next step is the first end-to-end run: drafting and correcting ground truth in pool order until the tuning part has at least 20 finished records, extracting them with the baseline schema, checking the translation table, reviewing the partial pairs, and evaluating the tuning part. That evaluation becomes the baseline every later change is compared with. The improvements list (`docs/improvements.md`) records the work after it, including:

- a setting that bypasses the answer cache, so one setup can be run several times and its noise measured before any difference is called an effect;
- experiments on step 040's sample and minimum support, and on leaving patterns out of the extraction prompt;
- about 10 records annotated from scratch, to measure how far drafting steers annotation, and a second annotator on a sample, to measure agreement [16];
- precision and recall per predicate and per entity class [17];
- for step 080, keeping each extracted triple apart from the graph built from it, so the graph can be rebuilt without asking a model again [17]; linking names to reference lists such as NASA's list of missions; and a set of questions the graph should answer;
- describing the catalog records with DCAT 3, the W3C vocabulary for data catalogs [18], once it is worked out what that would change.

The held-out part will be evaluated once, at the end, with the pipeline frozen, and that is the number this project will report.

## Acknowledgments

I thank my mentors, Jennifer Wei and Phillip Michael, for their guidance throughout this project.

## References

[1] N. Mihindukulasooriya, S. Tiwari, C. F. Enguix, and K. Lata, "Text2KGBench: A Benchmark for Ontology-Driven Knowledge Graph Generation from Text," in *The Semantic Web: ISWC 2023* (Resource Track), 2023. arXiv:2308.02357. https://arxiv.org/abs/2308.02357

[2] B. Zhang and H. Soh, "Extract, Define, Canonicalize: An LLM-based Framework for Knowledge Graph Construction," in *Proceedings of the 2024 Conference on Empirical Methods in Natural Language Processing (EMNLP)*, 2024. arXiv:2404.03868. https://arxiv.org/abs/2404.03868

[3] J. Bai, W. Fan, Q. Hu, et al., "AutoSchemaKG: Autonomous Knowledge Graph Construction through Dynamic Schema Induction from Web-Scale Corpora," arXiv:2505.23628, 2025. https://arxiv.org/abs/2505.23628

[4] T. Castro Ferreira, C. Gardent, N. Ilinykh, C. van der Lee, S. Mille, D. Moussallem, and A. Shimorina, "The 2020 Bilingual, Bi-Directional WebNLG+ Shared Task: Overview and Evaluation Results (WebNLG+ 2020)," in *Proceedings of the 3rd International Workshop on Natural Language Generation from the Semantic Web (WebNLG+)*, pp. 55–76, 2020. https://aclanthology.org/2020.webnlg-1.7/

[5] B. Taillé, V. Guigue, G. Scoutheeten, and P. Gallinari, "Let's Stop Incorrect Comparisons in End-to-end Relation Extraction!," in *Proceedings of EMNLP 2020*, pp. 3689–3701, 2020. doi:10.18653/v1/2020.emnlp-main.301

[6] S. Wadhwa, S. Amir, and B. C. Wallace, "Revisiting Relation Extraction in the era of Large Language Models," in *Proceedings of the 61st Annual Meeting of the Association for Computational Linguistics (ACL)*, pp. 15566–15589, 2023. https://aclanthology.org/2023.acl-long.868/

[7] K. Fort and B. Sagot, "Influence of Pre-annotation on POS-tagged Corpus Development," in *Proceedings of the Fourth Linguistic Annotation Workshop (LAW IV)*, pp. 56–63, 2010. https://aclanthology.org/W10-1807/

[8] H. Schroeder, D. Roy, and J. Kabbara, "Just Put a Human in the Loop? Investigating LLM-Assisted Annotation for Subjective Tasks," in *Findings of the Association for Computational Linguistics: ACL 2025*, pp. 25771–25795, 2025. https://aclanthology.org/2025.findings-acl.1323/

[9] E. Kim, A. Garg, K. Peng, and N. Garg, "Correlated Errors in Large Language Models," in *Proceedings of the 42nd International Conference on Machine Learning (ICML)*, PMLR 267, pp. 30038–30066, 2025. https://proceedings.mlr.press/v267/kim25e.html

[10] B. Efron and R. J. Tibshirani, *An Introduction to the Bootstrap*. Chapman & Hall, 1993.

[11] A. C. Davison and D. V. Hinkley, *Bootstrap Methods and their Application*. Cambridge University Press, 1997.

[12] P. Koehn, "Statistical Significance Tests for Machine Translation Evaluation," in *Proceedings of EMNLP 2004*, pp. 388–395, 2004. https://aclanthology.org/W04-3250/

[13] T. Hastie, R. Tibshirani, and J. Friedman, *The Elements of Statistical Learning*, 2nd ed., section 7.2. Springer, 2009.

[14] N. J. Gotelli and R. K. Colwell, "Estimating species richness," in A. E. Magurran and B. J. McGill (eds.), *Biological Diversity: Frontiers in Measurement and Assessment*, ch. 4. Oxford University Press, 2011.

[15] C. D. Manning, P. Raghavan, and H. Schütze, *Introduction to Information Retrieval*, sections 8.3 and 13.6. Cambridge University Press, 2008. https://nlp.stanford.edu/IR-book/

[16] G. Hripcsak and A. S. Rothschild, "Agreement, the F-Measure, and Reliability in Information Retrieval," *Journal of the American Medical Informatics Association*, 12(3):296–298, 2005. doi:10.1197/jamia.M1733

[17] A. Negro, G. Futia, V. Kůs, and F. Montagna, *Knowledge Graphs and LLMs in Action*. Manning, 2026.

[18] R. Albertoni, D. Browning, S. Cox, A. Gonzalez Beltran, A. Perego, and P. Winstanley (eds.), "Data Catalog Vocabulary (DCAT) - Version 3," W3C Recommendation, 22 August 2024. https://www.w3.org/TR/2024/REC-vocab-dcat-3-20240822/
