# Left out on purpose

Statements of a [record](../docs/terminology.md#1-records-and-their-text)'s [text](../docs/terminology.md#1-records-and-their-text) that have no [ground truth triple](../docs/terminology.md#4-ground-truth-and-samples), because I decided so or a rule of the [annotation guidelines](guidelines.md) says so. It is the one place where I keep them, so that what the [ground truth](../docs/terminology.md#4-ground-truth-and-samples) leaves out is not lost: some of these words carry information I may want back once an expert answers a question, or once the schema can say it. Terms: [docs/terminology.md](../docs/terminology.md).

One section per record I have annotated, in [pool](../docs/terminology.md#4-ground-truth-and-samples) order. Each item has the exact words (quoted from the record's text, as in `outputs/intermediate_results/020_clean/records.jsonl`), the rule that excluded them (quoted from `guidelines.md`), a *May matter because* line when the words carry information worth keeping, and the question in `questions_for_experts.md` that asks about it, if there is one. Left out here is not the same as wrong: a statement written in other words, or as part of a bigger ground truth triple, is not listed. Nor is a record's "is a data set" (the [describes class](../docs/terminology.md#2-triples) says it). When I annotate a record, I add its section; when an expert's answer brings a statement back as a ground truth triple, I delete its item.

## "NASA Standards and and Technical Assistance Resource Tool" (pool position 0, id 3122be4c-b9d0-4cc9-b6d3-9b96c6e743da)

2 items, none that may matter.

- **Left out:** "is a Web tool" (notes)
  - **Rule:** What counts as a fact, rule 4: "says what type of thing MODIS is: that belongs in its entity class"
  - A Web tool is what the thing is; its entity class WebTool already says it.
- **Left out:** "great" (notes, "access great NASA technical information")
  - **Rule:** What counts as a fact, rule 5: "Leave out words such as "great"."
  - My ground truth triple of the purpose is written without it.

## "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (pool position 1, id cfd6ec3f-1e63-4a77-bc3f-007d45f7e2fc)

3 items, 2 that may matter.

- **Left out:** "1/2/3" (title)
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or acronym stands for"
  - **May matter because:** I read it as processing levels of a Planetary Data System scale, but the record does not say so; if it is, the dataset has three processing levels, and a search by level would find it.
  - **Question:** Q6 (b).
- **Left out:** "1149" (title)
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or acronym stands for"
  - **May matter because:** I do not know what it stands for; if it is a standard slot of such a title (an observation or sequence number), it identifies this dataset among its siblings.
  - **Question:** Q6 (b).
- **Left out:** "comet" (notes, "at the comet 67P")
  - **Rule:** Writing a classed triple, rule 13: "Leave out a type word that only describes the thing,"
  - My ground truth triple has the target "67P".

## "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" (pool position 2, id 6cfafd07-40f1-46da-9d92-36c2bb319f0b)

2 items, none that may matter. The record has no list of other time steps or resolutions of its product ("daily" is its own, in "provides daily snow cover"), so nothing of a product family is left out here.

- **Left out:** "satellite" (notes, "the Aqua satellite")
  - **Rule:** Writing a classed triple, rule 13: "write "Aqua", not "Aqua satellite", since its entity class already says it's a satellite"
- **Left out:** "Each data granule contains" (notes), that the data come in granules
  - **Rule:** Writing a classed triple, rule 6: "Each fact once, even if the record states it twice or in other words."
  - My ground truth triple HAS_GRANULE_DURATION "5 minutes" already says each granule covers 5 minutes, which only makes sense if the data come in granules.

## "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005" (pool position 3, id 2705e0d1-95e7-4588-813b-ca91a6da94ff)

4 items, 2 that may matter.

- **Left out:** "retrievals" (notes, "Sea Surface Salinity (SSS) retrievals")
  - **Rule:** Writing a classed triple, rule 14: "Write each only if the record names both of its parts." My reading: "retrievals" says a processing step made the values, but the record names neither its method nor its input, so no triple of a step; the object is "Sea Surface Salinity (SSS)".
  - **May matter because:** it says the salinity values are computed from what the instrument measured, not measured directly.
  - **Question:** Q3 (what is measured, and what is computed).
- **Left out:** "Polar" as a fact of its own (title, "Polar-Gridded")
  - **Rule:** Writing a classed triple, rule 6: "one ground truth triple, with "Polar-Gridded""; the word stays whole in the spatial representation.
  - **May matter because:** "Polar" may name the grid used (a fact about which grid), or the area the data cover (the poles); I wrote neither.
  - **Question:** Q1 (c), and Q11 for the area.
- **Left out:** "collaboratively" (notes, "developed collaboratively between")
  - **Rule:** none to quote. The two developers are already ground truth triples (DEVELOPED_BY_PARTY: NASA and CONAE), and a query returns both; "collaboratively" adds only that they worked together, which no predicate of the ground truth schema expresses. Not worth a new predicate now. I decided this on 2026-10-25.
- **Left out:** "space agency" (notes, "Argentina's space agency")
  - **Rule:** What counts as a fact, rule 4: "says what type of thing MODIS is: that belongs in its entity class"; "Argentina's" is its own ground truth triple (BASED_IN). I decided this on 2026-10-25.
  - **Question:** Q8 (roles).

## "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (pool position 4, id 03a09af3-081e-4db6-9e3b-ea7c0e3138bd)

The dense record: its notes describe a whole family of products (several time steps, two resolutions, day and night, two kinds of temperature) and the title names the one this record is. 12 items, 7 that may matter. The product family as a whole is asked in Q24.

- **Left out:** "Day" (notes, "Day and night spatially gridded (L3) global NASA skin sea surface temperature (SST) products")
  - **Rule:** Writing a classed triple, rule 11: "a fact about another dataset, even a closely related one, such as the same data at another time step or resolution. That dataset has its own record, and its facts go there." The title says "Nighttime", so the dataset is the night one; the day products are the family's.
  - **May matter because:** it says daytime products exist.
  - **Question:** Q24.
- **Left out:** "daily", "monthly" and "annual" (notes, "Average daily, weekly (8 day), monthly and annual skin SST products")
  - **Rule:** Writing a classed triple, rule 11: "a fact about another dataset, even a closely related one, such as the same data at another time step or resolution. That dataset has its own record, and its facts go there." Only "weekly (8 day)" is this dataset's (its title says "8 Day").
  - **May matter because:** they describe the product family: which time steps of this product exist.
  - **Question:** Q24.
- **Left out:** "9.26 km" (notes, "available at both 4.63 and 9.26 km spatial resolution")
  - **Rule:** Writing a classed triple, rule 11: "a fact about another dataset, even a closely related one, such as the same data at another time step or resolution. That dataset has its own record, and its facts go there." Only "4.63 km" is this dataset's.
  - **May matter because:** it is the other resolution of the product family.
  - **Question:** Q24; whether the title's "4km" is the 4.63 km: Q22.
- **Left out:** "Average" (notes, "Average daily, weekly (8 day), monthly and annual skin SST products")
  - **Rule:** Writing a classed triple, rule 11, as for the list it belongs to.
  - **May matter because:** it says the products are averages over their time step, so the 8 days are the time each value averages over.
  - **Question:** Q5 (b), and Q24.
- **Left out:** "can be present" (notes, "Two SST products can be present in these files"), and with it the dataset's variable NSST
  - **Rule:** What counts as a fact, rule 7: "the record doesn't state that it does. The same for "might", "possibly", "is expected to"" (I read "can be present" as the same kind). My ground truth triple has the variable SST4 only, from the title's "SST MID-IR".
  - **May matter because:** if the files hold both, the dataset has two variables, not one.
  - **Question:** Q18.
- **Left out:** "binned" and "mapped" as methods (notes, "the L2 pixels are binned into an integerized sinusoidal area grid (ISEAG) and mapped into an equidistant cylindrical")
  - **Rule:** Writing a classed triple, rule 14: "Write each only if the record names both of its parts." The record names the grid and the projection but only says the pixels "are binned" and "mapped", so I wrote BINNED_INTO and MAPPED_INTO and no PRODUCED_USING_ALGORITHM.
  - **May matter because:** it is how the dataset was made, step by step.
  - **Question:** Q7.
- **Left out:** "NASA" (notes, "global NASA skin sea surface temperature (SST) products")
  - **Rule:** none needed: "NASA" qualifies the products, not the quantity; the producer is the ground truth triple from "generated by the NASA Ocean Biology Processing Group (OBPG)".
- **Left out:** "with other Earth Observation Satellites (EOS)" (notes)
  - **Rule:** none that I can quote: the words name no satellite, so there is no specific thing for a triple; "A-train" is the ground truth triple (FLIES_IN).
  - **Question:** Q23.
- **Left out:** "at a variety of spatial resolutions" (notes, "MODIS captures data in 36 spectral bands at a variety of spatial resolutions")
  - **Rule:** none that I can quote: the words name no value. What counts as a fact, rule 1: "Only what the record states."
- **Left out:** "projection" (notes, "Platte Carre projection")
  - **Rule:** Writing a classed triple, rule 13: "Leave out a type word that only describes the thing,"
  - **Question:** Q15.
- **Left out:** "satellite" (notes, "the Aqua satellite")
  - **Rule:** Writing a classed triple, rule 13: "write "Aqua", not "Aqua satellite", since its entity class already says it's a satellite"
- **Left out:** "which can be found at https://doi.org/10.5067/MODAM-8D4N4" (notes), the DOI of the previous v2014.1 datasets
  - **Rule:** Writing a classed triple, rule 11: "a fact about another dataset, even a closely related one, such as the same data at another time step or resolution. That dataset has its own record, and its facts go there." The DOI is the address of the older datasets, not of this one; the ground truth triple has only "V2019.0" SUPERSEDES "v2014.1".
  - **May matter because:** it is where the superseded release is.
  - **Question:** Q19, and Q24 (the releases of a product family).

## "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0" (pool position 5, id 99dff022-24ac-48cb-bc83-09fec8b90ad7)

1 item, 1 that may matter.

- **Left out:** "detrended" as a method (notes, "The nominal fast neutron count rates were detrended using the GRaND epithermal neutron map")
  - **Rule:** Writing a classed triple, rule 14: "Write each only if the record names both of its parts." The record says the rates "were detrended", only a verb; I wrote the two COMPUTED_FROM triples (the rates, the epithermal map) and no PRODUCED_USING_ALGORITHM.
  - **May matter because:** it is the method that made the residual map.
  - **Question:** Q7 (settled for now, not asked), Q12 (c) for the map as an input.

## "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (pool position 6, id 4c64f3ed-39b4-4f95-95a0-022898ba47a4)

5 items, all 5 that may matter. The record's decisions are complete (its ground truth triples are in `annotations/ground_truth/batch_001.csv`, a demo batch): these items are the ones I decided or am waiting on.

- **Left out:** "Near Real Time (NRT)" (notes)
  - **Rule:** none yet: pending an expert. What counts as a fact, rule 1 ("Only what the record states") does not tell whether it is a latency, a separate processing stream or a version, and the ground truth schema has no predicate for a latency.
  - **May matter because:** NRT products are made available within hours of the observation, so they are different from the standard product; I checked this, the record says no number of hours.
  - **Question:** Q20 (a); the pending fact is listed there.
- **Left out:** "Global" as an area the data cover (title, "Global 1km SIN Grid")
  - **Rule:** Writing a classed triple, rule 9: "if taking it out would give a triple that isn't true". Written alone, "Global" would claim the data cover the ocean too; the data cover "Land" (my ground truth triple). Checked: "Global" in the title belongs to the grid's name.
  - **May matter because:** the grid tiles the whole globe.
  - **Question:** Q11, Q1 (c).
- **Left out:** "SIN Grid" (title, "Global 1km SIN Grid"), the grid as a fact of its own
  - **Rule:** none yet: pending an expert. It would be a BINNED_INTO triple with a Grid, as in the record at pool position 4.
  - **May matter because:** the MODIS sinusoidal grid is the layout of the data (checked at NASA LAADS and MODAPS).
  - **Question:** Q1 (c); the pending fact is listed there.
- **Left out:** "used to calculate the MAIAC Land Surface Bidirectional Reflectance Factor (BRF) or surface reflectance, MCD19A1N product" (notes), that the product MCD19A1N is computed from this dataset
  - **Rule:** Writing a classed triple, rule 11: "a fact about another dataset, even a closely related one, such as the same data at another time step or resolution. That dataset has its own record, and its facts go there." The subject would be the other product. I decided this on 2026-10-25.
  - **May matter because:** it says which product this dataset feeds and what that product holds (a surface reflectance).
  - **Question:** Q20 (c); the pending fact is listed there.
- **Left out:** the same words as a purpose of this dataset ("calculate the MAIAC Land Surface Bidirectional Reflectance Factor (BRF) or surface reflectance")
  - **Rule:** none to quote: the ground truth schema's Purpose is "an aim something is meant to achieve", and the record says "used to calculate", not that the dataset is meant for it. I decided this on 2026-10-25.
  - **May matter because:** it is what the dataset is for.
  - **Question:** Q9 ("used to").

## "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" (pool position 7, id d5477563-0415-4e65-ab7c-d4bc9ed809e5)

15 items, 8 that may matter.

- **Left out:** "Global" as an area the data cover (title, "Global 1km SIN Grid")
  - **Rule:** Writing a classed triple, rule 9: "A qualifier stays in the instance, as written, if it is any other kind". "Global 1km SIN Grid" is the standard end of the titles of the MODIS products made on the MODIS sinusoidal grid (checked for the record at pool position 6), so "Global" belongs to the grid's name, not to an area.
  - **May matter because:** the grid tiles the whole globe.
  - **Question:** Q1 (c), Q11.
- **Left out:** "SIN Grid" (title, "Global 1km SIN Grid"), the grid as a fact of its own
  - **Rule:** none yet: pending an expert, as for the record at pool position 6.
  - **May matter because:** the MODIS sinusoidal grid is the layout of the data.
  - **Question:** Q1 (c); the pending fact is listed there.
- **Left out:** "in a 1,200 by 1,200 km grid" (notes)
  - **Rule:** none yet: pending an expert. It is a fact about the grid the data are laid on (its size), the same decision as "SIN Grid".
  - **May matter because:** my reading, not checked against a source: it is the size of one tile of the MODIS sinusoidal grid, which may be how much ground each file covers.
  - **Question:** Q1 (c); the pending fact is listed there.
- **Left out:** "per-pixel" (notes, "provides daily per-pixel Land Surface Temperature")
  - **Rule:** Writing a classed triple, rule 6: "Each fact once, even if the record states it twice or in other words." The ground truth triple HAS_SPATIAL_RESOLUTION "1 kilometer (km)" already says how much ground each value covers.
- **Left out:** "(LST&E)" (notes, "Land Surface Temperature and Emissivity (LST&E)")
  - **Rule:** Writing a classed triple, rule 12: "A list joined by "and": one ground truth triple per item, when each item alone is a complete object." The abbreviation names the pair, so it belongs to neither item after the split.
- **Left out:** "https://doi.org/10.5067/MODIS/MOD11A1.061" (notes, the address in "[MOD11A1 Version 6.1](https://doi.org/10.5067/MODIS/MOD11A1.061)"), the DOI of Version 6.1
  - **Rule:** Writing a classed triple, rule 11: "a fact about another dataset, even a closely related one, such as the same data at another time step or resolution. That dataset has its own record, and its facts go there." The ground truth triple has only "Version 6.1" SUPERSEDES "Version 6".
  - **May matter because:** it is where the newer release is.
  - **Question:** Q19, and Q24 (the releases of a product family).
- **Left out:** "Above 30 degrees latitude, some pixels may have multiple observations where the criteria for clear-sky are met." (notes)
  - **Rule:** What counts as a fact, rule 7: "the record doesn't state that it does. The same for "might", "possibly", "is expected to""
  - **May matter because:** it says where several observations go into one value.
- **Left out:** "When this occurs, the pixel value is a result of the average of all qualifying observations." (notes), the averaging as a method
  - **Rule:** What counts as a fact, rule 7: "the record doesn't state that it does. The same for "might", "possibly", "is expected to"". The averaging happens only "When this occurs", that is, where pixels "may have multiple observations", so I wrote no PRODUCED_USING_ALGORITHM "average".
  - **May matter because:** it is how a value is made from several observations.
  - **Question:** Q7.
- **Left out:** "surface temperature bands" as a thing of its own (notes, "the daytime and nighttime surface temperature bands")
  - **Rule:** Writing a classed triple, rule 6: "Each fact once, even if the record states it twice or in other words." "surface temperature" is the "Land Surface Temperature" already written (rule 13: the wording that says more); "bands" is a type word (rule 13: "Leave out a type word that only describes the thing,"). "daytime" and "nighttime" are ground truth triples of their own (OBSERVED_AT_TIME_OF_DAY, rule 9).
- **Left out:** "associated" (notes, "associated quality control assessments")
  - **Rule:** none to quote: it says only that the assessments go with the temperature bands.
- **Left out:** "Known Issues" (notes, the heading)
  - **Rule:** What counts as a fact, rule 3: "the names are formatting, not facts" (a heading, like a field name).
- **Left out:** the other products in "Production of V6 Terra MODIS Land Surface Temperature and Emissivity (LST&E) data products was discontinued" (notes)
  - **Rule:** Writing a classed triple, rule 11: "a fact about another dataset, even a closely related one, such as the same data at another time step or resolution. That dataset has its own record, and its facts go there." The sentence is about every Version 6 Terra MODIS land surface temperature and emissivity product; I wrote its two facts for this dataset only (PRODUCTION_DISCONTINUED_ON, PRODUCTION_DISCONTINUED_DUE_TO).
  - **May matter because:** the date and its cause hold for the whole family of these products.
  - **Question:** Q24.
- **Left out:** "known issues" as what the page is about (notes, "For complete information about known issues please refer to")
  - **Rule:** none to quote: DOCUMENTED_AT ("more details about it are written at") says only that the page has more about the dataset.
  - **May matter because:** a search for a dataset's known issues would need it.
- **Left out:** "website" (notes, "MODIS/VIIRS Land Quality Assessment website")
  - **Rule:** Writing a classed triple, rule 13: "Leave out a type word that only describes the thing,"
- **Left out:** "product" (notes, "[MOD11_L2](https://doi.org/10.5067/MODIS/MOD11_L2.006) swath product")
  - **Rule:** Writing a classed triple, rule 13: "Leave out a type word that only describes the thing,"; "swath" is a ground truth triple of its own (HAS_SPATIAL_REPRESENTATION, as "gridded" for the record at pool position 6).

## "STARDUST 9P/TEMPEL 1 DFMI 2/3 NEXT V1.0" (pool position 9, id dc4ff01b-12f0-4235-8c8a-afb4bfb3bdbb)

3 items, 1 that may matter.

- **Left out:** "comet" (notes, "encounter with comet 9P/Tempel 1" and "the entire comet encounter")
  - **Rule:** Writing a classed triple, rule 13: "Leave out a type word that only describes the thing,"
  - My ground truth triple has the target "9P/Tempel 1", and the phase "encounter".
- **Left out:** "convert" as a method (notes, "The RDR data convert the EDR (raw) sensor data")
  - **Rule:** Writing a classed triple, rule 14: "Write each only if the record names both of its parts." The record says the RDR data "convert" the EDR data, only a verb; I wrote "RDR data" COMPUTED_FROM "EDR (raw) sensor data" and no PRODUCED_USING_ALGORITHM.
  - **May matter because:** it is how the RDR data are made from the raw data.
  - **Question:** Q7.
- **Left out:** "entire" (notes, "from the entire comet encounter")
  - **Rule:** none to quote: HAS_MISSION_PHASE "encounter" says the RDR data come from the encounter; "entire" adds only that none of it is left out.

## "ROSETTA-ORBITER 67P/CAL ALICE 2 ESC1 V1.0" (pool position 10, id 3bceffb4-f01e-433c-af79-42b9d9427231)

2 items, 1 that may matter.

- **Left out:** "CAL" (title, "67P/CAL")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or acronym stands for"
  - **May matter because:** my reading, not checked against a source: it may mark calibration data; if so, it says what kind of data the dataset holds.
  - **Question:** Q6 (b).
- **Left out:** "mission phase" (notes, "comet escort 1 mission phase")
  - **Rule:** Writing a classed triple, rule 13: "Leave out a type word that only describes the thing,"
  - My ground truth triple has the phase "comet escort 1", its target "67P/Churyumov-Gerasimenko" a triple of its own (rule 9).

## "Ensemble X-Ray Variability of AGN in 2XMMi-DR3" (pool position 12, id bb1fe4b0-6543-42e3-9386-acbab0b37ad4)

The notes are mostly the abstract of the study the table comes from; whether a study's aim, method and findings belong in the ground truth is asked in Q26, and until it is answered they are left out (decision of 2026-10-25). 28 items, 15 that may matter.

- **Left out:** "The X-ray variability of active galactic nuclei (AGN) has been most often investigated with studies of individual, nearby sources, and only a few ensemble analyses have been applied to large samples in wide ranges of luminosity and redshift." (notes)
  - **Rule:** none to quote: it is background about earlier studies in general, naming no study, dataset or other specific thing for a triple.
  - **May matter because:** it says why the study was made.
  - **Question:** Q26.
- **Left out:** "and Swift (the latter is not included in this table, notice)" (notes), the study's second sample
  - **Rule:** What counts as a fact, rule 6: "A ground truth triple can't say "not"." The Swift sample is another dataset, too (Writing a classed triple, rule 11: "That dataset has its own record, and its facts go there.").
  - **May matter because:** the study's findings are about both samples.
  - **Question:** Q26 (c).
- **Left out:** "serendipitously selected" (notes)
  - **Rule:** none to quote: the selection is my ground truth triple COMPUTED_FROM "2XMMi-DR3".
- **Left out:** "which operates in the time domain" (notes, about the structure function)
  - **Rule:** What counts as a fact, rule 4: "says what type of thing MODIS is: that belongs in its entity class" (it says what kind of method it is).
- **Left out:** "The SF is also more appropriate than fractional variability and excess variance, because these parameters are biased by the duration of the monitoring time interval in the rest-frame, and therefore by cosmological time dilation." (notes)
  - **Rule:** What counts as a fact, rule 5: "Leave out words such as "great"." ("more appropriate" is the authors' judgement); the biases are about two measures the dataset doesn't use.
  - **May matter because:** it says why the method was chosen.
  - **Question:** Q26.
- **Left out:** "They do not find evidence of the break in the SF, at variance with the case of lower luminosity AGNs." (notes)
  - **Rule:** What counts as a fact, rule 6: "A ground truth triple can't say "not"."
- **Left out:** "then available" and "latest" (notes, "the version of the Serendipitous Source Catalog then available" and "the latest incremental update")
  - **Rule:** none to quote: they say what was so when the study was made, not a lasting fact.
- **Left out:** "all datasets were publicly available by 2009 October 31" (notes)
  - **Rule:** none to quote: it is about the observations the catalog was made from, which the record doesn't name, so there is no subject for a triple.
  - **May matter because:** it dates the data the catalog holds.
- **Left out:** "but not all public observations are included in this catalog" (notes)
  - **Rule:** What counts as a fact, rule 6: "A ground truth triple can't say "not"."
- **Left out:** "taking account of the substantial overlaps between observations" (notes)
  - **Rule:** none to quote: it only explains why the total area of the catalog's fields ("~ 814 deg^2", left out below) is larger than my ground truth triple HAS_SKY_AREA "~ 504 deg^2".
- **Left out:** "therefore a significant number of sources (41,979) have more than one record within the catalog" (notes)
  - **Rule:** none to quote: HAS_NUMBER_OF holds a number of things, and "sources with more than one record" isn't a thing the record names; "significant" is a judgement (What counts as a fact, rule 5: "Leave out words such as "great".").
  - **May matter because:** it says how many sources the catalog has detected more than once.
- **Left out:** "corresponding to the uncertainty in the X-ray positions" (notes)
  - **Rule:** none to quote: it is why the distance was chosen; it gives the uncertainty no value of its own (the matching distance itself is left out, below).
  - **May matter because:** it says how precise the X-ray positions are.
- **Left out:** "cross-correlated" as a method (notes, "The selected sources were cross-correlated with the DR7 edition of the SDSS Quasar Catalog")
  - **Rule:** Writing a classed triple, rule 14: "Write each only if the record names both of its parts." Only a verb; I wrote COMPUTED_FROM "DR7 edition of the SDSS Quasar Catalog" and no PRODUCED_USING_ALGORITHM.
  - **Question:** Q7.
- **Left out:** "This is a service" (notes, "This is a service provided by NASA HEASARC")
  - **Rule:** What counts as a fact, rule 4: "says what type of thing MODIS is: that belongs in its entity class"; who made the table is my ground truth triple DEVELOPED_BY_PARTY "NASA HEASARC".
- **Left out:** "the authors" HAS_PURPOSE "determine the ensemble variability properties of two serendipitously selected AGN samples" (notes, "In their study, the authors aimed to determine the ensemble variability properties of two serendipitously selected AGN samples")
  - **Rule:** none to quote: whether a study's aim, method and findings are facts of the ground truth is the owner's decision of 2026-10-25, pending the experts' answer (Q26).
  - **May matter because:** it says what the study set out to find.
  - **Question:** Q26.
- **Left out:** "the authors" USED_METHOD "structure function (SF)" (notes, "They used the structure function (SF)")
  - **Rule:** none to quote: whether a study's aim, method and findings are facts of the ground truth is the owner's decision of 2026-10-25, pending the experts' answer (Q26).
  - **May matter because:** it says how the study's results were obtained.
  - **Question:** Q26.
- **Left out:** "structure function (SF)" HAS_PURPOSE "ensemble analysis even when only a few observations are available for individual sources and the power spectral density (PSD) cannot be derived" (notes, "allows for an ensemble analysis even when only a few observations are available for individual sources and the power spectral density (PSD) cannot be derived")
  - **Rule:** none to quote: whether a study's aim, method and findings are facts of the ground truth is the owner's decision of 2026-10-25, pending the experts' answer (Q26). It is also what a method "allows for", asked in Q9 (d).
  - **May matter because:** it says why the method was used.
  - **Question:** Q26.
- **Left out:** "the authors" REPORTED "statistically consistent results for the two samples" (Finding) (notes, "The authors find statistically consistent results for the two samples")
  - **Rule:** none to quote: whether a study's aim, method and findings are facts of the ground truth is the owner's decision of 2026-10-25, pending the experts' answer (Q26).
  - **May matter because:** it is a result of the study the table comes from.
  - **Question:** Q26.
- **Left out:** "the authors" REPORTED "SF described by a power law of the time lag tau, approximately as SF ~ tau^0.1" (Finding) (notes, "with the SF described by a power law of the time lag tau, approximately as SF ~ tau^0.1")
  - **Rule:** none to quote: whether a study's aim, method and findings are facts of the ground truth is the owner's decision of 2026-10-25, pending the experts' answer (Q26).
  - **May matter because:** it is a result of the study the table comes from.
  - **Question:** Q26.
- **Left out:** "the authors" REPORTED "strong anti-correlation of the variability with X-ray luminosity, accompanied by a change of the slope of the SF" (Finding) (notes, "They confirm a strong anti-correlation of the variability with X-ray luminosity, accompanied by a change of the slope of the SF")
  - **Rule:** none to quote: whether a study's aim, method and findings are facts of the ground truth is the owner's decision of 2026-10-25, pending the experts' answer (Q26).
  - **May matter because:** it is a result of the study the table comes from.
  - **Question:** Q26.
- **Left out:** "the authors" REPORTED "evidence in support of a weak, intrinsic, average increase of X-ray variability with redshift" (Finding) (notes, "They also find evidence in support of a weak, intrinsic, average increase of X-ray variability with redshift")
  - **Rule:** none to quote: whether a study's aim, method and findings are facts of the ground truth is the owner's decision of 2026-10-25, pending the experts' answer (Q26).
  - **May matter because:** it is a result of the study the table comes from.
  - **Question:** Q26.
- **Left out:** "Ensemble X-Ray Variability of AGN in 2XMMi-DR3" DEVELOPED_BY_PARTY "the authors" (notes, "The authors used a maximum distance of 1.5 arcseconds")
  - **Rule:** none to quote: whether a study's aim, method and findings are facts of the ground truth is the owner's decision of 2026-10-25, pending the experts' answer (Q26). The table's developer is the HEASARC ("This table was created by the HEASARC"); the authors made the selection described in the study.
  - **May matter because:** it says who selected the table's sources.
  - **Question:** Q26.
- **Left out:** "Ensemble X-Ray Variability of AGN in 2XMMi-DR3" HAS_MATCHING_DISTANCE "1.5 arcseconds" (notes, "The authors used a maximum distance of 1.5 arcseconds")
  - **Rule:** none to quote: the maximum distance is a detail of the study's method, so it goes with the method (decision of 2026-10-25, with the study's method, Q26).
  - **May matter because:** it says how the sources of the table were matched with the quasar catalog.
  - **Question:** Q26.
- **Left out:** "2XMMi-DR3" VERSION_OF "Serendipitous Source Catalog" (notes, "the version of the Serendipitous Source Catalog then available, namely 2XMMi-DR3")
  - **Rule:** Writing a classed triple, rule 11: "a fact about another dataset, even a closely related one, such as the same data at another time step or resolution. That dataset has its own record, and its facts go there." The subject is the catalog, not the table.
- **Left out:** "2XMMi-DR3" UPDATE_OF "second version of the catalogue" (notes, "2XMMi-DR3, the latest incremental update of the second version of the catalogue")
  - **Rule:** Writing a classed triple, rule 11: "a fact about another dataset, even a closely related one, such as the same data at another time step or resolution. That dataset has its own record, and its facts go there." The subject is the catalog, not the table.
- **Left out:** "2XMMi-DR3" HAS_TOTAL_FIELD_AREA "~ 814 deg^2" (notes, "The total area of the catalog fields is ~ 814 deg^2")
  - **Rule:** Writing a classed triple, rule 11: "a fact about another dataset, even a closely related one, such as the same data at another time step or resolution. That dataset has its own record, and its facts go there." It also counts the overlapping fields each time, so it states the same area as HAS_SKY_AREA "~ 504 deg^2" a second time.
- **Left out:** "Ensemble X-Ray Variability of AGN in 2XMMi-DR3" ALSO_KNOWN_AS "XMM-Newton sample" (notes, "The authors refer to these sources as the XMM-Newton sample")
  - **Rule:** none to quote: "XMM-Newton sample" names the sources the table holds, not the table.
- **Left out:** "Ensemble X-Ray Variability of AGN in 2XMMi-DR3" PROVIDED_BY_PARTY "NASA HEASARC" (notes, "This is a service provided by NASA HEASARC")
  - **Rule:** What counts as a fact, rule 4: "says what type of thing MODIS is: that belongs in its entity class"; who provides the service adds nothing beyond my ground truth triple DEVELOPED_BY_PARTY "NASA HEASARC".

## "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0" (pool position 13, id ab33f184-95f4-4f33-8f3d-c4a09ec525d3)

10 items, 7 that may matter.

- **Left out:** "MTP020" (title, "ESC3-MTP020")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or acronym stands for"
  - **May matter because:** my reading, not checked against a source: it may name a planning period within the phase COMET ESCORT 3, which would tell this dataset from its siblings.
  - **Question:** Q6 (b).
- **Left out:** "RDR" (title, "RDR-INFLDSTR")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or acronym stands for"
  - **May matter because:** another record explains it as "Level 3 (RDR)"; this one doesn't, and its level is "CODMAC level 4".
  - **Question:** Q6 (b).
- **Left out:** "prime" (notes, "The prime target is comet 67P/Churyumov-Gerasimenko 1 (1969 R1)")
  - **Rule:** none to quote: HAS_TARGET says the dataset is about the comet; "prime" adds that it is the main target, so other bodies may be in the images.
  - **May matter because:** a search for other bodies in these images would need it.
- **Left out:** "comet" (notes, "comet 67P/Churyumov-Gerasimenko 1 (1969 R1)")
  - **Rule:** Writing a classed triple, rule 13: "Leave out a type word that only describes the thing,"
- **Left out:** "spacecraft" and "mission phase" (notes, "the Rosetta spacecraft" and "the COMET ESCORT 3 mission phase")
  - **Rule:** Writing a classed triple, rule 13: "Leave out a type word that only describes the thing,"; "the Rosetta spacecraft" is written as "ROSETTA-ORBITER", the wording that says more (rule 13).
  - **Question:** Q2 (b).
- **Left out:** "Lien" (notes, "Lien corrected dataset after September 2019 PSA/PDS external peer review")
  - **Rule:** none to quote: my ground truth triple REVISED_AFTER "September 2019 PSA/PDS external peer review" says the dataset was corrected after the review; "Lien" names what was corrected, the issues the review raised.
- **Left out:** PRODUCED_USING_ALGORITHM "solar stray-light corrected" (notes, "contains solar stray-light corrected, in-field stray-light corrected, radiometric calibrated and geometric distortion corrected (resampled) image data")
  - **Rule:** Writing a classed triple, rule 14: "Write each only if the record names both of its parts." "solar stray-light corrected" describes the data; it is not the name of a method (as for "detrended" in the record at pool position 5).
  - **May matter because:** it says which corrections were applied to the images.
  - **Question:** Q7 (e).
- **Left out:** PRODUCED_USING_ALGORITHM "in-field stray-light corrected" (notes, "contains solar stray-light corrected, in-field stray-light corrected, radiometric calibrated and geometric distortion corrected (resampled) image data")
  - **Rule:** Writing a classed triple, rule 14: "Write each only if the record names both of its parts." "in-field stray-light corrected" describes the data; it is not the name of a method (as for "detrended" in the record at pool position 5).
  - **May matter because:** it says which corrections were applied to the images.
  - **Question:** Q7 (e).
- **Left out:** PRODUCED_USING_ALGORITHM "radiometric calibrated" (notes, "contains solar stray-light corrected, in-field stray-light corrected, radiometric calibrated and geometric distortion corrected (resampled) image data")
  - **Rule:** Writing a classed triple, rule 14: "Write each only if the record names both of its parts." "radiometric calibrated" describes the data; it is not the name of a method (as for "detrended" in the record at pool position 5).
  - **May matter because:** it says which corrections were applied to the images.
  - **Question:** Q7 (e).
- **Left out:** PRODUCED_USING_ALGORITHM "geometric distortion corrected (resampled)" (notes, "contains solar stray-light corrected, in-field stray-light corrected, radiometric calibrated and geometric distortion corrected (resampled) image data")
  - **Rule:** Writing a classed triple, rule 14: "Write each only if the record names both of its parts." "geometric distortion corrected (resampled)" describes the data; it is not the name of a method (as for "detrended" in the record at pool position 5).
  - **May matter because:** it says which corrections were applied to the images.
  - **Question:** Q7 (e).
