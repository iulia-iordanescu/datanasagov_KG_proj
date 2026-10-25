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
  - **Rule:** none that I can quote. I wrote both developers as ground truth triples (DEVELOPED_BY_PARTY), and no predicate of the ground truth schema says "jointly". This is a gap in the ground truth that rule 2 of *What counts as a fact* ("Every fact the record states") would count against me; I have not decided it.
  - **May matter because:** it says the two developed the mission together, not each one part.
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
