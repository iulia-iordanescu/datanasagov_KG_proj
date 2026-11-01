# Left out on purpose

Statements of a [record](../docs/terminology.md#1-records-and-their-text)'s [text](../docs/terminology.md#1-records-and-their-text) that have no [ground truth triple](../docs/terminology.md#4-ground-truth-and-samples), because I decided so or a rule of the [annotation guidelines](guidelines.md) says so. It is the one place where I keep them, so that what the [ground truth](../docs/terminology.md#4-ground-truth-and-samples) leaves out is not lost: some of these words carry information I may want back once an expert answers a question, or once the schema can say it. Terms: [docs/terminology.md](../docs/terminology.md).

One section per record I have annotated, in [pool](../docs/terminology.md#4-ground-truth-and-samples) order. Each item has the exact words (quoted from the record's text, as in `outputs/intermediate_results/020_clean/records.jsonl`), the rule that excluded them (quoted from `guidelines.md`), a *May matter because* line when the words carry information worth keeping, and the question in `questions_for_experts.md` that asks about it, if there is one. Left out here is not the same as wrong: a statement written in other words, or as part of a bigger ground truth triple, is not listed. Nor is a record's "is a data set" (the [describes class](../docs/terminology.md#2-triples) says it). Nor are all the type words that rule 23 of *Writing a classed triple* leaves out ("Leave out a type word that only describes the thing,"): the items below name some of them, not every one. When I annotate a record, I add its section; when an expert's answer brings a statement back as a ground truth triple, I delete its item. An item that waits on an expert's answer (its rule is rule 2's "or it waits on an expert's answer") has its would-be ground truth triple in `annotations/pending_triples.csv`, so that step 070 doesn't count an extracted triple that matches it as wrong, or a note "No clear would-be triple:" that says why it has none.

## "NASA Standards and and Technical Assistance Resource Tool" (pool position 0, id 3122be4c-b9d0-4cc9-b6d3-9b96c6e743da)

2 items, none that may matter.

- **Left out:** "is a Web tool" (notes)
  - **Rule:** What counts as a fact, rule 4: "says what type of thing MODIS is: that belongs in its entity class"
  - A Web tool is what the thing is; its entity class WebTool already says it.
- **Left out:** "great" (notes, "access great NASA technical information")
  - **Rule:** What counts as a fact, rule 5: "Leave out words such as "great"."
  - My ground truth triple of the purpose is written without it.

## "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (pool position 1, id cfd6ec3f-1e63-4a77-bc3f-007d45f7e2fc)

4 items, 3 that may matter.

- **Left out:** "1/2/3" (title)
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for"
  - **May matter because:** checked on 2026-10-30, the record does not say so but the data set's own catalog does: "1/2/3 (Data set contains raw, edited and calibrated data)", CODMAC processing levels 1, 2 and 3 (the data set's DATASET.CAT, https://archives.esac.esa.int/psa/ftp/INTERNATIONAL-ROSETTA-MISSION/RSI/RO-C-RSI-1-2-3-ESC4-1149-V1.0/CATALOG/; the PDS3 Standards Reference, chapter 6, names the CODMAC level in this slot, https://pds.nasa.gov/datastandards/pds3/standards/sr/Chapter06.pdf). Still left out: the record's text does not explain it (rule 1). A search by level would find it.
  - **Question:** Q6 (b).
- **Left out:** "1149" (title)
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for"
  - **May matter because:** checked on 2026-10-30: a running measurement number, "incremented measurement by measurement, independent what kind of measurement was conducted" (the data set's catalog, https://archives.esac.esa.int/psa/ftp/INTERNATIONAL-ROSETTA-MISSION/RSI/RO-C-RSI-1-2-3-ESC4-1149-V1.0/CATALOG/); it tells this dataset from its siblings and states no fact about the data.
  - **Question:** Q6 (b).
- **Left out:** what "RSI" stands for (title)
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included"
  - **May matter because:** checked on 2026-10-30: the Planetary Data System files it as INSTRUMENT_ID = RSI, INSTRUMENT_TYPE = RADIO SCIENCE, the "ROSETTA RADIO SCIENCE INVESTIGATION" (the data set's catalog files, https://archives.esac.esa.int/psa/ftp/INTERNATIONAL-ROSETTA-MISSION/RSI/RO-C-RSI-1-2-3-ESC4-1149-V1.0/CATALOG/). Still left out: the record's text does not say what "RSI" stands for, so its entity class would rest on outside knowledge (rule 1). Decided on 2026-10-31 (audit finding G-2); until then, ACQUIRED_BY_INSTRUMENT "RSI" (Instrument) was a ground truth triple. Reversed later on 2026-10-31: the triple is written again, by rule 1's *Names on an official NASA list*; what "RSI" stands for stays left out.
  - The list: PDS4 context product urn:esa:psa:context:instrument:ro.rsi, "The Radio Science Investigations (RSI) for the Rosetta Orbiter", an instrument of the instrument host Rosetta Orbiter (https://pds.nasa.gov/data/pds4/context-pds4/instrument/, checked on 2026-10-31).
  - **Question:** Q10 (its part on RSI, settled from this source: see Q10's My notes).
- **Left out:** "comet" (notes, "at the comet 67P")
  - **Rule:** Writing a classed triple, rule 23: "Leave out a type word that only describes the thing,"
  - My ground truth triple has the target "67P".

## "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" (pool position 2, id 6cfafd07-40f1-46da-9d92-36c2bb319f0b)

2 items, none that may matter. The record has no list of other temporal resolutions or spatial resolutions of its product ("daily" is its own, in "provides daily snow cover"), so nothing of a product family is left out here.

- **Left out:** "satellite" (notes, "the Aqua satellite")
  - **Rule:** Writing a classed triple, rule 23: "write "Aqua", not "Aqua satellite", since its entity class, Platform, already says what it is"
- **Left out:** "Each data granule contains" (notes), that the data come in granules
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words."
  - My ground truth triple HAS_GRANULE_DURATION "5 minutes" already says each granule covers 5 minutes, which only makes sense if the data come in granules.

## "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005" (pool position 3, id 2705e0d1-95e7-4588-813b-ca91a6da94ff)

1 item, 1 that may matter.

- **Left out:** "collaboratively" (notes, "developed collaboratively between")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds gives no ground truth triple, and is not part of an instance: its subject would be that fact, not a thing the record names." "collaboratively" says only how NASA and CONAE developed the mission (together); the two developers are ground truth triples of their own (DEVELOPED_BY_PARTY: NASA and CONAE). Saying how a fact holds needs a fact about a fact, a qualifier kept with the ground truth triple it holds for (as Wikidata's statement qualifiers do), which is future work: docs/improvements.md, *Rule 19 can lose which fact a qualifier went with*, option 4 (recommended on 2026-10-27, decided on 2026-10-30). Decided on 2026-10-31; until then this item waited on the experts' answer to Q27 (rule 2 of *What counts as a fact*).
  - **May matter because:** it says how NASA and CONAE worked on the mission: together.
  - **Question:** Q27 (settled on 2026-10-31: see Q27's My notes).

## "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (pool position 4, id 03a09af3-081e-4db6-9e3b-ea7c0e3138bd)

The dense record: its notes describe a whole family of products (several temporal resolutions, two spatial resolutions, day and night, two kinds of temperature) and the title names the one this record is. 12 items, 9 that may matter. The product family as a whole is asked in Q24.

- **Left out:** "Day" (notes, "Day and night spatially gridded (L3) global NASA skin sea surface temperature (SST) products")
  - **Rule:** Writing a classed triple, rule 21: "Leave out facts about other datasets, such as a variant of the record's dataset (the same data at another temporal resolution, spatial resolution, or version), or a product made from it." The title says "Nighttime", so the dataset is the night one; the day products are the family's.
  - **May matter because:** it says daytime products exist.
  - **Question:** Q24.
- **Left out:** "daily", "monthly" and "annual" (notes, "Average daily, weekly (8 day), monthly and annual skin SST products")
  - **Rule:** Writing a classed triple, rule 21: "Leave out facts about other datasets, such as a variant of the record's dataset (the same data at another temporal resolution, spatial resolution, or version), or a product made from it." Only "weekly (8 day)" is this dataset's (its title says "8 Day").
  - **May matter because:** they describe the product family: which temporal resolutions of this product exist.
  - **Question:** Q24.
- **Left out:** "9.26 km" (notes, "available at both 4.63 and 9.26 km spatial resolution")
  - **Rule:** Writing a classed triple, rule 21: "Leave out facts about other datasets, such as a variant of the record's dataset (the same data at another temporal resolution, spatial resolution, or version), or a product made from it." Only "4.63 km" is this dataset's.
  - **May matter because:** it is the other resolution of the product family.
  - **Question:** Q24; whether the title's "4km" is the 4.63 km was Q22, withdrawn on 2026-10-26: settled from PO.DAAC's page for this dataset, "4km" is the rounded 4.63 km grid (see Q22's My notes).
- **Left out:** "can be present" (notes, "Two SST products can be present in these files"), and with it the dataset's variable "skin SST"
  - **Rule:** What counts as a fact, rule 7: "the record doesn't state that it does. The same for "might", "possibly", "is expected to"" (I read "can be present" as the same kind). My ground truth triple has the variable SST4 only, from the title's "SST MID-IR".
  - **May matter because:** if the files hold both, the dataset has two variables, not one.
  - **Question:** Q18.
- **Left out:** "binned" and "mapped" as methods (notes, "the L2 pixels are binned into an integerized sinusoidal area grid (ISEAG) and mapped into an equidistant cylindrical")
  - **Rule:** Writing a classed triple, rule 24: "A word that says only that something was done ("corrected", "calibrated", "detrended") names no method." The record names the grid and the projection but only says the pixels "are binned" and "mapped", so I wrote BINNED_INTO (renamed ON_GRID on 2026-10-31) and MAPPED_INTO and no PRODUCED_USING_ALGORITHM.
  - **May matter because:** it is how the dataset was made, step by step.
  - **Question:** Q7.
- **Left out:** "NASA" (notes, "global NASA skin sea surface temperature (SST) products")
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words." By rule 19 of *Writing a classed triple* (*Whose fact it is*), "NASA" qualifies the products, which are the record's dataset, a standalone entity class, so its fact would be the record's dataset's: who made the products. The record states that fact more precisely in "The NASA MODIS L3 SST data products are generated by the NASA Ocean Biology Processing Group (OBPG)", my ground truth triple DEVELOPED_BY_PARTY "NASA Ocean Biology Processing Group (OBPG)", whose wording contains "NASA" as a whole word and says more (rule 23). Rule 21 does not leave it out: the record's dataset is one of these products. Decided on 2026-10-31; until then this item waited on the experts' answer to Q28 (a) (rule 2 of *What counts as a fact*).
  - **May matter because:** it says whose products these are: NASA's.
  - **Question:** Q28 (a) (settled on 2026-10-31: see Q28's My notes).
- **Left out:** "at a variety of spatial resolutions" (notes, "MODIS captures data in 36 spectral bands at a variety of spatial resolutions")
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names." The words name no value.
- **Left out:** "projection" (notes, "Platte Carre projection")
  - **Rule:** Writing a classed triple, rule 23: "Leave out a type word that only describes the thing,"
  - **Question:** Q15 (whether a coordinate system is a map projection); its part on "Platte Carre" was settled on 2026-10-26: it is the record's spelling of "Plate Carrée", the equidistant cylindrical projection on the equator (see Q15's My notes).
- **Left out:** "satellite" (notes, "the Aqua satellite")
  - **Rule:** Writing a classed triple, rule 23: "write "Aqua", not "Aqua satellite", since its entity class, Platform, already says what it is"
- **Left out:** "which can be found at https://doi.org/10.5067/MODAM-8D4N4" (notes), the DOI of the previous v2014.1 datasets
  - **Rule:** Writing a classed triple, rule 21: "Leave out facts about other datasets, such as a variant of the record's dataset (the same data at another temporal resolution, spatial resolution, or version), or a product made from it." The DOI is the address of the older datasets, not of this one; the ground truth triple has only "V2019.0" SUPERSEDES "v2014.1".
  - **May matter because:** it is where the superseded release is.
  - **Question:** Q19, and Q24 (the releases of a product family).

- **Left out:** "his team" (notes, "Peter Minnett and his team at the Rosenstiel School of Marine and Atmospheric Science (RSMAS)  are responsible for sea surface temperature algorithm development, error statistics and quality flagging")
  - **Rule:** Writing a classed triple, rule 22: "A list: one ground truth triple per item. Apply rule 19 first. Then write one ground truth triple per item of the list, in which that item alone takes the list's place (the subject or the object)," which splits the subject into "Peter Minnett" and "his team"; then What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names." "his team" names no team, so only "Peter Minnett" keeps the four ground truth triples (decided on 2026-10-30).
  - **May matter because:** the record gives the responsibilities and the affiliation to the team as well as to Peter Minnett; the team's share is lost.
- **Left out:** "NSST" (notes, "The first is a skin SST produced for both day and night (NSST) observations"), as another wording of "skin SST"
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for." "(NSST)" follows "night", not "skin SST", so it is not a name with its abbreviation in parentheses (Writing a classed triple, rule 20: "A name with its own abbreviation, another name or code of its own, or a short note in parentheses is one instance, as written."), and the record does not say what NSST names. The ground truth triples use "skin SST" (decided on 2026-10-30, audit finding G7).
  - **May matter because:** NSST may be the product's own name; other records of the family may use it. Checked on 2026-10-30: NSST names NASA's nighttime long-wave (11 µm) SST product, "Aqua MODIS Level-3 Global Mapped 11µm Nighttime Sea Surface Temperature (NSST) Data, version R2019.0" (https://data.nasa.gov/dataset/aqua-modis-level-3-global-mapped-11m-nighttime-sea-surface-temperature-nsst-data-version-r), so it is not another wording of this record's day-and-night "skin SST"; it stays left out (rule 1 of *What counts as a fact*: the record doesn't explain it).
  - **Question:** Q18, (d). Its meaning may later come from the model, checked against a source: docs/improvements.md, *Knowledge enrichment from the model, verified and labelled* (080).

## "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0" (pool position 5, id 99dff022-24ac-48cb-bc83-09fec8b90ad7)

1 item, 1 that may matter.

- **Left out:** "detrended" as a method (notes, "The nominal fast neutron count rates were detrended using the GRaND epithermal neutron map")
  - **Rule:** Writing a classed triple, rule 24: "A word that says only that something was done ("corrected", "calibrated", "detrended") names no method." The record says the rates "were detrended", only a verb; I wrote the two COMPUTED_FROM triples (the rates, the epithermal map) and no PRODUCED_USING_ALGORITHM.
  - **May matter because:** it is the method that made the residual map.
  - **Question:** Q7 (settled for now, not asked), Q12 (c) for the map as an input.

## "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (pool position 6, id 4c64f3ed-39b4-4f95-95a0-022898ba47a4)

2 items, all 2 that may matter. The record's decisions are complete (its ground truth triples are in `annotations/ground_truth/batch_001.csv`, a demo batch): these items are the ones I decided or am waiting on.

- **Left out:** "surface reflectance" and "MCD19A1N" (notes, "used to calculate the MAIAC Land Surface Bidirectional Reflectance Factor (BRF) or surface reflectance, MCD19A1N product"), as other wordings of the product
  - **Rule:** Writing a classed triple, rule 21: "Leave out facts about other datasets, such as a variant of the record's dataset (the same data at another temporal resolution, spatial resolution, or version), or a product made from it." The three wordings name one product, made from the record's dataset, each once; "MAIAC Land Surface Bidirectional Reflectance Factor (BRF)" ALSO_KNOWN_AS "surface reflectance" and HAS_IDENTIFIER "MCD19A1N" would be facts about that product, so they are left out. My ground truth triple "MAIAC Land Surface Bidirectional Reflectance Factor (BRF)" COMPUTED_FROM the record's dataset uses the first wording (rule 23: on a tie, the one the record gives first). Until 2026-10-31 this item cited rule 23 (third audit, finding L-5) (decided on 2026-10-31, audit finding G-11; until then its subject instance was "MCD19A1N", and the first wording was left out as what that product holds, by rule 21).
  - **May matter because:** "MCD19A1N" is the product's short name, by which a search would find it.
  - **Question:** Q20 (c), now its (b) (withdrawn on 2026-10-31, settled from sources: see Q20's My notes).
- **Left out:** the same words as a purpose of this dataset ("calculate the MAIAC Land Surface Bidirectional Reflectance Factor (BRF) or surface reflectance")
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words." "used to calculate" the product is the fact my ground truth triple "MAIAC Land Surface Bidirectional Reflectance Factor (BRF)" COMPUTED_FROM the record's dataset already states; and the ground truth schema's Purpose is "an aim something is meant to achieve", while the record says "used to calculate", not that the dataset is meant for it. I decided this on 2026-10-25; the rule was named on 2026-10-31.
  - **May matter because:** it is what the dataset is for.
  - **Question:** Q9 ("used to"; settled on 2026-10-31, a use is not a purpose: see Q9's My notes).

## "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" (pool position 7, id d5477563-0415-4e65-ab7c-d4bc9ed809e5)

15 items, 9 that may matter.

- **Left out:** what "MODIS" stands for (title, "MODIS/Terra", and notes, "Terra MODIS")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for"
  - **May matter because:** its entity class, Instrument, is written (ACQUIRED_BY_INSTRUMENT "MODIS"), by rule 1's *Names on an official NASA list*.
  - The list: GCMD Instruments keywords (version 25.1), "MODIS", "Moderate-Resolution Imaging Spectroradiometer"; the CMR record of MOD11A1 version 006 lists it under the platform Terra (checked on 2026-10-31).
- **Left out:** "in a 1,200 by 1,200 km grid" (notes)
  - **Rule:** What counts as a fact, rule 1: "Only what the record states. Never add what you know from elsewhere". The record says only that the data are "in a 1,200 by 1,200 km grid"; that this is one tile of the MODIS sinusoidal grid, the ground each file covers, comes from NASA LAADS, not from the record, and the ground truth schema has no predicate for the ground each file covers (HAS_GRANULE_DURATION is the time each file covers; HAS_SPATIAL_RESOLUTION, the ground each value covers). Decided on 2026-10-31; until then this item waited on the experts' answer to Q1 (c) (rule 2 of *What counts as a fact*). The grid itself is now the ground truth triple BINNED_INTO "SIN Grid".
  - **May matter because:** it is the size of one tile of the MODIS sinusoidal grid, which is how much ground each file covers. Checked on 2026-10-30: "Each tile has fixed Earth-locations covering an area of approximately 1200 x 1200 km (10 x 10 degrees at the equator)" (NASA LAADS, "What are the Product Spatial Formats?", https://landweb.modaps.eosdis.nasa.gov/help/prod_format).
  - **Question:** Q1 (c) (settled on 2026-10-31: see Q1's My notes).
- **Left out:** "per-pixel" (notes, "provides daily per-pixel Land Surface Temperature")
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words." The ground truth triple HAS_SPATIAL_RESOLUTION "1 kilometer (km)" already says how much ground each value covers.
- **Left out:** "(LST&E)" (notes, "Land Surface Temperature and Emissivity (LST&E)")
  - **Rule:** Writing a classed triple, rule 22: "A list that the record gives one abbreviation of its own is a name, kept whole, only when the abbreviation stands for one thing; when it stands for several things, it is a list, and the abbreviation belongs to no item." "LST&E" stands for two quantities, so the list splits and "(LST&E)" belongs to neither item (the test was written on 2026-10-31, third audit, findings R-4 and G-5; until then this item cited only "A list: one ground truth triple per item.").
- **Left out:** "https://doi.org/10.5067/MODIS/MOD11A1.061" (notes, the address in "[MOD11A1 Version 6.1](https://doi.org/10.5067/MODIS/MOD11A1.061)"), the DOI of Version 6.1
  - **Rule:** Writing a classed triple, rule 21: "Leave out facts about other datasets, such as a variant of the record's dataset (the same data at another temporal resolution, spatial resolution, or version), or a product made from it." The ground truth triple has only "Version 6.1" SUPERSEDES "Version 6".
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
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words." "surface temperature" is the "Land Surface Temperature" already written (rule 23: the wording that says more); "bands" is a type word (rule 23: "Leave out a type word that only describes the thing,"). "daytime" and "nighttime" are ground truth triples of their own (OBSERVED_AT_TIME_OF_DAY, rule 19 of *Writing a classed triple*).
- **Left out:** "associated" (notes, "associated quality control assessments")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds gives no ground truth triple, and is not part of an instance: its subject would be that fact, not a thing the record names." "associated" says only that the quality control assessments go with the temperature bands, how the fact HAS_MEASUREMENTS_OF "quality control assessments" holds. Saying how a fact holds needs a fact about a fact, a qualifier kept with the ground truth triple it holds for (as Wikidata's statement qualifiers do), which is future work: docs/improvements.md, *Rule 19 can lose which fact a qualifier went with*, option 4 (recommended on 2026-10-27, decided on 2026-10-30). Decided on 2026-10-31; until then this item waited on the experts' answer to Q27 (rule 2 of *What counts as a fact*).
  - **May matter because:** it says which values the quality control assessments go with: the temperature bands.
  - **Question:** Q27 (settled on 2026-10-31: see Q27's My notes).
- **Left out:** "significant" (notes, "due to [significant loss of data retrieval](https://landweb.modaps.eosdis.nasa.gov/displayissue?id=98) following the Constellation Exit Maneuvers")
  - **Rule:** What counts as a fact, rule 5: "Leave out words such as "great"." "significant" is a judgement of how much was lost, as in the record "Ensemble X-Ray Variability of AGN in 2XMMi-DR3"; my two ground truth triples write the issue as "loss of data retrieval following the Constellation Exit Maneuvers" (decided on 2026-10-31, audit finding G-4).
- **Left out:** "Known Issues" (notes, the heading)
  - **Rule:** What counts as a fact, rule 3: "the field names are formatting, not facts" (a heading, like a field name).
- **Left out:** the other products in "Production of V6 Terra MODIS Land Surface Temperature and Emissivity (LST&E) data products was discontinued" (notes)
  - **Rule:** Writing a classed triple, rule 21: "Leave out facts about other datasets, such as a variant of the record's dataset (the same data at another temporal resolution, spatial resolution, or version), or a product made from it." The sentence is about every Version 6 Terra MODIS land surface temperature and emissivity product; I wrote its two facts for this dataset only (PRODUCTION_DISCONTINUED_ON, PRODUCTION_DISCONTINUED_DUE_TO).
  - **May matter because:** the date and its cause hold for the whole family of these products.
  - **Question:** Q24.
- **Left out:** "known issues" as what the page is about (notes, "For complete information about known issues please refer to")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds gives no ground truth triple, and is not part of an instance: its subject would be that fact, not a thing the record names." "about known issues" says only what the details at the page are about, how the fact DOCUMENTED_AT holds. The field's practice records the same fact and no more: W3C DCAT's `dcat:landingPage` and FOAF's `foaf:page` ("A page or document about this thing") link a thing to a page about it and say nothing of what the page covers. Saying how a fact holds needs a fact about a fact, a qualifier kept with the ground truth triple it holds for (as Wikidata's statement qualifiers do), which is future work: docs/improvements.md, *Rule 19 can lose which fact a qualifier went with*, option 4 (recommended on 2026-10-27, decided on 2026-10-30). Decided on 2026-10-31; until then this item waited on the experts' answer to Q28 (b) (rule 2 of *What counts as a fact*).
  - **May matter because:** a search for a dataset's known issues would need it.
  - **Question:** Q28 (b) (settled on 2026-10-31: see Q28's My notes).
- **Left out:** "MODIS/VIIRS Land Quality Assessment website" (notes, "[MODIS/VIIRS Land Quality Assessment website](https://landweb.modaps.eosdis.nasa.gov/knownissue?sensor=MODIS&sat=Terra&as=6)"), as the name of the page
  - **Rule:** Writing a classed triple, rule 20: "Write ALSO_KNOWN_AS only when the record gives the other name in words of its own". The words are the text of the page's link, not words of the record's own that give the page another name, and the ground truth schema's WebPage is "a web address, written as the address itself". My ground truth triple has the page as its address (DOCUMENTED_AT). Until 2026-10-31 the page had ALSO_KNOWN_AS "MODIS/VIIRS Land Quality Assessment", and this item left out only the type word "website" (third audit, finding G-1).
  - **May matter because:** it is the page's name, by which a person would look for it.
- **Left out:** "product" (notes, "[MOD11_L2](https://doi.org/10.5067/MODIS/MOD11_L2.006) swath product")
  - **Rule:** Writing a classed triple, rule 23: "Leave out a type word that only describes the thing,"; "swath" is a ground truth triple of its own (HAS_SPATIAL_REPRESENTATION, as "gridded" for the record at pool position 6).

## "STARDUST 9P/TEMPEL 1 DFMI 2/3 NEXT V1.0" (pool position 9, id dc4ff01b-12f0-4235-8c8a-afb4bfb3bdbb)

3 items, 2 that may matter.

- **Left out:** "comet" (notes, "encounter with comet 9P/Tempel 1" and "the entire comet encounter")
  - **Rule:** Writing a classed triple, rule 23: "Leave out a type word that only describes the thing,"
  - My ground truth triple has the target "9P/Tempel 1", and the phase "encounter".
- **Left out:** "convert" as a method (notes, "The RDR data convert the EDR (raw) sensor data")
  - **Rule:** Writing a classed triple, rule 24: "A word that says only that something was done ("corrected", "calibrated", "detrended") names no method." The record says the RDR data "convert" the EDR data, only a verb; I wrote "RDR data" COMPUTED_FROM "EDR (raw) sensor data" and no PRODUCED_USING_ALGORITHM.
  - **May matter because:** it is how the RDR data are made from the raw data.
  - **Question:** Q7.
- **Left out:** "entire" (notes, "from the entire comet encounter")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds gives no ground truth triple, and is not part of an instance: its subject would be that fact, not a thing the record names." HAS_MISSION_PHASE "encounter" says the RDR data come from the encounter; "entire" says only how much of it, how that fact holds. Saying how a fact holds needs a fact about a fact, a qualifier kept with the ground truth triple it holds for (as Wikidata's statement qualifiers do), which is future work: docs/improvements.md, *Rule 19 can lose which fact a qualifier went with*, option 4 (recommended on 2026-10-27, decided on 2026-10-30). Decided on 2026-10-31; until then this item waited on the experts' answer to Q27 (rule 2 of *What counts as a fact*).
  - **May matter because:** it says the data cover all of the encounter, not a part of it. Checked on 2026-10-31: that is the EDR (raw) data; the RDR data cover the encounter "up to before the start of the anomaly" (the data set's catalog file, https://pdssbn.astro.umd.edu/holdings/sdu-c_d-dfmi-2_3-next-tempel1-v1.0/catalog/; see Q5's My notes). Until 2026-10-31 this line said "it says the RDR data cover all of the encounter, not a part of it."
  - **Question:** Q27 (settled on 2026-10-31: see Q27's My notes).

## "ROSETTA-ORBITER 67P/CAL ALICE 2 ESC1 V1.0" (pool position 10, id 3bceffb4-f01e-433c-af79-42b9d9427231)

2 items, 1 that may matter.

- **Left out:** "CAL" (title, "67P/CAL")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for"
  - **May matter because:** checked on 2026-10-30: "CAL" is the PDS3 target "CALIBRATION" in the data set name (TARGET_NAME = "CALIBRATION"; the PDS3 Standards Reference lists "CAL Calibration" among target IDs, https://pds.nasa.gov/datastandards/pds3/standards/sr/Chapter06.pdf), so the data include observations of calibration targets. It does not mean "calibrated": the data set says its data are uncalibrated, CODMAC level 2 (https://archives.esac.esa.int/psa/ftp/INTERNATIONAL-ROSETTA-MISSION/ALICE/RO-C-CAL-ALICE-2-ESC1-V1.0/CATALOG/DATASET.CAT). My earlier reading ("calibration data") was close but imprecise. Still left out: the record's text does not explain it (rule 1).
  - **Question:** Q6 (b).
- **Left out:** "mission phase" (notes, "comet escort 1 mission phase")
  - **Rule:** Writing a classed triple, rule 23: "Leave out a type word that only describes the thing,"
  - My ground truth triple has the phase "comet escort 1", its target "67P/Churyumov-Gerasimenko" a triple of its own (rule 19 of *Writing a classed triple*).

## "Ensemble X-Ray Variability of AGN in 2XMMi-DR3" (pool position 12, id bb1fe4b0-6543-42e3-9386-acbab0b37ad4)

The notes are mostly the abstract of the study the table comes from; whether a study's aim, method and findings belong in the ground truth was asked in Q26, settled on 2026-10-31: the study's aim and method are ground truth triples of the record's dataset (HAS_PURPOSE, PRODUCED_USING_ALGORITHM), and its background and findings are left out (rule 8 of *What counts as a fact*, *A study a record tells*). 21 items, 16 that may matter.

- **Left out:** "The X-ray variability of active galactic nuclei (AGN) has been most often investigated with studies of individual, nearby sources, and only a few ensemble analyses have been applied to large samples in wide ranges of luminosity and redshift." (notes)
  - **Rule:** What counts as a fact, rule 8: "The rest of the study is not: its background, its findings, and what it says about methods it did not use." It is the background of the study, about earlier studies. Decided on 2026-10-31; until then this item waited on the experts' answer to Q26 (rule 2 of *What counts as a fact*). (Until 2026-10-31 this item had cited rule 9, as naming no specific thing; third audit, finding L-6.)
  - **May matter because:** it says why the study was made.
  - **Question:** Q26 (settled on 2026-10-31: see Q26's My notes).
- **Left out:** "and Swift (the latter is not included in this table, notice)" (notes), the study's second sample
  - **Rule:** What counts as a fact, rule 6: "A ground truth triple can't say "not"." The Swift sample is another dataset, too (Writing a classed triple, rule 21: "Leave out facts about other datasets, such as a variant of the record's dataset (the same data at another temporal resolution, spatial resolution, or version), or a product made from it.").
  - **May matter because:** the study's findings are about both samples.
  - **Question:** Q26 (c), withdrawn on 2026-10-31 (see Q26's My notes); the item is left out by rules 6 and 21 of its own. Checked on 2026-10-31: the Swift sample is the catalogue's other table, table2.dat (the CDS ReadMe of J/A+A/536/A84, http://vizier.nao.ac.jp/ftp/cats/J/A+A/536/A84/ReadMe).
- **Left out:** "which operates in the time domain" (notes, about the structure function)
  - **Rule:** What counts as a fact, rule 8: "When a record tells the study its dataset comes from, the study's aim and its method are facts of the record's dataset (HAS_PURPOSE; PRODUCED_USING_ALGORITHM, rule 24 of *Writing a classed triple*). The rest of the study is not". The method is a ground truth triple ("structure function (SF)", PRODUCED_USING_ALGORITHM); in which domain it works is a detail the study gives of its method, not the method. Decided on 2026-10-31 (Q28 (d), settled); until then it waited on the experts' answer to Q28 (d) (rule 2 of *What counts as a fact*, its part on waiting for an expert), with no clear would-be triple, since its predicate and the entity class of "time domain" were not settled. (Until 2026-10-31 it waited on Q26, and before that cited rule 4; third audit, finding L-7.) The field's home for it is a subject list, the Unified Astronomy Thesaurus's "Time domain astronomy": docs/improvements.md, *Knowledge enrichment from the model, verified and labelled* (080).
  - **May matter because:** it says how the method works: in the time domain.
  - **Question:** Q28 (d) (settled on 2026-10-31: see Q28's My notes).
- **Left out:** "The SF is also more appropriate than fractional variability and excess variance, because these parameters are biased by the duration of the monitoring time interval in the rest-frame, and therefore by cosmological time dilation." (notes)
  - **Rule:** What counts as a fact, rule 5: "Leave out words such as "great"." ("more appropriate" is the authors' judgement). The second clause, that "these parameters are biased by the duration of the monitoring time interval", is about two measures the study did not use: What counts as a fact, rule 8: "The rest of the study is not: its background, its findings, and what it says about methods it did not use." Decided on 2026-10-31; until then this item waited on the experts' answer to Q26 (rule 2 of *What counts as a fact*). (Until 2026-10-31 this clause had cited no rule; third audit, finding L-8.)
  - **May matter because:** it says why the method was chosen.
  - **Question:** Q26 (settled on 2026-10-31: see Q26's My notes).
- **Left out:** "They do not find evidence of the break in the SF, at variance with the case of lower luminosity AGNs." (notes)
  - **Rule:** What counts as a fact, rule 6: "A ground truth triple can't say "not"."
- **Left out:** "then available" and "latest" (notes, "the version of the Serendipitous Source Catalog then available" and "the latest incremental update")
  - **Rule:** What counts as a fact, rule 10: "Leave out "latest", "current", "now", "then available", and words like them." They say what was so when the study was made, not a lasting fact.
- **Left out:** "all datasets were publicly available by 2009 October 31" (notes)
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names." It is about the observations the catalog was made from, which the record doesn't name, so there is no subject for a triple.
  - **May matter because:** it dates the data the catalog holds.
- **Left out:** "but not all public observations are included in this catalog" (notes)
  - **Rule:** What counts as a fact, rule 6: "A ground truth triple can't say "not"."
- **Left out:** "taking account of the substantial overlaps between observations" (notes)
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words." It explains why my ground truth triple HAS_SKY_AREA "~ 504 deg^2" is smaller than HAS_SUMMED_SKY_AREA "~ 814 deg^2", which the two predicates' definitions already say: HAS_SKY_AREA counts "each part of the sky counted once", HAS_SUMMED_SKY_AREA "each part of the sky counted as many times as it is covered". Decided on 2026-10-31; until then this item waited on the experts' answer to Q26 (rule 2 of *What counts as a fact*).
  - **May matter because:** it says how the net sky area was computed from the catalog's fields.
  - **Question:** Q26 (settled on 2026-10-31: see Q26's My notes).
- **Left out:** "therefore a significant number of sources (41,979) have more than one record within the catalog" (notes)
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names." HAS_NUMBER_OF holds a number of things, and "sources with more than one record" isn't a thing the record names; "significant" is a judgement (What counts as a fact, rule 5: "Leave out words such as "great".").
  - **May matter because:** it says how many sources the catalog has detected more than once.
- **Left out:** "corresponding to the uncertainty in the X-ray positions" (notes)
  - **Rule:** Writing a classed triple, rule 24: "Each step gives up to two ground truth triples, each written only if the record names both of its ends: output COMPUTED_FROM input, and output PRODUCED_USING_ALGORITHM method." It is why the maximum distance of 1.5 arcseconds was chosen, a setting of the matching step, left out with that distance (below). Decided on 2026-10-31; until then this item waited on the experts' answer to Q26 (rule 2 of *What counts as a fact*).
  - **May matter because:** it says how precise the X-ray positions are.
  - **Question:** Q26 (settled on 2026-10-31: see Q26's My notes).
- **Left out:** "cross-correlated" as a method (notes, "The selected sources were cross-correlated with the DR7 edition of the SDSS Quasar Catalog")
  - **Rule:** Writing a classed triple, rule 24: "A word that says only that something was done ("corrected", "calibrated", "detrended") names no method." Only a verb; I wrote COMPUTED_FROM "DR7 edition of the SDSS Quasar Catalog" and no PRODUCED_USING_ALGORITHM.
  - **Question:** Q7.
- **Left out:** "structure function (SF)" HAS_PURPOSE "ensemble analysis even when only a few observations are available for individual sources and the power spectral density (PSD) cannot be derived" (notes, "allows for an ensemble analysis even when only a few observations are available for individual sources and the power spectral density (PSD) cannot be derived")
  - **Rule:** What counts as a fact, rule 8: "When a record tells the study its dataset comes from, the study's aim and its method are facts of the record's dataset (HAS_PURPOSE; PRODUCED_USING_ALGORITHM, rule 24 of *Writing a classed triple*). The rest of the study is not". What the structure function "allows for" is a use the study gives for its method, not a purpose: HAS_PURPOSE is "is meant to achieve", Wikidata's "has goal" (P3712), which Wikidata keeps apart from "has use" (P366, "can be used for"); coining a predicate for a use for this one record would tailor the schema to it. Decided on 2026-10-31 (Q9 (b), settled); until then it waited on the experts' answer to Q9 (b) (rule 2 of *What counts as a fact*, its part on waiting for an expert), and its would-be ground truth triple was in `annotations/pending_triples.csv`, now deleted. (Until 2026-10-31 it waited on Q26 too.)
  - **May matter because:** it says why the method was used.
  - **Question:** Q9 (b) (settled on 2026-10-31: see Q9's My notes).
- **Left out:** "the authors" REPORTED "statistically consistent results for the two samples" (Finding) (notes, "The authors find statistically consistent results for the two samples")
  - **Rule:** What counts as a fact, rule 8: "The rest of the study is not: its background, its findings, and what it says about methods it did not use." It is a finding of the study. Decided on 2026-10-31; until then this item waited on the experts' answer to Q26 (rule 2 of *What counts as a fact*).
  - **May matter because:** it is a result of the study the table comes from.
  - **Question:** Q26 (settled on 2026-10-31: see Q26's My notes).
- **Left out:** "the authors" REPORTED "SF described by a power law of the time lag tau, approximately as SF ~ tau^0.1" (Finding) (notes, "with the SF described by a power law of the time lag tau, approximately as SF ~ tau^0.1")
  - **Rule:** What counts as a fact, rule 8: "The rest of the study is not: its background, its findings, and what it says about methods it did not use." It is a finding of the study. Decided on 2026-10-31; until then this item waited on the experts' answer to Q26 (rule 2 of *What counts as a fact*).
  - **May matter because:** it is a result of the study the table comes from.
  - **Question:** Q26 (settled on 2026-10-31: see Q26's My notes).
- **Left out:** "the authors" REPORTED "strong anti-correlation of the variability with X-ray luminosity, accompanied by a change of the slope of the SF" (Finding) (notes, "They confirm a strong anti-correlation of the variability with X-ray luminosity, accompanied by a change of the slope of the SF")
  - **Rule:** What counts as a fact, rule 8: "The rest of the study is not: its background, its findings, and what it says about methods it did not use." It is a finding of the study. Decided on 2026-10-31; until then this item waited on the experts' answer to Q26 (rule 2 of *What counts as a fact*).
  - **May matter because:** it is a result of the study the table comes from.
  - **Question:** Q26 (settled on 2026-10-31: see Q26's My notes).
- **Left out:** "the authors" REPORTED "evidence in support of a weak, intrinsic, average increase of X-ray variability with redshift" (Finding) (notes, "They also find evidence in support of a weak, intrinsic, average increase of X-ray variability with redshift")
  - **Rule:** What counts as a fact, rule 8: "The rest of the study is not: its background, its findings, and what it says about methods it did not use." It is a finding of the study. Decided on 2026-10-31; until then this item waited on the experts' answer to Q26 (rule 2 of *What counts as a fact*).
  - **May matter because:** it is a result of the study the table comes from.
  - **Question:** Q26 (settled on 2026-10-31: see Q26's My notes).
- **Left out:** "Ensemble X-Ray Variability of AGN in 2XMMi-DR3" DEVELOPED_BY_PARTY "the authors" (notes, "The authors used a maximum distance of 1.5 arcseconds")
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names." "the authors" names no specific people (the record never names them). The table's developer is the HEASARC ("This table was created by the HEASARC"); the authors made the selection described in the study. (Until 2026-10-31 this item cited rule 2, as waiting on Q26 with the study's aim, method and findings; audit finding G-9 (b).)
  - **May matter because:** it says who selected the table's sources.
- **Left out:** "Ensemble X-Ray Variability of AGN in 2XMMi-DR3" HAS_MATCHING_DISTANCE "1.5 arcseconds" (notes, "The authors used a maximum distance of 1.5 arcseconds")
  - **Rule:** Writing a classed triple, rule 24: "Each step gives up to two ground truth triples, each written only if the record names both of its ends: output COMPUTED_FROM input, and output PRODUCED_USING_ALGORITHM method." The maximum distance is a setting of the step that matched the selected sources with the quasar catalog, which gives the ground truth triple COMPUTED_FROM "DR7 edition of the SDSS Quasar Catalog" and names no method ("cross-correlated", above); a setting of a step is neither of the step's two triples. Decided on 2026-10-31; until then this item waited on the experts' answer to Q26 (rule 2 of *What counts as a fact*).
  - **May matter because:** it says how the sources of the table were matched with the quasar catalog.
  - **Question:** Q26 (settled on 2026-10-31: see Q26's My notes).
- **Left out:** "Ensemble X-Ray Variability of AGN in 2XMMi-DR3" ALSO_KNOWN_AS "XMM-Newton sample" (notes, "The authors refer to these sources as the XMM-Newton sample")
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names." "XMM-Newton sample" names the sources the table holds, not the table, and the record names those sources only by a count ("412 quasars", a Value), so there is no instance for them to be the subject of an ALSO_KNOWN_AS triple (the rule was named on 2026-10-31).
- **Left out:** "from 2 to 25 epochs each" (notes, "resulting in 412 quasars that were observed by XMM-Newton from 2 to 25 epochs each"), as how many times each quasar was observed
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names." The count is each quasar's, not the dataset's, and the record names the quasars only by a count ("412 quasars", a Value), so there is no instance for them to be the subject (as for "XMM-Newton sample", above). Until 2026-10-31 the dataset had HAS_NUMBER_OF "from 2 to 25 epochs each" (third audit, finding G-8).
  - **May matter because:** it says how often each source was observed, which the study's variability measure depends on.

## "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0" (pool position 13, id ab33f184-95f4-4f33-8f3d-c4a09ec525d3)

10 items, 8 that may matter.

- **Left out:** "MTP020" (title, "ESC3-MTP020")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for"
  - **May matter because:** checked on 2026-10-30: planning period no. 20 (MTP, a numbered planning period; checked on 2026-10-31: ESA's *OSIRIS Science User Guide*, RO-RIS-MPAE-MA-011, section 5.1, spells it out as the Rosetta "Mid-Term Planning-cycle", covering "a timespan of roughly four weeks", https://archives.esac.esa.int/psa/ftp/INTERNATIONAL-ROSETTA-MISSION/OSINAC/RO-C-OSINAC-4-ESC3-67P-M20-INFLDSTR-V1.0/DOCUMENT/SCIENCE_USER_GUIDE/SCIENCE_USER_GUIDE_V05.PDF, not "Medium Term Plan"), inside the phase COMET ESCORT 3; the Rosetta NAVCAM archive lists "COMET ESCORT 3 MTP020 ESC3-MTP020 2015-08-25 23:25:00" (https://archives.esac.esa.int/psa/ftp/INTERNATIONAL-ROSETTA-MISSION/NAVCAM/RO-C-NAVCAM-2-ESC1-MTP010-V1.1/DOCUMENT/RO-SGS-IF-0001.ASC), and this data set covers 2015-08-25T23:25 to 2015-09-22T23:24:59 (https://archives.esac.esa.int/psa/ftp/INTERNATIONAL-ROSETTA-MISSION/OSINAC/RO-C-OSINAC-4-ESC3-67P-M20-INFLDSTR-V1.0/CATALOG/DATASET.CAT). It tells this dataset from its siblings. Still left out: the record's text does not explain it (rule 1).
  - **Question:** Q6 (b).
- **Left out:** "RDR" (title, "RDR-INFLDSTR")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for"
  - **May matter because:** another record uses it as a name of data ("The RDR data convert the EDR (raw) sensor data"); this one doesn't explain it, and its level is "CODMAC level 4". Checked on 2026-10-30: "RDR" is the data set type "Reduced Data Record", not a level (PDS3 Standards Reference, chapter 6, https://pds.nasa.gov/datastandards/pds3/standards/sr/Chapter06.pdf); Rosetta's archive conventions pair RDR with CODMAC 3 (ESA, RO-EST-TN-3372), while this data set uses it at CODMAC 4.
  - **Question:** Q6 (b).
- **Left out:** "prime" (notes, "The prime target is comet 67P/Churyumov-Gerasimenko 1 (1969 R1)")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds gives no ground truth triple, and is not part of an instance: its subject would be that fact, not a thing the record names." HAS_TARGET says the dataset is about the comet; "prime" says only that it is the main target, how that fact holds. Saying how a fact holds needs a fact about a fact, a qualifier kept with the ground truth triple it holds for (as Wikidata's statement qualifiers do), which is future work: docs/improvements.md, *Rule 19 can lose which fact a qualifier went with*, option 4 (recommended on 2026-10-27, decided on 2026-10-30). Decided on 2026-10-31; until then this item waited on the experts' answer to Q27 (b) (rule 2 of *What counts as a fact*).
  - **May matter because:** a search for other bodies in these images would need it.
  - **Question:** Q27 (settled on 2026-10-31: see Q27's My notes).
- **Left out:** "comet" (notes, "comet 67P/Churyumov-Gerasimenko 1 (1969 R1)")
  - **Rule:** Writing a classed triple, rule 23: "Leave out a type word that only describes the thing,"
- **Left out:** "spacecraft" and "mission phase" (notes, "the Rosetta spacecraft" and "the COMET ESCORT 3 mission phase")
  - **Rule:** Writing a classed triple, rule 23: "Leave out a type word that only describes the thing,"; "the Rosetta spacecraft" is written as "ROSETTA-ORBITER", the wording that says more (rule 23).
  - **Question:** Q2 (b) (settled on 2026-10-31: see Q2's My notes).
- **Left out:** "Lien" (notes, "Lien corrected dataset after September 2019 PSA/PDS external peer review")
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words." My ground truth triple REVISED_AFTER "September 2019 PSA/PDS external peer review" says the dataset was corrected after the review; "Lien" names what was corrected, the issues the review raised, which is what a correction after a review is (checked on 2026-10-30: PDS defines a lien as "A formally expressed issue with one or more products in a collection", and ESA's procedure for this review says "Within ESA, issues raised are known as RIDs (Review Item Discrepancies), while PDS refer to these as liens", https://sbnreview.astro.umd.edu/201909_Rosetta/procedure_docs/RO-SGS-PR-1023-App5%20-%20RSI%20Rosetta%20CLS%20Science%20Archive%20Review.pdf). Decided on 2026-10-31; until then this item waited on the experts' answer to Q28 (c) (rule 2 of *What counts as a fact*).
  - **May matter because:** it says what the correction was about.
  - **Question:** Q28 (c) (settled on 2026-10-31: see Q28's My notes).
- **Left out:** PRODUCED_USING_ALGORITHM "solar stray-light corrected" (notes, "contains solar stray-light corrected, in-field stray-light corrected, radiometric calibrated and geometric distortion corrected (resampled) image data")
  - **Rule:** Writing a classed triple, rule 24: "A word that says only that something was done ("corrected", "calibrated", "detrended") names no method." "solar stray-light corrected" describes the data; since 2026-10-31 what was corrected is written, CLEANED_OF "solar stray-light" (rule 24: "What a step removed from the data, or corrected in them, is neither the step's input nor its method"); it is not the name of a method (as for "detrended" in the record at pool position 5).
  - **May matter because:** it says which corrections were applied to the images.
  - **Question:** Q7 (c) (settled on 2026-10-31: see Q7's My notes).
- **Left out:** PRODUCED_USING_ALGORITHM "in-field stray-light corrected" (notes, "contains solar stray-light corrected, in-field stray-light corrected, radiometric calibrated and geometric distortion corrected (resampled) image data")
  - **Rule:** Writing a classed triple, rule 24: "A word that says only that something was done ("corrected", "calibrated", "detrended") names no method." "in-field stray-light corrected" describes the data; since 2026-10-31 what was corrected is written, CLEANED_OF "in-field stray-light" (rule 24: "What a step removed from the data, or corrected in them, is neither the step's input nor its method"); it is not the name of a method (as for "detrended" in the record at pool position 5).
  - **May matter because:** it says which corrections were applied to the images.
  - **Question:** Q7 (c) (settled on 2026-10-31: see Q7's My notes).
- **Left out:** PRODUCED_USING_ALGORITHM "radiometric calibrated" (notes, "contains solar stray-light corrected, in-field stray-light corrected, radiometric calibrated and geometric distortion corrected (resampled) image data")
  - **Rule:** Writing a classed triple, rule 24: "A word that says only that something was done ("corrected", "calibrated", "detrended") names no method." "radiometric calibrated" describes the data; it is not the name of a method (as for "detrended" in the record at pool position 5).
  - **May matter because:** it says which corrections were applied to the images.
  - **Question:** Q7 (c) (settled on 2026-10-31: see Q7's My notes).
- **Left out:** PRODUCED_USING_ALGORITHM "geometric distortion corrected (resampled)" (notes, "contains solar stray-light corrected, in-field stray-light corrected, radiometric calibrated and geometric distortion corrected (resampled) image data")
  - **Rule:** Writing a classed triple, rule 24: "A word that says only that something was done ("corrected", "calibrated", "detrended") names no method." "geometric distortion corrected (resampled)" describes the data; since 2026-10-31 what was corrected is written, CLEANED_OF "geometric distortion" (rule 24: "What a step removed from the data, or corrected in them, is neither the step's input nor its method"); it is not the name of a method (as for "detrended" in the record at pool position 5).
  - **May matter because:** it says which corrections were applied to the images.
  - **Question:** Q7 (c) (settled on 2026-10-31: see Q7's My notes).

## "Solar Orbiter Ephemeris, Heliocentric Trajectories, Heliographic, Heliographic Inertial, and Solar Ecliptic Coordinates, HelioWeb, Daily Data" (pool position 15, id 32614a2f-a286-4c7c-9f1e-deafdf8bd6a3)

13 items, 7 that may matter.

- **Left out:** "HelioWeb" (title)
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for". The record never says what HelioWeb is (a service, a web site, a collection), so it has no entity class.
  - **May matter because:** my reading, not checked: HelioWeb is the SPDF (NASA Goddard) service that serves these heliocentric trajectories; a search by service would need it.
- **Left out:** "where users can find many more objects" (notes)
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names." "many more objects" names none.
- **Left out:** "In the case of orbit data for planets, the orbit data can be used as a proxy for spacecraft ephemeris that are in orbit about the planets." (notes)
  - **Rule:** Writing a classed triple, rule 21: "Leave out facts about other datasets, such as a variant of the record's dataset (the same data at another temporal resolution, spatial resolution, or version), or a product made from it." Orbit data for planets are not this dataset, and no "part of" or "made from" link joins them; it is also a use (rule 9: "when the record doesn't name that work, it gives no ground truth triple.").
  - **May matter because:** it says what planet data of this kind are good for.
- **Left out:** "On a heliospheric scale, differences between the planet orbital tarjectory and that of the spacecraft are very small." (notes)
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names." "the planet" and "the spacecraft" name no particular ones; "very small" is a judgement (rule 5).
- **Left out:** "For instance, the heliocentric longitudes differ by only 0.25° for a spacecraft stationed near the L1 Lagrange point at approximately 100 Earth radii upstream of the Earth." (notes)
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names." The subject is "a spacecraft", none in particular.
  - **May matter because:** it gives the size of the error when planet data stand in for a spacecraft at L1.
- **Left out:** the definition of the "Equinox Epoch" ("which is defined as the epoch time when the direction from the Earth to the sun …") (notes)
  - **Rule:** Writing a classed triple, rule 21: "A statement that only explains a concept (what a term means, how a quantity behaves in general, which methods are in common use) and is about nothing so connected gives no ground truth triple". The Equinox Epoch is the subject or object of no ground truth triple connected to the record's id.
- **Left out:** "This direction is called the First Point of Aries, FPA and it is not a fixed direction but drifts by about 1.4° per century or 50.26" per year." (notes)
  - **Rule:** Writing a classed triple, rule 21: "A statement that only explains a concept (what a term means, how a quantity behaves in general, which methods are in common use) and is about nothing so connected gives no ground truth triple". "it is not a fixed direction": also rule 6 of *What counts as a fact*, "A ground truth triple can't say "not"."
  - **May matter because:** it explains why the choice of equinox matters for the coordinates.
- **Left out:** "In addition, there are tiny irregularities in FPA drift that are on the order of 1" per year or less." (notes)
  - **Rule:** Writing a classed triple, rule 21: "A statement that only explains a concept (what a term means, how a quantity behaves in general, which methods are in common use) and is about nothing so connected gives no ground truth triple"
- **Left out:** "The Equinox Epoch can be determined by using a variety of methods … Four methods for determining the Equinox Epoch are in common usage:" and the table rows "B1950.0", "J2000.0", "True of Date" (notes)
  - **Rule:** Writing a classed triple, rule 21: "A statement that only explains a concept (what a term means, how a quantity behaves in general, which methods are in common use) and is about nothing so connected gives no ground truth triple". "a variety of methods" names none (rule 9); the three methods the data did not use are connected to nothing.
- **Left out:** the table row "Mean of Date | the smoothed FPA at 00:00 UT on the date of interest" as a fact of its own (notes)
  - **Rule:** What counts as a fact, rule 4: "says what type of thing MODIS is: that belongs in its entity class". It defines the method; the method itself is a ground truth triple (PRODUCED_USING_ALGORITHM "Mean of Date").
  - **May matter because:** it is what "Mean of Date" means: the equinox of each day, smoothed.
- **Left out:** "requires a values for the "Equinox Epoch"" as a fact of its own (notes)
  - **Rule:** Writing a classed triple, rule 24: "A method is what could be applied again to other data (an algorithm, a procedure, and its settings, such as coefficients tuned per month)". The Equinox Epoch is the setting of the step whose method is "Mean of Date", so it is part of the method, not an input.
- **Left out:** "More precise coordinates, and some planet-centered coordinates, are found in the "traj" subdirectories of spacecraft specific directories at https://spdf.gsfc.nasa.gov/pub/data/ and http://ssd.jpl.nasa.gov/horizons.cgi." (notes)
  - **Rule:** Writing a classed triple, rule 21: "Leave out facts about other datasets, such as a variant of the record's dataset (the same data at another temporal resolution, spatial resolution, or version), or a product made from it." "More precise" compares those data with this dataset's, a fact of the other data.
  - **May matter because:** it is where better coordinates of the same objects are.
  - **Question:** Q24.
- **Left out:** the title's "Solar Orbiter" against the notes' "Heliocentric trajectories for Comet Borrelly" (title and notes), as a conflict to correct
  - **Rule:** Finishing a record, *A record that contradicts itself*: "write what each passage states (rule 1 of What counts as a fact), and correct neither from outside knowledge." Both are written: HAS_VARIABLE "Solar Orbiter Ephemeris" and HAS_TARGET "Comet Borrelly".
  - **May matter because:** my reading, not checked: the notes look copied from the record of the Comet Borrelly series of the same service; the catalog entry may be wrong, and the record's maintainer should be told.

## "VG1 J/S/SS PWS EDITED SPECTRUM ANALYZER FULL RES V1.0" (pool position 16, id ec41fd5d-1159-4aa8-9803-5346e2324a20)

9 items, 5 that may matter.

- **Left out:** "J/S/SS" (title)
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for"
  - **May matter because:** my reading, not checked: the PDS target codes for Jupiter, Saturn and the solar system, the targets of the data set; a search by target would need them. The notes say only "the planetary encounters".
  - **Question:** Q6 (b) lists other unexplained PDS title codes.
- **Left out:** "FULL RES" (title)
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for"; even spelled out, "full resolution" names no value (rule 9: "a variety of spatial resolutions" names no resolution).
  - **May matter because:** it says these are the analyzer's full-resolution data, not averages.
- **Left out:** "EDITED" (title), and "edited" (notes, "Some noise lines during the planetary encounters have been edited from the data set.") as a method
  - **Rule:** Writing a classed triple, rule 24: "A word that says only that something was done ("corrected", "calibrated", "detrended") names no method." What was removed is written: the record's dataset CLEANED_OF "noise lines during the planetary encounters" (rule 24: "What a step removed from the data, or corrected in them, is neither the step's input nor its method").
- **Left out:** "during the planetary encounters" as a mission phase of the dataset (notes)
  - **Rule:** What counts as a fact, rule 1: "Only what the record states." That the data include the encounters follows from the sentence (noise lines during them were in the data set) but is not stated.
  - **May matter because:** it says the data include the planetary encounters.
- **Left out:** "nearly all" (notes, "includes nearly all measurements")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds gives no ground truth triple, and is not part of an instance"
- **Left out:** "for the entire mission" (notes)
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names." The mission is not named, and "entire" only says how much of it.
  - **May matter because:** it says the data cover the whole mission (no dates are given).
- **Left out:** "Each sweep" (notes, "Each sweep of the PWS spectrum analyzer records")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds gives no ground truth triple, and is not part of an instance". It says how the analyzer records (sweep by sweep).
- **Left out:** "calibrated values" PRODUCED_USING_ALGORITHM "example C-language program" (notes)
  - **Rule:** Writing a classed triple, rule 21: "Leave out facts about other datasets, such as a variant of the record's dataset (the same data at another temporal resolution, spatial resolution, or version), or a product made from it." Its connection, "calibrated values" COMPUTED_FROM the record's dataset, is a ground truth triple.
  - **May matter because:** it is how users can calibrate the values.
- **Left out:** "reads this data set" as a fact of its own (notes)
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words." "calibrated values" COMPUTED_FROM the record's dataset already says it.

## "VIIRS/NPP BRDF/Albedo Parameter 3 Band M4 Daily L3 Global 30 ArcSec CMG V002" (pool position 18, id 0eedd2bc-b2e2-4cc1-a94d-41c141169334)

14 items, 6 that may matter.

- **Left out:** "NASA/NOAA" as a fact of its own (notes)
  - **Rule:** Writing a classed triple, rule 19: "A qualifier stays in the instance, as written, if it is any other kind" (an organization is not on its list); it stays in the platform's instance, "NASA/NOAA Suomi National Polar-orbiting Partnership (Suomi NPP)".
- **Left out:** "Data are temporally weighted to the ninth day, which is reflected in the file name." (notes)
  - **Rule:** Writing a classed triple, rule 24: "A word that says only that something was done ("corrected", "calibrated", "detrended") names no method." "the file name" names no particular file (rule 9).
  - **May matter because:** it says which day of the 16 each value stands for.
  - **Question:** Q7.
- **Left out:** "VNP43D product suite" and its facts as such (notes: "The VNP43D product suite is provided in a Climate Modeling Grid (CMG)"; "this product suite includes model parameters for the VIIRS Day/Night Band (DNB) as VNP43D37 through VNP43D39")
  - **Rule:** What counts as a fact, rule 1, *Membership by name*: "A statement about the group as a whole is not written for it". The record's identifier VNP43D12 contains "VNP43D", so the facts that hold for each member are written for the record's dataset (the grid, one data layer); the suite itself and its other members are not.
  - **May matter because:** it says which family the product belongs to, and that the family has 39 one-layer products.
  - **Question:** Q24; Q25 (b).
- **Left out:** "Each of the three model parameters (isotropic, volumetric, and geometric) for each of the nine VIIRS moderate resolution bands along with the visible, near-infrared (NIR), and shortwave bands included in the [VNP43MA1](…) product is stored in a separate file as VNP43D01 through VNP43D36." (notes)
  - **Rule:** Writing a classed triple, rule 21: "Leave out facts about other datasets, such as a variant of the record's dataset (the same data at another temporal resolution, spatial resolution, or version), or a product made from it." The files are the family's other products, and VNP43MA1 is another dataset with no "part of" or "made from" link stated.
  - **May matter because:** it says the parameters come from VNP43MA1, which a search for related products would need.
  - **Question:** Q24; Q12.
- **Left out:** "https://doi.org/10.5067/VIIRS/VNP43MA1.002" (notes), VNP43MA1's DOI
  - **Rule:** Writing a classed triple, rule 21: "Leave out facts about other datasets, such as a variant of the record's dataset (the same data at another temporal resolution, spatial resolution, or version), or a product made from it."
  - **May matter because:** it is where the related product is.
- **Left out:** "Due to the large file size" (notes)
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names." No file is named; "large" is a judgement (rule 5).
- **Left out:** "just" (notes, "contains just one data layer")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds gives no ground truth triple, and is not part of an instance"
- **Left out:** "entire" (notes, "covers the entire globe")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds gives no ground truth triple, and is not part of an instance"
- **Left out:** "BRDF/Albedo values for VIIRS band M4" COMPUTED_FROM "isotropic parameters" and "volumetric parameters" (notes)
  - **Rule:** Writing a classed triple, rule 21: "Leave out facts about other datasets, such as a variant of the record's dataset (the same data at another temporal resolution, spatial resolution, or version), or a product made from it." Its connection to the record's dataset is a ground truth triple ("BRDF/Albedo values for VIIRS band M4" COMPUTED_FROM the geometric parameter).
  - **May matter because:** it says the albedo needs all three parameters, that is, three of the family's products together.
  - **Question:** Q24.
- **Left out:** "used to derive" as a purpose of the parameter (notes)
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words." COMPUTED_FROM says it; and a use is not a purpose (rule 9: "What data have been used for, or can be used for, is a fact of the work that used them, not of the data").
- **Left out:** "Known Issues" (notes, the heading)
  - **Rule:** What counts as a fact, rule 3: "the names are formatting, not facts."
- **Left out:** "known issues" as what the page is about (notes)
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds gives no ground truth triple, and is not part of an instance"
- **Left out:** "MODIS/VIIRS Land Quality Assessment website" (notes), as the page's name
  - **Rule:** Writing a classed triple, rule 20: "Write ALSO_KNOWN_AS only when the record gives the other name in words of its own"
  - **May matter because:** it is the page's name.
- **Left out:** "NIR" as another name of "near-infrared", and "DNB" of "VIIRS Day/Night Band" (notes)
  - **Rule:** Writing a classed triple, rule 21: "Leave out facts about other datasets, such as a variant of the record's dataset (the same data at another temporal resolution, spatial resolution, or version), or a product made from it." The bands are the family's, not this dataset's.

## "BARREL 4G Rate Counter (RCNT) NaI Scintillator Diagnostics, Level 2, 4 s Data" (pool position 19, id 6f63dd10-376e-4d17-9156-f2155637e74d)

35 items, 15 that may matter.

- **Left out:** the launch stations and their places (notes, "with launches from two stations located in Antarctica: the British base located at Halley Bay on the Brunt Ice Shelf and the South African SANAE IV base", and "Later campaigns were undertaken in 2015 and 2016 from the Esrange Space Center located in Kiruna, Sweden")
  - **Rule:** What counts as a fact, rule 2: "or it waits on an expert's answer" (Q8 (c): whether a station or a space center is an Organization or a place).
  - **May matter because:** a search by launch site or region (Antarctica, Sweden) would need them.
  - **Question:** Q8 (c).
  - No clear would-be triple: whether a station is an Organization or a place decides its entity class and its predicates (LAUNCHED_FROM and LOCATED_IN for a place, none of them in the ground truth schema; BASED_IN "British", "South African" and "Sweden" for an Organization), so no row can be written in annotations/pending_triples.csv until Q8 (c) is answered.
- **Left out:** "4G" (title)
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for"
  - **May matter because:** my reading, not checked: the balloon payload's code (campaign 4, payload G), which tells this dataset from its siblings and gives its campaign.
  - **Question:** Q6 (b).
- **Left out:** "CDF" (notes, "all BARREL CDF data products")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for". "CDF" is on no official NASA list as an instrument or a platform, so rule 1's *Names on an official NASA list* does not apply.
  - **May matter because:** it is the file format (NASA's Common Data Format, my knowledge).
- **Left out:** "diagnostic fields" as a thing of its own (notes)
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words." HAS_VARIABLE "NaI Scintillator Diagnostics" says it (rule 23).
- **Left out:** "4 s" of "4 s accumulations" as a fact of its own (notes)
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words." HAS_TEMPORAL_RESOLUTION "4 s" says it.
- **Left out:** "was a multiple-balloon investigation" (notes)
  - **Rule:** What counts as a fact, rule 4: "says what type of thing MODIS is: that belongs in its entity class"
  - **May matter because:** it says the mission used many balloons at once.
- **Left out:** "Mission of Opportunity" and "Selected" (notes)
  - **Rule:** What counts as a fact, rule 4: "the kind is left out, and the belonging is a ground truth triple" ("BARREL" PART_OF "NASA Living with a Star"); "Selected" names no party (rule 1: "Never add what you know from elsewhere").
  - **May matter because:** it is NASA's funding category for the mission.
- **Left out:** "Each" (notes, "Each BARREL balloon")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds gives no ground truth triple, and is not part of an instance"
- **Left out:** "near latitudes close to either the antarctic and arctic circles" (notes)
  - **Rule:** What counts as a fact, rule 1, *Membership by name*: "A statement about the group as a whole is not written for it": "either … or". Which circle this payload flew near is not stated.
  - **May matter because:** a search by region (Antarctic, Arctic) would need it.
  - **Question:** Q24.
- **Left out:** "stratospheric altitudes" (notes)
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words." OBSERVED_AT_ALTITUDE "about 30 km" is the wording that says more (rule 23).
- **Left out:** "first balloon" (notes, "provided the first balloon measurements")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds gives no ground truth triple, and is not part of an instance"
  - **May matter because:** it says BARREL was the first to measure this from balloons.
- **Left out:** "while comprehensive in situ measurements of both plasma waves and energetic particles were available" (notes)
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names." Whose measurements is not said; "comprehensive" is a judgement (rule 5).
- **Left out:** "Also, the BARREL data has been used to characterize the spatial scale of precipitation at relativistic energies." (notes)
  - **Rule:** What counts as a fact, rule 9: "when the record doesn't name that work, it gives no ground truth triple." No work that used the data is named; the statement is also about the BARREL data as a whole (rule 1, *Membership by name*).
  - **May matter because:** it says what the data are good for.
  - **Question:** Q24.
- **Left out:** "initially" and "Austral summer months of" (notes)
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds gives no ground truth triple, and is not part of an instance" ("initially"). "Austral summer months": rule 16 of *Writing a classed triple*, since the months, HAS_TIME_SPAN "January and February of 2013" and "of 2014", say when.
  - **May matter because:** "Austral summer" says why those months (the southern summer).
- **Left out:** "Thus, the BARREL balloon constellation constituted an evolving and slowly moving array able to study relativistic electron precipitation from the radiation belts." (notes)
  - **Rule:** What counts as a fact, rule 4: "says what type of thing MODIS is: that belongs in its entity class" ("constituted an … array"); "able to study" is what it could do, not what it was meant for (HAS_PURPOSE "is meant to achieve").
  - **May matter because:** it says the balloons formed a moving array, which is how the mission measured spatial scales.
- **Left out:** "and other ground and space based instruments" (notes)
  - **Rule:** Writing a classed triple, rule 22: "An item that names no specific thing ("his team") gives no ground truth triple"
- **Left out:** "A total of eight flights occurred during August 2016." (notes)
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names." The sentence names no campaign; that these are the 2016 campaign's flights follows from the paragraph, but no test of rule 1 allows it.
  - **May matter because:** it is the 2016 campaign's number of flights.
- **Left out:** "successively" (notes)
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds gives no ground truth triple, and is not part of an instance"
- **Left out:** "The website creeated and hosted by A.J. Halford (see Information URL below) reports that: "By the end of the campaigns, there were over 90 researchers coordinating on a daily basis with the BARREL team working on 7 different satellite missions, 1 other balloon mission, and way too many ground based instruments to count."" (notes)
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names." The website has no address in the text (WebPage is "a web address, written as the address itself"), and the researchers are named only by a count; "way too many" is a judgement (rule 5).
  - **May matter because:** it names a person who keeps a BARREL web site, A.J. Halford, and the mission's reach.
- **Left out:** "only" (notes, "launched only balloons")
  - **Rule:** What counts as a fact, rule 6: "A ground truth triple can't say "not"." "only" says nothing else was launched.
- **Left out:** "research using data collected on these flights is ongoing, so stay tuned for updates!" (notes)
  - **Rule:** What counts as a fact, rule 10: "Leave out "latest", "current", "now", "then available", and words like them." ("ongoing"); "stay tuned" names nothing (rule 9).
- **Left out:** "All data and analysis software are freely available to the scientific community." (notes)
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words." For the data: HAS_ACCESS_RIGHTS "freely available to the public" says more. "analysis software": rule 9, no particular software is named.
- **Left out:** "primarily" (notes)
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds gives no ground truth triple, and is not part of an instance"
- **Left out:** "the website maintained by A.J. Halford" (notes)
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names." No address, so no instance.
- **Left out:** "current" (notes, "The current release")
  - **Rule:** What counts as a fact, rule 10: "Leave out "latest", "current", "now", "then available", and words like them."
- **Left out:** "BARREL will make all its scientific data products quickly and publicly available but all users are expected to read and follow the BARREL Data Usage Policy listed below." (notes)
  - **Rule:** What counts as a fact, rule 7: "Not facts the record doesn't assert as true: uncertain ones, and ones it requires, requests or recommends." "all users are expected to read and follow" asks it of users. "will make … publicly available": rule 16 of *Writing a classed triple* (HAS_ACCESS_RIGHTS). "quickly": rule 9.
  - **May matter because:** it ties the data to their usage policy.
- **Left out:** "BARREL Data Usage Policy" (notes, the heading)
  - **Rule:** What counts as a fact, rule 3: "the names are formatting, not facts."
- **Left out:** "every effort is made to ensure that these products are of the highest quality" (notes)
  - **Rule:** What counts as a fact, rule 5: "Leave out words such as "great"."
- **Left out:** "However, there may occasionally be issues with either the instruments or data processing that affect the accuracy of data." (notes)
  - **Rule:** What counts as a fact, rule 7: "Not facts the record doesn't assert as true: uncertain ones, and ones it requires, requests or recommends." ("may").
- **Left out:** "When possible, a quality flag is included in higher level data products, and known issues are posted in the BARREL data repository." (notes)
  - **Rule:** What counts as a fact, rule 7: "Not facts the record doesn't assert as true: uncertain ones, and ones it requires, requests or recommends." ("When possible"); "known issues" names no issue (rule 9).
  - **May matter because:** it says where the known issues are posted.
- **Left out:** "You are also strongly encouraged to follow the guidelines below … This will help you ensure that your science results are valid." (notes)
  - **Rule:** What counts as a fact, rule 7: "Not facts the record doesn't assert as true: uncertain ones, and ones it requires, requests or recommends." ("encouraged to").
- **Left out:** the bullets' advice to users ("Users should always use the highest version numbers …", "Users should notify the BARREL PI …", "users should Credit/Acknowledge the BARREL team as follows: We acknowledge the BARREL team … for use of BARREL data.", "Users are also requested to provide the PI with a copy …", "the citation should be transmitted to the PI") (notes)
  - **Rule:** What counts as a fact, rule 7: "Not facts the record doesn't assert as true: uncertain ones, and ones it requires, requests or recommends." ("should", "are requested to").
  - **May matter because:** the acknowledgement text is how the data should be credited.
- **Left out:** "Browse/quick-look plots are not intended for science analysis or publication and should not be used for those purposes without consent of the principal investigator, PI." (notes)
  - **Rule:** What counts as a fact, rule 6: "A ground truth triple can't say "not"."
- **Left out:** "if a BARREL team member is already working on a similar or related topic, they may be able to contribute intellectually" (notes)
  - **Rule:** What counts as a fact, rule 7: "Not facts the record doesn't assert as true: uncertain ones, and ones it requires, requests or recommends." ("may").
- **Left out:** "online copy" (notes)
  - **Rule:** Writing a classed triple, rule 23: "Leave out a type word that only describes the thing," The policy is the instance, AVAILABLE_AT its address.

## "CH1-ORB MOON M3 2 L0 RAW NEAR-IR SPECTRAL IMAGES V1.0" (pool position 21, id 264a9b23-9a86-46a7-ab61-9661230ea667)

3 items, 2 that may matter.

- **Left out:** "CH1-ORB" (title)
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for". It is on no list rule 1's *Names on an official NASA list* names, as written.
  - **May matter because:** in PDS3 naming it is the instrument host, the Chandrayaan-1 orbiter (my reading of the PDS3 naming order; not checked against this data set's catalog files). A search by platform would need it.
  - **Question:** Q6 (b).
- **Left out:** "2" (title, "M3 2 L0")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for"; a bare number is not "L" or "Level" followed by a number.
  - **May matter because:** in PDS3 naming it is most likely the CODMAC level (CODMAC 2 = NASA Level 0, which agrees with "L0"; my reading, not checked for this data set).
  - **Question:** Q6 (b).
- **Left out:** "instrument" (notes, "Moon Mineralogy Mapper (M3) instrument") and "mission" (notes, "Chandrayaan-1 mission")
  - **Rule:** Writing a classed triple, rule 23: "Leave out a type word that only describes the thing,"

## "Flight Data For Tail 655" (pool position 22, id 967275c7-aa2d-4b08-a9db-aff5cf6b7802)

4 items, 1 that may matter.

- **Left out:** "individual flight" (notes, "individual flight recorded data"), that each file holds one flight
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names." No flight is named.
  - **May matter because:** it says how the files are cut.
- **Left out:** "Flight Data" (title) as a fact
  - **Rule:** What counts as a fact, rule 4: "says what type of thing MODIS is: that belongs in its entity class". The flights are not named (rule 9).
- **Left out:** "each with a data structure" (notes), the structure as a thing of its own
  - **Rule:** What counts as a fact, rule 9: "is written for the thing the group belongs to only when it stays true of that thing: what it holds". The 186 parameters are named only by a count, so the structure's contents are written as the dataset's (HAS_ANCILLARY_DATA "sampling rate", "units", "parameter description", "parameter ID").
- **Left out:** "sensor recordings" (notes, the first item of the data structure)
  - **Rule:** What counts as a fact, rule 4: "says what type of thing MODIS is: that belongs in its entity class". The recordings are the values themselves, and name no property.

## "HIRDLS/Aura Level 3 Geopotential Height 1deg Lat Zonal Fourier Coefficients V007 (H3ZFCGPH)" (pool position 24, id 77a0cb5f-7d69-4f13-aeb1-ce1378d7f1a9)

7 items, 2 that may matter.

- **Left out:** what "HIRDLS" stands for (title, and notes "HIRDLS data", "HIRDLS Level 2 profiles")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for". Its entity class, Instrument, is written (ACQUIRED_BY_INSTRUMENT "HIRDLS", twice), by rule 1's *Names on an official NASA list*.
  - **May matter because:** it is the instrument's name, the main search key.
  - The list: GCMD Instruments keywords (version 25.1), "HIRDLS", "High-Resolution Dynamics Limb Sounder"; the CMR record of H3ZFCGPH version 007 lists it under the platform Aura (checked on 2026-10-31).
- **Left out:** "entire" (notes, twice: "the entire mission")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds gives no ground truth triple, and is not part of an instance"
- **Left out:** "mission" (notes, "the entire mission (~3 years) of HIRDLS data"), as FROM_MISSION
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names." No mission is named.
- **Left out:** "may be used to compute values at any longitude" (notes)
  - **Rule:** What counts as a fact, rule 7: "Not facts the record doesn't assert as true: uncertain ones, and ones it requires, requests or recommends." ("may"); and a use is a fact of the work that used the data (rule 9).
  - **May matter because:** it says what the coefficients are for.
- **Left out:** "approach" (notes, "a Kalman filter approach")
  - **Rule:** Writing a classed triple, rule 23: "Leave out a type word that only describes the thing,"
- **Left out:** "separate" (notes, "separate data fields")
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words." Three HAS_VARIABLE triples already say there are three fields.
- **Left out:** the notes' quoted name "HIRDLS/Aura Level 3 Geopotential Height Zonal Fourier Coefficients" as another name of the dataset
  - **Rule:** Writing a classed triple, rule 20: "Write ALSO_KNOWN_AS only when the record gives the other name in words of its own"; the thing the title names is always written as its title (rule 23).

## "OPERA Dynamic Surface Water Extent from Sentinel-1 (Version 1)" (pool position 25, id ed2cea26-ed6c-4138-be69-3d32d4ce4858)

7 items, 4 that may matter.

- **Left out:** "irrespective of cloud conditions and daylight illumination" (notes)
  - **Rule:** What counts as a fact, rule 6: "A ground truth triple can't say "not"." ("irrespective of" means "not affected by").
  - **May matter because:** all-weather, day-and-night mapping is a reason to choose a radar product.
- **Left out:** "that often pose challenges to optical sensors" (notes)
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names." "optical sensors" names no sensor.
- **Left out:** "Forward" (notes, "Forward production … began")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds gives no ground truth triple, and is not part of an instance"
  - **May matter because:** forward processing is new acquisitions, as against reprocessing of older ones, so data from before Sept 2024 may exist.
- **Left out:** "data record" (notes, "the DSWx-S1 data record")
  - **Rule:** Writing a classed triple, rule 23: "Leave out a type word that only describes the thing,"
- **Left out:** "a set of 3" (notes, "Each product is distributed as a set of 3 GeoTIFF … files")
  - **Rule:** What counts as a fact, rule 9: "An amount or a count per member gives no ground truth triple". The file format is written (HAS_FILE_FORMAT).
  - **May matter because:** it says how one granule is packaged.
- **Left out:** "To access the calibration/validation database for OPERA Dynamic Surface Water Extent Products, please contact podaac@podaac.jpl.nasa.gov" (notes)
  - **Rule:** Writing a classed triple, rule 21: "Leave out facts about other datasets, such as a variant of the record's dataset (the same data at another temporal resolution, spatial resolution, or version), or a product made from it." The database is not part of, or an input to, the record's dataset.
  - **May matter because:** it is where the validation data are, and who to ask.
  - **Question:** Q24.
- **Left out:** "an interagency effort" (notes)
  - **Rule:** What counts as a fact, rule 4: "says what type of thing MODIS is: that belongs in its entity class"
