# Left out on purpose

Statements of a [record](../docs/terminology.md#1-records-and-their-text)'s [text](../docs/terminology.md#1-records-and-their-text) that have no [ground truth triple](../docs/terminology.md#4-ground-truth-and-samples), because I decided so or a rule of the [annotation guidelines](guidelines.md) says so. It is the one place where I keep them, so that what the [ground truth](../docs/terminology.md#4-ground-truth-and-samples) leaves out is not lost: some of these words carry information I may want back once an expert answers a question, or once the schema can say it. Terms: [docs/terminology.md](../docs/terminology.md).

One section per record I have annotated, in [pool](../docs/terminology.md#4-ground-truth-and-samples) order. Each item has the exact words (quoted from the record's text, as in `outputs/intermediate_results/020_clean/records.jsonl`), the rule that excluded them (quoted from `guidelines.md`), a *May matter because* line when the words carry information worth keeping, and the question in `questions_for_experts.md` that asks about it, if there is one. Left out here is not the same as wrong: a statement written in other words, or as part of a bigger ground truth triple, is not listed. Nor is a record's "is a data set" (the [describes class](../docs/terminology.md#2-triples) says it). Nor are all the type words that rule 23 of *Writing a classed triple* leaves out ("Take out a type word that only describes the thing,"): the items below name some of them, not every one. When I annotate a record, I add its section; when an expert's answer brings a statement back as a ground truth triple, I delete its item. An item that waits on an expert's answer (its rule is rule 2's "or it waits on an expert's answer") has its would-be ground truth triple in `annotations/pending_triples.csv`, so that step 070 doesn't count an extracted triple that matches it as wrong, or a note "No clear would-be triple:" that says why it has none.

## "NASA Standards and and Technical Assistance Resource Tool" (pool position 0, id 3122be4c-b9d0-4cc9-b6d3-9b96c6e743da)

3 items, none that may matter.

- **Left out:** "is a Web tool" (notes)
  - **Rule:** What counts as a fact, rule 4: "A sentence that says what type of entity an instance refers to ("Kestrel is an imager") gives no ground truth triple: the instance's entity class says it"
  - A Web tool is what the thing is; its entity class WebTool already says it.
- **Left out:** "great" (notes, "access great NASA technical information")
  - **Rule:** What counts as a fact, rule 5: "Take out words such as "great"."
  - My ground truth triple of the purpose is written without it.
- **Left out:** what "NASA" is (title, and notes, "NASA developed standards and handbooks" and "The NASA Technical Standards Program")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what NASA is. Its entity class, Organization, is written ("NASA developed standards" and "NASA developed handbooks" DEVELOPED_BY_PARTY "NASA", and "NASA Technical Standards Program" PART_OF "NASA"), by rule 1's *A name the record does not explain*.
  - The reference: GCMD Providers keywords (version 25.2), the level "NASA" under "GOVERNMENT AGENCIES-U.S. FEDERAL AGENCIES", which holds NASA's centers and offices (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/providers?format=csv, checked on 2026-11-12).

## "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (pool position 1, id cfd6ec3f-1e63-4a77-bc3f-007d45f7e2fc)

6 items, 3 that may matter.

- **Left out:** "1/2/3" (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"
  - **May matter because:** checked on 2026-10-30, the record does not say so but the data set's own catalog does: "1/2/3 (Data set contains raw, edited and calibrated data)", CODMAC processing levels 1, 2 and 3 (the data set's DATASET.CAT, https://archives.esac.esa.int/psa/ftp/INTERNATIONAL-ROSETTA-MISSION/RSI/RO-C-RSI-1-2-3-ESC4-1149-V1.0/CATALOG/; the PDS3 Standards Reference, chapter 6, names the CODMAC level in this slot, https://pds.nasa.gov/datastandards/pds3/standards/sr/Chapter06.pdf). Still left out: the record's text does not explain it (rule 1). A search by level would find it.
  - **Question:** Q6 (b).
- **Left out:** "1149" (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"
  - **May matter because:** checked on 2026-10-30: a running measurement number, "incremented measurement by measurement, independent what kind of measurement was conducted" (the data set's catalog, https://archives.esac.esa.int/psa/ftp/INTERNATIONAL-ROSETTA-MISSION/RSI/RO-C-RSI-1-2-3-ESC4-1149-V1.0/CATALOG/); it tells this dataset from its siblings and states no fact about the data.
  - **Question:** Q6 (b).
- **Left out:** what "RSI" stands for (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included"
  - **May matter because:** checked on 2026-10-30: the Planetary Data System files it as INSTRUMENT_ID = RSI, INSTRUMENT_TYPE = RADIO SCIENCE, the "ROSETTA RADIO SCIENCE INVESTIGATION" (the data set's catalog files, https://archives.esac.esa.int/psa/ftp/INTERNATIONAL-ROSETTA-MISSION/RSI/RO-C-RSI-1-2-3-ESC4-1149-V1.0/CATALOG/). Still left out: the record's text does not say what "RSI" stands for, so its entity class would rest on outside knowledge (rule 1). Decided on 2026-10-31 (audit finding G-2); until then, ACQUIRED_BY_INSTRUMENT "RSI" (Instrument) was a ground truth triple. Reversed later on 2026-10-31: the triple is written again, by rule 1's *A name the record does not explain*; what "RSI" stands for stays left out.
  - The list: PDS4 context product urn:esa:psa:context:instrument:ro.rsi, "The Radio Science Investigations (RSI) for the Rosetta Orbiter", an instrument of the instrument host Rosetta Orbiter (https://pds.nasa.gov/data/pds4/context-pds4/instrument/, checked on 2026-10-31).
  - **Question:** Q10 (its part on RSI, settled from this source: see Q10's My notes).
- **Left out:** "comet" (notes, "at the comet 67P")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the entity,"
  - My ground truth triple has the target "67P".
- **Left out:** what "ROSETTA-ORBITER" is (title; the notes name only "Rosetta", in "a Rosetta Radio Science data set")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what ROSETTA-ORBITER is. Its entity class, Platform, is written (FROM_PLATFORM "ROSETTA-ORBITER"), by rule 1's *A name the record does not explain*.
  - The list: PDS4 context product urn:esa:psa:context:instrument_host:spacecraft.ro, "The Rosetta Orbiter Spacecraft", of type Spacecraft (https://pds.nasa.gov/data/pds4/context-pds4/instrument_host/spacecraft.ro_1.1.xml, checked on 2026-11-12).
- **Left out:** what "Rosetta" is (notes, "a Rosetta Radio Science data set")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what Rosetta is. Its entity class, Mission, is written (FROM_MISSION "Rosetta"), by rule 1's *A name the record does not explain*.
  - The reference: PDS4 context product urn:esa:psa:context:investigation:mission.international_rosetta_mission, "The International Rosetta Mission", also titled "ROSETTA", of type Mission (https://pds.nasa.gov/data/pds4/context-pds4/investigation/mission.international_rosetta_mission_1.1.xml, checked on 2026-11-12).

## "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" (pool position 2, id 6cfafd07-40f1-46da-9d92-36c2bb319f0b)

2 items, none that may matter. The record has no list of other temporal resolutions or spatial resolutions of its product ("daily" is its own, in "provides daily snow cover"), so nothing of a product family is left out here.

- **Left out:** "satellite" (notes, "the Aqua satellite")
  - **Rule:** Writing a classed triple, rule 23: "write "Halden", not "Halden satellite", since its entity class already says what it is"
- **Left out:** "Each data granule contains" (notes), that the data come in granules
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words."
  - My ground truth triple HAS_GRANULE_DURATION "5 minutes" already says each granule covers 5 minutes, which only makes sense if the data come in granules.

## "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005" (pool position 3, id 2705e0d1-95e7-4588-813b-ca91a6da94ff)

3 items, 1 that may matter.

- **Left out:** "collaboratively" (notes, "developed collaboratively between")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance: its subject would be that fact, not an entity the record names." "collaboratively" says only how NASA and CONAE developed the mission (together); the two developers are ground truth triples of their own (DEVELOPED_BY_PARTY: NASA and CONAE). Saying how a fact holds needs a fact about a fact, a qualifier kept with the ground truth triple it holds for (as Wikidata's statement qualifiers do), which is future work: docs/improvements.md, *Rule 19 can lose which fact a qualifier went with*, option 4 (recommended on 2026-10-27, decided on 2026-10-30). Decided on 2026-10-31; until then this item waited on the experts' answer to Q27 (rule 2 of *What counts as a fact*).
  - **May matter because:** it says how NASA and CONAE worked on the mission: together.
  - **Question:** Q27 (settled on 2026-10-31: see Q27's My notes).
- **Left out:** what "U.S." is (notes, "the U.S. National Aeronautics and Space Administration (NASA)")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what U.S. is. Its entity class, Country, is written (BASED_IN "U.S."), by rule 1's *A name the record does not explain*.
  - The reference: Wikidata, United States (Q30), also named "the U.S.", "country located primarily in North America", an instance of "country" and of "sovereign state" (https://www.wikidata.org/wiki/Q30, checked on 2026-11-13). Rule 1's official NASA lists (the GCMD Instruments, Platforms and Providers keywords, and the PDS4 context products) are not lists of countries, and they were not searched for it.
- **Left out:** what "Argentina" is (notes, "Argentina's space agency")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what Argentina is. Its entity class, Country, is written (BASED_IN "Argentina"), by rule 1's *A name the record does not explain*.
  - The reference: Wikidata, Argentina (Q414), "country in South America", an instance of "country" and of "sovereign state" (https://www.wikidata.org/wiki/Q414, checked on 2026-11-13). Rule 1's official NASA lists (the GCMD Instruments, Platforms and Providers keywords, and the PDS4 context products) are not lists of countries, and they were not searched for it.

## "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (pool position 4, id 03a09af3-081e-4db6-9e3b-ea7c0e3138bd)

The dense record: its notes describe a whole family of products (several temporal resolutions, two spatial resolutions, day and night, two kinds of temperature) and the title names the one this record is. 16 items, 9 that may matter. The product family as a whole is asked in Q24.

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
  - **Rule:** What counts as a fact, rule 7: ""May", "might", "possibly", and "is expected to" when it means "will probably" make a fact uncertain." (I read "can be present" as the same kind). My ground truth triple has the variable SST4 only, from the title's "SST MID-IR".
  - **May matter because:** if the files hold both, the dataset has two variables, not one.
  - **Question:** Q18.
- **Left out:** "binned" and "mapped" as methods (notes, "the L2 pixels are binned into an integerized sinusoidal area grid (ISEAG) and mapped into an equidistant cylindrical")
  - **Rule:** Writing a classed triple, rule 24: "A verb or participle that says only what was done to the data ("corrected", "calibrated", "detrended", "binned", "mapped", "edited", "convert", "weighted") names no method". The record names the grid and the projection but only says the pixels "are binned" and "mapped", so I wrote BINNED_INTO (renamed ON_GRID on 2026-10-31) and MAPPED_INTO and no PRODUCED_USING_ALGORITHM. Since 2026-11-12 the subject of the two ground truth triples is the record's dataset, whose values are on the grid and on the map (ON_GRID: "its values are given on the cells or points of this Grid"); until then it was "pixels", the input of the step.
  - **May matter because:** it is how the dataset was made, step by step.
  - **Question:** Q7.
- **Left out:** "NASA" (notes, "global NASA skin sea surface temperature (SST) products")
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words." By rule 19 of *Writing a classed triple* (*Whose fact it is*), "NASA" qualifies the products, which are the record's dataset, a standalone entity class, so its fact would be the record's dataset's: who made the products. The record states that fact more precisely in "The NASA MODIS L3 SST data products are generated by the NASA Ocean Biology Processing Group (OBPG)", my ground truth triple DEVELOPED_BY_PARTY "NASA Ocean Biology Processing Group (OBPG)", whose wording contains "NASA" as a whole word and says more (rule 23). Rule 21 does not leave it out: the record's dataset is one of these products. Decided on 2026-10-31; until then this item waited on the experts' answer to Q28 (a) (rule 2 of *What counts as a fact*).
  - **May matter because:** it says whose products these are: NASA's.
  - **Question:** Q28 (a) (settled on 2026-10-31: see Q28's My notes).
- **Left out:** "at a variety of spatial resolutions" (notes, "MODIS captures data in 36 spectral bands at a variety of spatial resolutions")
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names" The words name no value.
- **Left out:** "projection" (notes, "Platte Carre projection")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the entity,"
  - **Question:** Q15 (whether a coordinate system is a map projection); its part on "Platte Carre" was settled on 2026-10-26: it is the record's spelling of "Plate Carrée", the equidistant cylindrical projection on the equator (see Q15's My notes).
- **Left out:** "satellite" (notes, "the Aqua satellite")
  - **Rule:** Writing a classed triple, rule 23: "write "Halden", not "Halden satellite", since its entity class already says what it is"
- **Left out:** "which can be found at https://doi.org/10.5067/MODAM-8D4N4" (notes), the DOI of the previous v2014.1 datasets
  - **Rule:** Writing a classed triple, rule 21: "Leave out facts about other datasets, such as a variant of the record's dataset (the same data at another temporal resolution, spatial resolution, or version), or a product made from it." The DOI is the address of the older datasets, not of this one; the ground truth triple has only "R2019.0" SUPERSEDES "v2014.1" (until 2026-11-12 its subject instance was "V2019.0").
  - **May matter because:** it is where the superseded release is.
  - **Question:** Q19, and Q24 (the releases of a product family).

- **Left out:** "his team" (notes, "Peter Minnett and his team at the Rosenstiel School of Marine and Atmospheric Science (RSMAS)  are responsible for sea surface temperature algorithm development, error statistics and quality flagging")
  - **Rule:** Writing a classed triple, rule 22: "A list: one ground truth triple per item. Apply rule 19 (qualifiers) first. Then write one ground truth triple per item of the list, in which that item alone takes the list's place (the subject or the object)," which splits the subject into "Peter Minnett" and "his team"; then What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names." "his team" names no team, so only "Peter Minnett" keeps the four ground truth triples (decided on 2026-10-30).
  - **May matter because:** the record gives the responsibilities and the affiliation to the team as well as to Peter Minnett; the team's share is lost.
- **Left out:** "NSST" (notes, "The first is a skin SST produced for both day and night (NSST) observations"), as another wording of "skin SST"
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for" "(NSST)" follows "night", not "skin SST", so it is not a name with its abbreviation in parentheses (Writing a classed triple, rule 20: "A name with its own abbreviation, another name or code of its own, or a short note in parentheses is one instance, as written."), and the record does not say what NSST names. The ground truth triples use "skin SST" (decided on 2026-10-30, audit finding G7).
  - **May matter because:** NSST may be the product's own name; other records of the family may use it. Checked on 2026-10-30: NSST names NASA's nighttime long-wave (11 µm) SST product, "Aqua MODIS Level-3 Global Mapped 11µm Nighttime Sea Surface Temperature (NSST) Data, version R2019.0" (https://data.nasa.gov/dataset/aqua-modis-level-3-global-mapped-11m-nighttime-sea-surface-temperature-nsst-data-version-r), so it is not another wording of this record's day-and-night "skin SST"; it stays left out (rule 1 of *What counts as a fact*: the record doesn't explain it).
  - **Question:** Q18, (d). Its meaning may later come from the model, checked against a source: docs/improvements.md, *Knowledge enrichment from the model, verified and labelled* (080).
- **Left out:** what "NASA" is (notes, "Aqua was launched by NASA" and "the NASA Ocean Biology Processing Group (OBPG)")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what NASA is. Its entity class, Organization, is written ("Aqua" LAUNCHED_BY_PARTY "NASA", and "NASA Ocean Biology Processing Group (OBPG)" PART_OF "NASA"), by rule 1's *A name the record does not explain*.
  - The reference: GCMD Providers keywords (version 25.2), the level "NASA" under "GOVERNMENT AGENCIES-U.S. FEDERAL AGENCIES", which holds NASA's centers and offices (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/providers?format=csv, checked on 2026-11-12).
- **Left out:** what "JPL" stands for (notes, "JPL acquires MODIS ocean L3 SST data from the OBPG and is the official Physical Oceanography Data Archive (PO.DAAC) for SST")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what JPL is. Its entity class, Organization, is written ("JPL" OBTAINS_DATA_FROM "NASA Ocean Biology Processing Group (OBPG)", and "JPL" SERVES_AS "official Physical Oceanography Data Archive (PO.DAAC) for SST"), by rule 1's *A name the record does not explain*.
  - The reference: GCMD Providers keywords (version 25.2), "NASA/JPL", "Jet Propulsion Laboratory, NASA" (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/providers?format=csv, checked on 2026-11-12).
- **Left out:** what "Earth" is (notes, "Earth Observation Satellites (EOS)" and the purposes of Aqua)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what Earth is. Its entity class, CelestialBody, is written (HAS_TARGET "Earth"), by rule 1's *A name the record does not explain*.
  - The reference: PDS4 context product urn:nasa:pds:context:target:planet.earth, "Earth", of type Planet (https://pds.nasa.gov/data/pds4/context-pds4/target/planet.earth_1.1.xml, checked on 2026-11-12).
- **Left out:** that Aqua is one of the Earth Observation Satellites (EOS) (notes, "formation flying in the A-train with other Earth Observation Satellites (EOS)")
  - **Rule:** What counts as a fact, rule 4: "A sentence that says what type of entity an instance refers to ("Kestrel is an imager") gives no ground truth triple: the instance's entity class says it". "other Earth Observation Satellites (EOS)" says that Aqua is one of them, which is what kind of thing Aqua is. The record does not say that the satellites fly as a formation named EOS, so "Aqua" FLIES_IN "Earth Observation Satellites (EOS)" was deleted on 2026-11-13, after the last audits found it. Whether such a membership gives a ground truth triple is an open case.

## "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0" (pool position 5, id 99dff022-24ac-48cb-bc83-09fec8b90ad7)

4 items, 1 that may matter.

- **Left out:** "detrended" as a method (notes, "The nominal fast neutron count rates were detrended using the GRaND epithermal neutron map")
  - **Rule:** Writing a classed triple, rule 24: "A verb or participle that says only what was done to the data ("corrected", "calibrated", "detrended", "binned", "mapped", "edited", "convert", "weighted") names no method". The record says the rates "were detrended", only a verb; I wrote the two COMPUTED_FROM triples (the rates, the epithermal map) and no PRODUCED_USING_ALGORITHM.
  - **May matter because:** it is the method that made the residual map.
  - **Question:** Q7 (settled for now, not asked), Q12 (c) for the map as an input.
- **Left out:** what "DAWN" is (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what DAWN is. Its entity class, Platform, is written (FROM_PLATFORM "DAWN"), by rule 1's *A name the record does not explain*.
  - The list: PDS4 context product spacecraft.dawn, "The Dawn Spacecraft", of type Spacecraft (https://pds.nasa.gov/data/pds4/context-pds4/instrument_host/spacecraft.dawn_1.3.xml, checked on 2026-11-11).
- **Left out:** what "GRaND" stands for (title, "GRAND", and notes, "the GRaND plus Z boron loaded sensor" and "the GRaND epithermal neutron map")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what GRaND is. Its entity class, Instrument, is written (ACQUIRED_BY_INSTRUMENT "GRaND", twice, and "GRaND plus Z boron loaded sensor" PART_OF "GRaND"), by rule 1's *A name the record does not explain*.
  - The list: PDS4 context product urn:nasa:pds:context:instrument:dawn.grand, "The Gamma Ray and Neutron Detector (GRAND) for Dawn", an instrument of the instrument host spacecraft.dawn (https://pds.nasa.gov/data/pds4/context-pds4/instrument/dawn.grand_1.2.xml, checked on 2026-11-12).
- **Left out:** what "Vesta" is (title, "VESTA", and notes, "the average atomic mass on Vesta")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what Vesta is. Its entity class, CelestialBody, is written (HAS_TARGET "Vesta"), by rule 1's *A name the record does not explain*.
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
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for". "L2" is a processing level by a convention rule 1 names ("L" or "Level" followed by a number (a processing level)); the facts "G" may stand for are written from the notes' "gridded Level 2 product" (HAS_PROCESSING_LEVEL "Level 2", HAS_SPATIAL_REPRESENTATION "gridded"), and the record doesn't say what "G" stands for (decided on 2026-11-01, the review of the second opinion's facts).
- **Left out:** what "SIN" stands for (title, "SIN Grid")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for". The grid is written whole, ON_GRID "SIN Grid" (Writing a classed triple, rule 11: "A name stays whole: rules 19, 22 and 24 never split or shorten a name"), so no MAPPED_INTO "SIN" (decided on 2026-11-01, the review of the second opinion's facts; the same in the record at pool position 7).
- **Left out:** what "Terra" is (title, "MODIS/Terra+Aqua", and notes, "Combined Terra and Aqua")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what Terra is. Its entity class, Platform, is written (FROM_PLATFORM "Terra"), by rule 1's *A name the record does not explain*.
  - The list: GCMD Platforms keywords (version 25.2), "Terra", "Earth Observing System, Terra (AM-1)" (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/platforms?format=csv, checked on 2026-11-12).
- **Left out:** what "Aqua" is (title, "MODIS/Terra+Aqua", and notes, "Combined Terra and Aqua")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what Aqua is. Its entity class, Platform, is written (FROM_PLATFORM "Aqua"), by rule 1's *A name the record does not explain*.
  - The list: GCMD Platforms keywords (version 25.2), "Aqua", "Earth Observing System, Aqua" (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/platforms?format=csv, checked on 2026-11-12).

## "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" (pool position 7, id d5477563-0415-4e65-ab7c-d4bc9ed809e5)

17 items, 9 that may matter.

- **Left out:** what "MODIS" stands for (title, "MODIS/Terra", and notes, "Terra MODIS")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"
  - **May matter because:** its entity class, Instrument, is written (ACQUIRED_BY_INSTRUMENT "MODIS"), by rule 1's *A name the record does not explain*.
  - The list: GCMD Instruments keywords (version 25.1), "MODIS", "Moderate-Resolution Imaging Spectroradiometer"; the CMR record of MOD11A1 version 006 lists it under the platform Terra (checked on 2026-10-31).
- **Left out:** "in a 1,200 by 1,200 km grid" (notes)
  - **Rule:** What counts as a fact, rule 1: "Only what the record states. Never add what you know from elsewhere". The record says only that the data are "in a 1,200 by 1,200 km grid"; that this is one tile of the MODIS sinusoidal grid, the ground each file covers, comes from NASA LAADS, not from the record, and the ground truth schema has no predicate for the ground each file covers (HAS_GRANULE_DURATION is the time each file covers; HAS_SPATIAL_RESOLUTION, the ground each value covers). Decided on 2026-10-31; until then this item waited on the experts' answer to Q1 (c) (rule 2 of *What counts as a fact*). The grid itself is now the ground truth triple ON_GRID "SIN Grid".
  - **May matter because:** it is the size of one tile of the MODIS sinusoidal grid, which is how much ground each file covers. Checked on 2026-10-30: "Each tile has fixed Earth-locations covering an area of approximately 1200 x 1200 km (10 x 10 degrees at the equator)" (NASA LAADS, "What are the Product Spatial Formats?", https://landweb.modaps.eosdis.nasa.gov/help/prod_format).
  - **Question:** Q1 (c) (settled on 2026-10-31: see Q1's My notes).
- **Left out:** "per-pixel" (notes, "provides daily per-pixel Land Surface Temperature")
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words." The ground truth triple HAS_SPATIAL_RESOLUTION "1 kilometer (km)" already says how much ground each value covers.
- **Left out:** "(LST&E)" (notes, "Land Surface Temperature and Emissivity (LST&E)")
  - **Rule:** Writing a classed triple, rule 22: "A list that the record gives one abbreviation of its own is a name, and stays whole, only when the abbreviation stands for one entity; when it stands for several entities, it is a list, and the abbreviation belongs to no item." "LST&E" stands for two quantities, so the list splits and "(LST&E)" belongs to neither item (the test was written on 2026-10-31, third audit, findings R-4 and G-5; until then this item cited only "A list: one ground truth triple per item.").
- **Left out:** "https://doi.org/10.5067/MODIS/MOD11A1.061" (notes, the address in "[MOD11A1 Version 6.1](https://doi.org/10.5067/MODIS/MOD11A1.061)"), the DOI of Version 6.1
  - **Rule:** Writing a classed triple, rule 21: "Leave out facts about other datasets, such as a variant of the record's dataset (the same data at another temporal resolution, spatial resolution, or version), or a product made from it." The ground truth triple has only "Version 6.1" SUPERSEDES "Version 6".
  - **May matter because:** it is where the newer release is.
  - **Question:** Q19, and Q24 (the releases of a product family).
- **Left out:** "Above 30 degrees latitude, some pixels may have multiple observations where the criteria for clear-sky are met." (notes)
  - **Rule:** What counts as a fact, rule 7: ""May", "might", "possibly", and "is expected to" when it means "will probably" make a fact uncertain."
  - **May matter because:** it says where several observations go into one value.
- **Left out:** "When this occurs, the pixel value is a result of the average of all qualifying observations." (notes), the averaging as a method
  - **Rule:** What counts as a fact, rule 7: ""May", "might", "possibly", and "is expected to" when it means "will probably" make a fact uncertain.". The averaging happens only "When this occurs", that is, where pixels "may have multiple observations", so I wrote no PRODUCED_USING_ALGORITHM "average".
  - **May matter because:** it is how a value is made from several observations.
  - **Question:** Q7.
- **Left out:** "surface temperature bands" and "pixel temperature value" as things of their own (notes, "the daytime and nighttime surface temperature bands" and "The pixel temperature value is derived from")
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words." "surface temperature" is the "Land Surface Temperature" already written (rule 23: the wording that says more); "bands" is a type word (rule 23: "Take out a type word that only describes the thing,"). "daytime" and "nighttime" are ground truth triples of their own (OBSERVED_AT_TIME_OF_DAY, rule 19 of *Writing a classed triple*). "pixel temperature value" is the record's dataset's own values: their input is written for the dataset (COMPUTED_FROM "MOD11_L2", rule 23, *The title's instance*), and what they measure is the "Land Surface Temperature" already written (added to this item on 2026-11-01, the review of the second opinion's facts).
- **Left out:** "associated" (notes, "associated quality control assessments")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance: its subject would be that fact, not an entity the record names." "associated" says only that the quality control assessments go with the temperature bands, how the fact HAS_ANCILLARY_DATA "quality control assessments" holds. Saying how a fact holds needs a fact about a fact, a qualifier kept with the ground truth triple it holds for (as Wikidata's statement qualifiers do), which is future work: docs/improvements.md, *Rule 19 can lose which fact a qualifier went with*, option 4 (recommended on 2026-10-27, decided on 2026-10-30). Decided on 2026-10-31; until then this item waited on the experts' answer to Q27 (rule 2 of *What counts as a fact*).
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
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance: its subject would be that fact, not an entity the record names." "about known issues" says only what the details at the page are about, how the fact DOCUMENTED_AT holds. The field's practice records the same fact and no more: W3C DCAT's `dcat:landingPage` and FOAF's `foaf:page` ("A page or document about this thing") link a thing to a page about it and say nothing of what the page covers. Saying how a fact holds needs a fact about a fact, a qualifier kept with the ground truth triple it holds for (as Wikidata's statement qualifiers do), which is future work: docs/improvements.md, *Rule 19 can lose which fact a qualifier went with*, option 4 (recommended on 2026-10-27, decided on 2026-10-30). Decided on 2026-10-31; until then this item waited on the experts' answer to Q28 (b) (rule 2 of *What counts as a fact*).
  - **May matter because:** a search for a dataset's known issues would need it.
  - **Question:** Q28 (b) (settled on 2026-10-31: see Q28's My notes).
- **Left out:** "MODIS/VIIRS Land Quality Assessment website" (notes, "[MODIS/VIIRS Land Quality Assessment website](https://landweb.modaps.eosdis.nasa.gov/knownissue?sensor=MODIS&sat=Terra&as=6)"), as the name of the page
  - **Rule:** Writing a classed triple, rule 20: "Write that one name is also known as another (ALSO_KNOWN_AS) only when the record gives the other name in words of its own". The words are the text of the page's link, not words of the record's own that give the page another name, and the ground truth schema's WebPage is "a web address, written as the address itself". My ground truth triple has the page as its address (DOCUMENTED_AT). Until 2026-10-31 the page had ALSO_KNOWN_AS "MODIS/VIIRS Land Quality Assessment", and this item left out only the type word "website" (third audit, finding G-1).
  - **May matter because:** it is the page's name, by which a person would look for it.
- **Left out:** "product" (notes, "[MOD11_L2](https://doi.org/10.5067/MODIS/MOD11_L2.006) swath product")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the entity,"; "swath" is a ground truth triple of its own (HAS_SPATIAL_REPRESENTATION, as "gridded" for the record at pool position 6).
- **Left out:** what "SIN" stands for (title, "SIN Grid")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for". The grid is written whole, ON_GRID "SIN Grid" (Writing a classed triple, rule 11: "A name stays whole: rules 19, 22 and 24 never split or shorten a name"), so no MAPPED_INTO "SIN" (decided on 2026-11-01, the review of the second opinion's facts; the same in the record at pool position 6).
- **Left out:** what "Terra" is (title, "MODIS/Terra", and notes, "Terra MODIS")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what Terra is. Its entity class, Platform, is written (FROM_PLATFORM "Terra", and "MODIS" ABOARD "Terra"), by rule 1's *A name the record does not explain*.
  - The list: GCMD Platforms keywords (version 25.2), "Terra" (checked on 2026-11-11).

## "ROSETTA-ORBITER PRELANDING OSINAC 2 EDR MTP003 V2.0" (pool position 8, id 938ee451-561c-492d-9e24-fe9a1048b835)

A held-out record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. 7 items, 2 that may matter.

- **Left out:** "2" (title, "OSINAC 2")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"; a bare number is not "L" or "Level" followed by a number.
  - **Question:** Q6 (b).
- **Left out:** "EDR" (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"
  - The record "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0" leaves out its title's "RDR" the same way.
  - **Question:** Q6 (b).
- **Left out:** "MTP003" (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"
  - **May matter because:** it tells this dataset from its siblings, as "MTP020" does in the record "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0" (its item; not checked for this record).
  - The drafted triple HAS_MISSION_PHASE "MTP003" (drafted by Gemini 2.5 Pro, never finished) is deleted.
  - **Question:** Q6 (b).
- **Left out:** "supersedes previous deliveries of the same dataset" (notes, "This version V2.0 supersedes previous deliveries of the same dataset.")
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names"
  - "previous deliveries of the same dataset" names no particular delivery or version, so a SUPERSEDES triple would have no object the record names. The record "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" names the release it replaces ("the previous v2014.1 datasets"), and this record does not. The drafted triple "V2.0" SUPERSEDES "previous deliveries of the same dataset" is deleted.
  - **May matter because:** it says that earlier deliveries of this dataset exist and are replaced.
- **Left out:** "phase", "mission" and "comet" (notes, "the PRELANDING phase of the Rosetta mission at the comet 67P")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the entity,"
  - My ground truth triples have the phase "PRELANDING", the mission "Rosetta" and the target "67P"; the type words say what kind of thing each is, which their entity classes already say.
- **Left out:** what "ROSETTA-ORBITER" is (title; the notes name only "the Rosetta mission")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what ROSETTA-ORBITER is. Its entity class, Platform, is written (FROM_PLATFORM "ROSETTA-ORBITER"), by rule 1's *A name the record does not explain*.
  - The list: PDS4 context product urn:esa:psa:context:instrument_host:spacecraft.ro, "The Rosetta Orbiter Spacecraft", of type Spacecraft, also titled "ROSETTA-ORBITER" (https://pds.nasa.gov/data/pds4/context-pds4/instrument_host/spacecraft.ro_1.1.xml, checked on 2026-11-13).
- **Left out:** what "OSIRIS" stands for (notes, inside the name "OSIRIS Narrow Angle Camera")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record names "OSIRIS" only inside the camera's name and never says what it is. Its entity class, Instrument, is written ("OSIRIS Narrow Angle Camera" PART_OF "OSIRIS", with the source text "OSIRIS Narrow Angle Camera", by rule 17's *A name's facts*), by rule 1's *A name the record does not explain*.
  - The reference: Wikidata, Optical, Spectroscopic, and Infrared Remote Imaging System (Q7098805), also named "OSIRIS", "scientific instrument on the Rosetta spacecraft", an instance of "space instrument" (https://www.wikidata.org/wiki/Q7098805, checked on 2026-11-13). No official NASA list names it: the PDS4 context products have entries for its two cameras (urn:esa:psa:context:instrument:ro.osinac and ro.osiwac) and none for OSIRIS itself.

## "STARDUST 9P/TEMPEL 1 DFMI 2/3 NEXT V1.0" (pool position 9, id dc4ff01b-12f0-4235-8c8a-afb4bfb3bdbb)

4 items, 2 that may matter.

- **Left out:** "comet" (notes, "encounter with comet 9P/Tempel 1" and "the entire comet encounter")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the entity,"
  - My ground truth triple has the target "9P/Tempel 1", and the phase "encounter".
- **Left out:** "convert" as a method (notes, "The RDR data convert the EDR (raw) sensor data")
  - **Rule:** Writing a classed triple, rule 24: "A verb or participle that says only what was done to the data ("corrected", "calibrated", "detrended", "binned", "mapped", "edited", "convert", "weighted") names no method". The record says the RDR data "convert" the EDR data, only a verb; I wrote "RDR data" COMPUTED_FROM "EDR (raw) sensor data" and no PRODUCED_USING_ALGORITHM.
  - **May matter because:** it is how the RDR data are made from the raw data.
  - **Question:** Q7.
- **Left out:** "entire" (notes, "from the entire comet encounter")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance: its subject would be that fact, not an entity the record names." "EDR (raw) sensor data" HAS_MISSION_PHASE "encounter" says the EDR (raw) sensor data come from the encounter; "entire" says only how much of it, how that fact holds (until 2026-11-01 the phase was the RDR data's: "RDR data" HAS_MISSION_PHASE "encounter"; the review of the second opinion's facts, judgment call A). Saying how a fact holds needs a fact about a fact, a qualifier kept with the ground truth triple it holds for (as Wikidata's statement qualifiers do), which is future work: docs/improvements.md, *Rule 19 can lose which fact a qualifier went with*, option 4 (recommended on 2026-10-27, decided on 2026-10-30). Decided on 2026-10-31; until then this item waited on the experts' answer to Q27 (rule 2 of *What counts as a fact*).
  - **May matter because:** it says the data cover all of the encounter, not a part of it. Checked on 2026-10-31: that is the EDR (raw) data; the RDR data cover the encounter "up to before the start of the anomaly" (the data set's catalog file, https://pdssbn.astro.umd.edu/holdings/sdu-c_d-dfmi-2_3-next-tempel1-v1.0/catalog/; see Q5's My notes). Until 2026-10-31 this line said "it says the RDR data cover all of the encounter, not a part of it."
  - **Question:** Q27 (settled on 2026-10-31: see Q27's My notes).
- **Left out:** what "STARDUST" is (title; the notes name only "the Stardust-NExT mission")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what STARDUST is. Its entity class, Platform, is written (FROM_PLATFORM "STARDUST"), by rule 1's *A name the record does not explain*.
  - The list: PDS4 context product spacecraft.sdu, "The Stardust Spacecraft", of type Spacecraft (https://pds.nasa.gov/data/pds4/context-pds4/instrument_host/spacecraft.sdu_1.3.xml, checked on 2026-11-11).

## "ROSETTA-ORBITER 67P/CAL ALICE 2 ESC1 V1.0" (pool position 10, id 3bceffb4-f01e-433c-af79-42b9d9427231)

4 items, 1 that may matter.

- **Left out:** "CAL" (title, "67P/CAL")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"
  - **May matter because:** checked on 2026-10-30: "CAL" is the PDS3 target "CALIBRATION" in the data set name (TARGET_NAME = "CALIBRATION"; the PDS3 Standards Reference lists "CAL Calibration" among target IDs, https://pds.nasa.gov/datastandards/pds3/standards/sr/Chapter06.pdf), so the data include observations of calibration targets. It does not mean "calibrated": the data set says its data are uncalibrated, CODMAC level 2 (https://archives.esac.esa.int/psa/ftp/INTERNATIONAL-ROSETTA-MISSION/ALICE/RO-C-CAL-ALICE-2-ESC1-V1.0/CATALOG/DATASET.CAT). My earlier reading ("calibration data") was close but imprecise. Still left out: the record's text does not explain it (rule 1).
  - **Question:** Q6 (b).
- **Left out:** "mission phase" (notes, "comet escort 1 mission phase")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the entity,"
  - My ground truth triple has the phase "comet escort 1", its target "67P/Churyumov-Gerasimenko" a triple of its own (rule 19 of *Writing a classed triple*).
- **Left out:** what "Rosetta Orbiter" is (title, "ROSETTA-ORBITER", and notes, "the Rosetta Orbiter ALICE UV Spectrometer")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what the Rosetta Orbiter is. Its entity class, Platform, is written (FROM_PLATFORM "Rosetta Orbiter", and "Rosetta Orbiter ALICE UV Spectrometer" ABOARD "Rosetta Orbiter"), by rule 1's *A name the record does not explain*.
  - The list: PDS4 context product urn:esa:psa:context:instrument_host:spacecraft.ro, "The Rosetta Orbiter Spacecraft", of type Spacecraft (https://pds.nasa.gov/data/pds4/context-pds4/instrument_host/spacecraft.ro_1.1.xml, checked on 2026-11-12).
- **Left out:** what "67P/Churyumov-Gerasimenko" is (title, "67P", and notes, "the 67P/Churyumov-Gerasimenko comet escort 1 mission phase", where "comet" is a word of the phase's name)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what 67P/Churyumov-Gerasimenko is. Its entity class, CelestialBody, is written (HAS_TARGET "67P/Churyumov-Gerasimenko", of the record's dataset and of "comet escort 1"), by rule 1's *A name the record does not explain*.
  - The reference: PDS4 context product urn:nasa:pds:context:target:comet.67p_churyumov-gerasimenko, "67P/Churyumov-Gerasimenko", of type Comet (https://pds.nasa.gov/data/pds4/context-pds4/target/comet.67p_churyumov-gerasimenko_1.1.xml, checked on 2026-11-12).

## "Shawano (SWNO) Ground-based Vector Magnetic Field (L2) 0.5 s Data" (pool position 11, id 1e16bbd4-0f3f-4f88-bda1-55a553c1282e)

A held-out record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. 3 items, all 3 that may matter.

- **Left out:** what "WI" stands for (notes, "Shawano, WI")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what WI is. Wikidata's Wisconsin (Q1537) has "WI" among its other names and is an instance of "U.S. state", a kind that fits no entity class of the ground truth schema (Country is "a nation", and SpatialExtent is "an area the data cover", which the record does not say of Wisconsin), so the name stays unexplained (https://www.wikidata.org/wiki/Q1537, checked on 2026-11-13). "Shawano, WI" and "Shawano (SWNO)" name one station, written "Shawano (SWNO)" (rule 23 of *Writing a classed triple*, test 4: the wording the record gives first).
  - **May matter because:** it gives the state the station is in, which a search by place would need.
- **Left out:** what "GEO" stands for (notes, "Station Location: (GEO Latitude 44.8, Longitude 271.4)")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"
  - The record does not say which coordinate system "GEO" names, so no HAS_COORDINATE_SYSTEM triple is written. "GEO" stays in the instance of the station's position, as written (rule 11 of *Writing a classed triple*): "Shawano (SWNO)" LOCATED_AT "GEO Latitude 44.8, Longitude 271.4".
  - **May matter because:** my reading, not checked: geographic coordinates, as against the magnetic coordinates that magnetometer stations also give.
- **Left out:** "THEMIS EPO/UCLA Network" (notes, the last item of the notes' list)
  - **Rule:** What counts as a fact, rule 1: "Only what the record states." The notes name the network at the end of a list of the dataset's labels, with no words that say how the network and the dataset or the station are related (whether the station belongs to the network, or the network provides the data). Its kind word, "Network", fits no single entity class: a network of ground stations is not one Platform, and could be read as an Organization or as a Mission. No reference of rule 1's *A name the record does not explain* names it: the GCMD Platforms keywords (version 25.2) have "THEMIS", the satellites, and Wikidata has no entry named "THEMIS EPO" (checked on 2026-11-13). The "/" stays inside the name (rule 22 of *Writing a classed triple*, *Lists joined by "/" or "+"*: "UCLA" is never named alone).
  - **May matter because:** it names the network the station belongs to, which a search by network would need.

## "Ensemble X-Ray Variability of AGN in 2XMMi-DR3" (pool position 12, id bb1fe4b0-6543-42e3-9386-acbab0b37ad4)

The notes are mostly the abstract of the study the table comes from; whether a study's aim, method and findings belong in the ground truth was asked in Q26, settled on 2026-10-31: the study's aim and method are ground truth triples of the record's dataset (HAS_PURPOSE, PRODUCED_USING_ALGORITHM), and its background and findings are left out (rule 8 of *What counts as a fact*, *A study a record tells*). 27 items, 19 that may matter.

- **Left out:** "The X-ray variability of active galactic nuclei (AGN) has been most often investigated with studies of individual, nearby sources, and only a few ensemble analyses have been applied to large samples in wide ranges of luminosity and redshift." (notes)
  - **Rule:** What counts as a fact, rule 8: "Nothing else in the study is a fact of the record's dataset: its background, its findings, what it says about methods it did not use" It is the background of the study, about earlier studies. Decided on 2026-10-31; until then this item waited on the experts' answer to Q26 (rule 2 of *What counts as a fact*). (Until 2026-10-31 this item had cited rule 9, as naming no specific thing; third audit, finding L-6.)
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
  - **Rule:** What counts as a fact, rule 8: "When a record tells the study its dataset comes from, the study's aim and its method are facts of the record's dataset (its purpose, HAS_PURPOSE, and the method it was produced using, PRODUCED_USING_ALGORITHM, rule 24, a processing step). Nothing else in the study is a fact of the record's dataset". The method is a ground truth triple ("structure function (SF)", PRODUCED_USING_ALGORITHM); in which domain it works is a detail the study gives of its method, not the method. Decided on 2026-10-31 (Q28 (d), settled); until then it waited on the experts' answer to Q28 (d) (rule 2 of *What counts as a fact*, its part on waiting for an expert), with no clear would-be triple, since its predicate and the entity class of "time domain" were not settled. (Until 2026-10-31 it waited on Q26, and before that cited rule 4; third audit, finding L-7.) The field's home for it is a subject list, the Unified Astronomy Thesaurus's "Time domain astronomy": docs/improvements.md, *Knowledge enrichment from the model, verified and labelled* (080).
  - **May matter because:** it says how the method works: in the time domain.
  - **Question:** Q28 (d) (settled on 2026-10-31: see Q28's My notes).
- **Left out:** "The SF is also more appropriate than fractional variability and excess variance, because these parameters are biased by the duration of the monitoring time interval in the rest-frame, and therefore by cosmological time dilation." (notes)
  - **Rule:** What counts as a fact, rule 5: "Take out words such as "great"." ("more appropriate" is the authors' judgement). The second clause, that "these parameters are biased by the duration of the monitoring time interval", is about two measures the study did not use: What counts as a fact, rule 8: "Nothing else in the study is a fact of the record's dataset: its background, its findings, and what it says about methods it did not use." Decided on 2026-10-31; until then this item waited on the experts' answer to Q26 (rule 2 of *What counts as a fact*). (Until 2026-10-31 this clause had cited no rule; third audit, finding L-8.)
  - **May matter because:** it says why the method was chosen.
  - **Question:** Q26 (settled on 2026-10-31: see Q26's My notes).
- **Left out:** "They do not find evidence of the break in the SF, at variance with the case of lower luminosity AGNs." (notes)
  - **Rule:** What counts as a fact, rule 6: "A ground truth triple can't say "not"."
- **Left out:** "then available" and "latest" (notes, "the version of the Serendipitous Source Catalog then available" and "the latest incremental update")
  - **Rule:** What counts as a fact, rule 10: "Take out "latest", "current", "now", "then available", and words like them." They say what was so when the study was made, not a lasting fact.
- **Left out:** "all datasets were publicly available by 2009 October 31" (notes)
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names" It is about the observations the catalog was made from, which the record doesn't name, so there is no subject for a triple.
  - **May matter because:** it dates the data the catalog holds.
- **Left out:** "but not all public observations are included in this catalog" (notes)
  - **Rule:** What counts as a fact, rule 6: "A ground truth triple can't say "not"."
- **Left out:** "taking account of the substantial overlaps between observations" (notes)
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words." It explains why my ground truth triple HAS_SKY_AREA "~ 504 deg^2" is smaller than HAS_SUMMED_SKY_AREA "~ 814 deg^2", which the two predicates' definitions already say: HAS_SKY_AREA counts "each part of the sky counted once", HAS_SUMMED_SKY_AREA "each part of the sky counted as many times as it is covered". Decided on 2026-10-31; until then this item waited on the experts' answer to Q26 (rule 2 of *What counts as a fact*).
  - **May matter because:** it says how the net sky area was computed from the catalog's fields.
  - **Question:** Q26 (settled on 2026-10-31: see Q26's My notes).
- **Left out:** "therefore a significant number of sources (41,979) have more than one record within the catalog" (notes)
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names" HAS_NUMBER_OF holds a number of things, and "sources with more than one record" isn't a thing the record names; "significant" is a judgement (What counts as a fact, rule 5: "Take out words such as "great".").
  - **May matter because:** it says how many sources the catalog has detected more than once.
- **Left out:** "(above the processing likelihood threshold of 6)" (notes, "The 2XMMi-DR3 catalogue contains 353,191 detections (above the processing likelihood threshold of 6)")
  - **Rule:** Writing a classed triple, rule 24: "Each step gives up to two ground truth triples, each written only if the record names both of its ends: the output computed from the input (COMPUTED_FROM), and the output produced using the method (PRODUCED_USING_ALGORITHM)." The parentheses state a fact of their own, so they are taken out of the instance (rule 20: "Parentheses that state a fact of their own (a period, a duration, an amount, a place) are taken out of the instance"), and the ground truth triple is "2XMMi-DR3" HAS_NUMBER_OF "353,191 detections". The threshold is a setting of the processing that made the catalogue's detections, and the record names no method for that step. A setting of a step is neither of the step's two triples, as for the maximum distance of 1.5 arcseconds, below. Until 2026-11-12 the parentheses stayed in the instance.
  - **May matter because:** it says which detections the catalogue counts.
- **Left out:** "corresponding to the uncertainty in the X-ray positions" (notes)
  - **Rule:** Writing a classed triple, rule 24: "Each step gives up to two ground truth triples, each written only if the record names both of its ends: the output computed from the input (COMPUTED_FROM), and the output produced using the method (PRODUCED_USING_ALGORITHM)." It is why the maximum distance of 1.5 arcseconds was chosen, a setting of the matching step, left out with that distance (below). Decided on 2026-10-31; until then this item waited on the experts' answer to Q26 (rule 2 of *What counts as a fact*).
  - **May matter because:** it says how precise the X-ray positions are.
  - **Question:** Q26 (settled on 2026-10-31: see Q26's My notes).
- **Left out:** "cross-correlated" as a method (notes, "The selected sources were cross-correlated with the DR7 edition of the SDSS Quasar Catalog")
  - **Rule:** Writing a classed triple, rule 24: "A verb or participle that says only what was done to the data ("corrected", "calibrated", "detrended", "binned", "mapped", "edited", "convert", "weighted") names no method". Only a verb; I wrote COMPUTED_FROM "DR7 edition of the SDSS Quasar Catalog" and no PRODUCED_USING_ALGORITHM.
  - **Question:** Q7.
- **Left out:** "structure function (SF)" HAS_PURPOSE "ensemble analysis even when only a few observations are available for individual sources and the power spectral density (PSD) cannot be derived" (notes, "allows for an ensemble analysis even when only a few observations are available for individual sources and the power spectral density (PSD) cannot be derived")
  - **Rule:** What counts as a fact, rule 8: "When a record tells the study its dataset comes from, the study's aim and its method are facts of the record's dataset (its purpose, HAS_PURPOSE, and the method it was produced using, PRODUCED_USING_ALGORITHM, rule 24, a processing step). Nothing else in the study is a fact of the record's dataset". What the structure function "allows for" is a use the study gives for its method, not a purpose: HAS_PURPOSE is "is meant to achieve", Wikidata's "has goal" (P3712), which Wikidata keeps apart from "has use" (P366, "can be used for"); coining a predicate for a use for this one record would tailor the schema to it. Decided on 2026-10-31 (Q9 (b), settled); until then it waited on the experts' answer to Q9 (b) (rule 2 of *What counts as a fact*, its part on waiting for an expert), and its would-be ground truth triple was in `annotations/pending_triples.csv`, now deleted. (Until 2026-10-31 it waited on Q26 too.)
  - **May matter because:** it says why the method was used.
  - **Question:** Q9 (b) (settled on 2026-10-31: see Q9's My notes).
- **Left out:** "the authors" REPORTED "statistically consistent results for the two samples" (Finding) (notes, "The authors find statistically consistent results for the two samples")
  - **Rule:** What counts as a fact, rule 8: "Nothing else in the study is a fact of the record's dataset: its background, its findings, what it says about methods it did not use" It is a finding of the study. Decided on 2026-10-31; until then this item waited on the experts' answer to Q26 (rule 2 of *What counts as a fact*).
  - **May matter because:** it is a result of the study the table comes from.
  - **Question:** Q26 (settled on 2026-10-31: see Q26's My notes).
- **Left out:** "the authors" REPORTED "SF described by a power law of the time lag tau, approximately as SF ~ tau^0.1" (Finding) (notes, "with the SF described by a power law of the time lag tau, approximately as SF ~ tau^0.1")
  - **Rule:** What counts as a fact, rule 8: "Nothing else in the study is a fact of the record's dataset: its background, its findings, what it says about methods it did not use" It is a finding of the study. Decided on 2026-10-31; until then this item waited on the experts' answer to Q26 (rule 2 of *What counts as a fact*).
  - **May matter because:** it is a result of the study the table comes from.
  - **Question:** Q26 (settled on 2026-10-31: see Q26's My notes).
- **Left out:** "the authors" REPORTED "strong anti-correlation of the variability with X-ray luminosity, accompanied by a change of the slope of the SF" (Finding) (notes, "They confirm a strong anti-correlation of the variability with X-ray luminosity, accompanied by a change of the slope of the SF")
  - **Rule:** What counts as a fact, rule 8: "Nothing else in the study is a fact of the record's dataset: its background, its findings, what it says about methods it did not use" It is a finding of the study. Decided on 2026-10-31; until then this item waited on the experts' answer to Q26 (rule 2 of *What counts as a fact*).
  - **May matter because:** it is a result of the study the table comes from.
  - **Question:** Q26 (settled on 2026-10-31: see Q26's My notes).
- **Left out:** "the authors" REPORTED "evidence in support of a weak, intrinsic, average increase of X-ray variability with redshift" (Finding) (notes, "They also find evidence in support of a weak, intrinsic, average increase of X-ray variability with redshift")
  - **Rule:** What counts as a fact, rule 8: "Nothing else in the study is a fact of the record's dataset: its background, its findings, what it says about methods it did not use" It is a finding of the study. Decided on 2026-10-31; until then this item waited on the experts' answer to Q26 (rule 2 of *What counts as a fact*).
  - **May matter because:** it is a result of the study the table comes from.
  - **Question:** Q26 (settled on 2026-10-31: see Q26's My notes).
- **Left out:** "Ensemble X-Ray Variability of AGN in 2XMMi-DR3" DEVELOPED_BY_PARTY "the authors" (notes, "The authors used a maximum distance of 1.5 arcseconds")
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names" "the authors" names no specific people (the record never names them). The table's developer is the HEASARC ("This table was created by the HEASARC"); the authors made the selection described in the study. (Until 2026-10-31 this item cited rule 2, as waiting on Q26 with the study's aim, method and findings; audit finding G-9 (b).)
  - **May matter because:** it says who selected the table's sources.
- **Left out:** "Ensemble X-Ray Variability of AGN in 2XMMi-DR3" HAS_MATCHING_DISTANCE "1.5 arcseconds" (notes, "The authors used a maximum distance of 1.5 arcseconds")
  - **Rule:** Writing a classed triple, rule 24: "Each step gives up to two ground truth triples, each written only if the record names both of its ends: the output computed from the input (COMPUTED_FROM), and the output produced using the method (PRODUCED_USING_ALGORITHM)." The maximum distance is a setting of the step that matched the selected sources with the quasar catalog, which gives the ground truth triple COMPUTED_FROM "DR7 edition of the SDSS Quasar Catalog" and names no method ("cross-correlated", above); a setting of a step is neither of the step's two triples. Decided on 2026-10-31; until then this item waited on the experts' answer to Q26 (rule 2 of *What counts as a fact*).
  - **May matter because:** it says how the sources of the table were matched with the quasar catalog.
  - **Question:** Q26 (settled on 2026-10-31: see Q26's My notes).
- **Left out:** "Ensemble X-Ray Variability of AGN in 2XMMi-DR3" ALSO_KNOWN_AS "XMM-Newton sample" (notes, "The authors refer to these sources as the XMM-Newton sample")
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names" "XMM-Newton sample" names the sources the table holds, not the table, and the record names those sources only by a count ("412 quasars", a Value), so there is no instance for them to be the subject of an ALSO_KNOWN_AS triple (the rule was named on 2026-10-31).
- **Left out:** "from 2 to 25 epochs each" (notes, "resulting in 412 quasars that were observed by XMM-Newton from 2 to 25 epochs each"), as how many times each quasar was observed
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names" The count is each quasar's, not the dataset's, and the record names the quasars only by a count ("412 quasars", a Value), so there is no instance for them to be the subject (as for "XMM-Newton sample", above). Until 2026-10-31 the dataset had HAS_NUMBER_OF "from 2 to 25 epochs each" (third audit, finding G-8).
  - **May matter because:** it says how often each source was observed, which the study's variability measure depends on.
- **Left out:** what "XMM-Newton" is (notes, "the catalogs of XMM-Newton and Swift" and "412 quasars that were observed by XMM-Newton")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what XMM-Newton is. Its entity class, Platform, is written (FROM_PLATFORM "XMM-Newton", of the record's dataset), by rule 1's *A name the record does not explain*. Until 2026-11-12 its entity class rested on the record's words "observed by XMM-Newton" alone.
  - The reference: Wikidata, XMM-Newton (Q693861), an instance of "space telescope", a subclass of "artificial satellite", which carries a scientific instrument: a craft in space that carries instruments, the definition of Platform (https://www.wikidata.org/wiki/Q693861, checked on 2026-11-12). No official NASA list names it: the GCMD Platforms and Instruments keywords (version 25.2) and the PDS4 context products have no entry for it.
- **Left out:** "2XMMi-DR3" FROM_PLATFORM "XMM-Newton" (notes, "two serendipitously selected AGN samples extracted from the catalogs of XMM-Newton and Swift" … "For XMM, the authors used the version of the Serendipitous Source Catalog then available, namely 2XMMi-DR3")
  - **Rule:** What counts as a fact, rule 1: "A fact that the record does not state may be written only when it follows from what the record states by one of the three tests below (Replacement, Comparison, Membership by name); nothing else, and no outside knowledge, adds such a fact. The list of tests is closed". No passage states that 2XMMi-DR3 was collected from XMM-Newton. "the catalogs of XMM-Newton" joins the catalogs to the craft by "of" alone, which could mean that the catalogs were made from its observations, by its team or for its users, and does not say which, so it states no predicate of its own. "For XMM, … namely 2XMMi-DR3" says which catalog the study used for its XMM-Newton sample. That 2XMMi-DR3 holds observations made by XMM-Newton follows from the two sentences together, by none of the three tests (*Replacement*, *Comparison*, *Membership by name*), as for the eight flights of the record at pool position 19. The ground truth had this triple until 2026-11-13 (docs/improvements.md, *Fifth round of rule fixes*).
  - **May matter because:** it says which observatory the catalog comes from. The record's dataset keeps FROM_PLATFORM "XMM-Newton", which the record states ("412 quasars that were observed by XMM-Newton").
- **Left out:** what "HEASARC" stands for (notes, "This table was created by the HEASARC" and "a service provided by NASA HEASARC")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what HEASARC is. Its entity class, Organization, is written (DEVELOPED_BY_PARTY and PROVIDED_BY_PARTY "NASA HEASARC", and "NASA HEASARC" PART_OF "NASA"), by rule 1's *A name the record does not explain*.
  - The reference: Wikidata, High Energy Astrophysics Science Archive Research Center (Q130537792), also named "HEASARC", an instance of "research center" (https://www.wikidata.org/wiki/Q130537792, checked on 2026-11-12). No official NASA list names it: the GCMD Providers keywords (version 25.2) have no entry for it.
- **Left out:** what "NASA" is (notes, "NASA HEASARC")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what NASA is. Its entity class, Organization, is written ("NASA HEASARC" PART_OF "NASA"), by rule 1's *A name the record does not explain*.
  - The reference: GCMD Providers keywords (version 25.2), the level "NASA" under "GOVERNMENT AGENCIES-U.S. FEDERAL AGENCIES", which holds NASA's centers and offices (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/providers?format=csv, checked on 2026-11-12).

## "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0" (pool position 13, id ab33f184-95f4-4f33-8f3d-c4a09ec525d3)

11 items, 8 that may matter.

- **Left out:** "MTP020" (title, "ESC3-MTP020")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"
  - **May matter because:** checked on 2026-10-30: planning period no. 20 (MTP, a numbered planning period; checked on 2026-10-31: ESA's *OSIRIS Science User Guide*, RO-RIS-MPAE-MA-011, section 5.1, spells it out as the Rosetta "Mid-Term Planning-cycle", covering "a timespan of roughly four weeks", https://archives.esac.esa.int/psa/ftp/INTERNATIONAL-ROSETTA-MISSION/OSINAC/RO-C-OSINAC-4-ESC3-67P-M20-INFLDSTR-V1.0/DOCUMENT/SCIENCE_USER_GUIDE/SCIENCE_USER_GUIDE_V05.PDF, not "Medium Term Plan"), inside the phase COMET ESCORT 3; the Rosetta NAVCAM archive lists "COMET ESCORT 3 MTP020 ESC3-MTP020 2015-08-25 23:25:00" (https://archives.esac.esa.int/psa/ftp/INTERNATIONAL-ROSETTA-MISSION/NAVCAM/RO-C-NAVCAM-2-ESC1-MTP010-V1.1/DOCUMENT/RO-SGS-IF-0001.ASC), and this data set covers 2015-08-25T23:25 to 2015-09-22T23:24:59 (https://archives.esac.esa.int/psa/ftp/INTERNATIONAL-ROSETTA-MISSION/OSINAC/RO-C-OSINAC-4-ESC3-67P-M20-INFLDSTR-V1.0/CATALOG/DATASET.CAT). It tells this dataset from its siblings. Still left out: the record's text does not explain it (rule 1).
  - **Question:** Q6 (b).
- **Left out:** "RDR" (title, "RDR-INFLDSTR")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"
  - **May matter because:** another record uses it as a name of data ("The RDR data convert the EDR (raw) sensor data"); this one doesn't explain it, and its level is "CODMAC level 4". Checked on 2026-10-30: "RDR" is the data set type "Reduced Data Record", not a level (PDS3 Standards Reference, chapter 6, https://pds.nasa.gov/datastandards/pds3/standards/sr/Chapter06.pdf); Rosetta's archive conventions pair RDR with CODMAC 3 (ESA, RO-EST-TN-3372), while this data set uses it at CODMAC 4.
  - **Question:** Q6 (b).
- **Left out:** "prime" (notes, "The prime target is comet 67P/Churyumov-Gerasimenko 1 (1969 R1)")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance: its subject would be that fact, not an entity the record names." HAS_TARGET says the dataset is about the comet; "prime" says only that it is the main target, how that fact holds. Saying how a fact holds needs a fact about a fact, a qualifier kept with the ground truth triple it holds for (as Wikidata's statement qualifiers do), which is future work: docs/improvements.md, *Rule 19 can lose which fact a qualifier went with*, option 4 (recommended on 2026-10-27, decided on 2026-10-30). Decided on 2026-10-31; until then this item waited on the experts' answer to Q27 (b) (rule 2 of *What counts as a fact*).
  - **May matter because:** a search for other bodies in these images would need it.
  - **Question:** Q27 (settled on 2026-10-31: see Q27's My notes).
- **Left out:** "comet" (notes, "comet 67P/Churyumov-Gerasimenko 1 (1969 R1)")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the entity,"
- **Left out:** "spacecraft" and "mission phase" (notes, "the Rosetta spacecraft" and "the COMET ESCORT 3 mission phase")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the entity,"; "the Rosetta spacecraft" is written as "ROSETTA-ORBITER", the wording that says more (rule 23).
  - **Question:** Q2 (b) (settled on 2026-10-31: see Q2's My notes).
- **Left out:** "Lien" (notes, "Lien corrected dataset after September 2019 PSA/PDS external peer review")
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words." My ground truth triple REVISED_AFTER "September 2019 PSA/PDS external peer review" says the dataset was corrected after the review; "Lien" names what was corrected, the issues the review raised, which is what a correction after a review is (checked on 2026-10-30: PDS defines a lien as "A formally expressed issue with one or more products in a collection", and ESA's procedure for this review says "Within ESA, issues raised are known as RIDs (Review Item Discrepancies), while PDS refer to these as liens", https://sbnreview.astro.umd.edu/201909_Rosetta/procedure_docs/RO-SGS-PR-1023-App5%20-%20RSI%20Rosetta%20CLS%20Science%20Archive%20Review.pdf). Decided on 2026-10-31; until then this item waited on the experts' answer to Q28 (c) (rule 2 of *What counts as a fact*).
  - **May matter because:** it says what the correction was about.
  - **Question:** Q28 (c) (settled on 2026-10-31: see Q28's My notes).
- **Left out:** PRODUCED_USING_ALGORITHM "solar stray-light corrected" (notes, "contains solar stray-light corrected, in-field stray-light corrected, radiometric calibrated and geometric distortion corrected (resampled) image data")
  - **Rule:** Writing a classed triple, rule 24: "A verb or participle that says only what was done to the data ("corrected", "calibrated", "detrended", "binned", "mapped", "edited", "convert", "weighted") names no method". "solar stray-light corrected" describes the data; since 2026-10-31 what was corrected is written, CLEANED_OF "solar stray-light" (rule 24: "What a step removed from the data, or corrected in them, is neither the step's input nor its method"); it is not the name of a method (as for "detrended" in the record at pool position 5).
  - **May matter because:** it says which corrections were applied to the images.
  - **Question:** Q7 (c) (settled on 2026-10-31: see Q7's My notes).
- **Left out:** PRODUCED_USING_ALGORITHM "in-field stray-light corrected" (notes, "contains solar stray-light corrected, in-field stray-light corrected, radiometric calibrated and geometric distortion corrected (resampled) image data")
  - **Rule:** Writing a classed triple, rule 24: "A verb or participle that says only what was done to the data ("corrected", "calibrated", "detrended", "binned", "mapped", "edited", "convert", "weighted") names no method". "in-field stray-light corrected" describes the data; since 2026-10-31 what was corrected is written, CLEANED_OF "in-field stray-light" (rule 24: "What a step removed from the data, or corrected in them, is neither the step's input nor its method"); it is not the name of a method (as for "detrended" in the record at pool position 5).
  - **May matter because:** it says which corrections were applied to the images.
  - **Question:** Q7 (c) (settled on 2026-10-31: see Q7's My notes).
- **Left out:** PRODUCED_USING_ALGORITHM "radiometric calibrated" (notes, "contains solar stray-light corrected, in-field stray-light corrected, radiometric calibrated and geometric distortion corrected (resampled) image data")
  - **Rule:** Writing a classed triple, rule 24: "A verb or participle that says only what was done to the data ("corrected", "calibrated", "detrended", "binned", "mapped", "edited", "convert", "weighted") names no method". "radiometric calibrated" describes the data; it is not the name of a method (as for "detrended" in the record at pool position 5).
  - **May matter because:** it says which corrections were applied to the images.
  - **Question:** Q7 (c) (settled on 2026-10-31: see Q7's My notes).
- **Left out:** PRODUCED_USING_ALGORITHM "geometric distortion corrected (resampled)" (notes, "contains solar stray-light corrected, in-field stray-light corrected, radiometric calibrated and geometric distortion corrected (resampled) image data")
  - **Rule:** Writing a classed triple, rule 24: "A verb or participle that says only what was done to the data ("corrected", "calibrated", "detrended", "binned", "mapped", "edited", "convert", "weighted") names no method". "geometric distortion corrected (resampled)" describes the data; since 2026-10-31 what was corrected is written, CLEANED_OF "geometric distortion" (rule 24: "What a step removed from the data, or corrected in them, is neither the step's input nor its method"); it is not the name of a method (as for "detrended" in the record at pool position 5).
  - **May matter because:** it says which corrections were applied to the images.
  - **Question:** Q7 (c) (settled on 2026-10-31: see Q7's My notes).
- **Left out:** what "OSIRIS" stands for (notes, inside the name "OSIRIS Narrow Angle Camera")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record names "OSIRIS" only inside the camera's name and never says what it is. Its entity class, Instrument, is written ("OSIRIS Narrow Angle Camera" PART_OF "OSIRIS", with the source text "OSIRIS Narrow Angle Camera", by rule 17's *A name's facts*, as "GRaND plus Z boron loaded sensor" PART_OF "GRaND" in the record "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0"), by rule 1's *A name the record does not explain*. Until 2026-11-12 no ground truth triple had "OSIRIS" as an instance, since no official NASA list names it and its entity class would have rested on outside knowledge (decided on 2026-11-01, the review of the second opinion's facts).
  - The reference: Wikidata, Optical, Spectroscopic, and Infrared Remote Imaging System (Q7098805), also named "OSIRIS", "scientific instrument on the Rosetta spacecraft", an instance of "space instrument" (https://www.wikidata.org/wiki/Q7098805, checked on 2026-11-12). No official NASA list names it: the PDS4 context products have entries for its two cameras (urn:esa:psa:context:instrument:ro.osinac and ro.osiwac) and none for OSIRIS itself.

## "MARS EXPRESS ASPERA-3 RAW EDR ELECTRON SPECTROMTR EXT2 V1.0" (pool position 14, id 7400495e-f11f-475f-a647-070bc2f82a92)

A held-out record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. 5 items, none that may matter.

- **Left out:** "EDR" (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"
  - **Question:** Q6 (b).
- **Left out:** "RAW", "ELECTRON SPECTROMTR" and "EXT2" as facts of their own (title)
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words."
  - They are the title's wordings of facts the notes state: "raw units of counts/accumulation" (HAS_UNIT), the "Mars Express ASPERA-3 Electron Spectrometer (ELS)" (ACQUIRED_BY_INSTRUMENT; "SPECTROMTR" is a shortened spelling of "Spectrometer", and rule 23 of *Writing a classed triple* writes the wording that says more) and "the second mission extension" (HAS_MISSION_PHASE).
- **Left out:** what "Mars Express" is (title, "MARS EXPRESS", and notes, "Mars Express ASPERA-3 Electron Spectrometer (ELS)")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what Mars Express is. Its entity class, Platform, is written (FROM_PLATFORM "Mars Express", "Mars Express ASPERA-3 Electron Spectrometer (ELS)" ABOARD "Mars Express", and "Mars Express" HAS_TARGET "Mars"), by rule 1's *A name the record does not explain*. The PDS4 context products also hold the mission, urn:esa:psa:context:investigation:mission.mars_express, titled "MARS EXPRESS" too; the notes name the craft that carries the instrument (rule 17 of *Writing a classed triple*, *A platform in an instrument's name*), and the title's first word is the instrument host.
  - The list: PDS4 context product urn:esa:psa:context:instrument_host:spacecraft.mex, "The Mars Express Orbiter", of type Spacecraft, also titled "MARS EXPRESS" (https://pds.nasa.gov/data/pds4/context-pds4/instrument_host/spacecraft.mex_1.1.xml, checked on 2026-11-13).
  - **Question:** Q2.
- **Left out:** what "ASPERA-3" stands for (title, and notes, inside the name "Mars Express ASPERA-3 Electron Spectrometer (ELS)")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what ASPERA-3 is. Its entity class, Instrument, is written (ACQUIRED_BY_INSTRUMENT "ASPERA-3", and "Mars Express ASPERA-3 Electron Spectrometer (ELS)" PART_OF "ASPERA-3"), by rule 1's *A name the record does not explain*.
  - The list: PDS4 context product urn:esa:psa:context:instrument:mex.aspera-3 (earlier identifier urn:nasa:pds:context:instrument:aspera-3.mex), "Mars Express Orbiter Analyzer of Space Plasma and Energetic Atoms (3rd Version)", whose description names it "(ASPERA-3)" (https://pds.nasa.gov/data/pds4/context-pds4/instrument/mex.aspera-3_1.2.xml, checked on 2026-11-13).
- **Left out:** what "Mars" is (notes, inside the name "Mars Express")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what Mars is. Its entity class, CelestialBody, is written ("Mars Express" HAS_TARGET "Mars", by rule 2's *A fact inside a name*), by rule 1's *A name the record does not explain*.
  - The reference: PDS4 context product urn:nasa:pds:context:target:planet.mars, "Mars", of type Planet (https://pds.nasa.gov/data/pds4/context-pds4/target/planet.mars_1.3.xml, checked on 2026-11-13).

## "Solar Orbiter Ephemeris, Heliocentric Trajectories, Heliographic, Heliographic Inertial, and Solar Ecliptic Coordinates, HelioWeb, Daily Data" (pool position 15, id 32614a2f-a286-4c7c-9f1e-deafdf8bd6a3)

14 items, 8 that may matter.

- **Left out:** "HelioWeb" (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for". The record never says what HelioWeb is (a service, a web site, a collection), so it has no entity class. No reference of rule 1's *A name the record does not explain* names it: the GCMD Instruments, Platforms and Providers keywords (version 25.2), the PDS4 context products and Wikidata have no entry named HelioWeb (checked on 2026-11-12).
  - **May matter because:** my reading, not checked: HelioWeb is the SPDF (NASA Goddard) service that serves these heliocentric trajectories; a search by service would need it.
- **Left out:** "Solar Orbiter" as the craft whose ephemeris the dataset holds (title, "Solar Orbiter Ephemeris")
  - **Rule:** What counts as a fact, rule 2: "When the naming states more than one predicate, or none, the name's words give no ground truth triple" (*A fact inside a name*). "Solar Orbiter" stands inside the Variable's name "Solar Orbiter Ephemeris" (HAS_VARIABLE), with no words that say how the ephemeris and the craft are related, so the fact would be read from a name's words, and the test decides it: "The test decides only the facts that are read from a name's words." Naming an ephemeris with a craft's name states no predicate of the ground truth schema. FROM_PLATFORM is "was collected from this Platform", and an ephemeris gives the positions of the craft and is not collected from it. HAS_TARGET is "is about, or studies, this CelestialBody", and joins only a CelestialBody. No predicate is coined: rule 14 coins one for a fact "that a sentence states with words of its own", and no sentence of the record states this one (decided on 2026-11-12). The entity class of "Solar Orbiter", Platform, is by rule 1's *A name the record does not explain*, and no ground truth triple has "Solar Orbiter" as an instance.
  - The reference: Wikidata, Solar Orbiter (Q653731), a solar probe (https://www.wikidata.org/wiki/Q653731, looked up on 2026-11-12: docs/improvements.md, *An entity class may come from a public reference*). Whether an official NASA list names it was not recorded then.
  - **May matter because:** it says whose positions the title gives, and a search by spacecraft would need it. The notes name another body, Comet Borrelly (the last item of this section).
- **Left out:** "where users can find many more objects" (notes)
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names" "many more objects" names none.
- **Left out:** "In the case of orbit data for planets, the orbit data can be used as a proxy for spacecraft ephemeris that are in orbit about the planets." (notes)
  - **Rule:** Writing a classed triple, rule 21: "Leave out facts about other datasets, such as a variant of the record's dataset (the same data at another temporal resolution, spatial resolution, or version), or a product made from it." Orbit data for planets are not this dataset, and no "part of" or "made from" link joins them; it is also a use (rule 9: "when the record doesn't name that work, the use gives no ground truth triple.").
  - **May matter because:** it says what planet data of this kind are good for.
- **Left out:** "On a heliospheric scale, differences between the planet orbital tarjectory and that of the spacecraft are very small." (notes)
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names" "the planet" and "the spacecraft" name no particular ones; "very small" is a judgement (rule 5).
- **Left out:** "For instance, the heliocentric longitudes differ by only 0.25° for a spacecraft stationed near the L1 Lagrange point at approximately 100 Earth radii upstream of the Earth." (notes)
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names" The subject is "a spacecraft", none in particular.
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
  - **Rule:** What counts as a fact, rule 4: "A sentence that says what type of entity an instance refers to ("Kestrel is an imager") gives no ground truth triple: the instance's entity class says it". It defines the method; the method itself is a ground truth triple (PRODUCED_USING_ALGORITHM "Mean of Date").
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
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"
  - **May matter because:** my reading, not checked: the PDS target codes for Jupiter, Saturn and the solar system, the targets of the data set; a search by target would need them. The notes say only "the planetary encounters".
  - **Question:** Q6 (b) lists other unexplained PDS title codes.
- **Left out:** "FULL RES" (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"; even spelled out, "full resolution" names no value (rule 9: "a variety of spatial resolutions" names no resolution).
  - **May matter because:** it says these are the analyzer's full-resolution data, not averages.
- **Left out:** "EDITED" (title), and "edited" (notes, "Some noise lines during the planetary encounters have been edited from the data set.") as a method
  - **Rule:** Writing a classed triple, rule 24: "A verb or participle that says only what was done to the data ("corrected", "calibrated", "detrended", "binned", "mapped", "edited", "convert", "weighted") names no method". What was removed is written: the record's dataset CLEANED_OF "noise lines during the planetary encounters" (rule 24: "What a step removed from the data, or corrected in them, is neither the step's input nor its method").
- **Left out:** "during the planetary encounters" as a mission phase of the dataset (notes)
  - **Rule:** What counts as a fact, rule 1: "Only what the record states." That the data include the encounters follows from the sentence (noise lines during them were in the data set) but is not stated.
  - **May matter because:** it says the data include the planetary encounters.
- **Left out:** "nearly all" (notes, "includes nearly all measurements")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance"
- **Left out:** "for the entire mission" (notes)
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names" The mission is not named, and "entire" only says how much of it.
  - **May matter because:** it says the data cover the whole mission (no dates are given).
- **Left out:** "Each sweep" (notes, "Each sweep of the PWS spectrum analyzer records")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance". It says how the analyzer records (sweep by sweep).
- **Left out:** "calibrated values" PRODUCED_USING_ALGORITHM "example C-language program" (notes)
  - **Rule:** Writing a classed triple, rule 21: "Leave out facts about other datasets, such as a variant of the record's dataset (the same data at another temporal resolution, spatial resolution, or version), or a product made from it." Its connection, "calibrated values" COMPUTED_FROM the record's dataset, is a ground truth triple.
  - **May matter because:** it is how users can calibrate the values.
- **Left out:** "reads this data set" as a fact of its own (notes)
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words." "calibrated values" COMPUTED_FROM the record's dataset already says it.
- **Left out:** the record's dataset HAS_MEASUREMENTS_OF "spectral densities" (notes, "This data set includes nearly all measurements collected from the spectrum analyzer component" … "Each sweep of the PWS spectrum analyzer records spectral densities")
  - **Rule:** What counts as a fact, rule 1: "A fact that the record does not state may be written only when it follows from what the record states by one of the three tests below (Replacement, Comparison, Membership by name); nothing else, and no outside knowledge, adds such a fact. The list of tests is closed". The record states that the analyzer records spectral densities ("PWS spectrum analyzer" MEASURES "spectral densities") and that the data set holds the analyzer's measurements (ACQUIRED_BY_INSTRUMENT "PWS spectrum analyzer"); that the data set holds spectral densities follows from the two, but by none of the three tests (*Replacement*, *Comparison*, *Membership by name*) (decided on 2026-11-01, the review of the second opinion's facts).
  - **May matter because:** a search for datasets by what they measure would need it.
- **Left out:** what "Voyager 1" is (title, "VG1", and notes, "the Plasma Wave Spectrometer (PWS) onboard Voyager 1")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what Voyager 1 is. Its entity class, Platform, is written (FROM_PLATFORM "Voyager 1", and "Plasma Wave Spectrometer (PWS)" ABOARD "Voyager 1"), by rule 1's *A name the record does not explain*.
  - The reference: PDS4 context product urn:nasa:pds:context:instrument_host:spacecraft.vg1, "VOYAGER 1", of type Spacecraft, with the host id "VG1" (https://pds.nasa.gov/data/pds4/context-pds4/instrument_host/spacecraft.vg1_1.5.xml, checked on 2026-11-12).

## "ROSETTA-ORBITER 67P OSIWAC 4 EXT3-MTP033 RDR-STR-REFL V1.0" (pool position 17, id 792e45e8-e7fb-427f-a3fb-2c1dac5f545f)

A held-out record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. 9 items, 3 that may matter.

- **Left out:** "MTP033" (title, "EXT3-MTP033")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"
  - **May matter because:** it tells this dataset from its siblings, as "MTP020" does in the record "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0" (its item; not checked for this record).
  - **Question:** Q6 (b).
- **Left out:** "RDR", "STR" and "REFL" (title, "RDR-STR-REFL")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"
  - **Question:** Q6 (b).
- **Left out:** "prime" (notes, "The prime target is comet 67P/Churyumov-Gerasimenko 1 (1969 R1)")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance"
  - HAS_TARGET says the dataset is about the comet; "prime" says only that it is the main target, how that fact holds, as in the record "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0".
  - **May matter because:** a search for other bodies in these images would need it.
- **Left out:** "comet" (notes, "comet 67P/Churyumov-Gerasimenko 1 (1969 R1)")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the entity,"
- **Left out:** "spacecraft" and "mission phase" (notes, "the Rosetta spacecraft" and "the ROSETTA EXTENSION 3 mission phase")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the entity,"; "the Rosetta spacecraft" is written as "ROSETTA-ORBITER", the wording that says more (rule 23).
- **Left out:** "Lien" (notes, "Lien corrected dataset after October 2018 PSA/PDS external peer review")
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words."
  - My ground truth triple REVISED_AFTER "October 2018 PSA/PDS external peer review" says the dataset was corrected after the review; "Lien" names what was corrected, the issues the review raised, as in the record "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0".
- **Left out:** PRODUCED_USING_ALGORITHM "solar stray light corrected", "radiometric calibrated" and "geometric distortion corrected (resampled)" (notes, "contains solar stray light corrected, radiometric calibrated and geometric distortion corrected (resampled) image data")
  - **Rule:** Writing a classed triple, rule 24: "A verb or participle that says only what was done to the data ("corrected", "calibrated", "detrended", "binned", "mapped", "edited", "convert", "weighted") names no method"
  - The words describe the data and name no method. What was corrected is written: CLEANED_OF "solar stray light" and CLEANED_OF "geometric distortion" (rule 24: "What a step removed from the data, or corrected in them, is neither the step's input nor its method"); "radiometric calibrated" names nothing removed.
  - **May matter because:** it says which corrections were applied to the images.
  - **Question:** Q7 (c).
- **Left out:** what "OSIRIS" stands for (notes, inside the name "OSIRIS Wide Angle Camera")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record names "OSIRIS" only inside the camera's name and never says what it is. Its entity class, Instrument, is written ("OSIRIS Wide Angle Camera" PART_OF "OSIRIS"), by rule 1's *A name the record does not explain*.
  - The reference: Wikidata, Optical, Spectroscopic, and Infrared Remote Imaging System (Q7098805), also named "OSIRIS", "scientific instrument on the Rosetta spacecraft", an instance of "space instrument" (https://www.wikidata.org/wiki/Q7098805, checked on 2026-11-13). No official NASA list names it: the PDS4 context products have entries for its two cameras (urn:esa:psa:context:instrument:ro.osinac and ro.osiwac) and none for OSIRIS itself.
- **Left out:** what "ROSETTA" is (notes, inside the name "ROSETTA EXTENSION 3")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what ROSETTA is: "the Rosetta spacecraft" names the craft, and the phase's name holds "ROSETTA" alone. Its entity class, Mission, is written ("ROSETTA EXTENSION 3" PART_OF "ROSETTA", by rule 2's *A fact inside a name*: "a Mission named in the name of one of its parts ... gives PART_OF"), by rule 1's *A name the record does not explain*.
  - The list: PDS4 context product urn:esa:psa:context:investigation:mission.international_rosetta_mission, "The International Rosetta Mission", of type Mission, also titled "ROSETTA" (https://pds.nasa.gov/data/pds4/context-pds4/investigation/mission.international_rosetta_mission_1.1.xml, checked on 2026-11-13). The craft's entry, urn:esa:psa:context:instrument_host:spacecraft.ro, is titled "ROSETTA-ORBITER", not "ROSETTA".

## "VIIRS/NPP BRDF/Albedo Parameter 3 Band M4 Daily L3 Global 30 ArcSec CMG V002" (pool position 18, id 0eedd2bc-b2e2-4cc1-a94d-41c141169334)

15 items, 6 that may matter.

- **Left out:** "NASA/NOAA" as a fact of its own (notes)
  - **Rule:** What counts as a fact, rule 1: "Only what the record states." The words name the two agencies and the platform, and do not say how they are related (whether the agencies built the platform, launched it or operate it), so they state no fact (rule 2, *A fact inside a name*: "When the naming states more than one predicate, or none, the name's words give no ground truth triple"). Two agencies' names before a platform's own could mean that the agencies launched the platform, developed it or sponsored it (LAUNCHED_BY_PARTY, DEVELOPED_BY_PARTY, SPONSORED_BY_PARTY), and naming does not settle which: "A relationship that naming does not state (that one thing funded, developed, provided or sponsored the other) is never read from a name". "NASA/NOAA" stays in the platform's instance, "NASA/NOAA Suomi National Polar-orbiting Partnership (Suomi NPP)" (Writing a classed triple, rule 19: "A qualifier stays in the instance, as written, if it is any other kind"). Until 2026-11-12 this item cited rule 19 alone, which says how the instance is written and leaves no fact out.
- **Left out:** "Data are temporally weighted to the ninth day, which is reflected in the file name." (notes)
  - **Rule:** Writing a classed triple, rule 24: "A verb or participle that says only what was done to the data ("corrected", "calibrated", "detrended", "binned", "mapped", "edited", "convert", "weighted") names no method". "the file name" names no particular file (rule 9).
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
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names" No file is named; "large" is a judgement (rule 5).
- **Left out:** "just" (notes, "contains just one data layer")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance"
- **Left out:** "entire" (notes, "covers the entire globe")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance"
- **Left out:** "BRDF/Albedo values for VIIRS band M4" COMPUTED_FROM "isotropic parameters" and "volumetric parameters", and FOR_CHANNEL "VIIRS band M4 (0.555 μm)" (notes)
  - **Rule:** Writing a classed triple, rule 21: "Leave out facts about other datasets, such as a variant of the record's dataset (the same data at another temporal resolution, spatial resolution, or version), or a product made from it." Its connection to the record's dataset is a ground truth triple: "BRDF/Albedo values for VIIRS band M4" COMPUTED_FROM the record's dataset (rule 24, *The record's dataset's own values*: "when the input is the record's dataset's own values, the input is the record's dataset"). Until 2026-11-12 its object was the Variable "BRDF geometric parameter for VIIRS band M4 (0.555 μm)". The band named inside the product's words (rule 17, *A name's facts*) is a fact of that product too (added to this item on 2026-11-01, the review of the second opinion's facts).
  - **May matter because:** it says the albedo needs all three parameters, that is, three of the family's products together.
  - **Question:** Q24.
- **Left out:** "used to derive" as a purpose of the parameter (notes)
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words." COMPUTED_FROM says it; and a use is not a purpose (rule 9: "What data have been used for, or can be used for, is a fact of the work that used them, not of the data").
- **Left out:** "Known Issues" (notes, the heading)
  - **Rule:** What counts as a fact, rule 3: "A heading inside a text field, a line of its own that only names the passage below it ("Known Issues", "BARREL Data Usage Policy"), is formatting too, and gives no ground truth triple."
- **Left out:** "known issues" as what the page is about (notes)
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance"
- **Left out:** "MODIS/VIIRS Land Quality Assessment website" (notes), as the page's name
  - **Rule:** Writing a classed triple, rule 20: "Write that one name is also known as another (ALSO_KNOWN_AS) only when the record gives the other name in words of its own"
  - **May matter because:** it is the page's name.
- **Left out:** "NIR" as another name of "near-infrared", and "DNB" of "VIIRS Day/Night Band" (notes)
  - **Rule:** Writing a classed triple, rule 21: "Leave out facts about other datasets, such as a variant of the record's dataset (the same data at another temporal resolution, spatial resolution, or version), or a product made from it." The bands are the family's, not this dataset's.
- **Left out:** what "Suomi National Polar-orbiting Partnership (Suomi NPP)" is (notes; the title writes "NPP")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what the Suomi National Polar-orbiting Partnership is. Its entity class, Platform, is written (FROM_PLATFORM "NASA/NOAA Suomi National Polar-orbiting Partnership (Suomi NPP)", and "Visible Infrared Imaging Radiometer Suite (VIIRS)" ABOARD it), by rule 1's *A name the record does not explain*.
  - The list: GCMD Platforms keywords (version 25.2), "Suomi-NPP", "Suomi National Polar-orbiting Partnership" (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/platforms?format=csv, checked on 2026-11-12).

## "BARREL 4G Rate Counter (RCNT) NaI Scintillator Diagnostics, Level 2, 4 s Data" (pool position 19, id 6f63dd10-376e-4d17-9156-f2155637e74d)

40 items, 17 that may matter.

- **Left out:** the launch stations and their places (notes, "with launches from two stations located in Antarctica: the British base located at Halley Bay on the Brunt Ice Shelf and the South African SANAE IV base", and "Later campaigns were undertaken in 2015 and 2016 from the Esrange Space Center located in Kiruna, Sweden")
  - **Rule:** What counts as a fact, rule 2: "or it waits on an expert's answer" (Q8 (c): whether a station or a space center is an Organization or a place).
  - **May matter because:** a search by launch site or region (Antarctica, Sweden) would need them.
  - **Question:** Q8 (c).
  - No clear would-be triple: whether a station is an Organization or a place decides its entity class and its predicates (LAUNCHED_FROM and LOCATED_IN for a place, none of them in the ground truth schema; BASED_IN "British", "South African" and "Sweden" for an Organization), so no row can be written in annotations/pending_triples.csv until Q8 (c) is answered.
- **Left out:** "South African" (notes, inside the name "South African National Antarctic Expedition") as a Country of its own
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names" The record names no country. The ground truth schema's Country is "a nation", "South African" is an adjective, the record never writes "South Africa", and an instance is the record's own words (Writing a classed triple, rule 11: "Don't paraphrase them"). Until 2026-11-12 this item cited rule 11's "A name stays whole", which keeps the name whole and leaves no fact out (rule 2, *A fact inside a name*); the record at pool position 25 now has "U.S. Government" BASED_IN "U.S.", where the name holds the country's own name. Until 2026-11-01 the ground truth had "South African National Antarctic Expedition" BASED_IN "South African" (the double check of batches 4 and 5, finding F19.1).
  - **May matter because:** it says where the expedition is based, which a search by country would need.
  - **Question:** Q8 (c), with the launch stations.
- **Left out:** "4G" (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"
  - **May matter because:** my reading, not checked: the balloon payload's code (campaign 4, payload G), which tells this dataset from its siblings and gives its campaign.
  - **Question:** Q6 (b).
- **Left out:** "NaI Scintillator" as an instrument of its own (title, "NaI Scintillator Diagnostics")
  - **Rule:** What counts as a fact, rule 1: "Never add what you know from elsewhere". The words are part of the Variable "NaI Scintillator Diagnostics" (HAS_VARIABLE), and the record names no scintillator otherwise; that one is an instrument would come from outside the record (decided on 2026-11-01, the review of the second opinion's facts). Until 2026-11-12 this item cited rule 11's "A name stays whole" first, which keeps the Variable's instance whole and leaves no fact out (rule 2, *A fact inside a name*).
- **Left out:** what "CDF" stands for (notes, "all BARREL CDF data products")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what CDF is. Its entity class, FileFormat, is written (the record's dataset HAS_FILE_FORMAT "CDF", with the source text "all BARREL CDF data products"; the record's dataset is one of these products by rule 1's *Membership by name*, as for HAS_VERSION "Version 10", and "all" makes the format each member's), by rule 1's *A name the record does not explain*. Until 2026-11-12 "CDF" gave no ground truth triple, since it is on no official NASA list as an instrument or a platform.
  - The reference: Wikidata, Common Data Format (Q1116060), also named "CDF", "file format family for multi-dimensional data", an instance of "file format family" (https://www.wikidata.org/wiki/Q1116060, checked on 2026-11-12). No official NASA list names it: the GCMD Instruments, Platforms and Providers keywords (version 25.2) have no entry for it.
- **Left out:** "diagnostic fields" as a thing of its own (notes)
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words." HAS_VARIABLE "NaI Scintillator Diagnostics" says it (rule 23).
- **Left out:** "was a multiple-balloon investigation" (notes)
  - **Rule:** What counts as a fact, rule 4: "A sentence that says what type of entity an instance refers to ("Kestrel is an imager") gives no ground truth triple: the instance's entity class says it"
  - **May matter because:** it says the mission used many balloons at once.
- **Left out:** "Mission of Opportunity" and "Selected" (notes)
  - **Rule:** What counts as a fact, rule 4: "the type is left out, and the belonging is a ground truth triple" ("BARREL" PART_OF "NASA Living with a Star"); "Selected" names no party (rule 1: "Never add what you know from elsewhere").
  - **May matter because:** it is NASA's funding category for the mission.
- **Left out:** "Each" (notes, "Each BARREL balloon")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance"
- **Left out:** "near latitudes close to either the antarctic and arctic circles" (notes)
  - **Rule:** What counts as a fact, rule 1, *Membership by name*: "A statement about the group as a whole is not written for it": "either … or". Which circle this payload flew near is not stated.
  - **May matter because:** a search by region (Antarctic, Arctic) would need it.
  - **Question:** Q24.
- **Left out:** "stratospheric altitudes" (notes)
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words." OBSERVED_AT_ALTITUDE "about 30 km" is the wording that says more (rule 23).
- **Left out:** "first balloon" (notes, "provided the first balloon measurements")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance"
  - **May matter because:** it says BARREL was the first to measure this from balloons.
- **Left out:** "while comprehensive in situ measurements of both plasma waves and energetic particles were available" (notes)
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names" Whose measurements is not said; "comprehensive" is a judgement (rule 5).
- **Left out:** "Also, the BARREL data has been used to characterize the spatial scale of precipitation at relativistic energies." (notes)
  - **Rule:** What counts as a fact, rule 9: "when the record doesn't name that work, the use gives no ground truth triple." No work that used the data is named; the statement is also about the BARREL data as a whole (rule 1, *Membership by name*).
  - **May matter because:** it says what the data are good for.
  - **Question:** Q24.
- **Left out:** "initially" and "Austral summer months of" (notes)
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance" ("initially"). "Austral summer months": rule 16 of *Writing a classed triple*, since the months, HAS_TIME_SPAN "January and February of 2013" and "of 2014", say when.
  - **May matter because:** "Austral summer" says why those months (the southern summer).
- **Left out:** "Thus, the BARREL balloon constellation constituted an evolving and slowly moving array able to study relativistic electron precipitation from the radiation belts." (notes)
  - **Rule:** What counts as a fact, rule 4: "A sentence that says what type of entity an instance refers to ("Kestrel is an imager") gives no ground truth triple: the instance's entity class says it" ("constituted an … array"); "able to study" is what it could do, not what it was meant for (HAS_PURPOSE "is meant to achieve").
  - **May matter because:** it says the balloons formed a moving array, which is how the mission measured spatial scales.
- **Left out:** "and other ground and space based instruments" (notes)
  - **Rule:** Writing a classed triple, rule 22: "An item that names no specific entity ("his team") gives no ground truth triple"
- **Left out:** "successively" (notes)
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance"
- **Left out:** "approximately 20 kg" as the mass of each balloon (notes, "over 50 small, approximately 20 kg, stratospheric balloons were successively launched")
  - **Rule:** What counts as a fact, rule 9: "An amount or a count per member gives no ground truth triple". The mass is each balloon's, and the sentence names the balloons only by a count ("over 50 … balloons"). The same rule leaves out "from 2 to 25 epochs each" in the record at pool position 12 and "a set of 3" in the record at pool position 25. The words stay in the count, which is written whole: "BARREL" HAS_NUMBER_OF "over 50 small, approximately 20 kg, stratospheric balloons" (rule 22 of *Writing a classed triple*, *Describing words joined by "and" or a comma*). Until 2026-11-12 the ground truth had "BARREL balloon" (Platform) HAS_MASS "approximately 20 kg" (Value).
  - **May matter because:** it is the mass of each balloon the mission flew.
- **Left out:** "The website creeated and hosted by A.J. Halford (see Information URL below) reports that: "By the end of the campaigns, there were over 90 researchers coordinating on a daily basis with the BARREL team working on 7 different satellite missions, 1 other balloon mission, and way too many ground based instruments to count."" (notes)
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names" The researchers are named only by a count, and "way too many" is a judgement (rule 5). The website itself is a ground truth triple since 2026-11-01 (the review of the second opinion's facts, judgment call D): the record's dataset DOCUMENTED_AT "website creeated and hosted by A.J. Halford" (Document), with DEVELOPED_BY_PARTY and PROVIDED_BY_PARTY "A.J. Halford" (Person), since rule 20 of *Writing a classed triple* says "A page or site the record names in words, without a web address, is a Document"; until then this item left it out too ("The website has no address in the text").
  - **May matter because:** it gives the mission's reach.
- **Left out:** "only" (notes, "launched only balloons")
  - **Rule:** What counts as a fact, rule 6: "A ground truth triple can't say "not"." "only" says nothing else was launched.
- **Left out:** "research using data collected on these flights is ongoing, so stay tuned for updates!" (notes)
  - **Rule:** What counts as a fact, rule 10: "Take out "latest", "current", "now", "then available", and words like them." ("ongoing"); "stay tuned" names nothing (rule 9).
- **Left out:** "All data and analysis software are freely available to the scientific community." (notes)
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words." For the data: HAS_ACCESS_RIGHTS "freely available to the public" says more. "analysis software": rule 9, no particular software is named.
- **Left out:** "primarily" (notes)
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance"
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
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the entity," The policy is the instance, AVAILABLE_AT its address.
- **Left out:** what "NASA" is (notes, "a NASA Living with a Star Mission of Opportunity")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what NASA is. Its entity class, Organization, is written ("NASA Living with a Star" PART_OF "NASA"), by rule 1's *A name the record does not explain*.
  - The reference: GCMD Providers keywords (version 25.2), the level "NASA" under "GOVERNMENT AGENCIES-U.S. FEDERAL AGENCIES", which holds NASA's centers and offices (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/providers?format=csv, checked on 2026-11-12).
- **Left out:** what "Earth" is (notes)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what Earth is. Its entity class, CelestialBody, is written (HAS_TARGET "Earth"), by rule 1's *A name the record does not explain*.
  - The reference: PDS4 context product urn:nasa:pds:context:target:planet.earth, "Earth", of type Planet (https://pds.nasa.gov/data/pds4/context-pds4/target/planet.earth_1.1.xml, checked on 2026-11-12).
- **Left out:** what "NASA Living with a Star" is (notes, "Selected as a NASA Living with a Star Mission of Opportunity")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what NASA Living with a Star is. Its entity class, Organization, is written (PART_OF "NASA"), by rule 1's *A name the record does not explain*. A program that an organization runs is an Organization, one of that organization's named parts, which the ground truth schema's Organization includes ("a named institution or one of its named parts, not a Mission"). Living with a Star is a program of NASA, and the program itself collects no data, so it is not a Mission.
  - The reference: Wikidata Q1705257, "Living With a Star", "scientific program of NASA to study the Sun-Earth system" (https://www.wikidata.org/wiki/Q1705257, checked on 2026-11-12).
- **Left out:** "2016 campaign" HAS_NUMBER_OF "eight flights" (notes, "The 2015 and 2016 campaigns were undertaken in coordination with" … "A total of eight flights occurred during August 2016.")
  - **Rule:** What counts as a fact, rule 1: "A fact that the record does not state may be written only when it follows from what the record states by one of the three tests below (Replacement, Comparison, Membership by name); nothing else, and no outside knowledge, adds such a fact. The list of tests is closed". The sentence gives the eight flights a month, August 2016, and names no campaign. That they are the flights of the 2016 campaign follows from this sentence and the sentences that name the campaign, by none of the three tests (*Replacement*, *Comparison*, *Membership by name*), as for the spectral densities of the record at pool position 16. The ground truth had this triple from 2026-11-01 to 2026-11-12 (docs/improvements.md, *Fourth round of rule fixes*).
  - **May matter because:** it is the number of flights of the 2016 campaign, as "Seven balloon launches" is for the campaign of August 2015.
- **Left out:** the 2013, the 2014 and the 2016 campaign PART_OF "BARREL" (notes, "For the 2013 and 2014 the balloon campaigns", "The 2015 and 2016 campaigns" … "Summing over the four BARREL campaigns")
  - **Rule:** What counts as a fact, rule 1: "A fact that the record does not state may be written only when it follows from what the record states by one of the three tests below (Replacement, Comparison, Membership by name); nothing else, and no outside knowledge, adds such a fact. The list of tests is closed". The record names one campaign with the mission's name ("August 2015 BARREL campaign" PART_OF "BARREL", rule 2's *A fact inside a name*). No passage states that the 2013, the 2014 or the 2016 campaign is a campaign of BARREL: it follows from counting the campaigns the record describes up to "the four BARREL campaigns", by none of the three tests (*Replacement*, *Comparison*, *Membership by name*). The ground truth had the three triples until 2026-11-12 (docs/improvements.md, *Fourth round of rule fixes*).
  - **May matter because:** without them no ground truth triple connects the three campaigns to the mission.

## "Merged Catalog of Reflection Nebulae" (pool position 20, id a2d5781a-3b10-4bac-8993-295f235db4e4)

A held-out record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. 7 items, 4 that may matter.

- **Left out:** "Merged" (title) and "have been merged" (notes, "Several catalogs of reflection nebulae have been merged to create a uniform catalog") as a method
  - **Rule:** Writing a classed triple, rule 24: "A verb or participle that says only what was done to the data ("corrected", "calibrated", "detrended", "binned", "mapped", "edited", "convert", "weighted") names no method"
  - **May matter because:** it says how the catalog was made: by merging several catalogs.
- **Left out:** "Several catalogs of reflection nebulae" as the input of the catalog (notes)
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names"
  - The record names none of the catalogs, so COMPUTED_FROM has no object it names. The catalog's named input is written: COMPUTED_FROM "table1.dat".
  - **May matter because:** a search for the catalogs this one merges would need them.
- **Left out:** "uniform" (notes, "a uniform catalog of 913 objects")
  - **Rule:** What counts as a fact, rule 4: "A sentence that says what type of entity an instance refers to ("Kestrel is an imager") gives no ground truth triple: the instance's entity class says it"
  - "a uniform catalog" says what kind of catalog the record's dataset is; its entity class, Dataset, and HAS_NUMBER_OF "913 objects" are written.
- **Left out:** "The HEASARC has endeavored to render all identifications of the nebulae in the various catalogs according to the styles recommended by the Dictionary of Nomenclature of Celestial Objects." (notes)
  - **Rule:** What counts as a fact, rule 7: "Not facts the record doesn't assert as true: uncertain ones, and ones it requires, requests or recommends."
  - "has endeavored to render" says that the HEASARC tried, and does not assert that every identification follows those styles; "recommended" is the Dictionary's recommendation. "the various catalogs" names no catalog (rule 9).
  - **May matter because:** it says which naming styles the identifications follow.
- **Left out:** "IRAS" (notes, inside "identifications with IRAS point sources")
  - **Rule:** What counts as a fact, rule 2: "When the naming states more than one predicate, or none, the name's words give no ground truth triple" (*A fact inside a name*)
  - "IRAS" stands inside "IRAS point sources", within the Variable "identifications with IRAS point sources" (HAS_VARIABLE), with no words that say how the sources and the craft are related. IRAS is a Platform by rule 1's *A name the record does not explain*: the GCMD Platforms keywords (version 25.2) have "IRAS", "Infrared Astronomy Satellite", under Solar/Space Observation Satellites (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/platforms?format=csv, checked on 2026-11-13); the GCMD Instruments keywords' "IRAS", an InfraRed Atmospheric Sounder, does not fit a record about nebulae. Naming identifications or sources with a craft's name states no predicate of the ground truth schema: FROM_PLATFORM is "was collected from this Platform", which is not said of identifications.
  - **May matter because:** it says which survey the nebulae are matched with.
- **Left out:** what "HEASARC" stands for (notes, "The HEASARC has endeavored", "This table was created by the HEASARC" and "a service provided by NASA HEASARC")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what HEASARC is. Its entity class, Organization, is written (DEVELOPED_BY_PARTY and PROVIDED_BY_PARTY "NASA HEASARC", and "NASA HEASARC" PART_OF "NASA"), by rule 1's *A name the record does not explain*.
  - The reference: Wikidata, High Energy Astrophysics Science Archive Research Center (Q130537792), also named "HEASARC", an instance of "research center" and of "archive" (https://www.wikidata.org/wiki/Q130537792, checked on 2026-11-13). No official NASA list names it: the GCMD Providers keywords (version 25.2) have no entry for it.
- **Left out:** what "NASA" is (notes, "NASA HEASARC")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what NASA is. Its entity class, Organization, is written ("NASA HEASARC" PART_OF "NASA"), by rule 1's *A name the record does not explain*.
  - The reference: GCMD Providers keywords (version 25.2), the level "NASA" under "GOVERNMENT AGENCIES-U.S. FEDERAL AGENCIES", which holds NASA's centers and offices (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/providers?format=csv, checked on 2026-11-13).

## "CH1-ORB MOON M3 2 L0 RAW NEAR-IR SPECTRAL IMAGES V1.0" (pool position 21, id 264a9b23-9a86-46a7-ab61-9661230ea667)

4 items, 1 that may matter.

- **Left out:** what "CH1-ORB" stands for (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what CH1-ORB is. Its entity class, Platform, is written (FROM_PLATFORM "CH1-ORB"), by rule 1's *A name the record does not explain*. Until 2026-11-12 "CH1-ORB" gave no ground truth triple, and this item said that it was on no list as written.
  - The reference: PDS4 context product urn:isro:isda:context:instrument_host:spacecraft.ch1_cho, "Chandrayaan-1 Orbiter", of type Spacecraft, which keeps its earlier identifier urn:nasa:pds:context:instrument_host:spacecraft.ch1-orb as another title; the record names the "Chandrayaan-1 mission" (https://pds.nasa.gov/data/pds4/context-pds4/instrument_host/spacecraft.ch1_cho_1.1.xml, checked on 2026-11-12).
  - **Question:** Q6 (b).
- **Left out:** "2" (title, "M3 2 L0")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"; a bare number is not "L" or "Level" followed by a number.
  - **May matter because:** in PDS3 naming it is most likely the CODMAC level (CODMAC 2 = NASA Level 0, which agrees with "L0"; my reading, not checked for this data set).
  - **Question:** Q6 (b).
- **Left out:** "instrument" (notes, "Moon Mineralogy Mapper (M3) instrument") and "mission" (notes, "Chandrayaan-1 mission")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the entity,"
- **Left out:** what "Moon" is (title, "MOON", and notes, "mission to the Moon")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what Moon is. Its entity class, CelestialBody, is written (HAS_TARGET "Moon"), by rule 1's *A name the record does not explain*.
  - The reference: PDS4 context product urn:nasa:pds:context:target:satellite.earth.moon, "Moon", of type Satellite (https://pds.nasa.gov/data/pds4/context-pds4/target/satellite.earth.moon_1.1.xml, checked on 2026-11-12).

## "Flight Data For Tail 655" (pool position 22, id 967275c7-aa2d-4b08-a9db-aff5cf6b7802)

4 items, 2 that may matter.

- **Left out:** "Tail 655" (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what Tail 655 is, and no reference of rule 1's *A name the record does not explain* names it: the GCMD Platforms keywords (version 25.1, checked on 2026-11-01; version 25.2, checked on 2026-11-12) and Wikidata (checked on 2026-11-12) have no entry for it. Until 2026-11-01 the ground truth had FROM_PLATFORM "Tail 655" (Platform), read from the title; the record now names no platform, as the record at pool position 15 names none for "HelioWeb" (the double check of batches 4 and 5, finding F22.1).
  - **May matter because:** my reading, not checked: an aircraft's tail number, so the aircraft the data were recorded on; a search by aircraft would need it.
- **Left out:** "individual flight" (notes, "individual flight recorded data"), that each file holds one flight
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names" No flight is named.
  - **May matter because:** it says how the files are cut.
- **Left out:** "Flight Data" (title) as a fact
  - **Rule:** What counts as a fact, rule 4: "A sentence that says what type of entity an instance refers to ("Kestrel is an imager") gives no ground truth triple: the instance's entity class says it". The flights are not named (rule 9).
- **Left out:** "each with a data structure" (notes), the structure as a thing of its own
  - **Rule:** What counts as a fact, rule 9: "is written for the entity the group belongs to only when it stays true of that entity: what it holds". The 186 parameters are named only by a count, so the structure's contents are written as the dataset's (HAS_VARIABLE "sensor recordings"; HAS_ANCILLARY_DATA "sampling rate", "units", "parameter description", "parameter ID").

## "SOLVE I Ground Site Data" (pool position 23, id ccbc2b1c-cfa2-4867-9981-a845b91d90ab)

A held-out record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. 17 items, 5 that may matter.

- **Left out:** "ground site" (title, "Ground Site Data", and notes, "the ground site data")
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names"
  - No ground site is named, so no FROM_PLATFORM triple is written.
  - **May matter because:** it says the data were collected on the ground, at sites.
- **Left out:** "campaign", "multi-program effort" and "experiment" (notes, "The SOLVE campaign was a NASA multi-program effort", "SOLVE was a two-phase experiment" and "this validation experiment")
  - **Rule:** What counts as a fact, rule 4: "A sentence that says what type of entity an instance refers to ("Kestrel is an imager") gives no ground truth triple: the instance's entity class says it"
  - They say what kind of thing SOLVE is. Its entity class is Mission ("SAGE III Ozone Loss and Validation Experiment (SOLVE)"), whose definition is "a named effort to collect data, from space, from the air, on water or on the ground", the record's own word "effort"; the ground truth schema's Campaign is "carried out as part of a Mission", which the record does not say of SOLVE. "a NASA multi-program effort of" also names what SOLVE belongs to, written as PART_OF (rule 4: "the kind is left out, and the belonging is a ground truth triple"). The record also writes "SOLVE" for its first phase ("the first phase, SOLVE", and "SOLVE featuring 17 total flights" beside "SOLVE II featuring 11 flights"); those passages are written for the phase, "SOLVE I" (rule 23 of *Writing a classed triple*: the title's wording says more).
- **Left out:** "Atmospheric Effects of Aviation Project (AEAP)" (notes)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what AEAP is. Its kind word, "Project", fits more than one entity class (a named part of an organization, an Organization, or a named effort to collect data, a Mission), and no reference of rule 1's *A name the record does not explain* names it: the GCMD Providers, Platforms and Instruments keywords (version 25.2) and Wikidata have no entry for it (checked on 2026-11-13). So it gives no PART_OF triple, as the two programs beside it do.
  - **May matter because:** it is one of the programs SOLVE belonged to.
- **Left out:** "Earth Observing System (EOS)" (notes)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what the Earth Observing System is, and its kind word, "System", fits no single entity class, as in the record "HIRDLS/Aura Level 3 Geopotential Height 1deg Lat Zonal Fourier Coefficients V007 (H3ZFCGPH)". Wikidata's Earth Observing System (Q1277644), also named "EOS", is a "program of NASA comprising a series of artificial satellite missions and scientific instruments in Earth orbit", an instance of "science project", a kind that fits both Mission and Organization (https://www.wikidata.org/wiki/Q1277644, checked on 2026-11-13). So it gives no PART_OF triple, and its "Earth" gives no HAS_TARGET triple.
  - **May matter because:** it is one of the programs SOLVE belonged to.
- **Left out:** "primary" and "major" (notes, "SOLVE’s primary objective" and "The major goal of SAGE III")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance"
- **Left out:** "during the winter" (notes, "SOLVE took place in the Arctic high-latitude region during the winter")
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names"
  - "the winter" names no particular winter; the phases' periods are written (HAS_TIME_SPAN).
  - **May matter because:** it says in which season the measurements were made.
- **Left out:** "The polar ozone depletion processes cause by human-produced chlorine and bromine are most active in mid-to-late winter and early spring in the high Arctic." (notes)
  - **Rule:** Writing a classed triple, rule 21: "A statement that only explains a concept (what a term means, how a quantity behaves in general, which methods are in common use) and is about nothing so connected gives no ground truth triple"
  - It explains when the processes are most active in general, and is about nothing connected to the record's id.
- **Left out:** "balloon platforms" and "ground-based instruments" (notes, "SOLVE also utilized balloon platforms, ground-based instruments, and collaborations with")
  - **Rule:** Writing a classed triple, rule 22: "An item that names no specific entity ("his team") gives no ground truth triple"
  - **May matter because:** they say SOLVE also measured from balloons and from the ground.
- **Left out:** "to achieve the mission objectives" (notes)
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words."
  - The objectives are SOLVE's purposes, written from "SOLVE’s primary objective was" (HAS_PURPOSE).
- **Left out:** "a variety of atmospheric data", "among other atmospheric data" and "among the different aircrafts" (notes)
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names"
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
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what NASA is. Its entity class, Organization, is written ("SAGE III Ozone Loss and Validation Experiment (SOLVE)" PART_OF "NASA", "NASA’s Earth Science Enterprise (ESE)" PART_OF "NASA", and DEPLOYED_BY_PARTY "NASA"), by rule 1's *A name the record does not explain*.
  - The reference: GCMD Providers keywords (version 25.2), the level "NASA" under "GOVERNMENT AGENCIES-U.S. FEDERAL AGENCIES", which holds NASA's centers and offices (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/providers?format=csv, checked on 2026-11-13).
- **Left out:** what "SAGE III" is (notes, "Stratospheric Aerosol and Gas Experiment (SAGE) III satellite measurements" and "The major goal of SAGE III")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record spells out the abbreviation but never says what kind of thing SAGE III is: "Experiment" fits more than one entity class, and in "SAGE III satellite measurements" I read "satellite" as a word of the measurements, not a type word of SAGE III. Its entity class, Instrument, is written ("Stratospheric Aerosol and Gas Experiment (SAGE) III" HAS_PURPOSE "quantitatively assess ozone loss at high latitudes"), by rule 1's *A name the record does not explain*.
  - The list: GCMD Instruments keywords (version 25.2), "SAGE III", "Stratospheric Aerosol and Gas Experiment III", under Spectrometers (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/instruments?format=csv, checked on 2026-11-13).
- **Left out:** what "Earth" is (notes, inside the name "NASA’s Earth Science Enterprise (ESE)")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what Earth is. Its entity class, CelestialBody, is written ("NASA’s Earth Science Enterprise (ESE)" HAS_TARGET "Earth", by rule 2's *A fact inside a name*), by rule 1's *A name the record does not explain*.
  - The reference: PDS4 context product urn:nasa:pds:context:target:planet.earth, "Earth", of type Planet (https://pds.nasa.gov/data/pds4/context-pds4/target/planet.earth_1.1.xml, checked on 2026-11-13).

## "HIRDLS/Aura Level 3 Geopotential Height 1deg Lat Zonal Fourier Coefficients V007 (H3ZFCGPH)" (pool position 24, id 77a0cb5f-7d69-4f13-aeb1-ce1378d7f1a9)

9 items, 2 that may matter.

- **Left out:** what "HIRDLS" stands for (title, and notes "HIRDLS data", "HIRDLS Level 2 profiles")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for". Its entity class, Instrument, is written (ACQUIRED_BY_INSTRUMENT "HIRDLS", twice), by rule 1's *A name the record does not explain*.
  - **May matter because:** it is the instrument's name, the main search key.
  - The list: GCMD Instruments keywords (version 25.1), "HIRDLS", "High-Resolution Dynamics Limb Sounder"; the CMR record of H3ZFCGPH version 007 lists it under the platform Aura (checked on 2026-10-31).
- **Left out:** "entire" (notes, twice: "the entire mission")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance"
- **Left out:** "mission" (notes, "the entire mission (~3 years) of HIRDLS data"), as FROM_MISSION
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names" No mission is named.
- **Left out:** "may be used to compute values at any longitude" (notes)
  - **Rule:** What counts as a fact, rule 7: "Not facts the record doesn't assert as true: uncertain ones, and ones it requires, requests or recommends." ("may"); and a use is a fact of the work that used the data (rule 9).
  - **May matter because:** it says what the coefficients are for.
- **Left out:** "approach" (notes, "a Kalman filter approach")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the entity,"
- **Left out:** "Earth" (notes, "the version 5 Hierarchical Data Format for the Earth Observing System (HDF-EOS5)")
  - **Rule:** What counts as a fact, rule 2: "When the naming states more than one predicate, or none, the name's words give no ground truth triple" (*A fact inside a name*). The name is a file format's, written whole (HAS_FILE_FORMAT; rule 11 of *Writing a classed triple*). "Earth" does not qualify the format: it stands inside "Earth Observing System", the name of another thing, which the format's name joins to the format by "for". A file format is not about Earth (HAS_TARGET is "is about, or studies, this CelestialBody"), so the format's name states no predicate between the format and Earth. The fact that the inner name states, that the Earth Observing System observes Earth, would need "Earth Observing System" as an instance with an entity class. The record never says what it is, and its kind word "System" fits the definition of no single entity class of the ground truth schema, so its own words do not explain it (rule 1: a name "is explained by the record's own words, since the kind word inside the name is the record's own word, when that word fits the definition of exactly one entity class"). No public reference was looked up for it (rule 1, *A name the record does not explain*). So "Earth" gives no ground truth triple. In "Earth Observation Satellites (EOS)" (the record at pool position 4), "Earth" qualifies the satellites, which are the instance itself, so that name states HAS_TARGET "Earth" (rule 2, *A fact inside a name*; rule 19 of *Writing a classed triple*, a target body). The two cases differ in which thing the word qualifies: the instance, or another thing named inside it (decided on 2026-11-13).
- **Left out:** "separate" (notes, "separate data fields")
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words." Three HAS_VARIABLE triples already say there are three fields.
- **Left out:** the notes' quoted name "HIRDLS/Aura Level 3 Geopotential Height Zonal Fourier Coefficients" as another name of the dataset
  - **Rule:** Writing a classed triple, rule 20: "Write that one name is also known as another (ALSO_KNOWN_AS) only when the record gives the other name in words of its own"; the thing the title names is always written as its title (rule 23).
- **Left out:** what "Aura" is (title, "HIRDLS/Aura")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what Aura is. Its entity class, Platform, is written (FROM_PLATFORM "Aura"), by rule 1's *A name the record does not explain*.
  - The list: GCMD Platforms keywords (version 25.2), "Aura" (checked on 2026-11-11).

## "OPERA Dynamic Surface Water Extent from Sentinel-1 (Version 1)" (pool position 25, id ed2cea26-ed6c-4138-be69-3d32d4ce4858)

14 items, 6 that may matter.

- **Left out:** "irrespective of cloud conditions and daylight illumination" (notes)
  - **Rule:** What counts as a fact, rule 6: "A ground truth triple can't say "not"." ("irrespective of" means "not affected by").
  - **May matter because:** all-weather, day-and-night mapping is a reason to choose a radar product.
- **Left out:** "that often pose challenges to optical sensors" (notes)
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names" "optical sensors" names no sensor.
- **Left out:** "Forward" (notes, "Forward production … began")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance"
  - **May matter because:** forward processing is new acquisitions, as against reprocessing of older ones, so data from before Sept 2024 may exist.
- **Left out:** "data record" (notes, "the DSWx-S1 data record")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the entity,"
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
  - **Rule:** What counts as a fact, rule 4: "A sentence that says what type of entity an instance refers to ("Kestrel is an imager") gives no ground truth triple: the instance's entity class says it"
- **Left out:** what "Sentinel-1" is (title, and notes, "Sentinel-1 radar observations")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what Sentinel-1 is. Its entity class, Platform, is written (FROM_PLATFORM "Sentinel-1"), by rule 1's *A name the record does not explain*.
  - The list: GCMD Platforms keywords (version 25.2), "Sentinel-1" (checked on 2026-11-11).
- **Left out:** "associated" (notes, "water classification and associated confidence layers")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance". "associated" says only how the fact HAS_ANCILLARY_DATA "confidence" holds, as in the record at pool position 7.
- **Left out:** "OPERA" as the developer of the dataset (title; notes, "Dynamic OPERA Surface Water Extent" and "The OPERA DSWx-S1 product")
  - **Rule:** What counts as a fact, rule 2: "When the naming states more than one predicate, or none, the name's words give no ground truth triple" (*A fact inside a name*). The title and the product's name hold the word "OPERA", and no passage says that OPERA developed, produced or provides the dataset. An organization's name in a dataset's name could mean that the organization developed the dataset, provides it or sponsored it, and naming does not settle which: "A relationship that naming does not state (that one thing funded, developed, provided or sponsored the other) is never read from a name". Until 2026-11-12 the ground truth had the record's dataset DEVELOPED_BY_PARTY "OPERA" (Organization), with the source text "OPERA" (found by both audits of 2026-11-12).
  - The six ground truth triples about OPERA and the Satellite Needs Working Group stay, since the record states each of them: "OPERA" INFORMED_BY "Satellite Needs Working Group (SNWG)", the group's PART_OF "U.S. Government", its two HAS_PURPOSE and its HAS_TARGET "Earth", and "U.S. Government" BASED_IN "U.S.". No chain of ground truth triples links them to the record's id any more, and the record states no fact that would (guidelines, *Finishing a record*: "add that fact only if the record states it"). The same holds for the four ground truth triples about "Peter Minnett" in the record at pool position 4.
  - **May matter because:** my reading, not checked: OPERA is the project that makes the product, so a search by project would need it.
- **Left out:** what "OPERA" stands for (title; notes, "OPERA was informed by the Satellite Needs Working Group (SNWG)")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what OPERA is. Its entity class, Organization, is written ("OPERA" INFORMED_BY "Satellite Needs Working Group (SNWG)"), by rule 1's *A name the record does not explain*.
  - The reference: GCMD Providers keywords (version 25.2), "NASA/JPL/OPERA", "Observational Products for End-Users from Remote Sensing Analysis, Jet Propulsion Laboratory, NASA" (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/providers?format=csv, checked on 2026-11-12).
- **Left out:** what "Earth" is (notes)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what Earth is. Its entity class, CelestialBody, is written (HAS_TARGET "Earth"), by rule 1's *A name the record does not explain*.
  - The reference: PDS4 context product urn:nasa:pds:context:target:planet.earth, "Earth", of type Planet (https://pds.nasa.gov/data/pds4/context-pds4/target/planet.earth_1.1.xml, checked on 2026-11-12).
- **Left out:** what "U.S." is (notes, "an interagency effort of the U.S. Government")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what U.S. is. Its entity class, Country, is written (BASED_IN "U.S."), by rule 1's *A name the record does not explain*.
  - The reference: Wikidata, United States (Q30), also named "the U.S.", "country located primarily in North America", an instance of "country" and of "sovereign state" (https://www.wikidata.org/wiki/Q30, checked on 2026-11-13). Rule 1's official NASA lists (the GCMD Instruments, Platforms and Providers keywords, and the PDS4 context products) are not lists of countries, and they were not searched for it.

## "VIIRS/NPP BRDF/Albedo NBAR at Solar Noon Band M4 Daily L3 Global 30ArcSec CMG V002" (pool position 26, id b5ef7c20-8253-4c10-91bb-a24f4d26147e)

A held-out record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. 14 items, 5 that may matter.

- **Left out:** "NASA/NOAA" as a fact of its own (notes)
  - **Rule:** What counts as a fact, rule 1: "Only what the record states." The words name the two agencies and the platform, and do not say how they are related (whether the agencies built the platform, launched it or operate it), so they state no fact (rule 2, *A fact inside a name*: "When the naming states more than one predicate, or none, the name's words give no ground truth triple"). "NASA/NOAA" stays in the platform's instance, "NASA/NOAA Suomi National Polar-orbiting Partnership (Suomi NPP)", as in the record "VIIRS/NPP BRDF/Albedo Parameter 3 Band M4 Daily L3 Global 30 ArcSec CMG V002".
- **Left out:** "Data are temporally weighted to the ninth day, which is reflected in the file name." (notes)
  - **Rule:** Writing a classed triple, rule 24: "A verb or participle that says only what was done to the data ("corrected", "calibrated", "detrended", "binned", "mapped", "edited", "convert", "weighted") names no method"
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
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names" No file is named; "large" is a judgement (rule 5).
- **Left out:** "just" (notes, "contains just one data layer")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance"
- **Left out:** "entire" (notes, "covers the entire globe")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance"
- **Left out:** "Known Issues" (notes, the heading)
  - **Rule:** What counts as a fact, rule 3: "A heading inside a text field, a line of its own that only names the passage below it ("Known Issues", "BARREL Data Usage Policy"), is formatting too, and gives no ground truth triple."
- **Left out:** "known issues" as what the page is about (notes, "For complete information about known issues please refer to")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance"
- **Left out:** "MODIS/VIIRS Land Quality Assessment website" (notes), as the page's name
  - **Rule:** Writing a classed triple, rule 20: "Write that one name is also known as another (ALSO_KNOWN_AS) only when the record gives the other name in words of its own"
  - **May matter because:** it is the page's name, by which a person would look for it.
- **Left out:** "BRDF/Albedo" (title) and "Bidirectional Reflectance Distribution Function (BRDF) and Albedo" (notes) as what the dataset holds
  - **Rule:** What counts as a fact, rule 1, *Membership by name*: "A statement about the group as a whole is not written for it"
  - The words name the product suite the dataset belongs to ("the VNP43D BRDF/Albedo product suite"), not what this dataset holds: the notes say it is "the NBAR for VIIRS band M4 (0.555 μm)" (HAS_VARIABLE). The record "VIIRS/NPP BRDF/Albedo Parameter 3 Band M4 Daily L3 Global 30 ArcSec CMG V002" writes no ground truth triple from the same words.
- **Left out:** "at Solar Noon" (title)
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words."
  - The notes say it with words of their own: "NBAR algorithm" HAS_PURPOSE "model the values as if they were collected from a nadir view at local solar noon". The values are modelled for solar noon, not observed then, so no OBSERVED_AT_TIME_OF_DAY triple is written (rule 19 of *Writing a classed triple*, *What stays in the instance*).
- **Left out:** what "Suomi National Polar-orbiting Partnership (Suomi NPP)" is (notes; the title writes "NPP")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what the Suomi National Polar-orbiting Partnership is. Its entity class, Platform, is written (FROM_PLATFORM "NASA/NOAA Suomi National Polar-orbiting Partnership (Suomi NPP)", and "Visible Infrared Imaging Radiometer Suite (VIIRS)" ABOARD it), by rule 1's *A name the record does not explain*.
  - The list: GCMD Platforms keywords (version 25.2), "Suomi-NPP", "Suomi National Polar-orbiting Partnership" (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/platforms?format=csv, checked on 2026-11-13).

## "STEREO-A/SECCHI/HI-1 FITS data" (pool position 27, id 4b4681f4-215b-499c-864f-6f405743c775)

A tuning record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. 9 items, 2 that may matter.

- **Left out:** what "STEREO-A" is (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what STEREO-A is. Its entity class, Platform, is written (FROM_PLATFORM "STEREO-A"), by rule 1's *A name the record does not explain*.
  - The list: GCMD Platforms keywords (version 25.2), "STEREO A", under Solar/Space Observation Satellites (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/platforms?format=csv, checked on 2026-11-13); the record's "STEREO-A" differs from it only in a hyphen, which rule 23 of *Writing a classed triple* counts as the same wording.
- **Left out:** "telescope", "instrument suite" and "mission" (notes, "The Heliospheric Imager-1 (HI-1) telescope", "the Sun Earth Connection Coronal and Heliospheric Investigations (SECCHI) instrument suite" and "the NASA STEREO mission")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the entity,"
  - The type words are the record's own words for the entity classes written: HI-1 and SECCHI are Instruments, and STEREO is a Mission. The GCMD Instruments keywords (version 25.2) also have "SECCHI", under Ultraviolet Instruments (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/instruments?format=csv, checked on 2026-11-13).
- **Left out:** "are identical suites of remote sensing instruments" (notes, "The SECCHI on the two STEREO spacecraft are identical suites of remote sensing instruments")
  - **Rule:** What counts as a fact, rule 4: "A sentence that says what type of entity an instance refers to ("Kestrel is an imager") gives no ground truth triple: the instance's entity class says it"
  - **May matter because:** it says that both STEREO spacecraft carry the same suite.
  - "suites of instruments" says what kind of thing SECCHI is, which its entity class, Instrument, already says. "remote sensing" names the way it measures, written as USES_TECHNIQUE "remote sensing", as "Radio Science" is in the record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0". "identical" compares the suites on the two craft, which the record does not tell apart by name (rule 9: "A ground truth triple needs a subject and an object the record names.").
- **Left out:** "Heliospheric" and "Coronal" (notes, inside the names "Heliospheric Imager-1 (HI-1)" and "Sun Earth Connection Coronal and Heliospheric Investigations (SECCHI)")
  - **Rule:** What counts as a fact, rule 2: "Rule 1 (only what the record states) decides what a name's words state, as it does for all other words."
  - **May matter because:** they say that SECCHI observes the Sun's corona as well as the heliosphere.
  - Both are adjectives, and no reference names a body by them. The heliosphere is written from the record's own sentence, "The HI-1 telescope observes the inner heliosphere" (HAS_TARGET "inner heliosphere").
- **Left out:** what "NASA" is (notes, "the NASA STEREO mission")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what NASA is. Its entity class, Organization, is written ("STEREO" PART_OF "NASA"), by rule 1's *A name the record does not explain*.
  - "the NASA STEREO mission" is read as rule 4's "Selected as a NASA Living with a Star Mission of Opportunity": the phrase names the kind of thing STEREO is ("mission") and what it belongs to ("NASA"), so the mission is written "STEREO".
  - The reference: GCMD Providers keywords (version 25.2), the level "NASA" under "GOVERNMENT AGENCIES-U.S. FEDERAL AGENCIES", which holds NASA's centers and offices (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/providers?format=csv, checked on 2026-11-13).
- **Left out:** what "Sun" is (notes, "at the Sun", and inside the name "Sun Earth Connection Coronal and Heliospheric Investigations (SECCHI)")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what the Sun is. Its entity class, CelestialBody, is written (HAS_TARGET "Sun"), by rule 1's *A name the record does not explain*.
  - The reference: PDS4 context product urn:nasa:pds:context:target:star.sun, "Sun", of type Star (https://pds.nasa.gov/data/pds4/context-pds4/target/star.sun_1.1.xml, checked on 2026-11-13).
- **Left out:** what "Earth" is (notes, inside the name "Sun Earth Connection Coronal and Heliospheric Investigations (SECCHI)")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what Earth is. Its entity class, CelestialBody, is written (SECCHI HAS_TARGET "Earth", by rule 2's *A fact inside a name*), by rule 1's *A name the record does not explain*.
  - The reference: PDS4 context product urn:nasa:pds:context:target:planet.earth, "Earth", of type Planet (https://pds.nasa.gov/data/pds4/context-pds4/target/planet.earth_1.4.xml, checked on 2026-11-13).
- **Left out:** what "FITS" stands for (title, "HI-1 FITS data")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what FITS is. Its entity class, FileFormat, is written (HAS_FILE_FORMAT "FITS"), by rule 1's *A name the record does not explain*.
  - The reference: Wikidata, Flexible Image Transport System (Q1428303), also named "FITS", an instance of "file format" (https://www.wikidata.org/wiki/Q1428303, checked on 2026-11-13). No official NASA list names it: the GCMD Instruments, Platforms and Providers keywords (version 25.2) have no entry for it.
- **Left out:** what "heliosphere" is (notes, "observes the inner heliosphere")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what the heliosphere is. Its entity class, CelestialBody, is written ("Heliospheric Imager-1 (HI-1)" HAS_TARGET "inner heliosphere"), by rule 1's *A name the record does not explain*; "inner" stays in the instance (rule 19 of *Writing a classed triple*, *What stays in the instance*).
  - The reference: Wikidata, heliosphere (Q131687), "region of space dominated by the Sun", an instance of "stellar-wind bubble", which is a subclass of "nebula" and of "zone" (https://www.wikidata.org/wiki/Q131687, checked on 2026-11-13). A nebula is a natural object in space (CelestialBody); "zone" alone fits no entity class, since SpatialExtent is an area the data cover, so CelestialBody is the one entity class that fits. No official NASA list names it.

## "STEREO-B SWAVES One minute averages of the high (hfr) frequency receiver data." (pool position 28, id ba80e9b9-ff1a-4484-a6d5-78a086d66f2f)

A tuning record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. 7 items, 3 that may matter.

- **Left out:** what "STEREO-B" is (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what STEREO-B is. Its entity class, Platform, is written (FROM_PLATFORM "STEREO-B"), by rule 1's *A name the record does not explain*.
  - The list: GCMD Platforms keywords (version 25.2), "STEREO B", under Solar/Space Observation Satellites (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/platforms?format=csv, checked on 2026-11-13); "STEREO-B" differs from it only in a hyphen (rule 23 of *Writing a classed triple*).
- **Left out:** what "SWAVES" stands for (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what SWAVES is. Its entity class, Instrument, is written (ACQUIRED_BY_INSTRUMENT "SWAVES"), by rule 1's *A name the record does not explain*.
  - The list: GCMD Instruments keywords (version 25.2), "SWAVES", "STEREO WAVES", under Radio Wave Detectors (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/instruments?format=csv, checked on 2026-11-13).
- **Left out:** "STEREO" and "two" (notes, "The two STEREO radio receivers")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included"
  - **May matter because:** it says how many such receivers there are.
  - The record never says what STEREO is, and the GCMD Platforms keywords (version 25.2) have "STEREO" only as the name of the group that holds the two craft "STEREO A" and "STEREO B", a kind that fits no single entity class (a Platform is one craft, and a Mission is an effort, not a group of craft). So no ground truth triple has "STEREO" as an instance; the receivers are written whole, "STEREO radio receivers" (rule 11 of *Writing a classed triple*), and the count "two" has no subject to be written for.
- **Left out:** "One receiver makes high time resolution measurements at 50 MHz." (notes)
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names"
  - **May matter because:** it gives one receiver's frequency and its high time resolution.
  - "One receiver" names no receiver: the record uses "receiver" for every receiver it describes, and gives this one no words of its own that tell it apart, unlike the "10-40 kHz receiver" of the sentence before.
- **Left out:** "simultaneous" (notes, "Time Domain Samplers make simultaneous wideband waveform measurements")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance"
  - MEASURES "wideband waveform" is written; "simultaneous" says only how the measurements are made.
- **Left out:** "Antenna systems include three mutually orthogonal 6-meter monopoles." (notes)
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names"
  - **May matter because:** it says how the instruments sense the waves: three orthogonal 6-meter monopoles.
  - "Antenna systems" names no system, and the record does not say which instrument they belong to.
- **Left out:** what "Rs" stands for (notes, "about 1 Rs to 1 AU")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"
  - The value is written as the record writes it, HAS_SPATIAL_COVERAGE "about 1 Rs to 1 AU" (rule 18 of *Writing a classed triple*); what "Rs" stands for is not written.

## "MARS EXPRESS MARS MRS 1/2/3 EXTENDED MISSION 8 4193 V1.0" (pool position 29, id 6e6951d6-8ffd-4923-9b12-39d44ce6814d)

A held-out record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. 6 items, 2 that may matter.

- **Left out:** "1/2/3" (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"
  - **May matter because:** in the record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" the same place in the title was checked to hold the processing levels (its item); not checked for this record.
  - **Question:** Q6 (b).
- **Left out:** "4193" (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"
  - **May matter because:** it tells this dataset from its siblings, as "1149" does in the record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (its item); not checked for this record.
  - **Question:** Q6 (b).
- **Left out:** "phase" (notes, "the extended mission phase")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the entity,"
  - The phase is written in the title's wording, "EXTENDED MISSION 8", the wording that says more (rule 23).
- **Left out:** what "Mars Express" is (title, "MARS EXPRESS", and notes, "a Mars Express Radio Science data set")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what Mars Express is. The title's first word is the instrument host, a craft: FROM_PLATFORM "Mars Express" (Platform). The notes' "a Mars Express Radio Science data set" names the mission, as "a Rosetta Radio Science data set" does in the record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0": FROM_MISSION "Mars Express" (Mission), and "Mars Express" HAS_TARGET "Mars". Both entity classes are by rule 1's *A name the record does not explain*.
  - The list: PDS4 context product urn:esa:psa:context:instrument_host:spacecraft.mex, "The Mars Express Orbiter", of type Spacecraft, also titled "MARS EXPRESS" (https://pds.nasa.gov/data/pds4/context-pds4/instrument_host/spacecraft.mex_1.1.xml, checked on 2026-11-13).
  - The list: PDS4 context product urn:esa:psa:context:investigation:mission.mars_express, "Mars Express", of type Mission, also titled "MARS EXPRESS" (https://pds.nasa.gov/data/pds4/context-pds4/investigation/mission.mars_express_2.1.xml, checked on 2026-11-13).
  - **Question:** Q2.
- **Left out:** what "MRS" stands for (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what MRS is. Its entity class, Instrument, is written (ACQUIRED_BY_INSTRUMENT "MRS"), by rule 1's *A name the record does not explain*.
  - The list: PDS4 context product urn:esa:psa:context:instrument:mex.mrs, "Mars Express Orbiter Radio Science", an instrument of the instrument host Mars Express, whose earlier identifier is urn:nasa:pds:context:instrument:mrs.mex: "MRS" is its instrument id, as "VG1" is the host id of Voyager 1 in the record "VG1 J/S/SS PWS EDITED SPECTRUM ANALYZER FULL RES V1.0" (https://pds.nasa.gov/data/pds4/context-pds4/instrument/mex.mrs_1.2.xml, checked on 2026-11-13).
- **Left out:** what "Mars" is (title, "MARS", and notes, inside the name "Mars Express")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what Mars is. Its entity class, CelestialBody, is written (HAS_TARGET "Mars", of the record's dataset and of "Mars Express"), by rule 1's *A name the record does not explain*.
  - The reference: PDS4 context product urn:nasa:pds:context:target:planet.mars, "Mars", of type Planet (https://pds.nasa.gov/data/pds4/context-pds4/target/planet.mars_1.3.xml, checked on 2026-11-13).

## "MARS EXPRESS ASPERA-3 RAW EDR ION MASS ANALYZER EXT7 V1.0" (pool position 30, id 512dbadc-69c4-4e09-92d7-69887c4ba392)

A tuning record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. The record repeats the text of the held-out record "MARS EXPRESS ASPERA-3 RAW EDR ELECTRON SPECTROMTR EXT2 V1.0" (pool position 14), with another instrument and another mission extension, and its decisions are copied from that record. 5 items, none that may matter.

- **Left out:** "EDR" (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"
  - **Question:** Q6 (b).
- **Left out:** "RAW", "ION MASS ANALYZER" and "EXT7" as facts of their own (title)
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words."
  - They are the title's wordings of facts the notes state: "raw units of counts/accumulation" (HAS_UNIT), the "Mars Express ASPERA-3 Ion Mass Analyzer (IMA)" (ACQUIRED_BY_INSTRUMENT; rule 23 of *Writing a classed triple* writes the wording that says more) and "the seventh mission extension" (HAS_MISSION_PHASE).
- **Left out:** what "Mars Express" is (title, "MARS EXPRESS", and notes, "Mars Express ASPERA-3 Ion Mass Analyzer (IMA)")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what Mars Express is. Its entity class, Platform, is written (FROM_PLATFORM "Mars Express", "Mars Express ASPERA-3 Ion Mass Analyzer (IMA)" ABOARD "Mars Express", and "Mars Express" HAS_TARGET "Mars"), by rule 1's *A name the record does not explain*. The notes name the craft that carries the instrument (rule 17 of *Writing a classed triple*, *A platform in an instrument's name*), as in the record at pool position 14.
  - The list: PDS4 context product urn:esa:psa:context:instrument_host:spacecraft.mex, "The Mars Express Orbiter", of type Spacecraft, also titled "MARS EXPRESS" (https://pds.nasa.gov/data/pds4/context-pds4/instrument_host/spacecraft.mex_1.1.xml, checked on 2026-11-13).
  - **Question:** Q2.
- **Left out:** what "ASPERA-3" stands for (title, and notes, inside the name "Mars Express ASPERA-3 Ion Mass Analyzer (IMA)")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what ASPERA-3 is. Its entity class, Instrument, is written (ACQUIRED_BY_INSTRUMENT "ASPERA-3", and "Mars Express ASPERA-3 Ion Mass Analyzer (IMA)" PART_OF "ASPERA-3"), by rule 1's *A name the record does not explain*.
  - The list: PDS4 context product urn:esa:psa:context:instrument:mex.aspera-3, "Mars Express Orbiter Analyzer of Space Plasma and Energetic Atoms (3rd Version)", whose description names it "(ASPERA-3)" (https://pds.nasa.gov/data/pds4/context-pds4/instrument/mex.aspera-3_1.2.xml, checked on 2026-11-13).
- **Left out:** what "Mars" is (notes, inside the name "Mars Express")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what Mars is. Its entity class, CelestialBody, is written ("Mars Express" HAS_TARGET "Mars", by rule 2's *A fact inside a name*), by rule 1's *A name the record does not explain*.
  - The reference: PDS4 context product urn:nasa:pds:context:target:planet.mars, "Mars", of type Planet (https://pds.nasa.gov/data/pds4/context-pds4/target/planet.mars_1.3.xml, checked on 2026-11-13).

## "Gateway to Astronaut Photography of Earth" (pool position 31, id c4534993-09d1-468b-8bf1-febed049fd8c)

A tuning record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. Its describes class is WebTool, the entity class of the thing the title names, a gateway to photographs; the notes describe a gazetteer of planetary names instead (the first item). 7 items, 3 that may matter.

- **Left out:** the title's "Gateway to Astronaut Photography of Earth" against the notes' "This gazetteer contains detailed information about all names of topographic and albedo features on planets and satellites" (title and notes), as a conflict to correct
  - **Rule:** Finishing a record, *A record that contradicts itself*: "write what each passage states (rule 1 of What counts as a fact), and correct neither from outside knowledge." Both are written: HAS_TARGET "Earth" from the title, and the two HAS_VARIABLE and four HAS_TARGET triples of the gazetteer from the notes, all for the thing the title names ("This gazetteer" is the catalog entry, rule 23 of *Writing a classed triple*, *The title's instance*).
  - **May matter because:** my reading, not checked: the notes look copied from another catalog entry, a gazetteer of the names of features on planets and satellites; the record's maintainer should be told.
- **Left out:** "Planetary nomenclature, like terrestrial nomenclature, is used to uniquely identify a feature on the surface of a planet or satellite so that the feature can be easily located, described, and discussed." (notes)
  - **Rule:** Writing a classed triple, rule 21: "A statement that only explains a concept (what a term means, how a quantity behaves in general, which methods are in common use) and is about nothing so connected gives no ground truth triple"
- **Left out:** "Astronaut Photography" (title)
  - **Rule:** Writing a classed triple, rule 17: "A title's words give a fact only where a predicate fits what they state" (*A title's facts*)
  - **May matter because:** it says what the gateway gives access to: photographs of Earth taken by astronauts.
  - No predicate of the ground truth schema joins a web tool to the photographs it gives access to: PROVIDES_ACCESS_TO_DOCUMENT is pinned to a Document, and photographs are not one. "Astronaut" names no person (rule 9 of *What counts as a fact*).
- **Left out:** "detailed" (notes, "contains detailed information")
  - **Rule:** What counts as a fact, rule 5: "Take out words such as "great"."
  - "detailed" judges how much the information says; the two HAS_VARIABLE triples are written without it.
- **Left out:** "all" and "some" (notes, "about all names of topographic and albedo features" and "some planetary ring and ring-gap systems")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance"
  - They say how much of each group the gazetteer covers, how the facts HAS_VARIABLE and HAS_TARGET hold.
- **Left out:** "that the International Astronomical Union (IAU) has named and approved from its founding in 1919 through the present time" (notes)
  - **Rule:** What counts as a fact, rule 9: "A fact the record states for each member of a group it names only by a count or a common noun ("186 parameters each with …", "Each product is …") is written for the thing the group belongs to only when it stays true of that thing: what it holds, what it measures, what it comes from, or what format its files are in."
  - **May matter because:** it says who gives and approves the names the gazetteer holds, and since when.
  - The features are named only by common nouns, and naming and approving are facts of each feature's name, not of the gazetteer. The founding of the union is a fact of the union, written as "International Astronomical Union (IAU)" CREATED_ON "1919" (rule 21 of *Writing a classed triple* includes it, although no chain links it to the record's id); "through the present time" is true only as of writing (rule 10). The union is an Organization by its own word, "Union".
- **Left out:** what "Earth" is (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what Earth is. Its entity class, CelestialBody, is written (HAS_TARGET "Earth"), by rule 1's *A name the record does not explain*.
  - The reference: PDS4 context product urn:nasa:pds:context:target:planet.earth, "Earth", of type Planet (https://pds.nasa.gov/data/pds4/context-pds4/target/planet.earth_1.4.xml, checked on 2026-11-13).

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
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names"
  - The words name no particular channel or pair; the named inputs are written (COMPUTED_FROM "Wilkinson Microwave Anisotropy Probe (WMAP) 7-year data" and "internal templates").
- **Left out:** "Using the area of the sky outside the Kq85 galactic mask" (notes)
  - **Rule:** What counts as a fact, rule 8: "Nothing else in the study is a fact of the record's dataset: its background, its findings, what it says about methods it did not use, and the details of its method beyond what rule 24 writes (how the method was applied, its parameters, what it allows)."
  - It is how the method was applied, a setting of the detection step. "Kq85" is also an unexplained code (rule 1).
  - **May matter because:** it says which part of the sky the catalog covers.
- **Left out:** "at the 5-sigma level", "at 5 sigma" and ">= 3 sigma" (notes)
  - **Rule:** What counts as a fact, rule 8: "Nothing else in the study is a fact of the record's dataset: its background, its findings, what it says about methods it did not use, and the details of its method beyond what rule 24 writes (how the method was applied, its parameters, what it allows)."
  - They are the detection thresholds, parameters of the method.
- **Left out:** "they detect a total of 2102 point sources at the 5-sigma level in either the frequency maps or the internal templates. Of these, 1116 are detected either at 5 sigma directly in the frequency channels or at 5 sigma in the internal templates and >= 3 sigma at the corresponding position in the frequency channels." (notes)
  - **Rule:** What counts as a fact, rule 8: "Nothing else in the study is a fact of the record's dataset: its background, its findings, what it says about methods it did not use, and the details of its method beyond what rule 24 writes (how the method was applied, its parameters, what it allows)."
  - The counts are results the study drew from the data. "The authors have made a catalog of these sources" does not say which of the counts the catalog holds, so no HAS_NUMBER_OF triple is written.
  - **May matter because:** a search by catalog size would need the count.
- **Left out:** "Of the 1116 sources, 603 are detections that have not been reported so far in WMAP data." (notes)
  - **Rule:** What counts as a fact, rule 8: "Nothing else in the study is a fact of the record's dataset: its background, its findings, what it says about methods it did not use, and the details of its method beyond what rule 24 writes (how the method was applied, its parameters, what it allows)."
  - It is a finding of the study; it is also negated (rule 6: "A ground truth triple can't say "not".") and "so far" is true only as of writing (rule 10).
  - **May matter because:** it says how many of the sources are new.
- **Left out:** "In total, they identified 1029 of the 1116 sources with counterparts at 5 GHz and 69 at other frequencies." (notes)
  - **Rule:** What counts as a fact, rule 8: "Nothing else in the study is a fact of the record's dataset: its background, its findings, what it says about methods it did not use, and the details of its method beyond what rule 24 writes (how the method was applied, its parameters, what it allows)."
  - It is a finding of the study.
  - **May matter because:** it says how many sources have known counterparts.
- **Left out:** "The authors" as the dataset's developer (notes, "The authors have made a catalog of these sources available")
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names"
  - "The authors" names no specific people. The table's developer is written: DEVELOPED_BY_PARTY "NASA HEASARC" ("This table was created by the HEASARC").
- **Left out:** "the WMAP channels where they are seen" as channels of their own (notes)
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names"
  - The words name no particular channel, so no FOR_CHANNEL triple is written; they stay in the two Variables' instances, "position estimated in the WMAP channels where they are seen" and "flux estimated in the WMAP channels where they are seen".
- **Left out:** "the reference paper" as a Document of its own (notes, "Table 6 from the reference paper")
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names"
  - The record never names the paper, so no DOCUMENTED_AT triple is written; the words stay in the input's instance, "electronic version of Table 6 from the reference paper".
  - **May matter because:** the paper is where the method and the catalog are described.
- **Left out:** what "ApJ" stands for (notes, "the ApJ web site")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for". Its entity class, Document, is given by the record's own words "web site" (rule 20 of *Writing a classed triple*: "A page or site the record names in words, without a web address, is a Document"), and "web site" is a type word (rule 23).
- **Left out:** what "HEASARC" stands for (notes, "This table was created by the HEASARC" and "a service provided by NASA HEASARC")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what HEASARC is. Its entity class, Organization, is written (DEVELOPED_BY_PARTY and PROVIDED_BY_PARTY "NASA HEASARC", and "NASA HEASARC" PART_OF "NASA"), by rule 1's *A name the record does not explain*.
  - The reference: Wikidata, High Energy Astrophysics Science Archive Research Center (Q130537792), also named "HEASARC", an instance of "research center" and of "archive" (https://www.wikidata.org/wiki/Q130537792, checked on 2026-11-13). No official NASA list names it: the GCMD Providers keywords (version 25.2) have no entry for it.
- **Left out:** what "NASA" is (notes, "NASA HEASARC")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what NASA is. Its entity class, Organization, is written ("NASA HEASARC" PART_OF "NASA"), by rule 1's *A name the record does not explain*.
  - The reference: GCMD Providers keywords (version 25.2), the level "NASA" under "GOVERNMENT AGENCIES-U.S. FEDERAL AGENCIES", which holds NASA's centers and offices (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/providers?format=csv, checked on 2026-11-13).

## "NEAR GRS SPECTRA FOR CRUISE 4 PHASE" (pool position 33, id 4e7099c7-0f26-4d6e-a351-bf9c2c61b0f6)

A tuning record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. 5 items, 2 that may matter.

- **Left out:** "phase" and "mission" (notes, "the fourth cruise phase of the NEAR mission")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the entity,"
  - The type words are the record's own words for the entity classes written: "fourth cruise" is a MissionPhase, and "NEAR" a Mission.
- **Left out:** "GRS" and "CRUISE 4 PHASE" (title) as wordings of their own
  - **Rule:** Writing a classed triple, rule 23: "When a record names the same entity more than once, in different words, use the wording the first of the four tests below picks, in every ground truth triple"
  - "Gamma Ray Spectrometer (GRS)" spells out the title's "GRS" (test 1). "fourth cruise" and "CRUISE 4" say the same, and only the notes' sentence states the phase with words for its predicate, "observations made during the fourth cruise phase" (test 2).
- **Left out:** the title's "NEAR" as a craft (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included"
  - **May matter because:** the data come from the NEAR craft, which a search by platform would need.
  - The record names "NEAR" only as a mission ("the NEAR mission"), and the title's "NEAR" is the same wording (rule 23 of *Writing a classed triple*), so it is written as the Mission (FROM_MISSION "NEAR"), and no FROM_PLATFORM is written. The PDS4 context products agree that "NEAR" names the mission: urn:nasa:pds:context:investigation:mission.near_earth_asteroid_rendezvous, "The Near Earth Asteroid Rendezvous (NEAR) Mission", of type Mission, also titled "NEAR" (https://pds.nasa.gov/data/pds4/context-pds4/investigation/mission.near_earth_asteroid_rendezvous_1.3.xml), while the craft, urn:nasa:pds:context:instrument_host:spacecraft.near, is titled "NEAR EARTH ASTEROID RENDEZVOUS" (https://pds.nasa.gov/data/pds4/context-pds4/instrument_host/spacecraft.near_1.2.xml), both checked on 2026-11-13.
- **Left out:** "combined" (notes, "The individual observations are combined into a single file per day for each sensor")
  - **Rule:** Writing a classed triple, rule 24: "A verb or participle that says only what was done to the data ("corrected", "calibrated", "detrended", "binned", "mapped", "edited", "convert", "weighted") names no method"
  - The sentence says how the observations are put into files; HAS_GRANULE_DURATION "day" is written.
- **Left out:** "for each sensor" (notes)
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names"
  - **May matter because:** it says that the spectrometer has several sensors, with one file per sensor and day.
  - The record names none of the spectrometer's sensors, and does not say how many there are.

## "OrbView-2 SeaWiFS Global Binned Chlorophyll (CHL) Data, version R2022.0" (pool position 34, id 0efa4f80-4a96-4b07-9d2f-1d0315038d68)

A tuning record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. 4 items, 3 that may matter.

- **Left out:** "Binned" (title, "Global Binned Chlorophyll (CHL) Data")
  - **Rule:** Writing a classed triple, rule 24: "A verb or participle that says only what was done to the data ("corrected", "calibrated", "detrended", "binned", "mapped", "edited", "convert", "weighted") names no method"
  - **May matter because:** it says that the values are binned.
  - "Binned" describes the record's dataset itself, which is written as its title (rule 23 of *Writing a classed triple*, *The title's instance*), so the instance it would stay in is never written, as for "CALIBRATED" in the record "VG2 JUP LECP CALIBRATED RESAMPLED SECTORED 15MIN V1.1". The record names no grid the values are binned into, so no ON_GRID is written.
- **Left out:** "instrument" and "satellite" (notes, "The SeaWiFS instrument" and "the OrbView-2 (a.k.a. SeaStar) satellite"), and "sensor" (notes, "The mission and sensor")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the entity,"
  - The type words are the record's own words for the entity classes written: SeaWiFS is an Instrument and OrbView-2 a Platform. "sensor" is the record's other wording of SeaWiFS, its only instrument, written "SeaWiFS" (rule 23 of *Writing a classed triple*, test 1).
- **Left out:** "until the end of mission in December 2010" as the end of a mission, and "The mission" (notes)
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names"
  - **May matter because:** it says when the mission ended.
  - The record names no mission, so no ENDED_ON is written and the purpose and design of "The mission and sensor" are written for SeaWiFS alone. The date stays in the period SeaWiFS collected data over, HAS_TIME_SPAN "from September 1997 until December 2010" (rule 22 of *Writing a classed triple*).
- **Left out:** "global data" and "local data (limited onboard storage and direct broadcast)" as datasets of their own (notes, "It collected global data at 4 km resolution, and local data (limited onboard storage and direct broadcast) at 1 km")
  - **Rule:** Writing a classed triple, rule 21: "Leave out facts about other datasets, such as a variant of the record's dataset (the same data at another temporal resolution, spatial resolution, or version), or a product made from it."
  - **May matter because:** it says which data have which resolution, and how the local data were stored and sent.
  - The data SeaWiFS collected are not linked to the record's dataset by "part of" or "made from". Their resolutions are written as SeaWiFS's, HAS_SPATIAL_RESOLUTION "4 km" and "1 km", as rule 18's "MODIS has a spatial resolution of 250 m" gives "MODIS" HAS_SPATIAL_RESOLUTION "250 m"; "global", "local", "limited onboard storage" and "direct broadcast" are left out with the data.

## "MARS EXPRESS SUN MRS 1/2/3 EXTENDED MISSION 5 3750 V1.0" (pool position 35, id 25ad28f9-4dab-4d1a-9d77-dc648c793d5c)

A held-out record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. 6 items, 2 that may matter.

- **Left out:** "1/2/3" (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"
  - **May matter because:** in the record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" the same place in the title was checked to hold the processing levels (its item); not checked for this record.
  - **Question:** Q6 (b).
- **Left out:** "3750" (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"
  - **May matter because:** it tells this dataset from its siblings, as "1149" does in the record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (its item); not checked for this record.
  - **Question:** Q6 (b).
- **Left out:** "phase" (notes, "the extended mission phase")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the entity,"
  - The phase is written in the title's wording, "EXTENDED MISSION 5", the wording that says more (rule 23).
- **Left out:** what "Mars Express" is (title, "MARS EXPRESS", and notes, "a Mars Express Radio Science data set")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what Mars Express is. The title's first word is the instrument host, a craft: FROM_PLATFORM "Mars Express" (Platform). The notes' "a Mars Express Radio Science data set" names the mission, as "a Rosetta Radio Science data set" does in the record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0": FROM_MISSION "Mars Express" (Mission), and "Mars Express" HAS_TARGET "Mars". Both entity classes are by rule 1's *A name the record does not explain*.
  - The list: PDS4 context product urn:esa:psa:context:instrument_host:spacecraft.mex, "The Mars Express Orbiter", of type Spacecraft, also titled "MARS EXPRESS" (https://pds.nasa.gov/data/pds4/context-pds4/instrument_host/spacecraft.mex_1.1.xml, checked on 2026-11-13).
  - The list: PDS4 context product urn:esa:psa:context:investigation:mission.mars_express, "Mars Express", of type Mission, also titled "MARS EXPRESS" (https://pds.nasa.gov/data/pds4/context-pds4/investigation/mission.mars_express_2.1.xml, checked on 2026-11-13).
  - **Question:** Q2.
- **Left out:** what "MRS" stands for (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what MRS is. Its entity class, Instrument, is written (ACQUIRED_BY_INSTRUMENT "MRS"), by rule 1's *A name the record does not explain*.
  - The list: PDS4 context product urn:esa:psa:context:instrument:mex.mrs, "Mars Express Orbiter Radio Science", an instrument of the instrument host Mars Express, whose earlier identifier is urn:nasa:pds:context:instrument:mrs.mex: "MRS" is its instrument id, as "VG1" is the host id of Voyager 1 in the record "VG1 J/S/SS PWS EDITED SPECTRUM ANALYZER FULL RES V1.0" (https://pds.nasa.gov/data/pds4/context-pds4/instrument/mex.mrs_1.2.xml, checked on 2026-11-13).
- **Left out:** what "SUN" and "Mars" are (title, "SUN", and notes, inside the name "Mars Express")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what the Sun or Mars is. Their entity class, CelestialBody, is written (the record's dataset HAS_TARGET "SUN", and "Mars Express" HAS_TARGET "Mars"), by rule 1's *A name the record does not explain*.
  - The reference: PDS4 context product urn:nasa:pds:context:target:star.sun, "Sun", of type Star (https://pds.nasa.gov/data/pds4/context-pds4/target/star.sun_1.1.xml, checked on 2026-11-13); and, for Mars, urn:nasa:pds:context:target:planet.mars, "Mars", of type Planet (https://pds.nasa.gov/data/pds4/context-pds4/target/planet.mars_1.3.xml, checked on 2026-11-13).

## "CASSINI ORBITER SATURN UVIS IMAGE AT ONE WAVELENGTH 1.2" (pool position 36, id c5292e93-705c-4ac6-b0da-ba42c3dbdbfd)

A tuning record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. 6 items, 2 that may matter.

- **Left out:** "1.2" (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"; a bare number is not "V" or "Version" followed by a number.
  - **May matter because:** my reading, not checked: it is the version of the data set.
  - **Question:** Q6 (b).
- **Left out:** "Imaging" (notes, "Imaging of the Saturn system") as a fact of its own
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words."
  - It says what the title's "IMAGE" says, written once, HAS_SPATIAL_REPRESENTATION "IMAGE AT ONE WAVELENGTH", with both passages in its source text.
- **Left out:** the title's "SATURN" as a target of its own (title)
  - **Rule:** Writing a classed triple, rule 23: "When a record names the same entity more than once, in different words, use the wording the first of the four tests below picks, in every ground truth triple"
  - **May matter because:** a search for the planet Saturn would need it.
  - My reading: the title's "SATURN" names the target of the imaging, which the notes call "the Saturn system", the wording that says more (test 1), so one ground truth triple is written, HAS_TARGET "Saturn system".
- **Left out:** what "CASSINI ORBITER" is (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what CASSINI ORBITER is. Its entity class, Platform, is written (FROM_PLATFORM "CASSINI ORBITER"), by rule 1's *A name the record does not explain*.
  - The list: PDS4 context product urn:nasa:pds:context:instrument_host:spacecraft.co, "Cassini Orbiter", of type Spacecraft, also titled "CASSINI ORBITER" (https://pds.nasa.gov/data/pds4/context-pds4/instrument_host/spacecraft.co_1.4.xml, checked on 2026-11-13).
- **Left out:** what "UVIS" stands for (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what UVIS is. Its entity class, Instrument, is written (ACQUIRED_BY_INSTRUMENT "UVIS"), by rule 1's *A name the record does not explain*.
  - The list: PDS4 context product urn:nasa:pds:context:instrument:uvis.co, "Cassini Oribiter Ultraviolet Imaging Spectrograph", an instrument of the instrument host spacecraft.co, whose description names it "The Ultraviolet Imaging Spectrograph Subsystem (UVIS) of Cassini Orbiter" (https://pds.nasa.gov/data/pds4/context-pds4/instrument/co.uvis_1.3.xml, checked on 2026-11-13).
- **Left out:** what "Saturn system" is (notes, "the Saturn system")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what the Saturn system is. Its entity class, CelestialBody, is written (HAS_TARGET "Saturn system"), by rule 1's *A name the record does not explain*.
  - The reference: PDS4 context product urn:nasa:pds:context:target:planetary_system.saturn_system, "Saturn System", of type Planetary System, "Saturn and its satellites" (https://pds.nasa.gov/data/pds4/context-pds4/target/planetary_system.saturn_system_1.2.xml, checked on 2026-11-13). A group of natural objects in space fits CelestialBody, the one entity class whose definition takes in natural objects in space.

## "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP019 RDR-INFLDSTR V1.0" (pool position 37, id 8fa4b5c9-61e1-4331-92a1-51387242f4f1)

A tuning record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. The record repeats the text of the tuning record "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0" (pool position 13), with another planning period and another period covered, and its decisions are copied from that record. 8 items, 3 that may matter.

- **Left out:** "MTP019" (title, "ESC3-MTP019")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"
  - **May matter because:** it tells this dataset from its siblings, as "MTP020" does in the record "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0" (its item; not checked for this record).
  - **Question:** Q6 (b).
- **Left out:** "RDR" and "INFLDSTR" (title, "RDR-INFLDSTR")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"
  - The record "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0" lists only "RDR" in its item; "INFLDSTR" is left out there too.
  - **Question:** Q6 (b).
- **Left out:** "prime" (notes, "The prime target is comet 67P/Churyumov-Gerasimenko 1 (1969 R1)")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance"
  - **May matter because:** a search for other bodies in these images would need it.
  - HAS_TARGET says the dataset is about the comet; "prime" says only that it is the main target, how that fact holds, as in the record "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0".
- **Left out:** "comet" (notes, "comet 67P/Churyumov-Gerasimenko 1 (1969 R1)")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the entity,"
- **Left out:** "spacecraft" and "mission phase" (notes, "the Rosetta spacecraft" and "the COMET ESCORT 3 mission phase")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the entity,"; "the Rosetta spacecraft" is written as "ROSETTA-ORBITER", the wording that says more (rule 23).
- **Left out:** "Lien" (notes, "Lien corrected dataset after September 2019 PSA/PDS external peer review")
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words."
  - My ground truth triple REVISED_AFTER "September 2019 PSA/PDS external peer review" says the dataset was corrected after the review; "Lien" names what was corrected, the issues the review raised, as in the record "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0".
- **Left out:** PRODUCED_USING_ALGORITHM "solar stray-light corrected", "in-field stray-light corrected", "radiometric calibrated" and "geometric distortion corrected (resampled)" (notes, "contains solar stray-light corrected, in-field stray-light corrected, radiometric calibrated and geometric distortion corrected (resampled) image data")
  - **Rule:** Writing a classed triple, rule 24: "A verb or participle that says only what was done to the data ("corrected", "calibrated", "detrended", "binned", "mapped", "edited", "convert", "weighted") names no method"
  - **May matter because:** it says which corrections were applied to the images.
  - The words describe the data and name no method. What was corrected is written: CLEANED_OF "solar stray-light", CLEANED_OF "in-field stray-light" and CLEANED_OF "geometric distortion" (rule 24: "What a step removed from the data, or corrected in them, is neither the step's input nor its method"); "radiometric calibrated" names nothing removed.
  - **Question:** Q7 (c).
- **Left out:** what "OSIRIS" stands for (notes, inside the name "OSIRIS Narrow Angle Camera")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record names "OSIRIS" only inside the camera's name and never says what it is. Its entity class, Instrument, is written ("OSIRIS Narrow Angle Camera" PART_OF "OSIRIS"), by rule 1's *A name the record does not explain*.
  - The reference: Wikidata, Optical, Spectroscopic, and Infrared Remote Imaging System (Q7098805), also named "OSIRIS", "scientific instrument on the Rosetta spacecraft", an instance of "space instrument" (https://www.wikidata.org/wiki/Q7098805, checked on 2026-11-13). No official NASA list names it: the PDS4 context products have entries for its two cameras (urn:esa:psa:context:instrument:ro.osinac and ro.osiwac) and none for OSIRIS itself.

## "VIIRS/NOAA20 Dark Target Aerosol 6-Min L2 Swath 6 km" (pool position 38, id 6ed59de2-47ac-488a-8641-dbe6223fb0e6)

A held-out record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. 18 items, 5 that may matter.

- **Left out:** "satellite-derived" (notes, "provides satellite-derived measurements of Aerosol Optical Thickness (AOT)")
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names"
  - "satellite" names no particular satellite; the platform the record names is written (FROM_PLATFORM "NOAA-20"). "derived" names no method (rule 24 of *Writing a classed triple*).
- **Left out:** "their properties" (notes, "measurements of Aerosol Optical Thickness (AOT) and their properties over land and ocean")
  - **Rule:** Writing a classed triple, rule 22: "An item that names no specific entity ("his team") gives no ground truth triple"
  - "their size parameters" names a kind of property, and is written (HAS_MEASUREMENTS_OF "size parameters").
- **Left out:** "6-Min" (title) as a fact of its own
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words."
  - The notes state the 6 minutes twice. "every 6 minutes" is written HAS_TEMPORAL_RESOLUTION "6 minutes", the notes' wording, which spells out "Min" (rule 23). "incorporates 64 (750 m) pixels over a 6-minute acquisition" is written HAS_GRANULE_DURATION "6-minute": the record's dataset is a "set of products", and the six minutes are each product's (rule 9: "unless the predicate itself says "each""). The record does not say which of the two the title's "6-Min" means.
- **Left out:** "incarnation of the dark target (DT) aerosol product" (notes, "The NOAA-20 … Visible Infrared Imaging Radiometer Suite (VIIRS) incarnation of the dark target (DT) aerosol product")
  - **Rule:** What counts as a fact, rule 4: "A sentence that says what type of entity an instance refers to ("Kestrel is an imager") gives no ground truth triple: the instance's entity class says it"
  - The words say that the record's dataset is one form of the DT aerosol product, a kind of product. The method they name is written (PRODUCED_USING_ALGORITHM "dark target (DT)"), and "aerosol" is written in the wording that says more, "Aerosol Optical Thickness (AOT)" (rule 23).
- **Left out:** "the same" (notes, "is based on the same DT algorithm")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance"
- **Left out:** "One helps retrieve aerosol information over ocean (dark in visible and longer wavelengths), while the second aids retrievals over vegetated/dark-soiled land (dark in the visible)." (notes)
  - **Rule:** What counts as a fact, rule 9: "A fact the record states for each member of a group it names only by a count or a common noun ("186 parameters each with …", "Each product is …") is written for the thing the group belongs to only when it stays true of that thing: what it holds, what it measures, what it comes from, or what format its files are in."
  - The record names the two algorithms only by a count ("Two separate and distinct DT algorithms"). What each one helps to retrieve is not true of "dark target (DT)" as a whole, and a purpose is not among the facts the rule writes for the whole. The parentheses explain why the ocean and the land look dark, a statement that only explains a concept (rule 21 of *Writing a classed triple*).
  - **May matter because:** it says which of the two algorithms serves the ocean and which the land.
- **Left out:** "orbit-level" (notes, "This orbit-level product")
  - **Rule:** What counts as a fact, rule 4: "A sentence that says what type of entity an instance refers to ("Kestrel is an imager") gives no ground truth triple: the instance's entity class says it"
  - The words say what kind of product the record's dataset is. The layout the title names is written (HAS_SPATIAL_REPRESENTATION "Swath").
- **Left out:** "at-nadir" (notes, "has an at-nadir resolution of 6 km x 6 km, and progressively increases away from nadir given the sensor's scanning geometry and Earth's curvature")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance"
  - My ground truth triple HAS_SPATIAL_RESOLUTION "6 km x 6 km" is written without it, since the title states the resolution without it ("6 km", a shorter wording of the same fact, rule 23). The notes' sentence alone does not state the resolution without it, and rule 11 of *Writing a classed triple* would then keep "at-nadir" in what the predicate says, which HAS_SPATIAL_RESOLUTION does not say. The rest of the sentence names no value (rule 9) and explains its cause (rule 21 of *Writing a classed triple*).
  - **May matter because:** it says that the 6 km holds at nadir only, and that the cells grow away from it.
- **Left out:** "8 x 8" and "64" (notes, "accommodates 8 x 8 native VIIRS moderate-resolution (M-band) pixels" and "incorporates 64 (750 m) pixels")
  - **Rule:** What counts as a fact, rule 9: "An amount or a count per member gives no ground truth triple, unless the predicate itself says "each" (HAS_GRANULE_DURATION, HAS_SPATIAL_RESOLUTION)."
  - They count the pixels in each value of the record's dataset. The pixels are written as its input (COMPUTED_FROM "native VIIRS moderate-resolution (M-band) pixels").
- **Left out:** "moderate-resolution (M-band)" as a Channel (notes, inside "native VIIRS moderate-resolution (M-band) pixels")
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names"
  - The words name a group of the instrument's bands, not one band, so no FOR_CHANNEL or CHANNEL_OF triple is written. They stay in the pixels' instance.
  - **May matter because:** it says which of the instrument's bands the pixels come from.
- **Left out:** "nominally" (notes, "pixels that nominally have ~750 m horizontal pixel size")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance"
- **Left out:** "set of products" (notes, "This Version-2 set of products")
  - **Rule:** What counts as a fact, rule 4: "A sentence that says what type of entity an instance refers to ("Kestrel is an imager") gives no ground truth triple: the instance's entity class says it"
- **Left out:** "derived from the NOAA-20 VIIRS source" (notes, "the first collection of the Level-2 Dark Target Aerosol derived from the NOAA-20 VIIRS source")
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words."
  - ACQUIRED_BY_INSTRUMENT, FROM_PLATFORM and ABOARD already state it, and "Level-2 Dark Target Aerosol" repeats the level, the method and what is measured.
- **Left out:** "Hence, it bears outlining the differences between the products derived from NOAA-20 VIIRS as against the Suomi National Polar-orbiting Partnership (SNPP) VIIRS." (notes)
  - **Rule:** What counts as a fact, rule 7: "Not facts the record doesn't assert as true: uncertain ones, and ones it requires, requests or recommends."
  - "it bears outlining" recommends, and the products made from the SNPP VIIRS are other datasets (rule 21 of *Writing a classed triple*). The name "Suomi National Polar-orbiting Partnership (SNPP) VIIRS" still states that the instrument is aboard that platform, and is written so (rule 17 of *Writing a classed triple*, *A platform in an instrument's name*).
  - **May matter because:** it says that products of the same kind were made from the SNPP VIIRS before.
- **Left out:** "LAADS", "product description page" and "Dark Target aerosol team page" (notes, the words of the two links)
  - **Rule:** Writing a classed triple, rule 20: "Write that one name is also known as another (ALSO_KNOWN_AS) only when the record gives the other name in words of its own"
  - The two addresses are written (DOCUMENTED_AT, WebPage), as in the record "VIIRS/NPP BRDF/Albedo Parameter 3 Band M4 Daily L3 Global 30 ArcSec CMG V002". "LAADS" before a page's name, and the "Dark Target aerosol team" inside one, give no ground truth triple (rule 2, *A fact inside a name*: "When the naming states more than one predicate, or none, the name's words give no ground truth triple"): naming a page with an organization's or a team's name could mean that it wrote the page, keeps it or is its subject. The GCMD Providers keywords (version 25.2) have "NASA/GSFC/SED/ESD/HBSL/BISB/LAADS", the "L1 and Atmosphere Archive and Distribution System", at the web site of the first address (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/providers?format=csv, checked on 2026-11-13).
  - **May matter because:** they name who keeps the two pages.
- **Left out:** "mission" and "instruments" (notes, "the Terra and Aqua mission's MODIS instruments")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the entity,"
  - The record's lowercase type words give the entity classes: Mission for "Terra" and "Aqua", and Instrument for "MODIS". The GCMD Platforms keywords file Terra and Aqua as platforms, but a reference is used only for a name the record does not explain (rule 1, *A name the record does not explain*). The possessive "mission's" is written as PART_OF ("MODIS" PART_OF "Terra" and "MODIS" PART_OF "Aqua"), the predicate rule 2 names for "a Mission named in the name of one of its parts (an instrument, a craft, a campaign, a team)".
- **Left out:** what "NOAA-20" is (title, "NOAA20", and notes)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what NOAA-20 is. Its entity class, Platform, is written (FROM_PLATFORM "NOAA-20", "Visible Infrared Imaging Radiometer Suite (VIIRS)" ABOARD "NOAA-20", and "NOAA-20" ALSO_KNOWN_AS "Joint Polar Satellite System-1 (JPSS-1)"), by rule 1's *A name the record does not explain*. The title's "NOAA20" differs from "NOAA-20" only by a hyphen, so it is the same wording (rule 23 of *Writing a classed triple*).
  - The list: GCMD Platforms keywords (version 25.2), "NOAA-20", "Joint Polar Satellite System - 1", under Earth Observation Satellites (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/platforms?format=csv, checked on 2026-11-13).
- **Left out:** what "Suomi National Polar-orbiting Partnership (SNPP)" is (notes)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what the Suomi National Polar-orbiting Partnership is. Its entity class, Platform, is written ("Visible Infrared Imaging Radiometer Suite (VIIRS)" ABOARD it), by rule 1's *A name the record does not explain*.
  - The list: GCMD Platforms keywords (version 25.2), "Suomi-NPP", "Suomi National Polar-orbiting Partnership" (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/platforms?format=csv, checked on 2026-11-13).

## "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1228 V1.0" (pool position 39, id 874b6cc8-0d16-4efc-8125-f82aea1ef45f)

A tuning record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. The record repeats the text of the tuning record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (pool position 1), with another measurement number and another period covered, and its decisions are copied from that record. 6 items, 2 that may matter.

- **Left out:** "1/2/3" (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"
  - **May matter because:** in the record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" the same place in the title was checked to hold the processing levels (its item); not checked for this record.
  - **Question:** Q6 (b).
- **Left out:** "1228" (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"
  - **May matter because:** it tells this dataset from its siblings, as "1149" does in the record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (its item); not checked for this record.
  - **Question:** Q6 (b).
- **Left out:** what "RSI" stands for (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what RSI is. Its entity class, Instrument, is written (ACQUIRED_BY_INSTRUMENT "RSI"), by rule 1's *A name the record does not explain*.
  - The list: PDS4 context product urn:esa:psa:context:instrument:ro.rsi, "The Radio Science Investigations (RSI) for the Rosetta Orbiter", an instrument of the instrument host Rosetta Orbiter (https://pds.nasa.gov/data/pds4/context-pds4/instrument/ro.rsi_1.1.xml, checked on 2026-11-13).
- **Left out:** "comet" (notes, "at the comet 67P")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the entity,"
  - My ground truth triple has the target "67P".
- **Left out:** what "ROSETTA-ORBITER" is (title; the notes name only "Rosetta", in "a Rosetta Radio Science data set")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what ROSETTA-ORBITER is. Its entity class, Platform, is written (FROM_PLATFORM "ROSETTA-ORBITER"), by rule 1's *A name the record does not explain*.
  - The list: PDS4 context product urn:esa:psa:context:instrument_host:spacecraft.ro, "The Rosetta Orbiter Spacecraft", of type Spacecraft, also titled "ROSETTA-ORBITER" (https://pds.nasa.gov/data/pds4/context-pds4/instrument_host/spacecraft.ro_1.1.xml, checked on 2026-11-13).
- **Left out:** what "Rosetta" is (notes, "a Rosetta Radio Science data set")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what Rosetta is. Its entity class, Mission, is written (FROM_MISSION "Rosetta"), by rule 1's *A name the record does not explain*.
  - The reference: PDS4 context product urn:esa:psa:context:investigation:mission.international_rosetta_mission, "The International Rosetta Mission", also titled "ROSETTA", of type Mission (https://pds.nasa.gov/data/pds4/context-pds4/investigation/mission.international_rosetta_mission_1.1.xml, checked on 2026-11-13).

## "Model-Based Fault Detection and Diagnosis System for NASA Mars Subsurface Drill Prototype" (pool position 40, id 7404b473-5ea2-4383-b367-86a5c8d2a1b8)

A tuning record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. Its describes class is Document: the notes call the catalog entry "This paper", and the title is the paper's title. The facts of the paper are what it covers (DOCUMENTED_AT, from the thing covered to the paper). The places of the field tests are written as Place, coined for this record, since SpatialExtent is an area the data cover. 9 items, 2 that may matter.

- **Left out:** "for NASA Mars Subsurface Drill Prototype" (title), and "NASA" in it
  - **Rule:** Writing a classed triple, rule 17: "A title's words give a fact only where a predicate fits what they state" (*A title's facts*)
  - **May matter because:** it says which drill the fault detection and diagnosis system was made for.
  - No predicate of the ground truth schema says what a system is for. "NASA" before the prototype's name could mean that NASA built, owns or funded it, and naming does not settle which (rule 2 of *What counts as a fact*: "When the naming states more than one predicate, or none, the name's words give no ground truth triple"). The title's "Mars" gives HAS_TARGET "Mars".
- **Left out:** "project" (notes, "The Drilling Automation for Mars Environment (DAME) project")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the entity,"
  - "project" is the record's own word for the entity class written, Project, coined for this record: the ground truth schema's Mission is a named effort to collect data, and DAME develops a drill.
- **Left out:** "on a general level", "overall" and "The main focus, however," (notes, "This paper outlines, on a general level, the overall DAME architecture" and "The main focus, however, is on describing")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance"
  - They say how fully the paper covers each thing, how the facts DOCUMENTED_AT hold.
- **Left out:** "including the modeling approach, the fault modes handled, and the diagnostic algorithms" (notes)
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names"
  - **May matter because:** it says that the paper describes the system's model, the faults it handles and its algorithms.
  - The record names no approach, fault mode or algorithm: the words say what the paper's description of the system covers, by common nouns only.
- **Left out:** "latest" (notes, "The results of the latest field tests")
  - **Rule:** What counts as a fact, rule 10: "Take out "latest", "current", "now", "then available", and words like them."
- **Left out:** "The results of" (notes, "The results of the latest field tests … are also discussed")
  - **Rule:** What counts as a fact, rule 8: "Nothing else in the study is a fact of the record's dataset: its background, its findings, what it says about methods it did not use, and the details of its method beyond what rule 24 writes (how the method was applied, its parameters, what it allows)."
  - The results are findings, and the record does not give them; "field tests" DOCUMENTED_AT the paper is written.
- **Left out:** "a Mars analogue site" (notes, "Haughton Crater on Devon Island (a Mars analogue site in Canadian Arctic)")
  - **Rule:** What counts as a fact, rule 4: "A sentence that says what type of entity an instance refers to ("Kestrel is an imager") gives no ground truth triple: the instance's entity class says it"
  - It says what kind of place Haughton Crater is. Its "Mars" gives no HAS_TARGET: the site is on Earth, and stands in for Mars.
- **Left out:** what "NASA" is (notes, "NASA Ames Research Center")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what NASA is. Its entity class, Organization, is written ("NASA Ames Research Center" PART_OF "NASA"), by rule 1's *A name the record does not explain*.
  - The reference: GCMD Providers keywords (version 25.2), the level "NASA" under "GOVERNMENT AGENCIES-U.S. FEDERAL AGENCIES", which holds NASA's centers and offices (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/providers?format=csv, checked on 2026-11-13).
- **Left out:** what "Mars" is (title, and notes, "Mars Environment", "a Mars lander" and "the Mars surface")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what Mars is. Its entity class, CelestialBody, is written (HAS_TARGET "Mars", of the paper and of DAME), by rule 1's *A name the record does not explain*.
  - The reference: PDS4 context product urn:nasa:pds:context:target:planet.mars, "Mars", of type Planet (https://pds.nasa.gov/data/pds4/context-pds4/target/planet.mars_1.3.xml, checked on 2026-11-13).

## "First ISCCP Regional Experiment (FIRE) Cirrus Phase II Raman Lidar Data" (pool position 41, id 26714637-d3cd-4e11-9600-5b764346bef3)

A held-out record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. 12 items, 6 that may matter.

- **Left out:** what "First ISCCP Regional Experiment (FIRE)" is (title and notes)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The name's kind word, "Experiment", fits more than one entity class: a named effort to collect data (Mission), or a device (Instrument), as "Stratospheric Aerosol and Gas Experiment (SAGE) III" in the record "SOLVE I Ground Site Data". No reference of rule 1's *A name the record does not explain* names it: the GCMD Platforms, Instruments and Providers keywords (version 25.2) and Wikidata have no entry for it (checked on 2026-11-13). I read the record's own sentences as its explanation: FIRE has goals, its "four intensive field-observation periods were planned and executed", and "Each mission combined coordinated satellite, airborne, and surface observations". They fit the definition of Mission ("a named effort to collect data, from space, from the air, on water or on the ground") and of no other entity class, so Mission is written (FROM_MISSION, HAS_PURPOSE, HAS_NUMBER_OF, and the periods' PART_OF).
- **Left out:** "ISCCP" (title and notes, inside "First ISCCP Regional Experiment (FIRE)", and "ISCCP data")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what ISCCP is. Wikidata's International Satellite Cloud Climatology Project (Q6052840), labelled "ISCCP" in German, has no "instance of" statement, so its kind fits no entity class (https://www.wikidata.org/wiki/Q6052840, checked on 2026-11-13), and no official NASA list names it. So "ISCCP" gives no ground truth triple (rule 2, *A fact inside a name*), and its words stay in the instances that hold them.
  - **May matter because:** it names the project the experiment belongs to.
- **Left out:** "To-date" (notes, "To-date, four intensive field-observation periods were planned and executed")
  - **Rule:** What counts as a fact, rule 10: "Take out "latest", "current", "now", "then available", and words like them."
- **Left out:** "Cirrus Phase II" (title) as a wording of its own
  - **Rule:** Writing a classed triple, rule 23: "When a record names the same entity more than once, in different words, use the wording the first of the four tests below picks, in every ground truth triple"
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
  - **Rule:** Writing a classed triple, rule 24: "A verb or participle that says only what was done to the data ("corrected", "calibrated", "detrended", "binned", "mapped", "edited", "convert", "weighted") names no method"
  - The minute is written (HAS_COMPOSITING_PERIOD "one minute"). "in the detectors" and "to a file" name no detector and no file (rule 9).
  - **May matter because:** it says how each profile is made.
- **Left out:** "For the 10 minute averaged data, the data are summed for 10 minutes before the calculations are performed." (notes)
  - **Rule:** Writing a classed triple, rule 21: "Leave out facts about other datasets, such as a variant of the record's dataset (the same data at another temporal resolution, spatial resolution, or version), or a product made from it."
  - The 10 minute averaged data are the same data at another temporal resolution. The record's dataset "consists of a series of one minute profiles", and the record states no "part of" or "made from" link between the two.
  - **May matter because:** it says that 10-minute averages of the data exist.
- **Left out:** "Zero (0) km means sea level." (notes)
  - **Rule:** Writing a classed triple, rule 21: "A statement that only explains a concept (what a term means, how a quantity behaves in general, which methods are in common use) and is about nothing so connected gives no ground truth triple"
- **Left out:** "The site altitude is 0.229 km" (notes)
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names"
  - The record never names the site.
  - **May matter because:** it gives the height of the lidar's site.
- **Left out:** "thefirst data point is at 0.1845 km above ground level" (notes)
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words."
  - It gives the start of the vertical range counted from the ground: 0.229 km and 0.1845 km make the "0.4135" of "from 0.4135 to 10.299 kilometers", which counts from sea level. HAS_VERTICAL_RANGE is written once, from the sentence that states the whole range.

## "ROSETTA-ORBITER 67P RSI 1/2/3 PRELANDING 0230 V1.0" (pool position 42, id c8dde77f-9954-44fe-ad72-1f065efc34ca)

A tuning record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. The record repeats the text of the tuning record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1228 V1.0" (pool position 39), with another mission phase, another measurement number and another period covered, and its decisions are copied from that record. They differ in one ground truth triple: the phase's name "PRELANDING" holds no word for the comet, unlike "COMET ESCORT 4", so the phase has no HAS_TARGET triple here. 6 items, 2 that may matter.

- **Left out:** "1/2/3" (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"
  - **May matter because:** in the record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" the same place in the title was checked to hold the processing levels (its item); not checked for this record.
  - **Question:** Q6 (b).
- **Left out:** "0230" (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"
  - **May matter because:** it tells this dataset from its siblings, as "1149" does in the record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (its item); not checked for this record.
  - **Question:** Q6 (b).
- **Left out:** what "RSI" stands for (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what RSI is. Its entity class, Instrument, is written (ACQUIRED_BY_INSTRUMENT "RSI"), by rule 1's *A name the record does not explain*.
  - The list: PDS4 context product urn:esa:psa:context:instrument:ro.rsi, "The Radio Science Investigations (RSI) for the Rosetta Orbiter", an instrument of the instrument host Rosetta Orbiter (https://pds.nasa.gov/data/pds4/context-pds4/instrument/ro.rsi_1.1.xml, checked on 2026-11-13).
- **Left out:** "comet" (notes, "at the comet 67P")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the entity,"
  - My ground truth triple has the target "67P".
- **Left out:** what "ROSETTA-ORBITER" is (title; the notes name only "Rosetta", in "a Rosetta Radio Science data set")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what ROSETTA-ORBITER is. Its entity class, Platform, is written (FROM_PLATFORM "ROSETTA-ORBITER"), by rule 1's *A name the record does not explain*.
  - The list: PDS4 context product urn:esa:psa:context:instrument_host:spacecraft.ro, "The Rosetta Orbiter Spacecraft", of type Spacecraft, also titled "ROSETTA-ORBITER" (https://pds.nasa.gov/data/pds4/context-pds4/instrument_host/spacecraft.ro_1.1.xml, checked on 2026-11-13).
- **Left out:** what "Rosetta" is (notes, "a Rosetta Radio Science data set")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what Rosetta is. Its entity class, Mission, is written (FROM_MISSION "Rosetta"), by rule 1's *A name the record does not explain*.
  - The reference: PDS4 context product urn:esa:psa:context:investigation:mission.international_rosetta_mission, "The International Rosetta Mission", also titled "ROSETTA", of type Mission (https://pds.nasa.gov/data/pds4/context-pds4/investigation/mission.international_rosetta_mission_1.1.xml, checked on 2026-11-13).

## "VG2 NEP PLS DERIVED RDR ION INBOUND S-WIND 48SEC V1.0" (pool position 43, id cd62b985-b784-4df3-a0d0-cb9a5725349f)

A tuning record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. Its title is read as the titles of the tuning record "VG1 J/S/SS PWS EDITED SPECTRUM ANALYZER FULL RES V1.0" (pool position 16) and the held-out record "VG2 JUP LECP CALIBRATED RESAMPLED SECTORED 15MIN V1.1" (pool position 92) are: "VG2" is Voyager 2, and the target's code begins the name the notes give. 11 items, 3 that may matter.

- **Left out:** "best available" (notes, "the best available values")
  - **Rule:** What counts as a fact, rule 10: "Take out "latest", "current", "now", "then available", and words like them."
  - The values are the best ones as of when the record was written; "best" is also a judgement (rule 5).
- **Left out:** "DERIVED" (title) and "derived" (notes, "derived from data obtained by the Voyager 2 plasma experiment") as a method
  - **Rule:** Writing a classed triple, rule 24: "A verb or participle that says only what was done to the data ("corrected", "calibrated", "detrended", "binned", "mapped", "edited", "convert", "weighted") names no method"
  - The step is written: COMPUTED_FROM "observed spectra (current as a function of energy)" and PRODUCED_USING_ALGORITHM "fitting with Maxwellian plasma distributions, using a non-linear least squares fitting routine". The notes' "data obtained by the Voyager 2 plasma experiment" and "the observed spectra" name one input (rule 23 of *Writing a classed triple*: the fit is made "to find the plasma parameters which … best simulate the data"), written in the wording that is more precise.
- **Left out:** "RDR" and "S-WIND" (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"
  - **May matter because:** my reading, not checked: "S-WIND" names the solar wind, the plasma the ions belong to, which the notes never name; "RDR" is the data set type of the record "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0" (its item).
  - **Question:** Q6 (b).
- **Left out:** "INBOUND" (title)
  - **Rule:** Writing a classed triple, rule 17: "A title's words give a fact only where a predicate fits what they state" (*A title's facts*)
  - **May matter because:** it tells the data taken as the craft approached Neptune from those taken as it left.
  - The record names no mission phase "inbound" and gives the word no period, and no predicate of the ground truth schema says in which direction a craft was moving when the data were taken.
- **Left out:** "ION", "NEP", "PLS" and "VG2" (title) as wordings of their own
  - **Rule:** Writing a classed triple, rule 23: "When a record names the same entity more than once, in different words, use the wording the first of the four tests below picks, in every ground truth triple"
  - The notes give "ion densities, temperatures, and velocities", "Neptune", "Voyager 2 plasma experiment" and "Voyager 2" (test 1, the wording that says more). "NEP" is written "Neptune", as "JUP" is "Jupiter" in the record "VG2 JUP LECP CALIBRATED RESAMPLED SECTORED 15MIN V1.1": its letters begin the name the notes give. "PLS" is the instrument id of the Voyager 2 plasma experiment (below), and its letters are letters of "plasma", in order.
- **Left out:** "All" (notes, "All parameters are obtained by fitting")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance"
- **Left out:** "to find the plasma parameters which, when coupled with the full instrument response, best simulate the data" (notes)
  - **Rule:** What counts as a fact, rule 8: "Nothing else in the study is a fact of the record's dataset: its background, its findings, what it says about methods it did not use, and the details of its method beyond what rule 24 writes (how the method was applied, its parameters, what it allows)."
  - **May matter because:** it says that the fit takes the instrument's response into account.
- **Left out:** "as a function of energy" as a fact of its own (notes, inside "observed spectra (current as a function of energy)")
  - **Rule:** What counts as a fact, rule 2: "When the naming states more than one predicate, or none, the name's words give no ground truth triple, since choosing one would add what the record does not state." (*A fact inside a name*)
  - The gloss stays in the instance (rule 20 of *Writing a classed triple*). Its "current" gives HAS_MEASUREMENTS_OF "current", and "spectra" gives HAS_SPATIAL_REPRESENTATION "spectra"; no predicate of the ground truth schema says along which quantity a spectrum is laid out.
- **Left out:** what "Voyager 2" is (title, "VG2", and notes, "the Voyager 2 plasma experiment")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what Voyager 2 is. Its entity class, Platform, is written (FROM_PLATFORM "Voyager 2", and "Voyager 2 plasma experiment" ABOARD "Voyager 2"), by rule 1's *A name the record does not explain*. "VG2" is the craft's host id.
  - The reference: PDS4 context product urn:nasa:pds:context:instrument_host:spacecraft.vg2, "VOYAGER 2", of type Spacecraft, with the host id "VG2" (https://pds.nasa.gov/data/pds4/context-pds4/instrument_host/spacecraft.vg2_1.5.xml, checked on 2026-11-13).
- **Left out:** what "Voyager 2 plasma experiment" and "PLS" are (notes and title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record's own kind word, "experiment", fits more than one entity class. Its entity class, Instrument, is written (ACQUIRED_BY_INSTRUMENT "Voyager 2 plasma experiment", of the record's dataset and of the observed spectra, and ABOARD "Voyager 2"), by rule 1's *A name the record does not explain*. The name stays whole, as "Rosetta Orbiter ALICE UV Spectrometer" does in the record "ROSETTA-ORBITER 67P/CAL ALICE 2 ESC1 V1.0" (rule 17 of *Writing a classed triple*, *A platform in an instrument's name*): the notes never write the instrument without the craft's name, and the title's "PLS" is a shorter wording of it.
  - The list: PDS4 context product urn:nasa:pds:context:instrument:vg2.pls, "Plasma Science Experiment for VG2", an instrument of the instrument host Voyager 2, also titled "PLASMA SCIENCE EXPERIMENT", whose earlier identifier is urn:nasa:pds:context:instrument:pls.vg2: "PLS" is its instrument id (https://pds.nasa.gov/data/pds4/context-pds4/instrument/vg2.pls_1.2.xml, checked on 2026-11-13).
- **Left out:** what "Neptune" is (title, "NEP", and notes, "near Neptune")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what Neptune is. Its entity class, CelestialBody, is written (HAS_TARGET "Neptune"), by rule 1's *A name the record does not explain*; "near Neptune" is written whole as the area the data cover (HAS_SPATIAL_COVERAGE), as "vicinity of Jupiter" is in the record "VG2 JUP LECP CALIBRATED RESAMPLED SECTORED 15MIN V1.1".
  - The reference: PDS4 context product urn:nasa:pds:context:target:planet.neptune, "Neptune", of type Planet (https://pds.nasa.gov/data/pds4/context-pds4/target/planet.neptune_1.3.xml, checked on 2026-11-13).

## "ROSETTA-ORBITER 67P NAVCAM 2 COMET ESCORT 3 MTP019 V1.0" (pool position 44, id 87c1785c-4218-427d-a502-8ef5c6d7436a)

A held-out record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. 9 items, 2 that may matter.

- **Left out:** "2" (title, "NAVCAM 2")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"; a bare number is not "L" or "Level" followed by a number.
  - **Question:** Q6 (b).
- **Left out:** "MTP019" (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"
  - **May matter because:** it tells this dataset from its siblings, as "MTP020" does in the record "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0" (its item; not checked for this record).
  - **Question:** Q6 (b).
- **Left out:** "RAW" (notes, "ROSETTA NAVCAM RAW DATA")
  - **Rule:** Writing a classed triple, rule 19: "A qualifier that only says how far the data are processed ("raw", "edited", "calibrated", "derived") is not a processing level, and stays in the instance, as written."
  - "ROSETTA NAVCAM RAW DATA" names what the record's dataset contains, which is the record's dataset itself (rule 19, *Whose fact it is*: "A qualifier of the "data" or "products" that a dataset "contains" or "consists of" is that dataset's fact"). The record's dataset is written as its title (rule 23, *The title's instance*), so the instance the word would stay in is never written.
  - **May matter because:** it says that the images are not processed.
- **Left out:** "COMET" (title, "COMET ESCORT 3")
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names"
  - The phase is written in the notes' wording, "Escort Phase 3" (rule 23, test 2: the notes' sentence states the phase's facts with words for them). The title's "COMET" names no particular comet, and the record never calls "67P/CG" a comet, so no HAS_TARGET of the phase is written. The records "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" and "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0" write one, since their notes say "the comet 67P" and "comet 67P/Churyumov-Gerasimenko 1 (1969 R1)".
- **Left out:** "when at the vicinity of" (notes, "when at the vicinity of target 67P/CG")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance"
  - HAS_TARGET "67P/CG" is written; the words say where the craft was when the data were taken.
- **Left out:** what "ROSETTA-ORBITER" is (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what ROSETTA-ORBITER is. Its entity class, Platform, is written (FROM_PLATFORM "ROSETTA-ORBITER"), by rule 1's *A name the record does not explain*.
  - The list: PDS4 context product urn:esa:psa:context:instrument_host:spacecraft.ro, "The Rosetta Orbiter Spacecraft", of type Spacecraft, also titled "ROSETTA-ORBITER" (https://pds.nasa.gov/data/pds4/context-pds4/instrument_host/spacecraft.ro_1.1.xml, checked on 2026-11-13).
- **Left out:** what "ROSETTA" is (notes, "ROSETTA NAVCAM RAW DATA")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what ROSETTA is. Its entity class, Mission, is written (FROM_MISSION "ROSETTA", and "NAVCAM" PART_OF "ROSETTA", by rule 2's *A fact inside a name*), by rule 1's *A name the record does not explain*.
  - The list: PDS4 context product urn:esa:psa:context:investigation:mission.international_rosetta_mission, "The International Rosetta Mission", of type Mission, also titled "ROSETTA" (https://pds.nasa.gov/data/pds4/context-pds4/investigation/mission.international_rosetta_mission_1.1.xml, checked on 2026-11-13). The craft's entry is titled "ROSETTA-ORBITER", not "ROSETTA".
- **Left out:** what "NAVCAM" stands for (title and notes)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what NAVCAM is. Its entity class, Instrument, is written (ACQUIRED_BY_INSTRUMENT "NAVCAM", and "NAVCAM" PART_OF "ROSETTA"), by rule 1's *A name the record does not explain*.
  - The list: PDS4 context product urn:esa:psa:context:instrument:ro.navcam, "The Navigation Camera (NavCam) for the Rosetta Orbiter" (https://pds.nasa.gov/data/pds4/context-pds4/instrument/ro.navcam_1.2.xml, checked on 2026-11-13); "NAVCAM" and "NavCam" differ only in capitals (rule 23 of *Writing a classed triple*).
- **Left out:** what "67P/CG" is (title, "67P", and notes, "target 67P/CG")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what 67P/CG is. Its entity class, CelestialBody, is written (HAS_TARGET "67P/CG"), by rule 1's *A name the record does not explain*. "67P/CG" stays whole, since "CG" is never named alone (rule 22 of *Writing a classed triple*, *Lists joined by "/" or "+"*), and it says more than the title's "67P" (rule 23).
  - The reference: Wikidata, 67P/Churyumov–Gerasimenko (Q844672), whose other names include "67P" and "67P/C-G", an instance of "Jupiter-family comet" (https://www.wikidata.org/wiki/Q844672, checked on 2026-11-13). The record's "67P/CG" differs from "67P/C-G" only by a hyphen (rule 23). The PDS4 context product urn:nasa:pds:context:target:comet.67p_churyumov-gerasimenko names the comet "67P/Churyumov-Gerasimenko" only, a wording this record does not use.

## "STARDUST 9P/TEMPEL 1 NAVCAM 2 NEXT V1.0" (pool position 45, id dee11ff1-e2df-44a2-b43a-872a82f68405)

A tuning record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. Its decisions follow those of the tuning record "STARDUST 9P/TEMPEL 1 DFMI 2/3 NEXT V1.0" (pool position 9), whose text names the same craft, mission and comet, and of the held-out record "DEEP IMPACT 9P/TEMPEL CRUISE - RAW MRI NAV IMAGES V1.0" (pool position 53), whose text also lists the images its data set contains. As there, each kind of image the record lists is a part of the record's dataset (PART_OF), and the instrument, the mission phase and the mission that the record states for the images are written as facts of the record's dataset. 6 items, 1 that may matter.

- **Left out:** "2" (title, "NAVCAM 2") and "EDR" (notes, "EDR pre- and post-encounter and encounter images")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"; a bare number is not "L" or "Level" followed by a number.
  - **May matter because:** my reading, not checked: "2" holds the processing level in this place of the title, as "2/3" does in the record "STARDUST 9P/TEMPEL 1 DFMI 2/3 NEXT V1.0", whose notes give "Level 2/3 (EDR/RDR) data".
  - "EDR" stays in the instances of the three parts, as written (rule 11 of *Writing a classed triple*); this record never glosses it, as the record "STARDUST 9P/TEMPEL 1 DFMI 2/3 NEXT V1.0" does ("EDR (raw) sensor data").
  - **Question:** Q6 (b).
- **Left out:** "NAVCAM", "NEXT" and "9P/TEMPEL 1" (title) as wordings of their own
  - **Rule:** Writing a classed triple, rule 23: "When a record names the same entity more than once, in different words, use the wording the first of the four tests below picks, in every ground truth triple"
  - The notes spell them out: "Stardust Navigation Camera" (the letters of "NAVCAM" begin "Navigation" and "Camera"), "Stardust-NExT" and "9P/Tempel 1 (1867 G1)" (test 1, the wording that says more). The title's "9P/TEMPEL 1" is two items (rule 22, *Lists joined by "/" or "+"*), and both give HAS_TARGET "9P/Tempel 1 (1867 G1)".
- **Left out:** "comet" (notes, "during the encounter with comet 9P/Tempel 1 (1867 G1)")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the entity,"
  - My ground truth triples have the target "9P/Tempel 1 (1867 G1)" and the phase "encounter".
- **Left out:** "throughout" (notes, "calibration images taken throughout the Stardust-NExT mission")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance"
  - FROM_MISSION "Stardust-NExT" is written; "throughout" says only that the calibration images were taken over the whole mission, how that fact holds.
- **Left out:** what "STARDUST" is (title; the notes name "Stardust" only inside the names "Stardust Navigation Camera" and "Stardust-NExT")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what Stardust is. Its entity class, Platform, is written (FROM_PLATFORM "Stardust", and "Stardust Navigation Camera" ABOARD "Stardust", by rule 17 of *Writing a classed triple*, *A platform in an instrument's name*), by rule 1's *A name the record does not explain*. The notes' wording is written, since the title is typed all in capitals.
  - The list: PDS4 context product urn:nasa:pds:context:instrument_host:spacecraft.sdu, "The Stardust Spacecraft", of type Spacecraft (https://pds.nasa.gov/data/pds4/context-pds4/instrument_host/spacecraft.sdu_1.3.xml, checked on 2026-11-13). The camera's entity class, Instrument, is given by the record's own kind word "Camera"; the PDS4 context product urn:nasa:pds:context:instrument:sdu.navcam, "The Navigation Camera (NAVCAM) for Stardust", shows that the title's "NAVCAM" is the same camera (https://pds.nasa.gov/data/pds4/context-pds4/instrument/sdu.navcam_1.2.xml, checked on 2026-11-13).
  - "Stardust" inside the mission's name "Stardust-NExT" gives no ground truth triple: a Platform named in a Mission's name states no predicate of the ground truth schema (rule 2 of *What counts as a fact*, *A fact inside a name*).
- **Left out:** what "9P/Tempel 1 (1867 G1)" is (title, "9P/TEMPEL 1", and notes, "comet 9P/Tempel 1 (1867 G1)")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record's type word "comet" says what kind of thing 9P/Tempel 1 is. Its entity class, CelestialBody, is written (HAS_TARGET "9P/Tempel 1 (1867 G1)", of the record's dataset and of "encounter"); "(1867 G1)" is another code of the comet's own, kept in the instance (rule 20 of *Writing a classed triple*).
  - The reference: PDS4 context product urn:nasa:pds:context:target:comet.9p_tempel_1, "9P/Tempel 1", of type Comet (https://pds.nasa.gov/data/pds4/context-pds4/target/comet.9p_tempel_1_1.1.xml, checked on 2026-11-13).

## "Software Infrastructure to Enable Modeling & Simulation as a Service (M&SaaS) Project" (pool position 46, id 2d450311-b390-4fbd-9394-16132d43f426)

A tuning record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. Its describes class is Project, the entity class of the thing the title names, a named effort to build something, as the DAME project is in the record "Model-Based Fault Detection and Diagnosis System for NASA Mars Subsurface Drill Prototype" (pool position 40). The notes repeat the title, and the one fact written is the one that the words "to Enable" state inside the name. 3 items, 1 that may matter.

- **Left out:** the notes, "Software Infrastructure to Enable Modeling & Simulation as a Service (M&SaaS) Project"
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words."
  - The notes repeat the title word for word.
- **Left out:** how the project and its software infrastructure are related (title, "Software Infrastructure to Enable Modeling & Simulation as a Service (M&SaaS) Project")
  - **Rule:** What counts as a fact, rule 2: "When the naming states more than one predicate, or none, the name's words give no ground truth triple, since choosing one would add what the record does not state." (*A fact inside a name*)
  - **May matter because:** without it no ground truth triple connects the project with what it works on.
  - Naming a project with the words for a piece of software could mean that the project builds the software, that building it is the project's aim, or that the software is a part of the project, as "DAME autonomy package" PART_OF "Drilling Automation for Mars Environment (DAME)" is in the record "Model-Based Fault Detection and Diagnosis System for NASA Mars Subsurface Drill Prototype", and naming does not settle which. "Software Infrastructure" HAS_PURPOSE "Enable Modeling & Simulation as a Service (M&SaaS)", which the words "to Enable" state, is therefore connected to the record's id by no ground truth triple, and is kept (rule 21 of *Writing a classed triple*).
- **Left out:** "Modeling & Simulation" as two things (title, "Modeling & Simulation as a Service (M&SaaS)")
  - **Rule:** Writing a classed triple, rule 22: "A list that the record gives one abbreviation of its own is a name, and stays whole, only when the abbreviation stands for one entity"
  - "M&SaaS" stands for one thing, a service, so "Modeling & Simulation as a Service (M&SaaS)" stays whole.

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
  - **Rule:** What counts as a fact, rule 4: "A sentence that says what type of entity an instance refers to ("Kestrel is an imager") gives no ground truth triple: the instance's entity class says it"
  - They say what kind of data mining the title names.

## "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 2 0728 V1.0" (pool position 48, id 58210ae6-8fa8-4552-a52e-436cd3433c3d)

A tuning record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. The record repeats the text of the tuning record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1228 V1.0" (pool position 39), with another mission phase, another measurement number and another period covered, and its decisions are copied from that record. 6 items, 2 that may matter.

- **Left out:** "1/2/3" (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"
  - **May matter because:** in the record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" the same place in the title was checked to hold the processing levels (its item); not checked for this record.
  - **Question:** Q6 (b).
- **Left out:** "0728" (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"
  - **May matter because:** it tells this dataset from its siblings, as "1149" does in the record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (its item); not checked for this record.
  - **Question:** Q6 (b).
- **Left out:** what "RSI" stands for (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what RSI is. Its entity class, Instrument, is written (ACQUIRED_BY_INSTRUMENT "RSI"), by rule 1's *A name the record does not explain*.
  - The list: PDS4 context product urn:esa:psa:context:instrument:ro.rsi, "The Radio Science Investigations (RSI) for the Rosetta Orbiter", an instrument of the instrument host Rosetta Orbiter (https://pds.nasa.gov/data/pds4/context-pds4/instrument/ro.rsi_1.1.xml, checked on 2026-11-13).
- **Left out:** "comet" (notes, "at the comet 67P")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the entity,"
  - My ground truth triple has the target "67P".
- **Left out:** what "ROSETTA-ORBITER" is (title; the notes name only "Rosetta", in "a Rosetta Radio Science data set")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what ROSETTA-ORBITER is. Its entity class, Platform, is written (FROM_PLATFORM "ROSETTA-ORBITER"), by rule 1's *A name the record does not explain*.
  - The list: PDS4 context product urn:esa:psa:context:instrument_host:spacecraft.ro, "The Rosetta Orbiter Spacecraft", of type Spacecraft, also titled "ROSETTA-ORBITER" (https://pds.nasa.gov/data/pds4/context-pds4/instrument_host/spacecraft.ro_1.1.xml, checked on 2026-11-13).
- **Left out:** what "Rosetta" is (notes, "a Rosetta Radio Science data set")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what Rosetta is. Its entity class, Mission, is written (FROM_MISSION "Rosetta"), by rule 1's *A name the record does not explain*.
  - The reference: PDS4 context product urn:esa:psa:context:investigation:mission.international_rosetta_mission, "The International Rosetta Mission", also titled "ROSETTA", of type Mission (https://pds.nasa.gov/data/pds4/context-pds4/investigation/mission.international_rosetta_mission_1.1.xml, checked on 2026-11-13).

## "ARCTAS Model Data" (pool position 49, id 01432301-e0a8-4138-b1a1-ed57954c5fd6)

A tuning record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. The data set holds model output along the flight tracks of the aircraft of a field mission; most of the notes tell the mission, whose facts are general facts about something the record's dataset relates to (rule 21 of *Writing a classed triple*). 17 items, 7 that may matter.

- **Left out:** "field campaign" (notes, "ARCTAS was a field campaign") and "mission" (notes, "the Arctic Research of the Composition of the Troposphere from Aircraft & Satellites (ARCTAS) mission")
  - **Rule:** What counts as a fact, rule 4: "A sentence that says what type of entity an instance refers to ("Kestrel is an imager") gives no ground truth triple: the instance's entity class says it"
  - The record's own word "mission" gives ARCTAS its entity class, Mission ("a named effort to collect data, from space, from the air, on water or on the ground"); "mission" is also a type word (rule 23 of *Writing a classed triple*). The ground truth schema's Campaign is "carried out as part of a Mission", and the record names no Mission that ARCTAS is part of (the POLARCAT Experiment is unexplained, below).
- **Left out:** "Arctic", "Research of the Composition of the Troposphere" and "from Aircraft & Satellites" as facts of their own (notes, inside the name "Arctic Research of the Composition of the Troposphere from Aircraft & Satellites (ARCTAS)")
  - **Rule:** What counts as a fact, rule 2: "When the naming states more than one predicate, or none, the name's words give no ground truth triple, since choosing one would add what the record does not state." (*A fact inside a name*)
  - **May matter because:** it says where ARCTAS worked, the Arctic, which its purposes keep in their words.
  - A mission's name that says what the mission studies states no predicate, as "Drilling Automation" does not in the record "Model-Based Fault Detection and Diagnosis System for NASA Mars Subsurface Drill Prototype". "Arctic" may say where ARCTAS worked (LOCATED_AT) or what it studies, and the name does not settle which. "Aircraft & Satellites" names no specific craft (rule 9). The name stays whole (rule 11 of *Writing a classed triple*).
- **Left out:** "modeled chemical and aerosol data" as what the two parts hold (notes)
  - **Rule:** What counts as a fact, rule 2: "When the naming states more than one predicate, or none, the name's words give no ground truth triple, since choosing one would add what the record does not state." (*A fact inside a name*)
  - **May matter because:** a search by what the models give would need it.
  - The parts are written ("modeled chemical data" and "modeled aerosol data" PART_OF the record's dataset). The data are model output, not measurements, so HAS_MEASUREMENTS_OF ("holds measurements of this PhysicalQuantity") is false of them, and "chemical" is an adjective that names no quantity.
- **Left out:** what "GEOS-5", "GEOS-Chem", "STEM Model Forecasts", "MOZART-4" and "CMAQ" stand for (notes, "Models used include the GEOS-5, GEOS-Chem, STEM Model Forecasts, MOZART-4, and CMAQ models")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"
  - The record's own words say what they are, models that the data were made with ("Models used"), so each is written as PRODUCED_USING_ALGORITHM of the record's dataset, with the entity class Algorithm ("a method applied to data to compute a result"); "models" is a type word (rule 23 of *Writing a classed triple*). For the record: Wikidata's GEOS-Chem (Q122831932) is an instance of "software", and its CMAQ (Q23579663) of "chemical transport model" (checked on 2026-11-13).
- **Left out:** "The Arctic is a critical region in understanding climate change." and "The responses of the Arctic to environmental perturbations such as warming, pollution, and emissions from forest fires in boreal Eurasia and North America include key processes such as the melting of ice sheets and permafrost, a decrease in snow albedo, and the deposition of halogen radical chemistry from sea salt aerosols to ice." (notes)
  - **Rule:** Writing a classed triple, rule 21: "A statement that only explains a concept (what a term means, how a quantity behaves in general, which methods are in common use) and is about nothing so connected gives no ground truth triple"
  - They explain how the Arctic behaves in general, and are about nothing connected to the record's id; "critical" is also a judgement (rule 5).
- **Left out:** "Pollution brought to the Arctic from northern mid-latitude continents has environmental consequences, such as modifying regional and global climate and affecting the ozone budget.", "the smoke emissions from which act as an atmospheric perturbation to the Arctic by impacting the radiation budget and cloud processes and contributing to the production of tropospheric ozone", "as the Arctic is an important place for understanding radiative forcing due to the rapid pace of climate change in the region and its unique radiative environment" and "due to historically being the peak in the seasonal accumulation of pollution from northern mid-latitude continents in the Arctic" (notes)
  - **Rule:** Writing a classed triple, rule 21: "A statement that only explains a concept (what a term means, how a quantity behaves in general, which methods are in common use) and is about nothing so connected gives no ground truth triple"
  - They explain why the objectives and the month of the spring deployment matter, and are about nothing connected to the record's id. "April was chosen for the deployment phase" is read as the spring deployment's month, written "April 2008".
- **Left out:** "Prior to ARCTAS, these pathways remained largely uncertain." (notes)
  - **Rule:** What counts as a fact, rule 8: "Nothing else in the study is a fact of the record's dataset: its background, its findings, what it says about methods it did not use, and the details of its method beyond what rule 24 writes (how the method was applied, its parameters, what it allows)."
  - It is the background of the first objective.
- **Left out:** "International Global Atmospheric Chemistry (IGAC) Polar Study using Aircraft, Remote Sensing, Surface Measurements, and Models of Climate, Chemistry, Aerosols, and Transport (POLARCAT) Experiment for the International Polar Year 2007-2008" (notes, "ARCTAS was part of NASA’s contribution to the …")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what kind of thing the POLARCAT Experiment is: its kind word, "Experiment", fits more than one entity class, and no reference names it: the GCMD Instruments, Platforms and Providers keywords (version 25.2) and Wikidata have no entry for it (checked on 2026-11-13). So "ARCTAS" gives no PART_OF of it, and the organization named before its own name gives no PART_OF either (rule 2, *A fact inside a name*).
  - **May matter because:** a search for the datasets of POLARCAT or of the International Polar Year would need it.
  - Wikidata's International Global Atmospheric Chemistry (Q6050747) is an organization (https://www.wikidata.org/wiki/Q6050747, checked on 2026-11-13). Its International Polar Year (Q784374) is an instance of "International Year", a United Nations observance, a kind that fits no entity class (https://www.wikidata.org/wiki/Q784374, checked on 2026-11-13), so "for the International Polar Year 2007-2008" gives no ground truth triple either. "NASA’s contribution" names what ARCTAS belongs to, and is written "Arctic Research of the Composition of the Troposphere from Aircraft & Satellites (ARCTAS)" PART_OF "NASA" (rule 4: "the kind is left out, and the belonging is a ground truth triple").
- **Left out:** "expanding the potential for those models to predict future environmental change" (notes)
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names"
  - Its subject would be the capabilities ARCTAS sought to develop, which the record does not name, and "those models" are the earth science models, which it names by a common noun only.
- **Left out:** "three-week" as the duration of each deployment (notes, "two, three-week aircraft deployments")
  - **Rule:** What counts as a fact, rule 9: "An amount or a count per member gives no ground truth triple, unless the predicate itself says "each" (HAS_GRANULE_DURATION, HAS_SPATIAL_RESOLUTION)."
  - **May matter because:** it is how long each deployment lasted.
  - The words stay in the count, which is written whole: HAS_NUMBER_OF "two, three-week aircraft deployments" (rule 22 of *Writing a classed triple*, *Describing words joined by "and" or a comma*).
- **Left out:** "NASA" as a fact of the aircraft (notes, "three NASA aircrafts, the DC-8, P-3B, and BE-200")
  - **Rule:** What counts as a fact, rule 2: "A relationship that naming does not state (that one entity funded, developed, provided or sponsored the other) is never read from a name"
  - "NASA" before the aircraft says whose they are, and not whether NASA owns, operates or provides them. The aircraft are written as the platforms ARCTAS used: "Arctic Research of the Composition of the Troposphere from Aircraft & Satellites (ARCTAS)" USES_PLATFORM "DC-8", "P-3B" and "BE-200" (Platform; the record's own word "aircrafts" gives the entity class), and the count as HAS_NUMBER_OF "three NASA aircrafts".
- **Left out:** "conducted measurements and were equipped with suites of in-situ and remote sensing instrumentation" (notes)
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names"
  - **May matter because:** it says that the aircraft measured in situ and by remote sensing.
  - "suites of … instrumentation" names no instrument, and "conducted measurements" names nothing measured.
- **Left out:** "Airborne data was used in conjunction with satellite observations from AURA, AQUA, CloudSat, PARASOL, CALIPSO, and MISR." (notes)
  - **Rule:** What counts as a fact, rule 9: "What data have been used for, or can be used for, is a fact of the work that used them, not of the data: when the record doesn't name that work, the use gives no ground truth triple."
  - **May matter because:** it names the satellites whose observations went with the aircraft data.
- **Left out:** "The ASDC houses ARCTAS aircraft data, along with data related to MISR" (notes)
  - **Rule:** Writing a classed triple, rule 21: "Leave out facts about other datasets, such as a variant of the record's dataset (the same data at another temporal resolution, spatial resolution, or version), or a product made from it."
  - **May matter because:** it says where the aircraft data are kept.
  - The ARCTAS aircraft data and the data related to MISR are other datasets, which the record links to its dataset neither by "part of" nor by "made from". Their would-be ground truth triples: "ARCTAS aircraft data" PROVIDED_BY_PARTY "ASDC", and the same for "data related to MISR". The ASDC is an Organization: GCMD Providers keywords (version 25.2), "NASA/LARC/SD/ASDC", "Atmospheric Science Data Center, Science Directorate, Langley Research Center, NASA" (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/providers?format=csv, checked on 2026-11-13).
- **Left out:** "satellite instrument" and "satellite" (notes, "MISR, a satellite instrument aboard the Terra satellite")
  - **Rule:** What counts as a fact, rule 4: "A sentence that says what type of entity an instance refers to ("Kestrel is an imager") gives no ground truth triple: the instance's entity class says it"
  - The record's own words give MISR its entity class, Instrument, and Terra its own, Platform; "satellite" beside "Terra" is a type word (rule 23 of *Writing a classed triple*). The clause "which provides measurements that provide information about the Earth’s environment and climate" follows "the Terra satellite" with no comma, so it is written as Terra's (HAS_TARGET and two HAS_PURPOSE triples).
- **Left out:** what "NASA" is (notes, "NASA’s contribution" and "three NASA aircrafts")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what NASA is. Its entity class, Organization, is written ("Arctic Research of the Composition of the Troposphere from Aircraft & Satellites (ARCTAS)" PART_OF "NASA"), by rule 1's *A name the record does not explain*.
  - The reference: GCMD Providers keywords (version 25.2), the level "NASA" under "GOVERNMENT AGENCIES-U.S. FEDERAL AGENCIES", which holds NASA's centers and offices (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/providers?format=csv, checked on 2026-11-13).
- **Left out:** what "Earth" is (notes, "earth science models" and "the Earth’s environment and climate")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what Earth is. Its entity class, CelestialBody, is written (HAS_TARGET "earth", of ARCTAS and of Terra, by rule 19 of *Writing a classed triple*), by rule 1's *A name the record does not explain*. The two wordings differ only in capitals, and the first is written (rule 23, *Capitals and punctuation*). The word is taken out of "earth science models" in the purposes of ARCTAS, which are written with "science models", as "Earth's" is taken out of "Earth's Radiation Belts" in the record "BARREL 4G Rate Counter (RCNT) NaI Scintillator Diagnostics, Level 2, 4 s Data".
  - The reference: PDS4 context product urn:nasa:pds:context:target:planet.earth, "Earth", of type Planet (https://pds.nasa.gov/data/pds4/context-pds4/target/planet.earth_1.4.xml, checked on 2026-11-13).

## "VIIRS/NPP BRDF/Albedo Parameter 1 Band M3 Daily L3 Global 30 ArcSec CMG V002" (pool position 50, id 28e8b8fd-4463-4794-b810-44934fd449f6)

A held-out record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. Its text is that of the record "VIIRS/NPP BRDF/Albedo Parameter 3 Band M4 Daily L3 Global 30 ArcSec CMG V002" with another parameter, band and identifier, and it is annotated the same way. 16 items, 6 that may matter.

- **Left out:** "NASA/NOAA" as a fact of its own (notes)
  - **Rule:** What counts as a fact, rule 1: "Only what the record states." The words name the two agencies and the platform, and do not say how they are related (whether the agencies built the platform, launched it or operate it), so they state no fact (rule 2, *A fact inside a name*: "When the naming states more than one predicate, or none, the name's words give no ground truth triple"). "NASA/NOAA" stays in the platform's instance, "NASA/NOAA Suomi National Polar-orbiting Partnership (Suomi NPP)", as in the record "VIIRS/NPP BRDF/Albedo Parameter 3 Band M4 Daily L3 Global 30 ArcSec CMG V002".
- **Left out:** "Data are temporally weighted to the ninth day, which is reflected in the file name." (notes)
  - **Rule:** Writing a classed triple, rule 24: "A verb or participle that says only what was done to the data ("corrected", "calibrated", "detrended", "binned", "mapped", "edited", "convert", "weighted") names no method"
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
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names" No file is named; "large" is a judgement (rule 5).
- **Left out:** "just" (notes, "contains just one data layer")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance"
- **Left out:** "entire" (notes, "covers the entire globe")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance"
- **Left out:** "BRDF/Albedo values for VIIRS band M3" COMPUTED_FROM "volumetric parameters" and "geometric parameters", and FOR_CHANNEL "VIIRS band M3 (0.488 μm)" (notes)
  - **Rule:** Writing a classed triple, rule 21: "Leave out facts about other datasets, such as a variant of the record's dataset (the same data at another temporal resolution, spatial resolution, or version), or a product made from it." Its connection to the record's dataset is a ground truth triple: "BRDF/Albedo values for VIIRS band M3" COMPUTED_FROM the record's dataset (rule 24, *The record's dataset's own values*: "when the input is the record's dataset's own values, the input is the record's dataset").
  - **May matter because:** it says the albedo needs all three parameters, that is, three of the family's products together.
  - **Question:** Q24.
- **Left out:** "used to derive" as a purpose of the parameter (notes)
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words." COMPUTED_FROM says it; and a use is not a purpose (rule 9: "What data have been used for, or can be used for, is a fact of the work that used them, not of the data").
- **Left out:** "Known Issues" (notes, the heading)
  - **Rule:** What counts as a fact, rule 3: "A heading inside a text field, a line of its own that only names the passage below it ("Known Issues", "BARREL Data Usage Policy"), is formatting too, and gives no ground truth triple."
- **Left out:** "known issues" as what the page is about (notes, "For complete information about known issues please refer to")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance"
- **Left out:** "MODIS/VIIRS Land Quality Assessment website" (notes), as the page's name
  - **Rule:** Writing a classed triple, rule 20: "Write that one name is also known as another (ALSO_KNOWN_AS) only when the record gives the other name in words of its own"
  - **May matter because:** it is the page's name, by which a person would look for it.
- **Left out:** "NIR" as another name of "near-infrared", and "DNB" of "VIIRS Day/Night Band" (notes)
  - **Rule:** Writing a classed triple, rule 21: "Leave out facts about other datasets, such as a variant of the record's dataset (the same data at another temporal resolution, spatial resolution, or version), or a product made from it." The bands are the family's, not this dataset's.
- **Left out:** "BRDF/Albedo" (title) and "Bidirectional Reflectance Distribution Function (BRDF) and Albedo" (notes) as what the dataset holds
  - **Rule:** What counts as a fact, rule 1, *Membership by name*: "A statement about the group as a whole is not written for it"
  - The words name the product suite the dataset belongs to, not what this dataset holds: the notes say it is "the BRDF isotropic parameter for VIIRS band M3 (0.488 μm)" (HAS_VARIABLE), as in the record "VIIRS/NPP BRDF/Albedo NBAR at Solar Noon Band M4 Daily L3 Global 30ArcSec CMG V002".
- **Left out:** what "Suomi National Polar-orbiting Partnership (Suomi NPP)" is (notes; the title writes "NPP")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what the Suomi National Polar-orbiting Partnership is. Its entity class, Platform, is written (FROM_PLATFORM "NASA/NOAA Suomi National Polar-orbiting Partnership (Suomi NPP)", and "Visible Infrared Imaging Radiometer Suite (VIIRS)" ABOARD it), by rule 1's *A name the record does not explain*.
  - The list: GCMD Platforms keywords (version 25.2), "Suomi-NPP", "Suomi National Polar-orbiting Partnership" (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/platforms?format=csv, checked on 2026-11-13).

## "BARREL 2K X-ray Spectrometer (MSPC) Bremsstrahlung X-ray Spectrum Medium Time Resolution, Level 2, 4 s Data" (pool position 51, id 2445fb91-d303-487f-a07e-6f0d0742c338)

A tuning record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. The record repeats the text of the held-out record "BARREL 2D X-ray Spectrometer (SSPC) Bremsstrahlung X-ray Spectrum Slow Time Resolution, Level 2, 32 s Data" (pool position 71), with another payload, another variable, another number of channels, another time resolution and another energy range, and its decisions are copied from that record. Its paragraphs about the mission repeat those of the tuning record "BARREL 4G Rate Counter (RCNT) NaI Scintillator Diagnostics, Level 2, 4 s Data" (pool position 19), whose decisions are the same. 45 items, 18 that may matter.

- **Left out:** "2K" (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"
  - **May matter because:** my reading, not checked: the balloon payload's code (campaign 2, payload K), as "4G" in the record "BARREL 4G Rate Counter (RCNT) NaI Scintillator Diagnostics, Level 2, 4 s Data"; it tells this dataset from its siblings and gives its campaign.
  - **Question:** Q6 (b).
- **Left out:** "(MSPC)" as part of the instrument's name (title, "X-ray Spectrometer (MSPC)")
  - **Rule:** Writing a classed triple, rule 20: "Parentheses that hold the code of another entity are taken out of the instance."
  - The notes say that MSPC is the name of the variable ("All channels are combined to a single variable named MSPC"), written as HAS_VARIABLE "MSPC". "MSPC" is not an abbreviation of "X-ray Spectrometer" by rule 20's test (its first letter, "M", does not start "X-ray", the first of those words), so the instrument is "X-ray Spectrometer", the wording of "Each BARREL balloon carried an X-ray spectrometer" (rule 23: they differ only in capitals).
- **Left out:** "Medium Time Resolution" (title) and "medium" (notes, "48 channels of medium time resolution, 4 s")
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words."
  - HAS_TEMPORAL_RESOLUTION "4 s" states the resolution, the wording that says more (rule 23).
- **Left out:** "Bremsstrahlung X-ray Spectrum" (title) as a wording of its own
  - **Rule:** Writing a classed triple, rule 23: "When a record names the same entity more than once, in different words, use the wording the first of the four tests below picks, in every ground truth triple"
  - The form is written in the notes' wording, HAS_SPATIAL_REPRESENTATION "Bremsstrahlung X-ray spectra" (rule 23, test 2: the notes' sentence states a fact about the spectra with words for it, "detected with a NaI Scintillator").
- **Left out:** "Bremsstrahlung X-ray" as a thing of its own (notes, inside "Bremsstrahlung X-ray spectra")
  - **Rule:** What counts as a fact, rule 2, *A fact inside a name*: "When the naming states more than one predicate, or none, the name's words give no ground truth triple, since choosing one would add what the record does not state."
  - No predicate of the ground truth schema says what radiation a form of data is of, and the X-rays are not a bare property (PhysicalQuantity), so the name states no predicate. The spectrometer's purpose names them: HAS_PURPOSE "measure the bremsstrahlung X-rays produced by precipitating relativistic electrons as they collide with neutrals in the atmosphere".
  - **May matter because:** a search by what the data measure would need the X-rays.
- **Left out:** "nominal" (notes, "The nominal energy range covered by the 48 channels ranges from 0 MeV to 4 MeV")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance"
  - HAS_ENERGY_RANGE "from 0 MeV to 4 MeV" is written; "nominal" says that the range is the one the channels were designed for, which is how the fact holds.
- **Left out:** "combined" (notes, "All channels are combined to a single variable named MSPC")
  - **Rule:** Writing a classed triple, rule 24: "A verb or participle that says only what was done to the data ("corrected", "calibrated", "detrended", "binned", "mapped", "edited", "convert", "weighted") names no method"
  - The variable is written: HAS_VARIABLE "MSPC".
- **Left out:** what "NaI" stands for (notes, "detected with a NaI Scintillator")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"
  - The name stays whole, and its entity class, Instrument, is given by the record's own kind word "Scintillator" (rule 1: "A name whose own words say what kind of thing it is … is explained by the record's own words"): the record's dataset ACQUIRED_BY_INSTRUMENT "NaI Scintillator", since the record says the spectra were "detected with" it. In the record "BARREL 4G Rate Counter (RCNT) NaI Scintillator Diagnostics, Level 2, 4 s Data" the same words stand only inside the Variable "NaI Scintillator Diagnostics", with no words that state a fact about the scintillator.
- **Left out:** the launch stations and their places (notes, "with launches from two stations located in Antarctica: the British base located at Halley Bay on the Brunt Ice Shelf and the South African SANAE IV base", and "Later campaigns were undertaken in 2015 and 2016 from the Esrange Space Center located in Kiruna, Sweden")
  - **Rule:** What counts as a fact, rule 2: "or it waits on an expert's answer" (Q8 (c): whether a station or a space center is an Organization or a place).
  - No clear would-be triple: whether a station is an Organization or a place decides its entity class and its predicates (LAUNCHED_FROM and LOCATED_IN for a place, none of them in the ground truth schema; BASED_IN "British", "South African" and "Sweden" for an Organization), so no row can be written in annotations/pending_triples.csv until Q8 (c) is answered. The record "BARREL 4G Rate Counter (RCNT) NaI Scintillator Diagnostics, Level 2, 4 s Data" leaves them out the same way.
  - **May matter because:** a search by launch site or region (Antarctica, Sweden) would need them.
  - **Question:** Q8 (c).
- **Left out:** "South African" (notes, inside the name "South African National Antarctic Expedition") as a Country of its own
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names" The record names no country. The ground truth schema's Country is "a nation", "South African" is an adjective, the record never writes "South Africa", and an instance is the record's own words (Writing a classed triple, rule 11: "Don't paraphrase them").
  - **May matter because:** it says where the expedition is based, which a search by country would need.
  - **Question:** Q8 (c), with the launch stations.
- **Left out:** what "CDF" stands for (notes, "all BARREL CDF data products")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what CDF is. Its entity class, FileFormat, is written (the record's dataset HAS_FILE_FORMAT "CDF", with the source text "all BARREL CDF data products"; the record's dataset is one of these products by rule 1's *Membership by name*, as for HAS_VERSION "Version 10", and "all" makes the format each member's), by rule 1's *A name the record does not explain*.
  - The reference: Wikidata, Common Data Format (Q1116060), also named "CDF", "file format family for multi-dimensional data", an instance of "file format family" (https://www.wikidata.org/wiki/Q1116060, checked on 2026-11-13). No official NASA list names it: the GCMD Instruments, Platforms and Providers keywords (version 25.2) have no entry for it.
- **Left out:** "was a multiple-balloon investigation" (notes)
  - **Rule:** What counts as a fact, rule 4: "A sentence that says what type of entity an instance refers to ("Kestrel is an imager") gives no ground truth triple: the instance's entity class says it"
  - **May matter because:** it says the mission used many balloons at once.
- **Left out:** "Mission of Opportunity" and "Selected" (notes)
  - **Rule:** What counts as a fact, rule 4: "the type is left out, and the belonging is a ground truth triple" ("BARREL" PART_OF "NASA Living with a Star"); "Selected" names no party (rule 1: "Never add what you know from elsewhere").
  - **May matter because:** it is NASA's funding category for the mission.
- **Left out:** "Each" (notes, "Each BARREL balloon")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance"
- **Left out:** "near latitudes close to either the antarctic and arctic circles" (notes)
  - **Rule:** What counts as a fact, rule 1, *Membership by name*: "A statement about the group as a whole is not written for it": "either … or". Which circle this payload flew near is not stated.
  - **May matter because:** a search by region (Antarctic, Arctic) would need it.
  - **Question:** Q24.
- **Left out:** "stratospheric altitudes" (notes)
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words." OBSERVED_AT_ALTITUDE "about 30 km" is the wording that says more (rule 23).
- **Left out:** "first balloon" (notes, "provided the first balloon measurements")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance"
  - **May matter because:** it says BARREL was the first to measure this from balloons.
- **Left out:** "while comprehensive in situ measurements of both plasma waves and energetic particles were available" (notes)
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names" Whose measurements is not said; "comprehensive" is a judgement (rule 5).
- **Left out:** "Also, the BARREL data has been used to characterize the spatial scale of precipitation at relativistic energies." (notes)
  - **Rule:** What counts as a fact, rule 9: "when the record doesn't name that work, the use gives no ground truth triple." No work that used the data is named; the statement is also about the BARREL data as a whole (rule 1, *Membership by name*).
  - **May matter because:** it says what the data are good for.
  - **Question:** Q24.
- **Left out:** "initially" and "Austral summer months of" (notes)
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance" ("initially"). "Austral summer months": rule 16 of *Writing a classed triple*, since the months, HAS_TIME_SPAN "January and February of 2013" and "of 2014", say when.
  - **May matter because:** "Austral summer" says why those months (the southern summer).
- **Left out:** "Thus, the BARREL balloon constellation constituted an evolving and slowly moving array able to study relativistic electron precipitation from the radiation belts." (notes)
  - **Rule:** What counts as a fact, rule 4: "A sentence that says what type of entity an instance refers to ("Kestrel is an imager") gives no ground truth triple: the instance's entity class says it" ("constituted an … array"); "able to study" is what it could do, not what it was meant for (HAS_PURPOSE "is meant to achieve").
  - **May matter because:** it says the balloons formed a moving array, which is how the mission measured spatial scales.
- **Left out:** "and other ground and space based instruments" (notes)
  - **Rule:** Writing a classed triple, rule 22: "An item that names no specific entity ("his team") gives no ground truth triple"
- **Left out:** "successively" (notes)
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance"
- **Left out:** "approximately 20 kg" as the mass of each balloon (notes, "over 50 small, approximately 20 kg, stratospheric balloons were successively launched")
  - **Rule:** What counts as a fact, rule 9: "An amount or a count per member gives no ground truth triple, unless the predicate itself says "each" (HAS_GRANULE_DURATION, HAS_SPATIAL_RESOLUTION)." The mass is each balloon's, and the sentence names the balloons only by a count ("over 50 … balloons"). The words stay in the count, which is written whole: "BARREL" HAS_NUMBER_OF "over 50 small, approximately 20 kg, stratospheric balloons" (rule 22 of *Writing a classed triple*, *Describing words joined by "and" or a comma*).
  - **May matter because:** it is the mass of each balloon the mission flew.
- **Left out:** "The website creeated and hosted by A.J. Halford (see Information URL below) reports that: "By the end of the campaigns, there were over 90 researchers coordinating on a daily basis with the BARREL team working on 7 different satellite missions, 1 other balloon mission, and way too many ground based instruments to count."" (notes)
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names" The researchers are named only by a count, and "way too many" is a judgement (rule 5). The website itself is a ground truth triple: the record's dataset DOCUMENTED_AT "website creeated and hosted by A.J. Halford" (Document), with DEVELOPED_BY_PARTY and PROVIDED_BY_PARTY "A.J. Halford" (Person).
  - **May matter because:** it gives the mission's reach.
- **Left out:** "only" (notes, "launched only balloons")
  - **Rule:** What counts as a fact, rule 6: "A ground truth triple can't say "not"." "only" says nothing else was launched.
- **Left out:** "research using data collected on these flights is ongoing, so stay tuned for updates!" (notes)
  - **Rule:** What counts as a fact, rule 10: "Take out "latest", "current", "now", "then available", and words like them." ("ongoing"); "stay tuned" names nothing (rule 9).
- **Left out:** "All data and analysis software are freely available to the scientific community." (notes)
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words." For the data: HAS_ACCESS_RIGHTS "freely available to the public" says more. "analysis software": rule 9, no particular software is named.
- **Left out:** "primarily" (notes)
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance"
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
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the entity," The policy is the instance, AVAILABLE_AT its address.
- **Left out:** what "NASA" is (notes, "a NASA Living with a Star Mission of Opportunity")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what NASA is. Its entity class, Organization, is written ("NASA Living with a Star" PART_OF "NASA"), by rule 1's *A name the record does not explain*.
  - The reference: GCMD Providers keywords (version 25.2), the level "NASA" under "GOVERNMENT AGENCIES-U.S. FEDERAL AGENCIES", which holds NASA's centers and offices (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/providers?format=csv, checked on 2026-11-13).
- **Left out:** what "Earth" is (notes)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what Earth is. Its entity class, CelestialBody, is written (HAS_TARGET "Earth"), by rule 1's *A name the record does not explain*.
  - The reference: PDS4 context product urn:nasa:pds:context:target:planet.earth, "Earth", of type Planet (https://pds.nasa.gov/data/pds4/context-pds4/target/planet.earth_1.1.xml, checked on 2026-11-13).
- **Left out:** what "NASA Living with a Star" is (notes, "Selected as a NASA Living with a Star Mission of Opportunity")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what NASA Living with a Star is. Its entity class, Organization, is written (PART_OF "NASA"), by rule 1's *A name the record does not explain*. A program that an organization runs is an Organization, one of that organization's named parts, which the ground truth schema's Organization includes ("a named institution or one of its named parts, not a Mission"). Living with a Star is a program of NASA, and the program itself collects no data, so it is not a Mission.
  - The reference: Wikidata Q1705257, "Living With a Star", "scientific program of NASA to study the Sun-Earth system", an instance of "NASA program" (https://www.wikidata.org/wiki/Q1705257, checked on 2026-11-13).
- **Left out:** "2016 campaign" HAS_NUMBER_OF "eight flights" (notes, "The 2015 and 2016 campaigns were undertaken in coordination with" … "A total of eight flights occurred during August 2016.")
  - **Rule:** What counts as a fact, rule 1: "A fact that the record does not state may be written only when it follows from what the record states by one of the three tests below (Replacement, Comparison, Membership by name); nothing else, and no outside knowledge, adds such a fact. The list of tests is closed". The sentence gives the eight flights a month, August 2016, and names no campaign. That they are the flights of the 2016 campaign follows from this sentence and the sentences that name the campaign, by none of the three tests (*Replacement*, *Comparison*, *Membership by name*), as in the record "BARREL 4G Rate Counter (RCNT) NaI Scintillator Diagnostics, Level 2, 4 s Data".
  - **May matter because:** it is the number of flights of the 2016 campaign, as "Seven balloon launches" is for the campaign of August 2015.
- **Left out:** the 2013, the 2014 and the 2016 campaign PART_OF "BARREL" (notes, "For the 2013 and 2014 the balloon campaigns", "The 2015 and 2016 campaigns" … "Summing over the four BARREL campaigns")
  - **Rule:** What counts as a fact, rule 1: "A fact that the record does not state may be written only when it follows from what the record states by one of the three tests below (Replacement, Comparison, Membership by name); nothing else, and no outside knowledge, adds such a fact. The list of tests is closed". The record names one campaign with the mission's name ("August 2015 BARREL campaign" PART_OF "BARREL", rule 2's *A fact inside a name*). No passage states that the 2013, the 2014 or the 2016 campaign is a campaign of BARREL: it follows from counting the campaigns the record describes up to "the four BARREL campaigns", by none of the three tests (*Replacement*, *Comparison*, *Membership by name*), as in the record "BARREL 4G Rate Counter (RCNT) NaI Scintillator Diagnostics, Level 2, 4 s Data".
  - **May matter because:** without them no ground truth triple connects the three campaigns to the mission.

## "SENTINEL-1B_METADATA_RAW" (pool position 52, id 0c8a329f-6510-4167-9295-2437ca71e66e)

A tuning record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. Its describes class is Dataset: the notes call the catalog entry metadata, information about another product's data. No predicate of the ground truth schema says that one dataset is the metadata of another, so METADATA_FOR was coined for this record ("holds the metadata of this one: information that describes its data"). 4 items, 1 that may matter.

- **Left out:** "Metadata" as what the catalog entry is (notes, "Metadata for Sentinel-1B level zero product")
  - **Rule:** What counts as a fact, rule 4: "the type is left out, and the belonging is a ground truth triple"
  - The phrase says what kind of thing the catalog entry is and what it belongs to: the kind is the describes class, and the belonging is METADATA_FOR "Sentinel-1B product".
- **Left out:** "level zero" and "Sentinel-1B" as facts of the product (notes, "Metadata for Sentinel-1B level zero product")
  - **Rule:** Writing a classed triple, rule 21: "Leave out facts about other datasets, such as a variant of the record's dataset (the same data at another temporal resolution, spatial resolution, or version), or a product made from it."
  - **May matter because:** a search for the metadata of Sentinel-1B level zero data would need them.
  - The product is another dataset, which the record links to its dataset neither by "part of" nor by "made from". Its processing level, "level zero" ("Level" followed by a number, rule 1), is taken out of its instance by rule 19 of *Writing a classed triple*, and its would-be ground truth triples, "Sentinel-1B product" HAS_PROCESSING_LEVEL "level zero" and "Sentinel-1B product" FROM_PLATFORM "Sentinel-1B" (rule 2, *A fact inside a name*), are left out. "product" stays in the instance, since "Sentinel-1B" alone is the name of another thing, the craft (rule 23 of *Writing a classed triple*, *Type words*).
- **Left out:** "SENTINEL-1B", "METADATA" and "RAW" (title)
  - **Rule:** Writing a classed triple, rule 17: "A title's words give a fact only where a predicate fits what they state" (*A title's facts*)
  - "SENTINEL-1B" and "METADATA" are the title's wordings of the notes' "Metadata for Sentinel-1B" (rule 16). The title's "SENTINEL-1B" gives the record's dataset no FROM_PLATFORM ("was collected from this Platform"): the record does not state that the metadata of a product of the craft were collected from it, as an ephemeris of a craft is not in the record "Solar Orbiter Ephemeris, Heliocentric Trajectories, Heliographic, Heliographic Inertial, and Solar Ecliptic Coordinates, HelioWeb, Daily Data". My reading, not checked: "RAW" is the title's wording of the product's "level zero"; a word that only says how far data are processed is not a processing level (rule 19, *A processing level*).
- **Left out:** what "Sentinel-1B" is (title and notes)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what Sentinel-1B is. Its entity class, Platform, would be given by rule 1's *A name the record does not explain*; the name is written only inside the instance "Sentinel-1B product" (rule 11 of *Writing a classed triple*), and the product's FROM_PLATFORM is left out (the item above).
  - The list: GCMD Platforms keywords (version 25.2), "Sentinel-1B", under Earth Observation Satellites, Sentinel-1 (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/platforms?format=csv, checked on 2026-11-13).

## "DEEP IMPACT 9P/TEMPEL CRUISE - RAW MRI NAV IMAGES V1.0" (pool position 53, id 7edfd387-7276-4030-b01e-a15d6f7da5c9)

A held-out record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. 6 items, 1 that may matter.

- **Left out:** "These observations were used for optical and autonomous navigation (NAV) of the flyby spacecraft." (notes), and the title's "NAV"
  - **Rule:** What counts as a fact, rule 9: "What data have been used for, or can be used for, is a fact of the work that used them, not of the data: when the record doesn't name that work, the use gives no ground truth triple."
  - The navigation is the use itself, and no work that used the data is named. "the flyby spacecraft" is not a name, and the record does not say that it carries the instrument (rule 9: "A ground truth triple needs a subject and an object the record names.").
  - **May matter because:** it says what the images were taken for.
- **Left out:** "phase", "the mission" and "comet" (notes, "during the cruise phase of the mission" and "Test images of comet 9P/Tempel 1")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the entity,"
  - My ground truth triples have the phase "cruise" and the target "9P/Tempel 1". "the mission" names the mission in other words, and is written "Deep Impact", the one mission the record names (rule 23).
- **Left out:** "RAW", "CRUISE", "IMAGES" and "TEMPEL" (title) as facts of their own
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words."
  - The notes state them: "raw calibration and test images" (the two parts, and HAS_SPATIAL_REPRESENTATION "images"), "the cruise phase" (HAS_MISSION_PHASE "cruise") and "comet 9P/Tempel 1". The title's "9P/TEMPEL" is two items (rule 22, *Lists joined by "/" or "+"*), and both give HAS_TARGET "9P/Tempel 1", the wording that says more (rule 23).
- **Left out:** what "Deep Impact" is (title, "DEEP IMPACT", and notes, inside "Deep Impact Medium Resolution Instrument Visible CCD")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what Deep Impact is. Its entity class, Mission, is written (FROM_MISSION "Deep Impact", and PART_OF "Deep Impact" of the camera's CCD and of "cruise"), by rule 1's *A name the record does not explain*.
  - The list: PDS4 context product urn:nasa:pds:context:investigation:mission.deep_impact, "Deep Impact", of type Mission, also titled "DEEP IMPACT" (https://pds.nasa.gov/data/pds4/context-pds4/investigation/mission.deep_impact_1.2.xml, checked on 2026-11-13). The craft's entry, urn:nasa:pds:context:instrument_host:spacecraft.dif, is "The Deep Impact Flyby (DIF) Spacecraft", not "Deep Impact".
- **Left out:** what "Deep Impact Medium Resolution Instrument Visible CCD" and "MRI" are (notes and title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record's own kind words, "Instrument" and "CCD", give the entity class, Instrument. The title's "MRI" abbreviates the "Medium Resolution Instrument" inside the notes' name (rule 23: "what you know about the words (e.g. what an abbreviation stands for"), so the record's dataset ACQUIRED_BY_INSTRUMENT "Medium Resolution Instrument", in the wording that spells it out, and "Deep Impact Medium Resolution Instrument Visible CCD" PART_OF "Medium Resolution Instrument" (rule 2, *A fact inside a name*), as "OSIRIS Narrow Angle Camera" PART_OF "OSIRIS" in the record "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0".
  - The list: PDS4 context product urn:nasa:pds:context:instrument:dif.mri, "The Medium Resolution Instrument (MRI) for Deep Impact", also titled "DEEP IMPACT MEDIUM RESOLUTION INSTRUMENT - VISIBLE CCD" (https://pds.nasa.gov/data/pds4/context-pds4/instrument/dif.mri_1.2.xml, checked on 2026-11-13). The list gives the entity class only (rule 1), so its reading of the CCD's name as the whole instrument is not used.
- **Left out:** what "9P/Tempel 1" is (title, "9P/TEMPEL", and notes, "comet 9P/Tempel 1")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record's type word "comet" says what kind of thing 9P/Tempel 1 is. Its entity class, CelestialBody, is written (HAS_TARGET "9P/Tempel 1", of the record's dataset and of "raw test images").
  - The reference: PDS4 context product urn:nasa:pds:context:target:comet.9p_tempel_1, "9P/Tempel 1", of type Comet (https://pds.nasa.gov/data/pds4/context-pds4/target/comet.9p_tempel_1_1.1.xml, checked on 2026-11-13).

## "BOREAS TF-08 NSA-OJP and SSA-OBS Ceilometer Data" (pool position 54, id 002f1a9d-b125-4908-a75d-4c75fe344438)

A tuning record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. The team that collected the data is written as the party that made the record's dataset (DEVELOPED_BY_PARTY, as for a catalog "created by" an archive in the record "Ensemble X-Ray Variability of AGN in 2XMMi-DR3"), and the sites where the data were collected as the areas the data cover (HAS_SPATIAL_COVERAGE). 6 items, 3 that may matter.

- **Left out:** what "BOREAS" is (title, and notes, "The BOREAS TF-08 team")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". No reference of rule 1's *A name the record does not explain* names it: the GCMD Instruments, Platforms and Providers keywords (version 25.2) have no entry for it, and Wikidata's entries named "Boreas" are a journal, a god of Greek myth and others, none of them a study of the Earth (checked on 2026-11-13). So the title's "BOREAS" gives no FROM_MISSION, and the team gives no PART_OF; the word stays in the team's instance (rule 11 of *Writing a classed triple*).
  - **May matter because:** my reading, not checked: the Boreal Ecosystem-Atmosphere Study, a field study; a search by project would need it.
- **Left out:** what "TF-08" stands for (title, and notes, "The BOREAS TF-08 team")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"
  - The record's own word "team" gives the team its entity class, Organization. "team" stays in the instance, "BOREAS TF-08 team", as in "BARREL team" in the record "BARREL 4G Rate Counter (RCNT) NaI Scintillator Diagnostics, Level 2, 4 s Data": the title uses "BOREAS TF-08" for the data set too, so the words left once "team" is taken out are not shown to be the team's name (rule 23 of *Writing a classed triple*, *Type words*).
- **Left out:** what "NSA-OJP" and "SSA-OBS" stand for (title, and notes, "at the NSA-OJP site" and "at the NSA-OJP and SSA-OBS sites")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"
  - **May matter because:** my reading, not checked: two study sites and the kind of forest at each; a search by place or by forest would need them.
  - The record's own word "site" says what they are, places, and the data were collected at them, so they are written as the areas the data cover, HAS_SPATIAL_COVERAGE "NSA-OJP" and "SSA-OBS" (rule 23 of *Writing a classed triple* takes out "site" and "sites", type words).
- **Left out:** which site was observed in which year (notes, "Ceilometer data were collected at the NSA-OJP site in 1994 and at the NSA-OJP and SSA-OBS sites in 1996")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance: its subject would be that fact, not an entity the record names."
  - **May matter because:** a search for one site's data in one year would need it.
  - The sites (HAS_SPATIAL_COVERAGE) and the years (HAS_TIME_SPAN "1994" and "1996") are written as facts of the record's dataset. That the SSA-OBS data are from 1996 only would be a fact about one of those facts, a qualifier kept with the ground truth triple it holds for, which is future work (docs/improvements.md, *Rule 19 can lose which fact a qualifier went with*).
- **Left out:** "used ceilometers" as a fact of the team (notes, "The BOREAS TF-08 team used ceilometers to collect data")
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words."
  - The sentence is written as two facts of the record's dataset, which the team collected: ACQUIRED_BY_INSTRUMENT "ceilometers" and DEVELOPED_BY_PARTY "BOREAS TF-08 team".
- **Left out:** "Ceilometer" (title, "Ceilometer Data", and notes, "Ceilometer data were collected") as a wording of its own
  - **Rule:** Writing a classed triple, rule 23: "Otherwise, the wording from a sentence that states a fact about the entity with words for its predicate, rather than one that names it only by a title's or a name's words"
  - The instrument is written "ceilometers", the wording of "used ceilometers to collect data", which states the fact with words for it (test 2).

## "ROSETTA-ORBITER 67P OSIWAC 4 ESC2-MTP015 RDR-REFLECT V1.0" (pool position 55, id 7c37b7a0-c9d4-49aa-bf26-687a49d4e97f)

A tuning record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. The record repeats the text of the tuning record "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP019 RDR-INFLDSTR V1.0" (pool position 37), with another camera, another mission phase, another planning period, another period covered, fewer corrections, another unit and another review, and its decisions are copied from that record. 8 items, 3 that may matter.

- **Left out:** "MTP015" (title, "ESC2-MTP015")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"
  - **May matter because:** it tells this dataset from its siblings, as "MTP020" does in the record "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0" (its item; not checked for this record).
  - **Question:** Q6 (b).
- **Left out:** "RDR" and "REFLECT" (title, "RDR-REFLECT")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"
  - The record "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP019 RDR-INFLDSTR V1.0" leaves out "RDR" and "INFLDSTR" the same way. If "REFLECT" shortens the notes' "reflectance units", the unit is written in the notes' wording, HAS_UNIT "reflectance units (normalized and thus without unit)" (rule 23 of *Writing a classed triple*, test 1), so the title's word gives no ground truth triple either way.
  - **Question:** Q6 (b).
- **Left out:** "prime" (notes, "The prime target is comet 67P/Churyumov-Gerasimenko 1 (1969 R1)")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance"
  - **May matter because:** a search for other bodies in these images would need it.
  - HAS_TARGET says the dataset is about the comet; "prime" says only that it is the main target, how that fact holds, as in the record "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0".
- **Left out:** "comet" (notes, "comet 67P/Churyumov-Gerasimenko 1 (1969 R1)")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the entity,"
- **Left out:** "spacecraft" and "mission phase" (notes, "the Rosetta spacecraft" and "the COMET ESCORT 2 mission phase")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the entity,"; "the Rosetta spacecraft" is written as "ROSETTA-ORBITER", the wording that says more (rule 23).
- **Left out:** "Lien" (notes, "Lien corrected dataset after October 2018 PSA/PDS external peer review")
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words."
  - My ground truth triple REVISED_AFTER "October 2018 PSA/PDS external peer review" says the dataset was corrected after the review; "Lien" names what was corrected, the issues the review raised, as in the record "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0".
- **Left out:** PRODUCED_USING_ALGORITHM "radiometric calibrated" and "geometric distortion corrected (resampled)" (notes, "contains radiometric calibrated and geometric distortion corrected (resampled) image data")
  - **Rule:** Writing a classed triple, rule 24: "A verb or participle that says only what was done to the data ("corrected", "calibrated", "detrended", "binned", "mapped", "edited", "convert", "weighted") names no method"
  - **May matter because:** it says which corrections were applied to the images.
  - The words describe the data and name no method. What was corrected is written: CLEANED_OF "geometric distortion" (rule 24: "What a step removed from the data, or corrected in them, is neither the step's input nor its method"); "radiometric calibrated" names nothing removed.
  - **Question:** Q7 (c).
- **Left out:** what "OSIRIS" stands for (notes, inside the name "OSIRIS Wide Angle Camera")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record names "OSIRIS" only inside the camera's name and never says what it is. Its entity class, Instrument, is written ("OSIRIS Wide Angle Camera" PART_OF "OSIRIS"), by rule 1's *A name the record does not explain*.
  - The reference: Wikidata, Optical, Spectroscopic, and Infrared Remote Imaging System (Q7098805), also named "OSIRIS", "scientific instrument on the Rosetta spacecraft", an instance of "space instrument" (https://www.wikidata.org/wiki/Q7098805, checked on 2026-11-13). No official NASA list names it: the PDS4 context products have entries for its two cameras (urn:esa:psa:context:instrument:ro.osinac and ro.osiwac) and none for OSIRIS itself.

## "ROSETTA-ORBITER 67P ROSINA 2 EXT2 V2.0" (pool position 56, id 8e66de36-8623-4280-a913-02f03a930a91)

A held-out record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. 8 items, none that may matter.

- **Left out:** what "COPS", "DFMS" and "RTOF" stand for (notes, "the COPS, DFMS and RTOF ROSINA sensors")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"
  - Their entity class, Instrument, is the record's own type word "sensors". "sensor" stays in each instance, "COPS ROSINA sensor" and the others, since "COPS ROSINA" is not a name (rule 23 of *Writing a classed triple*, *Type words*), as in "GRaND plus Z boron loaded sensor" in the record "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0".
- **Left out:** "PDS" (notes, "Some missing DFMS PDS files were added")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"
- **Left out:** "Some" (notes, "Some missing DFMS PDS files were added")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance"
- **Left out:** "mission" and "comet" (notes, "the Rosetta mission at the comet 67P/CG")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the entity,"
  - My ground truth triples have the mission "Rosetta" and the target "67P/CG".
- **Left out:** "2" and "EXT2" (title) as facts of their own
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words."
  - The notes state them in the wordings that say more: "CODMAC level 2" (HAS_PROCESSING_LEVEL), as in the record "ROSETTA-ORBITER 67P/CAL ALICE 2 ESC1 V1.0", and "Extension phase 2" (HAS_MISSION_PHASE), which spells out "EXT" (rule 23).
- **Left out:** what "ROSETTA-ORBITER" is (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what ROSETTA-ORBITER is. Its entity class, Platform, is written (FROM_PLATFORM "ROSETTA-ORBITER"), by rule 1's *A name the record does not explain*.
  - The list: PDS4 context product urn:esa:psa:context:instrument_host:spacecraft.ro, "The Rosetta Orbiter Spacecraft", of type Spacecraft, also titled "ROSETTA-ORBITER" (https://pds.nasa.gov/data/pds4/context-pds4/instrument_host/spacecraft.ro_1.1.xml, checked on 2026-11-13).
- **Left out:** what "ROSINA" stands for (title and notes)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what ROSINA is. Its entity class, Instrument, is written (ACQUIRED_BY_INSTRUMENT "ROSINA", and the three sensors PART_OF "ROSINA", by rule 2's *A fact inside a name*), by rule 1's *A name the record does not explain*.
  - The list: PDS4 context product urn:esa:psa:context:instrument:ro.rosina, "The Rosetta Orbital Spectrometer for Ion and Neutral Analysis (ROSINA)" (https://pds.nasa.gov/data/pds4/context-pds4/instrument/ro.rosina_1.2.xml, checked on 2026-11-13).
- **Left out:** what "67P/CG" is (title, "67P", and notes, "the comet 67P/CG")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record's type word "comet" says what kind of thing 67P/CG is. Its entity class, CelestialBody, is written (HAS_TARGET "67P/CG"). "67P/CG" stays whole, since "CG" is never named alone (rule 22 of *Writing a classed triple*, *Lists joined by "/" or "+"*).
  - The reference: Wikidata, 67P/Churyumov–Gerasimenko (Q844672), whose other names include "67P" and "67P/C-G", an instance of "Jupiter-family comet" (https://www.wikidata.org/wiki/Q844672, checked on 2026-11-13).

## "VG1 SAT PWS EDITED SPECTRUM ANALYZER 4.0SEC V1.0" (pool position 59, id ef9ab3db-bef3-490f-8e24-0394345c39b6)

A held-out record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. 15 items, 8 that may matter.

- **Left out:** "SAT" (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"
  - **May matter because:** my reading, not checked: the PDS target code for Saturn, as "J/S/SS" in the record "VG1 J/S/SS PWS EDITED SPECTRUM ANALYZER FULL RES V1.0", while the notes say the data were obtained near "the Jovian magnetosphere"; if so, the title and the notes disagree.
  - **Question:** Q6 (b).
- **Left out:** "Jovian" as Jupiter (notes, "in the vicinity of the Jovian magnetosphere")
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names"
  - "Jovian" is an adjective and names no body, as "German" in the record "SOLVE I Ground Site Data". The area is written: HAS_SPATIAL_COVERAGE "vicinity of the Jovian magnetosphere"; "vicinity" stays, since the record does not say the data were obtained inside the magnetosphere (rule 11 of *Writing a classed triple*).
  - **May matter because:** a search by target would need Jupiter.
- **Left out:** "EDITED", "SPECTRUM ANALYZER" and "4.0SEC" (title) as facts of their own
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words."
  - The notes state them: "edited, wave electric field intensities" (HAS_MEASUREMENTS_OF), the "Voyager 1 Plasma Wave Receiver spectrum analyzer" (ACQUIRED_BY_INSTRUMENT) and "4-second" (HAS_TEMPORAL_RESOLUTION, the wording that spells out "SEC", rule 23).
- **Left out:** "edited" as a method (notes, "4-second edited, wave electric field intensities" and "Data are edited")
  - **Rule:** Writing a classed triple, rule 24: "A verb or participle that says only what was done to the data ("corrected", "calibrated", "detrended", "binned", "mapped", "edited", "convert", "weighted") names no method"
  - It stays in the instance, as written: HAS_MEASUREMENTS_OF "edited, wave electric field intensities". The record does not say what was edited out, so no CLEANED_OF triple is written, unlike the record "VG1 J/S/SS PWS EDITED SPECTRUM ANALYZER FULL RES V1.0".
- **Left out:** "but not calibrated" (notes, "Data are edited but not calibrated.")
  - **Rule:** What counts as a fact, rule 6: "A ground truth triple can't say "not", and a negated fact is not rewritten into a fact the record doesn't state."
  - **May matter because:** it says that the values are not calibrated.
- **Left out:** "center" (notes, "channels whose center frequencies range from 10 Hertz to 56.2 kiloHertz")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance"
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
  - **Rule:** Writing a classed triple, rule 24: "A verb or participle that says only what was done to the data ("corrected", "calibrated", "detrended", "binned", "mapped", "edited", "convert", "weighted") names no method"
  - "zero-filled" says what was done to the values and names no method.
  - **May matter because:** a zero in the data may stand for a missing measurement.
- **Left out:** "can be plotted in raw form for event searches and simple trend analysis" (notes)
  - **Rule:** What counts as a fact, rule 9: "What data have been used for, or can be used for, is a fact of the work that used them, not of the data: when the record doesn't name that work, the use gives no ground truth triple."
  - "can be plotted" is also a possibility, not a statement (rule 7). The reason the sentence gives is written: ROUGHLY_PROPORTIONAL_TO "log of the electric field strength".
- **Left out:** "the use of these is described below" (notes)
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names"
  - The record's text has nothing below this sentence.
- **Left out:** what "PWS" is (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what PWS is. Its entity class, Instrument, is written (ACQUIRED_BY_INSTRUMENT "PWS"), by rule 1's *A name the record does not explain*. The reference gives the entity class only, and "PWS" does not abbreviate the notes' "Plasma Wave Receiver" (rule 23), so the two are written as two instances.
  - The list: PDS4 context product urn:nasa:pds:context:instrument:vg1.pws, "Plasma Wave Receiver for VG1", whose earlier identifier is urn:nasa:pds:context:instrument:pws.vg1: "PWS" is its instrument id, as "MRS" is in the record "MARS EXPRESS MARS MRS 1/2/3 EXTENDED MISSION 8 4193 V1.0" (https://pds.nasa.gov/data/pds4/context-pds4/instrument/vg1.pws_1.2.xml, checked on 2026-11-13).
  - **May matter because:** by the list, "PWS" and the "Plasma Wave Receiver" are one instrument, which the ground truth then names twice.
- **Left out:** what "Voyager 1" is (title, "VG1", and notes, "the Voyager 1 Plasma Wave Receiver spectrum analyzer")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what Voyager 1 is. Its entity class, Platform, is written (FROM_PLATFORM "Voyager 1", and "Voyager 1 Plasma Wave Receiver spectrum analyzer" ABOARD "Voyager 1"), by rule 1's *A name the record does not explain*.
  - The reference: PDS4 context product urn:nasa:pds:context:instrument_host:spacecraft.vg1, "VOYAGER 1", of type Spacecraft, with the host id "VG1" (https://pds.nasa.gov/data/pds4/context-pds4/instrument_host/spacecraft.vg1_1.5.xml, checked on 2026-11-13).

## "CALIPSO Lidar Level 2 Vertical Feature Mask (VFM), V5-00" (pool position 62, id 9e49a827-733f-4a15-89e1-5f609f9a6b6e)

A held-out record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. 12 items, 3 that may matter.

- **Left out:** "Lidar" (title) and "CALIPSO Lidar" (notes, "the Cloud-Aerosol Lidar and Infrared Pathfinder Satellite Observation (CALIPSO) Lidar Level 2 Vertical Feature Mask (VFM) data product") as facts of their own
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words."
  - They name the instrument the notes spell out, "Cloud-Aerosol Lidar with Orthogonal Polarization (CALIOP)", the one lidar the record names (rule 23: the wording that says more). Its ABOARD triple is written from "The CALIPSO satellite carried three remote sensing instruments".
- **Left out:** "satellite", "instrument", "constellation" and "data product" (notes)
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the entity,"
- **Left out:** "French" as a country (notes, "the French Space Agency, CNES")
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names"
  - "French" is an adjective and names no country, as "German" in the record "SOLVE I Ground Site Data". The words stay in the Role, "CNES" SERVES_AS "French Space Agency", as "Argentina's space agency" in the record "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005". "CNES" after the comma fails the abbreviation test of rule 20 of *Writing a classed triple* (its first letter does not start "French"), and the words are read as the agency's role and its name, not as two partners.
- **Left out:** "many" (notes, "to study the many roles played by clouds and aerosols")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance"
- **Left out:** "for coincident Earth observations" and "from launch until September 13, 2018" (notes, "It flew in the international A-Train constellation for coincident Earth observations from launch until September 13, 2018")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance"
  - Both say how the fact "flew in the international A-Train" held, what for and when, so their subject would be that fact, not a thing the record names. FLIES_IN "international A-Train" is written.
  - **May matter because:** they say why CALIPSO flew in the A-Train, and when it left it.
- **Left out:** "to resume formation flying with CloudSat as part of the “C-Train”" (notes)
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance"
  - It says what the lowering of the orbit was for, so its subject would be that fact. CloudSat is a platform in the GCMD Platforms keywords (version 25.2) (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/platforms?format=csv, checked on 2026-11-13), and the C-Train a former satellite formation in Wikidata (Q92454159, https://www.wikidata.org/wiki/Q92454159, checked on 2026-11-13); neither gives a ground truth triple here.
  - **May matter because:** it names the craft and the formation CALIPSO was moved to join.
- **Left out:** "By mutual agreement between NASA and CNES" (notes, "By mutual agreement between NASA and CNES, the CALIPSO science mission concluded on August 1, 2023.")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance"
  - It says how the mission came to an end; its end is written (ENDED_ON "August 1, 2023").
  - **May matter because:** it says that both partners decided the end.
- **Left out:** "above the Earth" (notes, "lowering its orbit from 705 km to 688 km (428 miles)above the Earth")
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words."
  - HAS_TARGET "Earth" is written from "Earth’s climate and weather".
- **Left out:** "CALIPSO" in "the CALIPSO science mission" as a fact of its own (notes)
  - **Rule:** What counts as a fact, rule 2: "When the naming states more than one predicate, or none, the name's words give no ground truth triple" (*A fact inside a name*)
  - A craft's name inside a mission's name states no predicate of the ground truth schema: rule 2 gives PART_OF for a Mission named in the name of one of its parts, not for the reverse. "CALIPSO science mission" is therefore linked to no other ground truth triple, and its end is still written (rule 21 of *Writing a classed triple*). "science mission" stays in the instance, since "CALIPSO" alone names another thing, the craft (rule 23: "The type word stays in the instance only when the words left once it is taken out aren't a name, or are the name of another thing").
- **Left out:** what "NASA" is (notes, "a partnership between NASA" and "By mutual agreement between NASA and CNES")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what NASA is. Its entity class, Organization, is written (HAS_PARTNER "NASA"), by rule 1's *A name the record does not explain*.
  - The reference: GCMD Providers keywords (version 25.2), the level "NASA" under "GOVERNMENT AGENCIES-U.S. FEDERAL AGENCIES", which holds NASA's centers and offices (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/providers?format=csv, checked on 2026-11-13).
- **Left out:** what "CNES" stands for (notes, "the French Space Agency, CNES")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record's words "the French Space Agency" say what kind of thing CNES is. Its entity class, Organization, is written (HAS_PARTNER "CNES", and "CNES" SERVES_AS "French Space Agency").
  - The reference: GCMD Providers keywords (version 25.2), "FR/CNES", "Centre National d'Etudes Spatiales, France" (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/providers?format=csv, checked on 2026-11-13).
- **Left out:** what "Earth" is (notes, "Earth’s climate and weather")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what Earth is. Its entity class, CelestialBody, is written (HAS_TARGET "Earth"), by rule 1's *A name the record does not explain*.
  - The reference: PDS4 context product urn:nasa:pds:context:target:planet.earth, "Earth", of type Planet (https://pds.nasa.gov/data/pds4/context-pds4/target/planet.earth_1.1.xml, checked on 2026-11-13).

## "ROSETTA-ORBITER 67P NAVCAM 2 COMET ESCORT 1 MTP010 V1.1" (pool position 65, id 0ea5f919-f703-4edd-811d-cf4852a8d8a9)

A held-out record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. 11 items, 3 that may matter.

- **Left out:** "2" (title, "NAVCAM 2")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"; a bare number is not "L" or "Level" followed by a number.
  - **Question:** Q6 (b).
- **Left out:** "MTP010" (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"
  - **May matter because:** it tells this dataset from its siblings, as "MTP020" does in the record "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0" (its item; not checked for this record).
  - **Question:** Q6 (b).
- **Left out:** "RAW" (notes, "ROSETTA NAVCAM RAW DATA")
  - **Rule:** Writing a classed triple, rule 19: "A qualifier that only says how far the data are processed ("raw", "edited", "calibrated", "derived") is not a processing level, and stays in the instance, as written."
  - As in the record "ROSETTA-ORBITER 67P NAVCAM 2 COMET ESCORT 3 MTP019 V1.0": the words name the record's dataset itself, which is written as its title, so the instance the word would stay in is never written.
  - **May matter because:** it says that the images are not processed.
- **Left out:** "Escort Phase" (notes, "RAW DATA of the Escort Phase") as the phase's wording
  - **Rule:** Writing a classed triple, rule 23: "When a record names the same entity more than once, in different words, use the wording the first of the four tests below picks, in every ground truth triple"
  - The title's "COMET ESCORT 1" is more precise, since it holds the phase's number, so test 1 picks it: HAS_MISSION_PHASE "COMET ESCORT 1". "COMET" stays in the instance and gives no HAS_TARGET triple: it names no particular comet, and the record never calls "67P/CG" a comet (rule 9), as in the record "ROSETTA-ORBITER 67P NAVCAM 2 COMET ESCORT 3 MTP019 V1.0".
- **Left out:** "when at the vicinity of" (notes, "when at the vicinity of target 67P/CG")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance"
  - HAS_TARGET "67P/CG" is written; the words say where the craft was when the data were taken.
- **Left out:** "the Browse images" and "the FITS version" as what the record's dataset holds (notes, "It includes updates of the Browse images, adding of the FITS version")
  - **Rule:** What counts as a fact, rule 1: "Only what the record states."
  - That the data set holds browse images and a FITS version follows from the changes the record lists ("V1.1" HAS_CHANGE) but is not stated, as "during the planetary encounters" in the record "VG1 J/S/SS PWS EDITED SPECTRUM ANALYZER FULL RES V1.0". "FITS" is also an unexplained code (rule 1).
  - **May matter because:** a search by file format would need FITS.
- **Left out:** "resolve other minor outstanding errata" (notes)
  - **Rule:** Writing a classed triple, rule 22: "An item that names no specific entity ("his team") gives no ground truth triple"
  - The item names no particular erratum; "minor" is a judgement (rule 5).
- **Left out:** what "ROSETTA-ORBITER" is (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what ROSETTA-ORBITER is. Its entity class, Platform, is written (FROM_PLATFORM "ROSETTA-ORBITER"), by rule 1's *A name the record does not explain*.
  - The list: PDS4 context product urn:esa:psa:context:instrument_host:spacecraft.ro, "The Rosetta Orbiter Spacecraft", of type Spacecraft, also titled "ROSETTA-ORBITER" (https://pds.nasa.gov/data/pds4/context-pds4/instrument_host/spacecraft.ro_1.1.xml, checked on 2026-11-13).
- **Left out:** what "ROSETTA" is (notes, "ROSETTA NAVCAM RAW DATA")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what ROSETTA is. Its entity class, Mission, is written (FROM_MISSION "ROSETTA", and "NAVCAM" PART_OF "ROSETTA", by rule 2's *A fact inside a name*), by rule 1's *A name the record does not explain*.
  - The list: PDS4 context product urn:esa:psa:context:investigation:mission.international_rosetta_mission, "The International Rosetta Mission", of type Mission, also titled "ROSETTA" (https://pds.nasa.gov/data/pds4/context-pds4/investigation/mission.international_rosetta_mission_1.1.xml, checked on 2026-11-13). The craft's entry is titled "ROSETTA-ORBITER", not "ROSETTA".
- **Left out:** what "NAVCAM" stands for (title and notes)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what NAVCAM is. Its entity class, Instrument, is written (ACQUIRED_BY_INSTRUMENT "NAVCAM", and "NAVCAM" PART_OF "ROSETTA"), by rule 1's *A name the record does not explain*.
  - The list: PDS4 context product urn:esa:psa:context:instrument:ro.navcam, "The Navigation Camera (NavCam) for the Rosetta Orbiter" (https://pds.nasa.gov/data/pds4/context-pds4/instrument/ro.navcam_1.2.xml, checked on 2026-11-13); "NAVCAM" and "NavCam" differ only in capitals (rule 23 of *Writing a classed triple*).
- **Left out:** what "67P/CG" is (title, "67P", and notes, "target 67P/CG")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what 67P/CG is. Its entity class, CelestialBody, is written (HAS_TARGET "67P/CG"), by rule 1's *A name the record does not explain*. "67P/CG" stays whole, since "CG" is never named alone (rule 22 of *Writing a classed triple*, *Lists joined by "/" or "+"*), and it says more than the title's "67P" (rule 23).
  - The reference: Wikidata, 67P/Churyumov–Gerasimenko (Q844672), whose other names include "67P" and "67P/C-G", an instance of "Jupiter-family comet" (https://www.wikidata.org/wiki/Q844672, checked on 2026-11-13). The record's "67P/CG" differs from "67P/C-G" only by a hyphen (rule 23). The PDS4 context product urn:nasa:pds:context:target:comet.67p_churyumov-gerasimenko names the comet "67P/Churyumov-Gerasimenko" only, a wording this record does not use.

## "BARREL 2C Tri-axial Fluxgate Magnetometer (MAGN) Magnetic Field Data, no Gain Correction, not Despun, Level 2, 0.25 s Data" (pool position 68, id 73ffdeec-4229-4411-af13-3a47cf604575)

A held-out record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. 40 items, 18 that may matter.

- **Left out:** "2C" (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"
  - **May matter because:** my reading, not checked: the balloon payload's code (campaign 2, payload C), as "4G" in the record "BARREL 4G Rate Counter (RCNT) NaI Scintillator Diagnostics, Level 2, 4 s Data"; it tells this dataset from its siblings and gives its campaign.
  - **Question:** Q6 (b).
- **Left out:** "no Gain Correction, not Despun" (title) and "Data are neither gain corrected nor despun." (notes)
  - **Rule:** What counts as a fact, rule 6: "A ground truth triple can't say "not", and a negated fact is not rewritten into a fact the record doesn't state."
  - **May matter because:** it says that the field values are neither gain corrected nor despun, which a user of the data must know.
- **Left out:** "Three axis DC magnetometer" and "DC magnetometer" (notes, "Three axis DC magnetometer data" and "Each BARREL balloon carried … a DC magnetometer") as instruments of their own
  - **Rule:** Writing a classed triple, rule 23: "When a record names the same entity more than once, in different words, use the wording the first of the four tests below picks, in every ground truth triple"
  - The three wordings name the payload's one magnetometer ("Tri-axial" and "Three axis" say the same; "DC magnetometer" is in "Three axis DC magnetometer"). Test 1 picks "Three axis DC magnetometer" over "DC magnetometer", and does not decide between it and the title's wording, since each says something the other does not ("Fluxgate", "DC"); tests 2 and 3 do not decide either, and test 4 picks the title's "Tri-axial Fluxgate Magnetometer (MAGN)", given first. The record's dataset ACQUIRED_BY_INSTRUMENT, ABOARD "BARREL balloon" and HAS_PURPOSE "measure ULF-timescale variations of the magnetic field" all use it.
- **Left out:** the launch stations and their places (notes, "with launches from two stations located in Antarctica: the British base located at Halley Bay on the Brunt Ice Shelf and the South African SANAE IV base", and "Later campaigns were undertaken in 2015 and 2016 from the Esrange Space Center located in Kiruna, Sweden")
  - **Rule:** What counts as a fact, rule 2: "or it waits on an expert's answer" (Q8 (c): whether a station or a space center is an Organization or a place).
  - No clear would-be triple: whether a station is an Organization or a place decides its entity class and its predicates (LAUNCHED_FROM and LOCATED_IN for a place, none of them in the ground truth schema; BASED_IN "British", "South African" and "Sweden" for an Organization), so no row can be written in annotations/pending_triples.csv until Q8 (c) is answered. The record "BARREL 4G Rate Counter (RCNT) NaI Scintillator Diagnostics, Level 2, 4 s Data" leaves them out the same way.
  - **May matter because:** a search by launch site or region (Antarctica, Sweden) would need them.
  - **Question:** Q8 (c).
- **Left out:** "South African" (notes, inside the name "South African National Antarctic Expedition") as a Country of its own
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names" The record names no country. The ground truth schema's Country is "a nation", "South African" is an adjective, the record never writes "South Africa", and an instance is the record's own words (Writing a classed triple, rule 11: "Don't paraphrase them").
  - **May matter because:** it says where the expedition is based, which a search by country would need.
  - **Question:** Q8 (c), with the launch stations.
- **Left out:** what "CDF" stands for (notes, "all BARREL CDF data products")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what CDF is. Its entity class, FileFormat, is written (the record's dataset HAS_FILE_FORMAT "CDF", with the source text "all BARREL CDF data products"; the record's dataset is one of these products by rule 1's *Membership by name*, as for HAS_VERSION "Version 10", and "all" makes the format each member's), by rule 1's *A name the record does not explain*.
  - The reference: Wikidata, Common Data Format (Q1116060), also named "CDF", "file format family for multi-dimensional data", an instance of "file format family" (https://www.wikidata.org/wiki/Q1116060, checked on 2026-11-13). No official NASA list names it: the GCMD Instruments, Platforms and Providers keywords (version 25.2) have no entry for it.
- **Left out:** "was a multiple-balloon investigation" (notes)
  - **Rule:** What counts as a fact, rule 4: "A sentence that says what type of entity an instance refers to ("Kestrel is an imager") gives no ground truth triple: the instance's entity class says it"
  - **May matter because:** it says the mission used many balloons at once.
- **Left out:** "Mission of Opportunity" and "Selected" (notes)
  - **Rule:** What counts as a fact, rule 4: "the type is left out, and the belonging is a ground truth triple" ("BARREL" PART_OF "NASA Living with a Star"); "Selected" names no party (rule 1: "Never add what you know from elsewhere").
  - **May matter because:** it is NASA's funding category for the mission.
- **Left out:** "Each" (notes, "Each BARREL balloon")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance"
- **Left out:** "near latitudes close to either the antarctic and arctic circles" (notes)
  - **Rule:** What counts as a fact, rule 1, *Membership by name*: "A statement about the group as a whole is not written for it": "either … or". Which circle this payload flew near is not stated.
  - **May matter because:** a search by region (Antarctic, Arctic) would need it.
  - **Question:** Q24.
- **Left out:** "stratospheric altitudes" (notes)
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words." OBSERVED_AT_ALTITUDE "about 30 km" is the wording that says more (rule 23).
- **Left out:** "first balloon" (notes, "provided the first balloon measurements")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance"
  - **May matter because:** it says BARREL was the first to measure this from balloons.
- **Left out:** "while comprehensive in situ measurements of both plasma waves and energetic particles were available" (notes)
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names" Whose measurements is not said; "comprehensive" is a judgement (rule 5).
- **Left out:** "Also, the BARREL data has been used to characterize the spatial scale of precipitation at relativistic energies." (notes)
  - **Rule:** What counts as a fact, rule 9: "when the record doesn't name that work, the use gives no ground truth triple." No work that used the data is named; the statement is also about the BARREL data as a whole (rule 1, *Membership by name*).
  - **May matter because:** it says what the data are good for.
  - **Question:** Q24.
- **Left out:** "initially" and "Austral summer months of" (notes)
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance" ("initially"). "Austral summer months": rule 16 of *Writing a classed triple*, since the months, HAS_TIME_SPAN "January and February of 2013" and "of 2014", say when.
  - **May matter because:** "Austral summer" says why those months (the southern summer).
- **Left out:** "Thus, the BARREL balloon constellation constituted an evolving and slowly moving array able to study relativistic electron precipitation from the radiation belts." (notes)
  - **Rule:** What counts as a fact, rule 4: "A sentence that says what type of entity an instance refers to ("Kestrel is an imager") gives no ground truth triple: the instance's entity class says it" ("constituted an … array"); "able to study" is what it could do, not what it was meant for (HAS_PURPOSE "is meant to achieve").
  - **May matter because:** it says the balloons formed a moving array, which is how the mission measured spatial scales.
- **Left out:** "and other ground and space based instruments" (notes)
  - **Rule:** Writing a classed triple, rule 22: "An item that names no specific entity ("his team") gives no ground truth triple"
- **Left out:** "successively" (notes)
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance"
- **Left out:** "approximately 20 kg" as the mass of each balloon (notes, "over 50 small, approximately 20 kg, stratospheric balloons were successively launched")
  - **Rule:** What counts as a fact, rule 9: "An amount or a count per member gives no ground truth triple, unless the predicate itself says "each" (HAS_GRANULE_DURATION, HAS_SPATIAL_RESOLUTION)." The mass is each balloon's, and the sentence names the balloons only by a count ("over 50 … balloons"). The words stay in the count, which is written whole: "BARREL" HAS_NUMBER_OF "over 50 small, approximately 20 kg, stratospheric balloons" (rule 22 of *Writing a classed triple*, *Describing words joined by "and" or a comma*).
  - **May matter because:** it is the mass of each balloon the mission flew.
- **Left out:** "The website creeated and hosted by A.J. Halford (see Information URL below) reports that: "By the end of the campaigns, there were over 90 researchers coordinating on a daily basis with the BARREL team working on 7 different satellite missions, 1 other balloon mission, and way too many ground based instruments to count."" (notes)
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names" The researchers are named only by a count, and "way too many" is a judgement (rule 5). The website itself is a ground truth triple: the record's dataset DOCUMENTED_AT "website creeated and hosted by A.J. Halford" (Document), with DEVELOPED_BY_PARTY and PROVIDED_BY_PARTY "A.J. Halford" (Person).
  - **May matter because:** it gives the mission's reach.
- **Left out:** "only" (notes, "launched only balloons")
  - **Rule:** What counts as a fact, rule 6: "A ground truth triple can't say "not"." "only" says nothing else was launched.
- **Left out:** "research using data collected on these flights is ongoing, so stay tuned for updates!" (notes)
  - **Rule:** What counts as a fact, rule 10: "Take out "latest", "current", "now", "then available", and words like them." ("ongoing"); "stay tuned" names nothing (rule 9).
- **Left out:** "All data and analysis software are freely available to the scientific community." (notes)
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words." For the data: HAS_ACCESS_RIGHTS "freely available to the public" says more. "analysis software": rule 9, no particular software is named.
- **Left out:** "primarily" (notes)
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance"
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
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the entity," The policy is the instance, AVAILABLE_AT its address.
- **Left out:** what "NASA" is (notes, "a NASA Living with a Star Mission of Opportunity")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what NASA is. Its entity class, Organization, is written ("NASA Living with a Star" PART_OF "NASA"), by rule 1's *A name the record does not explain*.
  - The reference: GCMD Providers keywords (version 25.2), the level "NASA" under "GOVERNMENT AGENCIES-U.S. FEDERAL AGENCIES", which holds NASA's centers and offices (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/providers?format=csv, checked on 2026-11-13).
- **Left out:** what "Earth" is (notes)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what Earth is. Its entity class, CelestialBody, is written (HAS_TARGET "Earth"), by rule 1's *A name the record does not explain*.
  - The reference: PDS4 context product urn:nasa:pds:context:target:planet.earth, "Earth", of type Planet (https://pds.nasa.gov/data/pds4/context-pds4/target/planet.earth_1.1.xml, checked on 2026-11-13).
- **Left out:** what "NASA Living with a Star" is (notes, "Selected as a NASA Living with a Star Mission of Opportunity")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what NASA Living with a Star is. Its entity class, Organization, is written (PART_OF "NASA"), by rule 1's *A name the record does not explain*. A program that an organization runs is an Organization, one of that organization's named parts, which the ground truth schema's Organization includes ("a named institution or one of its named parts, not a Mission"). Living with a Star is a program of NASA, and the program itself collects no data, so it is not a Mission.
  - The reference: Wikidata Q1705257, "Living With a Star", "scientific program of NASA to study the Sun-Earth system", an instance of "NASA program" (https://www.wikidata.org/wiki/Q1705257, checked on 2026-11-13).
- **Left out:** "2016 campaign" HAS_NUMBER_OF "eight flights" (notes, "The 2015 and 2016 campaigns were undertaken in coordination with" … "A total of eight flights occurred during August 2016.")
  - **Rule:** What counts as a fact, rule 1: "A fact that the record does not state may be written only when it follows from what the record states by one of the three tests below (Replacement, Comparison, Membership by name); nothing else, and no outside knowledge, adds such a fact. The list of tests is closed". The sentence gives the eight flights a month, August 2016, and names no campaign. That they are the flights of the 2016 campaign follows from this sentence and the sentences that name the campaign, by none of the three tests (*Replacement*, *Comparison*, *Membership by name*), as in the record "BARREL 4G Rate Counter (RCNT) NaI Scintillator Diagnostics, Level 2, 4 s Data".
  - **May matter because:** it is the number of flights of the 2016 campaign, as "Seven balloon launches" is for the campaign of August 2015.
- **Left out:** the 2013, the 2014 and the 2016 campaign PART_OF "BARREL" (notes, "For the 2013 and 2014 the balloon campaigns", "The 2015 and 2016 campaigns" … "Summing over the four BARREL campaigns")
  - **Rule:** What counts as a fact, rule 1: "A fact that the record does not state may be written only when it follows from what the record states by one of the three tests below (Replacement, Comparison, Membership by name); nothing else, and no outside knowledge, adds such a fact. The list of tests is closed". The record names one campaign with the mission's name ("August 2015 BARREL campaign" PART_OF "BARREL", rule 2's *A fact inside a name*). No passage states that the 2013, the 2014 or the 2016 campaign is a campaign of BARREL: it follows from counting the campaigns the record describes up to "the four BARREL campaigns", by none of the three tests (*Replacement*, *Comparison*, *Membership by name*), as in the record "BARREL 4G Rate Counter (RCNT) NaI Scintillator Diagnostics, Level 2, 4 s Data".
  - **May matter because:** without them no ground truth triple connects the three campaigns to the mission.

## "BARREL 2D X-ray Spectrometer (SSPC) Bremsstrahlung X-ray Spectrum Slow Time Resolution, Level 2, 32 s Data" (pool position 71, id 4230ddcd-1523-4278-a7f2-7cb78262d2b7)

A held-out record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. 45 items, 18 that may matter.

- **Left out:** "2D" (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"
  - **May matter because:** my reading, not checked: the balloon payload's code (campaign 2, payload D), as "4G" in the record "BARREL 4G Rate Counter (RCNT) NaI Scintillator Diagnostics, Level 2, 4 s Data"; it tells this dataset from its siblings and gives its campaign.
  - **Question:** Q6 (b).
- **Left out:** "(SSPC)" as part of the instrument's name (title, "X-ray Spectrometer (SSPC)")
  - **Rule:** Writing a classed triple, rule 20: "Parentheses that hold the code of another entity are taken out of the instance."
  - The notes say that SSPC is the name of the variable ("All channels are combined to a single variable named SSPC"), written as HAS_VARIABLE "SSPC". "SSPC" is not an abbreviation of "X-ray Spectrometer" by rule 20's test ("Spectrometer" holds one "s" and "X-ray" none, so its letters are not letters of those words in the same order), so the instrument is "X-ray Spectrometer", the wording of "Each BARREL balloon carried an X-ray spectrometer" (rule 23: they differ only in capitals).
- **Left out:** "Slow Time Resolution" (title) and "slow" (notes, "256 channels of slow time resolution, 32 s")
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words."
  - HAS_TEMPORAL_RESOLUTION "32 s" states the resolution, the wording that says more (rule 23).
- **Left out:** "Bremsstrahlung X-ray Spectrum" (title) as a wording of its own
  - **Rule:** Writing a classed triple, rule 23: "When a record names the same entity more than once, in different words, use the wording the first of the four tests below picks, in every ground truth triple"
  - The form is written in the notes' wording, HAS_SPATIAL_REPRESENTATION "Bremsstrahlung X-ray spectra" (rule 23, test 2: the notes' sentence states a fact about the spectra with words for it, "detected with a NaI Scintillator").
- **Left out:** "Bremsstrahlung X-ray" as a thing of its own (notes, inside "Bremsstrahlung X-ray spectra")
  - **Rule:** What counts as a fact, rule 2, *A fact inside a name*: "When the naming states more than one predicate, or none, the name's words give no ground truth triple, since choosing one would add what the record does not state."
  - No predicate of the ground truth schema says what radiation a form of data is of, and the X-rays are not a bare property (PhysicalQuantity), so the name states no predicate. The spectrometer's purpose names them: HAS_PURPOSE "measure the bremsstrahlung X-rays produced by precipitating relativistic electrons as they collide with neutrals in the atmosphere".
  - **May matter because:** a search by what the data measure would need the X-rays.
- **Left out:** "nominal" (notes, "The nominal energy range covered by the 256 channels ranges from 0 MeV to 10 MeV")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance"
  - HAS_ENERGY_RANGE "from 0 MeV to 10 MeV" is written; "nominal" says that the range is the one the channels were designed for, which is how the fact holds.
- **Left out:** "combined" (notes, "All channels are combined to a single variable named SSPC")
  - **Rule:** Writing a classed triple, rule 24: "A verb or participle that says only what was done to the data ("corrected", "calibrated", "detrended", "binned", "mapped", "edited", "convert", "weighted") names no method"
  - The variable is written: HAS_VARIABLE "SSPC".
- **Left out:** what "NaI" stands for (notes, "detected with a NaI Scintillator")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"
  - The name stays whole, and its entity class, Instrument, is given by the record's own kind word "Scintillator" (rule 1: "A name whose own words say what kind of thing it is … is explained by the record's own words"): the record's dataset ACQUIRED_BY_INSTRUMENT "NaI Scintillator", since the record says the spectra were "detected with" it. In the record "BARREL 4G Rate Counter (RCNT) NaI Scintillator Diagnostics, Level 2, 4 s Data" the same words stand only inside the Variable "NaI Scintillator Diagnostics", with no words that state a fact about the scintillator.
- **Left out:** the launch stations and their places (notes, "with launches from two stations located in Antarctica: the British base located at Halley Bay on the Brunt Ice Shelf and the South African SANAE IV base", and "Later campaigns were undertaken in 2015 and 2016 from the Esrange Space Center located in Kiruna, Sweden")
  - **Rule:** What counts as a fact, rule 2: "or it waits on an expert's answer" (Q8 (c): whether a station or a space center is an Organization or a place).
  - No clear would-be triple: whether a station is an Organization or a place decides its entity class and its predicates (LAUNCHED_FROM and LOCATED_IN for a place, none of them in the ground truth schema; BASED_IN "British", "South African" and "Sweden" for an Organization), so no row can be written in annotations/pending_triples.csv until Q8 (c) is answered. The record "BARREL 4G Rate Counter (RCNT) NaI Scintillator Diagnostics, Level 2, 4 s Data" leaves them out the same way.
  - **May matter because:** a search by launch site or region (Antarctica, Sweden) would need them.
  - **Question:** Q8 (c).
- **Left out:** "South African" (notes, inside the name "South African National Antarctic Expedition") as a Country of its own
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names" The record names no country. The ground truth schema's Country is "a nation", "South African" is an adjective, the record never writes "South Africa", and an instance is the record's own words (Writing a classed triple, rule 11: "Don't paraphrase them").
  - **May matter because:** it says where the expedition is based, which a search by country would need.
  - **Question:** Q8 (c), with the launch stations.
- **Left out:** what "CDF" stands for (notes, "all BARREL CDF data products")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what CDF is. Its entity class, FileFormat, is written (the record's dataset HAS_FILE_FORMAT "CDF", with the source text "all BARREL CDF data products"; the record's dataset is one of these products by rule 1's *Membership by name*, as for HAS_VERSION "Version 10", and "all" makes the format each member's), by rule 1's *A name the record does not explain*.
  - The reference: Wikidata, Common Data Format (Q1116060), also named "CDF", "file format family for multi-dimensional data", an instance of "file format family" (https://www.wikidata.org/wiki/Q1116060, checked on 2026-11-13). No official NASA list names it: the GCMD Instruments, Platforms and Providers keywords (version 25.2) have no entry for it.
- **Left out:** "was a multiple-balloon investigation" (notes)
  - **Rule:** What counts as a fact, rule 4: "A sentence that says what type of entity an instance refers to ("Kestrel is an imager") gives no ground truth triple: the instance's entity class says it"
  - **May matter because:** it says the mission used many balloons at once.
- **Left out:** "Mission of Opportunity" and "Selected" (notes)
  - **Rule:** What counts as a fact, rule 4: "the type is left out, and the belonging is a ground truth triple" ("BARREL" PART_OF "NASA Living with a Star"); "Selected" names no party (rule 1: "Never add what you know from elsewhere").
  - **May matter because:** it is NASA's funding category for the mission.
- **Left out:** "Each" (notes, "Each BARREL balloon")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance"
- **Left out:** "near latitudes close to either the antarctic and arctic circles" (notes)
  - **Rule:** What counts as a fact, rule 1, *Membership by name*: "A statement about the group as a whole is not written for it": "either … or". Which circle this payload flew near is not stated.
  - **May matter because:** a search by region (Antarctic, Arctic) would need it.
  - **Question:** Q24.
- **Left out:** "stratospheric altitudes" (notes)
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words." OBSERVED_AT_ALTITUDE "about 30 km" is the wording that says more (rule 23).
- **Left out:** "first balloon" (notes, "provided the first balloon measurements")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance"
  - **May matter because:** it says BARREL was the first to measure this from balloons.
- **Left out:** "while comprehensive in situ measurements of both plasma waves and energetic particles were available" (notes)
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names" Whose measurements is not said; "comprehensive" is a judgement (rule 5).
- **Left out:** "Also, the BARREL data has been used to characterize the spatial scale of precipitation at relativistic energies." (notes)
  - **Rule:** What counts as a fact, rule 9: "when the record doesn't name that work, the use gives no ground truth triple." No work that used the data is named; the statement is also about the BARREL data as a whole (rule 1, *Membership by name*).
  - **May matter because:** it says what the data are good for.
  - **Question:** Q24.
- **Left out:** "initially" and "Austral summer months of" (notes)
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance" ("initially"). "Austral summer months": rule 16 of *Writing a classed triple*, since the months, HAS_TIME_SPAN "January and February of 2013" and "of 2014", say when.
  - **May matter because:** "Austral summer" says why those months (the southern summer).
- **Left out:** "Thus, the BARREL balloon constellation constituted an evolving and slowly moving array able to study relativistic electron precipitation from the radiation belts." (notes)
  - **Rule:** What counts as a fact, rule 4: "A sentence that says what type of entity an instance refers to ("Kestrel is an imager") gives no ground truth triple: the instance's entity class says it" ("constituted an … array"); "able to study" is what it could do, not what it was meant for (HAS_PURPOSE "is meant to achieve").
  - **May matter because:** it says the balloons formed a moving array, which is how the mission measured spatial scales.
- **Left out:** "and other ground and space based instruments" (notes)
  - **Rule:** Writing a classed triple, rule 22: "An item that names no specific entity ("his team") gives no ground truth triple"
- **Left out:** "successively" (notes)
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance"
- **Left out:** "approximately 20 kg" as the mass of each balloon (notes, "over 50 small, approximately 20 kg, stratospheric balloons were successively launched")
  - **Rule:** What counts as a fact, rule 9: "An amount or a count per member gives no ground truth triple, unless the predicate itself says "each" (HAS_GRANULE_DURATION, HAS_SPATIAL_RESOLUTION)." The mass is each balloon's, and the sentence names the balloons only by a count ("over 50 … balloons"). The words stay in the count, which is written whole: "BARREL" HAS_NUMBER_OF "over 50 small, approximately 20 kg, stratospheric balloons" (rule 22 of *Writing a classed triple*, *Describing words joined by "and" or a comma*).
  - **May matter because:** it is the mass of each balloon the mission flew.
- **Left out:** "The website creeated and hosted by A.J. Halford (see Information URL below) reports that: "By the end of the campaigns, there were over 90 researchers coordinating on a daily basis with the BARREL team working on 7 different satellite missions, 1 other balloon mission, and way too many ground based instruments to count."" (notes)
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names" The researchers are named only by a count, and "way too many" is a judgement (rule 5). The website itself is a ground truth triple: the record's dataset DOCUMENTED_AT "website creeated and hosted by A.J. Halford" (Document), with DEVELOPED_BY_PARTY and PROVIDED_BY_PARTY "A.J. Halford" (Person).
  - **May matter because:** it gives the mission's reach.
- **Left out:** "only" (notes, "launched only balloons")
  - **Rule:** What counts as a fact, rule 6: "A ground truth triple can't say "not"." "only" says nothing else was launched.
- **Left out:** "research using data collected on these flights is ongoing, so stay tuned for updates!" (notes)
  - **Rule:** What counts as a fact, rule 10: "Take out "latest", "current", "now", "then available", and words like them." ("ongoing"); "stay tuned" names nothing (rule 9).
- **Left out:** "All data and analysis software are freely available to the scientific community." (notes)
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words." For the data: HAS_ACCESS_RIGHTS "freely available to the public" says more. "analysis software": rule 9, no particular software is named.
- **Left out:** "primarily" (notes)
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance"
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
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the entity," The policy is the instance, AVAILABLE_AT its address.
- **Left out:** what "NASA" is (notes, "a NASA Living with a Star Mission of Opportunity")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what NASA is. Its entity class, Organization, is written ("NASA Living with a Star" PART_OF "NASA"), by rule 1's *A name the record does not explain*.
  - The reference: GCMD Providers keywords (version 25.2), the level "NASA" under "GOVERNMENT AGENCIES-U.S. FEDERAL AGENCIES", which holds NASA's centers and offices (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/providers?format=csv, checked on 2026-11-13).
- **Left out:** what "Earth" is (notes)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what Earth is. Its entity class, CelestialBody, is written (HAS_TARGET "Earth"), by rule 1's *A name the record does not explain*.
  - The reference: PDS4 context product urn:nasa:pds:context:target:planet.earth, "Earth", of type Planet (https://pds.nasa.gov/data/pds4/context-pds4/target/planet.earth_1.1.xml, checked on 2026-11-13).
- **Left out:** what "NASA Living with a Star" is (notes, "Selected as a NASA Living with a Star Mission of Opportunity")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what NASA Living with a Star is. Its entity class, Organization, is written (PART_OF "NASA"), by rule 1's *A name the record does not explain*. A program that an organization runs is an Organization, one of that organization's named parts, which the ground truth schema's Organization includes ("a named institution or one of its named parts, not a Mission"). Living with a Star is a program of NASA, and the program itself collects no data, so it is not a Mission.
  - The reference: Wikidata Q1705257, "Living With a Star", "scientific program of NASA to study the Sun-Earth system", an instance of "NASA program" (https://www.wikidata.org/wiki/Q1705257, checked on 2026-11-13).
- **Left out:** "2016 campaign" HAS_NUMBER_OF "eight flights" (notes, "The 2015 and 2016 campaigns were undertaken in coordination with" … "A total of eight flights occurred during August 2016.")
  - **Rule:** What counts as a fact, rule 1: "A fact that the record does not state may be written only when it follows from what the record states by one of the three tests below (Replacement, Comparison, Membership by name); nothing else, and no outside knowledge, adds such a fact. The list of tests is closed". The sentence gives the eight flights a month, August 2016, and names no campaign. That they are the flights of the 2016 campaign follows from this sentence and the sentences that name the campaign, by none of the three tests (*Replacement*, *Comparison*, *Membership by name*), as in the record "BARREL 4G Rate Counter (RCNT) NaI Scintillator Diagnostics, Level 2, 4 s Data".
  - **May matter because:** it is the number of flights of the 2016 campaign, as "Seven balloon launches" is for the campaign of August 2015.
- **Left out:** the 2013, the 2014 and the 2016 campaign PART_OF "BARREL" (notes, "For the 2013 and 2014 the balloon campaigns", "The 2015 and 2016 campaigns" … "Summing over the four BARREL campaigns")
  - **Rule:** What counts as a fact, rule 1: "A fact that the record does not state may be written only when it follows from what the record states by one of the three tests below (Replacement, Comparison, Membership by name); nothing else, and no outside knowledge, adds such a fact. The list of tests is closed". The record names one campaign with the mission's name ("August 2015 BARREL campaign" PART_OF "BARREL", rule 2's *A fact inside a name*). No passage states that the 2013, the 2014 or the 2016 campaign is a campaign of BARREL: it follows from counting the campaigns the record describes up to "the four BARREL campaigns", by none of the three tests (*Replacement*, *Comparison*, *Membership by name*), as in the record "BARREL 4G Rate Counter (RCNT) NaI Scintillator Diagnostics, Level 2, 4 s Data".
  - **May matter because:** without them no ground truth triple connects the three campaigns to the mission.

## "MARS EXPRESS SUN MRS 1/2/3 EXTENDED MISSION 8 4360 V1.0" (pool position 74, id 6d3c471e-464c-46d6-926c-ea7c5ae577cd)

A held-out record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. 6 items, 2 that may matter.

- **Left out:** "1/2/3" (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"
  - **May matter because:** in the record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" the same place in the title was checked to hold the processing levels (its item); not checked for this record.
  - **Question:** Q6 (b).
- **Left out:** "4360" (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"
  - **May matter because:** it tells this dataset from its siblings, as "1149" does in the record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (its item); not checked for this record.
  - **Question:** Q6 (b).
- **Left out:** "phase" (notes, "the extended mission phase")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the entity,"
  - The phase is written in the title's wording, "EXTENDED MISSION 8", the wording that says more (rule 23).
- **Left out:** what "Mars Express" is (title, "MARS EXPRESS", and notes, "a Mars Express Radio Science data set")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what Mars Express is. The title's first word is the instrument host, a craft: FROM_PLATFORM "Mars Express" (Platform). The notes' "a Mars Express Radio Science data set" names the mission, as in the record "MARS EXPRESS SUN MRS 1/2/3 EXTENDED MISSION 5 3750 V1.0": FROM_MISSION "Mars Express" (Mission), and "Mars Express" HAS_TARGET "Mars". Both entity classes are by rule 1's *A name the record does not explain*.
  - The list: PDS4 context product urn:esa:psa:context:instrument_host:spacecraft.mex, "The Mars Express Orbiter", of type Spacecraft, also titled "MARS EXPRESS" (https://pds.nasa.gov/data/pds4/context-pds4/instrument_host/spacecraft.mex_1.1.xml, checked on 2026-11-13).
  - The list: PDS4 context product urn:esa:psa:context:investigation:mission.mars_express, "Mars Express", of type Mission, also titled "MARS EXPRESS" (https://pds.nasa.gov/data/pds4/context-pds4/investigation/mission.mars_express_2.1.xml, checked on 2026-11-13).
  - **Question:** Q2.
- **Left out:** what "MRS" stands for (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what MRS is. Its entity class, Instrument, is written (ACQUIRED_BY_INSTRUMENT "MRS"), by rule 1's *A name the record does not explain*.
  - The list: PDS4 context product urn:esa:psa:context:instrument:mex.mrs, "Mars Express Orbiter Radio Science", an instrument of the instrument host Mars Express, whose earlier identifier is urn:nasa:pds:context:instrument:mrs.mex: "MRS" is its instrument id (https://pds.nasa.gov/data/pds4/context-pds4/instrument/mex.mrs_1.2.xml, checked on 2026-11-13).
- **Left out:** what "SUN" and "Mars" are (title, "SUN", and notes, inside the name "Mars Express")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what the Sun or Mars is. Their entity class, CelestialBody, is written (the record's dataset HAS_TARGET "SUN", and "Mars Express" HAS_TARGET "Mars"), by rule 1's *A name the record does not explain*.
  - The reference: PDS4 context product urn:nasa:pds:context:target:star.sun, "Sun", of type Star (https://pds.nasa.gov/data/pds4/context-pds4/target/star.sun_1.1.xml, checked on 2026-11-13); and, for Mars, urn:nasa:pds:context:target:planet.mars, "Mars", of type Planet (https://pds.nasa.gov/data/pds4/context-pds4/target/planet.mars_1.3.xml, checked on 2026-11-13).

## "Hubble Source Catalog Detailed Search" (pool position 77, id 79f8f9dd-ff7f-40ee-bd2e-bfbee219ca18)

A held-out record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. Its describes class is WebTool, since the title names a search and the notes say that it "displays an entry for each separate detection". 9 items, 3 that may matter.

- **Left out:** "Hubble Source Catalog" and "Hubble" as facts of the search tool (title, "Hubble Source Catalog Detailed Search", and notes, "The Hubble Source Catalog (HSC) detailed search")
  - **Rule:** What counts as a fact, rule 2, *A fact inside a name*: "When the naming states more than one predicate, or none, the name's words give no ground truth triple, since choosing one would add what the record does not state."
  - Naming a search with a catalog's name says that the tool searches the catalog, and no predicate of the ground truth schema says that; FROM_PLATFORM ("was collected from this Platform") is false of a search tool. The facts of the catalog and of the observations are written with their own subjects, and no ground truth triple joins the catalog to the tool.
  - **May matter because:** it says which catalog the tool searches.
- **Left out:** "combining" (notes, "by combining the tens of thousands of visit-based source lists in the Hubble Legacy Archive (HLA) into a single master catalog")
  - **Rule:** Writing a classed triple, rule 24: "A verb or participle that says only what was done to the data ("corrected", "calibrated", "detrended", "binned", "mapped", "edited", "convert", "weighted") names no method"
  - The input is written: "Hubble Source Catalog (HSC)" COMPUTED_FROM "visit-based source lists".
- **Left out:** "in the Hubble Legacy Archive (HLA)" and "tens of thousands of" (notes, "the tens of thousands of visit-based source lists in the Hubble Legacy Archive (HLA)")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what the Hubble Legacy Archive is, and no public reference names it (Wikidata has no entry for it; the GCMD Providers keywords, version 25.2, and the PDS4 context products have none either; checked on 2026-11-13). Its kind word "Archive" fits more than one entity class: a collection of data (Dataset) or the institution that keeps it (Organization). So no ground truth triple has it as an instance: neither the place of the source lists (PART_OF) nor their count, which is the archive's (HAS_NUMBER_OF).
  - **May matter because:** it says where the input lists are kept and how many there are.
- **Left out:** "single master catalog" (notes, "into a single master catalog")
  - **Rule:** What counts as a fact, rule 4: "A sentence that says what type of entity an instance refers to ("Kestrel is an imager") gives no ground truth triple: the instance's entity class says it"
- **Left out:** "if nothing is found at that position" (notes, "(or nondetection if nothing is found at that position)")
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words."
  - It says what a nondetection is, which DISPLAYS "entry for each separate nondetection" already names.
- **Left out:** "all the relevant" and "for a given object" (notes, "using all the relevant Hubble observations for a given object")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance"
  - COMPUTED_FROM "Hubble observations" is written; the words say which of the observations each entry is made from.
- **Left out:** "(i.e., different filters, detectors, separate visits)" (notes)
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names"
  - The words name no particular filter, detector or visit.
  - **May matter because:** they say that the entries combine observations across filters, detectors and visits.
- **Left out:** "currently" (notes, "The catalog currently contains over 100 million entries.")
  - **Rule:** What counts as a fact, rule 10: "Take out "latest", "current", "now", "then available", and words like them."
- **Left out:** what "Hubble Space Telescope" is (notes; also inside "Hubble Source Catalog (HSC)" and "Hubble observations")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what the Hubble Space Telescope is. Its entity class, Platform, is written (FROM_PLATFORM "Hubble Space Telescope" of the catalog and of "Hubble observations", where "Hubble" is a shorter wording of the telescope, rule 23), by rule 1's *A name the record does not explain*.
  - The list: GCMD Platforms keywords (version 25.2), "Space-based Platforms" > "Solar/Space Observation Satellites", short name "HST", long name "Hubble Space Telescope" (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/platforms?format=csv, checked on 2026-11-13).

## "ROSETTA-ORBITER 67P OSINAC 4 ESC4-MTP024 RDR-STRLIGHT V1.0" (pool position 80, id 29206dfa-52e6-4dc4-b0c7-4922bc68c5f0)

A held-out record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. 8 items, 3 that may matter.

- **Left out:** "MTP024" (title, "ESC4-MTP024")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"
  - **May matter because:** it tells this dataset from its siblings, as "MTP020" does in the record "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0" (its item; not checked for this record).
  - **Question:** Q6 (b).
- **Left out:** "RDR" and "STRLIGHT" (title, "RDR-STRLIGHT")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"
  - **Question:** Q6 (b).
- **Left out:** "prime" (notes, "The prime target is comet 67P/Churyumov-Gerasimenko 1 (1969 R1)")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance"
  - HAS_TARGET says the dataset is about the comet; "prime" says only that it is the main target, how that fact holds, as in the record "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0".
  - **May matter because:** a search for other bodies in these images would need it.
- **Left out:** "comet" (notes, "comet 67P/Churyumov-Gerasimenko 1 (1969 R1)")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the entity,"
- **Left out:** "spacecraft" and "mission phase" (notes, "the Rosetta spacecraft" and "the COMET ESCORT 4 mission phase")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the entity,"; "the Rosetta spacecraft" is written as "ROSETTA-ORBITER", the wording that says more (rule 23).
- **Left out:** "Lien" (notes, "Lien corrected dataset after October 2018 PSA/PDS external peer review")
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words."
  - My ground truth triple REVISED_AFTER "October 2018 PSA/PDS external peer review" says the dataset was corrected after the review; "Lien" names what was corrected, the issues the review raised, as in the record "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0".
- **Left out:** PRODUCED_USING_ALGORITHM "solar stray light corrected", "radiometric calibrated" and "geometric distortion corrected (resampled)" (notes, "contains solar stray light corrected, radiometric calibrated and geometric distortion corrected (resampled) image data")
  - **Rule:** Writing a classed triple, rule 24: "A verb or participle that says only what was done to the data ("corrected", "calibrated", "detrended", "binned", "mapped", "edited", "convert", "weighted") names no method"
  - The words describe the data and name no method. What was corrected is written: CLEANED_OF "solar stray light" and CLEANED_OF "geometric distortion" (rule 24: "What a step removed from the data, or corrected in them, is neither the step's input nor its method"); "radiometric calibrated" names nothing removed.
  - **May matter because:** it says which corrections were applied to the images.
  - **Question:** Q7 (c).
- **Left out:** what "OSIRIS" stands for (notes, inside the name "OSIRIS Narrow Angle Camera")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record names "OSIRIS" only inside the camera's name and never says what it is. Its entity class, Instrument, is written ("OSIRIS Narrow Angle Camera" PART_OF "OSIRIS"), by rule 1's *A name the record does not explain*.
  - The reference: Wikidata, Optical, Spectroscopic, and Infrared Remote Imaging System (Q7098805), also named "OSIRIS", "scientific instrument on the Rosetta spacecraft", an instance of "space instrument" (https://www.wikidata.org/wiki/Q7098805, checked on 2026-11-13). No official NASA list names it: the PDS4 context products have entries for its two cameras (urn:esa:psa:context:instrument:ro.osinac and ro.osiwac) and none for OSIRIS itself.

## "ROSETTA-ORBITER 67P RSI 1/2/3 PRELANDING 0294 V1.0" (pool position 83, id 99c8679f-ad3a-41e6-b28b-d33f6b101250)

A held-out record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. 6 items, 2 that may matter.

- **Left out:** "1/2/3" (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"
  - **May matter because:** in the record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" the same place in the title was checked to hold the processing levels (its item); not checked for this record.
  - **Question:** Q6 (b).
- **Left out:** "0294" (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"
  - **May matter because:** it tells this dataset from its siblings, as "1149" does in the record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (its item); not checked for this record.
  - **Question:** Q6 (b).
- **Left out:** what "RSI" stands for (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what RSI is. Its entity class, Instrument, is written (ACQUIRED_BY_INSTRUMENT "RSI"), by rule 1's *A name the record does not explain*.
  - The list: PDS4 context product urn:esa:psa:context:instrument:ro.rsi, "The Radio Science Investigations (RSI) for the Rosetta Orbiter", an instrument of the instrument host Rosetta Orbiter (https://pds.nasa.gov/data/pds4/context-pds4/instrument/ro.rsi_1.1.xml, checked on 2026-11-13).
- **Left out:** "comet" (notes, "at the comet 67P")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the entity,"
  - My ground truth triple has the target "67P".
- **Left out:** what "ROSETTA-ORBITER" is (title; the notes name only "Rosetta", in "a Rosetta Radio Science data set")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what ROSETTA-ORBITER is. Its entity class, Platform, is written (FROM_PLATFORM "ROSETTA-ORBITER"), by rule 1's *A name the record does not explain*.
  - The list: PDS4 context product urn:esa:psa:context:instrument_host:spacecraft.ro, "The Rosetta Orbiter Spacecraft", of type Spacecraft, also titled "ROSETTA-ORBITER" (https://pds.nasa.gov/data/pds4/context-pds4/instrument_host/spacecraft.ro_1.1.xml, checked on 2026-11-13).
- **Left out:** what "Rosetta" is (notes, "a Rosetta Radio Science data set")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what Rosetta is. Its entity class, Mission, is written (FROM_MISSION "Rosetta"), by rule 1's *A name the record does not explain*.
  - The reference: PDS4 context product urn:esa:psa:context:investigation:mission.international_rosetta_mission, "The International Rosetta Mission", also titled "ROSETTA", of type Mission (https://pds.nasa.gov/data/pds4/context-pds4/investigation/mission.international_rosetta_mission_1.1.xml, checked on 2026-11-13).

## "ROSETTA-ORBITER 67P RSI 1/2/3 PRELANDING 0324 V1.0" (pool position 86, id b4c2a310-936f-44b9-b8b7-4d9a785d7163)

A held-out record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. 6 items, 2 that may matter.

- **Left out:** "1/2/3" (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"
  - **May matter because:** in the record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" the same place in the title was checked to hold the processing levels (its item); not checked for this record.
  - **Question:** Q6 (b).
- **Left out:** "0324" (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"
  - **May matter because:** it tells this dataset from its siblings, as "1149" does in the record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (its item); not checked for this record.
  - **Question:** Q6 (b).
- **Left out:** what "RSI" stands for (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what RSI is. Its entity class, Instrument, is written (ACQUIRED_BY_INSTRUMENT "RSI"), by rule 1's *A name the record does not explain*.
  - The list: PDS4 context product urn:esa:psa:context:instrument:ro.rsi, "The Radio Science Investigations (RSI) for the Rosetta Orbiter", an instrument of the instrument host Rosetta Orbiter (https://pds.nasa.gov/data/pds4/context-pds4/instrument/ro.rsi_1.1.xml, checked on 2026-11-13).
- **Left out:** "comet" (notes, "at the comet 67P")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the entity,"
  - My ground truth triple has the target "67P".
- **Left out:** what "ROSETTA-ORBITER" is (title; the notes name only "Rosetta", in "a Rosetta Radio Science data set")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what ROSETTA-ORBITER is. Its entity class, Platform, is written (FROM_PLATFORM "ROSETTA-ORBITER"), by rule 1's *A name the record does not explain*.
  - The list: PDS4 context product urn:esa:psa:context:instrument_host:spacecraft.ro, "The Rosetta Orbiter Spacecraft", of type Spacecraft, also titled "ROSETTA-ORBITER" (https://pds.nasa.gov/data/pds4/context-pds4/instrument_host/spacecraft.ro_1.1.xml, checked on 2026-11-13).
- **Left out:** what "Rosetta" is (notes, "a Rosetta Radio Science data set")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what Rosetta is. Its entity class, Mission, is written (FROM_MISSION "Rosetta"), by rule 1's *A name the record does not explain*.
  - The reference: PDS4 context product urn:esa:psa:context:investigation:mission.international_rosetta_mission, "The International Rosetta Mission", also titled "ROSETTA", of type Mission (https://pds.nasa.gov/data/pds4/context-pds4/investigation/mission.international_rosetta_mission_1.1.xml, checked on 2026-11-13).

## "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 3 0908 V1.0" (pool position 89, id 1c601946-f1b4-4479-8d66-2ffd38e5192a)

A held-out record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. 6 items, 2 that may matter.

- **Left out:** "1/2/3" (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"
  - **May matter because:** in the record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" the same place in the title was checked to hold the processing levels (its item); not checked for this record.
  - **Question:** Q6 (b).
- **Left out:** "0908" (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"
  - **May matter because:** it tells this dataset from its siblings, as "1149" does in the record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (its item); not checked for this record.
  - **Question:** Q6 (b).
- **Left out:** what "RSI" stands for (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what RSI is. Its entity class, Instrument, is written (ACQUIRED_BY_INSTRUMENT "RSI"), by rule 1's *A name the record does not explain*.
  - The list: PDS4 context product urn:esa:psa:context:instrument:ro.rsi, "The Radio Science Investigations (RSI) for the Rosetta Orbiter", an instrument of the instrument host Rosetta Orbiter (https://pds.nasa.gov/data/pds4/context-pds4/instrument/ro.rsi_1.1.xml, checked on 2026-11-13).
- **Left out:** "comet" (notes, "at the comet 67P")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the entity,"
  - My ground truth triple has the target "67P".
- **Left out:** what "ROSETTA-ORBITER" is (title; the notes name only "Rosetta", in "a Rosetta Radio Science data set")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what ROSETTA-ORBITER is. Its entity class, Platform, is written (FROM_PLATFORM "ROSETTA-ORBITER"), by rule 1's *A name the record does not explain*.
  - The list: PDS4 context product urn:esa:psa:context:instrument_host:spacecraft.ro, "The Rosetta Orbiter Spacecraft", of type Spacecraft, also titled "ROSETTA-ORBITER" (https://pds.nasa.gov/data/pds4/context-pds4/instrument_host/spacecraft.ro_1.1.xml, checked on 2026-11-13).
- **Left out:** what "Rosetta" is (notes, "a Rosetta Radio Science data set")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what Rosetta is. Its entity class, Mission, is written (FROM_MISSION "Rosetta"), by rule 1's *A name the record does not explain*.
  - The reference: PDS4 context product urn:esa:psa:context:investigation:mission.international_rosetta_mission, "The International Rosetta Mission", also titled "ROSETTA", of type Mission (https://pds.nasa.gov/data/pds4/context-pds4/investigation/mission.international_rosetta_mission_1.1.xml, checked on 2026-11-13).

## "VG2 JUP LECP CALIBRATED RESAMPLED SECTORED 15MIN V1.1" (pool position 92, id 7aeed9f7-aa69-44bf-8433-859c6c22e937)

A held-out record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. 11 items, 6 that may matter.

- **Left out:** "CALIBRATED" and "RESAMPLED" (title), and "resampled" and "globally calibrated" (notes, "This data set consists of resampled data" and "The LECP data are globally calibrated")
  - **Rule:** Writing a classed triple, rule 24: "A verb or participle that says only what was done to the data ("corrected", "calibrated", "detrended", "binned", "mapped", "edited", "convert", "weighted") names no method"
  - The words describe the record's dataset itself, which is written as its title (rule 23, *The title's instance*), so the instance they would stay in is never written.
  - **May matter because:** they say that the data are resampled and calibrated.
- **Left out:** "to the extent possible (see below)" (notes)
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance"
  - "to the extent possible" says how the calibration holds; the record's text has nothing below this sentence about the calibration (rule 9: "A ground truth triple needs a subject and an object the record names.").
- **Left out:** "with various levels of discrimination based on energy, mass species, and angular arrival direction" (notes)
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names"
  - "various levels" names no level.
  - **May matter because:** it says that the instrument tells particles apart by energy, mass and direction.
- **Left out:** "A subset of" (notes, "A subset of almost 100 LECP channels are included with this data set")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance"
  - HAS_NUMBER_OF "almost 100 LECP channels" is written.
  - **May matter because:** it says that the instrument has more channels than the dataset holds.
- **Left out:** "with the exact beginning and ending times for those intervals matching the LECP instrumental cycle periods (the angular scanning periods)" (notes)
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance: its subject would be that fact, not an entity the record names."
  - The subject would be the averaging intervals of HAS_COMPOSITING_PERIOD "about 15 minute", a fact, not a thing the record names.
  - **May matter because:** it says how the averaging intervals are placed in time.
- **Left out:** "which has not been converted to the usual physical units" (notes)
  - **Rule:** What counts as a fact, rule 6: "A ground truth triple can't say "not", and a negated fact is not rewritten into a fact the record doesn't state."
  - **May matter because:** it says that the values are count rates, not intensities in physical units.
- **Left out:** "(8 sectors" and "all data for a given channel and time period … in a single record" (notes, "Data records for the version 1.1 data set provide all data for a given channel and time period (8 sectors, plus the average for all sectors) in a single record")
  - **Rule:** What counts as a fact, rule 9: "An amount or a count per member gives no ground truth triple, unless the predicate itself says "each" (HAS_GRANULE_DURATION, HAS_SPATIAL_RESOLUTION)."
  - Both say what each data record holds; the variable every record holds is written, HAS_VARIABLE "average for all sectors" (rule 9: "what it holds"), and the title's "SECTORED" gives HAS_SPATIAL_REPRESENTATION. "a given channel" names no channel.
  - **May matter because:** it says how the files are laid out, one record per channel and time period.
- **Left out:** "LECP", "15MIN" and "V1.1" (title) as wordings of their own
  - **Rule:** Writing a classed triple, rule 23: "When a record names the same entity more than once, in different words, use the wording the first of the four tests below picks, in every ground truth triple"
  - The notes spell them out: "Low Energy Charged Particle (LECP)", "about 15 minute" and "version 1.1" (test 1, the wording that says more).
- **Left out:** "experiment" (notes, "the Low Energy Charged Particle (LECP) experiment")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the entity,"
  - The record calls it "This instrument" in the next sentence, so its entity class, Instrument, is the record's own.
- **Left out:** what "Voyager 2" is (title, "VG2", and notes, "on Voyager 2")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what Voyager 2 is. Its entity class, Platform, is written (FROM_PLATFORM "Voyager 2", and "Low Energy Charged Particle (LECP)" ABOARD "Voyager 2"), by rule 1's *A name the record does not explain*. "VG2" is the craft's host id, as "VG1" is in the record "VG1 SAT PWS EDITED SPECTRUM ANALYZER 4.0SEC V1.0".
  - The reference: PDS4 context product urn:nasa:pds:context:instrument_host:spacecraft.vg2, "VOYAGER 2", of type Spacecraft, with the host id "VG2" (https://pds.nasa.gov/data/pds4/context-pds4/instrument_host/spacecraft.vg2_1.5.xml, checked on 2026-11-13).
- **Left out:** what "Jupiter" is, and "JUP" (title, "JUP", and notes, "in the vicinity of Jupiter")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what Jupiter is. Its entity class, CelestialBody, is written (HAS_TARGET "Jupiter"), by rule 1's *A name the record does not explain*. The title's "JUP" is written as "Jupiter": its letters begin the name the notes give (rule 23), unlike "SAT" in the record "VG1 SAT PWS EDITED SPECTRUM ANALYZER 4.0SEC V1.0", whose notes name no such body.
  - The reference: PDS4 context product urn:nasa:pds:context:target:planet.jupiter, "Jupiter", of type Planet (https://pds.nasa.gov/data/pds4/context-pds4/target/planet.jupiter_1.3.xml, checked on 2026-11-13).

## "Plasticity of the human IgM repertoire in response to a long-term spaceflight" (pool position 95, id 73521c6f-1378-4a8c-a47c-7626ee4f0de4)

A held-out record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. 6 items, 2 that may matter.

- **Left out:** "Immune dysregulation is among the main adverse outcomes of spaceflight. Despite its crucial role in host protection effects on the human antibody repertoire are unknown." (notes)
  - **Rule:** What counts as a fact, rule 8: "Nothing else in the study is a fact of the record's dataset: its background, its findings, what it says about methods it did not use, and the details of its method beyond what rule 24 writes (how the method was applied, its parameters, what it allows)."
  - It is the study's background.
- **Left out:** "Plasticity" and "in response to a long-term spaceflight" (title)
  - **Rule:** What counts as a fact, rule 8: "Nothing else in the study is a fact of the record's dataset: its background, its findings, what it says about methods it did not use, and the details of its method beyond what rule 24 writes (how the method was applied, its parameters, what it allows)."
  - The title states the study's finding, that the repertoire changes in response to spaceflight; what the data hold is written, HAS_MEASUREMENTS_OF "human IgM repertoire". "a long-term spaceflight" names no particular flight (rule 9).
  - **May matter because:** a search for data on spaceflight would need it.
- **Left out:** "25 days before launch after 64 and 129 days spent on the International Space Station (ISS) and after 1 7 and 30 days of Earth reambulation" (notes)
  - **Rule:** What counts as a fact, rule 8: "Nothing else in the study is a fact of the record's dataset: its background, its findings, what it says about methods it did not use, and the details of its method beyond what rule 24 writes (how the method was applied, its parameters, what it allows)."
  - The times say when the samples were taken, how the study's method was applied.
  - **May matter because:** they tie the data to the International Space Station and to the times of the flight.
- **Left out:** "This is the first study of this kind." (notes)
  - **Rule:** What counts as a fact, rule 8: "Nothing else in the study is a fact of the record's dataset: its background, its findings, what it says about methods it did not use, and the details of its method beyond what rule 24 writes (how the method was applied, its parameters, what it allows)."
- **Left out:** "Our data revealed that the IgM repertoire of cosmonauts was different from the one of control subjects already prior to launch" to "coincided with a higher stress response." (notes)
  - **Rule:** What counts as a fact, rule 8: "Nothing else in the study is a fact of the record's dataset: its background, its findings, what it says about methods it did not use, and the details of its method beyond what rule 24 writes (how the method was applied, its parameters, what it allows)."
  - They are the study's findings.
- **Left out:** "These data confirm that about half of the astronauts who spent six months on the ISS are subjected to immunological changes" to "an unprecedented amount of time." (notes)
  - **Rule:** What counts as a fact, rule 8: "Nothing else in the study is a fact of the record's dataset: its background, its findings, what it says about methods it did not use, and the details of its method beyond what rule 24 writes (how the method was applied, its parameters, what it allows)."
  - They are findings, and "personalized approaches should be implemented" is a recommendation (rule 7).

## "Dynamics and Chemistry of the Summer Stratosphere Radar and Satellite (Remote Sensing) Data Products" (pool position 98, id 972e69c6-676d-4b25-aaf8-e180a4745617)

A held-out record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. The data set holds radar and satellite products made for a field campaign; the last paragraph of the notes tells the campaign, whose facts are general facts about something the record's dataset relates to (rule 21 of *Writing a classed triple*). 16 items, 8 that may matter.

- **Left out:** "sub-orbital campaign", "field campaign" and "research project" (notes, "the Dynamics and Chemistry of the Summer Stratosphere sub-orbital campaign" and "The Dynamics and Chemistry of the Summer Stratosphere (DCOTSS) field campaign is a NASA Earth Venture Suborbital research project")
  - **Rule:** What counts as a fact, rule 4: "A sentence that says what type of entity an instance refers to ("Kestrel is an imager") gives no ground truth triple: the instance's entity class says it"
  - They say what kind of thing DCOTSS is. Its entity class is Mission ("a named effort to collect data, from space, from the air, on water or on the ground"), as for ARCTAS in the record "ARCTAS Model Data": the ground truth schema's Campaign is "carried out as part of a Mission", and the record names no Mission that DCOTSS is part of, and its Project is "other than a Mission (a named effort to collect data)". "campaign" is also a type word (rule 23 of *Writing a classed triple*).
- **Left out:** "NASA Earth Venture Suborbital" (notes, "is a NASA Earth Venture Suborbital research project")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what kind of thing NASA Earth Venture Suborbital is, and its words hold no kind word. No reference of rule 1's *A name the record does not explain* names it: the GCMD Instruments, Platforms and Providers keywords (version 25.2) have no entry for it, and Wikidata's nearest entry, "Earth Venture program" (Q125747756), a "series of low-cost NASA space missions and hosted instruments", is named neither "Earth Venture Suborbital" nor by another name of it (https://www.wikidata.org/wiki/Q125747756, checked on 2026-11-13). So DCOTSS gives no PART_OF of it, and the names inside it, "NASA" and "Earth", give no PART_OF and no HAS_TARGET (rule 2, *A fact inside a name*).
  - **May matter because:** a search for the datasets of NASA's Earth Venture Suborbital investigations would need it.
  - The GCMD Projects keywords have "EARTH VENTURE", "Earth Venture Sub-Orbital Investigations" (checked on 2026-11-13), but rule 1 names only the Instruments, Platforms and Providers keywords among the GCMD lists.
- **Left out:** "Satellite" (title) and "satellite" (notes, "the radar and satellite data products") as facts of their own
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names"
  - The words name no particular satellite. The two satellites that the record names are written with their products: "GOES-16 products" FROM_PLATFORM "GOES-16", and the same for GOES-17. The title's "Radar" and "(Remote Sensing)" are written as USES_TECHNIQUE "radar" and "Remote Sensing", as "radar" is in the record "OPERA Dynamic Surface Water Extent from Sentinel-1 (Version 1)".
- **Left out:** "NEXRAD WSR-88D radar products" and "the GridRad products" (notes) as wordings of their own
  - **Rule:** Writing a classed triple, rule 23: "When a record names the same entity more than once, in different words, use the wording the first of the four tests below picks, in every ground truth triple"
  - They name the radar part of the record's dataset, which the notes also call "NEXRAD GridRad data" and "GridRad data". Test 1 ties (the first wording names the radar, the second the product), test 2 finds words for predicates in both sentences, and test 3 picks "NEXRAD GridRad data", the wording the record uses most often. The radar that the first wording names is written: "NEXRAD GridRad data" ACQUIRED_BY_INSTRUMENT "NEXRAD WSR-88D", with "radar" taken out as a type word, which also gives the entity class, Instrument (rule 23).
- **Left out:** "GridRad" (notes, inside "NEXRAD GridRad data", "Identified GridRad overshoots" and "the GridRad products") as a thing of its own
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what GridRad is: it names data, overshoots and products with the word. The GCMD Instruments keywords (version 25.2) have "GridRad", "Gridded NEXRAD WSR-88D Radar", under Imaging Radars (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/instruments?format=csv, checked on 2026-11-13). The entry is an instrument, while the record uses the word for gridded data products, so the entry is not clearly the thing the record names, and the word stays in the instances that hold it.
  - **May matter because:** it names the gridded radar product that the data are.
- **Left out:** "derived products" (notes, "GOES-16 and GOES-17 geostationary satellite imagery and derived products")
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words."
  - The derived products are named later, "These products include derived cloud top altitude, convective overshoot probability, and visible texture rating product", and written for "GOES-16 products" and "GOES-17 products". "Featured in this product are … GOES-16 and GOES-17 geostationary satellite imagery and derived products" and "Also included are GOES-16 and GOES-17 satellite products" state one fact, the products' PART_OF, written from the second; the first gives the products' form, HAS_SPATIAL_REPRESENTATION "imagery".
- **Left out:** "geostationary satellite" and "satellite" (notes, "GOES-16 and GOES-17 geostationary satellite imagery", "GOES-16 and GOES-17 satellite products" and "GOES visible and infrared geostationary satellite imagery"), and "aircraft" (notes, "NASA’s ER-2 aircraft")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the entity,"
  - The words describe GOES-16, GOES-17 and the ER-2, and give their entity class, Platform. They are taken out of "GOES-16 products", "GOES-17 products", "GOES visible imagery" and "GOES infrared imagery" too, where they describe the craft.
- **Left out:** "primarily" (notes, "which were primarily used to identify tropopause-overshooting convection") and "separate" (notes, "are included in separate daily files")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance"
  - The use names what was made from the two volumes, so it gives that product's input (rule 9: "A use that names what was made from the data gives that product's input"): "Identified GridRad overshoots" COMPUTED_FROM each of the two volumes.
- **Left out:** "tropopause-overshooting convection" (notes, "used to identify tropopause-overshooting convection" and "Tropopause-overshooting convection is also identified using GOES visible and infrared geostationary satellite imagery") as a thing of its own
  - **Rule:** Writing a classed triple, rule 24: "For each processing step the record describes, find what it made (the output), what it was made from (the input), and how (the method)."
  - The convection is what the two steps look for. What they made is named: "Identified GridRad overshoots", from the radar volumes, and "The satellite overshoot products", from the GOES imagery, which the record says complement the GridRad products. Both are written with COMPUTED_FROM.
  - **May matter because:** it names what the overshoot products show.
- **Left out:** "ERA5" (notes, inside "ERA5 tropopause heights") as a fact of its own
  - **Rule:** What counts as a fact, rule 2: "When the naming states more than one predicate, or none, the name's words give no ground truth triple, since choosing one would add what the record does not state." (*A fact inside a name*)
  - A data set's name before "tropopause heights" could mean that the heights are part of it or that they were computed from it, and naming does not settle which. For the record: the GCMD Platforms keywords (version 25.2) have "ECMWF ERA5", "ECMWF ERA5 Atmospheric Reanalysis", under Models, and Wikidata's ERA5 (Q115748247) is an instance of "meteorological reanalysis" (https://www.wikidata.org/wiki/Q115748247, checked on 2026-11-13).
  - **May matter because:** a search for the products made with ERA5 would need it.
- **Left out:** "ongoing" and "currently" (notes, "Data collection for this product is ongoing and currently only features the first deployment")
  - **Rule:** What counts as a fact, rule 10: "Take out "latest", "current", "now", "then available", and words like them."
  - "only" is taken out too, by rule 9 ("A word that only says how another fact holds"): it stops being true once data of a later deployment are added. The rest of the fact is written: the record's dataset FROM_CAMPAIGN "first deployment". The deployments are Campaigns, as the deployments are in the record "ARCTAS Model Data", and no predicate of the ground truth schema links a data set to a Campaign (the record "First ISCCP Regional Experiment (FIRE) Cirrus Phase II Raman Lidar Data" notes the same gap), so FROM_CAMPAIGN is coined, marked held-out only.
  - **May matter because:** it says that the data collection is not finished.
- **Left out:** "Each summer the North American Monsoon Anticyclone (NAMA) dominates the circulation of the North-Western Hemisphere and acts to partially confine and isolate air from the surrounding atmosphere." and "Strong convective storms in the NAMA regularly reach altitudes deep into the lower stratosphere, with some ascending above 20 km." (notes)
  - **Rule:** Writing a classed triple, rule 21: "A statement that only explains a concept (what a term means, how a quantity behaves in general, which methods are in common use) and is about nothing so connected gives no ground truth triple"
  - They explain how the anticyclone and its storms behave in general, and are about nothing connected to the record's id. The purpose of DCOTSS keeps the storms in its words, "investigating these thunderstorms" (rule 11 of *Writing a classed triple*: the record's own words, as written).
  - **May matter because:** they say which storms the campaign studied, and where.
- **Left out:** "These storms carry water and pollutants from the troposphere into the otherwise very dry stratosphere, where they can have a significant impact on radiative and chemical processes, potentially including destruction of stratospheric ozone." (notes)
  - **Rule:** Writing a classed triple, rule 21: "A statement that only explains a concept (what a term means, how a quantity behaves in general, which methods are in common use) and is about nothing so connected gives no ground truth triple"
  - It explains what the storms do in general. "can have" and "potentially" are uncertain too (rule 7 of *What counts as a fact*), and "significant" is a judgement (rule 5).
- **Left out:** "NASA’s" (notes, "NASA’s ER-2 aircraft") as a fact of its own
  - **Rule:** What counts as a fact, rule 2: "A relationship that naming does not state (that one entity funded, developed, provided or sponsored the other) is never read from a name"
  - The possessive says that the aircraft is NASA's, and not whether NASA owns, operates or provides it, so no predicate is read from it. The word stays in the aircraft's instance, "NASA’s ER-2", as "German Aerospace Center’s (DLR)" stays in "German Aerospace Center’s (DLR) FALCON" in the record "SOLVE I Ground Site Data".
- **Left out:** "~8-week" as the duration of each deployment (notes, "conducted two ~8-week science deployments")
  - **Rule:** What counts as a fact, rule 9: "An amount or a count per member gives no ground truth triple, unless the predicate itself says "each" (HAS_GRANULE_DURATION, HAS_SPATIAL_RESOLUTION)."
  - **May matter because:** it is how long each deployment lasted.
  - The words stay in the count, which is written whole: HAS_NUMBER_OF "two ~8-week science deployments", as "two, three-week aircraft deployments" is in the record "ARCTAS Model Data".
- **Left out:** "based out of Salina, KS" and "spanning early to late summer" (notes, "conducted two ~8-week science deployments based out of Salina, KS spanning early to late summer")
  - **Rule:** What counts as a fact, rule 9: "A fact the record states for each member of a group it names only by a count or a common noun ("186 parameters each with …", "Each product is …") is written for the thing the group belongs to only when it stays true of that thing: what it holds, what it measures, what it comes from, or what format its files are in."
  - The deployments are named only by a count, and where they were based and when they took place are not among the facts the rule writes for the whole, as for "Each mission combined …" in the record "First ISCCP Regional Experiment (FIRE) Cirrus Phase II Raman Lidar Data". "early to late summer" also names no particular summer (rule 9: "A ground truth triple needs a subject and an object the record names."), as "during the winter" does not in the record "SOLVE I Ground Site Data". For the record: Wikidata's Salina (Q1650620), also named "Salina, KS", is an instance of "city in the United States" (https://www.wikidata.org/wiki/Q1650620, checked on 2026-11-13).
  - **May matter because:** it says where the aircraft flew from, and in which season.

## "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1202 V1.0" (pool position 101, id 0e0d4132-ea7e-4608-a588-5ec41fc18711)

A held-out record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. The record repeats the text of the tuning record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1228 V1.0" (pool position 39), with another measurement number and another period covered, and its decisions are copied from that record. 6 items, 2 that may matter.

- **Left out:** "1/2/3" (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"
  - **May matter because:** in the record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" the same place in the title was checked to hold the processing levels (its item); not checked for this record.
  - **Question:** Q6 (b).
- **Left out:** "1202" (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"
  - **May matter because:** it tells this dataset from its siblings, as "1149" does in the record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (its item); not checked for this record.
  - **Question:** Q6 (b).
- **Left out:** what "RSI" stands for (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what RSI is. Its entity class, Instrument, is written (ACQUIRED_BY_INSTRUMENT "RSI"), by rule 1's *A name the record does not explain*.
  - The list: PDS4 context product urn:esa:psa:context:instrument:ro.rsi, "The Radio Science Investigations (RSI) for the Rosetta Orbiter", an instrument of the instrument host Rosetta Orbiter (https://pds.nasa.gov/data/pds4/context-pds4/instrument/ro.rsi_1.1.xml, checked on 2026-11-13).
- **Left out:** "comet" (notes, "at the comet 67P")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the entity,"
  - My ground truth triple has the target "67P".
- **Left out:** what "ROSETTA-ORBITER" is (title; the notes name only "Rosetta", in "a Rosetta Radio Science data set")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what ROSETTA-ORBITER is. Its entity class, Platform, is written (FROM_PLATFORM "ROSETTA-ORBITER"), by rule 1's *A name the record does not explain*.
  - The list: PDS4 context product urn:esa:psa:context:instrument_host:spacecraft.ro, "The Rosetta Orbiter Spacecraft", of type Spacecraft, also titled "ROSETTA-ORBITER" (https://pds.nasa.gov/data/pds4/context-pds4/instrument_host/spacecraft.ro_1.1.xml, checked on 2026-11-13).
- **Left out:** what "Rosetta" is (notes, "a Rosetta Radio Science data set")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what Rosetta is. Its entity class, Mission, is written (FROM_MISSION "Rosetta"), by rule 1's *A name the record does not explain*.
  - The reference: PDS4 context product urn:esa:psa:context:investigation:mission.international_rosetta_mission, "The International Rosetta Mission", also titled "ROSETTA", of type Mission (https://pds.nasa.gov/data/pds4/context-pds4/investigation/mission.international_rosetta_mission_1.1.xml, checked on 2026-11-13).

## "Lower eukaryotic isolates belonging to class Tremellomycetes isolated from International Space Station Genome sequencing and assembly" (pool position 104, id fe89cd38-cd50-4960-90bc-209a23854037)

A held-out record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. The notes repeat the title's words in another order, so each fact is stated twice and written once (rule 16 of *Writing a classed triple*). The isolates are samples, a Dataset ("a set of observations, measurements, or samples"), and the record's dataset is made from them: the record's dataset COMPUTED_FROM "Lower eukaryotic isolates", with "Genome sequencing" as the way of measuring (USES_TECHNIQUE, as "high-throughput sequencing" is in the record "Plasticity of the human IgM repertoire in response to a long-term spaceflight") and "Genome assembly" as the method (PRODUCED_USING_ALGORITHM; rule 22 copies "Genome" onto both items). The isolates are written in the title's wording, the first of two that differ only in capitals (rule 23, *Capitals and punctuation*). 3 items, none that may matter.

- **Left out:** "class" (title and notes, the word before "Tremellomycetes")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the entity,"
  - The word says what kind of group Tremellomycetes is, a rank of the biological classification, which its entity class says. No entity class of the ground truth schema fits a group of organisms, so Taxon is coined, marked held-out only. "belonging to" names what the isolates belong to, written "Lower eukaryotic isolates" PART_OF "Tremellomycetes" (rule 4 of *What counts as a fact*: "the kind is left out, and the belonging is a ground truth triple").
- **Left out:** what "Tremellomycetes" is (title and notes)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what Tremellomycetes is, beyond the type word before it. Its entity class, Taxon, is written ("Lower eukaryotic isolates" PART_OF "Tremellomycetes"), by rule 1's *A name the record does not explain*.
  - The reference: Wikidata, Tremellomycetes (Q133144), a group of fungi, an instance of "taxon", which fits Taxon and no other entity class (https://www.wikidata.org/wiki/Q133144, checked on 2026-11-13).
- **Left out:** what "International Space Station" is (title and notes)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what the International Space Station is. Its entity class, Platform, is written ("Lower eukaryotic isolates" OBTAINED_FROM "International Space Station"), by rule 1's *A name the record does not explain*.
  - The list: GCMD Platforms keywords (version 25.2), "Space-based Platforms" > "Space Stations/Crewed Spacecraft" > "Space Station", short name "ISS", long name "International Space Station" (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/platforms?format=csv, checked on 2026-11-13).

## "CPEX-CV Dropsonde Data" (pool position 107, id 22291a4f-d7fd-49ae-ae8c-2e18a38ed388)

A held-out record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. The data set holds dropsonde data of a field campaign; most of the notes tell the campaign, whose facts are general facts about something the record's dataset relates to (rule 21 of *Writing a classed triple*). The notes tell the campaign in the future tense, as a plan, and also say that the data collection is complete. I read the statements in the future tense as asserted, since rule 7 of *What counts as a fact* leaves out only what the record does not assert as true, as "BARREL will make all its scientific data products quickly and publicly available" is written in the record "BARREL 4G Rate Counter (RCNT) NaI Scintillator Diagnostics, Level 2, 4 s Data". 10 items, 3 that may matter.

- **Left out:** "campaign" (notes, "Convective Processes Experiment – Cabo Verde (CPEX-CV) campaign" and "the CPEX – Aerosols & Winds (CPEX-AW) campaign") and "missions" (notes, "previous CPEX and CPEX-AW missions")
  - **Rule:** What counts as a fact, rule 4: "A sentence that says what type of entity an instance refers to ("Kestrel is an imager") gives no ground truth triple: the instance's entity class says it"
  - They say what kind of thing CPEX-CV and CPEX-AW are. Their entity class is Mission ("a named effort to collect data, from space, from the air, on water or on the ground"), as for SOLVE and ARCTAS in the records "SOLVE I Ground Site Data" and "ARCTAS Model Data": the ground truth schema's Campaign is "carried out as part of a Mission", and the record names no Mission that either is part of. The kind word "Experiment" inside the names fits more than one entity class, as in the record "First ISCCP Regional Experiment (FIRE) Cirrus Phase II Raman Lidar Data". "campaign" is also a type word (rule 23 of *Writing a classed triple*).
- **Left out:** "primary" (notes, "with the primary goal of")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance"
- **Left out:** "Measurements taken by CPEX-CV will assist in moving science forward from previous CPEX and CPEX-AW missions, the calibration and validation of satellite measurements, and the development of airborne sensors, especially those with potential for satellite deployment." (notes)
  - **Rule:** What counts as a fact, rule 9: "What data have been used for, or can be used for, is a fact of the work that used them, not of the data: when the record doesn't name that work, the use gives no ground truth triple."
  - **May matter because:** it names the earlier CPEX missions and the satellite work the measurements serve.
- **Left out:** "remote sensing instruments" and "that will allow for the measurement of tropospheric aerosols, winds, temperature, water vapor, and precipitation" (notes, "the NASA DC-8 aircraft will be deployed with remote sensing instruments and dropsondes that will allow for the measurement of …")
  - **Rule:** Writing a classed triple, rule 22: "An item that names no specific entity ("his team") gives no ground truth triple"
  - "remote sensing instruments" names no instrument. The measurement is said of the instruments and the dropsondes together, and the record does not say which of them measures which quantity, so no MEASURES triple is written for "dropsonde" alone (rule 1 of *What counts as a fact*: "Only what the record states"). The dropsondes are written ABOARD "NASA DC-8".
  - **May matter because:** it says what the aircraft's instruments measure.
- **Left out:** "lidars such as" (notes, "lidars such as the Doppler Aerosol WiNd Lidar (DAWN), High Altitude Lidar Observatory (HALO)")
  - **Rule:** What counts as a fact, rule 4: "A sentence that says what type of entity an instance refers to ("Kestrel is an imager") gives no ground truth triple: the instance's entity class says it"
  - The words say what kind of instruments DAWN and HALO are, which their entity class, Instrument, says; every item of the sentence is one of the "Instruments onboard the aircraft", which gives the entity class of each.
- **Left out:** "dropsonde system" and "instrument" (notes, "Advanced Vertical Atmospheric Profiling System (AVAPS) dropsonde system" and "the Airborne In-situ and Radio Occultation (AIRO) instrument")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the entity,"
  - "Advanced Vertical Atmospheric Profiling System (AVAPS)" and "Airborne In-situ and Radio Occultation (AIRO)" are names without them. The dropsondes of the record's dataset are written "dropsonde", the record's own word, and not as the AVAPS dropsonde system, since the record does not say that they are its dropsondes.
- **Left out:** "NASA" in "NASA DC-8" as a fact of its own (notes)
  - **Rule:** What counts as a fact, rule 2: "When the naming states more than one predicate, or none, the name's words give no ground truth triple" (*A fact inside a name*)
  - The name is the aircraft's own (the GCMD Platforms keywords, version 25.2, have "NASA DC-8", checked on 2026-11-13), and it stays whole, as in the record "SOLVE I Ground Site Data". The record says only that the aircraft "will be deployed", with no word for who deploys it, so no DEPLOYED_BY_PARTY is written.
- **Left out:** "Cabo Verde" (notes, "Sal Island, Cabo Verde") as a Country of its own
  - **Rule:** Writing a classed triple, rule 19: "Any other qualifier stays in the instance"
  - The country qualifies a place, neither a Person or Organization (BASED_IN) nor what is measured (HAS_SPATIAL_COVERAGE), so it stays in the instance: CPEX-CV LOCATED_AT "Sal Island, Cabo Verde".
  - **May matter because:** a search by country would need it.
- **Left out:** what "NASA" is (notes, "campaign conducted by NASA" and "NASA DC-8")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what NASA is. Its entity class, Organization, is written ("Convective Processes Experiment - Cabo Verde (CPEX-CV)" LED_BY_PARTY "NASA"), by rule 1's *A name the record does not explain*.
  - The reference: GCMD Providers keywords (version 25.2), the level "NASA" under "GOVERNMENT AGENCIES-U.S. FEDERAL AGENCIES", which holds NASA's centers and offices (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/providers?format=csv, checked on 2026-11-13).
- **Left out:** what "Sal Island" is (notes, "will operate out of Sal Island, Cabo Verde")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what Sal Island is. Its entity class, SpatialExtent, is written (CPEX-CV LOCATED_AT "Sal Island, Cabo Verde"), by rule 1's *A name the record does not explain*.
  - The reference: Wikidata, Sal (Q111989), also named "Sal Island", "island of Cape Verde", an instance of "island", a place, which fits SpatialExtent and no other entity class (https://www.wikidata.org/wiki/Q111989, checked on 2026-11-13).

## "UARS Cryogenic Limb Array Etalon Spectrometer (CLAES) Level 3AT V009 (UARCL3AT) at GES DISC" (pool position 110, id e7793e25-9923-44e2-8388-8f3fa0123f31)

A held-out record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. The title's "(UARCL3AT)" is written as the record's dataset's HAS_IDENTIFIER: it stands after "V009", not right after the words it would abbreviate, so it is a code (rule 20 of *Writing a classed triple*), as "(H3ZFCGPH)" is in the record "HIRDLS/Aura Level 3 Geopotential Height 1deg Lat Zonal Fourier Coefficients V007 (H3ZFCGPH)". 6 items, 2 that may matter.

- **Left out:** "alternating each satellite yaw cycle of about 36 days" (notes, "Data were collected between latitude 34S and 80N and 80S and 34N, alternating each satellite yaw cycle of about 36 days")
  - **Rule:** What counts as a fact, rule 9: "An amount or a count per member gives no ground truth triple, unless the predicate itself says "each" (HAS_GRANULE_DURATION, HAS_SPATIAL_RESOLUTION)."
  - "about 36 days" is the length of each yaw cycle of the satellite. "alternating" says how the two latitude ranges hold, which are written (HAS_SPATIAL_COVERAGE), and is taken out by rule 9 ("A word that only says how another fact holds gives no ground truth triple").
  - **May matter because:** it says which latitudes the data cover at which time.
- **Left out:** "The CLAES level 3AL product consists of 20 granules per day. A data granule is one CLAES species or subtype per day." (notes)
  - **Rule:** Writing a classed triple, rule 21: "Leave out facts about other datasets, such as a variant of the record's dataset (the same data at another temporal resolution, spatial resolution, or version), or a product made from it."
  - The record's dataset is the Level 3AT product. The level 3AL product is another dataset, which the record links to it by neither "part of" nor "made from", and the second sentence tells that product's granules.
  - **May matter because:** my reading, not checked: "3AL" may be a typing error for "3AT", and the record's maintainer should be told; if it is, the sentences give the record's dataset its granules.
- **Left out:** "NASA's" (notes, "NASA's Upper Atmosphere Research Satellite (UARS)") as a fact of its own
  - **Rule:** What counts as a fact, rule 2: "A relationship that naming does not state (that one entity funded, developed, provided or sponsored the other) is never read from a name"
  - The possessive says that the satellite is NASA's, and not whether NASA owns, operates or launched it, so no predicate is read from it. The word stays in the satellite's instance, as "German Aerospace Center’s (DLR)" stays in "German Aerospace Center’s (DLR) FALCON" in the record "SOLVE I Ground Site Data". The title's "UARS" is written in that wording too (rule 23, test 1: it spells out the abbreviation), and its kind word "Satellite" gives the entity class, Platform.
- **Left out:** "UARS" (notes, inside "the UARS standard pressure levels") as a fact of its own
  - **Rule:** What counts as a fact, rule 2: "When the naming states more than one predicate, or none, the name's words give no ground truth triple, since choosing one would add what the record does not state." (*A fact inside a name*)
  - Naming a set of pressure levels with a satellite's name states no predicate of the ground truth schema: FROM_PLATFORM ("was collected from this Platform") is false of a grid, as it is of an ephemeris in the record "Solar Orbiter Ephemeris, Heliocentric Trajectories, Heliographic, Heliographic Inertial, and Solar Ecliptic Coordinates, HelioWeb, Daily Data". The name stays whole (rule 11 of *Writing a classed triple*).
- **Left out:** "data product" and "data files" (notes, "Level 3AT data product" and "The data files are available"), and "The instrument" (notes, "The instrument measured infrared thermal emissions")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the entity,"
  - The record's dataset is written as its title (rule 23, *The title's instance*). "The instrument" is another wording of the spectrometer, written "Cryogenic Limb Array Etalon Spectrometer (CLAES)" (rule 23, test 1).
- **Left out:** what "GES DISC" is (title, "at GES DISC")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what GES DISC is. Its entity class, Organization, is written (the record's dataset PROVIDED_BY_PARTY "GES DISC", as "ARCTAS aircraft data" PROVIDED_BY_PARTY "ASDC" would be in the record "ARCTAS Model Data"), by rule 1's *A name the record does not explain*.
  - The list: GCMD Providers keywords (version 25.2), "NASA/GSFC/SED/ESD/TISL/GESDISC", "Goddard Earth Sciences Data and Information Services Center (formerly Goddard DAAC), Terrestrial Information Systems Laboratory, Earth Sciences Division, Science and Exploration Directorate, Goddard Space Flight Center, NASA" (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/providers?format=csv, checked on 2026-11-13). "GESDISC" and the record's "GES DISC" differ only in a space, the same wording (rule 23, *Capitals and punctuation*).

## "ROSETTA-ORBITER EARTH OSIWAC 3 EAR2 RDR V2.0" (pool position 113, id bda58c07-f36f-459f-b1c8-40d4ac3c15a5)

A held-out record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. Its text follows the held-out records "ROSETTA-ORBITER 67P OSIWAC 4 EXT3-MTP033 RDR-STR-REFL V1.0" (pool position 17) and "ROSETTA-ORBITER PRELANDING OSINAC 2 EDR MTP003 V2.0" (pool position 8), with another level, phase, period and target, and its decisions are copied from them where the words are the same. The phase's name holds the body the record names as its target, and gives "EARTH SWING-BY 2" HAS_TARGET "Earth", as a phase named with its comet gives "COMET ESCORT 4" HAS_TARGET "67P" in the record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0". 9 items, 3 that may matter.

- **Left out:** "RDR" (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"
  - **Question:** Q6 (b).
- **Left out:** "prime" (notes, "The prime target is planet Earth")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance"
  - HAS_TARGET says the dataset is about Earth; "prime" says only that it is the main target, how that fact holds, as in the record "ROSETTA-ORBITER 67P OSIWAC 4 EXT3-MTP033 RDR-STR-REFL V1.0".
  - **May matter because:** a search for other bodies in these images would need it.
- **Left out:** "planet" (notes, "planet Earth")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the entity,"
  - My ground truth triples have the target "Earth".
- **Left out:** "spacecraft" and "mission phase" (notes, "the Rosetta spacecraft" and "the EARTH SWING-BY 2 mission phase")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the entity,"; "the Rosetta spacecraft" is written as "ROSETTA-ORBITER", the wording that says more (rule 23).
- **Left out:** "supersedes previous deliveries of the same dataset" (notes, "This version V2.0 supersedes previous deliveries of the same dataset")
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names"
  - "previous deliveries of the same dataset" names no particular delivery or version, so a SUPERSEDES triple would have no object the record names, as in the record "ROSETTA-ORBITER PRELANDING OSINAC 2 EDR MTP003 V2.0".
  - **May matter because:** it says that earlier deliveries of this dataset exist and are replaced.
- **Left out:** "with the following changes since the last version" and "Reprocessed" (notes, "with the following changes since the last version: Reprocessed dataset after October 2018 PSA/PDS external peer review")
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words."
  - My ground truth triple REVISED_AFTER "October 2018 PSA/PDS external peer review" says that the dataset was revised after the review, as "Lien corrected dataset after October 2018 PSA/PDS external peer review" is written in the record "ROSETTA-ORBITER 67P OSIWAC 4 EXT3-MTP033 RDR-STR-REFL V1.0". "the last version" names no particular version (rule 9).
- **Left out:** PRODUCED_USING_ALGORITHM "radiometric calibrated" (notes, "contains radiometric calibrated image data")
  - **Rule:** Writing a classed triple, rule 24: "A verb or participle that says only what was done to the data ("corrected", "calibrated", "detrended", "binned", "mapped", "edited", "convert", "weighted") names no method"
  - The words describe the data and name no method, and name nothing removed; they stay in the instance, HAS_SPATIAL_REPRESENTATION "radiometric calibrated image data".
  - **May matter because:** it says that the images are radiometrically calibrated.
  - **Question:** Q7 (c).
- **Left out:** what "OSIRIS" stands for (notes, inside the name "OSIRIS Wide Angle Camera")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record names "OSIRIS" only inside the camera's name and never says what it is. Its entity class, Instrument, is written ("OSIRIS Wide Angle Camera" PART_OF "OSIRIS"), by rule 1's *A name the record does not explain*.
  - The reference: Wikidata, Optical, Spectroscopic, and Infrared Remote Imaging System (Q7098805), also named "OSIRIS", "scientific instrument on the Rosetta spacecraft", an instance of "space instrument" (https://www.wikidata.org/wiki/Q7098805, checked on 2026-11-13). No official NASA list names it: the PDS4 context products have entries for its two cameras (urn:esa:psa:context:instrument:ro.osinac and ro.osiwac) and none for OSIRIS itself.
- **Left out:** what "Earth" is (title, "EARTH", and notes, "the EARTH SWING-BY 2 mission phase" and "planet Earth")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what Earth is, beyond the type word "planet". Its entity class, CelestialBody, is written (HAS_TARGET "Earth", of the record's dataset and of "EARTH SWING-BY 2"), by rule 1's *A name the record does not explain*. The wording that is not typed all in capitals is written (rule 23, *Capitals and punctuation*).
  - The reference: PDS4 context product urn:nasa:pds:context:target:planet.earth, "Earth", of type Planet (https://pds.nasa.gov/data/pds4/context-pds4/target/planet.earth_1.4.xml, checked on 2026-11-13).

## "MMS 3 Magnetic Ephemeris and Coordinates (MEC) and Support (Tsyganenko 2004 model, Dynamic conditions), Level 2 (L2), Survey Mode, 30 s Data" (pool position 116, id d5d2e3f1-ff5b-49e4-b9f9-79f7705bd79f)

A held-out record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. The data set holds the position and the magnetic surroundings of one spacecraft, most of them computed with field models; each variable the notes name is written as HAS_VARIABLE or, for the "ancillary variables", HAS_ANCILLARY_DATA. The title's "Survey Mode" is written as USES_TECHNIQUE, the way the data were taken, since no other predicate of the ground truth schema fits a mode of operation. 11 items, 4 that may matter.

- **Left out:** "MMS 3" (title) as FROM_PLATFORM of the record's dataset
  - **Rule:** Writing a classed triple, rule 17: "A title's words give a fact only where a predicate fits what they state"
  - The title names the craft's magnetic ephemeris and coordinates, and FROM_PLATFORM ("was collected from this Platform") is false of an ephemeris of the craft, as it is of "Solar Orbiter" in the record "Solar Orbiter Ephemeris, Heliocentric Trajectories, Heliographic, Heliographic Inertial, and Solar Ecliptic Coordinates, HelioWeb, Daily Data". The one variable that the record says was measured at the craft is written: "magnetic field measured at the spacecraft" FROM_PLATFORM "Magnetospheric Multiscale 3 (MMS 3)", the wording that spells out the abbreviation (rule 23, test 1).
  - **May matter because:** a search for the data of MMS 3 would need it.
- **Left out:** "spacecraft" (notes, "Magnetospheric Multiscale 3 (MMS 3) spacecraft position, velocity, attitude, angular momentum vector, and magnetic ephemeris and coordinates (MEC)")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the entity,"
  - The word describes MMS 3 and gives its entity class, Platform. It is taken out of the six variables too, which rule 22 writes with the words the items share, "Magnetospheric Multiscale 3 (MMS 3)". Where "the spacecraft" stands alone inside a variable's words ("footpoints of the spacecraft"), it stays, as written (rule 11).
- **Left out:** "(MEC)" (title, "Magnetic Ephemeris and Coordinates (MEC)", and notes, "magnetic ephemeris and coordinates (MEC)")
  - **Rule:** Writing a classed triple, rule 22: "when it stands for several entities, it is a list, and the abbreviation belongs to no item."
  - "MEC" stands for two things, the ephemeris and the coordinates, so the list splits into "Magnetospheric Multiscale 3 (MMS 3) magnetic ephemeris" and "Magnetospheric Multiscale 3 (MMS 3) magnetic coordinates". The notes' "The Magnetic ephemeris data" names the first (rule 23, test 1: the wording that says whose ephemeris it is).
- **Left out:** "Support" (title, "and Support")
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names"
  - The word names no particular variable; the ancillary variables the notes name are written (HAS_ANCILLARY_DATA).
- **Left out:** "(Tsyganenko 2004 model, Dynamic conditions)" (title)
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words."
  - The notes state the same method in more words, written "Tsyganenko 2004 magnetic field model for disturbed magnetospheric conditions" (rule 23, test 1); "Dynamic conditions" and "disturbed magnetospheric conditions" name the same setting of the model, which stays in the method's words, as "using both forward and backward passes in time" does in "Kalman filter using both forward and backward passes in time" (rule 22).
- **Left out:** "Many variables are included in this data product" and "Other variables" (notes)
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names"
  - "Many variables" names none; the variables the record names are written (HAS_VARIABLE).
- **Left out:** "If possible" (notes, "If possible, the northern and southern hemisphere footpoints of the spacecraft are found")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance"
  - **May matter because:** it says that the footpoints are missing where they could not be found.
- **Left out:** "6 other coordinate systems" and the second "GSE" (notes, "from GEI into 6 other coordinate systems including BSC, GEO, GSE, GSE2000, GSE, and SM")
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words."
  - The list names six systems with "GSE" twice, five different ones, while "6 other" counts six. The purposes of the quaternions are written one per system named (rule 22), "GSE" once. The count gives no ground truth triple of its own, since its subject would be the transformation, not a thing the record names (rule 9).
  - **May matter because:** my reading, not checked: the second "GSE" may be a typing error for another system, and the record's maintainer should be told.
- **Left out:** "GEI", "BSC", "GEO", "GSE", "GSE2000" and "SM" as coordinate systems of the record's dataset (notes)
  - **Rule:** What counts as a fact, rule 1: "Never add what you know from elsewhere"
  - The record calls them coordinate systems, and says that the quaternions transform coordinates from GEI into the others; it does not say that the data give their positions in any of them, so no HAS_COORDINATE_SYSTEM triple is written. The names stay in the purposes of the quaternions.
  - **May matter because:** a search by coordinate system would need them.
- **Left out:** "separate" (notes, "separate flags that denote satellite eclipse by the Earth and Moon")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance"
  - It says that there is one flag for each body, which the two ground truth triples HAS_ANCILLARY_DATA already say.
- **Left out:** "the Earth" and "Moon" (notes, "flags that denote satellite eclipse by the Earth and Moon") as targets of the flags
  - **Rule:** What counts as a fact, rule 2: "When the naming states more than one predicate, or none, the name's words give no ground truth triple, since choosing one would add what the record does not state." (*A fact inside a name*)
  - The bodies qualify the eclipse, not the flags, so the flags' words state no HAS_TARGET, as "Earth" inside "Earth Observing System" gives none in the record "HIRDLS/Aura Level 3 Geopotential Height 1deg Lat Zonal Fourier Coefficients V007 (H3ZFCGPH)". The flags are written whole.

## "MARS EXPRESS SUN MRS 1/2/3 EXTENDED MISSION 5 3767 V1.0" (pool position 119, id ffa68737-ddfb-4545-b84f-26acfb4a36b6)

A held-out record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. The record repeats the text of the held-out record "MARS EXPRESS SUN MRS 1/2/3 EXTENDED MISSION 5 3750 V1.0" (pool position 35), with another measurement number and another period covered, and its decisions are copied from that record. 6 items, 2 that may matter.

- **Left out:** "1/2/3" (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"
  - **May matter because:** in the record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" the same place in the title was checked to hold the processing levels (its item); not checked for this record.
  - **Question:** Q6 (b).
- **Left out:** "3767" (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"
  - **May matter because:** it tells this dataset from its siblings, as "1149" does in the record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (its item); not checked for this record.
  - **Question:** Q6 (b).
- **Left out:** "phase" (notes, "the extended mission phase")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the entity,"
  - The phase is written in the title's wording, "EXTENDED MISSION 5", the wording that says more (rule 23).
- **Left out:** what "Mars Express" is (title, "MARS EXPRESS", and notes, "a Mars Express Radio Science data set")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what Mars Express is. The title's first word is the instrument host, a craft: FROM_PLATFORM "Mars Express" (Platform). The notes' "a Mars Express Radio Science data set" names the mission, as in the record "MARS EXPRESS SUN MRS 1/2/3 EXTENDED MISSION 5 3750 V1.0": FROM_MISSION "Mars Express" (Mission), and "Mars Express" HAS_TARGET "Mars". Both entity classes are by rule 1's *A name the record does not explain*.
  - The list: PDS4 context product urn:esa:psa:context:instrument_host:spacecraft.mex, "The Mars Express Orbiter", of type Spacecraft, also titled "MARS EXPRESS" (https://pds.nasa.gov/data/pds4/context-pds4/instrument_host/spacecraft.mex_1.1.xml, checked on 2026-11-13).
  - The list: PDS4 context product urn:esa:psa:context:investigation:mission.mars_express, "Mars Express", of type Mission, also titled "MARS EXPRESS" (https://pds.nasa.gov/data/pds4/context-pds4/investigation/mission.mars_express_2.1.xml, checked on 2026-11-13).
  - **Question:** Q2.
- **Left out:** what "MRS" stands for (title)
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what MRS is. Its entity class, Instrument, is written (ACQUIRED_BY_INSTRUMENT "MRS"), by rule 1's *A name the record does not explain*.
  - The list: PDS4 context product urn:esa:psa:context:instrument:mex.mrs, "Mars Express Orbiter Radio Science", an instrument of the instrument host Mars Express, whose earlier identifier is urn:nasa:pds:context:instrument:mrs.mex: "MRS" is its instrument id (https://pds.nasa.gov/data/pds4/context-pds4/instrument/mex.mrs_1.2.xml, checked on 2026-11-13).
- **Left out:** what "SUN" and "Mars" are (title, "SUN", and notes, inside the name "Mars Express")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what the Sun or Mars is. Their entity class, CelestialBody, is written (the record's dataset HAS_TARGET "SUN", and "Mars Express" HAS_TARGET "Mars"), by rule 1's *A name the record does not explain*.
  - The reference: PDS4 context product urn:nasa:pds:context:target:star.sun, "Sun", of type Star (https://pds.nasa.gov/data/pds4/context-pds4/target/star.sun_1.1.xml, checked on 2026-11-13); and, for Mars, urn:nasa:pds:context:target:planet.mars, "Mars", of type Planet (https://pds.nasa.gov/data/pds4/context-pds4/target/planet.mars_1.3.xml, checked on 2026-11-13).

## "MODIS_CR_Equal_Angle_Daily" (pool position 122, id 4ea399fb-dcc6-41df-945a-b829da60c586)

A held-out record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. The title's words, joined by underscores, are a list of facts of the record's dataset (rule 17 of *Writing a classed triple*, *A title's facts*). The cloud regimes are the dataset's own values, so the record's dataset is the output of the step the last sentence tells (rule 24, *The record's dataset's own values*). 6 items, 3 that may matter.

- **Left out:** the title's "Daily" against the notes' "Three-Hourly" (title and notes, "The MODIS Collection 6.1 Equal-Angle Three-Hourly Cloud Regime product"), as a conflict to correct
  - **Rule:** Finishing a record, *A record that contradicts itself*: "write what each passage states (rule 1 of What counts as a fact), and correct neither from outside knowledge." Both are written: HAS_TEMPORAL_RESOLUTION "Daily" and HAS_TEMPORAL_RESOLUTION "Three-Hourly".
  - **May matter because:** my reading, not checked: the title may name daily files of three-hourly values, or the record may have been copied from that of a daily product; the record's maintainer should be told.
- **Left out:** "Collection 6.1" (notes, "The MODIS Collection 6.1 Equal-Angle Three-Hourly Cloud Regime product")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". "Collection" followed by a number is not one of the catalog conventions ("V" or "Version" followed by a number), and the record never says what Collection 6.1 is. Its kind word, "Collection", fits more than one entity class (a set of data, Dataset, or a label of a release, Version), and no reference of rule 1's *A name the record does not explain* names it. So it gives no HAS_VERSION triple, unlike in the record "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061", whose text says that "Version 61" and "Collection 6.1" are used interchangeably.
  - **May matter because:** it is the release of the MODIS data that the product belongs to.
- **Left out:** "CR" (title) as a wording of its own
  - **Rule:** Writing a classed triple, rule 23: "When a record names the same entity more than once, in different words, use the wording the first of the four tests below picks, in every ground truth triple"
  - The notes spell it out, "Cloud Regime" (test 1), written HAS_VARIABLE "Cloud Regime": a cloud regime is a property narrowed by a method, the k-means clustering the record names.
- **Left out:** "discrete classification" (notes, "This product is a discrete classification of cloud fields at the mesoscale")
  - **Rule:** What counts as a fact, rule 4: "A sentence that says what type of entity an instance refers to ("Kestrel is an imager") gives no ground truth triple: the instance's entity class says it"
  - The words say what kind of product the record's dataset is. What it classifies is written: HAS_MEASUREMENTS_OF "cloud fields at the mesoscale", with "at the mesoscale" in the instance, since a scale of the clouds is not an amount of ground each value covers (rule 19 of *Writing a classed triple*: "A qualifier stays in the instance, as written, if it is any other kind").
- **Left out:** "the cloud regimes represent different atmospheric systems based on their cloud signatures" (notes)
  - **Rule:** What counts as a fact, rule 9: "A ground truth triple needs a subject and an object the record names"
  - "different atmospheric systems" names no particular system.
  - **May matter because:** it says what the cloud regimes stand for.
- **Left out:** "sensors", "satellites", "algorithm" and "product" (notes, "the MODIS sensors aboard the Terra and Aqua satellites", "the k-means clustering algorithm" and "Cloud Regime product")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the entity,"
  - "sensors" and "satellites" give MODIS and the two craft their entity classes, Instrument and Platform, and "k-means clustering" is a name without "algorithm". The record's dataset gets no FROM_PLATFORM: "observed by the MODIS sensors aboard the Terra and Aqua satellites" gives ACQUIRED_BY_INSTRUMENT "MODIS" and "MODIS" ABOARD each craft, as rule 15's example "The data were collected by MODIS aboard Terra" does.

## "ROSETTA-ORBITER 67P OSIWAC 4 EXT2-MTP028 RDR-INF-REFL V1.0" (pool position 125, id bbb8f62a-84d4-47cb-8ce6-5fd5820ee54d)

A held-out record, annotated on 2026-11-13 by a model (Claude Opus 5.5) with the rules frozen; preliminary, still to be reviewed by a person. Its text is that of the held-out record "ROSETTA-ORBITER 67P OSIWAC 4 EXT3-MTP033 RDR-STR-REFL V1.0" (pool position 17), with another planning period, phase and period covered, and with the in-field stray-light correction and the review of the tuning record "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP019 RDR-INFLDSTR V1.0" (pool position 37); its decisions are copied from those two records. 9 items, 3 that may matter.

- **Left out:** "MTP028" (title, "EXT2-MTP028")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"
  - **May matter because:** it tells this dataset from its siblings, as "MTP020" does in the record "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0" (its item; not checked for this record).
  - **Question:** Q6 (b).
- **Left out:** "RDR", "INF" and "REFL" (title, "RDR-INF-REFL")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for"
  - **Question:** Q6 (b).
- **Left out:** "prime" (notes, "The prime target is comet 67P/Churyumov-Gerasimenko 1 (1969 R1)")
  - **Rule:** What counts as a fact, rule 9: "A word that only says how another fact holds. Such a word gives no ground truth triple, and is taken out of the instance"
  - HAS_TARGET says the dataset is about the comet; "prime" says only that it is the main target, how that fact holds, as in the record "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0".
  - **May matter because:** a search for other bodies in these images would need it.
- **Left out:** "comet" (notes, "comet 67P/Churyumov-Gerasimenko 1 (1969 R1)")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the entity,"
- **Left out:** "spacecraft" and "mission phase" (notes, "the Rosetta spacecraft" and "the ROSETTA EXTENSION 2 mission phase")
  - **Rule:** Writing a classed triple, rule 23: "Take out a type word that only describes the entity,"; "the Rosetta spacecraft" is written as "ROSETTA-ORBITER", the wording that says more (rule 23).
- **Left out:** "Lien" (notes, "Lien corrected dataset after September 2019 PSA/PDS external peer review")
  - **Rule:** Writing a classed triple, rule 16: "Each fact once, even if the record states it twice or in other words."
  - My ground truth triple REVISED_AFTER "September 2019 PSA/PDS external peer review" says the dataset was corrected after the review; "Lien" names what was corrected, the issues the review raised, as in the record "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0".
- **Left out:** PRODUCED_USING_ALGORITHM "solar stray-light corrected", "in-field stray-light corrected", "radiometric calibrated" and "geometric distortion corrected (resampled)" (notes, "contains solar stray-light corrected, in-field stray-light corrected, radiometric calibrated and geometric distortion corrected (resampled) image data")
  - **Rule:** Writing a classed triple, rule 24: "A verb or participle that says only what was done to the data ("corrected", "calibrated", "detrended", "binned", "mapped", "edited", "convert", "weighted") names no method"
  - The words describe the data and name no method. What was corrected is written: CLEANED_OF "solar stray-light", CLEANED_OF "in-field stray-light" and CLEANED_OF "geometric distortion" (rule 24: "What a step removed from the data, or corrected in them, is neither the step's input nor its method"); "radiometric calibrated" names nothing removed.
  - **May matter because:** it says which corrections were applied to the images.
  - **Question:** Q7 (c).
- **Left out:** what "OSIRIS" stands for (notes, inside the name "OSIRIS Wide Angle Camera")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record names "OSIRIS" only inside the camera's name and never says what it is. Its entity class, Instrument, is written ("OSIRIS Wide Angle Camera" PART_OF "OSIRIS"), by rule 1's *A name the record does not explain*.
  - The reference: Wikidata, Optical, Spectroscopic, and Infrared Remote Imaging System (Q7098805), also named "OSIRIS", "scientific instrument on the Rosetta spacecraft", an instance of "space instrument" (https://www.wikidata.org/wiki/Q7098805, checked on 2026-11-13). No official NASA list names it: the PDS4 context products have entries for its two cameras (urn:esa:psa:context:instrument:ro.osinac and ro.osiwac) and none for OSIRIS itself.
- **Left out:** what "ROSETTA" is (notes, inside the name "ROSETTA EXTENSION 2")
  - **Rule:** What counts as a fact, rule 1: "An unexplained code or abbreviation gives no ground truth triple whose meaning depends on what it stands for, and what it stands for is never written, its entity class included". The record never says what ROSETTA is: "the Rosetta spacecraft" names the craft, and the phase's name holds "ROSETTA" alone. Its entity class, Mission, is written ("ROSETTA EXTENSION 2" PART_OF "ROSETTA", by rule 2's *A fact inside a name*: "a Mission named in the name of one of its parts ... gives PART_OF"), by rule 1's *A name the record does not explain*.
  - The list: PDS4 context product urn:esa:psa:context:investigation:mission.international_rosetta_mission, "The International Rosetta Mission", of type Mission, also titled "ROSETTA" (https://pds.nasa.gov/data/pds4/context-pds4/investigation/mission.international_rosetta_mission_1.1.xml, checked on 2026-11-13). The craft's entry, urn:esa:psa:context:instrument_host:spacecraft.ro, is titled "ROSETTA-ORBITER", not "ROSETTA".
