# Left out on purpose

Statements of a [record](../docs/terminology.md#1-records-and-their-text)'s [text](../docs/terminology.md#1-records-and-their-text) that have no [ground truth triple](../docs/terminology.md#4-ground-truth-and-samples), because I decided so or a rule of the [annotation guidelines](guidelines.md) says so. It is the one place where I keep them, so that what the [ground truth](../docs/terminology.md#4-ground-truth-and-samples) leaves out is not lost: some of these words carry information I may want back once an expert answers a question, or once the schema can say it. Terms: [docs/terminology.md](../docs/terminology.md).

One section per record I have annotated, in [pool](../docs/terminology.md#4-ground-truth-and-samples) order. Each item has the exact words (quoted from the record's text, as in `outputs/intermediate_results/020_clean/records.jsonl`), the rule that excluded them (quoted from `guidelines.md`), a *May matter because* line when the words carry information worth keeping, and the question in `questions_for_experts.md` that asks about it, if there is one. Left out here is not the same as wrong: a statement written in other words, or as part of a bigger ground truth triple, is not listed. Nor is a record's "is a data set" (the [describes class](../docs/terminology.md#2-triples) says it). Nor are all the type words that rule 23 of *Writing a classed triple* leaves out ("Take out a type word that only describes the thing,"): the items below name some of them, not every one. When I annotate a record, I add its section; when an expert's answer brings a statement back as a ground truth triple, I delete its item. An item that waits on an expert's answer (its rule is rule 2's "or it waits on an expert's answer") has its would-be ground truth triple in `annotations/pending_triples.csv`, so that step 070 doesn't count an extracted triple that matches it as wrong, or a note "No clear would-be triple:" that says why it has none.

## "NASA Standards and and Technical Assistance Resource Tool" (pool position 0, id 3122be4c-b9d0-4cc9-b6d3-9b96c6e743da)

3 items, none that may matter.

- **Left out:** "is a Web tool" (notes)
  - **Rule:** What counts as a fact, rule 4: "says what kind of thing MODIS is: that belongs in its entity class"
  - A Web tool is what the thing is; its entity class WebTool already says it.
- **Left out:** "great" (notes, "access great NASA technical information")
  - **Rule:** What counts as a fact, rule 5: "Take out words such as "great"."
  - My ground truth triple of the purpose is written without it.
- **Left out:** what "NASA" is (title, and notes, "NASA developed standards and handbooks" and "The NASA Technical Standards Program")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what NASA is. Its entity class, Organization, is written ("NASA developed standards" and "NASA developed handbooks" DEVELOPED_BY_PARTY "NASA", and "NASA Technical Standards Program" PART_OF "NASA"), by rule 1's *Names in a public reference*.
  - The reference: GCMD Providers keywords (version 25.2), the level "NASA" under "GOVERNMENT AGENCIES-U.S. FEDERAL AGENCIES", which holds NASA's centers and offices (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/providers?format=csv, checked on 2026-11-12).

## "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (pool position 1, id cfd6ec3f-1e63-4a77-bc3f-007d45f7e2fc)

6 items, 3 that may matter.

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
  - **May matter because:** checked on 2026-10-30: the Planetary Data System files it as INSTRUMENT_ID = RSI, INSTRUMENT_TYPE = RADIO SCIENCE, the "ROSETTA RADIO SCIENCE INVESTIGATION" (the data set's catalog files, https://archives.esac.esa.int/psa/ftp/INTERNATIONAL-ROSETTA-MISSION/RSI/RO-C-RSI-1-2-3-ESC4-1149-V1.0/CATALOG/). Still left out: the record's text does not say what "RSI" stands for, so its entity class would rest on outside knowledge (rule 1). Decided on 2026-10-31 (audit finding G-2); until then, ACQUIRED_BY_INSTRUMENT "RSI" (Instrument) was a ground truth triple. Reversed later on 2026-10-31: the triple is written again, by rule 1's *Names in a public reference*; what "RSI" stands for stays left out.
  - The list: PDS4 context product urn:esa:psa:context:instrument:ro.rsi, "The Radio Science Investigations (RSI) for the Rosetta Orbiter", an instrument of the instrument host Rosetta Orbiter (https://pds.nasa.gov/data/pds4/context-pds4/instrument/, checked on 2026-10-31).
  - **Question:** Q10 (its part on RSI, settled from this source: see Q10's My notes).
- **Left out:** "comet" (notes, "at the comet 67P")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the thing,"
  - My ground truth triple has the target "67P".
- **Left out:** what "ROSETTA-ORBITER" is (title; the notes name only "Rosetta", in "a Rosetta Radio Science data set")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what ROSETTA-ORBITER is. Its entity class, Platform, is written (FROM_PLATFORM "ROSETTA-ORBITER"), by rule 1's *Names in a public reference*.
  - The list: PDS4 context product urn:esa:psa:context:instrument_host:spacecraft.ro, "The Rosetta Orbiter Spacecraft", of type Spacecraft (https://pds.nasa.gov/data/pds4/context-pds4/instrument_host/spacecraft.ro_1.1.xml, checked on 2026-11-12).
- **Left out:** what "Rosetta" is (notes, "a Rosetta Radio Science data set")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what Rosetta is. Its entity class, Mission, is written (FROM_MISSION "Rosetta"), by rule 1's *Names in a public reference*.
  - The reference: PDS4 context product urn:esa:psa:context:investigation:mission.international_rosetta_mission, "The International Rosetta Mission", also titled "ROSETTA", of type Mission (https://pds.nasa.gov/data/pds4/context-pds4/investigation/mission.international_rosetta_mission_1.1.xml, checked on 2026-11-12).

## "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" (pool position 2, id 6cfafd07-40f1-46da-9d92-36c2bb319f0b)

2 items, none that may matter. The record has no list of other temporal resolutions or spatial resolutions of its product ("daily" is its own, in "provides daily snow cover"), so nothing of a product family is left out here.

- **Left out:** "satellite" (notes, "the Aqua satellite")
  - **Rule:** Writing a classed triple, rule 23: "write "Aqua", not "Aqua satellite", since its entity class, Platform, already says what it is"
- **Left out:** "Each data granule contains" (notes), that the data come in granules
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words."
  - My ground truth triple HAS_GRANULE_DURATION "5 minutes" already says each granule covers 5 minutes, which only makes sense if the data come in granules.

## "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005" (pool position 3, id 2705e0d1-95e7-4588-813b-ca91a6da94ff)

3 items, 1 that may matter.

- **Left out:** "collaboratively" (notes, "developed collaboratively between")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds gives no ground truth triple, and is taken out of the instance: its subject would be that fact, not a thing the record names." "collaboratively" says only how NASA and CONAE developed the mission (together); the two developers are ground truth triples of their own (DEVELOPED_BY_PARTY: NASA and CONAE). Saying how a fact holds needs a fact about a fact, a qualifier kept with the ground truth triple it holds for (as Wikidata's statement qualifiers do), which is future work: docs/improvements.md, *Rule 19 can lose which fact a qualifier went with*, option 4 (recommended on 2026-10-27, decided on 2026-10-30). Decided on 2026-10-31; until then this item waited on the experts' answer to Q27 (rule 2 of *What counts as a fact*).
  - **May matter because:** it says how NASA and CONAE worked on the mission: together.
  - **Question:** Q27 (settled on 2026-10-31: see Q27's My notes).
- **Left out:** what "U.S." is (notes, "the U.S. National Aeronautics and Space Administration (NASA)")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what U.S. is. Its entity class, Country, is written (BASED_IN "U.S."), by rule 1's *Names in a public reference*.
  - The reference: Wikidata, United States (Q30), also named "the U.S.", "country located primarily in North America", an instance of "country" and of "sovereign state" (https://www.wikidata.org/wiki/Q30, checked on 2026-11-13). Rule 1's official NASA lists (the GCMD Instruments, Platforms and Providers keywords, and the PDS4 context products) are not lists of countries, and they were not searched for it.
- **Left out:** what "Argentina" is (notes, "Argentina's space agency")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what Argentina is. Its entity class, Country, is written (BASED_IN "Argentina"), by rule 1's *Names in a public reference*.
  - The reference: Wikidata, Argentina (Q414), "country in South America", an instance of "country" and of "sovereign state" (https://www.wikidata.org/wiki/Q414, checked on 2026-11-13). Rule 1's official NASA lists (the GCMD Instruments, Platforms and Providers keywords, and the PDS4 context products) are not lists of countries, and they were not searched for it.

## "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (pool position 4, id 03a09af3-081e-4db6-9e3b-ea7c0e3138bd)

The dense record: its notes describe a whole family of products (several temporal resolutions, two spatial resolutions, day and night, two kinds of temperature) and the title names the one this record is. 15 items, 9 that may matter. The product family as a whole is asked in Q24.

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
  - **Rule:** Writing a classed triple, rule 24: "A verb or participle that says only that something was done to the data ("corrected", "calibrated", "detrended", "binned", "mapped", "edited", "convert", "weighted") names no method". The record names the grid and the projection but only says the pixels "are binned" and "mapped", so I wrote BINNED_INTO (renamed ON_GRID on 2026-10-31) and MAPPED_INTO and no PRODUCED_USING_ALGORITHM. Since 2026-11-12 the subject of the two ground truth triples is the record's dataset, whose values are on the grid and on the map (ON_GRID: "its values are given on the cells or points of this Grid"); until then it was "pixels", the input of the step.
  - **May matter because:** it is how the dataset was made, step by step.
  - **Question:** Q7.
- **Left out:** "NASA" (notes, "global NASA skin sea surface temperature (SST) products")
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words." By rule 19 of *Writing a classed triple* (*Whose fact it is*), "NASA" qualifies the products, which are the record's dataset, a standalone entity class, so its fact would be the record's dataset's: who made the products. The record states that fact more precisely in "The NASA MODIS L3 SST data products are generated by the NASA Ocean Biology Processing Group (OBPG)", my ground truth triple DEVELOPED_BY_PARTY "NASA Ocean Biology Processing Group (OBPG)", whose wording contains "NASA" as a whole word and says more (rule 23). Rule 21 does not leave it out: the record's dataset is one of these products. Decided on 2026-10-31; until then this item waited on the experts' answer to Q28 (a) (rule 2 of *What counts as a fact*).
  - **May matter because:** it says whose products these are: NASA's.
  - **Question:** Q28 (a) (settled on 2026-10-31: see Q28's My notes).
- **Left out:** "at a variety of spatial resolutions" (notes, "MODIS captures data in 36 spectral bands at a variety of spatial resolutions")
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names." The words name no value.
- **Left out:** "projection" (notes, "Platte Carre projection")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the thing,"
  - **Question:** Q15 (whether a coordinate system is a map projection); its part on "Platte Carre" was settled on 2026-10-26: it is the record's spelling of "Plate Carrée", the equidistant cylindrical projection on the equator (see Q15's My notes).
- **Left out:** "satellite" (notes, "the Aqua satellite")
  - **Rule:** Writing a classed triple, rule 23: "write "Aqua", not "Aqua satellite", since its entity class, Platform, already says what it is"
- **Left out:** "which can be found at https://doi.org/10.5067/MODAM-8D4N4" (notes), the DOI of the previous v2014.1 datasets
  - **Rule:** Writing a classed triple, rule 21: "Leave out facts about other datasets, such as a variant of the record's dataset (the same data at another temporal resolution, spatial resolution, or version), or a product made from it." The DOI is the address of the older datasets, not of this one; the ground truth triple has only "R2019.0" SUPERSEDES "v2014.1" (until 2026-11-12 its subject instance was "V2019.0").
  - **May matter because:** it is where the superseded release is.
  - **Question:** Q19, and Q24 (the releases of a product family).

- **Left out:** "his team" (notes, "Peter Minnett and his team at the Rosenstiel School of Marine and Atmospheric Science (RSMAS)  are responsible for sea surface temperature algorithm development, error statistics and quality flagging")
  - **Rule:** Writing a classed triple, rule 22: "A list: one ground truth triple per item. Apply rule 19 first. Then write one ground truth triple per item of the list, in which that item alone takes the list's place (the subject or the object)," which splits the subject into "Peter Minnett" and "his team"; then What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names." "his team" names no team, so only "Peter Minnett" keeps the four ground truth triples (decided on 2026-10-30).
  - **May matter because:** the record gives the responsibilities and the affiliation to the team as well as to Peter Minnett; the team's share is lost.
- **Left out:** "NSST" (notes, "The first is a skin SST produced for both day and night (NSST) observations"), as another wording of "skin SST"
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for." "(NSST)" follows "night", not "skin SST", so it is not a name with its abbreviation in parentheses (Writing a classed triple, rule 20: "A name with its own abbreviation, another name or code of its own, or a short note in parentheses is one instance, as written."), and the record does not say what NSST names. The ground truth triples use "skin SST" (decided on 2026-10-30, audit finding G7).
  - **May matter because:** NSST may be the product's own name; other records of the family may use it. Checked on 2026-10-30: NSST names NASA's nighttime long-wave (11 µm) SST product, "Aqua MODIS Level-3 Global Mapped 11µm Nighttime Sea Surface Temperature (NSST) Data, version R2019.0" (https://data.nasa.gov/dataset/aqua-modis-level-3-global-mapped-11m-nighttime-sea-surface-temperature-nsst-data-version-r), so it is not another wording of this record's day-and-night "skin SST"; it stays left out (rule 1 of *What counts as a fact*: the record doesn't explain it).
  - **Question:** Q18, (d). Its meaning may later come from the model, checked against a source: docs/improvements.md, *Knowledge enrichment from the model, verified and labelled* (080).
- **Left out:** what "NASA" is (notes, "Aqua was launched by NASA" and "the NASA Ocean Biology Processing Group (OBPG)")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what NASA is. Its entity class, Organization, is written ("Aqua" LAUNCHED_BY_PARTY "NASA", and "NASA Ocean Biology Processing Group (OBPG)" PART_OF "NASA"), by rule 1's *Names in a public reference*.
  - The reference: GCMD Providers keywords (version 25.2), the level "NASA" under "GOVERNMENT AGENCIES-U.S. FEDERAL AGENCIES", which holds NASA's centers and offices (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/providers?format=csv, checked on 2026-11-12).
- **Left out:** what "JPL" stands for (notes, "JPL acquires MODIS ocean L3 SST data from the OBPG and is the official Physical Oceanography Data Archive (PO.DAAC) for SST")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what JPL is. Its entity class, Organization, is written ("JPL" OBTAINS_DATA_FROM "NASA Ocean Biology Processing Group (OBPG)", and "JPL" SERVES_AS "official Physical Oceanography Data Archive (PO.DAAC) for SST"), by rule 1's *Names in a public reference*.
  - The reference: GCMD Providers keywords (version 25.2), "NASA/JPL", "Jet Propulsion Laboratory, NASA" (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/providers?format=csv, checked on 2026-11-12).
- **Left out:** what "Earth" is (notes, "Earth Observation Satellites (EOS)" and the purposes of Aqua)
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what Earth is. Its entity class, CelestialBody, is written (HAS_TARGET "Earth"), by rule 1's *Names in a public reference*.
  - The reference: PDS4 context product urn:nasa:pds:context:target:planet.earth, "Earth", of type Planet (https://pds.nasa.gov/data/pds4/context-pds4/target/planet.earth_1.1.xml, checked on 2026-11-12).

## "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0" (pool position 5, id 99dff022-24ac-48cb-bc83-09fec8b90ad7)

4 items, 1 that may matter.

- **Left out:** "detrended" as a method (notes, "The nominal fast neutron count rates were detrended using the GRaND epithermal neutron map")
  - **Rule:** Writing a classed triple, rule 24: "A verb or participle that says only that something was done to the data ("corrected", "calibrated", "detrended", "binned", "mapped", "edited", "convert", "weighted") names no method". The record says the rates "were detrended", only a verb; I wrote the two COMPUTED_FROM triples (the rates, the epithermal map) and no PRODUCED_USING_ALGORITHM.
  - **May matter because:** it is the method that made the residual map.
  - **Question:** Q7 (settled for now, not asked), Q12 (c) for the map as an input.
- **Left out:** what "DAWN" is (title)
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what DAWN is. Its entity class, Platform, is written (FROM_PLATFORM "DAWN"), by rule 1's *Names in a public reference*.
  - The list: PDS4 context product spacecraft.dawn, "The Dawn Spacecraft", of type Spacecraft (https://pds.nasa.gov/data/pds4/context-pds4/instrument_host/spacecraft.dawn_1.3.xml, checked on 2026-11-11).
- **Left out:** what "GRaND" stands for (title, "GRAND", and notes, "the GRaND plus Z boron loaded sensor" and "the GRaND epithermal neutron map")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what GRaND is. Its entity class, Instrument, is written (ACQUIRED_BY_INSTRUMENT "GRaND", twice, and "GRaND plus Z boron loaded sensor" PART_OF "GRaND"), by rule 1's *Names in a public reference*.
  - The list: PDS4 context product urn:nasa:pds:context:instrument:dawn.grand, "The Gamma Ray and Neutron Detector (GRAND) for Dawn", an instrument of the instrument host spacecraft.dawn (https://pds.nasa.gov/data/pds4/context-pds4/instrument/dawn.grand_1.2.xml, checked on 2026-11-12).
- **Left out:** what "Vesta" is (title, "VESTA", and notes, "the average atomic mass on Vesta")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what Vesta is. Its entity class, CelestialBody, is written (HAS_TARGET "Vesta"), by rule 1's *Names in a public reference*.
  - The reference: PDS4 context product urn:nasa:pds:context:target:asteroid.4_vesta, "4 Vesta", also titled "Vesta", of type Asteroid (https://pds.nasa.gov/data/pds4/context-pds4/target/asteroid.4_vesta_1.3.xml, checked on 2026-11-12).

## "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (pool position 6, id 4c64f3ed-39b4-4f95-95a0-022898ba47a4)

6 items, 2 that may matter. The record's decisions are complete (its ground truth triples are in `annotations/ground_truth/batch_001.csv`, a demo batch): these items are the ones I decided or am waiting on.

- **Left out:** "surface reflectance" and "MCD19A1N" (notes, "used to calculate the MAIAC Land Surface Bidirectional Reflectance Factor (BRF) or surface reflectance, MCD19A1N product"), as other wordings of the product
  - **Rule:** Writing a classed triple, rule 21: "Leave out facts about other datasets, such as a variant of the record's dataset (the same data at another temporal resolution, spatial resolution, or version), or a product made from it." The three wordings name one product, made from the record's dataset, each once; "MAIAC Land Surface Bidirectional Reflectance Factor (BRF)" ALSO_KNOWN_AS "surface reflectance" and HAS_IDENTIFIER "MCD19A1N" would be facts about that product, so they are left out. My ground truth triple "MAIAC Land Surface Bidirectional Reflectance Factor (BRF)" COMPUTED_FROM the record's dataset uses the first wording (rule 23: on a tie, the one the record gives first). Until 2026-10-31 this item cited rule 23 (third audit, finding L-5) (decided on 2026-10-31, audit finding G-11; until then its subject instance was "MCD19A1N", and the first wording was left out as what that product holds, by rule 21).
  - **May matter because:** "MCD19A1N" is the product's short name, by which a search would find it.
  - **Question:** Q20 (c), now its (b) (withdrawn on 2026-10-31, settled from sources: see Q20's My notes).
- **Left out:** the same words as a purpose of this dataset ("calculate the MAIAC Land Surface Bidirectional Reflectance Factor (BRF) or surface reflectance")
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words." "used to calculate" the product is the fact my ground truth triple "MAIAC Land Surface Bidirectional Reflectance Factor (BRF)" COMPUTED_FROM the record's dataset already states; and the ground truth schema's Purpose is "an aim something is meant to achieve", while the record says "used to calculate", not that the dataset is meant for it. I decided this on 2026-10-25; the rule was named on 2026-10-31.
  - **May matter because:** it is what the dataset is for.
  - **Question:** Q9 ("used to"; settled on 2026-10-31, a use is not a purpose: see Q9's My notes).
- **Left out:** "G" (title, "L2G")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for". "L2" is a processing level by a convention rule 1 names ("L" or "Level" followed by a number (a processing level)); the facts "G" may stand for are written from the notes' "gridded Level 2 product" (HAS_PROCESSING_LEVEL "Level 2", HAS_SPATIAL_REPRESENTATION "gridded"), and the record doesn't say what "G" stands for (decided on 2026-11-01, the review of the second opinion's facts).
- **Left out:** what "SIN" stands for (title, "SIN Grid")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for". The grid is written whole, ON_GRID "SIN Grid" (Writing a classed triple, rule 11: "A name stays whole: rules 19, 22 and 24 never split or shorten a name"), so no MAPPED_INTO "SIN" (decided on 2026-11-01, the review of the second opinion's facts; the same in the record at pool position 7).
- **Left out:** what "Terra" is (title, "MODIS/Terra+Aqua", and notes, "Combined Terra and Aqua")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what Terra is. Its entity class, Platform, is written (FROM_PLATFORM "Terra"), by rule 1's *Names in a public reference*.
  - The list: GCMD Platforms keywords (version 25.2), "Terra", "Earth Observing System, Terra (AM-1)" (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/platforms?format=csv, checked on 2026-11-12).
- **Left out:** what "Aqua" is (title, "MODIS/Terra+Aqua", and notes, "Combined Terra and Aqua")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what Aqua is. Its entity class, Platform, is written (FROM_PLATFORM "Aqua"), by rule 1's *Names in a public reference*.
  - The list: GCMD Platforms keywords (version 25.2), "Aqua", "Earth Observing System, Aqua" (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/platforms?format=csv, checked on 2026-11-12).

## "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" (pool position 7, id d5477563-0415-4e65-ab7c-d4bc9ed809e5)

17 items, 9 that may matter.

- **Left out:** what "MODIS" stands for (title, "MODIS/Terra", and notes, "Terra MODIS")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for"
  - **May matter because:** its entity class, Instrument, is written (ACQUIRED_BY_INSTRUMENT "MODIS"), by rule 1's *Names in a public reference*.
  - The list: GCMD Instruments keywords (version 25.1), "MODIS", "Moderate-Resolution Imaging Spectroradiometer"; the CMR record of MOD11A1 version 006 lists it under the platform Terra (checked on 2026-10-31).
- **Left out:** "in a 1,200 by 1,200 km grid" (notes)
  - **Rule:** What counts as a fact, rule 1: "Only what the record states. Never add what you know from elsewhere". The record says only that the data are "in a 1,200 by 1,200 km grid"; that this is one tile of the MODIS sinusoidal grid, the ground each file covers, comes from NASA LAADS, not from the record, and the ground truth schema has no predicate for the ground each file covers (HAS_GRANULE_DURATION is the time each file covers; HAS_SPATIAL_RESOLUTION, the ground each value covers). Decided on 2026-10-31; until then this item waited on the experts' answer to Q1 (c) (rule 2 of *What counts as a fact*). The grid itself is now the ground truth triple ON_GRID "SIN Grid".
  - **May matter because:** it is the size of one tile of the MODIS sinusoidal grid, which is how much ground each file covers. Checked on 2026-10-30: "Each tile has fixed Earth-locations covering an area of approximately 1200 x 1200 km (10 x 10 degrees at the equator)" (NASA LAADS, "What are the Product Spatial Formats?", https://landweb.modaps.eosdis.nasa.gov/help/prod_format).
  - **Question:** Q1 (c) (settled on 2026-10-31: see Q1's My notes).
- **Left out:** "per-pixel" (notes, "provides daily per-pixel Land Surface Temperature")
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words." The ground truth triple HAS_SPATIAL_RESOLUTION "1 kilometer (km)" already says how much ground each value covers.
- **Left out:** "(LST&E)" (notes, "Land Surface Temperature and Emissivity (LST&E)")
  - **Rule:** Writing a classed triple, rule 22: "A list that the record gives one abbreviation of its own is a name, and stays whole, only when the abbreviation stands for one thing; when it stands for several things, it is a list, and the abbreviation belongs to no item." "LST&E" stands for two quantities, so the list splits and "(LST&E)" belongs to neither item (the test was written on 2026-10-31, third audit, findings R-4 and G-5; until then this item cited only "A list: one ground truth triple per item.").
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
- **Left out:** "surface temperature bands" and "pixel temperature value" as things of their own (notes, "the daytime and nighttime surface temperature bands" and "The pixel temperature value is derived from")
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words." "surface temperature" is the "Land Surface Temperature" already written (rule 23: the wording that says more); "bands" is a type word (rule 23: "Take out a type word that only describes the thing,"). "daytime" and "nighttime" are ground truth triples of their own (OBSERVED_AT_TIME_OF_DAY, rule 19 of *Writing a classed triple*). "pixel temperature value" is the record's dataset's own values: their input is written for the dataset (COMPUTED_FROM "MOD11_L2", rule 23, *The thing the title names*), and what they measure is the "Land Surface Temperature" already written (added to this item on 2026-11-01, the review of the second opinion's facts).
- **Left out:** "associated" (notes, "associated quality control assessments")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds gives no ground truth triple, and is taken out of the instance: its subject would be that fact, not a thing the record names." "associated" says only that the quality control assessments go with the temperature bands, how the fact HAS_ANCILLARY_DATA "quality control assessments" holds. Saying how a fact holds needs a fact about a fact, a qualifier kept with the ground truth triple it holds for (as Wikidata's statement qualifiers do), which is future work: docs/improvements.md, *Rule 19 can lose which fact a qualifier went with*, option 4 (recommended on 2026-10-27, decided on 2026-10-30). Decided on 2026-10-31; until then this item waited on the experts' answer to Q27 (rule 2 of *What counts as a fact*).
  - **May matter because:** it says which values the quality control assessments go with: the temperature bands.
  - **Question:** Q27 (settled on 2026-10-31: see Q27's My notes).
- **Left out:** "significant" (notes, "due to [significant loss of data retrieval](https://landweb.modaps.eosdis.nasa.gov/displayissue?id=98) following the Constellation Exit Maneuvers")
  - **Rule:** What counts as a fact, rule 5: "Take out words such as "great"." "significant" is a judgement of how much was lost, as in the record "Ensemble X-Ray Variability of AGN in 2XMMi-DR3"; my two ground truth triples write the issue as "loss of data retrieval following the Constellation Exit Maneuvers" (decided on 2026-10-31, audit finding G-4).
- **Left out:** "Known Issues" (notes, the heading)
  - **Rule:** What counts as a fact, rule 3: "A heading inside a text field, a line of its own that only names the passage below it ("Known Issues", "BARREL Data Usage Policy"), is formatting too, and gives no ground truth triple."
- **Left out:** the other products in "Production of V6 Terra MODIS Land Surface Temperature and Emissivity (LST&E) data products was discontinued" (notes)
  - **Rule:** Writing a classed triple, rule 21: "Leave out facts about other datasets, such as a variant of the record's dataset (the same data at another temporal resolution, spatial resolution, or version), or a product made from it." The sentence is about every Version 6 Terra MODIS land surface temperature and emissivity product; I wrote its two facts for this dataset only (PRODUCTION_DISCONTINUED_ON, PRODUCTION_DISCONTINUED_DUE_TO).
  - **May matter because:** the date and its cause hold for the whole family of these products.
  - **Question:** Q24.
- **Left out:** "known issues" as what the page is about (notes, "For complete information about known issues please refer to")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds gives no ground truth triple, and is taken out of the instance: its subject would be that fact, not a thing the record names." "about known issues" says only what the details at the page are about, how the fact DOCUMENTED_AT holds. The field's practice records the same fact and no more: W3C DCAT's `dcat:landingPage` and FOAF's `foaf:page` ("A page or document about this thing") link a thing to a page about it and say nothing of what the page covers. Saying how a fact holds needs a fact about a fact, a qualifier kept with the ground truth triple it holds for (as Wikidata's statement qualifiers do), which is future work: docs/improvements.md, *Rule 19 can lose which fact a qualifier went with*, option 4 (recommended on 2026-10-27, decided on 2026-10-30). Decided on 2026-10-31; until then this item waited on the experts' answer to Q28 (b) (rule 2 of *What counts as a fact*).
  - **May matter because:** a search for a dataset's known issues would need it.
  - **Question:** Q28 (b) (settled on 2026-10-31: see Q28's My notes).
- **Left out:** "MODIS/VIIRS Land Quality Assessment website" (notes, "[MODIS/VIIRS Land Quality Assessment website](https://landweb.modaps.eosdis.nasa.gov/knownissue?sensor=MODIS&sat=Terra&as=6)"), as the name of the page
  - **Rule:** Writing a classed triple, rule 20: "Write ALSO_KNOWN_AS only when the record gives the other name in words of its own". The words are the text of the page's link, not words of the record's own that give the page another name, and the ground truth schema's WebPage is "a web address, written as the address itself". My ground truth triple has the page as its address (DOCUMENTED_AT). Until 2026-10-31 the page had ALSO_KNOWN_AS "MODIS/VIIRS Land Quality Assessment", and this item left out only the type word "website" (third audit, finding G-1).
  - **May matter because:** it is the page's name, by which a person would look for it.
- **Left out:** "product" (notes, "[MOD11_L2](https://doi.org/10.5067/MODIS/MOD11_L2.006) swath product")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the thing,"; "swath" is a ground truth triple of its own (HAS_SPATIAL_REPRESENTATION, as "gridded" for the record at pool position 6).
- **Left out:** what "SIN" stands for (title, "SIN Grid")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for". The grid is written whole, ON_GRID "SIN Grid" (Writing a classed triple, rule 11: "A name stays whole: rules 19, 22 and 24 never split or shorten a name"), so no MAPPED_INTO "SIN" (decided on 2026-11-01, the review of the second opinion's facts; the same in the record at pool position 6).
- **Left out:** what "Terra" is (title, "MODIS/Terra", and notes, "Terra MODIS")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what Terra is. Its entity class, Platform, is written (FROM_PLATFORM "Terra", and "MODIS" ABOARD "Terra"), by rule 1's *Names in a public reference*.
  - The list: GCMD Platforms keywords (version 25.2), "Terra" (checked on 2026-11-11).

## "ROSETTA-ORBITER PRELANDING OSINAC 2 EDR MTP003 V2.0" (pool position 8, id 938ee451-561c-492d-9e24-fe9a1048b835)

A held-out record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. 7 items, 2 that may matter.

- **Left out:** "2" (title, "OSINAC 2")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for"; a bare number is not "L" or "Level" followed by a number.
  - **Question:** Q6 (b).
- **Left out:** "EDR" (title)
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for"
  - The record "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0" leaves out its title's "RDR" the same way.
  - **Question:** Q6 (b).
- **Left out:** "MTP003" (title)
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for"
  - **May matter because:** it tells this dataset from its siblings, as "MTP020" does in the record "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0" (its item; not checked for this record).
  - The drafted triple HAS_MISSION_PHASE "MTP003" (drafted by Gemini 2.5 Pro, never finished) is deleted.
  - **Question:** Q6 (b).
- **Left out:** "supersedes previous deliveries of the same dataset" (notes, "This version V2.0 supersedes previous deliveries of the same dataset.")
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names."
  - "previous deliveries of the same dataset" names no particular delivery or version, so a SUPERSEDES triple would have no object the record names. The record "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" names the release it replaces ("the previous v2014.1 datasets"), and this record does not. The drafted triple "V2.0" SUPERSEDES "previous deliveries of the same dataset" is deleted.
  - **May matter because:** it says that earlier deliveries of this dataset exist and are replaced.
- **Left out:** "phase", "mission" and "comet" (notes, "the PRELANDING phase of the Rosetta mission at the comet 67P")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the thing,"
  - My ground truth triples have the phase "PRELANDING", the mission "Rosetta" and the target "67P"; the type words say what kind of thing each is, which their entity classes already say.
- **Left out:** what "ROSETTA-ORBITER" is (title; the notes name only "the Rosetta mission")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what ROSETTA-ORBITER is. Its entity class, Platform, is written (FROM_PLATFORM "ROSETTA-ORBITER"), by rule 1's *Names in a public reference*.
  - The list: PDS4 context product urn:esa:psa:context:instrument_host:spacecraft.ro, "The Rosetta Orbiter Spacecraft", of type Spacecraft, also titled "ROSETTA-ORBITER" (https://pds.nasa.gov/data/pds4/context-pds4/instrument_host/spacecraft.ro_1.1.xml, checked on 2026-11-13).
- **Left out:** what "OSIRIS" stands for (notes, inside the name "OSIRIS Narrow Angle Camera")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record names "OSIRIS" only inside the camera's name and never says what it is. Its entity class, Instrument, is written ("OSIRIS Narrow Angle Camera" PART_OF "OSIRIS", with the source text "OSIRIS Narrow Angle Camera", by rule 17's *A name's facts*), by rule 1's *Names in a public reference*.
  - The reference: Wikidata, Optical, Spectroscopic, and Infrared Remote Imaging System (Q7098805), also named "OSIRIS", "scientific instrument on the Rosetta spacecraft", an instance of "space instrument" (https://www.wikidata.org/wiki/Q7098805, checked on 2026-11-13). No official NASA list names it: the PDS4 context products have entries for its two cameras (urn:esa:psa:context:instrument:ro.osinac and ro.osiwac) and none for OSIRIS itself.

## "STARDUST 9P/TEMPEL 1 DFMI 2/3 NEXT V1.0" (pool position 9, id dc4ff01b-12f0-4235-8c8a-afb4bfb3bdbb)

4 items, 2 that may matter.

- **Left out:** "comet" (notes, "encounter with comet 9P/Tempel 1" and "the entire comet encounter")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the thing,"
  - My ground truth triple has the target "9P/Tempel 1", and the phase "encounter".
- **Left out:** "convert" as a method (notes, "The RDR data convert the EDR (raw) sensor data")
  - **Rule:** Writing a classed triple, rule 24: "A verb or participle that says only that something was done to the data ("corrected", "calibrated", "detrended", "binned", "mapped", "edited", "convert", "weighted") names no method". The record says the RDR data "convert" the EDR data, only a verb; I wrote "RDR data" COMPUTED_FROM "EDR (raw) sensor data" and no PRODUCED_USING_ALGORITHM.
  - **May matter because:** it is how the RDR data are made from the raw data.
  - **Question:** Q7.
- **Left out:** "entire" (notes, "from the entire comet encounter")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds gives no ground truth triple, and is taken out of the instance: its subject would be that fact, not a thing the record names." "EDR (raw) sensor data" HAS_MISSION_PHASE "encounter" says the EDR (raw) sensor data come from the encounter; "entire" says only how much of it, how that fact holds (until 2026-11-01 the phase was the RDR data's: "RDR data" HAS_MISSION_PHASE "encounter"; the review of the second opinion's facts, judgment call A). Saying how a fact holds needs a fact about a fact, a qualifier kept with the ground truth triple it holds for (as Wikidata's statement qualifiers do), which is future work: docs/improvements.md, *Rule 19 can lose which fact a qualifier went with*, option 4 (recommended on 2026-10-27, decided on 2026-10-30). Decided on 2026-10-31; until then this item waited on the experts' answer to Q27 (rule 2 of *What counts as a fact*).
  - **May matter because:** it says the data cover all of the encounter, not a part of it. Checked on 2026-10-31: that is the EDR (raw) data; the RDR data cover the encounter "up to before the start of the anomaly" (the data set's catalog file, https://pdssbn.astro.umd.edu/holdings/sdu-c_d-dfmi-2_3-next-tempel1-v1.0/catalog/; see Q5's My notes). Until 2026-10-31 this line said "it says the RDR data cover all of the encounter, not a part of it."
  - **Question:** Q27 (settled on 2026-10-31: see Q27's My notes).
- **Left out:** what "STARDUST" is (title; the notes name only "the Stardust-NExT mission")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what STARDUST is. Its entity class, Platform, is written (FROM_PLATFORM "STARDUST"), by rule 1's *Names in a public reference*.
  - The list: PDS4 context product spacecraft.sdu, "The Stardust Spacecraft", of type Spacecraft (https://pds.nasa.gov/data/pds4/context-pds4/instrument_host/spacecraft.sdu_1.3.xml, checked on 2026-11-11).

## "ROSETTA-ORBITER 67P/CAL ALICE 2 ESC1 V1.0" (pool position 10, id 3bceffb4-f01e-433c-af79-42b9d9427231)

4 items, 1 that may matter.

- **Left out:** "CAL" (title, "67P/CAL")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for"
  - **May matter because:** checked on 2026-10-30: "CAL" is the PDS3 target "CALIBRATION" in the data set name (TARGET_NAME = "CALIBRATION"; the PDS3 Standards Reference lists "CAL Calibration" among target IDs, https://pds.nasa.gov/datastandards/pds3/standards/sr/Chapter06.pdf), so the data include observations of calibration targets. It does not mean "calibrated": the data set says its data are uncalibrated, CODMAC level 2 (https://archives.esac.esa.int/psa/ftp/INTERNATIONAL-ROSETTA-MISSION/ALICE/RO-C-CAL-ALICE-2-ESC1-V1.0/CATALOG/DATASET.CAT). My earlier reading ("calibration data") was close but imprecise. Still left out: the record's text does not explain it (rule 1).
  - **Question:** Q6 (b).
- **Left out:** "mission phase" (notes, "comet escort 1 mission phase")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the thing,"
  - My ground truth triple has the phase "comet escort 1", its target "67P/Churyumov-Gerasimenko" a triple of its own (rule 19 of *Writing a classed triple*).
- **Left out:** what "Rosetta Orbiter" is (title, "ROSETTA-ORBITER", and notes, "the Rosetta Orbiter ALICE UV Spectrometer")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what the Rosetta Orbiter is. Its entity class, Platform, is written (FROM_PLATFORM "Rosetta Orbiter", and "Rosetta Orbiter ALICE UV Spectrometer" ABOARD "Rosetta Orbiter"), by rule 1's *Names in a public reference*.
  - The list: PDS4 context product urn:esa:psa:context:instrument_host:spacecraft.ro, "The Rosetta Orbiter Spacecraft", of type Spacecraft (https://pds.nasa.gov/data/pds4/context-pds4/instrument_host/spacecraft.ro_1.1.xml, checked on 2026-11-12).
- **Left out:** what "67P/Churyumov-Gerasimenko" is (title, "67P", and notes, "the 67P/Churyumov-Gerasimenko comet escort 1 mission phase", where "comet" is a word of the phase's name)
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what 67P/Churyumov-Gerasimenko is. Its entity class, CelestialBody, is written (HAS_TARGET "67P/Churyumov-Gerasimenko", of the record's dataset and of "comet escort 1"), by rule 1's *Names in a public reference*.
  - The reference: PDS4 context product urn:nasa:pds:context:target:comet.67p_churyumov-gerasimenko, "67P/Churyumov-Gerasimenko", of type Comet (https://pds.nasa.gov/data/pds4/context-pds4/target/comet.67p_churyumov-gerasimenko_1.1.xml, checked on 2026-11-12).

## "Shawano (SWNO) Ground-based Vector Magnetic Field (L2) 0.5 s Data" (pool position 11, id 1e16bbd4-0f3f-4f88-bda1-55a553c1282e)

A held-out record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. 3 items, all 3 that may matter.

- **Left out:** what "WI" stands for (notes, "Shawano, WI")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what WI is. Wikidata's Wisconsin (Q1537) has "WI" among its other names and is an instance of "U.S. state", a kind that fits no entity class of the ground truth schema (Country is "a nation", and SpatialExtent is "an area the data cover", which the record does not say of Wisconsin), so the name stays unexplained (https://www.wikidata.org/wiki/Q1537, checked on 2026-11-13). "Shawano, WI" and "Shawano (SWNO)" name one station, written "Shawano (SWNO)" (rule 23 of *Writing a classed triple*, test 4: the wording the record gives first).
  - **May matter because:** it gives the state the station is in, which a search by place would need.
- **Left out:** what "GEO" stands for (notes, "Station Location: (GEO Latitude 44.8, Longitude 271.4)")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for"
  - The record does not say which coordinate system "GEO" names, so no HAS_COORDINATE_SYSTEM triple is written. "GEO" stays in the instance of the station's position, as written (rule 11 of *Writing a classed triple*): "Shawano (SWNO)" LOCATED_AT "GEO Latitude 44.8, Longitude 271.4".
  - **May matter because:** my reading, not checked: geographic coordinates, as against the magnetic coordinates that magnetometer stations also give.
- **Left out:** "THEMIS EPO/UCLA Network" (notes, the last item of the notes' list)
  - **Rule:** What counts as a fact, rule 1: "Only what the record states." The notes name the network at the end of a list of the dataset's labels, with no words that say how the network and the dataset or the station are related (whether the station belongs to the network, or the network provides the data). Its kind word, "Network", fits no single entity class: a network of ground stations is not one Platform, and could be read as an Organization or as a Mission. No reference of rule 1's *Names in a public reference* names it: the GCMD Platforms keywords (version 25.2) have "THEMIS", the satellites, and Wikidata has no entry named "THEMIS EPO" (checked on 2026-11-13). The "/" stays inside the name (rule 22 of *Writing a classed triple*, *Lists joined by "/" or "+"*: "UCLA" is never named alone).
  - **May matter because:** it names the network the station belongs to, which a search by network would need.

## "Ensemble X-Ray Variability of AGN in 2XMMi-DR3" (pool position 12, id bb1fe4b0-6543-42e3-9386-acbab0b37ad4)

The notes are mostly the abstract of the study the table comes from; whether a study's aim, method and findings belong in the ground truth was asked in Q26, settled on 2026-10-31: the study's aim and method are ground truth triples of the record's dataset (HAS_PURPOSE, PRODUCED_USING_ALGORITHM), and its background and findings are left out (rule 8 of *What counts as a fact*, *A study a record tells*). 27 items, 19 that may matter.

- **Left out:** "The X-ray variability of active galactic nuclei (AGN) has been most often investigated with studies of individual, nearby sources, and only a few ensemble analyses have been applied to large samples in wide ranges of luminosity and redshift." (notes)
  - **Rule:** What counts as a fact, rule 8: "The rest of the study is not: its background, its findings, and what it says about methods it did not use." It is the background of the study, about earlier studies. Decided on 2026-10-31; until then this item waited on the experts' answer to Q26 (rule 2 of *What counts as a fact*). (Until 2026-10-31 this item had cited rule 9, as naming no specific thing; third audit, finding L-6.)
  - **May matter because:** it says why the study was made.
  - **Question:** Q26 (settled on 2026-10-31: see Q26's My notes).
- **Left out:** "and Swift (the latter is not included in this table, notice)" (notes), the study's second sample
  - **Rule:** What counts as a fact, rule 6: "A ground truth triple can't say "not"." The Swift sample is another dataset, too (Writing a classed triple, rule 21: "Leave out facts about other datasets, such as a variant of the record's dataset (the same data at another temporal resolution, spatial resolution, or version), or a product made from it.").
  - **May matter because:** the study's findings are about both samples.
  - **Question:** Q26 (c), withdrawn on 2026-10-31 (see Q26's My notes); the item is left out by rules 6 and 21 of its own. Checked on 2026-10-31: the Swift sample is the catalogue's other table, table2.dat (the CDS ReadMe of J/A+A/536/A84, http://vizier.nao.ac.jp/ftp/cats/J/A+A/536/A84/ReadMe).
- **Left out:** "with redshift between ~ 0.2 and ~ 4.5, and X-ray luminosities, in the 0.5 - 4.5 keV band, between ~ 10^43 erg/s and ~ 10^46 erg/s" (notes), the redshift range and the luminosity range of the study's two samples
  - **Rule:** What counts as a fact, rule 1: "Only what the record states." The record states the two ranges for "two serendipitously selected AGN samples extracted from the catalogs of XMM-Newton and Swift (the latter is not included in this table, notice)", that is, for the two samples taken together. This table holds the XMM-Newton sample alone, and no passage gives the ranges of that sample. A range that two samples cover together is not stated for one of them, as rule 1's *Membership by name* says of a group: "A statement about the group as a whole is not written for it: what the members cover taken together". Until 2026-11-12 the ground truth had the record's dataset HAS_REDSHIFT_RANGE "between ~ 0.2 and ~ 4.5" and HAS_LUMINOSITY_RANGE "in the 0.5 - 4.5 keV band, between ~ 10^43 erg/s and ~ 10^46 erg/s" (found by both audits of 2026-11-12).
  - **May matter because:** a search by redshift or by luminosity would use the ranges, and the table's own ranges lie within them.
- **Left out:** "which operates in the time domain" (notes, about the structure function)
  - **Rule:** What counts as a fact, rule 8: "When a record tells the study its dataset comes from, the study's aim and its method are facts of the record's dataset (HAS_PURPOSE; PRODUCED_USING_ALGORITHM, rule 24 of *Writing a classed triple*). The rest of the study is not". The method is a ground truth triple ("structure function (SF)", PRODUCED_USING_ALGORITHM); in which domain it works is a detail the study gives of its method, not the method. Decided on 2026-10-31 (Q28 (d), settled); until then it waited on the experts' answer to Q28 (d) (rule 2 of *What counts as a fact*, its part on waiting for an expert), with no clear would-be triple, since its predicate and the entity class of "time domain" were not settled. (Until 2026-10-31 it waited on Q26, and before that cited rule 4; third audit, finding L-7.) The field's home for it is a subject list, the Unified Astronomy Thesaurus's "Time domain astronomy": docs/improvements.md, *Knowledge enrichment from the model, verified and labelled* (080).
  - **May matter because:** it says how the method works: in the time domain.
  - **Question:** Q28 (d) (settled on 2026-10-31: see Q28's My notes).
- **Left out:** "The SF is also more appropriate than fractional variability and excess variance, because these parameters are biased by the duration of the monitoring time interval in the rest-frame, and therefore by cosmological time dilation." (notes)
  - **Rule:** What counts as a fact, rule 5: "Take out words such as "great"." ("more appropriate" is the authors' judgement). The second clause, that "these parameters are biased by the duration of the monitoring time interval", is about two measures the study did not use: What counts as a fact, rule 8: "The rest of the study is not: its background, its findings, and what it says about methods it did not use." Decided on 2026-10-31; until then this item waited on the experts' answer to Q26 (rule 2 of *What counts as a fact*). (Until 2026-10-31 this clause had cited no rule; third audit, finding L-8.)
  - **May matter because:** it says why the method was chosen.
  - **Question:** Q26 (settled on 2026-10-31: see Q26's My notes).
- **Left out:** "They do not find evidence of the break in the SF, at variance with the case of lower luminosity AGNs." (notes)
  - **Rule:** What counts as a fact, rule 6: "A ground truth triple can't say "not"."
- **Left out:** "then available" and "latest" (notes, "the version of the Serendipitous Source Catalog then available" and "the latest incremental update")
  - **Rule:** What counts as a fact, rule 10: "Take out "latest", "current", "now", "then available", and words like them." They say what was so when the study was made, not a lasting fact.
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
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names." HAS_NUMBER_OF holds a number of things, and "sources with more than one record" isn't a thing the record names; "significant" is a judgement (What counts as a fact, rule 5: "Take out words such as "great".").
  - **May matter because:** it says how many sources the catalog has detected more than once.
- **Left out:** "(above the processing likelihood threshold of 6)" (notes, "The 2XMMi-DR3 catalogue contains 353,191 detections (above the processing likelihood threshold of 6)")
  - **Rule:** Writing a classed triple, rule 24: "Each step gives up to two ground truth triples, each written only if the record names both of its ends: output COMPUTED_FROM input, and output PRODUCED_USING_ALGORITHM method." The parentheses state a fact of their own, so they are taken out of the instance (rule 20: "Parentheses that state a fact of their own (a period, a duration, an amount, a place) are taken out of the instance"), and the ground truth triple is "2XMMi-DR3" HAS_NUMBER_OF "353,191 detections". The threshold is a setting of the processing that made the catalogue's detections, and the record names no method for that step. A setting of a step is neither of the step's two triples, as for the maximum distance of 1.5 arcseconds, below. Until 2026-11-12 the parentheses stayed in the instance.
  - **May matter because:** it says which detections the catalogue counts.
- **Left out:** "corresponding to the uncertainty in the X-ray positions" (notes)
  - **Rule:** Writing a classed triple, rule 24: "Each step gives up to two ground truth triples, each written only if the record names both of its ends: output COMPUTED_FROM input, and output PRODUCED_USING_ALGORITHM method." It is why the maximum distance of 1.5 arcseconds was chosen, a setting of the matching step, left out with that distance (below). Decided on 2026-10-31; until then this item waited on the experts' answer to Q26 (rule 2 of *What counts as a fact*).
  - **May matter because:** it says how precise the X-ray positions are.
  - **Question:** Q26 (settled on 2026-10-31: see Q26's My notes).
- **Left out:** "cross-correlated" as a method (notes, "The selected sources were cross-correlated with the DR7 edition of the SDSS Quasar Catalog")
  - **Rule:** Writing a classed triple, rule 24: "A verb or participle that says only that something was done to the data ("corrected", "calibrated", "detrended", "binned", "mapped", "edited", "convert", "weighted") names no method". Only a verb; I wrote COMPUTED_FROM "DR7 edition of the SDSS Quasar Catalog" and no PRODUCED_USING_ALGORITHM.
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
- **Left out:** what "XMM-Newton" is (notes, "the catalogs of XMM-Newton and Swift" and "412 quasars that were observed by XMM-Newton")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what XMM-Newton is. Its entity class, Platform, is written (FROM_PLATFORM "XMM-Newton", of the record's dataset), by rule 1's *Names in a public reference*. Until 2026-11-12 its entity class rested on the record's words "observed by XMM-Newton" alone.
  - The reference: Wikidata, XMM-Newton (Q693861), an instance of "space telescope", a subclass of "artificial satellite", which carries a scientific instrument: a craft in space that carries instruments, the definition of Platform (https://www.wikidata.org/wiki/Q693861, checked on 2026-11-12). No official NASA list names it: the GCMD Platforms and Instruments keywords (version 25.2) and the PDS4 context products have no entry for it.
- **Left out:** "2XMMi-DR3" FROM_PLATFORM "XMM-Newton" (notes, "two serendipitously selected AGN samples extracted from the catalogs of XMM-Newton and Swift" … "For XMM, the authors used the version of the Serendipitous Source Catalog then available, namely 2XMMi-DR3")
  - **Rule:** What counts as a fact, rule 1: "A fact the record does not state in one passage may be written when the record's own statements meet one of the three tests below; never infer from outside knowledge. The list of tests is closed". No passage states that 2XMMi-DR3 was collected from XMM-Newton. "the catalogs of XMM-Newton" joins the catalogs to the craft by "of" alone, which could mean that the catalogs were made from its observations, by its team or for its users, and does not say which, so it states no predicate of its own. "For XMM, … namely 2XMMi-DR3" says which catalog the study used for its XMM-Newton sample. That 2XMMi-DR3 holds observations made by XMM-Newton follows from the two sentences together, by none of the three tests (*Replacement*, *Comparison*, *Membership by name*), as for the eight flights of the record at pool position 19. The ground truth had this triple until 2026-11-13 (docs/improvements.md, *Fifth round of rule fixes*).
  - **May matter because:** it says which observatory the catalog comes from. The record's dataset keeps FROM_PLATFORM "XMM-Newton", which the record states ("412 quasars that were observed by XMM-Newton").
- **Left out:** what "HEASARC" stands for (notes, "This table was created by the HEASARC" and "a service provided by NASA HEASARC")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what HEASARC is. Its entity class, Organization, is written (DEVELOPED_BY_PARTY and PROVIDED_BY_PARTY "NASA HEASARC", and "NASA HEASARC" PART_OF "NASA"), by rule 1's *Names in a public reference*.
  - The reference: Wikidata, High Energy Astrophysics Science Archive Research Center (Q130537792), also named "HEASARC", an instance of "research center" (https://www.wikidata.org/wiki/Q130537792, checked on 2026-11-12). No official NASA list names it: the GCMD Providers keywords (version 25.2) have no entry for it.
- **Left out:** what "NASA" is (notes, "NASA HEASARC")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what NASA is. Its entity class, Organization, is written ("NASA HEASARC" PART_OF "NASA"), by rule 1's *Names in a public reference*.
  - The reference: GCMD Providers keywords (version 25.2), the level "NASA" under "GOVERNMENT AGENCIES-U.S. FEDERAL AGENCIES", which holds NASA's centers and offices (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/providers?format=csv, checked on 2026-11-12).

## "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0" (pool position 13, id ab33f184-95f4-4f33-8f3d-c4a09ec525d3)

11 items, 8 that may matter.

- **Left out:** "MTP020" (title, "ESC3-MTP020")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for"
  - **May matter because:** checked on 2026-10-30: planning period no. 20 (MTP, a numbered planning period; checked on 2026-10-31: ESA's *OSIRIS Science User Guide*, RO-RIS-MPAE-MA-011, section 5.1, spells it out as the Rosetta "Mid-Term Planning-cycle", covering "a timespan of roughly four weeks", https://archives.esac.esa.int/psa/ftp/INTERNATIONAL-ROSETTA-MISSION/OSINAC/RO-C-OSINAC-4-ESC3-67P-M20-INFLDSTR-V1.0/DOCUMENT/SCIENCE_USER_GUIDE/SCIENCE_USER_GUIDE_V05.PDF, not "Medium Term Plan"), inside the phase COMET ESCORT 3; the Rosetta NAVCAM archive lists "COMET ESCORT 3 MTP020 ESC3-MTP020 2015-08-25 23:25:00" (https://archives.esac.esa.int/psa/ftp/INTERNATIONAL-ROSETTA-MISSION/NAVCAM/RO-C-NAVCAM-2-ESC1-MTP010-V1.1/DOCUMENT/RO-SGS-IF-0001.ASC), and this data set covers 2015-08-25T23:25 to 2015-09-22T23:24:59 (https://archives.esac.esa.int/psa/ftp/INTERNATIONAL-ROSETTA-MISSION/OSINAC/RO-C-OSINAC-4-ESC3-67P-M20-INFLDSTR-V1.0/CATALOG/DATASET.CAT). It tells this dataset from its siblings. Still left out: the record's text does not explain it (rule 1).
  - **Question:** Q6 (b).
- **Left out:** "RDR" (title, "RDR-INFLDSTR")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for"
  - **May matter because:** another record uses it as a name of data ("The RDR data convert the EDR (raw) sensor data"); this one doesn't explain it, and its level is "CODMAC level 4". Checked on 2026-10-30: "RDR" is the data set type "Reduced Data Record", not a level (PDS3 Standards Reference, chapter 6, https://pds.nasa.gov/datastandards/pds3/standards/sr/Chapter06.pdf); Rosetta's archive conventions pair RDR with CODMAC 3 (ESA, RO-EST-TN-3372), while this data set uses it at CODMAC 4.
  - **Question:** Q6 (b).
- **Left out:** "prime" (notes, "The prime target is comet 67P/Churyumov-Gerasimenko 1 (1969 R1)")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds gives no ground truth triple, and is taken out of the instance: its subject would be that fact, not a thing the record names." HAS_TARGET says the dataset is about the comet; "prime" says only that it is the main target, how that fact holds. Saying how a fact holds needs a fact about a fact, a qualifier kept with the ground truth triple it holds for (as Wikidata's statement qualifiers do), which is future work: docs/improvements.md, *Rule 19 can lose which fact a qualifier went with*, option 4 (recommended on 2026-10-27, decided on 2026-10-30). Decided on 2026-10-31; until then this item waited on the experts' answer to Q27 (b) (rule 2 of *What counts as a fact*).
  - **May matter because:** a search for other bodies in these images would need it.
  - **Question:** Q27 (settled on 2026-10-31: see Q27's My notes).
- **Left out:** "comet" (notes, "comet 67P/Churyumov-Gerasimenko 1 (1969 R1)")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the thing,"
- **Left out:** "spacecraft" and "mission phase" (notes, "the Rosetta spacecraft" and "the COMET ESCORT 3 mission phase")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the thing,"; "the Rosetta spacecraft" is written as "ROSETTA-ORBITER", the wording that says more (rule 23).
  - **Question:** Q2 (b) (settled on 2026-10-31: see Q2's My notes).
- **Left out:** "Lien" (notes, "Lien corrected dataset after September 2019 PSA/PDS external peer review")
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words." My ground truth triple REVISED_AFTER "September 2019 PSA/PDS external peer review" says the dataset was corrected after the review; "Lien" names what was corrected, the issues the review raised, which is what a correction after a review is (checked on 2026-10-30: PDS defines a lien as "A formally expressed issue with one or more products in a collection", and ESA's procedure for this review says "Within ESA, issues raised are known as RIDs (Review Item Discrepancies), while PDS refer to these as liens", https://sbnreview.astro.umd.edu/201909_Rosetta/procedure_docs/RO-SGS-PR-1023-App5%20-%20RSI%20Rosetta%20CLS%20Science%20Archive%20Review.pdf). Decided on 2026-10-31; until then this item waited on the experts' answer to Q28 (c) (rule 2 of *What counts as a fact*).
  - **May matter because:** it says what the correction was about.
  - **Question:** Q28 (c) (settled on 2026-10-31: see Q28's My notes).
- **Left out:** PRODUCED_USING_ALGORITHM "solar stray-light corrected" (notes, "contains solar stray-light corrected, in-field stray-light corrected, radiometric calibrated and geometric distortion corrected (resampled) image data")
  - **Rule:** Writing a classed triple, rule 24: "A verb or participle that says only that something was done to the data ("corrected", "calibrated", "detrended", "binned", "mapped", "edited", "convert", "weighted") names no method". "solar stray-light corrected" describes the data; since 2026-10-31 what was corrected is written, CLEANED_OF "solar stray-light" (rule 24: "What a step removed from the data, or corrected in them, is neither the step's input nor its method"); it is not the name of a method (as for "detrended" in the record at pool position 5).
  - **May matter because:** it says which corrections were applied to the images.
  - **Question:** Q7 (c) (settled on 2026-10-31: see Q7's My notes).
- **Left out:** PRODUCED_USING_ALGORITHM "in-field stray-light corrected" (notes, "contains solar stray-light corrected, in-field stray-light corrected, radiometric calibrated and geometric distortion corrected (resampled) image data")
  - **Rule:** Writing a classed triple, rule 24: "A verb or participle that says only that something was done to the data ("corrected", "calibrated", "detrended", "binned", "mapped", "edited", "convert", "weighted") names no method". "in-field stray-light corrected" describes the data; since 2026-10-31 what was corrected is written, CLEANED_OF "in-field stray-light" (rule 24: "What a step removed from the data, or corrected in them, is neither the step's input nor its method"); it is not the name of a method (as for "detrended" in the record at pool position 5).
  - **May matter because:** it says which corrections were applied to the images.
  - **Question:** Q7 (c) (settled on 2026-10-31: see Q7's My notes).
- **Left out:** PRODUCED_USING_ALGORITHM "radiometric calibrated" (notes, "contains solar stray-light corrected, in-field stray-light corrected, radiometric calibrated and geometric distortion corrected (resampled) image data")
  - **Rule:** Writing a classed triple, rule 24: "A verb or participle that says only that something was done to the data ("corrected", "calibrated", "detrended", "binned", "mapped", "edited", "convert", "weighted") names no method". "radiometric calibrated" describes the data; it is not the name of a method (as for "detrended" in the record at pool position 5).
  - **May matter because:** it says which corrections were applied to the images.
  - **Question:** Q7 (c) (settled on 2026-10-31: see Q7's My notes).
- **Left out:** PRODUCED_USING_ALGORITHM "geometric distortion corrected (resampled)" (notes, "contains solar stray-light corrected, in-field stray-light corrected, radiometric calibrated and geometric distortion corrected (resampled) image data")
  - **Rule:** Writing a classed triple, rule 24: "A verb or participle that says only that something was done to the data ("corrected", "calibrated", "detrended", "binned", "mapped", "edited", "convert", "weighted") names no method". "geometric distortion corrected (resampled)" describes the data; since 2026-10-31 what was corrected is written, CLEANED_OF "geometric distortion" (rule 24: "What a step removed from the data, or corrected in them, is neither the step's input nor its method"); it is not the name of a method (as for "detrended" in the record at pool position 5).
  - **May matter because:** it says which corrections were applied to the images.
  - **Question:** Q7 (c) (settled on 2026-10-31: see Q7's My notes).
- **Left out:** what "OSIRIS" stands for (notes, inside the name "OSIRIS Narrow Angle Camera")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record names "OSIRIS" only inside the camera's name and never says what it is. Its entity class, Instrument, is written ("OSIRIS Narrow Angle Camera" PART_OF "OSIRIS", with the source text "OSIRIS Narrow Angle Camera", by rule 17's *A name's facts*, as "GRaND plus Z boron loaded sensor" PART_OF "GRaND" in the record "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0"), by rule 1's *Names in a public reference*. Until 2026-11-12 no ground truth triple had "OSIRIS" as an instance, since no official NASA list names it and its entity class would have rested on outside knowledge (decided on 2026-11-01, the review of the second opinion's facts).
  - The reference: Wikidata, Optical, Spectroscopic, and Infrared Remote Imaging System (Q7098805), also named "OSIRIS", "scientific instrument on the Rosetta spacecraft", an instance of "space instrument" (https://www.wikidata.org/wiki/Q7098805, checked on 2026-11-12). No official NASA list names it: the PDS4 context products have entries for its two cameras (urn:esa:psa:context:instrument:ro.osinac and ro.osiwac) and none for OSIRIS itself.

## "MARS EXPRESS ASPERA-3 RAW EDR ELECTRON SPECTROMTR EXT2 V1.0" (pool position 14, id 7400495e-f11f-475f-a647-070bc2f82a92)

A held-out record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. 5 items, none that may matter.

- **Left out:** "EDR" (title)
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for"
  - **Question:** Q6 (b).
- **Left out:** "RAW", "ELECTRON SPECTROMTR" and "EXT2" as facts of their own (title)
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words."
  - They are the title's wordings of facts the notes state: "raw units of counts/accumulation" (HAS_UNIT), the "Mars Express ASPERA-3 Electron Spectrometer (ELS)" (ACQUIRED_BY_INSTRUMENT; "SPECTROMTR" is a shortened spelling of "Spectrometer", and rule 23 of *Writing a classed triple* writes the wording that says more) and "the second mission extension" (HAS_MISSION_PHASE).
- **Left out:** what "Mars Express" is (title, "MARS EXPRESS", and notes, "Mars Express ASPERA-3 Electron Spectrometer (ELS)")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what Mars Express is. Its entity class, Platform, is written (FROM_PLATFORM "Mars Express", "Mars Express ASPERA-3 Electron Spectrometer (ELS)" ABOARD "Mars Express", and "Mars Express" HAS_TARGET "Mars"), by rule 1's *Names in a public reference*. The PDS4 context products also hold the mission, urn:esa:psa:context:investigation:mission.mars_express, titled "MARS EXPRESS" too; the notes name the craft that carries the instrument (rule 17 of *Writing a classed triple*, *A platform in an instrument's name*), and the title's first word is the instrument host.
  - The list: PDS4 context product urn:esa:psa:context:instrument_host:spacecraft.mex, "The Mars Express Orbiter", of type Spacecraft, also titled "MARS EXPRESS" (https://pds.nasa.gov/data/pds4/context-pds4/instrument_host/spacecraft.mex_1.1.xml, checked on 2026-11-13).
  - **Question:** Q2.
- **Left out:** what "ASPERA-3" stands for (title, and notes, inside the name "Mars Express ASPERA-3 Electron Spectrometer (ELS)")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what ASPERA-3 is. Its entity class, Instrument, is written (ACQUIRED_BY_INSTRUMENT "ASPERA-3", and "Mars Express ASPERA-3 Electron Spectrometer (ELS)" PART_OF "ASPERA-3"), by rule 1's *Names in a public reference*.
  - The list: PDS4 context product urn:esa:psa:context:instrument:mex.aspera-3 (earlier identifier urn:nasa:pds:context:instrument:aspera-3.mex), "Mars Express Orbiter Analyzer of Space Plasma and Energetic Atoms (3rd Version)", whose description names it "(ASPERA-3)" (https://pds.nasa.gov/data/pds4/context-pds4/instrument/mex.aspera-3_1.2.xml, checked on 2026-11-13).
- **Left out:** what "Mars" is (notes, inside the name "Mars Express")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what Mars is. Its entity class, CelestialBody, is written ("Mars Express" HAS_TARGET "Mars", by rule 2's *A fact inside a name*), by rule 1's *Names in a public reference*.
  - The reference: PDS4 context product urn:nasa:pds:context:target:planet.mars, "Mars", of type Planet (https://pds.nasa.gov/data/pds4/context-pds4/target/planet.mars_1.3.xml, checked on 2026-11-13).

## "Solar Orbiter Ephemeris, Heliocentric Trajectories, Heliographic, Heliographic Inertial, and Solar Ecliptic Coordinates, HelioWeb, Daily Data" (pool position 15, id 32614a2f-a286-4c7c-9f1e-deafdf8bd6a3)

14 items, 8 that may matter.

- **Left out:** "HelioWeb" (title)
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for". The record never says what HelioWeb is (a service, a web site, a collection), so it has no entity class. No reference of rule 1's *Names in a public reference* names it: the GCMD Instruments, Platforms and Providers keywords (version 25.2), the PDS4 context products and Wikidata have no entry named HelioWeb (checked on 2026-11-12).
  - **May matter because:** my reading, not checked: HelioWeb is the SPDF (NASA Goddard) service that serves these heliocentric trajectories; a search by service would need it.
- **Left out:** "Solar Orbiter" as the craft whose ephemeris the dataset holds (title, "Solar Orbiter Ephemeris")
  - **Rule:** What counts as a fact, rule 2: "When the naming states more than one predicate, or none, the name's words give no ground truth triple" (*A fact inside a name*). "Solar Orbiter" stands inside the Variable's name "Solar Orbiter Ephemeris" (HAS_VARIABLE), with no words that say how the ephemeris and the craft are related, so the fact would be read from a name's words, and the test decides it: "The test decides only the facts that are read from a name's words." Naming an ephemeris with a craft's name states no predicate of the ground truth schema. FROM_PLATFORM is "was collected from this Platform", and an ephemeris gives the positions of the craft and is not collected from it. HAS_TARGET is "is about, or studies, this CelestialBody", and joins only a CelestialBody. No predicate is coined: rule 14 coins one for a fact "that a sentence states with words of its own", and no sentence of the record states this one (decided on 2026-11-12). The entity class of "Solar Orbiter", Platform, is by rule 1's *Names in a public reference*, and no ground truth triple has "Solar Orbiter" as an instance.
  - The reference: Wikidata, Solar Orbiter (Q653731), a solar probe (https://www.wikidata.org/wiki/Q653731, looked up on 2026-11-12: docs/improvements.md, *An entity class may come from a public reference*). Whether an official NASA list names it was not recorded then.
  - **May matter because:** it says whose positions the title gives, and a search by spacecraft would need it. The notes name another body, Comet Borrelly (the last item of this section).
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
  - **Rule:** What counts as a fact, rule 4: "says what kind of thing MODIS is: that belongs in its entity class". It defines the method; the method itself is a ground truth triple (PRODUCED_USING_ALGORITHM "Mean of Date").
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

11 items, 6 that may matter.

- **Left out:** "J/S/SS" (title)
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for"
  - **May matter because:** my reading, not checked: the PDS target codes for Jupiter, Saturn and the solar system, the targets of the data set; a search by target would need them. The notes say only "the planetary encounters".
  - **Question:** Q6 (b) lists other unexplained PDS title codes.
- **Left out:** "FULL RES" (title)
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for"; even spelled out, "full resolution" names no value (rule 9: "a variety of spatial resolutions" names no resolution).
  - **May matter because:** it says these are the analyzer's full-resolution data, not averages.
- **Left out:** "EDITED" (title), and "edited" (notes, "Some noise lines during the planetary encounters have been edited from the data set.") as a method
  - **Rule:** Writing a classed triple, rule 24: "A verb or participle that says only that something was done to the data ("corrected", "calibrated", "detrended", "binned", "mapped", "edited", "convert", "weighted") names no method". What was removed is written: the record's dataset CLEANED_OF "noise lines during the planetary encounters" (rule 24: "What a step removed from the data, or corrected in them, is neither the step's input nor its method").
- **Left out:** "during the planetary encounters" as a mission phase of the dataset (notes)
  - **Rule:** What counts as a fact, rule 1: "Only what the record states." That the data include the encounters follows from the sentence (noise lines during them were in the data set) but is not stated.
  - **May matter because:** it says the data include the planetary encounters.
- **Left out:** "nearly all" (notes, "includes nearly all measurements")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds gives no ground truth triple, and is taken out of the instance"
- **Left out:** "for the entire mission" (notes)
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names." The mission is not named, and "entire" only says how much of it.
  - **May matter because:** it says the data cover the whole mission (no dates are given).
- **Left out:** "Each sweep" (notes, "Each sweep of the PWS spectrum analyzer records")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds gives no ground truth triple, and is taken out of the instance". It says how the analyzer records (sweep by sweep).
- **Left out:** "calibrated values" PRODUCED_USING_ALGORITHM "example C-language program" (notes)
  - **Rule:** Writing a classed triple, rule 21: "Leave out facts about other datasets, such as a variant of the record's dataset (the same data at another temporal resolution, spatial resolution, or version), or a product made from it." Its connection, "calibrated values" COMPUTED_FROM the record's dataset, is a ground truth triple.
  - **May matter because:** it is how users can calibrate the values.
- **Left out:** "reads this data set" as a fact of its own (notes)
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words." "calibrated values" COMPUTED_FROM the record's dataset already says it.
- **Left out:** the record's dataset HAS_MEASUREMENTS_OF "spectral densities" (notes, "This data set includes nearly all measurements collected from the spectrum analyzer component" … "Each sweep of the PWS spectrum analyzer records spectral densities")
  - **Rule:** What counts as a fact, rule 1: "A fact the record does not state in one passage may be written when the record's own statements meet one of the three tests below; never infer from outside knowledge. The list of tests is closed". The record states that the analyzer records spectral densities ("PWS spectrum analyzer" MEASURES "spectral densities") and that the data set holds the analyzer's measurements (ACQUIRED_BY_INSTRUMENT "PWS spectrum analyzer"); that the data set holds spectral densities follows from the two, but by none of the three tests (*Replacement*, *Comparison*, *Membership by name*) (decided on 2026-11-01, the review of the second opinion's facts).
  - **May matter because:** a search for datasets by what they measure would need it.
- **Left out:** what "Voyager 1" is (title, "VG1", and notes, "the Plasma Wave Spectrometer (PWS) onboard Voyager 1")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what Voyager 1 is. Its entity class, Platform, is written (FROM_PLATFORM "Voyager 1", and "Plasma Wave Spectrometer (PWS)" ABOARD "Voyager 1"), by rule 1's *Names in a public reference*.
  - The reference: PDS4 context product urn:nasa:pds:context:instrument_host:spacecraft.vg1, "VOYAGER 1", of type Spacecraft, with the host id "VG1" (https://pds.nasa.gov/data/pds4/context-pds4/instrument_host/spacecraft.vg1_1.5.xml, checked on 2026-11-12).

## "ROSETTA-ORBITER 67P OSIWAC 4 EXT3-MTP033 RDR-STR-REFL V1.0" (pool position 17, id 792e45e8-e7fb-427f-a3fb-2c1dac5f545f)

A held-out record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. 9 items, 3 that may matter.

- **Left out:** "MTP033" (title, "EXT3-MTP033")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for"
  - **May matter because:** it tells this dataset from its siblings, as "MTP020" does in the record "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0" (its item; not checked for this record).
  - **Question:** Q6 (b).
- **Left out:** "RDR", "STR" and "REFL" (title, "RDR-STR-REFL")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for"
  - **Question:** Q6 (b).
- **Left out:** "prime" (notes, "The prime target is comet 67P/Churyumov-Gerasimenko 1 (1969 R1)")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds gives no ground truth triple, and is taken out of the instance"
  - HAS_TARGET says the dataset is about the comet; "prime" says only that it is the main target, how that fact holds, as in the record "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0".
  - **May matter because:** a search for other bodies in these images would need it.
- **Left out:** "comet" (notes, "comet 67P/Churyumov-Gerasimenko 1 (1969 R1)")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the thing,"
- **Left out:** "spacecraft" and "mission phase" (notes, "the Rosetta spacecraft" and "the ROSETTA EXTENSION 3 mission phase")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the thing,"; "the Rosetta spacecraft" is written as "ROSETTA-ORBITER", the wording that says more (rule 23).
- **Left out:** "Lien" (notes, "Lien corrected dataset after October 2018 PSA/PDS external peer review")
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words."
  - My ground truth triple REVISED_AFTER "October 2018 PSA/PDS external peer review" says the dataset was corrected after the review; "Lien" names what was corrected, the issues the review raised, as in the record "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0".
- **Left out:** PRODUCED_USING_ALGORITHM "solar stray light corrected", "radiometric calibrated" and "geometric distortion corrected (resampled)" (notes, "contains solar stray light corrected, radiometric calibrated and geometric distortion corrected (resampled) image data")
  - **Rule:** Writing a classed triple, rule 24: "A verb or participle that says only that something was done to the data ("corrected", "calibrated", "detrended", "binned", "mapped", "edited", "convert", "weighted") names no method"
  - The words describe the data and name no method. What was corrected is written: CLEANED_OF "solar stray light" and CLEANED_OF "geometric distortion" (rule 24: "What a step removed from the data, or corrected in them, is neither the step's input nor its method"); "radiometric calibrated" names nothing removed.
  - **May matter because:** it says which corrections were applied to the images.
  - **Question:** Q7 (c).
- **Left out:** what "OSIRIS" stands for (notes, inside the name "OSIRIS Wide Angle Camera")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record names "OSIRIS" only inside the camera's name and never says what it is. Its entity class, Instrument, is written ("OSIRIS Wide Angle Camera" PART_OF "OSIRIS"), by rule 1's *Names in a public reference*.
  - The reference: Wikidata, Optical, Spectroscopic, and Infrared Remote Imaging System (Q7098805), also named "OSIRIS", "scientific instrument on the Rosetta spacecraft", an instance of "space instrument" (https://www.wikidata.org/wiki/Q7098805, checked on 2026-11-13). No official NASA list names it: the PDS4 context products have entries for its two cameras (urn:esa:psa:context:instrument:ro.osinac and ro.osiwac) and none for OSIRIS itself.
- **Left out:** what "ROSETTA" is (notes, inside the name "ROSETTA EXTENSION 3")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what ROSETTA is: "the Rosetta spacecraft" names the craft, and the phase's name holds "ROSETTA" alone. Its entity class, Mission, is written ("ROSETTA EXTENSION 3" PART_OF "ROSETTA", by rule 2's *A fact inside a name*: "a Mission named in the name of one of its parts ... gives PART_OF"), by rule 1's *Names in a public reference*.
  - The list: PDS4 context product urn:esa:psa:context:investigation:mission.international_rosetta_mission, "The International Rosetta Mission", of type Mission, also titled "ROSETTA" (https://pds.nasa.gov/data/pds4/context-pds4/investigation/mission.international_rosetta_mission_1.1.xml, checked on 2026-11-13). The craft's entry, urn:esa:psa:context:instrument_host:spacecraft.ro, is titled "ROSETTA-ORBITER", not "ROSETTA".

## "VIIRS/NPP BRDF/Albedo Parameter 3 Band M4 Daily L3 Global 30 ArcSec CMG V002" (pool position 18, id 0eedd2bc-b2e2-4cc1-a94d-41c141169334)

15 items, 6 that may matter.

- **Left out:** "NASA/NOAA" as a fact of its own (notes)
  - **Rule:** What counts as a fact, rule 1: "Only what the record states." The words name the two agencies and the platform, and do not say how they are related (whether the agencies built the platform, launched it or operate it), so they state no fact (rule 2, *A fact inside a name*: "When the naming states more than one predicate, or none, the name's words give no ground truth triple"). Two agencies' names before a platform's own could mean that the agencies launched the platform, developed it or sponsored it (LAUNCHED_BY_PARTY, DEVELOPED_BY_PARTY, SPONSORED_BY_PARTY), and naming does not settle which: "A relationship that naming does not state (that one thing funded, developed, provided or sponsored the other) is never read from a name". "NASA/NOAA" stays in the platform's instance, "NASA/NOAA Suomi National Polar-orbiting Partnership (Suomi NPP)" (Writing a classed triple, rule 19: "A qualifier stays in the instance, as written, if it is any other kind"). Until 2026-11-12 this item cited rule 19 alone, which says how the instance is written and leaves no fact out.
- **Left out:** "Data are temporally weighted to the ninth day, which is reflected in the file name." (notes)
  - **Rule:** Writing a classed triple, rule 24: "A verb or participle that says only that something was done to the data ("corrected", "calibrated", "detrended", "binned", "mapped", "edited", "convert", "weighted") names no method". "the file name" names no particular file (rule 9).
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
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds gives no ground truth triple, and is taken out of the instance"
- **Left out:** "entire" (notes, "covers the entire globe")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds gives no ground truth triple, and is taken out of the instance"
- **Left out:** "BRDF/Albedo values for VIIRS band M4" COMPUTED_FROM "isotropic parameters" and "volumetric parameters", and FOR_CHANNEL "VIIRS band M4 (0.555 μm)" (notes)
  - **Rule:** Writing a classed triple, rule 21: "Leave out facts about other datasets, such as a variant of the record's dataset (the same data at another temporal resolution, spatial resolution, or version), or a product made from it." Its connection to the record's dataset is a ground truth triple: "BRDF/Albedo values for VIIRS band M4" COMPUTED_FROM the record's dataset (rule 24, *The record's dataset's own values*: "when the input is the record's dataset's own values, the input is the record's dataset"). Until 2026-11-12 its object was the Variable "BRDF geometric parameter for VIIRS band M4 (0.555 μm)". The band named inside the product's words (rule 17, *A name's facts*) is a fact of that product too (added to this item on 2026-11-01, the review of the second opinion's facts).
  - **May matter because:** it says the albedo needs all three parameters, that is, three of the family's products together.
  - **Question:** Q24.
- **Left out:** "used to derive" as a purpose of the parameter (notes)
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words." COMPUTED_FROM says it; and a use is not a purpose (rule 9: "What data have been used for, or can be used for, is a fact of the work that used them, not of the data").
- **Left out:** "Known Issues" (notes, the heading)
  - **Rule:** What counts as a fact, rule 3: "A heading inside a text field, a line of its own that only names the passage below it ("Known Issues", "BARREL Data Usage Policy"), is formatting too, and gives no ground truth triple."
- **Left out:** "known issues" as what the page is about (notes)
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds gives no ground truth triple, and is taken out of the instance"
- **Left out:** "MODIS/VIIRS Land Quality Assessment website" (notes), as the page's name
  - **Rule:** Writing a classed triple, rule 20: "Write ALSO_KNOWN_AS only when the record gives the other name in words of its own"
  - **May matter because:** it is the page's name.
- **Left out:** "NIR" as another name of "near-infrared", and "DNB" of "VIIRS Day/Night Band" (notes)
  - **Rule:** Writing a classed triple, rule 21: "Leave out facts about other datasets, such as a variant of the record's dataset (the same data at another temporal resolution, spatial resolution, or version), or a product made from it." The bands are the family's, not this dataset's.
- **Left out:** what "Suomi National Polar-orbiting Partnership (Suomi NPP)" is (notes; the title writes "NPP")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what the Suomi National Polar-orbiting Partnership is. Its entity class, Platform, is written (FROM_PLATFORM "NASA/NOAA Suomi National Polar-orbiting Partnership (Suomi NPP)", and "Visible Infrared Imaging Radiometer Suite (VIIRS)" ABOARD it), by rule 1's *Names in a public reference*.
  - The list: GCMD Platforms keywords (version 25.2), "Suomi-NPP", "Suomi National Polar-orbiting Partnership" (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/platforms?format=csv, checked on 2026-11-12).

## "BARREL 4G Rate Counter (RCNT) NaI Scintillator Diagnostics, Level 2, 4 s Data" (pool position 19, id 6f63dd10-376e-4d17-9156-f2155637e74d)

40 items, 17 that may matter.

- **Left out:** the launch stations and their places (notes, "with launches from two stations located in Antarctica: the British base located at Halley Bay on the Brunt Ice Shelf and the South African SANAE IV base", and "Later campaigns were undertaken in 2015 and 2016 from the Esrange Space Center located in Kiruna, Sweden")
  - **Rule:** What counts as a fact, rule 2: "or it waits on an expert's answer" (Q8 (c): whether a station or a space center is an Organization or a place).
  - **May matter because:** a search by launch site or region (Antarctica, Sweden) would need them.
  - **Question:** Q8 (c).
  - No clear would-be triple: whether a station is an Organization or a place decides its entity class and its predicates (LAUNCHED_FROM and LOCATED_IN for a place, none of them in the ground truth schema; BASED_IN "British", "South African" and "Sweden" for an Organization), so no row can be written in annotations/pending_triples.csv until Q8 (c) is answered.
- **Left out:** "South African" (notes, inside the name "South African National Antarctic Expedition") as a Country of its own
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names." The record names no country. The ground truth schema's Country is "a nation", "South African" is an adjective, the record never writes "South Africa", and an instance is the record's own words (Writing a classed triple, rule 11: "Don't paraphrase them"). Until 2026-11-12 this item cited rule 11's "A name stays whole", which keeps the name whole and leaves no fact out (rule 2, *A fact inside a name*); the record at pool position 25 now has "U.S. Government" BASED_IN "U.S.", where the name holds the country's own name. Until 2026-11-01 the ground truth had "South African National Antarctic Expedition" BASED_IN "South African" (the double check of batches 4 and 5, finding F19.1).
  - **May matter because:** it says where the expedition is based, which a search by country would need.
  - **Question:** Q8 (c), with the launch stations.
- **Left out:** "4G" (title)
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for"
  - **May matter because:** my reading, not checked: the balloon payload's code (campaign 4, payload G), which tells this dataset from its siblings and gives its campaign.
  - **Question:** Q6 (b).
- **Left out:** "NaI Scintillator" as an instrument of its own (title, "NaI Scintillator Diagnostics")
  - **Rule:** What counts as a fact, rule 1: "Never add what you know from elsewhere". The words are part of the Variable "NaI Scintillator Diagnostics" (HAS_VARIABLE), and the record names no scintillator otherwise; that one is an instrument would come from outside the record (decided on 2026-11-01, the review of the second opinion's facts). Until 2026-11-12 this item cited rule 11's "A name stays whole" first, which keeps the Variable's instance whole and leaves no fact out (rule 2, *A fact inside a name*).
- **Left out:** what "CDF" stands for (notes, "all BARREL CDF data products")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what CDF is. Its entity class, FileFormat, is written (the record's dataset HAS_FILE_FORMAT "CDF", with the source text "all BARREL CDF data products"; the record's dataset is one of these products by rule 1's *Membership by name*, as for HAS_VERSION "Version 10", and "all" makes the format each member's), by rule 1's *Names in a public reference*. Until 2026-11-12 "CDF" gave no ground truth triple, since it is on no official NASA list as an instrument or a platform.
  - The reference: Wikidata, Common Data Format (Q1116060), also named "CDF", "file format family for multi-dimensional data", an instance of "file format family" (https://www.wikidata.org/wiki/Q1116060, checked on 2026-11-12). No official NASA list names it: the GCMD Instruments, Platforms and Providers keywords (version 25.2) have no entry for it.
- **Left out:** "diagnostic fields" as a thing of its own (notes)
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words." HAS_VARIABLE "NaI Scintillator Diagnostics" says it (rule 23).
- **Left out:** "was a multiple-balloon investigation" (notes)
  - **Rule:** What counts as a fact, rule 4: "says what kind of thing MODIS is: that belongs in its entity class"
  - **May matter because:** it says the mission used many balloons at once.
- **Left out:** "Mission of Opportunity" and "Selected" (notes)
  - **Rule:** What counts as a fact, rule 4: "the kind is left out, and the belonging is a ground truth triple" ("BARREL" PART_OF "NASA Living with a Star"); "Selected" names no party (rule 1: "Never add what you know from elsewhere").
  - **May matter because:** it is NASA's funding category for the mission.
- **Left out:** "Each" (notes, "Each BARREL balloon")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds gives no ground truth triple, and is taken out of the instance"
- **Left out:** "near latitudes close to either the antarctic and arctic circles" (notes)
  - **Rule:** What counts as a fact, rule 1, *Membership by name*: "A statement about the group as a whole is not written for it": "either … or". Which circle this payload flew near is not stated.
  - **May matter because:** a search by region (Antarctic, Arctic) would need it.
  - **Question:** Q24.
- **Left out:** "stratospheric altitudes" (notes)
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words." OBSERVED_AT_ALTITUDE "about 30 km" is the wording that says more (rule 23).
- **Left out:** "first balloon" (notes, "provided the first balloon measurements")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds gives no ground truth triple, and is taken out of the instance"
  - **May matter because:** it says BARREL was the first to measure this from balloons.
- **Left out:** "while comprehensive in situ measurements of both plasma waves and energetic particles were available" (notes)
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names." Whose measurements is not said; "comprehensive" is a judgement (rule 5).
- **Left out:** "Also, the BARREL data has been used to characterize the spatial scale of precipitation at relativistic energies." (notes)
  - **Rule:** What counts as a fact, rule 9: "when the record doesn't name that work, it gives no ground truth triple." No work that used the data is named; the statement is also about the BARREL data as a whole (rule 1, *Membership by name*).
  - **May matter because:** it says what the data are good for.
  - **Question:** Q24.
- **Left out:** "initially" and "Austral summer months of" (notes)
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds gives no ground truth triple, and is taken out of the instance" ("initially"). "Austral summer months": rule 16 of *Writing a classed triple*, since the months, HAS_TIME_SPAN "January and February of 2013" and "of 2014", say when.
  - **May matter because:** "Austral summer" says why those months (the southern summer).
- **Left out:** "Thus, the BARREL balloon constellation constituted an evolving and slowly moving array able to study relativistic electron precipitation from the radiation belts." (notes)
  - **Rule:** What counts as a fact, rule 4: "says what kind of thing MODIS is: that belongs in its entity class" ("constituted an … array"); "able to study" is what it could do, not what it was meant for (HAS_PURPOSE "is meant to achieve").
  - **May matter because:** it says the balloons formed a moving array, which is how the mission measured spatial scales.
- **Left out:** "and other ground and space based instruments" (notes)
  - **Rule:** Writing a classed triple, rule 22: "An item that names no specific thing ("his team") gives no ground truth triple"
- **Left out:** "successively" (notes)
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds gives no ground truth triple, and is taken out of the instance"
- **Left out:** "approximately 20 kg" as the mass of each balloon (notes, "over 50 small, approximately 20 kg, stratospheric balloons were successively launched")
  - **Rule:** What counts as a fact, rule 9: "An amount or a count per member gives no ground truth triple". The mass is each balloon's, and the sentence names the balloons only by a count ("over 50 … balloons"). The same rule leaves out "from 2 to 25 epochs each" in the record at pool position 12 and "a set of 3" in the record at pool position 25. The words stay in the count, which is written whole: "BARREL" HAS_NUMBER_OF "over 50 small, approximately 20 kg, stratospheric balloons" (rule 22 of *Writing a classed triple*, *Describing words joined by "and" or a comma*). Until 2026-11-12 the ground truth had "BARREL balloon" (Platform) HAS_MASS "approximately 20 kg" (Value).
  - **May matter because:** it is the mass of each balloon the mission flew.
- **Left out:** "The website creeated and hosted by A.J. Halford (see Information URL below) reports that: "By the end of the campaigns, there were over 90 researchers coordinating on a daily basis with the BARREL team working on 7 different satellite missions, 1 other balloon mission, and way too many ground based instruments to count."" (notes)
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names." The researchers are named only by a count, and "way too many" is a judgement (rule 5). The website itself is a ground truth triple since 2026-11-01 (the review of the second opinion's facts, judgment call D): the record's dataset DOCUMENTED_AT "website creeated and hosted by A.J. Halford" (Document), with DEVELOPED_BY_PARTY and PROVIDED_BY_PARTY "A.J. Halford" (Person), since rule 20 of *Writing a classed triple* says "A page or site the record names in words, without a web address, is a Document"; until then this item left it out too ("The website has no address in the text").
  - **May matter because:** it gives the mission's reach.
- **Left out:** "only" (notes, "launched only balloons")
  - **Rule:** What counts as a fact, rule 6: "A ground truth triple can't say "not"." "only" says nothing else was launched.
- **Left out:** "research using data collected on these flights is ongoing, so stay tuned for updates!" (notes)
  - **Rule:** What counts as a fact, rule 10: "Take out "latest", "current", "now", "then available", and words like them." ("ongoing"); "stay tuned" names nothing (rule 9).
- **Left out:** "All data and analysis software are freely available to the scientific community." (notes)
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words." For the data: HAS_ACCESS_RIGHTS "freely available to the public" says more. "analysis software": rule 9, no particular software is named.
- **Left out:** "primarily" (notes)
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds gives no ground truth triple, and is taken out of the instance"
- **Left out:** "current" (notes, "The current release")
  - **Rule:** What counts as a fact, rule 10: "Take out "latest", "current", "now", "then available", and words like them."
- **Left out:** "BARREL will make all its scientific data products quickly and publicly available but all users are expected to read and follow the BARREL Data Usage Policy listed below." (notes)
  - **Rule:** What counts as a fact, rule 7: "Not facts the record doesn't assert as true: uncertain ones, and ones it requires, requests or recommends." "all users are expected to read and follow" asks it of users. "will make … publicly available": rule 16 of *Writing a classed triple* (HAS_ACCESS_RIGHTS). "quickly": rule 9.
  - **May matter because:** it ties the data to their usage policy.
- **Left out:** "BARREL Data Usage Policy" (notes, the heading)
  - **Rule:** What counts as a fact, rule 3: "A heading inside a text field, a line of its own that only names the passage below it ("Known Issues", "BARREL Data Usage Policy"), is formatting too, and gives no ground truth triple."
- **Left out:** "every effort is made to ensure that these products are of the highest quality" (notes)
  - **Rule:** What counts as a fact, rule 5: "Take out words such as "great"."
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
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the thing," The policy is the instance, AVAILABLE_AT its address.
- **Left out:** what "NASA" is (notes, "a NASA Living with a Star Mission of Opportunity")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what NASA is. Its entity class, Organization, is written ("NASA Living with a Star" PART_OF "NASA"), by rule 1's *Names in a public reference*.
  - The reference: GCMD Providers keywords (version 25.2), the level "NASA" under "GOVERNMENT AGENCIES-U.S. FEDERAL AGENCIES", which holds NASA's centers and offices (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/providers?format=csv, checked on 2026-11-12).
- **Left out:** what "Earth" is (notes)
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what Earth is. Its entity class, CelestialBody, is written (HAS_TARGET "Earth"), by rule 1's *Names in a public reference*.
  - The reference: PDS4 context product urn:nasa:pds:context:target:planet.earth, "Earth", of type Planet (https://pds.nasa.gov/data/pds4/context-pds4/target/planet.earth_1.1.xml, checked on 2026-11-12).
- **Left out:** what "NASA Living with a Star" is (notes, "Selected as a NASA Living with a Star Mission of Opportunity")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what NASA Living with a Star is. Its entity class, Organization, is written (PART_OF "NASA"), by rule 1's *Names in a public reference*. A program that an organization runs is an Organization, one of that organization's named parts, which the ground truth schema's Organization includes ("a named institution or one of its named parts, not a Mission"). Living with a Star is a program of NASA, and the program itself collects no data, so it is not a Mission.
  - The reference: Wikidata Q1705257, "Living With a Star", "scientific program of NASA to study the Sun-Earth system" (https://www.wikidata.org/wiki/Q1705257, checked on 2026-11-12).
- **Left out:** "2016 campaign" HAS_NUMBER_OF "eight flights" (notes, "The 2015 and 2016 campaigns were undertaken in coordination with" … "A total of eight flights occurred during August 2016.")
  - **Rule:** What counts as a fact, rule 1: "A fact the record does not state in one passage may be written when the record's own statements meet one of the three tests below; never infer from outside knowledge. The list of tests is closed". The sentence gives the eight flights a month, August 2016, and names no campaign. That they are the flights of the 2016 campaign follows from this sentence and the sentences that name the campaign, by none of the three tests (*Replacement*, *Comparison*, *Membership by name*), as for the spectral densities of the record at pool position 16. The ground truth had this triple from 2026-11-01 to 2026-11-12 (docs/improvements.md, *Fourth round of rule fixes*).
  - **May matter because:** it is the number of flights of the 2016 campaign, as "Seven balloon launches" is for the campaign of August 2015.
- **Left out:** the 2013, the 2014 and the 2016 campaign PART_OF "BARREL" (notes, "For the 2013 and 2014 the balloon campaigns", "The 2015 and 2016 campaigns" … "Summing over the four BARREL campaigns")
  - **Rule:** What counts as a fact, rule 1: "A fact the record does not state in one passage may be written when the record's own statements meet one of the three tests below; never infer from outside knowledge. The list of tests is closed". The record names one campaign with the mission's name ("August 2015 BARREL campaign" PART_OF "BARREL", rule 2's *A fact inside a name*). No passage states that the 2013, the 2014 or the 2016 campaign is a campaign of BARREL: it follows from counting the campaigns the record describes up to "the four BARREL campaigns", by none of the three tests (*Replacement*, *Comparison*, *Membership by name*). The ground truth had the three triples until 2026-11-12 (docs/improvements.md, *Fourth round of rule fixes*).
  - **May matter because:** without them no ground truth triple connects the three campaigns to the mission.

## "Merged Catalog of Reflection Nebulae" (pool position 20, id a2d5781a-3b10-4bac-8993-295f235db4e4)

A held-out record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. 7 items, 4 that may matter.

- **Left out:** "Merged" (title) and "have been merged" (notes, "Several catalogs of reflection nebulae have been merged to create a uniform catalog") as a method
  - **Rule:** Writing a classed triple, rule 24: "A verb or participle that says only that something was done to the data ("corrected", "calibrated", "detrended", "binned", "mapped", "edited", "convert", "weighted") names no method"
  - **May matter because:** it says how the catalog was made: by merging several catalogs.
- **Left out:** "Several catalogs of reflection nebulae" as the input of the catalog (notes)
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names."
  - The record names none of the catalogs, so COMPUTED_FROM has no object it names. The catalog's named input is written: COMPUTED_FROM "table1.dat".
  - **May matter because:** a search for the catalogs this one merges would need them.
- **Left out:** "uniform" (notes, "a uniform catalog of 913 objects")
  - **Rule:** What counts as a fact, rule 4: "says what kind of thing MODIS is: that belongs in its entity class"
  - "a uniform catalog" says what kind of catalog the record's dataset is; its entity class, Dataset, and HAS_NUMBER_OF "913 objects" are written.
- **Left out:** "The HEASARC has endeavored to render all identifications of the nebulae in the various catalogs according to the styles recommended by the Dictionary of Nomenclature of Celestial Objects." (notes)
  - **Rule:** What counts as a fact, rule 7: "Not facts the record doesn't assert as true: uncertain ones, and ones it requires, requests or recommends."
  - "has endeavored to render" says that the HEASARC tried, and does not assert that every identification follows those styles; "recommended" is the Dictionary's recommendation. "the various catalogs" names no catalog (rule 9).
  - **May matter because:** it says which naming styles the identifications follow.
- **Left out:** "IRAS" (notes, inside "identifications with IRAS point sources")
  - **Rule:** What counts as a fact, rule 2: "When the naming states more than one predicate, or none, the name's words give no ground truth triple" (*A fact inside a name*)
  - "IRAS" stands inside "IRAS point sources", within the Variable "identifications with IRAS point sources" (HAS_VARIABLE), with no words that say how the sources and the craft are related. IRAS is a Platform by rule 1's *Names in a public reference*: the GCMD Platforms keywords (version 25.2) have "IRAS", "Infrared Astronomy Satellite", under Solar/Space Observation Satellites (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/platforms?format=csv, checked on 2026-11-13); the GCMD Instruments keywords' "IRAS", an InfraRed Atmospheric Sounder, does not fit a record about nebulae. Naming identifications or sources with a craft's name states no predicate of the ground truth schema: FROM_PLATFORM is "was collected from this Platform", which is not said of identifications.
  - **May matter because:** it says which survey the nebulae are matched with.
- **Left out:** what "HEASARC" stands for (notes, "The HEASARC has endeavored", "This table was created by the HEASARC" and "a service provided by NASA HEASARC")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what HEASARC is. Its entity class, Organization, is written (DEVELOPED_BY_PARTY and PROVIDED_BY_PARTY "NASA HEASARC", and "NASA HEASARC" PART_OF "NASA"), by rule 1's *Names in a public reference*.
  - The reference: Wikidata, High Energy Astrophysics Science Archive Research Center (Q130537792), also named "HEASARC", an instance of "research center" and of "archive" (https://www.wikidata.org/wiki/Q130537792, checked on 2026-11-13). No official NASA list names it: the GCMD Providers keywords (version 25.2) have no entry for it.
- **Left out:** what "NASA" is (notes, "NASA HEASARC")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what NASA is. Its entity class, Organization, is written ("NASA HEASARC" PART_OF "NASA"), by rule 1's *Names in a public reference*.
  - The reference: GCMD Providers keywords (version 25.2), the level "NASA" under "GOVERNMENT AGENCIES-U.S. FEDERAL AGENCIES", which holds NASA's centers and offices (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/providers?format=csv, checked on 2026-11-13).

## "CH1-ORB MOON M3 2 L0 RAW NEAR-IR SPECTRAL IMAGES V1.0" (pool position 21, id 264a9b23-9a86-46a7-ab61-9661230ea667)

4 items, 1 that may matter.

- **Left out:** what "CH1-ORB" stands for (title)
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what CH1-ORB is. Its entity class, Platform, is written (FROM_PLATFORM "CH1-ORB"), by rule 1's *Names in a public reference*. Until 2026-11-12 "CH1-ORB" gave no ground truth triple, and this item said that it was on no list as written.
  - The reference: PDS4 context product urn:isro:isda:context:instrument_host:spacecraft.ch1_cho, "Chandrayaan-1 Orbiter", of type Spacecraft, which keeps its earlier identifier urn:nasa:pds:context:instrument_host:spacecraft.ch1-orb as another title; the record names the "Chandrayaan-1 mission" (https://pds.nasa.gov/data/pds4/context-pds4/instrument_host/spacecraft.ch1_cho_1.1.xml, checked on 2026-11-12).
  - **Question:** Q6 (b).
- **Left out:** "2" (title, "M3 2 L0")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for"; a bare number is not "L" or "Level" followed by a number.
  - **May matter because:** in PDS3 naming it is most likely the CODMAC level (CODMAC 2 = NASA Level 0, which agrees with "L0"; my reading, not checked for this data set).
  - **Question:** Q6 (b).
- **Left out:** "instrument" (notes, "Moon Mineralogy Mapper (M3) instrument") and "mission" (notes, "Chandrayaan-1 mission")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the thing,"
- **Left out:** what "Moon" is (title, "MOON", and notes, "mission to the Moon")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what Moon is. Its entity class, CelestialBody, is written (HAS_TARGET "Moon"), by rule 1's *Names in a public reference*.
  - The reference: PDS4 context product urn:nasa:pds:context:target:satellite.earth.moon, "Moon", of type Satellite (https://pds.nasa.gov/data/pds4/context-pds4/target/satellite.earth.moon_1.1.xml, checked on 2026-11-12).

## "Flight Data For Tail 655" (pool position 22, id 967275c7-aa2d-4b08-a9db-aff5cf6b7802)

4 items, 2 that may matter.

- **Left out:** "Tail 655" (title)
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what Tail 655 is, and no reference of rule 1's *Names in a public reference* names it: the GCMD Platforms keywords (version 25.1, checked on 2026-11-01; version 25.2, checked on 2026-11-12) and Wikidata (checked on 2026-11-12) have no entry for it. Until 2026-11-01 the ground truth had FROM_PLATFORM "Tail 655" (Platform), read from the title; the record now names no platform, as the record at pool position 15 names none for "HelioWeb" (the double check of batches 4 and 5, finding F22.1).
  - **May matter because:** my reading, not checked: an aircraft's tail number, so the aircraft the data were recorded on; a search by aircraft would need it.
- **Left out:** "individual flight" (notes, "individual flight recorded data"), that each file holds one flight
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names." No flight is named.
  - **May matter because:** it says how the files are cut.
- **Left out:** "Flight Data" (title) as a fact
  - **Rule:** What counts as a fact, rule 4: "says what kind of thing MODIS is: that belongs in its entity class". The flights are not named (rule 9).
- **Left out:** "each with a data structure" (notes), the structure as a thing of its own
  - **Rule:** What counts as a fact, rule 9: "is written for the thing the group belongs to only when it stays true of that thing: what it holds". The 186 parameters are named only by a count, so the structure's contents are written as the dataset's (HAS_VARIABLE "sensor recordings"; HAS_ANCILLARY_DATA "sampling rate", "units", "parameter description", "parameter ID").

## "SOLVE I Ground Site Data" (pool position 23, id ccbc2b1c-cfa2-4867-9981-a845b91d90ab)

A held-out record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. 17 items, 5 that may matter.

- **Left out:** "ground site" (title, "Ground Site Data", and notes, "the ground site data")
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names."
  - No ground site is named, so no FROM_PLATFORM triple is written.
  - **May matter because:** it says the data were collected on the ground, at sites.
- **Left out:** "campaign", "multi-program effort" and "experiment" (notes, "The SOLVE campaign was a NASA multi-program effort", "SOLVE was a two-phase experiment" and "this validation experiment")
  - **Rule:** What counts as a fact, rule 4: "says what kind of thing MODIS is: that belongs in its entity class"
  - They say what kind of thing SOLVE is. Its entity class is Mission ("SAGE III Ozone Loss and Validation Experiment (SOLVE)"), whose definition is "a named effort to collect data, from space, from the air, on water or on the ground", the record's own word "effort"; the ground truth schema's Campaign is "carried out as part of a Mission", which the record does not say of SOLVE. "a NASA multi-program effort of" also names what SOLVE belongs to, written as PART_OF (rule 4: "the kind is left out, and the belonging is a ground truth triple"). The record also writes "SOLVE" for its first phase ("the first phase, SOLVE", and "SOLVE featuring 17 total flights" beside "SOLVE II featuring 11 flights"); those passages are written for the phase, "SOLVE I" (rule 23 of *Writing a classed triple*: the title's wording says more).
- **Left out:** "Atmospheric Effects of Aviation Project (AEAP)" (notes)
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what AEAP is. Its kind word, "Project", fits more than one entity class (a named part of an organization, an Organization, or a named effort to collect data, a Mission), and no reference of rule 1's *Names in a public reference* names it: the GCMD Providers, Platforms and Instruments keywords (version 25.2) and Wikidata have no entry for it (checked on 2026-11-13). So it gives no PART_OF triple, as the two programs beside it do.
  - **May matter because:** it is one of the programs SOLVE belonged to.
- **Left out:** "Earth Observing System (EOS)" (notes)
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what the Earth Observing System is, and its kind word, "System", fits no single entity class, as in the record "HIRDLS/Aura Level 3 Geopotential Height 1deg Lat Zonal Fourier Coefficients V007 (H3ZFCGPH)". Wikidata's Earth Observing System (Q1277644), also named "EOS", is a "program of NASA comprising a series of artificial satellite missions and scientific instruments in Earth orbit", an instance of "science project", a kind that fits both Mission and Organization (https://www.wikidata.org/wiki/Q1277644, checked on 2026-11-13). So it gives no PART_OF triple, and its "Earth" gives no HAS_TARGET triple.
  - **May matter because:** it is one of the programs SOLVE belonged to.
- **Left out:** "primary" and "major" (notes, "SOLVE’s primary objective" and "The major goal of SAGE III")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds gives no ground truth triple, and is taken out of the instance"
- **Left out:** "during the winter" (notes, "SOLVE took place in the Arctic high-latitude region during the winter")
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names."
  - "the winter" names no particular winter; the phases' periods are written (HAS_TIME_SPAN).
  - **May matter because:** it says in which season the measurements were made.
- **Left out:** "The polar ozone depletion processes cause by human-produced chlorine and bromine are most active in mid-to-late winter and early spring in the high Arctic." (notes)
  - **Rule:** Writing a classed triple, rule 21: "A statement that only explains a concept (what a term means, how a quantity behaves in general, which methods are in common use) and is about nothing so connected gives no ground truth triple"
  - It explains when the processes are most active in general, and is about nothing connected to the record's id.
- **Left out:** "balloon platforms" and "ground-based instruments" (notes, "SOLVE also utilized balloon platforms, ground-based instruments, and collaborations with")
  - **Rule:** Writing a classed triple, rule 22: "An item that names no specific thing ("his team") gives no ground truth triple"
  - **May matter because:** they say SOLVE also measured from balloons and from the ground.
- **Left out:** "to achieve the mission objectives" (notes)
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words."
  - The objectives are SOLVE's purposes, written from "SOLVE’s primary objective was" (HAS_PURPOSE).
- **Left out:** "a variety of atmospheric data", "among other atmospheric data" and "among the different aircrafts" (notes)
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names."
  - The words name no quantity and no aircraft; the named quantities are written (MEASURES).
- **Left out:** "JPL" (notes, inside the name "JPL MkIV Balloon Interferometer (MkIV)")
  - **Rule:** What counts as a fact, rule 2: "When the naming states more than one predicate, or none, the name's words give no ground truth triple" (*A fact inside a name*)
  - An organization's name before an instrument's own name could mean that the organization built, operates or owns the instrument, and naming does not settle which: "A relationship that naming does not state (that one thing funded, developed, provided or sponsored the other) is never read from a name". The name stays whole (rule 11 of *Writing a classed triple*); "Balloon" inside it names no particular balloon.
- **Left out:** "NASA" in "NASA ER-2" and "NASA DC-8" as a fact of its own (notes)
  - **Rule:** What counts as a fact, rule 2: "When the naming states more than one predicate, or none, the name's words give no ground truth triple" (*A fact inside a name*)
  - The names are the aircraft's own (the GCMD Platforms keywords, version 25.2, have "NASA ER-2" and "NASA DC-8", checked on 2026-11-13), and they stay whole. The record's own sentence "NASA deployed the NASA ER-2 aircraft and NASA DC-8 aircraft" states what NASA did, written as DEPLOYED_BY_PARTY "NASA".
- **Left out:** "German Aerospace Center’s (DLR)" as a fact of its own (notes, "the German Aerospace Center’s (DLR) FALCON aircraft")
  - **Rule:** What counts as a fact, rule 2: "When the naming states more than one predicate, or none, the name's words give no ground truth triple" (*A fact inside a name*)
  - The possessive says that the aircraft is the Center's, and not whether the Center owns, operates or provides it, so no predicate is read from it; the words stay in the aircraft's instance, as "NASA/NOAA" stays in the platform's instance in the record "VIIRS/NPP BRDF/Albedo Parameter 3 Band M4 Daily L3 Global 30 ArcSec CMG V002". "German" is an adjective and names no country (rule 9, as "South African" in the record "BARREL 4G Rate Counter (RCNT) NaI Scintillator Diagnostics, Level 2, 4 s Data").
- **Left out:** "Stratospheric Aerosol and Gas Experiment (SAGE) III" inside the name "SAGE III Ozone Loss and Validation Experiment (SOLVE)" (notes)
  - **Rule:** What counts as a fact, rule 2: "When the naming states more than one predicate, or none, the name's words give no ground truth triple" (*A fact inside a name*)
  - An Instrument named in a Mission's name states no predicate of the ground truth schema. What SOLVE does for SAGE III is written from its own sentence: HAS_PURPOSE "calibrating the Stratospheric Aerosol and Gas Experiment (SAGE) III satellite measurements" and "validating …".
- **Left out:** what "NASA" is (notes, "a NASA multi-program effort", "NASA’s Earth Science Enterprise (ESE)" and "NASA deployed")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what NASA is. Its entity class, Organization, is written ("SAGE III Ozone Loss and Validation Experiment (SOLVE)" PART_OF "NASA", "NASA’s Earth Science Enterprise (ESE)" PART_OF "NASA", and DEPLOYED_BY_PARTY "NASA"), by rule 1's *Names in a public reference*.
  - The reference: GCMD Providers keywords (version 25.2), the level "NASA" under "GOVERNMENT AGENCIES-U.S. FEDERAL AGENCIES", which holds NASA's centers and offices (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/providers?format=csv, checked on 2026-11-13).
- **Left out:** what "SAGE III" is (notes, "Stratospheric Aerosol and Gas Experiment (SAGE) III satellite measurements" and "The major goal of SAGE III")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record spells out the abbreviation but never says what kind of thing SAGE III is: "Experiment" fits more than one entity class, and in "SAGE III satellite measurements" I read "satellite" as a word of the measurements, not a type word of SAGE III. Its entity class, Instrument, is written ("Stratospheric Aerosol and Gas Experiment (SAGE) III" HAS_PURPOSE "quantitatively assess ozone loss at high latitudes"), by rule 1's *Names in a public reference*.
  - The list: GCMD Instruments keywords (version 25.2), "SAGE III", "Stratospheric Aerosol and Gas Experiment III", under Spectrometers (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/instruments?format=csv, checked on 2026-11-13).
- **Left out:** what "Earth" is (notes, inside the name "NASA’s Earth Science Enterprise (ESE)")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what Earth is. Its entity class, CelestialBody, is written ("NASA’s Earth Science Enterprise (ESE)" HAS_TARGET "Earth", by rule 2's *A fact inside a name*), by rule 1's *Names in a public reference*.
  - The reference: PDS4 context product urn:nasa:pds:context:target:planet.earth, "Earth", of type Planet (https://pds.nasa.gov/data/pds4/context-pds4/target/planet.earth_1.1.xml, checked on 2026-11-13).

## "HIRDLS/Aura Level 3 Geopotential Height 1deg Lat Zonal Fourier Coefficients V007 (H3ZFCGPH)" (pool position 24, id 77a0cb5f-7d69-4f13-aeb1-ce1378d7f1a9)

9 items, 2 that may matter.

- **Left out:** what "HIRDLS" stands for (title, and notes "HIRDLS data", "HIRDLS Level 2 profiles")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for". Its entity class, Instrument, is written (ACQUIRED_BY_INSTRUMENT "HIRDLS", twice), by rule 1's *Names in a public reference*.
  - **May matter because:** it is the instrument's name, the main search key.
  - The list: GCMD Instruments keywords (version 25.1), "HIRDLS", "High-Resolution Dynamics Limb Sounder"; the CMR record of H3ZFCGPH version 007 lists it under the platform Aura (checked on 2026-10-31).
- **Left out:** "entire" (notes, twice: "the entire mission")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds gives no ground truth triple, and is taken out of the instance"
- **Left out:** "mission" (notes, "the entire mission (~3 years) of HIRDLS data"), as FROM_MISSION
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names." No mission is named.
- **Left out:** "may be used to compute values at any longitude" (notes)
  - **Rule:** What counts as a fact, rule 7: "Not facts the record doesn't assert as true: uncertain ones, and ones it requires, requests or recommends." ("may"); and a use is a fact of the work that used the data (rule 9).
  - **May matter because:** it says what the coefficients are for.
- **Left out:** "approach" (notes, "a Kalman filter approach")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the thing,"
- **Left out:** "Earth" (notes, "the version 5 Hierarchical Data Format for the Earth Observing System (HDF-EOS5)")
  - **Rule:** What counts as a fact, rule 2: "When the naming states more than one predicate, or none, the name's words give no ground truth triple" (*A fact inside a name*). The name is a file format's, written whole (HAS_FILE_FORMAT; rule 11 of *Writing a classed triple*). "Earth" does not qualify the format: it stands inside "Earth Observing System", the name of another thing, which the format's name joins to the format by "for". A file format is not about Earth (HAS_TARGET is "is about, or studies, this CelestialBody"), so the format's name states no predicate between the format and Earth. The fact that the inner name states, that the Earth Observing System observes Earth, would need "Earth Observing System" as an instance with an entity class. The record never says what it is, and its kind word "System" fits the definition of no single entity class of the ground truth schema, so its own words do not explain it (rule 1: a name "is explained by the record's own words, since the kind word inside the name is the record's own word, when that word fits the definition of exactly one entity class"). No public reference was looked up for it (rule 1, *Names in a public reference*). So "Earth" gives no ground truth triple. In "Earth Observation Satellites (EOS)" (the record at pool position 4), "Earth" qualifies the satellites, which are the instance itself, so that name states HAS_TARGET "Earth" (rule 2, *A fact inside a name*; rule 19 of *Writing a classed triple*, a target body). The two cases differ in which thing the word qualifies: the instance, or another thing named inside it (decided on 2026-11-13).
- **Left out:** "separate" (notes, "separate data fields")
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words." Three HAS_VARIABLE triples already say there are three fields.
- **Left out:** the notes' quoted name "HIRDLS/Aura Level 3 Geopotential Height Zonal Fourier Coefficients" as another name of the dataset
  - **Rule:** Writing a classed triple, rule 20: "Write ALSO_KNOWN_AS only when the record gives the other name in words of its own"; the thing the title names is always written as its title (rule 23).
- **Left out:** what "Aura" is (title, "HIRDLS/Aura")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what Aura is. Its entity class, Platform, is written (FROM_PLATFORM "Aura"), by rule 1's *Names in a public reference*.
  - The list: GCMD Platforms keywords (version 25.2), "Aura" (checked on 2026-11-11).

## "OPERA Dynamic Surface Water Extent from Sentinel-1 (Version 1)" (pool position 25, id ed2cea26-ed6c-4138-be69-3d32d4ce4858)

14 items, 6 that may matter.

- **Left out:** "irrespective of cloud conditions and daylight illumination" (notes)
  - **Rule:** What counts as a fact, rule 6: "A ground truth triple can't say "not"." ("irrespective of" means "not affected by").
  - **May matter because:** all-weather, day-and-night mapping is a reason to choose a radar product.
- **Left out:** "that often pose challenges to optical sensors" (notes)
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names." "optical sensors" names no sensor.
- **Left out:** "Forward" (notes, "Forward production … began")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds gives no ground truth triple, and is taken out of the instance"
  - **May matter because:** forward processing is new acquisitions, as against reprocessing of older ones, so data from before Sept 2024 may exist.
- **Left out:** "data record" (notes, "the DSWx-S1 data record")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the thing,"
- **Left out:** "a set of 3" (notes, "Each product is distributed as a set of 3 GeoTIFF … files")
  - **Rule:** What counts as a fact, rule 9: "An amount or a count per member gives no ground truth triple". The file format is written (HAS_FILE_FORMAT).
  - **May matter because:** it says how one granule is packaged.
- **Left out:** "Copernicus" and "Sentinel" as things of their own (notes, "The OPERA DSWx-S1 product contains modified Copernicus Sentinel data (2024-2025)")
  - **Rule:** What counts as a fact, rule 2: "When the naming states more than one predicate, or none, the name's words give no ground truth triple" (*A fact inside a name*). The two words stand inside the name of the input data, "modified Copernicus Sentinel data", and the record does not say how those data are related to what the words name (whose data they are, or which craft took them). A programme's name before "Sentinel data" could mean that the programme provided the data, funded them or collected them, and naming does not settle which: "A relationship that naming does not state (that one thing funded, developed, provided or sponsored the other) is never read from a name". An entity class is not what is missing: a programme that an organization runs is an Organization, one of that organization's named parts, as "NASA Living with a Star" is in the record at pool position 19. Wikidata's nearest entries are "Copernicus Programme" (Q1531636) and "Sentinel programme" (Q4303731), and neither has the record's wording as its name (looked up on 2026-11-12).
  - **May matter because:** the words say where the input data come from.
- **Left out:** "To access the calibration/validation database for OPERA Dynamic Surface Water Extent Products, please contact podaac@podaac.jpl.nasa.gov" (notes)
  - **Rule:** Writing a classed triple, rule 21: "Leave out facts about other datasets, such as a variant of the record's dataset (the same data at another temporal resolution, spatial resolution, or version), or a product made from it." The database is not part of, or an input to, the record's dataset.
  - **May matter because:** it is where the validation data are, and who to ask.
  - **Question:** Q24.
- **Left out:** "an interagency effort" (notes)
  - **Rule:** What counts as a fact, rule 4: "says what kind of thing MODIS is: that belongs in its entity class"
- **Left out:** what "Sentinel-1" is (title, and notes, "Sentinel-1 radar observations")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what Sentinel-1 is. Its entity class, Platform, is written (FROM_PLATFORM "Sentinel-1"), by rule 1's *Names in a public reference*.
  - The list: GCMD Platforms keywords (version 25.2), "Sentinel-1" (checked on 2026-11-11).
- **Left out:** "associated" (notes, "water classification and associated confidence layers")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds gives no ground truth triple, and is taken out of the instance". "associated" says only how the fact HAS_ANCILLARY_DATA "confidence" holds, as in the record at pool position 7.
- **Left out:** "OPERA" as the developer of the dataset (title; notes, "Dynamic OPERA Surface Water Extent" and "The OPERA DSWx-S1 product")
  - **Rule:** What counts as a fact, rule 2: "When the naming states more than one predicate, or none, the name's words give no ground truth triple" (*A fact inside a name*). The title and the product's name hold the word "OPERA", and no passage says that OPERA developed, produced or provides the dataset. An organization's name in a dataset's name could mean that the organization developed the dataset, provides it or sponsored it, and naming does not settle which: "A relationship that naming does not state (that one thing funded, developed, provided or sponsored the other) is never read from a name". Until 2026-11-12 the ground truth had the record's dataset DEVELOPED_BY_PARTY "OPERA" (Organization), with the source text "OPERA" (found by both audits of 2026-11-12).
  - The six ground truth triples about OPERA and the Satellite Needs Working Group stay, since the record states each of them: "OPERA" INFORMED_BY "Satellite Needs Working Group (SNWG)", the group's PART_OF "U.S. Government", its two HAS_PURPOSE and its HAS_TARGET "Earth", and "U.S. Government" BASED_IN "U.S.". No chain of ground truth triples links them to the record's id any more, and the record states no fact that would (guidelines, *Finishing a record*: "add that fact only if the record states it"). The same holds for the four ground truth triples about "Peter Minnett" in the record at pool position 4.
  - **May matter because:** my reading, not checked: OPERA is the project that makes the product, so a search by project would need it.
- **Left out:** what "OPERA" stands for (title; notes, "OPERA was informed by the Satellite Needs Working Group (SNWG)")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what OPERA is. Its entity class, Organization, is written ("OPERA" INFORMED_BY "Satellite Needs Working Group (SNWG)"), by rule 1's *Names in a public reference*.
  - The reference: GCMD Providers keywords (version 25.2), "NASA/JPL/OPERA", "Observational Products for End-Users from Remote Sensing Analysis, Jet Propulsion Laboratory, NASA" (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/providers?format=csv, checked on 2026-11-12).
- **Left out:** what "Earth" is (notes)
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what Earth is. Its entity class, CelestialBody, is written (HAS_TARGET "Earth"), by rule 1's *Names in a public reference*.
  - The reference: PDS4 context product urn:nasa:pds:context:target:planet.earth, "Earth", of type Planet (https://pds.nasa.gov/data/pds4/context-pds4/target/planet.earth_1.1.xml, checked on 2026-11-12).
- **Left out:** what "U.S." is (notes, "an interagency effort of the U.S. Government")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what U.S. is. Its entity class, Country, is written (BASED_IN "U.S."), by rule 1's *Names in a public reference*.
  - The reference: Wikidata, United States (Q30), also named "the U.S.", "country located primarily in North America", an instance of "country" and of "sovereign state" (https://www.wikidata.org/wiki/Q30, checked on 2026-11-13). Rule 1's official NASA lists (the GCMD Instruments, Platforms and Providers keywords, and the PDS4 context products) are not lists of countries, and they were not searched for it.

## "VIIRS/NPP BRDF/Albedo NBAR at Solar Noon Band M4 Daily L3 Global 30ArcSec CMG V002" (pool position 26, id b5ef7c20-8253-4c10-91bb-a24f4d26147e)

A held-out record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. 14 items, 5 that may matter.

- **Left out:** "NASA/NOAA" as a fact of its own (notes)
  - **Rule:** What counts as a fact, rule 1: "Only what the record states." The words name the two agencies and the platform, and do not say how they are related (whether the agencies built the platform, launched it or operate it), so they state no fact (rule 2, *A fact inside a name*: "When the naming states more than one predicate, or none, the name's words give no ground truth triple"). "NASA/NOAA" stays in the platform's instance, "NASA/NOAA Suomi National Polar-orbiting Partnership (Suomi NPP)", as in the record "VIIRS/NPP BRDF/Albedo Parameter 3 Band M4 Daily L3 Global 30 ArcSec CMG V002".
- **Left out:** "Data are temporally weighted to the ninth day, which is reflected in the file name." (notes)
  - **Rule:** Writing a classed triple, rule 24: "A verb or participle that says only that something was done to the data ("corrected", "calibrated", "detrended", "binned", "mapped", "edited", "convert", "weighted") names no method"
  - "the file name" names no particular file (rule 9).
  - **May matter because:** it says which day of the 16 each value stands for.
  - **Question:** Q7.
- **Left out:** "VNP43D product suite" and its facts as such (notes: "The VNP43D product suite is provided in a Climate Modeling Grid (CMG)"; "VNP43D80 through VNP43D89 are the NBAR products of the VNP43D BRDF/Albedo product suite"; "this product suite includes NBAR values for the VIIRS Day/Night Band (DNB)")
  - **Rule:** What counts as a fact, rule 1, *Membership by name*: "A statement about the group as a whole is not written for it"
  - The record's identifier VNP43D83 contains "VNP43D", so the facts that hold for each member are written for the record's dataset (the grid, one data layer, the NBAR algorithm); the suite itself and its other members are not, as in the record "VIIRS/NPP BRDF/Albedo Parameter 3 Band M4 Daily L3 Global 30 ArcSec CMG V002".
  - **May matter because:** it says which family the product belongs to.
  - **Question:** Q24; Q25 (b).
- **Left out:** "NBAR values are provided for the nine VIIRS moderate resolution bands (M1 through M5, M7, M8, M10, and M11) included in the [VNP43MA4](https://doi.org/10.5067/VIIRS/VNP43MA4.002) product." (notes)
  - **Rule:** What counts as a fact, rule 1, *Membership by name*: "A statement about the group as a whole is not written for it"
  - The nine bands are what the suite's members cover taken together ("what the members cover taken together"); this dataset's band is written (FOR_CHANNEL "VIIRS band M4 (0.555 μm)"). VNP43MA4 is another dataset, with no "part of" or "made from" link stated (rule 21 of *Writing a classed triple*).
  - **May matter because:** it says the suite's bands come from VNP43MA4, which a search for related products would need.
  - **Question:** Q24.
- **Left out:** "https://doi.org/10.5067/VIIRS/VNP43MA4.002" (notes), VNP43MA4's DOI
  - **Rule:** Writing a classed triple, rule 21: "Leave out facts about other datasets, such as a variant of the record's dataset (the same data at another temporal resolution, spatial resolution, or version), or a product made from it."
  - **May matter because:** it is where the related product is.
- **Left out:** "Due to the large file size" (notes)
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names." No file is named; "large" is a judgement (rule 5).
- **Left out:** "just" (notes, "contains just one data layer")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds gives no ground truth triple, and is taken out of the instance"
- **Left out:** "entire" (notes, "covers the entire globe")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds gives no ground truth triple, and is taken out of the instance"
- **Left out:** "Known Issues" (notes, the heading)
  - **Rule:** What counts as a fact, rule 3: "A heading inside a text field, a line of its own that only names the passage below it ("Known Issues", "BARREL Data Usage Policy"), is formatting too, and gives no ground truth triple."
- **Left out:** "known issues" as what the page is about (notes, "For complete information about known issues please refer to")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds gives no ground truth triple, and is taken out of the instance"
- **Left out:** "MODIS/VIIRS Land Quality Assessment website" (notes), as the page's name
  - **Rule:** Writing a classed triple, rule 20: "Write ALSO_KNOWN_AS only when the record gives the other name in words of its own"
  - **May matter because:** it is the page's name, by which a person would look for it.
- **Left out:** "BRDF/Albedo" (title) and "Bidirectional Reflectance Distribution Function (BRDF) and Albedo" (notes) as what the dataset holds
  - **Rule:** What counts as a fact, rule 1, *Membership by name*: "A statement about the group as a whole is not written for it"
  - The words name the product suite the dataset belongs to ("the VNP43D BRDF/Albedo product suite"), not what this dataset holds: the notes say it is "the NBAR for VIIRS band M4 (0.555 μm)" (HAS_VARIABLE). The record "VIIRS/NPP BRDF/Albedo Parameter 3 Band M4 Daily L3 Global 30 ArcSec CMG V002" writes no ground truth triple from the same words.
- **Left out:** "at Solar Noon" (title)
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words."
  - The notes say it with words of their own: "NBAR algorithm" HAS_PURPOSE "model the values as if they were collected from a nadir view at local solar noon". The values are modelled for solar noon, not observed then, so no OBSERVED_AT_TIME_OF_DAY triple is written (rule 19 of *Writing a classed triple*, *What stays in the instance*).
- **Left out:** what "Suomi National Polar-orbiting Partnership (Suomi NPP)" is (notes; the title writes "NPP")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what the Suomi National Polar-orbiting Partnership is. Its entity class, Platform, is written (FROM_PLATFORM "NASA/NOAA Suomi National Polar-orbiting Partnership (Suomi NPP)", and "Visible Infrared Imaging Radiometer Suite (VIIRS)" ABOARD it), by rule 1's *Names in a public reference*.
  - The list: GCMD Platforms keywords (version 25.2), "Suomi-NPP", "Suomi National Polar-orbiting Partnership" (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/platforms?format=csv, checked on 2026-11-13).

## "MARS EXPRESS MARS MRS 1/2/3 EXTENDED MISSION 8 4193 V1.0" (pool position 29, id 6e6951d6-8ffd-4923-9b12-39d44ce6814d)

A held-out record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. 6 items, 2 that may matter.

- **Left out:** "1/2/3" (title)
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for"
  - **May matter because:** in the record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" the same place in the title was checked to hold the processing levels (its item); not checked for this record.
  - **Question:** Q6 (b).
- **Left out:** "4193" (title)
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for"
  - **May matter because:** it tells this dataset from its siblings, as "1149" does in the record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (its item); not checked for this record.
  - **Question:** Q6 (b).
- **Left out:** "phase" (notes, "the extended mission phase")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the thing,"
  - The phase is written in the title's wording, "EXTENDED MISSION 8", the wording that says more (rule 23).
- **Left out:** what "Mars Express" is (title, "MARS EXPRESS", and notes, "a Mars Express Radio Science data set")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what Mars Express is. The title's first word is the instrument host, a craft: FROM_PLATFORM "Mars Express" (Platform). The notes' "a Mars Express Radio Science data set" names the mission, as "a Rosetta Radio Science data set" does in the record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0": FROM_MISSION "Mars Express" (Mission), and "Mars Express" HAS_TARGET "Mars". Both entity classes are by rule 1's *Names in a public reference*.
  - The list: PDS4 context product urn:esa:psa:context:instrument_host:spacecraft.mex, "The Mars Express Orbiter", of type Spacecraft, also titled "MARS EXPRESS" (https://pds.nasa.gov/data/pds4/context-pds4/instrument_host/spacecraft.mex_1.1.xml, checked on 2026-11-13).
  - The list: PDS4 context product urn:esa:psa:context:investigation:mission.mars_express, "Mars Express", of type Mission, also titled "MARS EXPRESS" (https://pds.nasa.gov/data/pds4/context-pds4/investigation/mission.mars_express_2.1.xml, checked on 2026-11-13).
  - **Question:** Q2.
- **Left out:** what "MRS" stands for (title)
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what MRS is. Its entity class, Instrument, is written (ACQUIRED_BY_INSTRUMENT "MRS"), by rule 1's *Names in a public reference*.
  - The list: PDS4 context product urn:esa:psa:context:instrument:mex.mrs, "Mars Express Orbiter Radio Science", an instrument of the instrument host Mars Express, whose earlier identifier is urn:nasa:pds:context:instrument:mrs.mex: "MRS" is its instrument id, as "VG1" is the host id of Voyager 1 in the record "VG1 J/S/SS PWS EDITED SPECTRUM ANALYZER FULL RES V1.0" (https://pds.nasa.gov/data/pds4/context-pds4/instrument/mex.mrs_1.2.xml, checked on 2026-11-13).
- **Left out:** what "Mars" is (title, "MARS", and notes, inside the name "Mars Express")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what Mars is. Its entity class, CelestialBody, is written (HAS_TARGET "Mars", of the record's dataset and of "Mars Express"), by rule 1's *Names in a public reference*.
  - The reference: PDS4 context product urn:nasa:pds:context:target:planet.mars, "Mars", of type Planet (https://pds.nasa.gov/data/pds4/context-pds4/target/planet.mars_1.3.xml, checked on 2026-11-13).

## "WMAP 7-Year Internal Templates and Needlets New Source Catalog" (pool position 32, id c2488fc9-0b15-4105-b245-85d889ac84c4)

A held-out record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. 14 items, 6 that may matter.

- **Left out:** "new" (notes, "a new needlet-based method") and "New" (title, "New Source Catalog")
  - **Rule:** What counts as a fact, rule 10: "Take out "latest", "current", "now", "then available", and words like them."
  - Both are true only as of when the study was written. The method is written without it, PRODUCED_USING_ALGORITHM "needlet-based method".
  - **May matter because:** the title's "New" says the catalog holds sources not reported before.
- **Left out:** "having the advantage that" (notes, "hence having the advantage that the CMB component is eliminated")
  - **Rule:** What counts as a fact, rule 5: "Take out words such as "great"."
  - What the templates are cleaned of is written: "internal templates" CLEANED_OF "CMB component".
- **Left out:** "the individual frequency channels" and "pairs of frequency channels" (notes)
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names."
  - The words name no particular channel or pair; the named inputs are written (COMPUTED_FROM "Wilkinson Microwave Anisotropy Probe (WMAP) 7-year data" and "internal templates").
- **Left out:** "Using the area of the sky outside the Kq85 galactic mask" (notes)
  - **Rule:** What counts as a fact, rule 8: "The rest of the study is not: its background, its findings, what it says about methods it did not use, and the details of its method beyond what rule 24 of *Writing a classed triple* writes (how the method was applied, its parameters, what it allows)."
  - It is how the method was applied, a setting of the detection step. "Kq85" is also an unexplained code (rule 1).
  - **May matter because:** it says which part of the sky the catalog covers.
- **Left out:** "at the 5-sigma level", "at 5 sigma" and ">= 3 sigma" (notes)
  - **Rule:** What counts as a fact, rule 8: "The rest of the study is not: its background, its findings, what it says about methods it did not use, and the details of its method beyond what rule 24 of *Writing a classed triple* writes (how the method was applied, its parameters, what it allows)."
  - They are the detection thresholds, parameters of the method.
- **Left out:** "they detect a total of 2102 point sources at the 5-sigma level in either the frequency maps or the internal templates. Of these, 1116 are detected either at 5 sigma directly in the frequency channels or at 5 sigma in the internal templates and >= 3 sigma at the corresponding position in the frequency channels." (notes)
  - **Rule:** What counts as a fact, rule 8: "The rest of the study is not: its background, its findings, what it says about methods it did not use, and the details of its method beyond what rule 24 of *Writing a classed triple* writes (how the method was applied, its parameters, what it allows)."
  - The counts are results the study drew from the data. "The authors have made a catalog of these sources" does not say which of the counts the catalog holds, so no HAS_NUMBER_OF triple is written.
  - **May matter because:** a search by catalog size would need the count.
- **Left out:** "Of the 1116 sources, 603 are detections that have not been reported so far in WMAP data." (notes)
  - **Rule:** What counts as a fact, rule 8: "The rest of the study is not: its background, its findings, what it says about methods it did not use, and the details of its method beyond what rule 24 of *Writing a classed triple* writes (how the method was applied, its parameters, what it allows)."
  - It is a finding of the study; it is also negated (rule 6: "A ground truth triple can't say "not".") and "so far" is true only as of writing (rule 10).
  - **May matter because:** it says how many of the sources are new.
- **Left out:** "In total, they identified 1029 of the 1116 sources with counterparts at 5 GHz and 69 at other frequencies." (notes)
  - **Rule:** What counts as a fact, rule 8: "The rest of the study is not: its background, its findings, what it says about methods it did not use, and the details of its method beyond what rule 24 of *Writing a classed triple* writes (how the method was applied, its parameters, what it allows)."
  - It is a finding of the study.
  - **May matter because:** it says how many sources have known counterparts.
- **Left out:** "The authors" as the dataset's developer (notes, "The authors have made a catalog of these sources available")
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names."
  - "The authors" names no specific people. The table's developer is written: DEVELOPED_BY_PARTY "NASA HEASARC" ("This table was created by the HEASARC").
- **Left out:** "the WMAP channels where they are seen" as channels of their own (notes)
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names."
  - The words name no particular channel, so no FOR_CHANNEL triple is written; they stay in the two Variables' instances, "position estimated in the WMAP channels where they are seen" and "flux estimated in the WMAP channels where they are seen".
- **Left out:** "the reference paper" as a Document of its own (notes, "Table 6 from the reference paper")
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names."
  - The record never names the paper, so no DOCUMENTED_AT triple is written; the words stay in the input's instance, "electronic version of Table 6 from the reference paper".
  - **May matter because:** the paper is where the method and the catalog are described.
- **Left out:** what "ApJ" stands for (notes, "the ApJ web site")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for". Its entity class, Document, is given by the record's own words "web site" (rule 20 of *Writing a classed triple*: "A page or site the record names in words, without a web address, is a Document"), and "web site" is a type word (rule 23).
- **Left out:** what "HEASARC" stands for (notes, "This table was created by the HEASARC" and "a service provided by NASA HEASARC")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what HEASARC is. Its entity class, Organization, is written (DEVELOPED_BY_PARTY and PROVIDED_BY_PARTY "NASA HEASARC", and "NASA HEASARC" PART_OF "NASA"), by rule 1's *Names in a public reference*.
  - The reference: Wikidata, High Energy Astrophysics Science Archive Research Center (Q130537792), also named "HEASARC", an instance of "research center" and of "archive" (https://www.wikidata.org/wiki/Q130537792, checked on 2026-11-13). No official NASA list names it: the GCMD Providers keywords (version 25.2) have no entry for it.
- **Left out:** what "NASA" is (notes, "NASA HEASARC")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what NASA is. Its entity class, Organization, is written ("NASA HEASARC" PART_OF "NASA"), by rule 1's *Names in a public reference*.
  - The reference: GCMD Providers keywords (version 25.2), the level "NASA" under "GOVERNMENT AGENCIES-U.S. FEDERAL AGENCIES", which holds NASA's centers and offices (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/providers?format=csv, checked on 2026-11-13).

## "MARS EXPRESS SUN MRS 1/2/3 EXTENDED MISSION 5 3750 V1.0" (pool position 35, id 25ad28f9-4dab-4d1a-9d77-dc648c793d5c)

A held-out record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. 6 items, 2 that may matter.

- **Left out:** "1/2/3" (title)
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for"
  - **May matter because:** in the record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" the same place in the title was checked to hold the processing levels (its item); not checked for this record.
  - **Question:** Q6 (b).
- **Left out:** "3750" (title)
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for"
  - **May matter because:** it tells this dataset from its siblings, as "1149" does in the record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (its item); not checked for this record.
  - **Question:** Q6 (b).
- **Left out:** "phase" (notes, "the extended mission phase")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the thing,"
  - The phase is written in the title's wording, "EXTENDED MISSION 5", the wording that says more (rule 23).
- **Left out:** what "Mars Express" is (title, "MARS EXPRESS", and notes, "a Mars Express Radio Science data set")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what Mars Express is. The title's first word is the instrument host, a craft: FROM_PLATFORM "Mars Express" (Platform). The notes' "a Mars Express Radio Science data set" names the mission, as "a Rosetta Radio Science data set" does in the record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0": FROM_MISSION "Mars Express" (Mission), and "Mars Express" HAS_TARGET "Mars". Both entity classes are by rule 1's *Names in a public reference*.
  - The list: PDS4 context product urn:esa:psa:context:instrument_host:spacecraft.mex, "The Mars Express Orbiter", of type Spacecraft, also titled "MARS EXPRESS" (https://pds.nasa.gov/data/pds4/context-pds4/instrument_host/spacecraft.mex_1.1.xml, checked on 2026-11-13).
  - The list: PDS4 context product urn:esa:psa:context:investigation:mission.mars_express, "Mars Express", of type Mission, also titled "MARS EXPRESS" (https://pds.nasa.gov/data/pds4/context-pds4/investigation/mission.mars_express_2.1.xml, checked on 2026-11-13).
  - **Question:** Q2.
- **Left out:** what "MRS" stands for (title)
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what MRS is. Its entity class, Instrument, is written (ACQUIRED_BY_INSTRUMENT "MRS"), by rule 1's *Names in a public reference*.
  - The list: PDS4 context product urn:esa:psa:context:instrument:mex.mrs, "Mars Express Orbiter Radio Science", an instrument of the instrument host Mars Express, whose earlier identifier is urn:nasa:pds:context:instrument:mrs.mex: "MRS" is its instrument id, as "VG1" is the host id of Voyager 1 in the record "VG1 J/S/SS PWS EDITED SPECTRUM ANALYZER FULL RES V1.0" (https://pds.nasa.gov/data/pds4/context-pds4/instrument/mex.mrs_1.2.xml, checked on 2026-11-13).
- **Left out:** what "SUN" and "Mars" are (title, "SUN", and notes, inside the name "Mars Express")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what the Sun or Mars is. Their entity class, CelestialBody, is written (the record's dataset HAS_TARGET "SUN", and "Mars Express" HAS_TARGET "Mars"), by rule 1's *Names in a public reference*.
  - The reference: PDS4 context product urn:nasa:pds:context:target:star.sun, "Sun", of type Star (https://pds.nasa.gov/data/pds4/context-pds4/target/star.sun_1.1.xml, checked on 2026-11-13); and, for Mars, urn:nasa:pds:context:target:planet.mars, "Mars", of type Planet (https://pds.nasa.gov/data/pds4/context-pds4/target/planet.mars_1.3.xml, checked on 2026-11-13).

## "VIIRS/NOAA20 Dark Target Aerosol 6-Min L2 Swath 6 km" (pool position 38, id 6ed59de2-47ac-488a-8641-dbe6223fb0e6)

A held-out record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. 18 items, 5 that may matter.

- **Left out:** "satellite-derived" (notes, "provides satellite-derived measurements of Aerosol Optical Thickness (AOT)")
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names."
  - "satellite" names no particular satellite; the platform the record names is written (FROM_PLATFORM "NOAA-20"). "derived" names no method (rule 24 of *Writing a classed triple*).
- **Left out:** "their properties" (notes, "measurements of Aerosol Optical Thickness (AOT) and their properties over land and ocean")
  - **Rule:** Writing a classed triple, rule 22: "An item that names no specific thing ("his team") gives no ground truth triple"
  - "their size parameters" names a kind of property, and is written (HAS_MEASUREMENTS_OF "size parameters").
- **Left out:** "6-Min" (title) as a fact of its own
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words."
  - The notes state the 6 minutes twice. "every 6 minutes" is written HAS_TEMPORAL_RESOLUTION "6 minutes", the notes' wording, which spells out "Min" (rule 23). "incorporates 64 (750 m) pixels over a 6-minute acquisition" is written HAS_GRANULE_DURATION "6-minute": the record's dataset is a "set of products", and the six minutes are each product's (rule 9: "unless the predicate itself says "each""). The record does not say which of the two the title's "6-Min" means.
- **Left out:** "incarnation of the dark target (DT) aerosol product" (notes, "The NOAA-20 … Visible Infrared Imaging Radiometer Suite (VIIRS) incarnation of the dark target (DT) aerosol product")
  - **Rule:** What counts as a fact, rule 4: "says what kind of thing MODIS is: that belongs in its entity class"
  - The words say that the record's dataset is one form of the DT aerosol product, a kind of product. The method they name is written (PRODUCED_USING_ALGORITHM "dark target (DT)"), and "aerosol" is written in the wording that says more, "Aerosol Optical Thickness (AOT)" (rule 23).
- **Left out:** "the same" (notes, "is based on the same DT algorithm")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds gives no ground truth triple, and is taken out of the instance"
- **Left out:** "One helps retrieve aerosol information over ocean (dark in visible and longer wavelengths), while the second aids retrievals over vegetated/dark-soiled land (dark in the visible)." (notes)
  - **Rule:** What counts as a fact, rule 9: "A fact the record states for each member of a group it names only by a count or a common noun ("186 parameters each with …", "Each product is …") is written for the thing the group belongs to only when it stays true of that thing: what it holds, what it measures, what it comes from, or what format its files are in."
  - The record names the two algorithms only by a count ("Two separate and distinct DT algorithms"). What each one helps to retrieve is not true of "dark target (DT)" as a whole, and a purpose is not among the facts the rule writes for the whole. The parentheses explain why the ocean and the land look dark, a statement that only explains a concept (rule 21 of *Writing a classed triple*).
  - **May matter because:** it says which of the two algorithms serves the ocean and which the land.
- **Left out:** "orbit-level" (notes, "This orbit-level product")
  - **Rule:** What counts as a fact, rule 4: "says what kind of thing MODIS is: that belongs in its entity class"
  - The words say what kind of product the record's dataset is. The layout the title names is written (HAS_SPATIAL_REPRESENTATION "Swath").
- **Left out:** "at-nadir" (notes, "has an at-nadir resolution of 6 km x 6 km, and progressively increases away from nadir given the sensor's scanning geometry and Earth's curvature")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds gives no ground truth triple, and is taken out of the instance"
  - My ground truth triple HAS_SPATIAL_RESOLUTION "6 km x 6 km" is written without it, since the title states the resolution without it ("6 km", a shorter wording of the same fact, rule 23). The notes' sentence alone does not state the resolution without it, and rule 11 of *Writing a classed triple* would then keep "at-nadir" in what the predicate says, which HAS_SPATIAL_RESOLUTION does not say. The rest of the sentence names no value (rule 9) and explains its cause (rule 21 of *Writing a classed triple*).
  - **May matter because:** it says that the 6 km holds at nadir only, and that the cells grow away from it.
- **Left out:** "8 x 8" and "64" (notes, "accommodates 8 x 8 native VIIRS moderate-resolution (M-band) pixels" and "incorporates 64 (750 m) pixels")
  - **Rule:** What counts as a fact, rule 9: "An amount or a count per member gives no ground truth triple, unless the predicate itself says "each" (HAS_GRANULE_DURATION, HAS_SPATIAL_RESOLUTION)."
  - They count the pixels in each value of the record's dataset. The pixels are written as its input (COMPUTED_FROM "native VIIRS moderate-resolution (M-band) pixels").
- **Left out:** "moderate-resolution (M-band)" as a Channel (notes, inside "native VIIRS moderate-resolution (M-band) pixels")
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names."
  - The words name a group of the instrument's bands, not one band, so no FOR_CHANNEL or CHANNEL_OF triple is written. They stay in the pixels' instance.
  - **May matter because:** it says which of the instrument's bands the pixels come from.
- **Left out:** "nominally" (notes, "pixels that nominally have ~750 m horizontal pixel size")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds gives no ground truth triple, and is taken out of the instance"
- **Left out:** "set of products" (notes, "This Version-2 set of products")
  - **Rule:** What counts as a fact, rule 4: "says what kind of thing MODIS is: that belongs in its entity class"
- **Left out:** "derived from the NOAA-20 VIIRS source" (notes, "the first collection of the Level-2 Dark Target Aerosol derived from the NOAA-20 VIIRS source")
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words."
  - ACQUIRED_BY_INSTRUMENT, FROM_PLATFORM and ABOARD already state it, and "Level-2 Dark Target Aerosol" repeats the level, the method and what is measured.
- **Left out:** "Hence, it bears outlining the differences between the products derived from NOAA-20 VIIRS as against the Suomi National Polar-orbiting Partnership (SNPP) VIIRS." (notes)
  - **Rule:** What counts as a fact, rule 7: "Not facts the record doesn't assert as true: uncertain ones, and ones it requires, requests or recommends."
  - "it bears outlining" recommends, and the products made from the SNPP VIIRS are other datasets (rule 21 of *Writing a classed triple*). The name "Suomi National Polar-orbiting Partnership (SNPP) VIIRS" still states that the instrument is aboard that platform, and is written so (rule 17 of *Writing a classed triple*, *A platform in an instrument's name*).
  - **May matter because:** it says that products of the same kind were made from the SNPP VIIRS before.
- **Left out:** "LAADS", "product description page" and "Dark Target aerosol team page" (notes, the words of the two links)
  - **Rule:** Writing a classed triple, rule 20: "Write ALSO_KNOWN_AS only when the record gives the other name in words of its own"
  - The two addresses are written (DOCUMENTED_AT, WebPage), as in the record "VIIRS/NPP BRDF/Albedo Parameter 3 Band M4 Daily L3 Global 30 ArcSec CMG V002". "LAADS" before a page's name, and the "Dark Target aerosol team" inside one, give no ground truth triple (rule 2, *A fact inside a name*: "When the naming states more than one predicate, or none, the name's words give no ground truth triple"): naming a page with an organization's or a team's name could mean that it wrote the page, keeps it or is its subject. The GCMD Providers keywords (version 25.2) have "NASA/GSFC/SED/ESD/HBSL/BISB/LAADS", the "L1 and Atmosphere Archive and Distribution System", at the web site of the first address (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/providers?format=csv, checked on 2026-11-13).
  - **May matter because:** they name who keeps the two pages.
- **Left out:** "mission" and "instruments" (notes, "the Terra and Aqua mission's MODIS instruments")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the thing,"
  - The record's lowercase type words give the entity classes: Mission for "Terra" and "Aqua", and Instrument for "MODIS". The GCMD Platforms keywords file Terra and Aqua as platforms, but a reference is used only for a name the record does not explain (rule 1, *Names in a public reference*). The possessive "mission's" is written as PART_OF ("MODIS" PART_OF "Terra" and "MODIS" PART_OF "Aqua"), the predicate rule 2 names for "a Mission named in the name of one of its parts (an instrument, a craft, a campaign, a team)".
- **Left out:** what "NOAA-20" is (title, "NOAA20", and notes)
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what NOAA-20 is. Its entity class, Platform, is written (FROM_PLATFORM "NOAA-20", "Visible Infrared Imaging Radiometer Suite (VIIRS)" ABOARD "NOAA-20", and "NOAA-20" ALSO_KNOWN_AS "Joint Polar Satellite System-1 (JPSS-1)"), by rule 1's *Names in a public reference*. The title's "NOAA20" differs from "NOAA-20" only by a hyphen, so it is the same wording (rule 23 of *Writing a classed triple*).
  - The list: GCMD Platforms keywords (version 25.2), "NOAA-20", "Joint Polar Satellite System - 1", under Earth Observation Satellites (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/platforms?format=csv, checked on 2026-11-13).
- **Left out:** what "Suomi National Polar-orbiting Partnership (SNPP)" is (notes)
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what the Suomi National Polar-orbiting Partnership is. Its entity class, Platform, is written ("Visible Infrared Imaging Radiometer Suite (VIIRS)" ABOARD it), by rule 1's *Names in a public reference*.
  - The list: GCMD Platforms keywords (version 25.2), "Suomi-NPP", "Suomi National Polar-orbiting Partnership" (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/platforms?format=csv, checked on 2026-11-13).

## "First ISCCP Regional Experiment (FIRE) Cirrus Phase II Raman Lidar Data" (pool position 41, id 26714637-d3cd-4e11-9600-5b764346bef3)

A held-out record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. 12 items, 6 that may matter.

- **Left out:** what "First ISCCP Regional Experiment (FIRE)" is (title and notes)
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The name's kind word, "Experiment", fits more than one entity class: a named effort to collect data (Mission), or a device (Instrument), as "Stratospheric Aerosol and Gas Experiment (SAGE) III" in the record "SOLVE I Ground Site Data". No reference of rule 1's *Names in a public reference* names it: the GCMD Platforms, Instruments and Providers keywords (version 25.2) and Wikidata have no entry for it (checked on 2026-11-13). I read the record's own sentences as its explanation: FIRE has goals, its "four intensive field-observation periods were planned and executed", and "Each mission combined coordinated satellite, airborne, and surface observations". They fit the definition of Mission ("a named effort to collect data, from space, from the air, on water or on the ground") and of no other entity class, so Mission is written (FROM_MISSION, HAS_PURPOSE, HAS_NUMBER_OF, and the periods' PART_OF).
- **Left out:** "ISCCP" (title and notes, inside "First ISCCP Regional Experiment (FIRE)", and "ISCCP data")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what ISCCP is. Wikidata's International Satellite Cloud Climatology Project (Q6052840), labelled "ISCCP" in German, has no "instance of" statement, so its kind fits no entity class (https://www.wikidata.org/wiki/Q6052840, checked on 2026-11-13), and no official NASA list names it. So "ISCCP" gives no ground truth triple (rule 2, *A fact inside a name*), and its words stay in the instances that hold them.
  - **May matter because:** it names the project the experiment belongs to.
- **Left out:** "To-date" (notes, "To-date, four intensive field-observation periods were planned and executed")
  - **Rule:** What counts as a fact, rule 10: "Take out "latest", "current", "now", "then available", and words like them."
- **Left out:** "Cirrus Phase II" (title) as a wording of its own
  - **Rule:** Writing a classed triple, rule 23: "When a record names the same thing more than once, in different words, use the wording the first of the four tests below picks, in every ground truth triple"
  - The title's "Cirrus Phase II" and the notes' "a second cirrus IFO in southeastern Kansas (November 13 - December 7, 1991)" name one period: the record's dataset was collected "from 13 Nov 1991 to07 Dec 1991", the dates of the second cirrus period. Test 1 ties, and test 2 picks the notes' wording, which states the period's facts with words for them: HAS_MISSION_PHASE "second cirrus IFO". The entity class of the four periods is MissionPhase, from the title's word "Phase" (rule 1). The ground truth schema's Campaign ("a named period of field measurements …") fits the notes' "intensive field-observation periods" as well, and no predicate of the ground truth schema links a dataset to a Campaign.
- **Left out:** "cirrus" and "marine stratocumulus" as facts of the periods (notes, inside "a cirrus IFO", "a marine stratocumulus IFO", "a second cirrus IFO" and "a second marine stratocumulus IFO")
  - **Rule:** What counts as a fact, rule 2: "When the naming states more than one predicate, or none, the name's words give no ground truth triple" (*A fact inside a name*)
  - Naming a period with a kind of cloud states no predicate of the ground truth schema: HAS_TARGET is for a CelestialBody.
  - **May matter because:** it says which clouds each period studied.
- **Left out:** "Each mission combined coordinated satellite, airborne, and surface observations with modeling studies to investigate the cloud properties and physical processes of the cloud systems." (notes)
  - **Rule:** What counts as a fact, rule 9: "A fact the record states for each member of a group it names only by a count or a common noun ("186 parameters each with …", "Each product is …") is written for the thing the group belongs to only when it stays true of that thing: what it holds, what it measures, what it comes from, or what format its files are in."
  - "Each mission" names its members only by a common noun. What they combined and what they investigated are not among the facts the rule writes for the whole, and the observations name no satellite, aircraft or site (rule 9: "A ground truth triple needs a subject and an object the record names.").
  - **May matter because:** it says how FIRE collected its data.
- **Left out:** "GSFC" (notes, inside "GSFC Raman Lidar")
  - **Rule:** What counts as a fact, rule 2: "When the naming states more than one predicate, or none, the name's words give no ground truth triple" (*A fact inside a name*)
  - An organization's name before an instrument's own name could mean that the organization built, operates or owns the instrument, as "JPL" in "JPL MkIV Balloon Interferometer (MkIV)" in the record "SOLVE I Ground Site Data". The name stays whole (rule 11 of *Writing a classed triple*).
- **Left out:** "summed" as a method (notes, "Data are summed for one minute in the detectors and saved to a file.")
  - **Rule:** Writing a classed triple, rule 24: "A verb or participle that says only that something was done to the data ("corrected", "calibrated", "detrended", "binned", "mapped", "edited", "convert", "weighted") names no method"
  - The minute is written (HAS_COMPOSITING_PERIOD "one minute"). "in the detectors" and "to a file" name no detector and no file (rule 9).
  - **May matter because:** it says how each profile is made.
- **Left out:** "For the 10 minute averaged data, the data are summed for 10 minutes before the calculations are performed." (notes)
  - **Rule:** Writing a classed triple, rule 21: "Leave out facts about other datasets, such as a variant of the record's dataset (the same data at another temporal resolution, spatial resolution, or version), or a product made from it."
  - The 10 minute averaged data are the same data at another temporal resolution. The record's dataset "consists of a series of one minute profiles", and the record states no "part of" or "made from" link between the two.
  - **May matter because:** it says that 10-minute averages of the data exist.
- **Left out:** "Zero (0) km means sea level." (notes)
  - **Rule:** Writing a classed triple, rule 21: "A statement that only explains a concept (what a term means, how a quantity behaves in general, which methods are in common use) and is about nothing so connected gives no ground truth triple"
- **Left out:** "The site altitude is 0.229 km" (notes)
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names."
  - The record never names the site.
  - **May matter because:** it gives the height of the lidar's site.
- **Left out:** "thefirst data point is at 0.1845 km above ground level" (notes)
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words."
  - It gives the start of the vertical range counted from the ground: 0.229 km and 0.1845 km make the "0.4135" of "from 0.4135 to 10.299 kilometers", which counts from sea level. HAS_VERTICAL_RANGE is written once, from the sentence that states the whole range.

## "ROSETTA-ORBITER 67P NAVCAM 2 COMET ESCORT 3 MTP019 V1.0" (pool position 44, id 87c1785c-4218-427d-a502-8ef5c6d7436a)

A held-out record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. 9 items, 2 that may matter.

- **Left out:** "2" (title, "NAVCAM 2")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for"; a bare number is not "L" or "Level" followed by a number.
  - **Question:** Q6 (b).
- **Left out:** "MTP019" (title)
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for"
  - **May matter because:** it tells this dataset from its siblings, as "MTP020" does in the record "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0" (its item; not checked for this record).
  - **Question:** Q6 (b).
- **Left out:** "RAW" (notes, "ROSETTA NAVCAM RAW DATA")
  - **Rule:** Writing a classed triple, rule 19: "A qualifier that only says how far the data are processed ("raw", "edited", "calibrated", "derived") is not a processing level, and stays in the instance, as written."
  - "ROSETTA NAVCAM RAW DATA" names what the record's dataset contains, which is the record's dataset itself (rule 19, *Whose fact it is*: "A qualifier of the "data" or "products" that a dataset "contains" or "consists of" is that dataset's fact"). The record's dataset is written as its title (rule 23, *The thing the title names*), so the instance the word would stay in is never written.
  - **May matter because:** it says that the images are not processed.
- **Left out:** "COMET" (title, "COMET ESCORT 3")
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names."
  - The phase is written in the notes' wording, "Escort Phase 3" (rule 23, test 2: the notes' sentence states the phase's facts with words for them). The title's "COMET" names no particular comet, and the record never calls "67P/CG" a comet, so no HAS_TARGET of the phase is written. The records "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" and "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0" write one, since their notes say "the comet 67P" and "comet 67P/Churyumov-Gerasimenko 1 (1969 R1)".
- **Left out:** "when at the vicinity of" (notes, "when at the vicinity of target 67P/CG")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds gives no ground truth triple, and is taken out of the instance"
  - HAS_TARGET "67P/CG" is written; the words say where the craft was when the data were taken.
- **Left out:** what "ROSETTA-ORBITER" is (title)
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what ROSETTA-ORBITER is. Its entity class, Platform, is written (FROM_PLATFORM "ROSETTA-ORBITER"), by rule 1's *Names in a public reference*.
  - The list: PDS4 context product urn:esa:psa:context:instrument_host:spacecraft.ro, "The Rosetta Orbiter Spacecraft", of type Spacecraft, also titled "ROSETTA-ORBITER" (https://pds.nasa.gov/data/pds4/context-pds4/instrument_host/spacecraft.ro_1.1.xml, checked on 2026-11-13).
- **Left out:** what "ROSETTA" is (notes, "ROSETTA NAVCAM RAW DATA")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what ROSETTA is. Its entity class, Mission, is written (FROM_MISSION "ROSETTA", and "NAVCAM" PART_OF "ROSETTA", by rule 2's *A fact inside a name*), by rule 1's *Names in a public reference*.
  - The list: PDS4 context product urn:esa:psa:context:investigation:mission.international_rosetta_mission, "The International Rosetta Mission", of type Mission, also titled "ROSETTA" (https://pds.nasa.gov/data/pds4/context-pds4/investigation/mission.international_rosetta_mission_1.1.xml, checked on 2026-11-13). The craft's entry is titled "ROSETTA-ORBITER", not "ROSETTA".
- **Left out:** what "NAVCAM" stands for (title and notes)
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what NAVCAM is. Its entity class, Instrument, is written (ACQUIRED_BY_INSTRUMENT "NAVCAM", and "NAVCAM" PART_OF "ROSETTA"), by rule 1's *Names in a public reference*.
  - The list: PDS4 context product urn:esa:psa:context:instrument:ro.navcam, "The Navigation Camera (NavCam) for the Rosetta Orbiter" (https://pds.nasa.gov/data/pds4/context-pds4/instrument/ro.navcam_1.2.xml, checked on 2026-11-13); "NAVCAM" and "NavCam" differ only in capitals (rule 23 of *Writing a classed triple*).
- **Left out:** what "67P/CG" is (title, "67P", and notes, "target 67P/CG")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what 67P/CG is. Its entity class, CelestialBody, is written (HAS_TARGET "67P/CG"), by rule 1's *Names in a public reference*. "67P/CG" stays whole, since "CG" is never named alone (rule 22 of *Writing a classed triple*, *Lists joined by "/" or "+"*), and it says more than the title's "67P" (rule 23).
  - The reference: Wikidata, 67P/Churyumov–Gerasimenko (Q844672), whose other names include "67P" and "67P/C-G", an instance of "Jupiter-family comet" (https://www.wikidata.org/wiki/Q844672, checked on 2026-11-13). The record's "67P/CG" differs from "67P/C-G" only by a hyphen (rule 23). The PDS4 context product urn:nasa:pds:context:target:comet.67p_churyumov-gerasimenko names the comet "67P/Churyumov-Gerasimenko" only, a wording this record does not use.

## "Privacy Preserving Distributed Data Mining" (pool position 47, id 7615f547-e889-493f-b13b-0b54a3029a71)

A held-out record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. The record states no facts, so it keeps its describes triple alone. Its describes class is Algorithm, since the title names a kind of data mining, a method, and the text never says what the catalog entry holds. 4 items, 1 that may matter.

- **Left out:** "Distributed data mining from privacy-sensitive multi-party data is likely to play an important role in the next generation of integrated vehicle health monitoring systems." (notes)
  - **Rule:** What counts as a fact, rule 7: "Not facts the record doesn't assert as true: uncertain ones, and ones it requires, requests or recommends."
  - "is likely to" means "will probably", which rule 7 names for "is expected to".
- **Left out:** the example, from "For example, consider an airline manufacturer" to "were available to [tex]$\mathcal{C}$[/tex]." (notes)
  - **Rule:** What counts as a fact, rule 7: "Not facts the record doesn't assert as true: uncertain ones, and ones it requires, requests or recommends."
  - The record asks the reader to suppose a case ("consider"), and states none of it as true; its manufacturer, aircraft model and companies are letters that name nothing specific (rule 9), and "can reveal", "may not be an option" and "may be statistically more significant" are uncertain.
  - **May matter because:** it says what the method is meant for: mining data that several airlines hold, without collecting them in one place.
- **Left out:** "The potential problems arising out of such a data mining scenario are:" (notes)
  - **Rule:** What counts as a fact, rule 7: "Not facts the record doesn't assert as true: uncertain ones, and ones it requires, requests or recommends."
  - "potential" makes the problems uncertain, and the text ends before it names any (rule 9).
- **Left out:** "Privacy Preserving" and "Distributed" (title)
  - **Rule:** What counts as a fact, rule 4: "says what kind of thing MODIS is: that belongs in its entity class"
  - They say what kind of data mining the title names.

## "VIIRS/NPP BRDF/Albedo Parameter 1 Band M3 Daily L3 Global 30 ArcSec CMG V002" (pool position 50, id 28e8b8fd-4463-4794-b810-44934fd449f6)

A held-out record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. Its text is that of the record "VIIRS/NPP BRDF/Albedo Parameter 3 Band M4 Daily L3 Global 30 ArcSec CMG V002" with another parameter, band and identifier, and it is annotated the same way. 16 items, 6 that may matter.

- **Left out:** "NASA/NOAA" as a fact of its own (notes)
  - **Rule:** What counts as a fact, rule 1: "Only what the record states." The words name the two agencies and the platform, and do not say how they are related (whether the agencies built the platform, launched it or operate it), so they state no fact (rule 2, *A fact inside a name*: "When the naming states more than one predicate, or none, the name's words give no ground truth triple"). "NASA/NOAA" stays in the platform's instance, "NASA/NOAA Suomi National Polar-orbiting Partnership (Suomi NPP)", as in the record "VIIRS/NPP BRDF/Albedo Parameter 3 Band M4 Daily L3 Global 30 ArcSec CMG V002".
- **Left out:** "Data are temporally weighted to the ninth day, which is reflected in the file name." (notes)
  - **Rule:** Writing a classed triple, rule 24: "A verb or participle that says only that something was done to the data ("corrected", "calibrated", "detrended", "binned", "mapped", "edited", "convert", "weighted") names no method"
  - "the file name" names no particular file (rule 9).
  - **May matter because:** it says which day of the 16 each value stands for.
  - **Question:** Q7.
- **Left out:** "VNP43D product suite" and its facts as such (notes: "The VNP43D product suite is provided in a Climate Modeling Grid (CMG)"; "this product suite includes model parameters for the VIIRS Day/Night Band (DNB) as VNP43D37 through VNP43D39")
  - **Rule:** What counts as a fact, rule 1, *Membership by name*: "A statement about the group as a whole is not written for it"
  - The record's identifier VNP43D07 contains "VNP43D", so the facts that hold for each member are written for the record's dataset (the grid, one data layer); the suite itself and its other members are not.
  - **May matter because:** it says which family the product belongs to, and that the family has 39 one-layer products.
  - **Question:** Q24; Q25 (b).
- **Left out:** "Each of the three model parameters (isotropic, volumetric, and geometric) for each of the nine VIIRS moderate resolution bands along with the visible, near-infrared (NIR), and shortwave bands included in the [VNP43MA1](…) product is stored in a separate file as VNP43D01 through VNP43D36." (notes)
  - **Rule:** Writing a classed triple, rule 21: "Leave out facts about other datasets, such as a variant of the record's dataset (the same data at another temporal resolution, spatial resolution, or version), or a product made from it."
  - The files are the family's other products, and VNP43MA1 is another dataset with no "part of" or "made from" link stated.
  - **May matter because:** it says that the parameters come from VNP43MA1, which a search for related products would need.
  - **Question:** Q24; Q12.
- **Left out:** "https://doi.org/10.5067/VIIRS/VNP43MA1.002" (notes), VNP43MA1's DOI
  - **Rule:** Writing a classed triple, rule 21: "Leave out facts about other datasets, such as a variant of the record's dataset (the same data at another temporal resolution, spatial resolution, or version), or a product made from it."
  - **May matter because:** it is where the related product is.
- **Left out:** "Due to the large file size" (notes)
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names." No file is named; "large" is a judgement (rule 5).
- **Left out:** "just" (notes, "contains just one data layer")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds gives no ground truth triple, and is taken out of the instance"
- **Left out:** "entire" (notes, "covers the entire globe")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds gives no ground truth triple, and is taken out of the instance"
- **Left out:** "BRDF/Albedo values for VIIRS band M3" COMPUTED_FROM "volumetric parameters" and "geometric parameters", and FOR_CHANNEL "VIIRS band M3 (0.488 μm)" (notes)
  - **Rule:** Writing a classed triple, rule 21: "Leave out facts about other datasets, such as a variant of the record's dataset (the same data at another temporal resolution, spatial resolution, or version), or a product made from it." Its connection to the record's dataset is a ground truth triple: "BRDF/Albedo values for VIIRS band M3" COMPUTED_FROM the record's dataset (rule 24, *The record's dataset's own values*: "when the input is the record's dataset's own values, the input is the record's dataset").
  - **May matter because:** it says the albedo needs all three parameters, that is, three of the family's products together.
  - **Question:** Q24.
- **Left out:** "used to derive" as a purpose of the parameter (notes)
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words." COMPUTED_FROM says it; and a use is not a purpose (rule 9: "What data have been used for, or can be used for, is a fact of the work that used them, not of the data").
- **Left out:** "Known Issues" (notes, the heading)
  - **Rule:** What counts as a fact, rule 3: "A heading inside a text field, a line of its own that only names the passage below it ("Known Issues", "BARREL Data Usage Policy"), is formatting too, and gives no ground truth triple."
- **Left out:** "known issues" as what the page is about (notes, "For complete information about known issues please refer to")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds gives no ground truth triple, and is taken out of the instance"
- **Left out:** "MODIS/VIIRS Land Quality Assessment website" (notes), as the page's name
  - **Rule:** Writing a classed triple, rule 20: "Write ALSO_KNOWN_AS only when the record gives the other name in words of its own"
  - **May matter because:** it is the page's name, by which a person would look for it.
- **Left out:** "NIR" as another name of "near-infrared", and "DNB" of "VIIRS Day/Night Band" (notes)
  - **Rule:** Writing a classed triple, rule 21: "Leave out facts about other datasets, such as a variant of the record's dataset (the same data at another temporal resolution, spatial resolution, or version), or a product made from it." The bands are the family's, not this dataset's.
- **Left out:** "BRDF/Albedo" (title) and "Bidirectional Reflectance Distribution Function (BRDF) and Albedo" (notes) as what the dataset holds
  - **Rule:** What counts as a fact, rule 1, *Membership by name*: "A statement about the group as a whole is not written for it"
  - The words name the product suite the dataset belongs to, not what this dataset holds: the notes say it is "the BRDF isotropic parameter for VIIRS band M3 (0.488 μm)" (HAS_VARIABLE), as in the record "VIIRS/NPP BRDF/Albedo NBAR at Solar Noon Band M4 Daily L3 Global 30ArcSec CMG V002".
- **Left out:** what "Suomi National Polar-orbiting Partnership (Suomi NPP)" is (notes; the title writes "NPP")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what the Suomi National Polar-orbiting Partnership is. Its entity class, Platform, is written (FROM_PLATFORM "NASA/NOAA Suomi National Polar-orbiting Partnership (Suomi NPP)", and "Visible Infrared Imaging Radiometer Suite (VIIRS)" ABOARD it), by rule 1's *Names in a public reference*.
  - The list: GCMD Platforms keywords (version 25.2), "Suomi-NPP", "Suomi National Polar-orbiting Partnership" (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/platforms?format=csv, checked on 2026-11-13).

## "DEEP IMPACT 9P/TEMPEL CRUISE - RAW MRI NAV IMAGES V1.0" (pool position 53, id 7edfd387-7276-4030-b01e-a15d6f7da5c9)

A held-out record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. 6 items, 1 that may matter.

- **Left out:** "These observations were used for optical and autonomous navigation (NAV) of the flyby spacecraft." (notes), and the title's "NAV"
  - **Rule:** What counts as a fact, rule 9: "What data have been used for, or can be used for, is a fact of the work that used them, not of the data: when the record doesn't name that work, it gives no ground truth triple."
  - The navigation is the use itself, and no work that used the data is named. "the flyby spacecraft" is not a name, and the record does not say that it carries the instrument (rule 9: "A ground truth triple needs a subject and an object the record names.").
  - **May matter because:** it says what the images were taken for.
- **Left out:** "phase", "the mission" and "comet" (notes, "during the cruise phase of the mission" and "Test images of comet 9P/Tempel 1")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the thing,"
  - My ground truth triples have the phase "cruise" and the target "9P/Tempel 1". "the mission" names the mission in other words, and is written "Deep Impact", the one mission the record names (rule 23).
- **Left out:** "RAW", "CRUISE", "IMAGES" and "TEMPEL" (title) as facts of their own
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words."
  - The notes state them: "raw calibration and test images" (the two parts, and HAS_SPATIAL_REPRESENTATION "images"), "the cruise phase" (HAS_MISSION_PHASE "cruise") and "comet 9P/Tempel 1". The title's "9P/TEMPEL" is two items (rule 22, *Lists joined by "/" or "+"*), and both give HAS_TARGET "9P/Tempel 1", the wording that says more (rule 23).
- **Left out:** what "Deep Impact" is (title, "DEEP IMPACT", and notes, inside "Deep Impact Medium Resolution Instrument Visible CCD")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what Deep Impact is. Its entity class, Mission, is written (FROM_MISSION "Deep Impact", and PART_OF "Deep Impact" of the camera's CCD and of "cruise"), by rule 1's *Names in a public reference*.
  - The list: PDS4 context product urn:nasa:pds:context:investigation:mission.deep_impact, "Deep Impact", of type Mission, also titled "DEEP IMPACT" (https://pds.nasa.gov/data/pds4/context-pds4/investigation/mission.deep_impact_1.2.xml, checked on 2026-11-13). The craft's entry, urn:nasa:pds:context:instrument_host:spacecraft.dif, is "The Deep Impact Flyby (DIF) Spacecraft", not "Deep Impact".
- **Left out:** what "Deep Impact Medium Resolution Instrument Visible CCD" and "MRI" are (notes and title)
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record's own kind words, "Instrument" and "CCD", give the entity class, Instrument. The title's "MRI" abbreviates the "Medium Resolution Instrument" inside the notes' name (rule 23: "what you know about the words (e.g. what an abbreviation stands for"), so the record's dataset ACQUIRED_BY_INSTRUMENT "Medium Resolution Instrument", in the wording that spells it out, and "Deep Impact Medium Resolution Instrument Visible CCD" PART_OF "Medium Resolution Instrument" (rule 2, *A fact inside a name*), as "OSIRIS Narrow Angle Camera" PART_OF "OSIRIS" in the record "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0".
  - The list: PDS4 context product urn:nasa:pds:context:instrument:dif.mri, "The Medium Resolution Instrument (MRI) for Deep Impact", also titled "DEEP IMPACT MEDIUM RESOLUTION INSTRUMENT - VISIBLE CCD" (https://pds.nasa.gov/data/pds4/context-pds4/instrument/dif.mri_1.2.xml, checked on 2026-11-13). The list gives the entity class only (rule 1), so its reading of the CCD's name as the whole instrument is not used.
- **Left out:** what "9P/Tempel 1" is (title, "9P/TEMPEL", and notes, "comet 9P/Tempel 1")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record's type word "comet" says what kind of thing 9P/Tempel 1 is. Its entity class, CelestialBody, is written (HAS_TARGET "9P/Tempel 1", of the record's dataset and of "raw test images").
  - The reference: PDS4 context product urn:nasa:pds:context:target:comet.9p_tempel_1, "9P/Tempel 1", of type Comet (https://pds.nasa.gov/data/pds4/context-pds4/target/comet.9p_tempel_1_1.1.xml, checked on 2026-11-13).

## "ROSETTA-ORBITER 67P ROSINA 2 EXT2 V2.0" (pool position 56, id 8e66de36-8623-4280-a913-02f03a930a91)

A held-out record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. 8 items, none that may matter.

- **Left out:** what "COPS", "DFMS" and "RTOF" stand for (notes, "the COPS, DFMS and RTOF ROSINA sensors")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for"
  - Their entity class, Instrument, is the record's own type word "sensors". "sensor" stays in each instance, "COPS ROSINA sensor" and the others, since "COPS ROSINA" is not a name (rule 23 of *Writing a classed triple*, *Type words*), as in "GRaND plus Z boron loaded sensor" in the record "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0".
- **Left out:** "PDS" (notes, "Some missing DFMS PDS files were added")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for"
- **Left out:** "Some" (notes, "Some missing DFMS PDS files were added")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds gives no ground truth triple, and is taken out of the instance"
- **Left out:** "mission" and "comet" (notes, "the Rosetta mission at the comet 67P/CG")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the thing,"
  - My ground truth triples have the mission "Rosetta" and the target "67P/CG".
- **Left out:** "2" and "EXT2" (title) as facts of their own
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words."
  - The notes state them in the wordings that say more: "CODMAC level 2" (HAS_PROCESSING_LEVEL), as in the record "ROSETTA-ORBITER 67P/CAL ALICE 2 ESC1 V1.0", and "Extension phase 2" (HAS_MISSION_PHASE), which spells out "EXT" (rule 23).
- **Left out:** what "ROSETTA-ORBITER" is (title)
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what ROSETTA-ORBITER is. Its entity class, Platform, is written (FROM_PLATFORM "ROSETTA-ORBITER"), by rule 1's *Names in a public reference*.
  - The list: PDS4 context product urn:esa:psa:context:instrument_host:spacecraft.ro, "The Rosetta Orbiter Spacecraft", of type Spacecraft, also titled "ROSETTA-ORBITER" (https://pds.nasa.gov/data/pds4/context-pds4/instrument_host/spacecraft.ro_1.1.xml, checked on 2026-11-13).
- **Left out:** what "ROSINA" stands for (title and notes)
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what ROSINA is. Its entity class, Instrument, is written (ACQUIRED_BY_INSTRUMENT "ROSINA", and the three sensors PART_OF "ROSINA", by rule 2's *A fact inside a name*), by rule 1's *Names in a public reference*.
  - The list: PDS4 context product urn:esa:psa:context:instrument:ro.rosina, "The Rosetta Orbital Spectrometer for Ion and Neutral Analysis (ROSINA)" (https://pds.nasa.gov/data/pds4/context-pds4/instrument/ro.rosina_1.2.xml, checked on 2026-11-13).
- **Left out:** what "67P/CG" is (title, "67P", and notes, "the comet 67P/CG")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record's type word "comet" says what kind of thing 67P/CG is. Its entity class, CelestialBody, is written (HAS_TARGET "67P/CG"). "67P/CG" stays whole, since "CG" is never named alone (rule 22 of *Writing a classed triple*, *Lists joined by "/" or "+"*).
  - The reference: Wikidata, 67P/Churyumov–Gerasimenko (Q844672), whose other names include "67P" and "67P/C-G", an instance of "Jupiter-family comet" (https://www.wikidata.org/wiki/Q844672, checked on 2026-11-13).

## "VG1 SAT PWS EDITED SPECTRUM ANALYZER 4.0SEC V1.0" (pool position 59, id ef9ab3db-bef3-490f-8e24-0394345c39b6)

A held-out record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. 15 items, 8 that may matter.

- **Left out:** "SAT" (title)
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for"
  - **May matter because:** my reading, not checked: the PDS target code for Saturn, as "J/S/SS" in the record "VG1 J/S/SS PWS EDITED SPECTRUM ANALYZER FULL RES V1.0", while the notes say the data were obtained near "the Jovian magnetosphere"; if so, the title and the notes disagree.
  - **Question:** Q6 (b).
- **Left out:** "Jovian" as Jupiter (notes, "in the vicinity of the Jovian magnetosphere")
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names."
  - "Jovian" is an adjective and names no body, as "German" in the record "SOLVE I Ground Site Data". The area is written: HAS_SPATIAL_COVERAGE "vicinity of the Jovian magnetosphere"; "vicinity" stays, since the record does not say the data were obtained inside the magnetosphere (rule 11 of *Writing a classed triple*).
  - **May matter because:** a search by target would need Jupiter.
- **Left out:** "EDITED", "SPECTRUM ANALYZER" and "4.0SEC" (title) as facts of their own
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words."
  - The notes state them: "edited, wave electric field intensities" (HAS_MEASUREMENTS_OF), the "Voyager 1 Plasma Wave Receiver spectrum analyzer" (ACQUIRED_BY_INSTRUMENT) and "4-second" (HAS_TEMPORAL_RESOLUTION, the wording that spells out "SEC", rule 23).
- **Left out:** "edited" as a method (notes, "4-second edited, wave electric field intensities" and "Data are edited")
  - **Rule:** Writing a classed triple, rule 24: "A verb or participle that says only that something was done to the data ("corrected", "calibrated", "detrended", "binned", "mapped", "edited", "convert", "weighted") names no method"
  - It stays in the instance, as written: HAS_MEASUREMENTS_OF "edited, wave electric field intensities". The record does not say what was edited out, so no CLEANED_OF triple is written, unlike the record "VG1 J/S/SS PWS EDITED SPECTRUM ANALYZER FULL RES V1.0".
- **Left out:** "but not calibrated" (notes, "Data are edited but not calibrated.")
  - **Rule:** What counts as a fact, rule 6: "A ground truth triple can't say "not", and a negated fact is not rewritten into a fact the record doesn't state."
  - **May matter because:** it says that the values are not calibrated.
- **Left out:** "center" (notes, "channels whose center frequencies range from 10 Hertz to 56.2 kiloHertz")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds gives no ground truth triple, and is taken out of the instance"
  - HAS_FREQUENCY_RANGE "from 10 Hertz to 56.2 kiloHertz" is written for the spectrum analyzer. The range is that of the channels' center frequencies, and rule 11 of *Writing a classed triple* would keep "center" in what the predicate says, which HAS_FREQUENCY_RANGE ("its frequencies lie in this range") does not say.
  - **May matter because:** the channels reach somewhat beyond the range of their centers.
- **Left out:** "logarithmically spaced in frequency, four channels per decade" (notes)
  - **Rule:** What counts as a fact, rule 9: "An amount or a count per member gives no ground truth triple, unless the predicate itself says "each" (HAS_GRANULE_DURATION, HAS_SPATIAL_RESOLUTION)."
  - "four channels per decade" is a count for each decade of frequency, and the spacing names no value.
  - **May matter because:** it says how the channels are placed across the range.
- **Left out:** "For each 4-second interval" and "(16 channels)" as counts of their own (notes)
  - **Rule:** What counts as a fact, rule 9: "An amount or a count per member gives no ground truth triple, unless the predicate itself says "each" (HAS_GRANULE_DURATION, HAS_SPATIAL_RESOLUTION)."
  - The interval is written as the dataset's temporal resolution ("4-second"), and the 16 channels as the analyzer's (HAS_NUMBER_OF "16 spectrum analyzer channels").
- **Left out:** "a field strength is determined" (notes)
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words."
  - HAS_MEASUREMENTS_OF "edited, wave electric field intensities" states it.
- **Left out:** "During data gaps where complete 4-second spectra are missing, no entries exist in the file, that is, the gaps are not zero-filled or tagged in any other way." (notes)
  - **Rule:** What counts as a fact, rule 6: "A ground truth triple can't say "not", and a negated fact is not rewritten into a fact the record doesn't state."
  - **May matter because:** it says that a missing scan leaves no line in the file.
- **Left out:** "When one or more channels are missing within a scan, the missing measurements are zero-filled." (notes)
  - **Rule:** Writing a classed triple, rule 24: "A verb or participle that says only that something was done to the data ("corrected", "calibrated", "detrended", "binned", "mapped", "edited", "convert", "weighted") names no method"
  - "zero-filled" says what was done to the values and names no method.
  - **May matter because:** a zero in the data may stand for a missing measurement.
- **Left out:** "can be plotted in raw form for event searches and simple trend analysis" (notes)
  - **Rule:** What counts as a fact, rule 9: "What data have been used for, or can be used for, is a fact of the work that used them, not of the data: when the record doesn't name that work, it gives no ground truth triple."
  - "can be plotted" is also a possibility, not a statement (rule 7). The reason the sentence gives is written: ROUGHLY_PROPORTIONAL_TO "log of the electric field strength".
- **Left out:** "the use of these is described below" (notes)
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names."
  - The record's text has nothing below this sentence.
- **Left out:** what "PWS" is (title)
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what PWS is. Its entity class, Instrument, is written (ACQUIRED_BY_INSTRUMENT "PWS"), by rule 1's *Names in a public reference*. The reference gives the entity class only, and "PWS" does not abbreviate the notes' "Plasma Wave Receiver" (rule 23), so the two are written as two instances.
  - The list: PDS4 context product urn:nasa:pds:context:instrument:vg1.pws, "Plasma Wave Receiver for VG1", whose earlier identifier is urn:nasa:pds:context:instrument:pws.vg1: "PWS" is its instrument id, as "MRS" is in the record "MARS EXPRESS MARS MRS 1/2/3 EXTENDED MISSION 8 4193 V1.0" (https://pds.nasa.gov/data/pds4/context-pds4/instrument/vg1.pws_1.2.xml, checked on 2026-11-13).
  - **May matter because:** by the list, "PWS" and the "Plasma Wave Receiver" are one instrument, which the ground truth then names twice.
- **Left out:** what "Voyager 1" is (title, "VG1", and notes, "the Voyager 1 Plasma Wave Receiver spectrum analyzer")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what Voyager 1 is. Its entity class, Platform, is written (FROM_PLATFORM "Voyager 1", and "Voyager 1 Plasma Wave Receiver spectrum analyzer" ABOARD "Voyager 1"), by rule 1's *Names in a public reference*.
  - The reference: PDS4 context product urn:nasa:pds:context:instrument_host:spacecraft.vg1, "VOYAGER 1", of type Spacecraft, with the host id "VG1" (https://pds.nasa.gov/data/pds4/context-pds4/instrument_host/spacecraft.vg1_1.5.xml, checked on 2026-11-13).

## "CALIPSO Lidar Level 2 Vertical Feature Mask (VFM), V5-00" (pool position 62, id 9e49a827-733f-4a15-89e1-5f609f9a6b6e)

A held-out record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. 12 items, 3 that may matter.

- **Left out:** "Lidar" (title) and "CALIPSO Lidar" (notes, "the Cloud-Aerosol Lidar and Infrared Pathfinder Satellite Observation (CALIPSO) Lidar Level 2 Vertical Feature Mask (VFM) data product") as facts of their own
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words."
  - They name the instrument the notes spell out, "Cloud-Aerosol Lidar with Orthogonal Polarization (CALIOP)", the one lidar the record names (rule 23: the wording that says more). Its ABOARD triple is written from "The CALIPSO satellite carried three remote sensing instruments".
- **Left out:** "satellite", "instrument", "constellation" and "data product" (notes)
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the thing,"
- **Left out:** "French" as a country (notes, "the French Space Agency, CNES")
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names."
  - "French" is an adjective and names no country, as "German" in the record "SOLVE I Ground Site Data". The words stay in the Role, "CNES" SERVES_AS "French Space Agency", as "Argentina's space agency" in the record "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005". "CNES" after the comma fails the abbreviation test of rule 20 of *Writing a classed triple* (its first letter does not start "French"), and the words are read as the agency's role and its name, not as two partners.
- **Left out:** "many" (notes, "to study the many roles played by clouds and aerosols")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds gives no ground truth triple, and is taken out of the instance"
- **Left out:** "for coincident Earth observations" and "from launch until September 13, 2018" (notes, "It flew in the international A-Train constellation for coincident Earth observations from launch until September 13, 2018")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds gives no ground truth triple, and is taken out of the instance"
  - Both say how the fact "flew in the international A-Train" held, what for and when, so their subject would be that fact, not a thing the record names. FLIES_IN "international A-Train" is written.
  - **May matter because:** they say why CALIPSO flew in the A-Train, and when it left it.
- **Left out:** "to resume formation flying with CloudSat as part of the “C-Train”" (notes)
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds gives no ground truth triple, and is taken out of the instance"
  - It says what the lowering of the orbit was for, so its subject would be that fact. CloudSat is a platform in the GCMD Platforms keywords (version 25.2) (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/platforms?format=csv, checked on 2026-11-13), and the C-Train a former satellite formation in Wikidata (Q92454159, https://www.wikidata.org/wiki/Q92454159, checked on 2026-11-13); neither gives a ground truth triple here.
  - **May matter because:** it names the craft and the formation CALIPSO was moved to join.
- **Left out:** "By mutual agreement between NASA and CNES" (notes, "By mutual agreement between NASA and CNES, the CALIPSO science mission concluded on August 1, 2023.")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds gives no ground truth triple, and is taken out of the instance"
  - It says how the mission came to an end; its end is written (ENDED_ON "August 1, 2023").
  - **May matter because:** it says that both partners decided the end.
- **Left out:** "above the Earth" (notes, "lowering its orbit from 705 km to 688 km (428 miles)above the Earth")
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words."
  - HAS_TARGET "Earth" is written from "Earth’s climate and weather".
- **Left out:** "CALIPSO" in "the CALIPSO science mission" as a fact of its own (notes)
  - **Rule:** What counts as a fact, rule 2: "When the naming states more than one predicate, or none, the name's words give no ground truth triple" (*A fact inside a name*)
  - A craft's name inside a mission's name states no predicate of the ground truth schema: rule 2 gives PART_OF for a Mission named in the name of one of its parts, not for the reverse. "CALIPSO science mission" is therefore linked to no other ground truth triple, and its end is still written (rule 21 of *Writing a classed triple*). "science mission" stays in the instance, since "CALIPSO" alone names another thing, the craft (rule 23: "The type word stays in the instance only when the words left once it is taken out aren't a name, or are the name of another thing").
- **Left out:** what "NASA" is (notes, "a partnership between NASA" and "By mutual agreement between NASA and CNES")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what NASA is. Its entity class, Organization, is written (HAS_PARTNER "NASA"), by rule 1's *Names in a public reference*.
  - The reference: GCMD Providers keywords (version 25.2), the level "NASA" under "GOVERNMENT AGENCIES-U.S. FEDERAL AGENCIES", which holds NASA's centers and offices (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/providers?format=csv, checked on 2026-11-13).
- **Left out:** what "CNES" stands for (notes, "the French Space Agency, CNES")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record's words "the French Space Agency" say what kind of thing CNES is. Its entity class, Organization, is written (HAS_PARTNER "CNES", and "CNES" SERVES_AS "French Space Agency").
  - The reference: GCMD Providers keywords (version 25.2), "FR/CNES", "Centre National d'Etudes Spatiales, France" (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/providers?format=csv, checked on 2026-11-13).
- **Left out:** what "Earth" is (notes, "Earth’s climate and weather")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what Earth is. Its entity class, CelestialBody, is written (HAS_TARGET "Earth"), by rule 1's *Names in a public reference*.
  - The reference: PDS4 context product urn:nasa:pds:context:target:planet.earth, "Earth", of type Planet (https://pds.nasa.gov/data/pds4/context-pds4/target/planet.earth_1.1.xml, checked on 2026-11-13).

## "ROSETTA-ORBITER 67P NAVCAM 2 COMET ESCORT 1 MTP010 V1.1" (pool position 65, id 0ea5f919-f703-4edd-811d-cf4852a8d8a9)

A held-out record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. 11 items, 3 that may matter.

- **Left out:** "2" (title, "NAVCAM 2")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for"; a bare number is not "L" or "Level" followed by a number.
  - **Question:** Q6 (b).
- **Left out:** "MTP010" (title)
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for"
  - **May matter because:** it tells this dataset from its siblings, as "MTP020" does in the record "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0" (its item; not checked for this record).
  - **Question:** Q6 (b).
- **Left out:** "RAW" (notes, "ROSETTA NAVCAM RAW DATA")
  - **Rule:** Writing a classed triple, rule 19: "A qualifier that only says how far the data are processed ("raw", "edited", "calibrated", "derived") is not a processing level, and stays in the instance, as written."
  - As in the record "ROSETTA-ORBITER 67P NAVCAM 2 COMET ESCORT 3 MTP019 V1.0": the words name the record's dataset itself, which is written as its title, so the instance the word would stay in is never written.
  - **May matter because:** it says that the images are not processed.
- **Left out:** "Escort Phase" (notes, "RAW DATA of the Escort Phase") as the phase's wording
  - **Rule:** Writing a classed triple, rule 23: "When a record names the same thing more than once, in different words, use the wording the first of the four tests below picks, in every ground truth triple"
  - The title's "COMET ESCORT 1" is more precise, since it holds the phase's number, so test 1 picks it: HAS_MISSION_PHASE "COMET ESCORT 1". "COMET" stays in the instance and gives no HAS_TARGET triple: it names no particular comet, and the record never calls "67P/CG" a comet (rule 9), as in the record "ROSETTA-ORBITER 67P NAVCAM 2 COMET ESCORT 3 MTP019 V1.0".
- **Left out:** "when at the vicinity of" (notes, "when at the vicinity of target 67P/CG")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds gives no ground truth triple, and is taken out of the instance"
  - HAS_TARGET "67P/CG" is written; the words say where the craft was when the data were taken.
- **Left out:** "the Browse images" and "the FITS version" as what the record's dataset holds (notes, "It includes updates of the Browse images, adding of the FITS version")
  - **Rule:** What counts as a fact, rule 1: "Only what the record states."
  - That the data set holds browse images and a FITS version follows from the changes the record lists ("V1.1" HAS_CHANGE) but is not stated, as "during the planetary encounters" in the record "VG1 J/S/SS PWS EDITED SPECTRUM ANALYZER FULL RES V1.0". "FITS" is also an unexplained code (rule 1).
  - **May matter because:** a search by file format would need FITS.
- **Left out:** "resolve other minor outstanding errata" (notes)
  - **Rule:** Writing a classed triple, rule 22: "An item that names no specific thing ("his team") gives no ground truth triple"
  - The item names no particular erratum; "minor" is a judgement (rule 5).
- **Left out:** what "ROSETTA-ORBITER" is (title)
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what ROSETTA-ORBITER is. Its entity class, Platform, is written (FROM_PLATFORM "ROSETTA-ORBITER"), by rule 1's *Names in a public reference*.
  - The list: PDS4 context product urn:esa:psa:context:instrument_host:spacecraft.ro, "The Rosetta Orbiter Spacecraft", of type Spacecraft, also titled "ROSETTA-ORBITER" (https://pds.nasa.gov/data/pds4/context-pds4/instrument_host/spacecraft.ro_1.1.xml, checked on 2026-11-13).
- **Left out:** what "ROSETTA" is (notes, "ROSETTA NAVCAM RAW DATA")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what ROSETTA is. Its entity class, Mission, is written (FROM_MISSION "ROSETTA", and "NAVCAM" PART_OF "ROSETTA", by rule 2's *A fact inside a name*), by rule 1's *Names in a public reference*.
  - The list: PDS4 context product urn:esa:psa:context:investigation:mission.international_rosetta_mission, "The International Rosetta Mission", of type Mission, also titled "ROSETTA" (https://pds.nasa.gov/data/pds4/context-pds4/investigation/mission.international_rosetta_mission_1.1.xml, checked on 2026-11-13). The craft's entry is titled "ROSETTA-ORBITER", not "ROSETTA".
- **Left out:** what "NAVCAM" stands for (title and notes)
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what NAVCAM is. Its entity class, Instrument, is written (ACQUIRED_BY_INSTRUMENT "NAVCAM", and "NAVCAM" PART_OF "ROSETTA"), by rule 1's *Names in a public reference*.
  - The list: PDS4 context product urn:esa:psa:context:instrument:ro.navcam, "The Navigation Camera (NavCam) for the Rosetta Orbiter" (https://pds.nasa.gov/data/pds4/context-pds4/instrument/ro.navcam_1.2.xml, checked on 2026-11-13); "NAVCAM" and "NavCam" differ only in capitals (rule 23 of *Writing a classed triple*).
- **Left out:** what "67P/CG" is (title, "67P", and notes, "target 67P/CG")
  - **Rule:** What counts as a fact, rule 1: "never write down what an unexplained code or abbreviation stands for, its entity class included". The record never says what 67P/CG is. Its entity class, CelestialBody, is written (HAS_TARGET "67P/CG"), by rule 1's *Names in a public reference*. "67P/CG" stays whole, since "CG" is never named alone (rule 22 of *Writing a classed triple*, *Lists joined by "/" or "+"*), and it says more than the title's "67P" (rule 23).
  - The reference: Wikidata, 67P/Churyumov–Gerasimenko (Q844672), whose other names include "67P" and "67P/C-G", an instance of "Jupiter-family comet" (https://www.wikidata.org/wiki/Q844672, checked on 2026-11-13). The record's "67P/CG" differs from "67P/C-G" only by a hyphen (rule 23). The PDS4 context product urn:nasa:pds:context:target:comet.67p_churyumov-gerasimenko names the comet "67P/Churyumov-Gerasimenko" only, a wording this record does not use.
