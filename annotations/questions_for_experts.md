# Questions for subject-matter experts

The questions I ask subject-matter experts, one per decision an expert's answer would settle, each written out whole, so that it can be read without anything else: the question, one record as its clearest example (quoted in full, with its ground truth triples), the definitions of the ground truth schema, the rows of the translation table and the rules of the annotation guidelines it is judged by (quoted), the options I see, as plain choices, and my current reading. That part is all the expert reads to answer; it never names a record by its pool position or id, only by its title, in quotes. The rest is my bookkeeping, which the page shows folded at the bottom, under *The answer to this question impacts:*: *My notes*, the *Consequences* of each option, and *Affects*, where each question lists everything its answer may change: every record and classed triple, row, ground truth schema entry, rule and pipeline method, not only the example. The review page (`py helpers/review_page.py`) shows the open ones in its **Questions** view, most urgent first, each with a box for the expert's answer, which comes back with their other comments.

This file is the questions' one home: I write and change them here, and nowhere else. The page reads it in a strict format, and refuses to be made while a question isn't in it, while a quote isn't what its source says now (a record's title or notes, a ground truth triple, a definition, a row, a rule), or while *Affects* leaves out a ground truth triple or a row of a ground truth schema entry it names, naming the line. Only tuning records may appear: the page refuses a held-out record. A new doubt that one of these answers would settle goes into that question (a sub-question, and its records and classed triples under *Affects*), not into a question of its own; a question keeps its number for good, since comments are filed under it. The format, and how to add to a question: [helpers/review_page.md](../helpers/review_page.md), *The questions file*.

## Q1: Should SpatialRepresentation be a closed list?

- status: open
- priority: high
- question kind: schema entry
- topic: the ground truth schema's SpatialRepresentation, and rule 1 of the annotation guidelines

### The question

How a dataset's data are laid out over the ground is, so far, written in each [record](../docs/terminology.md#1-records-and-their-text)'s own words: "swath", "Polar-Gridded", "spatially gridded", "map", "gridded". I am not sure whether to keep those words, or to use a closed list of values instead, the same few words for every record of the catalog. To decide, I need to know:

- (a) Is the spatial representation, for the records of this catalog, a closed set of values? Beyond swath and gridded, which layouts occur? The CF conventions name the layouts of data that are not on a grid, their discrete sampling geometries: a single point, a time series at one place, a trajectory (e.g. an aircraft's or a ship's track), a vertical profile, a time series of profiles, and a trajectory of profiles (Eaton, Gregory, Drach, Taylor, Hankin, et al., *NetCDF Climate and Forecast (CF) Metadata Conventions*, version 1.13, 17 December 2025, chapter 9, *Discrete Sampling Geometries*, Table 9.1; https://cfconventions.org/, doi:10.5281/zenodo.17801666). Which of these occur in this catalog, and are there others?
- (b) Is a Planetary Data System "map" product gridded? For example, the record "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0" says "These data are maps of fast neutron residual count rates".
- (c) Is "Polar-Gridded" (in the example below) gridded, on a polar grid? That is, would it be the value gridded, plus a separate fact about which grid? The same for the record "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid", whose title ends in "Global 1km SIN Grid", the MODIS sinusoidal grid (checked, see below): should a record's grid be a fact of its own, written with the predicate BINNED_INTO and a Grid, as the record "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" already has: "pixels" (Dataset) BINNED_INTO "integerized sinusoidal area grid (ISEAG)" (Grid)? And does a polar grid say anything about the area the data cover: do "Polar-Gridded" data cover only the polar regions, or the whole Earth, laid out on a grid drawn around a pole? The example states no area, so I wrote none for it.
- (d) What kinds of thing collect the data of this catalog, and for each kind, which spatial representations occur? My guess is below: please complete or correct it.

| What collects the data | Spatial representations I expect |
|---|---|
| a satellite | swath; gridded |
| an aircraft, or a ship | a track (a trajectory) |
| a ground station | a point; a time series at one place |
| an instrument that measures along the vertical (e.g. a balloon) | a vertical profile |
| others? | ? |

### Context

The records I have read so far write a layout in these words: "5 minutes of swath data" (written down as "swath"), "Polar-Gridded", "spatially gridded (L3)" (written down as "spatially gridded"), "These data are maps" ("map") and "gridded Level 2 product" ("gridded"). The example below writes its layout in two ways, "Polar-Gridded" in its title and "gridded" in its notes.

Checked on 2026-10-25: "SIN Grid" is the MODIS sinusoidal grid, and "Global 1km SIN Grid" is the standard end of the titles of the MODIS products made on it, so "Global" there names the grid's worldwide tiling (NASA LAADS, the MCD19A2 product page, https://ladsweb.modaps.eosdis.nasa.gov/missions-and-measurements/products/MCD19A2; NASA MODAPS, MCD19A2N, https://modaps.modaps.eosdis.nasa.gov/services/about/products/c61-nrt/MCD19A2N.html). Whether that grid is a fact of its own is still question (c).

### Example record

- record id: 2705e0d1-95e7-4588-813b-ca91a6da94ff
- pool position: 3
- title: Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005
- notes: This data set consists of weekly gridded Level-3 products of Aquarius L-band radiometer Sea Surface Salinity (SSS) retrievals from the Aquarius/Satélite de Aplicaciones Científicas (SAC-D) mission, developed collaboratively between the U.S. National Aeronautics and Space Administration (NASA) and Argentina's space agency, Comisión Nacional de Actividades Espaciales (CONAE).
- source text: Polar-Gridded
- source text: weekly gridded Level-3 products
- classed triple: "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005" (Dataset) HAS_SPATIAL_REPRESENTATION "Polar-Gridded" (SpatialRepresentation)

### Ground truth schema

- entity class SpatialRepresentation: how data are laid out over the ground; for a satellite, this is typically either along the satellite's path, as observed (swath), or on a fixed map grid (gridded)
- predicate HAS_SPATIAL_REPRESENTATION: lays out its data as
- entity class Grid: a fixed set of cells that data values are collected into, e.g. ISEAG
- predicate BINNED_INTO: its values were collected into the cells of this Grid

### Annotation guidelines

- Writing a classed triple, rule 1: Subject instance and object instance: the record's own words, as written. Don't paraphrase them, and don't expand an acronym the record leaves unexpanded. Three exceptions: rule 9 takes some qualifiers out of an instance, rule 12 copies a list's shared words onto each item, and rule 13 uses one wording for a thing everywhere in the record.
- Writing a classed triple, rule 6: Each fact once, even if the record states it twice or in other words. Keep the wording that says the most: Suppose: the notes say "gridded" and the title says "Polar-Gridded". Then: one ground truth triple, with "Polar-Gridded".
- Writing a classed triple, rule 9: A qualifier that is a temporal resolution, an area the data cover, a processing level, a spatial resolution, a country, a time of day, or a target body is a ground truth triple of its own, and is taken out of the instance.
- Writing a classed triple, rule 9: A qualifier stays in the instance, as written, if it is any other kind ("sea surface salinity" stays whole), or if taking it out would give a triple that isn't true.
- Writing a classed triple, rule 12: A list joined by "and": one ground truth triple per item, when each item alone is a complete object.
- Writing a classed triple, rule 13: One thing, one wording, within a record.

### Options

#### Option 1: Keep each record's own words

Each record keeps its own words for its layout, as written (rule 1): "swath", "Polar-Gridded", "spatially gridded", "map", "gridded".

#### Option 2: A closed list

A short list of layouts (swath, gridded, and the others your answers to (a) and (d) name), and each record's layout is written as the value of the list its words mean, in place of its own words: "spatially gridded" becomes "gridded".

### My current reading

Undecided, leaning towards option 2, a closed list, if the answers to (a) and (d) give a list that covers the catalog. Until then, the ground truth keeps each record's own words (option 1).

### My notes

I have annotated the records at [pool positions](../docs/terminology.md#4-ground-truth-and-samples) 0 to 5, all [tuning records](../docs/terminology.md#7-evaluating-extraction-step-070), and I am annotating the one at pool position 6 (not in the ground truth yet). Of these seven, five state a spatial representation: pool position 2 ("5 minutes of swath data": "swath"), 3 ("Polar-Gridded"), 4 ("spatially gridded (L3)": "spatially gridded"), 5 ("These data are maps": "map") and 6 ("gridded Level 2 product": "gridded"). The example is the one at pool position 3; all five, with their classed triples, are listed under Affects.

Until the questions are answered, the ground truth keeps each record's own words: the record at pool position 4 keeps "spatially gridded" as written (rule 1, and rule 9: "A qualifier stays in the instance, as written, if it is any other kind"). The record at pool position 3 states no area, so its ground truth has none.

Pending facts, for the record at pool position 6 (4c64f3ed, not in the ground truth yet):

- pending fact: its fact 14, "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) BINNED_INTO "SIN Grid" or "Global 1km SIN Grid" (Grid), left out for now; added if the answer to (c) says a record's grid is a fact of its own (and which wording).

### Consequences

#### Option 1: Keep each record's own words

- Nothing changes: not the annotation guidelines, not the copy of the rules the [model](../docs/terminology.md#8-the-pipeline) follows when it extracts (`common/common_prompts/extraction_rules.txt`), and not the ground truth triples listed under Affects.
- One layout is written in different words in different records ("gridded", "spatially gridded", and perhaps "Polar-Gridded" and "map"), so a search of the knowledge graph for gridded data has to know every wording.

#### Option 2: A closed list

- A new exception to rule 1, like rules 9, 12 and 13 (quoted above): written in the annotation guidelines and in the copy of the rules the model follows, which both change.
- The ground truth triples listed under Affects are checked again, and some object instances change ("spatially gridded"; "map" and "Polar-Gridded", depending on the answers to (b) and (c)).
- The list has to cover the catalog: a record whose layout isn't on it has no value to use (question (a)).
- A record's own word for its layout ("Polar-Gridded") is no longer in that triple; what it adds to the value (a polar grid) is kept only if it is a fact of its own (question (c)).
- Every record names a layout the same way, so a search of the knowledge graph for gridded data needs one value.

### Affects

- record at pool position 2: 6cfafd07-40f1-46da-9d92-36c2bb319f0b
- record at pool position 3: 2705e0d1-95e7-4588-813b-ca91a6da94ff
- record at pool position 4: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- record at pool position 5: 99dff022-24ac-48cb-bc83-09fec8b90ad7
- record at pool position 6: 4c64f3ed-39b4-4f95-95a0-022898ba47a4
- classed triple of the record at pool position 2: "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" (Dataset) HAS_SPATIAL_REPRESENTATION "swath" (SpatialRepresentation)
- classed triple of the record at pool position 3: "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005" (Dataset) HAS_SPATIAL_REPRESENTATION "Polar-Gridded" (SpatialRepresentation)
- classed triple of the record at pool position 4: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) HAS_SPATIAL_REPRESENTATION "spatially gridded" (SpatialRepresentation)
- classed triple of the record at pool position 5: "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0" (Dataset) HAS_SPATIAL_REPRESENTATION "map" (SpatialRepresentation)
- classed triple of the record at pool position 6: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) HAS_SPATIAL_REPRESENTATION "gridded" (SpatialRepresentation)
- ground truth schema entry: entity class SpatialRepresentation
- ground truth schema entry: predicate HAS_SPATIAL_REPRESENTATION
- rule: Writing a classed triple, rule 1
- rule: Writing a classed triple, rule 6
- pipeline method: common/common_prompts/extraction_rules.txt: the model's copy of the annotation guidelines' rules, which a closed list would change

## Q2: Mission or Spacecraft, when a mission and its spacecraft are written with the same words?

- status: open
- priority: high
- question kind: schema entry
- topic: the ground truth schema's Mission and Spacecraft, and FROM_MISSION and FROM_SPACECRAFT

### The question

Many records name where their data came from with one word that can mean a mission or the spacecraft that flew it: "DAWN", "Aqua", "Terra", "Rosetta", "Aquarius". The ground truth schema has an entity class for each, Mission ("a named spaceflight effort") and Spacecraft ("a craft that operates in space"), and a predicate for each, FROM_MISSION and FROM_SPACECRAFT. When a record writes only such a word, I have to choose one of the two, and the [fact](../docs/terminology.md#2-triples) I write down depends on that choice. To decide, I need to know:

- (a) When a record says only "DAWN", "Aqua" or "Terra", without the word "mission" or "satellite" next to it, would someone in your field read it as the spacecraft, as the mission, or as both at once?
- (b) In a Planetary Data System data set title, such as "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0" or "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0", is the first word the spacecraft that carried the instrument? My reading, not checked against a source: these titles start with the spacecraft, which the Planetary Data System calls the instrument host.
- (c) "Aquarius/Satélite de Aplicaciones Científicas (SAC-D) mission" (in the record "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005"): my reading, not checked against a source, is that Aquarius was an instrument carried on the SAC-D spacecraft, and Aquarius/SAC-D the mission. Is that right, and if so, should the record's "Aquarius L-band radiometer" be the only Instrument here, with no Spacecraft named?
- (d) Is there a rule that holds for this whole catalog, e.g. "a word that is only a mission's word is a Mission; a word written before an instrument (MODIS/Aqua) is a Spacecraft"?

### Context

The example below has both. So far I have used Mission where the record writes the word "mission" or a mission's data set ("a Rosetta Radio Science data set", "the Aquarius/… (SAC-D) mission"), and Spacecraft where the word names the craft that carries the instrument ("MODIS/Aqua", "on board the Aqua satellite", "DAWN" in the title, "ROSETTA-ORBITER").

For the example, I wrote "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (Dataset) FROM_MISSION "Rosetta" (Mission), from "a Rosetta Radio Science data set", and "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (Dataset) FROM_SPACECRAFT "ROSETTA-ORBITER" (Spacecraft), from its title. For the record "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0", I wrote only "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0" (Dataset) FROM_SPACECRAFT "DAWN" (Spacecraft), from its title, although DAWN is also the name of the mission.

### Example record

- record id: cfd6ec3f-1e63-4a77-bc3f-007d45f7e2fc
- pool position: 1
- title: ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0
- notes: This is a Rosetta Radio Science data set, collected during the COMET ESCORT 4 phase 2015-10-22 to 2015-12-31. It is a Global Gravity measurement at the comet 67P and covers the time 2015-11-01T19:58:35.000 to 2015-11-02T04:59:27.000.
- source text: This is a Rosetta Radio Science data set
- source text: ROSETTA-ORBITER
- classed triple: "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (Dataset) FROM_MISSION "Rosetta" (Mission)
- classed triple: "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (Dataset) FROM_SPACECRAFT "ROSETTA-ORBITER" (Spacecraft)

### Ground truth schema

- entity class Mission: a named spaceflight effort
- entity class Spacecraft: a craft that operates in space
- entity class Instrument: a device that takes measurements
- predicate FROM_MISSION: came from this Mission
- predicate FROM_SPACECRAFT: was collected from this Spacecraft
- predicate ABOARD: is carried on

### Translation table

- entity class Mission -> Mission: A planned space or flight undertaking, such as a satellite mission, balloon program, or spaceflight of a given duration, carried out to accomplish scientific objectives.
- entity class Spacecraft -> Spacecraft: A vehicle or platform, such as a satellite, aircraft, or balloon, that carries instruments to collect observations.

### Annotation guidelines

- What counts as a fact, rule 1: Only what the record states. Never add what you know from elsewhere, and never write down what an unexplained code or acronym stands for.
- Writing a classed triple, rule 1: Subject instance and object instance: the record's own words, as written.
- Writing a classed triple, rule 4: Entity classes and predicates: the ground truth schema's, when one fits, so records name the same things the same way.
- Writing a classed triple, rule 13: One thing, one wording, within a record.

### Options

#### Option 1: Spacecraft where the words name the craft, Mission where they name the mission

What the ground truth does now: FROM_SPACECRAFT when the record's words name the craft that carries the instrument ("MODIS/Aqua", "DAWN" at the start of a Planetary Data System title), FROM_MISSION when they name the mission ("a Rosetta Radio Science data set", "the … mission").

#### Option 2: Always Mission

Every such word becomes FROM_MISSION, with the object instance a Mission, whether the record names the craft or the mission.

#### Option 3: Both, a Mission and a Spacecraft

Every such word gives two ground truth triples, FROM_MISSION and FROM_SPACECRAFT, with the same words.

#### Option 4: A rule by where the record comes from

A rule per part of the catalog, e.g. in a Planetary Data System title, the first word is the Spacecraft (the instrument host); in an Earth science record, "<instrument>/<word>" names the Spacecraft; the word "mission" names the Mission.

### My current reading

Option 1, as the ground truth does now, because it follows the record's own words (rule 1) and adds nothing the record doesn't state. I would move to option 4 if your answers to (b) and (d) give a rule that holds across the catalog, since it would make the choice the same for every record.

### My notes

Of the [tuning records](../docs/terminology.md#7-evaluating-extraction-step-070) I have annotated so far, six name a mission or a spacecraft, at pool positions 1 to 6 (the one at pool position 6 is not in the ground truth yet: I am annotating it); all their classed triples that the answer may change are listed under Affects. The example is the record at pool position 1; the record "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0" is at pool position 5.

### Consequences

#### Option 1: Spacecraft where the words name the craft, Mission where they name the mission

- No change to the ground truth triples listed under Affects, nor to the annotation guidelines.
- Each record needs a judgment, made from clues in its own words; two people may judge the same word differently, and so may the [model](../docs/terminology.md#8-the-pipeline) when it extracts.
- A search of the knowledge graph for "all data from DAWN" has to look under both FROM_MISSION and FROM_SPACECRAFT.

#### Option 2: Always Mission

- One choice for every record: easier to apply the same way.
- The ground truth triples with FROM_SPACECRAFT (listed under Affects) change to FROM_MISSION ("DAWN", "Aqua", "ROSETTA-ORBITER", "Terra").
- "MODIS" ABOARD "Aqua" (pool positions 2 and 4) would join an Instrument to a Mission, which ABOARD's definition ("is carried on") doesn't fit: a mission doesn't carry an instrument.

#### Option 3: Both, a Mission and a Spacecraft

- A search finds the data under either predicate.
- Against "What counts as a fact", rule 1 (quoted above): a record that names only the craft doesn't state the mission, so the second ground truth triple adds what I know from elsewhere.
- The ground truth gets more ground truth triples per record, and the model would be expected to write both too.

#### Option 4: A rule by where the record comes from

- The same words are always read the same way within each part of the catalog.
- The rule has to be written into the annotation guidelines and into the copy of the rules the model follows, and it holds only if your answers to (b) and (d) confirm it.

### Affects

- record at pool position 1: cfd6ec3f-1e63-4a77-bc3f-007d45f7e2fc
- record at pool position 2: 6cfafd07-40f1-46da-9d92-36c2bb319f0b
- record at pool position 3: 2705e0d1-95e7-4588-813b-ca91a6da94ff
- record at pool position 4: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- record at pool position 5: 99dff022-24ac-48cb-bc83-09fec8b90ad7
- record at pool position 6: 4c64f3ed-39b4-4f95-95a0-022898ba47a4
- classed triple of the record at pool position 1: "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (Dataset) FROM_MISSION "Rosetta" (Mission)
- classed triple of the record at pool position 1: "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (Dataset) FROM_SPACECRAFT "ROSETTA-ORBITER" (Spacecraft)
- classed triple of the record at pool position 2: "Moderate Resolution Imaging Spectroradiometer (MODIS)" (Instrument) ABOARD "Aqua" (Spacecraft)
- classed triple of the record at pool position 2: "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" (Dataset) FROM_SPACECRAFT "Aqua" (Spacecraft)
- classed triple of the record at pool position 3: "Aquarius/Satélite de Aplicaciones Científicas (SAC-D)" (Mission) DEVELOPED_BY_PARTY "Comisión Nacional de Actividades Espaciales (CONAE)" (Organization)
- classed triple of the record at pool position 3: "Aquarius/Satélite de Aplicaciones Científicas (SAC-D)" (Mission) DEVELOPED_BY_PARTY "National Aeronautics and Space Administration (NASA)" (Organization)
- classed triple of the record at pool position 3: "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005" (Dataset) FROM_MISSION "Aquarius/Satélite de Aplicaciones Científicas (SAC-D)" (Mission)
- classed triple of the record at pool position 4: "Moderate-resolution Imaging Spectroradiometer (MODIS)" (Instrument) ABOARD "Aqua" (Spacecraft)
- classed triple of the record at pool position 4: "Aqua" (Spacecraft) FLIES_IN "A-train" (SatelliteFormation)
- classed triple of the record at pool position 4: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) FROM_SPACECRAFT "Aqua" (Spacecraft)
- classed triple of the record at pool position 4: "Aqua" (Spacecraft) HAS_ORBIT "sun synchronous, polar orbit with a daylight ascending node at 13:30" (Orbit)
- classed triple of the record at pool position 4: "Aqua" (Spacecraft) HAS_PURPOSE "study the global dynamics of the Earth atmosphere, land and oceans" (Purpose)
- classed triple of the record at pool position 4: "Aqua" (Spacecraft) LAUNCHED_BY_PARTY "NASA" (Organization)
- classed triple of the record at pool position 4: "Aqua" (Spacecraft) LAUNCHED_ON "May 4, 2002" (Time)
- classed triple of the record at pool position 5: "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0" (Dataset) FROM_SPACECRAFT "DAWN" (Spacecraft)
- classed triple of the record at pool position 6: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) FROM_SPACECRAFT "Terra" (Spacecraft)
- classed triple of the record at pool position 6: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) FROM_SPACECRAFT "Aqua" (Spacecraft)
- translation table row: entity class Mission
- translation table row: entity class Spacecraft
- translation table row: entity class SpaceStation
- ground truth schema entry: entity class Mission
- ground truth schema entry: entity class Spacecraft
- ground truth schema entry: predicate FROM_MISSION
- ground truth schema entry: predicate FROM_SPACECRAFT
- rule: What counts as a fact, rule 1
- rule: Writing a classed triple, rule 1
- rule: Writing a classed triple, rule 4
- rule: Writing a classed triple, rule 13
- pipeline method: common/common_prompts/extraction_rules.txt: the model's copy of the annotation guidelines' rules, which follows any change to them

## Q3: Variable or PhysicalQuantity: what is measured, and what is computed?

- status: open
- priority: high
- question kind: schema entry
- topic: the ground truth schema's Variable and PhysicalQuantity, and HAS_MEASUREMENTS_OF, HAS_VARIABLE and ESTIMATES

### The question

The ground truth schema separates two things a dataset can hold. A PhysicalQuantity is "a property that can be measured, in general, whatever method measures it" (sea surface temperature, snow cover). A Variable is "one named kind of value computed from an Instrument's measurements by one particular Algorithm" (SST4, NDSI). A dataset HAS_MEASUREMENTS_OF a PhysicalQuantity, and HAS_VARIABLE a Variable; a Variable ESTIMATES a PhysicalQuantity. I am not sure the line falls where I put it in the records annotated so far. I would like to know:

- (a) Is the line right as the two definitions draw it: a PhysicalQuantity is a property of the thing observed, which any method could measure; a Variable is one named product of one algorithm?
- (b) The Normalized Difference Snow Index (NDSI, in the record "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061") is an index computed from radiances. Is it a Variable, or something of its own (an index), neither a Variable nor a PhysicalQuantity? And is my reading of how the snow cover is made right: the NDSI is computed from the radiance data (by a method the record doesn't name), and the snow cover from the NDSI by "a series of screens"?
- (c) "fast neutron residual count rates" (in the record "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0") are rates an instrument counts, not a property of Vesta. Are they a Variable, or a third thing: what the instrument recorded, before it is turned into a property of the body? The same record says "The nominal fast neutron count rates were detrended", and the ground truth writes "nominal fast neutron count rates" as a Variable too. Those are the counts as the instrument recorded them, before any processing, which sits badly with a Variable's "computed from an Instrument's measurements by one particular Algorithm": what are they?
- (d) "Sea Surface Salinity (SSS) retrievals" (in the record "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005") is written down as "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005" (Dataset) HAS_MEASUREMENTS_OF "Sea Surface Salinity (SSS)" (PhysicalQuantity). Should every quantity a record calls a "retrieval" be a Variable instead, since an algorithm computed it?
- (e) The record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" says "It is a Global Gravity measurement at the comet 67P", and I wrote "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (Dataset) HAS_MEASUREMENTS_OF "Gravity" (PhysicalQuantity) and "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (Dataset) HAS_SPATIAL_COVERAGE "Global" (SpatialExtent). Is "Gravity" the quantity measured (the comet's gravity field)? Or is "Global Gravity" the name of a kind of radio science measurement, as a whole, beside "Occultation" and "Solar Conjunction", which other records of the catalog name in the same sentence? If these are kinds of measurement: what is measured in each, in plain words (for example, my reading, not checked against a source: an occultation measures the atmosphere the radio signal passes through)?
- (f) "Aerosol Optical Depth" (in the record "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid") is what the record's product holds, computed by MAIAC ("Multi-Angle Implementation of Atmospheric Correction (MAIAC) Land Aerosol Optical Depth gridded Level 2 product"). I wrote it as a PhysicalQuantity, a property of the atmosphere that other methods could measure too, and MAIAC as the method. Is that right, or is it a Variable, since one algorithm computed it?
- (g) The same record says "The MCD19A2N product provides the atmospheric properties and view geometry", and I wrote "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) HAS_MEASUREMENTS_OF "atmospheric properties" (PhysicalQuantity) and "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) HAS_MEASUREMENTS_OF "view geometry" (PhysicalQuantity). Is "atmospheric properties" specific enough to be a fact, or too vague to write down? And is "view geometry" (the angles between the sun, the satellite and the ground) a PhysicalQuantity, something measured, or supporting information the files hold, which would need another entity class or predicate?

### Context

The example below holds both: a PhysicalQuantity, and two Variables that estimate it. The record "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" says its snow cover is "detected using Normalized Difference Snow Index (NDSI) and a series of screens", and "The NDSI is derived from radiance data"; the record "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0" says "These data are maps of fast neutron residual count rates"; and the record "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005" says "Aquarius L-band radiometer Sea Surface Salinity (SSS) retrievals".

The sentence of the record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" recurs across the catalog. I counted it in the records of the catalog (020's records.jsonl, 36,406 records, harvested before 2026-10-24): "It is a Global Gravity measurement" in 2,835 records (2,442 of them "at the comet 67P"), "It is a Occultation measurement" in 439, "It is a Solar Conjunction measurement" in 240, and "It is a Phobos Gravity measurement" in 9. Since "Phobos Gravity" sits beside "Global Gravity", my reading is that the word before "Gravity" says which gravity measurement it is, not an area; but I don't know. (Whether "Global" can be an area at a comet at all, I ask separately; here the question is only what is measured.)

### Example record

- record id: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- pool position: 4
- title: MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0
- notes: Day and night spatially gridded (L3) global NASA skin sea surface temperature (SST) products from the Moderate-resolution Imaging Spectroradiometer (MODIS) onboard the Aqua satellite. Average daily, weekly (8 day), monthly and annual skin SST products at are available at both 4.63 and 9.26 km spatial resolution. Aqua was launched by NASA on May 4, 2002, into a sun synchronous, polar orbit with a daylight ascending node at 13:30, formation flying in the A-train with other Earth Observation Satellites (EOS), to study the global dynamics of the Earth atmosphere, land and oceans. MODIS captures data in 36 spectral bands at a variety of spatial resolutions. Two SST products can be present in these files. The first is a skin SST produced for both day and night (NSST) observations, derived from the long wave IR 11 and 12 micron wavelength channels, using a modified nonlinear SST algorithm intended to provide continuity of SST derived from heritage and current NASA sensors. At night, a second SST product is generated using the mid-infrared 3.95 and 4.05 micron wavelength channels which are unique to MODIS; the SST derived from these measurements is identified as SST4. The SST4 product has lower uncertainty, but due to sun glint can only be used at night. To generate the L3 products the L2 pixels are binned into an integerized sinusoidal area grid (ISEAG) and mapped into an equidistant cylindrical (also known as Platte Carre projection. Additional projection detailed can be found at https://oceancolor.gsfc.nasa.gov/docs/format/ The NASA MODIS L3 SST data products are generated by the NASA Ocean Biology Processing Group (OBPG) and Peter Minnett and his team at the Rosenstiel School of Marine and Atmospheric Science (RSMAS) are responsible for sea surface temperature algorithm development, error statistics and quality flagging. JPL acquires MODIS ocean L3 SST data from the OBPG and is the official Physical Oceanography Data Archive (PO.DAAC) for SST. The R2019.0 supersedes the previous v2014.1 datasets which can be found at https://doi.org/10.5067/MODAM-8D4N4
- source text: global NASA skin sea surface temperature (SST) products
- source text: SST MID-IR
- source text: The first is a skin SST produced for both day and night (NSST)
- source text: the SST derived from these measurements is identified as SST4
- classed triple: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) HAS_MEASUREMENTS_OF "skin sea surface temperature (SST)" (PhysicalQuantity)
- classed triple: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) HAS_VARIABLE "SST4" (Variable)
- classed triple: "skin SST (NSST)" (Variable) ESTIMATES "skin sea surface temperature (SST)" (PhysicalQuantity)
- classed triple: "SST4" (Variable) ESTIMATES "SST" (PhysicalQuantity)

### Ground truth schema

- entity class PhysicalQuantity: a property that can be measured, in general, whatever method measures it, e.g. sea surface temperature; snow cover
- entity class Variable: one named kind of value computed from an Instrument's measurements by one particular Algorithm, e.g. SST4; NDSI
- entity class Algorithm: a method applied to data to compute a result, e.g. a series of screens; a modified nonlinear SST algorithm
- entity class SpatialExtent: the area the data cover, of the CelestialBody they are about: all of it (global) or part of it (e.g. the Arctic; the south pole of Mars)
- entity class CelestialBody: a natural object in space
- predicate HAS_MEASUREMENTS_OF: holds measurements of
- predicate HAS_VARIABLE: holds this Variable in its files
- predicate ESTIMATES: gives approximate values for
- predicate COMPUTED_FROM: was made by processing this input
- predicate PRODUCED_USING_ALGORITHM: was made or detected by applying this Algorithm
- predicate HAS_SPATIAL_COVERAGE: covers this area
- predicate HAS_TARGET: is about this CelestialBody

### Translation table

- entity class PhysicalQuantity -> PhysicalQuantity: A measurable physical property or variable, such as temperature, wind speed, water vapor, or emission distribution, that is observed or derived in a dataset.
- predicate MEASURES -> HAS_MEASUREMENTS_OF: The subject (an instrument, mission, dataset or product) measures or provides data on the object, a physical quantity, variable or phenomenon.
- predicate PROVIDES -> HAS_MEASUREMENTS_OF: The subject (an instrument, data center, product or dataset) supplies or produces the object, a data product, measurement, variable or information layer.
- predicate MEASURED_BY -> HAS_MEASUREMENTS_OF (swap subject and object): Links a measured quantity to the instrument, system or method used to measure it.

### Annotation guidelines

- Writing a classed triple, rule 4: Entity classes and predicates: the ground truth schema's, when one fits, so records name the same things the same way.
- Writing a classed triple, rule 9: A qualifier that is a temporal resolution, an area the data cover, a processing level, a spatial resolution, a country, a time of day, or a target body is a ground truth triple of its own, and is taken out of the instance.
- Writing a classed triple, rule 9: A qualifier stays in the instance, as written, if it is any other kind ("sea surface salinity" stays whole), or if taking it out would give a triple that isn't true.
- Writing a classed triple, rule 14: A processing step: output_i = method_i(input_i). For each processing step i the record describes, find its output_i, method_i, and input_i, and write at most two ground truth triples: output_i COMPUTED_FROM input_i, and output_i PRODUCED_USING_ALGORITHM method_i. Write each only if the record names both of its parts.

### Options

#### Option 1: Keep the line as the definitions draw it

A PhysicalQuantity for a property of what is observed (snow cover, sea surface salinity, gravity, aerosol optical depth); a Variable for a named value one algorithm computes (SST4, NDSI, the count rates).

#### Option 2: An entity class of its own for an index

Coin an entity class for an index computed from other values (the NDSI), apart from Variable and PhysicalQuantity.

#### Option 3: Every computed quantity is a Variable

A quantity the record says was retrieved or computed ("Sea Surface Salinity (SSS) retrievals", the aerosol optical depth MAIAC computes) is a Variable; a PhysicalQuantity only where the record names the property alone.

#### Option 4: An entity class of its own for what an instrument records

Coin an entity class for what the instrument itself records, before any conversion (count rates, radiances), apart from Variable.

#### Option 5: A kind of measurement of its own

Coin an entity class for a kind of measurement (for example, MeasurementType), with "Global Gravity", "Occultation" and "Solar Conjunction" as its object instances, and a predicate joining a Dataset to it; what is measured (gravity, for example) stays a PhysicalQuantity, where the record names it.

### My current reading

Option 1, because the two definitions already separate what is measured from the values an algorithm computes, and most records annotated so far fit them; "Aerosol Optical Depth" stays a PhysicalQuantity, since my reading is that other methods measure it too. Your answers to (b) and (c) decide whether the NDSI and the count rates need an entity class of their own (options 2 and 4). For (e), I lean towards "Global Gravity" whole (option 5, or its last consequence), because "Phobos Gravity" in other records reads like the same kind of name, with no area in it.

### My notes

Six of the [tuning records](../docs/terminology.md#7-evaluating-extraction-step-070) I have annotated so far hold a PhysicalQuantity or a Variable, at pool positions 1 to 6 (the one at pool position 6 is not in the ground truth yet: I am annotating it); their classed triples that say what the dataset holds, and what a value was computed from, are listed under Affects. The example is the record at pool position 4. The others named: pool position 1 (the "Global Gravity" sentence), 2 (the NDSI), 3 (the salinity retrievals), 5 (the count rates), 6 (the aerosol optical depth, the atmospheric properties and the view geometry).

Approved on 2026-10-25, for the record at pool position 6 (fact 13): HAS_MEASUREMENTS_OF "atmospheric properties" and HAS_MEASUREMENTS_OF "view geometry", source text "The MCD19A2N product provides the atmospheric properties and view geometry"; sub-question (g) asks the two doubts about them.

### Consequences

#### Option 1: Keep the line as the definitions draw it

- No change to the ground truth triples listed under Affects.
- The NDSI and the count rates stay Variables, though neither is a property of what is observed, and the current schema's PhysicalQuantity (in the translation table below) mixes the two ("a measurable physical property or variable"), so an extracted triple may use the other entity class.

#### Option 2: An entity class of its own for an index

- The ground truth triples with the NDSI change their entity class.
- One more entity class in the ground truth schema, for the annotation guidelines and the [model](../docs/terminology.md#8-the-pipeline) to tell apart from the other two.

#### Option 3: Every computed quantity is a Variable

- The ground truth triple with "Sea Surface Salinity (SSS)" (pool position 3) changes to HAS_VARIABLE, a Variable, and so does "Aerosol Optical Depth" (pool position 6).
- Almost every value in a satellite dataset is computed by some algorithm, so most PhysicalQuantities would become Variables, and a search for "salinity data" would have to look under both.
- The annotation guidelines, and the model's copy of their rules, say when a quantity counts as computed.

#### Option 4: An entity class of its own for what an instrument records

- The ground truth triples with the count rates (pool position 5) change their entity class, and perhaps "radiance data" (pool position 2).
- One more distinction for the annotation guidelines, and it holds only if your answer to (c) confirms it.

#### Option 5: A kind of measurement of its own

- The record at pool position 1's ground truth triples with "Gravity" and with "Global" become one ground truth triple with "Global Gravity" (rule 9: "Global" stays in the instance if it is no area).
- A new entity class and predicate in the ground truth schema; the model must learn to tell a kind of measurement from a quantity measured.
- If your answer to (e) is that "Global Gravity" is a name as a whole but still something measured, it stays a PhysicalQuantity instead, "Global Gravity", with the same change to the two ground truth triples.

### Affects

- record at pool position 1: cfd6ec3f-1e63-4a77-bc3f-007d45f7e2fc
- record at pool position 2: 6cfafd07-40f1-46da-9d92-36c2bb319f0b
- record at pool position 3: 2705e0d1-95e7-4588-813b-ca91a6da94ff
- record at pool position 4: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- record at pool position 5: 99dff022-24ac-48cb-bc83-09fec8b90ad7
- record at pool position 6: 4c64f3ed-39b4-4f95-95a0-022898ba47a4
- classed triple of the record at pool position 1: "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (Dataset) HAS_MEASUREMENTS_OF "Gravity" (PhysicalQuantity)
- classed triple of the record at pool position 1: "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (Dataset) HAS_SPATIAL_COVERAGE "Global" (SpatialExtent)
- classed triple of the record at pool position 2: "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" (Dataset) COMPUTED_FROM "Normalized Difference Snow Index (NDSI)" (Variable)
- classed triple of the record at pool position 2: "Normalized Difference Snow Index (NDSI)" (Variable) COMPUTED_FROM "radiance data" (Dataset)
- classed triple of the record at pool position 2: "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" (Dataset) HAS_MEASUREMENTS_OF "snow cover" (PhysicalQuantity)
- classed triple of the record at pool position 3: "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005" (Dataset) HAS_MEASUREMENTS_OF "Sea Surface Salinity (SSS)" (PhysicalQuantity)
- classed triple of the record at pool position 4: "skin SST (NSST)" (Variable) COMPUTED_FROM "long wave IR 11 micron wavelength channel" (Channel)
- classed triple of the record at pool position 4: "skin SST (NSST)" (Variable) COMPUTED_FROM "long wave IR 12 micron wavelength channel" (Channel)
- classed triple of the record at pool position 4: "SST4" (Variable) COMPUTED_FROM "mid-infrared 3.95 micron wavelength channel" (Channel)
- classed triple of the record at pool position 4: "SST4" (Variable) COMPUTED_FROM "mid-infrared 4.05 micron wavelength channel" (Channel)
- classed triple of the record at pool position 4: "SST4" (Variable) ESTIMATES "SST" (PhysicalQuantity)
- classed triple of the record at pool position 4: "skin SST (NSST)" (Variable) ESTIMATES "skin sea surface temperature (SST)" (PhysicalQuantity)
- classed triple of the record at pool position 4: "SST4" (Variable) HAS_LOWER_UNCERTAINTY_THAN "skin SST (NSST)" (Variable)
- classed triple of the record at pool position 4: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) HAS_MEASUREMENTS_OF "skin sea surface temperature (SST)" (PhysicalQuantity)
- classed triple of the record at pool position 4: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) HAS_VARIABLE "SST4" (Variable)
- classed triple of the record at pool position 4: "SST4" (Variable) LIMITED_BY "sun glint" (Phenomenon)
- classed triple of the record at pool position 4: "skin SST (NSST)" (Variable) OBSERVED_AT_TIME_OF_DAY "day" (TimeOfDay)
- classed triple of the record at pool position 4: "skin SST (NSST)" (Variable) OBSERVED_AT_TIME_OF_DAY "night" (TimeOfDay)
- classed triple of the record at pool position 4: "SST4" (Variable) OBSERVED_AT_TIME_OF_DAY "night" (TimeOfDay)
- classed triple of the record at pool position 4: "skin SST (NSST)" (Variable) PRODUCED_USING_ALGORITHM "modified nonlinear SST algorithm" (Algorithm)
- classed triple of the record at pool position 5: "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0" (Dataset) COMPUTED_FROM "nominal fast neutron count rates" (Variable)
- classed triple of the record at pool position 5: "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0" (Dataset) HAS_VARIABLE "fast neutron residual count rates" (Variable)
- classed triple of the record at pool position 5: "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0" (Dataset) RELATED_TO "average atomic mass" (PhysicalQuantity)
- classed triple of the record at pool position 6: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) HAS_MEASUREMENTS_OF "Aerosol Optical Depth" (PhysicalQuantity)
- classed triple of the record at pool position 6: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) HAS_MEASUREMENTS_OF "atmospheric properties" (PhysicalQuantity)
- classed triple of the record at pool position 6: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) HAS_MEASUREMENTS_OF "view geometry" (PhysicalQuantity)
- classed triple of the record at pool position 6: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) PRODUCED_USING_ALGORITHM "Multi-Angle Implementation of Atmospheric Correction (MAIAC)" (Algorithm)
- translation table row: entity class PhysicalQuantity
- translation table row: predicate MEASURES
- translation table row: predicate PROVIDES
- translation table row: predicate MEASURED_BY
- ground truth schema entry: entity class PhysicalQuantity
- ground truth schema entry: entity class Variable
- ground truth schema entry: predicate HAS_MEASUREMENTS_OF
- ground truth schema entry: predicate HAS_VARIABLE
- ground truth schema entry: predicate ESTIMATES
- rule: Writing a classed triple, rule 4
- rule: Writing a classed triple, rule 9
- rule: Writing a classed triple, rule 14
- pipeline method: common/common_prompts/extraction_rules.txt: the model's copy of the annotation guidelines' rules, which follows any change to them

## Q4: Where a dataset's data come from: which relationships to tell apart, and what carries the instruments?

- status: open
- priority: high
- question kind: schema entry
- topic: the ground truth schema's FROM_MISSION, FROM_SPACECRAFT, ACQUIRED_BY_INSTRUMENT, HAS_MISSION_PHASE and OBTAINS_DATA_FROM, its Spacecraft, Mission and MissionPhase, and the translation table's rows for the current schema's SOURCED_FROM, platforms and campaigns

### The question

A record often says where its data came from: an instrument, the craft that carried it, a mission, a phase of a mission, a field campaign, or the data center that holds the data. The ground truth schema has one predicate for each of several of these (FROM_MISSION, FROM_SPACECRAFT, ACQUIRED_BY_INSTRUMENT, HAS_MISSION_PHASE, OBTAINS_DATA_FROM), and its Spacecraft is "a craft that operates in space", its Mission "a named spaceflight effort". The schema the [model](../docs/terminology.md#8-the-pipeline) extracts with, the current schema, learned from other records of the catalog, draws these lines differently: it has mostly one broad predicate for all of them, SOURCED_FROM, which the translation table translates to (none), nothing in the ground truth schema; its Spacecraft includes aircraft and balloons, and its Mission includes balloon programs. So a [fact](../docs/terminology.md#2-triples) of FROM_MISSION or FROM_SPACECRAFT, when the model extracts it under SOURCED_FROM, can't count as found, and the same aircraft counts differently depending on which word of the current schema the model used. I would like to know:

- (a) For a dataset of this catalog, which of these are different relationships that someone in your field would ask about separately: the instrument, the craft that carried it (a spacecraft, or an aircraft, ship, balloon, ground station), the mission, the phase of a mission, the field campaign, the data center?
- (b) Which of them could be one relationship, "comes from", without losing anything you would search for?
- (c) Are there others a record of this catalog often states that are missing from that list?
- (d) Is an aircraft or a balloon that carries instruments the same kind of thing as a spacecraft, for this catalog (a "platform" in Earth science)? Should the ground truth schema have one entity class for anything that carries instruments, or keep spacecraft apart?
- (e) Is a space station (the International Space Station) a spacecraft?
- (f) Is a field campaign (a period of aircraft or balloon measurements) a phase of a mission, a mission of its own, or something else?
- (g) Is a scientific program (for example, a telescope's legacy program) a mission?

### Context

The example below names an instrument, the spacecraft that carries it, and a data center. In the current schema, the model filed such facts under SOURCED_FROM, ACQUIRED_BY and COLLECTED_DURING (the translation table's [rows](../docs/terminology.md#8-the-pipeline) for them are below). The example also says that the data center, JPL, "acquires MODIS ocean L3 SST data from the OBPG", which the ground truth writes with OBTAINS_DATA_FROM.

None of the records I have read so far names an aircraft, a balloon, a space station or a field campaign; they come up in records the model read when it learned the current schema. Before the model's classed triples are compared with the ground truth, each entity class and predicate of the current schema is translated into the one of the ground truth schema its row of the translation table names; a row that names (none) means the model's classed triples with it count as not in the ground truth.

### Example record

- record id: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- pool position: 4
- title: MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0
- notes: Day and night spatially gridded (L3) global NASA skin sea surface temperature (SST) products from the Moderate-resolution Imaging Spectroradiometer (MODIS) onboard the Aqua satellite. Average daily, weekly (8 day), monthly and annual skin SST products at are available at both 4.63 and 9.26 km spatial resolution. Aqua was launched by NASA on May 4, 2002, into a sun synchronous, polar orbit with a daylight ascending node at 13:30, formation flying in the A-train with other Earth Observation Satellites (EOS), to study the global dynamics of the Earth atmosphere, land and oceans. MODIS captures data in 36 spectral bands at a variety of spatial resolutions. Two SST products can be present in these files. The first is a skin SST produced for both day and night (NSST) observations, derived from the long wave IR 11 and 12 micron wavelength channels, using a modified nonlinear SST algorithm intended to provide continuity of SST derived from heritage and current NASA sensors. At night, a second SST product is generated using the mid-infrared 3.95 and 4.05 micron wavelength channels which are unique to MODIS; the SST derived from these measurements is identified as SST4. The SST4 product has lower uncertainty, but due to sun glint can only be used at night. To generate the L3 products the L2 pixels are binned into an integerized sinusoidal area grid (ISEAG) and mapped into an equidistant cylindrical (also known as Platte Carre projection. Additional projection detailed can be found at https://oceancolor.gsfc.nasa.gov/docs/format/ The NASA MODIS L3 SST data products are generated by the NASA Ocean Biology Processing Group (OBPG) and Peter Minnett and his team at the Rosenstiel School of Marine and Atmospheric Science (RSMAS) are responsible for sea surface temperature algorithm development, error statistics and quality flagging. JPL acquires MODIS ocean L3 SST data from the OBPG and is the official Physical Oceanography Data Archive (PO.DAAC) for SST. The R2019.0 supersedes the previous v2014.1 datasets which can be found at https://doi.org/10.5067/MODAM-8D4N4
- source text: products from the Moderate-resolution Imaging Spectroradiometer (MODIS)
- source text: MODIS Aqua
- source text: JPL acquires MODIS ocean L3 SST data from the OBPG
- source text: The NASA MODIS L3 SST data products are generated by the NASA Ocean Biology Processing Group (OBPG)
- classed triple: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) ACQUIRED_BY_INSTRUMENT "Moderate-resolution Imaging Spectroradiometer (MODIS)" (Instrument)
- classed triple: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) FROM_SPACECRAFT "Aqua" (Spacecraft)
- classed triple: "JPL" (Organization) OBTAINS_DATA_FROM "NASA Ocean Biology Processing Group (OBPG)" (Organization)
- classed triple: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) DEVELOPED_BY_PARTY "NASA Ocean Biology Processing Group (OBPG)" (Organization)

### Ground truth schema

- entity class Spacecraft: a craft that operates in space
- entity class Mission: a named spaceflight effort
- entity class MissionPhase: a named phase of a Mission
- predicate FROM_MISSION: came from this Mission
- predicate FROM_SPACECRAFT: was collected from this Spacecraft
- predicate ACQUIRED_BY_INSTRUMENT: was collected by this Instrument
- predicate HAS_MISSION_PHASE: was collected during this MissionPhase
- predicate OBTAINS_DATA_FROM: receives data from
- predicate DEVELOPED_BY_PARTY: was built or created by this Person, Team, or Organization

### Translation table

- predicate SOURCED_FROM -> (none): The subject (a dataset, file, objective or person) originates from the object, a source instrument, platform, observation set, data portion or institution.
- predicate ACQUIRED_BY -> ACQUIRED_BY_INSTRUMENT: The subject (a dataset or observed class of objects) is collected or detected by the object, an instrument or platform.
- predicate COLLECTED_DURING -> HAS_MISSION_PHASE: The subject (a dataset, campaign, mission activity or event) took place or was gathered during the object, a time period or named field campaign.
- predicate PROVIDED_BY -> (none): The subject (a product, campaign or responsibility) is supplied, conducted or overseen by the object, an organization, team or instrument mission.
- entity class Spacecraft -> Spacecraft: A vehicle or platform, such as a satellite, aircraft, or balloon, that carries instruments to collect observations.
- entity class SpaceStation -> Spacecraft: A crewed orbiting space station, such as the International Space Station, used as a platform for research and observation.
- entity class Aircraft -> (none): A crewed or research airplane used as a platform for airborne observations or measurements.
- entity class Mission -> Mission: A planned space or flight undertaking, such as a satellite mission, balloon program, or spaceflight of a given duration, carried out to accomplish scientific objectives.
- entity class Campaign -> (none): A coordinated period of field or flight measurement activity, such as an aircraft or balloon campaign, conducted to collect data.
- entity class Program -> (none): A named organized scientific initiative, often a telescope legacy or key program, encompassing coordinated observations and data products.

### Annotation guidelines

- Writing a classed triple, rule 4: Entity classes and predicates: the ground truth schema's, when one fits, so records name the same things the same way.
- Writing a classed triple, rule 5: One fact per ground truth triple. A sentence that states two facts gives two ground truth triples.

### Options

#### Option 1: Keep the ground truth schema and the translation table as they are

SOURCED_FROM, an aircraft, a campaign and a program (current schema) translate to (none); a space station to Spacecraft; the current schema's Spacecraft and Mission to the ground truth schema's Spacecraft and Mission; "collected during" to HAS_MISSION_PHASE.

#### Option 2: Translate SOURCED_FROM by the entity class of its object

A row of the translation table could say: SOURCED_FROM (current schema) with a Mission as object instance translates to FROM_MISSION (ground truth schema), with a Spacecraft to FROM_SPACECRAFT, and with anything else to (none). Today a row translates a predicate one way only, whatever its object.

#### Option 3: Let the current schema split SOURCED_FROM into one predicate per sense

When the current schema is learned (step 040), a broad predicate whose object instances are of several entity classes is split into one predicate per entity class, each of which the translation table can translate on its own.

#### Option 4: One "comes from" predicate in the ground truth schema

Merge the ground truth schema's predicates for the senses your answer to (b) says can be one.

#### Option 5: One entity class for anything that carries instruments

The ground truth schema's Spacecraft is widened (or a new entity class, for example Platform, takes its place) to any craft or station that carries instruments: satellites, aircraft, balloons, ships, space stations.

#### Option 6: Campaigns of their own

Coin an entity class for a field campaign (for example, Campaign) and a predicate for "collected during" a campaign, apart from MissionPhase.

### My current reading

Options 2 to 4 are about the predicates, options 5 and 6 about the entity classes, so one of each can be combined. For the predicates, option 3, then option 2 for what it leaves mixed: they keep the ground truth schema's distinctions, which follow what the records state, and fix the cause in the current schema, while option 4 throws the distinctions away. Your answers to (a) and (b) tell me which distinctions are worth keeping. For the entity classes, undecided: option 5 looks closer to how Earth science data are described, but no record annotated so far needs it, nor option 6; your answers to (d) and (f) decide them.

### My notes

Three [tuning records](../docs/terminology.md#7-evaluating-extraction-step-070), at pool positions 1, 3 and 4, have ground truth that states several of these relationships; every classed triple the answer may change is listed under Affects. The example is the record at pool position 4. None of the records annotated so far (pool positions 0 to 5, and 6, which I am annotating now) names an aircraft, a balloon, a space station or a field campaign, so no ground truth triple shows them yet.

### Consequences

#### Option 1: Keep the ground truth schema and the translation table as they are

- Nothing changes.
- Facts the model extracts under SOURCED_FROM never count as found.
- An aircraft that the current schema calls a Spacecraft is compared with the ground truth's Spacecraft, while one it calls an Aircraft is left out.
- A dataset "collected during" a field campaign is compared with HAS_MISSION_PHASE, though a campaign isn't a phase of a spaceflight effort.

#### Option 2: Translate SOURCED_FROM by the entity class of its object

- The ground truth stays as it is; the change is in how the extracted triples are compared with it ([step](../docs/terminology.md#8-the-pipeline) 070 and the translation table's format).
- It works only for the relationships that differ by the object's entity class; two that share one (a campaign and a mission, if both are Missions) stay mixed.

#### Option 3: Let the current schema split SOURCED_FROM into one predicate per sense

- The model extracts with the separate predicates, so the facts can count as found.
- A few more predicates in the current schema, so a longer schema in every request to the model; steps 040, 060 and 070 run again.

#### Option 4: One "comes from" predicate in the ground truth schema

- The ground truth triples listed under Affects that use those predicates change, and the ground truth schema loses the difference between them.
- Extraction and the ground truth agree more easily, but a search for "all data from the Aqua spacecraft" can no longer be told from "all data of the Aqua mission".

#### Option 5: One entity class for anything that carries instruments

- The rows for Aircraft and SpaceStation (current schema) translate to it; FROM_SPACECRAFT is renamed or widened with it.
- The annotation guidelines and the ground truth triples with Spacecraft are checked again.

#### Option 6: Campaigns of their own

- The rows for Campaign and COLLECTED_DURING (current schema) translate to them.
- A new entity class and predicate in the ground truth schema, used by no tuning record yet.

### Affects

- record at pool position 1: cfd6ec3f-1e63-4a77-bc3f-007d45f7e2fc
- record at pool position 2: 6cfafd07-40f1-46da-9d92-36c2bb319f0b
- record at pool position 3: 2705e0d1-95e7-4588-813b-ca91a6da94ff
- record at pool position 4: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- record at pool position 5: 99dff022-24ac-48cb-bc83-09fec8b90ad7
- record at pool position 6: 4c64f3ed-39b4-4f95-95a0-022898ba47a4
- classed triple of the record at pool position 1: "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (Dataset) ACQUIRED_BY_INSTRUMENT "RSI" (Instrument)
- classed triple of the record at pool position 1: "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (Dataset) FROM_MISSION "Rosetta" (Mission)
- classed triple of the record at pool position 1: "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (Dataset) FROM_SPACECRAFT "ROSETTA-ORBITER" (Spacecraft)
- classed triple of the record at pool position 1: "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (Dataset) HAS_MISSION_PHASE "COMET ESCORT 4" (MissionPhase)
- classed triple of the record at pool position 1: "COMET ESCORT 4" (MissionPhase) HAS_TIME_SPAN "2015-10-22 to 2015-12-31" (Time)
- classed triple of the record at pool position 2: "Moderate Resolution Imaging Spectroradiometer (MODIS)" (Instrument) ABOARD "Aqua" (Spacecraft)
- classed triple of the record at pool position 2: "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" (Dataset) ACQUIRED_BY_INSTRUMENT "Moderate Resolution Imaging Spectroradiometer (MODIS)" (Instrument)
- classed triple of the record at pool position 2: "radiance data" (Dataset) ACQUIRED_BY_INSTRUMENT "Moderate Resolution Imaging Spectroradiometer (MODIS)" (Instrument)
- classed triple of the record at pool position 2: "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" (Dataset) FROM_SPACECRAFT "Aqua" (Spacecraft)
- classed triple of the record at pool position 3: "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005" (Dataset) ACQUIRED_BY_INSTRUMENT "Aquarius L-band radiometer" (Instrument)
- classed triple of the record at pool position 3: "Aquarius/Satélite de Aplicaciones Científicas (SAC-D)" (Mission) DEVELOPED_BY_PARTY "Comisión Nacional de Actividades Espaciales (CONAE)" (Organization)
- classed triple of the record at pool position 3: "Aquarius/Satélite de Aplicaciones Científicas (SAC-D)" (Mission) DEVELOPED_BY_PARTY "National Aeronautics and Space Administration (NASA)" (Organization)
- classed triple of the record at pool position 3: "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005" (Dataset) FROM_MISSION "Aquarius/Satélite de Aplicaciones Científicas (SAC-D)" (Mission)
- classed triple of the record at pool position 4: "Moderate-resolution Imaging Spectroradiometer (MODIS)" (Instrument) ABOARD "Aqua" (Spacecraft)
- classed triple of the record at pool position 4: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) ACQUIRED_BY_INSTRUMENT "Moderate-resolution Imaging Spectroradiometer (MODIS)" (Instrument)
- classed triple of the record at pool position 4: "Aqua" (Spacecraft) FLIES_IN "A-train" (SatelliteFormation)
- classed triple of the record at pool position 4: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) FROM_SPACECRAFT "Aqua" (Spacecraft)
- classed triple of the record at pool position 4: "Aqua" (Spacecraft) HAS_ORBIT "sun synchronous, polar orbit with a daylight ascending node at 13:30" (Orbit)
- classed triple of the record at pool position 4: "Aqua" (Spacecraft) HAS_PURPOSE "study the global dynamics of the Earth atmosphere, land and oceans" (Purpose)
- classed triple of the record at pool position 4: "Aqua" (Spacecraft) LAUNCHED_BY_PARTY "NASA" (Organization)
- classed triple of the record at pool position 4: "Aqua" (Spacecraft) LAUNCHED_ON "May 4, 2002" (Time)
- classed triple of the record at pool position 4: "JPL" (Organization) OBTAINS_DATA_FROM "NASA Ocean Biology Processing Group (OBPG)" (Organization)
- classed triple of the record at pool position 5: "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0" (Dataset) ACQUIRED_BY_INSTRUMENT "GRaND" (Instrument)
- classed triple of the record at pool position 5: "GRaND epithermal neutron map" (Dataset) ACQUIRED_BY_INSTRUMENT "GRaND" (Instrument)
- classed triple of the record at pool position 5: "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0" (Dataset) ACQUIRED_BY_INSTRUMENT "GRaND plus Z boron loaded sensor" (Instrument)
- classed triple of the record at pool position 5: "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0" (Dataset) FROM_SPACECRAFT "DAWN" (Spacecraft)
- classed triple of the record at pool position 6: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) FROM_SPACECRAFT "Terra" (Spacecraft)
- classed triple of the record at pool position 6: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) FROM_SPACECRAFT "Aqua" (Spacecraft)
- classed triple of the record at pool position 6: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) ACQUIRED_BY_INSTRUMENT "Moderate Resolution Imaging Spectroradiometer (MODIS)" (Instrument)
- translation table row: entity class Spacecraft
- translation table row: entity class SpaceStation
- translation table row: entity class Mission
- translation table row: predicate ACQUIRED_BY
- translation table row: predicate COLLECTED_DURING
- translation table row: predicate SOURCED_FROM
- translation table row: predicate PROVIDED_BY
- translation table row: entity class Aircraft
- translation table row: entity class Campaign
- translation table row: entity class Program
- ground truth schema entry: entity class Spacecraft
- ground truth schema entry: entity class Mission
- ground truth schema entry: entity class MissionPhase
- ground truth schema entry: predicate FROM_MISSION
- ground truth schema entry: predicate FROM_SPACECRAFT
- ground truth schema entry: predicate ACQUIRED_BY_INSTRUMENT
- ground truth schema entry: predicate HAS_MISSION_PHASE
- ground truth schema entry: predicate OBTAINS_DATA_FROM
- rule: Writing a classed triple, rule 4
- rule: Writing a classed triple, rule 5
- pipeline method: 040_induce_schema/run.py: how the current schema is learned (option 3: splitting a broad predicate)
- pipeline method: common/common_helpers/component_class_mapping.py: how a row of the translation table translates (option 2: by the entity class of the object)

## Q5: Time in a record: temporal resolution, the time a file covers, and the period a dataset covers

- status: open
- priority: high
- question kind: schema entry
- topic: the ground truth schema's TemporalResolution, Time and Value, its HAS_TEMPORAL_RESOLUTION, HAS_GRANULE_DURATION and HAS_TIME_SPAN, and the translation table's rows for the current schema's Frequency, HAS_TIME_RESOLUTION, COVERS and HAS_DURATION

### The question

The ground truth schema has three entity classes for time: Time, "a point or period on the calendar, which happens once"; TemporalResolution, "the amount of time between one value of the data and the next, e.g. daily; weekly (8 day)"; and Value, "an amount", which HAS_GRANULE_DURATION uses for how much time each file covers. Its predicates for time are HAS_TEMPORAL_RESOLUTION ("gives values this often"), HAS_GRANULE_DURATION ("each of its files covers this much time") and HAS_TIME_SPAN ("covers this period"). Some records' words for time fit more than one of them, and the schema the [model](../docs/terminology.md#8-the-pipeline) extracts with, the current schema, learned from other records of the catalog, draws the lines more widely (its entries are in the translation table, below). I would like to know:

- (a) The record "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061", the example below, is a Level-2 swath dataset whose files each hold "5 minutes of swath data", and the record says it "provides daily snow cover". Is "daily" its temporal resolution, the time between one value and the next? My reading, not checked against a source: each file holds what the instrument saw along its path in those 5 minutes, and "daily" says how often the product is made, or how often the instrument passes over the same ground, not the time between two values in a file.
- (b) The record "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" is an "8 Day" average ("Average daily, weekly (8 day), monthly and annual skin SST products"). Its 8 days are both the time each value averages over and the time between one value and the next. Is that one thing, a temporal resolution, or two that should be told apart (the period a value averages over, and how often a value is given)?
- (c) Is the line between Time (a date or period that happens once), TemporalResolution (how often), and the time a file covers (HAS_GRANULE_DURATION, a Value) the one you would draw?
- (d) Is a granule, for this catalog, always one file? The ground truth schema's HAS_GRANULE_DURATION says "each of its files", reading the example below that way.
- (e) Is "each file (granule) covers 5 minutes" the same kind of fact as "the observation series lasted 3 years"? Would someone searching this catalog want them kept apart?
- (f) In this catalog, when a record says a dataset "covers" something, is it more often a period, an area, or a measured variable? Should "covers the Arctic" and "covers 2003 to 2010" ever share one predicate?
- (g) The current schema's entity class Frequency puts two things together: "A rate of occurrence, such as daily or weekly, or a radio frequency band, such as S-, X-, or Ku-band", and the translation table translates it into TemporalResolution. In this catalog, are how often data are given (daily, weekly) and a radio frequency band (S-band, X-band, Ku-band) two different kinds of thing, which should never share an entity class? (My reading is that they are: one is a time between values, the other a part of the radio spectrum. Where a radio band belongs, I ask separately.)

### Context

The example below states both how often ("daily") and how much time each file covers ("5 minutes"). Under annotation rule 9 (quoted below), a word such as "daily" in "daily snow cover" is taken out of the object instance and written as a temporal resolution of its own.

I write these facts with different predicates of the ground truth schema: HAS_TIME_SPAN for a period (the record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0": "covers the time 2015-11-01T19:58:35.000 to 2015-11-02T04:59:27.000"), HAS_SPATIAL_COVERAGE for an area, and HAS_GRANULE_DURATION for the time each file covers (the example below). Before the model's classed triples are compared with the ground truth, each entity class and predicate of the current schema is translated into the one of the ground truth schema its [row](../docs/terminology.md#8-the-pipeline) of the translation table names, and a row names only one. So a classed triple of the model that uses COVERS for an area is compared as a period, and one that files a radio band under Frequency is compared as a temporal resolution: both are counted wrong even when the model found the fact.

### Example record

- record id: 6cfafd07-40f1-46da-9d92-36c2bb319f0b
- pool position: 2
- title: MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061
- notes: This global Level-2 (L2) data set provides daily snow cover detected using Normalized Difference Snow Index (NDSI) and a series of screens designed to alleviate errors and flag uncertain snow cover detections. The NDSI is derived from radiance data acquired by the Moderate Resolution Imaging Spectroradiometer (MODIS) on board the Aqua satellite: DOI:10.5067/MODIS/MYD02HKM.061 and DOI:10.5067/MODIS/MYD021KM.061. Each data granule contains 5 minutes of swath data observed at a resolution of 500 m.

  The terms "Version 61" and "Collection 6.1" are used interchangeably in reference to this release of MODIS data.
- source text: provides daily snow cover
- source text: Each data granule contains 5 minutes of swath data
- source text: 5 minutes of swath data
- source text: This global Level-2 (L2) data set
- classed triple: "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" (Dataset) HAS_TEMPORAL_RESOLUTION "daily" (TemporalResolution)
- classed triple: "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" (Dataset) HAS_GRANULE_DURATION "5 minutes" (Value)
- classed triple: "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" (Dataset) HAS_SPATIAL_REPRESENTATION "swath" (SpatialRepresentation)
- classed triple: "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" (Dataset) HAS_SPATIAL_COVERAGE "global" (SpatialExtent)

### Ground truth schema

- entity class TemporalResolution: the amount of time between one value of the data and the next, e.g. daily; weekly (8 day)
- entity class Time: a point or period on the calendar, which happens once, e.g. March 11, 2016 19:08:03; May 4, 2002; the first week of February 2003; 2015-10-22 to 2015-12-31
- entity class Value: an amount, as a number with its unit or in words, e.g. 36 spectral bands; 5 minutes
- predicate HAS_TEMPORAL_RESOLUTION: gives values this often, e.g. daily; weekly (8 day)
- predicate HAS_GRANULE_DURATION: each of its files covers this much time
- predicate HAS_TIME_SPAN: covers this period
- predicate HAS_SPATIAL_COVERAGE: covers this area

### Translation table

- entity class Frequency -> TemporalResolution: A rate of occurrence, such as daily or weekly, or a radio frequency band, such as S-, X-, or Ku-band.
- predicate HAS_TIME_RESOLUTION -> HAS_TEMPORAL_RESOLUTION: The subject (a dataset or measurement) has the object as its temporal resolution, averaging interval, cycle or file time-period.
- predicate COVERS -> HAS_TIME_SPAN: The subject (a dataset, campaign, flight series or technique) spans the object, a time period, geographic area or measured variable.
- predicate HAS_DURATION -> HAS_GRANULE_DURATION: The subject (a dataset, granule, orbit portion or observation series) lasts for or spans the object, a time length or period.

### Annotation guidelines

- Writing a classed triple, rule 9: A qualifier that is a temporal resolution, an area the data cover, a processing level, a spatial resolution, a country, a time of day, or a target body is a ground truth triple of its own, and is taken out of the instance.
- Writing a classed triple, rule 11: General facts: include them, unless they're about another dataset.
- Writing a classed triple, rule 11: Leave out a fact about another dataset, even a closely related one, such as the same data at another time step or resolution. That dataset has its own record, and its facts go there. Suppose: a record's title says "8 Day", and its notes say "daily, weekly (8 day), and monthly products are available". Then: the dataset HAS_TEMPORAL_RESOLUTION "weekly (8 day)", its own (rule 13: it says more than the title's "8 Day"); the daily and monthly products are other datasets, so they get none.

### Options

#### Option 1: Keep the ground truth schema and the translation table as they are

Any word that says how often values come, or the period they average over ("daily", "weekly", "weekly (8 day)"), is a TemporalResolution, in the record's own words; the rows stay: Frequency into TemporalResolution, COVERS into HAS_TIME_SPAN, HAS_DURATION into HAS_GRANULE_DURATION.

#### Option 2: Tell apart how often from the period a value averages over

TemporalResolution only for the time between one value and the next; a new entity class, and a new predicate, for the period one value averages over ("8 day" in an 8-day average).

#### Option 3: No temporal resolution for a swath dataset

Where the dataset's files hold what the instrument saw along its path, "daily" is not a temporal resolution, so it gets no ground truth triple of HAS_TEMPORAL_RESOLUTION; it would be a different relationship ("is made daily"), or none.

#### Option 4: Let the current schema keep the meanings apart

The [step](../docs/terminology.md#8-the-pipeline) that learns the current schema splits a predicate whose object instances are of several entity classes into one predicate per entity class (COVERS with a period; COVERS with an area), and keeps how often data are given apart from a radio frequency band; each part gets its own row: into HAS_TIME_SPAN, into HAS_SPATIAL_COVERAGE, into TemporalResolution.

### My current reading

Option 1 for now, because the definition of TemporalResolution covers the records I have read so far as they are written and needs no knowledge from outside the record; and option 4 later. If your answer to (a) is that "daily" means something else for a swath dataset, I would move to option 3 for those datasets; if your answer to (b) is that the averaging period is a separate thing, to option 2. Your answer to (e) decides whether the ground truth schema also needs a predicate for how long a whole series lasted.

### My notes

Five of the [tuning records](../docs/terminology.md#7-evaluating-extraction-step-070) I have annotated so far state a time of these sorts, at pool positions 1, 2, 3, 4 and 6 (the one at pool position 6 is not in the ground truth yet: I am annotating it); every classed triple the answer may change is listed under Affects. The example is the record at pool position 2; the "8 Day" one is at pool position 4, the period one at pool position 1.

Option 4 comes when I improve the step that learns the schema (040): splitting a broad predicate by its object's entity class is on my list of improvements.

### Consequences

#### Option 1: Keep the ground truth schema and the translation table as they are

- No change to the ground truth triples listed under Affects.
- "daily" for a dataset of 5-minute swath files and "daily" for a dataset with one value per place per day look the same, though they may mean different things (your answer to (a)).
- An area or a variable the model writes with COVERS, a whole series' duration written with HAS_DURATION, and a radio band filed under Frequency are compared with the wrong ground truth predicate or entity class, and counted wrong.

#### Option 2: Tell apart how often from the period a value averages over

- The ground truth triple "weekly (8 day)" (pool position 4) may become two, or move to the new predicate, depending on your answer to (b).
- One more entity class and predicate in the ground truth schema, for the annotation guidelines and the model to tell apart.

#### Option 3: No temporal resolution for a swath dataset

- The ground truth triple "daily" (pool position 2) is deleted or moved to another predicate, and the annotation guidelines say when.
- The record states "daily snow cover", so that [fact](../docs/terminology.md#2-triples) must still be written down somehow ("Every fact the record states", rule 2 of "What counts as a fact").

#### Option 4: Let the current schema keep the meanings apart

- Each meaning is compared with the right ground truth predicate or entity class.
- The learning step changes, and its next run costs model calls; the new rows are checked by hand.
- It doesn't settle (e): whether a whole series' duration needs a predicate of its own in the ground truth schema.

### Affects

- record at pool position 1: cfd6ec3f-1e63-4a77-bc3f-007d45f7e2fc
- record at pool position 2: 6cfafd07-40f1-46da-9d92-36c2bb319f0b
- record at pool position 3: 2705e0d1-95e7-4588-813b-ca91a6da94ff
- record at pool position 4: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- record at pool position 6: 4c64f3ed-39b4-4f95-95a0-022898ba47a4
- classed triple of the record at pool position 1: "COMET ESCORT 4" (MissionPhase) HAS_TIME_SPAN "2015-10-22 to 2015-12-31" (Time)
- classed triple of the record at pool position 1: "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (Dataset) HAS_TIME_SPAN "2015-11-01T19:58:35.000 to 2015-11-02T04:59:27.000" (Time)
- classed triple of the record at pool position 2: "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" (Dataset) HAS_GRANULE_DURATION "5 minutes" (Value)
- classed triple of the record at pool position 2: "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" (Dataset) HAS_TEMPORAL_RESOLUTION "daily" (TemporalResolution)
- classed triple of the record at pool position 3: "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005" (Dataset) HAS_TEMPORAL_RESOLUTION "weekly" (TemporalResolution)
- classed triple of the record at pool position 4: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) HAS_TEMPORAL_RESOLUTION "weekly (8 day)" (TemporalResolution)
- classed triple of the record at pool position 6: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) HAS_TEMPORAL_RESOLUTION "daily" (TemporalResolution)
- translation table row: entity class Frequency
- translation table row: predicate HAS_TIME_RESOLUTION
- translation table row: predicate HAS_DURATION
- translation table row: predicate COVERS
- ground truth schema entry: entity class TemporalResolution
- ground truth schema entry: predicate HAS_TEMPORAL_RESOLUTION
- ground truth schema entry: predicate HAS_GRANULE_DURATION
- ground truth schema entry: predicate HAS_TIME_SPAN
- rule: Writing a classed triple, rule 9
- rule: Writing a classed triple, rule 11
- pipeline method: 040_induce_schema/run.py: how the current schema is learned (option 4: splitting a broad predicate or entity class)

## Q6: Processing levels: what is L2G, what are "1/2/3" in a Planetary Data System title, and which list should the ground truth follow?

- status: open
- priority: medium
- question kind: schema entry
- topic: the ground truth schema's ProcessingLevel and HAS_PROCESSING_LEVEL, and a reference list of processing levels

### The question

The ground truth schema's ProcessingLevel is "how far data have been processed from what the Instrument recorded, e.g. Level 2". The records write it in many ways ("Level-2 (L2)", "Level-3", "Level 3", "L2", "L2G", and perhaps "1/2/3"), and so far the ground truth keeps each record's own words. I would like to know:

- (a) The example below has "L2G" in its title and "gridded Level 2 product" in its notes. Is L2G "Level 2, gridded": a processing level (Level 2) plus a layout on a grid, which the ground truth writes as two [facts](../docs/terminology.md#2-triples)? Or is L2G a processing level of its own?
- (b) The record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0", from the Planetary Data System, has "RSI 1/2/3" in its title. Are 1, 2 and 3 processing levels of the data from the instrument RSI? My reading, not checked against a source: they may be levels of a planetary data scale, but the record doesn't say so, and the annotation guidelines say never to write down what an unexplained code stands for, so the ground truth has no processing level for this record. If they are levels, are they CODMAC levels (my reading, not checked against a source: the Planetary Data System has numbered its data's processing levels by the CODMAC scale)? And what does "1149" stand for, in the same title's "COMET ESCORT 4 1149 V1.0"? If the Planetary Data System's data set names give it a fixed place with a fixed meaning, should the ground truth write it as a fact of its own? One answer about how these data set names are built would settle both codes.
- (c) Which list of processing levels should the ground truth follow? The one I know of is NASA Earthdata's *Data Processing Levels* (Level 0, Level 1A, 1B, 1C, Level 2, 2A, 2B, Level 3, 3A, Level 4; https://www.earthdata.nasa.gov/learn/earth-observation-data-basics/data-processing-levels). Does it hold for the whole catalog, or do records of other parts of NASA, e.g. the Planetary Data System, use other levels? If there are two lists, how do they line up?

### Context

Of the records I have read so far, the example below is the one whose "L2G" I am least sure of. The record "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" has two levels: "Level 3" for its own dataset, and "L2" for the pixels it was made from ("the L2 pixels are binned").

The knowledge graph will be built from the records' metadata fields and the extracted triples. Two records that write one level in two wordings ("Level 3" and "L3") give two different object instances; a reference list would give one.

### Example record

- record id: 4c64f3ed-39b4-4f95-95a0-022898ba47a4
- pool position: 6
- title: MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid
- notes: The Moderate Resolution Imaging Spectroradiometer (MODIS) Near Real Time (NRT) Combined Terra and Aqua Multi-Angle Implementation of Atmospheric Correction (MAIAC) Land Aerosol Optical Depth gridded Level 2 product (MCD19A2N) produced daily at 1 kilometer (km) pixel resolutions. The MCD19A2N product provides the atmospheric properties and view geometry used to calculate the MAIAC Land Surface Bidirectional Reflectance Factor (BRF) or surface reflectance, MCD19A1N product.
- in the ground truth: not yet: I am annotating this record now, so its classed triples below are my drafts, approved so far, not yet in annotations/ground_truth/
- source text: L2G
- source text: gridded Level 2 product
- classed triple: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) HAS_PROCESSING_LEVEL "Level 2" (ProcessingLevel)
- classed triple: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) HAS_SPATIAL_REPRESENTATION "gridded" (SpatialRepresentation)

### Ground truth schema

- entity class ProcessingLevel: how far data have been processed from what the Instrument recorded, e.g. Level 2
- predicate HAS_PROCESSING_LEVEL: is processed to this ProcessingLevel

### Translation table

- entity class ProcessingLevel -> ProcessingLevel: A designation of how far a data product has been processed from raw instrument output, such as Level 0 through Level 3 or Near Real Time.
- predicate HAS_PROCESSING_LEVEL -> HAS_PROCESSING_LEVEL: The subject (a data product) has the object as its data processing level, such as L0, Level-2 or Level-3.

### Annotation guidelines

- What counts as a fact, rule 1: Only what the record states. Never add what you know from elsewhere, and never write down what an unexplained code or acronym stands for.
- Writing a classed triple, rule 1: Subject instance and object instance: the record's own words, as written.
- Writing a classed triple, rule 9: A qualifier that is a temporal resolution, an area the data cover, a processing level, a spatial resolution, a country, a time of day, or a target body is a ground truth triple of its own, and is taken out of the instance.
- Writing a classed triple, rule 10: A name with its abbreviation in parentheses is one instance, as written. Suppose: a record says "This Level-2 (L2) dataset". Then: the instance is "Level-2 (L2)", with no ALSO_KNOWN_AS triple.
- Writing a classed triple, rule 13: One thing, one wording, within a record.

### Options

#### Option 1: Keep each record's own words

The object instance of HAS_PROCESSING_LEVEL is the record's words, as written ("Level-2 (L2)", "Level-3", "Level 3", "L2"), and a code the record doesn't explain ("1/2/3") gets no ground truth triple.

#### Option 2: A closed list of processing levels in the ground truth

The ground truth schema lists the processing levels (from the list your answer to (c) names), and the object instance is the value of the list that the record's words mean ("Level-2 (L2)" becomes "Level 2").

#### Option 3: Own words in the ground truth, the list's value added later

The ground truth keeps each record's own words; the value of the list each wording means is added to the knowledge graph in a later stage, next to the record's words.

### My current reading

Option 1 for now, because it writes only the record's own words. I would move to option 2 or 3 if your answer to (c) gives one list that covers the catalog. For the example, I have written "Level 2" and "gridded" as two facts, my reading of "gridded Level 2 product"; your answer to (a) tells me whether that is right.

### My notes

Five of the tuning records I have annotated so far write a processing level, or a code that may be one, at pool positions 1, 2, 3, 4 and 6 (the one at pool position 6 is not in the ground truth yet: I am annotating it); every classed triple the answer may change is listed under Affects. The example is the record at pool position 6.

### Consequences

#### Option 1: Keep each record's own words

- No change to the ground truth triples listed under Affects, nor to the annotation guidelines.
- One processing level is written in several ways across records ("Level-2 (L2)", "L2", "Level 2"), so a search of the knowledge graph for Level 2 data has to know every wording.

#### Option 2: A closed list of processing levels in the ground truth

- A new exception to rule 1 of "Writing a classed triple" (quoted below), written in the annotation guidelines and in the copy of the rules the [model](../docs/terminology.md#8-the-pipeline) follows, which both change.
- The ground truth triples listed under Affects are checked again, and some object instances change.
- Every record names a processing level the same way, so a search needs one value; a code such as "1/2/3" still gets a value only if the record explains it.
- A record's level that isn't on the list has no value to use, unless the list covers the whole catalog.

#### Option 3: Own words in the ground truth, the list's value added later

- The annotation guidelines and the ground truth don't change, and the knowledge graph can still be searched by the list's values.
- Work to match each wording to a value of the list, outside the ground truth, which this project hasn't planned yet.

### Affects

- record at pool position 1: cfd6ec3f-1e63-4a77-bc3f-007d45f7e2fc
- record at pool position 2: 6cfafd07-40f1-46da-9d92-36c2bb319f0b
- record at pool position 3: 2705e0d1-95e7-4588-813b-ca91a6da94ff
- record at pool position 4: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- record at pool position 6: 4c64f3ed-39b4-4f95-95a0-022898ba47a4
- classed triple of the record at pool position 2: "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" (Dataset) HAS_PROCESSING_LEVEL "Level-2 (L2)" (ProcessingLevel)
- classed triple of the record at pool position 3: "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005" (Dataset) HAS_PROCESSING_LEVEL "Level-3" (ProcessingLevel)
- classed triple of the record at pool position 4: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) HAS_PROCESSING_LEVEL "Level 3" (ProcessingLevel)
- classed triple of the record at pool position 4: "pixels" (Dataset) HAS_PROCESSING_LEVEL "L2" (ProcessingLevel)
- classed triple of the record at pool position 6: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) HAS_PROCESSING_LEVEL "Level 2" (ProcessingLevel)
- classed triple of the record at pool position 6: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) HAS_SPATIAL_REPRESENTATION "gridded" (SpatialRepresentation)
- translation table row: entity class ProcessingLevel
- translation table row: predicate HAS_PROCESSING_LEVEL
- ground truth schema entry: entity class ProcessingLevel
- ground truth schema entry: predicate HAS_PROCESSING_LEVEL
- rule: What counts as a fact, rule 1
- rule: Writing a classed triple, rule 1
- rule: Writing a classed triple, rule 9
- rule: Writing a classed triple, rule 10
- rule: Writing a classed triple, rule 13
- pipeline method: common/common_prompts/extraction_rules.txt: the model's copy of the annotation guidelines' rules, which a list of processing levels to follow would change

## Q7: A processing step: what is its input, and what is its method?

- status: open
- priority: medium
- question kind: rule
- topic: rule 14 of the annotation guidelines (a processing step), and the ground truth schema's COMPUTED_FROM and PRODUCED_USING_ALGORITHM

### The question

Rule 14 of the annotation guidelines (quoted below) writes each processing step a record describes as output = method(input): the output COMPUTED_FROM ("was made by processing this input") each input, and the output PRODUCED_USING_ALGORITHM ("was made or detected by applying this Algorithm") the method. In one record I am not sure which part is the input, and I would like a general way to tell. I would like to know:

- (a) The example below says its two sea surface temperature (SST) products are "derived from the long wave IR 11 and 12 micron wavelength channels" and generated "using the mid-infrared 3.95 and 4.05 micron wavelength channels". I wrote each channel as an input: COMPUTED_FROM, with a Channel ("a range of wavelengths an Instrument measures separately") as its object instance. Is it right to say that an SST product is computed from a wavelength channel? My reading, not checked against a source: it is computed from what the instrument measured in those channels, and the channel says where in the spectrum that was, not what was processed.
- (b) If a channel is not an input: how would you say it? Is "uses the 11 micron channel" or "is measured in the 11 micron channel" a relationship of its own, apart from "is computed from"?
- (c) Is there a general way to tell an input from a method, that would settle the case above and others like it? For example, the record "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" says its index "is derived from radiance data", which I wrote as an input, and the record "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" names its product a "Multi-Angle Implementation of Atmospheric Correction (MAIAC) Land Aerosol Optical Depth gridded Level 2 product", which I write as made using MAIAC, a method.
- (d) I split "the long wave IR 11 and 12 micron wavelength channels" into "long wave IR 11 micron wavelength channel" and "long wave IR 12 micron wavelength channel" (rule 12, quoted below). Would someone in your field write each channel that way?

### Context

The example below has products computed from channels, and facts that say which channels are unique to MODIS.

Settled, so not asked here: the record "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0" says "The nominal fast neutron count rates were detrended using the GRaND epithermal neutron map to produced this residual map", and I wrote the epithermal neutron map as an input, COMPUTED_FROM, beside the count rates. A review of that record on 2026-10-22 checked NASA's archive documents for it: the epithermal neutron map is used to correct the fast neutron counts, so it is an input. No method is written for that record, since "detrended" names an operation but no algorithm with a name of its own.

### Example record

- record id: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- pool position: 4
- title: MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0
- notes: Day and night spatially gridded (L3) global NASA skin sea surface temperature (SST) products from the Moderate-resolution Imaging Spectroradiometer (MODIS) onboard the Aqua satellite. Average daily, weekly (8 day), monthly and annual skin SST products at are available at both 4.63 and 9.26 km spatial resolution. Aqua was launched by NASA on May 4, 2002, into a sun synchronous, polar orbit with a daylight ascending node at 13:30, formation flying in the A-train with other Earth Observation Satellites (EOS), to study the global dynamics of the Earth atmosphere, land and oceans. MODIS captures data in 36 spectral bands at a variety of spatial resolutions. Two SST products can be present in these files. The first is a skin SST produced for both day and night (NSST) observations, derived from the long wave IR 11 and 12 micron wavelength channels, using a modified nonlinear SST algorithm intended to provide continuity of SST derived from heritage and current NASA sensors. At night, a second SST product is generated using the mid-infrared 3.95 and 4.05 micron wavelength channels which are unique to MODIS; the SST derived from these measurements is identified as SST4. The SST4 product has lower uncertainty, but due to sun glint can only be used at night. To generate the L3 products the L2 pixels are binned into an integerized sinusoidal area grid (ISEAG) and mapped into an equidistant cylindrical (also known as Platte Carre projection. Additional projection detailed can be found at https://oceancolor.gsfc.nasa.gov/docs/format/ The NASA MODIS L3 SST data products are generated by the NASA Ocean Biology Processing Group (OBPG) and Peter Minnett and his team at the Rosenstiel School of Marine and Atmospheric Science (RSMAS) are responsible for sea surface temperature algorithm development, error statistics and quality flagging. JPL acquires MODIS ocean L3 SST data from the OBPG and is the official Physical Oceanography Data Archive (PO.DAAC) for SST. The R2019.0 supersedes the previous v2014.1 datasets which can be found at https://doi.org/10.5067/MODAM-8D4N4
- source text: The first is a skin SST produced for both day and night (NSST) observations, derived from the long wave IR 11 and 12 micron wavelength channels
- source text: At night, a second SST product is generated using the mid-infrared 3.95 and 4.05 micron wavelength channels which are unique to MODIS; the SST derived from these measurements is identified as SST4
- source text: To generate the L3 products the L2 pixels are binned
- source text: The first is a skin SST produced for both day and night (NSST) observations, derived from the long wave IR 11 and 12 micron wavelength channels, using a modified nonlinear SST algorithm
- source text: the mid-infrared 3.95 and 4.05 micron wavelength channels which are unique to MODIS
- classed triple: "skin SST (NSST)" (Variable) COMPUTED_FROM "long wave IR 11 micron wavelength channel" (Channel)
- classed triple: "skin SST (NSST)" (Variable) COMPUTED_FROM "long wave IR 12 micron wavelength channel" (Channel)
- classed triple: "SST4" (Variable) COMPUTED_FROM "mid-infrared 3.95 micron wavelength channel" (Channel)
- classed triple: "SST4" (Variable) COMPUTED_FROM "mid-infrared 4.05 micron wavelength channel" (Channel)
- classed triple: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) COMPUTED_FROM "pixels" (Dataset)
- classed triple: "skin SST (NSST)" (Variable) PRODUCED_USING_ALGORITHM "modified nonlinear SST algorithm" (Algorithm)
- classed triple: "mid-infrared 3.95 micron wavelength channel" (Channel) UNIQUE_TO_INSTRUMENT "Moderate-resolution Imaging Spectroradiometer (MODIS)" (Instrument)
- classed triple: "mid-infrared 4.05 micron wavelength channel" (Channel) UNIQUE_TO_INSTRUMENT "Moderate-resolution Imaging Spectroradiometer (MODIS)" (Instrument)

### Ground truth schema

- predicate COMPUTED_FROM: was made by processing this input
- predicate PRODUCED_USING_ALGORITHM: was made or detected by applying this Algorithm
- entity class Channel: a range of wavelengths an Instrument measures separately, e.g. the 11 micron channel
- entity class Variable: one named kind of value computed from an Instrument's measurements by one particular Algorithm, e.g. SST4; NDSI
- entity class Algorithm: a method applied to data to compute a result, e.g. a series of screens; a modified nonlinear SST algorithm
- predicate UNIQUE_TO_INSTRUMENT: is found only on this Instrument

### Translation table

- entity class Wavelength -> Channel: A wavelength band or spectral range, such as an infrared filter band, in which observations are made.
- predicate DERIVED_FROM -> COMPUTED_FROM: The subject (a data product, quantity, value or format) is computed from or based on the object, a source measurement, signal, input data or prior standard.

### Annotation guidelines

- What counts as a fact, rule 1: Only what the record states. Never add what you know from elsewhere, and never write down what an unexplained code or acronym stands for.
- Writing a classed triple, rule 12: A list joined by "and": one ground truth triple per item, when each item alone is a complete object. Put one item alone after the predicate. Suppose: a record says the SST is "derived from the long wave IR 11 and 12 micron wavelength channels". Then: "long wave IR 11 micron wavelength channel" alone is a complete object, so two ground truth triples, each object with the words the items share copied onto it, in the singular, since each is now one item: "long wave IR 11 micron wavelength channel" and "long wave IR 12 micron wavelength channel".
- Writing a classed triple, rule 14: A processing step: output_i = method_i(input_i). For each processing step i the record describes, find its output_i, method_i, and input_i, and write at most two ground truth triples: output_i COMPUTED_FROM input_i, and output_i PRODUCED_USING_ALGORITHM method_i. Write each only if the record names both of its parts.

### Options

#### Option 1: Keep the inputs as they are

The channels stay inputs: "skin SST (NSST)" COMPUTED_FROM "long wave IR 11 micron wavelength channel".

#### Option 2: A predicate of its own for the channels a product uses

Coin a predicate in the ground truth schema for "uses the measurements of this Channel", and write the channels with it instead of COMPUTED_FROM.

### My current reading

Option 1 until you answer, because the record's own words are "derived from", which read to me as an input used in the computation. If your answer to (a) is that a channel is not an input, I would choose option 2, since a ground truth triple should say what is true. Your answer to (c) would become part of rule 14.

### My notes

Four of the tuning records I have annotated so far describe a processing step, at pool positions 2, 4, 5 and 6 (the one at pool position 6 is not in the ground truth yet: I am annotating it); all their classed triples with COMPUTED_FROM or PRODUCED_USING_ALGORITHM are listed under Affects. The example is the record at pool position 4; the settled one is at pool position 5.

### Consequences

#### Option 1: Keep the inputs as they are

- No change to the ground truth triples listed under Affects.
- If your answer to (a) is that a channel is not an input, the ground truth says the product was made by processing a range of wavelengths, which is not literally true.

#### Option 2: A predicate of its own for the channels a product uses

- The four ground truth triples with COMPUTED_FROM and a Channel, below, change to the new predicate.
- COMPUTED_FROM keeps one meaning, an input that was processed; one more predicate for the annotation guidelines and the [model](../docs/terminology.md#8-the-pipeline) to use.
- The schema the model extracts with has DERIVED_FROM (translated to COMPUTED_FROM, in the translation table below); an extracted triple of DERIVED_FROM with a channel would then no longer agree with the ground truth unless the translation depends on the object instance's entity class.

### Affects

- record at pool position 2: 6cfafd07-40f1-46da-9d92-36c2bb319f0b
- record at pool position 4: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- record at pool position 5: 99dff022-24ac-48cb-bc83-09fec8b90ad7
- classed triple of the record at pool position 2: "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" (Dataset) COMPUTED_FROM "Normalized Difference Snow Index (NDSI)" (Variable)
- classed triple of the record at pool position 2: "Normalized Difference Snow Index (NDSI)" (Variable) COMPUTED_FROM "radiance data" (Dataset)
- classed triple of the record at pool position 2: "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" (Dataset) PRODUCED_USING_ALGORITHM "a series of screens" (Algorithm)
- classed triple of the record at pool position 4: "skin SST (NSST)" (Variable) COMPUTED_FROM "long wave IR 11 micron wavelength channel" (Channel)
- classed triple of the record at pool position 4: "skin SST (NSST)" (Variable) COMPUTED_FROM "long wave IR 12 micron wavelength channel" (Channel)
- classed triple of the record at pool position 4: "SST4" (Variable) COMPUTED_FROM "mid-infrared 3.95 micron wavelength channel" (Channel)
- classed triple of the record at pool position 4: "SST4" (Variable) COMPUTED_FROM "mid-infrared 4.05 micron wavelength channel" (Channel)
- classed triple of the record at pool position 4: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) COMPUTED_FROM "pixels" (Dataset)
- classed triple of the record at pool position 4: "skin SST (NSST)" (Variable) PRODUCED_USING_ALGORITHM "modified nonlinear SST algorithm" (Algorithm)
- classed triple of the record at pool position 5: "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0" (Dataset) COMPUTED_FROM "nominal fast neutron count rates" (Variable)
- classed triple of the record at pool position 5: "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0" (Dataset) COMPUTED_FROM "GRaND epithermal neutron map" (Dataset)
- record at pool position 6: 4c64f3ed-39b4-4f95-95a0-022898ba47a4
- classed triple of the record at pool position 6: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) PRODUCED_USING_ALGORITHM "Multi-Angle Implementation of Atmospheric Correction (MAIAC)" (Algorithm)
- translation table row: predicate DERIVED_FROM
- ground truth schema entry: predicate COMPUTED_FROM
- ground truth schema entry: predicate PRODUCED_USING_ALGORITHM
- rule: Writing a classed triple, rule 12
- rule: Writing a classed triple, rule 14
- pipeline method: common/common_prompts/extraction_rules.txt: the model's copy of rule 14, which a general way to tell an input from a method would change

## Q8: Organizations, teams, roles, programs, facilities and places: which entity class?

- status: open
- priority: medium
- question kind: schema entry
- topic: the ground truth schema's Organization, Team, Role and BASED_IN, and the translation table's rows for Program, Facility, Location and LOCATED_IN

### The question

The records name groups of people, offices, programs, sites and places in several ways, and I am not sure I sort them the way someone in the field would. The ground truth schema has three entity classes for groups: Organization (a named institution or one of its named parts), Team (a group of people without a name of its own) and Role (a position someone holds). It has no entity class for a place, and one predicate about where something is: BASED_IN, "belongs to this Country". I would like to know:

- (a) The example below says that JPL "is the official Physical Oceanography Data Archive (PO.DAAC) for SST". I wrote this down as a role JPL holds. Would you say PO.DAAC is a role (a job JPL does), or an organization of its own (with JPL as where it is, or who runs it)?
- (b) The example also names the "NASA Ocean Biology Processing Group (OBPG)" and "Peter Minnett and his team". I wrote the first as an Organization, since it has a name of its own, and the second as a Team, since it doesn't. Is that line (a name of its own, or not) the right one?
- (c) The record "NASA Standards and and Technical Assistance Resource Tool" names the "NASA Technical Standards Program", which provides access to standards and sponsors a web tool. I wrote it as an Organization. Is a NASA "program" like this one an organization (an office with staff), or something else, such as a funded effort? And is "NASA" part of the program's name, so that I keep "NASA Technical Standards Program" whole, as I do now, or does it say whose program it is, which would be a fact of its own (the program a part of NASA)?
- (d) In this catalog, is a facility (e.g. a space center, an observatory, a ground station) best thought of as an Organization, as a place, or as both, depending on the sentence?
- (e) Do the records of this catalog name places (a research station, a field of the sky, a site) often enough, and in [facts](../docs/terminology.md#2-triples) that matter enough, that the ground truth schema should have an entity class for them?
- (f) Is "is located in" the same relationship as "belongs to this Country" when the place is a country (e.g. a center located in the U.S.)? When the place is not a country (a state, a city, a region), what should it be?

### Context

The example below names an archive, a named group and a team. Which entity class each gets decides which predicates fit it (for example, SPONSORED_BY_PARTY joins only an Organization, a Person or a Team), and how a search of the knowledge graph finds it. The only facts about where something is that I have written so far are two of the record "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005", both about which country an organization belongs to: "National Aeronautics and Space Administration (NASA)" (Organization) BASED_IN "U.S." (Country), and "Comisión Nacional de Actividades Espaciales (CONAE)" (Organization) BASED_IN "Argentina" (Country).

The [model](../docs/terminology.md#8-the-pipeline) that reads the records has its own entity classes, and the translation table (quoted below) says which entity class of the ground truth schema each one means. It has an entity class Program (which means nothing in the ground truth schema: (none)), Facility (which means Organization), Location ((none)), and a predicate LOCATED_IN (which means BASED_IN).

### Example record

- record id: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- pool position: 4
- title: MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0
- notes: Day and night spatially gridded (L3) global NASA skin sea surface temperature (SST) products from the Moderate-resolution Imaging Spectroradiometer (MODIS) onboard the Aqua satellite. Average daily, weekly (8 day), monthly and annual skin SST products at are available at both 4.63 and 9.26 km spatial resolution. Aqua was launched by NASA on May 4, 2002, into a sun synchronous, polar orbit with a daylight ascending node at 13:30, formation flying in the A-train with other Earth Observation Satellites (EOS), to study the global dynamics of the Earth atmosphere, land and oceans. MODIS captures data in 36 spectral bands at a variety of spatial resolutions. Two SST products can be present in these files. The first is a skin SST produced for both day and night (NSST) observations, derived from the long wave IR 11 and 12 micron wavelength channels, using a modified nonlinear SST algorithm intended to provide continuity of SST derived from heritage and current NASA sensors. At night, a second SST product is generated using the mid-infrared 3.95 and 4.05 micron wavelength channels which are unique to MODIS; the SST derived from these measurements is identified as SST4. The SST4 product has lower uncertainty, but due to sun glint can only be used at night. To generate the L3 products the L2 pixels are binned into an integerized sinusoidal area grid (ISEAG) and mapped into an equidistant cylindrical (also known as Platte Carre projection. Additional projection detailed can be found at https://oceancolor.gsfc.nasa.gov/docs/format/ The NASA MODIS L3 SST data products are generated by the NASA Ocean Biology Processing Group (OBPG) and Peter Minnett and his team at the Rosenstiel School of Marine and Atmospheric Science (RSMAS) are responsible for sea surface temperature algorithm development, error statistics and quality flagging. JPL acquires MODIS ocean L3 SST data from the OBPG and is the official Physical Oceanography Data Archive (PO.DAAC) for SST. The R2019.0 supersedes the previous v2014.1 datasets which can be found at https://doi.org/10.5067/MODAM-8D4N4
- source text: JPL acquires MODIS ocean L3 SST data from the OBPG and is the official Physical Oceanography Data Archive (PO.DAAC) for SST
- source text: JPL acquires MODIS ocean L3 SST data from the OBPG
- source text: The NASA MODIS L3 SST data products are generated by the NASA Ocean Biology Processing Group (OBPG)
- source text: Aqua was launched by NASA
- source text: Peter Minnett and his team at the Rosenstiel School of Marine and Atmospheric Science (RSMAS) are responsible for sea surface temperature algorithm development, error statistics and quality flagging
- classed triple: "JPL" (Organization) SERVES_AS "official Physical Oceanography Data Archive (PO.DAAC) for SST" (Role)
- classed triple: "JPL" (Organization) OBTAINS_DATA_FROM "NASA Ocean Biology Processing Group (OBPG)" (Organization)
- classed triple: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) DEVELOPED_BY_PARTY "NASA Ocean Biology Processing Group (OBPG)" (Organization)
- classed triple: "Aqua" (Spacecraft) LAUNCHED_BY_PARTY "NASA" (Organization)
- classed triple: "Peter Minnett and his team" (Team) AFFILIATED_WITH "Rosenstiel School of Marine and Atmospheric Science (RSMAS)" (Organization)
- classed triple: "Peter Minnett and his team" (Team) RESPONSIBLE_FOR "sea surface temperature algorithm development" (Task)
- classed triple: "Peter Minnett and his team" (Team) RESPONSIBLE_FOR "error statistics" (Task)
- classed triple: "Peter Minnett and his team" (Team) RESPONSIBLE_FOR "quality flagging" (Task)

### Ground truth schema

- entity class Organization: a named institution or one of its named parts, not a Mission, e.g. NASA; OBPG
- entity class Team: a group of people without a name of its own, e.g. Peter Minnett and his team
- entity class Role: a position a Person, Team, or Organization holds, what they are, e.g. the official archive for SST
- entity class Country: a nation, e.g. U.S.; Argentina
- predicate SERVES_AS: holds this Role
- predicate AFFILIATED_WITH: works at or belongs to this Organization
- predicate SPONSORED_BY_PARTY: is sponsored by this Person, Team, or Organization
- predicate BASED_IN: belongs to this Country

### Translation table

- entity class Organization -> Organization: An institution, agency, center, or collaborative body, such as NASA, HEASARC, or CIESIN, responsible for producing, managing, or distributing data or research.
- entity class Team -> Team: A group of people, such as investigators, specialists or institutional groups, working together on a mission, project or study.
- entity class Program -> (none): A named organized scientific initiative, often a telescope legacy or key program, encompassing coordinated observations and data products.
- entity class Facility -> Organization: A physical site, base, space center or installation, or the organization operating it, where research, launches or observations are carried out.
- entity class Location -> (none): A named geographic, terrestrial, or celestial place or region, such as a research station, sky field, or facility, where observations or activities occur.
- predicate LOCATED_IN -> BASED_IN: The subject (a facility, site, observation or item) is situated at or in the object, a geographic place, region or physical setting.

### Annotation guidelines

- What counts as a fact, rule 1: Only what the record states. Never add what you know from elsewhere, and never write down what an unexplained code or acronym stands for.
- What counts as a fact, rule 4: Not "is a" facts. "MODIS is a spectroradiometer" says what type of thing MODIS is: that belongs in its entity class, not in a classed triple of its own. A sentence that names one specific role or thing is not an "is a" fact, though: Suppose: a record says "JPL is the official Physical Oceanography Data Archive (PO.DAAC) for SST". Then: a ground truth triple, because it names a role only JPL holds, not a type.
- Writing a classed triple, rule 4: Entity classes and predicates: the ground truth schema's, when one fits, so records name the same things the same way.
- Writing a classed triple, rule 9: A qualifier that is a temporal resolution, an area the data cover, a processing level, a spatial resolution, a country, a time of day, or a target body is a ground truth triple of its own, and is taken out of the instance.

### Options

#### Option 1: Keep the line as it is

A named group or office is an Organization; a group without a name of its own is a Team; what an Organization is for (the official archive for SST) is a Role it holds, written with SERVES_AS. The translation table stays as it is: Program and Location mean nothing in the ground truth schema, Facility means Organization, LOCATED_IN means BASED_IN.

#### Option 2: A named archive or program is an Organization too

"Physical Oceanography Data Archive (PO.DAAC)" becomes an Organization of its own, and the NASA Technical Standards Program stays an Organization; the role JPL holds is then written as a fact joining JPL and PO.DAAC, with a predicate the ground truth schema doesn't have yet.

#### Option 3: A program is its own entity class

Coin an entity class for a named program (for example, Program), for the NASA Technical Standards Program and others like it, and keep Organization for institutions and their parts.

#### Option 4: Places get an entity class of the ground truth schema

When a record names a place in a fact of its own, the ground truth schema gets an entity class for it (and a predicate, "is located in this place"), and the model's Location and LOCATED_IN mean them; Facility means the place or Organization, as your answer to (d) says.

### My current reading

Option 1, for now: it follows the records' own words (JPL "is" the archive), every case above fits it, and so far no fact I wrote depends on a facility or a place other than a country. I would change it if you tell me that PO.DAAC, or a NASA program, is usually thought of as an organization in its own right (option 2 or 3), and choose option 4 once a record states a fact about a place.

### My notes

The groups appear as the subject instance or object instance of the classed triples listed under Affects; the example is the record at pool position 4, and the program of (c) is the record at pool position 0's. The facts about a country are the record at pool position 3's: rule 9 makes a country that qualifies an organization ("U.S. National Aeronautics and Space Administration (NASA)") a ground truth triple of its own.

The model extracts classed triples with the current schema. Before they are compared with the ground truth, each entity class and predicate of that schema is replaced by the one of the ground truth schema its [row](../docs/terminology.md#8-the-pipeline) of the translation table names; a row that names (none): a classed triple that uses it always counts as extracted only. I would choose option 4 with the answers to (d) to (f) telling me what to coin, once a tuning record states a fact about a place.

### Consequences

#### Option 1: Keep the line as it is

- Nothing changes in the ground truth triples listed under Affects, the annotation guidelines, or the translation table.
- PO.DAAC appears only inside the Role "official Physical Oceanography Data Archive (PO.DAAC) for SST", so a search of the knowledge graph for PO.DAAC as an organization doesn't find it.
- A facility the model extracts is compared as an Organization: right for a center named as the body that runs something, wrong for a site named as the place where something happens; a classed triple with LOCATED_IN is right when its object instance is a country, and counted wrong when it is any other place.

#### Option 2: A named archive or program is an Organization too

- A new predicate is coined (for example, for "is run by" or "hosts"), and the record at pool position 4 gets one more classed triple.
- Only what the record states may be written (rule 1 of *What counts as a fact*): the record says JPL "is" the archive, not that JPL runs or hosts it, so the new predicate has to say exactly that.
- A search of the knowledge graph for PO.DAAC finds it as an organization, like any other data center.

#### Option 3: A program is its own entity class

- The translation table's row for the current schema's Program changes from (none) to the new entity class, so the model's Program instances can be compared with the ground truth.
- SPONSORED_BY_PARTY and DEVELOPED_BY_PARTY join only an Organization, a Person or a Team: they would need the new entity class added, or the record at pool position 0 changes.

#### Option 4: Places get an entity class of the ground truth schema

- Places are compared rightly.
- The ground truth schema gains an entity class and a predicate, and the rows of the translation table that point to them are checked again.
- It waits for a tuning record that names a place: the annotation guidelines coin an entity class only when a record needs it.

### Affects

- record at pool position 0: 3122be4c-b9d0-4cc9-b6d3-9b96c6e743da
- record at pool position 3: 2705e0d1-95e7-4588-813b-ca91a6da94ff
- record at pool position 4: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- classed triple of the record at pool position 0: "NASA Technical Standards Program" (Organization) PROVIDES_ACCESS_TO_DOCUMENT "NASA developed standards" (Document)
- classed triple of the record at pool position 0: "NASA Technical Standards Program" (Organization) PROVIDES_ACCESS_TO_DOCUMENT "NASA developed handbooks" (Document)
- classed triple of the record at pool position 0: "NASA Standards and and Technical Assistance Resource Tool" (WebTool) SPONSORED_BY_PARTY "NASA Technical Standards Program" (Organization)
- classed triple of the record at pool position 3: "Aquarius/Satélite de Aplicaciones Científicas (SAC-D)" (Mission) DEVELOPED_BY_PARTY "National Aeronautics and Space Administration (NASA)" (Organization)
- classed triple of the record at pool position 3: "National Aeronautics and Space Administration (NASA)" (Organization) BASED_IN "U.S." (Country)
- classed triple of the record at pool position 3: "Aquarius/Satélite de Aplicaciones Científicas (SAC-D)" (Mission) DEVELOPED_BY_PARTY "Comisión Nacional de Actividades Espaciales (CONAE)" (Organization)
- classed triple of the record at pool position 3: "Comisión Nacional de Actividades Espaciales (CONAE)" (Organization) BASED_IN "Argentina" (Country)
- classed triple of the record at pool position 4: "Aqua" (Spacecraft) LAUNCHED_BY_PARTY "NASA" (Organization)
- classed triple of the record at pool position 4: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) DEVELOPED_BY_PARTY "NASA Ocean Biology Processing Group (OBPG)" (Organization)
- classed triple of the record at pool position 4: "Peter Minnett and his team" (Team) AFFILIATED_WITH "Rosenstiel School of Marine and Atmospheric Science (RSMAS)" (Organization)
- classed triple of the record at pool position 4: "JPL" (Organization) OBTAINS_DATA_FROM "NASA Ocean Biology Processing Group (OBPG)" (Organization)
- classed triple of the record at pool position 4: "JPL" (Organization) SERVES_AS "official Physical Oceanography Data Archive (PO.DAAC) for SST" (Role)
- classed triple of the record at pool position 4: "Peter Minnett and his team" (Team) RESPONSIBLE_FOR "sea surface temperature algorithm development" (Task)
- classed triple of the record at pool position 4: "Peter Minnett and his team" (Team) RESPONSIBLE_FOR "error statistics" (Task)
- classed triple of the record at pool position 4: "Peter Minnett and his team" (Team) RESPONSIBLE_FOR "quality flagging" (Task)
- translation table row: entity class Program
- translation table row: entity class Location
- translation table row: entity class Organization
- translation table row: entity class Facility
- translation table row: entity class Team
- translation table row: predicate LOCATED_IN
- ground truth schema entry: entity class Organization
- ground truth schema entry: entity class Team
- ground truth schema entry: entity class Role
- ground truth schema entry: predicate SERVES_AS
- ground truth schema entry: predicate BASED_IN
- rule: What counts as a fact, rule 4
- rule: Writing a classed triple, rule 4
- rule: Writing a classed triple, rule 9

## Q9: Whose purpose is it, and is "used to study" a purpose?

- status: open
- priority: medium
- question kind: schema entry
- topic: the ground truth schema's Purpose and HAS_PURPOSE

### The question

The ground truth schema has an entity class Purpose ("an aim something is meant to achieve") and a predicate HAS_PURPOSE. I am not sure how far it should reach. To decide, I need to know:

- (a) The example below says Aqua was launched "to study the global dynamics of the Earth atmosphere, land and oceans". I wrote this as the purpose of Aqua, the spacecraft, because that is what the sentence is about. Would you say it is the spacecraft's purpose, or its mission's (a satellite mission usually has the science goals)? The record names no mission for Aqua, so I can't write the mission without adding what the record doesn't state.
- (b) In that phrase, "Earth" is the body studied. The annotation guidelines take a target body out of an instance as a [fact](../docs/terminology.md#2-triples) of its own (rule 9). I kept the phrase whole, since "study the global dynamics of the atmosphere, land and oceans" without "Earth" no longer says whose atmosphere. Is keeping it whole right, or should "Earth" also be its own fact (Aqua is about the Earth)?
- (c) The [model](../docs/terminology.md#8-the-pipeline) that reads the records has predicates for what something is "used to study" and for its "objective", and the translation table translates both to HAS_PURPOSE. Is "used to study ocean salinity" a purpose, in your field, or a different relationship (what a mission or instrument studies), better kept apart?

### Context

The purposes I have written so far are a web tool's (the record "NASA Standards and and Technical Assistance Resource Tool"), those of a series of screens applied to data (the record "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061"), and those of Aqua and of an algorithm (the example below, whose purpose of Aqua the questions above are about).

### Example record

- record id: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- pool position: 4
- title: MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0
- notes: Day and night spatially gridded (L3) global NASA skin sea surface temperature (SST) products from the Moderate-resolution Imaging Spectroradiometer (MODIS) onboard the Aqua satellite. Average daily, weekly (8 day), monthly and annual skin SST products at are available at both 4.63 and 9.26 km spatial resolution. Aqua was launched by NASA on May 4, 2002, into a sun synchronous, polar orbit with a daylight ascending node at 13:30, formation flying in the A-train with other Earth Observation Satellites (EOS), to study the global dynamics of the Earth atmosphere, land and oceans. MODIS captures data in 36 spectral bands at a variety of spatial resolutions. Two SST products can be present in these files. The first is a skin SST produced for both day and night (NSST) observations, derived from the long wave IR 11 and 12 micron wavelength channels, using a modified nonlinear SST algorithm intended to provide continuity of SST derived from heritage and current NASA sensors. At night, a second SST product is generated using the mid-infrared 3.95 and 4.05 micron wavelength channels which are unique to MODIS; the SST derived from these measurements is identified as SST4. The SST4 product has lower uncertainty, but due to sun glint can only be used at night. To generate the L3 products the L2 pixels are binned into an integerized sinusoidal area grid (ISEAG) and mapped into an equidistant cylindrical (also known as Platte Carre projection. Additional projection detailed can be found at https://oceancolor.gsfc.nasa.gov/docs/format/ The NASA MODIS L3 SST data products are generated by the NASA Ocean Biology Processing Group (OBPG) and Peter Minnett and his team at the Rosenstiel School of Marine and Atmospheric Science (RSMAS) are responsible for sea surface temperature algorithm development, error statistics and quality flagging. JPL acquires MODIS ocean L3 SST data from the OBPG and is the official Physical Oceanography Data Archive (PO.DAAC) for SST. The R2019.0 supersedes the previous v2014.1 datasets which can be found at https://doi.org/10.5067/MODAM-8D4N4
- source text: Aqua was launched by NASA on May 4, 2002, into a sun synchronous, polar orbit with a daylight ascending node at 13:30, formation flying in the A-train with other Earth Observation Satellites (EOS), to study the global dynamics of the Earth atmosphere, land and oceans
- source text: using a modified nonlinear SST algorithm intended to provide continuity of SST derived from heritage and current NASA sensors
- classed triple: "Aqua" (Spacecraft) HAS_PURPOSE "study the global dynamics of the Earth atmosphere, land and oceans" (Purpose)
- classed triple: "modified nonlinear SST algorithm" (Algorithm) HAS_PURPOSE "provide continuity of SST derived from heritage and current NASA sensors" (Purpose)

### Ground truth schema

- entity class Purpose: an aim something is meant to achieve
- predicate HAS_PURPOSE: is meant to achieve
- entity class CelestialBody: a natural object in space
- predicate HAS_TARGET: is about this CelestialBody
- entity class Mission: a named spaceflight effort
- entity class Spacecraft: a craft that operates in space

### Translation table

- predicate USED_TO_STUDY -> HAS_PURPOSE: The subject (a mission, instrument, program or dataset) is designed or used to investigate, characterize or trace the object, a scientific phenomenon or process.
- predicate HAS_OBJECTIVE -> HAS_PURPOSE: The subject (a mission, campaign, project or set of researchers) aims to achieve, study or address the object, a scientific goal, question or problem.

### Annotation guidelines

- Writing a classed triple, rule 2: The subject instance is what the sentence is about, which isn't always the title.
- Writing a classed triple, rule 9: A qualifier that is a temporal resolution, an area the data cover, a processing level, a spatial resolution, a country, a time of day, or a target body is a ground truth triple of its own, and is taken out of the instance.
- Writing a classed triple, rule 9: A qualifier stays in the instance, as written, if it is any other kind ("sea surface salinity" stays whole), or if taking it out would give a triple that isn't true.
- Writing a classed triple, rule 12: A list joined by "and": one ground truth triple per item, when each item alone is a complete object. Put one item alone after the predicate.
- Writing a classed triple, rule 12: Suppose: a record says Aqua was launched "to study the global dynamics of the Earth atmosphere, land and oceans". Then: "atmosphere" alone isn't a purpose (it needs "study the global dynamics of the Earth"), so one ground truth triple keeps the whole phrase.

### Options

#### Option 1: Keep it as it is

The purpose stays with what the sentence is about (Aqua), the phrase stays whole with "Earth" in it, and "used to study" and "objective" both count as a purpose.

#### Option 2: Take the body studied out as its own fact

"Earth" becomes a fact of its own, "Aqua" (Spacecraft) HAS_TARGET "Earth" (CelestialBody), and the purpose keeps its words.

#### Option 3: What something studies apart from its purpose

A predicate of its own for what a mission, spacecraft or instrument studies (a PhysicalQuantity or a Phenomenon), and keep HAS_PURPOSE for aims written as an action ("make it simpler to access…").

### My current reading

Option 1, for now: it writes what each sentence says, about what it is about. I would choose option 3 if you tell me that what a mission studies and what it is meant to achieve are kept apart in your field.

### My notes

All the HAS_PURPOSE classed triples of the records annotated so far are listed under Affects: a web tool's purpose (pool position 0), the purposes of a series of screens applied to data (pool position 2), and those of Aqua and of an algorithm (pool position 4, the example). The predicates of (c) are the current schema's USED_TO_STUDY and HAS_OBJECTIVE.

### Consequences

#### Option 1: Keep it as it is

- Nothing changes in the ground truth triples listed under Affects, the annotation guidelines, or the translation table.
- A search of the knowledge graph for what studies the Earth's atmosphere has to search inside the words of purposes.

#### Option 2: Take the body studied out as its own fact

- HAS_TARGET so far joins a Dataset to a CelestialBody; it would join a Spacecraft too, a new pattern.
- The purpose's object instance keeps "Earth" (taking it out would leave "the atmosphere, land and oceans" of no body), so the body is written twice, once inside the purpose.

#### Option 3: What something studies apart from its purpose

- The translation table's [row](../docs/terminology.md#8-the-pipeline) for USED_TO_STUDY (current schema) changes to the new predicate.
- An annotator, and the model, must tell an aim from a thing studied in each sentence; "to study the global dynamics of the Earth atmosphere" is both.

### Affects

- record at pool position 0: 3122be4c-b9d0-4cc9-b6d3-9b96c6e743da
- record at pool position 2: 6cfafd07-40f1-46da-9d92-36c2bb319f0b
- record at pool position 4: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- classed triple of the record at pool position 0: "NASA Standards and and Technical Assistance Resource Tool" (WebTool) HAS_PURPOSE "make it simpler for technical people to access NASA technical information quickly and conveniently" (Purpose)
- classed triple of the record at pool position 2: "a series of screens" (Algorithm) HAS_PURPOSE "alleviate errors" (Purpose)
- classed triple of the record at pool position 2: "a series of screens" (Algorithm) HAS_PURPOSE "flag uncertain snow cover detections" (Purpose)
- classed triple of the record at pool position 4: "Aqua" (Spacecraft) HAS_PURPOSE "study the global dynamics of the Earth atmosphere, land and oceans" (Purpose)
- classed triple of the record at pool position 4: "modified nonlinear SST algorithm" (Algorithm) HAS_PURPOSE "provide continuity of SST derived from heritage and current NASA sensors" (Purpose)
- translation table row: predicate USED_TO_STUDY
- translation table row: predicate HAS_OBJECTIVE
- ground truth schema entry: entity class Purpose
- ground truth schema entry: predicate HAS_PURPOSE
- rule: Writing a classed triple, rule 2
- rule: Writing a classed triple, rule 9
- rule: Writing a classed triple, rule 12

## Q10: Radio science, techniques and fields of science: is RSI an Instrument, is Radio Science a Discipline, and which list of disciplines?

- status: open
- priority: medium
- question kind: schema entry
- topic: the ground truth schema's Discipline and Instrument for radio science data, the translation table's rows for Method and Topic, and a reference list of disciplines

### The question

The example below is a Rosetta radio science dataset. Its title has "RSI", and its notes call it "a Rosetta Radio Science data set". I wrote "RSI" as the Instrument that collected the data, and "Radio Science" as its Discipline ("a field of science"). I am not sure about either, nor about where a technique of measuring belongs. To decide, I need to know:

- (a) Is "RSI" in a title like this one the name of an instrument? My reading (not checked in a source): radio science measures the spacecraft's own radio signal, as received on Earth, so the "instrument" is the spacecraft's radio system together with the ground stations. Is it right to call RSI an Instrument?
- (b) Is "Radio Science" a field of science (like oceanography), or a technique (a way of measuring, used in several fields)?
- (c) If it is a technique: should the ground truth have an entity class for techniques, apart from Algorithm ("a method applied to data to compute a result") and Discipline? The [model](../docs/terminology.md#8-the-pipeline) that reads the records has an entity class Method that also covers ways of collecting or sending data (an operating mode; my example: radio occultation, an observing technique), and the translation table (quoted below) says it means Algorithm. Is such a technique an Algorithm, or something else?
- (d) The model's Topic covers any subject a dataset addresses ("agriculture", "AGN", "ecosystem interaction"), and the translation table says it means Discipline. Is a subject like these a Discipline, a field of science?
- (e) Which list of disciplines should the ground truth follow, so that a record's words can be checked against it? The one I know of is the divisions of NASA's Science Mission Directorate, among them Earth Science, Planetary Science, Astrophysics and Heliophysics (https://science.nasa.gov/about-us/). Is that the right list for this catalog, or is another one used?

### Context

The record doesn't say what "RSI" stands for, and the annotation guidelines don't let me write what an unexplained acronym stands for, so the object instance is "RSI", as written. "Radio Science" is the only Discipline I have written so far. The translation table names one entity class of the ground truth schema for each of the model's, whatever the record: so every Method the model finds is judged as an Algorithm, and every Topic as a Discipline. The two Algorithms I have written so far are methods applied to data.

### Example record

- record id: cfd6ec3f-1e63-4a77-bc3f-007d45f7e2fc
- pool position: 1
- title: ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0
- notes: This is a Rosetta Radio Science data set, collected during the COMET ESCORT 4 phase 2015-10-22 to 2015-12-31. It is a Global Gravity measurement at the comet 67P and covers the time 2015-11-01T19:58:35.000 to 2015-11-02T04:59:27.000.
- source text: RSI
- source text: This is a Rosetta Radio Science data set
- classed triple: "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (Dataset) ACQUIRED_BY_INSTRUMENT "RSI" (Instrument)
- classed triple: "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (Dataset) HAS_DISCIPLINE "Radio Science" (Discipline)

### Ground truth schema

- entity class Instrument: a device that takes measurements
- entity class Discipline: a field of science
- entity class Algorithm: a method applied to data to compute a result, e.g. a series of screens; a modified nonlinear SST algorithm
- predicate ACQUIRED_BY_INSTRUMENT: was collected by this Instrument
- predicate HAS_DISCIPLINE: belongs to this Discipline
- predicate PRODUCED_USING_ALGORITHM: was made or detected by applying this Algorithm

### Translation table

- entity class Method -> Algorithm: A technique, procedure, operating mode, or analytical approach used to acquire, transmit, or analyze data.
- entity class Topic -> Discipline: A subject area or theme, such as agriculture, AGN, or ecosystem interaction, that a dataset or study addresses.
- predicate HAS_DISCIPLINE -> HAS_DISCIPLINE: The subject (a set of observations or data) belongs to the object, a scientific discipline or category.

### Annotation guidelines

- What counts as a fact, rule 1: Only what the record states. Never add what you know from elsewhere, and never write down what an unexplained code or acronym stands for.
- Writing a classed triple, rule 1: Subject instance and object instance: the record's own words, as written.
- Writing a classed triple, rule 4: Entity classes and predicates: the ground truth schema's, when one fits, so records name the same things the same way.

### Options

#### Option 1: Keep it as it is

"RSI" is an Instrument, and "Radio Science" a Discipline; the model's Method means Algorithm, and its Topic means Discipline; a Discipline is written in the record's own words.

#### Option 2: A technique is its own entity class

An entity class of its own for a technique of measuring (for example, Technique), and a predicate joining a Dataset to it; "Radio Science" moves there, "RSI" stays an Instrument, and the model's Method means the new entity class where what it names is a technique.

#### Option 3: No instrument for radio science

"RSI" is written as something other than an Instrument (for example, the name of the investigation), if radio science has no instrument of its own.

#### Option 4: Disciplines from a reference list

A Discipline's object instance is the value of the list your answer to (e) names that the record's words mean; a subject that is not on the list (a Topic such as "agriculture") is not a Discipline, and the model's Topic means nothing in the ground truth schema, or an entity class of its own for subjects.

### My current reading

Option 1, for now, since the record gives no more than the code and the words "Radio Science", and every Algorithm and Discipline I have written so far fits its definition. Your answers to (a) and (b) decide options 2 and 3; your answers to (d) and (e) decide option 4.

### My notes

The example is the record at pool position 1. The model extracts classed triples with the current schema. Before they are compared with the ground truth, each entity class and predicate of that schema is replaced by the one of the ground truth schema its [row](../docs/terminology.md#8-the-pipeline) of the translation table names. The ground truth's two Algorithms so far are the records' at pool positions 2 and 4 (not listed under Affects: no option changes them).

### Consequences

#### Option 1: Keep it as it is

- Nothing changes in the ground truth triples listed under Affects, or in the translation table.
- Every radio science dataset of the catalog gets an "instrument" named by the title's code, and the field "Radio Science"; a search of the knowledge graph for the fields of science finds Radio Science among them.
- A technique or a topic the model extracts is compared as an Algorithm or a Discipline; if your answers say they aren't, those classed triples are counted wrong, or counted right when they shouldn't be.

#### Option 2: A technique is its own entity class

- The ground truth triple with HAS_DISCIPLINE "Radio Science" changes, and the ground truth schema gets a new entity class and predicate.
- The row for the current schema's Method changes, and is checked again.

#### Option 3: No instrument for radio science

- The ground truth triple ACQUIRED_BY_INSTRUMENT "RSI" changes, and a new entity class or predicate may be needed for an investigation.

#### Option 4: Disciplines from a reference list

- A new exception to rule 1 of "Writing a classed triple" (quoted above), in the annotation guidelines and in the copy of the rules the model follows, which both change.
- The ground truth triple HAS_DISCIPLINE "Radio Science" is checked against the list.
- Every record names a field of science the same way, so a search of the knowledge graph by field needs one value.

### Affects

- record at pool position 1: cfd6ec3f-1e63-4a77-bc3f-007d45f7e2fc
- classed triple of the record at pool position 1: "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (Dataset) HAS_DISCIPLINE "Radio Science" (Discipline)
- classed triple of the record at pool position 1: "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (Dataset) ACQUIRED_BY_INSTRUMENT "RSI" (Instrument)
- translation table row: entity class Method
- translation table row: entity class Topic
- translation table row: predicate HAS_DISCIPLINE
- ground truth schema entry: entity class Discipline
- ground truth schema entry: predicate HAS_DISCIPLINE
- rule: What counts as a fact, rule 1
- rule: Writing a classed triple, rule 1
- rule: Writing a classed triple, rule 4
- pipeline method: common/common_prompts/extraction_rules.txt: the model's copy of the annotation guidelines' rules, which a list of disciplines to follow would change

## Q11: What counts as an area the data cover: "Global" at a comet, and "Land"?

- status: open
- priority: medium
- question kind: schema entry
- topic: the ground truth schema's SpatialExtent and HAS_SPATIAL_COVERAGE, and rule 9 of the annotation guidelines

### The question

The ground truth schema's SpatialExtent is "the area the data cover, of the CelestialBody they are about: all of it (global) or part of it (e.g. the Arctic; the south pole of Mars)", and a dataset HAS_SPATIAL_COVERAGE such an area. Rule 9 of the annotation guidelines (quoted below) takes an area the data cover out of an instance, as a fact of its own. In two records I am not sure whether a word is such an area. To decide, I need to know:

- (a) The record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" says "It is a Global Gravity measurement at the comet 67P". I wrote "Global" as the area the data cover (all of the comet 67P). At a comet, what would "Global" mean: the whole comet, or something else? Or is "Global Gravity" the name of one sort of radio science measurement, as a whole, so that "Global" is no area at all? (Other records of the catalog have the same sentence with "Phobos Gravity", "Occultation" or "Solar Conjunction" in its place: see below.)
- (b) The example below is a dataset of "Land Aerosol Optical Depth". I took "Land" out as the area the data cover ("MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) HAS_SPATIAL_COVERAGE "Land" (SpatialExtent)), and kept "Aerosol Optical Depth" as the quantity measured. Is "Land" (the land surfaces of the Earth, as against the oceans) an area in the sense of SpatialExtent, "part of" the Earth? Or is "Land Aerosol Optical Depth" one quantity, the aerosol optical depth over land, which should stay whole? Or does "Land" say what sort of surface the method that computes the product (MAIAC) is made for, so that it stays in the quantity's words as a qualifier of another sort (rule 9's "any other kind")?
- (c) In general: should SpatialExtent hold only a region of a body (the Arctic, a pole, the whole body), or also a sort of surface (land, ocean, sea ice) that the data are limited to?

### Context

The areas I have written so far are "Global" (the record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0"), "global" (the records "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" and "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0"), and my draft "Land" (the example below, which question (b) is about).

Settled, so not asked here: the example's title ends in "Global 1km SIN Grid". Checked on 2026-10-25, "SIN Grid" is the MODIS sinusoidal grid, and "Global 1km SIN Grid" is the standard end of the titles of the MODIS products made on it, so "Global" there names the grid's worldwide tiling, not the area this dataset covers (NASA LAADS, the MCD19A2 product page, https://ladsweb.modaps.eosdis.nasa.gov/missions-and-measurements/products/MCD19A2; NASA MODAPS, MCD19A2N, https://modaps.modaps.eosdis.nasa.gov/services/about/products/c61-nrt/MCD19A2N.html). So I wrote no area "Global" for it. A "global" written as a word of its own ("This global Level-2 (L2) data set") I am sure of; the three words above I am not.

The sentence of the record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" recurs across the catalog. I counted it in the catalog's 36,406 records: "It is a Global Gravity measurement" in 2,835 records (2,442 of them "at the comet 67P"), "It is a Occultation measurement" in 439, "It is a Solar Conjunction measurement" in 240, and "It is a Phobos Gravity measurement" in 9. Since "Phobos Gravity" sits beside "Global Gravity", my reading is that the word before "Gravity" may say which gravity measurement it is, not an area; but I don't know.

### Example record

- record id: 4c64f3ed-39b4-4f95-95a0-022898ba47a4
- pool position: 6
- title: MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid
- notes: The Moderate Resolution Imaging Spectroradiometer (MODIS) Near Real Time (NRT) Combined Terra and Aqua Multi-Angle Implementation of Atmospheric Correction (MAIAC) Land Aerosol Optical Depth gridded Level 2 product (MCD19A2N) produced daily at 1 kilometer (km) pixel resolutions. The MCD19A2N product provides the atmospheric properties and view geometry used to calculate the MAIAC Land Surface Bidirectional Reflectance Factor (BRF) or surface reflectance, MCD19A1N product.
- in the ground truth: not yet: I am annotating this record now, so its classed triples below are my drafts, approved so far, not yet in annotations/ground_truth/
- source text: Land Aerosol Optical Depth
- source text: Global 1km SIN Grid
- classed triple: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) HAS_SPATIAL_COVERAGE "Land" (SpatialExtent)
- classed triple: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) HAS_MEASUREMENTS_OF "Aerosol Optical Depth" (PhysicalQuantity)

### Ground truth schema

- entity class SpatialExtent: the area the data cover, of the CelestialBody they are about: all of it (global) or part of it (e.g. the Arctic; the south pole of Mars)
- entity class PhysicalQuantity: a property that can be measured, in general, whatever method measures it, e.g. sea surface temperature; snow cover
- entity class CelestialBody: a natural object in space
- predicate HAS_SPATIAL_COVERAGE: covers this area
- predicate HAS_MEASUREMENTS_OF: holds measurements of
- predicate HAS_TARGET: is about this CelestialBody

### Translation table

- entity class SpatialCoverage -> SpatialExtent: The geographic or sky extent covered by a dataset or observation, such as global, a swath width, or a number of square degrees or areas.
- predicate HAS_SPATIAL_COVERAGE -> HAS_SPATIAL_COVERAGE: The subject (a dataset or survey) covers the object, a geographic region, latitude range, area extent or coverage descriptor.

### Annotation guidelines

- Writing a classed triple, rule 9: A qualifier that is a temporal resolution, an area the data cover, a processing level, a spatial resolution, a country, a time of day, or a target body is a ground truth triple of its own, and is taken out of the instance.
- Writing a classed triple, rule 9: A qualifier stays in the instance, as written, if it is any other kind ("sea surface salinity" stays whole), or if taking it out would give a triple that isn't true.

### Options

#### Option 1: Keep them as I wrote them

"Global" (at the comet 67P) and "Land" (in the example) are areas the data cover, each a fact of its own.

#### Option 2: Only regions of a body are areas

SpatialExtent holds only a region of a body, or the whole of it. "Land Aerosol Optical Depth" stays whole, as the quantity measured, since rule 9 keeps a qualifier that is no area in the instance; "Global Gravity" stays whole too, if the answer to (a) is that it names a measurement.

#### Option 3: Name sorts of surface in the definition

The definition of SpatialExtent says that a sort of surface the data are limited to (land, ocean, sea ice) is an area too, and rule 9 takes it out like any area.

### My current reading

Undecided. For "Land", I lean towards option 3: it says which part of the Earth the data cover, which is what a search would ask. For "Global Gravity", I lean towards keeping it whole, since "Phobos Gravity" in other records reads like the same sort of title; your answer to (a) decides it.

### My notes

Every ground truth triple with HAS_SPATIAL_COVERAGE so far is listed under Affects: "Global" (pool position 1), "global" (pool positions 2 and 4), and my draft "Land" (pool position 6, the example, which I am annotating now). The count of the recurring sentence is over 020's records.jsonl (36,406 records). Until the answers, the ground truth stays as written (option 1).

How the translation table is used: the [model](../docs/terminology.md#8-the-pipeline) extracts classed triples with a schema it learned from other records of the catalog (the current schema; a schema an earlier run used is a past schema). Before its classed triples are compared with the ground truth, each entity class and predicate of that schema is replaced by the one of the ground truth schema its [row](../docs/terminology.md#8-the-pipeline) of the translation table names. A row that names (none) says nothing in the ground truth schema means the same: a classed triple that uses it can never be part of a [pair](../docs/terminology.md#7-evaluating-extraction-step-070) with a ground truth triple, so it always counts as extracted only. The current schema's SpatialCoverage and HAS_SPATIAL_COVERAGE translate into SpatialExtent and HAS_SPATIAL_COVERAGE, so the answer also decides what an extracted triple with them is compared with.

### Consequences

#### Option 1: Keep them as I wrote them

- Nothing changes in the ground truth triples listed under Affects.
- If "Global Gravity" is the name of one sort of measurement, the area "Global" is a [fact](../docs/terminology.md#2-triples) the record doesn't state, and the 2,835 records with this sentence would each get it.
- SpatialExtent holds both regions and sorts of surface (land); its definition would say so.

#### Option 2: Only regions of a body are areas

- The draft triples of the record at pool position 6 become one: HAS_MEASUREMENTS_OF "Land Aerosol Optical Depth", with no HAS_SPATIAL_COVERAGE.
- The record at pool position 1 loses HAS_SPATIAL_COVERAGE "Global", and its HAS_MEASUREMENTS_OF "Gravity" becomes "Global Gravity", if the answer to (a) says so.
- A search for land-only data has to look inside the quantities' words.

#### Option 3: Name sorts of surface in the definition

- The ground truth schema's definition of SpatialExtent changes, and the rows of the translation table into it are checked again.
- The model's copy of the rules (rule 9) says the same, so extraction takes "Land" out too.

### Affects

- record at pool position 1: cfd6ec3f-1e63-4a77-bc3f-007d45f7e2fc
- record at pool position 2: 6cfafd07-40f1-46da-9d92-36c2bb319f0b
- record at pool position 4: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- record at pool position 6: 4c64f3ed-39b4-4f95-95a0-022898ba47a4
- classed triple of the record at pool position 1: "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (Dataset) HAS_SPATIAL_COVERAGE "Global" (SpatialExtent)
- classed triple of the record at pool position 2: "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" (Dataset) HAS_SPATIAL_COVERAGE "global" (SpatialExtent)
- classed triple of the record at pool position 4: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) HAS_SPATIAL_COVERAGE "global" (SpatialExtent)
- classed triple of the record at pool position 1: "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (Dataset) HAS_MEASUREMENTS_OF "Gravity" (PhysicalQuantity)
- classed triple of the record at pool position 6: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) HAS_SPATIAL_COVERAGE "Land" (SpatialExtent)
- classed triple of the record at pool position 6: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) HAS_MEASUREMENTS_OF "Aerosol Optical Depth" (PhysicalQuantity)
- translation table row: entity class SpatialCoverage
- translation table row: predicate HAS_SPATIAL_COVERAGE
- ground truth schema entry: entity class SpatialExtent
- ground truth schema entry: predicate HAS_SPATIAL_COVERAGE
- rule: Writing a classed triple, rule 9
- pipeline method: common/common_prompts/extraction_rules.txt: the model's copy of the annotation guidelines' rules (rule 9's list of qualifiers taken out)

## Q12: What counts as a dataset: inputs named in a record, and archives, catalogs and data products?

- status: open
- priority: medium
- question kind: schema entry
- topic: the ground truth schema's Dataset, for the data a record's dataset is made from and for collections of datasets; four rows of the translation table into Dataset

### The question

The ground truth schema's Dataset is "a set of observations, measurements, or samples". Besides each record's own dataset, I have written three other things as Datasets, all inputs from which the record's dataset was made; and the [model](../docs/terminology.md#8-the-pipeline) that reads the records has three entity classes for collections of data that the translation table (quoted below) says also mean Dataset. I am not sure each is a dataset in the sense someone in the field would use. To decide, I need to know:

- (a) The example below says the index it uses "is derived from radiance data acquired by" MODIS, followed by two DOIs, MYD02HKM and MYD021KM. I wrote one Dataset, "radiance data", with both DOIs. Are these one dataset or two (my reading: two products, at two resolutions)? If two, how should two inputs with the same words be told apart, when the record names them only by their DOIs?
- (b) The record "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" says "the L2 pixels are binned" into a grid. I wrote "pixels" as a Dataset, at processing level "L2". Is a set of Level 2 pixels a dataset, or just the Level 2 data, unnamed?
- (c) The record "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0" says the counts "were detrended using the GRaND epithermal neutron map". I wrote that map as a Dataset, collected by GRaND. No record of the catalog has "epithermal" in its title (I searched the catalog's titles), so I can't tell whether the map is a dataset of its own; the catalog has other GRaND maps of Vesta (for example, "DAWN GRAND MAP VESTA NEUTRON ABSORPTION V1.0"). The annotation guidelines leave out facts about another dataset (rule 11). Is it right to keep the map as an input, with what collected it?
- (d) For someone using this catalog, is an astronomical source catalog (a list of objects, each with its measured properties) a dataset in the same sense as a set of measurements of the Earth's surface?
- (e) Is a database or archive that holds many datasets the same sort of thing as one of the datasets it holds, or should the two be kept apart (e.g. so that a search for datasets doesn't return archives)?
- (f) Is a "data product" (e.g. "Level-3 products", "the SST4 product") always a dataset, or sometimes one variable inside a dataset?

### Context

The example below is the one whose input, "radiance data", has the most facts of its own (four, two of them DOIs). COMPUTED_FROM joins what was made to what it was made from. None of the records I have read so far names an astronomical source catalog or a database. The translation table says that the model's Dataset, DataProduct, Catalog and Database all mean the ground truth schema's Dataset.

### Example record

- record id: 6cfafd07-40f1-46da-9d92-36c2bb319f0b
- pool position: 2
- title: MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061
- notes: This global Level-2 (L2) data set provides daily snow cover detected using Normalized Difference Snow Index (NDSI) and a series of screens designed to alleviate errors and flag uncertain snow cover detections. The NDSI is derived from radiance data acquired by the Moderate Resolution Imaging Spectroradiometer (MODIS) on board the Aqua satellite: DOI:10.5067/MODIS/MYD02HKM.061 and DOI:10.5067/MODIS/MYD021KM.061. Each data granule contains 5 minutes of swath data observed at a resolution of 500 m.

  The terms "Version 61" and "Collection 6.1" are used interchangeably in reference to this release of MODIS data.
- source text: The NDSI is derived from radiance data
- source text: radiance data acquired by the Moderate Resolution Imaging Spectroradiometer (MODIS)
- source text: radiance data acquired by the Moderate Resolution Imaging Spectroradiometer (MODIS) on board the Aqua satellite: DOI:10.5067/MODIS/MYD02HKM.061
- source text: radiance data acquired by the Moderate Resolution Imaging Spectroradiometer (MODIS) on board the Aqua satellite: DOI:10.5067/MODIS/MYD02HKM.061 and DOI:10.5067/MODIS/MYD021KM.061
- classed triple: "Normalized Difference Snow Index (NDSI)" (Variable) COMPUTED_FROM "radiance data" (Dataset)
- classed triple: "radiance data" (Dataset) ACQUIRED_BY_INSTRUMENT "Moderate Resolution Imaging Spectroradiometer (MODIS)" (Instrument)
- classed triple: "radiance data" (Dataset) HAS_DOI "DOI:10.5067/MODIS/MYD02HKM.061" (Identifier)
- classed triple: "radiance data" (Dataset) HAS_DOI "DOI:10.5067/MODIS/MYD021KM.061" (Identifier)

### Ground truth schema

- entity class Dataset: a set of observations, measurements, or samples
- entity class Variable: one named kind of value computed from an Instrument's measurements by one particular Algorithm, e.g. SST4; NDSI
- entity class Identifier: a code that names one thing permanently, e.g. a DOI
- predicate COMPUTED_FROM: was made by processing this input
- predicate HAS_DOI: has the Digital Object Identifier

### Translation table

- entity class Dataset -> Dataset: A named collection of data compiled from observations, measurements, experiments, or statistics and distributed as a unit, such as an index, data collection, or instrument time series.
- entity class DataProduct -> Dataset: A specific processed output of data, such as calibrated images, retrieval products, files, or data segments, generated from instrument or model data.
- entity class Catalog -> Dataset: A published, organized list of astronomical sources or objects with their properties, typically derived from a survey or mission.
- entity class Database -> Dataset: An organized collection or repository of data records, sources or proposals that can be stored, queried and accessed.

### Annotation guidelines

- Writing a classed triple, rule 1: Subject instance and object instance: the record's own words, as written.
- Writing a classed triple, rule 11: General facts: include them, unless they're about another dataset.
- Writing a classed triple, rule 11: Leave out a fact about another dataset, even a closely related one, such as the same data at another time step or resolution. That dataset has its own record, and its facts go there.
- Writing a classed triple, rule 14: A processing step: output_i = method_i(input_i).

### Options

#### Option 1: Keep them all as Datasets

Every input named in a record is a Dataset, in the record's words, with the facts the record states about it; the model's Catalog, Database and DataProduct all mean Dataset.

#### Option 2: One input per DOI

When a record names inputs by their DOIs, each DOI is its own Dataset, and the record's words ("radiance data") are written once per DOI.

#### Option 3: Inputs only, no facts about them

Keep each input as a Dataset, but write nothing else about an input that is another dataset of the catalog (its instrument, its processing level), as rule 11 says.

#### Option 4: An entity class for collections of datasets

When a record names an archive, a database or a source catalog that holds many datasets, the ground truth schema gets an entity class for it, and the model's Database (and Catalog, if your answer to (d) is no) means it.

### My current reading

Option 1, for now: it writes what each record states, and every collection of data in the records I have read so far is one set of measurements. Your answers decide whether (a) needs option 2, whether (c) needs option 3, and whether (d) and (e) need option 4.

### My notes

The example is the record at pool position 2. The other two inputs are "the L2 pixels" of the record at pool position 4 and "the GRaND epithermal neutron map" of the record at pool position 5; every ground truth triple about each of the three inputs is listed under Affects. None of the tuning records so far names an astronomical source catalog or a database. The search of (c) was over the titles of 020's records.jsonl.

How the translation table is used: the [model](../docs/terminology.md#8-the-pipeline) extracts classed triples with a schema it learned from other records of the catalog (the current schema; a schema an earlier run used is a past schema). Before its classed triples are compared with the ground truth, each entity class and predicate of that schema is replaced by the one of the ground truth schema its [row](../docs/terminology.md#8-the-pipeline) of the translation table names. A row that names (none) says nothing in the ground truth schema means the same: a classed triple that uses it can never be part of a [pair](../docs/terminology.md#7-evaluating-extraction-step-070) with a ground truth triple, so it always counts as extracted only.

### Consequences

#### Option 1: Keep them all as Datasets

- Nothing changes in the ground truth triples or the rows above.
- Two inputs named by the same words ("radiance data") become one node of the knowledge graph, with both DOIs.
- Facts about an input that has its own record (the epithermal map's instrument) are written in this record too, against rule 11's "Leave out a fact about another dataset".
- An archive and the datasets inside it carry the same entity class, so the knowledge graph can't tell them apart by their entity class.

#### Option 2: One input per DOI

- The record at pool position 2 gets two inputs, each with one DOI; their instances share the same words, so the ground truth needs a way to tell them apart (for example, the DOI written in the instance), which is a new exception to rule 1.

#### Option 3: Inputs only, no facts about them

- The ground truth triples "GRaND epithermal neutron map" ACQUIRED_BY_INSTRUMENT "GRaND", "radiance data" ACQUIRED_BY_INSTRUMENT "Moderate Resolution Imaging Spectroradiometer (MODIS)", and "pixels" HAS_PROCESSING_LEVEL "L2" are left out.
- An annotator, and the model, must know whether an input has its own record, which the record's [text](../docs/terminology.md#1-records-and-their-text) often doesn't say.

#### Option 4: An entity class for collections of datasets

- Archives and datasets are kept apart.
- The ground truth schema gains an entity class, and the rows that point to it are checked again.
- It waits for a tuning record that names one.

### Affects

- record at pool position 2: 6cfafd07-40f1-46da-9d92-36c2bb319f0b
- record at pool position 4: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- record at pool position 5: 99dff022-24ac-48cb-bc83-09fec8b90ad7
- classed triple of the record at pool position 2: "Normalized Difference Snow Index (NDSI)" (Variable) COMPUTED_FROM "radiance data" (Dataset)
- classed triple of the record at pool position 2: "radiance data" (Dataset) ACQUIRED_BY_INSTRUMENT "Moderate Resolution Imaging Spectroradiometer (MODIS)" (Instrument)
- classed triple of the record at pool position 2: "radiance data" (Dataset) HAS_DOI "DOI:10.5067/MODIS/MYD02HKM.061" (Identifier)
- classed triple of the record at pool position 2: "radiance data" (Dataset) HAS_DOI "DOI:10.5067/MODIS/MYD021KM.061" (Identifier)
- classed triple of the record at pool position 4: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) COMPUTED_FROM "pixels" (Dataset)
- classed triple of the record at pool position 4: "pixels" (Dataset) HAS_PROCESSING_LEVEL "L2" (ProcessingLevel)
- classed triple of the record at pool position 4: "pixels" (Dataset) BINNED_INTO "integerized sinusoidal area grid (ISEAG)" (Grid)
- classed triple of the record at pool position 4: "pixels" (Dataset) MAPPED_INTO "equidistant cylindrical" (MapProjection)
- classed triple of the record at pool position 5: "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0" (Dataset) COMPUTED_FROM "GRaND epithermal neutron map" (Dataset)
- classed triple of the record at pool position 5: "GRaND epithermal neutron map" (Dataset) ACQUIRED_BY_INSTRUMENT "GRaND" (Instrument)
- translation table row: entity class Dataset
- translation table row: entity class DataProduct
- translation table row: entity class Catalog
- translation table row: entity class Database
- rule: Writing a classed triple, rule 11
- rule: Writing a classed triple, rule 14

## Q13: What counts as a channel: radio frequency bands and wavelength bands?

- status: open
- priority: medium
- question kind: schema entry
- topic: the ground truth schema's Channel; the translation table's rows for Wavelength and Frequency (current or past schema)

### The question

The ground truth schema's Channel is "a range of wavelengths an Instrument measures separately, e.g. the 11 micron channel". The schema the [model](../docs/terminology.md#8-the-pipeline) learned from the catalog's records has two entity classes that hold bands of the spectrum: Wavelength ("A wavelength band or spectral range, such as an infrared filter band, in which observations are made"), which the translation table translates into Channel, and Frequency ("A rate of occurrence, such as daily or weekly, or a radio frequency band, such as S-, X-, or Ku-band"), which it translates into TemporalResolution, which fits only the rates. To decide where bands of the spectrum belong, I need to know:

- (a) Which radio frequency bands occur in the records of this catalog, and what do they describe there: the band an Instrument measures in (e.g. a radar or a radiometer), the band a Spacecraft sends its data down in, or something else?
- (b) For a radio frequency band that an Instrument measures in, is Channel the right entity class, or does a radio band need an entity class of its own? And when a record writes the band as part of the Instrument's words ("Aquarius L-band radiometer", in the record "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005"), should it stay inside them, as it does now, or be a [fact](../docs/terminology.md#2-triples) of its own?
- (c) Is every wavelength band in which observations are made (e.g. an infrared filter band) a Channel, or only a band the Instrument measures separately?

### Context

The example below has every Channel I have written down so far: four wavelength channels its two sea surface temperature products are computed from, two of them "unique to MODIS". The record "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005" names a radio frequency band inside its Instrument's words: "Aquarius L-band radiometer" keeps "L-band", since rule 9 takes a qualifier out of an instance only if it is one of the sorts it lists, and a radio band isn't one. So none of the facts I have written down yet has a radio band as its object.

How the translation table is used: the [model](../docs/terminology.md#8-the-pipeline) extracts classed triples with a schema it learned from other records of the catalog (the current schema; a schema an earlier run used is a past schema). Before its classed triples are compared with mine, each entity class and predicate of that schema is replaced by the one of the ground truth schema its [row](../docs/terminology.md#8-the-pipeline) of the translation table names.

### Example record

- record id: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- pool position: 4
- title: MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0
- notes: Day and night spatially gridded (L3) global NASA skin sea surface temperature (SST) products from the Moderate-resolution Imaging Spectroradiometer (MODIS) onboard the Aqua satellite. Average daily, weekly (8 day), monthly and annual skin SST products at are available at both 4.63 and 9.26 km spatial resolution. Aqua was launched by NASA on May 4, 2002, into a sun synchronous, polar orbit with a daylight ascending node at 13:30, formation flying in the A-train with other Earth Observation Satellites (EOS), to study the global dynamics of the Earth atmosphere, land and oceans. MODIS captures data in 36 spectral bands at a variety of spatial resolutions. Two SST products can be present in these files. The first is a skin SST produced for both day and night (NSST) observations, derived from the long wave IR 11 and 12 micron wavelength channels, using a modified nonlinear SST algorithm intended to provide continuity of SST derived from heritage and current NASA sensors. At night, a second SST product is generated using the mid-infrared 3.95 and 4.05 micron wavelength channels which are unique to MODIS; the SST derived from these measurements is identified as SST4. The SST4 product has lower uncertainty, but due to sun glint can only be used at night. To generate the L3 products the L2 pixels are binned into an integerized sinusoidal area grid (ISEAG) and mapped into an equidistant cylindrical (also known as Platte Carre projection. Additional projection detailed can be found at https://oceancolor.gsfc.nasa.gov/docs/format/ The NASA MODIS L3 SST data products are generated by the NASA Ocean Biology Processing Group (OBPG) and Peter Minnett and his team at the Rosenstiel School of Marine and Atmospheric Science (RSMAS) are responsible for sea surface temperature algorithm development, error statistics and quality flagging. JPL acquires MODIS ocean L3 SST data from the OBPG and is the official Physical Oceanography Data Archive (PO.DAAC) for SST. The R2019.0 supersedes the previous v2014.1 datasets which can be found at https://doi.org/10.5067/MODAM-8D4N4
- source text: The first is a skin SST produced for both day and night (NSST) observations, derived from the long wave IR 11 and 12 micron wavelength channels
- source text: At night, a second SST product is generated using the mid-infrared 3.95 and 4.05 micron wavelength channels which are unique to MODIS; the SST derived from these measurements is identified as SST4
- source text: the mid-infrared 3.95 and 4.05 micron wavelength channels which are unique to MODIS
- classed triple: "skin SST (NSST)" (Variable) COMPUTED_FROM "long wave IR 11 micron wavelength channel" (Channel)
- classed triple: "skin SST (NSST)" (Variable) COMPUTED_FROM "long wave IR 12 micron wavelength channel" (Channel)
- classed triple: "SST4" (Variable) COMPUTED_FROM "mid-infrared 3.95 micron wavelength channel" (Channel)
- classed triple: "SST4" (Variable) COMPUTED_FROM "mid-infrared 4.05 micron wavelength channel" (Channel)
- classed triple: "mid-infrared 3.95 micron wavelength channel" (Channel) UNIQUE_TO_INSTRUMENT "Moderate-resolution Imaging Spectroradiometer (MODIS)" (Instrument)
- classed triple: "mid-infrared 4.05 micron wavelength channel" (Channel) UNIQUE_TO_INSTRUMENT "Moderate-resolution Imaging Spectroradiometer (MODIS)" (Instrument)

### Ground truth schema

- entity class Channel: a range of wavelengths an Instrument measures separately, e.g. the 11 micron channel
- entity class Instrument: a device that takes measurements
- entity class TemporalResolution: the amount of time between one value of the data and the next, e.g. daily; weekly (8 day)
- predicate COMPUTED_FROM: was made by processing this input
- predicate UNIQUE_TO_INSTRUMENT: is found only on this Instrument
- predicate ACQUIRED_BY_INSTRUMENT: was collected by this Instrument

### Translation table

- entity class Wavelength -> Channel: A wavelength band or spectral range, such as an infrared filter band, in which observations are made.
- entity class Frequency -> TemporalResolution: A rate of occurrence, such as daily or weekly, or a radio frequency band, such as S-, X-, or Ku-band.

### Annotation guidelines

- Writing a classed triple, rule 4: Entity classes and predicates: the ground truth schema's, when one fits, so records name the same things the same way.
- Writing a classed triple, rule 9: A qualifier that is a temporal resolution, an area the data cover, a processing level, a spatial resolution, a country, a time of day, or a target body is a ground truth triple of its own, and is taken out of the instance.
- Writing a classed triple, rule 9: A qualifier stays in the instance, as written, if it is any other kind ("sea surface salinity" stays whole), or if taking it out would give a triple that isn't true.

### Options

#### Option 1: Keep Channel narrow, and radio bands inside the Instrument's words

Channel stays a range of wavelengths an Instrument measures separately; a radio band written in an Instrument's words stays there; the rows stay as they are.

#### Option 2: Widen Channel to any band of the spectrum

Channel's definition says any band of the spectrum an Instrument measures in, radio bands included, and a radio band in an Instrument's words ("L-band" in "Aquarius L-band radiometer") becomes a fact of its own.

#### Option 3: An entity class of its own for radio bands

A radio band gets an entity class of its own; Channel stays a range of wavelengths an Instrument measures separately.

### My current reading

Option 1 for now: the only radio band I have met so far is inside an Instrument's words, and the four channels fit Channel as it is. If radio bands are common in the catalog (a), option 2 or 3, as your answer to (b) says.

### My notes

The example is the record at pool position 4; the record at pool position 3 has "Aquarius L-band radiometer". A row of the translation table that names (none) says nothing in the ground truth schema means the same: a classed triple that uses it can never be part of a [pair](../docs/terminology.md#7-evaluating-extraction-step-070) with a ground truth triple, so it always counts as extracted only.

Option 2 also means a new exception to rule 9's list, and telling the step that learns the current schema to keep radio bands apart from rates, so that they get a row into Channel. Option 3: the entity class is one I coin in the ground truth schema, once a tuning record needs it.

### Consequences

#### Option 1: Keep Channel narrow, and radio bands inside the Instrument's words

- Nothing changes in the ground truth triples above.
- A filter band or a radio band the model extracts as Wavelength is compared as a Channel; one it extracts as Frequency is compared as a TemporalResolution, which no ground truth triple will give it, so it is counted wrong even when the model found the band.

#### Option 2: Widen Channel to any band of the spectrum

- The ground truth schema's definition of Channel, rule 9, and the model's copy of the rules change; the record at pool position 3 gets a triple for "L-band".
- The learning step's instructions change, and its next run costs model calls.

#### Option 3: An entity class of its own for radio bands

- Radio bands and wavelength channels are kept apart, as the answer to (b) may say they should be.
- The rows that hold radio bands are pointed at the new entity class and checked again.

### Affects

- record at pool position 3: 2705e0d1-95e7-4588-813b-ca91a6da94ff
- record at pool position 4: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- classed triple of the record at pool position 4: "skin SST (NSST)" (Variable) COMPUTED_FROM "long wave IR 11 micron wavelength channel" (Channel)
- classed triple of the record at pool position 4: "skin SST (NSST)" (Variable) COMPUTED_FROM "long wave IR 12 micron wavelength channel" (Channel)
- classed triple of the record at pool position 4: "SST4" (Variable) COMPUTED_FROM "mid-infrared 3.95 micron wavelength channel" (Channel)
- classed triple of the record at pool position 4: "SST4" (Variable) COMPUTED_FROM "mid-infrared 4.05 micron wavelength channel" (Channel)
- classed triple of the record at pool position 4: "mid-infrared 3.95 micron wavelength channel" (Channel) UNIQUE_TO_INSTRUMENT "Moderate-resolution Imaging Spectroradiometer (MODIS)" (Instrument)
- classed triple of the record at pool position 4: "mid-infrared 4.05 micron wavelength channel" (Channel) UNIQUE_TO_INSTRUMENT "Moderate-resolution Imaging Spectroradiometer (MODIS)" (Instrument)
- classed triple of the record at pool position 3: "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005" (Dataset) ACQUIRED_BY_INSTRUMENT "Aquarius L-band radiometer" (Instrument)
- translation table row: entity class Wavelength
- translation table row: entity class Frequency
- ground truth schema entry: entity class Channel
- rule: Writing a classed triple, rule 9
- pipeline method: common/common_prompts/extraction_rules.txt: the model's copy of the annotation guidelines' rules (rule 9's list of qualifiers taken out)

## Q14: Is every process or effect a phenomenon, including ones caused by people or by spaceflight?

- status: open
- priority: low
- question kind: translation table rows
- topic: the translation table's row for PhysicalPhenomenon (current or past schema), into the ground truth schema's Phenomenon

### The question

The ground truth schema's Phenomenon is "something that happens in nature and can be observed, e.g. sun glint". The schema the [model](../docs/terminology.md#8-the-pipeline) learned has an entity class PhysicalPhenomenon, "A natural or induced process, event, or effect, such as radiation-belt electron losses, signal refraction, or biological responses to spaceflight, that is observed or studied", which the translation table translates into Phenomenon. I would like to know:

- (a) Is every natural or induced process or effect, as PhysicalPhenomenon has it, a Phenomenon in the sense of the ground truth schema, including effects caused by people or by spaceflight (biological responses to spaceflight)?
- (b) If not: should Phenomenon's definition be widened ("something that happens, in nature or caused by people, and can be observed"), or should induced effects be something else?

### Context

The records I have read so far have one Phenomenon, "sun glint", in the example below. It fits both definitions; the question is about records still to come.

How the translation table is used: the [model](../docs/terminology.md#8-the-pipeline) extracts classed triples with a schema it learned from other records of the catalog (the current schema; a schema an earlier run used is a past schema). Before its classed triples are compared with mine, each entity class and predicate of that schema is replaced by the one of the ground truth schema its [row](../docs/terminology.md#8-the-pipeline) of the translation table names. A row that names (none) says nothing in the ground truth schema means the same.

### Example record

- record id: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- pool position: 4
- title: MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0
- notes: Day and night spatially gridded (L3) global NASA skin sea surface temperature (SST) products from the Moderate-resolution Imaging Spectroradiometer (MODIS) onboard the Aqua satellite. Average daily, weekly (8 day), monthly and annual skin SST products at are available at both 4.63 and 9.26 km spatial resolution. Aqua was launched by NASA on May 4, 2002, into a sun synchronous, polar orbit with a daylight ascending node at 13:30, formation flying in the A-train with other Earth Observation Satellites (EOS), to study the global dynamics of the Earth atmosphere, land and oceans. MODIS captures data in 36 spectral bands at a variety of spatial resolutions. Two SST products can be present in these files. The first is a skin SST produced for both day and night (NSST) observations, derived from the long wave IR 11 and 12 micron wavelength channels, using a modified nonlinear SST algorithm intended to provide continuity of SST derived from heritage and current NASA sensors. At night, a second SST product is generated using the mid-infrared 3.95 and 4.05 micron wavelength channels which are unique to MODIS; the SST derived from these measurements is identified as SST4. The SST4 product has lower uncertainty, but due to sun glint can only be used at night. To generate the L3 products the L2 pixels are binned into an integerized sinusoidal area grid (ISEAG) and mapped into an equidistant cylindrical (also known as Platte Carre projection. Additional projection detailed can be found at https://oceancolor.gsfc.nasa.gov/docs/format/ The NASA MODIS L3 SST data products are generated by the NASA Ocean Biology Processing Group (OBPG) and Peter Minnett and his team at the Rosenstiel School of Marine and Atmospheric Science (RSMAS) are responsible for sea surface temperature algorithm development, error statistics and quality flagging. JPL acquires MODIS ocean L3 SST data from the OBPG and is the official Physical Oceanography Data Archive (PO.DAAC) for SST. The R2019.0 supersedes the previous v2014.1 datasets which can be found at https://doi.org/10.5067/MODAM-8D4N4
- source text: The SST4 product has lower uncertainty, but due to sun glint can only be used at night
- classed triple: "SST4" (Variable) LIMITED_BY "sun glint" (Phenomenon)

### Ground truth schema

- entity class Phenomenon: something that happens in nature and can be observed, e.g. sun glint
- predicate LIMITED_BY: its use is restricted by

### Translation table

- entity class PhysicalPhenomenon -> Phenomenon: A natural or induced process, event, or effect, such as radiation-belt electron losses, signal refraction, or biological responses to spaceflight, that is observed or studied.

### Annotation guidelines

- Writing a classed triple, rule 4: Entity classes and predicates: the ground truth schema's, when one fits, so records name the same things the same way.

### Options

#### Option 1: Keep the row

PhysicalPhenomenon (current or past schema) translates into Phenomenon.

#### Option 2: Widen Phenomenon's definition

The ground truth schema's Phenomenon also holds effects caused by people or by spaceflight.

#### Option 3: Translate PhysicalPhenomenon into (none), or into an entity class of its own

Natural and induced effects are kept apart: PhysicalPhenomenon translates into nothing of the ground truth schema, or into an entity class of its own for induced effects.

### My current reading

Option 1 for now: the only Phenomenon so far fits both definitions. Your answer to (a) decides between option 2 and option 3.

### My notes

The example is the record at pool position 4, the only tuning record annotated so far with a Phenomenon; since "sun glint" fits both definitions, the row translates it rightly, which is why this question's priority is low. A classed triple that uses a row naming (none) can never be part of a [pair](../docs/terminology.md#7-evaluating-extraction-step-070) with a ground truth triple, so it always counts as extracted only. Option 3's entity class would be one I coin once a tuning record needs one.

### Consequences

#### Option 1: Keep the row

- Right for "sun glint", and for any natural process.
- An induced effect the model extracts is compared as a Phenomenon, which the ground truth schema's definition ("happens in nature") doesn't cover: counted right, or wrong, depending on how the annotator read the definition.
- Nothing changes now.

#### Option 2: Widen Phenomenon's definition

- The ground truth schema's definition changes, and the row into it is checked again.
- The ground truth written so far stays right, since "sun glint" fits both.

#### Option 3: Translate PhysicalPhenomenon into (none), or into an entity class of its own

- Classed triples that use PhysicalPhenomenon count as extracted only (with (none)), natural ones too, until the ground truth schema has an entity class for them.

### Affects

- record at pool position 4: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- classed triple of the record at pool position 4: "SST4" (Variable) LIMITED_BY "sun glint" (Phenomenon)
- translation table row: entity class PhysicalPhenomenon
- ground truth schema entry: entity class Phenomenon

## Q15: Is a coordinate system a map projection, and how should "Platte Carre" be written?

- status: open
- priority: low
- question kind: translation table rows
- topic: the translation table's rows for CoordinateSystem and HAS_COORDINATE_SYSTEM (current or past schema), and the ground truth schema's MapProjection

### The question

The schema the [model](../docs/terminology.md#8-the-pipeline) learned has an entity class CoordinateSystem: "A spatial reference frame or grid, such as a heliographic system or equidistant grid, used to locate or map data", and a predicate HAS_COORDINATE_SYSTEM. The translation table translates them into the ground truth schema's MapProjection, "a way of drawing the curved Earth on a flat map, e.g. equidistant cylindrical", and MAPPED_INTO. I would like to know:

- (a) Is every coordinate system a record of this catalog names a map projection? My reading is that it isn't: a coordinate system says how a position is given (e.g. a heliographic system, positions on the Sun), while a map projection says how a curved surface is drawn flat; and a grid ("a fixed set of cells that data values are collected into, e.g. ISEAG") is a third thing. If so, where should a coordinate system go?
- (b) The record below writes "Platte Carre". Is that the projection usually spelled "Plate Carrée", and is it the same projection as "equidistant cylindrical", so that the fact "equidistant cylindrical" (MapProjection) ALSO_KNOWN_AS "Platte Carre" (MapProjection) is true?
- (c) Should the knowledge graph keep a record's own spelling ("Platte Carre"), as the annotation guidelines do now, or the usual one?

### Context

How the translation table is used: the [model](../docs/terminology.md#8-the-pipeline) extracts classed triples with a schema it learned from other records of the catalog (the current schema; a schema an earlier run used is a past schema). Before its classed triples are compared with mine, each entity class and predicate of that schema is replaced by the one of the ground truth schema its [row](../docs/terminology.md#8-the-pipeline) of the translation table names. A row that names (none) says nothing in the ground truth schema means the same.

The record below is the only one so far where I wrote down a map projection. I kept the record's own words, as rule 1 says, also for "Platte Carre".

### Example record

- record id: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- pool position: 4
- title: MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0
- notes: Day and night spatially gridded (L3) global NASA skin sea surface temperature (SST) products from the Moderate-resolution Imaging Spectroradiometer (MODIS) onboard the Aqua satellite. Average daily, weekly (8 day), monthly and annual skin SST products at are available at both 4.63 and 9.26 km spatial resolution. Aqua was launched by NASA on May 4, 2002, into a sun synchronous, polar orbit with a daylight ascending node at 13:30, formation flying in the A-train with other Earth Observation Satellites (EOS), to study the global dynamics of the Earth atmosphere, land and oceans. MODIS captures data in 36 spectral bands at a variety of spatial resolutions. Two SST products can be present in these files. The first is a skin SST produced for both day and night (NSST) observations, derived from the long wave IR 11 and 12 micron wavelength channels, using a modified nonlinear SST algorithm intended to provide continuity of SST derived from heritage and current NASA sensors. At night, a second SST product is generated using the mid-infrared 3.95 and 4.05 micron wavelength channels which are unique to MODIS; the SST derived from these measurements is identified as SST4. The SST4 product has lower uncertainty, but due to sun glint can only be used at night. To generate the L3 products the L2 pixels are binned into an integerized sinusoidal area grid (ISEAG) and mapped into an equidistant cylindrical (also known as Platte Carre projection. Additional projection detailed can be found at https://oceancolor.gsfc.nasa.gov/docs/format/ The NASA MODIS L3 SST data products are generated by the NASA Ocean Biology Processing Group (OBPG) and Peter Minnett and his team at the Rosenstiel School of Marine and Atmospheric Science (RSMAS) are responsible for sea surface temperature algorithm development, error statistics and quality flagging. JPL acquires MODIS ocean L3 SST data from the OBPG and is the official Physical Oceanography Data Archive (PO.DAAC) for SST. The R2019.0 supersedes the previous v2014.1 datasets which can be found at https://doi.org/10.5067/MODAM-8D4N4
- source text: the L2 pixels are binned into an integerized sinusoidal area grid (ISEAG) and mapped into an equidistant cylindrical
- source text: an equidistant cylindrical (also known as Platte Carre projection
- source text: Additional projection detailed can be found at https://oceancolor.gsfc.nasa.gov/docs/format/
- classed triple: "pixels" (Dataset) MAPPED_INTO "equidistant cylindrical" (MapProjection)
- classed triple: "equidistant cylindrical" (MapProjection) ALSO_KNOWN_AS "Platte Carre" (MapProjection)
- classed triple: "equidistant cylindrical" (MapProjection) DOCUMENTED_AT "https://oceancolor.gsfc.nasa.gov/docs/format/" (WebPage)

### Ground truth schema

- entity class MapProjection: a way of drawing the curved Earth on a flat map, e.g. equidistant cylindrical
- entity class Grid: a fixed set of cells that data values are collected into, e.g. ISEAG
- predicate MAPPED_INTO: its values were laid onto a map drawn with this MapProjection
- predicate ALSO_KNOWN_AS: is the same thing under another name
- predicate DOCUMENTED_AT: more details about it are written at

### Translation table

- entity class CoordinateSystem -> MapProjection: A spatial reference frame or grid, such as a heliographic system or equidistant grid, used to locate or map data.
- predicate HAS_COORDINATE_SYSTEM -> MAPPED_INTO: The subject (a dataset) is expressed in, projected to, or mapped onto the object, a coordinate system or grid projection.

### Annotation guidelines

- Writing a classed triple, rule 1: Subject instance and object instance: the record's own words, as written. Don't paraphrase them, and don't expand an acronym the record leaves unexpanded.
- Writing a classed triple, rule 13: One thing, one wording, within a record.
- Writing a classed triple, rule 13: the other appears only in an ALSO_KNOWN_AS triple, and only if the record states one (rule 10).

### Options

#### Option 1: Keep the rows and the record's spelling

CoordinateSystem and HAS_COORDINATE_SYSTEM (current or past schema) translate into MapProjection and MAPPED_INTO; the ground truth keeps "Platte Carre" as written.

#### Option 2: Translate CoordinateSystem into (none), or into an entity class of its own

CoordinateSystem and HAS_COORDINATE_SYSTEM translate into nothing of the ground truth schema, or into an entity class (and a predicate) of their own for coordinate systems that aren't map projections.

### My current reading

Option 1: in the records I have read so far, the only coordinate system is a map projection; the spelling stays the record's own, as rule 1 says. I would choose option 2 if other coordinate systems are common in the catalog (a).

### My notes

The example is the record at pool position 4, the only tuning record whose ground truth so far has a map projection as an object instance, so the rows translate it rightly; that is why this question's priority is low: one record, and the facts are written down either way. A classed triple that uses a row naming (none) can never be part of a [pair](../docs/terminology.md#7-evaluating-extraction-step-070) with a ground truth triple, so it always counts as extracted only. Option 2's entity class (and predicate) would be ones I coin in the ground truth schema once a tuning record names a coordinate system that isn't a map projection.

### Consequences

#### Option 1: Keep the rows and the record's spelling

- Right when a coordinate system the model extracts is a map projection; counted wrong when it is a coordinate system of another sort (a heliographic system).
- The knowledge graph holds the record's spelling, so a search for "Plate Carrée" misses it.
- Nothing changes now.

#### Option 2: Translate CoordinateSystem into (none), or into an entity class of its own

- Map projections the model files under CoordinateSystem then count as extracted only (with (none)), or are compared with a coordinate system entity class the ground truth doesn't use for them.
- Right only if coordinate systems that aren't map projections are common in the catalog (question (a)).

### Affects

- record at pool position 4: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- classed triple of the record at pool position 4: "pixels" (Dataset) MAPPED_INTO "equidistant cylindrical" (MapProjection)
- classed triple of the record at pool position 4: "equidistant cylindrical" (MapProjection) ALSO_KNOWN_AS "Platte Carre" (MapProjection)
- classed triple of the record at pool position 4: "equidistant cylindrical" (MapProjection) DOCUMENTED_AT "https://oceancolor.gsfc.nasa.gov/docs/format/" (WebPage)
- translation table row: entity class CoordinateSystem
- translation table row: predicate HAS_COORDINATE_SYSTEM
- ground truth schema entry: entity class MapProjection
- ground truth schema entry: predicate MAPPED_INTO
- rule: Writing a classed triple, rule 1
- rule: Writing a classed triple, rule 13

## Q16: Is the time "13:30" in Aqua's orbit a fact of its own?

- status: open
- priority: low
- question kind: schema entry
- topic: the ground truth schema's Orbit and TimeOfDay, and rule 9 of the annotation guidelines

### The question

A record says that Aqua was launched "into a sun synchronous, polar orbit with a daylight ascending node at 13:30". The ground truth keeps that whole passage as one object instance: Aqua HAS_ORBIT "sun synchronous, polar orbit with a daylight ascending node at 13:30". I would like to know:

- (a) Is the time of the ascending node (13:30) something people who use this catalog search on by itself, for instance to find the satellites that cross the equator in the early afternoon? My reading, not checked against a source: the ascending node is where the orbit crosses the equator going north, and 13:30 is the local time at which it does so in daylight.
- (b) Are "sun synchronous" and "polar" two properties of the orbit, each worth a classed triple of its own, or does "sun synchronous, polar orbit" name one type of orbit?
- (c) If the time is a [fact](../docs/terminology.md#2-triples) of its own, what does it belong to: the orbit, or the satellite (Aqua)?

### Context

The ground truth schema has a TimeOfDay entity class, and rule 9 of the annotation guidelines takes a time of day out of an instance, as a ground truth triple of its own, unless taking it out would give a triple that isn't true. Taking "13:30" out with the only predicate the ground truth schema has for a time of day, OBSERVED_AT_TIME_OF_DAY, would say that the orbit comes from observations made at 13:30, which isn't true. So, by rule 9, "13:30" stays in the orbit's instance. The question is whether the ground truth schema should have another predicate for this time, so that it can be a ground truth triple of its own.

### Example record

- record id: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- pool position: 4
- title: MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0
- notes: Day and night spatially gridded (L3) global NASA skin sea surface temperature (SST) products from the Moderate-resolution Imaging Spectroradiometer (MODIS) onboard the Aqua satellite. Average daily, weekly (8 day), monthly and annual skin SST products at are available at both 4.63 and 9.26 km spatial resolution. Aqua was launched by NASA on May 4, 2002, into a sun synchronous, polar orbit with a daylight ascending node at 13:30, formation flying in the A-train with other Earth Observation Satellites (EOS), to study the global dynamics of the Earth atmosphere, land and oceans. MODIS captures data in 36 spectral bands at a variety of spatial resolutions. Two SST products can be present in these files. The first is a skin SST produced for both day and night (NSST) observations, derived from the long wave IR 11 and 12 micron wavelength channels, using a modified nonlinear SST algorithm intended to provide continuity of SST derived from heritage and current NASA sensors. At night, a second SST product is generated using the mid-infrared 3.95 and 4.05 micron wavelength channels which are unique to MODIS; the SST derived from these measurements is identified as SST4. The SST4 product has lower uncertainty, but due to sun glint can only be used at night. To generate the L3 products the L2 pixels are binned into an integerized sinusoidal area grid (ISEAG) and mapped into an equidistant cylindrical (also known as Platte Carre projection. Additional projection detailed can be found at https://oceancolor.gsfc.nasa.gov/docs/format/ The NASA MODIS L3 SST data products are generated by the NASA Ocean Biology Processing Group (OBPG) and Peter Minnett and his team at the Rosenstiel School of Marine and Atmospheric Science (RSMAS) are responsible for sea surface temperature algorithm development, error statistics and quality flagging. JPL acquires MODIS ocean L3 SST data from the OBPG and is the official Physical Oceanography Data Archive (PO.DAAC) for SST. The R2019.0 supersedes the previous v2014.1 datasets which can be found at https://doi.org/10.5067/MODAM-8D4N4
- source text: Aqua was launched by NASA on May 4, 2002, into a sun synchronous, polar orbit with a daylight ascending node at 13:30
- classed triple: "Aqua" (Spacecraft) HAS_ORBIT "sun synchronous, polar orbit with a daylight ascending node at 13:30" (Orbit)

### Ground truth schema

- entity class Orbit: the path a Spacecraft travels around a CelestialBody
- predicate HAS_ORBIT: travels in this Orbit
- entity class TimeOfDay: a point or period in the day, which comes back every day, e.g. 2:39 PM; morning; nighttime
- predicate OBSERVED_AT_TIME_OF_DAY: comes from observations made at or during this TimeOfDay

### Annotation guidelines

- Writing a classed triple, rule 5: One fact per ground truth triple. A sentence that states two facts gives two ground truth triples.
- Writing a classed triple, rule 9: A qualifier that is a temporal resolution, an area the data cover, a processing level, a spatial resolution, a country, a time of day, or a target body is a ground truth triple of its own, and is taken out of the instance.
- Writing a classed triple, rule 9: A qualifier stays in the instance, as written, if it is any other kind ("sea surface salinity" stays whole), or if taking it out would give a triple that isn't true. Suppose: a record says "an afternoon orbit". Then: taking "afternoon" out would give "orbit" OBSERVED_AT_TIME_OF_DAY "afternoon", which says the orbit comes from observations made in the afternoon. That isn't true, so the instance stays "afternoon orbit".

### Options

#### Option 1: Keep the orbit whole

The ground truth keeps one classed triple, as now: "Aqua" (Spacecraft) HAS_ORBIT "sun synchronous, polar orbit with a daylight ascending node at 13:30" (Orbit).

#### Option 2: The time as a ground truth triple of its own

A new predicate in the ground truth schema, e.g. HAS_ASCENDING_NODE_TIME ("crosses the equator going north at this TimeOfDay"), and the ground truth writes two classed triples: "Aqua" (Spacecraft) HAS_ORBIT "sun synchronous, polar orbit" (Orbit), and a second one that gives "13:30" (TimeOfDay), with Aqua or the orbit as its subject instance (question (c)).

#### Option 3: Split the orbit into all its properties

As option 2, and "sun synchronous" and "polar" also become ground truth triples of their own (question (b)).

### My current reading

Option 1, keep the orbit whole, because rule 9 keeps the time in the instance, and the records I have read so far name an orbit only once (Aqua's, in the example below). I would change to option 2 if people search this catalog by the time a satellite crosses the equator.

### My notes

The example is the record at pool position 4, the only tuning record annotated so far that names an orbit.

### Consequences

#### Option 1: Keep the orbit whole

- Nothing changes: not the annotation guidelines, not the ground truth schema, not the ground truth.
- The time 13:30 can be found only by searching inside the words of the orbit's instance; a search for satellites by the time they cross the equator has to read those words.
- Two records that describe the same orbit in different words give two different object instances.

#### Option 2: The time as a ground truth triple of its own

- A new predicate in the ground truth schema, and an example for it in the annotation guidelines, so that I write it the same way in every record; the [model](../docs/terminology.md#8-the-pipeline) follows the same rules, so its copy of the rules changes too.
- The orbit's instance loses the words "with a daylight ascending node at 13:30", which are no longer in that triple.
- The time can be searched for by itself.

#### Option 3: Split the orbit into all its properties

- Everything option 2 brings, and more predicates or entity classes for the properties of an orbit.
- More ground truth triples per record that describes an orbit, each of which the model must also extract.

### Affects

- record at pool position 4: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- classed triple of the record at pool position 4: "Aqua" (Spacecraft) HAS_ORBIT "sun synchronous, polar orbit with a daylight ascending node at 13:30" (Orbit)
- ground truth schema entry: entity class Orbit
- ground truth schema entry: predicate HAS_ORBIT
- rule: Writing a classed triple, rule 5
- rule: Writing a classed triple, rule 9
- pipeline method: annotations/ground_truth_schema.txt: a new predicate for the time an orbit crosses the equator (option 2), or for each property of an orbit (option 3)
- pipeline method: common/common_prompts/extraction_rules.txt: the model's copy of the annotation guidelines' rules, which changes with a rule

## Q17: The GRaND residual map is "related to the average atomic mass on Vesta": is there a more specific relationship?

- status: answered
- priority: low
- question kind: records and triples
- topic: the ground truth schema's RELATED_TO and ESTIMATES, and rule 1 of *What counts as a fact* in the annotation guidelines

### The question

A record of data from the GRaND instrument of the Dawn spacecraft says: "The residual map is related to the average atomic mass on Vesta." The ground truth writes this as the dataset RELATED_TO "average atomic mass". I would like to know:

- (a) What is the relationship between the residual map and the average atomic mass: does the residual map give approximate values of the average atomic mass, or is it only one clue among several?
- (b) Would someone in your field read "is related to" in such a record as "gives approximate values for", or only as "has something to do with"?

### Context

I write only what a record states (rule 1 of *What counts as a fact*, quoted below), so a more specific predicate than RELATED_TO needs words in the record that say so. The ground truth schema has ESTIMATES, "gives approximate values for", which the ground truth uses for what a Variable gives approximate values of.

### Example record

- record id: 99dff022-24ac-48cb-bc83-09fec8b90ad7
- pool position: 5
- title: DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0
- notes: These data are maps of fast neutron residual count rates from the GRaND plus Z boron loaded sensor. The nominal fast neutron count rates were detrended using the GRaND epithermal neutron map to produced this residual map. The residual map is related to the average atomic mass on Vesta. Details of the map and data reduction are described in LAWRENCEETAL2013.
- source text: The residual map is related to the average atomic mass on Vesta
- classed triple: "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0" (Dataset) RELATED_TO "average atomic mass" (PhysicalQuantity)

### Ground truth schema

- predicate RELATED_TO: is related to
- predicate ESTIMATES: gives approximate values for
- entity class PhysicalQuantity: a property that can be measured, in general, whatever method measures it, e.g. sea surface temperature; snow cover

### Annotation guidelines

- What counts as a fact, rule 1: Only what the record states. Never add what you know from elsewhere, and never write down what an unexplained code or acronym stands for.

### Options

#### Option 1: Keep RELATED_TO

The ground truth stays as it is: the dataset RELATED_TO "average atomic mass".

#### Option 2: A more specific predicate for the average atomic mass

Only if "related to" here means "gives approximate values for" (question (a)): the dataset ESTIMATES "average atomic mass" in place of RELATED_TO.

### My current reading

Option 1, because "related to" is all the record states. I would change to option 2 if experts say that, in such a record, "related to" means that the map gives approximate values of the average atomic mass.

### The answer

Settled by checked sources, option 1. A review of this record on 2026-10-22 checked NASA's archive documents for it, and the paper the record cites, LAWRENCEETAL2013 (Lawrence et al. 2013): it says the corrected fast neutron counts vary with the average atomic mass. So the record's "related to" is accurate, and ESTIMATES would claim more than the record and the paper say. The ground truth keeps RELATED_TO "average atomic mass".

### Consequences

#### Option 1: Keep RELATED_TO

- Nothing changes.
- RELATED_TO says only that some relationship exists; a search for datasets that give values of the average atomic mass won't find this one by that predicate.

#### Option 2: A more specific predicate for the average atomic mass

- One ground truth triple changes its predicate, and a search for datasets that give values of the average atomic mass finds this one.
- If "related to" means less than that, it would add a [fact](../docs/terminology.md#2-triples) the record doesn't state, against rule 1 of *What counts as a fact*.

### Affects

- record at pool position 5: 99dff022-24ac-48cb-bc83-09fec8b90ad7
- classed triple of the record at pool position 5: "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0" (Dataset) RELATED_TO "average atomic mass" (PhysicalQuantity)
- ground truth schema entry: predicate RELATED_TO
- rule: What counts as a fact, rule 1

## Q18: SST4 and NSST: is SST4 a skin sea surface temperature, lower uncertainty than what, and does this product hold both?

- status: open
- priority: low
- question kind: records and triples
- topic: the ground truth schema's Variable, ESTIMATES and HAS_LOWER_UNCERTAINTY_THAN, and rule 13 of the annotation guidelines

### The question

A record of MODIS sea surface temperature (SST) products describes two SST products in its files: a skin SST made for day and night (NSST), and, at night, a second SST product, identified as SST4. The ground truth now says that NSST gives approximate values of the "skin sea surface temperature (SST)", that SST4 gives approximate values of "SST", and that SST4 has lower uncertainty than NSST. I would like to know:

- (a) Is SST4 a skin SST too, so that both products estimate the same quantity, the skin sea surface temperature? If so, rule 13 of the annotation guidelines (one thing, one wording, within a record) would write "skin sea surface temperature (SST)" for both.
- (b) The record says "The SST4 product has lower uncertainty", without saying than what. The ground truth reads it as "lower uncertainty than NSST", the other product the record describes. Is that how an expert reads it?
- (c) The dataset's title is "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0", and the record says "Two SST products can be present in these files". The ground truth says the dataset HAS_VARIABLE "SST4", from the title's "SST MID-IR" (SST4 is the one made from the mid-infrared channels), and writes no HAS_VARIABLE for NSST, since "can be present" is not a statement that it is (rule 7 of *What counts as a fact*: "Not uncertain facts."). Does a "SST MID-IR ... Nighttime" product hold SST4 only, or NSST too?

### Context

The record introduces the two products as "Two SST products can be present in these files. The first is a skin SST ... At night, a second SST product ...". Whether "a second SST product" is a skin SST too is what (a) asks: I may use what the words mean to see that two wordings name the same thing (rule 13), but I may not add a [fact](../docs/terminology.md#2-triples) the record doesn't state (rule 1 of *What counts as a fact*).

### Example record

- record id: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- pool position: 4
- title: MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0
- notes: Day and night spatially gridded (L3) global NASA skin sea surface temperature (SST) products from the Moderate-resolution Imaging Spectroradiometer (MODIS) onboard the Aqua satellite. Average daily, weekly (8 day), monthly and annual skin SST products at are available at both 4.63 and 9.26 km spatial resolution. Aqua was launched by NASA on May 4, 2002, into a sun synchronous, polar orbit with a daylight ascending node at 13:30, formation flying in the A-train with other Earth Observation Satellites (EOS), to study the global dynamics of the Earth atmosphere, land and oceans. MODIS captures data in 36 spectral bands at a variety of spatial resolutions. Two SST products can be present in these files. The first is a skin SST produced for both day and night (NSST) observations, derived from the long wave IR 11 and 12 micron wavelength channels, using a modified nonlinear SST algorithm intended to provide continuity of SST derived from heritage and current NASA sensors. At night, a second SST product is generated using the mid-infrared 3.95 and 4.05 micron wavelength channels which are unique to MODIS; the SST derived from these measurements is identified as SST4. The SST4 product has lower uncertainty, but due to sun glint can only be used at night. To generate the L3 products the L2 pixels are binned into an integerized sinusoidal area grid (ISEAG) and mapped into an equidistant cylindrical (also known as Platte Carre projection. Additional projection detailed can be found at https://oceancolor.gsfc.nasa.gov/docs/format/ The NASA MODIS L3 SST data products are generated by the NASA Ocean Biology Processing Group (OBPG) and Peter Minnett and his team at the Rosenstiel School of Marine and Atmospheric Science (RSMAS) are responsible for sea surface temperature algorithm development, error statistics and quality flagging. JPL acquires MODIS ocean L3 SST data from the OBPG and is the official Physical Oceanography Data Archive (PO.DAAC) for SST. The R2019.0 supersedes the previous v2014.1 datasets which can be found at https://doi.org/10.5067/MODAM-8D4N4
- source text: The first is a skin SST produced for both day and night (NSST)
- source text: the SST derived from these measurements is identified as SST4
- source text: The SST4 product has lower uncertainty
- classed triple: "skin SST (NSST)" (Variable) ESTIMATES "skin sea surface temperature (SST)" (PhysicalQuantity)
- classed triple: "SST4" (Variable) ESTIMATES "SST" (PhysicalQuantity)
- classed triple: "SST4" (Variable) HAS_LOWER_UNCERTAINTY_THAN "skin SST (NSST)" (Variable)

### Ground truth schema

- entity class Variable: one named kind of value computed from an Instrument's measurements by one particular Algorithm, e.g. SST4; NDSI
- entity class PhysicalQuantity: a property that can be measured, in general, whatever method measures it, e.g. sea surface temperature; snow cover
- predicate ESTIMATES: gives approximate values for
- predicate HAS_LOWER_UNCERTAINTY_THAN: its values are more certain than those of

### Translation table

- predicate MORE_ACCURATE_THAN -> HAS_LOWER_UNCERTAINTY_THAN: Links a measurement method or instrument to another method that it outperforms in accuracy.

### Annotation guidelines

- What counts as a fact, rule 1: Only what the record states. Never add what you know from elsewhere, and never write down what an unexplained code or acronym stands for.
- What counts as a fact, rule 7: Not uncertain facts.
- Writing a classed triple, rule 13: One thing, one wording, within a record. When a record names the same thing more than once, in different words: if one wording says more (it contains the other, is more precise, or spells out its abbreviation), use it

### Options

#### Option 1: Keep the ground truth as it is

The facts stay as written: "SST4" (Variable) ESTIMATES "SST" (PhysicalQuantity); "skin SST (NSST)" (Variable) ESTIMATES "skin sea surface temperature (SST)" (PhysicalQuantity); and "SST4" (Variable) HAS_LOWER_UNCERTAINTY_THAN "skin SST (NSST)" (Variable).

#### Option 2: Both estimate the skin sea surface temperature

If SST4 is a skin SST: "SST4" (Variable) ESTIMATES "skin sea surface temperature (SST)" (PhysicalQuantity), one wording for both, by rule 13.

#### Option 3: Leave out the comparison

If "lower uncertainty" doesn't clearly mean "than NSST": no comparison is written, so there is no fact "SST4" (Variable) HAS_LOWER_UNCERTAINTY_THAN "skin SST (NSST)" (Variable).

### My current reading

Option 1, because the record names SST4's quantity only "SST", and the comparison with NSST is the only reading I see, with two products introduced as "the first" and "a second". For (c), I write only that the dataset holds SST4, since "can be present" doesn't state that NSST is there.

### My notes

The example is the record at pool position 4. Until an expert answers, its ground truth keeps option 1, and HAS_VARIABLE "SST4" only. If experts say a "Nighttime" "SST MID-IR" product holds NSST too, I would still write it only if the record says so, and note the gap.

### Consequences

#### Option 1: Keep the ground truth as it is

- Nothing changes.
- If SST4 is a skin SST, the two products appear to estimate two different quantities ("SST" and "skin sea surface temperature (SST)"), and a search for skin SST data finds only NSST.

#### Option 2: Both estimate the skin sea surface temperature

- One ground truth triple changes its object instance.
- The record's word for SST4's quantity is "SST", so this relies on rule 13's "what you know about the words", which an expert has to confirm.

#### Option 3: Leave out the comparison

- One ground truth triple fewer; the record's statement that SST4 is more certain is no longer in the ground truth at all, since a comparison needs two sides.

### Affects

- record at pool position 4: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- classed triple of the record at pool position 4: "skin SST (NSST)" (Variable) ESTIMATES "skin sea surface temperature (SST)" (PhysicalQuantity)
- classed triple of the record at pool position 4: "SST4" (Variable) ESTIMATES "SST" (PhysicalQuantity)
- classed triple of the record at pool position 4: "SST4" (Variable) HAS_LOWER_UNCERTAINTY_THAN "skin SST (NSST)" (Variable)
- classed triple of the record at pool position 4: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) HAS_VARIABLE "SST4" (Variable)
- rule: What counts as a fact, rule 7
- translation table row: predicate MORE_ACCURATE_THAN
- ground truth schema entry: predicate ESTIMATES
- ground truth schema entry: predicate HAS_LOWER_UNCERTAINTY_THAN
- rule: What counts as a fact, rule 1
- rule: Writing a classed triple, rule 13

## Q19: Versions and releases: are "R2019.0" and "V2019.0" the same release, and is a MODIS "Collection" a version?

- status: open
- priority: low
- question kind: records and triples
- topic: the ground truth schema's Version, HAS_VERSION, SUPERSEDES and ALSO_KNOWN_AS, and rules 10 and 13 of the annotation guidelines

### The question

A record's title ends in "V2019.0", and its notes say "The R2019.0 supersedes the previous v2014.1 datasets". I read "R2019.0" and "V2019.0" as two names of one release, and wrote: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) HAS_VERSION "V2019.0" (Version), and "V2019.0" (Version) SUPERSEDES "v2014.1" (Version). I would like to know:

- (a) Are "R2019.0" and "V2019.0" the same release of the data? My reading, not checked against a source: "R" may stand for a reprocessing, and the reprocessing of 2019 made version 2019.0.
- (b) If they are not the same, what is "R2019.0": a reprocessing, a release of the processing software, or something else?
- (c) The record "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" says "The terms "Version 61" and "Collection 6.1" are used interchangeably in reference to this release of MODIS data". I wrote the facts "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" (Dataset) HAS_VERSION "Version 61" (Version) and "Version 61" (Version) ALSO_KNOWN_AS "Collection 6.1" (Version). Is a MODIS "Collection" a version of this one dataset, or a reprocessing of all MODIS products at once, which this dataset is part of (and so something the dataset belongs to, not its version)? And is the title's "V061" that same Version 61?

### Context

Rule 13 of the annotation guidelines writes one thing with one wording in a record: of two names that say the same, the one the record uses most often, or, on a tie, the one it gives first. Each wording appears once, and the title comes first, so I wrote "V2019.0". If they are two names of one release, rule 10 allows an ALSO_KNOWN_AS triple only when the record gives the other name in words of its own, which it doesn't here.

### Example record

- record id: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- pool position: 4
- title: MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0
- notes: Day and night spatially gridded (L3) global NASA skin sea surface temperature (SST) products from the Moderate-resolution Imaging Spectroradiometer (MODIS) onboard the Aqua satellite. Average daily, weekly (8 day), monthly and annual skin SST products at are available at both 4.63 and 9.26 km spatial resolution. Aqua was launched by NASA on May 4, 2002, into a sun synchronous, polar orbit with a daylight ascending node at 13:30, formation flying in the A-train with other Earth Observation Satellites (EOS), to study the global dynamics of the Earth atmosphere, land and oceans. MODIS captures data in 36 spectral bands at a variety of spatial resolutions. Two SST products can be present in these files. The first is a skin SST produced for both day and night (NSST) observations, derived from the long wave IR 11 and 12 micron wavelength channels, using a modified nonlinear SST algorithm intended to provide continuity of SST derived from heritage and current NASA sensors. At night, a second SST product is generated using the mid-infrared 3.95 and 4.05 micron wavelength channels which are unique to MODIS; the SST derived from these measurements is identified as SST4. The SST4 product has lower uncertainty, but due to sun glint can only be used at night. To generate the L3 products the L2 pixels are binned into an integerized sinusoidal area grid (ISEAG) and mapped into an equidistant cylindrical (also known as Platte Carre projection. Additional projection detailed can be found at https://oceancolor.gsfc.nasa.gov/docs/format/ The NASA MODIS L3 SST data products are generated by the NASA Ocean Biology Processing Group (OBPG) and Peter Minnett and his team at the Rosenstiel School of Marine and Atmospheric Science (RSMAS) are responsible for sea surface temperature algorithm development, error statistics and quality flagging. JPL acquires MODIS ocean L3 SST data from the OBPG and is the official Physical Oceanography Data Archive (PO.DAAC) for SST. The R2019.0 supersedes the previous v2014.1 datasets which can be found at https://doi.org/10.5067/MODAM-8D4N4
- source text: V2019.0
- source text: The R2019.0 supersedes the previous v2014.1 datasets
- classed triple: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) HAS_VERSION "V2019.0" (Version)
- classed triple: "V2019.0" (Version) SUPERSEDES "v2014.1" (Version)

### Ground truth schema

- entity class Version: a label that marks one release of something
- predicate HAS_VERSION: carries this Version
- predicate SUPERSEDES: replaces this earlier one
- predicate ALSO_KNOWN_AS: is the same thing under another name

### Annotation guidelines

- Writing a classed triple, rule 10: A name with its abbreviation in parentheses is one instance, as written. Suppose: a record says "This Level-2 (L2) dataset". Then: the instance is "Level-2 (L2)", with no ALSO_KNOWN_AS triple. Write ALSO_KNOWN_AS only when the record gives the other name in words of its own
- Writing a classed triple, rule 13: One thing, one wording, within a record. When a record names the same thing more than once, in different words: if one wording says more (it contains the other, is more precise, or spells out its abbreviation), use it; if they are two names that say the same, use the one the record uses most often (on a tie, the one it gives first)

### Options

#### Option 1: The same release (as now)

They are one release, written as now: the dataset HAS_VERSION "V2019.0" (Version), and "V2019.0" (Version) SUPERSEDES "v2014.1" (Version).

#### Option 2: Two different things

They differ: "R2019.0" SUPERSEDES "v2014.1" (Version), as the record writes it, with "R2019.0" in an entity class that fits what it is (question (b)), and the dataset still HAS_VERSION "V2019.0" (Version).

### My current reading

Option 1, because the record calls both the release that replaces v2014.1, and nothing in it says they differ. I would change to option 2 if experts say "R" and "V" mark different things in NASA's ocean products. For (c), I keep "Version 61" (Version) ALSO_KNOWN_AS "Collection 6.1" (Version), since the record says the two terms "are used interchangeably"; if a Collection is a reprocessing of all MODIS products, "Collection 6.1" would need an entity class and a predicate of its own (something the dataset belongs to), which the ground truth schema doesn't have yet.

### My notes

The example is the record at pool position 4; (c) is about the record at pool position 2. Until an expert answers, the ground truth keeps option 1, and "Version 61" ALSO_KNOWN_AS "Collection 6.1".

### Consequences

#### Option 1: The same release (as now)

- Nothing changes.
- The word "R2019.0" isn't in the ground truth; a search for it won't find this record.

#### Option 2: Two different things

- "R2019.0" is linked to the dataset by no ground truth triple, since the record doesn't say how the two relate; the annotation tool flags such a triple as not connected to the catalog entry.
- Perhaps a new entity class, if "R2019.0" is neither a Version nor anything the ground truth schema has.

### Affects

- record at pool position 4: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- classed triple of the record at pool position 4: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) HAS_VERSION "V2019.0" (Version)
- classed triple of the record at pool position 4: "V2019.0" (Version) SUPERSEDES "v2014.1" (Version)
- record at pool position 2: 6cfafd07-40f1-46da-9d92-36c2bb319f0b
- classed triple of the record at pool position 2: "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" (Dataset) HAS_VERSION "Version 61" (Version)
- classed triple of the record at pool position 2: "Version 61" (Version) ALSO_KNOWN_AS "Collection 6.1" (Version)
- translation table row: predicate SUPERSEDES
- ground truth schema entry: predicate SUPERSEDES
- rule: Writing a classed triple, rule 10
- rule: Writing a classed triple, rule 13

## Q20: What is "Near Real Time (NRT)", what counts as an identifier ("MCD19A2N", "LAWRENCEETAL2013"), and is "MCD19A1N" another dataset?

- status: open
- priority: low
- question kind: records and triples
- topic: the ground truth schema's Identifier, HAS_DOI, Document, Version and COMPUTED_FROM, the predicate HAS_IDENTIFIER I have coined, and rules 10, 11 and 14 of the annotation guidelines

### The question

I am annotating a record of a MODIS aerosol product, and three passages of its [text](../docs/terminology.md#1-records-and-their-text) I am not sure how to write as classed triples; one of them raises a question about another record too:

- (a) "Near Real Time (NRT)": is it a latency (how soon after the observation the data are made available), a separate processing stream (a different product from the standard one), or a version? Each would be a different predicate, and the ground truth schema has none for a latency. Until you answer, I write no classed triple for it.
- (b) "(MCD19A2N)": I have written it as an identifier of the dataset, with a predicate I coined for it, HAS_IDENTIFIER, "has this Identifier": the dataset HAS_IDENTIFIER "MCD19A2N" (Identifier), an Identifier being "a code that names one thing permanently, e.g. a DOI". Is a NASA product short name such as MCD19A2N permanent in that sense, or a label that can change, or be given to another product later? And should HAS_DOI ("has the Digital Object Identifier") and HAS_IDENTIFIER be one predicate, a DOI being one sort of identifier, or stay two?
- (c) "The MCD19A2N product provides the atmospheric properties and view geometry used to calculate the MAIAC Land Surface Bidirectional Reflectance Factor (BRF) or surface reflectance, MCD19A1N product": is "MCD19A1N" another dataset? If it is, is "MCD19A1N is computed from this dataset" a [fact](../docs/terminology.md#2-triples) about this dataset, to write, or a fact about the other dataset, to leave out? And are "the atmospheric properties and view geometry" what this dataset holds, to write as facts about it, or only the part of it the other product uses? (Whether each is specific enough, and what kind of thing each is, is asked in another question, about what is measured and what is computed.)
- (d) The same question of what counts as an identifier, in another record: the record "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0" says "Details of the map and data reduction are described in LAWRENCEETAL2013". I wrote LAWRENCEETAL2013 as a Document, "a written publication, or a set of them, named in words or by a reference key": "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0" (Dataset) DOCUMENTED_AT "LAWRENCEETAL2013" (Document). Is a Planetary Data System reference key such as LAWRENCEETAL2013 the publication itself (a Document named by its key, as now), or an identifier of the publication, an Identifier of its own?

### Context

Below are the facts I have written for this record so far, a draft not checked yet; one of them is "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) HAS_IDENTIFIER "MCD19A2N" (Identifier), which (b) asks about. I have written no fact for "Near Real Time (NRT)" until (a) is answered, and none yet for (c).

What I have checked about (a), on 2026-10-25. NASA's LANCE page (https://www.earthdata.nasa.gov/data/projects/lance) says: "Near real-time (NRT) refers to data available 1 to 3 hours after an observation by an instrument aboard a space-based platform"; the Terra, Aqua and Aura measurements "are processed into higher-level "standard" products within 8 to 40 hours of observation"; and "If latency is not a primary concern, users are encouraged to use standard science products, which are created using the best available ancillary, calibration, and ephemeris information". MODAPS lists MCD19A2N among its Collection 6.1 NRT products, as a product of its own, with its own DOI, 10.5067/MODIS/MCD19A2N.NRT.061 (https://modaps.modaps.eosdis.nasa.gov/services/about/products/c61-nrt/MCD19A2N.html), apart from the standard product MCD19A2. So my reading of the sources: NRT here names a processing stream, a separate product, whose defining property is how soon it is made available. The record itself states no number of hours, and the annotation guidelines write only what the record states, so a latency value from these sources can't go into its ground truth. The catalog also has another record, titled "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid NRT", whose notes begin with the same words as this record's.

### Example record

- record id: 4c64f3ed-39b4-4f95-95a0-022898ba47a4
- pool position: 6
- title: MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid
- notes: The Moderate Resolution Imaging Spectroradiometer (MODIS) Near Real Time (NRT) Combined Terra and Aqua Multi-Angle Implementation of Atmospheric Correction (MAIAC) Land Aerosol Optical Depth gridded Level 2 product (MCD19A2N) produced daily at 1 kilometer (km) pixel resolutions. The MCD19A2N product provides the atmospheric properties and view geometry used to calculate the MAIAC Land Surface Bidirectional Reflectance Factor (BRF) or surface reflectance, MCD19A1N product.
- in the ground truth: not yet: I am annotating this record now, so its classed triples below are my drafts, approved so far, not yet in annotations/ground_truth/
- source text: Near Real Time (NRT)
- source text: Land Aerosol Optical Depth gridded Level 2 product (MCD19A2N)
- source text: produced daily at 1 kilometer (km) pixel resolutions
- source text: Multi-Angle Implementation of Atmospheric Correction (MAIAC)
- source text: The MCD19A2N product provides the atmospheric properties and view geometry used to calculate the MAIAC Land Surface Bidirectional Reflectance Factor (BRF) or surface reflectance, MCD19A1N product
- classed triple: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) ACQUIRED_BY_INSTRUMENT "Moderate Resolution Imaging Spectroradiometer (MODIS)" (Instrument)
- classed triple: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) FROM_SPACECRAFT "Terra" (Spacecraft)
- classed triple: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) FROM_SPACECRAFT "Aqua" (Spacecraft)
- classed triple: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) HAS_MEASUREMENTS_OF "Aerosol Optical Depth" (PhysicalQuantity)
- classed triple: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) HAS_SPATIAL_COVERAGE "Land" (SpatialExtent)
- classed triple: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) HAS_TEMPORAL_RESOLUTION "daily" (TemporalResolution)
- classed triple: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) HAS_PROCESSING_LEVEL "Level 2" (ProcessingLevel)
- classed triple: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) HAS_SPATIAL_REPRESENTATION "gridded" (SpatialRepresentation)
- classed triple: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) HAS_SPATIAL_RESOLUTION "1 kilometer (km)" (SpatialResolution)
- classed triple: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) PRODUCED_USING_ALGORITHM "Multi-Angle Implementation of Atmospheric Correction (MAIAC)" (Algorithm)
- classed triple: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) HAS_IDENTIFIER "MCD19A2N" (Identifier)

### Ground truth schema

- entity class Identifier: a code that names one thing permanently, e.g. a DOI
- predicate HAS_DOI: has the Digital Object Identifier
- entity class Document: a written publication, or a set of them, named in words or by a reference key, e.g. NASA developed standards; LAWRENCEETAL2013
- predicate DOCUMENTED_AT: more details about it are written at
- entity class Version: a label that marks one release of something
- predicate ALSO_KNOWN_AS: is the same thing under another name
- predicate COMPUTED_FROM: was made by processing this input

### Translation table

- predicate HAS_LATENCY -> (none): The subject (a data product or table) is made available or updated with the object, a latency or update delay.
- predicate HAS_IDENTIFIER -> (none): The subject (a dataset, data series or document) is indexed by, or refers to items using, the object, which is a key, label or designator such as a prime key or detector name.

### Annotation guidelines

- What counts as a fact, rule 1: Only what the record states. Never add what you know from elsewhere, and never write down what an unexplained code or acronym stands for.
- Writing a classed triple, rule 10: A name with its abbreviation in parentheses is one instance, as written.
- Writing a classed triple, rule 11: General facts: include them, unless they're about another dataset.
- Writing a classed triple, rule 11: Leave out a fact about another dataset, even a closely related one, such as the same data at another time step or resolution. That dataset has its own record, and its facts go there.
- Writing a classed triple, rule 14: A processing step: output_i = method_i(input_i).

### Options

#### Option 1: Write none of the three for now

None of (a), (b), (c) is written as a fact for now: the record keeps only the facts written so far.

#### Option 2: Write each with what the ground truth schema has

(a) "Near Real Time (NRT)" kept inside the dataset's description, with no fact of its own; (b) "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) ALSO_KNOWN_AS "MCD19A2N", in place of HAS_IDENTIFIER, and HAS_DOI as it is; (c) "MCD19A1N product" (Dataset) COMPUTED_FROM "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset), as a processing step of rule 14 with this dataset as its input.

#### Option 3: New predicates for a latency and an identifier

A new predicate for a latency (the dataset has the latency "Near Real Time (NRT)"), and the one I coined for an identifier kept (the dataset HAS_IDENTIFIER "MCD19A2N" (Identifier)), both in the ground truth schema, with HAS_DOI either kept or made one with HAS_IDENTIFIER (question (b)); (c) and (d) as you answer them.

### My current reading

Undecided. For (a), I lean towards reading NRT as a processing stream, a product of its own (the sources above), with no latency value, since the record states none. For (b), I lean towards option 3, an identifier, since a product code names one product permanently, much as a DOI does. For (c), I lean towards leaving out "MCD19A1N" COMPUTED_FROM this dataset, by rule 11 ("Leave out a fact about another dataset"): its subject is the other product, so the fact is about that product. For (d), I keep LAWRENCEETAL2013 a Document, as the definition of Document names it. I would still like to know whether MCD19A1N is computed from this product, and whether "the atmospheric properties and view geometry" are what this dataset holds.

### My notes

The example is the record at pool position 6, not in the ground truth yet: its classed triples are my drafts, and the one with HAS_IDENTIFIER is its fact 10, written so for now. "Near Real Time (NRT)" has no classed triple until (a) is answered. The record titled "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid NRT" is not in my ground truth candidates pool. (d) is about the record at pool position 5, only named in the question; its classed triple is listed under Affects. Until an expert answers (d), its ground truth keeps LAWRENCEETAL2013 a Document.

Pending facts, for the record at pool position 6:

- pending fact: its fact 11, "Near Real Time (NRT)", left without a fact for now; added if the answer to (a) says what it is (a latency, a processing stream or a version), with the predicate that answer calls for.
- pending fact: its fact 12, "MCD19A1N" (Dataset) COMPUTED_FROM "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset), left out by rule 11 of *Writing a classed triple* ("General facts: include them, unless they're about another dataset"); added if the answer to (c) says it is a fact about this dataset.
- "atmospheric properties" and "view geometry": written as its fact 13, two HAS_MEASUREMENTS_OF triples (approved 2026-10-25); their doubts are Q3 (g).

### Consequences

#### Option 1: Write none of the three for now

- The facts the three passages may state are missing from the ground truth: an extracted triple that states one of them counts as wrong when this record is evaluated.
- Nothing in the ground truth schema or the annotation guidelines changes.

#### Option 2: Write each with what the ground truth schema has

- No new entity class or predicate.
- (b) treats a product code as another name, which rule 10 doesn't cover (it covers an abbreviation in parentheses, and MCD19A2N doesn't abbreviate the words before it).
- (c) writes a fact whose subject instance is another dataset, which rule 11 may forbid (question (c)).

#### Option 3: New predicates for a latency and an identifier

- Two new predicates in the ground truth schema, each with a definition and an example in the annotation guidelines; the [model](../docs/terminology.md#8-the-pipeline) follows the same rules, so its copy changes too.
- Other records with a product code or a latency are written the same way.

### Affects

- record at pool position 6: 4c64f3ed-39b4-4f95-95a0-022898ba47a4
- classed triple of the record at pool position 6: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) HAS_IDENTIFIER "MCD19A2N" (Identifier)
- record at pool position 2: 6cfafd07-40f1-46da-9d92-36c2bb319f0b
- classed triple of the record at pool position 2: "radiance data" (Dataset) HAS_DOI "DOI:10.5067/MODIS/MYD02HKM.061" (Identifier)
- classed triple of the record at pool position 2: "radiance data" (Dataset) HAS_DOI "DOI:10.5067/MODIS/MYD021KM.061" (Identifier)
- record at pool position 5: 99dff022-24ac-48cb-bc83-09fec8b90ad7
- classed triple of the record at pool position 5: "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0" (Dataset) DOCUMENTED_AT "LAWRENCEETAL2013" (Document)
- ground truth schema entry: entity class Identifier
- ground truth schema entry: predicate HAS_DOI
- translation table row: entity class DOI
- translation table row: predicate HAS_DOI
- translation table row: predicate HAS_LATENCY
- translation table row: predicate HAS_IDENTIFIER
- rule: What counts as a fact, rule 1
- rule: Writing a classed triple, rule 10
- rule: Writing a classed triple, rule 11
- rule: Writing a classed triple, rule 14
- pipeline method: annotations/ground_truth_schema.txt: a new predicate for a latency and one for an identifier (option 3)
- pipeline method: common/common_prompts/extraction_rules.txt: the model's copy of the annotation guidelines' rules, which changes with a rule

## Q21: Should instruments, spacecraft, missions and physical quantities follow a reference list, and what should the knowledge graph answer?

- status: open
- priority: low
- question kind: general
- topic: reference lists for the ground truth schema's Instrument, Spacecraft, Mission and PhysicalQuantity, and the questions the knowledge graph is for

### The question

The ground truth writes each subject instance and object instance in the record's own words. For the instruments, spacecraft, missions and physical quantities of the ground truth schema, published lists of values exist, and a record's words could be checked against them, or replaced by them. I would like to know:

- (a) Which reference list do experts in this field rely on for the Instrument, Spacecraft, Mission and PhysicalQuantity of a dataset? The one I know of is the Global Change Master Directory (GCMD) Keywords, "a hierarchical set of controlled Earth Science vocabularies", with lists of Instruments/Sensors, Platforms/Sources, Projects, and Measurement Names, among others (https://www.earthdata.nasa.gov/data/tools/gcmd-keyword-viewer). Is it the right one for this catalog, and is there a list of the same standing for the planetary, astrophysics and heliophysics records, whose missions and instruments are beyond Earth science?
- (b) What questions should the knowledge graph built from this catalog be able to answer for you? For example: "Which datasets were collected by MODIS aboard Aqua at Level 3?", or "Which datasets cover the Arctic every day?". Your questions decide which facts matter most, and so which entity classes and predicates the ground truth schema needs.

### Context

The knowledge graph will be built from the records' metadata fields and the extracted triples. Two records that write one thing in two wordings (e.g. "Moderate Resolution Imaging Spectroradiometer (MODIS)" and "MODIS") give two different instances; a reference list would give one.

### Annotation guidelines

- Writing a classed triple, rule 1: Subject instance and object instance: the record's own words, as written.

### Options

#### Option 1: The record's own words everywhere (as now)

Every subject instance and object instance stays as the record writes it, and no reference list is used.

#### Option 2: Reference lists in the ground truth

For Instrument, Spacecraft, Mission and PhysicalQuantity, the instance is the reference list's value that the record's words mean, in place of the record's words.

#### Option 3: Own words in the ground truth, reference lists added later

Each record keeps its own words; the values on a reference list are added to the knowledge graph later, next to the record's words.

### My current reading

Undecided, leaning towards option 3, because it keeps the ground truth close to what each record states, and still lets the knowledge graph use a reference list. I would choose option 2 for an entity class whose values an expert says form a short, closed list.

### My notes

Linking instances to reference lists is on my list of improvements to the pipeline (quoted below, under Pipeline method), as a later stage that keeps each record's own words.

### Consequences

#### Option 1: The record's own words everywhere (as now)

- Nothing changes in the annotation guidelines or the ground truth schema.
- One value may appear in several wordings across records, so a search of the knowledge graph has to know each wording.

#### Option 2: Reference lists in the ground truth

- A new exception to rule 1 of *Writing a classed triple* (the record's own words, as written), in the annotation guidelines and in the copy of the rules the [model](../docs/terminology.md#8-the-pipeline) follows.
- The ground truth triples written so far are checked again, and some object instances change.
- A record's value that isn't on the list has no value to use, unless the list is complete for this catalog.

#### Option 3: Own words in the ground truth, reference lists added later

- The annotation guidelines and the ground truth don't change, and the knowledge graph can still be searched by a list's values.
- Work to match each wording to a list's value, outside the ground truth: on my list of improvements, not built yet.

### Affects

- record at pool position 1: cfd6ec3f-1e63-4a77-bc3f-007d45f7e2fc
- record at pool position 2: 6cfafd07-40f1-46da-9d92-36c2bb319f0b
- record at pool position 3: 2705e0d1-95e7-4588-813b-ca91a6da94ff
- record at pool position 4: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- record at pool position 5: 99dff022-24ac-48cb-bc83-09fec8b90ad7
- record at pool position 6: 4c64f3ed-39b4-4f95-95a0-022898ba47a4
- classed triple of the record at pool position 6: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) ACQUIRED_BY_INSTRUMENT "Moderate Resolution Imaging Spectroradiometer (MODIS)" (Instrument)
- classed triple of the record at pool position 6: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) FROM_SPACECRAFT "Terra" (Spacecraft)
- classed triple of the record at pool position 6: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) FROM_SPACECRAFT "Aqua" (Spacecraft)
- classed triple of the record at pool position 6: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) HAS_MEASUREMENTS_OF "Aerosol Optical Depth" (PhysicalQuantity)
- classed triple of the record at pool position 1: "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (Dataset) ACQUIRED_BY_INSTRUMENT "RSI" (Instrument)
- classed triple of the record at pool position 2: "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" (Dataset) ACQUIRED_BY_INSTRUMENT "Moderate Resolution Imaging Spectroradiometer (MODIS)" (Instrument)
- classed triple of the record at pool position 2: "radiance data" (Dataset) ACQUIRED_BY_INSTRUMENT "Moderate Resolution Imaging Spectroradiometer (MODIS)" (Instrument)
- classed triple of the record at pool position 2: "Moderate Resolution Imaging Spectroradiometer (MODIS)" (Instrument) ABOARD "Aqua" (Spacecraft)
- classed triple of the record at pool position 3: "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005" (Dataset) ACQUIRED_BY_INSTRUMENT "Aquarius L-band radiometer" (Instrument)
- classed triple of the record at pool position 4: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) ACQUIRED_BY_INSTRUMENT "Moderate-resolution Imaging Spectroradiometer (MODIS)" (Instrument)
- classed triple of the record at pool position 4: "Moderate-resolution Imaging Spectroradiometer (MODIS)" (Instrument) ABOARD "Aqua" (Spacecraft)
- classed triple of the record at pool position 4: "Moderate-resolution Imaging Spectroradiometer (MODIS)" (Instrument) HAS_SPECTRAL_BANDS "36 spectral bands" (Value)
- classed triple of the record at pool position 4: "mid-infrared 3.95 micron wavelength channel" (Channel) UNIQUE_TO_INSTRUMENT "Moderate-resolution Imaging Spectroradiometer (MODIS)" (Instrument)
- classed triple of the record at pool position 4: "mid-infrared 4.05 micron wavelength channel" (Channel) UNIQUE_TO_INSTRUMENT "Moderate-resolution Imaging Spectroradiometer (MODIS)" (Instrument)
- classed triple of the record at pool position 5: "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0" (Dataset) ACQUIRED_BY_INSTRUMENT "GRaND" (Instrument)
- classed triple of the record at pool position 5: "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0" (Dataset) ACQUIRED_BY_INSTRUMENT "GRaND plus Z boron loaded sensor" (Instrument)
- classed triple of the record at pool position 5: "GRaND plus Z boron loaded sensor" (Instrument) PART_OF "GRaND" (Instrument)
- classed triple of the record at pool position 5: "GRaND epithermal neutron map" (Dataset) ACQUIRED_BY_INSTRUMENT "GRaND" (Instrument)
- classed triple of the record at pool position 1: "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (Dataset) FROM_SPACECRAFT "ROSETTA-ORBITER" (Spacecraft)
- classed triple of the record at pool position 2: "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" (Dataset) FROM_SPACECRAFT "Aqua" (Spacecraft)
- classed triple of the record at pool position 4: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) FROM_SPACECRAFT "Aqua" (Spacecraft)
- classed triple of the record at pool position 4: "Aqua" (Spacecraft) LAUNCHED_BY_PARTY "NASA" (Organization)
- classed triple of the record at pool position 4: "Aqua" (Spacecraft) LAUNCHED_ON "May 4, 2002" (Time)
- classed triple of the record at pool position 4: "Aqua" (Spacecraft) HAS_ORBIT "sun synchronous, polar orbit with a daylight ascending node at 13:30" (Orbit)
- classed triple of the record at pool position 4: "Aqua" (Spacecraft) FLIES_IN "A-train" (SatelliteFormation)
- classed triple of the record at pool position 4: "Aqua" (Spacecraft) HAS_PURPOSE "study the global dynamics of the Earth atmosphere, land and oceans" (Purpose)
- classed triple of the record at pool position 5: "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0" (Dataset) FROM_SPACECRAFT "DAWN" (Spacecraft)
- classed triple of the record at pool position 1: "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (Dataset) FROM_MISSION "Rosetta" (Mission)
- classed triple of the record at pool position 3: "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005" (Dataset) FROM_MISSION "Aquarius/Satélite de Aplicaciones Científicas (SAC-D)" (Mission)
- classed triple of the record at pool position 3: "Aquarius/Satélite de Aplicaciones Científicas (SAC-D)" (Mission) DEVELOPED_BY_PARTY "National Aeronautics and Space Administration (NASA)" (Organization)
- classed triple of the record at pool position 3: "Aquarius/Satélite de Aplicaciones Científicas (SAC-D)" (Mission) DEVELOPED_BY_PARTY "Comisión Nacional de Actividades Espaciales (CONAE)" (Organization)
- classed triple of the record at pool position 1: "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (Dataset) HAS_MEASUREMENTS_OF "Gravity" (PhysicalQuantity)
- classed triple of the record at pool position 2: "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" (Dataset) HAS_MEASUREMENTS_OF "snow cover" (PhysicalQuantity)
- classed triple of the record at pool position 3: "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005" (Dataset) HAS_MEASUREMENTS_OF "Sea Surface Salinity (SSS)" (PhysicalQuantity)
- classed triple of the record at pool position 4: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) HAS_MEASUREMENTS_OF "skin sea surface temperature (SST)" (PhysicalQuantity)
- classed triple of the record at pool position 4: "skin SST (NSST)" (Variable) ESTIMATES "skin sea surface temperature (SST)" (PhysicalQuantity)
- classed triple of the record at pool position 4: "SST4" (Variable) ESTIMATES "SST" (PhysicalQuantity)
- classed triple of the record at pool position 5: "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0" (Dataset) RELATED_TO "average atomic mass" (PhysicalQuantity)
- translation table row: entity class Instrument
- translation table row: entity class Spacecraft
- translation table row: entity class SpaceStation
- translation table row: entity class Mission
- translation table row: entity class PhysicalQuantity
- ground truth schema entry: entity class Instrument
- ground truth schema entry: entity class Spacecraft
- ground truth schema entry: entity class Mission
- ground truth schema entry: entity class PhysicalQuantity
- rule: Writing a classed triple, rule 1
- pipeline method: docs/improvements.md: linking subject instances and object instances to reference lists
- pipeline method: common/common_prompts/extraction_rules.txt: the model's copy of the annotation guidelines' rules, which changes with a rule

### Pipeline method

- docs/improvements.md: Linking subject instances and object instances to reference lists, so that one thing named several ways ("Aqua", "EOS PM-1") becomes one node.

## Q22: Is a title's "4km" the notes' "4.63 km"?

- status: open
- priority: low
- question kind: records and triples
- topic: the ground truth schema's SpatialResolution and HAS_SPATIAL_RESOLUTION, and rules 11 and 13 of the annotation guidelines

### The question

The title of the example below says "4km", and its notes say the products "are available at both 4.63 and 9.26 km spatial resolution". Rule 13 of the annotation guidelines writes one thing with one wording in a record, the more precise one when two wordings name the same thing; its own example is this record: "a title says "4km" and the notes say "4.63 km". Then: "4.63 km", the more precise." So I wrote "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) HAS_SPATIAL_RESOLUTION "4.63 km" (SpatialResolution), and nothing for 9.26 km, which rule 11 leaves out as a fact about another dataset (the same data at another resolution). Whether that is right depends on facts I can't check from the record. I would like to know:

- (a) Is "4km" in such a title the rounded name of the 4.63 km grid, so that the two name one resolution? My reading, not checked against a source: 4.63 km is about 1/24 of a degree at the equator, and the products are named by the rounded value.
- (b) Is the dataset of this record only the 4.63 km one, with the 9.26 km products in a record of their own, so that 9.26 km is about another dataset?
- (c) The record "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" is the same case: its title says "1km" and its notes "produced daily at 1 kilometer (km) pixel resolutions", and I have written "1 kilometer (km)", the wording that spells out its abbreviation. Is a title's rounded or shortened value always the notes' value, for products of this catalog, or can the two differ?

### Context

The spatial resolutions I have written so far: "500m" (the record "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061"), "4.63 km" (the example below), and, in a draft, "1 kilometer (km)" (the record "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid").

### Example record

- record id: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- pool position: 4
- title: MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0
- notes: Day and night spatially gridded (L3) global NASA skin sea surface temperature (SST) products from the Moderate-resolution Imaging Spectroradiometer (MODIS) onboard the Aqua satellite. Average daily, weekly (8 day), monthly and annual skin SST products at are available at both 4.63 and 9.26 km spatial resolution. Aqua was launched by NASA on May 4, 2002, into a sun synchronous, polar orbit with a daylight ascending node at 13:30, formation flying in the A-train with other Earth Observation Satellites (EOS), to study the global dynamics of the Earth atmosphere, land and oceans. MODIS captures data in 36 spectral bands at a variety of spatial resolutions. Two SST products can be present in these files. The first is a skin SST produced for both day and night (NSST) observations, derived from the long wave IR 11 and 12 micron wavelength channels, using a modified nonlinear SST algorithm intended to provide continuity of SST derived from heritage and current NASA sensors. At night, a second SST product is generated using the mid-infrared 3.95 and 4.05 micron wavelength channels which are unique to MODIS; the SST derived from these measurements is identified as SST4. The SST4 product has lower uncertainty, but due to sun glint can only be used at night. To generate the L3 products the L2 pixels are binned into an integerized sinusoidal area grid (ISEAG) and mapped into an equidistant cylindrical (also known as Platte Carre projection. Additional projection detailed can be found at https://oceancolor.gsfc.nasa.gov/docs/format/ The NASA MODIS L3 SST data products are generated by the NASA Ocean Biology Processing Group (OBPG) and Peter Minnett and his team at the Rosenstiel School of Marine and Atmospheric Science (RSMAS) are responsible for sea surface temperature algorithm development, error statistics and quality flagging. JPL acquires MODIS ocean L3 SST data from the OBPG and is the official Physical Oceanography Data Archive (PO.DAAC) for SST. The R2019.0 supersedes the previous v2014.1 datasets which can be found at https://doi.org/10.5067/MODAM-8D4N4
- source text: 4km
- source text: available at both 4.63 and 9.26 km spatial resolution
- classed triple: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) HAS_SPATIAL_RESOLUTION "4.63 km" (SpatialResolution)

### Ground truth schema

- entity class SpatialResolution: the amount of ground each value of the data covers, e.g. 500 m; 4.63 km
- predicate HAS_SPATIAL_RESOLUTION: each of its values covers this much ground, e.g. 500 m

### Annotation guidelines

- Writing a classed triple, rule 11: Leave out a fact about another dataset, even a closely related one, such as the same data at another time step or resolution. That dataset has its own record, and its facts go there.
- Writing a classed triple, rule 13: One thing, one wording, within a record. When a record names the same thing more than once, in different words: if one wording says more (it contains the other, is more precise, or spells out its abbreviation), use it

### Options

#### Option 1: Keep the notes' value (as now)

The dataset HAS_SPATIAL_RESOLUTION "4.63 km" (SpatialResolution), the more precise wording, and no fact for 9.26 km.

#### Option 2: The title's value, when the two differ

"4km" is a resolution of its own, not the rounded 4.63 km: the dataset HAS_SPATIAL_RESOLUTION "4km" (SpatialResolution), and rule 13's example changes.

### My current reading

Option 1, because rule 13 takes the more precise wording and the record's own words give 4.63 km as one of the two resolutions it is available at. I would move to option 2 only if experts say a title's value and the notes' value can name different resolutions.

### My notes

The example is the record at pool position 4. The ground truth triples with HAS_SPATIAL_RESOLUTION so far are listed under Affects: "500m" (pool position 2), "4.63 km" (pool position 4), and my draft "1 kilometer (km)" (pool position 6, which I am annotating now).

### Consequences

#### Option 1: Keep the notes' value (as now)

- Nothing changes.
- If "4km" and 4.63 km are one resolution, the ground truth names it the more precise way, and a search by the title's "4km" must know that.

#### Option 2: The title's value, when the two differ

- One ground truth triple changes its object instance, and rule 13's example in the annotation guidelines and in the copy of the rules the [model](../docs/terminology.md#8-the-pipeline) follows changes.
- The notes' "4.63 and 9.26 km" would then describe the products in general, not this dataset.

### Affects

- record at pool position 2: 6cfafd07-40f1-46da-9d92-36c2bb319f0b
- record at pool position 4: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- record at pool position 6: 4c64f3ed-39b4-4f95-95a0-022898ba47a4
- classed triple of the record at pool position 2: "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" (Dataset) HAS_SPATIAL_RESOLUTION "500m" (SpatialResolution)
- classed triple of the record at pool position 4: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) HAS_SPATIAL_RESOLUTION "4.63 km" (SpatialResolution)
- classed triple of the record at pool position 6: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) HAS_SPATIAL_RESOLUTION "1 kilometer (km)" (SpatialResolution)
- ground truth schema entry: entity class SpatialResolution
- ground truth schema entry: predicate HAS_SPATIAL_RESOLUTION
- translation table row: entity class SpatialResolution
- translation table row: predicate HAS_RESOLUTION
- rule: Writing a classed triple, rule 11
- rule: Writing a classed triple, rule 13

## Q23: Is the A-train a formation, a constellation, or something else?

- status: open
- priority: low
- question kind: schema entry
- topic: the ground truth schema's SatelliteFormation and FLIES_IN

### The question

The example below says Aqua was launched "into a sun synchronous, polar orbit with a daylight ascending node at 13:30, formation flying in the A-train with other Earth Observation Satellites (EOS)". I wrote "Aqua" (Spacecraft) FLIES_IN ("flies in formation as part of") "A-train" (SatelliteFormation), a SatelliteFormation being "a group of Spacecraft flying together in formation in orbit, e.g. the A-train". The A-train may be read in more than one way, and I would like to know:

- (a) Is the A-train a formation (spacecraft flying close together, in an arrangement kept on purpose), a constellation (spacecraft in coordinated orbits, which need not fly close together), or something else? My reading, not checked against a source: NASA also calls it the "Afternoon Constellation".
- (b) If it is a constellation: should the ground truth schema's entity class be one for any group of spacecraft that work together (a constellation, a formation, a train), or should formations and constellations be told apart?
- (c) Is "formation flying in the A-train" a fact about Aqua (the spacecraft) or about its mission?

### Context

Of the records I have read so far, the example below is the only one that names a group of spacecraft.

### Example record

- record id: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- pool position: 4
- title: MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0
- notes: Day and night spatially gridded (L3) global NASA skin sea surface temperature (SST) products from the Moderate-resolution Imaging Spectroradiometer (MODIS) onboard the Aqua satellite. Average daily, weekly (8 day), monthly and annual skin SST products at are available at both 4.63 and 9.26 km spatial resolution. Aqua was launched by NASA on May 4, 2002, into a sun synchronous, polar orbit with a daylight ascending node at 13:30, formation flying in the A-train with other Earth Observation Satellites (EOS), to study the global dynamics of the Earth atmosphere, land and oceans. MODIS captures data in 36 spectral bands at a variety of spatial resolutions. Two SST products can be present in these files. The first is a skin SST produced for both day and night (NSST) observations, derived from the long wave IR 11 and 12 micron wavelength channels, using a modified nonlinear SST algorithm intended to provide continuity of SST derived from heritage and current NASA sensors. At night, a second SST product is generated using the mid-infrared 3.95 and 4.05 micron wavelength channels which are unique to MODIS; the SST derived from these measurements is identified as SST4. The SST4 product has lower uncertainty, but due to sun glint can only be used at night. To generate the L3 products the L2 pixels are binned into an integerized sinusoidal area grid (ISEAG) and mapped into an equidistant cylindrical (also known as Platte Carre projection. Additional projection detailed can be found at https://oceancolor.gsfc.nasa.gov/docs/format/ The NASA MODIS L3 SST data products are generated by the NASA Ocean Biology Processing Group (OBPG) and Peter Minnett and his team at the Rosenstiel School of Marine and Atmospheric Science (RSMAS) are responsible for sea surface temperature algorithm development, error statistics and quality flagging. JPL acquires MODIS ocean L3 SST data from the OBPG and is the official Physical Oceanography Data Archive (PO.DAAC) for SST. The R2019.0 supersedes the previous v2014.1 datasets which can be found at https://doi.org/10.5067/MODAM-8D4N4
- source text: Aqua was launched by NASA on May 4, 2002, into a sun synchronous, polar orbit with a daylight ascending node at 13:30, formation flying in the A-train with other Earth Observation Satellites (EOS)
- classed triple: "Aqua" (Spacecraft) FLIES_IN "A-train" (SatelliteFormation)

### Ground truth schema

- entity class SatelliteFormation: a group of Spacecraft flying together in formation in orbit, e.g. the A-train
- predicate FLIES_IN: flies in formation as part of
- entity class Spacecraft: a craft that operates in space

### Options

#### Option 1: Keep SatelliteFormation as it is

The A-train stays a SatelliteFormation, as the record's own words "formation flying" say.

#### Option 2: One entity class for any group of spacecraft

An entity class for any group of spacecraft that work together, in place of SatelliteFormation, with a definition that covers formations, constellations and trains, and FLIES_IN read as "is part of this group".

### My current reading

Option 1 for now, because the record itself says "formation flying". I would move to option 2 if experts say the A-train is a constellation, or that the difference doesn't matter for a search of this catalog.

### My notes

The example is the record at pool position 4, the only tuning record annotated so far that names a group of spacecraft; its one classed triple with FLIES_IN is listed under Affects.

### Consequences

#### Option 1: Keep SatelliteFormation as it is

- Nothing changes.
- If the A-train is a constellation, the definition of SatelliteFormation, and its example, say something an expert would not.

#### Option 2: One entity class for any group of spacecraft

- The entity class and predicate are renamed and redefined in the ground truth schema; the one ground truth triple keeps its instances.
- Groups of spacecraft that other records name are written the same way, whatever their arrangement.

### Affects

- record at pool position 4: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- classed triple of the record at pool position 4: "Aqua" (Spacecraft) FLIES_IN "A-train" (SatelliteFormation)
- ground truth schema entry: entity class SatelliteFormation
- ground truth schema entry: predicate FLIES_IN

## Q24: Should facts about a product family be recorded, and as what?

- status: open
- priority: medium
- question kind: records and triples
- topic: rule 11 of the annotation guidelines, and the facts about the other versions, time steps and resolutions of a product

### The question

The notes of a record often describe more than the one dataset the record is about: they describe the product family it belongs to. The example below is titled "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0", so its dataset is the 8-day, 4 km (4.63 km), nighttime product; its notes say that "Average daily, weekly (8 day), monthly and annual skin SST products at are available at both 4.63 and 9.26 km spatial resolution", and begin "Day and night spatially gridded (L3) ... products". So the record also states which time steps (daily, monthly, annual), which resolution (9.26 km) and which time of day (day) the other products of the family have. Rule 11 of the annotation guidelines leaves these out, because each of those products is another dataset with a record of its own, where its facts go. The ground truth then says that this dataset is "weekly (8 day)" and "4.63 km", and nothing says that the others exist. I would like to know:

- (a) Is the information about the family worth keeping, in a knowledge graph of this catalog? Would someone ask "which time steps does this product come in?", or "is there a 9.26 km version of it?", and expect an answer from the record that describes only one of them?
- (b) If it is, as what? As facts about each of the other products (each of them a dataset, but with no record of its own to hold its title), as facts about a family of products (a group of datasets sharing a name, with the family's own facts), or on the instrument that makes them?
- (c) Where a family is named by one record only, as here, is a fact such as "there is also a daily product" about this dataset (it has siblings), or only about the family?

### Context

The same happens with the releases of a product: the record also says "The R2019.0 supersedes the previous v2014.1 datasets which can be found at https://doi.org/10.5067/MODAM-8D4N4", and I wrote only that "V2019.0" replaces "v2014.1", not the address of the older datasets. Another record of the catalog (titled "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid") names the standard product and its Near Real Time sibling in one sentence.

How the groups of datasets could be written, if they are, depends on how the ground truth schema treats kinds and parts of things; that is asked in another question (Q25).

### Example record

- record id: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- pool position: 4
- title: MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0
- notes: Day and night spatially gridded (L3) global NASA skin sea surface temperature (SST) products from the Moderate-resolution Imaging Spectroradiometer (MODIS) onboard the Aqua satellite. Average daily, weekly (8 day), monthly and annual skin SST products at are available at both 4.63 and 9.26 km spatial resolution. Aqua was launched by NASA on May 4, 2002, into a sun synchronous, polar orbit with a daylight ascending node at 13:30, formation flying in the A-train with other Earth Observation Satellites (EOS), to study the global dynamics of the Earth atmosphere, land and oceans. MODIS captures data in 36 spectral bands at a variety of spatial resolutions. Two SST products can be present in these files. The first is a skin SST produced for both day and night (NSST) observations, derived from the long wave IR 11 and 12 micron wavelength channels, using a modified nonlinear SST algorithm intended to provide continuity of SST derived from heritage and current NASA sensors. At night, a second SST product is generated using the mid-infrared 3.95 and 4.05 micron wavelength channels which are unique to MODIS; the SST derived from these measurements is identified as SST4. The SST4 product has lower uncertainty, but due to sun glint can only be used at night. To generate the L3 products the L2 pixels are binned into an integerized sinusoidal area grid (ISEAG) and mapped into an equidistant cylindrical (also known as Platte Carre projection. Additional projection detailed can be found at https://oceancolor.gsfc.nasa.gov/docs/format/ The NASA MODIS L3 SST data products are generated by the NASA Ocean Biology Processing Group (OBPG) and Peter Minnett and his team at the Rosenstiel School of Marine and Atmospheric Science (RSMAS) are responsible for sea surface temperature algorithm development, error statistics and quality flagging. JPL acquires MODIS ocean L3 SST data from the OBPG and is the official Physical Oceanography Data Archive (PO.DAAC) for SST. The R2019.0 supersedes the previous v2014.1 datasets which can be found at https://doi.org/10.5067/MODAM-8D4N4
- source text: Day and night spatially gridded (L3) global NASA skin sea surface temperature (SST) products
- source text: Average daily, weekly (8 day), monthly and annual skin SST products
- source text: available at both 4.63 and 9.26 km spatial resolution
- source text: The R2019.0 supersedes the previous v2014.1 datasets
- classed triple: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) HAS_TEMPORAL_RESOLUTION "weekly (8 day)" (TemporalResolution)
- classed triple: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) HAS_SPATIAL_RESOLUTION "4.63 km" (SpatialResolution)
- classed triple: "V2019.0" (Version) SUPERSEDES "v2014.1" (Version)

### Ground truth schema

- entity class TemporalResolution: the amount of time between one value of the data and the next, e.g. daily; weekly (8 day)
- predicate HAS_TEMPORAL_RESOLUTION: gives values this often, e.g. daily; weekly (8 day)
- entity class SpatialResolution: the amount of ground each value of the data covers, e.g. 500 m; 4.63 km
- predicate HAS_SPATIAL_RESOLUTION: each of its values covers this much ground, e.g. 500 m
- predicate SUPERSEDES: replaces this earlier one

### Annotation guidelines

- Writing a classed triple, rule 11: Leave out a fact about another dataset, even a closely related one, such as the same data at another time step or resolution. That dataset has its own record, and its facts go there.

### Options

#### Option 1: Leave them out, as now

The family's other time steps, resolutions and times of day are not recorded, by rule 11. A search finds this dataset by its own time step and resolution only.

#### Option 2: A new entity class for a product family, with its own facts

A family of products (for the example, the MODIS Aqua skin sea surface temperature products) is a thing of its own, with its time steps, resolutions and times of day as its facts, and the dataset of the record is one of its members.

#### Option 3: Record them on the instrument

The facts are written about the instrument that makes the products, as general facts about it (rule 11 includes general facts about a dataset's instrument): the instrument "Moderate-resolution Imaging Spectroradiometer (MODIS)" with the time steps and resolutions of its skin sea surface temperature products.

#### Option 4: Another way

Please describe it.

### My current reading

Option 1 for now, because rule 11 says so and the family facts need an entity class and predicates the ground truth schema does not have. But I think the information is worth keeping if an expert says people ask for it, and I would then lean towards option 2, since the facts are about the family, not about one instrument. I would like to know first whether a person looking for this product would expect to learn the other time steps and resolutions from this record.

### My notes

The example is the record at pool position 4, the densest record I have annotated: the items its notes leave out are listed in `annotations/left_out.md`. Q22 asks a narrower question about the same sentence (is the title's "4km" the notes' "4.63 km"), and Q5 (b) what the "Average" means; neither is settled by this one. I decided against merging this into Q19 (releases, "R2019.0" and "Collection"): an answer about whether "R2019.0" is "V2019.0" does not settle whether a family of products is recorded. It is not merged into Q25 either: Q25 asks how the schema groups things; this asks whether the facts are wanted at all, and one answer to this does not settle the other, though option 2 needs Q25's answer for a part-of predicate.

Items of `annotations/left_out.md` that this answer may bring back as ground truth triples:

- the record at pool position 4: "Day"; "daily", "monthly" and "annual"; "9.26 km"; "Average"; the DOI of the previous v2014.1 datasets;
- the record at pool position 6: the Near Real Time (NRT) product and the product MCD19A1N computed from this dataset, as members of a family (their own question: Q20).

### Consequences

#### Option 1: Leave them out, as now

- Nothing changes.
- The ground truth never holds a fact of a family, and the model's extracted triples that state one count as wrong.

#### Option 2: A new entity class for a product family, with its own facts

- A new entity class and a predicate saying a dataset is a member of a family (see Q25), in the ground truth schema, with their definitions, and an example in rule 11 of the annotation guidelines and in the model's copy of the rules.
- The listed items become ground truth triples of the family; the record at pool position 4 gets one more ground truth triple, for the membership.
- Every record that lists its siblings is written the same way, so a family has one name in all of them: the work of joining the names of one family grows.

#### Option 3: Record them on the instrument

- The facts are written about MODIS, not about the dataset or its family; they would say that the instrument has "daily" and "monthly" products, which is true of one product of it only, not of all.
- Rule 11's second sentence changes.

#### Option 4: Another way

- Depends on the answer.

### Affects

- record at pool position 4: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- record at pool position 6: 4c64f3ed-39b4-4f95-95a0-022898ba47a4
- classed triple of the record at pool position 4: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) HAS_TEMPORAL_RESOLUTION "weekly (8 day)" (TemporalResolution)
- classed triple of the record at pool position 4: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) HAS_SPATIAL_RESOLUTION "4.63 km" (SpatialResolution)
- classed triple of the record at pool position 4: "V2019.0" (Version) SUPERSEDES "v2014.1" (Version)
- rule: Writing a classed triple, rule 11
- pipeline method: common/common_prompts/extraction_rules.txt: the model's copy of the annotation guidelines' rules, which changes with a rule

## Q25: Which entity classes are kinds of others, and which groupings of things matter?

- status: open
- priority: medium
- question kind: schema entry
- topic: the ground truth schema as a flat list of entity classes, and its PART_OF predicate

### The question

The ground truth schema is a flat list: no entity class is a kind of another, and no predicate says a thing belongs to a group of things, except PART_OF ("is one part of"), which I coined for one record. Two questions follow, and I would like to know:

- (1) Which entity classes are kinds of others? My guess: a Spacecraft, an aircraft, a ship, a balloon and a ground station are kinds of a platform (the thing that carries instruments; whether this catalog needs one entity class for it is Q4 (d)); a Person, a Team and an Organization are kinds of an agent (a party that develops, sponsors, launches or is responsible for something). If these were kinds of a larger entity class, a predicate such as "developed by" could say "any agent" instead of listing the three, and a search could ask for anything a platform carries. Are these two groups right? Which other kinds of kinds do you see in this catalog (for example, a Dataset and a Document as kinds of something that holds information)?
- (2) Which groupings of instances matter? In the example below, the notes name a part of an instrument: "GRaND plus Z boron loaded sensor" is one part of "GRaND". Other groupings of the same shape: a product family (the daily, weekly, monthly and annual products of one kind of data, Q24), a mission and its phases, a formation and its spacecraft. For each, is "is part of" the right link, or are they different kinds of link (a member of a group, a part of a whole, a phase of a mission) that should not share one predicate?

### Context

Today each predicate lists the entity classes it takes, so "developed by" lists Organization, Person and Team one by one. A hierarchy (an entity class that is a kind of another) is standard in schemas of knowledge graphs; adding one to the ground truth schema would change how the ground truth is written and how the model's schema is compared with it, so I want to know first whether the catalog needs it.

### Example record

- record id: 99dff022-24ac-48cb-bc83-09fec8b90ad7
- pool position: 5
- title: DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0
- notes: These data are maps of fast neutron residual count rates from the GRaND plus Z boron loaded sensor. The nominal fast neutron count rates were detrended using the GRaND epithermal neutron map to produced this residual map. The residual map is related to the average atomic mass on Vesta. Details of the map and data reduction are described in LAWRENCEETAL2013.
- source text: the GRaND plus Z boron loaded sensor
- classed triple: "GRaND plus Z boron loaded sensor" (Instrument) PART_OF "GRaND" (Instrument)

### Ground truth schema

- entity class Instrument: a device that takes measurements
- entity class Spacecraft: a craft that operates in space
- entity class Organization: a named institution or one of its named parts, not a Mission, e.g. NASA; OBPG
- entity class Team: a group of people without a name of its own, e.g. Peter Minnett and his team
- entity class Person: one named human being, e.g. Peter Minnett
- predicate PART_OF: is one part of

### Options

#### Option 1: Keep the schema flat

No entity class is a kind of another, and PART_OF stays for any part of a whole.

#### Option 2: A hierarchy of entity classes, and PART_OF as it is

Entity classes get kinds (for example a platform with Spacecraft, aircraft, ship, balloon and ground station under it; an agent with Person, Team and Organization under it), and PART_OF keeps its one meaning.

#### Option 3: A hierarchy, and separate links for a part, a member and a phase

As option 2, and the groupings of question (2) get one predicate each (part of a whole; member of a group; phase of a mission).

#### Option 4: Another way

Please describe it.

### My current reading

Option 1 for now: the ground truth has one use of PART_OF and no record whose facts need a kind of a kind. I would move to option 2 if experts say the two groups of question (1) are right, since the same fact is then asked across several entity classes, and I would add the separate links of option 3 only for groupings that experts say differ.

### My notes

The example is the record at pool position 5, the only tuning record annotated so far with a PART_OF triple (listed under Affects). Q4 (d) asks the platform half of (1) for the data's carriers; Q24 is the product family half of (2), kept apart because it asks whether the family facts are wanted at all. Both would use the hierarchy this question asks for if it is kept: the improvements item "An entity class hierarchy for the schemas" (`docs/improvements.md`) lists what it touches (the schema reader and its file format, the pin check, step 040's induced schema, the translation table). The same file's item "Kinds of translation, not only "means the same"" would let a row of the translation table say a current-schema entity class is narrower or broader than a ground truth schema one, instead of only equal or none: with a hierarchy, a row for an aircraft could say it is a kind of a platform.

### Consequences

#### Option 1: Keep the schema flat

- Nothing changes.
- A pin lists every entity class one by one, and a question across kinds (anything that carries instruments) can't be asked.

#### Option 2: A hierarchy of entity classes, and PART_OF as it is

- The ground truth schema's file format, the schema reader, the pin check, step 040's induced schema and step 070's translation table change; each umbrella entity class gets a definition.
- A translation row can say narrower or broader, not only the same or none.
- PART_OF is read for any grouping, as now.

#### Option 3: A hierarchy, and separate links for a part, a member and a phase

- As option 2, and the one ground truth triple with PART_OF may be renamed; Q24's option 2 gets its membership predicate.

#### Option 4: Another way

- Depends on the answer.

### Affects

- record at pool position 5: 99dff022-24ac-48cb-bc83-09fec8b90ad7
- classed triple of the record at pool position 5: "GRaND plus Z boron loaded sensor" (Instrument) PART_OF "GRaND" (Instrument)
- ground truth schema entry: predicate PART_OF
- translation table row: predicate PART_OF
- translation table row: predicate CONTAINS
- pipeline method: docs/improvements.md: An entity class hierarchy for the schemas
- pipeline method: docs/improvements.md: Judgements are Equivalent, Narrower, Broader, or Unrelated
